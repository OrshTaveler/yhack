import os
import time
from collections import deque

import numpy as np
import torch
import torch.nn.functional as F
import soundfile as sf

try:
    from speechbrain.inference.speaker import EncoderClassifier
except ImportError:
    from speechbrain.pretrained import EncoderClassifier


ENROLLED_VOICE_FILE = "allowed_speaker.wav"

SAMPLE_RATE = 16000

WINDOW_SECONDS = 5.0
CHECK_EVERY_SECONDS = 1
MATCH_THRESHOLD = 0.45
SILENCE_RMS_THRESHOLD = 0.012


def calculate_rms(audio):
    return float(np.sqrt(np.mean(audio ** 2)))


def calculate_dbfs(audio):
    rms = np.sqrt(np.mean(audio ** 2))

    if rms <= 1e-10:
        return -100.0

    return float(20 * np.log10(rms))


def update_background_noise(old_value, new_value, alpha=0.2):
    if old_value is None:
        return new_value

    return old_value * (1 - alpha) + new_value * alpha


def audio_numpy_to_tensor(audio_np):
    audio_np = np.asarray(audio_np, dtype=np.float32)
    audio_np = np.clip(audio_np, -1.0, 1.0)

    tensor = torch.from_numpy(audio_np).float()
    tensor = tensor.unsqueeze(0)

    return tensor


def load_enrolled_audio(path):
    audio_np, sample_rate = sf.read(path, dtype="float32")

    if audio_np.ndim > 1:
        audio_np = np.mean(audio_np, axis=1)

    if sample_rate != SAMPLE_RATE:
        raise ValueError(
            f"{path} must be {SAMPLE_RATE} Hz, but it is {sample_rate} Hz. "
            "Convert it to 16 kHz mono first."
        )

    audio_np = np.clip(audio_np, -1.0, 1.0)

    tensor = torch.from_numpy(audio_np).float()
    tensor = tensor.unsqueeze(0)

    return tensor


def get_embedding(classifier, audio_tensor):
    with torch.no_grad():
        embedding = classifier.encode_batch(audio_tensor)

    return embedding.squeeze()


def cosine_similarity(embedding_a, embedding_b):
    return float(
        F.cosine_similarity(
            embedding_a.unsqueeze(0),
            embedding_b.unsqueeze(0),
        ).item()
    )


class VoiceDetector:
    def __init__(
        self,
        enrolled_voice_file=ENROLLED_VOICE_FILE,
        sample_rate=SAMPLE_RATE,
        window_seconds=WINDOW_SECONDS,
        check_every_seconds=CHECK_EVERY_SECONDS,
        match_threshold=MATCH_THRESHOLD,
        silence_rms_threshold=SILENCE_RMS_THRESHOLD,
    ):
        self.enrolled_voice_file = enrolled_voice_file
        self.sample_rate = sample_rate
        self.window_seconds = window_seconds
        self.check_every_seconds = check_every_seconds
        self.match_threshold = match_threshold
        self.silence_rms_threshold = silence_rms_threshold

        if not os.path.exists(self.enrolled_voice_file):
            raise FileNotFoundError(
                f"Missing enrolled voice file: {self.enrolled_voice_file}"
            )

        self.classifier = EncoderClassifier.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb",
            savedir="pretrained_models/spkrec-ecapa-voxceleb",
        )

        enrolled_audio = load_enrolled_audio(self.enrolled_voice_file)
        self.enrolled_embedding = get_embedding(self.classifier, enrolled_audio)

        self.audio_buffer = deque(
            maxlen=int(self.sample_rate * self.window_seconds * 2)
        )

        self.last_check_time = time.time()
        self.background_noise_dbfs = None

    def process_audio(self, audio):
        audio = np.asarray(audio, dtype=np.float32)
        audio = np.clip(audio, -1.0, 1.0)
    
        rms = calculate_rms(audio)
    
        if rms < self.silence_rms_threshold:
            current_dbfs = calculate_dbfs(audio)
    
            self.background_noise_dbfs = update_background_noise(
                self.background_noise_dbfs,
                current_dbfs,
            )
    
            return {
                "status": "silence",
                "sampled_person_speaking": False,
                "score": None,
                "current_dbfs": round(current_dbfs, 1),
                "background_noise_dbfs": round(self.background_noise_dbfs, 1),
                "rms": round(rms, 4),
            }
    
        live_tensor = audio_numpy_to_tensor(audio)
        live_embedding = get_embedding(self.classifier, live_tensor)
    
        score = cosine_similarity(self.enrolled_embedding, live_embedding)
        sampled_person_speaking = score >= self.match_threshold
    
        current_dbfs = calculate_dbfs(audio)
    
        if sampled_person_speaking:
            status = "sampled_person_speaking"
        else:
            status = "other_speaker_or_unknown"
            self.background_noise_dbfs = update_background_noise(
                self.background_noise_dbfs,
                current_dbfs,
            )
    
        return {
            "status": status,
            "sampled_person_speaking": sampled_person_speaking,
            "score": round(score, 3),
            "current_dbfs": round(current_dbfs, 1),
            "background_noise_dbfs": (
                None
                if self.background_noise_dbfs is None
                else round(self.background_noise_dbfs, 1)
            ),
            "rms": round(rms, 4),
        }