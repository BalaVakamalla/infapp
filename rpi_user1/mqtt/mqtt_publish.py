# Import package
import sys
import ssl
import paho.mqtt.client as mqtt
import json
import time
import RPi.GPIO as GPIO
LED_PIN = 11
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(LED_PIN, GPIO.OUT) 

# Define Variables
MQTT_PORT = 8883
MQTT_KEEPALIVE_INTERVAL = 45
MQTT_TOPIC = "rpi/user1"
MQTT_MSG_ON = "SWITCHING OFF LED "
MQTT_MSG_OFF = "SWITCHING OF LED "


MQTT_HOST = "a1wwkwvws5h8go.iot.us-west-2.amazonaws.com"
CA_ROOT_CERT_FILE = "../certs/root-CA.crt"
THING_CERT_FILE = "../certs/9e70d62d62-certificate.pem.crt"
THING_PRIVATE_KEY = "../certs/9e70d62d62-private.pem.key"


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
	mqttc.publish(MQTT_TOPIC, MQTT_MSG_ON, qos=1)
	GPIO.output(LED_PIN, True)
	time.sleep(2)
	mqttc.publish(MQTT_TOPIC, MQTT_MSG_OFF, qos=1)
	GPIO.output(LED_PIN, False)	
	time.sleep(2)

# Disconnect from MQTT_Broker
# mqttc.disconnect()
