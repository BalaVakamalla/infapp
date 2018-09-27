/*
OpenTherm Communication Example Code
By: Ihor Melnyk
Date: January 19th, 2018

Uses the OpenTherm library to get/set boiler status and water temperature
Open serial monitor at 115200 baud to see output.

Hardware Connections (OpenTherm Adapter (http://ihormelnyk.com/pages/OpenTherm) to Arduino/ESP8266):
-OT1/OT2 = Boiler X1/X2
-VCC = 5V or 3.3V
-GND = GND
-IN  = Arduino (3) / ESP8266 (5) Output Pin
-OUT = Arduino (2) / ESP8266 (4) Input Pin

Controller(Arduino/ESP8266) input pin should support interrupts.
Arduino digital pins usable for interrupts: Uno, Nano, Mini: 2,3; Mega: 2, 3, 18, 19, 20, 21
ESP8266: Interrupts may be attached to any GPIO pin except GPIO16,
but since GPIO6-GPIO11 are typically used to interface with the flash memory ICs on most esp8266 modules, applying interrupts to these pins are likely to cause problems
*/


#include <Arduino.h> 
#include "OpenTherm.h"

const int inPin = 2; //4
const int outPin = 3; //5
OpenTherm ot(inPin, outPin);

void handleInterrupt() {
	ot.handleInterrupt();
}

void setup()
{
	Serial.begin(115200);
	Serial.println("Start");
	
	ot.begin(handleInterrupt);
}

void loop()
{	
	//Set/Get Boiler Status
	bool enableCentralHeating = true;
	bool enableHotWater = true;
	bool enableCooling = false;
	unsigned long response = ot.setBoilerStatus(enableCentralHeating, enableHotWater, enableCooling);
	OpenThermResponseStatus responseStatus = ot.getLastResponseStatus();
	if (responseStatus == OpenThermResponseStatus::SUCCESS) {		
		Serial.println("Central Heating: " + String(ot.isCentralHeatingEnabled(response) ? "on" : "off"));
		Serial.println("Hot Water: " + String(ot.isHotWaterEnabled(response) ? "on" : "off"));
		Serial.println("Flame: " + String(ot.isFlameOn(response) ? "on" : "off"));
    Serial.println("Fault: " + String(ot.isFault(response) ? "Yes" : "No"));
	}
	if (responseStatus == OpenThermResponseStatus::NONE) {
		Serial.println("Error: OpenTherm is not initialized");
	}
	else if (responseStatus == OpenThermResponseStatus::INVALID) {
		Serial.println("Error: Invalid response " + String(response, HEX));
	}
	else if (responseStatus == OpenThermResponseStatus::TIMEOUT) {
		Serial.println("Error: Response timeout");
	}
 

	//Set Boiler Temperature to 64 degrees C
//	ot.setBoilerTemperature(64);

	//Get Boiler Temperature
	float temperature = ot.getBoilerTemperature();
	Serial.print("DHW temperature is ");	
  Serial.println(temperature,DEC);

  float returnTemp = ot.getReturnTemp();
  Serial.print("return temp "); 
  Serial.println(returnTemp,DEC);

  float flowRate = ot.getFlowRate();
  Serial.print("flowrate "); 
  Serial.println(flowRate,DEC);

  /*CH Water pressure*/
  float CH_waterpress = ot.getCHwaterpressure();
  Serial.print("CH Water pressure "); 
  Serial.println(CH_waterpress,DEC);

  /*Boiler flow temperature*/
  float Boilerflow_Temp = ot.getBoilerflowTemp();
  Serial.print("Boiler flow temperature "); 
  Serial.println(Boilerflow_Temp,DEC);

  /*Relative modulation level*/
  float Modulation_Level = ot.getModulationLevel();
  Serial.print("Relative modulation level "); 
  Serial.println(Modulation_Level,DEC);

  /*Boiler exhaust temperature*/
  float Exhaust_Temp = ot.getExhaustTemp();
  Serial.print("Boiler exhaust temperature "); 
  Serial.println(Exhaust_Temp,DEC);
  
  unsigned int diagcode = ot.getdiagcode();
  Serial.print("OEMdiagnosticcode is "); 
  switch (diagcode)
  {
    case 1:
    Serial.println("F4 Flow thermistor");
    break;
    case 3:
    Serial.println("F5 Return thermistor fault");
    break;
    case 9:
    Serial.println("F6 Outside sensor Failure");
    break;
    case 33:
    Serial.println("FA Flow thermistor out of range");
    break;
    case 38:
    Serial.println("FU Pulled pump electric connection");
    break;
    case 51:
    Serial.println("F1 Low water pressure");
    break;
    case 53:
    Serial.println("F2 Flame Loss");
    break;
    case 58:
    Serial.println("L2 ignition fault");
    break;
    case 60:
    Serial.println("F3 fan fault");
    break;
    default:
    Serial.println(diagcode,DEC);
    break;
  }
  /*****************Application specific fault flags********************/
  unsigned int App_fault = ot.getAppFault();
  Serial.print("Application specific fault is:\n"); 
  /*Service flag*/
  if (App_fault & 1)
  {
    Serial.print("Service Required\n");
  }
  else
  {
    Serial.print("Service Not Required\n");
  }
  /*lockout reset*/
  if ((App_fault>>1) & 1)
  {
    Serial.print("Remote Reset Enabled\n");
  }
  else
  {
    Serial.print("Remote Reset Disabled\n");
  }
  /*Low Water Pressure*/
  if ((App_fault>>2) & 1)
  {
    Serial.print("Water Pressure Fault\n");
  }
  else
  {
    Serial.print("No Water Pressure Fault\n");
  }
  /*Gas/Flame fault*/
  if ((App_fault>>3) & 1)
  {
    Serial.print("Gas/Flame Fault\n");
  }
  else
  {
    Serial.print("No Gas/Flame Fault\n");
  }
  /*Air-Press Fault*/
  if ((App_fault>>4) & 1)
  {
    Serial.print("Air-Press Fault\n");
  }
  else
  {
    Serial.print("No Air-Press Fault\n");
  }
  /*Water over-temp*/
  if ((App_fault>>4) & 1)
  {
    Serial.print("Water over-temp Fault\n");
  }
  else
  {
    Serial.print("No Water over-temp Fault\n");
  }
/**********************************************************************/
 //# unsigned int diagval = 0xFF;
//  diagval = ot.sendrequest(ot.buildRequest(READ, OEMDiagnosticCode, diagval);
// diagval = ot.sendRequest(115);
 // responseStatus = ot.getLastResponseStatus();
  //if (responseStatus == OpenThermResponseStatus::SUCCESS) {
//    Serial.println("diagnostic code " + String(diagval));
  //}
  
	Serial.println();
	delay(1000);
}
