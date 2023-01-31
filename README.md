# Lab Equipment Controller Application
## Table of contents
* [General info](#general-info)
* [Technologies](#technologies)
* [How to use](#how-to-use)
* [Rigol DP832](#Rigol-DP832)
* [Pico TC-08](#Pico-TC08)
* [Keithley 2308](#Keithley-2308)

## General info
This project is used to control laboratory equipment via UI

## How to use	
Run application.py and select your devices from options > Choose Lab Equipment

## Technologies
Project is created with:
* Python v3.9
* PyQt v5.15

### Rigol DP832
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

### Pico TC-08
You shall install SKD from manufacturer:
[64-bit version](https://www.picotech.com/downloads/_lightbox/pico-software-development-kit-64bit)
or [32-bit version](https://www.picotech.com/downloads/_lightbox/pico-software-development-kit-32-bit)

You can find Pico TC-08 library README [here](https://github.com/picotech/picosdk-python-wrappers#readme)

### Keithley 2308
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