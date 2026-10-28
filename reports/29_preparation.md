# 六人《年轮说》准备

日期：2026-10-20。新建独立实验 stage22-nianlun，成品目录 outputs/stage22-six-nianlun/。原唱杨丞琳在四大三小七人内，按既有六人规则排除杨丞琳，制作孙燕姿、蔡依林、萧亚轩、梁静茹、张韶涵、王心凌。

完整默认阵容冻结于 reports/evidence/stage22/default-roster.json，SHA256 `c228d2daea315fa2b0509c6a9bd23e49c8796a38b2ab9fe9528ac3eb2f8f8f8a`。六份既有 15 秒参考已逐一核验歌手、歌曲、原区间与 SHA256，不换曲、不重新挑片。每人零样本参考，不训练；各参考候选不足 10 分钟，未经人工确认的干净总时长 N/A。公共参考原件在 work/stage9-* 与 work/stage11-cyndi-reference，本轮只复制，不改写。stage21 成品、参数对照、既有 data/source 全曲和历史配置列入保护快照，共 1114 个文件，不含 .DS_Store。快照取于本轮新源 WAV 和 stage22 配置写入之前。

复核本地官方 Seed-VC README 与锁定 commit `51383efd921027683c89e5348211d93ff12ac2a8`，README SHA256 `293507df928d542341a69b9c93e3b7344f7cc7abe73ac4b2c6395d86527a1ce4`。歌声模型为 V1 `seed-uvit-whisper-base`。README 写明歌唱转换使用 f0-condition、不使用 auto-f0-adjust、0 半音、CFG 0.7，扩散步数建议 30–50。本轮按用户默认取 30 步。README 的 fp16 默认在本机改为已审计的 FP32；MPS 跑扩散、Whisper、CAMPPlus，CPU 跑 BigVGAN、RMVPE 和频谱。没有新安装或新权重。显存峰值未测项目写 N/A；MPS 分配与驱动读数分开记录，不是独立显存。

开始时没有其他重模型在跑。本轮新脚本在生成前冻结，共 14 份，见 reports/evidence/stage22/execution-scripts.json。

## 素材

统一媒体入口 doctor 通过，yt-dlp 2026.06.09，ffmpeg/ffprobe 8.1.1。Cookie 只经只读快照使用。

杨丞琳官方频道 [年輪說 Official HD MV](https://www.youtube.com/watch?v=anurOHpo0aY) 探测到 opus 精确 4,690,490 字节、266 秒。Cookie GET 超时，传输 0 字节，目录 `work/acquisition/stage22-source-nianlun/` 保留。同一地址的公开模式在传输前返回 BLOCKED_ACCESS，没有建立目录。该地址不再用同一方式重试。

歌词上传 [年輪說 歌詞](https://www.youtube.com/watch?v=hC9w0QHBJT4) 探测到 opus 精确 4,556,147 字节。GET 返回 HTTP 403，传输 0 字节，目录 `work/acquisition/stage22-source-nianlun-lyric/` 保留。该地址不再用同一方式重试。演唱会、合唱、花絮、remix、伴奏和电视表演未下载。

正式源是 B 站 [楊丞琳 Rainie Yang - 年輪說 (Official HD MV)](https://www.bilibili.com/video/BV1js411t7N6/)。上传者“莫呼洛迦”，不是厂牌；页面标题写 Official，许可证 unknown。HEAD 后 m4a 精确 4,149,439 字节，SHA256 `9d3f2448aa3ad8ca282afe95f9afe5809062d15b0a4a96965d0d59387bdf2919`。派生 WAV `data/source/stage22-source-nianlun-bili.wav`，SHA256 `ce7cb342ef221550bfcb8a0bcb240b828a21484387bc107ff472113703fc55f7`，46,927,950 字节，44100 Hz 立体声，266.031 秒。下载耗时 2.482 秒。

全曲人声 ASR 对上的是这首歌的歌词，不是剧情对白。开头约 30 秒里有 28.4 秒人声 RMS 低于 0.001，全曲 ASR 在这一段写成重复的“看”，记为器乐上的识别，不当口播。文件末尾的“字幕by索兰娅”与 stage20、stage21 相同，记为 Whisper 片尾幻觉。

## 副歌定位与预处理

选定第一段完整副歌 78.20–138.60 秒，共 60.4 秒。公开歌词结构把“一是婴儿哭啼”到“细数自己”标成连续副歌；全曲 ASR 与 70–86 秒短窗把前句收到约 79.08 秒，副歌从这里起。76.20–78.35 秒人声 RMS 低于 0.001，78.55 秒抬到 0.0098、79.15 秒 0.0839，因此从 78.20 秒切入。

118–146 秒短窗把末句收到 129.0 秒，下一句“听”标在 139.0 秒。末句能量在 137.6 秒仍高于 0.02，138.75 秒落到 0.0004，下一句在 139.30 秒起音。收在 138.60 秒，保留尾音，不带入下一句。这段内部没有长于 0.8 秒的静音，没有按 30 秒硬截。ASR 把若干字写成别的词，这些是识别误差，不当歌词真值。非人工听音，CER=N/A。证据 reports/evidence/stage22/nianlun-boundary-rms.json。

分离使用 UVR_Demucs_Model_1，MPS，two-stems vocals、shifts 1、overlap 0.25、segment 7、float32。正式源分离 14.39 秒，全曲人声 ASR 外层 16.978 秒。人声干声 SHA256 `32aae4d06397280ac8d55d15bc774cbacd70313446aeb94ab848a4879c178a90`。分离 MPS 峰值未采样，记 N/A；日志里的 RSS 不是显存。

4 秒 30 步 MPS 技术冒烟通过，外层耗时 41.539 秒。证据 smoke-validation.json。短片段不替代正式副歌。冒烟成品 SHA256 `9a9b82ff99ca2fde3b175c3350cc9ab79e96d47741d054af61706fc269deb284`，时长约 3.994 秒，目标是孙燕姿的固定 15 秒参考。冒烟由 demucs 环境的 Python 启动，时长核验在同一次进程内完成。

六人共用这一段。片段 44100 Hz PCM16，2,663,640 帧，正好 60.4 秒。人声单声道，伴奏和原曲双声道。六份 target 是既有 15 秒参考的逐字节复制。
