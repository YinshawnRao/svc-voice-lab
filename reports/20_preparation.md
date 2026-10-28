# 七人《蒲公英的约定》素材准备

日期：2026-10-18。用户明确选择“完整一段副歌，延续最近几轮”；新建独立目录outputs/stage13-seven-pugongying/。默认七人及七首参考不变，实际15秒参考逐一核对歌曲、原区间与SHA256。

沿用Seed-VC commit 51383efd921027683c89e5348211d93ff12ac2a8，已复核本地锁定README歌声参数；30步、F0=true、autoF0=false、0半音、CFG0.7、FP32、seed20261016。保留源歌曲音高，不自行更换女调。没有新增模型或依赖，重模型串行离线执行。

已保护451个既有数据/输出/历史配置/全局规范文件，大小与SHA256清单位于reports/evidence/stage13/protected-before.json。README、总报告和状态修改前备份到work/stage13-before/。

来源优先[周杰伦官方MV](https://www.youtube.com/watch?v=VitJnr3IySc)，备用[公开MV存档](https://www.bilibili.com/video/BV1nb411L78Z/)仅探测。统一scripts/media.py doctor→probe→download，Cookie只读，下载前精确大小预检，记录台账和unknown许可证。

现有本地wrapper提供可选F0修复开关；本轮未启用，沿用原始源F0与既有0半音设置，不修改并行开发中的脚本。执行脚本SHA256另存reports/evidence/stage13/execution-scripts.json。

## 素材获取结果

官方YouTube源首次下载成功，耗时141.579秒；Bilibili备用仅探测，未下载，无失败重试。Opus流4,361,952 bytes，SHA256=7c9c3380a60b3f6f3b558e991867f981195c757c021decaa6a8e696fc5b29360。派生WAV47,573,866 bytes，48kHz双声道，247.780146秒，SHA256=2dc7499964ae365786d243d27f70769050f6d51e44710a76223569c87797a668；许可证unknown。原始流、WAV、回执和台账保留。下载阶段不使用GPU，显存N/A。

```sh
python3 scripts/media.py --cookies /Users/yinshawnrao/explorer/cc-media/all_cookies.txt doctor
python3 scripts/media.py --cookies /Users/yinshawnrao/explorer/cc-media/all_cookies.txt probe https://www.youtube.com/watch?v=VitJnr3IySc
python3 scripts/media.py --cookies /Users/yinshawnrao/explorer/cc-media/all_cookies.txt download https://www.youtube.com/watch?v=VitJnr3IySc --kind audio --run-id stage13-source-pugongying --role source --purpose 固定七人参考演唱蒲公英的约定完整副歌，源歌曲
.envs/demucs/bin/python scripts/run_pugongying_experiment.py prepare-source --song pugongying
```

## 副歌选择与预处理

本轮取第一段完整副歌85.2–116.2秒（1:25.2–1:56.2），31.0秒。人声能量在85.2–85.3秒为低谷、85.4秒起音，尾音在115.6秒降至RMS<0.001，保留到116.2秒。
50秒ASR细化窗早段时间戳约提前8秒，不采纳其首句时间。16秒窗口确认前一句延续至约85.24秒；从85.2秒开始的原曲30秒窗口识别出副歌首句，结合全曲初次ASR及能量边界确认范围。ASR存在错字与漏句，不当作歌词真值或人工听音，CER=N/A。

分离：UVR_Demucs_Model_1，MPS，two-stems vocals，shifts1，overlap0.25，segment7，float32。共同片段：44100Hz，源人声单声道、原曲/伴奏双声道，PCM16。七人逐字节共用同一组source，参考逐份复用固定15秒WAV；无需新增target预处理。

stage13-pugongying-separate：耗时17.984秒，子进程RSS峰值2493022208 bytes。
stage13-pugongying-asr：耗时18.856秒，子进程RSS峰值1112489984 bytes。
stage13-pugongying-asr-refine：耗时6.426秒，子进程RSS峰值715390976 bytes。
stage13-pugongying-asr-onset：耗时3.536秒，子进程RSS峰值572538880 bytes。
stage13-pugongying-asr-chorus-check：耗时4.075秒，子进程RSS峰值647987200 bytes。

RSS不是显存；分离MPS峰值未采样，N/A。ASR推理结束的MPS读数不是峰值。七人的原候选素材各不足10分钟，使用既有15秒零样本参考，不训练；未经人工确认的干净总时长=N/A。未额外去混响/和声，不声称纯净。

```sh
.envs/demucs/bin/python scripts/run_pugongying_experiment.py clips --song pugongying --start 85.2 --end 116.2
python3 scripts/run_pugongying_experiment.py generate --song pugongying
```
