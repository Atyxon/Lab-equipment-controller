from RigolDP832.RIGOL832 import RigolDP832

if __name__ == "__main__":
    Rigol = RigolDP832()  # Create instance of Rigol DP832
    Rigol.channel_turn_on(1)  # Turn ON power supply channel [1]
    Rigol.channel_turn_off(1)  # Turn OFF power supply channel [1]
    Rigol.register_status(1)  # Register status of channel in list as string
    Rigol.output_voltage_set(1, 15)  # Set power supply output voltage to 15V on channel [1]
    print(Rigol.output_voltage_measure(1))  # Get power supply output voltage on channel [1]
    Rigol.output_current_set(1, 3)  # Set power supply output current to 3A on channel [1]
    print(Rigol.output_current_measure(1))  # Get power supply output current on channel [1]
    print(Rigol.output_voltage_value_get(1))  # Get power supply output voltage of channel [1]
    print(Rigol.output_current_value_get(1))  # Get power supply output current of channel [1]
    print(Rigol.measure_all_values(1))  # Measure voltage in [V], current in [A], and power in [W] on specified channel
    Rigol.ovp_turn_on(1)  # Turn ON power supply OVP on channel [1]
    Rigol.ovp_turn_off(1)  # Turn OFF power supply OVP on channel [1]
    Rigol.ovp_value_set(1, 12)  # Set value of OVP Voltage limit to 12V on channel [1]
    print(Rigol.ovp_value_get(1))  # Read value from OVP on channel [1]
    print(Rigol.ovp_status_read(1))  # Read status from OVP on channel [1]
    Rigol.ocp_turn_on(1)  # Turn ON power supply OCP on channel [1]
    Rigol.ocp_turn_off(1)  # Turn OFF power supply OCP on channel [1]
    Rigol.ocp_value_set(1, 12)  # Set value of OCP Voltage limit to 12V on channel [1]
    print(Rigol.ocp_value_get(1))  # Read value from OCP on channel [1]
    print(Rigol.ocp_status_read(1))  # Read status from OCP on channel [1]
    print(Rigol.channel_state_read(1))  # Read status from channel [1]
    print(Rigol.channel_mode_read(1))  # Read mode from channel [1]
