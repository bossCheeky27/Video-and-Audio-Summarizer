import os
import subprocess
import wave
import numpy as np
from faster_whisper import WhisperModel
from config import WHISPER_MODEL
import database as db


_model = None


def get_model():
    global _model
    if _model is None:
        print(f"Loading Whisper model '{WHISPER_MODEL}'...")
        _model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
        print("Whisper model loaded.")
    return _model


def extract_audio(video_path):
    """Extract audio from a video or audio file as 16kHz mono WAV using FFmpeg."""
    # Distinct suffix so a .wav upload is never overwritten (or deleted) as its own temp file
    audio_path = os.path.splitext(video_path)[0] + '_whisper.wav'
    command = [
        'ffmpeg', '-i', video_path,
        '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1',
        '-y', audio_path
    ]
    try:
        subprocess.run(command, check=True, capture_output=True)
        return audio_path
    except subprocess.CalledProcessError as e:
        raise Exception(f"FFmpeg error: {e.stderr.decode()}")
    except FileNotFoundError:
        raise Exception("FFmpeg not found. Please install FFmpeg and add it to your PATH.")


def load_wav(audio_path):
    """Load a 16kHz mono 16-bit WAV (as written by extract_audio) into a float32 array.

    Passing samples instead of a path skips faster-whisper's PyAV decoder, which breaks
    on newer PyAV releases (open() got an unexpected keyword argument 'metadata_errors').
    """
    with wave.open(audio_path, 'rb') as wav:
        frames = wav.readframes(wav.getnframes())
    return np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0


def transcribe_video(video_path, lecture_id=None):
    """Transcribe a video or audio file. Returns the transcript text."""
    audio_path = None
    try:
        print("Extracting audio...")
        audio_path = extract_audio(video_path)

        print("Transcribing audio with Whisper...")
        model = get_model()
        segments, info = model.transcribe(load_wav(audio_path), beam_size=5, language="en")
        duration = info.duration
        print(f"Audio duration: {duration:.0f}s")

        parts = []
        for segment in segments:
            parts.append(segment.text)
            if duration > 0:
                pct = min(100, int(segment.end / duration * 100))
                print(f"Transcribed {segment.end:.0f}s / {duration:.0f}s ({pct}%)")
                if lecture_id is not None:
                    db.update_lecture_progress(lecture_id, pct)

        transcript = " ".join(parts)
        print("Transcription finished.")
        return transcript
    finally:
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)


def transcribe_audio(audio_path, lecture_id=None):
    """Transcribe an audio file directly. Returns the transcript text."""
    print("Transcribing audio with Whisper...")
    model = get_model()
    segments, info = model.transcribe(audio_path, beam_size=5, language="en")
    duration = info.duration

    parts = []
    for segment in segments:
        parts.append(segment.text)
        if duration > 0 and lecture_id is not None:
            db.update_lecture_progress(lecture_id, min(100, int(segment.end / duration * 100)))

    return " ".join(parts)
