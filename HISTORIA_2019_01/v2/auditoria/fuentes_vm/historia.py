#!/usr/bin/env python3
"""HISTORIA 2019: ejecución reproducible; octubre se predice, nunca se evalúa aquí."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import csv
from datetime import datetime, timezone
import fcntl
import gc
import hashlib
from importlib.metadata import version
import json
import math
import os
from pathlib import Path
import platform
import sys
import time
from zoneinfo import ZoneInfo

import lightgbm as lgb
import numpy as np
import optuna
import polars as pl

from historia_features import (
    ID, MONTH, LABEL, add_lags_deltas, build_hypothesis_families,
    load_and_audit, split_partitions,
)
from historia_metrics import binary_auc, choose_winner, diagnostic_plateau, paired_decision

HP_NAMES = ("num_leaves", "learning_rate", "min_data_in_leaf", "feature_fraction", "bagging_fraction")
ROOT = Path(__file__).resolve().parent
TZ = ZoneInfo("America/Argentina/Buenos_Aires")


def now() -> str:
    return datetime.now(TZ).isoformat(timespec="seconds")


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def write_table(path: Path, rows: list[dict], columns: list[str], delimiter=",") -> None:
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter=delimiter, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in columns})
    tmp.replace(path)


def positive_int(value, key: str) -> int:
    if type(value) is not int or value < 1:
        raise ValueError(f"{key} debe ser un entero positivo.")
    return value


def validate_hp(hp: dict) -> dict:
    if not isinstance(hp, dict) or set(hp) != {"params", "rounds"}:
        raise ValueError("Hiperparámetros externos: JSON con exactamente params y rounds.")
    params = hp["params"]
    if not isinstance(params, dict) or set(params) != set(HP_NAMES):
        raise ValueError(f"params debe contener exactamente {HP_NAMES}.")
    for key in ("num_leaves", "min_data_in_leaf"):
        positive_int(params[key], key)
    if params["num_leaves"] < 2:
        raise ValueError("num_leaves debe ser >= 2.")
    for key in ("learning_rate", "feature_fraction", "bagging_fraction"):
        x = params[key]
        if type(x) not in (int, float) or not math.isfinite(x) or not 0 < x <= 1:
            raise ValueError(f"{key} debe estar en (0, 1].")
    positive_int(hp["rounds"], "rounds")
    return hp


def read_config(args) -> dict:
    config_path = args.config.expanduser().resolve()
    cfg = read_json(config_path)
    selected = args.data if args.data is not None else cfg.get("data")
    if not selected:
        raise ValueError("Falta el dato real: usar --data /ruta/datos_2019.parquet. No se inventa una ruta.")
    data = Path(selected).expanduser()
    if not data.is_absolute():
        data = (Path.cwd() if args.data is not None else config_path.parent) / data
    cfg["data"] = str(data.resolve())
    if not data.is_file():
        raise FileNotFoundError(f"No existe {data}.")
    hp_path = cfg.get("baseline_hyperparams_file")
    if hp_path:
        hp_path = Path(hp_path).expanduser()
        if not hp_path.is_absolute():
            hp_path = config_path.parent / hp_path
        cfg["baseline_hyperparams_file"] = str(hp_path.resolve())
        validate_hp(read_json(hp_path))
    if args.sanitization_reviewed:
        cfg["sanitization_reviewed"] = True
        cfg["review_acknowledgement"] = "flag --sanitization-reviewed; responsabilidad de quien ejecuta"
    if type(cfg.get("sanitization_reviewed")) is not bool:
        raise ValueError("sanitization_reviewed debe ser true o false, no un texto.")
    for key in ("enable_rank_package", "enable_canaries", "enable_final_bo", "optimize_b0_if_missing"):
        if type(cfg.get(key)) is not bool:
            raise ValueError(f"{key} debe ser un booleano JSON.")
    for key, sign in (("gain_pos", 1), ("gain_neg", -1)):
        x = cfg.get(key)
        if type(x) not in (int, float) or not math.isfinite(x) or x * sign <= 0:
            raise ValueError(f"{key} debe ser finito y tener el signo previsto para ganancia/costo.")
    epsilon = cfg.get("ratio_epsilon", 1e-8)
    if type(epsilon) not in (int, float) or not math.isfinite(epsilon) or epsilon < 0:
        raise ValueError("ratio_epsilon debe ser finito y no negativo.")
    cfg["mode"] = args.mode
    if args.mode == "pilot":
        # Un piloto técnico nuevo, nunca una reproducción abreviada del resultado científico.
        cfg.update(bo_trials=2, max_rounds=min(80, cfg["max_rounds"]),
                   early_stopping_rounds=min(15, cfg["early_stopping_rounds"]),
                   seeds=cfg["seeds"][:1], min_wins_keep=0,
                   optimize_b0_if_missing=True, baseline_hyperparams_file=None)
    for key in ("bo_trials", "bo_seed", "max_rounds", "early_stopping_rounds", "threads", "top_core", "plateau_window"):
        positive_int(cfg[key], key)
    seeds = cfg["seeds"]
    if not isinstance(seeds, list) or not seeds or any(type(s) is not int or not 0 <= s < 2**31 for s in seeds):
        raise ValueError("seeds debe ser una lista no vacía de enteros de 0 a 2**31-1.")
    if len(seeds) != len(set(seeds)):
        raise ValueError("No repetir semillas.")
    if args.mode != "pilot" and len(seeds) < 2:
        raise ValueError("La comparación científica necesita al menos dos semillas pareadas.")
    if type(cfg["min_wins_keep"]) is not int or not 0 <= cfg["min_wins_keep"] <= len(seeds):
        raise ValueError("min_wins_keep incompatible con la cantidad de semillas.")
    for key in ("min_delta_auc_keep", "max_hours"):
        x = cfg[key]
        if type(x) not in (int, float) or not math.isfinite(x) or x < 0 or (key == "max_hours" and x == 0):
            raise ValueError(f"{key} inválido.")
    if cfg["plateau_window"] % 2 != 1:
        raise ValueError("plateau_window debe ser impar.")
    space = cfg["search_space"]
    if set(space) != set(HP_NAMES):
        raise ValueError("search_space debe contener los cinco hiperparámetros previstos.")
    for key, spec in space.items():
        kind = "int" if key in ("num_leaves", "min_data_in_leaf") else "float"
        lo, hi = spec["low"], spec["high"]
        if "log" in spec and type(spec["log"]) is not bool:
            raise ValueError(f"log en {key} debe ser booleano, no texto.")
        if spec["type"] != kind or type(lo) not in (int, float) or type(hi) not in (int, float):
            raise ValueError(f"Rango mal definido para {key}.")
        if not math.isfinite(lo) or not math.isfinite(hi) or not 0 < lo <= hi:
            raise ValueError(f"Rango no positivo/finito/ordenado para {key}.")
        if kind == "int" and (type(lo) is not int or type(hi) is not int):
            raise ValueError(f"Los extremos de {key} deben ser enteros.")
        if key in ("learning_rate", "feature_fraction", "bagging_fraction") and hi > 1:
            raise ValueError(f"El límite superior de {key} no puede superar 1.")
        if key == "num_leaves" and lo < 2:
            raise ValueError("num_leaves >= 2.")
    if cfg.get("enable_canaries"):
        positive_int(cfg["canary_count"], "canary_count")
        positive_int(cfg["canary_seed"], "canary_seed")
        if not 0 < cfg["canary_quantile"] < 1:
            raise ValueError("canary_quantile debe estar entre 0 y 1.")
    if not cfg.get("optimize_b0_if_missing", True) and not cfg.get("baseline_hyperparams_file"):
        raise ValueError("No optimizar B0 requiere baseline_hyperparams_file REAL. No se usarán valores ficticios.")
    return cfg


def identity(cfg: dict) -> dict:
    return {
        "config": cfg,
        "input_sha256": file_hash(Path(cfg["data"])),
        "external_hyperparams_sha256": file_hash(Path(cfg["baseline_hyperparams_file"])) if cfg.get("baseline_hyperparams_file") else None,
        "source_sha256": {name: file_hash(ROOT / name) for name in ("historia.py", "historia_features.py", "historia_metrics.py", "requirements.txt")},
        "environment": {"python": platform.python_version(), **{name: version(name) for name in ("numpy", "scipy", "scikit-learn", "polars", "lightgbm", "optuna", "pyarrow")}},
    }


class Paused(RuntimeError):
    pass


class Budget:
    def __init__(self, out: Path, deadline: float):
        self.out, self.deadline = out, deadline

    def check(self):
        if (self.out / "STOP").exists():
            raise Paused(f"Pausa solicitada mediante {self.out / 'STOP'}.")
        if time.time() >= self.deadline:
            raise Paused("Alcanzado max_hours; se conservaron los checkpoints completos.")

    def callback(self):
        def check(_env):
            self.check()
        check.order = 5
        check.before_iteration = True
        return check


@contextmanager
def locked(out: Path):
    with (out / ".runner.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("Otro proceso ya está usando esta carpeta de salida.") from exc
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


class Arrays:
    def __init__(self, frame: pl.DataFrame, features: list[str], *, training_only=False, with_test=True):
        if len(features) != len(set(features)) or set(features) & {ID, MONTH, LABEL, "_month_index"}:
            raise ValueError("Lista de features duplicada o con claves/target.")
        view = frame.select([ID, MONTH, LABEL, *features])
        if training_only:
            train = view.filter(pl.col(MONTH).is_in([201903, 201904, 201905, 201906]))
        else:
            train, valid, test = split_partitions(view)
        self.x_train = train.select(features).to_numpy().astype(np.float32, copy=False)
        self.y_train = train[LABEL].is_in(["BAJA+1", "BAJA+2"]).to_numpy().astype(np.int8)
        if np.unique(self.y_train).size != 2:
            raise ValueError("Entrenamiento sin ambas clases binarias.")
        self.names = [f"f{i}" for i in range(len(features))]
        if np.isinf(self.x_train).any():
            raise ValueError("Infinitos en la matriz de entrenamiento.")
        if not training_only:
            self.x_valid = valid.select(features).to_numpy().astype(np.float32, copy=False)
            self.y_valid = (valid[LABEL] == "BAJA+2").to_numpy().astype(np.int8)
            self.ids_valid = valid[ID].to_numpy()
            if np.isinf(self.x_valid).any():
                raise ValueError("Infinitos en validación.")
            if with_test:
                self.x_test = test.select(features).to_numpy().astype(np.float32, copy=False)
                self.ids_test = test[ID].to_numpy()
                if np.isinf(self.x_test).any():
                    raise ValueError("Infinitos en test.")
            binary_auc(self.y_valid, np.full(len(self.y_valid), 0.5))

    def train_dataset(self):
        return lgb.Dataset(self.x_train, label=self.y_train, feature_name=self.names, free_raw_data=False)


def lgb_params(cfg: dict, hp: dict, seed: int) -> dict:
    return dict(hp, objective="binary", metric="auc", verbosity=-1,
                bagging_freq=1, num_threads=cfg["threads"], deterministic=True,
                force_col_wise=True, seed=seed, data_random_seed=seed,
                bagging_seed=seed, feature_fraction_seed=seed)


def optimize(frame: pl.DataFrame, features: list[str], cfg: dict, folder: Path, budget: Budget) -> dict:
    folder.mkdir(parents=True, exist_ok=True)
    recipe = digest({"features": features, "space": cfg["search_space"], "trials": cfg["bo_trials"],
                     "seed": cfg["bo_seed"], "max_rounds": cfg["max_rounds"], "early_stop": cfg["early_stopping_rounds"]})
    best_file = folder / "best.json"
    if best_file.exists():
        saved = read_json(best_file)
        if saved["recipe"] != recipe:
            raise ValueError("Checkpoint BO incompatible.")
        return validate_hp(saved["hyperparams"])
    arrays = Arrays(frame, features, with_test=False)
    storage = "sqlite:///" + str((folder / "trials.sqlite3").resolve())
    study_name = "historia_" + recipe[:16]
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(study_name=study_name, storage=storage, direction="maximize", load_if_exists=True)
    # Un cierre abrupto no convierte un trial inconcluso en un resultado válido.
    for previous in study.get_trials(deepcopy=False, states=(optuna.trial.TrialState.RUNNING,)):
        study.tell(previous.number, state=optuna.trial.TrialState.FAIL)
    trials = study.get_trials(deepcopy=False)
    completed = sum(t.state == optuna.trial.TrialState.COMPLETE for t in trials)
    while completed < cfg["bo_trials"]:
        budget.check()
        # Semilla por número de trial: puede retomarse sin estado RNG oculto.
        index = len(study.get_trials(deepcopy=False))
        sampler = optuna.samplers.TPESampler(seed=cfg["bo_seed"] + index)
        study = optuna.load_study(study_name=study_name, storage=storage, sampler=sampler)
        trial = study.ask()
        params = {}
        try:
            for name, spec in cfg["search_space"].items():
                suggest = trial.suggest_int if spec["type"] == "int" else trial.suggest_float
                params[name] = suggest(name, spec["low"], spec["high"], log=bool(spec.get("log", False)))
            dtrain = arrays.train_dataset()  # Dataset nuevo: min_data_in_leaf puede cambiar.
            dvalid = lgb.Dataset(arrays.x_valid, label=arrays.y_valid, reference=dtrain,
                                 feature_name=arrays.names, free_raw_data=False)
            model = lgb.train(lgb_params(cfg, params, cfg["bo_seed"]), dtrain,
                              num_boost_round=cfg["max_rounds"], valid_sets=[dvalid], valid_names=["valid_201908"],
                              callbacks=[budget.callback(), lgb.early_stopping(cfg["early_stopping_rounds"],
                                         first_metric_only=True, verbose=False)])
            rounds = int(model.best_iteration or model.current_iteration())
            auc = binary_auc(arrays.y_valid, model.predict(arrays.x_valid, num_iteration=rounds))
            trial.set_user_attr("rounds", rounds)
            study.tell(trial, auc)
            completed += 1
            print(f"[{now()}] BO {folder.name}: {completed}/{cfg['bo_trials']}; AUC08={auc:.6f}", flush=True)
            del model, dtrain, dvalid
            gc.collect()
        except BaseException:
            study.tell(trial, state=optuna.trial.TrialState.FAIL)
            raise
    best = study.best_trial
    hp = validate_hp({"params": best.params, "rounds": best.user_attrs["rounds"]})
    trials = [{"trial": t.number, "state": t.state.name, "auc_val": t.value,
               "rounds": t.user_attrs.get("rounds"), **t.params} for t in study.get_trials(deepcopy=False)]
    write_table(folder / "trials.csv", trials, ["trial", "state", "auc_val", "rounds", *HP_NAMES])
    write_json(best_file, {"recipe": recipe, "hyperparams": hp, "best_trial": best.number,
                          "auc_val": best.value, "metric": "AUC 201908; BAJA+2 positiva"})
    return hp


class Runner:
    def __init__(self, cfg: dict, out: Path, budget: Budget, run_id: str):
        self.cfg, self.out, self.budget, self.run_id = cfg, out, budget, run_id
        self.results = read_json(out / "resultados.json") if (out / "resultados.json").exists() else []

    def store(self, row: dict):
        self.results = sorted([r for r in self.results if r["iteration"] != row["iteration"]] + [row], key=lambda r: r["iteration"])
        write_json(self.out / "resultados.json", self.results)
        rows = []
        for r in self.results:
            rows.append({"iteracion": r["iteration"], "tratamiento": r["name"], "hipotesis": r.get("hypothesis", ""),
                         "estado": r["status"], "resultado": r["decision"], "inicio": r.get("start", ""),
                         "fin": r.get("end", ""), "tiempo_min": r.get("minutes", ""), "n_features": r.get("n_features", ""),
                         "auc_val_201908_mean": r.get("auc_mean", ""), "auc_val_201908_std": r.get("auc_std", ""),
                         "auc_val_201908_ensemble": r.get("auc_ensemble", ""),
                         "ganancia_meseta_val_DIAGNOSTICA": r.get("plateau", {}).get("gain_smoothed", ""),
                         "envios_meseta_val_DIAGNOSTICA": r.get("plateau", {}).get("n_send", ""),
                         "delta_auc_vs_B0_mean": r.get("versus_baseline", {}).get("delta_mean", ""),
                         "wins_vs_B0": r.get("versus_baseline", {}).get("wins", ""),
                         "delta_auc_vs_B0_ensemble": r.get("versus_baseline", {}).get("delta_ensemble", ""),
                         "referencia": r.get("reference", ""),
                         "delta_auc_vs_referencia_mean": r.get("versus_reference", {}).get("delta_mean", ""),
                         "wins_vs_referencia": r.get("versus_reference", {}).get("wins", ""),
                         "delta_auc_vs_referencia_ensemble": r.get("versus_reference", {}).get("delta_ensemble", ""),
                         "motivo": r.get("reason", "")})
        columns = ["iteracion", "tratamiento", "hipotesis", "estado", "resultado", "inicio", "fin", "tiempo_min", "n_features",
                   "auc_val_201908_mean", "auc_val_201908_std", "auc_val_201908_ensemble", "ganancia_meseta_val_DIAGNOSTICA",
                   "envios_meseta_val_DIAGNOSTICA", "delta_auc_vs_B0_mean", "wins_vs_B0", "delta_auc_vs_B0_ensemble",
                   "referencia", "delta_auc_vs_referencia_mean", "wins_vs_referencia", "delta_auc_vs_referencia_ensemble", "motivo"]
        write_table(self.out / "resultados.tsv", rows, columns, "\t")

    def skip(self, number: int, name: str, reason: str):
        self.store({"iteration": f"{number:03}", "name": name, "status": "skipped", "decision": "no_ejecutado", "reason": reason})
        print(f"[{now()}] {number:03} omitida: {reason}", flush=True)

    def stage(self, number: int, name: str, hypothesis: str, frame: pl.DataFrame,
              features: list[str], hp: dict, baseline=None, reference=None) -> dict:
        self.budget.check()
        folder = self.out / "iteraciones" / f"{number:03}"
        folder.mkdir(parents=True, exist_ok=True)
        recipe = digest({"run": self.run_id, "features": features, "hyperparams": hp, "seeds": self.cfg["seeds"],
                         "baseline": baseline["iteration"] if baseline else None,
                         "reference": reference["iteration"] if reference else None})
        result_file = folder / "result.json"
        if result_file.exists():
            row = read_json(result_file)
            if row["recipe"] != recipe:
                raise ValueError(f"Receta incompatible en {folder}.")
            for export in row["exports"].values():
                if file_hash(folder / export["file"]) != export["sha256"]:
                    raise ValueError(f"Predicciones alteradas en {folder}.")
            self.store(row)
            print(f"[{now()}] {number:03} completa: reutilizada sin entrenar.", flush=True)
            return row
        meta_file = folder / "recipe.json"
        if meta_file.exists():
            meta = read_json(meta_file)
            if meta["recipe"] != recipe:
                raise ValueError(f"Receta de iteración parcial incompatible: {folder}.")
        else:
            meta = {"recipe": recipe, "start": now(), "start_unix": time.time(), "hypothesis": hypothesis,
                    "features": features, "hyperparams": hp, "seeds": self.cfg["seeds"]}
            write_json(meta_file, meta)
        arrays = Arrays(frame, features)
        write_json(folder / "features.json", features)
        write_json(folder / "hyperparams.json", hp)
        aucs, gains = [], []
        sum_val = np.zeros(len(arrays.y_valid), dtype=np.float64)
        sum_test = np.zeros(len(arrays.ids_test), dtype=np.float64)
        dtrain = None
        for seed in self.cfg["seeds"]:
            self.budget.check()
            prefix = folder / f"seed_{seed}"
            checkpoint, model_path, scores_path = prefix.with_suffix(".json"), prefix.with_suffix(".txt"), prefix.with_suffix(".npz")
            if checkpoint.exists():
                saved = read_json(checkpoint)
                if saved["recipe"] != recipe or saved["model_sha256"] != file_hash(model_path) or saved["scores_sha256"] != file_hash(scores_path):
                    raise ValueError(f"Checkpoint alterado/incompatible: {checkpoint}.")
                with np.load(scores_path, allow_pickle=False) as scores:
                    pv, pt, gain = scores["validation"], scores["test"], scores["gain"]
            else:
                # data_random_seed también cambia: no reutilizar un Dataset
                # ya construido con otra semilla de binning.
                dtrain = arrays.train_dataset()
                print(f"[{now()}] {number:03} {name}: semilla {seed}", flush=True)
                model = lgb.train(lgb_params(self.cfg, hp["params"], seed), dtrain,
                                  num_boost_round=hp["rounds"], callbacks=[self.budget.callback()])
                pv = model.predict(arrays.x_valid, num_iteration=hp["rounds"])
                pt = model.predict(arrays.x_test, num_iteration=hp["rounds"])
                gain = model.feature_importance(importance_type="gain").astype(np.float64)
                model_tmp = model_path.with_suffix(".txt.tmp")
                model.save_model(str(model_tmp))
                model_tmp.replace(model_path)
                scores_tmp = scores_path.with_suffix(".npz.tmp")
                with scores_tmp.open("wb") as handle:
                    np.savez_compressed(handle, validation=pv, test=pt, gain=gain)
                scores_tmp.replace(scores_path)
                write_json(checkpoint, {"recipe": recipe, "seed": seed, "finished": now(),
                                       "model_sha256": file_hash(model_path), "scores_sha256": file_hash(scores_path)})
                del model
            if pv.shape != sum_val.shape or pt.shape != sum_test.shape or gain.shape != (len(features),):
                raise ValueError("Dimensión incorrecta en checkpoint/predicciones.")
            if not np.isfinite(pt).all() or ((pt < 0) | (pt > 1)).any() or not np.isfinite(gain).all() or (gain < 0).any():
                raise ValueError("Predicciones o importancia inválidas.")
            aucs.append(binary_auc(arrays.y_valid, pv))
            gains.append(gain)
            sum_val += pv
            sum_test += pt
        pv, pt = sum_val / len(aucs), sum_test / len(aucs)
        exports = {}
        for month, ids, probabilities in ((201908, arrays.ids_valid, pv), (201910, arrays.ids_test, pt)):
            path = folder / f"pred_{month}.csv"
            tmp = path.with_suffix(".csv.tmp")
            pl.DataFrame({ID: ids, "probabilidad": probabilities}).write_csv(tmp)
            tmp.replace(path)
            exports[str(month)] = {"file": path.name, "sha256": file_hash(path), "rows": len(ids)}
        gains = np.asarray(gains)
        total = gains.sum(axis=1, keepdims=True)
        norm = np.divide(gains, total, out=np.zeros_like(gains), where=total > 0)
        importance = [{"feature": f, "gain_mean": float(gains[:, i].mean()), "gain_fraction_mean": float(norm[:, i].mean())}
                      for i, f in enumerate(features)]
        write_table(folder / "importance.csv", importance, ["feature", "gain_mean", "gain_fraction_mean"])
        row = {"iteration": f"{number:03}", "name": name, "hypothesis": hypothesis, "recipe": recipe,
               "status": "completed", "decision": "baseline" if baseline is None else "descartado",
               "start": meta["start"], "end": now(), "minutes": (time.time() - meta["start_unix"]) / 60,
               "features": features, "n_features": len(features), "hyperparams": hp,
               "seeds": self.cfg["seeds"], "seed_aucs": aucs, "auc_mean": float(np.mean(aucs)),
               "auc_std": float(np.std(aucs, ddof=1)) if len(aucs) > 1 else None,
               "auc_ensemble": binary_auc(arrays.y_valid, pv),
               "plateau": diagnostic_plateau(arrays.ids_valid, arrays.y_valid, pv, self.cfg["plateau_window"],
                                              self.cfg["gain_pos"], self.cfg["gain_neg"]),
               "importance": importance, "exports": exports,
               "test_metric": None, "test_status": "SOLO_PREDICCIONES_EVALUACION_EXTERNA_PENDIENTE"}
        if baseline is not None:
            def compare(ref):
                if ref["seeds"] != row["seeds"]:
                    raise ValueError("No coinciden las semillas pareadas.")
                return paired_decision(aucs, ref["seed_aucs"], row["auc_ensemble"], ref["auc_ensemble"],
                                       self.cfg["min_delta_auc_keep"], self.cfg["min_wins_keep"])
            row["versus_baseline"] = compare(baseline)
            row["versus_reference"] = compare(reference or baseline)
            if row["versus_baseline"]["accepted"] and row["versus_reference"]["accepted"]:
                row["decision"] = "mantenido"
            row["reference"] = (reference or baseline)["iteration"]
            row["reason"] = (f"Cumple regla vs B0: {row['versus_baseline']['accepted']}; "
                             f"vs referencia {row['reference']}: {row['versus_reference']['accepted']}. "
                             "Regla de AUC/semillas/ensamble, sin p-valor ni uso de octubre.")
        write_json(result_file, row)
        self.store(row)
        del arrays, dtrain
        gc.collect()
        print(f"[{now()}] {number:03} {row['decision']}; AUC08 ensamble={row['auc_ensemble']:.6f}", flush=True)
        return row


def select_leaders(base: dict, original: list[str], cfg: dict, out: Path) -> list[str]:
    pool = cfg["core_candidates"]
    if not isinstance(pool, list) or len(pool) != len(set(pool)) or not pool:
        raise ValueError("core_candidates debe ser una lista única, explícita y no vacía.")
    missing = set(pool) - set(original)
    if missing:
        raise ValueError(f"Candidatas ausentes o excluidas: {sorted(missing)}. Revisar config; no se sustituyen silenciosamente.")
    importance = {row["feature"]: row["gain_fraction_mean"] for row in base["importance"]}
    rows = []
    for source in pool:
        relatives = [source] + [f"{source}__{op}{k}" for k in (1, 2) for op in ("lag", "delta")]
        rows.append({"variable": source, "family_gain_fraction": sum(importance.get(c, 0) for c in relatives)})
    rows.sort(key=lambda r: (-r["family_gain_fraction"], r["variable"]))
    selected = [row["variable"] for row in rows[:cfg["top_core"]]]
    write_json(out / "core_frozen.json", {"rule": "Top core_candidates por Gain normalizado medio de RAW+lag/delta1/2 en modelos B0; sólo train03–06",
                                          "rows": rows, "selected": selected,
                                          "warning": "Importancia de entrenamiento, no prueba de causalidad ni garantía de utilidad fuera de tiempo."})
    return selected


def screen_canaries(frame, features, baseline_features, hp, cfg, out: Path, budget: Budget, run_id: str) -> list[str]:
    recipe = digest({"run": run_id, "features": features, "hp": hp, "base": baseline_features})
    saved_file = out / "canary_screen.json"
    if saved_file.exists():
        saved = read_json(saved_file)
        if saved["recipe"] != recipe or saved["table_sha256"] != file_hash(out / "screen_importance.csv"):
            raise ValueError("Checkpoint de canaritos incompatible/alterado.")
        return saved["features_kept"]
    budget.check()
    arrays = Arrays(frame, features, training_only=True)
    rng = np.random.default_rng(cfg["canary_seed"])
    noise = rng.uniform(0, 1, size=(len(arrays.y_train), cfg["canary_count"])).astype(np.float32)
    augmented = np.concatenate([arrays.x_train, noise], axis=1)
    names = features + [f"canarito_{i:03}" for i in range(cfg["canary_count"])]
    data = lgb.Dataset(augmented, label=arrays.y_train, feature_name=[f"f{i}" for i in range(len(names))])
    model = lgb.train(lgb_params(cfg, hp["params"], cfg["canary_seed"]), data,
                      num_boost_round=hp["rounds"], callbacks=[budget.callback()])
    gain = model.feature_importance(importance_type="gain").astype(np.float64)
    threshold = float(np.quantile(gain[len(features):], cfg["canary_quantile"]))
    base = set(baseline_features)
    kept = [f for f, value in zip(features, gain[:len(features)]) if f in base or value > threshold]
    rows = [{"feature": name, "gain": float(value), "noise_threshold": threshold,
             "is_canary": i >= len(features), "protected_baseline": name in base,
             "kept": name in kept} for i, (name, value) in enumerate(zip(names, gain))]
    table = out / "screen_importance.csv"
    write_table(table, rows, ["feature", "gain", "noise_threshold", "is_canary", "protected_baseline", "kept"])
    write_json(saved_file, {"recipe": recipe, "features_kept": kept, "threshold": threshold,
                           "table_sha256": file_hash(table), "seed": cfg["canary_seed"],
                           "warning": "Filtro heurístico de una semilla; no es Boruta ni control formal del error estadístico."})
    return kept


def write_final(runner: Runner, *, pilot=False):
    winner = choose_winner(runner.results)
    baseline = next(row for row in runner.results if row["iteration"] == "000")
    exports = {}
    for label, row in (("baseline", baseline), ("selected", winner)):
        folder = runner.out / "iteraciones" / row["iteration"]
        exports[label] = {"iteration": row["iteration"], "prediction_201910": str(folder / row["exports"]["201910"]["file"]),
                          "sha256": row["exports"]["201910"]["sha256"], "auc_selection_201908": row["auc_ensemble"]}
    write_json(runner.out / "FINAL.json", {"status": "PILOTO_TECNICO_NO_CONCLUSION" if pilot else "MODELOS_CONGELADOS_TEST_EXTERNO_PENDIENTE",
                                         "finished": now(), "run_id": runner.run_id, "exports": exports,
                                         "chosen_on": "AUC 201908, exclusivamente",
                                         "test_gain": None, "test_auc": None,
                                         "instruction": "Evaluar GANANCIA en 201910 fuera de este runner con la regla acordada. No elegir modelos ni cortes mirando octubre.",
                                         "scores": "Modelo entrenado en BAJA+1+BAJA+2; score de ranking, no probabilidad calibrada de BAJA+2."})
    return winner


def pipeline(cfg: dict, out: Path, budget: Budget, run_id: str):
    print(f"[{now()}] Lectura y auditoría; modo {cfg['mode']}. Octubre sin etiquetas.", flush=True)
    frame, original, audit = load_and_audit(cfg)
    frame = frame.sort([MONTH, ID])
    by_month = audit.pop("variables_by_month")
    write_json(out / "audit.json", audit)
    write_table(out / "audit_variables_by_month.csv", by_month, ["foto_mes", "variable", "rows", "nulls", "zeros", "min", "max"])
    valid_rows = audit["partitions"]["validation"]
    if cfg["plateau_window"] > valid_rows:
        raise ValueError("plateau_window excede las filas de agosto; ajustar explícitamente, no se recorta sola.")
    # Comprobar el contrato incluso en preflight, sin construir matrices anchas.
    raw_train, raw_valid, _ = split_partitions(frame)
    if raw_train.select(pl.col(LABEL).is_in(["BAJA+1", "BAJA+2"]).n_unique()).item() != 2:
        raise ValueError("Train requiere ambas clases binarias.")
    binary_auc((raw_valid[LABEL] == "BAJA+2").to_numpy(), np.full(raw_valid.height, 0.5))
    del raw_train, raw_valid, _
    lists_to_check = ["core_candidates", "zero_columns", "ratio_columns", "monetary_columns"]
    for field in lists_to_check:
        values = cfg.get(field, [])
        if not isinstance(values, list) or len(values) != len(set(values)) or set(values) - set(original):
            raise ValueError(f"{field}: revisar nombres ausentes, excluidos o duplicados.")
    estimate = audit["retained_rows"] * len(original) * 5 * 4
    write_json(out / "preflight.json", {"status": "DATOS_LEIBLES_CONTRATO_OK", "mode": cfg["mode"],
                                       "baseline_features_expected": len(original) * 5,
                                       "baseline_float32_payload_gib": estimate / 1024**3,
                                       "memory_warning": "Sólo valores del panel: faltan joins, matrices y estructuras LightGBM; no es estimación de RAM pico.",
                                       "sanitization_reviewed": cfg["sanitization_reviewed"],
                                       "next": "Revisar audit.json/audit_variables_by_month.csv y broken_variables. Pilot antes de full.",
                                       "readiness": "No afirma compatibilidad histórica exacta con otro baseline ni prueba de entrenamiento."})
    print(f"[{now()}] Preflight OK. RAW={len(original)}, baseline={len(original)*5}. Panel Float32 mínimo≈{estimate/1024**3:.2f} GiB.", flush=True)
    if cfg["mode"] == "preflight":
        return
    if not cfg["sanitization_reviewed"]:
        raise ValueError("Entrenamiento bloqueado: falta revisar saneamiento. Ver audit.json y luego --sanitization-reviewed, sólo si corresponde.")
    budget.check()
    frame = add_lags_deltas(frame, original)
    base_features = original + [f"{col}__{op}{k}" for col in original for k in (1, 2) for op in ("lag", "delta")]
    runner = Runner(cfg, out, budget, run_id)
    if cfg.get("baseline_hyperparams_file"):
        hp = validate_hp(read_json(Path(cfg["baseline_hyperparams_file"])))
        source = "Archivo externo explícito; resultados no importados ni garantizados."
    else:
        hp = optimize(frame, base_features, cfg, out / "bo_baseline", budget)
        source = "BO 201908; train03–06"
    write_json(out / "b0_hyperparams.json", hp)
    write_json(out / "b0_hyperparams_source.json", {"source": source})
    baseline = runner.stage(0, "B0_baseline", "Referencia RAW + lag/delta1/2, train03–06 completo.", frame, base_features, hp)
    if cfg["mode"] == "pilot":
        write_final(runner, pilot=True)
        return
    budget.check()
    leaders = select_leaders(baseline, original, cfg, out)
    frame, families, manifest = build_hypothesis_families(frame, original, leaders, cfg)
    write_json(out / "feature_manifest.json", manifest)
    write_json(out / "families.json", families)
    tasks = [
        (1, "resumen_3m", "Media, mínimo, máximo y std3 ddof0 sobre tres fotos; representación adicional, no meses nuevos."),
        (2, "inactividad", "Rachas observadas de cero en variables explícitas; cero y faltante no son equivalentes."),
        (3, "ratios_personales", "Valor/mean3 con ventana completa no negativa; los negativos quedan NA."),
        (4, "rangos_monetarios", "Paquete de rango intra-mes y derivados; probar robustez de representación, no inmunidad al drift."),
    ]
    accepted_families = []
    for number, family, hypothesis in tasks:
        if (family == "rangos_monetarios" and not cfg.get("enable_rank_package")) or not families[family]:
            runner.skip(number, family, "Familia desactivada o sin columnas elegibles.")
            continue
        row = runner.stage(number, family, hypothesis, frame, base_features + families[family], hp, baseline=baseline)
        if row["decision"] == "mantenido":
            accepted_families.append(family)
    if len(accepted_families) >= 2:
        union = list(dict.fromkeys(base_features + [f for family in accepted_families for f in families[family]]))
        runner.stage(5, "union_familias", "Unir únicamente las familias aceptadas frente a B0; puede perder por interacción.",
                     frame, union, hp, baseline=baseline)
    else:
        runner.skip(5, "union_familias", "Menos de dos familias aceptadas: no duplicar un modelo ni rescatar familias descartadas.")
    parent = choose_winner([r for r in runner.results if int(r["iteration"]) <= 5])
    if cfg.get("enable_canaries") and parent["iteration"] != "000":
        kept = screen_canaries(frame, parent["features"], base_features, hp, cfg, out, budget, run_id)
        if kept == parent["features"] or set(kept) == set(base_features):
            runner.skip(6, "canaritos", "La poda repite un modelo ya evaluado (padre o B0); consultar screen_importance.csv.")
        else:
            runner.stage(6, "canaritos", "Filtrar sólo nuevas columnas por Gain > p95 del ruido; proteger todas las columnas B0.",
                         frame, kept, hp, baseline=baseline, reference=parent)
    else:
        runner.skip(6, "canaritos", "Desactivado o ninguna variante mejoró a B0.")
    parent = choose_winner([r for r in runner.results if int(r["iteration"]) <= 6])
    if cfg.get("enable_final_bo") and parent["iteration"] != "000":
        tuned = optimize(frame, parent["features"], cfg, out / "bo_final", budget)
        runner.stage(7, "BO_final", "Reoptimización separada de la representación elegida; comparar de nuevo con padre y B0.",
                     frame, parent["features"], tuned, baseline=baseline, reference=parent)
    else:
        runner.skip(7, "BO_final", "Desactivado o ninguna variante mejoró a B0.")
    winner = write_final(runner)
    print(f"[{now()}] Final: iteración {winner['iteration']}. Predicciones de octubre listas; ganancia de test NO evaluada.", flush=True)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config_historia.json")
    parser.add_argument("--data", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=["preflight", "pilot", "full"], default="preflight")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--sanitization-reviewed", action="store_true")
    args = parser.parse_args(argv)
    cfg = read_config(args)
    out = args.output.expanduser().resolve()
    if args.resume:
        if not (out / "run_manifest.json").is_file():
            raise ValueError("--resume requiere una carpeta con run_manifest.json existente.")
    else:
        if out.exists():
            raise FileExistsError(f"La salida ya existe: {out}. Usar una carpeta nueva o --resume sin cambiar receta.")
        out.mkdir(parents=True)
    with locked(out):
        print(f"[{now()}] Verificando identidad de datos/código/configuración (SHA256).", flush=True)
        ident = identity(cfg)
        run_id = digest(ident)
        if args.resume:
            run_manifest = read_json(out / "run_manifest.json")
            if run_manifest["run_id"] != run_id:
                raise ValueError("No se puede reanudar: cambiaron datos, código, configuración o versiones. Usar una salida nueva.")
        else:
            start = time.time()
            run_manifest = {"run_id": run_id, "start": now(), "start_utc": datetime.fromtimestamp(start, timezone.utc).isoformat(),
                            "start_unix": start, "deadline_unix": start + cfg["max_hours"] * 3600, "identity": ident}
            write_json(out / "run_manifest.json", run_manifest)
            write_json(out / "config_frozen.json", cfg)
        budget = Budget(out, run_manifest["deadline_unix"])
        try:
            if (out / "FINAL.json").exists() and cfg["mode"] != "preflight":
                # Verificar exportaciones completas antes de declarar la corrida terminada.
                for row in read_json(out / "resultados.json"):
                    for export in row.get("exports", {}).values():
                        path = out / "iteraciones" / row["iteration"] / export["file"]
                        if file_hash(path) != export["sha256"]:
                            raise ValueError(f"Exportación final alterada: {path}")
                print(f"[{now()}] La corrida ya está completa. No se volvió a entrenar.", flush=True)
                return 0
            pipeline(cfg, out, budget, run_id)
            write_json(out / "status.json", {"status": "complete", "at": now(), "mode": cfg["mode"]})
            return 0
        except (Paused, KeyboardInterrupt) as exc:
            write_json(out / "status.json", {"status": "paused", "at": now(), "reason": str(exc) or "Interrupción de teclado"})
            print(f"PAUSADO: {exc}. Los checkpoints completos se conservan.", file=sys.stderr, flush=True)
            return 2
        except Exception as exc:
            write_json(out / "status.json", {"status": "error", "at": now(), "reason": str(exc), "type": type(exc).__name__})
            raise


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        sys.exit(1)
