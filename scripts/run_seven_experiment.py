#!/usr/bin/env python3
"""Generate the seven configured singers serially into one experiment directory."""
import datetime as dt
import html
import json
from pathlib import Path
import shutil
import subprocess
import time
from common import ROOT, local_env
from download import hash_file

CONFIG=ROOT/'config/experiments/seven-ruguoniyetingshuo.json'
EVIDENCE=ROOT/'reports/evidence/stage9'


def dump(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def copy_checked(source,dest):
    if dest.exists():assert hash_file(source)==hash_file(dest),'Existing destination differs'
    else:
        with source.open('rb') as src,dest.open('xb') as out:shutil.copyfileobj(src,out)
    return {'path':str(dest.relative_to(ROOT)),'sha256':hash_file(dest),'size_bytes':dest.stat().st_size}


def page(c):
    dest=ROOT/c['output_directory'];tracks=[];rows=[]
    for a in c['artists']:
        if a['status']!='POC_PASSED':continue
        for mode,field in [('mix','mix'),('dry','dry'),('reference','reference')]:
            p=ROOT/a['deliverables'][field]['path']
            tracks.append({'id':a['key']+'-'+mode,'label':a['artist']+({'mix':' · AI 混音','dry':' · AI 纯人声','reference':' · 参考《'+a['reference_song']+'》'}[mode]),
                           'url':str(p.relative_to(dest)),'reference':mode=='reference'})
        rows.append('<tr><td><strong>'+html.escape(a['artist'])+'</strong></td><td>'+html.escape(a['reference_song'])+'</td><td>'+''.join(
            f'<button data-track="{a["key"]}-{mode}">{label}</button>' for mode,label in [('mix','AI 混音'),('dry','AI 纯人声'),('reference','参考人声')])+'</td><td>'+f'<a href="{html.escape(Path(a["deliverables"]["mix"]["path"]).name)}" download>下载混音</a></td></tr>')
    tracks.extend([{'id':'original','label':c['source_artist']+' · 原曲片段','url':'inputs/source_original.wav','reference':False},
                   {'id':'source','label':c['source_artist']+' · 分离人声','url':'inputs/source_vocals.wav','reference':False}])
    document='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>如果你也听说 · 七种音色</title><style>body{font:16px/1.6 system-ui,sans-serif;color:#172033;background:#f3f5f8;max-width:1040px;margin:40px auto;padding:0 24px}h1{margin-bottom:4px}p{color:#536077}section{background:white;padding:24px;border-radius:16px;margin:24px 0}audio{width:100%}table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:14px 10px;border-bottom:1px solid #e5e9ef}button{border:1px solid #d0d7e2;border-radius:8px;background:#fff;padding:8px 12px;margin:3px;cursor:pointer}button.active{background:#2345bb;color:white}a{color:#2345bb}small{color:#657184}@media(max-width:650px){td,th{padding:10px 4px}button{display:block}}</style>
<h1>《如果你也听说》· 七种音色</h1><p>同一段 DURATION 秒副歌。选择歌手可接着当前进度试听；参考人声从头播放，返回翻唱时恢复副歌进度。</p>
<section><h2 id="now">请选择歌手</h2><audio id="player" controls preload="metadata"></audio><p id="error" role="status"></p><button data-track="original">原唱片段</button><button data-track="source">源人声</button><button id="restart">从头播放</button></section>
<section><table><thead><tr><th>音色参考</th><th>参考歌曲</th><th>试听</th><th>文件</th></tr></thead><tbody>ROWS</tbody></table></section>
<small>本地 AI 歌声转换实验。七份结果均保留原唱音高与演唱节奏，参考片段均为 15 秒；音色相似程度请以实际试听为准。</small>
<script>const tracks=TRACKS;
const player=document.getElementById('player'),now=document.getElementById('now'),error=document.getElementById('error');let current=null,chorusPosition=0,request=0;
function choose(id,fromStart=false){const track=tracks.find(t=>t.id===id);if(!track)return;if(current&&!current.reference)chorusPosition=player.currentTime||0;if(fromStart)chorusPosition=0;player.pause();const position=track.reference?0:chorusPosition;current=track;const ticket=++request;now.textContent=track.label;error.textContent='';document.querySelectorAll('[data-track]').forEach(b=>b.classList.toggle('active',b.dataset.track===id));player.onloadedmetadata=()=>{if(ticket!==request)return;player.currentTime=Math.min(position,Math.max(0,player.duration-.02));player.play().catch(()=>{error.textContent='请点击播放器中的播放按钮。'})};player.src=track.url;player.load()}
document.querySelectorAll('[data-track]').forEach(b=>b.addEventListener('click',()=>choose(b.dataset.track)));document.getElementById('restart').addEventListener('click',()=>choose(current?current.id:tracks[0].id,true));player.addEventListener('error',()=>{error.textContent='音频无法加载，请确认实验目录中的文件完整。'});
</script></html>'''
    document=document.replace('如果你也听说',html.escape(c['source_song'])).replace('七种音色',f"{len(c['artists'])} 种音色").replace('七份结果',f"{len(c['artists'])} 份结果")
    (dest/'listen.html').write_text(document.replace('ROWS',''.join(rows)).replace('TRACKS',json.dumps(tracks,ensure_ascii=False)).replace('DURATION',str(c['duration_seconds'])))


def report(c):
    rows=['# 七人《如果你也听说》副歌实验','',f"状态：{c['status']}；本地查阅/执行日期：2026-10-16（跨午夜时以日志时间戳为准）。",'',
          '用户指定七首参考歌；每人单版30步，F0开启、自动F0调整关闭、0半音、CFG 0.7、FP32、种子20261016。',
          'Seed-VC commit：`51383efd921027683c89e5348211d93ff12ac2a8`。沿用已验证本地环境与模型，没有新下载权重。',
          'MPS运行扩散模型/Whisper/音色编码器，CPU运行BigVGAN/RMVPE/频谱操作；重模型串行执行。','',
          f"源：张惠妹《如果你也听说》，原素材区间 {c['source_start_seconds']}–{c['source_start_seconds']+c['duration_seconds']} 秒。副歌位置由离线Whisper辅助定位，非人工歌词审核。",
          f"源页面：{c['source_url']}；上传者见下载回执，标题中official不等于上传者获得官方认证。",'',
          '| 歌手 | 参考歌 | 原参考时间段/s | 状态 | 推理秒 | 音色余弦 | F0相关 | MPS分配峰值/GiB |',
          '|---|---|---|---|---:|---:|---:|---:|']
    for a in c['artists']:
        metrics=a.get('metrics',{});interval=a.get('reference_interval_seconds',[])
        rows.append('| '+' | '.join([a['artist'],a['reference_song'],str(interval),a['status'],
            str(metrics.get('inference_seconds','N/A')),str(metrics.get('speaker_cosine','N/A')),str(metrics.get('f0_pearson','N/A')),str(metrics.get('mps_allocated_peak_gib','N/A'))])+' |')
    rows+=['','所有成品在 `'+c['output_directory']+'/`；根目录每人一份混音和一份纯人声，`listen.html`支持同进度切换。',
        '每人的原始run/evaluation/progress/mix收据在同一实验目录的 `runs/<key>/`，用于复现与审计。',
        'CAMPPlus也用于生成条件，余弦并非独立音色准确率；F0分数仅对齐共同有声帧。CER=N/A，没有经独立核对的歌词。',
        '未进行人工听感验收；没有声称本人演唱。分离与自动切片无法保证无混响、和声或伴奏残留。',
        '每首参考仅提供一首歌，候选素材不足10分钟；本轮为零样本15秒参考，不训练歌手模型。','',
        '## 复现','',
        '```sh',
        '# 新参考分离（首次准备；已有目录会拒绝覆盖）',
        '.envs/demucs/bin/python scripts/prepare_seven_experiment.py separate --artist stefanie',
        '.envs/demucs/bin/python scripts/prepare_seven_experiment.py separate --artist elva',
        '.envs/demucs/bin/python scripts/prepare_seven_experiment.py separate --artist angela',
        '# config中的source_start_seconds由本轮ASR定位；生成共同片段并核对参考',
        '.envs/demucs/bin/python scripts/prepare_seven_experiment.py clips',
        '# 已完成成员会验证并跳过；失败产物保留，检查日志后另用新的run-id重试',
        'python3 scripts/run_seven_experiment.py','```','',
        '下载来源/大小/许可证：`reports/downloads.md`；素材回执：`work/acquisition/stage9-*/receipt.json`。',
        '具体命令、耗时、源输入/输出SHA256、峰值、校验：`reports/evidence/stage9/` 与本实验 `runs/`。']
    (ROOT/'reports/16_seven_ruguoniyetingshuo.md').write_text('\n'.join(rows)+'\n')


def main():
    c=json.loads(CONFIG.read_text());assert c['steps']==[30] and c['source_start_seconds'] is not None
    dest=ROOT/c['output_directory'];assert dest.resolve().is_relative_to(ROOT/'outputs')
    dest.mkdir(exist_ok=True);(dest/'inputs').mkdir(exist_ok=True)
    for name in ('source_original.wav','source_vocals.wav','source_accompaniment.wav'):
        copy_checked(ROOT/'work/stage9-shared-chorus'/name,dest/'inputs'/name)
    started=time.monotonic();c.setdefault('started_at',dt.datetime.now(dt.timezone.utc).isoformat())
    c['status']='RUNNING';dump(CONFIG,c);report(c)
    for a in c['artists']:
        if a['status']=='POC_PASSED':
            for row in a['deliverables'].values():assert hash_file(ROOT/row['path'])==row['sha256']
            continue
        out=dest/'runs'/a['key'];a['status']='RUNNING';dump(CONFIG,c)
        try:
            command=['python3','scripts/run_stage2_poc.py','--run-id',a['run_id'],'--clips',a['clips'],
                '--output-dir',str(out),'--evidence-dir',str(EVIDENCE),'--device','mps','--steps','30']
            with (ROOT/'logs'/f"{a['run_id']}-launch.log").open('x') as log:
                subprocess.run(command,cwd=ROOT,env=local_env(),stdout=log,stderr=subprocess.STDOUT,check=True)
            check=EVIDENCE/f"{a['key']}-validation.json"
            subprocess.run([str(ROOT/'.envs/demucs/bin/python'),'scripts/validate_full_song.py','--run',str(out/'run.json'),
                '--duration',str(c['duration_seconds']),'--evidence',str(check)],cwd=ROOT,env=local_env(),check=True)
            run=json.loads((out/'run.json').read_text());evaluation=json.loads((out/'evaluation.json').read_text())
            assert run['requested_steps']==[30] and run['target_sha256']==a['reference_sha256']
            a['deliverables']={}
            for mode,source,name in [('dry',out/'seed-vc_AI.wav',a['artist']+'_如果你也听说_AI.wav'),
                ('mix',out/'seed-vc_mix_AI.wav',a['artist']+'_如果你也听说_mix_AI.wav'),
                ('reference',ROOT/a['clips']/'target_reference_1.wav','inputs/'+a['artist']+'_参考_'+a['reference_song']+'.wav')]:
                a['deliverables'][mode]=copy_checked(source,dest/name)
            m=evaluation['variants'][0]
            a['metrics']={'inference_seconds':round(run['elapsed_seconds'],3),'speaker_cosine':round(m['speaker_cosine_target'],6),
                'f0_pearson':round(m['f0_pearson'],6),'common_voiced_coverage':m['common_voiced_coverage'],
                'mps_allocated_peak_gib':round(run['sampled_mps_allocated_peak_bytes']/2**30,3),
                'mps_driver_peak_gib':round(run['sampled_mps_driver_peak_bytes']/2**30,3),'CER':None}
            a['status']='POC_PASSED';a['human_audition']=False
        except Exception as exc:
            a.update(status='FAILED',error=f'{type(exc).__name__}: {exc}')
            print('FAILED '+a['artist']+' '+str(exc),flush=True)
        dump(CONFIG,c);dump(dest/'manifest.json',c);page(c);report(c)
        print('ARTIST_COMPLETED '+a['artist']+' '+a['status'],flush=True)
    c.update(status='POC_PASSED' if all(a['status']=='POC_PASSED' for a in c['artists']) else 'PARTIAL',
        completed_at=dt.datetime.now(dt.timezone.utc).isoformat(),batch_elapsed_seconds=time.monotonic()-started)
    dump(CONFIG,c);dump(dest/'manifest.json',c);page(c);report(c)


if __name__=='__main__':main()
