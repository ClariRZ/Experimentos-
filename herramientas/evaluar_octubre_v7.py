"""Continuation of a frozen v7, one in-memory feature matrix at a time; no fitting."""
import argparse
import gc
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import time


def load_original(source):
    scripts = source.parents[1] / 'scripts'
    sys.path.insert(0, str(scripts))
    spec = importlib.util.spec_from_file_location('frozen_v7_runner', scripts / 'ejecutar_v7.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    identity = json.loads((source / 'code_identity.json').read_text())
    for name, digest in identity.items():
        if module.sha(scripts / name) != digest:
            raise ValueError('Original code mismatch: ' + name)
    return module


def frame_for_arm(m, hist, raw, cfg, registry, arm):
    frame = hist
    if arm == 'H_T':
        frame, _ = m.extras(frame, 'R4', cfg['data']['history_sources'])
        frame, _ = m.extras(frame, 'T4', cfg['data']['history_sources'])
    elif arm == 'H_S':
        frame, _ = m.extras(frame, 'R4', cfg['data']['history_sources'])
        frame, _ = m.extras(frame, 'SYM', cfg['data']['history_sources'])
    elif arm != 'B0':
        frame, _ = m.extras(frame, arm, cfg['data']['history_sources'])
    cols = registry[arm]['columns']
    return m.numeric(frame.select([m.ID, m.MONTH, *cols]), cols)


def evaluate(source, output, dataset, deadline, clean_training_matrices=False):
    m = load_original(source)
    cfg = json.loads((source / 'config_frozen.json').read_text())
    frozen = json.loads((source / 'policy_frozen.json').read_text())
    registry = json.loads((source / 'feature_manifest.json').read_text())
    if (source / 'FINAL.json').exists():
        raise ValueError('Original run already has a final result; refusing duplicate evaluation')
    if json.loads((source / 'status.json').read_text())['status'] != 'DEVELOPMENT_FROZEN':
        raise ValueError('Development is not frozen')
    if m.sha(dataset) != cfg['data']['sha256']:
        raise ValueError('Dataset mismatch')
    for name, h in frozen['source_hashes'].items():
        if m.sha(source / name) != h:
            raise ValueError('Frozen source mismatch: ' + name)
    for arm, hashes in frozen['models'].items():
        for artifacts in hashes.values():
            for name, h in artifacts.items():
                if m.sha(source / 'private' / arm / name) != h:
                    raise ValueError('Frozen model/prediction mismatch')
    environment = m.capture_environment(cfg)
    output.mkdir(parents=True, exist_ok=False)
    private = output / 'private'
    private.mkdir()
    m.save(output / 'continuation.json', {'source': str(source), 'source_policy_sha256': m.sha(source / 'policy_frozen.json'),
        'new_fits': 0, 'feature_generation': 'original functions, frozen columns, one arm at a time in memory',
        'script_sha256': m.sha(Path(__file__)), 'started_epoch': time.time()})
    m.save(output / 'environment.json', environment)
    for name in ['config_frozen.json', 'feature_manifest.json', 'policy_frozen.json', 'comparisons_201908.json', 'common_policy.json']:
        shutil.copy2(source / name, output / name)
    for arm in m.ARMS:
        (output / arm).mkdir()
        shutil.copy2(source / arm / 'result_august.json', output / arm / 'result_august.json')
    # Remove only known generated training matrices, after exact hash verification.
    # Original models, predictions, metadata and manifests remain untouched.
    if clean_training_matrices:
        removed = []
        for arm in m.ARMS:
            p = source / 'private' / (arm + '.parquet')
            if p.exists():
                if p.is_symlink() or m.sha(p) != registry[arm]['matrix_sha256']:
                    raise ValueError('Matrix identity mismatch; refusing removal: ' + arm)
                record = {'path': str(p), 'sha256': registry[arm]['matrix_sha256'], 'bytes': p.stat().st_size,
                          'reason': 'Generated training matrix; training frozen; models and predictions verified; unused by continuation'}
                with (output / 'removed_generated_matrices.jsonl').open('a') as f:
                    f.write(json.dumps(record) + '\n'); f.flush(); os.fsync(f.fileno())
                p.unlink()
                removed.append(record)
                m.save(output / 'removed_generated_matrices.json', removed)
    runner = m.Runner.__new__(m.Runner)
    runner.cfg = cfg; runner.out = output; runner.private = private
    runner.start = time.time(); runner.deadline = deadline; runner.fits = 150
    runner.registry = registry; runner.dataset = dataset
    runner.policies = frozen['policies']; runner.common_prop = frozen['common_proportion']
    runner.common_k = frozen['common_august_k']
    runner.check()
    runner.state('PREPARING_OCTOBER_NO_TRAINING')
    df = m.read_data(dataset, list(range(201901, 201911)), labels=False)
    m.save(output / 'coverage_provenance_october.json', m.coverage_provenance(df, cfg, [201908, 201910]))
    hist, raw = m.history(df, cfg, [201908, 201910]); del df; gc.collect()
    saved_ids = m.np.load(source / 'private' / 'august_labels.npz')['ids']
    verification = {}; octids = None
    for arm in m.ARMS:
        runner.check(); runner.state('VERIFY_AUGUST_AND_SCORE_OCTOBER', arm=arm)
        frame = frame_for_arm(m, hist, raw, cfg, registry, arm)
        va = frame.filter(m.pl.col(m.MONTH) == 201908)
        ot = frame.filter(m.pl.col(m.MONTH) == 201910)
        if not m.np.array_equal(va[m.ID].to_numpy(), saved_ids):
            raise ValueError('August IDs changed')
        ids = ot[m.ID].to_numpy()
        if octids is None: octids = ids
        if not m.np.array_equal(ids, octids): raise ValueError('October IDs differ')
        cols = registry[arm]['columns']
        x = va.select(cols).to_numpy(order='c'); xo = ot.select(cols).to_numpy(order='c')
        dest = private / arm; dest.mkdir(); preds = []; verification[arm] = {}
        for seed in cfg['evaluation']['seeds']:
            runner.check()
            model = m.lgb.Booster(model_file=str(source / 'private' / arm / f'seed_{seed}.txt'))
            pred = model.predict(x, num_threads=4)
            stored = m.np.load(source / 'private' / arm / f'seed_{seed}.npz')['prediction']
            if not m.np.array_equal(pred, stored): raise ValueError('August predictions differ: ' + arm)
            verification[arm][str(seed)] = {'exact': True, 'max_error': 0.0}
            po = model.predict(xo, num_threads=4); preds.append(po)
            m.np.savez_compressed(dest / f'seed_{seed}.npz', ids=ids, prediction=po)
        m.np.savez_compressed(dest / 'ensemble.npz', ids=ids, prediction=m.np.mean(preds, axis=0))
        m.save(output / 'august_verification.json', verification)
        del frame, va, ot, x, xo, preds, model; gc.collect()
    del hist; gc.collect()
    # Read October outcomes only after all fifty August checks and October predictions.
    labels = m.pl.scan_csv(dataset, infer_schema_length=20000).select([m.ID, m.MONTH, m.LABEL]).filter(m.pl.col(m.MONTH) == 201910).sort(m.ID).collect()
    if not m.np.array_equal(labels[m.ID].to_numpy(), octids): raise ValueError('October label IDs differ')
    if labels[m.LABEL].null_count() or not set(labels[m.LABEL].unique()) <= {'BAJA+1', 'BAJA+2', 'CONTINUA'}:
        raise ValueError('Invalid October labels')
    y = (labels[m.LABEL] == 'BAJA+2').to_numpy().astype(m.np.int8)
    cut = int(m.np.floor(runner.common_prop * len(y)))
    m.np.savez_compressed(private / 'labels.npz', ids=octids, y=y)
    for arm in m.ARMS:
        rows = []
        for seed in cfg['evaluation']['seeds']:
            p = m.np.load(private / arm / f'seed_{seed}.npz')['prediction']
            own = int(m.np.floor(runner.policies[arm]['seeds'][str(seed)] * len(y)))
            rows.append({'seed': seed, 'auc': float(m.roc_auc_score(y,p)), 'common': m.payoff(octids,p,y,cut)[0], 'own': m.payoff(octids,p,y,own)[0]})
        p = m.np.load(private / arm / 'ensemble.npz')['prediction']
        own = int(m.np.floor(runner.policies[arm]['ensemble'] * len(y)))
        m.save(output / arm / 'result_october.json', {'arm':arm, 'seeds':rows, 'ensemble_auc':float(m.roc_auc_score(y,p)),
            'common':m.payoff(octids,p,y,cut)[0], 'own':m.payoff(octids,p,y,own)[0]})
    runner.compare_month(201910, octids, y, cut, private)
    m.save(output / 'private_manifest.json', {str(p.relative_to(private)):m.sha(p) for p in private.rglob('*') if p.is_file()})
    m.save(output / 'FINAL.json', {'status':'COMPLETE_EXPLORATORY', 'source_run':str(source), 'new_fits':0,
        'original_fits':150, 'arms':m.ARMS, 'august_predictions_regenerated':50, 'common_october_contacts':cut,
        'seconds':time.time()-runner.start, 'independent_full_rerun':False})
    runner.state('COMPLETE')


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--dataset',type=Path,required=True);p.add_argument('--deadline',type=float,required=True)
    p.add_argument('--clean-training-matrices',action='store_true')
    a=p.parse_args()
    evaluate(a.source,a.output,a.dataset,a.deadline,a.clean_training_matrices)
