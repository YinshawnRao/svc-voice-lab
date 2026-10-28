#!/usr/bin/env python3
"""Five wide-span parameter versions for 萧亚轩 and 张韶涵, isolated from stage21."""
import datetime as dt
import html
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

from common import ROOT, local_env
from download import hash_file
from run_seven_experiment import copy_checked

OUT = ROOT / 'outputs/stage21-yigeren-param-elva-angela'
EVIDENCE = ROOT / 'reports/evidence/stage21-param'
SEED_PY = ROOT / '.envs/seed-vc/bin/python'
GENERATED = (
    ('s10', 10, 0.7),
    ('cfg00', 30, 0.0),
    ('cfg20', 30, 2.0),
    ('s100', 100, 0.7),
)
ORDER = ('s10', 'cfg00', 'base', 'cfg20', 's100')
LABELS = {
    's10': '10步 · CFG 0.7',
    'cfg00': '30步 · CFG 0',
    'base': '30步 · CFG 0.7 · 现成品',
    'cfg20': '30步 · CFG 2.0',
    's100': '100步 · CFG 0.7',
}
ARTISTS = (
    {'key': 'elva', 'artist': '萧亚轩', 'reference_song': '错的人',
     'clips': 'work/stage21-yigeren-elva-clips',
     'delivered_dry': 'outputs/stage21-seven-yigeren/萧亚轩_一个人生活_AI.wav',
     'delivered_mix': 'outputs/stage21-seven-yigeren/萧亚轩_一个人生活_mix_AI.wav'},
    {'key': 'angela', 'artist': '张韶涵', 'reference_song': '亲爱的那不是爱情',
     'clips': 'work/stage21-yigeren-angela-clips',
     'delivered_dry': 'outputs/stage21-seven-yigeren/张韶涵_一个人生活_AI.wav',
     'delivered_mix': 'outputs/stage21-seven-yigeren/张韶涵_一个人生活_mix_AI.wav'},
)


def wait_for_heavy():
    patterns = ('scripts/run_yigeren_experiment.py generate',
                'scripts/seed_vc_local.py', 'scripts/seed_vc_param_compare.py', 'scripts/run_stage2_poc.py',
                'scripts/evaluate_stage2.py', 'scripts/transcribe_local.py', '-m demucs')
    started = time.monotonic()
    while True:
        result = subprocess.run(['ps', '-axo', 'pid=,command='], check=True, capture_output=True, text=True)
        active = []
        for line in result.stdout.splitlines():
            fields = line.strip().split(None, 1)
            if len(fields) != 2 or int(fields[0]) == os.getpid():
                continue
            if any(pattern in fields[1] for pattern in patterns):
                active.append(int(fields[0]))
        if not active:
            return
        print('WAIT_HEAVY', active, round(time.monotonic() - started, 1), flush=True)
        if time.monotonic() - started > 3600:
            raise RuntimeError('Heavy process still running after one hour')
        time.sleep(30)


def logged(name, args, timeout):
    command = ['python3', 'scripts/run_logged.py', '--name', name, '--evidence-dir', EVIDENCE,
               '--timeout', str(timeout), '--', *map(str, args)]
    subprocess.run(command, cwd=ROOT, env=local_env(), check=True)


def prepare_inputs():
    shared = ROOT / 'work/stage21-yigeren-shared'
    dest = OUT / 'inputs'
    dest.mkdir(parents=True, exist_ok=True)
    for name in ('source_vocals.wav', 'source_accompaniment.wav', 'source_original.wav'):
        copy_checked(shared / name, dest / name)
    for artist in ARTISTS:
        reference = ROOT / artist['clips'] / 'target_reference_1.wav'
        copy_checked(reference, dest / f"{artist['artist']}_参考_{artist['reference_song']}.wav")


def add_baseline(artist, out):
    run_path = out / 'run.json'
    run = json.loads(run_path.read_text())
    if any(row['label'] == 'base' for row in run['variants']):
        return
    assert [row['label'] for row in run['variants']] == ['s10', 'cfg00', 'cfg20', 's100']
    dry = out / 'seed-vc_base_AI.wav'
    mix = out / 'seed-vc_base_mix_AI.wav'
    copy_checked(ROOT / artist['delivered_dry'], dry)
    copy_checked(ROOT / artist['delivered_mix'], mix)
    source = ROOT / artist['clips'] / 'source_vocals.wav'
    backing = ROOT / artist['clips'] / 'source_accompaniment.wav'
    peak = subprocess.check_output([str(ROOT / '.envs/demucs/bin/python'), '-c',
        'import soundfile,numpy,sys; w,_=soundfile.read(sys.argv[1],always_2d=True); print(float(numpy.max(numpy.abs(w))))',
        str(mix)], text=True, cwd=ROOT).strip()
    receipt = {
        'algorithm': 'rms_clamp05_2_peak098_v1',
        'inputs': {'source_sha256': hash_file(source), 'dry_sha256': hash_file(dry), 'backing_sha256': hash_file(backing)},
        'mix_path': str(mix.relative_to(ROOT)), 'mix_sha256': hash_file(mix), 'mix_peak': float(peak),
        'note': 'Byte copy of the stage21 delivered mix.',
    }
    (out / 'seed-vc_base_mix_AI.mix.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    run['variants'].insert(2, {
        'label': 'base', 'steps': 30, 'f0_condition': True, 'auto_f0_adjust': False, 'semitones': 0,
        'cfg_rate': 0.7, 'fp16': False, 'elapsed_seconds': None, 'includes_initial_model_load': False,
        'path': str(dry.relative_to(ROOT)), 'sha256': hash_file(dry),
        'origin': 'byte copy of stage21 deliverable', 'origin_path': artist['delivered_dry'],
    })
    run_path.write_text(json.dumps(run, ensure_ascii=False, indent=2) + '\n')


def generate(artist):
    out = OUT / 'runs' / artist['key']
    if (out / 'evaluation.json').exists():
        print('ALREADY_EVALUATED', artist['artist'], flush=True)
        return
    if not (out / 'run.json').exists():
        logged(f"stage21-param-{artist['key']}-convert", [
            SEED_PY, 'scripts/seed_vc_param_compare.py',
            '--source', ROOT / artist['clips'] / 'source_vocals.wav',
            '--target', ROOT / artist['clips'] / 'target_reference_1.wav',
            '--run-id', f"stage21-yigeren-param-{artist['key']}",
            '--output-dir', out, '--device', 'mps', '--seed', '20261016',
            *[arg for label, steps, cfg in GENERATED for arg in ('--variant', f'{label}:{steps}:{cfg}')],
        ], 3600)
    add_baseline(artist, out)
    logged(f"stage21-param-{artist['key']}-evaluate", [
        SEED_PY, 'scripts/evaluate_stage2.py', '--run', out / 'run.json',
        '--accompaniment', ROOT / artist['clips'] / 'source_accompaniment.wav',
    ], 1200)
    print('ARTIST_COMPLETED', artist['artist'], 'PARAM_COMPARE', flush=True)


def publish_names():
    rows = []
    for artist in ARTISTS:
        evaluation = json.loads((OUT / 'runs' / artist['key'] / 'evaluation.json').read_text())
        by_label = {row['label']: row for row in evaluation['variants']}
        for label in ORDER:
            row = by_label[label]
            dry_name = f"{artist['artist']}_一个人生活_{label}_AI.wav"
            mix_name = f"{artist['artist']}_一个人生活_{label}_mix_AI.wav"
            copy_checked(ROOT / row['dry_path'], OUT / dry_name)
            copy_checked(ROOT / row['mix_path'], OUT / mix_name)
            rows.append({**artist, 'label': label, 'setting': LABELS[label], 'dry': dry_name, 'mix': mix_name,
                         'steps': row['steps'], 'speaker_cosine_target': row['speaker_cosine_target'],
                         'f0_pearson': row['f0_pearson'], 'common_voiced_coverage': row['common_voiced_coverage'],
                         'mix_peak': row.get('mix_peak'), 'vocal_rms_matching_gain': row.get('vocal_rms_matching_gain')})
    return rows


def write_page(rows):
    tracks, buttons = [], []
    for row in rows:
        for mode, filename, suffix in (('mix', row['mix'], 'AI 混音'), ('dry', row['dry'], 'AI 纯人声')):
            track_id = f"{row['key']}-{row['label']}-{mode}"
            tracks.append({'id': track_id, 'label': f"{row['artist']} · {row['setting']} · {suffix}",
                           'url': filename, 'reference': False})
            suffix = '混音' if mode == 'mix' else '纯人声'
            buttons.append(f'<button data-track="{track_id}">{html.escape(row["artist"])} · {html.escape(row["setting"])} · {suffix}</button>')
    for artist in ARTISTS:
        filename = f"inputs/{artist['artist']}_参考_{artist['reference_song']}.wav"
        track_id = artist['key'] + '-reference'
        tracks.append({'id': track_id, 'label': f"{artist['artist']} · 参考《{artist['reference_song']}》",
                       'url': filename, 'reference': True})
        buttons.append(f'<button data-track="{track_id}">{html.escape(artist["artist"])}参考</button>')
    tracks.extend([
        {'id': 'original', 'label': '林凡 · 原曲片段', 'url': 'inputs/source_original.wav', 'reference': False},
        {'id': 'source', 'label': '林凡 · 分离人声', 'url': 'inputs/source_vocals.wav', 'reference': False},
    ])
    buttons.append('<button data-track="original">原曲片段</button><button data-track="source">源人声</button>')
    document = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>一个人生活 · 参数对照</title><style>body{font:16px/1.6 system-ui,sans-serif;color:#172033;background:#f3f5f8;max-width:1040px;margin:40px auto;padding:0 24px}h1{margin-bottom:4px}p{color:#536077}section{background:white;padding:24px;border-radius:16px;margin:24px 0}audio{width:100%}button{border:1px solid #d0d7e2;border-radius:8px;background:#fff;padding:8px 12px;margin:3px;cursor:pointer}button.active{background:#2345bb;color:white}small{color:#657184}</style>
<h1>《一个人生活》· 萧亚轩 / 张韶涵参数对照</h1>
<p>同一段 33.0 秒副歌。切换版本会留在当前进度。现成品是 stage21 的 30 步、CFG 0.7，其余每次只改步数或 CFG。参考人声从头播放。</p>
<section><h2 id="now">请选择版本</h2><audio id="player" controls preload="metadata"></audio><p id="error" role="status"></p>BUTTONS<button id="restart">从头播放</button></section>
<small>本地参数对照。F0 开启，自动移调关闭，0 半音，FP32，种子 20261016。技术测量不代表听感结论。</small>
<script>const tracks=TRACKS;
const player=document.getElementById('player'),now=document.getElementById('now'),error=document.getElementById('error');let current=null,chorusPosition=0,request=0;
function choose(id,fromStart=false){const track=tracks.find(t=>t.id===id);if(!track)return;if(current&&!current.reference)chorusPosition=player.currentTime||0;if(fromStart)chorusPosition=0;player.pause();const position=track.reference?0:chorusPosition;current=track;const ticket=++request;now.textContent=track.label;error.textContent='';document.querySelectorAll('[data-track]').forEach(b=>b.classList.toggle('active',b.dataset.track===id));player.onloadedmetadata=()=>{if(ticket!==request)return;player.currentTime=Math.min(position,Math.max(0,player.duration-.02));player.play().catch(()=>{error.textContent='请点击播放器中的播放按钮。'})};player.src=track.url;player.load()}
document.querySelectorAll('[data-track]').forEach(b=>b.addEventListener('click',()=>choose(b.dataset.track)));document.getElementById('restart').addEventListener('click',()=>choose(current?current.id:tracks[0].id,true));player.addEventListener('error',()=>{error.textContent='音频无法加载，请确认实验目录中的文件完整。'});
</script></html>'''
    (OUT / 'listen.html').write_text(document.replace('BUTTONS', ''.join(buttons)).replace('TRACKS', json.dumps(tracks, ensure_ascii=False)))


def write_report(rows):
    lines = ['# 萧亚轩、张韶涵《一个人生活》参数对照', '',
             f"日期：2026-10-19。目录：`outputs/stage21-yigeren-param-elva-angela/`。stage21 七人成品未改。", '',
             '同一段 78.20–111.20 秒副歌，同一 15 秒参考。固定项：F0 开、自动移调关、0 半音、FP32、种子 20261016。',
             '现成品是 stage21 干声和混音的逐字节复制。另外四版每次只改一个旋钮：10 步、CFG 0、CFG 2.0、100 步。',
             '步数跨度覆盖 README 的快速档到本地上限；CFG 从关闭拉到 2.0，高于默认 0.7。', '',
             '| 歌手 | 版本 | 音色余弦 | F0 相关 | 共同有声覆盖 | 混音峰值 |',
             '|---|---|---:|---:|---:|---:|']
    for row in rows:
        lines.append('| ' + ' | '.join(map(str, [
            row['artist'], row['setting'], row['speaker_cosine_target'], row['f0_pearson'],
            row['common_voiced_coverage'], row['mix_peak']])) + ' |')
    lines += ['', '试听页 `listen.html` 支持同一进度切换。没有人工听感结论。CER=N/A。',
              '干声峰值和满幅比例见各 run.json。混音不能消除干声里已经削平的采样。']
    (ROOT / 'reports/28_yigeren_param.md').write_text('\n'.join(lines) + '\n')
    note = '\n## 参数对照\n\n萧亚轩、张韶涵各 5 个版本在 `outputs/stage21-yigeren-param-elva-angela/`，说明见 [28_yigeren_param.md](28_yigeren_param.md)。stage21 原成品未改。\n'
    report = ROOT / 'reports/28_yigeren.md'
    text = report.read_text()
    if '## 参数对照' not in text:
        report.write_text(text + note)


def main():
    wait_for_heavy()
    assert not (OUT / 'listen.html').exists(), 'Parameter directory already published'
    prepare_inputs()
    started = time.monotonic()
    for artist in ARTISTS:
        generate(artist)
    rows = publish_names()
    write_page(rows)
    manifest = {'id': 'stage21-yigeren-param-elva-angela', 'created_at': dt.datetime.now(dt.timezone.utc).isoformat(),
                'source_song': '一个人生活', 'source_interval_seconds': [78.2, 111.2], 'duration_seconds': 33.0,
                'held_fixed': {'f0_condition': True, 'auto_f0_adjust': False, 'semitones': 0, 'fp16': False, 'seed': 20261016},
                'versions': [{'label': label, 'setting': LABELS[label]} for label in ORDER],
                'elapsed_seconds': round(time.monotonic() - started, 3), 'rows': rows, 'human_audition': False}
    (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    write_report(rows)
    checked = subprocess.run(['node', 'scripts/check_group_player.cjs', str(OUT / 'listen.html')],
                             cwd=ROOT, check=True, capture_output=True, text=True)
    print(checked.stdout, flush=True)
    print(OUT / 'listen.html', flush=True)


if __name__ == '__main__':
    main()
