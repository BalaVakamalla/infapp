#! /bin/bash
echo "Do you want to clear the previous data record ? y/n"
read input
if [ "$input" = "y" ] || [ "$input" = "Y" ]
then
	rm -fr boiler_data.db boiler_db_data.csv
	echo "Cleared the files."
	ls -lr
	echo "Do you want to execute the script ? y/n"
	read var
	if [ "$var" = "y" ] || [ "$var" = "Y" ]
	then
		./final_db_script.py
	else
		echo "Exiting..."
	fi
else
	clear
	./final_db_script.py
fi
