# xboxrc

Raspberry pi zero-based UAV RC using XboxOne controller and FrSky DHT transmitter module

# Recommended Hardware

- XboxOne controller (tested with Microsoft model)
- Raspberry pi zero (older pi's cannot execute the gpios quickly enough)
- FrSky DHT 8ch DIY telemetry compatible transmitter module 
- FrSky D4R-II receiver module (on the vehicle)

Other hardware controllers and transmitter modules (e.g, Orange) may be compatible, but I haven't tested them.

# Software Requirements

- Rasbian Jessie Lite or greater
- Establish network connection to install
- sudo apt-get update
- sudo apt-get install git wget raspi-gpio python-dev capnp
- cd ~/ && wget https://bootstrap.pypa.io/get-pip.py
- sudo python get-pip.py && rm get-pip.py
- sudo pip install pycapnp
- sudo modprobe xpad
- cd ~/ && wget abyz.co.uk/rpi/pigpio/pigpio.zip && unzip pigpio.zip
- cd PIGPIO && make && sudo make install && rm ../pigpio.zip
- set GPIO 18 as PWM0 using: raspi-gpio set 18 a5
- verify GPIO 18 is set using: raspi-gpio get

# About

The XboxOne controller transmits joystick and button data over a USB connection to the pi. Raspbian provides the xpad linux kernel module to parse the serial stream from the controller. The xpad module mounts the controller as a device, which can be accessed using its api and enumerations.

Stick commands and buttons are mapped to specific actions. Since there are no switches an internal state machine manages the active mode and submode (ch 5 and 6). The stick commands are mapped to the normal commands for manual / altitude assist / position assist modes. Buttons are mapped as follows:


X: 

Y: 

A:

B:

Left button:

Right button:


The FrSky DHT transmitter module expects a CPPM signal from the pi with a 27ms frame length. This allows us to combine the 8 channels with 1ms minimums, 2ms maximums and 100 microsecond gaps. The remaining frame time is allocated for the sync pulse. You can read more about how CPPM signals work [here](https://www.youtube.com/watch?v=sEChFDRf8Ek) and [here](https://sourceforge.net/p/arduinorclib/ ... %20Signal/). To generate the CPPM signal, we use the [pigpio library](https://github.com/joan2937/pigpio/tree/master). Thanks to [Joan](https://github.com/joan2937) for the support.

# Troubleshooting

## Can't find xbox controller

  Try installing the joystick project from apt-get, and then run 

  ```joytest /dev/input/js0```

  You should see a stream of commands printing to the terminal.
