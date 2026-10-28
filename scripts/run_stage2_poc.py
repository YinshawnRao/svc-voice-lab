#!/usr/bin/env python3
"""Generate a prepared Seed-VC clip, defaulting to one 30-step version."""
import argparse
from pathlib import Path
import subprocess
import sys
from common import ROOT, local_env, DEFAULT_STEPS

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id',required=True)
    parser.add_argument('--output-dir',type=Path,help='Optional new directory under outputs/, for grouped experiments')
    parser.add_argument('--clips',type=Path,default=ROOT/'work/stage2-clips')
    parser.add_argument('--device',choices=['mps','cpu'],default='mps')
    parser.add_argument('--steps',type=int,nargs='+',default=list(DEFAULT_STEPS),help='Default: 30; multiple values explicitly request a comparison')
    parser.add_argument('--evidence-dir',type=Path,default=ROOT/'reports/evidence/stage2')
    args=parser.parse_args()
    if any(step<1 or step>100 for step in args.steps):raise SystemExit('steps must be 1-100')
    if not args.run_id.replace('-','').replace('_','').isalnum():raise SystemExit('Invalid run-id')
    clips=args.clips.resolve()
    evidence=args.evidence_dir.resolve()
    if not evidence.is_relative_to(ROOT/'reports/evidence'):raise SystemExit('Evidence must be under reports/evidence/')
    if not clips.is_relative_to(ROOT/'work'):raise SystemExit('Prepared clips must be under work/')
    for filename in ['source_vocals.wav','source_accompaniment.wav','target_reference_1.wav']:
        if not (clips/filename).is_file():raise SystemExit('Missing prepared clip: '+filename)
    output=(args.output_dir or ROOT/'outputs'/args.run_id).resolve()
    if not output.is_relative_to(ROOT/'outputs') or output==ROOT/'outputs':raise SystemExit('Output directory must be under outputs/')
    if output.exists():raise SystemExit('Choose a new output directory; output exists')
    commands=[
        [sys.executable,'scripts/bootstrap.py','seed-vc-cli'],
        [sys.executable,'scripts/run_logged.py','--name',args.run_id+'-convert','--evidence-dir',str(evidence),'--timeout','2400','--',
         str(ROOT/'.envs/seed-vc/bin/python'),'scripts/seed_vc_local.py','--source',str(clips/'source_vocals.wav'),
         '--target',str(clips/'target_reference_1.wav'),'--run-id',args.run_id,'--output-dir',str(output),'--steps',*map(str,args.steps),'--device',args.device],
        [sys.executable,'scripts/run_logged.py','--name',args.run_id+'-evaluate','--evidence-dir',str(evidence),'--timeout','600','--',
         str(ROOT/'.envs/seed-vc/bin/python'),'scripts/evaluate_stage2.py','--run',str(output/'run.json'),
         '--accompaniment',str(clips/'source_accompaniment.wav')],
    ]
    for command in commands:
        subprocess.run(command,cwd=ROOT,env=local_env(),check=True)
    print('Local listening page:',output/'listen.html')

if __name__=='__main__':main()
