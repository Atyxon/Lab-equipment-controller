from PicoTC08.PICOTC08 import PicoTC08, TempUnits

if __name__ == "__main__":
    Pico = PicoTC08()  # Create instance of Pico TC-08
    Pico.channel_enable(1)  # Enable channel [1] of Pico TC-08 with default input type value
    # Pico.channel_disable(1)  # Disable channel [1]  of Pico TC-08
    # Pico.all_channel_enable()  # Enable evey channel of Pico TC-08
    # Pico.all_channel_disable()  # Disable evey channel of Pico TC-08
    # print(Pico.status_read())  # Read status of Pico TC-08
    # print(Pico.all_temp_read())  # Measure and return temperature on every channel of Pico TC-08
    print(Pico.single_temp_read(1))  # Measure and return temperature on channel [1] of Pico TC-08
    Pico.temp_unit_set(TempUnits.UNIT_KELVIN)
    print(Pico.single_temp_read(1))  # Measure and return temperature on channel [1] of Pico TC-08
    print(Pico.minimum_interval_get())  # Get minimum interval value in [ms]
