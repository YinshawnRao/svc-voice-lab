# 心墙/小幸运补齐五位：准备

日期：2026-10-18。用户已明确认可前轮张韶涵、萧亚轩的两首歌效果，并授权补齐孙燕姿《我怀念的》、蔡依林《天空》、梁静茹《崇拜》、王心凌《我会好好的》、杨丞琳《雨爱》。这不是对尚未生成的十份演唱的认可。

保留outputs/stage10-xinqiang/与outputs/stage10-xiaoxingyun/，每曲沿用原副歌31.4秒/53.8秒和原伴奏；原两位的四份演唱（八个音频文件）不重跑。最终各7位、各14个成品。阶段11配置单独存档，原阶段10配置/报告保留；仅更新两份根manifest与试听页，4个旧文件已按原路径备份到work/stage11-before/。保护清单含246个旧数据、输出和阶段10配置文件，后续验证SHA256。

孙燕姿/蔡依林/梁静茹/杨丞琳引用stage9相同15秒人声，原歌曲映射和哈希已锁定。王心凌新歌单独获取和分离，不能沿用旧《变成陌生人》参考。两首源歌曲对每位歌手使用逐字节相同参考。

Seed-VC锁定commit 51383efd921027683c89e5348211d93ff12ac2a8，已复核本地README；30步、F0=true、autoF0=false、0半音、CFG0.7、FP32、seed20261016。无新增模型或依赖，串行本地执行，未上传音频。

媒体获取：统一scripts/media.py doctor/search/probe/download，Cookie只读。候选BV1MQ9UBnEMc约2MB/327秒，估算码率偏低，仅探测；BV13NtS6cEiy为标题声称修复的FLAC封装约108MB，但下载前大小探测返回HTTP404，未开始传输；保留失败事件。BV15v8U6BEJo探测成功，约2.7MB/327秒作为备用。另一存档候选BV1xs411h7hK的probe未执行：自动权限审核在截止前未完成（超时，不是安全风险判定），没有反复重试，继续处理已获准候选。

完整事件见reports/evidence/media-events/20261018T0547*之后记录；不将MV标题中的官方/正版或FLAC封装当作许可证及原始母带质量证明。

实际采用[王心凌《我会好好的》MV](https://www.bilibili.com/video/BV15v8U6BEJo/)（上传者星辉音乐，非据标题认定官方）。AAC流2,692,726 bytes，原始时长327.808秒，48kHz双声道WAV；平均流码率约65.7kbps，是当前可获取的完整单人版本，音质有限。原始流/派生/receipt保留，许可证unknown。爱贝克思官方YouTube地址Gw4Q7-NBFWs探测成功，但媒体下载124.394秒超时、传输0字节，保守计入预算5,356,164 bytes；未重复死磕。

## 参考准备结果

王心凌候选人声总时长217.462秒（不足10分钟）；未经人工确认的干净时长=N/A。本轮零样本使用15秒，不做训练。
UVR_Demucs_Model_1，MPS，two-stems vocals，shifts1，overlap0.25，segment7，float32；静音阈值-40dB、持续0.4秒，切片2–15秒、44100Hz单声道。未额外去混响/和声，自动切片不证明没有伴奏残留。
选择片段原区间：[247.215374, 262.215374]；SHA256：c8462086f546e7c54a53b3514fa36de82786930db14cb5200e9c9f4683282fd5。
初次候选排序第一名长14.509秒，触发固定15秒约束；一次修复：在原排序中选最高分的完整15秒候选（原第二名），保留原选择文件，另写work/stage11-cyndi-reference/，不重跑分离。score为活动率减20倍满幅比例，RMS作同分排序；选中活动率1.0、满幅比例0。对应失败与修复日志均保留。

随机5个候选供抽听：
- `work/stage11-cyndi-slices/target-slices/00004_9ca4886316.wav`
- `work/stage11-cyndi-slices/target-slices/00017_9ca4886316.wav`
- `work/stage11-cyndi-slices/target-slices/00016_9ca4886316.wav`
- `work/stage11-cyndi-slices/target-slices/00021_9ca4886316.wav`
- `work/stage11-cyndi-slices/target-slices/00013_9ca4886316.wav`

separate：24.628秒；子进程RSS峰值2628124672 bytes；分离MPS峰值未测，RSS不等于显存。

slice：1.107秒；子进程RSS峰值47235072 bytes；分离MPS峰值未测，RSS不等于显存。

select：0.571秒；子进程RSS峰值168460288 bytes；分离MPS峰值未测，RSS不等于显存。

新参考离线Whisper-small转写完成，模型推理2.533秒；内容呈连续歌词而非明显对白，仅辅助筛选，不证明歌手身份/纯净度，不作为CER真值。证据work/stage11-cyndi-reference-asr/transcript.json。
