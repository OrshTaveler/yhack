import base64
import io
import wave
from typing import Optional

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from voice_filter_stream import VoiceDetector

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

detector = VoiceDetector()


class VoiceRecognitionRequest(BaseModel):
    audio_data: str
    sample_rate: int = 16000


class VoiceRecognitionResponse(BaseModel):
    status: str
    sampled_person_speaking: bool
    score: Optional[float] = None
    current_dbfs: float
    background_noise_dbfs: Optional[float] = None
    rms: float


@app.get("/health")
def health():
    return {"status": "ok"}


def decode_wav_base64(audio_base64: str) -> tuple[np.ndarray, int]:
    if "," in audio_base64:
        audio_base64 = audio_base64.split(",", 1)[1]

    audio_bytes = base64.b64decode(audio_base64)

    with wave.open(io.BytesIO(audio_bytes), "rb") as wav:
        channels = wav.getnchannels()
        sample_width = wav.getsampwidth()
        sample_rate = wav.getframerate()
        frames = wav.readframes(wav.getnframes())

    if sample_width != 2:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported WAV sample width: {sample_width}. Expected 16-bit PCM.",
        )

    audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0

    if channels > 1:
        audio = audio.reshape(-1, channels).mean(axis=1)

    if audio.size == 0:
        raise HTTPException(status_code=400, detail="Empty audio chunk")

    return audio, sample_rate


@app.post("/recognize-voice", response_model=VoiceRecognitionResponse)
async def recognize_voice(request: VoiceRecognitionRequest):
    try:
        audio_chunk, sample_rate = decode_wav_base64(request.audio_data)

        result = detector.process_audio(audio_chunk)

        print("DETECTOR RESULT:", result)

        if result is None:
            raise HTTPException(status_code=400, detail="No voice detected")

        return VoiceRecognitionResponse(
            status=result["status"],
            sampled_person_speaking=result["sampled_person_speaking"],
            score=result.get("score"),
            current_dbfs=result["current_dbfs"],
            background_noise_dbfs=result.get("background_noise_dbfs"),
            rms=result["rms"],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))