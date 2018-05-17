# Import package
import sys
import ssl
import paho.mqtt.client as mqtt
import json
import time
import RPi.GPIO as GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.IN) 

# Define Variables
MQTT_PORT = 8883
MQTT_KEEPALIVE_INTERVAL = 45
MQTT_TOPIC = "rpiTopic"
MQTT_MSG = "Intruder detected "

MQTT_HOST = "a1wwkwvws5h8go.iot.us-west-2.amazonaws.com"
CA_ROOT_CERT_FILE = "../certs/root-CA.crt"
THING_CERT_FILE = "../certs/db3038efd5-certificate.pem.crt"
THING_PRIVATE_KEY = "../certs/db3038efd5-private.pem.key"


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

counter = 0
det = 0
num = 0
while True:
	det=GPIO.input(11)
	if det==0:                 #When output from motion sensor is LOW
		print "No intruders"
		counter = 0
		time.sleep(0.5)
	elif det==1:               #When output from motion sensor is HIGH
		print "Intruder detected"
		counter += 1
		time.sleep(0.5)
		if counter >= 5:
			counter = 0
			num += 1
			mqttc.publish(MQTT_TOPIC,MQTT_MSG + str(num)+" times",qos=1)

# Disconnect from MQTT_Broker
# mqttc.disconnect()
