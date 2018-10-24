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

#Installing keys into the greengrass device
if [ ! -e root.ca.pem ]
then
	#Download and save ROOT-CA to /greengrass/certs/
	sudo wget -O /greengrass/certs/root.ca.pem  http://www.symantec.com/content/en/us/enterprise/verisign/roots/VeriSign-Class%203-Public-Primary-Certification-Authority-G5.pem

	#Download cert keys from S3 bucket using CURL to /greengrass/certs/
	s3FilePath="boilerbot/devices-certificates/1539963012-03d7"
	amzFile="1539963012-03d7."
	declare -a certExt=("key" "public.key")		## declare an array with values as certificate extensions
	bucket="davidf-provisioning-test"
	resource="/${bucket}/${amzFile}/${s3FilePath}"
	contentType="device/certificate"
	dateValue=`date -R`
	stringToSign="GET\n\n${contentType}\n${dateValue}\n${resource}"
	s3Key="AKIAJ2YOT47HVNNQYIHA"
	s3Secret="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"
	signature=`echo -en ${stringToSign} | openssl sha1 -hmac ${s3Secret} -binary | base64`

	for i in "${certExt[@]}"
	do
		sudo curl  -H "Host: ${bucket}.s3.amazonaws.com" \
		     -H "Date: ${dateValue}" \
		     -H "Content-Type: ${contentType}" \
		     -H "Authorization: AWS ${s3Key}:${signature}" \
		     https://${bucket}.s3.amazonaws.com/${s3FilePath}${amzFile}$i -o "/greengrass/certs/${amzFile}$i"
	done
fi

# Starting greengrassd
sudo bash /greengrass/ggc/core/greengrassd start
