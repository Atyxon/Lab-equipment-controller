import sys
from PyQt5.QtWidgets import QApplication
from Keithley2308.Keithley2308 import Keithley2308, KeithleyCurrentMeasRange, Keithley2308RelayState

if __name__ == "__main__":
    app = QApplication(sys.argv)

    Keithley = Keithley2308()
    Keithley.batt_sim_turn_on()  # Turn ON battery simulator
    Keithley.batt_sim_turn_off()  # Turn OFF battery simulator
    Keithley.triger_continuous_mode_enable()  # Enable trigger continuous mode on battery sim channel to speed up measurements
    Keithley.triger_continuous_mode_disable()  # Disable trigger continuous mode on battery sim channel
    Keithley.simulator_reset()  # Returns the simulator to the *RST default conditions
    Keithley.batt_sim_current_meas_range_set(KeithleyCurrentMeasRange.RANGE_5_MA)  # Set battery simulator current measurement range to 5mA
    Keithley.batt_sim_voltage_amplitude_set(2)  # Set battery simulator voltage amplitude to 2V
    Keithley.batt_sim_current_limit_set(1)  # Set battery simulator current limit to 1A
    Keithley.batt_sim_bandwidth_set_low()  # Set device battery bandwidth to LOW
    Keithley.batt_sim_bandwidth_set_high()  # Set device battery bandwidth to HIGH
    Keithley.batt_sim_output_impedance_set(.7)  # Set impedance of battery sim to 0.7Ω
    Keithley.batt_sim_readback_function_select_voltage()  # Select readback function to VOLTAGE
    Keithley.batt_sim_readback_function_select_current()  # Select readback function to CURRENT
    Keithley.batt_sim_integration_rate_set(9)  # Set battery simulator integration rate for voltage and current to 9
    Keithley.batt_sim_average_count_volt_curr_set(3)  # Set average count value for voltage and current measurements to 3
    Keithley.relays_control(1, Keithley2308RelayState.RELAY_CIRCUIT_OPEN)  # Open first relay circuit
    print(Keithley.measure_battery_sim_current())  # Measure current in [A] value of battery sim channel
    print(Keithley.batt_sim_status_read())  # Read and return status of battery simulator
    print(Keithley.sim_error_read())  # Read and return error of simulator
    print(Keithley.batt_sim_trigger_and_return_reading())  # Trigger and return one reading for battery channel
    print(Keithley.batt_sim_trigger_and_return_readings_array())  # Trigger and return array of readings for battery channel

    sys.exit(app.exec_())
