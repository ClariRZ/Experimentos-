#!/usr/bin/env python3
# Ruta sugerida: HISTORIA_2019_01/v4/pruebas/test_integrity.py
"""Suite de pruebas sinteticas de integridad antes de habilitar entrenamientos."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import polars as pl
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from fe_core import (  # noqa: E402
    add_baseline_lags_deltas,
    assert_october_locked,
    build_exact_lags,
    build_monthly_rankings,
    build_window_families,
    evaluate_gain_curve,
    sanitize_base,
)


def test_missing_months_and_year_boundary_do_not_shift_rows() -> None:
    df = pl.DataFrame({
        "numero_de_cliente": [1, 1, 1],
        "foto_mes": [201812, 201901, 201903],  # falta 201902
        "m_saldo": [100.0, 200.0, 500.0],
    })
    out = build_exact_lags(df, ["m_saldo"], max_lag=2)
    out = add_baseline_lags_deltas(out, ["m_saldo"])
    out = build_window_families(out, ["m_saldo"], L=3, include_f1=True, include_f2=True, include_f3=True)

    r_jan = out.filter(pl.col("foto_mes") == 201901).row(0, named=True)
    assert r_jan["m_saldo__lag1"] == 100.0  # 201812 -> 201901 cruza bien el anio

    r_mar = out.filter(pl.col("foto_mes") == 201903).row(0, named=True)
    assert r_mar["m_saldo__lag1"] is None  # 201902 ausente -> null, NO 200.0
    assert r_mar["m_saldo__lag2"] == 200.0  # 201901 exacto
    assert r_mar["m_saldo__f1_mean_W3"] is None  # ventana incompleta -> null sin borrar al cliente
    assert out.height == 3


def test_zero_mean_from_sign_compensation_yields_null_in_f3() -> None:
    df = pl.DataFrame({
        "numero_de_cliente": [10, 10, 10],
        "foto_mes": [201901, 201902, 201903],
        "m_cc": [-100.0, 100.0, 0.0],  # promedio W3 = 0 por compensacion, actual = 0
    })
    out = build_exact_lags(df, ["m_cc"], max_lag=2)
    out = build_window_families(out, ["m_cc"], L=3, include_f1=True, include_f2=False, include_f3=True)
    row = out.filter(pl.col("foto_mes") == 201903).row(0, named=True)
    assert row["m_cc__f1_mean_W3"] == 0.0
    assert row["m_cc__f3_rel_mean_W3"] is None  # NUNCA 0.0 ni 1.0 cuando el denominador es 0
    assert row["m_cc__f3_rel_prev_W3"] == -1.0  # (0 - 100) / |100| = -1.0
    assert row["m_cc__f3_rel_first_W3"] == 1.0  # (0 - (-100)) / |-100| = +1.0


def test_w4_and_w6_slope_matches_ols() -> None:
    vals = [10.0, 13.0, 19.0, 22.0, 25.0, 31.0]
    df = pl.DataFrame({
        "numero_de_cliente": [7] * 6,
        "foto_mes": [201901, 201902, 201903, 201904, 201905, 201906],
        "m_x": vals,
    })
    out = build_exact_lags(df, ["m_x"], max_lag=5)
    out = build_window_families(out, ["m_x"], L=6, include_f1=True, include_f2=True, include_f3=True)
    row = out.filter(pl.col("foto_mes") == 201906).row(0, named=True)
    expected_slope = float(np.polyfit(np.arange(6, dtype=float), vals, 1)[0])
    assert np.isclose(row["m_x__f2_slope_W6"], expected_slope, atol=1e-12)


def test_monthly_rankings_do_not_leak_across_months_and_handle_ties() -> None:
    df = pl.DataFrame({
        "numero_de_cliente": [1, 2, 3, 4, 1, 2, 3, 4],
        "foto_mes": [201905] * 4 + [201906] * 4,
        "m_x": [10.0, 10.0, 50.0, None, 10.0, 1000.0, 2000.0, 3000.0],
    })
    rk_may_only = build_monthly_rankings(df.filter(pl.col("foto_mes") == 201905), ["m_x"])
    rk_panel = build_monthly_rankings(df, ["m_x"]).filter(pl.col("foto_mes") == 201905)
    assert rk_may_only["m_x__rk0"].to_list() == rk_panel["m_x__rk0"].to_list()
    # En 201905 hay 3 no nulos: empate en pos 1 y 2 -> rango medio 1.5 / 3 = 0.5; el nulo queda None
    assert rk_panel["m_x__rk0"].to_list() == [0.5, 0.5, 1.0, None]


def test_october_guard_and_duplicate_key_guard() -> None:
    with pytest.raises(RuntimeError, match="Meses prohibidos"):
        assert_october_locked({201906, 201908, 201910}, stage="DEV")

    dup_df = pl.DataFrame({
        "numero_de_cliente": [1, 1],
        "foto_mes": [201903, 201903],
        "m_x": [1.0, 2.0],
    })
    with pytest.raises(RuntimeError, match="duplicadas"):
        sanitize_base(dup_df, ["m_x"])


def test_gain_curve_tiebreak_and_frozen_october_policy() -> None:
    n = 3000
    clients = np.arange(1, n + 1)
    scores = np.linspace(1.0, 0.0, n)
    scores[0] = scores[1]  # empate: debe ganar cliente 1 antes que cliente 2
    baja2 = np.zeros(n, dtype=int)
    baja2[:300] = 1
    aug = evaluate_gain_curve(clients, scores, baja2, smooth_window=2001)
    oct_eval = evaluate_gain_curve(clients[:2500], scores[:2500], baja2[:2500], frozen_prop=float(aug["contact_proportion"]))
    assert oct_eval["cut_contacts"] == int(np.floor(aug["contact_proportion"] * 2500))

