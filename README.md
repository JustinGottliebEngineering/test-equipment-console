# \# Test Equipment Communication Console

# 

# A desktop application for communicating with simulated and real electronic test equipment.

# 

# The application provides a structured instrument-driver architecture, PySide6 desktop interface, SCPI-style command console, live measurement monitoring, CSV data export, PyVISA resource discovery, and automated tests.

# 

# !\[Python](https://img.shields.io/badge/Python-3.12%2B-3776AB)

# !\[PySide6](https://img.shields.io/badge/GUI-PySide6-41CD52)

# !\[PyVISA](https://img.shields.io/badge/Instrumentation-PyVISA-5C4EE5)

# !\[Tests](https://img.shields.io/badge/tests-83%20passing-brightgreen)

# !\[License](https://img.shields.io/badge/license-MIT-blue)

# 

# \## Overview

# 

# The Test Equipment Communication Console demonstrates how production-test software can support both simulated hardware and physical instruments through a common driver interface.

# 

# The built-in simulators allow the application to be demonstrated and tested without laboratory hardware. Real instruments can be discovered and opened through PyVISA when a compatible VISA implementation and instrument connection are available.

# 

# \## Features

# 

# \- PySide6 desktop interface

# \- Abstract instrument-driver architecture

# \- Simulated frequency counter

# \- Simulated programmable DC power supply

# \- Generic PyVISA instrument driver

# \- VISA resource discovery

# \- GPIB, USB, serial, TCP/IP, PXI, and VXI resource classification

# \- SCPI-style command console

# \- Instrument identity display

# \- Instrument-specific control panels

# \- Live measurement monitoring

# \- Frequency-error calculations in hertz and parts per million

# \- Voltage, current, and power measurements

# \- Timestamped measurement history

# \- CSV data export

# \- Windows standalone executable build

# \- Automated unit tests using simulated and fake VISA resources

# 

# \## Application Modes

# 

# \### Simulation Mode

# 

# Simulation mode requires no external equipment.

# 

# The application includes:

# 

# \- OpenBench FC-1000 simulated frequency counter

# \- OpenBench PS-305 simulated programmable power supply

# 

# These simulators support connection state, command processing, measurement noise, forced test values, reset behavior, output state, current limiting, and SCPI-style queries.

# 

# \### VISA Mode

# 

# VISA mode supports real laboratory instruments through PyVISA.

# 

# The application can discover resources exposed by the installed VISA implementation, including:

# 

# \- GPIB

# \- USB

# \- Serial

# \- TCP/IP

# \- PXI

# \- VXI

# 

# A discovered resource can be added to the instrument list and controlled through the generic command console.

# 

# Real-instrument communication requires:

# 

# \- a compatible VISA implementation

# \- the appropriate hardware interface and driver

# \- a connected instrument

# \- correct communication settings

# \- commands supported by the selected instrument

# 

# \## Screenshots

# 

# Repository screenshots can be added under:

# 

# ```text

# docs/screenshots/

