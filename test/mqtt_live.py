#!/usr/bin/python

import ssl
import paho.mqtt.client as mqtt
import json
import time
import subprocess
import shlex
import re
import os
from datetime import datetime
from threading import Timer

d=datetime.today()
#e=d.replace(day=d.day+1, hour=1, minute=0, second=0, microsecond=0)
#e=d.replace(day=d.day+1, hour=1, minute=0, second=0, microsecond=0)
#delta_t=e-d

#secs=delta_t.seconds+1
secs=3

devID=os.environ['dev_id']
send=False
live=0

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

spec_list= [["currenterror","eb1"],
            ["Statenumber","eb2"],
            ["flowtemp","eb3"],
            ["ReturnTemp","eb4"],
            ["IonisationVoltageLevel","eb5"],
            ["fanspeed","eb6"],
            ["waterpressure","eb7"],
            ["HwcWaterflow","eb8"],
            ["HwcTemp","eb9"],
            ["PositionValveSet","eb10"],
            ["Flame","eb11"],
            ["HwcDemand","eb12"],
            ["ACRoomthermostat","eb13"],
            ["DCRoomthermostat","eb14"]
                ]
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
m_cmd_list =    [["HwcHours","eb16"],
                ["HcHours","eb19"],
                ["CounterStartattempts1","eb17"],
                ["CounterStartattempts2","eb18"],
                ["averageIgnitiontime","eb21"],
                ["HwcSetPotmeter","eb22"],
                ["flowtempdesired","eb24"]]

# Declaring list of datas to be stored and dictionary for indexing
arr_data = []
data_dict = {}
batchVal = []	# List containing all 4 second data
data = {}		# Store data for the JSON payload

def maint_data():
    arr_data[:] = []
    data_dict.clear()
    data_dict['recutc'] = int(time.time())
    data_dict['type']="maint"
    data_dict['deviceid']=devID
    data_dict['bus']="ebus2.1"
    for i in m_cmd_list:
        cmd_arr = "ebusctl r -m 10 {}".format(i[0])
        args =  shlex.split(cmd_arr)
        cmd_output = subprocess.Popen(args,stdout=subprocess.PIPE)
        result = cmd_output.communicate()
        temp_result = result[0]
        #print "temp_result="+str(temp_result)
        final_result = re.split('; |,|\:|\n|\;',temp_result)
        #print "final_result="+str(final_result)
        arr_data.append(final_result[0])
        #print "arr_data="+str(arr_data)
        # Loop to store the boiler parameters in a dictionary opposite to the parameter names
        n = 0
    for j in m_cmd_list:
        if arr_data[n] == '-':
            arr_data[n] = str(0)
        if arr_data[n] == 'ERR':
            arr_data[n] = -1
        data_dict[j[1]] = float(arr_data[n])
        n = n+1
    payload = json.dumps(data_dict)
    client.publish('test/maintData', payload, qos=1) #send maintanence data
    print("Maintanance data sent")
    print str(payload)
    data_dict.clear()

rec_count = 0
while True:
	arr_data[:] = []
	for i in spec_list:
		cmd_arr = "ebusctl r -m 10 {}".format(i[0])
		args =  shlex.split(cmd_arr)
		cmd_output = subprocess.Popen(args,stdout=subprocess.PIPE)
		result = cmd_output.communicate()
		temp_result = result[0]
		final_result = re.split('; |,|\:|\n|\;',temp_result)
		arr_data.append(final_result[0])

	#data_dict['timestamp'] = int(time.time())
	data_dict['recutc'] = int(time.time())
        #data_dict['recdate'] = time.strftime("%x")
	#data_dict['rectime'] = time.strftime("%X")
        #data_dict['devID'] = devID

	# Loop to store the boiler parameters in a dictionary opposite to the parameter names
	n = 0
	for j in spec_list:
		if j[0] == "currenterror":
			if  arr_data[n] == '-':
				data_dict[j[1]] = int(0)
                                live = 0
			else:
				data_dict[j[1]] = str(arr_data[n])
                                live = live+1
		else:
                        if arr_data[n] == 'on' or arr_data[n] == 'yes':
                            arr_data[n] = 1
                        if arr_data[n] == 'off' or arr_data[n] == 'no':
                            arr_data[n] = 0
                        if arr_data[n] == '-':
                            arr_data[n]=0
		        if arr_data[n] == 'ERR':
                            arr_data[n] = -1
                        data_dict[j[1]] = float(arr_data[n])
		n = n+1

	batchVal.append(data_dict)
        print str(data_dict)
	time.sleep(4)
	rec_count += 1

	# Send live data into "'testout/'+devID" on demand triggered on
	# message with devID same as the devicedID in "'testout/'+devID"
	if send :
		if (time.time() - clkStart) < 300:
                        data['type']="dataLive"
                        data['deviceid']=devID
                        data['bus']="ebus2.1"
			data['data'] = data_dict
                        live_payload = json.dumps(data)
			client.publish('test/batchlive', live_payload, qos=1)
			print("Sending live data!!")
		else:
			send = False
			clkStart = 0
	data_dict = {} # Flush dictionary before storing the next set of 4 sec data

	# Batch the 4 second data to 5 minute intervals
	if rec_count == 3 or live == 1:
                data.clear()
		#data['date'] = time.strftime("%x")
		#data['time'] = time.strftime("%X")
		data['type']="data"
        data['deviceid']=devID
        data['bus']="ebus2.1"
        data['data'] = batchVal
		payload = json.dumps(data)
		client.publish('test/batchData', payload, qos=1)	# Send The batched data to topic "batch/test"
		print("Sending Batch data!!")

		# Clearing the list and dictionaries (arr_data is cleared at the start of the while loop)
		batchVal[:] = []
		data_dict.clear()
		data.clear()
		rec_count = 0
                maint_data()

            #Maintenance data start


#t = Timer(secs, maint_data)
#t.start()
