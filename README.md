# 🎯 Verba AI Transcription
### *Offline-First Audio Transcription with Speaker Diarization & AI Summarization*

<div align="center">

![Verba Banner](https://via.placeholder.com/800x200/6366f1/ffffff?text=🎯+VERBA+•+AI+Transcription+•+Privacy-First)

[![MIT License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/React-18+-61dafb.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![Whisper AI](https://img.shields.io/badge/Whisper-AI-ff6b35.svg)](https://openai.com/blog/whisper/)
[![Vercel](https://img.shields.io/badge/Demo-Vercel-000000.svg)](https://verba-devops-fawn.vercel.app/)

**🛡️ Privacy-First • 🚀 Lightning-Fast • 🤖 AI-Powered • 📱 Cross-Platform**

*Complete offline transcription with speaker identification, AI summaries, and export capabilities*

</div>

---

## 🎯 **Why Verba?**

<table>
<tr>
<td width="50%">

### 🔥 **What Makes It Special**
🛡️ **100% Privacy-First** - All AI processing happens offline  
🎙️ **Speaker Diarization** - Identifies who said what  
🤖 **AI Summarization** - Automatic key points & action items  
📄 **Multi-Format Export** - Markdown, PDF, JSON, SRT with metadata  
⚡ **Enhanced VAD** - Smart voice activity detection  
⌨️ **Keyboard Shortcuts** - Power user friendly  
📱 **Desktop Apps** - Tauri-powered native applications

</td>
<td width="50%">

### 🚀 **Perfect For**
🎓 **Students** - Record lectures, meetings, interviews  
💼 **Professionals** - Meeting notes, voice memos  
🎬 **Content Creators** - Video subtitles, podcasts  
♿ **Accessibility** - Voice-to-text for everyone  
🔬 **Researchers** - Interview transcriptions  
📝 **Writers** - Voice-to-draft your ideas  

</td>
</tr>
</table>

---

## 🛠️ **Cutting-Edge Tech Stack**

<div align="center">

| **Backend Powerhouse** | **Frontend Excellence** | **AI & Processing** |
|:---:|:---:|:---:|
| ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white) | ![React](https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black) | ![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white) |
| ![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white) | ![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white) | ![Whisper](https://img.shields.io/badge/Whisper-FF6B35?style=for-the-badge&logo=openai&logoColor=white) |
| ![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white) | ![Vite](https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white) | ![WebRTC](https://img.shields.io/badge/WebRTC-333333?style=for-the-badge&logo=webrtc&logoColor=white) |

</div>

---

## ⚡ **Quick Start Guide**

<div align="center">

### 🎬 **Get Running in 3 Steps!**

</div>

```bash
# 🔥 Step 1: Clone the repo
git clone https://github.com/OP-88/Verba.devops.git
cd Verba.devops

# 🚀 Step 2: Backend setup
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# ⚡ Step 3: Start backend server
uvicorn src.run_fastapi_audio_fixed:app --reload --host 0.0.0.0 --port 8000

# 🎨 Step 4: Frontend setup (new terminal)
cd frontend
export VITE_API_URL=http://localhost:8000  # Windows: set VITE_API_URL=http://localhost:8000
npm install && npm run dev
```

<div align="center">

**🎉 Visit `http://localhost:8080` and start transcribing! 🎉**

🌐 **[Try the Live Demo](https://verba-devops-fawn.vercel.app/)** • 📝 **[Read the Docs](./docs/)** • 🐛 **[Report Issues](https://github.com/OP-88/Verba.devops/issues)**

</div>

---

## 🎆 **Complete Feature Set**

### 🎙️ **Audio Processing**
- **⚡ Real-Time Transcription** - Live microphone recording with instant text conversion
- **📁 File Upload Support** - Process WAV, MP3, M4A, and more audio formats
- **🔊 Smart VAD** - Enhanced voice activity detection with Silero VAD
- **🎯 Noise Reduction** - Advanced audio preprocessing for clarity
- **📊 Audio Visualization** - Real-time waveform and level monitoring

### 🧑‍💼 **Speaker Intelligence**
- **🎙️ Speaker Diarization** - Automatic "who said what" identification using pyannote.audio
- **📊 Speaker Statistics** - Speaking time analysis and dominant speaker detection
- **🏷️ Smart Labeling** - Automatic speaker assignment to transcript segments
- **🔄 Segment Merging** - Intelligent combining of short speech segments

### 🤖 **AI-Powered Analysis**
- **📝 Auto-Summarization** - T5-powered summaries with key points extraction
- **🎯 Action Items** - Automatic detection of tasks and follow-ups
- **📈 Sentiment Analysis** - Meeting tone and mood detection
- **💬 Smart Chat** - AI assistant for transcript queries (hybrid mode)

### 📊 **Export & Sharing**
- **📄 Multiple Formats** - Markdown, PDF, JSON, TXT, SRT with full metadata
- **⚙️ Customizable Exports** - Include/exclude metadata, speakers, summaries
- **📋 One-Click Copy** - Instant clipboard access with formatting
- **💾 Auto-Save** - SQLite database with full history tracking

### ⌨️ **Keyboard Shortcuts**
- **Ctrl+R** - Start/Stop recording
- **Ctrl+P** - Pause/Resume recording  
- **Ctrl+C** - Copy transcription
- **Ctrl+E** - Edit transcription
- **Ctrl+S** - Save/Export
- **Esc** - Cancel current action

### 📱 **Cross-Platform**
- **🌐 Web App** - Modern React interface with PWA support
- **🖥️ Desktop Apps** - Native Tauri applications for Windows, macOS, Linux
- **📱 Mobile Responsive** - Touch-optimized interface for tablets and phones
- **☁️ Cloud Deploy** - One-click Vercel deployment ready

---

## 🏗️ **Project Architecture**

<div align="center">

```mermaid
graph TB
    A[🎤 Audio Input] --> B[🌊 WebRTC Stream]
    B --> C[⚡ FastAPI Backend]
    C --> D[🤖 Whisper AI]
    D --> E[📝 Transcription]
    E --> F[💾 SQLite Storage]
    F --> G[📱 React Frontend]
    G --> H[👤 Beautiful UI]
```

</div>

### 📁 **Crystal Clear Structure**

```
🏠 verba/
├── 🚀 backend/           # FastAPI powerhouse
│   ├── 🎯 main.py        # Server magic starts here
│   ├── 🗃️ models/        # Database schemas
│   ├── 🛣️ routes/        # API endpoints
│   ├── ⚙️ services/      # Whisper AI integration
│   └── 📋 requirements.txt
├── 💎 frontend/          # React brilliance
│   ├── 🎨 src/
│   │   ├── 🧩 components/  # Reusable UI magic
│   │   ├── 📄 pages/      # Main app screens
│   │   ├── 🔗 services/   # API communication
│   │   └── 🎯 types/      # TypeScript definitions
│   ├── 📦 package.json
│   └── ⚡ vite.config.ts
└── 📚 docs/              # Everything you need to know
```

---

## 🎯 **API Endpoints**

<div align="center">

### 🌐 **RESTful API That Just Works**

</div>

| 🚀 Method | 🎯 Endpoint | 💡 What It Does | ✨ Magic |
|:---------:|:----------:|:---------------:|:--------:|
| `GET` | `/health` | 💚 Server heartbeat | Always alive |
| `POST` | `/transcribe` | 🎤 Transform audio → text | AI-powered |
| `GET` | `/history` | 📜 Your transcription story | Full history |
| `POST` | `/history` | 💾 Save your gems | Instant storage |
| `DELETE` | `/history/{id}` | 🗑️ Clean up | One-click delete |
| `GET` | `/export/{id}` | 📤 Download magic | Multiple formats |

### 🔌 **WebSocket Superpowers**
| 🎯 Endpoint | 💫 Real-Time Magic |
|:-----------:|:------------------:|
| `/ws/transcribe` | ⚡ Live transcription stream |

---

## 🎨 **Supported Formats & Languages**

<div align="center">

<table>
<tr>
<td width="50%">

### 🎵 **Audio Formats**
```
📀 Input Support:
🔊 WAV • MP3 • M4A • FLAC
⚡ Real-time: WebRTC streams
🎯 Optimal: 16kHz, 16-bit

🤖 AI Models:
⚡ Whisper Tiny  → Lightning fast
🎯 Whisper Base  → Balanced magic
🔥 Whisper Large → Ultimate accuracy
```

</td>
<td width="50%">

### 🌍 **Global Language Support**
```
🌐 90+ Languages Including:
🇺🇸 English     🇪🇸 Spanish     🇫🇷 French
🇩🇪 German      🇮🇹 Italian     🇵🇹 Portuguese  
🇷🇺 Russian     🇯🇵 Japanese    🇰🇷 Korean
🇨🇳 Chinese     🇦🇪 Arabic      🇮🇳 Hindi
🔄 Auto-detection magic built-in!
```

</td>
</tr>
</table>

</div>

---

## 💪 **System Requirements**

<table>
<tr>
<td width="50%">

### 🎯 **Minimum Specs**
```yaml
💾 RAM: 4GB
💿 Storage: 2GB free
⚡ CPU: Dual-core
🌐 Browser: Chrome 80+ | Firefox 75+ | Safari 13+
```

</td>
<td width="50%">

### 🚀 **Recommended Power**
```yaml
🔥 RAM: 8GB+
💿 Storage: 5GB free
⚡ CPU: Quad-core+
🎮 GPU: CUDA-compatible (optional boost!)
```

</td>
</tr>
</table>

---

## 🗺️ **Development Roadmap**

<div align="center">

### 🎯 **The Journey to Transcription Excellence**

</div>

```mermaid
gantt
    title 🚀 Verba Development Timeline
    dateFormat  YYYY-MM-DD
    section 🏗️ Foundation
    Backend API Core    :active, 2024-09-15, 7d
    Database Schema     :active, 2024-09-16, 5d
    Whisper Integration :2024-09-20, 4d
    section 🎨 Frontend
    React UI Base       :2024-09-18, 6d
    WebRTC Recording    :2024-09-22, 5d
    Real-time Display   :2024-09-25, 4d
    section ✨ Polish
    Export Features     :2024-09-28, 3d
    UI/UX Enhancement   :2024-09-30, 5d
    Testing & Deploy    :2024-10-03, 4d
```

### 🎯 **Feature Status**

<div align="center">

| Phase | Feature | Status | Timeline |
|:-----:|:-------:|:------:|:--------:|
| 🏗️ | **Core API** | 🔄 In Progress | Week 1 |
| 🤖 | **Whisper AI** | ⏳ Planned | Week 2 |
| 🎨 | **React UI** | 🔄 In Progress | Week 2 |
| ⚡ | **Real-time** | ⏳ Planned | Week 3 |
| 💎 | **Export** | ⏳ Planned | Week 4 |

</div>

---

## 🤝 **Join the Revolution**

<div align="center">

### 🌟 **We Need You!**

**Help us build the future of voice transcription!**

</div>

### 🎯 **How to Contribute**

```bash
# 🍴 Fork it
git clone https://github.com/YOUR-USERNAME/Verba.devops.git

# 🌱 Branch it  
git checkout -b feature/amazing-transcription-magic

# ✨ Code it
# ... your brilliant contributions ...

# 🚀 Push it
git push origin feature/amazing-transcription-magic

# 🎉 PR it - Open a Pull Request!
```

### 💡 **Contribution Ideas**

<table>
<tr>
<td width="33%">

**🎨 Frontend Magic**
- UI/UX improvements
- New themes & designs
- Mobile responsiveness
- Accessibility features

</td>
<td width="33%">

**⚡ Backend Power**
- API optimizations
- New endpoints
- Database improvements
- Performance tuning

</td>
<td width="33%">

**🤖 AI Enhancement**
- Model optimizations
- Language support
- Accuracy improvements
- Processing speed

</td>
</tr>
</table>

---

## 🏆 **Recognition Wall**

<div align="center">

### 🌟 **Hall of Fame** 🌟

*Coming soon - your name could be here!*

**Be the first to contribute and earn your place in Verba history!** 🚀

</div>

---

## 🐛 **Known Issues & Solutions**

<div align="center">

### 🔧 **We're Transparent About Everything**

</div>

| 🐛 Issue | 💡 Status | 🎯 Solution |
|:--------:|:---------:|:----------:|
| Repository URL verification | 🔄 Working | Testing clone process |
| Development environment | ⚡ Priority | Automated setup script |
| Dependency management | 🔄 Active | Version compatibility check |

---

## 📞 **Get Help & Support**

<div align="center">

### 💬 **We're Here for You!**

</div>

<table>
<tr>
<td width="50%">

### 🆘 **Need Help?**
1. 📚 **Check Documentation** - `docs/` folder
2. 🔍 **Search Issues** - GitHub Issues tab  
3. 💬 **Ask Questions** - Create new issue
4. 🐛 **Report Bugs** - Detailed bug reports

</td>
<td width="50%">

### 🎯 **Quick Links**
- 📖 [Documentation](docs/)
- 🐛 [Report Issues](../../issues)
- 💡 [Feature Requests](../../issues)
- 🤝 [Contributing Guide](CONTRIBUTING.md)

</td>
</tr>
</table>

---

## 📄 **License**

<div align="center">

### 📜 **MIT License - Freedom to Innovate**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**🎉 Free to use, modify, and distribute! 🎉**

</div>

---

<div align="center">

## 🌟 **Star the Repo • Share the Love • Build the Future** 🌟

[![GitHub stars](https://img.shields.io/github/stars/marc-254/Verba.devops?style=social)](https://github.com/marc-254/Verba.devops/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/marc-254/Verba.devops?style=social)](https://github.com/marc-254/Verba.devops/network)
[![GitHub watchers](https://img.shields.io/github/watchers/marc-254/Verba.devops?style=social)](https://github.com/marc-254/Verba.devops/watchers)

---

### 💝 **Built with ❤️ for Developers by Developers**

*Transforming the way we interact with audio, one transcription at a time*

**🚀 Ready to revolutionize transcription? Let's build something amazing together! 🚀**

---

*Made with 🔥 passion and ⚡ cutting-edge technology*

</div>
