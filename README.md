# SmartGreenhouse
Source code for a project implemented for my engineering thesis: "Design of a humidity and temperature control system in a greenhouse" (final project for my electrical engineering degree).

This system monitors the air temperature, air humidity, and soil moisture in a greenhouse. Based on sensor readings, it automatically adjusts the operation of heating and irrigation components to maintain target values for temperature and humidity. There is also an option for manual parameter adjustment. The control system is built with Arduino UNO and Raspberry Pi 3B+ microcontrollers.

Features
- Automated control of heating and irrigation based on sensor data.
- Manual adjustment of parameters (temperature, humidity).
- Web interface for monitoring and control.

Components
- Sensors: Air temperature (AHT20), air humidity (AHT20), soil moisture (V2.0), soil temperature (DS18B20).
- Actuators: Ceramic heating element, water pump, PC fans, USB air humidifier.
- Microcontrollers: Arduino UNO (for sensors) and Raspberry Pi 3B+ (for web interface and control logic).
