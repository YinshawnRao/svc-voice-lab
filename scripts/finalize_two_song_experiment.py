#!/usr/bin/env python3
"""Publish local navigation after validation; leave remaining singers awaiting feedback."""
import datetime as dt
import json
from pathlib import Path
import shutil
from zoneinfo import ZoneInfo
from common import ROOT
from run_seven_experiment import dump


def main():
    evidence=ROOT/'reports/evidence/stage10'
    validation=json.loads((evidence/'final-validation.json').read_text())
    assert validation['status']=='PASSED' and validation['remaining_five_generated'] is False
    configs=[json.loads((ROOT/f'config/experiments/stage10-{key}.json').read_text()) for key in ('xinqiang','xiaoxingyun')]
    assert all(c['status']=='POC_PASSED' for c in configs)
    backups=ROOT/'work/stage10-documents-before';backups.mkdir(exist_ok=False)
    for name in ['README.md','config/status.json','reports/06_summary.md']:
        p=backups/name;p.parent.mkdir(exist_ok=True,parents=True);shutil.copy2(ROOT/name,p)
    p=ROOT/'README.md';text=p.read_text()
    marker='**最新交付：七位歌手'
    assert marker in text
    text=text.replace(marker,'**前轮交付：七位歌手',1)
    line='**最新交付：《心墙》《小幸运》两人先行试听。** 两首各自独立目录，每首张韶涵、萧亚轩各一份30步混音和纯人声。'
    line+='[《心墙》31.4秒试听](outputs/stage10-xinqiang/listen.html) · [《小幸运》53.8秒试听](outputs/stage10-xiaoxingyun/listen.html)。'
    line+='两首统一参考张韶涵《亲爱的那不是爱情》、萧亚轩《错的人》，复用上轮同一15秒人声。其余五位明确等待用户试听认可后再做。'
    line+='[准备报告](reports/17_preparation.md) · [心墙报告](reports/17_xinqiang.md) · [小幸运报告](reports/17_xiaoxingyun.md)。\n\n'
    text=text.replace('**前轮交付：七位歌手',line+'**前轮交付：七位歌手',1);p.write_text(text)
    p=ROOT/'config/status.json';status=json.loads(p.read_text())
    status['stage9_deliverables']=status['deliverables']
    status['stage9_listening_page']=status['listening_page']
    status['stage9_experiment']=status['latest_experiment']
    status['previous_group_listening_pages']=status.get('listening_pages',{})
    status.update(as_of=dt.datetime.now(ZoneInfo('Asia/Shanghai')).date().isoformat(),
        scope='《心墙》《小幸运》各张韶涵/萧亚轩两人先行，30步单版；其余五位等用户试听认可',
        deliverables=[a['deliverables'][mode]['path'] for c in configs for a in c['artists'] for mode in ('mix','dry')],
        listening_page=configs[0]['output_directory']+'/listen.html',
        listening_pages={c['source_song']:c['output_directory']+'/listen.html' for c in configs},
        latest_experiment='config/experiments/stage10-xinqiang.json',
        latest_experiments=['config/experiments/'+c['id']+'.json' for c in configs],
        next=['等待用户试听《心墙》《小幸运》两人的效果；明确认可后再扩展其余五位'],
        manual_items=['用户试听音色、咬字、高音及混音效果；尚未人工质量验收', '如需CER，需独立校对歌词'])
    status['projects']['seed-vc']='POC_PASSED; stage10 2 songs x 2 singers, 30 steps; HUMAN_LISTENING_PENDING'
    dump(p,status)
    summary=['## 最新：两首歌，两位先行试听','',
        '《心墙》31.4秒与《小幸运》53.8秒均完成张韶涵/萧亚轩单版，合计4份混音+4份纯人声。',
        '[心墙试听](../outputs/stage10-xinqiang/listen.html) · [小幸运试听](../outputs/stage10-xiaoxingyun/listen.html)。',
        f"{validation['protected_files_unchanged']}个旧data/outputs文件大小与SHA256保持不变。技术校验通过，音色尚待用户试听。其余五位未生成，等待明确认可。",'']
    p=ROOT/'reports/06_summary.md';p.write_text('\n'.join(summary)+'\n'+p.read_text().replace('## 最新：七人','## 前轮：七人',1))
    extra=['','## 最终检查与空间快照','',
        f"校验：4份独立转换，8个最终音频；每首同源、同歌手跨歌同参考，{validation['protected_files_unchanged']}个既有文件不变。",
        '文件检查包括采样率、声道、时长、非静音、有限值、哈希、混音峰值；播放器8条本地音轨，并以Node mock DOM检查同进度切换、参考返回、从头播放。没有真实浏览器/人工听音验收。',
        f"空间快照 {validation['checked_at']}：work={validation['space_bytes']['work']:,} bytes；outputs={validation['space_bytes']['outputs']:,} bytes；可用磁盘={validation['disk_free_bytes']:,} bytes。未删除文件。",
        f"下载累计计入={validation['download_budget']['charged']:,} bytes，保留预留={validation['download_budget']['reserved']:,} bytes，低于30,000,000,000 bytes。",
        '失败下载记录保留，未新增模型/依赖；没有commit、push或发布。','',
        '| 歌手 | 模式 | 时长/s | 绝对峰值 | >=0.999样本比例 |','|---|---|---:|---:|---:|']
    for c in configs:
        table=[f"| {r['artist']} | {r['mode']} | {r['duration']:.6f} | {r['peak']:.6f} | {r['near_full_scale_fraction']:.6%} |" for r in validation['audio'] if r['song']==c['source_song'] and r['mode']!='reference']
        p=ROOT/f"reports/17_{c['id'].removeprefix('stage10-')}.md"
        p.write_text(p.read_text()+'\n'.join(extra+table)+ '\n\n干声保留模型原始输出；接近满幅的样本比例不证明主观破音。混音只做RMS匹配/峰值保护，不是LUFS统一。\n')
    for c in configs:
        print(c['source_song'],c['duration_seconds'],'秒：')
        for a in c['artists']:print(' ',a['artist'],ROOT/a['deliverables']['mix']['path'])
    print('4份演唱结果全部完成；30步单版。其余五位等待用户试听认可。')


if __name__=='__main__':main()
