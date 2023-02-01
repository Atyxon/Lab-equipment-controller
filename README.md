# Lab Equipment Controller Application
## Table of contents
* [General info](#general-info)
* [Technologies](#technologies)
* [How to use](#how-to-use)
* [Rigol DP832](#rigol-dp832)
* [Pico TC-08](#pico-tc08)
* [Keithley 2308](#keithley-2308)

## General info
This project is used to control laboratory equipment via UI created with Python and PyQt

Visualisation of Rigol DP832 Power Supply controll panel:

<img src="https://user-images.githubusercontent.com/75041222/216007440-355c39b1-ff14-44c3-bd42-5c8c1c1b2197.png" width="440" height="325">


Script made for handling UI elements is **application.py**, all equipment drivers are inside **Drivers** folder, and example usage of these drivers is inside **Examples** folder


## How to use	
Run application.py and select your devices from options > Choose Lab Equipment

## Technologies
Project is created with:
* Python v3.9
* PyQt v5.15

## Rigol DP832
You may need to install drivers from manufacturer: [link](https://www.rigol.eu/products/dc-power/dp800.html) <br>

Find connected devices using `DeviceFinder.py`, it should return something like 
`('ASRL10::INSTR', 'USB0::0x1AB1::0x0E11::DP8XXXXXXXXXX::INSTR')`
Connect to `'USB0::0x1AB1::0x0E11::DP8XXXXXXXXXX::INSTR'` and return `IDN` using:

```
import pyvisa

if __name__ == "__main__":
   rm = pyvisa.ResourceManager()
   adress = 'USB0::0x1AB1::0x0E11::DPXXXXXXXXXXX::INSTR'
   ins = rm.open_resource(adress)
   print(ins.query('*IDN?'))

```

In case of not finding an instrument, try to download `libusb-win32` from [here](https://sourceforge.net/projects/libusb-win32/) 
and install device filter on hardware

## Pico TC-08
You shall install SKD from manufacturer:
[64-bit version](https://www.picotech.com/downloads/_lightbox/pico-software-development-kit-64bit)
or [32-bit version](https://www.picotech.com/downloads/_lightbox/pico-software-development-kit-32-bit)

You can find Pico TC-08 library README [here](https://github.com/picotech/picosdk-python-wrappers#readme)

## Keithley 2308
Download and install IO Libraries Suite from [here](https://www.keysight.com/us/en/lib/software-detail/computer-software/io-libraries-suite-downloads-2175637.html)

Find connected devices using `DeviceFinder.py`, it should return something `('ASRL10::INSTR', 'GPIB0::XX::INSTR')`

Connect to `'GPIB0::16::INSTR'` and return `IDN` using:

```
import pyvisa

if __name__ == "__main__":
   rm = pyvisa.ResourceManager()
   ins = rm.open_resource('GPIB0::16::INSTR')
   print(ins.query('*IDN?'))
```

it should return `KEITHLEY INSTRUMENTS INC.,[MODEL NAME]`
