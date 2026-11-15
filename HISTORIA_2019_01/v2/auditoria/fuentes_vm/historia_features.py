"""Ingeniería HISTORIA 2019: calendario exacto, faltantes explícitos y test ciego.

Este módulo no entrena, no reconstruye etiquetas y no modifica el archivo fuente.
Las cuatro familias son hipótesis nuevas frente al baseline lag/delta 1 y 2;
su implementación no constituye evidencia de mejora predictiva.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import polars as pl

ID = "numero_de_cliente"
MONTH = "foto_mes"
LABEL = "clase_ternaria"
MONTH_INDEX = "_month_index"
TRAIN_MONTHS = (201903, 201904, 201905, 201906)
VALID_MONTH = 201908
TEST_MONTH = 201910
CLASSES = ("BAJA+1", "BAJA+2", "CONTINUA")
RESERVED = {ID, MONTH, LABEL, MONTH_INDEX}


def _names(values: Iterable[str], context: str) -> list[str]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{context} debe ser una lista de nombres, no un texto.")
    result = list(values)
    if any(not isinstance(value, str) or not value for value in result):
        raise ValueError(f"{context} contiene un nombre inválido.")
    if len(result) != len(set(result)):
        raise ValueError(f"{context} contiene nombres duplicados.")
    return result


def _integer_key(series: pl.Series, name: str) -> pl.Series:
    """No redondear claves; las cadenas deben representar enteros exactos."""
    if series.null_count():
        raise ValueError(f"{name}: hay claves nulas.")
    if series.dtype == pl.Boolean or series.dtype.is_temporal():
        raise ValueError(f"{name}: se requieren enteros, no booleanos/fechas.")
    if series.dtype.is_float():
        invalid = (~series.is_finite()) | (series != series.floor())
        if invalid.any():
            raise ValueError(f"{name}: hay claves no enteras o no finitas.")
        if name == ID and (series.abs() > 2**53).any():
            raise ValueError("numero_de_cliente: float fuera del rango de enteros exactos.")
    try:
        result = series.cast(pl.Int64, strict=False)
    except Exception as exc:
        raise ValueError(f"{name}: no se puede convertir la clave a entero.") from exc
    if result.null_count():
        raise ValueError(f"{name}: hay claves no parseables como enteros Int64.")
    return result.rename(name)


def _check_months(series: pl.Series) -> None:
    valid = (series >= 100001) & (series <= 999912)
    valid &= (series % 100 >= 1) & (series % 100 <= 12)
    if not valid.all():
        raise ValueError("foto_mes contiene fechas inválidas: se requiere YYYYMM calendario.")


def _ensure_panel(df: pl.DataFrame) -> pl.DataFrame:
    """Valida claves y recalcula el índice sin ordenar ni rellenar meses."""
    if ID not in df.columns or MONTH not in df.columns:
        raise ValueError(f"Faltan claves {ID}/{MONTH}.")
    ids = _integer_key(df[ID], ID)
    months = _integer_key(df[MONTH], MONTH)
    _check_months(months)
    result = df.with_columns(ids, months)
    if result.select(pl.struct([ID, MONTH]).is_duplicated().any()).item():
        raise ValueError("Hay filas duplicadas para numero_de_cliente + foto_mes.")
    return result.with_columns(
        ((pl.col(MONTH) // 100) * 12 + pl.col(MONTH) % 100 - 1)
        .cast(pl.Int64).alias(MONTH_INDEX)
    )


def _check_labeled_partition(df: pl.DataFrame, name: str) -> None:
    if LABEL not in df.columns:
        raise ValueError(f"{name}: falta {LABEL}.")
    if df.is_empty():
        raise ValueError(f"{name}: partición vacía.")
    invalid = pl.col(LABEL).is_null() | ~pl.col(LABEL).is_in(CLASSES)
    if df.select(invalid.any()).item():
        raise ValueError(
            f"{name}: etiquetas incompletas o inválidas; se admiten sólo {CLASSES}."
        )


def split_partitions(df: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    """Devuelve train03–06, valid08 y test10 con etiqueta anulada, sin binarizar."""
    if MONTH not in df.columns or LABEL not in df.columns:
        raise ValueError(f"Se necesitan {MONTH} y {LABEL} para partir el panel.")
    present = set(df[MONTH].unique().to_list())
    missing = set(TRAIN_MONTHS) - present
    if missing:
        raise ValueError(f"Faltan meses de entrenamiento: {sorted(missing)}.")
    train = df.filter(pl.col(MONTH).is_in(TRAIN_MONTHS))
    valid = df.filter(pl.col(MONTH) == VALID_MONTH)
    test = df.filter(pl.col(MONTH) == TEST_MONTH).with_columns(
        pl.lit(None, dtype=pl.String).alias(LABEL)
    )
    _check_labeled_partition(train, "train 201903–201906")
    _check_labeled_partition(valid, "validación 201908")
    if test.is_empty():
        raise ValueError("Test 201910 vacío: no sería posible guardar sus predicciones.")
    # Nunca se consulta, cuenta ni valida la clase original de octubre.
    return train, valid, test


def _month_audit(df: pl.DataFrame, columns: list[str], min_max: bool) -> list[dict]:
    """Estadísticas de saneamiento exclusivamente en enero–agosto, sin etiquetas."""
    exprs = [pl.len().alias("rows")]
    for i, column in enumerate(columns):
        x = pl.col(column)
        exprs.extend([
            x.is_null().sum().alias(f"n{i}"),
            (x == 0).fill_null(False).sum().alias(f"z{i}"),
        ])
        if min_max:
            exprs.extend([x.min().alias(f"lo{i}"), x.max().alias(f"hi{i}")])
    grouped = (df.filter(pl.col(MONTH) <= VALID_MONTH)
               .group_by(MONTH).agg(exprs).sort(MONTH))
    result = []
    for row in grouped.iter_rows(named=True):
        for i, column in enumerate(columns):
            record = {"foto_mes": row[MONTH], "variable": column, "rows": row["rows"],
                      "nulls": row[f"n{i}"], "zeros": row[f"z{i}"]}
            if min_max:
                record.update(min=row[f"lo{i}"], max=row[f"hi{i}"])
            result.append(record)
    return result


def load_and_audit(cfg: dict) -> tuple[pl.DataFrame, list[str], dict]:
    """Carga 201901–10 y audita; no requiere ni activa el permiso de entrenamiento.

    ``expected_raw_features`` controla el esquema fuente antes de exclusiones.
    El target de octubre se anula en la proyección de lectura, antes de materializar
    el panel de trabajo. Noviembre/diciembre y otros años no ingresan al panel.
    ``broken_variables`` se aplica antes de convertir/transformar predictores.
    """
    path = Path(cfg["data"]).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"No existe el archivo de datos: {path}")
    lower = path.name.lower()
    if lower.endswith(".parquet"):
        source = pl.scan_parquet(path)
    elif lower.endswith((".csv", ".csv.gz")):
        source = pl.scan_csv(
            path, separator=cfg.get("csv_separator", ","), infer_schema=False,
            null_values=["", "NA", "NaN", "nan", "NULL", "null"],
            try_parse_dates=False,
        )
    else:
        raise ValueError("Formato no soportado: usar .parquet, .csv o .csv.gz.")
    schema = source.collect_schema()
    missing = {ID, MONTH, LABEL} - set(schema.names())
    if missing:
        raise ValueError(f"Faltan columnas obligatorias: {sorted(missing)}.")

    # Primero sólo claves: ni valores de predictores ni etiquetas de meses futuros.
    keys = source.select(ID, MONTH).collect()
    months = _integer_key(keys[MONTH], MONTH)
    _check_months(months)
    keys = keys.with_columns(months)
    eligible_keys = _ensure_panel(keys.filter(pl.col(MONTH).is_between(201901, 201910)))
    if eligible_keys.is_empty():
        raise ValueError("No hay filas en 201901–201910.")
    source_rows = keys.height
    df = (source.with_columns(
              pl.col(MONTH).cast(pl.Int64, strict=False),
              pl.col(ID).cast(pl.Int64, strict=False))
          .filter(pl.col(MONTH).is_between(201901, 201910))
          .with_columns(
              pl.when(pl.col(MONTH) == TEST_MONTH)
              .then(pl.lit(None, dtype=pl.String))
              .otherwise(pl.col(LABEL).cast(pl.String, strict=False)).alias(LABEL))
          .collect())
    df = _ensure_panel(df)
    raw = [column for column in schema.names() if column not in RESERVED]
    expected = cfg.get("expected_raw_features", 152)
    if expected is not None and len(raw) != expected:
        raise ValueError(f"Esquema RAW inesperado: {len(raw)} columnas; se esperaban {expected}.")
    excluded = _names(cfg.get("exclude_features", []), "exclude_features")
    if set(excluded) - set(raw):
        raise ValueError("exclude_features contiene columnas que no son predictores RAW.")
    original = [column for column in raw if column not in excluded]
    if not original:
        raise ValueError("No quedaron predictores originales.")

    broken = cfg.get("broken_variables", {})
    if not isinstance(broken, dict) or set(broken) - set(raw):
        raise ValueError("broken_variables debe mapear predictores existentes a meses.")
    masks = []
    for column, broken_months in broken.items():
        if not isinstance(broken_months, list) or any(type(m) is not int for m in broken_months):
            raise ValueError(f"broken_variables[{column}] debe ser una lista de meses enteros.")
        if broken_months:
            _check_months(pl.Series(broken_months, dtype=pl.Int64))
        affected = df.filter(pl.col(MONTH).is_in(broken_months))
        masks.append({"variable": column, "months": broken_months,
                      "rows": affected.height, "observed_values_masked": affected[column].count()})
        df = df.with_columns(
            pl.when(pl.col(MONTH).is_in(broken_months)).then(None)
            .otherwise(pl.col(column)).alias(column))

    nonfinite = {}
    clean = []
    for column in original:
        original_values = df[column]
        try:
            values = original_values.cast(pl.Float64, strict=False)
        except Exception as exc:
            raise ValueError(f"Predictor {column}: tipo no convertible a numérico.") from exc
        bad_parse = original_values.is_not_null() & values.is_null()
        if bad_parse.any():
            raise ValueError(f"Predictor {column}: {bad_parse.sum()} valores no parseables como números.")
        as32 = values.cast(pl.Float32)
        counts = {
            "nan": int(values.is_nan().fill_null(False).sum()),
            "infinite": int(values.is_infinite().fill_null(False).sum()),
            "float32_overflow": int((values.is_finite() & as32.is_infinite()).fill_null(False).sum()),
        }
        if any(counts.values()):
            nonfinite[column] = counts
        clean.append(as32.set(~as32.is_finite().fill_null(False), None).rename(column))
    df = df.with_columns(clean)
    train, valid, test = split_partitions(df)
    warnings = []
    if nonfinite:
        warnings.append("Se convirtieron NaN/inf/desbordamientos Float32 en nulos; revisar nonfinite_to_null.")
    if masks:
        warnings.append("Se aplicaron máscaras explícitas de broken_variables antes de cualquier rezago.")
    audit = {
        "data": str(path.resolve()), "source_rows": source_rows,
        "retained_rows": df.height, "excluded_rows_outside_201901_201910": source_rows - df.height,
        "source_raw_count": len(raw), "model_raw_count": len(original),
        "excluded_features": excluded, "original_features": original,
        "months": sorted(df[MONTH].unique().to_list()),
        "partitions": {"train": train.height, "validation": valid.height, "test": test.height},
        "training_positive_classes": ["BAJA+1", "BAJA+2"],
        "validation_positive_class": "BAJA+2",
        "label_counts_train": dict(train.group_by(LABEL).len().iter_rows()),
        "label_counts_validation": dict(valid.group_by(LABEL).len().iter_rows()),
        "test_target": "anulado sin inspeccionar ni contar sus valores originales",
        "nonfinite_to_null": nonfinite, "broken_variables_applied": masks,
        "variables_by_month": _month_audit(df, original, bool(cfg.get("audit_min_max", True))),
        "warnings": warnings,
    }
    return df, original, audit


def _assert_new(df: pl.DataFrame, names: list[str]) -> None:
    if len(set(names)) != len(names) or set(names) & set(df.columns):
        raise ValueError("Colisión de nombres al crear variables históricas.")


def _finite32(expression: pl.Expr) -> pl.Expr:
    as32 = expression.cast(pl.Float32)
    return pl.when(as32.is_finite()).then(as32).otherwise(pl.lit(None, dtype=pl.Float32))


def add_lags_deltas(df: pl.DataFrame, columns: list[str]) -> pl.DataFrame:
    """Agrega lag/delta1/2 por JOIN de mes exacto, conservando el orden original.

    Si falta t−1 pero existe t−2, lag2 sigue siendo válido. No hay forward-fill,
    backfill ni conversión de ausencia a cero. El mismo helper admite otros años.
    """
    columns = _names(columns, "columns")
    if set(columns) & RESERVED or set(columns) - set(df.columns):
        raise ValueError("Sólo se pueden transformar predictores presentes, nunca claves/target.")
    result = _ensure_panel(df)
    new = [f"{column}__{operation}{k}" for column in columns for operation in ("lag", "delta") for k in (1, 2)]
    _assert_new(result, new)
    if not columns:
        return result
    for k in (1, 2):
        history = result.select(
            pl.col(ID), (pl.col(MONTH_INDEX) + k).alias(MONTH_INDEX),
            *[_finite32(pl.col(column).cast(pl.Float64)).alias(f"{column}__lag{k}") for column in columns],
        )
        result = result.join(history, on=[ID, MONTH_INDEX], how="left",
                             validate="1:1", maintain_order="left")
        result = result.with_columns([
            _finite32(pl.col(column).cast(pl.Float64) - pl.col(f"{column}__lag{k}").cast(pl.Float64))
            .alias(f"{column}__delta{k}") for column in columns
        ])
    return result


def _with_required_lags(df: pl.DataFrame, columns: list[str]) -> pl.DataFrame:
    needed = []
    for column in columns:
        names = {f"{column}__{op}{k}" for op in ("lag", "delta") for k in (1, 2)}
        present = names & set(df.columns)
        if present and present != names:
            raise ValueError(f"Historia parcialmente preexistente de {column}: no se sobrescribe.")
        if not present:
            needed.append(column)
    return add_lags_deltas(df, needed) if needed else df


def _window3(column: str) -> tuple[list[pl.Expr], pl.Expr, pl.Expr]:
    values = [pl.col(name).cast(pl.Float64)
              for name in (column, f"{column}__lag1", f"{column}__lag2")]
    complete = pl.all_horizontal([value.is_finite().fill_null(False) for value in values])
    mean = (values[0] + values[1] + values[2]) / 3.0
    return values, complete, mean


def _summary_exprs(column: str, prefix: str) -> list[tuple[str, pl.Expr, str]]:
    values, complete, mean = _window3(column)
    variance = sum((value - mean).pow(2) for value in values) / 3.0
    definitions = [
        ("mean3", mean, "(x_t + x_t-1 + x_t-2) / 3"),
        ("min3", pl.min_horizontal(values), "min(x_t, x_t-1, x_t-2)"),
        ("max3", pl.max_horizontal(values), "max(x_t, x_t-1, x_t-2)"),
        ("std3", variance.sqrt(), "sqrt(sum((x_i - mean3)^2) / 3); ddof=0"),
    ]
    return [(f"{prefix}__{name}", _finite32(pl.when(complete).then(expr).otherwise(None)), formula)
            for name, expr, formula in definitions]


def build_hypothesis_families(
    df: pl.DataFrame, original: list[str], leaders: list[str], cfg: dict,
) -> tuple[pl.DataFrame, dict[str, list[str]], list[dict]]:
    """Genera familias independientes; el runner decide qué columnas usa cada brazo.

    Ratios: lista explícita ``ratio_columns`` si existe; por defecto ``leaders``.
    Rachas: sólo ``zero_columns``. Rangos: ``leaders ∩ monetary_columns``.
    Los resúmenes requieren las tres fotos y tres valores observados. Los rangos
    son una representación adicional, no una garantía de inmunidad al drift.
    """
    original = _names(original, "original")
    leaders = _names(leaders, "leaders")
    if set(original) & RESERVED or set(original) - set(df.columns):
        raise ValueError("Lista original inválida: incluye claves/target o columnas ausentes.")
    if set(leaders) - set(original):
        raise ValueError("leaders debe contener únicamente variables originales elegibles.")
    zeros = _names(cfg.get("zero_columns", []), "zero_columns")
    ratios = _names(cfg.get("ratio_columns", leaders), "ratio_columns")
    monetary = _names(cfg.get("monetary_columns", []), "monetary_columns")
    if (set(zeros) | set(ratios)) - set(original):
        raise ValueError("zero_columns/ratio_columns contienen variables ausentes o excluidas.")
    if set(monetary) - set(df.columns) or set(monetary) & RESERVED:
        raise ValueError("monetary_columns contiene columnas ausentes o claves/target.")
    ranked = [column for column in leaders if column in monetary]
    epsilon = cfg.get("ratio_epsilon", 1e-8)
    if not isinstance(epsilon, (int, float)) or not np.isfinite(epsilon) or epsilon < 0:
        raise ValueError("ratio_epsilon debe ser un número finito no negativo.")
    used = list(dict.fromkeys(leaders + zeros + ratios))
    result = _with_required_lags(_ensure_panel(df), used)
    families = {name: [] for name in ("resumen_3m", "inactividad", "ratios_personales", "rangos_monetarios")}
    manifest: list[dict] = []

    def record(family: str, name: str, source: str, formula: str,
               missing_policy: str, notes: str = "", window: int = 3) -> None:
        families[family].append(name)
        manifest.append({"feature": name, "family": family, "sources": [source],
                         "formula": formula, "window_months": window,
                         "missing_policy": missing_policy, "notes": notes})

    expressions = []
    for column in leaders:
        for name, expression, formula in _summary_exprs(column, f"hist__resumen_3m__{column}"):
            expressions.append(expression.alias(name))
            record("resumen_3m", name, column, formula,
                   "NA si no hay tres valores finitos en t, t-1, t-2.")
    for column in zeros:
        values, complete, _ = _window3(column)
        streak = (pl.when(values[0] != 0).then(0)
                  .when(values[1] != 0).then(1)
                  .when(values[2] != 0).then(2).otherwise(3))
        name = f"hist__inactividad__{column}__zero_streak3"
        expressions.append(_finite32(pl.when(complete).then(streak).otherwise(None)).alias(name))
        record("inactividad", name, column,
               "ceros consecutivos desde t hacia atrás: 0, 1, 2 o 3",
               "NA si cualquier foto/valor de la ventana de tres meses falta.",
               "Racha observada censurada a tres fotos; cero no equivale universalmente a inactividad.")
    for column in ratios:
        values, complete, mean = _window3(column)
        valid = complete & pl.all_horizontal([value >= 0 for value in values]) & (mean > epsilon)
        name = f"hist__ratios_personales__{column}__ratio3"
        expressions.append(_finite32(pl.when(valid).then(values[0] / mean).otherwise(None)).alias(name))
        record("ratios_personales", name, column, f"x_t / mean3; mean3 > {epsilon}; x_t,x_t-1,x_t-2 >= 0",
               "NA ante ventana incompleta, negativos o media insuficiente; sin epsilon añadido al cociente.",
               "Representación relativa de valores no negativos; no interpreta saldos negativos como flujos.")
    names = [entry["feature"] for entry in manifest]
    _assert_new(result, names)
    if expressions:
        result = result.with_columns(expressions)

    rank_names = []
    rank_expressions = []
    rank_summaries = []
    for column in ranked:
        x = pl.col(column).cast(pl.Float64)
        positive = pl.when(x.is_finite() & (x > 0)).then(x).otherwise(None)
        negative = pl.when(x.is_finite() & (x < 0)).then(x.abs()).otherwise(None)
        npositive = positive.count().over(MONTH)
        nnegative = negative.count().over(MONTH)
        positive_rank = positive.rank(method="average").over(MONTH) / pl.when(npositive > 0).then(npositive).otherwise(None)
        negative_rank = negative.rank(method="average").over(MONTH) / pl.when(nnegative > 0).then(nnegative).otherwise(None)
        rank = (pl.when(~x.is_finite()).then(None).when(x == 0).then(0.0)
                .when(x > 0).then(positive_rank).otherwise(-negative_rank))
        name = f"hist__rangos_monetarios__{column}__rank"
        rank_names.append(name)
        rank_expressions.append(_finite32(rank).alias(name))
        record("rangos_monetarios", name, column,
               "0 si x=0; +rank_promedio(x)/n_pos si x>0; -rank_promedio(abs(x))/n_neg si x<0; dentro del mes",
               "NA permanece NA; grupos por signo, empates con rango promedio.",
               "Usa la cohorte mensual completa sin target; puede cambiar por composición poblacional. No inmuniza contra drift.", 1)
        for k in (1, 2):
            for operation, formula in (("lag", f"rank(t-{k}) por mes calendario"),
                                       ("delta", f"rank(t) - rank(t-{k})")):
                record("rangos_monetarios", f"{name}__{operation}{k}", column, formula,
                       "NA si falta el mes o el valor requerido.", window=k + 1)
        summaries = _summary_exprs(name, f"hist__rangos_monetarios__{column}__rank")
        rank_summaries.extend(summaries)
        for feature, _, formula in summaries:
            record("rangos_monetarios", feature, column, formula.replace("x_", "rank_"),
                   "NA si no hay tres rangos mensuales observados.",
                   "El paquete incluye rango actual y derivados: no aísla exclusivamente el efecto de añadir historia.")
    if rank_names:
        _assert_new(result, families["rangos_monetarios"])
        result = result.with_columns(rank_expressions)
        # Dos joins para toda la familia, no dos joins del panel ancho por variable.
        result = add_lags_deltas(result, rank_names)
        result = result.with_columns([
            expression.alias(feature) for feature, expression, _ in rank_summaries
        ])
    return result, families, manifest
