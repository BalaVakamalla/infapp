#!/usr/bin/python

# Import package
import sys
import shlex
import subprocess
import re
import time

cmd_list =      ["flowtemp",
                "waterpressure",
                "IonisationVoltageLevel",
                "fanspeed",
                "ExternGasvalve",
                "Statenumber",
                "ReturnTemp",
                "PumpHwcFlowSum",
                "HwcTemp",
                "HcHours",      ##Diagnostic parameters##
                "HwcHours",
                "CounterStartattempts1",
                "CounterStartattempts2",
                "currenterror"]

#Array of datas to be stored and dictionary for indexing also declared
arr_data = []

while True:
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
        #Print the whole data packet
        j=0
        print("###########################################################################################")
        for i in cmd_list:
            print(i+': '+str(arr_data[j]))
            j+=1
        print("###########################################################################################")
        time.sleep(4)

