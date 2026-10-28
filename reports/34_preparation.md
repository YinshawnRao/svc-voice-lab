# 六人《寓言》准备（stage27）

2026-10-28。用户请求“开启一轮新的试验，让四大三小的6个人演唱张韶涵的寓言”。原唱张韶涵在默认七人内，按既有六人规则排除。本轮为孙燕姿、蔡依林、萧亚轩、梁静茹、杨丞琳、王心凌。成品目录 `outputs/stage27-six-yuyan/`。

## 环境与方法

本次重读本地锁定 Seed-VC README 的歌声转换参数。沿用已审计 commit `51383efd921027683c89e5348211d93ff12ac2a8` 与独立 `.envs/seed-vc/`，没有新安装或权重下载。README 写明唱歌使用 f0-condition、diffusion steps 建议 30–50、inference-cfg-rate 0.7、auto-f0-adjust 关闭、semi-tone-shift 0。本轮 30 步单版，F0=true，autoF0=false，0 半音，CFG 0.7，FP32，seed 20261016。官方示例的 fp16 默认为 true；本机继续使用已有适配：MPS 扩散/Whisper/音色编码，CPU BigVGAN/RMVPE/频谱，FP32。

开始时没有其他重模型进程。`.envs/seed-vc` 的 512×512 FP32 MPS 探测 finite=true，耗时 0.11 秒。这只证明张量执行，不是歌声结果。证据 `reports/evidence/stage27/mps-probe.json`。

默认阵容快照 `reports/evidence/stage27/default-roster.json`，SHA256 `c228d2daea315fa2b0509c6a9bd23e49c8796a38b2ab9fe9528ac3eb2f8f8f8a`。六份 15 秒参考已核验歌手、歌曲、原区间和 SHA256，不换曲、不重新挑片。每份参考不足 10 分钟；本轮零样本，不训练。人工确认的干净人声总时长 N/A。

初始冻结 5185 份已有文件、21,166,543,246 字节的大小与 SHA256，见 `reports/evidence/stage27/protected-before.json`。共享下载台账 `reports/downloads.jsonl`、`reports/downloads.md`、`reports/download-reservations.json` 不在这份快照里，因为本轮要追加媒体记录。14 份执行脚本另存在 `execution-scripts.json`，并与初始快照逐份一致。

## 音源

媒体 doctor PASS。yt-dlp 2026.06.09，ffmpeg/ffprobe 8.1.1。Cookie 通过只读快照守卫使用已授权的 cc-media jar，未改用户 jar。

福茂唱片官方 MV `https://www.youtube.com/watch?v=-4eJy_cpvoo` 探测 PASS：标题“張韶涵 Angela Zhang - 寓言 (官方版MV)”，上传者福茂唱片，时长 245 秒，opus 精确 4,185,374 字节。下载 HTTP 403，传输 0 字节。目录 `work/acquisition/stage27-source-yuyan/` 保留。该地址不再用同一方式重试。

张韶涵频道上的厂牌提供音源 `https://www.youtube.com/watch?v=87OewfCp3W4` 探测 PASS：标题“寓言”，时长 247 秒，opus 精确 4,152,069 字节。下载同样 HTTP 403，传输 0 字节。目录 `work/acquisition/stage27-source-yuyan-topic/` 保留。该地址不再用同一方式重试。

正式源是 B 站 `https://www.bilibili.com/video/BV1wH4y157yR/`。标题“张韶涵《寓言》百万豪装录音棚大声听【Hi-res】”，上传者 JLRS-LeoFM，不是厂牌。时长 247.800 秒，接近专辑曲长 4 分 7 秒。HEAD 后 m4a 精确 51,579,354 字节，SHA256 `e3bc76f8b8af920952211896a9c001a99c5fd040b9623b278a8c0956c79f0e99`。派生 WAV `data/source/stage27-source-yuyan-bili.wav`，SHA256 `3490cf7b77d8b22ba40b8eb098a19cd8971dd67cabaf1ffb6b2120bbd7970f7a`，47,577,678 字节，48000 Hz 立体声。下载耗时 7.941 秒。许可证 unknown。同长度的 MV 剪辑候选未下载。

## 分离与副歌

Demucs MPS 分离成功，外层耗时 18.885 秒。人声与伴奏均为 44100 Hz，247.800 秒；人声峰值 0.743。RSS 记录不等于显存，分离峰值统一内存 N/A。全曲 ASR 外层耗时 36.007 秒。开头约 10 秒人声能量极低，随后识别到副歌歌词；文件前段的重复句和片尾重复记为识别漂移，不当口播，也不当歌词真值。CER=N/A。

50–78 秒短窗把主歌尾句 “na” 标到 53.84 秒，副歌首句从 53.84 秒起，副歌尾部 “na” 到 73.04 秒，下一句从 73.04 秒起。53.70 秒起的短窗只识别副歌首句。73.04 秒起的短窗只识别下一句。入口收在 53.84 秒，结束收在 73.00 秒，留在下一句起音之前。这段内部低于 0.01 的能量最长约 0.1 秒，没有按 30 秒硬截。六人共用 53.84–73.00 秒，实际 19.16 秒。证据 `reports/evidence/stage27/yuyan-boundary-rms.json`。

## 技术冒烟

4 秒、30 步、孙燕姿固定 15 秒参考的 MPS 冒烟通过。外层耗时 38.628 秒。输出 3.993832 秒，SHA256 `a6e4c65c409a337d1831324d500d994223ee16447c22a0e4e2d0337657e05a9e`。这只证明短片段能跑。正式交付仍是六人同一段 19.16 秒副歌。

六人正式生成与评测批次耗时 890.846 秒。技术校验通过。试听入口与峰值见 34_yuyan.md。人工听感仍待用户试听。
