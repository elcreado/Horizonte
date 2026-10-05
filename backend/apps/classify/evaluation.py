"""Evaluación selectiva con abstenciones explícitas y corpus separados."""

from collections import Counter
from decimal import Decimal

from .services import normalize
from .tfidf import fit_tfidf


def ratio(numerator: int, denominator: int) -> str | None:
    return str(Decimal(numerator) / denominator) if denominator else None


def evaluate_classifier(training: list[tuple[str, str]], testing: list[tuple[str, str]]) -> dict:
    """El llamador garantiza mismo tenant/dirección y corte temporal de etiquetas.

    Se excluye fuga por descripción normalizada compartida, pero esto no garantiza
    separación de comercios/plantillas semánticas; esa división requiere IDs del corpus.
    """
    if not testing:
        raise ValueError("El conjunto de prueba no puede estar vacío.")
    training = [(normalize(text), category) for text, category in training]
    testing = [(normalize(text), category) for text, category in testing]
    if any(not text or not category for text, category in testing):
        raise ValueError("Cada observación de prueba requiere descripción y etiqueta.")
    if {text for text, _ in training} & {text for text, _ in testing}:
        raise ValueError("Entrenamiento y prueba comparten descripciones normalizadas.")
    if len({text for text, _ in testing}) != len(testing):
        raise ValueError(
            "La prueba requiere descripciones distintas; no inflar soporte con repeticiones."
        )
    model = fit_tfidf(training)
    confusion = Counter()
    accepted = correct = 0
    for text, truth in testing:
        predicted = model.suggest(text)["category"]
        confusion[(truth, predicted)] += 1
        accepted += predicted is not None
        correct += predicted == truth
    categories = sorted(set(model.centroids) | {label for _, label in testing})
    per_category = []
    for category in categories:
        tp = confusion[(category, category)]
        fp = sum(
            count
            for (truth, prediction), count in confusion.items()
            if prediction == category and truth != category
        )
        fn = sum(
            count
            for (truth, prediction), count in confusion.items()
            if truth == category and prediction != category
        )
        per_category.append(
            {
                "category": category,
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "precision": ratio(tp, tp + fp),
                "recall": ratio(tp, tp + fn),
                "f1": ratio(2 * tp, 2 * tp + fp + fn),
            }
        )
    return {
        "version": "tfidf_centroid_selective_v1",
        "training_descriptions": model.examples,
        "testing_descriptions": len(testing),
        "suggested": accepted,
        "abstained": len(testing) - accepted,
        "correct": correct,
        "coverage": ratio(accepted, len(testing)),
        "accuracy_when_suggested": ratio(correct, accepted),
        "correct_fraction_all": ratio(correct, len(testing)),
        "per_category": per_category,
        "confusion": [
            {"actual": actual, "predicted": predicted, "count": count}
            for (actual, predicted), count in sorted(
                confusion.items(), key=lambda item: (item[0][0], item[0][1] or "")
            )
        ],
        "notice": "Resultado del corpus aportado; no prueba eficacia en empresas reales ni calibración de confianza.",
    }
