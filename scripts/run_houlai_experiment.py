#!/usr/bin/env python3
"""Stage12: seven fixed references singing Hou Lai, preserving historical experiments."""
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

EVIDENCE = ROOT / 'reports/evidence/stage12'
KEYS = ('houlai',)


def config_path(key):
    return ROOT / f'config/experiments/stage12-{key}.json'


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
    return ROOT / f'work/stage12-{key}-prep/separated/UVR_Demucs_Model_1' / load(key)['source_acquisition_id']


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
    prep = ROOT / f'work/stage12-{key}-prep'
    assert not prep.exists(), 'Preparation exists; inspect evidence before retrying'
    logged(f'stage12-{key}-separate', [ROOT/'.envs/demucs/bin/python', '-m', 'demucs',
        '--repo', 'models/demucs-uvr', '-n', 'UVR_Demucs_Model_1', '--two-stems', 'vocals',
        '-d', 'mps', '--shifts', '1', '--overlap', '0.25', '--segment', '7', '--float32',
        '-j', '1', '-o', prep/'separated', raw])
    c['source_receipt'] = str(receipt_path.relative_to(ROOT))
    c['source_sha256'] = hash_file(raw)
    c['source_raw'] = str(raw.relative_to(ROOT))
    c['source_stems'] = [audio_row(stems(key)/n) for n in ('vocals.wav', 'no_vocals.wav')]
    c['status'] = 'SOURCE_SEPARATED'
    save(key, c)
    logged(f'stage12-{key}-asr', [ROOT/'.envs/seed-vc/bin/python', 'scripts/transcribe_local.py',
        '--input', stems(key)/'vocals.wav', '--run-id', f'stage12-{key}-asr',
        '--start', '0', '--duration', '210', '--device', 'mps'])


def clips(key, start, end):
    c = load(key)
    verify_roster(c)
    assert end > start >= 0
    c.update(source_start_seconds=start, duration_seconds=round(end-start, 6),
             chorus_evidence={'selected_interval_seconds': [start, end],
                 'transcript': f'work/stage12-{key}-asr/transcript.json',
                 'method': 'Offline Whisper phrase timestamps and vocal RMS boundaries; not human audition'})
    shared = ROOT / f'work/stage12-{key}-shared'
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
    rows = [f"# 七人《{c['source_song']}》副歌实验", '',
        f"日期：2026-10-18；技术状态：{c['status']}；人工听感：待用户试听。", '',
        '参考阵容固定于config/default-roster.json；本轮复制配置快照，逐份核验15秒参考SHA256。',
        f"源：{c['source_artist']}《{c['source_song']}》；[公开来源]({c['source_url']})。",
        f"原素材区间：{c.get('source_start_seconds')} 秒起，时长 {c.get('duration_seconds')} 秒。离线ASR与人声能量辅助定位，非人工听音或歌词真值。", '',
        'Seed-VC V1 commit `51383efd921027683c89e5348211d93ff12ac2a8`，2026-10-18复核本地锁定README。',
        '30步单版，F0=true，autoF0=false，0半音，CFG0.7，FP32，seed20261016。',
        'MPS扩散/Whisper/音色编码器，CPU BigVGAN/RMVPE/频谱；沿用已审计环境及权重，重模型串行离线执行。',
        '分离：UVR_Demucs_Model_1，MPS，two-stems vocals，shifts1，overlap0.25，segment7，float32。',
        '七个参考均复用旧片段，不重新分离/挑片；一首参考素材不足10分钟，本轮零样本15秒参考，不训练。未额外去混响/和声，自动筛选不能证明纯净。', '',
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
        '.envs/demucs/bin/python scripts/run_houlai_experiment.py prepare-source --song houlai',
        f".envs/demucs/bin/python scripts/run_houlai_experiment.py clips --song houlai --start {c.get('source_start_seconds')} --end {round((c.get('source_start_seconds') or 0)+(c.get('duration_seconds') or 0),6)}",
        'python3 scripts/run_houlai_experiment.py generate --song houlai',
        '.envs/demucs/bin/python scripts/run_houlai_experiment.py validate', '```', '',
        '准备目录拒绝覆盖；成功生成会校验哈希后跳过。各run保存完整命令/参数/哈希/进度；日志logs/stage12-*，证据reports/evidence/stage12/，下载台账reports/downloads.md。']
    if 'batch_elapsed_seconds' in c:rows+=['',f"生成与评测批次耗时：{c['batch_elapsed_seconds']:.3f}秒。"]
    (ROOT/'reports/19_houlai.md').write_text('\n'.join(rows)+'\n')


def verify_roster(c):
    p=ROOT/c['roster_config']
    assert hash_file(p)==c['roster_config_sha256'], 'Global roster changed: explicitly review before generation'
    roster=json.loads(p.read_text())
    assert c['steps']==roster['steps']==[30] and c['roster_id']==roster['id']
    assert [a['key'] for a in c['artists']]==[a['key'] for a in roster['artists']]
    for a,default in zip(c['artists'],roster['artists']):
        for field in ('artist','reference_song','reuse_reference_from','reference_sha256','reference_interval_seconds'):
            assert a[field]==default[field], 'Reference differs from fixed roster'
        assert hash_file(ROOT/a['reuse_reference_from']/'target_reference_1.wav')==a['reference_sha256']


def generate(key):
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
    for row in old:
        p=ROOT/row['path']
        assert p.stat().st_size==row['size'] and hash_file(p)==row['sha256'],'Protected file changed'
    results=[];sources=set();references={};dry_hashes=set();players={}
    for key in KEYS:
        c=load(key);dest=ROOT/c['output_directory']
        assert c['status']=='POC_PASSED' and json.loads((dest/'manifest.json').read_text())==c
        verify_roster(c)
        assert {p.name for p in (dest/'runs').iterdir()}=={a['key'] for a in c['artists']}
        assert len(list(dest.glob('*_AI.wav')))==14
        receipt=json.loads((ROOT/c['source_receipt']).read_text())
        assert hash_file(ROOT/c['source_raw'])==c['source_sha256']==receipt['output']['sha256']
        song_sources=set()
        for a in c['artists']:
            run=json.loads((dest/'runs'/a['key']/'run.json').read_text())
            prepared=json.loads((ROOT/a['clips']/'manifest.json').read_text())
            assert (prepared['target_artist'],prepared['target_song'],prepared['source_song'])==(a['artist'],a['reference_song'],c['source_song'])
            assert run['requested_steps']==[30] and len(run['variants'])==1 and run['target_sha256']==a['reference_sha256']
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
        assert len(tracks)==23 and len({t['url'] for t in tracks})==23 and c['source_song'] in document and 'A/B' not in document
        assert 'http://' not in document and 'https://' not in document
        for t in tracks:
            p=(dest/t['url']).resolve();assert p.is_relative_to(dest) and p.is_file()
        checked=subprocess.run(['node','scripts/check_group_player.cjs',str(dest/'listen.html')],
                               check=True,capture_output=True,text=True,env=local_env())
        players[key]=json.loads(checked.stdout)
        for a in c['artists']:
            assert json.loads((EVIDENCE/f"{key}-{a['key']}-validation.json").read_text())['status']=='PASSED'
    assert len(sources)==1 and len(dry_hashes)==7 and len(references)==7 and all(len(v)==1 for v in references.values())
    assert len({next(iter(v)) for v in references.values()})==7
    result={'status':'PASSED','checked_at':dt.datetime.now(dt.timezone.utc).isoformat(),
        'audio':results,'protected_files_unchanged':len(old),'distinct_sources':1,'distinct_conversions':7,'final_audio_files':14,
        'fixed_roster_references_verified':True,'human_audition':False,'players':players,
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
