# 六人《勇气》准备

日期：2026-10-18。新建独立实验 stage20-yongqi，成品目录 outputs/stage20-six-yongqi/。按上一期做法排除原唱梁静茹，制作孙燕姿、蔡依林、萧亚轩、张韶涵、杨丞琳、王心凌。

完整默认阵容冻结于 reports/evidence/stage20/default-roster.json，SHA256 `c228d2daea315fa2b0509c6a9bd23e49c8796a38b2ab9fe9528ac3eb2f8f8f8a`。六份既有 15 秒参考已逐一核验歌手、歌曲、原区间与 SHA256，不换曲、不重新挑片。每人零样本参考，不训练；各参考候选不足 10 分钟，未经人工确认的干净总时长 N/A。公共参考原件在 work/stage9-* 与 work/stage11-cyndi-reference，本轮只复制，不改写。stage19 成品和配置列入保护快照。

复核本地官方 Seed-VC README 与锁定 commit `51383efd921027683c89e5348211d93ff12ac2a8`，README SHA256 `293507df928d542341a69b9c93e3b7344f7cc7abe73ac4b2c6395d86527a1ce4`。歌声模型为 V1 `seed-uvit-whisper-base`。README 写明歌唱转换使用 f0-condition、不使用 auto-f0-adjust、0 半音、CFG 0.7，扩散步数建议 30–50。本轮按用户默认取 30 步。README 的 fp16 默认在本机改为已审计的 FP32；MPS 跑扩散、Whisper、CAMPPlus，CPU 跑 BigVGAN、RMVPE 和频谱。没有新安装或新权重。显存峰值未测项目写 N/A；MPS 分配与驱动读数分开记录，不是独立显存。

开始时没有其他重模型在跑。897 个已完成成品、参考片段、历史配置和 data/source 全曲已记录大小与 SHA256，不含 .DS_Store。本轮新脚本在生成前冻结，共 14 份。

## 素材

统一媒体入口 doctor 通过，yt-dlp 2026.06.09，ffmpeg/ffprobe 8.1.1。Cookie 只经只读快照使用。

滚石官方 [勇氣 Official Music Video](https://www.youtube.com/watch?v=nDchQNPuA0k) 探测到 opus 精确 6,030,116 字节、358 秒，已下载并分离。上传者“滾石唱片 ROCK RECORDS”，许可证 unknown。派生 WAV SHA256 `8608ce6040c41de13b47793580797b015b3116ec43a3d2ef58cde2caeca36202`，68,774,986 字节。开头是电视剧对白，全曲人声 ASR 在两段副歌内部也出现对白，因此不用于转换。原文件、分离结果和 ASR 留在 `data/source/stage20-source-yongqi.wav`、`work/stage20-yongqi-mv-prep/`、`work/stage20-yongqi-asr-mv/`。

歌词版 [勇气 梁静茹 (歌词版)](https://www.youtube.com/watch?v=KfwJhh0MLLU) 探测到 opus 精确 4,095,267 字节。GET 返回 HTTP 403，传输 0 字节，目录 `work/acquisition/stage20-source-yongqi-studio/` 保留。该地址不再用同一方式重试。演唱会、合唱和官方现场候选未下载。

改用 [梁靜茹 - 勇氣](https://www.youtube.com/watch?v=BVpXUyXPKOg)。上传者 fishleunglike33 不是厂牌，许可证 unknown。opus 精确 4,118,739 字节，SHA256 `f524889cc4bfa0bb9af10e295d0807fb49676c0dc63636802269816af76f3126`；派生 WAV 46,136,086 字节，48 kHz 立体声，240.292 秒，SHA256 `5a7df748547b2360eb44a96e9dcadfcf101e6e52b6ab90a7451adb1f6710e3b4`。开头 23 秒是器乐，23.0 秒起是“终于做了这个决定”，不是现场口播。

## 副歌定位与预处理

选定第一段完整副歌 52.20–92.00 秒，共 39.8 秒。全曲人声 ASR 把前句“最怕你忽然说要放弃”收到 48.24 秒，副歌“爱真的需要勇气”从 52.24 秒起。48.25–52.35 秒人声 RMS 低于 0.001，52.40 秒抬到 0.0084、52.45 秒 0.0282，因此从 52.20 秒切入。46–58 秒短窗把副歌句标到 46–48 秒，该能量属于前句，不采用。

副歌含“爱真的需要勇气”“来面对流言蜚语”“只要你一个眼神肯定”“我的爱就有意义”“我们都需要勇气”“去相信会在一起”“人潮拥挤我能感觉你”“放在我手心里”“你的真心”。ASR 写成“流言飞雨”“人潮勇气”“你的珍惜”，这些是识别误差，不当歌词真值。末句短窗只收到这一句并标到 89.0 秒；89.45 秒后 RMS 低于 0.001，下一句“终于做了这个决定”在 100.05 秒起音。收在 92.00 秒，保留尾音，不带入下一句。没有按 30 秒硬截。非人工听音，CER=N/A。

分离使用 UVR_Demucs_Model_1，MPS，two-stems vocals、shifts 1、overlap 0.25、segment 7、float32。正式源分离 17.215 秒，全曲人声 ASR 22.983 秒。被放弃的官方 MV 分离 23.332 秒、ASR 23.399 秒。分离 MPS 峰值未采样，记 N/A；日志里的 RSS 不是显存。

4 秒 30 步 MPS 技术冒烟通过，外层耗时 40.821 秒。证据 smoke-validation.json。短片段不替代正式副歌。冒烟成品 SHA256 `b224d161e3c004409b171bdb6252f5600adedf16ee8a119803ee3987bb7e4e96`，时长约 3.994 秒。系统 python 没有 numpy，冒烟推理完成后的时长核验改由 demucs 环境补记，没有重跑模型。

六人共用这一段。片段 44100 Hz PCM16，人声单声道，伴奏和原曲双声道。六份 target 是既有 15 秒参考的逐字节复制。
