"""Clasificador experimental TF-IDF y centroides, sin modificar movimientos.

Entrenar con descripciones normalizadas y etiquetas revisadas del mismo tenant y
dirección. Similitud/margen son criterios de abstención, no probabilidades.
"""

import math
from collections import Counter
from dataclasses import dataclass


def features(text: str) -> Counter:
    words = text.split()
    return Counter(words + [f"{left} {right}" for left, right in zip(words, words[1:])])


def unit(vector: dict[str, float]) -> dict[str, float]:
    magnitude = math.sqrt(sum(value * value for value in vector.values()))
    return {key: value / magnitude for key, value in vector.items()} if magnitude else {}


@dataclass
class TfidfClassifier:
    idf: dict[str, float]
    centroids: dict[str, dict[str, float]]
    examples: int

    def vector(self, text: str) -> dict[str, float]:
        return unit(
            {
                key: (1 + math.log(count)) * self.idf[key]
                for key, count in features(text).items()
                if key in self.idf
            }
        )

    def suggest(self, text: str, *, min_similarity: float = 0.35, min_margin: float = 0.15) -> dict:
        if not 0 <= min_similarity <= 1 or not 0 <= min_margin <= 1:
            raise ValueError("Umbrales de similitud/margen inválidos.")
        vector = self.vector(text)
        scores = sorted(
            (
                (sum(value * centroid.get(key, 0) for key, value in vector.items()), category)
                for category, centroid in self.centroids.items()
            ),
            reverse=True,
        )
        score, category = scores[0]
        margin = score - scores[1][0]
        accepted = bool(vector) and score >= min_similarity and margin >= min_margin
        return {
            "category": category if accepted else None,
            "similarity": score,
            "margin": margin,
            "status": "suggested" if accepted else "abstained",
            "examples": self.examples,
            "notice": "Sugerencia experimental; similitud no equivale a probabilidad de acierto.",
        }


def fit_tfidf(examples: list[tuple[str, str]]) -> TfidfClassifier:
    unique = {}
    for text, category in examples:
        if not text.strip() or not category:
            raise ValueError("Descripción y categoría requeridas.")
        if text in unique and unique[text] != category:
            raise ValueError("La misma descripción tiene etiquetas contradictorias.")
        unique[text] = category
    counts = Counter(unique.values())
    if len(counts) < 2 or any(count < 3 for count in counts.values()):
        raise ValueError(
            "Requiere al menos dos categorías con tres descripciones distintas cada una."
        )
    documents = Counter(key for text in unique for key in features(text))
    idf = {key: math.log((1 + len(unique)) / (1 + count)) + 1 for key, count in documents.items()}
    model = TfidfClassifier(idf, {}, len(unique))
    totals = {category: Counter() for category in counts}
    for text, category in unique.items():
        totals[category].update(model.vector(text))
    model.centroids = {category: unit(dict(vector)) for category, vector in totals.items()}
    return model
