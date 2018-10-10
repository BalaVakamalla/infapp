#!/usr/bin/python

# Import package
import sys
import subprocess
import shlex
import re
import time
import sqlite3
import os
import signal
# import data_analysis
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


cmd_list =      ["flowtemp",
                "waterpressure",
                "IonisationVoltageLevel",
                "ReturnTemp",
                "ExternGasvalve",
                "currenterror"]

#Array of datas to be stored and dictionary for indexing also declared
arr_data = []


#File created and opened in appendmode
fo = open("boiler_db_data.csv", "a+")

#Table name declaration
sqlite_db = 'boiler_data.db'    # name of the sqlite database file
table_name = 'ebus_data'  # name of the table to be created

# Connect to sqlite database
conn = sqlite3.connect(sqlite_db)
crsr = conn.cursor()

# Create Table if table doesn't exist
crsr.execute('CREATE TABLE IF NOT EXISTS {tn} (row_num BIGINT, epochtime BIGINT, date char(10), time char(10), flow_temp FLOAT, water_press FLOAT, Ionisation_volt_level FLOAT, fan_speed FLOAT, gas_valve FLOAT, fault_code varchar(20) )'.format(tn=table_name))

#row index
row_index=0
noof_entries=32
flag = 0

while True:
        # Re-Connect to sqlite database
        conn.close()
        conn = sqlite3.connect(sqlite_db)
        crsr = conn.cursor()
        fo = open("boiler_db_data.csv", "a+")
        #Insert rows into the table
        crsr.execute("SELECT strftime('%s', 'now')")
        #time storage
        ep_tm=crsr.fetchone()[0]
        date_str = time.strftime("%x")
        time_str = time.strftime("%X")
        arr_data[:] = []
        for i in cmd_list:
                cmd_arr = "ebusctl r -m 10 {}".format(i)
                args =  shlex.split(cmd_arr)
                cmd_output = subprocess.Popen(args,stdout=subprocess.PIPE)
                result = cmd_output.communicate()
                temp_result = result[0]
                final_result = re.split(b'; |,|\:|\n|\;',temp_result)
                if i =="currenterror":
                    if final_result[0] == "-":
                       arr_data.append(0)
                    else:
                        arr_data.append(final_result[0])
                elif final_result[0]=='ERR':
                    print("Connection lost.")
                    break
                else:
                    arr_data.append(float(final_result[0]))
        if final_result[0]=='ERR':
            continue
        row_index+=1

        crsr.execute("INSERT INTO {} (row_num, epochtime, date, time, flow_temp, water_press, Ionisation_volt_level, fan_speed, gas_valve, fault_code) VALUES ({}, {}, '{}', '{}', {}, {}, {}, {}, {}, {})".format(table_name, row_index, ep_tm, date_str, time_str, arr_data[0], arr_data[1], arr_data[2],  arr_data[3], arr_data[4], arr_data[5]))

        conn.commit()

        if row_index > noof_entries:
            if ((arr_data[-1] == '28')or(arr_data[-1] == '29')) and  (arr_data[2] > 45):
                #call lambda function
                #calling local function
                if flag == 0:
                    data_analysis.change_in_inc_dcr(row_index, noof_entries)
                flag = 1
            elif arr_data[-1] == '75':
                #call lambda for analysis
                #print(final_result[0])
                if flag == 0:
                    flowtemp_changed=data_analysis.change_in_values("flow_temp", row_index, noof_entries)
                    waterpress_changed=data_analysis.change_in_values("water_press", row_index, noof_entries)
                    rateof_change=float(data_analysis.change_in_rate("flow_temp", row_index, noof_entries))
                    records = data_analysis.change_in_delta (row_index, 9)
                    #(flowtemp_changed != 1)
                    #if ((rateof_change > 0 and (rateof_change < float(0.1))) or (rateof_change >= 10)): # and (waterpress_changed != 1):
                    if (records >= 31):
                        print("#########################")
                        print("Replace pump")
                    elif (flowtemp_changed == 1): # and (waterpress_changed != 1):
                        print("#########################")
                        print("Replace pressure sensor")
                    else:
                        print("!!!!!!! Failed to detect Algorithm !!!!!!!!")
                    flag = 1
            elif arr_data[-1] == 0:
                flag = 0


        #Create a string and Append data to file
        data_str = str(row_index)+', '+ep_tm+', '+date_str+', '+time_str+', '
        i = 0
        length = len(arr_data)
        while i < length:
            if i != length-1:
                data_str = data_str+str(arr_data[i])+', '
            else:
               data_str = data_str+str(arr_data[i])+'\n'
            i+=1
        #Print the whole data packet
        print(data_str)
        
        print("Replace Flame rectification lead")
        payload = {}
        key = "Error"
       # value = str(index_strt)+", "+str(index)+", "+"Replace Flame rectification lead"
        value = "Replace Flame rectification lead"
        payload[key] = value
        data = json.dumps(payload)
        mqttc.publish('boiler/data', data, qos=1)

        fo.write(data_str)
        fo.close()
        time.sleep(10)
