# 七人《再见中国海》准备

本轮 stage24，明确保留七人，包括杨丞琳。默认阵容完整快照与七份 15 秒参考的歌手、歌名、原时间范围和 SHA256 已核验。每份参考不足 10 分钟，不训练；人工确认的干净总时长 N/A。

沿用已审计 Seed-VC V1 51383efd921027683c89e5348211d93ff12ac2a8，已重读本地官方 README 歌声模式及参数。30 步单版、F0=true、autoF0=false、0 半音、CFG0.7、FP32、seed20261016。沿用 MPS 与 CPU 适配，无新安装或权重下载。

媒体 doctor PASS；受限网络公开搜索 transport_unresolved，在授权网络上下文重复同一搜索后 PASS。源版本与副歌范围仍待核验。

已冻结 1247 个历史文件的大小与哈希，共享推理脚本保持不变。

## 环境复核

Seed-VC 与 Demucs 独立环境 pip check 均通过。MPS 本机 512x512 FP32 张量探测 finite=true；这仅是执行能力探测。结果见 reports/evidence/stage24/mps-probe-host.json。

## 来源尝试

YouTube 4 In Love - Topic 的 dktnIhzM0rU 公开探测受限；只读 Cookie 探测通过，下载阶段 HTTP 403、实际传输 0 字节，已保留回执并计费预算 4,792,860 字节。未将探测成功当作下载成功，转独立 B 站来源。

## 已下载源曲

来源：https://www.bilibili.com/video/BV1RXMe6VE9Y/，上传者 感动心灵音乐之声。Apple Music 曲目页 https://music.apple.com/us/song/1320812081 支持歌名与艺人映射；B 站上传不是官方认证母带。精确流大小 3,340,657 bytes，SHA256 709606764f8118cf9462724014a3ac336ab7c9d1c9d692a491a295a9f6946484，媒体许可证 unknown。派生 WAV 48000 Hz 双声道，300.906667 秒，SHA256 a39451aa64c9ab0025ae52bcfdfb0fdad4051ead53365ac64fd72fe378a2d7d1。原始流、完整 WAV、公开来源和回执均保留。

## 副歌范围

选定第一段完整副歌 69.90–120.80 秒，共 50.9 秒，包含连续的两个副歌乐段。短窗 ASR 定位首句约 69.72 秒、末句约 111–118 秒；人声 RMS 显示 69.9 秒为低能量谷、70.0 秒进入首句，末句持续尾音到约119.7秒，120.6秒后RMS低于0.0004，故保留到120.8秒。完整 ASR 在间奏出现幻觉重复，不用于末句截断。定位依据：work/stage24-chorus-boundaries/transcript.json 与 reports/evidence/stage24/chorus-boundary-rms.json；没有人工听感结论、没有校对歌词真值，CER=N/A。

Demucs 分离16.865秒，完整ASR外层32.680秒，短窗ASR模型耗时4.759秒。Demucs峰值统一内存未采样，N/A；RSS不等于显存。

## 技术冒烟

4秒、30步、孙燕姿固定15秒参考的MPS冒烟通过；外层耗时 35.572秒，输出实际 3.993832秒。SHA256 146a0a0a4fbd4a6755d11d63b11e1e8c1b8eee1549cc572b75f655b65017bab9。此处仅证明短片段执行成功，正式交付仍为七位50.9秒完整副歌。
