#!/usr/bin/env python3
import streamlit as st
from verba_gui_integration import VerbaStreamlitAudio

st.set_page_config(
    page_title="Verba Real-Time Audio",
    page_icon="🎤",
    layout="wide"
)

# Initialize and render audio interface
audio_app = VerbaStreamlitAudio()
audio_app.render_audio_interface()

# Auto-refresh for real-time updates
if st.session_state.is_recording:
    time.sleep(1)
    st.experimental_rerun()
