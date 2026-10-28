#!/usr/bin/env python3
"""Convert the complete local source, defaulting to one 30-step Seed-VC version.

Uses the audited local installation and original full-length separated stems.
No downloads, clipping of song duration, or replacement of earlier outputs.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
from common import ROOT, local_env, DEFAULT_STEPS
from download import hash_file
from inventory import probe


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vocals',type=Path,required=True)
    parser.add_argument('--accompaniment',type=Path,required=True)
    parser.add_argument('--reference',type=Path,required=True)
    parser.add_argument('--original',type=Path,help='Optional original full mix for listening comparisons')
    parser.add_argument('--title',default='完整歌曲试听')
    parser.add_argument('--run-id',required=True)
    parser.add_argument('--device',choices=['cpu','mps'],default='mps')
    parser.add_argument('--steps',type=int,nargs='+',default=list(DEFAULT_STEPS),help='Default: 30; multiple values explicitly request a comparison')
    args=parser.parse_args()
    if any(step<1 or step>100 for step in args.steps):raise SystemExit('steps must be 1-100')
    if not args.run_id.replace('-','').replace('_','').isalnum():raise SystemExit('Invalid run-id')
    for path in [args.vocals,args.accompaniment,args.reference]+([args.original] if args.original else []):
        if not path.resolve().is_relative_to(ROOT) or not path.is_file():raise SystemExit('Inputs must exist inside this repository')
    work=ROOT/'work'/args.run_id; output=ROOT/'outputs'/args.run_id
    if work.exists() or output.exists():raise SystemExit('Choose a new run-id; existing files are preserved')
    info=probe(args.vocals);back_info=probe(args.accompaniment)
    if 'error' in info or 'error' in back_info or abs(info['duration_seconds']-back_info['duration_seconds'])>.05:
        raise SystemExit('Full vocals and accompaniment must have matching durations')
    inputs=work/'inputs';inputs.mkdir(parents=True)
    commands=[];start=time.monotonic()
    def run(command):
        commands.append(command)
        subprocess.run(command,cwd=ROOT,env=local_env(),check=True)
    for path,name,channels in [(args.vocals,'source_vocals.wav',1),(args.accompaniment,'source_accompaniment.wav',2)]:
        run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-n','-i',str(path.resolve()),
             '-ar','44100','-ac',str(channels),'-c:a','pcm_s16le',str(inputs/name)])
    shutil.copyfile(args.reference,inputs/'target_reference_1.wav')
    manifest={'scope':'full source, no song trimming','source_interval_seconds':[0,info['duration_seconds']],
              'display_title':args.title,'original_mix_path':str(args.original.resolve()) if args.original else None,
              'source_full_vocals':str(args.vocals.resolve()),'source_full_accompaniment':str(args.accompaniment.resolve()),
              'reference_original':str(args.reference.resolve()),'commands':commands.copy(),
              'preparation_seconds':time.monotonic()-start,'files':[]}
    for path in sorted(inputs.glob('*.wav')):
        manifest['files'].append({'path':str(path.relative_to(ROOT)),'sha256':hash_file(path),**probe(path)})
    (inputs/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    run([sys.executable,'scripts/bootstrap.py','seed-vc-cli'])
    run([sys.executable,'scripts/run_logged.py','--name',args.run_id+'-convert','--evidence-dir','reports/evidence/stage3','--timeout','10800','--',
         str(ROOT/'.envs/seed-vc/bin/python'),'scripts/seed_vc_local.py','--source',str(inputs/'source_vocals.wav'),
         '--target',str(inputs/'target_reference_1.wav'),'--run-id',args.run_id,'--steps',*map(str,args.steps),'--device',args.device])
    run([sys.executable,'scripts/run_logged.py','--name',args.run_id+'-evaluate','--evidence-dir','reports/evidence/stage3','--timeout','1200','--',
         str(ROOT/'.envs/seed-vc/bin/python'),'scripts/evaluate_stage2.py','--run',str(output/'run.json'),
         '--accompaniment',str(inputs/'source_accompaniment.wav')])
    run([str(ROOT/'.envs/seed-vc/bin/python'),'scripts/validate_full_song.py','--run',str(output/'run.json'),
         '--evidence',str(ROOT/'reports/evidence/stage3'/f'{args.run_id}-validation.json')])
    print('Full-song listening page:',output/'listen.html')


if __name__=='__main__':main()
