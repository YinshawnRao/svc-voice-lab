#!/usr/bin/env python3
"""Audited, serial regeneration and explicit replacement for the 2026-10-18 repair."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from common import ROOT, local_env
from download import hash_file

RUN = 'xinqiang-fa-repair-20261018'
WORK = ROOT / 'work' / RUN
STAGED = ROOT / 'outputs' / RUN
DEST = ROOT / 'outputs/stage10-xinqiang'
CONFIG = ROOT / 'config/experiments' / (RUN + '.json')
SPEC = ROOT / 'config/experiments' / (RUN + '-f0.json')
EVIDENCE = ROOT / 'reports/evidence' / RUN
PYTHON = ROOT / '.envs/seed-vc/bin/python'


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def replace_audio(source, target):
    temporary=target.with_name('.'+target.name+'.repair-tmp')
    if temporary.exists():raise RuntimeError('Unexpected replacement temporary file')
    shutil.copy2(source,temporary)
    assert hash_file(temporary)==hash_file(source)
    os.replace(temporary,target)


def logged(name, command):
    subprocess.run([sys.executable, str(ROOT/'scripts/run_logged.py'), '--name', name,
                    '--evidence-dir', str(EVIDENCE), '--', *map(str, command)],
                   cwd=ROOT, env=local_env(), check=True)


def generate():
    smoke = json.loads((EVIDENCE/'smoke-f0-validation.json').read_text())
    assert smoke['status'] == 'PASSED', 'Short smoke must pass first'
    c = json.loads(CONFIG.read_text())
    before = json.loads((WORK/'backup/manifest.json').read_text())
    for a in c['artists']:
        key = a['key']
        dest = STAGED/'full'/key
        original = json.loads((WORK/'backup/runs'/key/'run.json').read_text())
        assert hash_file(Path(original['source'])) == original['source_sha256']
        assert hash_file(Path(original['target'])) == a['reference_sha256']
        if not (dest/'run.json').exists():
            logged(RUN+'-'+key+'-convert', [PYTHON, ROOT/'scripts/seed_vc_local.py',
                   '--source', original['source'], '--target', original['target'],
                   '--run-id', RUN+'-'+key, '--output-dir', dest, '--steps', '30',
                   '--seed', '20261016', '--f0-repair', SPEC])
        run = json.loads((dest/'run.json').read_text())
        assert len(run['variants']) == 1
        assert run['source_f0_repair']['sha256'] == hash_file(SPEC)
        assert hash_file(ROOT/run['variants'][0]['path']) == run['variants'][0]['sha256']
        backing = Path(original['source']).parent/'source_accompaniment.wav'
        if not (dest/'evaluation.json').exists():
            logged(RUN+'-'+key+'-evaluate', [PYTHON, ROOT/'scripts/evaluate_stage2.py',
                                           '--run', dest/'run.json', '--accompaniment', backing])
        validation = EVIDENCE/(key+'-audio-validation.json')
        if not validation.exists():
            logged(RUN+'-'+key+'-validate', [PYTHON, ROOT/'scripts/validate_full_song.py',
                   '--run', dest/'run.json', '--duration', '31.4', '--evidence', validation])
        a['status'] = 'POC_PASSED'
        a['run_id'] = RUN+'-'+key
        a['generation_stage'] = RUN
        a['staged_run'] = str((dest/'run.json').relative_to(ROOT))
        a['previous_deliverables'] = next(x for x in before['artists'] if x['key']==key)['deliverables']
        a['metrics'] = {'inference_seconds': run['elapsed_seconds'],
                       'human_audition': False}
        dump(CONFIG, c)
        print('REGENERATED '+a['artist'], flush=True)
    c['status'] = 'POC_PASSED'
    c['technical_validation'] = 'PENDING_FOCUSED_F0_CHECK'
    dump(CONFIG, c)


def focused_check(smoke=False):
    os.environ.update(local_env())
    from seed_vc_local import verify_artifacts, block_network
    verify_artifacts(); block_network()
    import numpy as np
    import soundfile as sf
    import torch
    import torchaudio
    sys.path.insert(0, str(ROOT/'vendor/seed-vc'))
    from modules.rmvpe import RMVPE
    torch.set_num_threads(4)
    estimator = RMVPE(str(ROOT/'models/rmvpe/rmvpe.pt'), is_half=False, device=torch.device('cpu'))
    c = json.loads(CONFIG.read_text())
    pairs = [('smoke', STAGED/'smoke-baseline/seed-vc_AI.wav', STAGED/'smoke-fixed/seed-vc_AI.wav')] if smoke else [
        (a['key'], WORK/'backup'/Path(a['deliverables']['dry']['path']).name,
         STAGED/'full'/a['key']/'seed-vc_AI.wav') for a in c['artists']]
    rows = []
    for key, old, new in pairs:
        row = {'key': key}
        for label, path in [('before', old), ('after', new)]:
            wave, sr = sf.read(path, dtype='float32', always_2d=True)
            mono = torchaudio.functional.resample(torch.from_numpy(wave.mean(axis=1)), sr, 16000)
            with torch.no_grad():
                f0 = estimator.infer_from_audio(mono, thred=.03).astype(np.float32)
            # Estimate after synthesis independently of the edited conditioning array.
            local = f0[507:513]
            voiced = local > 50
            cents = 1200*np.log2(local[voiced]/470)
            row[label] = {'path': str(path.relative_to(ROOT)), 'sha256': hash_file(path),
                          'f0_4_9_to_5_3': f0[490:531].tolist(),
                          'interval_seconds': [5.07, 5.13], 'voiced_coverage': float(voiced.mean()),
                          'median_absolute_cents_from_470hz': float(np.median(np.abs(cents))) if len(cents) else None,
                          'lower_pitch_frames_below_400hz': int(((local > 50)&(local < 400)).sum())}
        assert row['before']['lower_pitch_frames_below_400hz'] >= 4
        assert row['after']['voiced_coverage'] == 1
        assert row['after']['lower_pitch_frames_below_400hz'] == 0
        assert row['after']['median_absolute_cents_from_470hz'] < 80
        rows.append(row)
        print(key, 'FOCUSED_F0_PASS', row['before']['median_absolute_cents_from_470hz'],
              row['after']['median_absolute_cents_from_470hz'], flush=True)
    result = {'status': 'PASSED', 'human_audition': False,
              'scope': 'six-frame competing-pitch excursion; not a subjective audio-quality score', 'rows': rows}
    dump(EVIDENCE/('smoke-f0-validation.json' if smoke else 'full-f0-validation.json'), result)


def install():
    from run_seven_experiment import page
    c = json.loads(CONFIG.read_text())
    validation = json.loads((EVIDENCE/'full-f0-validation.json').read_text())
    assert validation['status'] == 'PASSED' and len(validation['rows']) == 7
    # Reject concurrent changes before replacing any old deliverable.
    baseline = json.loads((WORK/'before-files.json').read_text())
    for row in baseline:
        if row['path'].startswith('outputs/stage10-xinqiang/'):
            assert hash_file(ROOT/row['path']) == row['sha256'], 'Concurrent modification: '+row['path']
            backup = WORK/'backup'/Path(row['path']).relative_to('outputs/stage10-xinqiang')
            assert hash_file(backup) == row['sha256'], 'Backup mismatch'
    for a in c['artists']:
        source = STAGED/'full'/a['key']
        focused = next(r for r in validation['rows'] if r['key']==a['key'])
        assert hash_file(source/'seed-vc_AI.wav') == focused['after']['sha256']
        assert json.loads((EVIDENCE/(a['key']+'-audio-validation.json')).read_text())['status']=='PASSED'
    changed = []
    for a in c['artists']:
        source = STAGED/'full'/a['key']
        dest = DEST/'runs'/a['key']
        # Keep the generation-time receipts intact in the staging directory.
        for path in source.iterdir():
            if path.name=='listen.html' or not path.is_file():
                continue
            target = dest/path.name
            if path.suffix in ('.json', '.jsonl'):
                body = path.read_text().replace(str(source.relative_to(ROOT)),str(dest.relative_to(ROOT)))
                target.write_text(body)
            else:
                replace_audio(path,target)
            changed.append(str(target.relative_to(ROOT)))
        run = json.loads((dest/'run.json').read_text())
        evaluation = json.loads((dest/'evaluation.json').read_text())
        # Both staging and final runs have the same depth below ROOT; their
        # already validated relative audio links remain valid after copying.
        assert len(source.relative_to(ROOT).parts)==len(dest.relative_to(ROOT).parts)
        replace_audio(source/'listen.html',dest/'listen.html')
        changed.append(str((dest/'listen.html').relative_to(ROOT)))
        for mode,filename in [('dry','seed-vc_AI.wav'),('mix','seed-vc_mix_AI.wav')]:
            target = ROOT/a['deliverables'][mode]['path']
            replace_audio(dest/filename,target)
            a['deliverables'][mode].update(sha256=hash_file(target),size_bytes=target.stat().st_size)
            changed.append(str(target.relative_to(ROOT)))
        a['metrics'].update(evaluation['variants'][0])
        a['metrics']['mps_allocated_peak_gib']=run['sampled_mps_allocated_peak_bytes']/1024**3
        a['metrics']['mps_driver_peak_gib']=run['sampled_mps_driver_peak_bytes']/1024**3
    c['installed_at'] = dt.datetime.now(dt.timezone.utc).isoformat()
    for key in ('created_at','extension_created_at','user_feedback','parent_batch_elapsed_seconds',
                'parent_started_at','parent_completed_at','extension_started_at',
                'extension_completed_at','extension_elapsed_seconds'):
        c.pop(key,None)
    c['parent_experiment']='config/experiments/stage11-xinqiang.json'
    runs=[json.loads((STAGED/'full'/a['key']/'run.json').read_text()) for a in c['artists']]
    c['started_at']=min(r['started_at'] for r in runs)
    c['completed_at']=c['installed_at']
    c['inference_seconds_total']=sum(r['elapsed_seconds'] for r in runs)
    c['technical_validation'] = 'PASSED; human listening pending'
    feedback=EVIDENCE/'user-smoke-feedback.json'
    if feedback.exists():c['user_smoke_feedback']=json.loads(feedback.read_text())
    c['backup_directory'] = str((WORK/'backup').relative_to(ROOT))
    dump(CONFIG,c);dump(DEST/'manifest.json',c)
    page(c)
    # A version query prevents stale audio in a previously opened listening page.
    p=DEST/'listen.html'
    body=p.read_text().replace('<section><h2 id="now">',
        '<p>已修复约 5 秒的音高误跳；七位均已重新生成，待复听。</p><section><h2 id="now">')
    for a in c['artists']:
        for mode in ('dry','mix'):
            name=Path(a['deliverables'][mode]['path']).name
            body=body.replace('"url": "'+name+'"','"url": "'+name+'?v='+a['deliverables'][mode]['sha256'][:12]+'"')
    p.write_text(body)
    changed.extend([str(p.relative_to(ROOT)),str((DEST/'manifest.json').relative_to(ROOT))])
    dump(EVIDENCE/'installed-files.json', {'files': changed,'installed_at':c['installed_at']})
    print('INSTALLED_7_SINGERS_14_WAVS')


def verify_installed():
    import re
    from urllib.parse import urlsplit, unquote
    import numpy as np
    import soundfile as sf
    c=json.loads((DEST/'manifest.json').read_text())
    assert c==json.loads(CONFIG.read_text())
    assert hash_file(ROOT/c['source_raw'])==c['source_sha256']
    for item in c['source_stems']:
        assert hash_file(ROOT/item['path'])==item['sha256']
    changed=set(json.loads((EVIDENCE/'installed-files.json').read_text())['files'])
    changed.add('scripts/seed_vc_local.py')
    protected=[]
    concurrent_path=EVIDENCE/'concurrent-changes.json'
    concurrent=json.loads(concurrent_path.read_text()) if concurrent_path.exists() else []
    concurrent_by_path={row['path']:row for row in concurrent}
    for row in json.loads((WORK/'before-files.json').read_text()):
        if row['path'] in changed:continue
        if row['path'] in concurrent_by_path:
            assert hash_file(ROOT/row['path'])==concurrent_by_path[row['path']]['current_sha256'], 'Concurrent file changed again'
            continue
        assert hash_file(ROOT/row['path'])==row['sha256'], 'Protected file changed: '+row['path']
        protected.append(row['path'])
    audio=[]
    for a in c['artists']:
        dest=DEST/'runs'/a['key']
        run=json.loads((dest/'run.json').read_text())
        assert hash_file(Path(run['source']))==run['source_sha256']
        assert hash_file(Path(run['target']))==run['target_sha256']==a['reference_sha256']
        prepared=json.loads((Path(run['source']).parent/'manifest.json').read_text())
        for item in prepared['files']:
            assert hash_file(ROOT/item['path'])==item['sha256']
        assert hash_file(SPEC)==run['source_f0_repair']['sha256']
        repair=json.loads((dest/'f0-repair-applied.json').read_text())['repairs']
        assert len(repair)==1 and repair[0]['start_frame']==507 and repair[0]['end_frame_exclusive']==513
        assert run['requested_steps']==[30] and run['seed']==20261016
        for mode,filename,channels in [('dry','seed-vc_AI.wav',1),('mix','seed-vc_mix_AI.wav',2)]:
            row=a['deliverables'][mode];path=ROOT/row['path']
            assert hash_file(path)==row['sha256']==hash_file(dest/filename)
            wave,sr=sf.read(path,always_2d=True)
            assert sr==44100 and wave.shape[1]==channels and np.isfinite(wave).all()
            assert np.sqrt(np.mean(wave**2))>1e-4
            assert abs(len(wave)/sr-31.4)<.012
            if mode=='mix':assert np.max(np.abs(wave))<=.981
            audio.append({'artist':a['artist'],'mode':mode,'sha256':row['sha256'],
                          'seconds':len(wave)/sr,'channels':channels,'peak':float(np.max(np.abs(wave)))})
    # Check every dynamic track URL, including the cache-busting query.
    body=(DEST/'listen.html').read_text()
    tracks=json.loads(re.search(r'const tracks=(.*?);\n',body).group(1))
    assert len(tracks)==23
    for track in tracks:
        url=urlsplit(track['url'])
        assert not url.scheme and not url.netloc
        assert (DEST/unquote(url.path)).is_file()
    node=subprocess.run(['node',str(ROOT/'scripts/check_group_player.cjs'),str(DEST/'listen.html')],
                        cwd=ROOT,capture_output=True,text=True,check=True)
    result={'status':'PASSED','audio':audio,'protected_baseline_files_unchanged':len(protected),
            'protected_paths':protected,'concurrent_changes_not_written_by_this_task':concurrent,
            'player':json.loads(node.stdout),'human_audition':False}
    dump(EVIDENCE/'final-validation.json',result)
    print(json.dumps({'status':'PASSED','final_wavs':len(audio),'protected_files':len(protected),
                      'player':result['player']},ensure_ascii=False))


def archive_intermediates():
    """Keep the user's existing output directory as the only final delivery."""
    assert json.loads((EVIDENCE/'final-validation.json').read_text())['status']=='PASSED'
    archive=WORK/'generation-evidence'
    assert STAGED.is_dir() and not archive.exists()
    before={str(p.relative_to(STAGED)):hash_file(p) for p in STAGED.rglob('*') if p.is_file()}
    shutil.move(str(STAGED),str(archive))
    assert not STAGED.exists()
    assert all(hash_file(archive/relative)==digest for relative,digest in before.items())
    c=json.loads(CONFIG.read_text())
    for a in c['artists']:
        a['staged_run']=str((archive/'full'/a['key']/'run.json').relative_to(ROOT))
    c['generation_evidence_archive']=str(archive.relative_to(ROOT))
    if 'user_smoke_feedback' in c:
        c['user_smoke_feedback']['archived_smoke_file']=str((archive/'smoke-fixed/seed-vc_AI.wav').relative_to(ROOT))
    dump(CONFIG,c);dump(DEST/'manifest.json',c)
    dump(EVIDENCE/'intermediate-archive.json',{'from':str(STAGED.relative_to(ROOT)),
        'to':str(archive.relative_to(ROOT)),'files_sha256':before,
        'note':'Generation-time receipts retain historical paths; this map resolves their archived locations.'})
    print('INTERMEDIATES_ARCHIVED_TO_WORK; FINAL_DESTINATION_UNCHANGED')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['generate','check-smoke','check-full','install','verify-installed','archive'])
    action=parser.parse_args().action
    if action=='generate':generate()
    elif action=='check-smoke':focused_check(smoke=True)
    elif action=='check-full':focused_check()
    elif action=='install':install()
    elif action=='verify-installed':verify_installed()
    else:archive_intermediates()
