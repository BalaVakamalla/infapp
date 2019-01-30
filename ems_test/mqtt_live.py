#!/usr/bin/python

import ssl
import paho.mqtt.client as mqtt
import json
import time
import subprocess
import shlex
import re
import os
import serial
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
fault=0
prvfault=0

MQTT_PORT = 8883
MQTT_KEEPALIVE_INTERVAL = 45
BATCH_TOTAL=66
FREQ=4
BUSTYPE="EMS1.0"

MQTT_HOST = "a1qvp87d3vdcq7-ats.iot.us-west-2.amazonaws.com"
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
client.subscribe('test/d194568452418e3bc1de5b0f913def8b100586068eb84a4a8a10ec2e3b430e98', 1 )
client.loop_start()
time.sleep(2)

ser = serialport = serial.Serial("/dev/ttyACM0", 9600, timeout=1)
# List of commands from boiler
cmd_list =      ['errorcode1',
                'statuscode',
                'Flowtemp',
                'outsideTemp',
                'Flamecurrent',
                'systempressure',
                'errorcode2',
		'returntemp',
                'dhwflowrate',
                'curburnerpow',
                'dhwtemp',
                'selflowtemp',
                'selburnerpow',
                'curboilerperfm'
                ]

ems_json =      {"errorcode1":"em2",
                "statuscode":"em1",
                "errorcode2":"em3",
                "outsideTemp":"em5",
                "systempressure":"em7",
                "Flowtemp":"em4",
                "Flamecurrent":"em6",
                "emsflags":"em8",
                "curburnerpow":"em9",
                "dhwtemp":"em10",
                "returntemp":"em5",
		"dhwflowrate":"em14",
                "selflowtemp":"em12",
                "selburnerpow":"em13",
                "curboilerperfm":"em15"
                }
prv_val  = ["fr"]*15

# Declaring list of datas to be stored and dictionary for indexing
arr_data = [len(cmd_list)] * 0
data_dict = {}
batchVal = []   # List containing all 4 second data
data = {}       # Store data for the JSON payload

# Loop to get the boiler parameters and temporarily store in a list before storing in a dictionary
rec_count = 0
curtime = int (time.time())
nexttime = curtime + FREQ 
for x in cmd_list:
    data_dict[ems_json[x]] = "fr"
while True:

        if (ser.isOpen == False):
            ser.open()
        response = serialport.readlines()
        #response = str(response)
        response = [i.replace("\r\n","") for i in response]
        print response

        #for y in response:
        for x in cmd_list:
            xx = x+":.*"
            data_dict[ems_json[x]] = prv_val[cmd_list.index(x)]
            #data_dict[ems_json[x]] = "fr"
            for i in response:
                ss=re.search(xx,i,flags=0)
                if (ss):
                    val=ss.group(0)
                    #print val
                    final_result = re.split(':',val)

                    #data_dict['recutc'] = int(time.time())
                    #arr_data[y] = float(final_result[1])
                    if ((final_result[0] == "errorcode1" or final_result[0] == "errorcode2") and final_result[1] > 0):
                        if (final_result[1] != fault):
                            fault = final_result[1]
                    prv_val[cmd_list.index(x)] = final_result[1]  
                    data_dict[ems_json[x]] = (final_result[1])
                    

        #for j,i in enumerate(cmd_list):
            #print data_dict[i
            #print j
            #data_dict[i] = float(arr_data[j])
            #print i

        #batchVal.append(data_dict)
        curtime = int(time.time())

        if (curtime > nexttime):
            data_dict['timestamp'] = str(curtime)
            nexttime = (curtime + FREQ)
            print data_dict
            rec_count += 1
            batchVal.append(data_dict)

        # Send live data into "'testout/'+devID" on demand triggered on
        # message with devID same as the devicedID in "'testout/'+devID"
        if send :
                if (time.time() - clkStart) < 300:
                    data['type']="dataLive"
                    data['deviceid']=devID
                    data['bus']=BUSTYPE
                    data['data']=data_dict
                    live_payload = json.dumps(data)
                    client.publish('test/liveData', live_payload, qos=1)
                    print("Sending live data!!")
                else:
                    send = False
                    clkStart = 0
        data_dict = {} # Flush dictionary before storing the next set of 4 sec data

        # Batch the 4 second data to 5 minute intervals
        if rec_count == BATCH_TOTAL:
            data['type']="data"
            data['deviceid']=devID
            data['bus']=BUSTYPE
            data['data'] = batchVal
            payload = json.dumps(data)
            client.publish('test/batchData', payload, qos=1)        # Send The batched data to topic "batch/test"
            print("Sending Batch data!!")
            # Clearing the list and dictionaries (arr_data is cleared at the start of the while loop)
            batchVal[:] = []
            data_dict.clear()
            data.clear()
            rec_count = 0

        if fault != prvfault:
            data.clear()
            data['type']="faultData"
            data['deviceid']=devID
            data['bus']=BUSTYPE
            data['data'] = batchVal
            payload = json.dumps(data)
            client.publish('test/faultData', payload, qos=1)
            print ("Sent fault Data !!")
            print payload
            prvfault = fault
