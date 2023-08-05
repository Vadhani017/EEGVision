import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import mne
from io import BytesIO

def generate_dummy_eeg_data(duration, sfreq):
    # Generate time vector
    times = np.arange(0, duration, 1/sfreq)

    # Generate dummy EEG signals
    num_channels = 8
    eeg_data = np.random.randn(num_channels, len(times))

    return eeg_data, times

def apply_ica(eeg_data):
    # Create MNE RawArray object
    ch_names = [f"Channel {i+1}" for i in range(eeg_data.shape[0])]
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types='eeg')
    raw = mne.io.RawArray(eeg_data, info)

    # Apply ICA
    ica = mne.preprocessing.ICA(n_components=eeg_data.shape[0])
    ica.fit(raw)

    # Get the independent components
    ica_data = ica.get_sources(raw)

    return ica_data

def main():
    st.title("EEG Signal Viewer with ICA")

    # Generate dummy EEG data
    duration = 10  # 10 seconds
    sfreq = 250  # 250 Hz
    data, times = generate_dummy_eeg_data(duration, sfreq)

    # Apply ICA to the EEG data
    ica_data = apply_ica(data)

    # Convert EEG data to MNE RawArray format
    info = mne.create_info(ch_names=[f"Channel {i+1}" for i in range(data.shape[0])], sfreq=sfreq, ch_types='eeg')
    raw = mne.io.RawArray(data, info)

    # Display the original EEG signals using Streamlit's MNE component
    st.set_option('deprecation.showPyplotGlobalUse', False)  # Prevent showing plot twice
    fig = raw.plot(show_scrollbars=False, show_scalebars=True, duration=duration, n_channels=data.shape[0])
    st.pyplot(fig, clear_figure=True)

    # Display the extracted independent components using Streamlit's MNE component
    st.subheader("Independent Components")
    ica_fig = ica_data.plot(show_scrollbars=False, show_scalebars=True, duration=duration, n_channels=data.shape[0])
    st.pyplot(ica_fig, clear_figure=True)

if __name__ == "__main__":
    main()
