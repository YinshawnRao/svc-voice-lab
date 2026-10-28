#!/usr/bin/env python3
"""Stage15: add four authorized singers while preserving the approved two-singer pilot."""
import argparse
import datetime as dt
import json
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import time

from common import ROOT, local_env
from download import hash_file, records, charged, reservations
from run_seven_experiment import copy_checked, dump, page

EVIDENCE = ROOT / 'reports/evidence/stage15'
NEW = ('stefanie','jolin','fish','rainie')
EXPECTED = ('stefanie','jolin','elva','fish','rainie','cyndi')
KEYS = ('shouxin',)


def config_path(key):
    return ROOT / f'config/experiments/stage15-{key}.json'


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
    return ROOT / f'work/stage14-{key}-prep/separated/UVR_Demucs_Model_1' / load(key)['source_acquisition_id']


def audio_row(path):
    import numpy as np
    import soundfile as sf
    wave, sr = sf.read(path, always_2d=True)
    assert sr == 44100 and np.isfinite(wave).all() and np.max(np.abs(wave)) > 1e-5
    return {'path': str(path.relative_to(ROOT)), 'sha256': hash_file(path),
            'duration': len(wave)/sr, 'sr': sr, 'channels': wave.shape[1]}


def prepare(key):
    c=load(key);verify_roster(c)
    shared=ROOT/c['shared_clips'];sharedm=json.loads((shared/'manifest.json').read_text())
    dest=ROOT/c['output_directory']
    for row in sharedm['files']:
        source=ROOT/row['path']
        assert hash_file(source)==row['sha256']==hash_file(dest/'inputs'/source.name)
    for a in c['artists']:
        if a['generation_stage']=='stage14':continue
        old=ROOT/a['reuse_reference_from'];oldm=json.loads((old/'manifest.json').read_text())
        work=ROOT/a['clips'];work.mkdir(exist_ok=False)
        copy_checked(old/'target_reference_1.wav',work/'target_reference_1.wav')
        for row in sharedm['files']:
            source=ROOT/row['path'];copy_checked(source,work/source.name)
        m={'source_interval_seconds':c['chorus_evidence']['selected_interval_seconds'],
           'source_artist':c['source_artist'],'source_song':c['source_song'],
           'target_artist':a['artist'],'target_song':a['reference_song'],
           'display_title':f"{a['artist']}音色 ·《{c['source_song']}》副歌",
           'original_mix_path':str(work/'source_original.wav'),
           'reference_note':f"参考人声：{a['artist']}《{a['reference_song']}》，沿用固定15秒片段。",
           'references':oldm['references'][:1],'reference_reuse':{'path':str(old/'target_reference_1.wav'),'byte_identical':True},
           'selection_basis':oldm['selection_basis'],'cleanliness':'PROVISIONAL_NOT_AUDITIONED',
           'other_artist_target_audio_used':False,'chorus_evidence':c['chorus_evidence'],
           'source_reuse':{'path':c['shared_clips'],'byte_identical':True},
           'files':[audio_row(p) for p in sorted(work.glob('*.wav'))]}
        dump(work/'manifest.json',m);a['status']='PREPARED'
    c['status']='PREPARED_EXTENSION';save(key,c);page(c);report(key,c)


def report(key, c):
    rows = [f"# 六位歌手《{c['source_song']}》副歌补齐实验", '',
        f"日期：2026-10-18；技术状态：{c['status']}；人工听感：前轮萧亚轩、王心凌已获用户认可；新增四位待试听。", '',
        '参考阵容固定于config/default-roster.json；用户已认可前轮两位并明确授权补齐其余四位；原两位不重跑，原唱张韶涵排除。六位均逐份核验固定15秒参考SHA256，用户认可不扩展到新增结果。',
        f"源：{c['source_artist']}《{c['source_song']}》；[公开来源]({c['source_url']})。",
        f"原素材区间：{c.get('source_start_seconds')} 秒起，时长 {c.get('duration_seconds')} 秒。离线ASR与人声能量辅助定位，非人工听音或歌词真值。", '',
        'Seed-VC V1 commit `51383efd921027683c89e5348211d93ff12ac2a8`，2026-10-18复核本地锁定README。',
        '30步单版，F0=true，autoF0=false，0半音，CFG0.7，FP32，seed20261016。',
        'MPS扩散/Whisper/音色编码器，CPU BigVGAN/RMVPE/频谱；沿用已审计环境及权重，重模型串行离线执行。',
        '直接复用stage14源人声、伴奏及原曲片段，逐字节核验；不重新下载、分离或选择副歌。',
        '六份参考均复用固定片段，不重新分离/挑片；一首参考素材不足10分钟，本轮零样本15秒参考，不训练。未额外去混响/和声，自动筛选不能证明纯净。', '',
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
        '新增四位尚无人工听感验收；不声称本人演唱，不虚构咬字或高音主观评价。统一内存分配与驱动峰值不能相加，也不是独立显存。', '',
        '## 复现', '', '```sh',
        '.envs/demucs/bin/python scripts/extend_shouxin_experiment.py prepare',
        'python3 scripts/extend_shouxin_experiment.py generate',
        '.envs/demucs/bin/python scripts/extend_shouxin_experiment.py validate', '```', '',
        '准备目录拒绝覆盖；成功生成会校验哈希后跳过。各run保存完整命令/参数/哈希/进度；日志logs/stage15-*，证据reports/evidence/stage15/，下载台账reports/downloads.md。']
    if 'batch_elapsed_seconds' in c:rows+=['',f"本轮新增四位生成与评测批次耗时（不含原两位）：{c['batch_elapsed_seconds']:.3f}秒。"]
    (ROOT/'reports/22_shouxin.md').write_text('\n'.join(rows)+'\n')


def verify_roster(c):
    p=ROOT/c['roster_config']
    assert hash_file(p)==c['roster_config_sha256'], 'Global roster changed: explicitly review before generation'
    roster=json.loads(p.read_text())
    assert c['steps']==roster['steps']==[30] and c['roster_id']==roster['id']
    assert tuple(a['key'] for a in c['artists'])==tuple(c['authorization']['authorized_artist_keys'])==EXPECTED
    assert tuple(c['authorization']['new_artist_keys'])==NEW
    assert c['authorization']['expansion_requires_user_feedback'] is False
    pilot=json.loads((ROOT/c['pilot_experiment']).read_text())
    for name in ('source_sha256','source_start_seconds','source_end_seconds','duration_seconds','steps','seed'):
        assert c[name]==pilot[name], 'Pilot settings must remain identical'
    if 'output_relocation' in c:
        relocation=c['output_relocation']
        assert relocation['from']==pilot['output_directory']=='outputs/stage14-shouxin'
        assert relocation['to']==c['output_directory']=='outputs/stage14-seven-shouxindetaiyang'
    else:
        assert c['output_directory']==pilot['output_directory']
    for old in pilot['artists']:
        current=next(a for a in c['artists'] if a['key']==old['key'])
        assert current['status']=='POC_PASSED' and current['generation_stage']=='stage14'
        expected=json.loads(json.dumps(old['deliverables']))
        if 'output_relocation' in c:
            for row in expected.values():
                row['path']=row['path'].replace(pilot['output_directory']+'/',c['output_directory']+'/',1)
        assert current['deliverables']==expected and current['metrics']==old['metrics']
        assert current['user_audition']=='APPROVED_IN_THIS_SCOPE'
        for row in current['deliverables'].values():assert hash_file(ROOT/row['path'])==row['sha256']
    assert c['source_artist']=='张韶涵' and c['source_song']=='手心的太阳'
    assert hash_file(ROOT/c['roster_snapshot'])==c['roster_config_sha256']
    assert c['source_segment_policy']['mode']=='single_complete_chorus'
    for a in c['artists']:
        default=next(item for item in roster['artists'] if item['key']==a['key'])
        for field in ('artist','reference_song','reuse_reference_from','reference_sha256','reference_interval_seconds'):
            assert a[field]==default[field], 'Reference differs from fixed roster'
        assert hash_file(ROOT/a['reuse_reference_from']/'target_reference_1.wav')==a['reference_sha256']
        original=json.loads((ROOT/a['reuse_reference_from']/'manifest.json').read_text())
        assert (original['target_artist'],original['target_song'])==(a['artist'],a['reference_song'])
        reference=original['references'][0]
        assert reference['original_interval_seconds']==a['reference_interval_seconds']
        assert reference['duration']==15 and reference['sha256']==a['reference_sha256']


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
        assert a['key'] in NEW and a['generation_stage']=='stage15'
        assert a['run_id']==f"stage15-{key}-{a['key']}"
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


def audit_shared_ledger(old):
    expected={r['path']:r for r in old}
    ledger=expected['reports/downloads.jsonl']
    content=(ROOT/ledger['path']).read_bytes()
    assert hashlib.sha256(content[:ledger['size']]).hexdigest()==ledger['sha256'], 'Original ledger prefix changed'
    prior=[json.loads(line) for line in content[:ledger['size']].decode().splitlines()]
    added=[json.loads(line) for line in content[ledger['size']:].decode().splitlines()]
    assert added and all(r['dest'].startswith('work/acquisition/stage16-source-xingfu/') for r in added)
    current=prior+added
    lines=(ROOT/'reports/downloads.md').read_text().splitlines()
    esc=lambda s:str(s).replace('|','\\|').replace('\n',' ')
    def table(rows):
        return ['| '+' | '.join(esc(v) for v in (r['dest'],r['status'],r.get('transferred_bytes',0),
                f"[来源]({r['url']}) / [依据]({r['evidence']})",r['license'],r.get('sha256','N/A')))+' |' for r in rows]
    assert lines[14:]==table(current), 'Markdown ledger diverged from raw records'
    transmitted=lambda rows:f"累计已传输：{sum(r.get('transferred_bytes',0) for r in rows):,} bytes；上限 30,000,000,000 bytes。"
    budget=lambda rows:f"预算已计费：{charged(rows):,} bytes（已开始但失败的请求按整文件保守计入）。"
    assert lines[6]==transmitted(current) and lines[8]==budget(current)
    restored=lines[:14]+table(prior);restored[6]=transmitted(prior);restored[8]=budget(prior)
    assert hashlib.sha256(('\n'.join(restored)+'\n').encode()).hexdigest()==expected['reports/downloads.md']['sha256']
    result={'original_ledger_prefix_unchanged':True,'original_markdown_reconstructs_exactly':True,
            'changed_shared_files':['reports/downloads.jsonl','reports/downloads.md'],
            'concurrent_experiment':'stage16-xingfu','added_records':[{'dest':r['dest'],'sha256':r.get('sha256'),'size_bytes':r['size_bytes']} for r in added],
            'action':'Preserved concurrent append; no ledger writes by stage15'}
    dump(EVIDENCE/'concurrent-ledger-audit.json',result)
    return result


def validate(evidence_name='final-validation.json'):
    import numpy as np
    import soundfile as sf
    old=json.loads((EVIDENCE/'protected-before.json').read_text())
    current=load('shouxin')
    ledger_changed=any(hash_file(ROOT/r['path'])!=r['sha256'] for r in old if r['path'] in ('reports/downloads.jsonl','reports/downloads.md'))
    shared_audit=audit_shared_ledger(old) if ledger_changed else None
    for row in old:
        if shared_audit and row['path'] in shared_audit['changed_shared_files']:continue
        path=row['path']
        if 'output_relocation' in current and path.startswith(current['output_relocation']['from']+'/'):
            path=current['output_relocation']['to']+path[len(current['output_relocation']['from']):]
        p=ROOT/path
        assert p.stat().st_size==row['size'] and hash_file(p)==row['sha256'],'Protected file changed'
    for row in json.loads((EVIDENCE/'mutable-with-backups.json').read_text()):
        p=ROOT/row['backup']
        assert p.stat().st_size==row['size'] and hash_file(p)==row['sha256']
    execution=json.loads((EVIDENCE/'execution-scripts.json').read_text())
    for row in execution['files']:
        p=ROOT/row['path']
        assert p.stat().st_size==row['size_bytes'] and hash_file(p)==row['sha256'], 'Execution wrapper changed during experiment'
    results=[];sources=set();references={};dry_hashes=set();players={}
    for key in KEYS:
        c=load(key);dest=ROOT/c['output_directory']
        assert c['status']=='POC_PASSED' and json.loads((dest/'manifest.json').read_text())==c
        verify_roster(c)
        assert {p.name for p in (dest/'runs').iterdir()}=={a['key'] for a in c['artists']}
        assert len(list(dest.glob('*_AI.wav')))==12
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
        assert len(tracks)==20 and len({t['url'] for t in tracks})==20 and c['source_song'] in document and 'A/B' not in document
        assert 'http://' not in document and 'https://' not in document
        for t in tracks:
            p=(dest/t['url']).resolve();assert p.is_relative_to(dest) and p.is_file()
        checked=subprocess.run(['node','scripts/check_group_player.cjs',str(dest/'listen.html')],
                               check=True,capture_output=True,text=True,env=local_env())
        players[key]=json.loads(checked.stdout)
        for a in c['artists']:
            evidence=ROOT/'reports/evidence'/a['generation_stage']/f"{key}-{a['key']}-validation.json"
            assert json.loads(evidence.read_text())['status']=='PASSED'
    assert len(sources)==1 and len(dry_hashes)==6 and len(references)==6 and all(len(v)==1 for v in references.values())
    assert len({next(iter(v)) for v in references.values()})==6
    result={'status':'PASSED','checked_at':dt.datetime.now(dt.timezone.utc).isoformat(),
        'audio':results,'protected_files_unchanged':len(old)-(2 if shared_audit else 0),'shared_ledger_audit':shared_audit,'distinct_sources':1,'distinct_conversions':6,'new_conversions':4,'final_audio_files':12,'approved_two_preserved':True,
        'fixed_roster_references_verified':True,'new_human_audition':False,'players':players,
        'execution_wrappers_unchanged':len(execution['files']),'f0_repair_used':False,
        'space_bytes':{n:sum(p.stat().st_size for p in (ROOT/n).rglob('*') if p.is_file()) for n in ['work','outputs']},
        'disk_free_bytes':shutil.disk_usage(ROOT).free,
        'download_budget':{'charged':charged(records()),'reserved':sum(reservations().values())}}
    with (EVIDENCE/evidence_name).open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['prepare','generate','validate'])
    a=p.parse_args()
    if a.action=='validate':validate()
    elif a.action=='prepare':prepare('shouxin')
    else:generate('shouxin')
