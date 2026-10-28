#!/usr/bin/env python3
"""Stage10: prepare and generate only Angela/Elva; other singers require user feedback."""
import argparse
import datetime as dt
import json
from pathlib import Path
import re
import shutil
import subprocess
import time

from common import ROOT, local_env
from download import hash_file, records, charged, reservations
from run_seven_experiment import copy_checked, dump, page

EVIDENCE = ROOT / 'reports/evidence/stage10'
KEYS = ('xinqiang', 'xiaoxingyun')


def config_path(key):
    return ROOT / f'config/experiments/stage10-{key}.json'


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
    return ROOT / f'work/stage10-{key}-prep/separated/UVR_Demucs_Model_1' / load(key)['source_acquisition_id']


def audio_row(path):
    import numpy as np
    import soundfile as sf
    wave, sr = sf.read(path, always_2d=True)
    assert sr == 44100 and np.isfinite(wave).all() and np.max(np.abs(wave)) > 1e-5
    return {'path': str(path.relative_to(ROOT)), 'sha256': hash_file(path),
            'duration': len(wave)/sr, 'sr': sr, 'channels': wave.shape[1]}


def prepare_source(key):
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
    prep = ROOT / f'work/stage10-{key}-prep'
    assert not prep.exists(), 'Preparation exists; inspect evidence before retrying'
    logged(f'stage10-{key}-separate', [ROOT/'.envs/demucs/bin/python', '-m', 'demucs',
        '--repo', 'models/demucs-uvr', '-n', 'UVR_Demucs_Model_1', '--two-stems', 'vocals',
        '-d', 'mps', '--shifts', '1', '--overlap', '0.25', '--segment', '7', '--float32',
        '-j', '1', '-o', prep/'separated', raw])
    c['source_receipt'] = str(receipt_path.relative_to(ROOT))
    c['source_sha256'] = hash_file(raw)
    c['source_raw'] = str(raw.relative_to(ROOT))
    c['source_stems'] = [audio_row(stems(key)/n) for n in ('vocals.wav', 'no_vocals.wav')]
    c['status'] = 'SOURCE_SEPARATED'
    save(key, c)
    logged(f'stage10-{key}-asr', [ROOT/'.envs/seed-vc/bin/python', 'scripts/transcribe_local.py',
        '--input', stems(key)/'vocals.wav', '--run-id', f'stage10-{key}-asr',
        '--start', '35', '--duration', '145', '--device', 'mps'])


def clips(key, start, end):
    c = load(key)
    assert end > start >= 0
    c.update(source_start_seconds=start, duration_seconds=round(end-start, 6),
             chorus_evidence={'selected_interval_seconds': [start, end],
                 'transcript': f'work/stage10-{key}-asr/transcript.json',
                 'method': 'Offline Whisper phrase timestamps and vocal RMS boundaries; not human audition'})
    shared = ROOT / f'work/stage10-{key}-shared'
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


def report(key, c):
    rows = [f"# 《{c['source_song']}》两人先行试听", '',
        f"日期：2026-10-18；技术状态：{c['status']}；人工试听：待用户反馈。", '',
        '本轮仅生成张韶涵、萧亚轩。其余五位明确等待用户试听认可，不自动启动。',
        f"源版本：{c['source_artist']}；[来源页面]({c['source_url']})。",
        f"源区间：{c.get('source_start_seconds')} 秒起，时长 {c.get('duration_seconds')} 秒。副歌由离线 ASR 和人声能量边界辅助定位，非人工歌词验收。", '',
        'Seed-VC V1，commit `51383efd921027683c89e5348211d93ff12ac2a8`；2026-10-18复核本地锁定 README 的歌声参数。',
        '30步单版、F0开启、自动F0调整关闭、0半音、CFG 0.7、FP32、种子20261016。',
        '复用已审计本地环境/权重；MPS扩散与编码器，CPU BigVGAN/RMVPE；串行本地运行，无音频上传。',
        '人声分离：UVR_Demucs_Model_1，two-stems vocals，MPS，shifts=1，overlap=0.25，segment=7，float32。',
        '两个参考片段均复用上一轮原字节，各15秒；参考素材不足10分钟，本轮零样本转换，不训练歌手模型。未额外去混响/和声，纯净度仍待试听。', '',
        '| 歌手 | 参考歌曲及原始区间/s | 状态 | 推理秒 | 音色余弦 | F0相关 | 有声覆盖 | MPS分配/驱动峰值GiB |',
        '|---|---|---|---:|---:|---:|---:|---|']
    for a in c['artists']:
        m = a.get('metrics', {})
        rows.append('| '+' | '.join(map(str, [a['artist'], a['reference_song']+' '+str(a['reference_interval_seconds']), a['status'],
            m.get('inference_seconds','N/A'),m.get('speaker_cosine','N/A'),m.get('f0_pearson','N/A'),m.get('common_voiced_coverage','N/A'),
            str(m.get('mps_allocated_peak_gib','N/A'))+' / '+str(m.get('mps_driver_peak_gib','N/A'))]))+' |')
    rows += ['', f"成品：`{c['output_directory']}/`；根目录每人混音和纯人声，`listen.html`支持同进度切换。",
        'CAMPPlus同时作为生成条件和评测，余弦不是独立身份准确率；F0仅统计共同有声帧。CER=N/A：缺独立核对歌词。',
        '混音沿用源人声RMS匹配（增益0.5–2），母带峰值上限0.98；不是LUFS统一响度。不声称已听过或已获用户认可。',
        '统一内存的分配与驱动峰值不能相加，也不等于独立显存。', '', '## 复现', '', '```sh',
        f'.envs/demucs/bin/python scripts/run_two_song_experiment.py prepare-source --song {key}',
        f'.envs/demucs/bin/python scripts/run_two_song_experiment.py clips --song {key} --start {c.get("source_start_seconds")} --end {round((c.get("source_start_seconds") or 0)+(c.get("duration_seconds") or 0),6)}',
        f'python3 scripts/run_two_song_experiment.py generate --song {key}',
        '.envs/demucs/bin/python scripts/run_two_song_experiment.py validate', '```', '',
        '现有准备目录拒绝覆盖；已成功成员生成时校验哈希后跳过，失败目录保留供诊断；真正重跑需新run-id/路径。',
        '具体调用、时间和资源证据：`reports/evidence/stage10/`；日志：`logs/stage10-*`。下载与许可证见 `reports/downloads.md`；许可证unknown，不新增权重或依赖。']
    if 'batch_elapsed_seconds' in c: rows += ['',f"生成与评测批次耗时：{c['batch_elapsed_seconds']:.3f} 秒。"]
    (ROOT/f'reports/17_{key}.md').write_text('\n'.join(rows)+'\n')


def generate(key):
    c = load(key)
    assert c['steps'] == [30] and [a['key'] for a in c['artists']] == ['angela','elva']
    assert c['remaining_artists']['authorized_to_generate'] is False
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
    for row in old:
        p=ROOT/row['path']
        assert p.stat().st_size==row['size'] and hash_file(p)==row['sha256'],'Protected file changed'
    results=[];sources=set();references={};dry_hashes=set();players={}
    for key in KEYS:
        c=load(key);dest=ROOT/c['output_directory']
        assert c['status']=='POC_PASSED' and json.loads((dest/'manifest.json').read_text())==c
        assert [a['key'] for a in c['artists']]==['angela','elva']
        assert {p.name for p in (dest/'runs').iterdir()}=={'angela','elva'}
        assert len(list(dest.glob('*_AI.wav')))==4
        assert c['remaining_artists']['authorized_to_generate'] is False
        receipt=json.loads((ROOT/c['source_receipt']).read_text())
        assert hash_file(ROOT/c['source_raw'])==c['source_sha256']==receipt['output']['sha256']
        song_sources=set()
        for a in c['artists']:
            run=json.loads((dest/'runs'/a['key']/'run.json').read_text())
            prepared=json.loads((ROOT/a['clips']/'manifest.json').read_text())
            assert (prepared['target_artist'],prepared['target_song'],prepared['source_song'])==(a['artist'],a['reference_song'],c['source_song'])
            assert run['requested_steps']==[30] and run['target_sha256']==a['reference_sha256']
            song_sources.add(run['source_sha256'])
            references.setdefault(a['key'],set()).add(run['target_sha256'])
            for mode,row in a['deliverables'].items():
                p=ROOT/row['path'];assert hash_file(p)==row['sha256'] and p.stat().st_size==row['size_bytes']
                w,sr=sf.read(p,always_2d=True);assert sr==44100 and np.isfinite(w).all() and np.max(np.abs(w))>1e-5
                expected=15 if mode=='reference' else c['duration_seconds']
                assert abs(len(w)-round(sr*expected))<=(512 if mode=='dry' else 0)
                assert w.shape[1]==(2 if mode=='mix' else 1)
                if mode=='mix':assert np.max(np.abs(w))<=.981
                if mode=='dry':dry_hashes.add(row['sha256'])
                results.append({'song':c['source_song'],'artist':a['artist'],'mode':mode,**row,
                    'duration':len(w)/sr,'peak':float(np.max(np.abs(w))),'near_full_scale_fraction':float(np.mean(np.abs(w)>=.999))})
        assert len(song_sources)==1
        sources.update(song_sources)
        document=(dest/'listen.html').read_text()
        tracks=json.loads(re.search(r'const tracks=(\[.*?\]);',document).group(1))
        assert len(tracks)==8 and c['source_song'] in document and 'A/B' not in document
        assert 'http://' not in document and 'https://' not in document
        for t in tracks:
            p=(dest/t['url']).resolve();assert p.is_relative_to(dest) and p.is_file()
        checked=subprocess.run(['node','scripts/check_group_player.cjs',str(dest/'listen.html')],
                               check=True,capture_output=True,text=True,env=local_env())
        players[key]=json.loads(checked.stdout)
        assert json.loads((EVIDENCE/f'{key}-angela-validation.json').read_text())['status']=='PASSED'
        assert json.loads((EVIDENCE/f'{key}-elva-validation.json').read_text())['status']=='PASSED'
    assert len(sources)==2 and len(dry_hashes)==4 and all(len(v)==1 for v in references.values())
    result={'status':'PASSED','checked_at':dt.datetime.now(dt.timezone.utc).isoformat(),
        'audio':results,'protected_files_unchanged':len(old),'distinct_sources':2,'distinct_conversions':4,
        'same_references_across_songs':True,'remaining_five_generated':False,'human_audition':False,'players':players,
        'space_bytes':{n:sum(p.stat().st_size for p in (ROOT/n).rglob('*') if p.is_file()) for n in ['work','outputs']},
        'disk_free_bytes':shutil.disk_usage(ROOT).free,
        'download_budget':{'charged':charged(records()),'reserved':sum(reservations().values())}}
    with (EVIDENCE/'final-validation.json').open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['prepare-source','clips','generate','validate'])
    p.add_argument('--song',choices=KEYS);p.add_argument('--start',type=float);p.add_argument('--end',type=float)
    a=p.parse_args()
    if a.action=='validate':validate()
    else:
        if a.song is None:p.error('--song required')
        if a.action=='prepare-source':prepare_source(a.song)
        elif a.action=='clips':
            if a.start is None or a.end is None:p.error('--start and --end required')
            clips(a.song,a.start,a.end)
        else:generate(a.song)
