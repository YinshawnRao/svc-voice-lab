# 六人《只想爱你》准备

本轮使用 stage23-zhixiangaini；排除原唱杨丞琳，制作孙燕姿、蔡依林、萧亚轩、梁静茹、张韶涵、王心凌。完整默认阵容配置冻结于 reports/evidence/stage23/default-roster.json，六份固定 15 秒参考的歌手、歌名、原区间、SHA256 均已核验。每份参考不足 10 分钟，不训练，未经人工确认的干净总时长 N/A。历史音频、配置及参考共 1179 个文件纳入保护快照。

沿用本地 Seed-VC V1 51383efd921027683c89e5348211d93ff12ac2a8，已重读本地官方 README 的 SVC 用法和参数。30 步单版、F0=true、autoF0=false、0 半音、CFG0.7、FP32、seed20261016。沿用已审计的 CPU BigVGAN/RMVPE/频谱与 MPS 扩散/Whisper/CAMPPlus 适配。本轮没有安装依赖或下载新权重，pip check 通过，真实本机上下文 MPS 512x512 张量探测通过。共享脚本不修改；新批次脚本直接调用已校验推理和评测入口，省去重复 bootstrap。所有重模型串行并使用本地离线权重。

## 原唱来源

媒体 doctor 通过。YouTube 官方频道 https://www.youtube.com/watch?v=hpkBwizROaE 公开探测返回 BLOCKED_ACCESS。B 站公开搜索返回 nav -101；使用已有用户 Cookie 的只读快照后搜索通过。最终下载索尼音乐中国发布的 https://www.bilibili.com/video/BV1rJ411x7QG/ ，标题《只想爱你 - 杨丞琳》。许可证 unknown。HEAD 核验 m4a 精确 4,474,234 字节后下载，SHA256 e0f3f3cde15723b8cb316f65fbc09cee37919ced693fece6083dc1cb1e2324e9。派生 WAV 为 48000 Hz 立体声、269.482667 秒，SHA256 9f3aac610ea513c10004bf630011fbdebcc625100ffbde9e2b801108bb54c4ff。完整回执在 work/acquisition/stage23-source-zhixiangaini-bili/receipt.json；下载台账同步登记。没有下载现场、卡拉 OK、其他歌曲或 MV 合集。

副歌范围待离线 ASR 和能量边界定位。公开歌词结构用于识别重复段落：https://www.flmp3.com/song/16667.html ；不作为人工校对真值，CER=N/A。不保存全文歌词。

## 副歌与分离

选定 61.20–100.00 秒，共 38.8 秒，两个连续副歌乐段和末句尾音全部保留。54–74 秒短窗与 61.2 秒起的入口复核都识别到副歌首句；61.2–61.7 秒为低能量过渡，61.7 秒起人声增强。88–112 秒短窗把末句收在 99.44 秒，尾音 RMS 在 99.8 秒低于 0.001，因此保留到 100.0 秒。下一段主歌在间奏后约 112.5 秒开始。整曲 ASR 在 97.52–106 秒把副歌末句和下一主歌混写，按短窗与人声能量纠正，不把其歌词当真值。所有六人使用同一段，44100 Hz、1,711,080 帧；人声单声道，伴奏和原曲片段双声道。

分离使用 UVR_Demucs_Model_1，MPS，two-stems vocals、shifts1、overlap0.25、segment7、float32，14.372 秒。全曲 ASR 外层耗时 24.444 秒。分离峰值统一内存未采样，N/A；RSS 不作为显存。完整人声及伴奏保存在 work/stage23-zhixiangaini-prep/。边界证据在 reports/evidence/stage23/chorus-boundary-rms.json，三份短窗口识别在 work/stage23-chorus-*/。没有人工听音结论。

## 冒烟

4 秒、30 步、孙燕姿固定参考的本机 MPS 冒烟通过，外层耗时 37.467 秒。输出实际 3.993832 秒，SHA256 `5872d8fcb8557ffc4d83ac78c953652cc793fdf85edc204bb1d8aef0453aaccb`。这只是短片段技术检查；正式交付仍为六位完整 38.8 秒副歌。
