import requests, datetime, sys
from aws_sig_ver_4 import get_HTTP_Request_Header
import RPi.GPIO as GPIO
import time

LED_PIN = 11
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(LED_PIN, GPIO.OUT) 

# ==================================================================
ACCESS_KEY = "AKIAIJYZ75IC53FGUCDA" # Create one from AWS IAM Module 
SECRET_KEY = "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" # Create one from AWS IAM Module
IOT_ENDPOINT = "a1wwkwvws5h8go.iot.us-west-2.amazonaws.com" # From AWS IoT Dashboard, go to "settings" to find your IoT Endpoint
AWS_REGION = "us-west-2" # Your AWS Region. Full list at - http://docs.aws.amazon.com/general/latest/gr/rande.html#iot_region
HTTPS_ENDPOINT_URL = "https://a1wwkwvws5h8go.iot.us-west-2.amazonaws.com" # Prefix your AWS IoT Endpoint with "https://" 
IoT_THING_NAME = "rpi_user1" # Put your AWS IoT Thing name here.

# ==================================================================
HTTPS_METHOD ="POST"
SHADOW_URI = "/things/" + IoT_THING_NAME + "/shadow" # Standard URL
HTTPS_REQUEST_PAYLOAD = ""

# ==================================================================
level = int(input("Enter 0 to SWITCH OFF LED or 1 to SWITCH ON "))

if (level == 0): 
	GPIO.output(LED_PIN, False)
	HTTPS_REQUEST_PAYLOAD = """{"state" : {	"reported" : {"ID": "USER1", "COLOR" : "GREEN", "STATE" : "OFF"}}}"""
elif (level == 1):
	GPIO.output(LED_PIN, True)
	HTTPS_REQUEST_PAYLOAD = """{"state" : {"reported" : {"ID": "USER1", "COLOR" : "GREEN", "STATE" : "ON"}}}"""


# Construct URL for Post Request 
Request_Url = HTTPS_ENDPOINT_URL + SHADOW_URI

# Get HTTP Headers with AWS Signature 4 Signed Authorization Header
Request_Headers = get_HTTP_Request_Header(HTTPS_METHOD, IOT_ENDPOINT, AWS_REGION, SHADOW_URI, ACCESS_KEY, SECRET_KEY, HTTPS_REQUEST_PAYLOAD)

# Make HTTPS Request
HTTP_RESPONSE = requests.request(HTTPS_METHOD, Request_Url, data=HTTPS_REQUEST_PAYLOAD ,headers=Request_Headers)

# Print Response 
print ("\nHTTP Response Code:" + str(HTTP_RESPONSE.status_code))
print ("Response:")
print (HTTP_RESPONSE.text)
# ==================================================================
