import qdarkstyle as qdarkstyle
import webbrowser
import logging
import sys

from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QPixmap
from DriverThreads.RigolDP832Thread import RigolDP832Thread
from Drivers.RigolDP832.RIGOL832 import OutputProtectionStates, OutputModes, OutputStates, RigolDP832
from ui_files.ui_lab_equipment_controler import Ui_MainWindow
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QPushButton


class MainWindow(QMainWindow):
    """
    Class that inherit from generated Ui_MainWindow class.
    """
    toggle_channel = pyqtSignal(bool, int)
    toggle_ovp = pyqtSignal(bool, int, float)
    toggle_ocp = pyqtSignal(bool, int, float)
    output_voltage_changed = pyqtSignal(int, float)
    output_current_changed = pyqtSignal(int, float)
    ovp_value_changed = pyqtSignal(int, float)
    ocp_value_changed = pyqtSignal(int, float)

    LED_DISABLED_PATH = './Images/led_disabled.png'
    LED_ENABLED_PATH = './Images/led_enabled.png'
    THE_HEART_LOGO_PATH = 'Images/the_heart_logo_dark_small.png'
    BUTTON_ENABLED_STYLESHEET = 'background-color: rgb(85, 170, 127);\nborder-radius: 10px;\npadding: 5px; font: 75 9pt'
    BUTTON_DISABLED_STYLESHEET = 'background-color: #1f1d2c;\nborder-radius: 10px;\npadding: 5px; font: 75 9pt'

    RIGOL_DP832_CHANNELS_QUANTITY = 3
    PLOT_LENGTH_THRESHOLD = 28
    SET_TIMER_INTERVAL = 300  # Time in [ms]
    PLOT_INTERVAL = 200  # Time in [ms]
    RIGOL_DP832_TAB_INDEX = 1

    def __init__(self):
        super(MainWindow, self).__init__()
        """
        Class initialization
        """
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle('Lab Equipment Controller')
        self.setWindowIcon(QIcon(self.THE_HEART_LOGO_PATH))

        self.tab_array = [self.ui.tab_RigolDp832,
                          self.ui.tab_Keithley2308,
                          self.ui.tab_ItechIT,
                          self.ui.tab_RigolDS1054,
                          self.ui.tab_Multimeter,
                          self.ui.tab_Siglent]
        self.settings_tab_checkable = [self.ui.settings_check_Rigol_DP832,
                                       self.ui.settings_check_Keithley_2308,
                                       self.ui.settings_check_Itech_IT8512,
                                       self.ui.settings_check_Rigol_DS1054,
                                       self.ui.settings_check_Multimeter_34401A,
                                       self.ui.settings_check_Siglent_SDG2122X]
        self.ui.settings_check_Rigol_DP832.triggered.connect(lambda: self.tab_checkbox_state_changed(self.ui.tabWidget.indexOf(self.ui.tab_RigolDp832)))
        self.ui.settings_check_Keithley_2308.triggered.connect(lambda: self.tab_checkbox_state_changed(self.ui.tabWidget.indexOf(self.ui.tab_Keithley2308)))
        self.ui.settings_check_Itech_IT8512.triggered.connect(lambda: self.tab_checkbox_state_changed(self.ui.tabWidget.indexOf(self.ui.tab_ItechIT)))
        self.ui.settings_check_Rigol_DS1054.triggered.connect(lambda: self.tab_checkbox_state_changed(self.ui.tabWidget.indexOf(self.ui.tab_RigolDS1054)))
        self.ui.settings_check_Multimeter_34401A.triggered.connect(lambda: self.tab_checkbox_state_changed(self.ui.tabWidget.indexOf(self.ui.tab_Multimeter)))
        self.ui.settings_check_Siglent_SDG2122X.triggered.connect(lambda: self.tab_checkbox_state_changed(self.ui.tabWidget.indexOf(self.ui.tab_Siglent)))
        self.ui.actionOpen_Controller_Repository.triggered.connect(self.open_repo_controller)
        self.ui.actionOpen_Drivers_Repository.triggered.connect(self.open_repo_drivers)
        self.init_tabs()

    def init_rigoldp832(self):
        self.rigoldp832_address = 'USB0::0x1AB1::0x0E11::DP8C193604338::INSTR'
        self.rigolThread = QThread()
        self.RigolDp832Thread = RigolDP832Thread(self.RIGOL_DP832_CHANNELS_QUANTITY, self.rigoldp832_address)
        self.RigolDp832Thread.moveToThread(self.rigolThread)

        if self.RIGOL_DP832_CHANNELS_QUANTITY != self.RigolDp832Thread.Rigol.CHANNEL_MAX:
            raise ValueError("Invalid number of channels!")

        self.toggle_channel.connect(self.RigolDp832Thread.channel_toggle)
        self.toggle_ovp.connect(self.RigolDp832Thread.ovp_toggle)
        self.toggle_ocp.connect(self.RigolDp832Thread.ocp_toggle)
        self.ovp_value_changed.connect(self.RigolDp832Thread.ovp_value_changed)
        self.ocp_value_changed.connect(self.RigolDp832Thread.ocp_value_changed)
        self.output_voltage_changed.connect(self.RigolDp832Thread.voltage_value_changed)
        self.output_current_changed.connect(self.RigolDp832Thread.current_value_changed)
        self.RigolDp832Thread.measure_values_signal.connect(self.overwrite_measured_values)
        self.RigolDp832Thread.mode_read_signal.connect(self.cvcc_led_refresh)
        self.rigolThread.start()

        self.set_timer_1 = QTimer(self)
        self.set_timer_1.setInterval(self.SET_TIMER_INTERVAL)
        self.set_timer_1.timeout.connect(lambda: self.voltage_spinbox_value_changed(RigolDP832.CHANNEL_FIRST - 1))
        self.set_timer_2 = QTimer(self)
        self.set_timer_2.setInterval(self.SET_TIMER_INTERVAL)
        self.set_timer_2.timeout.connect(lambda: self.voltage_spinbox_value_changed(RigolDP832.CHANNEL_SECOND - 1))
        self.set_timer_3 = QTimer(self)
        self.set_timer_3.setInterval(self.SET_TIMER_INTERVAL)
        self.set_timer_3.timeout.connect(lambda: self.voltage_spinbox_value_changed(RigolDP832.CHANNEL_THIRD - 1))
        self.set_timers = [self.set_timer_1,
                           self.set_timer_2,
                           self.set_timer_3]

        self.channels_voltage = [self.RigolDp832Thread.channels_voltage_set_value[RigolDP832.CHANNEL_FIRST - 1],
                                 self.RigolDp832Thread.channels_voltage_set_value[RigolDP832.CHANNEL_SECOND - 1],
                                 self.RigolDp832Thread.channels_voltage_set_value[RigolDP832.CHANNEL_THIRD - 1]]
        self.voltage_spinboxes = [self.ui.doubleSpinBox_voltage_channel_1,
                                  self.ui.doubleSpinBox_voltage_channel_2,
                                  self.ui.doubleSpinBox_voltage_channel_3]
        self.channels_current = [self.RigolDp832Thread.channels_current_set_value[RigolDP832.CHANNEL_FIRST - 1],
                                 self.RigolDp832Thread.channels_current_set_value[RigolDP832.CHANNEL_SECOND - 1],
                                 self.RigolDp832Thread.channels_current_set_value[RigolDP832.CHANNEL_THIRD - 1]]
        self.current_spinboxes = [self.ui.doubleSpinBox_current_channel_1,
                                  self.ui.doubleSpinBox_current_channel_2,
                                  self.ui.doubleSpinBox_current_channel_3]
        self.ovp_spinboxes = [self.ui.doubleSpinBox_ovp_channel_1,
                              self.ui.doubleSpinBox_ovp_channel_2,
                              self.ui.doubleSpinBox_ovp_channel_3]
        self.ocp_spinboxes = [self.ui.doubleSpinBox_ocp_channel_1,
                              self.ui.doubleSpinBox_ocp_channel_2,
                              self.ui.doubleSpinBox_ocp_channel_3]
        self.voltage_measure_pushbuttons = [self.ui.pushButton_voltage_measured_values_1,
                                            self.ui.pushButton_voltage_measured_values_2,
                                            self.ui.pushButton_voltage_measured_values_3]
        self.current_measure_pushbuttons = [self.ui.pushButton_current_measured_values_1,
                                            self.ui.pushButton_current_measured_values_2,
                                            self.ui.pushButton_current_measured_values_3]
        self.power_measure_pushbuttons = [self.ui.pushButton_power_measured_values_1,
                                          self.ui.pushButton_power_measured_values_1,
                                          self.ui.pushButton_power_measured_values_1]

        self.channels_state = [False] * self.RIGOL_DP832_CHANNELS_QUANTITY
        self.channels_ovp_state = [False] * self.RIGOL_DP832_CHANNELS_QUANTITY
        self.channels_ocp_state = [False] * self.RIGOL_DP832_CHANNELS_QUANTITY
        self.channels_cvcc_labels = [self.ui.label_cvcc_1, self.ui.label_cvcc_2, self.ui.label_cvcc_3]
        self.channels_led = [self.ui.led_cvcc_1, self.ui.led_cvcc_2, self.ui.led_cvcc_3]
        self.channels_state_buttons = [self.ui.pushButton_enable_channel_1, self.ui.pushButton_enable_channel_2, self.ui.pushButton_enable_channel_3]
        self.channels_ovp_state_buttons = [self.ui.pushButton_ovp_channel_1, self.ui.pushButton_ovp_channel_2, self.ui.pushButton_ovp_channel_3]
        self.channels_ocp_state_buttons = [self.ui.pushButton_ocp_channel_1, self.ui.pushButton_ocp_channel_2, self.ui.pushButton_ocp_channel_3]
        self.ui.pushButton_enable_channel_1.clicked.connect(lambda: self.channel_toggle_button_clicked(0))
        self.ui.pushButton_enable_channel_2.clicked.connect(lambda: self.channel_toggle_button_clicked(1))
        self.ui.pushButton_enable_channel_3.clicked.connect(lambda: self.channel_toggle_button_clicked(2))
        self.ui.pushButton_ovp_channel_1.clicked.connect(lambda: self.channel_toggle_ovp_button_clicked(0))
        self.ui.pushButton_ovp_channel_2.clicked.connect(lambda: self.channel_toggle_ovp_button_clicked(1))
        self.ui.pushButton_ovp_channel_3.clicked.connect(lambda: self.channel_toggle_ovp_button_clicked(2))
        self.ui.pushButton_ocp_channel_1.clicked.connect(lambda: self.channel_toggle_ocp_button_clicked(0))
        self.ui.pushButton_ocp_channel_2.clicked.connect(lambda: self.channel_toggle_ocp_button_clicked(1))
        self.ui.pushButton_ocp_channel_3.clicked.connect(lambda: self.channel_toggle_ocp_button_clicked(2))

        self.init_rigol_ui()
        self.ui.doubleSpinBox_voltage_channel_1.valueChanged.connect(self.set_timer_1.start)
        self.ui.doubleSpinBox_voltage_channel_2.valueChanged.connect(self.set_timer_2.start)
        self.ui.doubleSpinBox_voltage_channel_3.valueChanged.connect(self.set_timer_3.start)
        self.ui.doubleSpinBox_current_channel_1.valueChanged.connect(lambda: self.current_spinbox_value_changed(0))
        self.ui.doubleSpinBox_current_channel_2.valueChanged.connect(lambda: self.current_spinbox_value_changed(1))
        self.ui.doubleSpinBox_current_channel_3.valueChanged.connect(lambda: self.current_spinbox_value_changed(2))
        self.ui.doubleSpinBox_ovp_channel_1.valueChanged.connect(lambda: self.ovp_spinbox_value_changed(0))
        self.ui.doubleSpinBox_ovp_channel_2.valueChanged.connect(lambda: self.ovp_spinbox_value_changed(1))
        self.ui.doubleSpinBox_ovp_channel_3.valueChanged.connect(lambda: self.ovp_spinbox_value_changed(2))
        self.ui.doubleSpinBox_ocp_channel_1.valueChanged.connect(lambda: self.ocp_spinbox_value_changed(0))
        self.ui.doubleSpinBox_ocp_channel_2.valueChanged.connect(lambda: self.ocp_spinbox_value_changed(1))
        self.ui.doubleSpinBox_ocp_channel_3.valueChanged.connect(lambda: self.ocp_spinbox_value_changed(2))
        self.ui.graphicsView.setLimits(yMin=-1, yMax=31)
        self.x_min_value = 2
        self.x_max_value = 28
        self.plot_time = 0
        self.plot_length = 0
        self.ui.graphicsView.setXRange(self.x_min_value, self.x_max_value)
        self.ui.graphicsView.setYRange(0, 30)
        self.channel_1_plot_voltage_values = []
        self.channel_2_plot_voltage_values = []
        self.channel_3_plot_voltage_values = []
        self.channel_1_plot_current_values = []
        self.channel_2_plot_current_values = []
        self.channel_3_plot_current_values = []
        self.plot_time_array = []
        self.plots_voltage_values_arrays = [self.channel_1_plot_voltage_values, self.channel_2_plot_voltage_values, self.channel_3_plot_voltage_values]
        self.plots_current_values_arrays = [self.channel_1_plot_current_values, self.channel_2_plot_current_values, self.channel_3_plot_current_values]
        self.ui.pushButton_voltage_measured_values_1.clicked.connect(lambda: self.toggle_voltage_plot(0))
        self.ui.pushButton_voltage_measured_values_2.clicked.connect(lambda: self.toggle_voltage_plot(1))
        self.ui.pushButton_voltage_measured_values_3.clicked.connect(lambda: self.toggle_voltage_plot(2))
        self.ui.pushButton_current_measured_values_1.clicked.connect(lambda: self.toggle_current_plot(0))
        self.ui.pushButton_current_measured_values_2.clicked.connect(lambda: self.toggle_current_plot(1))
        self.ui.pushButton_current_measured_values_3.clicked.connect(lambda: self.toggle_current_plot(2))
        self.plots_voltage_enabled = [False] * self.RIGOL_DP832_CHANNELS_QUANTITY
        self.plots_current_enabled = [False] * self.RIGOL_DP832_CHANNELS_QUANTITY
        self.plot_border_colors = ['red', 'green', 'blue', 'cyan', 'magenta', 'yellow']
        self.plot_pens_colors = ['r', 'g', 'b', 'c', 'm', 'y']

        self.plot_interval_value = self.PLOT_INTERVAL  # Time in [ms]
        self.plot_timer = QTimer(self)
        self.plot_timer.setInterval(self.plot_interval_value)
        self.plot_timer.timeout.connect(self.draw_plot)
        self.plot_timer.start()

    def init_tabs(self):
        """
        Main Window tabs initialization
        """
        for index, tab in enumerate(self.settings_tab_checkable):
            if not tab.isChecked():
                self.ui.tabWidget.setTabVisible(index+1, False)

    def open_connection_error_messagebox(self, index: int):
        """
        Open connection error QMessageBox if application can't connect to selected device
        :param index: index of device tab
        """
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowIcon(QIcon(self.THE_HEART_LOGO_PATH))
        msg.setText("Can't connect to device")
        msg.setInformativeText("Make sure device is connected and try again")
        msg.setWindowTitle("Connection Error")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Close)
        buttonY = msg.button(QMessageBox.Ok)
        buttonY.setText('Reconnect')
        result = msg.exec_()
        if result == QMessageBox.Ok:
            self.tab_checkbox_state_changed(index)
        elif result == QMessageBox.Close:
            self.settings_tab_checkable[index - 1].setChecked(False)

    def tab_checkbox_state_changed(self, index: int):
        """
        Toggle device tab when checkbox is triggered
        :param index: index value of tab in array
        """
        if self.settings_tab_checkable[index-1].isChecked():
            if index == self.RIGOL_DP832_TAB_INDEX:
                try:
                    self.init_rigoldp832()
                except ConnectionError:
                    self.open_connection_error_messagebox(index)
                    raise ConnectionError(f"Can't connect to device")
            self.ui.tabWidget.setTabVisible(index, True)
        else:
            self.ui.tabWidget.setTabVisible(index, False)

        self.ui.tabWidget.setTabVisible(0, True)
        for index, tab in enumerate(self.settings_tab_checkable):
            if tab.isChecked():
                self.ui.tabWidget.setTabVisible(0, False)

    @staticmethod
    def open_repo_controller():
        """
        Open device controller repository in web browser
        """
        webbrowser.open('https://gitlab.rndlab.online/embedded/others/lab-equipment-control')

    @staticmethod
    def open_repo_drivers():
        """
        Open drivers repository in web browser
        """
        webbrowser.open('https://gitlab.rndlab.online/embedded/drivers/lab-equipment-drivers')

    def toggle_voltage_plot(self, channel: int):
        """
        Toggle visibility of voltage plot in [V] in graph
        :param channel: specific channel to interact with
        """
        if self.plots_voltage_enabled[channel] is True:
            self.plots_voltage_enabled[channel] = False
            self.voltage_measure_pushbuttons[channel].setStyleSheet("border : 3px solid #1f1d2c;\
                                                                    color: rgb(250, 250, 250);\
                                                                    background-color: #262837;\
                                                                    border-radius: 5px;\
                                                                    padding: 1px;")
        else:
            self.plots_voltage_enabled[channel] = True
            self.voltage_measure_pushbuttons[channel].setStyleSheet(f"border : 3px solid #1f1d2c;\
                                                                    color: rgb(250, 250, 250);\
                                                                    background-color: #262837;\
                                                                    border-radius: 5px;\
                                                                    border-color: {self.plot_border_colors[channel]};\
                                                                    padding: 1px;")

    def toggle_current_plot(self, channel: int):
        """
        Toggle visibility of current plot in [A] in graph
        :param channel: specific channel to interact with
        """
        if self.plots_current_enabled[channel] is True:
            self.plots_current_enabled[channel] = False
            self.current_measure_pushbuttons[channel].setStyleSheet("border : 3px solid #1f1d2c;\
                                                                    color: rgb(250, 250, 250);\
                                                                    background-color: #262837;\
                                                                    border-radius: 5px;\
                                                                    padding: 1px;")
        else:
            self.plots_current_enabled[channel] = True
            self.current_measure_pushbuttons[channel].setStyleSheet(f"border : 3px solid #1f1d2c;\
                                                                    color: rgb(250, 250, 250);\
                                                                    background-color: #262837;\
                                                                    border-radius: 5px;\
                                                                    border-color: {self.plot_border_colors[3+channel]};\
                                                                    padding: 1px;")

    def draw_plot(self):
        """
        Draw all selected plots in graph
        """
        self.ui.graphicsView.clear()
        self.plot_time_array.append(self.RigolDp832Thread.timestamp)
        self.plot_length += self.plot_time_array[len(self.plot_time_array)-1] - self.plot_time_array[len(self.plot_time_array)-2]
        for i in range(self.RIGOL_DP832_CHANNELS_QUANTITY):
            voltage = self.RigolDp832Thread.channels_voltage[i]
            self.plots_voltage_values_arrays[i].append(voltage)
            if self.plots_voltage_enabled[i] is True:
                x = self.plot_time_array
                y = self.plots_voltage_values_arrays[i]
                self.ui.graphicsView.plot(x, y, pen=self.plot_pens_colors[i], name=f"Channel {i+1} Voltage")

            current = self.RigolDp832Thread.channels_current[i]
            self.plots_current_values_arrays[i].append(current)
            if self.plots_current_enabled[i] is True:
                x = self.plot_time_array
                y = self.plots_current_values_arrays[i]
                self.ui.graphicsView.plot(x, y, pen=self.plot_pens_colors[3+i], name=f"Channel {i+1} Voltage")

        if self.plot_length > self.PLOT_LENGTH_THRESHOLD:
            value = self.plot_time_array[len(self.plot_time_array)-1] - self.plot_time_array[len(self.plot_time_array)-2]
            self.x_min_value += value
            self.x_max_value += value
            self.ui.graphicsView.setXRange(self.x_min_value - 2, self.x_max_value + 2)

    def init_rigol_ui(self):
        """
        Rigol DP832 UI elements initialization
        """
        self.cvcc_led_refresh()

        for index, box in enumerate(self.voltage_spinboxes):
            box.setValue(self.channels_voltage[index])

        for index, box in enumerate(self.current_spinboxes):
            box.setValue(self.channels_current[index])

        for i in range(self.RIGOL_DP832_CHANNELS_QUANTITY):
            if self.RigolDp832Thread.output_status_read(i) == OutputStates.ON:
                self.channels_state[i] = True
            if self.channels_state[i] is True:
                self.channels_state_buttons[i].setStyleSheet(
                    "background-color: rgb(85, 170, 127);\nborder-radius: 10px;\npadding: 10px; font: 75 11pt")
                self.channels_state_buttons[i].setText(OutputStates.ON.value)

            if self.RigolDp832Thread.ovp_status_read(i) == OutputProtectionStates.ON:
                self.channels_ovp_state[i] = True
            if self.channels_ovp_state[i] is True:
                self.channels_ovp_state_buttons[i].setStyleSheet(self.BUTTON_ENABLED_STYLESHEET)
                self.channels_ovp_state_buttons[i].setText(OutputProtectionStates.ON.value)

            if self.RigolDp832Thread.ocp_status_read(i) == OutputProtectionStates.ON:
                self.channels_ocp_state[i] = True
            if self.channels_ocp_state[i] is True:
                self.channels_ocp_state_buttons[i].setStyleSheet(self.BUTTON_ENABLED_STYLESHEET)
                self.channels_ocp_state_buttons[i].setText(OutputProtectionStates.ON.value)
            self.ovp_spinboxes[i].setValue(self.RigolDp832Thread.ovp_value_read(i))
            self.ocp_spinboxes[i].setValue(self.RigolDp832Thread.ocp_value_read(i))

    def cvcc_led_refresh(self):
        """
        Check if output mode of all channels changed
        """
        for i in range(self.RIGOL_DP832_CHANNELS_QUANTITY):
            if self.RigolDp832Thread.channels_mode[i] == OutputModes.CONSTANT_VOLTAGE:
                self.channels_led[i].setPixmap(QPixmap(self.LED_DISABLED_PATH))
                self.channels_cvcc_labels[i].setText(OutputModes.CONSTANT_VOLTAGE.value)
            else:
                self.channels_led[i].setPixmap(QPixmap(self.LED_ENABLED_PATH))
                self.channels_cvcc_labels[i].setText(OutputModes.CONSTANT_CURRENT.value)

    def channel_toggle_button_clicked(self, channel: int):
        """
        Toggle channel output
        :param channel: specific channel to interact with
        """
        if self.channels_state[channel] is False:
            if self.channels_ovp_state[channel] and \
                    self.RigolDp832Thread.output_voltage_value_get(channel) > \
                    self.RigolDp832Thread.ovp_value_read(channel):
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowIcon(QIcon(self.THE_HEART_LOGO_PATH))
                msg.setText("Output voltage is greater than OVP limit")
                msg.setInformativeText("Do you want to continue and disable OVP?")
                msg.setWindowTitle("OVP limit WARNING")
                msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                result = msg.exec_()
                if result == QMessageBox.Ok:
                    self.channel_toggle_ovp_button_clicked(channel)
                    self.channel_toggle_button_clicked(channel)
            else:
                if self.channels_ocp_state[channel] and \
                        self.RigolDp832Thread.output_current_value_get(channel) > \
                        self.RigolDp832Thread.ocp_value_read(channel):
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setWindowIcon(QIcon(self.THE_HEART_LOGO_PATH))
                    msg.setText("Output current is greater than OCP limit")
                    msg.setInformativeText("Do you want to continue and disable OCP?")
                    msg.setWindowTitle("OCP limit WARNING")
                    msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                    result = msg.exec_()
                    if result == QMessageBox.Ok:
                        self.channel_toggle_ocp_button_clicked(channel)
                        self.channel_toggle_button_clicked(channel)
                else:
                    self.channels_state_buttons[channel].setStyleSheet("background-color: rgb(85, 170, 127);\nborder-radius: 10px;\npadding: 10px; font: 75 11pt")
                    self.channels_state_buttons[channel].setText(OutputStates.ON.value)
                    self.channels_state[channel] = True
                    self.toggle_channel.emit(True, channel+1)
        else:
            self.channels_state_buttons[channel].setStyleSheet("background-color: #1f1d2c;\nborder-radius: 10px;\npadding: 10px; font: 75 11pt")
            self.channels_state_buttons[channel].setText(OutputStates.OFF.value)
            self.channels_state[channel] = False
            self.toggle_channel.emit(False, channel+1)

    def channel_toggle_ovp_button_clicked(self, channel: int):
        """
        Toggle channel OVP
        :param channel: specific channel to interact with
        """
        if self.channels_ovp_state[channel] is False:
            if self.channels_state[channel] and \
                    self.RigolDp832Thread.output_voltage_value_get(channel) > \
                    self.ovp_spinboxes[channel].value():
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowIcon(QIcon(self.THE_HEART_LOGO_PATH))
                msg.setText("Requested OVP limit is lower than output voltage")
                msg.setInformativeText("Do you want to continue and disable channel?")
                msg.setWindowTitle("OVP limit WARNING")
                msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                result = msg.exec_()
                if result == QMessageBox.Ok:
                    self.channel_toggle_button_clicked(channel)
                    self.channels_ovp_state_buttons[channel].setStyleSheet(self.BUTTON_ENABLED_STYLESHEET)
                    self.channels_ovp_state_buttons[channel].setText(OutputProtectionStates.ON.value)
                    self.channels_ovp_state[channel] = True
                    self.toggle_ovp.emit(True, channel+1, self.ovp_spinboxes[channel].value())
            else:
                self.channels_ovp_state_buttons[channel].setStyleSheet(self.BUTTON_ENABLED_STYLESHEET)
                self.channels_ovp_state_buttons[channel].setText(OutputProtectionStates.ON.value)
                self.channels_ovp_state[channel] = True
                self.toggle_ovp.emit(True, channel + 1, self.ovp_spinboxes[channel].value())
        else:
            self.channels_ovp_state_buttons[channel].setStyleSheet(self.BUTTON_DISABLED_STYLESHEET)
            self.channels_ovp_state_buttons[channel].setText(OutputProtectionStates.OFF.value)
            self.channels_ovp_state[channel] = False
            self.toggle_ovp.emit(False, channel+1, self.ovp_spinboxes[channel].value())

    def channel_toggle_ocp_button_clicked(self, channel: int):
        """
        Toggle channel OCP
        :param channel: specific channel to interact with
        """
        if self.channels_ocp_state[channel] is False:
            if self.channels_state[channel] and \
                    self.RigolDp832Thread.output_current_value_get(channel) > \
                    self.ocp_spinboxes[channel].value():
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowIcon(QIcon(self.THE_HEART_LOGO_PATH))
                msg.setText("Requested OCP limit is lower than output current")
                msg.setInformativeText("Do you want to continue and disable channel?")
                msg.setWindowTitle("OCP limit WARNING")
                msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                result = msg.exec_()
                if result == QMessageBox.Ok:
                    self.channel_toggle_button_clicked(channel)
                    self.channels_ocp_state_buttons[channel].setStyleSheet(self.BUTTON_ENABLED_STYLESHEET)
                    self.channels_ocp_state_buttons[channel].setText(OutputProtectionStates.ON.value)
                    self.channels_ocp_state[channel] = True
                    self.toggle_ocp.emit(True, channel+1, self.ocp_spinboxes[channel].value())
            else:
                self.channels_ocp_state_buttons[channel].setStyleSheet(self.BUTTON_ENABLED_STYLESHEET)
                self.channels_ocp_state_buttons[channel].setText(OutputProtectionStates.ON.value)
                self.channels_ocp_state[channel] = True
                self.toggle_ocp.emit(True, channel + 1, self.ocp_spinboxes[channel].value())
        else:
            self.channels_ocp_state_buttons[channel].setStyleSheet(self.BUTTON_DISABLED_STYLESHEET)
            self.channels_ocp_state_buttons[channel].setText(OutputProtectionStates.OFF.value)
            self.channels_ocp_state[channel] = False
            self.toggle_ocp.emit(False, channel+1, self.ocp_spinboxes[channel].value())

    def voltage_spinbox_value_changed(self, channel: int):
        """
        Change value of voltage in [V] in channel output
        :param channel: specific channel to interact with
        """
        self.set_timers[channel].stop()
        voltage = self.voltage_spinboxes[channel].value()

        if self.channels_ovp_state[channel] and voltage > self.RigolDp832Thread.ovp_value_read(channel):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowIcon(QIcon(self.THE_HEART_LOGO_PATH))
            msg.setText("Requested output voltage is greater than OVP limit")
            msg.setInformativeText("Do you want to continue and disable OVP?")
            msg.setWindowTitle("OVP limit WARNING")
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            result = msg.exec_()
            if result == QMessageBox.Ok:
                self.channel_toggle_ovp_button_clicked(channel)
                self.output_voltage_changed.emit(channel + 1, voltage)
            else:
                self.voltage_spinboxes[channel].setValue(self.voltage_spinboxes[channel].value() - 1)
                self.voltage_spinbox_value_changed(channel)
        else:
            self.output_voltage_changed.emit(channel + 1, voltage)

    def current_spinbox_value_changed(self, channel: int):
        """
        Change value of current in [A] in channel output
        :param channel: specific channel to interact with
        """
        current = self.current_spinboxes[channel].value()

        if self.channels_ocp_state[channel] and current > self.RigolDp832Thread.ocp_value_read(channel):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowIcon(QIcon(self.THE_HEART_LOGO_PATH))
            msg.setText("Requested output current is greater than OCP limit")
            msg.setInformativeText("Do you want to continue and disable OCP?")
            msg.setWindowTitle("OCP limit WARNING")
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            result = msg.exec_()
            if result == QMessageBox.Ok:
                self.channel_toggle_ocp_button_clicked(channel)
                self.output_current_changed.emit(channel + 1, current)
            else:
                self.current_spinboxes[channel].setValue(self.current_spinboxes[channel].value() - .2)
                self.current_spinbox_value_changed(channel)
        else:
            self.output_current_changed.emit(channel+1, current)

    def ovp_spinbox_value_changed(self, channel: int):
        """
        Change value of OVP in channel output
        :param channel: specific channel to interact with
        """
        limit = self.ovp_spinboxes[channel].value()
        if self.channels_ovp_state[channel] and \
                self.channels_state[channel] and \
                limit < self.RigolDp832Thread.output_voltage_value_get(channel):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowIcon(QIcon(self.THE_HEART_LOGO_PATH))
            msg.setText("Requested OVP limit is lower than output voltage")
            msg.setInformativeText("Do you want to continue and disable channel?")
            msg.setWindowTitle("OVP limit WARNING")
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            result = msg.exec_()
            if result == QMessageBox.Ok:
                self.channel_toggle_button_clicked(channel)
                self.ovp_value_changed.emit(channel + 1, limit)
            else:
                self.ovp_spinboxes[channel].setValue(limit + 1)
                self.ovp_spinbox_value_changed(channel)
        else:
            self.ovp_value_changed.emit(channel+1, limit)

    def ocp_spinbox_value_changed(self, channel: int):
        """
        Change value of OCP in channel output
        :param channel: specific channel to interact with
        """
        limit = self.ocp_spinboxes[channel].value()
        if self.channels_ocp_state[channel] and \
                self.channels_state[channel] and \
                limit < self.RigolDp832Thread.output_voltage_value_get(channel):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowIcon(QIcon(self.THE_HEART_LOGO_PATH))
            msg.setText("Requested OCP limit is lower than output current")
            msg.setInformativeText("Do you want to continue and disable channel?")
            msg.setWindowTitle("OCP limit WARNING")
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            result = msg.exec_()
            if result == QMessageBox.Ok:
                self.channel_toggle_button_clicked(channel)
                self.ocp_value_changed.emit(channel + 1, limit)
            else:
                self.ocp_spinboxes[channel].setValue(limit + 1)
                self.ocp_spinbox_value_changed(channel)
        else:
            self.ocp_value_changed.emit(channel + 1, limit)

    def overwrite_measured_values(self):
        """
        Read values of Rigol DP832 thread object and overwrite it to ui elements
        """
        for i in range(self.RIGOL_DP832_CHANNELS_QUANTITY):
            self.voltage_measure_pushbuttons[i].setText(f"{self.RigolDp832Thread.channels_voltage[i]} V")
            self.current_measure_pushbuttons[i].setText(f"{self.RigolDp832Thread.channels_current[i]} A")
            self.power_measure_pushbuttons[i].setText(f"{self.RigolDp832Thread.channels_power[i]} W")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    logging.warning('Starting Application')
    app.setStyleSheet(qdarkstyle.load_stylesheet())
    myapp = MainWindow()
    myapp.show()

    sys.exit(app.exec_())
