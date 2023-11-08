import numpy as np
import scipy.io as sio
import mne
import numpy as np
import matplotlib.pyplot as plt
import spkit as sp
import streamlit as st
from scipy.signal import butter, filtfilt
import os
import mysql.connector
from passlib.hash import bcrypt

# Define a function to apply a high-pass filter
def highpass_filter(data, cutoff_freq, sampling_rate):
    nyquist_freq = 0.5 * sampling_rate
    normal_cutoff = cutoff_freq / nyquist_freq
    b, a = butter(4, normal_cutoff, btype='high', analog=False)
    filtered_data = filtfilt(b, a, data, axis=1)
    return filtered_data

# Define a function to load and process EEG data
def process_eeg_data(file_path, selected_channels, highpass_cutoff):
    mat_data = sio.loadmat(file_path)
    eeg_data = mat_data['eeg']

    # Replace with the correct channel names from your .mat file
    channel_names = ['Fp1', 'Fp2', 'F3', 'F4', 'C3', 'C4', 'P3', 'P4', 'O1', 'O2', 'F7', 'F8', 'T7', 'T8', 'Status']

    # Extract other relevant information such as sampling rate
    sampling_rate = float(mat_data['info']['ns'][0][0][0][0])

    # Remove the 'Status' channel
    status_channel_index = channel_names.index('Status')
    eeg_data = np.delete(eeg_data, status_channel_index, axis=0)
    channel_names.remove('Status')

    # Create an MNE-Python info object
    info = mne.create_info(channel_names, sampling_rate)

    # Create an MNE-Python Raw object
    raw = mne.io.RawArray(eeg_data, info)

    # Get the EEG data and channel names
    X = raw.get_data()
    ch_names = raw.info['ch_names']
    fs = raw.info['sfreq']

    # Apply high-pass filtering
    X_filtered = highpass_filter(X, highpass_cutoff, fs)

    # Create a time vector
    t = np.arange(X_filtered.shape[1]) / fs

    # Plot the noisy signal for selected channels
    fig_noisy, ax_noisy = plt.subplots(figsize=(12, 5))
    if "All Channels" in selected_channels:
        selected_channel_indices = range(len(ch_names))
    else:
        selected_channel_indices = [ch_names.index(channel) for channel in selected_channels]

    for idx, channel_idx in enumerate(selected_channel_indices):
        ax_noisy.plot(t, X_filtered[channel_idx] + idx * 200, label=ch_names[channel_idx])
    ax_noisy.set_xlim(t[0], t[-1])
    ax_noisy.set_xlabel('Time (sec)')
    ax_noisy.set_yticks(np.arange(len(selected_channels)) * 200)
    ax_noisy.set_yticklabels(selected_channels)
    ax_noisy.grid()
    ax_noisy.set_title('High-Pass Filtered EEG Signal')
    st.pyplot(fig_noisy)

    # Apply denoising
    XR = sp.eeg.ATAR(X_filtered.copy(), verbose=0)

    # Plot the corrected signal for selected channels
    fig_corrected, ax_corrected = plt.subplots(figsize=(12, 5))
    for idx, channel_idx in enumerate(selected_channel_indices):
        ax_corrected.plot(t, XR[channel_idx] + idx * 200, label=ch_names[channel_idx])
    ax_corrected.set_xlim(t[0], t[-1])
    ax_corrected.set_xlabel('Time (sec)')
    ax_corrected.set_yticks(np.arange(len(selected_channels)) * 200)
    ax_corrected.set_yticklabels(selected_channels)
    ax_corrected.grid()
    ax_corrected.set_title('Corrected EEG Signal')
    st.pyplot(fig_corrected)

    n_channels, n_samples = XR.shape

    # Create an MNE-Python info object with the correct number of channels
    info = mne.create_info(channel_names[:n_channels], fs, ch_types='eeg')

    # Create an MNE-Python Raw object
    raw = mne.io.RawArray(XR, info)

    # Create the output folder if it doesn't exist
    output_folder = 'C:\\Users\\Sundaraavadhani\\Desktop\\PROJECT\\downloaded file'

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Specify the output file path within this folder
    output_file_path = os.path.join(output_folder, 'corrected_eeg.fif')

    # Save the corrected signal as a .fif file
    raw.save(output_file_path, overwrite=True)

    # Create a download button for the corrected signal
    st.download_button(label="Download Corrected EEG Signal", data=open(output_file_path, "rb").read(), file_name='corrected_eeg.fif', key="download_button")

    return info

background_style = f"""
    background-image: url("eegpic.jpg");
    background-repeat: no-repeat;
    background-attachment: fixed;
    background-size: cover;
    background-position: center;
"""

# Apply the background style to the entire page
st.markdown(
    f"""
    <style>
        body {{
            {background_style}
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize Streamlit app
st.title("EEG Data Processing")

# Create a sidebar for user registration and login
st.sidebar.title("User Authentication")

# Connect to the MySQL database
conn = mysql.connector.connect(
    host="localhost",
    port=3306,
    user="root",
    password="Virussv017*",
    database="eegdata"
)

# Create a cursor to interact with the database
cursor = conn.cursor()

# User Registration
def register_user(username, password):
    hashed_password = bcrypt.using(rounds=13).hash(password)
    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
    conn.commit()

# User Login
def login_user(username, passcode):
    cursor.execute("SELECT passcode FROM users WHERE username = %s", (int(username),))
    result = cursor.fetchone()

    if result and int(passcode) == result[0]:
        return True
    else:
        return False

# Check if the user is logged in
is_authenticated = False
# User Registration Form
if st.sidebar.button("Register"):
    st.sidebar.write('Registration Form')
    new_username = st.sidebar.text_input("New Username", key="new_username")  # Unique key
    new_password = st.sidebar.text_input("New Password", type="password", key="new_password")  # Unique key

    if new_username and new_password:
        # Attempt to register the user
        if register_user(new_username, new_password):
            st.sidebar.success("Registration successful. You can now log in.")
        else:
            st.sidebar.error("Registration failed. The username may already exist.")

# Initialize session state
if 'is_authenticated' not in st.session_state:
    st.session_state.is_authenticated = False

# User Login Form
if not st.session_state.is_authenticated:
    username = st.sidebar.text_input("Username")
    passcode = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"):
        if username and passcode:
            if login_user(username, passcode):
                st.session_state.is_authenticated = True
                st.sidebar.success("Login successful.")
            else:
                st.sidebar.error("Login failed. Please check your credentials.")
# Check authentication status
if st.session_state.is_authenticated:
    # Authenticated functionality goes here
    st.write("You are authenticated. You can access this section.")
    uploaded_file = st.file_uploader("Upload a .mat EEG data file", type=["mat"])
    channel_names = ['Fp1', 'Fp2', 'F3', 'F4', 'C3', 'C4', 'P3', 'P4', 'O1', 'O2', 'F7', 'F8', 'T7', 'T8']
    channel_names.append("All Channels")  # Add an option to display all channels
    selected_channels = st.multiselect("Select channels to display", channel_names)
    highpass_cutoff = st.number_input("High-Pass Filter Cutoff Frequency (Hz)", min_value=0.01, max_value=50.0, value=0.5)
    if st.button("Process and Display"):
        info = process_eeg_data(uploaded_file, selected_channels, highpass_cutoff)
else:
    st.write("You are not authenticated. Please log in to access this section.")