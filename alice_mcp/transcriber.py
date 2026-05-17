"""Распознавание речи (STT) через faster-whisper.

Модель грузится один раз при старте. Если faster-whisper не установлен
или модель не загрузилась — транскрайбер работает в «пустом» режиме:
возвращает "" и не роняет сервис.
"""

import os
import tempfile

import numpy as np
import soundfile as sf

# faster-whisper опционален — сервис должен подниматься и без него.
try:
    from faster_whisper import WhisperModel

    _WHISPER_AVAILABLE = True
except Exception:  # noqa: BLE001
    _WHISPER_AVAILABLE = False


class VoiceTranscriber:
    def __init__(
        self,
        model_size="base",
        device="cpu",
        compute_type="int8",
        language="ru",
    ):
        self.language = language
        self.model = None
        self.enabled = False

        if not _WHISPER_AVAILABLE:
            print("VoiceTranscriber: faster-whisper не установлен — STT отключён.")
            return

        try:
            self.model = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type,
            )
            self.enabled = True
            print(f"VoiceTranscriber: модель Whisper «{model_size}» загружена.")
        except Exception as e:  # noqa: BLE001
            self.model = None
            self.enabled = False
            print(f"VoiceTranscriber: не удалось загрузить модель ({e}) — STT отключён.")

    def transcribe_audio(self, audio, sample_rate=16000) -> str:
        """Аудио (numpy float32) → распознанный текст. При сбое — пустая строка."""
        if not self.enabled or self.model is None:
            return ""

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
        except Exception as e:  # noqa: BLE001
            print(f"VoiceTranscriber: ошибка распознавания ({e})")
            return ""
        finally:
            try:
                os.remove(temp_path)
            except OSError:
                pass
