"""Pure metrics and selection rules for HISTORIA 2019.

This module does not load data, train models, or evaluate an October holdout.
``diagnostic_plateau`` is an explicitly local diagnostic, not the official
``evaluar.py`` and not an optimization objective.
"""

from __future__ import annotations

from numbers import Integral, Real
from typing import Any

import numpy as np
from sklearn.metrics import roc_auc_score


def _vector(values: Any, name: str, *, dtype: Any = None) -> np.ndarray:
    try:
        array = np.asarray(values, dtype=dtype)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} must be a one-dimensional vector") from exc
    if array.ndim != 1 or array.size == 0:
        raise ValueError(f"{name} must be a nonempty one-dimensional vector")
    return array


def _probabilities(values: Any, name: str) -> np.ndarray:
    raw = _vector(values, name)
    if np.iscomplexobj(raw):
        raise ValueError(f"{name} must contain real probabilities, not complex values")
    array = _vector(values, name, dtype=np.float64)
    if not np.isfinite(array).all():
        raise ValueError(f"{name} must contain only finite values")
    if ((array < 0.0) | (array > 1.0)).any():
        raise ValueError(f"{name} must be within [0, 1]")
    return array


def _labels_and_scores(y: Any, scores: Any) -> tuple[np.ndarray, np.ndarray]:
    labels = _vector(y, "y")
    if labels.dtype.kind not in "biufO" or not np.isin(labels, [0, 1]).all():
        raise ValueError("y must contain binary labels 0 and/or 1")
    probabilities = _probabilities(scores, "scores")
    if labels.shape != probabilities.shape:
        raise ValueError("y and scores must have the same one-dimensional shape")
    return labels.astype(np.int8), probabilities


def _finite_scalar(value: Any, name: str) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite numeric scalar")
    converted = float(value)
    if not np.isfinite(converted):
        raise ValueError(f"{name} must be a finite numeric scalar")
    return converted


def _probability_scalar(value: Any, name: str) -> float:
    converted = _finite_scalar(value, name)
    if not 0.0 <= converted <= 1.0:
        raise ValueError(f"{name} must be within [0, 1]")
    return converted


def _integer(value: Any, name: str, minimum: int, maximum: int | None = None) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise ValueError(f"{name} must be an integer")
    converted = int(value)
    if converted < minimum or (maximum is not None and converted > maximum):
        upper = "" if maximum is None else f" and at most {maximum}"
        raise ValueError(f"{name} must be at least {minimum}{upper}")
    return converted


def _ordered_inputs(ids: Any, y: Any, scores: Any) -> tuple[np.ndarray, np.ndarray]:
    labels, probabilities = _labels_and_scores(y, scores)
    # Object conversion preserves large integer IDs instead of coercing them
    # through float64, whose exact-integer range ends at 2**53.
    identifiers = _vector(ids, "ids", dtype=object)
    if identifiers.shape != labels.shape:
        raise ValueError("ids, y and scores must have the same shape")
    normalized: list[int | float | str] = []
    kinds: set[str] = set()
    for identifier in identifiers:
        if isinstance(identifier, (bool, np.bool_)):
            raise ValueError("ids must be finite numeric IDs or nonempty strings")
        if isinstance(identifier, str):
            if not identifier.strip():
                raise ValueError("ids must not be empty strings")
            normalized.append(identifier)
            kinds.add("text")
        elif isinstance(identifier, Integral):
            normalized.append(int(identifier))
            kinds.add("numeric")
        elif isinstance(identifier, Real) and np.isfinite(identifier):
            normalized.append(float(identifier))
            kinds.add("numeric")
        else:
            raise ValueError("ids must be finite numeric IDs or nonempty strings")
    if len(kinds) != 1:
        raise ValueError("ids must not mix text and numeric identifiers")
    if len(set(normalized)) != len(normalized):
        raise ValueError("ids must be unique")
    order = np.array(
        sorted(range(len(labels)), key=lambda i: (-float(probabilities[i]), normalized[i])),
        dtype=np.int64,
    )
    return labels, order


def _ordered_gains(
    ids: Any, y: Any, scores: Any, gain_pos: Any, gain_neg: Any
) -> np.ndarray:
    labels, order = _ordered_inputs(ids, y, scores)
    positive = _finite_scalar(gain_pos, "gain_pos")
    negative = _finite_scalar(gain_neg, "gain_neg")
    return np.where(labels[order] == 1, positive, negative)


def binary_auc(y: Any, scores: Any) -> float:
    """Compute ROC AUC for binary 0/1 labels; both classes are required.

    Scores are finite probabilities in the inclusive interval [0, 1]. Constant
    scores, including all zeros, are valid and yield AUC 0.5 with both classes.
    """
    labels, probabilities = _labels_and_scores(y, scores)
    if np.unique(labels).size != 2:
        raise ValueError("AUC requires both binary classes in y")
    return float(roc_auc_score(labels, probabilities))


def gain_at_n(
    ids: Any,
    y: Any,
    scores: Any,
    n: int,
    gain_pos: float = 1_072_500,
    gain_neg: float = -27_500,
) -> float:
    """Net gain for exactly n sends, ranked by score descending then ID ascending.

    IDs must be unique, all inputs aligned, and 0 <= n <= the number of rows.
    Invalid n values are rejected, never clamped. A single label class is valid
    for gain, unlike AUC. Sending to zero customers returns zero.
    """
    gains = _ordered_gains(ids, y, scores, gain_pos, gain_neg)
    count = _integer(n, "n", 0, len(gains))
    with np.errstate(over="ignore", invalid="ignore"):
        value = float(np.sum(gains[:count], dtype=np.float64))
    if not np.isfinite(value):
        raise ValueError("Accumulated gain is not finite")
    return value


def diagnostic_plateau(
    ids: Any,
    y: Any,
    scores: Any,
    window: int,
    gain_pos: float,
    gain_neg: float,
) -> dict[str, Any]:
    """Find a validation-only diagnostic plateau, not the official evaluator.

    Average complete, centered odd windows over cumulative gains for sends
    1..N. No zero padding, partial windows, or fictitious send-zero observation
    is introduced. The selected n_send is the center of the winning window;
    exact ties prefer the smaller n_send. gain_at_n is its unsmoothed gain.
    This diagnostic must not select hyperparameters or evaluate the blind test.
    """
    gains = _ordered_gains(ids, y, scores, gain_pos, gain_neg)
    width = _integer(window, "window", 1, len(gains))
    if width % 2 == 0:
        raise ValueError("window must be odd")
    with np.errstate(over="ignore", invalid="ignore"):
        cumulative = np.cumsum(gains, dtype=np.float64)
        prefix = np.concatenate(([0.0], np.cumsum(cumulative, dtype=np.float64)))
        means = (prefix[width:] - prefix[:-width]) / width
    if not np.isfinite(cumulative).all() or not np.isfinite(means).all():
        raise ValueError("Accumulated or smoothed gain is not finite")
    # Means correspond to centers in ascending order, so argmax's first-match
    # behavior implements the declared smaller-n tie rule.
    winning_window = int(np.argmax(means))
    n_send = winning_window + width // 2 + 1
    return {
        "gain_smoothed": float(means[winning_window]),
        "n_send": n_send,
        "gain_at_n": float(cumulative[n_send - 1]),
        "window": width,
        "method": "centered_full_window_mean_on_cumulative_gain",
    }


def paired_decision(
    candidate_aucs: Any,
    reference_aucs: Any,
    candidate_ensemble_auc: float,
    reference_ensemble_auc: float,
    min_delta_auc: float,
    min_wins: int,
) -> dict[str, Any]:
    """Apply the fixed promotion heuristic to aligned, paired seed results.

    The caller must align the vectors by the same seed IDs. At least two seed
    pairs are required for sample standard deviations (ddof=1). These results
    describe algorithmic variability on the same data, not independent test
    samples, population significance, or an out-of-time confirmation.
    """
    candidate = _probabilities(candidate_aucs, "candidate_aucs")
    reference = _probabilities(reference_aucs, "reference_aucs")
    if candidate.shape != reference.shape:
        raise ValueError("Candidate and reference seed vectors must have the same shape")
    if len(candidate) < 2:
        raise ValueError("At least two paired seed results are required")
    threshold = _finite_scalar(min_delta_auc, "min_delta_auc")
    if threshold < 0.0:
        raise ValueError("min_delta_auc must not be negative")
    minimum_wins = _integer(min_wins, "min_wins", 0, len(candidate))
    candidate_ensemble = _probability_scalar(candidate_ensemble_auc, "candidate_ensemble_auc")
    reference_ensemble = _probability_scalar(reference_ensemble_auc, "reference_ensemble_auc")
    differences = candidate - reference
    delta_mean = float(differences.mean())
    wins = int(np.count_nonzero(differences > 0.0))
    losses = int(np.count_nonzero(differences < 0.0))
    ties = int(np.count_nonzero(differences == 0.0))
    accepted = (
        delta_mean >= threshold
        and wins >= minimum_wins
        and candidate_ensemble >= reference_ensemble
    )
    return {
        "n_seeds": int(len(candidate)),
        "candidate_mean": float(candidate.mean()),
        "reference_mean": float(reference.mean()),
        "candidate_std": float(candidate.std(ddof=1)),
        "reference_std": float(reference.std(ddof=1)),
        "candidate_median": float(np.median(candidate)),
        "reference_median": float(np.median(reference)),
        "delta_mean": delta_mean,
        "delta_median": float(np.median(differences)),
        "delta_std": float(differences.std(ddof=1)),
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "delta_ensemble": float(candidate_ensemble - reference_ensemble),
        "accepted": bool(accepted),
    }


def choose_winner(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Select an eligible completed row; never promote a discarded candidate.

    Only decision='baseline' or 'mantenido' is eligible. Order by descending
    auc_ensemble, then fewer n_features, then smaller numeric iteration (stored
    as a string). Exact remaining ties preserve input order. Return the original
    row, including any extra fields. Raise when no eligible row exists.
    """
    if not isinstance(results, list):
        raise ValueError("results must be a list of dictionaries")
    eligible: list[tuple[tuple[float, int, int], dict[str, Any]]] = []
    for row in results:
        if not isinstance(row, dict):
            raise ValueError("Every result must be a dictionary")
        if row.get("status") != "completed" or row.get("decision") not in {"baseline", "mantenido"}:
            continue
        if not {"auc_ensemble", "n_features", "iteration"}.issubset(row):
            raise ValueError("Eligible results require auc_ensemble, n_features and iteration")
        auc = _probability_scalar(row["auc_ensemble"], "auc_ensemble")
        feature_count = _integer(row["n_features"], "n_features", 0)
        iteration = row["iteration"]
        if not isinstance(iteration, str) or not iteration or not iteration.isdecimal():
            raise ValueError("iteration must be a nonnegative integer stored as a string")
        eligible.append(((-auc, feature_count, int(iteration)), row))
    if not eligible:
        raise ValueError("No completed baseline or maintained result is eligible")
    return min(eligible, key=lambda item: item[0])[1]
