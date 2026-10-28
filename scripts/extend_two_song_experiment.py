#!/usr/bin/env python3
"""Stage11: add five authorized singers to the two approved Stage10 experiments."""
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
from run_two_song_experiment import audio_row, command

EV = ROOT/'reports/evidence/stage11'
SONGS = ('xinqiang','xiaoxingyun')
NEW = ('stefanie','jolin','fish','cyndi','rainie')
EXPECTED = {'angela':'亲爱的那不是爱情','elva':'错的人','stefanie':'我怀念的',
            'jolin':'天空','fish':'崇拜','cyndi':'我会好好的','rainie':'雨爱'}


def config_path(key): return ROOT/f'config/experiments/stage11-{key}.json'
def load(key): return json.loads(config_path(key).read_text())
def save(key,c):
    dump(config_path(key),c)
    dump(ROOT/c['output_directory']/'manifest.json',c)


def logged(name,args,timeout=900):
    command(['python3','scripts/run_logged.py','--name',name,'--evidence-dir',EV,
             '--timeout',timeout,'--',*args])


def verify_deliverables(a):
    assert a['status']=='POC_PASSED'
    for r in a['deliverables'].values():
        p=ROOT/r['path'];assert p.stat().st_size==r['size_bytes'] and hash_file(p)==r['sha256']


def prepare_reference():
    acquisition=next(a for a in load('xinqiang')['artists'] if a['key']=='cyndi')['acquisition_id']
    receipt_path=ROOT/'work/acquisition'/acquisition/'receipt.json'
    receipt=json.loads(receipt_path.read_text());assert receipt['status']=='PASS'
    raw=ROOT/receipt['output']['data_path']
    assert raw.stat().st_size==receipt['output']['size_bytes'] and hash_file(raw)==receipt['output']['sha256']
    for r in json.loads((ROOT/'config/separation-models.json').read_text()):
        p=ROOT/r['dest'];assert p.stat().st_size==r['size_bytes'] and hash_file(p)==r['sha256']
    prep=ROOT/'work/stage11-cyndi-prep';assert not prep.exists()
    logged('stage11-cyndi-separate',[ROOT/'.envs/demucs/bin/python','-m','demucs','--repo','models/demucs-uvr',
        '-n','UVR_Demucs_Model_1','--two-stems','vocals','-d','mps','--shifts','1','--overlap','0.25',
        '--segment','7','--float32','-j','1','-o',prep/'separated',raw])
    stems=prep/'separated/UVR_Demucs_Model_1'/raw.stem
    target=prep/'target-vocals';target.mkdir();copy_checked(stems/'vocals.wav',target/'cyndi.wav')
    logged('stage11-cyndi-slice',['python3','scripts/slice_vocals.py','--input',target,'--run-id','stage11-cyndi-slices'])
    source=ROOT/'work/stage10-xinqiang-prep/separated/UVR_Demucs_Model_1/stage10-source-xinqiang-bili'
    logged('stage11-cyndi-select',[ROOT/'.envs/demucs/bin/python','scripts/prepare_stage2_clips.py',
        '--slices',ROOT/'work/stage11-cyndi-slices/target-slices','--source-vocals',source/'vocals.wav',
        '--source-accompaniment',source/'no_vocals.wav','--run-id','stage11-cyndi-selection',
        '--start','65.3','--duration','31.4'])
    select_reference()


def select_reference():
    acquisition=next(a for a in load('xinqiang')['artists'] if a['key']=='cyndi')['acquisition_id']
    receipt_path=ROOT/'work/acquisition'/acquisition/'receipt.json'
    receipt=json.loads(receipt_path.read_text());raw=ROOT/receipt['output']['data_path']
    assert receipt['status']=='PASS' and hash_file(raw)==receipt['output']['sha256']
    stems=ROOT/'work/stage11-cyndi-prep/separated/UVR_Demucs_Model_1'/raw.stem
    selected=ROOT/'work/stage11-cyndi-selection';m=json.loads((selected/'manifest.json').read_text())
    sm=json.loads((ROOT/'work/stage11-cyndi-slices/target-slices/manifest.json').read_text())
    # Retain the unconstrained selection; choose the highest-ranked full 15s candidate separately.
    ref=dict(next(r for r in m['candidates'] if r['duration']==15))
    row=next(r for r in sm['clips'] if (ROOT/r['path']).resolve()==Path(ref['path']).resolve())
    assert hash_file(Path(ref['path']))==row['sha256']==ref['sha256']
    ref['original_interval_seconds']=[row['start'],row['end']]
    selected=ROOT/'work/stage11-cyndi-reference';selected.mkdir(exist_ok=False)
    copy_checked(Path(ref['path']),selected/'target_reference_1.wav')
    m={'target_artist':'王心凌','target_song':'我会好好的','acquisition_receipt':str(receipt_path.relative_to(ROOT)),
       'references':[ref],'selection_basis':m['selection_basis']+'; require full 15 seconds for cross-song consistency',
       'cleanliness':'PROVISIONAL_NOT_AUDITIONED','files':[audio_row(selected/'target_reference_1.wav')]}
    dump(selected/'manifest.json',m);digest=hash_file(selected/'target_reference_1.wav')
    for key in SONGS:
        c=load(key);a=next(a for a in c['artists'] if a['key']=='cyndi')
        a.update(reference_sha256=digest,reference_interval_seconds=m['references'][0]['original_interval_seconds'],
                 reuse_reference_from=str(selected.relative_to(ROOT)),status='REFERENCE_READY')
        dump(config_path(key),c)
    dump(EV/'cyndi-preparation.json',{'receipt':str(receipt_path.relative_to(ROOT)),
        'stems':[audio_row(stems/n) for n in ('vocals.wav','no_vocals.wav')],
        'candidate_seconds':sm['candidate_seconds'],'approved_clean_seconds':None,
        'audition_sample':sm['audition_sample'],'selected_reference_sha256':digest,
        'selected_reference_interval_seconds':m['references'][0]['original_interval_seconds']})


def prepare_clips():
    for key in SONGS:
        c=load(key);assert {a['key']:a['reference_song'] for a in c['artists']}==EXPECTED
        shared=ROOT/f'work/stage10-{key}-shared';sharedm=json.loads((shared/'manifest.json').read_text())
        for r in sharedm['files']:assert hash_file(ROOT/r['path'])==r['sha256']
        for a in c['artists']:
            if a['generation_stage']=='stage10':verify_deliverables(a);continue
            old=ROOT/a['reuse_reference_from'];oldm=json.loads((old/'manifest.json').read_text())
            assert (oldm['target_artist'],oldm['target_song'])==(a['artist'],a['reference_song'])
            assert hash_file(old/'target_reference_1.wav')==a['reference_sha256']
            work=ROOT/a['clips'];work.mkdir(exist_ok=False)
            copy_checked(old/'target_reference_1.wav',work/'target_reference_1.wav')
            for r in sharedm['files']:
                p=ROOT/r['path'];copy_checked(p,work/p.name)
                assert hash_file(ROOT/c['output_directory']/'inputs'/p.name)==r['sha256']
            m={'source_interval_seconds':c['chorus_evidence']['selected_interval_seconds'],
               'source_artist':c['source_artist'],'source_song':c['source_song'],
               'target_artist':a['artist'],'target_song':a['reference_song'],
               'display_title':f"{a['artist']}音色 ·《{c['source_song']}》副歌",
               'original_mix_path':str(work/'source_original.wav'),
               'reference_note':f"参考人声：{a['artist']}《{a['reference_song']}》，两首歌共用同一15秒参考。",
               'references':oldm['references'][:1], 'selection_basis':oldm['selection_basis'],
               'reference_reuse':{'path':str(old/'target_reference_1.wav'),'byte_identical':True},
               'cleanliness':'PROVISIONAL_NOT_AUDITIONED','other_artist_target_audio_used':False,
               'files':[audio_row(p) for p in sorted(work.glob('*.wav'))]}
            dump(work/'manifest.json',m);a['status']='PREPARED'
        c['status']='PREPARED_EXTENSION';save(key,c);page(c);report(key,c)


def report(key,c):
    lines=[f"# 《{c['source_song']}》补齐七位歌手",'',
        f"2026-10-18；状态：{c['status']}。原实验目录：`{c['output_directory']}/`。",'',
        '用户明确评价前轮张韶涵、萧亚轩的两首结果“效果都很好”，并授权补齐其余五位。该认可只属于原四份演唱；新增十份尚待用户试听。',
        f"原四份成品保留不重跑；源区间保持{c['chorus_evidence']['selected_interval_seconds']}秒，时长{c['duration_seconds']}秒。源人声/伴奏逐字节复用。",'',
        'Seed-VC commit `51383efd921027683c89e5348211d93ff12ac2a8`；2026-10-18复核本地锁定README歌声参数。',
        '30步单版，F0开启，autoF0关闭，0半音，CFG0.7，FP32，seed20261016。扩散/编码器MPS，BigVGAN/RMVPE等CPU；重模型串行、全部本地、无音频上传。',
        '孙燕姿/蔡依林/梁静茹/杨丞琳沿用stage9同一15秒参考；王心凌改用本轮《我会好好的》，两首新歌共享相同新片段，不使用《变成陌生人》。', '',
        '| 歌手 | 参考歌 | 原参考区间/s | 状态 | 推理秒 | 音色余弦 | F0相关 | MPS分配/驱动GiB | 用户试听 |',
        '|---|---|---|---|---:|---:|---:|---|---|']
    for a in c['artists']:
        m=a.get('metrics',{})
        def fmt(k):return f"{m[k]:.4f}" if k in m else 'N/A'
        lines.append('| '+' | '.join([a['artist'],a['reference_song'],str(a.get('reference_interval_seconds')),a['status'],
            fmt('inference_seconds'),fmt('speaker_cosine'),fmt('f0_pearson'),fmt('mps_allocated_peak_gib')+' / '+fmt('mps_driver_peak_gib'),
            '前轮已认可' if a['generation_stage']=='stage10' else '待试听'])+' |')
    lines+=['','CAMPPlus也参与生成条件，余弦并非独立身份准确率；F0仅共同有声帧，覆盖率见manifest。缺独立歌词，CER=N/A。',
        '分离/自动选片不能保证无和声、混响或伴奏残留。各歌手素材不足10分钟；本轮零样本参考，不做歌手训练。',
        '统一内存分配与驱动峰值不能相加，不是独立显存。混音沿用源人声RMS增益0.5–2与0.98峰值保护，不是LUFS归一化。',
        '根目录每位混音、纯人声；listen.html支持同进度切换。每位run/evaluation/progress/mix收据在runs/<key>/。', '',
        '## 复现','', '```sh',
        '.envs/demucs/bin/python scripts/extend_two_song_experiment.py prepare-reference',
        '.envs/demucs/bin/python scripts/extend_two_song_experiment.py prepare-clips',
        'python3 scripts/extend_two_song_experiment.py generate',
        '.envs/demucs/bin/python scripts/extend_two_song_experiment.py validate',
        '```','',
        '准备目录已存在时拒绝覆盖；generate仅处理本轮五人，已成功项核验后跳过，保留原时间证据。失败项保留日志，先定位后使用新run-id修复；不覆盖原成品。',
        '阶段准备见18_preparation.md；逐条命令/耗时/检查见reports/evidence/stage11/及logs/stage11-*；下载台账见downloads.md。']
    if 'extension_elapsed_seconds' in c:lines+=['',f"本曲新增五位生成与评测：{c['extension_elapsed_seconds']:.3f} 秒；不含素材准备，不含前轮原两位成本。"]
    (ROOT/f'reports/18_{key}.md').write_text('\n'.join(lines)+'\n')


def generate():
    for key in SONGS:
        c=load(key);assert c['steps']==[30] and {a['key']:a['reference_song'] for a in c['artists']}==EXPECTED
        assert len([a for a in c['artists'] if a['generation_stage']=='stage11'])==5
        for a in c['artists']:
            if a['status']=='POC_PASSED':verify_deliverables(a)
        if all(a['status']=='POC_PASSED' for a in c['artists']):continue
        start=time.monotonic();c.update(status='RUNNING_EXTENSION',extension_started_at=dt.datetime.now(dt.timezone.utc).isoformat())
        save(key,c)
        for a in c['artists']:
            if a['generation_stage']=='stage10' or a['status']=='POC_PASSED':continue
            assert a['key'] in NEW and a['run_id']==f"stage11-{key}-{a['key']}"
            dest=ROOT/c['output_directory'];out=dest/'runs'/a['key']
            try:
                assert not out.exists(),'Refusing existing run directory; inspect before retry'
                a['status']='RUNNING';save(key,c)
                with (ROOT/'logs'/f"{a['run_id']}-launch.log").open('x') as log:
                    subprocess.run(['python3','scripts/run_stage2_poc.py','--run-id',a['run_id'],'--clips',a['clips'],
                        '--output-dir',str(out),'--evidence-dir',str(EV),'--device','mps','--steps','30'],
                        cwd=ROOT,env=local_env(),stdout=log,stderr=subprocess.STDOUT,check=True)
                command([ROOT/'.envs/demucs/bin/python','scripts/validate_full_song.py','--run',out/'run.json',
                    '--duration',c['duration_seconds'],'--evidence',EV/f"{key}-{a['key']}-validation.json"])
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
                a.update(status='FAILED',error=f'{type(exc).__name__}: {exc}');print(a['error'],flush=True)
            save(key,c);page(c);report(key,c)
            print('ARTIST_COMPLETED',c['source_song'],a['artist'],a['status'],flush=True)
        c.update(status='POC_PASSED' if all(a['status']=='POC_PASSED' for a in c['artists']) else 'PARTIAL',
            extension_completed_at=dt.datetime.now(dt.timezone.utc).isoformat(),extension_elapsed_seconds=time.monotonic()-start)
        save(key,c);page(c);report(key,c)


def validate():
    import numpy as np
    import soundfile as sf
    old=json.loads((EV/'protected-before.json').read_text())
    for r in old:
        p=ROOT/r['path'];assert p.stat().st_size==r['size'] and hash_file(p)==r['sha256'],r['path']
    for r in json.loads((EV/'mutable-with-backups.json').read_text()):
        p=ROOT/r['backup'];assert hash_file(p)==r['sha256'] and p.stat().st_size==r['size']
    acquisition=next(a for a in load('xinqiang')['artists'] if a['key']=='cyndi')['acquisition_id']
    receipt=json.loads((ROOT/'work/acquisition'/acquisition/'receipt.json').read_text())
    raw=ROOT/receipt['output']['data_path'];assert hash_file(raw)==receipt['output']['sha256'] and raw.stat().st_size==receipt['output']['size_bytes']
    rows=[];refs={};sources=set();conversions=set();players={};new_count=0
    for key in SONGS:
        c=load(key);dest=ROOT/c['output_directory'];assert c['status']=='POC_PASSED'
        assert json.loads((dest/'manifest.json').read_text())==c
        assert {a['key']:a['reference_song'] for a in c['artists']}==EXPECTED
        assert {p.name for p in (dest/'runs').iterdir()}==set(EXPECTED)
        assert len(list(dest.glob('*_AI.wav')))==14
        common=set()
        for a in c['artists']:
            verify_deliverables(a)
            r=json.loads((dest/'runs'/a['key']/'run.json').read_text());e=json.loads((dest/'runs'/a['key']/'evaluation.json').read_text())
            m=json.loads((ROOT/a['clips']/'manifest.json').read_text())
            assert (m['target_artist'],m['target_song'],m['source_song'])==(a['artist'],a['reference_song'],c['source_song'])
            assert r['requested_steps']==[30] and r['target_sha256']==a['reference_sha256']==hash_file(Path(r['target']))
            common.add(r['source_sha256']);refs.setdefault(a['key'],set()).add(r['target_sha256'])
            stage='stage11' if a['generation_stage']=='stage11' else 'stage10'
            assert json.loads((ROOT/f"reports/evidence/{stage}/{key}-{a['key']}-validation.json").read_text())['status']=='PASSED'
            if stage=='stage11':new_count+=1
            else:assert a['user_audition']=='APPROVED_IN_THIS_SCOPE'
            for mode,row in a['deliverables'].items():
                p=ROOT/row['path'];w,sr=sf.read(p,always_2d=True)
                assert sr==44100 and np.isfinite(w).all() and np.max(np.abs(w))>1e-5
                assert w.shape[1]==(2 if mode=='mix' else 1)
                assert abs(len(w)-round((15 if mode=='reference' else c['duration_seconds'])*sr))<=(512 if mode=='dry' else 0)
                if mode=='mix':assert np.max(np.abs(w))<=.981 and row['sha256']==e['variants'][0]['mix_sha256']
                if mode=='dry':
                    assert row['sha256']==r['variants'][0]['sha256']!=r['source_sha256'];conversions.add(row['sha256'])
                rows.append({'song':c['source_song'],'artist':a['artist'],'generation_stage':stage,'mode':mode,**row,
                    'duration':len(w)/sr,'peak':float(np.max(np.abs(w))),'near_full_scale_fraction':float(np.mean(np.abs(w)>=.999))})
        assert len(common)==1;sources.update(common)
        doc=(dest/'listen.html').read_text();tracks=json.loads(re.search(r'const tracks=(\[.*?\]);',doc).group(1))
        assert len(tracks)==23 and len({t['url'] for t in tracks})==23 and 'A/B' not in doc
        assert 'http://' not in doc and 'https://' not in doc
        for t in tracks:
            p=(dest/t['url']).resolve();assert p.is_relative_to(dest) and p.is_file()
        player=subprocess.run(['node','scripts/check_group_player.cjs',str(dest/'listen.html')],check=True,capture_output=True,text=True,env=local_env())
        players[key]=json.loads(player.stdout);assert players[key]['mix_tracks']==7
    assert len(sources)==2 and len(conversions)==14 and new_count==10
    assert all(len(v)==1 for v in refs.values()) and len(set.union(*refs.values()))==7
    previous=json.loads((ROOT/'config/experiments/seven-ruguoniyetingshuo.json').read_text())
    assert next(iter(refs['cyndi']))!=next(a for a in previous['artists'] if a['key']=='cyndi')['reference_sha256']
    result={'status':'PASSED','checked_at':dt.datetime.now(dt.timezone.utc).isoformat(),'audio':rows,
        'protected_files_unchanged':len(old),'original_four_conversions_unchanged':True,'new_conversions':new_count,
        'total_conversions':14,'final_audio_files':28,'same_references_across_songs':True,'cyndi_new_song_verified':True,
        'players':players,'new_human_audition':False,
        'space_bytes':{n:sum(p.stat().st_size for p in (ROOT/n).rglob('*') if p.is_file()) for n in ['work','outputs']},
        'disk_free_bytes':shutil.disk_usage(ROOT).free,'download_budget':{'charged':charged(records()),'reserved':sum(reservations().values())}}
    with (EV/'final-validation.json').open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k!='audio'},ensure_ascii=False,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['prepare-reference','select-reference','prepare-clips','generate','validate']);a=p.parse_args()
    {'prepare-reference':prepare_reference,'select-reference':select_reference,'prepare-clips':prepare_clips,'generate':generate,'validate':validate}[a.action]()
