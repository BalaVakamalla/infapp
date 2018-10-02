#!/usr/bin/python

# Import package
import sys
import subprocess
import shlex
import re
import time
import sqlite3
import ssl
import paho.mqtt.client as mqtt
import json

MQTT_PORT = 8883
MQTT_KEEPALIVE_INTERVAL = 45


MQTT_HOST = "a1qvp87d3vdcq7.iot.us-west-2.amazonaws.com"
CA_ROOT_CERT_FILE = "/greengrass/certs/root.ca.pem"
THING_CERT_FILE = "/greengrass/certs/c600ad23bf.cert.pem"
THING_PRIVATE_KEY = "/greengrass/certs/c600ad23bf.private.key"

# Define on_publish event function
def on_publish(client, userdata, mid):
        print ("Message Published!!")


# Initiate MQTT Client
mqttc = mqtt.Client()
# Register publish callback function
mqttc.on_publish = on_publish
# Configure TLS Set
mqttc.tls_set(CA_ROOT_CERT_FILE, certfile=THING_CERT_FILE, keyfile=THING_PRIVATE_KEY, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)
# Connect with MQTT Broker
mqttc.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE_INTERVAL)
mqttc.loop_start()

#####################################################################
# The function calculates the total change in rate                  #
# Returns the value of total change in rate                         #
#####################################################################
def change_in_rate(param, index, noof_rcrd):

    #Table name declaration
    sqlite_db = 'boiler_data.db'    # name of the sqlite database file
    table_name = 'ebus_data'  # name of the table

    # Connect to sqlite database
    conn = sqlite3.connect(sqlite_db)
    crsr = conn.cursor()

    index_strt = index - noof_rcrd
    if index_strt==0:
        index_strt=1
    #fetching the data from the sqlite on the basis of index no
    calc_data=crsr.execute('SELECT {} FROM {tn} WHERE row_num BETWEEN {strt} AND {end}'.format(param,tn=table_name, strt=index_strt, end=index))

    count=1
    total_change_rate=0
    for i in calc_data:
        #count determines the first record and stroes the value as previous value for calculation
        if count == 1:
            count=0
            prv_val=i[0]
        else:
            crnt_val=i[0]
            #whenever the previous value is 0 then divided by 1 to avoid error
            if prv_val == 0:
                crnt_change_rate=((crnt_val-prv_val)/1)*100
            else:
                crnt_change_rate=((crnt_val-prv_val)/prv_val)*100
            total_change_rate+=crnt_change_rate
            prv_val=crnt_val

    print(total_change_rate)
    if total_change_rate > 0:
        print("Increase in {}").format(param)
    elif total_change_rate == 0:
        print("No change in Rate of {}").format(param)
    else:
        print("Decrease in {}").format(param)

    return float(total_change_rate)

#####################################################################
# The function calculates the rate of increase and peak value        #
# Returns the value whether increased or decreased                  #
#####################################################################
def change_in_inc_dcr(index, noof_rcrd):
    #Table name declaration
    sqlite_db = 'boiler_data.db'    # name of the sqlite database file
    table_name = 'ebus_data'  # name of the table

    # Connect to sqlite database
    conn = sqlite3.connect(sqlite_db)
    crsr = conn.cursor()
    index_strt = index - noof_rcrd
    if index_strt==0:
        index_strt=1
    #fetching the data from the sqlite on the basis of index no
    sql_data=crsr.execute('SELECT flow_temp,Ionisation_volt_level FROM {tn} WHERE row_num BETWEEN {strt} AND {end}'.format(tn=table_name, strt=index_strt, end=index))
    calc_data=sql_data.fetchall()
    count=1
    length=len(calc_data)
    i=0
    pi=0
    high_peak=low_peak=peak_found=low_found=0
    #finding peak - step 2
    while i < length:
        #count determines the first record and stroes the value as previous value for calculation
        if count == 1:
            count=0
            prv_val=calc_data[i][0]
        else:
            crnt_val=calc_data[i][0]
            #checking whether the next increased rate is greater than 0.5 or not and calculating the change in rate
            if crnt_val-prv_val>0.5:
                if i!=length-1:
                   # if (calc_data[i+1][0])-crnt_val>=0.1:
                   #     if calc_data[i][1] > 45:
                   if (crnt_val > high_peak):
                       high_peak=crnt_val
                       peak_found=1
                       pi=i
                       print("high peak"+str(crnt_val))
                       rate_inc=((crnt_val-prv_val)/prv_val)*100
                       print("incrate "+str(rate_inc)+"%")
            prv_val=crnt_val
        i+=1
       # print("high peak"+str(high_peak))
    #finding low when peak is there - step 3
    if(peak_found==1):
        prv_val=calc_data[pi-1][0]
        low_peak = prv_val
        while pi < length:
            crnt_val=calc_data[pi][0]
            #calculating the rate of decrease and deciding the assumed low peak
            if prv_val-crnt_val>0.5:
                if pi!=length-1:
                    if (crnt_val < low_peak):
                        low_peak=crnt_val
                        low_found=1
                        print("low peak"+str(crnt_val))
                        rate_dcr=((prv_val-crnt_val)/prv_val)*100
                        print("decrate "+str(rate_dcr)+"%")
            prv_val=crnt_val
            pi+=1

    if peak_found== 1 and low_found==1 and rate_inc>2:
        print("################################")
        print("Replace Flame rectification lead")
        payload = {}
        key = "Error"
        value = "Hi Bryn, it looks like you’re having trouble with your boiler, no problem, you’re covered by HomeServe and we are here to help! Your engineer, Chris has ordered a replacement rectification cable for your Vaillant boiler and will be in touch within the hour to book a repair visit."
        payload[key] = value
        data = json.dumps(payload)
        mqttc.publish('boiler/data', data, qos=1)
        value = str(index_strt)+", "+str(noof_rcrd)
        payload[key] = value
        data = json.dumps(payload)
        mqttc.publish('boiler/fault', data, qos=1)
    else:
        print("################################")
        print("Do you have gas supply? Check to see if your other gas appliances are working. If they are, please reply Yes to this message to book in an engineer visit")
        payload = {}
        key = "Error"
       # value = str(index_strt)+", "+str(index)+", "+"Do you have gas supply? Check to see if your other gas appliances are working. If they are, please reply Yes to this message to book in an engineer visit"
        value = "Hi Bryn, it looks like you’re having trouble with your boiler, no problem, you’re covered by HomeServe and we are here to help! Click here to troubleshoot the cause, which may be the gas supply to your property. If not, HomeServe are on hand to get you back up and running as quickly as possible. https://www.youtube.com/watch?v=JMFlU3-gEJ4"
        payload[key] = value
        data = json.dumps(payload)
        mqttc.publish('boiler/data', data, qos=1)
        value = str(index_strt)+", "+str(noof_rcrd)
        payload[key] = value
        data = json.dumps(payload)
        mqttc.publish('boiler/fault', data, qos=1)

    return 0
###################################################################################################3
#####################################################################
# The function decides whether ther is change or not                #
# Returns 1 if changed or else 0                                    #
#####################################################################
def change_in_values(param_ID, index, noof_rcrd):
    #Table name declaration
    sqlite_db = 'boiler_data.db'    # name of the sqlite database file
    table_name = 'ebus_data'  # name of the table to be created

    # Connect to sqlite database
    conn = sqlite3.connect(sqlite_db)
    crsr = conn.cursor()

    index_strt = index-noof_rcrd
    if index_strt==0:
        index_strt=1
    calc_data=crsr.execute('SELECT {} FROM {tn} WHERE row_num BETWEEN {strt} AND {end}'.format(param_ID,tn=table_name, strt=index_strt, end=index))

    count=1
    change_in_val=0
    for i in calc_data:
        if count == 1:
            count=0
            prv_val=i[0]
        else:
            crnt_val=i[0]
            #condition to check whether the value got changed in betweeen or not
            if crnt_val != prv_val and ((crnt_val-prv_val >0.1) or (prv_val-crnt_val >0.1)):
                change_in_val = 1
            prv_val=crnt_val

    if change_in_val==1:
        print("Change in values of {} happened").format(param_ID)
    else:
        print("No Change in values of {}.").format(param_ID)
    return change_in_val

###################################################################################################3
#####################################################################
# The function decides whether there is change in delta                #
# Returns delta                                    #
#####################################################################
def change_in_delta( index, noof_rcrd):
        #Table name declaration
    sqlite_db = 'boiler_data.db'    # name of the sqlite database file
    table_name = 'ebus_data'  # name of the table to be created

    # Connect to sqlite database
    conn = sqlite3.connect(sqlite_db)
    crsr = conn.cursor()
    index_strt = index - noof_rcrd
    if index_strt==0:
        index_strt=1
    #fetching hte data from the sqlite on the basis of index no
    sql_data=crsr.execute('SELECT flow_temp,fan_speed FROM {tn} WHERE row_num BETWEEN {strt} AND {end}'.format(tn=table_name, strt=index_strt, end=index))
    calc_data=sql_data.fetchall()
    count=1
    length=len(calc_data)
    i=0
    peak_found=low_found=0
    #finding peak - step 2
    while i < length:
         if ((calc_data[i][1])-(calc_data[i][0])) < 1:
             i+=1
         else:
             print("!!! difference is greater than 0.5!!!")
             break;
         return i

#####################################################################
# The function calculates the rate of increase and peak value        #
# Returns the value whether increased or decreased                  #
#####################################################################
def find_peak_low(index, noof_rcrd):
    #Table name declaration
    sqlite_db = 'boiler_data.db'    # name of the sqlite database file
    table_name = 'ebus_data'  # name of the table

    # Connect to sqlite database
    conn = sqlite3.connect(sqlite_db)
    crsr = conn.cursor()
    index_strt = index - noof_rcrd
    if index_strt==0:
        index_strt=1
    #fetching the data from the sqlite on the basis of index no
    sql_data=crsr.execute('SELECT flow_temp,Ionisation_volt_level FROM {tn} WHERE row_num BETWEEN {strt} AND {end}'.format(tn=table_name, strt=index_strt, end=index))
    calc_data=sql_data.fetchall()
    count=1
    length=len(calc_data)
    i=0
    peak_found=low_found=0
    #finding peak - step 2
    
    #######################

    high_peak=low_peak=peak_found=low_found=0
    #finding peak - step 2
    while i < length:
        #count determines the first record and stroes the value as previous value for calculation
        if count == 1:
            count=0
            prv_val=calc_data[i][0]
        else:
            crnt_val=calc_data[i][0]
            #checking whether the next increased rate is greater than 0.5 or not and calculating the change in rate
            if crnt_val-prv_val>0.1:
                if i!=length-1:
                   # if (calc_data[i+1][0])-crnt_val>=0.1:
                   #     if calc_data[i][1] > 45:
                   if (crnt_val > high_peak):
                       high_peak=crnt_val
                       peak_found=1
                       pi=i
                       print("high peak"+str(crnt_val))
                       rate_inc=((crnt_val-prv_val)/prv_val)*100
                       print("incrate "+str(rate_inc)+"%")
            prv_val=crnt_val
        i+=1
       # print("high peak"+str(high_peak))
    #finding low when peak is there - step 3
    if(peak_found==1):
        i=0
        prv_val=calc_data[i][0]
        low_peak = prv_val
        while i < length:
            crnt_val=calc_data[i][0]
            #calculating the rate of decrease and deciding the assumed low peak
            if prv_val-crnt_val>0.1:
                if i!=length-1:
                    if (crnt_val < low_peak):
                        low_peak=crnt_val
                        low_found=1
                        print("low peak"+str(crnt_val))
                        rate_dcr=((prv_val-crnt_val)/prv_val)*100
                        print("decrate "+str(rate_dcr)+"%")
            prv_val=crnt_val
            i+=1

    if peak_found== 1: #and low_found==1:# and rate_inc>5:
        print("################################")
        print("Error: Replace pressure sensor ")
        payload = {}
        key = "Error"
       # value = str(index_strt)+", "+str(index)+", "+"Replace Flame rectification lead"
        value = "Hi Bryn, it looks like you’re having trouble with your boiler, no problem, you’re covered by HomeServe and we are here to help! Your engineer, Chris has ordered a replacement F75 pressure sensor for your Vaillant boiler and will be in touch within the hour to book a repair visit. "
        payload[key] = value
        data = json.dumps(payload)
        mqttc.publish('boiler/data', data, qos=1)
    else:
        print("################################")
        print("Error: Replace pump ")
        payload = {}
        key = "Error"
       # value = str(index_strt)+", "+str(index)+", "+"Do you have gas supply? Check to see if your other gas appliances are working. If they are, please reply Yes to this message to book in an engineer visit"
        value = "Hi Bryn, it looks like you’re having trouble with your boiler, no problem, you’re covered by HomeServe and we are here to help! Your engineer, Chris has ordered a replacement pump for your Vaillant boiler and will be in touch within the hour to book a repair visit."
        payload[key] = value
        data = json.dumps(payload)
        mqttc.publish('boiler/data', data, qos=1)

    return 0
