#!/usr/bin/env python3
from verba_gui_integration import VerbaGradioAudio

if __name__ == "__main__":
    audio_app = VerbaGradioAudio()
    demo = audio_app.create_gradio_interface()
    demo.launch(
        share=False, 
        server_name="0.0.0.0", 
        server_port=7860,
        show_error=True
    )
