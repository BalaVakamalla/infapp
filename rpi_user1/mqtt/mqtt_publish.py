# Import package
import sys
import ssl
import paho.mqtt.client as mqtt
import json
import time
import RPi.GPIO as GPIO
import subprocess
import shlex
import re
import time
import datetime

#List of commands
cmd_list =      ["flowtemp",
                "waterpressure",
                "IonisationVoltageLevel",
                "fanspeed",
                "currenterror"]

#Array of datas to be stored and dictionary for indexing also declared
arr_data = []
data_dict = {}


MQTT_PORT = 8883
MQTT_KEEPALIVE_INTERVAL = 45
MQTT_TOPIC1 = "boiler/data"
#MQTT_TOPIC2 = "OPENTHERM: boiler/data"
#MQTT_TOPIC3 = "EMS: boiler/data"
#MQTT_TOPIC2 = "boiler/waterpressure"
#MQTT_MSG_ON = '''{ "utctime":1111,"flowtemp": 50,"waterpressure": 1,"IonisationVolt": 86,"fanspeed": 2200   }'''


MQTT_MSG_OFF = "faultcode:F46"


#MQTT_HOST = "a1wwkwvws5h8go.iot.us-west-2.amazonaws.com"
#CA_ROOT_CERT_FILE = "../certs/root-CA.crt"
#THING_CERT_FILE = "../certs/9e70d62d62-certificate.pem.crt"
#THING_PRIVATE_KEY = "../certs/9e70d62d62-private.pem.key"

MQTT_HOST = "a1qvp87d3vdcq7.iot.us-west-2.amazonaws.com"
CA_ROOT_CERT_FILE = "../certs/root-CA.crt"
THING_CERT_FILE = "../certs/36628caa7d-certificate.pem.crt"
THING_PRIVATE_KEY = "../certs/36628caa7d-private.pem.key"

# Define on_publish event function
def on_publish(client, userdata, mid):
	print ("Message Published...")


# Initiate MQTT Client
mqttc = mqtt.Client()

# Register publish callback function
mqttc.on_publish = on_publish

# Configure TLS Set
mqttc.tls_set(CA_ROOT_CERT_FILE, certfile=THING_CERT_FILE, keyfile=THING_PRIVATE_KEY, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)

# Connect with MQTT Broker
mqttc.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE_INTERVAL)
mqttc.loop_start()

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

	cur_time = time.time()
	data_dict['deviceid'] = 'gateway01'
	data_dict['date'] = str(time.strftime('%Y-%m-%d'))
	data_dict['time'] = str(time.strftime('%H-%M-%S'))
	n = 0
	for j in cmd_list:
		if j == "currenterror":
			if  arr_data[n] == '-':
 		                data_dict[j] = str(arr_data[n])
			else:
				data_dict[j] = str('F'+arr_data[n])
		else:
        	        data_dict[j] = float(arr_data[n])
		n = n+1
	payload = json.dumps(data_dict)
#	print(data_dict)
	mqttc.publish(MQTT_TOPIC1, payload, qos=1)
#	GPIO.output(LED_PIN, True)
	time.sleep(5)
#	mqttc.publish(MQTT_TOPIC2, MQTT_MSG_OFF, qos=1)
#	GPIO.output(LED_PIN, False)	
#	time.sleep(2)

# Disconnect from MQTT_Broker
# mqttc.disconnect()
