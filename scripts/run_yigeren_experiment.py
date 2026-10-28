#!/usr/bin/env python3
"""Stage21: all seven fixed references singing 林凡《一个人生活》."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

from common import ROOT, local_env
from download import hash_file, records, charged, reservations
from run_seven_experiment import copy_checked, dump, page

EVIDENCE = ROOT / 'reports/evidence/stage21'
KEYS = ('yigeren',)
ARTIST_COUNT = 7


def wait_for_heavy():
    """Wait for the already-running local experiment without interrupting it."""
    started = time.monotonic()
    observed = set()
    patterns = ('scripts/extend_shouxin_experiment.py generate',
                'scripts/run_turan_experiment.py', 'scripts/run_xingfu_experiment.py',
                'scripts/run_nanguo_experiment.py generate',
                'scripts/run_haohao_experiment.py generate',
                'scripts/run_yongqi_experiment.py generate',
                'scripts/run_yigeren_experiment.py generate',
                'scripts/run_stage2_poc.py', 'scripts/seed_vc_local.py',
                'scripts/evaluate_stage2.py', 'scripts/transcribe_local.py', '-m demucs')
    while True:
        result = subprocess.run(['ps', '-axo', 'pid=,command='], check=True,
                                capture_output=True, text=True)
        active = []
        for line in result.stdout.splitlines():
            fields = line.strip().split(None, 1)
            if len(fields) != 2 or int(fields[0]) == os.getpid():
                continue
            if any(pattern in fields[1] for pattern in patterns):
                active.append(int(fields[0]))
        if not active:
            break
        observed.update(active)
        print('WAIT_HEAVY', active, round(time.monotonic()-started, 1), flush=True)
        if time.monotonic()-started > 3600:
            raise RuntimeError('Heavy process still running after one hour; preserve it')
        time.sleep(30)
    dump(EVIDENCE/f'queue-{time.time_ns()}.json', {
        'waited_seconds': time.monotonic()-started, 'observed_pids': sorted(observed),
        'checked_at': dt.datetime.now(dt.timezone.utc).isoformat(),
        'policy': 'Existing experiment preserved; no concurrent heavy local model'})


def config_path(key):
    return ROOT / f'config/experiments/stage21-{key}.json'


def load(key):
    return json.loads(config_path(key).read_text())


def save(key, c):
    dump(config_path(key), c)
    dump(ROOT / c['output_directory'] / 'manifest.json', c)


def command(args):
    subprocess.run(list(map(str, args)), cwd=ROOT, env=local_env(), check=True)


def logged(name, args, timeout=900):
    command(['python3', 'scripts/run_logged.py', '--name', name,
             '--evidence-dir', EVIDENCE, '--timeout', timeout, '--', *args])


def stems(key):
    return ROOT / f'work/stage21-{key}-prep/separated/UVR_Demucs_Model_1' / load(key)['source_acquisition_id']


def audio_row(path):
    import numpy as np
    import soundfile as sf
    wave, sr = sf.read(path, always_2d=True)
    assert sr == 44100 and np.isfinite(wave).all() and np.max(np.abs(wave)) > 1e-5
    return {'path': str(path.relative_to(ROOT)), 'sha256': hash_file(path),
            'duration': len(wave)/sr, 'sr': sr, 'channels': wave.shape[1]}


def prepare_source(key):
    wait_for_heavy()
    c = load(key)
    receipt_path = ROOT / 'work/acquisition' / c['source_acquisition_id'] / 'receipt.json'
    receipt = json.loads(receipt_path.read_text())
    assert receipt['status'] == 'PASS'
    raw = ROOT / receipt['output']['data_path']
    assert raw.stat().st_size == receipt['output']['size_bytes']
    assert hash_file(raw) == receipt['output']['sha256']
    for row in json.loads((ROOT/'config/separation-models.json').read_text()):
        p = ROOT / row['dest']
        assert p.stat().st_size == row['size_bytes'] and hash_file(p) == row['sha256']
    prep = ROOT / f'work/stage21-{key}-prep'
    assert not prep.exists(), 'Preparation exists; inspect evidence before retrying'
    info = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams',
        'a:0', '-show_entries', 'stream=channels,sample_rate', '-of', 'json', str(raw)]))['streams'][0]
    separation_input = raw
    if info['channels'] > 2:
        # Demucs otherwise keeps only the first two channels, discarding center vocals.
        prep.mkdir(exist_ok=False)
        separation_input = prep/f"{c['source_acquisition_id']}.wav"
        downmix = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-n',
                   '-i', raw, '-ar', '44100', '-ac', '2', '-c:a', 'pcm_f32le', separation_input]
        command(downmix)
        c['source_preprocessing'] = {'reason':'Explicit FFmpeg stereo downmix for multichannel source; preserve center channel contribution',
            'raw_channels':info['channels'], 'command':list(map(str,downmix)),
            'path':str(separation_input.relative_to(ROOT)), 'sha256':hash_file(separation_input)}
    logged(f'stage21-{key}-separate', [ROOT/'.envs/demucs/bin/python', '-m', 'demucs',
        '--repo', 'models/demucs-uvr', '-n', 'UVR_Demucs_Model_1', '--two-stems', 'vocals',
        '-d', 'mps', '--shifts', '1', '--overlap', '0.25', '--segment', '7', '--float32',
        '-j', '1', '-o', prep/'separated', separation_input])
    c['source_receipt'] = str(receipt_path.relative_to(ROOT))
    c['source_sha256'] = hash_file(raw)
    c['source_raw'] = str(raw.relative_to(ROOT))
    vocal = stems(key)/'vocals.wav'
    c['source_stems'] = [audio_row(vocal), audio_row(stems(key)/'no_vocals.wav')]
    c['status'] = 'SOURCE_SEPARATED'
    (ROOT / c['output_directory']).mkdir(parents=True, exist_ok=True)
    save(key, c)
    logged(f'stage21-{key}-asr', [ROOT/'.envs/seed-vc/bin/python', 'scripts/transcribe_local.py',
        '--input', vocal, '--run-id', f'stage21-{key}-asr',
        '--start', '0', '--duration', f"{c['source_stems'][0]['duration']:.3f}", '--device', 'mps'])


def clips(key, start, end):
    c = load(key)
    verify_roster(c)
    assert end > start >= 0
    c.update(source_start_seconds=start, source_end_seconds=end, duration_seconds=round(end-start, 6),
             chorus_evidence={'selected_interval_seconds': [start, end],
                 'transcript': f'work/stage21-{key}-asr/transcript.json',
                 'method': 'Offline Whisper phrase timestamps and vocal RMS boundaries; not human audition'})
    shared = ROOT / f'work/stage21-{key}-shared'
    shared.mkdir(exist_ok=False)
    commands = []
    for name, source, channels in [('source_vocals.wav', stems(key)/'vocals.wav', 1),
        ('source_accompaniment.wav', stems(key)/'no_vocals.wav', 2),
        ('source_original.wav', ROOT/c['source_raw'], 2)]:
        cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-n', '-ss', start,
               '-t', c['duration_seconds'], '-i', source, '-ar', '44100', '-ac', channels,
               '-c:a', 'pcm_s16le', shared/name]
        command(cmd)
        commands.append(list(map(str, cmd)))
    shared_rows = [audio_row(p) for p in sorted(shared.glob('*.wav'))]
    dump(shared/'manifest.json', {'files': shared_rows, 'commands': commands, **c['chorus_evidence']})
    dest = ROOT/c['output_directory']
    (dest/'inputs').mkdir(exist_ok=True)
    for row in shared_rows:
        p = ROOT/row['path']
        copy_checked(p, dest/'inputs'/p.name)
    for a in c['artists']:
        old = ROOT/a['reuse_reference_from']
        oldm = json.loads((old/'manifest.json').read_text())
        assert (oldm['target_artist'], oldm['target_song']) == (a['artist'], a['reference_song'])
        reference = old/'target_reference_1.wav'
        assert hash_file(reference) == a['reference_sha256']
        work = ROOT/a['clips']
        work.mkdir(exist_ok=False)
        copy_checked(reference, work/reference.name)
        for row in shared_rows:
            p = ROOT/row['path']
            copy_checked(p, work/p.name)
        m = {'source_interval_seconds': [start, end], 'source_full_vocals': str(stems(key)/'vocals.wav'),
             'source_full_accompaniment': str(stems(key)/'no_vocals.wav'),
             'source_artist': c['source_artist'], 'source_song': c['source_song'],
             'target_artist': a['artist'], 'target_song': a['reference_song'],
             'display_title': f"{a['artist']}音色 ·《{c['source_song']}》副歌",
             'original_mix_path': str(work/'source_original.wav'),
             'reference_note': f"参考人声：{a['artist']}《{a['reference_song']}》，沿用上轮同一15秒片段。",
             'references': oldm['references'][:1], 'reference_reuse': {'path': str(reference), 'byte_identical': True},
             'selection_basis': oldm['selection_basis'], 'cleanliness': 'PROVISIONAL_NOT_AUDITIONED',
             'other_artist_target_audio_used': False, 'chorus_evidence': c['chorus_evidence'],
             'files': [audio_row(p) for p in sorted(work.glob('*.wav'))]}
        dump(work/'manifest.json', m)
        a['status'] = 'PREPARED'
    c['status'] = 'PREPARED'
    save(key, c)
    report(key, c)


def smoke(key):
    wait_for_heavy()
    c = load(key)
    verify_roster(c)
    a = c['artists'][0]
    work = ROOT/'work/stage21-yigeren-smoke'
    work.mkdir(exist_ok=False)
    source = work/'source_vocals.wav'
    command(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-n',
             '-ss', '0', '-t', '4', '-i', ROOT/a['clips']/'source_vocals.wav',
             '-ar', '44100', '-ac', '1', '-c:a', 'pcm_s16le', source])
    out = ROOT/'outputs/stage21-yigeren-smoke'
    logged('stage21-yigeren-smoke', [ROOT/'.envs/seed-vc/bin/python',
        'scripts/seed_vc_local.py', '--source', source,
        '--target', ROOT/a['clips']/'target_reference_1.wav', '--run-id',
        'stage21-yigeren-smoke', '--output-dir', out, '--steps', '30', '--device', 'mps'], 600)
    r = json.loads((out/'run.json').read_text())
    row = audio_row(out/'seed-vc_AI.wav')
    assert r['requested_steps']==[30] and r['target_sha256']==a['reference_sha256']
    assert abs(row['duration']-4)<.02 and row['sha256']!=hash_file(source)
    dump(EVIDENCE/'smoke-validation.json', {'status':'PASSED', 'audio':row,
        'run':'outputs/stage21-yigeren-smoke/run.json', 'human_audition':False,
        'note':'Technical short smoke only; full chorus delivery still required'})


def report(key, c):
    rows = [f"# 七人《{c['source_song']}》副歌实验", '',
        f"日期：2026-10-19；技术状态：{c['status']}；人工听感：待用户试听。", '',
        '参考阵容固定于config/default-roster.json。原唱林凡不在四大三小七人内，本轮七人全部参与，复制完整配置快照，逐份核验15秒参考SHA256。',
        f"源：{c['source_artist']}《{c['source_song']}》；[公开来源]({c['source_url']})。",
        f"原素材区间：{c.get('source_start_seconds')} 秒起，时长 {c.get('duration_seconds')} 秒。离线ASR与人声能量辅助定位，非人工听音或歌词真值。", '',
        'Seed-VC V1 commit `51383efd921027683c89e5348211d93ff12ac2a8`，2026-10-19复核本地锁定README。',
        '30步单版，F0=true，autoF0=false，0半音，CFG0.7，FP32，seed20261016。',
        'MPS扩散/Whisper/音色编码器，CPU BigVGAN/RMVPE/频谱；沿用已审计环境及权重，重模型串行离线执行。',
        '分离：UVR_Demucs_Model_1，MPS，two-stems vocals，shifts1，overlap0.25，segment7，float32。',
        '七个参考均复用旧片段，不重新分离/挑片；每首参考素材不足10分钟，本轮零样本15秒参考，不训练。未额外去混响/和声，自动筛选不能证明纯净。', '',
        '| 歌手 | 参考歌 | 原参考区间/s | 状态 | 推理/s | 音色余弦 | F0相关 | 共同有声覆盖率 | MPS分配/驱动峰值GiB |',
        '|---|---|---|---|---:|---:|---:|---:|---|']
    for a in c['artists']:
        m=a.get('metrics',{})
        rows.append('| '+' | '.join(map(str,[a['artist'],a['reference_song'],a['reference_interval_seconds'],a['status'],
            m.get('inference_seconds','N/A'),m.get('speaker_cosine','N/A'),m.get('f0_pearson','N/A'),m.get('common_voiced_coverage','N/A'),
            str(m.get('mps_allocated_peak_gib','N/A'))+' / '+str(m.get('mps_driver_peak_gib','N/A'))]))+' |')
    rows += ['',f"成品目录：`{c['output_directory']}/`；每人混音和纯人声，listen.html支持同进度切换和参考返回。",
        '混音沿用源人声RMS匹配（增益0.5–2），母带峰值上限0.98；非LUFS统一响度。',
        'CAMPPlus同时用于生成条件，因此相似度并非独立身份准确率；F0仅共同有声帧，CER=N/A（无独立校对歌词）。',
        '没有人工听感验收；不声称本人演唱，不虚构咬字或高音主观评价。统一内存分配与驱动峰值不能相加，也不是独立显存。', '',
        '## 复现', '', '```sh',
        '.envs/demucs/bin/python scripts/run_yigeren_experiment.py prepare-source --song yigeren',
        f".envs/demucs/bin/python scripts/run_yigeren_experiment.py clips --song yigeren --start {c.get('source_start_seconds')} --end {round((c.get('source_start_seconds') or 0)+(c.get('duration_seconds') or 0),6)}",
        'python3 scripts/run_yigeren_experiment.py generate --song yigeren',
        '.envs/demucs/bin/python scripts/run_yigeren_experiment.py validate', '```', '',
        '准备目录拒绝覆盖；成功生成会校验哈希后跳过。各run保存完整命令/参数/哈希/进度；日志logs/stage21-*，证据reports/evidence/stage21/，下载台账reports/downloads.md。']
    if 'batch_elapsed_seconds' in c:rows+=['',f"生成与评测批次耗时：{c['batch_elapsed_seconds']:.3f}秒。"]
    (ROOT/'reports/28_yigeren.md').write_text('\n'.join(rows)+'\n')


def verify_roster(c):
    p=ROOT/c['roster_config']
    assert hash_file(p)==c['roster_config_sha256'], 'Global roster changed: explicitly review before generation'
    roster=json.loads(p.read_text())
    assert c['steps']==roster['steps']==[30] and c['roster_id']==roster['id']
    defaults=list(roster['artists'])
    assert len(defaults)==ARTIST_COUNT
    assert [a['key'] for a in c['artists']]==[a['key'] for a in defaults]==c['authorization']['authorized_artist_keys']
    assert c['authorization'].get('excluded_original_artist') is None
    assert (c['source_artist'],c['source_song'])==('林凡','一个人生活')
    assert hash_file(ROOT/c['roster_snapshot'])==c['roster_config_sha256']
    for a,default in zip(c['artists'],defaults):
        for field in ('artist','reference_song','reuse_reference_from','reference_sha256','reference_interval_seconds'):
            assert a[field]==default[field], 'Reference differs from fixed roster'
        assert hash_file(ROOT/a['reuse_reference_from']/'target_reference_1.wav')==a['reference_sha256']
        m=json.loads((ROOT/a['reuse_reference_from']/'manifest.json').read_text())
        assert (m['target_artist'],m['target_song'])==(a['artist'],a['reference_song'])
        assert m['references'][0]['original_interval_seconds']==a['reference_interval_seconds']
        assert m['references'][0]['duration']==15 and m['references'][0]['sha256']==a['reference_sha256']


def generate(key):
    wait_for_heavy()
    c = load(key)
    verify_roster(c)
    dest = ROOT/c['output_directory']
    if c['status'] == 'POC_PASSED':
        for a in c['artists']:
            assert a['status'] == 'POC_PASSED'
            for row in a['deliverables'].values():
                p = ROOT/row['path']
                assert hash_file(p) == row['sha256'] and p.stat().st_size == row['size_bytes']
        print('ALREADY_PASSED; verified files, preserving original timing and evidence', flush=True)
        return
    started = time.monotonic()
    assert json.loads((EVIDENCE/'smoke-validation.json').read_text())['status']=='PASSED'
    c.update(status='RUNNING', started_at=dt.datetime.now(dt.timezone.utc).isoformat())
    save(key,c)
    for a in c['artists']:
        if a['status'] == 'POC_PASSED':
            for row in a['deliverables'].values(): assert hash_file(ROOT/row['path']) == row['sha256']
            continue
        try:
            a['status']='RUNNING'
            save(key,c)
            out = dest/'runs'/a['key']
            with (ROOT/'logs'/f"{a['run_id']}-launch.log").open('x') as log:
                subprocess.run(['python3','scripts/run_stage2_poc.py','--run-id',a['run_id'],
                    '--clips',a['clips'],'--output-dir',str(out),'--evidence-dir',str(EVIDENCE),
                    '--device','mps','--steps','30'],cwd=ROOT,env=local_env(),stdout=log,stderr=subprocess.STDOUT,check=True)
            command([ROOT/'.envs/demucs/bin/python','scripts/validate_full_song.py','--run',out/'run.json',
                '--duration',c['duration_seconds'],'--evidence',EVIDENCE/f"{key}-{a['key']}-validation.json"])
            r=json.loads((out/'run.json').read_text());e=json.loads((out/'evaluation.json').read_text())
            assert r['requested_steps']==[30] and r['target_sha256']==a['reference_sha256']
            assert r['seed']==c['seed'] and 'source_f0_repair' not in r
            variant=r['variants'][0]
            assert (variant['f0_condition'],variant['auto_f0_adjust'],variant['semitones'],variant['cfg_rate'],variant['fp16'])==(True,False,0,.7,False)
            assert r['source_sha256']==hash_file(ROOT/a['clips']/'source_vocals.wav')
            a['deliverables']={}
            for mode,source,name in [('dry',out/'seed-vc_AI.wav',f"{a['artist']}_{c['source_song']}_AI.wav"),
                ('mix',out/'seed-vc_mix_AI.wav',f"{a['artist']}_{c['source_song']}_mix_AI.wav"),
                ('reference',ROOT/a['clips']/'target_reference_1.wav',f"inputs/{a['artist']}_参考_{a['reference_song']}.wav")]:
                a['deliverables'][mode]=copy_checked(source,dest/name)
            m=e['variants'][0]
            a['metrics']={'inference_seconds':round(r['elapsed_seconds'],3),'speaker_cosine':m['speaker_cosine_target'],
                'f0_pearson':m['f0_pearson'],'common_voiced_coverage':m['common_voiced_coverage'],
                'mps_allocated_peak_gib':r['sampled_mps_allocated_peak_bytes']/2**30,
                'mps_driver_peak_gib':r['sampled_mps_driver_peak_bytes']/2**30,'CER':None}
            a.update(status='POC_PASSED',human_audition=False)
        except Exception as exc:
            a.update(status='FAILED',error=f'{type(exc).__name__}: {exc}')
            print(a['error'],flush=True)
        save(key,c);page(c);report(key,c)
        print('ARTIST_COMPLETED',c['source_song'],a['artist'],a['status'],flush=True)
    c.update(status='POC_PASSED' if all(a['status']=='POC_PASSED' for a in c['artists']) else 'PARTIAL',
             completed_at=dt.datetime.now(dt.timezone.utc).isoformat(),batch_elapsed_seconds=time.monotonic()-started)
    save(key,c);page(c);report(key,c)


def validate():
    import numpy as np
    import soundfile as sf
    old=json.loads((EVIDENCE/'protected-before.json').read_text())
    relocation_path=EVIDENCE/'protected-relocations.json'
    relocations={}
    if relocation_path.exists():
        relocation=json.loads(relocation_path.read_text())
        assert relocation['status']=='PASSED'
        assert hash_file(ROOT/relocation['source_evidence'])==relocation['source_evidence_sha256']
        relocations=relocation['files']
    relocated=0
    for row in old:
        p=ROOT/row['path']
        if not p.exists() and row['path'] in relocations:
            moved=relocations[row['path']]
            assert moved['sha256']==row['sha256'] and moved['size_bytes']==row['size']
            p=(ROOT/moved['path']).resolve()
            assert p.is_relative_to(ROOT/'outputs')
            relocated+=1
        assert p.stat().st_size==row['size'] and hash_file(p)==row['sha256'],'Protected file changed'
    execution=json.loads((EVIDENCE/'execution-scripts.json').read_text())
    for row in execution['files']:
        p=ROOT/row['path']
        assert p.stat().st_size==row['size_bytes'] and hash_file(p)==row['sha256'], 'Execution wrapper changed during experiment'
    results=[];sources=set();references={};dry_hashes=set();players={}
    expected_tracks=ARTIST_COUNT*3+2
    expected_wavs=ARTIST_COUNT*2
    for key in KEYS:
        c=load(key);dest=ROOT/c['output_directory']
        assert c['status']=='POC_PASSED' and json.loads((dest/'manifest.json').read_text())==c
        verify_roster(c)
        assert {p.name for p in (dest/'runs').iterdir()}=={a['key'] for a in c['artists']}
        assert len(list(dest.glob('*_AI.wav')))==expected_wavs
        receipt=json.loads((ROOT/c['source_receipt']).read_text())
        assert hash_file(ROOT/c['source_raw'])==c['source_sha256']==receipt['output']['sha256']
        song_sources=set()
        for a in c['artists']:
            run=json.loads((dest/'runs'/a['key']/'run.json').read_text())
            prepared=json.loads((ROOT/a['clips']/'manifest.json').read_text())
            assert (prepared['target_artist'],prepared['target_song'],prepared['source_song'])==(a['artist'],a['reference_song'],c['source_song'])
            assert run['requested_steps']==[30] and len(run['variants'])==1 and run['target_sha256']==a['reference_sha256']
            assert run['seed']==c['seed'] and 'source_f0_repair' not in run
            variant=run['variants'][0]
            assert (variant['f0_condition'],variant['auto_f0_adjust'],variant['semitones'],variant['cfg_rate'],variant['fp16'])==(True,False,0,.7,False)
            assert run['source_sha256']==hash_file(ROOT/a['clips']/'source_vocals.wav')
            evaluation=json.loads((dest/'runs'/a['key']/'evaluation.json').read_text())
            song_sources.add(run['source_sha256'])
            references.setdefault(a['key'],set()).add(run['target_sha256'])
            for mode,row in a['deliverables'].items():
                p=ROOT/row['path'];assert hash_file(p)==row['sha256'] and p.stat().st_size==row['size_bytes']
                w,sr=sf.read(p,always_2d=True);assert sr==44100 and np.isfinite(w).all() and np.max(np.abs(w))>1e-5
                expected=15 if mode=='reference' else c['duration_seconds']
                assert abs(len(w)-round(sr*expected))<=(512 if mode=='dry' else 0)
                assert w.shape[1]==(2 if mode=='mix' else 1)
                if mode=='mix':
                    assert np.max(np.abs(w))<=.981 and row['sha256']==evaluation['variants'][0]['mix_sha256']
                if mode=='dry':
                    assert row['sha256']==run['variants'][0]['sha256']!=run['source_sha256']
                    dry_hashes.add(row['sha256'])
                results.append({'song':c['source_song'],'artist':a['artist'],'mode':mode,**row,
                    'duration':len(w)/sr,'peak':float(np.max(np.abs(w))),'near_full_scale_fraction':float(np.mean(np.abs(w)>=.999))})
        assert len(song_sources)==1
        sources.update(song_sources)
        document=(dest/'listen.html').read_text()
        tracks=json.loads(re.search(r'const tracks=(\[.*?\]);',document).group(1))
        assert len(tracks)==expected_tracks and len({t['url'] for t in tracks})==expected_tracks and c['source_song'] in document and 'A/B' not in document
        assert 'http://' not in document and 'https://' not in document
        for t in tracks:
            p=(dest/t['url']).resolve();assert p.is_relative_to(dest) and p.is_file()
        checked=subprocess.run(['node','scripts/check_group_player.cjs',str(dest/'listen.html')],
                               check=True,capture_output=True,text=True,env=local_env())
        players[key]=json.loads(checked.stdout)
        for a in c['artists']:
            assert json.loads((EVIDENCE/f"{key}-{a['key']}-validation.json").read_text())['status']=='PASSED'
    assert len(sources)==1 and len(dry_hashes)==ARTIST_COUNT and len(references)==ARTIST_COUNT and all(len(v)==1 for v in references.values())
    assert len({next(iter(v)) for v in references.values()})==ARTIST_COUNT
    result={'status':'PASSED','checked_at':dt.datetime.now(dt.timezone.utc).isoformat(),
        'audio':results,'protected_files_unchanged':len(old),'distinct_sources':1,'distinct_conversions':ARTIST_COUNT,'final_audio_files':expected_wavs,
        'protected_files_relocated':relocated,'protected_files_at_original_paths':len(old)-relocated,
        'fixed_roster_references_verified':True,'human_audition':False,'players':players,
        'execution_wrappers_verified':len(execution['files']),
        'execution_wrappers_unchanged':len(execution['files'])-len({r['path'] for r in execution.get('post_generation_validation_revisions',[])}),
        'post_generation_wrapper_revisions':execution.get('post_generation_validation_revisions',[]),'f0_repair_used':False,
        'space_bytes':{n:sum(p.stat().st_size for p in (ROOT/n).rglob('*') if p.is_file()) for n in ['work','outputs']},
        'disk_free_bytes':shutil.disk_usage(ROOT).free,
        'download_budget':{'charged':charged(records()),'reserved':sum(reservations().values())}}
    with (EVIDENCE/'final-validation.json').open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['prepare-source','clips','smoke','generate','validate'])
    p.add_argument('--song',choices=KEYS);p.add_argument('--start',type=float);p.add_argument('--end',type=float)
    a=p.parse_args()
    if a.action=='validate':validate()
    else:
        if a.song is None:p.error('--song required')
        if a.action=='prepare-source':prepare_source(a.song)
        elif a.action=='smoke':smoke(a.song)
        elif a.action=='clips':
            if a.start is None or a.end is None:p.error('--start and --end required')
            clips(a.song,a.start,a.end)
        else:generate(a.song)
