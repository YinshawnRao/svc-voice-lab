#!/usr/bin/env python3
"""Local mix, signal checks and provisional CAMPPlus/F0 diagnostics."""
import argparse
import json
import os
from pathlib import Path
import sys
import time
from common import ROOT, local_env, variant_filename
from download import hash_file
from seed_vc_local import block_network, verify_artifacts
from listening_page import write_page
from mix_audio import mix_file

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--accompaniment',type=Path,required=True)
    args=parser.parse_args()
    run=json.loads(args.run.read_text());dest=args.run.parent
    if not dest.resolve().is_relative_to(ROOT/'outputs'):raise SystemExit('run must be under outputs/')
    os.environ.update(local_env());block_network();verify_artifacts()
    import numpy as np
    import soundfile as sf
    import torch
    import torchaudio
    torch.set_num_threads(4)
    sys.path.insert(0,str(ROOT/'vendor/seed-vc'))
    from modules.campplus.DTDNN import CAMPPlus
    from modules.rmvpe import RMVPE
    start=time.monotonic()
    speaker=CAMPPlus(feat_dim=80,embedding_size=192)
    speaker.load_state_dict(torch.load(ROOT/'models/campplus/campplus_cn_common.bin',map_location='cpu',weights_only=True));speaker.eval()
    pitch=RMVPE(str(ROOT/'models/rmvpe/rmvpe.pt'),is_half=False,device=torch.device('cpu'))
    def features(path):
        wave,sr=sf.read(path,dtype='float32',always_2d=True)
        tensor=torch.from_numpy(wave.mean(axis=1)).unsqueeze(0)
        tensor=torchaudio.functional.resample(tensor,sr,16000)
        with torch.no_grad():
            bank=torchaudio.compliance.kaldi.fbank(tensor,num_mel_bins=80,dither=0,sample_frequency=16000)
            bank-=bank.mean(dim=0,keepdim=True)
            emb=speaker(bank.unsqueeze(0))[0].numpy()
            f0=pitch.infer_from_audio(tensor[0],thred=.03).astype(np.float32)
        return emb,f0
    def cosine(a,b):return float(np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b)))
    ref_emb,_=features(run['target']);source_emb,source_f0=features(run['source'])
    source,source_sr=sf.read(run['source'],dtype='float32',always_2d=True)
    backing,back_sr=sf.read(args.accompaniment,dtype='float32',always_2d=True)
    if source_sr!=back_sr:raise RuntimeError('source/backing sample rates differ')
    result={'speaker_encoder':'CAMPPlus cn 192D; also used for conditioning, not independent validation',
            'pitch_estimator':'RMVPE CPU; hop 160 at 16kHz; zero-lag common voiced frames',
            'reference':run['target'],'source':run['source'],'source_target_cosine':cosine(source_emb,ref_emb),
            'CER':None,'CER_reason':'no independently verified lyrics; ASR output is not ground truth',
            'human_listening':'PENDING','variants':[]}
    for row in run['variants']:
        path=ROOT/row['path'];wave,sr=sf.read(path,dtype='float32',always_2d=True)
        if sr!=back_sr:raise RuntimeError('converted sample rate differs')
        emb,f0=features(path);n=min(len(f0),len(source_f0))
        mask=(f0[:n]>50)&(source_f0[:n]>50)
        a,b=f0[:n][mask],source_f0[:n][mask]
        correlation=float(np.corrcoef(a,b)[0,1]) if len(a)>2 and np.std(a)>1e-8 and np.std(b)>1e-8 else None
        log_correlation=float(np.corrcoef(np.log2(a),np.log2(b))[0,1]) if correlation is not None else None
        cents=1200*np.log2(a/b) if len(a) else np.array([])
        mix_path=dest/variant_filename(row['label'],mixed=True)
        mixed=mix_file(Path(run['source']),path,args.accompaniment,mix_path)
        result['variants'].append({'label':row['label'],'steps':row['steps'],'speaker_cosine_target':cosine(emb,ref_emb),
            'speaker_cosine_source':cosine(emb,source_emb),'f0_pearson':correlation,'log2_f0_pearson':log_correlation,'common_voiced_frames':int(mask.sum()),
            'common_voiced_coverage':float(mask.mean()) if n else 0.,
            'median_absolute_pitch_error_cents':float(np.median(np.abs(cents))) if len(a) else None,
            'octave_error_fraction_1200pm100_cents':float(np.mean(np.abs(np.abs(cents)-1200)<=100)) if len(a) else None,
            'dry_path':row['path'],**mixed,'converted_is_not_source_copy':hash_file(path)!=hash_file(Path(run['source']))})
    result['elapsed_seconds']=time.monotonic()-start
    with (dest/'evaluation.json').open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    write_page(dest,run,result)
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
