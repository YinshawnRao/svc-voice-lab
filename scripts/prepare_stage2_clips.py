#!/usr/bin/env python3
"""Select provisional references from local vocal slices; never certifies cleanliness."""
import argparse
import json
from pathlib import Path
import subprocess
import numpy as np
import soundfile as sf
from common import ROOT, local_env
from download import hash_file

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--slices", type=Path, required=True)
    parser.add_argument("--source-vocals",type=Path,required=True)
    parser.add_argument("--source-accompaniment",type=Path,required=True)
    parser.add_argument("--run-id",required=True)
    parser.add_argument("--start",type=float,default=60)
    parser.add_argument("--duration",type=float,default=20)
    args=parser.parse_args()
    if not args.run_id.replace('-','').replace('_','').isalnum():raise SystemExit('invalid run id')
    dest=ROOT/'work'/args.run_id;dest.mkdir(parents=True,exist_ok=False)
    candidates=[]
    for path in sorted(args.slices.glob('*.wav')):
        x,sr=sf.read(path,always_2d=True);x=x.mean(axis=1)
        duration=len(x)/sr
        if not 8<=duration<=15.01:continue
        frame=int(.1*sr);rms=np.sqrt(np.mean(x[:len(x)//frame*frame].reshape(-1,frame)**2,axis=1))
        activity=float(np.mean(rms>10**(-40/20)))
        clipping=float(np.mean(np.abs(x)>=.999))
        level=float(np.sqrt(np.mean(x*x)))
        candidates.append({'path':str(path),'sha256':hash_file(path),'duration':duration,'activity_ratio_100ms':activity,
                           'rms':level,'clipping_fraction':clipping,'score':activity-20*clipping})
    candidates.sort(key=lambda r:(r['score'],r['rms']),reverse=True)
    if not candidates:raise SystemExit('no 8-15s references; inspect slice manifest')
    selected=candidates[:3]
    command=['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-n']
    commands=[]
    for name,source,mono in [('source_vocals.wav',args.source_vocals,True),('source_accompaniment.wav',args.source_accompaniment,False)]:
        cmd=command+['-ss',str(args.start),'-t',str(args.duration),'-i',str(source),'-ar','44100']
        if mono:cmd+=['-ac','1']
        cmd+=['-c:a','pcm_s16le',str(dest/name)]
        subprocess.run(cmd,check=True,env=local_env());commands.append(cmd)
    for i,row in enumerate(selected,1):
        cmd=command+['-i',row['path'],'-ar','44100','-ac','1','-c:a','pcm_s16le',str(dest/f'target_reference_{i}.wav')]
        subprocess.run(cmd,check=True,env=local_env());commands.append(cmd)
    manifest={'source_interval_seconds':[args.start,args.start+args.duration],'source_full_vocals':str(args.source_vocals),
              'source_full_accompaniment':str(args.source_accompaniment),'references':selected,'candidates':candidates,'commands':commands,
              'selection_basis':'8-15s, high non-silent-frame coverage, low clipping; RMS tie-breaker; does not prove no harmony/reverb or residual backing',
              'cleanliness':'PROVISIONAL_NOT_AUDITIONED','files':[]}
    for path in sorted(dest.glob('*.wav')):
        info=sf.info(path);manifest['files'].append({'path':str(path.relative_to(ROOT)),'sha256':hash_file(path),'duration':info.duration,'sr':info.samplerate,'channels':info.channels})
    (dest/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'directory':str(dest),'reference_candidates':len(candidates),'selected':selected},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
