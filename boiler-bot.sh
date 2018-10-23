#!/bin/bash

#Install Python3 and pip3 if not installed
if command -v python3 &>/dev/null; then #Check if python3 is installed
	echo Python3 is installed           #Python 3 is installed
else
	echo Python3 not installed
	sudo apt update
	sudo apt install python3 -y         #Install Python3
	sudo apt install python3-pip -y     #Install pip3
fi

# Add Greengrass User and Group if not exists
if [ ! id -u ggc_user &>/dev/null ]; then
	sudo adduser --system ggc_user
        sudo groupadd --system ggc_group

	echo "fs.protected_hardlinks = 1" | sudo tee -a /etc/sysctl.d/??-sysctl.conf
        echo "fs.protected_symlinks = 1" | sudo tee -a /etc/sysctl.d/??-sysctl.conf

	sudo reboot
fi

Download certs from S3 using CURL
#
#
#


#Download ROOT-CA to /greengrass/certs/
sudo wget -O /greengrass/certs/root.ca.pem  http://www.symantec.com/content/en/us/enterprise/verisign/roots/VeriSign-Class%203-Public-Primary-Certification-Authority-G5.pem

# Starting greengrassd
sudo bash /greengrass/ggc/core/greengrassd start
