# 七人《一个人生活》准备

日期：2026-10-19。新建独立实验 stage21-yigeren，成品目录 outputs/stage21-seven-yigeren/。原唱林凡不在四大三小七人内，用户要求所有人演唱，因此孙燕姿、蔡依林、萧亚轩、梁静茹、张韶涵、杨丞琳、王心凌全部参与。

完整默认阵容冻结于 reports/evidence/stage21/default-roster.json，SHA256 `c228d2daea315fa2b0509c6a9bd23e49c8796a38b2ab9fe9528ac3eb2f8f8f8a`。七份既有 15 秒参考已逐一核验歌手、歌曲、原区间与 SHA256，不换曲、不重新挑片。每人零样本参考，不训练；各参考候选不足 10 分钟，未经人工确认的干净总时长 N/A。公共参考原件在 work/stage9-* 与 work/stage11-cyndi-reference，本轮只复制，不改写。stage19、stage20 成品和既有 data/source 全曲列入保护快照，共 968 个文件，不含 .DS_Store。快照取于本轮新源 WAV 和 stage21 配置写入之前。

复核本地官方 Seed-VC README 与锁定 commit `51383efd921027683c89e5348211d93ff12ac2a8`，README SHA256 `293507df928d542341a69b9c93e3b7344f7cc7abe73ac4b2c6395d86527a1ce4`。歌声模型为 V1 `seed-uvit-whisper-base`。README 写明歌唱转换使用 f0-condition、不使用 auto-f0-adjust、0 半音、CFG 0.7，扩散步数建议 30–50。本轮按用户默认取 30 步。README 的 fp16 默认在本机改为已审计的 FP32；MPS 跑扩散、Whisper、CAMPPlus，CPU 跑 BigVGAN、RMVPE 和频谱。没有新安装或新权重。显存峰值未测项目写 N/A；MPS 分配与驱动读数分开记录，不是独立显存。

开始时没有其他重模型在跑。

## 素材

统一媒体入口 doctor 通过，yt-dlp 2026.06.09，ffmpeg/ffprobe 8.1.1。Cookie 只经只读快照使用。

正式源是滚石官方 [一個人生活 Official Music Video](https://www.youtube.com/watch?v=hUJl1HwYIN8)。上传者“滾石唱片 ROCK RECORDS”，许可证 unknown。页面标题为“林凡 Freya Lim【一個人生活 Living alone】Official Music Video (2012幸福蛻變版)”。opus 精确 5,037,059 字节，SHA256 `dceb33a12d21ed819d8cc9144aca4654b06d24f4d7a3ae5c46bf0e8356913b71`。派生 WAV `data/source/stage21-source-yigeren.wav`，SHA256 `77a92c0fff80df3432305bb9362e0c11e4dcb619d0327ffe2e45130e4c30a3d2`，54,147,530 字节，48 kHz 立体声，282.018 秒。下载耗时 146.8 秒。

全曲人声 ASR 识别到的是歌词，不是剧情对白。约 14 秒前没有人声，第一句是主歌。文件末尾的“字幕by索兰娅”与 stage20 相同，记为 Whisper 片尾幻觉，不当成素材里的口播。139–189 秒全曲 ASR 写成一长串“啊”，但该段人声 RMS 仍然很高，189 秒后歌词又恢复；这段不在所选副歌内，不据此判定对白。

探测后未下载：MusicDelta 纯享 `wBfuoG12HCo`（263 秒，opus 精确 4,607,268 字节）、HXP 动态歌词 `psfbGIvdc-E`（265 秒，4,603,060 字节）、Timeless Music 歌词版 `rsiH3r7y7_c`（272 秒，4,639,074 字节）。未下载的还有翻唱 `bWJNMit0B-g`、132 秒片段 `uuVwqQzPWcY`、演唱会 `6tt1MfjPqCw`，以及同一支官方 MV 的英文字幕版 `508ype14fRo`。

## 副歌定位与预处理

选定第一段完整副歌 78.20–111.20 秒，共 33.0 秒。全曲人声 ASR 把前句“我現在有多寂寞”收到 78.76 秒，副歌“我想我可以習慣一個人生活”从 78.76 秒起。74–84 秒短窗只在 74–76 秒收到“我”，78.64 秒才是副歌句。76.80–78.20 秒人声 RMS 低于 0.001，78.40 秒抬到 0.0100、78.75 秒 0.1191，因此从 78.20 秒切入。

副歌六句是“我想我可以習慣一個人生活”“我想我可以假裝不再難過”“冰冷的夜 眼淚溫熱我”“我想我可以習慣一個人生活”“在記憶裡面擦去你的承諾”“愛情怎麼會是這個結果”。ASR 写成“不再耐煌”“冰涼的眼淚讓眼淚溫熱我”，这些是识别误差，不当歌词真值。

100–116 秒短窗把末句收到 111.96 秒，并把下一句“叶子在庄危”标在同一时刻。末句能量从 110.00 秒的 0.0181 落到 110.80 秒的 0.0003，111.80 秒前保持低于 0.001，下一句在 111.95 秒起音。收在 111.20 秒，保留尾音，不带入下一句。没有按 30 秒硬截。非人工听音，CER=N/A。

分离使用 UVR_Demucs_Model_1，MPS，two-stems vocals、shifts 1、overlap 0.25、segment 7、float32。正式源分离 14.74 秒，全曲人声 ASR 外层 33.515 秒。人声干声 SHA256 `e546fe264b9d2191ecfa98cf540f82e6026a0c325a137be730db6a6d5c9ec4c8`。分离 MPS 峰值未采样，记 N/A；日志里的 RSS 不是显存。

4 秒 30 步 MPS 技术冒烟通过，外层耗时 35.114 秒。证据 smoke-validation.json。短片段不替代正式副歌。冒烟成品 SHA256 `251687fd922259ee23687dabde0873967f0b41cd064fe1891581e29b860ca663`，时长约 3.994 秒，目标是孙燕姿的固定 15 秒参考。冒烟由 demucs 环境的 Python 启动，时长核验在同一次进程内完成。

七人共用这一段。片段 44100 Hz PCM16，1,455,300 帧，正好 33.0 秒。人声单声道，伴奏和原曲双声道。七份 target 是既有 15 秒参考的逐字节复制。
