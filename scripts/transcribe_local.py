#!/usr/bin/env python3
"""Locate phrases locally with audited Whisper. ASR timestamps are not verified lyrics."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time

from common import ROOT, local_env
from download import hash_file, records
from seed_vc_local import block_network


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--run-id', required=True)
    p.add_argument('--start', type=float, default=0)
    p.add_argument('--duration', type=float, required=True)
    p.add_argument('--device', choices=['cpu', 'mps'], default='mps')
    args = p.parse_args()
    source = args.input.resolve()
    if not source.is_relative_to(ROOT) or not source.is_file():
        raise SystemExit('Local repository audio required')
    if not args.run_id.replace('-', '').replace('_', '').isalnum() or args.start < 0 or args.duration <= 0:
        raise SystemExit('Invalid run or interval')
    os.environ.update(local_env())
    approved = {r['dest']: r for r in records() if r['status'] == 'DOWNLOADED'}
    artifacts = []
    for name in ('seed-vc-models.json', 'whisper-asr-files.json'):
        for item in json.loads((ROOT / 'config' / name).read_text()):
            if not item['dest'].startswith('models/whisper-small/'):
                continue
            path = ROOT / item['dest']
            row = approved.get(item['dest'])
            if not row or path.stat().st_size != item['size_bytes'] or hash_file(path) != row['sha256']:
                raise SystemExit('Unverified Whisper file: ' + item['dest'])
            artifacts.append({'path': item['dest'], 'sha256': row['sha256']})
    block_network()
    import numpy as np
    import soundfile as sf
    import torch
    from transformers import WhisperProcessor, WhisperForConditionalGeneration, pipeline
    torch.set_num_threads(4)
    dest = ROOT / 'work' / args.run_id
    dest.mkdir(parents=True, exist_ok=False)
    command = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-n',
               '-ss', str(args.start), '-t', str(args.duration), '-i', str(source),
               '-ar', '16000', '-ac', '1', '-c:a', 'pcm_s16le', str(dest / 'input.wav')]
    subprocess.run(command, check=True, env=local_env())
    audio, sr = sf.read(dest / 'input.wav', dtype='float32')
    if not np.isfinite(audio).all() or len(audio) == 0:
        raise SystemExit('Invalid audio')
    started = time.monotonic()
    model_path = ROOT / 'models/whisper-small'
    processor = WhisperProcessor.from_pretrained(model_path, local_files_only=True)
    model = WhisperForConditionalGeneration.from_pretrained(model_path, local_files_only=True,
                                                            torch_dtype=torch.float32)
    asr = pipeline('automatic-speech-recognition', model=model, tokenizer=processor.tokenizer,
                   feature_extractor=processor.feature_extractor, device=args.device)
    result = asr({'array': audio, 'sampling_rate': sr}, chunk_length_s=30, stride_length_s=5,
                 return_timestamps=True, generate_kwargs={'language': 'zh', 'task': 'transcribe', 'do_sample': False})
    for row in result.get('chunks', []):
        row['source_timestamp'] = [None if t is None else round(args.start + t, 3) for t in row['timestamp']]
    result.update(source=str(source.relative_to(ROOT)), source_sha256=hash_file(source),
                  source_interval_seconds=[args.start, args.start + len(audio)/sr],
                  model_revision='973afd24965f72e36ca33b3055d56a652f456b4d', artifacts=artifacts,
                  device=args.device, elapsed_seconds=time.monotonic()-started, command=command,
                  limitations='Machine ASR for approximate phrase locations only; not human audition or lyrics truth',
                  sampled_mps_allocated_bytes=torch.mps.current_allocated_memory() if args.device == 'mps' else None,
                  sampled_mps_driver_bytes=torch.mps.driver_allocated_memory() if args.device == 'mps' else None)
    (dest / 'transcript.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'path': str(dest / 'transcript.json'), 'chunks': len(result.get('chunks', [])),
                      'elapsed_seconds': result['elapsed_seconds']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
