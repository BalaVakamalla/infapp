#!/usr/bin/python

import ssl
import paho.mqtt.client as mqtt
import json
import time
import subprocess
import shlex
import re

MQTT_PORT = 8883
MQTT_KEEPALIVE_INTERVAL = 45

MQTT_HOST = "a1qvp87d3vdcq7.iot.us-west-2.amazonaws.com"
CA_ROOT_CERT_FILE = "/greengrass/certs/root.ca.pem"
THING_CERT_FILE = "/greengrass/certs/Sandwhich.cert.pem"
THING_PRIVATE_KEY = "/greengrass/certs/Sandwhich.private.key"

# Define on_publish event function
def on_publish(client, userdata, mid):
        print ("Message Published!!")

# Initiate MQTT Client
client = mqtt.Client()
# Register publish callback function
client.on_publish = on_publish
# Configure TLS Set
client.tls_set(CA_ROOT_CERT_FILE, certfile=THING_CERT_FILE, keyfile=THING_PRIVATE_KEY, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)
# Connect with MQTT Broker
client.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE_INTERVAL)
client.loop_start()

# List of commands from boiler
cmd_list =      ["flowtemp",
                "waterpressure",
                "IonisationVoltageLevel",
                "fanspeed",
                "ExternGasvalve",
                "Statenumber",
                "ReturnTemp",
                "PumpHwcFlowSum",
                "HwcTemp",
                "HcHours",      ##Diagnostic parameters##
                "HwcHours",
                "CounterStartattempts1",
                "CounterStartattempts2",
                "currenterror"]

# Declaring list of datas to be stored and dictionary for indexing
arr_data = []
data_dict = {}
batchVal = []	# List containing all 4 second data
data = {}		# Store data for the JSON payload

# Loop to get the boiler parameters and temporarily store in a list before storing in a dictionary
rec_count = 0
while True:
	arr_data[:] = []
	for i in cmd_list:
		cmd_arr = "ebusctl r -m 10 {}".format(i)
		args =  shlex.split(cmd_arr)
		cmd_output = subprocess.Popen(args,stdout=subprocess.PIPE)
		result = cmd_output.communicate()
		temp_result = result[0]
		final_result = re.split('; |,|\:|\n|\;',temp_result)
		arr_data.append(final_result[0])

	data_dict['recutc'] = str(int(time.time()))
	data_dict['recdate'] = time.strftime("%x")
	data_dict['rectime'] = time.strftime("%X")

	# Loop to store the boiler parameters in a dictionary opposite to the parameter names
	n = 0
	for j in cmd_list:
		if j == "currenterror":
			if  arr_data[n] == '-':
				data_dict[j] = str(0)
			else:
				data_dict[j] = str('F'+arr_data[n])
		else:
			data_dict[j] = float(arr_data[n])
		n = n+1

	batchVal.append(data_dict)
	data_dict = {}
	time.sleep(4)
	rec_count += 1
	if rec_count == 75:
		data['date'] = time.strftime("%x")
		data['time'] = time.strftime("%X")
		data['data'] = batchVal
		payload = json.dumps(data)
		client.publish('batch/test', payload, qos=1)	# Send The batched data to topic "batch/test"

		# Clearing the list and dictionaries (arr_data is cleared at the start of the while loop)
		batchVal[:] = []
		data_dict.clear()
		data.clear()
		rec_count = 0
