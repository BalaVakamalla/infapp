#!/usr/bin/python3

# Import package
import sys
import subprocess
import shlex
import re
import time
import sqlite3
import os
import signal
import paho.mqtt.client as mqtt
import ssl
import json


MQTT_PORT = 8883
MQTT_KEEPALIVE_INTERVAL = 45
MQTT_TOPIC1 = "diag/dev"

MQTT_HOST = "a1qvp87d3vdcq7.iot.us-west-2.amazonaws.com"
CA_ROOT_CERT_FILE = "/greengrass/certs/root.ca.pem"
THING_CERT_FILE = "/greengrass/certs/bf66a988ff.cert.pem"
THING_PRIVATE_KEY = "/greengrass/certs/bf66a988ff.private.key"

# Initiate MQTT Client
mqttc = mqtt.Client()

# Configure TLS Set
mqttc.tls_set(CA_ROOT_CERT_FILE, certfile=THING_CERT_FILE, keyfile=THING_PRIVATE_KEY, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)

# Connect with MQTT Broker
mqttc.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE_INTERVAL)
mqttc.loop_start()

#parameter accepts the recent value
def change_in_rate(param, epoch, noof_rcrd):
    epoch_start= epoch - (noof_rcrd*5)
    calc_data=crsr.execute('SELECT {} FROM {tn} WHERE epochtime BETWEEN {strt} AND {end}'.format(param,tn=table_name, strt=epoch_start, end=epoch))
    count=1
    index=0
    for i in calc_data:
        if count == 1:
            count=0
            prv_val=i[index]
            index+=1
        else:
            crnt_val=i[index]
            index+=1
            crnt_change_rate=((crnt_val-prv_val)/prv_val)*100
            total_change_rate+=crnt_change
            prv_val=crnt_val

    return total_cahnge_rate

def change_in_values(param_ID, epoch, noof_rcrd):
    epoch_start=epoch -(noof_rcrd*5)
    calc_data=crsr.execute('SELECT {} FROM {tn} WHERE epochtime BETWEEN {strt} AND {end}'.format(param_ID,tn=table_name, strt=epoch_start, end=epoch))
    count=1
    index=0
    change_in_val=0
    for i in calc_data:
        if count == 1:
            count=0
            prv_val=i[index]
            index+=1
        else:
            crnt_val=i[index]
            index+=1
            if crnt_val != prv_val:
                change_in_val = 1
            prv_val=crnt_val
    return change_in_val

def Data_Analysis():

    if arr_data[2] > 40:
        ch_IV = 1
    else:
        ch_IV = 0

    if arr_data[4]==230:        ##closed condition of gas valve
        GV_open=0
    else:
        GV_open=1

    # Connect to sqlite database
    conn = sqlite3.connect(sqlite_db)
    crsr = conn.cursor()
    crsr.execute('SELECT epochtime from {tn} WHERE fault_code=28'.format(tn=table_name))
    epoch=crsr.fetchone()[0]

    flow_temp_rate=change_in_rate("flow_temp", epoch, 30)
    if flow_temp_rate < 0:
        print("Flowtemp Decreased")
        Inc_flowtemp=0
    elif fow_temp_rate == 0:
        print("No increase in flowtemp")
        Inc_flowtemp=2
    else:
        print("Flowtemp Increased")
        Inc_flowtemp=1

    fan_speed_rate=change_in_rate("fan_speed", epoch, 30)
    if fan_speed_rate < 0:
        print("Decreased")
        Inc_fanspeed=0
    elif fan_speed_rate==0:
        print("No increase in fanspeed")
        Inc_fanspeed=2
    else:
        print("Increased")
        Inc_fanspeed=1

    value_changed_IV=change_in_values("Ionisation_volt_level", epoch, 30)
    if value_changed_IV==1:
        print("Changed in Values of Ionisation voltage")
        Ch_val_IV=1
    else:
        print("No change in Ionisation level")
        Ch_val_IV=0

    value_changed_GV=change_in_values("Ionisation_volt_level", epoch, 30)
    if value_changed_GV==1:
        print("Changed in Values of Gas Valve")
        Ch_val_GV=1
    else:
        print("No change in Gas Valve")
        Ch_val_GV=0

    ########Data Analysis Condition###########
    ##########################################
    if ch_IV==1 and Inc_fanspeed==1 and Inc_flowtemp==2 and Ch_val_GV==1:
        print("Gas Supply")
        payload = json.dumps("Gas supply Issue")
        mqttc.publish(MQTT_TOPIC1, payload, qos=1)

    if ch_IV==1 and Inc_fanspeed==1 and Inc_flowtemp==2 and GV_open==0:
        print("Gas valve")
        payload = json.dumps("Gas valve Issue")
        mqttc.publish(MQTT_TOPIC1, payload, qos=1)

    if ch_IV==1 and Ch_val_IV==0 and Inc_fanspeed==1 and flow_temp_rate>0.5 and GV_open==1:
        print("Flame rectification")
        payload = json.dumps("Flame rectification Issue")
        mqttc.publish(MQTT_TOPIC1, payload, qos=1)


    #########killing the process ############3
    os.kill(pid, signal.SIGKILL)



cmd_list =      ["flowtemp",
                "waterpressure",
                "IonisationVoltageLevel",
                "fanspeed",
                "gasvalve" ###check the command if error comes
                "currenterror"]



#Table name declaration
sqlite_db = 'boiler_data.db'    # name of the sqlite database file
table_name = 'ebus_data'  # name of the table to be created

# Connect to sqlite database
conn = sqlite3.connect(sqlite_db)
crsr = conn.cursor()
# Create Table if table doesn't exist
crsr.execute('CREATE TABLE IF NOT EXISTS {tn} (epochtime BIGINT, date char(10), time char(8), flow_temp FLOAT, water_press FLOAT, Ionisation_volt_level FLOAT, fan_speed FLOAT, gas_valve FLOAT, fault_code char(4) )'.format(tn=table_name))

#Array of datas to be stored and dictionary for indexing also declared
arr_data = []
#data_dict = {}

#File created and opened in appendmode
fo = open("boiler_db_data.csv", "a+")

while True:
        # Re-Connect to sqlite database
        conn.close()
        conn = sqlite3.connect(sqlite_db)
        crsr = conn.cursor()
        fo = open("boiler_db_data.txt", "a+")
        arr_data[:] = []
        for i in cmd_list:
                cmd_arr = "ebusctl r -m 10 {}".format(i)
                args =  shlex.split(cmd_arr)
                cmd_output = subprocess.Popen(args,stdout=subprocess.PIPE)
                result = cmd_output.communicate()
                temp_result = result[0]
                final_result = re.split(b'; |,|\:|\n|\;',temp_result)
                if i == 'currenterror':
                    if final_result == '-':
                        arr_data.append('NULL')
                    elif int(final_result)==28:
                        arr_data.append(str('F'+final_result[0]))
                    else:
                        arr_data.append(str(final_result[0]))
                else:
                    arr_data.append(float(final_result[0]))
        print(arr_data)
        #Insert rows into the table
        crsr.execute("INSERT INTO {} (epochtime, date, time, flow_temp, water_press, Ionisation_volt_level, fan_speed, gas_valve, fault_code) VALUES (strftime('%s', 'now'), date('now','localtime'), time('now','localtime'), {}, {}, {}, {}, {}, {})".format(table_name, arr_data[0], arr_data[1], arr_data[2],  arr_data[3], arr_data[4], arr_data[5]))
        conn.commit()
        #data analysis part
        if arr_data[5] == 'F28':
            try:
                 pid = os.fork()
            except OSError:
                exit("Could not create a child process")
            if pid == 0:
                Data_Analysis()

        #Create a string and Append data to file
        date_str = time.strftime("%x")
        time_str = time.strftime("%X")
        data_str = date_str+', '+time_str+', '
        i = 0
        length = len(arr_data)
        while i < length:
            if i != length-1:
                data_str = data_str+str(arr_data[i])+', '
            else:
               data_str = data_str+str(arr_data[i])+'\n'
            i+=1

        fo.write(data_str)
        fo.close()
        time.sleep(5)

