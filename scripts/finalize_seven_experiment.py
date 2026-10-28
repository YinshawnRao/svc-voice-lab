#!/usr/bin/env python3
"""Update repository handoff only after the grouped experiment passes validation."""
import json
import datetime as dt
from pathlib import Path
import shutil
from zoneinfo import ZoneInfo
from common import ROOT


def main():
    c=json.loads((ROOT/'config/experiments/seven-ruguoniyetingshuo.json').read_text())
    check=json.loads((ROOT/'reports/evidence/stage9/final-validation.json').read_text())
    assert c['status']=='POC_PASSED' and check['status']=='PASSED'
    backup=ROOT/'work/stage9-documentation-before';backup.mkdir(exist_ok=True)
    for name in ['README.md','config/status.json','reports/06_summary.md']:
        out=backup/name;out.parent.mkdir(parents=True,exist_ok=True)
        if not out.exists():shutil.copy2(ROOT/name,out)
    status_path=ROOT/'config/status.json';status=json.loads(status_path.read_text())
    status.setdefault('stage8_deliverables',status['deliverables'])
    completed_local=dt.datetime.fromisoformat(c['completed_at']).astimezone(ZoneInfo('Asia/Shanghai'))
    status.update(as_of=completed_local.date().isoformat(),scope='七位歌手《如果你也听说》33.3秒副歌，30步单版，全部成品同一新实验目录',
        deliverables=[a['deliverables'][mode]['path'] for a in c['artists'] for mode in ['mix','dry']],
        listening_page=c['output_directory']+'/listen.html',latest_experiment='config/experiments/seven-ruguoniyetingshuo.json',
        next=['用户试听七种音色及实际参考人声，再决定是否更换参考片段或扩大时长'],
        manual_items=['试听七位歌手的音色、咬字和高音；未做人工质量验收','如需CER，提供独立核对的歌词'])
    status['projects']['seed-vc']='POC_PASSED; 7 singers, one30-step version each, one shared experiment folder; HUMAN_LISTENING_PENDING'
    status_path.write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n')
    readme=ROOT/'README.md';text=readme.read_text()
    if '**最新交付：七位歌手《如果你也听说》' not in text:
        text=text.replace('**最新交付：四位新歌手','**历史交付：四位新歌手',1)
        anchor='**历史交付：四位新歌手'
        paragraph='**最新交付：七位歌手《如果你也听说》33.3秒副歌，30步单版。** [统一试听页](outputs/stage9-seven-ruguoniyetingshuo/listen.html) · [实验目录](outputs/stage9-seven-ruguoniyetingshuo/) · [本轮报告](reports/16_seven_ruguoniyetingshuo.md) · [素材准备](reports/16_seven_preparation.md)。七份混音和七份纯人声集中放在目录根部，以歌手名命名；可以同进度切换。参考歌：孙燕姿《我怀念的》、蔡依林《天空》、萧亚轩《错的人》、梁静茹《崇拜》、张韶涵《亲爱的那不是爱情》、杨丞琳《雨爱》、王心凌《变成陌生人》。本轮源区间为1:07.3–1:40.6；没有A/B分版。\n\n'
        assert anchor in text;text=text.replace(anchor,paragraph+anchor,1);readme.write_text(text)
    summary=ROOT/'reports/06_summary.md';text=summary.read_text()
    marker='## 最新：七人《如果你也听说》副歌'
    if marker not in text:
        text=marker+'\n\n七位歌手30步单版全部完成，每人33.3秒混音与纯人声，同目录 `outputs/stage9-seven-ruguoniyetingshuo/`；[统一试听](../outputs/stage9-seven-ruguoniyetingshuo/listen.html)、[报告](16_seven_ruguoniyetingshuo.md)。本轮115个既有数据/输出文件SHA256保持不变。音色/高音/咬字仍待用户试听。\n\n'+text
        summary.write_text(text)
    report=ROOT/'reports/16_seven_ruguoniyetingshuo.md';text=report.read_text();marker='## 最终交付校验与成本'
    if marker not in text:
        sizes=check['space_bytes'];budget=check['download_budget']
        extra=['',marker,'',f"完成时间：{completed_local.isoformat()}（Asia/Shanghai）；本轮从10月16日跨午夜执行到10月17日。",f"串行生成、评测及打包总耗时：{c['batch_elapsed_seconds']:.1f}秒（不含之前下载/分离/素材准备）。七人推理累计{sum(a['metrics']['inference_seconds'] for a in c['artists']):.1f}秒。",
            f"实际运行峰值：MPS分配最高{max(a['metrics']['mps_allocated_peak_gib'] for a in c['artists']):.3f}GiB，MPS驱动最高{max(a['metrics']['mps_driver_peak_gib'] for a in c['artists']):.3f}GiB；两种统计不相加，不是独立显存。",'',
            '14个根目录WAV哈希、时长、声道、采样率、有限数值与混音峰值通过；七个输出互不相同，七个参考分别对应指定歌曲，源片段完全一致。',
            '试听页23条本地音轨链接通过；Node模拟DOM验证同进度切换、参考切换后恢复、从头播放。此项不等于真实浏览器/人工试听验收。',
            f"{check['protected_files_unchanged']}个既有data/outputs文件大小和SHA256不变；没有删除文件。完整证据：`reports/evidence/stage9/final-validation.json`。",'',
            '| 歌手 | 纯人声峰值 | 接近满幅样本比例 | 混音峰值 |', '|---|---:|---:|---:|']
        for a in c['artists']:
            run=json.loads((ROOT/c['output_directory']/'runs'/a['key']/'run.json').read_text());r=run['variants'][0]
            mix=next(row for row in check['audio'] if row['artist']==a['artist'] and row['mode']=='mix')
            extra.append(f"| {a['artist']} | {r['peak']:.6f} | {r['clipping_fraction']:.6%} | {mix['peak']:.6f} |")
        extra+=['','接近满幅按绝对值≥0.999统计；数值提示不等于已听见破音。纯人声保持模型原输出，混音使用原流程RMS匹配（增益限制0.5–2）及0.98峰值上限，不额外做LUFS一致化。',
            '',f"校验时空间快照（{check['checked_at']}）：本实验{sizes['experiment']:,}字节；整个work/ {sizes['work']:,}字节；outputs/ {sizes['outputs']:,}字节；data/ {sizes['data']:,}字节；磁盘可用{sizes['disk_free']:,}字节。",
            f"下载预算累计计费{budget['charged_bytes']:,}字节，保守预留{budget['reserved_bytes']:,}字节，上限{budget['limit_bytes']:,}字节。预留来自之前中断任务，未清除。",
            '', '本轮故障：素材准备时旧雨爱元数据缺少时间段字段，一次修复成功；七个生成任务均成功。人工事项只有试听判断（与可选独立歌词核对），没有待补模型或素材。']
        report.write_text(text+'\n'.join(extra)+'\n')
    print('七位歌手全部完成：'+str(ROOT/c['output_directory']))
    print('统一试听：'+str(ROOT/c['output_directory']/'listen.html'))
    for a in c['artists']:print(a['artist']+': '+a['deliverables']['mix']['path'])


if __name__=='__main__':main()
