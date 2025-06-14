import subprocess
import numpy as np
from rtlsdr import RtlSdr
import time
from colorama import Fore
import csv
from Calculations import *
import matplotlib.pyplot as plt 
import ast
import pandas as pd
import scipy.io
import os
import random
import pickle
from sklearn.preprocessing import MinMaxScaler


def freq_select():
    frequency = float(input(Fore.GREEN + "Choose a frequency to use (MHz): "))
    freq_mhz = float(frequency)
    freq_in_hz = freq_mhz * 1e6
    print(Fore.GREEN + f"Using {freq_in_hz} Hz")
    return freq_in_hz



def get_signal(seconds, frequency):
    sdr = RtlSdr()

    try:
        sdr.center_freq = frequency  
        sdr.sample_rate = DEFAULT_FS
        sdr.gain = 'auto'  

        total_samples = int(seconds * sdr.sample_rate)  
        chunk_size = 256 * 1024 
        captured_samples = []

        sdr.read_samples(2048)

        while len(captured_samples) < total_samples:
            samples_needed = total_samples - len(captured_samples)
            chunk = sdr.read_samples(min(chunk_size, samples_needed))  
            captured_samples.extend(chunk)

        captured_samples_np = np.array(captured_samples, dtype=np.complex64)
        output_path = "iq_samples.dat"
        captured_samples_np.tofile(output_path)

        print(Fore.GREEN + f"Capture complete. Collected {len(captured_samples)} samples\nSaving to {output_path}")

    finally:
        sdr.close()

def check_rtl_sdr():
    try:
        result = subprocess.run(["lsusb"], capture_output=True, text=True)
        return any("Realtek" in line or "RTL2838" in line for line in result.stdout.splitlines())
    except Exception as e:
        print(Fore.RED + f"Error checking RTL-SDR with lsusb: {e}")
        return False
    

def view_CSV(file_path, num_rows):

    with open (file_path) as file:
        
        reader_obj = csv.reader(file, delimiter=',', quotechar='|')
        for i, row in enumerate(reader_obj):
            print(', '.join(row))
            if i + 1 >= num_rows: 
                break
 


def rolling_window(seconds, frequency, classification):

    fs = DEFAULT_FS
    sdr = RtlSdr()
    rtl_gain = None
    captured_samples_np = None

    try:
        freq = sdr.center_freq = frequency
        fs = sdr.fs = DEFAULT_FS
        sdr.gain = DEFAULT_RTL_GAIN
        time.sleep(0.5)
        rtl_gain = sdr.gain

        total_samples = int(seconds * fs)
        chunk_size = 256 * 1024
        captured_samples = []
        start_time = time.time()

        while len(captured_samples) < total_samples:
            sampled_needed = total_samples - len(captured_samples)
            chunk = sdr.read_samples(min(chunk_size, sampled_needed))
            captured_samples.extend(chunk)

            if time.time() - start_time >= seconds:
                break

        captured_samples_np = np.array(captured_samples, dtype=np.complex64)
        output_path = 'iq_samples.dat'
        captured_samples_np.tofile(output_path)

    except Exception as e:
        print(Fore.RED + f"Error capturing samples: {e}")

    finally:
        sdr.close()

    if captured_samples_np is not None and rtl_gain is not None:
        file = 'iq_samples.dat'
        iq_data = np.fromfile(file, dtype=np.complex64)
        feature_extraction(iq_data, frequency, fs, rtl_gain)
        export_csv(iq_data, frequency, fs, classification)


def signalCapture(seconds, frequency):
    fs = DEFAULT_FS
    sdr = RtlSdr()
    rtl_gain = None
    captured_samples_np = None

    try:
        freq = sdr.center_freq = frequency
        fs = sdr.fs = DEFAULT_FS
        sdr.gain = DEFAULT_RTL_GAIN
        time.sleep(0.5)
        rtl_gain = sdr.gain

        total_samples = int(seconds * fs)
        chunk_size = 256 * 1024
        captured_samples = []
        start_time = time.time()

        while len(captured_samples) < total_samples:
            sampled_needed = total_samples - len(captured_samples)
            chunk = sdr.read_samples(min(chunk_size, sampled_needed))
            captured_samples.extend(chunk)

            if time.time() - start_time >= seconds:
                break

        captured_samples_np = np.array(captured_samples, dtype=np.complex64)
        captured_samples_np.tofile('iq_samples.dat')

    except Exception as e:
        print(Fore.RED + f"Error capturing signal: {e}")

    finally:
        sdr.close()

    if captured_samples_np is None or rtl_gain is None:
        return None

    features = feature_extraction(captured_samples_np, frequency, fs, rtl_gain)
    return features



def visualise_signal(file, freq_hz):

    samples = np.fromfile(file, dtype=np.complex64)

    fs = DEFAULT_FS
    fc = freq_hz

    N = len(samples)
    fft_data = np.fft.fftshift(np.abs(np.fft.fft(samples))**2)
    freqs = np.fft.fftshift(np.fft.fftfreq(N, 1 / fs)) + fc  

    plt.figure(figsize=(10, 5))
    plt.plot(freqs / 1e6, 10 * np.log10(fft_data))  
    plt.xlabel("Frequency (MHz)")
    plt.ylabel("Power (dB)")
    plt.title(f"FFT Spectrum (Centered at {fc/1e6} MHz)")
    plt.grid()
    plt.show()


def convert_to_dat(row):

    row_index = row
    df = pd.read_csv("Filtered_data.csv", skiprows=row_index, nrows=1, header=None)
    df.columns = ["Frequency", "I/Q Data"]
    frequency = df["Frequency"].iloc[0]
    iq_data = ast.literal_eval(df["I/Q Data"].iloc[0])
    iq_array = np.array(iq_data, dtype=np.complex64)
    iq_array.tofile("new_iq_samples.dat")
    print(f"Frequency = {frequency}")
    print(f"Success, row number {row} converted to dat as new_iq_sample.dat")

    return frequency



def mat_to_dat(filename):

    mat_data = scipy.io.loadmat(filename)

    print("Variables found in mat file:", mat_data.keys())

    for key, value in mat_data.items():
        if not key.startswith("__"):
            print(f"\nVariables name: {key}")
            print(value)


    mat_file = filename
    data = scipy.io.loadmat(mat_file)
    iq_data = data.get('GNSS_plus_Jammer_awgn', None)

    if iq_data is None:
        print("Variable 'GNSS_plus_Jammer_awgn' not found in mat file")
    else:
        iq_data = np.array(iq_data, dtype=np.complex64)

        project_dir = os.path.expanduser("~/Documents/SignalSentinel")
        output_file = os.path.join(project_dir, 'Jamming_raw_iq.dat')
        iq_data.tofile(output_file)
        print(f"Saved mat file to {output_file}")


def gen_jam_data(frequency, classification, jam_file):
    fs = DEFAULT_FS
    jam_iq = np.fromfile(jam_file, dtype=np.complex64)
    feature_extraction(jam_iq, frequency)
    export_csv(jam_iq, frequency, fs, classification)
    

def generate_random_frequency():
    frequency = random.uniform(433.05e6, 2e9)
    frequency_int = int(frequency)
    return frequency_int


def process_mat_files_in_folder(folder_path, classification, max_files=None):
    processed_files = 0
    
    for filename in os.listdir(folder_path):

        if filename.endswith(".mat"):
            if max_files is not None and processed_files >= max_files:
                print(f"Reached the limit of {max_files} files. Stopping.")
                break

            full_path = os.path.join(folder_path, filename)
            print(f"Processing file: {full_path}")

            jam_file = mat_to_dat(full_path)
            if jam_file:
                frequency = generate_random_frequency()
                print(f"Using frequency: {frequency / 1e6} MHz")
                gen_jam_data(frequency, classification, jam_file)
                processed_files += 1


def auto_jam(folder_path, num_files):
 
    def mat_to_dat(filename):
        mat_data = scipy.io.loadmat(filename)

        print("Variables found in mat file:", mat_data.keys())

        for key, value in mat_data.items():
            if not key.startswith("__"):
                print(f"\nVariable name: {key}")
                print(value)

        mat_file = filename
        data = scipy.io.loadmat(mat_file)
        iq_data = data.get('GNSS_plus_Jammer_awgn', None)

        if iq_data is None:
            print(f"Variable 'GNSS_plus_Jammer_awgn' not found in {filename}")
            return None
        else:
            iq_data = np.array(iq_data, dtype=np.complex64)

            project_dir = os.path.expanduser("~/Documents/SignalSentinel")
            output_file = os.path.join(project_dir, 'Jamming_raw_iq.dat')
            iq_data.tofile(output_file)
            print(f"Saved mat file to {output_file}")
            return output_file
        
    def gen_jam_data(frequency, classification, jam_file):
        fs = DEFAULT_FS
        jam_iq = np.fromfile(jam_file, dtype=np.complex64)
        feature_extraction(jam_iq, frequency)
        export_csv(jam_iq, frequency, fs, classification)


    def generate_random_frequency():
        frequency = random.uniform(433.05e6, 2e9)
        frequency_int = int(frequency)
        return frequency_int

    processed_files = 0 
    for filename in os.listdir(folder_path):
        if filename.endswith(".mat"):
            if processed_files >= num_files:
                print(f"Reached the limit of {num_files} files. Stopping.")
                break

            full_path = os.path.join(folder_path, filename)
            print(f"Processing file: {full_path}")

            jam_file = mat_to_dat(full_path)
            if jam_file:
                frequency = generate_random_frequency()
                print(f"Using frequency: {frequency} Hz") 
                classification = 'Jamming' 
                gen_jam_data(frequency, classification, jam_file)
                processed_files += 1




def modelTest(sample_file, frequency, fs, rtl_gain):
    """
    Function to load the trained model and scaler, then predict on new sample data.
    """
    with open("naive_bayes_model.pkl", "rb") as model_file:
        naiveBayes = pickle.load(model_file)

    with open("scaler.pkl", "rb") as scaler_file:
        scaler = pickle.load(scaler_file)
    
    new_features = feature_extraction(sample_file, frequency, fs, rtl_gain)

    new_features_selected = new_features[['RMS', 'Max Magnitude', 'Amplitude', 'PSD', 'Signal To Noise']]

    new_features_scaled = scaler.transform(new_features_selected)

    prediction = naiveBayes.predict(new_features_scaled)

    prediction_text = "Safe" if prediction[0] == 0 else "Jamming"

    if prediction[0] == 0:
        print(Fore.GREEN + f'The predicted classification is: {prediction_text}')
    else:
        print(Fore.RED + f'The predicted classification is: {prediction_text}')


def jam_analyzer(frequency, seconds=2, rms_threshold=0.2):
    """Check one ``frequency`` for possible jamming.

    This helper captures ``seconds`` of IQ data and prints a warning if the
    calculated RMS level is above ``rms_threshold``. The check uses no machine
    learning models and simply compares the measured RMS power.
    """


    print(Fore.CYAN + f"Scanning {frequency/1e6:.2f} MHz...")
    features = signalCapture(seconds, frequency)
    if features is None:
        print(Fore.RED + "Capture failed. Skipping frequency.")
        return

    rms = float(features['RMS'].iloc[0])
    if rms > rms_threshold:
        print(
            Fore.RED
            + f"Possible jamming detected at {frequency/1e6:.2f} MHz (RMS {rms:.2f})"
        )
    else:
        print(
            Fore.GREEN
            + f"No jamming detected at {frequency/1e6:.2f} MHz (RMS {rms:.2f})"
        )


def jam_analyzer_list(frequencies, seconds=2, rms_threshold=0.2):

    """Run :func:`jam_analyzer` on each frequency in ``frequencies``.

    The list can contain any number of discrete values, typically the preset
    frequencies defined in :mod:`Main`. Each frequency is scanned in turn using
    the same ``seconds`` and ``rms_threshold`` parameters.
    """
    for freq in frequencies:
        jam_analyzer(freq, seconds=seconds, rms_threshold=rms_threshold)



