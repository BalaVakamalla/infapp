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
while [ count = 0 ]
do
	#Downloading the keys
	declare -a certExt=("private.key" "public.key" "cert.pem")              ## declare an array with values as certificate extensions
	file="boilerbot/devices-certificates/54268963-cc76-4776-b290-cd188563e3e7/54268963-cc76-4776-b290-cd188563e3e7."
	bucket="boilerbot-provisioning"
	dateValue=`date -R`
	s3Key="AKIAI56LNSUKIXBZWPMQ"
	s3Secret="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"
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
		     --fail https://${bucket}.s3.amazonaws.com/${file}$i -o "/greengrass/certs/cert.$i"
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
	sleep 30s
done

# Starting greengrassd
sudo /greengrass/ggc/core/greengrassd start
