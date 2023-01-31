import time

from PyQt5.QtCore import QObject, pyqtSignal, QMutex, QTimer
from Drivers.RigolDP832.RIGOL832 import RigolDP832, OutputModes, OutputStates, OutputProtectionStates


class RigolDP832Thread(QObject):
    """
    Class responsible for Rigol DP832 thread
    """
    measure_values_signal = pyqtSignal()  # Signal used to send information about measured output values
    mode_read_signal = pyqtSignal()  # Signal used to send information about output mode

    mutex = QMutex()  # Mutex used to prevent Rigol DP832 thread functions overlaping

    MEASURE_VALUES_INTERVAL = 300  # Time in [ms]
    READ_MODE_INTERVAL = 2000  # Time in [ms]

    def __init__(self, channels_quantity: int, address='USB0::0x1AB1::0x0E11::DP8C193604338::INSTR'):
        """
        Class initialization
        """
        super(RigolDP832Thread, self).__init__()
        if channels_quantity != RigolDP832.CHANNEL_MAX:
            raise Exception("Invalid number of channels")

        self.channels_quantity = channels_quantity
        self.Rigol = RigolDP832(address)
        self.channels_voltage = [0] * self.channels_quantity
        self.channels_current = [0] * self.channels_quantity
        self.channels_power = [0] * self.channels_quantity
        self.channels_voltage_set_value = [self.Rigol.output_voltage_value_get(self.Rigol.CHANNEL_FIRST),
                                           self.Rigol.output_voltage_value_get(self.Rigol.CHANNEL_SECOND),
                                           self.Rigol.output_voltage_value_get(self.Rigol.CHANNEL_THIRD)]
        self.channels_current_set_value = [self.Rigol.output_current_value_get(self.Rigol.CHANNEL_FIRST),
                                           self.Rigol.output_current_value_get(self.Rigol.CHANNEL_SECOND),
                                           self.Rigol.output_current_value_get(self.Rigol.CHANNEL_THIRD)]
        self.timestamp = 0
        self.channels_mode = [OutputModes.UNREGULATED, OutputModes.UNREGULATED, OutputModes.UNREGULATED]

        self.check_thread_timer = QTimer(self)
        self.check_thread_timer.setInterval(self.MEASURE_VALUES_INTERVAL)
        self.check_thread_timer.timeout.connect(self.measure_values)
        self.check_thread_timer.start()

        self.mode_measure_timer = QTimer(self)
        self.mode_measure_timer.setInterval(self.READ_MODE_INTERVAL)
        self.mode_measure_timer.timeout.connect(self.measure_output_mode)
        self.mode_measure_timer.start()

        self.time_start = time.time()

    def channel_toggle(self, toggle: bool, channel: int):
        """
        Toggle power supply channel
        :param toggle: set power supply state
        :param channel: specific channel to interact with
        """

        self.mutex.lock()
        if toggle is True:
            self.Rigol.channel_turn_on(channel)
        else:
            self.Rigol.channel_turn_off(channel)

        self.mutex.unlock()

    def ovp_toggle(self, toggle: bool, channel: int):
        """
        Toggle power supply OVP
        :param toggle: set OVP state
        :param channel: specific channel to interact with
        """
        self.mutex.lock()

        if toggle is True:
            self.Rigol.ovp_turn_on(channel)
        else:
            self.Rigol.ovp_turn_off(channel)

        self.mutex.unlock()

    def ocp_toggle(self, toggle: bool, channel: int):
        """
        Toggle power supply OCP
        :param toggle: set OCP state
        :param channel: specific channel to interact with
        """
        self.mutex.lock()

        if toggle is True:
            self.Rigol.ocp_turn_on(channel)
        else:
            self.Rigol.ocp_turn_off(channel)

        self.mutex.unlock()

    def voltage_value_changed(self, channel: int, voltage: float):
        """
        Triggered when voltage spinbox value changed
        :param channel: specific channel to interact with
        :param voltage: value to be set as output voltage in [V]
        """
        self.mutex.lock()
        self.Rigol.output_voltage_set(channel, voltage)
        self.mutex.unlock()

    def current_value_changed(self, channel: int, current: float):
        """
        Triggered when current spinbox value changed
        :param channel: specific channel to interact with
        :param current: value to be set as output current in [A]
        """
        self.mutex.lock()
        self.Rigol.output_current_set(channel, current)
        self.mutex.unlock()

    def ovp_value_changed(self, channel: int, voltage: float):
        """
        Triggered when OVP spinbox value changed
        :param channel: specific channel to interact with
        :param voltage: value to be set as OVP in [V]
        """
        self.mutex.lock()
        self.Rigol.ovp_value_set(channel, voltage)
        self.mutex.unlock()

    def ocp_value_changed(self, channel: int, current: float):
        """
        Triggered when OCP spinbox value changed
        :param channel: specific channel to interact with
        :param current: value to be set as OCP in [A]
        """
        self.mutex.lock()
        self.Rigol.ocp_value_set(channel, current)
        self.mutex.unlock()

    def measure_values(self):
        """
        Measure values of all channels and store them in variables
        """
        self.mutex.lock()

        for i in range(self.channels_quantity):
            measurements = self.Rigol.measure_all_values(i+1)
            self.channels_voltage[i] = measurements.voltage
            self.channels_current[i] = measurements.current
            self.channels_power[i] = measurements.power

        self.timestamp = round(time.time() - self.time_start, 5)  # Rounding to 0.1 ms
        self.measure_values_signal.emit()
        self.mutex.unlock()

    def measure_output_mode(self):
        """
        Read output mode of all channels
        """
        self.mutex.lock()

        for i in range(self.channels_quantity):
            mode = self.Rigol.channel_mode_read(i+1)
            if mode != self.channels_mode[i]:
                self.channels_mode[i] = mode
                self.mode_read_signal.emit()

        self.mutex.unlock()

    def output_status_read(self, index: int) -> OutputStates:
        """
        Read output status of selected channel
        :param index: index of channel to interact with
        :return: state of selected channel output
        """
        self.mutex.lock()

        status = self.Rigol.channel_status_read(index+1)
        if status == f"{OutputStates.ON.value}\n":

            self.mutex.unlock()
            return OutputStates.ON
        else:

            self.mutex.unlock()
            return OutputStates.OFF

    def ovp_status_read(self, index: int) -> OutputProtectionStates:
        """
        Read OVP status of selected channel
        :param index: index of channel to interact with
        :return: state of selected channel OVP
        """
        self.mutex.lock()

        status = self.Rigol.ovp_status_read(index+1)

        self.mutex.unlock()
        return status

    def ocp_status_read(self, index: int) -> OutputProtectionStates:
        """
        Read OCP status of selected channel
        :param index: index of channel to interact with
        :return: state of selected channel OCP
        """
        self.mutex.lock()

        status = self.Rigol.ocp_status_read(index+1)

        self.mutex.unlock()
        return status

    def ovp_value_read(self, index: int) -> float:
        """
        Read OVP value in [V] of selected channel
        :param index: index of channel to interact with
        :return: value of selected channel OVP in [V]
        """
        self.mutex.lock()

        voltage = self.Rigol.ovp_value_get(index+1)

        self.mutex.unlock()
        return voltage

    def ocp_value_read(self, index: int) -> float:
        """
        Read OCP in [A] value of selected channel
        :param index: index of channel to interact with
        :return: value of selected channel OCP in [A]
        """
        self.mutex.lock()

        current = self.Rigol.ocp_value_get(index+1)

        self.mutex.unlock()
        return current

    def output_voltage_value_get(self, index: int) -> float:
        """
        Get output voltege value in [V] of selected channel
        :param index: index of channel to interact with
        :return: output voltage in [V] of selected channel
        """
        self.mutex.lock()

        voltage = self.Rigol.output_voltage_value_get(index+1)

        self.mutex.unlock()
        return voltage

    def output_current_value_get(self, index: int) -> float:
        """
        Get output current value in [A] of selected channel
        :param index: index of channel to interact with
        :return: output current in [A] of selected channel
        """
        self.mutex.lock()

        current = self.Rigol.output_current_value_get(index+1)

        self.mutex.unlock()
        return current
