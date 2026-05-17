import os
import tempfile

import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel


class VoiceTranscriber:
    def __init__(
        self,
        model_size="base",
        device="cpu",
        compute_type="int8",
        language="ru",
    ):
        self.language = language

        self.model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type,
        )

    def transcribe_audio(self, audio, sample_rate=16000):
        audio = np.asarray(audio, dtype=np.float32)
        audio = np.clip(audio, -1.0, 1.0)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp:
            temp_path = temp.name

        try:
            sf.write(temp_path, audio, sample_rate)

            segments, _ = self.model.transcribe(
                temp_path,
                language=self.language,
                vad_filter=True,
            )

            text = " ".join(
                segment.text.strip()
                for segment in segments
                if segment.text.strip()
            )

            return text.strip()

        finally:
            try:
                os.remove(temp_path)
            except OSError:
                pass
