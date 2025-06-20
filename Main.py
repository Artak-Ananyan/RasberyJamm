from Calculations import *
from pyfiglet import Figlet
from colorama import Fore
import numpy as np

from Functions import *

# Frequencies to scan for potential jamming without machine learning
PRESET_FREQUENCIES = [433e6, 868e6, 915e6, 2.437e9]

def opening_script():
    f = Figlet(font='slant')
    print(Fore.RED + f.renderText("Signal Sentinel"))
    if check_rtl_sdr():
        print(Fore.GREEN + "RTL_SDR Device found")
    else:
        print(Fore.RED + "No RTL-SDR device found, please reinstall device and start again")

    print("Josh Perryman Bcs(Hons) Cyber Security 2025\n")
    

def main(frequency):

    f = Figlet(font='slant')
    freq_hz = frequency


    try: 
        while True:

            print(Fore.BLUE + "-" * 25)
            print(Fore.GREEN + "| Main Menu                        |")
            print(Fore.BLUE + "-" * 25)
            print(Fore.GREEN + "| Signal to CSV                [1] |")
            print(Fore.BLUE + "-" * 25)
            print(Fore.GREEN + "| Change frequency             [2] |")
            print(Fore.BLUE + "-" * 25)
            print(Fore.GREEN + "| Test model with live signal  [3] |")
            print(Fore.BLUE + "-" * 25)
            print(Fore.GREEN + "| Test model with saved signal [4] |")
            print(Fore.BLUE + "-" * 25)
            print(Fore.GREEN + "| Exit                         [5] |")
            print(Fore.BLUE + "-" * 25)

            option = int(input(Fore.GREEN + "| Choose an option: "))
            print(Fore.BLUE + "-" * 25)

            if option == 1:
                print(Fore.GREEN + "Choose how long to capture for: (seconds)")
                seconds = int(input(Fore.GREEN + "Time in Seconds: "))
                classification = input(Fore.GREEN + "Is this signal Safe or Jamming?: ")
                print(Fore.GREEN + f"Capturing on frequency {freq_hz} MHz for {seconds} seconds")
                rolling_window(seconds, freq_hz, classification)
                input(Fore.GREEN + "\nPress Enter to return to the menu...")
                continue

            elif option == 2:
                print(Fore.YELLOW + "Changing frequency...")
                freq_hz = freq_select()
                print(Fore.GREEN + f"New frequency set: {freq_hz} MHz")
                continue 

            elif option == 3:
                print(Fore.GREEN + "Choose how long to capture for: (seconds)")
                seconds = int(input(Fore.GREEN + "Time in Seconds: "))
                signalCapture(seconds, freq_hz)
                
                file = 'iq_samples.dat'
                iq_data = np.fromfile(file, dtype=np.complex64)
                rtl_gain = 30 
                modelTest(iq_data, freq_hz, DEFAULT_FS, rtl_gain)

                input(Fore.GREEN + "\nPress Enter to return to the menu...")
                continue

            elif option == 4:
                test_file = input(Fore.GREEN + "Choose a file to test with: ")
                iqfile = np.fromfile(test_file, dtype=np.complex64)
                rtl_gain = 30
                modelTest(iqfile, freq_hz, DEFAULT_FS, rtl_gain)

            elif option == 5:
                print(Fore.RED + f.renderText("Exiting"))
                quit()

            else:
                print(Fore.RED + "Select an option")

    except KeyboardInterrupt:
        print("\nProgram interrupted. Exiting...")
        exit()


def start_jam_detection():
    """Run the non-ML jam analyzer on :data:`PRESET_FREQUENCIES`."""

    opening_script()
    jam_analyzer_list(PRESET_FREQUENCIES)


if __name__ == "__main__":
    start_jam_detection()
