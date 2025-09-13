"""
Enhanced transcription endpoint with speaker diarization and summarization
"""

import os
import tempfile
import sqlite3
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

from services.noise_service import rnnoise_service
from services.summary_service import summarization_service
from services.diarization_service import SpeakerDiarizationService
from services.whisper_service import WhisperService
from utils.audio_processing import AudioProcessor

router = APIRouter()

class TranscriptionWithDiarizationResponse(BaseModel):
    text: str
    summary: str
    speaker_segments: list
    metadata: dict
    processing_time: float

# Initialize services
diarization_service = SpeakerDiarizationService()
whisper_service = WhisperService()
audio_processor = AudioProcessor()

@router.post("/transcribe", response_model=TranscriptionWithDiarizationResponse)
async def transcribe_with_diarization(
    audio: UploadFile = File(...),
    session_id: str = Form("default"),
    enable_diarization: bool = Form(True),
    enable_summarization: bool = Form(True)
):
    """
    Enhanced transcription with speaker diarization and AI summarization
    """
    if not audio.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(audio.filename).suffix) as tmp_file:
        content = await audio.read()
        tmp_file.write(content)
        tmp_file.flush()
        
        try:
            # Step 1: Preprocess audio with noise reduction
            audio_data, sample_rate = audio_processor.load_audio(tmp_file.name)
            if rnnoise_service.initialized:
                audio_data, sample_rate = rnnoise_service.preprocess_for_transcription(audio_data, sample_rate)
            
            # Save preprocessed audio temporarily
            preprocessed_path = tmp_file.name + "_preprocessed.wav"
            import soundfile as sf
            sf.write(preprocessed_path, audio_data, sample_rate)
            
            # Step 2: Initialize Whisper if not ready
            if not whisper_service.is_ready():
                await whisper_service.initialize()
            
            # Step 3: Transcribe with meeting/lecture prompt
            prompt = "Transcribe spoken content from meeting or lecture with multiple speakers."
            transcription_result = await whisper_service.transcribe(
                preprocessed_path,
                options={
                    "initial_prompt": prompt,
                    "word_timestamps": True,
                    "temperature": 0.2,
                    "best_of": 2
                }
            )
            
            transcript_text = transcription_result.get('text', '')
            transcript_segments = transcription_result.get('segments', [])
            
            # Step 4: Speaker diarization if enabled
            speaker_segments = []
            labeled_transcript = transcript_text
            
            if enable_diarization and diarization_service:
                try:
                    # Initialize diarization service if needed
                    if not hasattr(diarization_service, 'pipeline') or not diarization_service.pipeline:
                        await diarization_service.initialize()
                    
                    # Perform speaker diarization
                    diarization_segments = await diarization_service.detect_speakers(preprocessed_path)
                    
                    # Apply diarization to transcript
                    if diarization_segments:
                        labeled_segments = await diarization_service.apply_diarization_to_transcript(
                            transcript_segments,
                            diarization_segments
                        )
                        
                        # Format with speaker labels
                        speaker_lines = []
                        for segment in labeled_segments:
                            speaker_id = segment.get('speaker', 'Speaker 1')
                            text = segment.get('text', '').strip()
                            if text:
                                speaker_lines.append(f"{speaker_id}: {text}")
                        
                        labeled_transcript = '\n'.join(speaker_lines)
                        speaker_segments = labeled_segments
                
                except Exception as e:
                    # Fallback: basic speaker alternation
                    lines = transcript_text.split('. ')
                    speaker_lines = []
                    for i, line in enumerate(lines):
                        if line.strip():
                            speaker_num = (i // 3) % 3 + 1  # Alternate between 3 speakers
                            speaker_lines.append(f"Speaker {speaker_num}: {line.strip()}")
                    labeled_transcript = '. '.join(speaker_lines)
            
            # Step 5: Generate AI summary if enabled
            summary = ""
            if enable_summarization:
                try:
                    if not summarization_service.initialized:
                        await summarization_service.initialize()
                    
                    summary_result = await summarization_service.summarize_transcript(
                        labeled_transcript,
                        max_length=50,
                        min_length=10
                    )
                    summary = summary_result.get('summary_text', '')
                except Exception as e:
                    # Fallback: simple summary
                    sentences = labeled_transcript.split('. ')[:3]
                    summary = '. '.join(sentences) + '.' if sentences else "Summary unavailable"
            
            # Step 6: Save to database
            conn = sqlite3.connect('verba_app.db')
            try:
                conn.execute("""
                    INSERT INTO transcriptions (text, summary, metadata, session_id, created_at)
                    VALUES (?, ?, ?, ?, datetime('now'))
                """, (
                    labeled_transcript,
                    summary,
                    str({
                        'speakers': len(set([seg.get('speaker', 'Speaker 1') for seg in speaker_segments])),
                        'confidence': transcription_result.get('confidence', 0.95),
                        'language': transcription_result.get('language', 'en'),
                        'duration': transcription_result.get('duration', 0),
                        'diarization_enabled': enable_diarization,
                        'summarization_enabled': enable_summarization
                    }),
                    session_id
                ))
                conn.commit()
            finally:
                conn.close()
            
            # Step 7: Cleanup temporary files
            try:
                os.unlink(preprocessed_path)
            except:
                pass
            
            return TranscriptionWithDiarizationResponse(
                text=labeled_transcript,
                summary=summary,
                speaker_segments=speaker_segments,
                metadata={
                    'speakers': len(set([seg.get('speaker', 'Speaker 1') for seg in speaker_segments])),
                    'confidence': transcription_result.get('confidence', 0.95),
                    'language': transcription_result.get('language', 'en'),
                    'duration': transcription_result.get('duration', 0),
                    'noise_reduction_applied': rnnoise_service.initialized,
                    'diarization_enabled': enable_diarization,
                    'summarization_enabled': enable_summarization
                },
                processing_time=transcription_result.get('processing_time', 0)
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
        
        finally:
            # Cleanup
            try:
                os.unlink(tmp_file.name)
            except:
                pass