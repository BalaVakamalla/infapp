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
count=`ls -1 /greengrass/certs/*.key 2>/dev/null | wc -l`
while [ count = 0 ]
do
	declare -a certExt=("private.key" "public.key" "cert.pem")              ## declare an array with values as certificate extensions
	for i in "${certExt[@]}"
	do
		file="boilerbot/devices-certificates/c48043bb-c0c5-4b44-a5fa-6dac3eff5d78/c48043bb-c0c5-4b44-a5fa-6dac3eff5d78."
		bucket="boilerbot-provisioning"
		resource="/${bucket}/${file}$i"
		contentType="device/certificate"
		dateValue=`date -R`
		stringToSign="GET\n\n${contentType}\n${dateValue}\n${resource}"
		s3Key="AKIAI56LNSUKIXBZWPMQ"
		s3Secret="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"
		signature=`echo -en ${stringToSign} | openssl sha1 -hmac ${s3Secret} -binary | base64`
		echo $resource

		curl  -H "Host: ${bucket}.s3.amazonaws.com" \
		     -H "Date: ${dateValue}" \
		     -H "Content-Type: ${contentType}" \
		     -H "Authorization: AWS ${s3Key}:${signature}" \
		     --fail https://${bucket}.s3.amazonaws.com/${file}$i -o "/greengrass/certs/${file}$i"
	done
	count=`ls -1 /greengrass/certs/*.key 2>/dev/null | wc -l`
	sleep 30s
done

# Starting greengrassd
sudo /greengrass/ggc/core/greengrassd start
