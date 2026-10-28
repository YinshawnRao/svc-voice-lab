#!/usr/bin/env python3
"""Build offline environments, separate data/, select references and run one short PoC.

Requires the audited source, weights and dependency cache already present. Never
downloads automatically or overwrites inputs, work or outputs. All target vocals
are provisional candidates; automatic selection does not certify cleanliness.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

from common import ROOT, local_env, DEFAULT_STEPS
from download import hash_file
from inventory import AUDIO, probe
from separate import select_songs


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id',required=True)
    parser.add_argument('--source',type=Path,help='Required when data/source contains multiple songs')
    parser.add_argument('--target',type=Path,action='append',help='Repeat for the same target artist; required when data/target has multiple files')
    parser.add_argument('--start',type=float,default=60)
    parser.add_argument('--duration',type=float,default=20)
    parser.add_argument('--device',choices=['mps','cpu'],default='mps')
    parser.add_argument('--steps',type=int,nargs='+',default=list(DEFAULT_STEPS),help='Default: 30; multiple values explicitly request a comparison')
    args=parser.parse_args()
    if any(step<1 or step>100 for step in args.steps):raise SystemExit('steps must be 1-100')
    if not args.run_id.replace('-','').replace('_','').isalnum():raise SystemExit('Invalid run-id')
    if args.start<0 or not 1<=args.duration<=30:raise SystemExit('Use a 1-30 second short PoC interval')
    sources=sorted(p.resolve() for p in (ROOT/'data/source').rglob('*') if p.is_file() and p.suffix.lower() in AUDIO)
    source=args.source.resolve() if args.source else sources[0] if len(sources)==1 else None
    if source is None or source not in sources:raise SystemExit('Select a song in data/source with --source')
    if not source.is_relative_to(ROOT/'data/source'):raise SystemExit('Source must resolve under data/source')
    targets=args.target or sorted(p for p in (ROOT/'data/target').rglob('*') if p.is_file() and p.suffix.lower() in AUDIO)
    if not args.target and len(targets)!=1:raise SystemExit('Select same-artist target files with --target; multiple artists must never be combined')
    selected_inputs=select_songs(targets,[source])
    selected_flags=[]
    for role,path in selected_inputs:selected_flags.extend(['--'+role,str(path)])
    metadata=probe(source)
    if metadata.get('duration_seconds',0)<args.start+args.duration:raise SystemExit('Requested interval exceeds source duration; adjust --start/--duration')
    stem=args.run_id
    for name in [stem,stem+'-separate',stem+'-slices',stem+'-clips']:
        if (ROOT/'work'/name).exists() or (ROOT/'outputs'/name).exists():raise SystemExit('Choose a new run-id; files already exist')
    def run(*command):subprocess.run(list(command),cwd=ROOT,env=local_env(),check=True)
    run(sys.executable,'scripts/bootstrap.py','demucs')
    run(sys.executable,'scripts/separate.py','--model-repo','models/demucs-uvr','--model','UVR_Demucs_Model_1','--run-id',stem+'-separate','--device',args.device,*selected_flags)
    separated=json.loads((ROOT/'work'/f'{stem}-separate'/'separated/manifest.json').read_text())
    vocals=ROOT/'work'/stem/'target-vocals';vocals.mkdir(parents=True)
    provenance=[];selected=None
    for song in separated['songs']:
        original=ROOT/song['source']
        folder=ROOT/song['output_directory']/separated['model']/original.stem
        if original.resolve().is_relative_to(ROOT/'data/target'):
            target=vocals/(song['sha256'][:12]+'.wav')
            if not target.exists():shutil.copyfile(folder/'vocals.wav',target)
            provenance.append({'source':song['source'],'source_sha256':song['sha256'],'vocals':str(target.relative_to(ROOT)),'vocals_sha256':hash_file(target)})
        if original.resolve()==source:selected=folder
    (vocals/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    if not provenance or selected is None:raise SystemExit('Missing target or selected source stems')
    run(sys.executable,'scripts/slice_vocals.py','--input',str(vocals),'--run-id',stem+'-slices')
    clips=ROOT/'work'/f'{stem}-clips'
    run(str(ROOT/'.envs/demucs/bin/python'),'scripts/prepare_stage2_clips.py','--slices',str(ROOT/'work'/f'{stem}-slices'/'target-slices'),
        '--source-vocals',str(selected/'vocals.wav'),'--source-accompaniment',str(selected/'no_vocals.wav'),
        '--run-id',stem+'-clips','--start',str(args.start),'--duration',str(args.duration))
    run(sys.executable,'scripts/run_stage2_poc.py','--run-id',stem,'--clips',str(clips),'--steps',*map(str,args.steps),'--device',args.device)


if __name__=='__main__':main()
