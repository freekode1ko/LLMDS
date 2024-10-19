import logging
import torch
import librosa
from transformers import WhisperProcessor, WhisperForConditionalGeneration


class WhisperHandler:
    """
    Класс WhisperHandler предоставляет функционал для использования модели Whisper
    для преобразования аудио в текст.
    """

    def __init__(self):
        """
        Инициализирует модель Whisper Large v3 из Hugging Face и процессор для обработки аудиоданных.
        """
        self.processor = WhisperProcessor.from_pretrained("openai/whisper-large-v3")
        self.model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-large-v3").to(
            "cuda" if torch.cuda.is_available() else "cpu")

    def transcribe_audio(self, audio_path: str) -> str:
        """
        Преобразует аудиофайл в текст с использованием модели Whisper.

        Args:
            audio_path (str): Путь к аудиофайлу для транскрипции.

        Returns:
            str: Распознанный текст из аудиофайла.
        """
        try:
            # Загрузка аудиофайла
            audio, sr = librosa.load(audio_path, sr=16000)

            # Подготовка аудиоданных для Whisper
            input_features = self.processor(audio, sampling_rate=16000, return_tensors="pt").input_features

            # Передача данных в модель
            input_features = input_features.to("cuda" if torch.cuda.is_available() else "cpu")
            generated_ids = self.model.generate(input_features)

            # Декодирование выходных данных в текст
            transcription = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

            return transcription
        except Exception as e:
            logging.error(f"Ошибка при транскрипции аудиофайла: {e}")
            return "Не удалось транскрибировать аудиофайл."
