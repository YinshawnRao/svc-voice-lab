# 《手心的太阳》两人先行实验准备

日期：2026-10-18。用户指定先由萧亚轩、王心凌演唱张韶涵《手心的太阳》，试听认可后再决定是否扩展到其他四位；本轮禁止自动补齐，原唱张韶涵不参与转换。

按照最新全局默认，制作一段完整副歌，Agent 自行定位、记录起止，不固定为30秒、不再询问时长。独立目录 `outputs/stage14-shouxin/`。参考复用固定15秒WAV：萧亚轩《错的人》189.094785–204.094785秒；王心凌《我会好好的》247.215374–262.215374秒，歌曲、区间、SHA256已与原manifest及全局阵容配置核对。

完整阵容快照位于 `reports/evidence/stage14/default-roster.json`；生成器仅授权elva、cyndi。此前528个数据、成品、历史配置和全局规范已记录大小与SHA256，清单见 `reports/evidence/stage14/protected-before.json`。README、状态、总报告原件保存在 `work/stage14-before/`，旧实验不覆盖。

2026-10-18复核本地锁定 Seed-VC README：commit `51383efd921027683c89e5348211d93ff12ac2a8`，歌声专用44.1kHz F0模型，推荐30–50步。沿用已验证30步单版、F0=true、autoF0=false、0半音、CFG0.7、FP32、seed20261016；不启用可选F0修复。未安装新依赖或模型。执行脚本哈希见 `reports/evidence/stage14/execution-scripts.json`。

公开来源为[福茂唱片官方MV](https://www.youtube.com/watch?v=LbDVqYaQboY)。搜索和探测均PASS，元数据308秒；选中Opus音轨format251，预检5,386,588字节。许可证unknown；官方上传不等于可发布授权。统一 `scripts/media.py` 和只读Cookie快照工作流，未获取其他歌手参考素材。

```sh
python3 scripts/media.py doctor
python3 scripts/media.py --cookies /Users/yinshawnrao/explorer/cc-media/all_cookies.txt search '張韶涵 手心的太陽 官方 MV' --platform youtube --limit 5
python3 scripts/media.py --cookies /Users/yinshawnrao/explorer/cc-media/all_cookies.txt probe 'https://www.youtube.com/watch?v=LbDVqYaQboY'
python3 scripts/media.py --cookies /Users/yinshawnrao/explorer/cc-media/all_cookies.txt download 'https://www.youtube.com/watch?v=LbDVqYaQboY' --kind audio --run-id stage14-source-shouxin --role source --purpose '萧亚轩与王心凌演唱手心的太阳完整副歌，先行两人实验源歌曲'
```

原始音频保留；只对新source执行UVR_Demucs_Model_1分离，two-stems vocals、MPS、shifts1、overlap0.25、segment7、float32。参考不重新分离或挑片。每人素材不足10分钟，本轮使用15秒零样本参考，不训练；未经人工确认的干净时长=N/A。未额外去混响/和声，不声称已无残留。各阶段耗时、资源见本轮证据与后续记录；RSS不是显存，未测MPS峰值写N/A。

## 来源访问问题

官方YouTube第一次下载返回HTTP 403，耗时5.531秒，实际传输0字节，保留失败回执和part文件；按预算规则保守计费5,386,588字节。此为媒体访问拒绝，不是模型不兼容；不更改Cookie、代理或TLS，转向独立公开来源。

备用页面BV1sb4y1R7pr（玉兔Chika）和BV1Bf4y177vw（舒言星）均探测成功；后者提供约191kbps AAC，相比前者约67kbps优先选择，大小仍须下载器HEAD确认。4K为页面标题，不作音质保证；上传者不是福茂官方，许可证unknown。

## 下载完成

备用源首次成功，耗时7.347秒；HEAD精确大小7,346,649 bytes，AAC format30280，SHA256=881795a90fa58e7f3916cc412902f6dd1f50e5784d07be77b03848c94e1ef52b。派生WAV59,035,726 bytes，48000Hz双声道，307.477333秒，SHA256=4aba0003d1d60cdc263e91def19bac9d3244767c326eab575c0e11e00ab4c2ac。原始流、派生文件和回执均保留；许可证unknown。下载阶段显存N/A。

```sh
python3 scripts/media.py --cookies /Users/yinshawnrao/explorer/cc-media/all_cookies.txt download https://www.bilibili.com/video/BV1Bf4y177vw/ --kind audio --run-id stage14-source-shouxin-bili --role source --purpose 萧亚轩与王心凌手心的太阳副歌实验
.envs/demucs/bin/python scripts/run_shouxin_experiment.py prepare-source --song shouxin
```

## 副歌定位与输入准备

选择第一段完整副歌109.4–144.9秒（1:49.4–2:24.9），35.5秒。50秒人声细化窗定位首句109.6秒；109.4秒RMS约0.0021，保留起音前余量。末句在人声细化窗结束约143.0秒，在原曲20秒独立窗口结束143.04秒；尾部保留到144.9秒低能量点（RMS约0.0122），保留144.5–144.7秒的衰减尾声。ASR有错字，时间仅辅助定位，不作为歌词真值或人工试听。

证据：work/stage14-shouxin-asr/、stage14-shouxin-asr-refine/、stage14-shouxin-asr-tail/；人声100毫秒RMS记录reports/evidence/stage14/shouxin-boundary-rms.json。每轮manifest保留起止、实际长度和定位依据。

共同片段44100Hz PCM16；源人声单声道，伴奏与原曲双声道。两人source逐字节一致；15秒参考核对歌曲、原时间范围、SHA256后复制，未重新选段。源完整人声与伴奏保留在work/stage14-shouxin-prep/。

separate：耗时16.889秒；子进程RSS峰值2,493,677,568 bytes。

asr：耗时23.957秒；子进程RSS峰值887,209,984 bytes。

asr-refine：耗时14.105秒；子进程RSS峰值776,503,296 bytes。

asr-tail：耗时6.782秒；子进程RSS峰值625,623,040 bytes。

RSS不是显存，分离与ASR的MPS峰值未采样，N/A。

```sh
.envs/demucs/bin/python scripts/run_shouxin_experiment.py clips --song shouxin --start 109.4 --end 144.9
python3 scripts/run_shouxin_experiment.py generate --song shouxin
```
