"""
Verba Real-Time Audio GUI Integration
Supports multiple frameworks: Streamlit, Gradio, FastAPI, Flask
"""
import streamlit as st
import gradio as gr
import asyncio
import threading
import time
import json
from typing import Optional, Dict, Any
from real_time_audio_capture import (
    create_microphone_capture, 
    create_system_audio_capture,
    RealTimeAudioCapture
)
from enhanced_transcription_service import EnhancedTranscriptionService

# =============================================================================
# STREAMLIT INTEGRATION
# =============================================================================

class VerbaStreamlitAudio:
    """Streamlit integration for real-time audio"""
    
    def __init__(self):
        if 'transcription_service' not in st.session_state:
            st.session_state.transcription_service = None
        if 'audio_capture' not in st.session_state:
            st.session_state.audio_capture = None
        if 'is_recording' not in st.session_state:
            st.session_state.is_recording = False
        if 'transcriptions' not in st.session_state:
            st.session_state.transcriptions = []
        if 'audio_stats' not in st.session_state:
            st.session_state.audio_stats = {}
    
    def initialize_services(self):
        """Initialize transcription service"""
        if st.session_state.transcription_service is None:
            with st.spinner("🔧 Initializing transcription service..."):
                try:
                    st.session_state.transcription_service = EnhancedTranscriptionService(
                        model_name="openai/whisper-tiny",
                        device="cpu",
                        vad_aggressiveness=2
                    )
                    st.success("✅ Transcription service ready!")
                except Exception as e:
                    st.error(f"❌ Failed to initialize service: {e}")
                    return False
        return True
    
    def transcription_callback(self, result):
        """Handle transcription results"""
        if result.success and result.text.strip():
            transcription_data = {
                'timestamp': time.strftime("%H:%M:%S"),
                'text': result.text.strip(),
                'processing_time': result.processing_time,
                'efficiency_gain': result.efficiency_gain,
                'segments': len(result.segments)
            }
            st.session_state.transcriptions.append(transcription_data)
            
            # Update stats
            if result.statistics:
                st.session_state.audio_stats = result.statistics
    
    def start_recording(self, audio_source: str = "microphone"):
        """Start audio recording"""
        if not self.initialize_services():
            return
        
        try:
            if audio_source == "microphone":
                st.session_state.audio_capture = create_microphone_capture(
                    transcription_service=st.session_state.transcription_service,
                    transcription_callback=self.transcription_callback
                )
            else:  # system audio
                st.session_state.audio_capture = create_system_audio_capture(
                    transcription_service=st.session_state.transcription_service,
                    transcription_callback=self.transcription_callback
                )
            
            st.session_state.audio_capture.start_recording()
            st.session_state.is_recording = True
            st.success(f"🎤 {audio_source.title()} recording started!")
            
        except Exception as e:
            st.error(f"❌ Failed to start recording: {e}")
    
    def stop_recording(self):
        """Stop audio recording"""
        if st.session_state.audio_capture:
            st.session_state.audio_capture.stop_recording()
            st.session_state.is_recording = False
            st.success("⏹️ Recording stopped!")
    
    def render_audio_interface(self):
        """Render the Streamlit audio interface"""
        st.title("🎤 Verba Real-Time Audio Transcription")
        
        # Audio source selection
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🎤 Start Microphone", disabled=st.session_state.is_recording):
                self.start_recording("microphone")
        
        with col2:
            if st.button("🖥️ Start System Audio", disabled=st.session_state.is_recording):
                self.start_recording("system")
        
        # Stop button
        if st.session_state.is_recording:
            if st.button("⏹️ Stop Recording", type="primary"):
                self.stop_recording()
            
            # Real-time stats
            if st.session_state.audio_capture:
                stats = st.session_state.audio_capture.get_stats()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Buffer Duration", f"{stats.get('buffer_duration', 0):.1f}s")
                with col2:
                    st.metric("Processed Audio", f"{stats.get('total_audio_processed', 0):.1f}s")
                with col3:
                    st.metric("Queue Size", stats.get('queue_size', 0))
        
        # Display transcriptions
        st.subheader("📝 Live Transcriptions")
        
        if st.session_state.transcriptions:
            # Show recent transcriptions
            for trans in reversed(st.session_state.transcriptions[-10:]):  # Last 10
                with st.container():
                    st.write(f"**{trans['timestamp']}** - {trans['text']}")
                    st.caption(f"⏱️ {trans['processing_time']:.2f}s | 🚀 {trans['efficiency_gain']:.1f}x")
                    st.divider()
        else:
            st.info("🗣️ Start recording to see live transcriptions here")
        
        # Audio statistics
        if st.session_state.audio_stats:
            with st.expander("📊 Audio Statistics"):
                stats = st.session_state.audio_stats
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Speech Ratio", f"{stats.get('speech_ratio', 0):.1f}%")
                    st.metric("Voice Segments", stats.get('voice_segments', 0))
                
                with col2:
                    st.metric("Processing Speed", f"{stats.get('processing_speed', 0):.1f}x")
                    st.metric("Voice Duration", f"{stats.get('voice_duration', 0):.1f}s")

# =============================================================================
# GRADIO INTEGRATION
# =============================================================================

class VerbaGradioAudio:
    """Gradio integration for real-time audio"""
    
    def __init__(self):
        self.transcription_service = None
        self.audio_capture = None
        self.is_recording = False
        self.transcriptions = []
        self.current_stats = {}
    
    def initialize_services(self):
        """Initialize transcription service"""
        if self.transcription_service is None:
            try:
                self.transcription_service = EnhancedTranscriptionService(
                    model_name="openai/whisper-tiny",
                    device="cpu",
                    vad_aggressiveness=2
                )
                return "✅ Transcription service initialized!"
            except Exception as e:
                return f"❌ Failed to initialize: {e}"
        return "✅ Service already running"
    
    def transcription_callback(self, result):
        """Handle transcription results"""
        if result.success and result.text.strip():
            transcription_text = f"[{time.strftime('%H:%M:%S')}] {result.text.strip()}"
            self.transcriptions.append(transcription_text)
            
            # Keep only recent transcriptions
            if len(self.transcriptions) > 20:
                self.transcriptions = self.transcriptions[-20:]
            
            # Update stats
            if result.statistics:
                self.current_stats = result.statistics
    
    def start_microphone(self):
        """Start microphone recording"""
        try:
            if not self.transcription_service:
                self.initialize_services()
            
            self.audio_capture = create_microphone_capture(
                transcription_service=self.transcription_service,
                transcription_callback=self.transcription_callback
            )
            
            self.audio_capture.start_recording()
            self.is_recording = True
            return "🎤 Microphone recording started!", self.get_transcriptions_text()
            
        except Exception as e:
            return f"❌ Failed to start microphone: {e}", ""
    
    def start_system_audio(self):
        """Start system audio recording"""
        try:
            if not self.transcription_service:
                self.initialize_services()
            
            self.audio_capture = create_system_audio_capture(
                transcription_service=self.transcription_service,
                transcription_callback=self.transcription_callback
            )
            
            self.audio_capture.start_recording()
            self.is_recording = True
            return "🖥️ System audio recording started!", self.get_transcriptions_text()
            
        except Exception as e:
            return f"❌ Failed to start system audio: {e}", ""
    
    def stop_recording(self):
        """Stop audio recording"""
        if self.audio_capture:
            self.audio_capture.stop_recording()
            self.is_recording = False
            return "⏹️ Recording stopped!", self.get_transcriptions_text()
        return "No recording to stop", self.get_transcriptions_text()
    
    def get_transcriptions_text(self):
        """Get formatted transcriptions"""
        if not self.transcriptions:
            return "🗣️ Start recording to see transcriptions here..."
        
        return "\n".join(reversed(self.transcriptions[-10:]))  # Last 10, newest first
    
    def get_stats(self):
        """Get current statistics"""
        if not self.audio_capture:
            return "No active recording"
        
        stats = self.audio_capture.get_stats()
        return f"""📊 **Live Stats:**
- Buffer: {stats.get('buffer_duration', 0):.1f}s
- Processed: {stats.get('total_audio_processed', 0):.1f}s
- Queue: {stats.get('queue_size', 0)}
- Transcriptions: {len(self.transcriptions)}
"""
    
    def create_gradio_interface(self):
        """Create Gradio interface"""
        with gr.Blocks(title="Verba Real-Time Audio") as demo:
            gr.Markdown("# 🎤 Verba Real-Time Audio Transcription")
            
            # Initialize button
            with gr.Row():
                init_btn = gr.Button("🔧 Initialize Services")
                init_output = gr.Textbox(label="Initialization Status", interactive=False)
            
            init_btn.click(self.initialize_services, outputs=init_output)
            
            # Control buttons
            with gr.Row():
                mic_btn = gr.Button("🎤 Start Microphone")
                sys_btn = gr.Button("🖥️ Start System Audio")
                stop_btn = gr.Button("⏹️ Stop Recording", variant="stop")
            
            # Status and transcriptions
            with gr.Row():
                with gr.Column():
                    status_box = gr.Textbox(label="Status", interactive=False)
                    stats_box = gr.Markdown("📊 Statistics will appear here")
                
                with gr.Column():
                    transcription_box = gr.Textbox(
                        label="Live Transcriptions",
                        lines=15,
                        interactive=False,
                        placeholder="Transcriptions will appear here..."
                    )
            
            # Event handlers
            mic_btn.click(
                self.start_microphone,
                outputs=[status_box, transcription_box]
            )
            
            sys_btn.click(
                self.start_system_audio,
                outputs=[status_box, transcription_box]
            )
            
            stop_btn.click(
                self.stop_recording,
                outputs=[status_box, transcription_box]
            )
            
            # Auto-refresh transcriptions and stats
            demo.load(
                lambda: (self.get_transcriptions_text(), self.get_stats()),
                outputs=[transcription_box, stats_box],
                every=2  # Refresh every 2 seconds
            )
        
        return demo

# =============================================================================
# FASTAPI INTEGRATION
# =============================================================================

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import uvicorn

class VerbaFastAPIAudio:
    """FastAPI integration with WebSocket for real-time updates"""
    
    def __init__(self):
        self.app = FastAPI(title="Verba Real-Time Audio API")
        self.transcription_service = None
        self.audio_capture = None
        self.connected_clients = []
        self.setup_routes()
    
    def setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/")
        async def get_audio_interface():
            return HTMLResponse(self.get_html_interface())
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.connected_clients.append(websocket)
            
            try:
                while True:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    if message["action"] == "start_microphone":
                        await self.start_microphone(websocket)
                    elif message["action"] == "start_system":
                        await self.start_system_audio(websocket)
                    elif message["action"] == "stop":
                        await self.stop_recording(websocket)
                        
            except WebSocketDisconnect:
                self.connected_clients.remove(websocket)
    
    async def broadcast_message(self, message: dict):
        """Broadcast message to all connected clients"""
        for client in self.connected_clients[:]:  # Copy list to avoid modification during iteration
            try:
                await client.send_text(json.dumps(message))
            except:
                self.connected_clients.remove(client)
    
    def transcription_callback(self, result):
        """Handle transcription results"""
        if result.success and result.text.strip():
            message = {
                "type": "transcription",
                "timestamp": time.strftime("%H:%M:%S"),
                "text": result.text.strip(),
                "processing_time": result.processing_time,
                "efficiency_gain": result.efficiency_gain
            }
            
            # Broadcast to all connected clients
            asyncio.create_task(self.broadcast_message(message))
    
    def get_html_interface(self):
        """Return HTML interface for real-time audio"""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>Verba Real-Time Audio</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .controls { margin: 20px 0; }
        button { padding: 10px 20px; margin: 5px; border: none; border-radius: 5px; cursor: pointer; }
        .start-btn { background-color: #4CAF50; color: white; }
        .stop-btn { background-color: #f44336; color: white; }
        .transcriptions { border: 1px solid #ddd; padding: 15px; height: 400px; overflow-y: auto; }
        .transcription { margin: 10px 0; padding: 10px; background-color: #f9f9f9; border-radius: 5px; }
        .timestamp { color: #666; font-size: 0.9em; }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .success { background-color: #d4edda; color: #155724; }
        .error { background-color: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <h1>🎤 Verba Real-Time Audio Transcription</h1>
    
    <div class="controls">
        <button class="start-btn" onclick="startMicrophone()">🎤 Start Microphone</button>
        <button class="start-btn" onclick="startSystemAudio()">🖥️ Start System Audio</button>
        <button class="stop-btn" onclick="stopRecording()">⏹️ Stop Recording</button>
    </div>
    
    <div id="status" class="status"></div>
    
    <h2>📝 Live Transcriptions</h2>
    <div id="transcriptions" class="transcriptions">
        <p>🗣️ Start recording to see transcriptions here...</p>
    </div>
    
    <script>
        const ws = new WebSocket('ws://localhost:8000/ws');
        const statusDiv = document.getElementById('status');
        const transcriptionsDiv = document.getElementById('transcriptions');
        
        ws.onmessage = function(event) {
            const message = JSON.parse(event.data);
            
            if (message.type === 'transcription') {
                addTranscription(message);
            } else if (message.type === 'status') {
                updateStatus(message.text, message.success);
            }
        };
        
        function startMicrophone() {
            ws.send(JSON.stringify({action: 'start_microphone'}));
        }
        
        function startSystemAudio() {
            ws.send(JSON.stringify({action: 'start_system'}));
        }
        
        function stopRecording() {
            ws.send(JSON.stringify({action: 'stop'}));
        }
        
        function addTranscription(message) {
            const div = document.createElement('div');
            div.className = 'transcription';
            div.innerHTML = `
                <div class="timestamp">${message.timestamp}</div>
                <div>${message.text}</div>
                <small>⏱️ ${message.processing_time.toFixed(2)}s | 🚀 ${message.efficiency_gain.toFixed(1)}x</small>
            `;
            transcriptionsDiv.insertBefore(div, transcriptionsDiv.firstChild);
            
            // Keep only last 20 transcriptions
            while (transcriptionsDiv.children.length > 20) {
                transcriptionsDiv.removeChild(transcriptionsDiv.lastChild);
            }
        }
        
        function updateStatus(text, success) {
            statusDiv.textContent = text;
            statusDiv.className = success ? 'status success' : 'status error';
        }
    </script>
</body>
</html>
        """

# =============================================================================
# USAGE EXAMPLES
# =============================================================================

def run_streamlit_app():
    """Run Streamlit version"""
    audio_app = VerbaStreamlitAudio()
    audio_app.render_audio_interface()

def run_gradio_app():
    """Run Gradio version"""
    audio_app = VerbaGradioAudio()
    demo = audio_app.create_gradio_interface()
    demo.launch(share=True, server_name="0.0.0.0", server_port=7860)

def run_fastapi_app():
    """Run FastAPI version"""
    audio_app = VerbaFastAPIAudio()
    uvicorn.run(audio_app.app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        framework = sys.argv[1].lower()
        
        if framework == "streamlit":
            run_streamlit_app()
        elif framework == "gradio":
            run_gradio_app()
        elif framework == "fastapi":
            run_fastapi_app()
        else:
            print("Usage: python verba_gui_integration.py [streamlit|gradio|fastapi]")
    else:
        print("Available frameworks:")
        print("- streamlit: streamlit run verba_gui_integration.py")
        print("- gradio: python verba_gui_integration.py gradio")
        print("- fastapi: python verba_gui_integration.py fastapi")
