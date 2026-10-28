#!/usr/bin/env python3
"""Validate single or comparison audio, input preservation and local links."""
import argparse
import json
from html.parser import HTMLParser
from pathlib import Path
import numpy as np
import soundfile as sf
from common import ROOT
from download import hash_file


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--evidence',type=Path,required=True)
    parser.add_argument('--duration',type=float,help='Expected clip seconds; omitted means a complete song over 60 seconds')
    args=parser.parse_args()
    run=json.loads(args.run.read_text());dest=args.run.parent
    evaluation=json.loads((dest/'evaluation.json').read_text())
    inputs=json.loads((Path(run['source']).parent/'manifest.json').read_text())
    for item in inputs['files']:
        assert hash_file(ROOT/item['path'])==item['sha256'],'Prepared input changed'
    for key in ['source','target']:
        assert hash_file(Path(run[key]))==run[key+'_sha256'],'Inference input changed'
    source_info=sf.info(run['source'])
    if args.duration is None:
        assert source_info.duration>60,'Expected a complete song, not the short PoC'
    else:
        assert args.duration>0 and source_info.frames==round(args.duration*source_info.samplerate),'Unexpected clip duration'
    steps=run.get('requested_steps',[30,50])  # Historical manifests predate this field.
    assert steps and all(isinstance(s,int) and 1<=s<=100 for s in steps),'Invalid requested steps'
    expected=[('single',steps[0])] if len(steps)==1 else [(chr(ord('A')+i),s) for i,s in enumerate(steps)]
    assert [(x['label'],x['steps']) for x in run['variants']]==expected,'Missing or unexpected generated version'
    assert [(x['label'],x['steps']) for x in evaluation['variants']]==expected,'Missing or unexpected evaluated version'
    checks=[];digests=[]
    for row,metric in zip(run['variants'],evaluation['variants']):
        assert (row['f0_condition'],row['auto_f0_adjust'],row['semitones'],row['cfg_rate'])==(True,False,0,.7)
        for key,hash_key,channels in [('path','sha256',1),('mix_path','mix_sha256',2)]:
            record=row if key=='path' else metric
            path=ROOT/record[key];wave,sr=sf.read(path,always_2d=True)
            assert hash_file(path)==record[hash_key],'Output hash mismatch'
            assert sr==44100 and wave.shape[1]==channels
            assert np.isfinite(wave).all() and np.max(np.abs(wave))>1e-5
            if channels==2:
                assert len(wave)==source_info.frames and np.max(np.abs(wave))<=.981
            else:
                assert abs(len(wave)-source_info.frames)<=512,'Over one hop length mismatch'
                digests.append(record[hash_key])
            checks.append({'path':record[key],'duration_seconds':len(wave)/sr,'frames':len(wave),'channels':channels,
                           'peak':float(np.max(np.abs(wave))),'near_full_scale_fraction':float(np.mean(np.abs(wave)>=.999))})
    if len(expected)>1:assert len(set(digests))==len(expected),'Comparison versions unexpectedly identical'
    class LocalLinks(HTMLParser):
        def handle_starttag(self,tag,attrs):
            for name,value in attrs:
                if name in ['href','src']:
                    assert not value.startswith(('http:','https:','//')),'External resource'
                    assert (dest/value).resolve().is_file(),'Missing local listening file'
    LocalLinks().feed((dest/'listen.html').read_text())
    result={'status':'PASSED','input_hashes_unchanged':True,'source_duration_seconds':source_info.duration,
            'scope':'complete song' if args.duration is None else 'exact-duration clip',
            'audio':checks,'local_listening_links':'PASSED','human_audition':False,
            'limits':'Length checks do not prove every internal syllable is aligned or every join is inaudible.'}
    with args.evidence.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
