"""Create an offline listening page for one result or an explicit comparison."""
import html
import json
import os
from pathlib import Path
from common import ROOT


def write_page(dest,run,evaluation):
    dest=Path(dest)
    inputs=Path(run['source']).parent/'manifest.json'
    manifest=json.loads(inputs.read_text()) if inputs.exists() else {}
    single=len(evaluation['variants'])==1
    full=manifest.get('scope','').startswith('full source')
    title=manifest.get('display_title') or ('完整歌曲 A/B 对比' if full else '歌声转换片段 A/B 对比')
    if single:title=title.replace('A/B 对比','试听').replace('A/B','试听')
    listening_note=('先连续听完整首，再回到有疑问的位置切换版本。两组保留完整歌曲时间轴。' if full
                    else '先连续听完整段，再回到有疑问的位置切换版本。两组使用同一段源歌曲时间轴。')
    reference_note=manifest.get('reference_note','本轮两版使用同一段目标参考音色。播放参考时会暂停主播放器。')
    if single:
        listening_note=listening_note.replace('两组','音轨')
        artist,song=manifest.get('target_artist'),manifest.get('target_song')
        origin=f'从{artist}《{song}》中分离出的' if artist and song else '选定的'
        reference_note=f'本次使用{origin}目标参考人声。播放参考时会暂停主播放器。'
        version_note='本次生成一个版本。可以在相同播放位置切换混音、原唱和纯人声，方便对照。'
    else:
        settings=' / '.join(f"{row['label']}：{row['steps']} 步" for row in evaluation['variants'])
        version_note=f'本次参数对照为{settings}。目标参考、原调和其他设置相同，更多步数不代表音色变化更强。点击版本按钮会保留播放位置，适合对照同一句。'
    def relative(path):
        resolved=Path(path).resolve()
        if not resolved.is_relative_to(ROOT) or not resolved.is_file():raise ValueError('Missing local listening file')
        return os.path.relpath(resolved,dest.resolve())
    tracks=[]
    for row in evaluation['variants']:
        tracks.append({'id':row['label'],'label':'AI 混音' if single else f"{row['label']} · {row['steps']} 步 · AI 混音",'url':relative(ROOT/row['mix_path'])})
    original=manifest.get('original_mix_path')
    if original:
        tracks.append({'id':'original','label':'原唱 · '+('完整原始音轨' if full else '同一片段'),'url':relative(original)})
    # Source vocals and converted vocals can also be switched on the same timeline.
    tracks.append({'id':'source','label':'源人声 · 无伴奏','url':relative(run['source'])})
    for row in evaluation['variants']:
        tracks.append({'id':row['label']+'-dry','label':'AI 纯人声' if single else f"{row['label']} · AI 纯人声",'url':relative(ROOT/row['dry_path'])})
    buttons=''.join(f'<button type="button" data-track="{html.escape(t["id"])}" aria-pressed="false">{html.escape(t["label"])}</button>' for t in tracks)
    links=''.join(f'<a href="{html.escape(t["url"])}" download>{html.escape(t["label"])}</a>' for t in tracks if t['id'] not in ['original','source'])
    payload=json.dumps(tracks,ensure_ascii=False).replace('<','\\u003c')
    page='''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title><style>
*{box-sizing:border-box}body{font:16px system-ui;line-height:1.7;margin:0;background:#f3f4f0;color:#202723}
main{max-width:960px;margin:48px auto;padding:0 22px}h1{font-size:clamp(25px,4vw,38px);line-height:1.3;margin:12px 0 18px}
.tag{font-size:13px;letter-spacing:.08em;color:#536759}.panel{background:#fff;border:1px solid #d7dfd6;border-radius:16px;padding:24px;margin:22px 0}
#tracks{display:flex;gap:10px;flex-wrap:wrap}button{font:inherit;border:1px solid #bac9bd;border-radius:8px;background:#fafcf9;padding:9px 14px;cursor:pointer}
button[aria-pressed=true]{background:#244c37;color:white;border-color:#244c37}button:focus-visible{outline:3px solid #d6902b;outline-offset:3px}
audio{width:100%;margin:12px 0}#now{font-weight:650;margin-top:20px}.muted{color:#607064;font-size:14px}#status{min-height:24px;font-size:14px}
.downloads{display:flex;gap:12px 22px;flex-wrap:wrap}a{color:#265c3c}details{margin-top:22px}summary{cursor:pointer;font-weight:600}
</style></head><body><main><div class="tag">本地个人试听 · AI 歌声转换</div><h1>__TITLE__</h1>
<p>__VERSION_NOTE__</p>
<section class="panel"><div id="tracks" role="group" aria-label="选择试听版本">__BUTTONS__</div>
<div id="now" aria-live="polite"></div><audio id="player" controls preload="metadata" src="__INITIAL__"></audio><div id="status" aria-live="polite"></div>
<p class="muted">__LISTENING_NOTE__ 纯人声末尾可能比混音短不足一个音频帧。原唱与转换版本的混音电平可能不同，请注意音量差异。</p></section>
<details><summary>目标音色参考</summary><p class="muted">__REFERENCE_NOTE__</p><audio id="reference" controls preload="none" src="__REFERENCE__"></audio></details>
<section class="panel"><h2>保存 WAV</h2><div class="downloads">__LINKS__</div><p class="muted">文件就在本机。没有外部播放器、上传或在线分析。</p></section>
</main><script>
const tracks=__TRACKS__;
const player=document.getElementById('player'), reference=document.getElementById('reference');
const buttons=[...document.querySelectorAll('[data-track]')], now=document.getElementById('now'), status=document.getElementById('status');
let active=tracks[0].id, request=0, switching=false, desiredTime=0, desiredPlaying=false;
function mark(track){now.textContent=track.label;buttons.forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.track===track.id)));}
mark(tracks[0]);
function choose(id){
  if(id===active)return;
  const track=tracks.find(t=>t.id===id);if(!track)return;
  if(!switching){desiredTime=player.currentTime||0;desiredPlaying=!player.paused;}
  const ticket=++request;switching=true;active=id;player.pause();reference.pause();mark(track);status.textContent='正在切换，保留当前播放位置…';
  player.addEventListener('loadedmetadata',()=>{
    if(ticket!==request)return;
    player.currentTime=Math.min(desiredTime,Number.isFinite(player.duration)?Math.max(0,player.duration-.01):desiredTime);
    switching=false;status.textContent='已切换到 '+track.label;
    if(desiredPlaying)player.play().catch(()=>{status.textContent='已定位，请点击播放继续。';});
  },{once:true});
  player.src=track.url;player.load();
}
buttons.forEach(button=>button.addEventListener('click',()=>choose(button.dataset.track)));
player.addEventListener('error',()=>{switching=false;status.textContent='本地文件加载失败，请使用下方 WAV 链接打开。';});
player.addEventListener('play',()=>reference.pause());reference.addEventListener('play',()=>player.pause());
</script></body></html>'''
    for key,value in {'TITLE':html.escape(title),'BUTTONS':buttons,'INITIAL':html.escape(tracks[0]['url']),
                      'REFERENCE':html.escape(relative(run['target'])),'LINKS':links,'TRACKS':payload,
                      'LISTENING_NOTE':html.escape(listening_note),'REFERENCE_NOTE':html.escape(reference_note),
                      'VERSION_NOTE':html.escape(version_note)}.items():
        page=page.replace('__'+key+'__',value)
    with (dest/'listen.html').open('x') as stream:stream.write(page)
