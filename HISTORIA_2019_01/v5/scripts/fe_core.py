#!/usr/bin/env python3
# Ruta sugerida: HISTORIA_2019_01/v4/scripts/fe_core.py
"""Motor determinista de saneamiento, ventanas calendario exactas y metricas."""
from __future__ import annotations
import numpy as np
import polars as pl

FORBIDDEN_DEV_MONTHS = {201910, 201911, 201912}
GAIN_HIT = 1_072_500.0
GAIN_MISS = -27_500.0


def assert_october_locked(df_months: set[int], stage: str = "DEV") -> None:
    if stage != "FINAL_OCTOBER_EVAL":
        leaked = df_months.intersection(FORBIDDEN_DEV_MONTHS)
        if leaked:
            raise RuntimeError(f"ABORTADO: Meses prohibidos en etapa {stage}: {sorted(leaked)}")


def month_to_idx(col_name: str = "foto_mes") -> pl.Expr:
    return (pl.col(col_name) // 100) * 12 + (pl.col(col_name) % 100)


def sanitize_base(
    df: pl.DataFrame,
    feature_cols: list[str],
    known_broken_masks: dict[int, list[str]] | None = None,
) -> pl.DataFrame:
    """Limpia +-inf -> null y aplica mascaras de bloques rotos documentados sin convertir null en 0."""
    if df.select(["numero_de_cliente", "foto_mes"]).is_duplicated().any():
        n_dup = int(df.select(["numero_de_cliente", "foto_mes"]).is_duplicated().sum())
        raise RuntimeError(f"ABORTADO: {n_dup} filas duplicadas en clave (numero_de_cliente, foto_mes).")

    exprs: list[pl.Expr] = []
    float_cols = {
        c for c in feature_cols
        if df.schema[c] in (pl.Float32, pl.Float64)
    }
    for c in feature_cols:
        e = pl.col(c)
        if c in float_cols:
            e = pl.when(e.is_infinite() | e.is_nan()).then(None).otherwise(e)
        if known_broken_masks:
            broken_months = [m for m, cols in known_broken_masks.items() if c in cols]
            if broken_months:
                e = pl.when(pl.col("foto_mes").is_in(broken_months)).then(None).otherwise(e)
        exprs.append(e.alias(c))

    return df.with_columns(exprs)


def build_exact_lags(df: pl.DataFrame, cols: list[str], max_lag: int) -> pl.DataFrame:
    """Construye rezagos k=1..max_lag por coincidencia exacta de cliente e indice calendario."""
    base = df.with_columns(month_to_idx("foto_mes").alias("_m_idx"))
    out = base
    for k in range(1, max_lag + 1):
        shifted = base.select(
            pl.col("numero_de_cliente"),
            (pl.col("_m_idx") + k).alias("_m_idx"),
            *[pl.col(c).cast(pl.Float64).alias(f"{c}__lag{k}") for c in cols],
        )
        out = out.join(shifted, on=["numero_de_cliente", "_m_idx"], how="left")
    return out.drop("_m_idx")


def add_baseline_lags_deltas(df_with_lags: pl.DataFrame, base_cols: list[str]) -> pl.DataFrame:
    """Agrega delta1 y delta2 sobre lag1 y lag2 ya alineados por calendario."""
    exprs: list[pl.Expr] = []
    for c in base_cols:
        x0 = pl.col(c).cast(pl.Float64)
        l1 = pl.col(f"{c}__lag1")
        l2 = pl.col(f"{c}__lag2")
        exprs.append((x0 - l1).alias(f"{c}__delta1"))
        exprs.append((x0 - l2).alias(f"{c}__delta2"))
    return df_with_lags.with_columns(exprs)


def build_window_families(
    df_with_lags: pl.DataFrame,
    sources: list[str],
    L: int,
    include_f1: bool = True,
    include_f2: bool = False,
    include_f3: bool = True,
) -> pl.DataFrame:
    """
    Construye F1, F2, F3 sobre ventana estricta W_L (requiere las L observaciones no nulas).
    F3 usa receta unica: (x_m - ref) / |ref|, produciendo null cuando ref == 0 o falta algun mes.
    """
    assert L >= 3, "La ventana minima definida es W3."
    t_vals = np.arange(L, dtype=np.float64)  # 0 .. L-1 desde m-L+1 hasta m
    t_centered = t_vals - t_vals.mean()
    denom_ss = float(np.sum(t_centered ** 2))

    new_exprs: list[pl.Expr] = []
    for c in sources:
        # Orden cronologico: m-(L-1), ..., m-1, m
        seq = [pl.col(f"{c}__lag{j}") for j in range(L - 1, 0, -1)] + [pl.col(c).cast(pl.Float64)]
        valid_window = pl.all_horizontal([e.is_not_null() & e.is_finite() for e in seq])

        mean_expr = pl.sum_horizontal(seq) / float(L)
        min_expr = pl.min_horizontal(seq)
        max_expr = pl.max_horizontal(seq)

        if include_f1:
            new_exprs.extend([
                pl.when(valid_window).then(mean_expr).otherwise(None).alias(f"{c}__f1_mean_W{L}"),
                pl.when(valid_window).then(min_expr).otherwise(None).alias(f"{c}__f1_min_W{L}"),
                pl.when(valid_window).then(max_expr).otherwise(None).alias(f"{c}__f1_max_W{L}"),
                pl.when(valid_window).then(max_expr - min_expr).otherwise(None).alias(f"{c}__f1_range_W{L}"),
            ])

        if include_f2:
            num_slope = pl.sum_horizontal([ seq[idx] * float(t_centered[idx]) for idx in range(L) ])
            new_exprs.append(
                pl.when(valid_window).then(num_slope / denom_ss).otherwise(None).alias(f"{c}__f2_slope_W{L}")
            )

        if include_f3:
            xm = seq[-1]
            x_prev = seq[-2]
            x_first = seq[0]
            # Receta unica: (xm - ref) / |ref| si ventana completa y ref != 0; null en caso contrario
            new_exprs.extend([
                pl.when(valid_window & (mean_expr != 0.0))
                .then((xm - mean_expr) / mean_expr.abs())
                .otherwise(None)
                .alias(f"{c}__f3_rel_mean_W{L}"),
                pl.when(valid_window & (x_prev != 0.0))
                .then((xm - x_prev) / x_prev.abs())
                .otherwise(None)
                .alias(f"{c}__f3_rel_prev_W{L}"),
                pl.when(valid_window & (x_first != 0.0))
                .then((xm - x_first) / x_first.abs())
                .otherwise(None)
                .alias(f"{c}__f3_rel_first_W{L}"),
            ])

    out = df_with_lags.with_columns(new_exprs)
    names = [e.meta.output_name() for e in new_exprs]
    return out.with_columns([pl.when(pl.col(c).is_finite()).then(pl.col(c)).otherwise(None).alias(c) for c in names])


def build_monthly_rankings(df: pl.DataFrame, sources: list[str]) -> pl.DataFrame:
    """Ranking transversal [0, 1] estrictamente dentro de cada foto_mes; nulos quedan nulos."""
    exprs: list[pl.Expr] = []
    for c in sources:
        col_f = pl.col(c).cast(pl.Float64)
        n_valid = col_f.count().over("foto_mes")
        rk = (col_f.rank(method="average").over("foto_mes")) / n_valid
        exprs.append(pl.when(col_f.is_not_null() & (n_valid > 0)).then(rk).otherwise(None).alias(f"{c}__rk0"))
    return df.with_columns(exprs)


def evaluate_gain_curve(
    client_ids: np.ndarray,
    scores: np.ndarray,
    is_baja2: np.ndarray,
    smooth_window: int = 2001,
    frozen_prop: float | None = None,
) -> dict[str, float | int]:
    """
    Ordena por score DESC y numero_de_cliente ASC.
    Si frozen_prop es None (agosto), halla el maximo de la curva suavizada completa (2001).
    Si frozen_prop esta fijado (octubre), evalua exactamente floor(frozen_prop * N).
    """
    if len(scores) == 0 or len(client_ids) != len(scores) or len(is_baja2) != len(scores):
        raise ValueError("Arrays vacios o longitudes diferentes")
    if not np.isfinite(scores).all() or not np.isin(is_baja2, [0, 1]).all():
        raise ValueError("Scores o etiquetas invalidos")
    if frozen_prop is not None and not 0 <= frozen_prop <= 1:
        raise ValueError("Proporcion fuera de [0,1]")
    if smooth_window < 1 or smooth_window % 2 != 1:
        raise ValueError("Ventana debe ser impar positiva")
    order = np.lexsort((client_ids, -scores))
    payoffs = np.where(is_baja2[order] == 1, GAIN_HIT, GAIN_MISS)
    cum_gain = np.cumsum(payoffs)
    n_total = len(payoffs)

    if frozen_prop is not None:
        cut = int(np.floor(frozen_prop * n_total))
        point_gain = float(cum_gain[cut - 1]) if cut > 0 else 0.0
        return {
            "n_clients": n_total,
            "cut_contacts": cut,
            "contact_proportion": float(cut / n_total) if n_total else 0.0,
            "point_gain": point_gain,
        }

    if n_total < smooth_window:
        raise ValueError(f"Poblacion ({n_total}) menor que la ventana de suavizado ({smooth_window}).")

    kernel = np.ones(smooth_window, dtype=np.float64) / float(smooth_window)
    smoothed_valid = np.convolve(cum_gain, kernel, mode="valid")  # indices k = half .. n_total - 1 - half
    half = smooth_window // 2
    best_rel_idx = int(np.argmax(smoothed_valid))
    best_zero_based = best_rel_idx + half
    cut_contacts = best_zero_based + 1  # cantidad de contactos (1-based)

    return {
        "n_clients": n_total,
        "smoothed_gain_max": float(smoothed_valid[best_rel_idx]),
        "cut_contacts": cut_contacts,
        "contact_proportion": float(cut_contacts / n_total),
        "point_gain_at_cut": float(cum_gain[best_zero_based]),
    }

