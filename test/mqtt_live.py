#!/usr/bin/python

import ssl
import paho.mqtt.client as mqtt
import json
import time
import subprocess
import shlex
import re
import os

devID=os.environ['dev_id']
send=False

MQTT_PORT = 8883
MQTT_KEEPALIVE_INTERVAL = 45

MQTT_HOST = "a1qvp87d3vdcq7.iot.us-west-2.amazonaws.com"
CA_ROOT_CERT_FILE = "/"+ devID +"/certs/root.ca.pem"
THING_CERT_FILE = "/"+ devID +"/certs/"+ devID +".cert.pem"
THING_PRIVATE_KEY = "/"+ devID +"/certs/"+ devID +".private.key"

# Define on_connect event function
def on_connect(client, userdata, flags, rc):
	print("Connection returned result: " + str(rc) )

# Define on_publish event function
def on_publish(client, userdata, mid):
	print ("Message Published!!")

# Define on_message event function
def on_message(client, userdata, msg):
    print("topic: "+msg.topic)
    print("payload: "+str(msg.payload))
    data = json.loads(str(msg.payload))
    global send, clkStart
    if data['devID'] == devID:
		print("Device ID Match!!")
		send = True
		clkStart = time.time()
    else:
		send = False

# Initiate MQTT Client
client = mqtt.Client()

# Register callback functions
client.on_connect = on_connect
client.on_message = on_message
client.on_publish = on_publish

# Configure TLS Set
client.tls_set(CA_ROOT_CERT_FILE, certfile=THING_CERT_FILE, keyfile=THING_PRIVATE_KEY, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)

# Connect with MQTT Broker
client.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE_INTERVAL)
client.subscribe('testin/'+devID , 1 )
client.loop_start()
time.sleep(2)

# List of commands from boiler
cmd_list =     	["flowtemp",
                "waterpressure",
                "IonisationVoltageLevel",
                "fanspeed",
                "Statenumber",
                "ReturnTemp",
                "PumpHwcFlowSum",
                "HwcWaterflow",
                "HwcTemp",   
                "PositionValveSet",
                "HwcTempDesired",
                "flame",
                "currenterror",
                "ACRoomthermostat",
                "DCRoomthermostat"]

# List of maintanence data from boiler
m_cmd_list =    ["HwcHours",
                "HcHours",
                "CounterStartattempts1",
                "CounterStartattempts2",
                "averageIgnitiontime",
                "HwcSetPotmeter",
                "flowtempdesired"]

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

	data_dict['recutc'] = int(time.time())
	data_dict['recdate'] = time.strftime("%x")
	data_dict['rectime'] = time.strftime("%X")
        data_dict['devID'] = devID

	# Loop to store the boiler parameters in a dictionary opposite to the parameter names
	n = 0
	for j in cmd_list:
		if j == "currenterror":
			if  arr_data[n] == '-':
				data_dict[j] = str(0)
			else:
				data_dict[j] = str('F'+arr_data[n])
		else:
                        if arr_data[n] == 'on':
                            arr_data[n] = 1
                        if arr_data[n] == 'off':
                            arr_data[n] = 0
			data_dict[j] = float(arr_data[n])
		n = n+1

	batchVal.append(data_dict)
        print str(data_dict)
	time.sleep(4)
	rec_count += 1

	# Send live data into "'testout/'+devID" on demand triggered on
	# message with devID same as the devicedID in "'testout/'+devID"
	if send :
		if (time.time() - clkStart) < 300:
			live_payload = json.dumps(data_dict)
			client.publish('batch/testlive', live_payload, qos=1)
			print("Sending live data!!")
		else:
			send = False
			clkStart = 0
	data_dict = {} # Flush dictionary before storing the next set of 4 sec data

	# Batch the 4 second data to 5 minute intervals
	if rec_count == 75:
		data['date'] = time.strftime("%x")
		data['time'] = time.strftime("%X")
		data['data'] = batchVal
		payload = json.dumps(data)
		client.publish('test/batchData', payload, qos=1)	# Send The batched data to topic "batch/test"
		print("Sending Batch data!!")

		# Clearing the list and dictionaries (arr_data is cleared at the start of the while loop)
		batchVal[:] = []
		data_dict.clear()
		data.clear()
		rec_count = 0
            #
            #Maintenance data start
                arr_data[:] = []
                for i in m_cmd_list:
                    cmd_arr = "ebusctl r -m 10 {}".format(i)
                    args =  shlex.split(cmd_arr)
                    cmd_output = subprocess.Popen(args,stdout=subprocess.PIPE)
                    result = cmd_output.communicate()
                    temp_result = result[0]
                    final_result = re.split('; |,|\:|\n|\;',temp_result)
                    arr_data.append(final_result[0])
                data_dict['utc'] = int(time.time())
                #data_dict['recdate'] = time.strftime("%x")
                #data_dict['rectime'] = time.strftime("%X")
                data_dict['devID'] = devID

                # Loop to store the boiler parameters in a dictionary opposite to the parameter names
                n = 0
                for j in m_cmd_list:
                    data_dict[j] = float(arr_data[n])
                    n = n+1
                payload = json.dumps(data_dict)
                client.publish('test/maintData', payload, qos=1) #send maintanence data
                print("Maintanance data sent")
                print str(payload)



