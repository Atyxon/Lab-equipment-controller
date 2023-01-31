import ctypes
from enum import Enum

from picosdk.usbtc08 import usbtc08 as tc08
from picosdk.functions import assert_pico2000_ok


class PicoInputTypes(Enum):
    """
    Enum class with Pico TC-08 input types
    """
    OUTPUT_MODE_DISABLED = 32
    OUTPUT_MODE_TYPE_B = 66
    OUTPUT_MODE_TYPE_E = 69
    OUTPUT_MODE_TYPE_J = 74
    OUTPUT_MODE_TYPE_K = 75
    OUTPUT_MODE_TYPE_N = 78
    OUTPUT_MODE_TYPE_R = 82
    OUTPUT_MODE_TYPE_S = 83
    OUTPUT_MODE_TYPE_T = 84
    OUTPUT_MODE_TYPE_X = 88


class TempUnits(Enum):
    """
    Enum class with temperature units supported by Pico TC-08
    """
    UNIT_CELCIUS = 'USBTC08_UNITS_CENTIGRADE'
    UNIT_FAHRENHEIT = 'USBTC08_UNITS_FAHRENHEIT'
    UNIT_KELVIN = 'USBTC08_UNITS_KELVIN'
    UNIT_RANKINE = 'USBTC08_UNITS_RANKINE'


class PicoTC08:
    """
    Class for controlling Pico TC-08
    """
    CHANNEL_FIRST = 1  # First channel of Pico TC-08
    CHANNEL_SECOND = 2  # Second channel of Pico TC-08
    CHANNEL_THIRD = 3  # Third channel of Pico TC-08
    CHANNEL_FOURTH = 4  # Fourth channel of Pico TC-08
    CHANNEL_FIFTH = 5  # Fifth channel of Pico TC-08
    CHANNEL_SIXTH = 6  # Sixth channel of Pico TC-08
    CHANNEL_SEVENTH = 7  # Seventh channel of Pico TC-08
    CHANNEL_EIGHTH = 8  # Eighth channel of Pico TC-08
    CHANNEL_MIN = CHANNEL_FIRST  # Min channel range value
    CHANNEL_MAX = CHANNEL_EIGHTH  # Max channel range value

    def __init__(self):
        self.chandle = ctypes.c_int16()
        self.status = {"open_unit": tc08.usb_tc08_open_unit()}
        assert_pico2000_ok(self.status["open_unit"])
        self.chandle = self.status["open_unit"]

        # set mains rejection to 50 Hz
        self.status["set_mains"] = tc08.usb_tc08_set_mains(self.chandle, 0)
        assert_pico2000_ok(self.status["set_mains"])

        self.temp = (ctypes.c_float * 9)()
        self.overflow = ctypes.c_int16(0)
        self.units = tc08.USBTC08_UNITS[TempUnits.UNIT_CELCIUS.value]

    def __validate_channel_index(self, channel: int):
        """
        Valiate if channel index is within range
        :param channel: specific channel to interact with
        """
        if self.CHANNEL_MAX < channel < self.CHANNEL_MIN:
            raise ValueError(f"Error: Channel index out of range [{self.CHANNEL_MIN};{self.CHANNEL_MAX}]")

    def temp_unit_set(self, unit: TempUnits):
        """
        Set Pico TC-08 temperature unit
        :param unit: temperature unit to be used
        """
        self.units = tc08.USBTC08_UNITS[unit.value]

    def single_temp_read(self, channel: int) -> float:
        """
        Read temperature on selected channel
        :param channel: channel to interact with
        """
        self.__validate_channel_index(channel)

        self.channel_enable(channel)
        self.status["get_single"] = tc08.usb_tc08_get_single(self.chandle, ctypes.byref(self.temp), ctypes.byref(self.overflow), self.units)
        assert_pico2000_ok(self.status["get_single"])
        return self.temp[channel]

    def all_temp_read(self) -> [float]:
        """
        Read temperature on selected channel
        :return: array of measured temperature of all channels
        """
        self.all_channel_enable()
        self.status["get_single"] = tc08.usb_tc08_get_single(self.chandle, ctypes.byref(self.temp), ctypes.byref(self.overflow), self.units)
        assert_pico2000_ok(self.status["get_single"])
        temperature = [0] * (self.CHANNEL_MAX + self.CHANNEL_MIN)
        temperature[self.CHANNEL_FIRST] = self.temp[self.CHANNEL_FIRST]
        temperature[self.CHANNEL_SECOND] = self.temp[self.CHANNEL_SECOND]
        temperature[self.CHANNEL_THIRD] = self.temp[self.CHANNEL_THIRD]
        temperature[self.CHANNEL_FOURTH] = self.temp[self.CHANNEL_FOURTH]
        temperature[self.CHANNEL_FIFTH] = self.temp[self.CHANNEL_FIFTH]
        temperature[self.CHANNEL_SIXTH] = self.temp[self.CHANNEL_SIXTH]
        temperature[self.CHANNEL_SEVENTH] = self.temp[self.CHANNEL_SEVENTH]
        temperature[self.CHANNEL_EIGHTH] = self.temp[self.CHANNEL_EIGHTH]
        return temperature

    def return_status(self):
        """
        Return status of Pico TC-08
        :return: Status of Pico TC-08
        """
        return self.status

    def channel_enable(self, channel: int, input_type: PicoInputTypes = PicoInputTypes.OUTPUT_MODE_TYPE_K):
        """
        Enable selected channel of Pico TC-08
        :param input_type: input type to be set on Pico TC-08 channel
        :param channel: Channel to interact with
        """
        self.__validate_channel_index(channel)

        type = ctypes.c_int8(input_type.value)
        self.status["set_channel"] = tc08.usb_tc08_set_channel(self.chandle, channel, type)
        assert_pico2000_ok(self.status["set_channel"])

    def channel_disable(self, channel: int):
        """
        Disable selected channel of Pico TC-08
        :param channel: Channel to interact with
        """
        self.__validate_channel_index(channel)

        Disable = ctypes.c_int8(PicoInputTypes.OUTPUT_MODE_DISABLED.value)
        self.status["set_channel"] = tc08.usb_tc08_set_channel(self.chandle, channel, Disable)
        assert_pico2000_ok(self.status["set_channel"])

    def all_channel_enable(self):
        """
        Enable all channels of Pico TC-08
        """
        typeK = ctypes.c_int8(PicoInputTypes.OUTPUT_MODE_TYPE_K.value)
        self.status["set_channel"] = tc08.usb_tc08_set_channel(self.chandle, self.CHANNEL_FIRST, typeK)
        self.status["set_channel"] = tc08.usb_tc08_set_channel(self.chandle, self.CHANNEL_SECOND, typeK)
        self.status["set_channel"] = tc08.usb_tc08_set_channel(self.chandle, self.CHANNEL_THIRD, typeK)
        self.status["set_channel"] = tc08.usb_tc08_set_channel(self.chandle, self.CHANNEL_FOURTH, typeK)
        self.status["set_channel"] = tc08.usb_tc08_set_channel(self.chandle, self.CHANNEL_FIFTH, typeK)
        self.status["set_channel"] = tc08.usb_tc08_set_channel(self.chandle, self.CHANNEL_SIXTH, typeK)
        self.status["set_channel"] = tc08.usb_tc08_set_channel(self.chandle, self.CHANNEL_SEVENTH, typeK)
        self.status["set_channel"] = tc08.usb_tc08_set_channel(self.chandle, self.CHANNEL_EIGHTH, typeK)
        assert_pico2000_ok(self.status["set_channel"])

    def all_channel_disable(self):
        """
        Disable all channels of Pico TC-08
        """
        Disable = ctypes.c_int8(PicoInputTypes.OUTPUT_MODE_DISABLED.value)
        self.status["set_channel"] = tc08.usb_tc08_set_channel(self.chandle, self.CHANNEL_FIRST,  Disable)
        self.status["set_channel"] = tc08.usb_tc08_set_channel(self.chandle, self.CHANNEL_SECOND, Disable)
        self.status["set_channel"] = tc08.usb_tc08_set_channel(self.chandle, self.CHANNEL_THIRD,  Disable)
        self.status["set_channel"] = tc08.usb_tc08_set_channel(self.chandle, self.CHANNEL_FOURTH, Disable)
        self.status["set_channel"] = tc08.usb_tc08_set_channel(self.chandle, self.CHANNEL_FIFTH,  Disable)
        self.status["set_channel"] = tc08.usb_tc08_set_channel(self.chandle, self.CHANNEL_SIXTH,  Disable)
        self.status["set_channel"] = tc08.usb_tc08_set_channel(self.chandle, self.CHANNEL_SEVENTH, Disable)
        self.status["set_channel"] = tc08.usb_tc08_set_channel(self.chandle, self.CHANNEL_EIGHTH, Disable)
        assert_pico2000_ok(self.status["set_channel"])

    def minimum_interval_get(self) -> int:
        """
        Get minimum interval value in [ms]
        :return: Minimum interval in [ms]
        """
        self.status["get_minimum_interval_ms"] = tc08.usb_tc08_get_minimum_interval_ms(self.chandle)
        return self.status["get_minimum_interval_ms"]

    def __del__(self):
        self.status["close_unit"] = tc08.usb_tc08_close_unit(self.chandle)
        assert_pico2000_ok(self.status["close_unit"])
