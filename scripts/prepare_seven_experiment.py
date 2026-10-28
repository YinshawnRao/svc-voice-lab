#!/usr/bin/env python3
"""Prepare the seven requested references and one shared chorus; run with demucs Python."""
import argparse
import json
import shutil
import subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
from common import ROOT, local_env
from download import hash_file

CONFIG = ROOT/'config/experiments/seven-ruguoniyetingshuo.json'
EVIDENCE = ROOT/'reports/evidence/stage9'


def run(command):
    subprocess.run(list(map(str,command)),cwd=ROOT,env=local_env(),check=True)


def dump(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def file_row(path):
    audio,sr=sf.read(path,always_2d=True)
    assert sr==44100 and np.isfinite(audio).all() and np.max(np.abs(audio))>1e-5
    return {'path':str(path.relative_to(ROOT)),'sha256':hash_file(path),
            'duration':len(audio)/sr,'sr':sr,'channels':audio.shape[1]}


def separate(a):
    receipt_path=ROOT/'work/acquisition'/a['acquisition_id']/'receipt.json'
    receipt=json.loads(receipt_path.read_text());assert receipt['status']=='PASS'
    raw=ROOT/receipt['output']['data_path']
    assert hash_file(raw)==receipt['output']['sha256'] and raw.stat().st_size==receipt['output']['size_bytes']
    for row in json.loads((ROOT/'config/separation-models.json').read_text()):
        path=ROOT/row['dest']
        assert path.stat().st_size==row['size_bytes'] and hash_file(path)==row['sha256']
    prep=ROOT/f"work/stage9-{a['key']}-prep"
    assert not prep.exists(),'Preparation already exists; inspect before retrying'
    run(['python3','scripts/run_logged.py','--name',f"stage9-{a['key']}-separate",'--evidence-dir',EVIDENCE,'--timeout','900','--',
         ROOT/'.envs/demucs/bin/python','-m','demucs','--repo','models/demucs-uvr','-n','UVR_Demucs_Model_1',
         '--two-stems','vocals','-d','mps','--shifts','1','--overlap','0.25','--segment','7','--float32','-j','1',
         '-o',prep/'separated',raw])
    stems=prep/'separated/UVR_Demucs_Model_1'/raw.stem
    rows=[file_row(stems/name) for name in ('vocals.wav','no_vocals.wav')]
    vocals=prep/'target-vocals';vocals.mkdir()
    shutil.copy2(stems/'vocals.wav',vocals/(a['key']+'.wav'))
    run(['python3','scripts/slice_vocals.py','--input',vocals,'--run-id',f"stage9-{a['key']}-slices"])
    sm=json.loads((ROOT/f"work/stage9-{a['key']}-slices/target-slices/manifest.json").read_text())
    dump(EVIDENCE/f"{a['key']}-preparation.json",{'artist':a['artist'],'song':a['reference_song'],
        'receipt':str(receipt_path.relative_to(ROOT)),'stems':rows,'candidate_seconds':sm['candidate_seconds'],
        'approved_clean_seconds':None,'audition_sample':sm['audition_sample'],'slicing_elapsed_seconds':sm['elapsed_seconds']})


def clips(c):
    start=c['source_start_seconds'];duration=c['duration_seconds']
    assert start is not None,'Locate the chorus first'
    source_stems=ROOT/'work/stage9-source-prep/separated/UVR_Demucs_Model_1/stage9-source-ruguoniyetingshuo'
    shared=ROOT/'work/stage9-shared-chorus'
    if shared.exists():
        prior=json.loads((shared/'manifest.json').read_text())
        assert prior['source_interval_seconds']==[start,start+duration]
        for row in prior['files']:assert hash_file(ROOT/row['path'])==row['sha256']
    else:shared.mkdir()
    for name,path,channels in [('source_vocals.wav',source_stems/'vocals.wav',1),
        ('source_accompaniment.wav',source_stems/'no_vocals.wav',2),
        ('source_original.wav',ROOT/'data/source/stage9-source-ruguoniyetingshuo.wav',2)]:
        if not (shared/name).exists():
            run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-n','-ss',start,'-t',duration,'-i',path,
                 '-ar','44100','-ac',channels,'-c:a','pcm_s16le',shared/name])
    shared_rows=[file_row(p) for p in sorted(shared.glob('*.wav'))]
    dump(shared/'manifest.json',{'files':shared_rows,'source_interval_seconds':[start,start+duration],'chorus_evidence':c['chorus_evidence']})
    for a in c['artists']:
        dest=ROOT/a['clips']
        if dest.exists():
            m=json.loads((dest/'manifest.json').read_text())
            assert (m['target_artist'],m['target_song'])==(a['artist'],a['reference_song'])
            for row in m['files']:assert hash_file(ROOT/row['path'])==row['sha256']
        elif a.get('reuse_reference_from'):
            old=ROOT/a['reuse_reference_from'];oldm=json.loads((old/'manifest.json').read_text())
            assert (oldm['target_artist'],oldm['target_song'])==(a['artist'],a['reference_song'])
            row=next(r for r in oldm['files'] if r['path'].endswith('target_reference_1.wav'))
            assert hash_file(old/'target_reference_1.wav')==row['sha256']
            dest.mkdir(exist_ok=False)
            shutil.copy2(old/'target_reference_1.wav',dest/'target_reference_1.wav')
            m={k:oldm[k] for k in ('selection_basis','cleanliness')}
            m['references']=oldm['references'][:1]
            m['reference_reuse']={'previous':str(old/'target_reference_1.wav'),'sha256':row['sha256'],'byte_identical':True}
        else:
            slices=ROOT/f"work/stage9-{a['key']}-slices/target-slices"
            run([ROOT/'.envs/demucs/bin/python','scripts/prepare_stage2_clips.py','--slices',slices,
                '--source-vocals',source_stems/'vocals.wav','--source-accompaniment',source_stems/'no_vocals.wav',
                '--run-id',dest.name,'--start',start,'--duration',duration])
            m=json.loads((dest/'manifest.json').read_text());sm=json.loads((slices/'manifest.json').read_text())
            for ref in m['references']:
                row=next(r for r in sm['clips'] if (ROOT/r['path']).resolve()==Path(ref['path']).resolve())
                ref['original_interval_seconds']=[row['start'],row['end']]
        for ref in m['references']:
            if 'original_interval_seconds' not in ref:
                refpath=ROOT/ref['path']
                sm=json.loads((refpath.parent/'manifest.json').read_text())
                row=next(r for r in sm['clips'] if (ROOT/r['path']).resolve()==refpath.resolve())
                assert hash_file(refpath)==row['sha256']==ref['sha256']
                ref['original_interval_seconds']=[row['start'],row['end']]
        for row in shared_rows:
            path=ROOT/row['path'];out=dest/path.name
            if out.exists():assert hash_file(out)==row['sha256']
            else:shutil.copy2(path,out)
        m.update(source_interval_seconds=[start,start+duration],source_full_vocals=str(source_stems/'vocals.wav'),
            source_full_accompaniment=str(source_stems/'no_vocals.wav'),source_artist=c['source_artist'],source_song=c['source_song'],
            target_artist=a['artist'],target_song=a['reference_song'],display_title=f"{a['artist']}音色 ·《{c['source_song']}》副歌",
            original_mix_path=str(dest/'source_original.wav'),chorus_evidence=c['chorus_evidence'],
            reference_note=f"参考人声：{a['artist']}《{a['reference_song']}》",other_artist_target_audio_used=False,
            files=[file_row(p) for p in sorted(dest.glob('*.wav'))])
        dump(dest/'manifest.json',m)
        a.update(status='PREPARED',reference_interval_seconds=m['references'][0]['original_interval_seconds'],
                 reference_sha256=hash_file(dest/'target_reference_1.wav'))
        dump(CONFIG,c)
    c['status']='PREPARED';dump(CONFIG,c)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['separate','clips']);p.add_argument('--artist')
    args=p.parse_args();c=json.loads(CONFIG.read_text())
    if args.action=='separate':separate(next(a for a in c['artists'] if a['key']==args.artist))
    else:clips(c)
