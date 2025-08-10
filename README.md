# Verba - Offline AI Meeting Assistant

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Development Status](https://img.shields.io/badge/status-beta-orange.svg)](https://github.com/marc-254/Verba.devops)

**Verba** is a privacy-first, offline AI transcription assistant that runs efficiently on low-spec devices. Perfect for students, professionals, and anyone who needs reliable speech-to-text without internet dependency or cloud services.

## ✨ Key Features

- **🎙️ Real-Time Transcription** - Live speech-to-text using OpenAI Whisper
- **🔒 100% Offline** - No internet required, complete privacy protection  
- **📝 Smart Summarization** - AI-generated meeting summaries with Hugging Face models
- **🔇 Noise Reduction** - Clean audio processing with RNNoise
- **💾 Local Storage** - All data stays on your device
- **⚡ Resource Efficient** - Runs smoothly on 4GB RAM systems
- **🎯 Multiple Input Modes** - Microphone, system audio, or file upload
- **⌨️ Keyboard Shortcuts** - Quick recording with `Ctrl+T`

## 🚀 Quick Start

### Prerequisites

- **Python 3.8 or higher**
- **Node.js and npm** (temporary - being phased out)
- **Minimum 4GB RAM**
- **2GB free disk space** (for AI models)

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/marc-254/Verba.devops.git
cd Verba.devops
```

2. **Install Python dependencies:**
```bash
pip install -r backend/requirements.txt
```

3. **Install frontend dependencies** (temporary):
```bash
npm install
```

4. **Download AI models** (first run only):
```bash
cd backend
python download_models.py
```

### Running Verba

1. **Start the backend server:**
```bash
cd backend
uvicorn main:app --host 127.0.0.1 --port 8000
```

2. **Start the frontend** (in a new terminal):
```bash
npm run dev
```

3. **Open your browser:** Navigate to `http://localhost:5173`

### First-Time Setup

1. **Test your microphone** - Click the microphone test button
2. **Choose input mode** - Select between microphone or system audio
3. **Start recording** - Press the Record button or use `Ctrl+T`
4. **View transcription** - See real-time text appear as you speak
5. **Get summary** - AI automatically generates meeting summaries

## 📋 System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **RAM** | 4GB | 8GB |
| **CPU** | Any modern processor | Multi-core preferred |
| **Storage** | 2GB free space | 4GB free space |
| **OS** | Windows 10, macOS 10.15, Ubuntu 20.04+ | Latest versions |
| **Audio** | Built-in mic/speakers | External microphone |

## 🎯 Usage Examples

### Recording a Meeting
1. Select "Microphone" mode
2. Press `Ctrl+T` or click Record
3. Speak normally - transcription appears in real-time
4. Press `Ctrl+T` again to stop
5. Review and save your notes

### Transcribing Online Meetings
1. Select "System Audio" mode  
2. Join your Zoom/Teams meeting
3. Start Verba recording
4. Get transcripts of all participants
5. Generate automatic meeting summary

### Processing Audio Files
1. Click "Upload File" button
2. Select your audio file (MP3, WAV, M4A, FLAC)
3. Wait for processing to complete
4. Download transcription and summary

## 🏗️ Architecture Roadmap

Verba is transitioning to a more efficient, native desktop architecture:

```
Current (Beta):     React Frontend ↔ Python Backend
Target (v1.0):      Native Desktop ↔ Python Backend  
Future (v2.0):      Single Binary Executable
```

### Upcoming Changes
- **Native Desktop App** - Moving away from React for better performance
- **Single Binary** - No installation required, just download and run
- **Enhanced Security** - Advanced protection against reverse engineering
- **Improved Efficiency** - Even lower memory usage and faster processing

## 🔒 Privacy & Security

- **Zero Data Transmission** - Nothing leaves your device
- **Local Processing** - All AI models run offline
- **No Telemetry** - We don't collect any usage data  
- **Secure Storage** - Transcripts saved locally with user control
- **Open Source** - Full transparency in our code

## 🛠️ Development Status

| Component | Status | Progress |
|-----------|--------|----------|
| **Frontend UI** | ✅ Complete | 99% |
| **Backend API** | 🚧 In Progress | 75% |
| **AI Models** | ✅ Integrated | 90% |
| **Desktop App** | 📋 Planned | 0% |
| **Security Features** | 🚧 In Progress | 50% |

**Current Focus:** Completing backend stability and beginning native desktop migration.

## 📅 Development Timeline

- **August 2025** - Beta release with web interface
- **September 2025** - Native desktop app alpha  
- **October 2025** - Security hardening and optimization
- **November 2025** - Version 1.0 stable release

## 🤝 Contributing

We welcome contributions! Please help us improve Verba:

### How to Help
- **🐛 Report Bugs** - Open issues for any problems you find
- **💡 Suggest Features** - Share ideas for improvements  
- **🧪 Test on Low-Spec Devices** - Help us optimize performance
- **📚 Improve Documentation** - Make setup easier for others
- **🔊 Test in Noisy Environments** - Help improve audio processing

### Development Setup
```bash
# Fork the repo and clone your fork
git clone https://github.com/YOUR-USERNAME/Verba.devops.git
cd Verba.devops

# Create a feature branch
git checkout -b feature/your-feature-name

# Make your changes and test thoroughly
# Submit a pull request with clear description
```

## 📖 Documentation

- **[Installation Guide](docs/installation.md)** - Detailed setup instructions
- **[User Manual](docs/user-guide.md)** - Complete usage documentation  
- **[API Documentation](docs/api.md)** - Backend API reference
- **[Development Guide](docs/development.md)** - Contributing guidelines
- **[Timeline](docs/timeline.md)** - Project roadmap and milestones

## ⚡ Performance Tips

- **Close unnecessary applications** to free up RAM
- **Use a good microphone** for better transcription accuracy
- **Speak clearly** and avoid background noise when possible
- **Regular restarts** help maintain optimal performance
- **Keep audio files under 2 hours** for best processing speed

## ❓ Troubleshooting

### Common Issues

**"Models not found" error:**
```bash
cd backend
python download_models.py
```

**High memory usage:**
- Close other applications
- Restart Verba periodically  
- Use shorter recording sessions

**Poor transcription quality:**
- Check microphone settings
- Reduce background noise
- Speak closer to the microphone
- Try adjusting audio input levels

**Can't connect to backend:**
- Ensure backend is running on port 8000
- Check if another app is using the port
- Restart both frontend and backend

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Mark Munene** - [@marc-254](https://github.com/marc-254)

## 🙏 Acknowledgments

- **OpenAI** for the Whisper speech recognition model
- **Hugging Face** for transformer-based summarization
- **RNNoise** project for audio noise reduction
- **Open source community** for inspiration and support

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/marc-254/Verba.devops/issues)
- **Discussions:** [GitHub Discussions](https://github.com/marc-254/Verba.devops/discussions)  
- **Email:** Contact via GitHub profile

---

**⭐ Star this repo if Verba helps you stay organized and productive!**

*Built with ❤️ for students, professionals, and anyone who values privacy and efficiency.*
