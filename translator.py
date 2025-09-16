import json
from pathlib import Path
import re

class AklanonTranslator:
    def __init__(self, dict_path: str = "aklanon_dict.json"):
        with open(Path(dict_path), "r", encoding="utf-8") as f:
            self.dictionary = json.load(f)

        # Build reverse lookup per language
        self.reverse = {lang: {} for lang in ["tl", "akl", "en"]}
        for _, langs in self.dictionary.items():
            for lang, phrase in langs.items():
                if phrase:  # skip empty/null
                    self.reverse[lang][phrase.lower()] = langs

        # Sort by length (longest phrase first → phrase preference)
        for lang in self.reverse:
            self.reverse[lang] = dict(
                sorted(self.reverse[lang].items(), key=lambda x: len(x[0]), reverse=True)
            )

    def translate(self, text: str, src: str, tgt: str) -> str:
        """Translate text from src → tgt, preferring phrase matches over single words."""
        lowered = text.lower()
        translated = lowered

        # --- Step 1: Replace multi-word/longest matches first
        for phrase, langs in self.reverse[src].items():
            if phrase in translated:
                translated = re.sub(
                    r"\b" + re.escape(phrase) + r"\b",
                    langs.get(tgt, phrase),
                    translated
                )

        # --- Step 2: Word-level fallback
        words = translated.split()
        final = []
        for w in words:
            if w in self.reverse[src]:
                final.append(self.reverse[src][w].get(tgt, w))
            else:
                final.append(w)  # keep original if unknown
        return " ".join(final)

    def to_tagalog(self, text: str, src: str) -> str:
        return self.translate(text, src, "tl")

    def to_aklanon(self, text: str, src: str) -> str:
        return self.translate(text, src, "akl")

    def to_english(self, text: str, src: str) -> str:
        return self.translate(text, src, "en")
