#!/bin/bash

export $(cat /home/pi/boiler-bot/OT_test/boiler-config.env | grep -v ^'#' | xargs)
#Download and save ROOT-CA to /greengrass/certs/
sudo mkdir -p /"$dev_id"/certs
sudo wget -O /"$dev_id"/certs/root.ca.pem http://www.symantec.com/content/en/us/enterprise/verisign/roots/VeriSign-Class%203-Public-Primary-Certification-Authority-G5.pem

# Check if the certs are already downloaded
count=`ls -1 /"$dev_id"/certs/*.key 2>/dev/null | wc -l`

#Downloading keys into the device
# export $(cat ~/test/boiler-config.env | grep -v ^'#' | xargs)
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

		sudo curl  -H "Host: ${bucket}.s3.amazonaws.com" \
		     -H "Date: ${dateValue}" \
		     -H "Content-Type: ${contentType}" \
		     -H "Authorization: AWS ${s3Key}:${signature}" \
		     --fail https://${bucket}.s3.amazonaws.com/${file}$i -o "/$deviceid/certs/$deviceid.$i"

	done

	count=`ls -1 /$deviceid/certs/*.key 2>/dev/null | wc -l`
	if [[ "$count" -eq 0 ]]
	then
		sleep 30s
	fi

done

# unset dev_id deviceid file auth_path bucket s3_bucket s3Key s3_access s3Secret s3_secret resource stringToSign signature

# Start ebusd
ebus_pid=`/bin/ps -fu root| grep "ebusd" | grep -v "grep" | awk '{print $2}'`
if [[ "$ebus_pid" -eq ""  ]]
then
	sudo /usr/bin/ebusd --scanconfig --lograwdata --receivetimeout=25000
        sleep 2s
	ebusctl scan 08
        echo ebusd started with pid =	
        pidof ebusd
fi
echo going live
#exec python /home/ubuntu/final_test/final_db_script.py
# /home/ubuntu/final_test/final_db_script.py |& tee -a log
/home/pi/boiler-bot/OT_test/mqtt_live.py |& tee -a /home/pi/boiler-bot/OT_test/batch_live_log

