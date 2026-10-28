#!/usr/bin/env python3
"""Run Seed-VC V1 singing variants with explicit step and CFG pairs.

Same audited local path as scripts/seed_vc_local.py. This file exists so a
parameter comparison can change CFG without editing the frozen stage21 wrapper.
"""
import argparse
import contextlib
import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import random
import resource
import shutil
import socket
import sys
import threading
import time
from types import SimpleNamespace

from common import ROOT, local_env, variant_filename
from download import hash_file, records


def verify_artifacts():
    approved = {row['dest']:row for row in records() if row['status']=='DOWNLOADED'}
    for item in json.loads((ROOT/'config/seed-vc-models.json').read_text()):
        path=ROOT/item['dest'];row=approved.get(item['dest'])
        if not row or not path.is_file() or path.stat().st_size!=item['size_bytes'] or hash_file(path)!=row.get('sha256'):
            raise RuntimeError('Missing or unverified local model: '+item['dest'])
    sources=[row for row in approved.values() if row.get('kind')=='source' and row['dest'].startswith('vendor/seed-vc/')]
    if not sources:raise RuntimeError('Missing audited source checkout')
    for row in sources:
        if hash_file(ROOT/row['dest'])!=row['sha256']:raise RuntimeError('Upstream source changed: '+row['dest'])


def block_network():
    original=socket.socket.connect
    def local_connect(sock,address):
        if sock.family in (socket.AF_INET,socket.AF_INET6):
            raise RuntimeError('Offline inference: internet socket denied')
        return original(sock,address)
    socket.socket.connect=local_connect
    def deny(*args,**kwargs):raise RuntimeError('Offline inference: internet connection denied')
    socket.create_connection=deny


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--target',type=Path,required=True)
    parser.add_argument('--run-id',required=True)
    parser.add_argument('--output-dir',type=Path,help='Optional new directory under outputs/, for grouped experiments')
    parser.add_argument('--variant',action='append',required=True,help='label:steps:cfg, for example s10:10:0.7')
    parser.add_argument('--device',choices=['cpu','mps'],default='mps')
    parser.add_argument('--seed',type=int,default=20261016)
    parser.add_argument('--f0-repair',type=Path,help='Optional source-hash-bound, explicitly audited local F0 repair JSON')
    args=parser.parse_args()
    if not args.run_id.replace('-','').replace('_','').isalnum():raise SystemExit('Invalid run-id')
    variants=[]
    for text in args.variant:
        label,step_text,cfg_text=text.split(':')
        step,cfg=int(step_text),float(cfg_text)
        if not label.isalnum() or label=='single':raise SystemExit('Invalid variant label: '+label)
        if not 1<=step<=100:raise SystemExit('steps must be 1-100')
        if not 0<=cfg<=3:raise SystemExit('cfg must be between 0 and 3')
        variants.append((label,step,cfg))
    if len({label for label,_,_ in variants})!=len(variants):raise SystemExit('Duplicate variant label')
    args.variants=variants
    output=(args.output_dir or ROOT/'outputs'/args.run_id).resolve()
    if not output.is_relative_to(ROOT/'outputs') or output==ROOT/'outputs':raise SystemExit('Output directory must be under outputs/')
    if output.exists():raise SystemExit('Choose a new output directory')
    for path in (args.source,args.target):
        if not path.resolve().is_relative_to(ROOT):raise SystemExit('Inputs must be local repository files')
    repair_spec=None
    if args.f0_repair:
        if not args.f0_repair.resolve().is_relative_to(ROOT):raise SystemExit('F0 repair must be a local repository file')
        from f0_repair import load_spec
        repair_spec=load_spec(args.f0_repair)
        if repair_spec['source_sha256']!=hash_file(args.source):raise SystemExit('F0 repair source hash mismatch')
    os.environ.update(local_env())
    os.environ.update(OMP_NUM_THREADS='4',MKL_NUM_THREADS='4',PYTORCH_ENABLE_MPS_FALLBACK='1')
    verify_artifacts()
    block_network()
    import numpy as np
    import soundfile as sf
    import torch
    import torchaudio
    import yaml
    torch.set_num_threads(4)
    if args.device=='mps' and not torch.backends.mps.is_available():raise RuntimeError('MPS unavailable in this execution context')
    output.mkdir(parents=True,exist_ok=False)
    runtime=ROOT/'work'/args.run_id/'runtime';runtime.mkdir(parents=True,exist_ok=False)
    upstream=ROOT/'vendor/seed-vc'
    sys.path.insert(0,str(upstream))
    text=(upstream/'inference.py').read_text()
    replacements={
        'torch_dtype=torch.float16':'torch_dtype=torch.float32',
        'with torch.autocast(device_type=device.type, dtype=torch.float16 if fp16 else torch.float32):':
        'with (torch.autocast(device_type=device.type, dtype=torch.float16) if fp16 else __import__("contextlib").nullcontext()):',
    }
    for old,new in replacements.items():
        if text.count(old)!=1:raise RuntimeError('Upstream adaptation anchor changed')
        text=text.replace(old,new)
    if repair_spec:
        anchor='F0_alt = f0_fn(converted_waves_16k[0], thred=0.03)'
        if text.count(anchor)!=1:raise RuntimeError('Upstream F0 adaptation anchor changed')
        text=text.replace(anchor,anchor+'\n        F0_alt = repair_source_f0(F0_alt)')
    runtime_script=runtime/'inference_local.py';runtime_script.write_text(text)
    spec=importlib.util.spec_from_file_location('seed_vc_stage2_inference',runtime_script)
    inference=importlib.util.module_from_spec(spec);spec.loader.exec_module(inference)
    if repair_spec:
        from f0_repair import apply_f0_repair
        def repair_source_f0(f0):
            repaired,evidence=apply_f0_repair(f0,repair_spec,hash_file(args.source))
            (output/'f0-repair-applied.json').write_text(json.dumps({'specification':repair_spec,'repairs':evidence},indent=2)+'\n')
            return repaired
        inference.repair_source_f0=repair_source_f0
    os.environ['HF_HUB_CACHE']=str(ROOT/'.cache/huggingface/hub')
    inference.device=torch.device(args.device)
    paths={('lj1995/VoiceConversionWebUI','rmvpe.pt'):ROOT/'models/rmvpe/rmvpe.pt',
           ('funasr/campplus','campplus_cn_common.bin'):ROOT/'models/campplus/campplus_cn_common.bin'}
    def local_model(repo_id,model_filename='pytorch_model.bin',config_filename=None):
        if config_filename is not None or (repo_id,model_filename) not in paths:
            raise RuntimeError('Unregistered model request blocked')
        return str(paths[(repo_id,model_filename)])
    inference.load_custom_model_from_hf=local_model
    # Upstream uses strict=False; fail if any active learned parameter is absent.
    # Old checkpoints also contain unused Wavenet keys and a generated position buffer.
    original_checkpoint=inference.load_checkpoint
    def audited_checkpoint(model,optimizer,path,*a,**kw):
        checkpoint=torch.load(path,map_location='cpu',weights_only=False)
        audit={}
        for key,module in model.items():
            stored={name.removeprefix('module.'):value for name,value in checkpoint['net'][key].items()}
            current=module.state_dict()
            missing=[name for name,param in module.named_parameters() if name not in stored or param.shape!=stored[name].shape]
            audit[key]={'missing_or_mismatched_learned_parameters':missing,
                        'unused_checkpoint_keys':sorted(set(stored)-set(current)),
                        'mismatched_buffers':{name:[list(value.shape),list(current[name].shape)] for name,value in stored.items() if name in current and value.shape!=current[name].shape}}
            if missing:raise RuntimeError('Active checkpoint parameter mismatch: '+repr(missing))
        (runtime/'checkpoint-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
        del checkpoint,stored
        return original_checkpoint(model,optimizer,path,*a,**kw)
    inference.load_checkpoint=audited_checkpoint
    config=yaml.safe_load((ROOT/'models/seed-vc/config_dit_mel_seed_uvit_whisper_base_f0_44k.yml').read_text())
    config['model_params']['speech_tokenizer']['name']=str(ROOT/'models/whisper-small')
    config['model_params']['vocoder']['name']=str(ROOT/'models/bigvgan')
    config_path=runtime/'local-config.yml';config_path.write_text(yaml.safe_dump(config))
    # Keep FFT/feature operations on CPU, return their results to the inference device.
    import modules.audio as audio_module
    original_mel=audio_module.mel_spectrogram
    def cpu_mel(wave,*a,**kw):return original_mel(wave.cpu(),*a,**kw).to(wave.device)
    audio_module.mel_spectrogram=cpu_mel
    original_fbank=torchaudio.compliance.kaldi.fbank
    def cpu_fbank(wave,*a,**kw):return original_fbank(wave.cpu(),*a,**kw).to(wave.device)
    torchaudio.compliance.kaldi.fbank=cpu_fbank
    import modules.rmvpe as rmvpe_module
    original_rmvpe=rmvpe_module.RMVPE
    class CpuRMVPE(original_rmvpe):
        def __init__(self,model_path,is_half,device=None,**kw):
            super().__init__(model_path,is_half=False,device=torch.device('cpu'),**kw)
        def infer_from_audio(self,*a,**kw):return super().infer_from_audio(*a,**kw).astype(np.float32)
    rmvpe_module.RMVPE=CpuRMVPE
    memory={'sampled_mps_allocated_peak_bytes':0,'sampled_mps_driver_peak_bytes':0}
    stop=threading.Event()
    def sample_memory():
        while not stop.wait(.1):
            if args.device=='mps':
                memory['sampled_mps_allocated_peak_bytes']=max(memory['sampled_mps_allocated_peak_bytes'],torch.mps.current_allocated_memory())
                memory['sampled_mps_driver_peak_bytes']=max(memory['sampled_mps_driver_peak_bytes'],torch.mps.driver_allocated_memory())
    monitor=threading.Thread(target=sample_memory,daemon=True);monitor.start()
    original_loader=inference.load_models
    loaded=[]
    progress={'variant':None,'chunks_completed':0}
    def cached_loader(options):
        if not loaded:
            modules=list(original_loader(options))
            vocoder=modules[3].cpu()
            def cpu_vocoder(mel):
                before=time.monotonic()
                wave=vocoder(mel.cpu()).to(mel.device)
                progress['chunks_completed']+=1
                row={**progress,'chunk_audio_seconds':wave.shape[-1]/44100,
                     'vocoder_seconds':time.monotonic()-before,'at':dt.datetime.now(dt.timezone.utc).isoformat()}
                with (output/'progress.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
                print('CHUNK_COMPLETED '+json.dumps(row),flush=True)
                return wave
            modules[3]=cpu_vocoder
            loaded.append(tuple(modules))
        return loaded[0]
    inference.load_models=cached_loader
    result={'started_at':dt.datetime.now(dt.timezone.utc).isoformat(),'device':args.device,'seed':args.seed,
            'source':str(args.source),'source_sha256':hash_file(args.source),'target':str(args.target),'target_sha256':hash_file(args.target),
            'upstream_commit':'51383efd921027683c89e5348211d93ff12ac2a8','network':'blocked Python internet sockets + offline library flags',
            'adaptations':['local model paths','FP32 Whisper','no FP32 autocast','CPU spectral features and RMVPE','CPU BigVGAN (MPS grouped conv_transpose1d limit)','float32 F0','reuse loaded models between variants'],
            'requested_variants':[{'label':label,'steps':step,'cfg_rate':cfg} for label,step,cfg in args.variants],'variants':[]}
    if repair_spec:
        result['source_f0_repair']={'path':str(args.f0_repair),'sha256':hash_file(args.f0_repair),'specification':repair_spec}
        result['adaptations'].append('explicit source-only F0 repair; reference F0 unchanged')
    started=time.monotonic()
    try:
        for index,(label,steps,cfg) in enumerate(args.variants):
            progress.update(variant=label,chunks_completed=0)
            random.seed(args.seed);np.random.seed(args.seed);torch.manual_seed(args.seed)
            if args.device=='mps':torch.mps.manual_seed(args.seed)
            raw=runtime/label
            options=SimpleNamespace(source=str(args.source.resolve()),target=str(args.target.resolve()),output=str(raw),
                checkpoint=str(ROOT/'models/seed-vc/DiT_seed_v2_uvit_whisper_base_f0_44k_bigvgan_pruned_ft_ema_v2.pth'),config=str(config_path),
                fp16=False,f0_condition=True,auto_f0_adjust=False,semi_tone_shift=0,diffusion_steps=steps,length_adjust=1.,inference_cfg_rate=cfg)
            before=time.monotonic();inference.main(options)
            if args.device=='mps':torch.mps.synchronize()
            elapsed=time.monotonic()-before
            paths=list(raw.glob('*.wav'))
            if len(paths)!=1:raise RuntimeError('Expected exactly one generated wave')
            wave,sr=sf.read(paths[0],always_2d=True)
            if not np.isfinite(wave).all() or np.max(np.abs(wave))<1e-5:raise RuntimeError('Invalid generated audio')
            target=output/variant_filename(label)
            with paths[0].open('rb') as source,target.open('xb') as dest:shutil.copyfileobj(source,dest)
            result['variants'].append({'label':label,'steps':steps,'f0_condition':True,'auto_f0_adjust':False,'semitones':0,'cfg_rate':cfg,
                'fp16':False,'elapsed_seconds':elapsed,'includes_initial_model_load':index==0,'path':str(target.relative_to(ROOT)),
                'duration':len(wave)/sr,'samplerate':sr,'sha256':hash_file(target),'peak':float(np.max(np.abs(wave))),
                'rms':float(np.sqrt(np.mean(wave**2))),'clipping_fraction':float(np.mean(np.abs(wave)>=.999))})
            print(json.dumps(result['variants'][-1]),flush=True)
            (output/'run.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    finally:
        stop.set();monitor.join(timeout=2)
        result.update(memory);result['elapsed_seconds']=time.monotonic()-started
        result['peak_process_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        (output/'run.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
