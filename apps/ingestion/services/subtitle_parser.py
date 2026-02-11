import re
from collections import Counter
from typing import List, Iterable

from apps.dictionary.models import Word
from apps.ingestion.services.nlp_loader import load_nlp


class SubtitleWord:
    def __init__(
        self,
        name: str,
        frequency: int,
        transcription: str = "",
        selected_pos: str = "",
        selected_translation: str = "",
        pos_list: list[str] | None = None,
        translations_for_pos: dict[str, list[str]] | None = None,
    ):
        self.name = name
        self.frequency = frequency
        self.transcription = transcription
        self.selected_pos = selected_pos
        self.selected_translation = selected_translation
        self.pos_list = pos_list or []
        self.translations_for_pos = translations_for_pos or {}


class ConvertTextToSubtitleWords:
    keep_pos = {"NOUN", "VERB", "ADJ"}
    min_len = 2
    chunk_size = 20000  # размер чанка текста (символы)

    def __init__(self, text: str):
        self.nlp = load_nlp()
        self.subtitle_words: List[SubtitleWord] = self._convert(text)

    # =========================
    # Основной pipeline
    # =========================

    def _convert(self, text: str) -> List[SubtitleWord]:
        text = self._clean_text(text)
        word_counter = self._get_word_frequencies(text)
        return self._map_existing_words(word_counter)

    # =========================
    # Очистка текста
    # =========================

    def _clean_text(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"\d*:\d*:.*\n", "", text)
        text = re.sub(r"<[^>]*>", "", text)
        text = re.sub(r"\n+", " ", text)
        text = re.sub(r"[0-9]", "", text)
        text = re.sub(r"[^\w\s]", " ", text)
        return text.strip()

    # =========================
    # Чанкование
    # =========================

    def _chunk_text(self, text: str) -> Iterable[str]:
        for i in range(0, len(text), self.chunk_size):
            yield text[i : i + self.chunk_size]

    # =========================
    # NLP обработка
    # =========================

    def _get_word_frequencies(self, text: str) -> Counter:
        words = []

        for doc in self.nlp.pipe(
            self._chunk_text(text),
            batch_size=32,
        ):
            for token in doc:
                if token.is_stop or token.is_punct or token.is_space:
                    continue

                lemma = token.lemma_.lower()

                if len(lemma) < self.min_len:
                    continue

                if self.keep_pos and token.pos_.upper() not in self.keep_pos:
                    continue

                words.append(lemma)

        return Counter(words)

    # =========================
    # Работа с БД
    # =========================

    def _map_existing_words(self, word_counter: Counter) -> List[SubtitleWord]:
        subtitle_words = []

        if not word_counter:
            return subtitle_words

        existing_words_qs = Word.objects.filter(
            name__in=word_counter.keys()
        ).prefetch_related("parts_of_speech__translations")

        for word in existing_words_qs:
            frequency = word_counter.get(word.name, 0)
            if frequency == 0:
                continue

            pos_objs = list(word.parts_of_speech.all())
            if not pos_objs:
                continue

            pos_list = [p.name for p in pos_objs]

            # главная часть речи
            main_pos_obj = next(
                (p for p in pos_objs if getattr(p, "is_main", False)),
                pos_objs[0],
            )

            selected_pos = main_pos_obj.name

            # словарь переводов
            translations_for_pos = {}
            for pos in pos_objs:
                translations = pos.translations.all()
                translations_for_pos[pos.name] = [t.translation for t in translations]

            # главный перевод
            main_translation_obj = main_pos_obj.translations.filter(
                is_main=True
            ).first()

            if main_translation_obj:
                selected_translation = main_translation_obj.translation
            else:
                selected_translation = (
                    translations_for_pos[selected_pos][0]
                    if translations_for_pos[selected_pos]
                    else ""
                )

            subtitle_words.append(
                SubtitleWord(
                    name=word.name,
                    frequency=frequency,
                    transcription=word.transcription,
                    selected_pos=selected_pos,
                    selected_translation=selected_translation,
                    pos_list=pos_list,
                    translations_for_pos=translations_for_pos,
                )
            )

        return subtitle_words

    # =========================
    # Сериализация
    # =========================

    def to_dict(self) -> List[dict]:
        return [
            {
                "name": w.name,
                "transcription": w.transcription,
                "frequency": w.frequency,
                "pos_list": w.pos_list,
                "selected_pos": w.selected_pos,
                "translations_for_pos": w.translations_for_pos,
                "selected_translation": w.selected_translation,
            }
            for w in self.subtitle_words
        ]
