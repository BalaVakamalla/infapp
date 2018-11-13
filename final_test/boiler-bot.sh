#!/bin/bash

#Install Python3 and pip3 if not installed
if [ ! command -v python3 &>/dev/null ]
then #Check if python3 is installed
	sudo apt update
	sudo apt install python3 -y         #Install Python3
	sudo apt install python3-pip -y     #Install pip3
fi

# Add Greengrass User and Group if not exists
if [ ! id -u ggc_user &>/dev/null ]
then
	sudo adduser --system ggc_user
	sudo groupadd --system ggc_group

	echo "fs.protected_hardlinks = 1" | sudo tee -a /etc/sysctl.d/??-sysctl.conf
	echo "fs.protected_symlinks = 1" | sudo tee -a /etc/sysctl.d/??-sysctl.conf

	sudo reboot
fi

#Download and save ROOT-CA to /greengrass/certs/
sudo wget -O /greengrass/certs/root.ca.pem  http://www.symantec.com/content/en/us/enterprise/verisign/roots/VeriSign-Class%203-Public-Primary-Certification-Authority-G5.pem

#Installing keys into the greengrass device
count=`ls -1 /greengrass/certs/*.key 2>/dev/null | wc -l`			#checks if the certs are already downloaded
export $(cat ~/final_test/boiler-config.env | grep -v ^'#' | xargs)
while [[ "$count" -eq 0 ]]
do
	#Downloading the keys
	declare -a certExt=("private.key" "public.key" "cert.pem")              ## declare an array with values as certificate extensions
	deviceid="$dev_id"
	file="$auth_path/$deviceid/$deviceid."
	bucket="$s3_bucket"
	dateValue=`date -R`
	s3Key="$s3_access"
	s3Secret="$s3_secret"
	for i in "${certExt[@]}"
	do
		resource="/${bucket}/${file}$i"
		contentType="device/certificate"
		stringToSign="GET\n\n${contentType}\n${dateValue}\n${resource}"
		signature=`echo -en ${stringToSign} | openssl sha1 -hmac ${s3Secret} -binary | base64`
		echo "File is $file"

		sudo curl  -H "Host: ${bucket}.s3.amazonaws.com" \
		     -H "Date: ${dateValue}" \
		     -H "Content-Type: ${contentType}" \
		     -H "Authorization: AWS ${s3Key}:${signature}" \
		     --fail https://${bucket}.s3.amazonaws.com/${file}$i -o "/greengrass/certs/$deviceid.$i"
	done

	#Downloading the config.json file
	resource="/${bucket}/${file}config.json"
	contentType="application/json"
	stringToSign="GET\n\n${contentType}\n${dateValue}\n${resource}"
	signature=`echo -en ${stringToSign} | openssl sha1 -hmac ${s3Secret} -binary | base64`
	echo $resource

	sudo curl  -H "Host: ${bucket}.s3.amazonaws.com" \
	     -H "Date: ${dateValue}" \
	     -H "Content-Type: ${contentType}" \
	     -H "Authorization: AWS ${s3Key}:${signature}" \
	     --fail https://${bucket}.s3.amazonaws.com/${file}config.json -o "/greengrass/config/config.json"

	count=`ls -1 /greengrass/certs/*.key 2>/dev/null | wc -l`
	if [[ "$count" -eq 0 ]]
	then
		sleep 30s
	fi

done

#unset dev_id deviceid file auth_path bucket s3_bucket s3Key s3_access s3Secret s3_secret resource stringToSign signature

# Start ebusd
ebus_pid=`/bin/ps -fu root| grep "ebusd" | grep -v "grep" | awk '{print $2}'`
if [[ "$ebus_pid" -eq ""  ]]
then
	sudo /usr/bin/ebusd --scanconfig --lograwdata --receivetimeout=25000
        sleep 2s
	ebusctl scan 08
	pidof ebusd
fi

# Starts greengrass if not already running
gg_pid=`/bin/ps -fu root| grep "greengrass" | grep -v "grep" | awk '{print $2}'`
if [[ "$gg_pid" -eq ""  ]]
then
	# Starting greengrassd
	sudo /greengrass/ggc/core/greengrassd start
	sleep 5s
fi

#exec python /home/ubuntu/final_test/final_db_script.py
/home/ubuntu/final_test/final_db_script.py |& tee -a log