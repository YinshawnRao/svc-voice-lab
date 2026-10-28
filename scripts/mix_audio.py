#!/usr/bin/env python3
"""Mix completed local variants without loading any model; reuse only verified receipts."""
import argparse
import json
from pathlib import Path
from common import ROOT, variant_filename
from download import hash_file


def mix_file(source_path,dry_path,backing_path,dest):
    import numpy as np
    import soundfile as sf
    source_path,dry_path,backing_path,dest=(Path(p).resolve() for p in (source_path,dry_path,backing_path,dest))
    if not dest.is_relative_to(ROOT/'outputs'):raise ValueError('Mix must be under outputs')
    receipt=dest.with_suffix('.mix.json')
    inputs={'source_sha256':hash_file(source_path),'dry_sha256':hash_file(dry_path),'backing_sha256':hash_file(backing_path)}
    if dest.exists():
        if not receipt.exists():raise RuntimeError('Existing mix has no receipt; refusing overwrite')
        previous=json.loads(receipt.read_text())
        if previous.get('algorithm')!='rms_clamp05_2_peak098_v1' or previous['inputs']!=inputs or previous['mix_sha256']!=hash_file(dest):
            raise RuntimeError('Existing mix receipt does not match inputs/output')
        return previous
    source,sr=sf.read(source_path,dtype='float32',always_2d=True)
    wave,dry_sr=sf.read(dry_path,dtype='float32',always_2d=True)
    backing,back_sr=sf.read(backing_path,dtype='float32',always_2d=True)
    if sr!=dry_sr or sr!=back_sr:raise ValueError('Mix sample rates differ')
    if not all(np.isfinite(x).all() for x in [source,wave,backing]):raise ValueError('Non-finite input audio')
    if len(source)!=len(backing):raise ValueError('Source and backing length mismatch')
    if abs(len(wave)-len(backing))>sr*.05:raise ValueError('Converted length differs by over 50ms; inspect alignment before mixing')
    mono=wave.mean(axis=1)
    gain=float(np.clip(np.sqrt(np.mean(source**2))/max(np.sqrt(np.mean(mono**2)),1e-8),.5,2))
    aligned=np.pad(mono[:len(backing)],(0,max(0,len(backing)-len(mono))))
    mix=backing+aligned[:,None]*gain
    master_gain=min(1.,.98/max(float(np.max(np.abs(mix))),1e-8));mix*=master_gain
    sf.write(dest,mix,sr,subtype='PCM_16')
    row={'algorithm':'rms_clamp05_2_peak098_v1','inputs':inputs,'mix_path':str(dest.relative_to(ROOT)),
         'mix_sha256':hash_file(dest),'mix_peak':float(np.max(np.abs(mix))),'vocal_rms_matching_gain':gain,
         'master_peak_gain':master_gain,'alignment':'start-aligned, pad/trim only at tail for original backing length',
         'pad_tail_samples':max(0,len(backing)-len(mono)),'trim_tail_samples':max(0,len(mono)-len(backing)),
         'duration_seconds':len(mix)/sr}
    with receipt.open('x') as f:json.dump(row,f,indent=2);f.write('\n')
    return row


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,required=True)
    p.add_argument('--accompaniment',type=Path,required=True)
    args=p.parse_args();run=json.loads(args.run.read_text())
    for row in run['variants']:
        result=mix_file(run['source'],ROOT/row['path'],args.accompaniment,args.run.parent/variant_filename(row['label'],mixed=True))
        print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
