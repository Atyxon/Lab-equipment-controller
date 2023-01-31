import logging
from enum import Enum
from datetime import datetime
from dataclasses import dataclass, field
import pyvisa
import time


@dataclass
class PowerSupplyMeas:
    """
    Class for sending Power Supply measured values
    """
    _voltage_idx: int = field(default=0, init=False, repr=False, hash=False, compare=False)
    _current_idx: int = field(default=1, init=False, repr=False, hash=False, compare=False)
    _power_idx: int = field(default=2, init=False, repr=False, hash=False, compare=False)
    voltage: float = None
    current: float = None
    power: float = None

    def __init__(self, *args, **kwargs):
        if len(kwargs) > 0:
            if kwargs.get('data') is not None:
                data = kwargs.get('data')
                self.voltage = float(data.split(',')[self._voltage_idx])
                self.current = float(data.split(',')[self._current_idx])
                self.power = float(data.split(',')[self._power_idx])
            else:
                self.voltage = kwargs.get('voltage')
                self.current = kwargs.get('current')
                self.power = kwargs.get('power')
        else:
            if isinstance(args[0], str):
                elements = args[0].split(',')
                if len(elements) == (self._power_idx + 1):
                    self.voltage = float(elements[self._voltage_idx])
                    self.current = float(elements[self._current_idx])
                    self.power = float(elements[self._power_idx])


class RigolDP832Commands(Enum):
    """
    Enum class with commends in string format
    """
    SELECT_CHANNEL = 'INST:SELE CH'
    SET_OUTPUT_CURRENT = ':CURR'
    SET_OUTPUT_VOLTAGE = ':VOLT'
    GET_OUTPUT_VALUES = 'APPL? CH'
    MEASURE_VOLTAGE = 'MEAS? CH'
    MEASURE_CURRENT = 'MEAS:CURR? CH'
    MEASURE_ALL = 'MEAS:ALL? CH'
    TURN_ON_OFF_CHANNEL = 'OUTP CH'
    SET_OVP = 'OUTP:OVP CH'
    SET_OCP = 'OUTP:OCP CH'
    SET_OVP_LIMIT = 'OUTP:OVP:VAL CH'
    SET_OCP_LIMIT = 'OUTP:OCP:VAL CH'
    READ_CHANNEL_STATE = 'OUTP? CH'
    READ_OVP_STATE = 'OUTP:OVP? CH'
    READ_OCP_STATE = 'OUTP:OCP? CH'
    GET_OVP_VALUE = 'OUTP:OVP:VAL? CH'
    GET_OCP_VALUE = 'OUTP:OCP:VAL? CH'
    READ_OUTPUT_MODE = ':OUTP:MODE? CH'


class RigolDP832OutputProtectionStates(Enum):
    """
    Enum class with OVP and OCP states
    """
    OFF = 'OFF'
    ON = 'ON'
    UNKNOWN = 'UNKNOWN'


class RigolDP832OutputStates(Enum):
    """
    Enum class with output states
    """
    OFF = 'OFF'
    ON = 'ON'
    UNKNOWN = 'UNKNOWN'


class RigolDP832OutputModes(Enum):
    """
    Enum class with output modes
    """
    CONSTANT_CURRENT = 'CC'
    CONSTANT_VOLTAGE = 'CV'
    UNREGULATED = 'UR'


class RigolDP832:
    """
    Class for controlling Rigol DP832/DP832A power supply
    """
    RECONNECT_TIME = 2.0  # Time in [S] to try again to connect to instrument
    CHANNEL_FIRST = 1  # First channel of Rigol DP832/DP832A
    CHANNEL_SECOND = 2  # Second channel of Rigol DP832/DP832A
    CHANNEL_THIRD = 3  # Third channel of Rigol DP832/DP832A
    CHANNEL_MIN = CHANNEL_FIRST  # Min channel range value
    CHANNEL_MAX = CHANNEL_THIRD  # Max channel range value
    OUTPUT_VOLTAGE_MAX = 30.0  # Max voltage in [V] to be set on channel
    OUTPUT_VOLTAGE_MAX_CHANNEL_THIRD = 5.0  # Max voltage in [V] to be set on third channel
    OUTPUT_VOLTAGE_MIN = 0.0  # Min voltage in [V] to be set on channel
    OUTPUT_CURRENT_MAX = 3.0  # Max current in [A] to be set on channel
    OUTPUT_CURRENT_MIN = 0.0  # Min current in [A] to be set on channel

    def __init__(self, address='USB0::0x1AB1::0x0E11::DP8C193604338::INSTR', boudrate=9600, time_out=10):
        """
        init function of RigolDP832 driver
        :param address: Address of Rigol power supply to connect with
        :param boudrate: communication channel boudrate
        :param: time_out: time in [s] before connection timeout
        """
        self.address = address
        self.instrument = None

        rm = pyvisa.ResourceManager()
        start_time = time.time()
        while self.instrument is None:
            if time.time() - start_time < time_out:
                try:
                    self.instrument = rm.open_resource(self.address)
                except pyvisa.VisaIOError as e:
                    if rm.last_status == pyvisa.constants.StatusCode.error_resource_busy:
                        logging.error(f"Failed to connect, instrument is busy, try again in {self.RECONNECT_TIME}s")
                    else:
                        raise ConnectionError(f"Can't connect to device")
                    time.sleep(self.RECONNECT_TIME)
            else:
                raise ConnectionError(f"Can't connect to device")

        self.instrument.baud_rate = boudrate

        self.status_channel_register = []

    def __validate_channel_index(self, channel: int):
        """
        Valiate if channel index is within range
        :param channel: specific channel to interact with
        """
        if self.CHANNEL_MAX < channel < self.CHANNEL_MIN:
            raise ValueError(f"Error: Channel index out of range [{self.CHANNEL_MIN};{self.CHANNEL_MAX}]")

    def register_status(self, channel: int):
        """
        Register status of channel in list as string
        :param channel: specific channel to interact with
        """
        self.__validate_channel_index(channel)
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        status = f"[{current_time}] Channel {channel} status: {self.channel_state_read(channel)}"
        self.status_channel_register.append(status)

    @staticmethod
    def wait_for_ps_action():
        """
        There is need to wait after cmd write for power supply action
        """
        cmd_wait_time = 1  # in seconds
        time.sleep(cmd_wait_time)

    def output_voltage_set(self, channel: int, output_voltage: float):
        """
        Set power supply output voltage on channel
        :param channel: specific channel to interact with
        :param output_voltage: new output voltage in [V] to be set on channel
        """
        self.__validate_channel_index(channel)
        if channel == self.CHANNEL_THIRD:
            if self.OUTPUT_VOLTAGE_MAX_CHANNEL_THIRD < output_voltage < self.OUTPUT_VOLTAGE_MIN:
                raise ValueError("Error: Wrong output Voltage value was given")
        else:
            if self.OUTPUT_VOLTAGE_MAX < output_voltage < self.OUTPUT_VOLTAGE_MIN:
                raise ValueError("Error: Wrong output Voltage value was given")

        command = f"{RigolDP832Commands.SELECT_CHANNEL.value}{channel}"
        self.instrument.write(command)
        command = f"{RigolDP832Commands.SET_OUTPUT_VOLTAGE.value} {output_voltage}"  # command to change voltage in specific channel
        self.instrument.write(command)  # send command to Rigol power supply
        self.wait_for_ps_action()  # wait for Rigol power supply to execute command

    def output_voltage_measure(self, channel: int) -> float:
        """
        Get power supply output voltage on channel
        :param channel: specific channel to interact with
        :return: returns voltage value in [V] on specific channel
        """
        self.__validate_channel_index(channel)
        command = f"{RigolDP832Commands.MEASURE_VOLTAGE.value}{channel}"  # command to get voltage in specific channel
        voltage = float(self.instrument.query(command))  # query instrument with command to get voltage
        self.wait_for_ps_action()  # wait for Rigol power supply to execute command
        return voltage

    def output_current_set(self, channel: int, output_current: float):
        """
            Set power supply output current on channel
        :param channel: specific channel to interact with
        :param output_current: new output current in [A] to be set on channel
        """
        self.__validate_channel_index(channel)
        if self.OUTPUT_CURRENT_MAX < output_current < self.OUTPUT_CURRENT_MIN:
            raise ValueError("Error: Wrong Current value was given")
        command = f"{RigolDP832Commands.SELECT_CHANNEL.value}{channel}"
        self.instrument.write(command)
        command = f"{RigolDP832Commands.SET_OUTPUT_CURRENT.value} {output_current}"  # command to change current in specific channel
        self.instrument.write(command)  # send command to Rigol power supply
        self.wait_for_ps_action()  # wait for Rigol power supply to execute command

    def output_current_measure(self, channel: int) -> float:
        """
        Get power supply output current on channel
        :param channel: specific channel to interact with
        :return: returns current value in [A] on specific channel
        """
        self.__validate_channel_index(channel)
        command = f"{RigolDP832Commands.MEASURE_CURRENT.value}{channel}"  # command to get current in specific channel
        current = float(self.instrument.query(command))  # query instrument with command to get current
        self.wait_for_ps_action()  # wait for Rigol power supply to execute command
        return current

    def output_voltage_value_get(self, channel: int) -> float:
        """
        Get power supply output voltage of channel
        :param channel: specific channel to interact with
        :return: returns voltage value in [V] of specific channel
        """
        self.__validate_channel_index(channel)
        command = f"{RigolDP832Commands.GET_OUTPUT_VALUES.value}{channel}"
        voltage = float(self.instrument.query(command).split(',')[1])
        return voltage

    def output_current_value_get(self, channel: int) -> float:
        """
        Get power supply output current of channel
        :param channel: specific channel to interact with
        :return: returns current value in [A] of specific channel
        """
        self.__validate_channel_index(channel)
        command = f"{RigolDP832Commands.GET_OUTPUT_VALUES.value}{channel}"
        current = float(self.instrument.query(command).split(',')[2])
        return current

    def measure_all_values(self, channel: int) -> PowerSupplyMeas:
        """
        Measure voltage in [V], current in [A], and power in [W] on specified channel
        :param channel: specific channel to interact with
        :return: return PowerSupplyMeas class containing voltage in [V], current in [A], and power in [W]
        """
        self.__validate_channel_index(channel)
        command = f"{RigolDP832Commands.MEASURE_ALL.value}{channel}"
        output = self.instrument.query(command)
        return PowerSupplyMeas(output)

    def channel_turn_on(self, channel: int):
        """
        Turn ON power supply channel
        :param channel: specific channel to interact with
        """
        self.__validate_channel_index(channel)
        command = f"{RigolDP832Commands.TURN_ON_OFF_CHANNEL.value}{channel},ON"  # command to turn ON specific channel
        self.instrument.write(command)  # send command to Rigol power supply
        self.wait_for_ps_action()  # wait for Rigol power supply to execute command

    def channel_turn_off(self, channel: int):
        """
        Turn ON power supply channel
        :param channel: specific channel to interact with
        """
        self.__validate_channel_index(channel)
        command = f"{RigolDP832Commands.TURN_ON_OFF_CHANNEL.value}{channel},OFF"  # command to turn OFF specific channel
        self.instrument.write(command)  # send command to Rigol power supply
        self.wait_for_ps_action()  # wait for Rigol power supply to execute command

    def ovp_turn_on(self, channel: int):
        """
        Turn ON power supply OVP on channel
        :param channel: specific channel to interact with
        """
        self.__validate_channel_index(channel)
        command = f"{RigolDP832Commands.SET_OVP.value}{channel},ON"  # command to turn ON OVP in specific channel
        self.instrument.write(command)  # send command to Rigol power supply
        self.wait_for_ps_action()  # wait for Rigol power supply to execute command

    def ovp_value_set(self, channel: int, limit_value: float):
        """
        Set value of OVP Voltage limit in [V]
        :param channel: specific channel to interact with
        :param limit_value: max value of voltage in [V] on specific channel
        """
        self.__validate_channel_index(channel)
        if channel == self.CHANNEL_THIRD:
            if self.OUTPUT_VOLTAGE_MAX_CHANNEL_THIRD < limit_value < self.OUTPUT_VOLTAGE_MIN:
                raise ValueError("Error: Wrong Voltage limit value was given")
        else:
            if self.OUTPUT_VOLTAGE_MAX < limit_value < self.OUTPUT_VOLTAGE_MIN:
                raise ValueError("Error: Wrong Voltage limit value was given")
        command_limit = f"{RigolDP832Commands.SET_OVP_LIMIT.value}{channel},{limit_value}"  # command to set voltage limit
        self.instrument.write(command_limit)  # send command to Rigol power supply
        self.wait_for_ps_action()  # wait for Rigol power supply to execute command

    def ovp_turn_off(self, channel: int):
        """
        Turn ON power supply OVP on channel
        :param channel: specific channel to interact with
        """
        self.__validate_channel_index(channel)
        command = f"{RigolDP832Commands.SET_OVP.value}{channel},OFF"  # command to turn OFF OVP in specific channel
        self.instrument.write(command)  # send command to Rigol power supply
        self.wait_for_ps_action()  # wait for Rigol power supply to execute command

    def ocp_turn_on(self, channel: int):
        """
        Turn ON power supply OCP on channel
        :param channel: specific channel to interact with
        """
        self.__validate_channel_index(channel)
        command = f"{RigolDP832Commands.SET_OCP.value}{channel},ON"  # command to turn ON OCP in specific channel
        self.instrument.write(command)  # send command to Rigol power supply
        self.wait_for_ps_action()  # wait for Rigol power supply to execute command

    def ocp_value_set(self, channel: int, limit_value: float):
        """
        Set value of OCP Voltage limit in [A]
        :param channel: specific channel to interact with
        :param limit_value: max value of current in [A] on specific channel
        """
        self.__validate_channel_index(channel)
        if self.OUTPUT_CURRENT_MAX < limit_value < self.OUTPUT_CURRENT_MIN:
            raise ValueError("Error: Wrong Current limit value was given")
        command_limit = f"{RigolDP832Commands.SET_OCP_LIMIT.value}{channel},{limit_value}"  # command to set current limit
        self.instrument.write(command_limit)  # send command to Rigol power supply
        self.wait_for_ps_action()  # wait for Rigol power supply to execute command

    def ocp_turn_off(self, channel: int):
        """
        Turn ON power supply OCP on channel
        :param channel: specific channel to interact with
        """
        self.__validate_channel_index(channel)
        command = f"{RigolDP832Commands.SET_OCP.value}{channel},OFF"  # command to turn OFF OCP in specific channel
        self.instrument.write(command)  # send command to Rigol power supply
        self.wait_for_ps_action()  # wait for Rigol power supply to execute command

    def ovp_status_read(self, channel: int) -> RigolDP832OutputProtectionStates:
        """
        Read status from ovp on selected channel
        :param channel: specific channel to interact with
        :return: returns ovp status
        """
        self.__validate_channel_index(channel)
        command = f"{RigolDP832Commands.READ_OVP_STATE.value}{channel}"  # command to get ovp status
        status = self.instrument.query(command)  # query instrument with command to get ovp status
        if status == f"{RigolDP832OutputProtectionStates.OFF.value}\n":
            return RigolDP832OutputProtectionStates.OFF
        elif status == f"{RigolDP832OutputProtectionStates.ON.value}\n":
            return RigolDP832OutputProtectionStates.ON
        else:
            return RigolDP832OutputProtectionStates.UNKNOWN

    def ocp_status_read(self, channel: int) -> RigolDP832OutputProtectionStates:
        """
        Read status from ocp on selected channel
        :param channel: specific channel to interact with
        :return: returns ocp status
        """
        self.__validate_channel_index(channel)
        command = f"{RigolDP832Commands.READ_OCP_STATE.value}{channel}"  # command to get ocp status
        status = self.instrument.query(command)  # query instrument with command to get ocp status
        if status == f"{RigolDP832OutputProtectionStates.OFF.value}\n":
            return RigolDP832OutputProtectionStates.OFF
        elif status == f"{RigolDP832OutputProtectionStates.ON.value}\n":
            return RigolDP832OutputProtectionStates.ON
        else:
            return RigolDP832OutputProtectionStates.UNKNOWN

    def ovp_value_get(self, channel: int) -> float:
        """
        Read value from ovp on selected channel
        :param channel: specific channel to interact with
        :return: returns ovp value in [V]
        """
        self.__validate_channel_index(channel)
        command = f"{RigolDP832Commands.GET_OVP_VALUE.value}{channel}"  # command to get ovp value
        ovp = float(self.instrument.query(command))  # query instrument with command to get ovp value
        return ovp

    def ocp_value_get(self, channel: int) -> float:
        """
        Read value from ocp on selected channel
        :param channel: specific channel to interact with
        :return: returns ocp value in [A]
        """
        self.__validate_channel_index(channel)
        command = f"{RigolDP832Commands.GET_OCP_VALUE.value}{channel}"  # command to get ocp value
        ocp = float(self.instrument.query(command))  # query instrument with command to get ocp value
        return ocp

    def channel_state_read(self, channel: int) -> RigolDP832OutputStates:
        """
        Read status from selected channel
        :param channel: specific channel to interact with
        :return: returns channel status
        """
        self.__validate_channel_index(channel)
        command = f"{RigolDP832Commands.READ_CHANNEL_STATE.value}{channel}"  # command to get channel status
        output = self.instrument.query(command)
        if output == f"{RigolDP832OutputStates.ON.value}\n":
            return RigolDP832OutputStates.ON
        elif output == f"{RigolDP832OutputStates.OFF.value}\n":
            return RigolDP832OutputStates.OFF
        else:
            return RigolDP832OutputStates.UNKNOWN

    def channel_mode_read(self, channel: int) -> RigolDP832OutputModes:
        """
        Read mode from selected channel
        :param channel: specific channel to interact with
        :return: returns channel mode
        """
        self.__validate_channel_index(channel)
        command = f"{RigolDP832Commands.READ_OUTPUT_MODE.value}{channel}"  # command to get channel mode
        mode = self.instrument.query(command)  # query instrument with command to get channel mode
        if mode == f"{RigolDP832OutputModes.CONSTANT_CURRENT.value}\n":
            return RigolDP832OutputModes.CONSTANT_CURRENT
        elif mode == f"{RigolDP832OutputModes.CONSTANT_VOLTAGE.value}\n":
            return RigolDP832OutputModes.CONSTANT_VOLTAGE
        else:
            return RigolDP832OutputModes.UNREGULATED
