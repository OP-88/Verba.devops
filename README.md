# Verba: Offline-First Audio Transcription System

## Overview

Verba is an open-source, AI-powered meeting assistant for transcribing, summarizing, and storing notes from lectures and meetings. It runs offline on low-spec devices (4GB RAM) using Whisper, RNNoise, and Hugging Face Transformers. Verba is free, sustained by voluntary donations, and designed for students, professionals, and low-resource settings.

## Features

- **Real-Time Transcription**: Converts audio to text using OpenAI Whisper.
- **Offline Mode**: Fully functional without internet.
- **Summarization**: Generates concise summaries with Hugging Face Transformers.
- **Noise Reduction**: Cleans audio with RNNoise.
- **Note Storage**: Saves transcripts and summaries locally.
- **Simple UI**: Built with Vite, TypeScript, shadcn-ui, and Tailwind CSS.

## Installation

1. Clone the repo: `git clone https://github.com/marc-254/hello-world-wizardry-time.git`
2. Install UI dependencies: `cd hello-world-wizardry-time && npm i`
3. Install backend dependencies: `pip install -r backend/requirements.txt`
4. Run the UI: `npm run dev`
5. Run the backend: `cd backend && uvicorn main:app --host 0.0.0.0 --port 8000`

**Requirements**:

- Node.js, npm (UI)
- Python 3.8+, Whisper, transformers, RNNoise (backend)
- Minimum 4GB RAM

## Usage

1. Open the UI at `http://localhost:5173`.
2. Select input mode (mic for physical meetings, system audio for online).
3. Start transcription with the “Record” button or `Ctrl+T`.
4. View real-time transcripts and summaries.
5. Save notes locally or toggle hybrid mode (v1.2).

## Project Status

- **UI**: 99% complete (Tauri-based shell with dark mode, mode toggle).
- **Backend**: In progress (Whisper Tiny, RNNoise, summarization).
- **Timeline**: Aug 20–Sept 23, 2025 (see [docs/timeline.md](docs/timeline.md)).

## Contributing

We welcome feedback! Please:

- Open issues for bugs or suggestions.
- Submit pull requests with clear descriptions.
- Test on low-spec devices or noisy environments.

## License

MIT License

## Contact

Developed by Mark Munene. Reach out via GitHub Issues.
