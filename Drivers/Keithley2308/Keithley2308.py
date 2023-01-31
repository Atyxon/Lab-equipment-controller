import logging
from enum import Enum
from datetime import datetime
import pyvisa
import time

from PyQt5.QtCore import QMutex, QTimer, QObject


class Keithley2308Commands(Enum):
    """
    Enum class with commands in string format
    """
    SIMULATOR_RESET = '*RST'
    READ_BATT_SIM_STATUS = 'OUTP?'
    READ_SIM_ERROR = 'STAT:QUE?'
    SET_BATT_SIM_CURRENT_MEAS_RANGE = 'SENS:CURR:UPP'
    SET_BATT_SIM_VOLTAGE_AMPLITUDE = 'SOUR:VOLT'
    SET_BATT_SIM_CURRENT_LIMIT_VALUE = 'SOUR:CURR'
    TURN_ON_OFF_BATT_SIM_OUTPUT = 'OUTP:STAT'
    SET_BATT_SIM_OUTPUT_BANDWIDTH = 'OUTP:BAND'
    SET_BATT_SIM_OUTPUT_IMPEDANCE = 'SOUR:IMP'
    BATT_SIM_SELECT_READBACK_FUNCTION = 'SENS:FUNC'
    SET_BATT_SIM_INTEGRATION_RATE = 'SENS:NPLC'
    SET_BATT_SIM_AVERAGE_COUNT_VOLT_CURR = 'SENS:AVER'
    TRIGGER_AND_RETURN_BATTERY_CHANNEL = 'READ?'
    TRIGGER_AND_RETURN_ARRAY_BATTERY_CHANNEL = 'READ:ARR?'
    CONTROL_OUTPUT_RELAY = 'OUTP:REL'
    SELECT_PROTOCOL = 'SYST:MEP:STAT'
    ENABLE_TRIGGER_CONTINUOUS_MODE = 'SYST:TRIG:CONT'


class KeithleyCurrentMeasRange(Enum):
    """
    Enum class with current measurements range
    """
    RANGE_5_MA = 5
    RANGE_50_MA = 50
    RANGE_500_MA = 500
    RANGE_5_A = 5000


class RelayCircuitStates(Enum):
    """
    Enum class with relay circuit states
    """
    OFF = 0
    ON = 1
    UNKNOWN = 2


class SimStates(Enum):
    """
    Enum class with sim states
    """
    OFF = 0
    ON = 1
    UNKNOWN = 2


class ContinuousTriggerStates(Enum):
    """
    Enum class with continuous trigger mode states
    """
    OFF = 0
    ON = 1
    UNKNOWN = 2


class SelectedProtocol(Enum):
    """
    Enum class with continuous trigger mode states
    """
    PROTOCOL_488_1 = 0
    PROTOCOL_SCPI = 1


class Keithley2308RelayState(Enum):
    """
    Enum class with parameters to open/close relay circuit
    """
    RELAY_CIRCUIT_OPEN = 'ZERO'  # Value to open relay circuit
    RELAY_CIRCUIT_CLOSE = 'ONE'  # Value to close relay circuit


class ReadbackFunctionTypes(Enum):
    """
    Enum class with readback function types
    """
    READBACK_CURRENT = 'CURR'
    READBACK_VOLTAGE = 'VOLT'


class Keithley2308:
    """
    Class for controlling Keithley 2308 Portable Device Battery/Charger Simulator
    """
    RECONNECT_TIME = 2.0  # Time in [s] to try again to connect to instrument
    MEASUREMENT_RANGE_MIN = 0.0  # Min value of measurement range of current in [A]
    MEASUREMENT_RANGE_MAX = 5.0  # Max value of measurement range of current in [A]
    VOLTAGE_AMPLITUDE_MIN = 0.0  # Min value of voltage amplitude in [V]
    VOLTAGE_AMPLITUDE_MAX = 15.0  # Max value of voltage amplitude in [V]
    CURRENT_LIMIT_MIN = 0.006  # Min value of simulator current limit in [A]
    CURRENT_LIMIT_MAX = 5.0  # Max value of simulator current limit in [A]
    OUTPUT_IMPEDANCE_MIN = 0.0  # Min value of simulator output impedance in [Ω]
    OUTPUT_IMPEDANCE_MAX = 1.0  # Max value of simulator output impedance in [Ω]
    INTEGRATION_RATE_MIN = 0.002  # Min integration rate of voltage and current (in line cycles)
    INTEGRATION_RATE_MAX = 10.0  # Max integration rate of voltage and current (in line cycles)
    AVERAGE_COUNT_VOLT_CURR_MIN = 1.0  # Min average count for voltage and current
    AVERAGE_COUNT_VOLT_CURR_MAX = 10.0  # Max average count for voltage and current
    RELAY_INDEX_MIN = 1  # Min index of output relay array
    RELAY_INDEX_MAX = 4  # Max index of output relay array

    mutex = QMutex()  # Mutex used to prevent Keithley 2308 functions overlaping

    def __init__(self, adress='GPIB0::16::INSTR', boudrate=9600, time_out=10):
        """
        init function of Keithley2308 driver
        :param adress: Adress of Keithley 2308 to connect with
        :param boudrate: communication channel boudrate
        :param: time_out: time in [s] before connection timeout
        """
        self.adress = adress
        self.instrument = None

        rm = pyvisa.ResourceManager()
        start_time = time.time()

        while self.instrument is None:
            if time.time() - start_time < time_out:
                try:
                    self.instrument = rm.open_resource(self.adress, timeout=10000)
                except pyvisa.VisaIOError as e:
                    if rm.last_status == pyvisa.constants.StatusCode.error_resource_busy:
                        logging.error(f"Failed to connect, instrument is busy, try again in {self.RECONNECT_TIME}s")
                    else:
                        raise ConnectionError(f"Can't connect to device")
                    time.sleep(self.RECONNECT_TIME)
            else:
                raise ConnectionError(f"Can't connect to device")

        self.instrument.baud_rate = boudrate

    @staticmethod
    def wait_for_sim_action():
        """
        There is need to wait after cmd write for simulator action
        """
        cmd_wait_time = 1  # in seconds
        time.sleep(cmd_wait_time)

    def measure_battery_sim_current(self):
        """
        Measure current in [A] value of battery sim channel
        """
        self.mutex.lock()
        command = f"{Keithley2308Commands.BATT_SIM_SELECT_READBACK_FUNCTION.value} '{ReadbackFunctionTypes.READBACK_CURRENT.value}'"
        self.instrument.write(command)
        self.wait_for_sim_action()
        value = float(self.instrument.query(Keithley2308Commands.TRIGGER_AND_RETURN_BATTERY_CHANNEL.value))
        self.mutex.unlock()
        return value

    def triger_continuous_mode_disable(self):
        """
        Disable trigger continuous mode on battery sim channel
        """
        command = f"{Keithley2308Commands.ENABLE_TRIGGER_CONTINUOUS_MODE.value} {ContinuousTriggerStates.OFF.value}]"
        self.instrument.write(command)
        self.wait_for_sim_action()

    def triger_continuous_mode_enable(self):
        """
        Enable trigger continuous mode on battery sim channel to speed up measurements
        """
        self.triger_continuous_mode_disable()
        command = f"{Keithley2308Commands.BATT_SIM_SELECT_READBACK_FUNCTION.value} '{ReadbackFunctionTypes.READBACK_CURRENT.value}'"
        self.instrument.write(command)
        self.wait_for_sim_action()
        command = f"{Keithley2308Commands.SELECT_PROTOCOL.value} {SelectedProtocol.PROTOCOL_488_1}"
        self.instrument.write(command)
        self.wait_for_sim_action()
        command = f"{Keithley2308Commands.ENABLE_TRIGGER_CONTINUOUS_MODE.value} {ContinuousTriggerStates.ON.value}"
        self.instrument.write(command)
        self.wait_for_sim_action()

    def simulator_reset(self):
        """
        Returns the simulator to the *RST default conditions
        """
        command = f"{Keithley2308Commands.SIMULATOR_RESET.value}"
        self.instrument.write(command)
        self.wait_for_sim_action()

    def batt_sim_status_read(self) -> SimStates:
        """
        Read and return status of battery simulator
        :return: simulator status
        """
        command = f"{Keithley2308Commands.READ_BATT_SIM_STATUS.value}"
        status = self.instrument.query(command)
        if int(status) == SimStates.OFF.value:
            return SimStates.OFF.value
        elif int(status) == SimStates.ON.value:
            return SimStates.ON.value
        else:
            return SimStates.UNKNOWN.value

    def sim_error_read(self) -> str:
        """
        Read and return error of simulator
        :return: simulator error
        """
        command = f"{Keithley2308Commands.READ_SIM_ERROR.value}"
        return self.instrument.query(command)

    def batt_sim_current_meas_range_set(self, current: KeithleyCurrentMeasRange):
        """
        Set battery simulator current measurement range.
        Value setting will designate one of four ranges:
        5 mA, 50 mA, 500 mA and 5 A.
        :param current: new current measurement range in [A]
        """
        if self.MEASUREMENT_RANGE_MAX < current.value or self.MEASUREMENT_RANGE_MIN > current.value:
            raise ValueError("Error: Wrong current measurement range value was given")

        command = f"{Keithley2308Commands.SET_BATT_SIM_CURRENT_MEAS_RANGE.value} {current.value}"
        self.instrument.write(command)
        self.wait_for_sim_action()

    def batt_sim_voltage_amplitude_set(self, voltage_amplitude: float):
        """
        Set battery simulator voltage amplitude
        :param voltage_amplitude: new voltage amplitude in [V]
        """
        if self.VOLTAGE_AMPLITUDE_MAX < voltage_amplitude or self.VOLTAGE_AMPLITUDE_MIN > voltage_amplitude:
            raise ValueError("Error: Wrong voltage amplitude value was given")

        command = f"{Keithley2308Commands.SET_BATT_SIM_VOLTAGE_AMPLITUDE.value} {voltage_amplitude}"
        self.instrument.write(command)
        self.wait_for_sim_action()

    def batt_sim_current_limit_set(self, value: float):
        """
        Set battery simulator current limit
        :param value: new current limit value in [A]
        """
        if self.CURRENT_LIMIT_MAX < value or self.CURRENT_LIMIT_MIN > value:
            raise ValueError("Error: Wrong current limit value was given")

        command = f"{Keithley2308Commands.SET_BATT_SIM_CURRENT_LIMIT_VALUE.value} {value}"
        self.instrument.write(command)
        self.wait_for_sim_action()

    def batt_sim_turn_on(self):
        """
        Turn ON battery simulator
        """
        command = f"{Keithley2308Commands.TURN_ON_OFF_BATT_SIM_OUTPUT.value} ON"
        self.instrument.write(command)
        self.wait_for_sim_action()

    def batt_sim_turn_off(self):
        """
        Turn OFF battery simulator
        """
        command = f"{Keithley2308Commands.TURN_ON_OFF_BATT_SIM_OUTPUT.value} OFF"
        self.instrument.write(command)
        self.wait_for_sim_action()

    def batt_sim_bandwidth_set_low(self):
        """
        Set device battery bandwidth to LOW
        """
        command = f"{Keithley2308Commands.SET_BATT_SIM_OUTPUT_BANDWIDTH.value} LOW"
        self.instrument.write(command)
        self.wait_for_sim_action()

    def batt_sim_bandwidth_set_high(self):
        """
        Set device battery bandwidth to HIGH
        """
        command = f"{Keithley2308Commands.SET_BATT_SIM_OUTPUT_BANDWIDTH.value} HIGH"
        self.instrument.write(command)
        self.wait_for_sim_action()

    def batt_sim_output_impedance_set(self, impedance: float):
        """
        Set impedance in [Ω] of battery sim
        :param impedance: value of impedance to be set
        """
        if self.OUTPUT_IMPEDANCE_MAX < impedance or self.OUTPUT_IMPEDANCE_MIN > impedance:
            raise ValueError("Error: Wrong output impedance value was given")

        command = f"{Keithley2308Commands.SET_BATT_SIM_OUTPUT_IMPEDANCE.value} {impedance}"
        self.instrument.write(command)
        self.wait_for_sim_action()

    def batt_sim_readback_function_select_voltage(self):
        """
        Select readback function to VOLTAGE
        """
        command = f"{Keithley2308Commands.BATT_SIM_SELECT_READBACK_FUNCTION.value} 'VOLT'"
        self.instrument.write(command)
        self.wait_for_sim_action()

    def batt_sim_readback_function_select_current(self):
        """
        Select readback function to CURRENT
        """
        command = f"{Keithley2308Commands.BATT_SIM_SELECT_READBACK_FUNCTION.value} 'CURR'"
        self.instrument.write(command)
        self.wait_for_sim_action()

    def batt_sim_integration_rate_set(self, rate_value: float):
        """
        Set battery simulator integration rate for voltage and current
        :param rate_value: new value of integration rate in line cycles
        """
        if self.INTEGRATION_RATE_MAX < rate_value or self.INTEGRATION_RATE_MIN > rate_value:
            raise ValueError("Error: Wrong integration rate value was given")

        command = f"{Keithley2308Commands.SET_BATT_SIM_INTEGRATION_RATE.value} {rate_value}"
        self.instrument.write(command)
        self.wait_for_sim_action()

    def batt_sim_average_count_volt_curr_set(self, count_value: float):
        """
        Set average count value for voltage and current measurements
        :param count_value: Set average reading count
        """
        if self.AVERAGE_COUNT_VOLT_CURR_MAX < count_value or self.AVERAGE_COUNT_VOLT_CURR_MIN > count_value:
            raise ValueError("Error: Wrong integration rate value was given")

        command = f"{Keithley2308Commands.SET_BATT_SIM_AVERAGE_COUNT_VOLT_CURR.value} {count_value}"
        self.instrument.write(command)
        self.wait_for_sim_action()

    def batt_sim_trigger_and_return_reading(self) -> float:
        """
        Trigger and return one reading for battery channel
        :return: value of reading for battery channel
        """
        command = f"{Keithley2308Commands.TRIGGER_AND_RETURN_BATTERY_CHANNEL.value}"
        value = self.instrument.query(command)
        return value

    def batt_sim_trigger_and_return_readings_array(self) -> [float]:
        """
        Trigger and return array of readings for battery channel
        :return: array of readings for battery channel
        """
        command = f"{Keithley2308Commands.TRIGGER_AND_RETURN_ARRAY_BATTERY_CHANNEL.value}"
        value = self.instrument.query(command)
        return value

    def relays_control(self, relay_index: int, state: Keithley2308RelayState):
        """
        Control output relay subsystem
        :param relay_index: index of relay in array [1-4]
        :param state: state of control circuit, [Close (1)] or [Open (0)]
        """
        if self.RELAY_INDEX_MAX < relay_index or self.RELAY_INDEX_MIN > relay_index:
            raise ValueError("Error: Wrong relay index was given")

        command = f"{Keithley2308Commands.CONTROL_OUTPUT_RELAY.value}{relay_index} {state.value}"
        self.instrument.write(command)
        self.wait_for_sim_action()
