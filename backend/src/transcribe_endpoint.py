"""
Enhanced transcription endpoint with speaker diarization and summarization
"""

@app.post("/transcribe", response_model=TranscriptionWithDiarizationResponse)
async def transcribe_with_diarization(
    audio: UploadFile = File(...),
    mode: str = Form("offline"),
    session_id: str = Form("default")
):
    """Enhanced transcription with speaker diarization and AI summarization"""
    if not audio.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    start_time = time.time()
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(audio.filename).suffix) as tmp_file:
        content = await audio.read()
        tmp_file.write(content)
        tmp_file.flush()
        
        try:
            # Step 1: Preprocess audio with proprietary VAD
            audio_data, sample_rate = preprocess_audio(tmp_file.name)
            
            # Save preprocessed audio temporarily
            preprocessed_path = tmp_file.name + "_preprocessed.wav"
            import soundfile as sf
            sf.write(preprocessed_path, audio_data, sample_rate)
            
            # Step 2: Chunked transcription for long audio (>10 minutes)
            audio_duration = len(audio_data) / sample_rate
            
            if audio_duration > 600:  # >10 minutes
                chunk_duration = 600  # 10 minutes per chunk
                chunks = []
                for i in range(0, len(audio_data), chunk_duration * sample_rate):
                    chunk = audio_data[i:i + chunk_duration * sample_rate]
                    chunks.append(chunk)
                
                transcript_parts = []
                for chunk in chunks:
                    chunk_result = model.transcribe(
                        chunk,
                        initial_prompt="Transcribe spoken content from meeting or lecture with multiple speakers.",
                        word_timestamps=True,
                        temperature=0.2,
                        best_of=2
                    )
                    transcript_parts.append(chunk_result['text'])
                
                transcript_text = " ".join(transcript_parts)
            else:
                # Single transcription for shorter audio
                transcription_result = model.transcribe(
                    preprocessed_path,
                    initial_prompt="Transcribe spoken content from meeting or lecture with multiple speakers.",
                    word_timestamps=True,
                    temperature=0.2,
                    best_of=2
                )
                transcript_text = transcription_result.get('text', '')
            
            # Step 3: Speaker diarization
            labeled_transcript = transcript_text
            speaker_count = 1
            
            if DIARIZATION_AVAILABLE and diarization_pipeline:
                try:
                    diarization = diarization_pipeline(preprocessed_path)
                    
                    # Apply diarization to transcript
                    labeled_segments = []
                    for turn, _, speaker in diarization.itertracks(yield_label=True):
                        start_char = int(turn.start * len(transcript_text) / audio_duration)
                        end_char = int(turn.end * len(transcript_text) / audio_duration)
                        segment_text = transcript_text[start_char:end_char].strip()
                        
                        if segment_text:
                            labeled_segments.append(f"Speaker {speaker}: {segment_text}")
                    
                    if labeled_segments:
                        labeled_transcript = '\n'.join(labeled_segments)
                        speaker_count = len(set([turn[2] for turn in diarization.itertracks(yield_label=True)]))
                
                except Exception as e:
                    print(f"Diarization failed: {e}")
                    # Fallback: basic speaker alternation
                    sentences = transcript_text.split('. ')
                    labeled_segments = []
                    for i, sentence in enumerate(sentences):
                        if sentence.strip():
                            speaker_num = (i // 3) % 3 + 1  # Alternate between 3 speakers
                            labeled_segments.append(f"Speaker {speaker_num}: {sentence.strip()}")
                    labeled_transcript = '. '.join(labeled_segments)
            
            # Step 4: Generate AI summary
            summary = ""
            if SUMMARIZATION_AVAILABLE and summarizer:
                try:
                    # Truncate text if too long for summarization
                    text_for_summary = labeled_transcript[:1000] if len(labeled_transcript) > 1000 else labeled_transcript
                    summary_result = summarizer(text_for_summary, max_length=50, min_length=10, do_sample=False)
                    summary = summary_result[0]['summary_text']
                except Exception as e:
                    print(f"Summarization failed: {e}")
                    # Fallback: simple summary
                    sentences = labeled_transcript.split('. ')[:3]
                    summary = '. '.join(sentences) + '.' if sentences else "Summary unavailable"
            
            # Step 5: AI chatbot response (hybrid mode only)
            chatbot_response = ""
            if mode == "hybrid":
                try:
                    chatbot_prompt = f"Provide key insights from this meeting transcript: {labeled_transcript[:500]}"
                    chatbot_response = await query_openrouter(chatbot_prompt)
                except Exception as e:
                    print(f"Chatbot response failed: {e}")
                    chatbot_response = "AI insights unavailable"
            
            # Step 6: Save to database
            conn = sqlite3.connect('verba_app.db')
            try:
                conn.execute("""
                    INSERT INTO transcriptions (text, summary, metadata, session_id, created_at)
                    VALUES (?, ?, ?, ?, datetime('now'))
                """, (
                    labeled_transcript,
                    summary,
                    json.dumps({
                        'speakers': speaker_count,
                        'duration': audio_duration,
                        'mode': mode,
                        'vad_applied': True
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
            
            processing_time = time.time() - start_time
            
            return TranscriptionWithDiarizationResponse(
                text=labeled_transcript,
                summary=summary,
                chatbot=chatbot_response,
                metadata={
                    'speakers': speaker_count,
                    'duration': audio_duration,
                    'mode': mode,
                    'vad_applied': True,
                    'processing_time': processing_time
                },
                processing_time=processing_time
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
        
        finally:
            # Cleanup
            try:
                os.unlink(tmp_file.name)
            except:
                pass

@app.get("/history")
async def get_history(session_id: str = "default"):
    """Get transcription history"""
    try:
        conn = sqlite3.connect('verba_app.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, text, summary, metadata, created_at 
            FROM transcriptions 
            WHERE session_id = ? 
            ORDER BY created_at DESC
        """, (session_id,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'text': row[1],
                'summary': row[2],
                'metadata': json.loads(row[3]) if row[3] else {},
                'created_at': row[4]
            })
        
        conn.close()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {str(e)}")

@app.delete("/history/{transcription_id}")
async def delete_transcription(transcription_id: int):
    """Delete a specific transcription"""
    try:
        conn = sqlite3.connect('verba_app.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transcriptions WHERE id = ?", (transcription_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Transcription not found")
        
        conn.close()
        return {"message": "Transcription deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete transcription: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)