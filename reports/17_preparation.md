# 两首歌曲先行试听准备

日期：2026-10-18。用户指定《心墙》《小幸运》，各先做张韶涵与萧亚轩；其余五位等待明确试听认可。沿用30步单版，每人保留混音与纯人声。

新目录：`outputs/stage10-xinqiang/`、`outputs/stage10-xiaoxingyun/`。配置：`config/experiments/stage10-{xinqiang,xiaoxingyun}.json`。旧data/outputs的196个文件已记录哈希，最终检查不变。

参考直接复用上轮：张韶涵《亲爱的那不是爱情》41.227755–56.227755秒；萧亚轩《错的人》189.094785–204.094785秒。均15秒，各自SHA在配置中锁定，两首新歌使用完全相同参考。

源曲版本按郭静《心墙》、田馥甄《小幸运》准备。搜索/探测/下载统一通过scripts/media.py，Cookie只读使用，不上传音频。网页搜索在2026-10-18查阅：[心墙官方MV](https://www.youtube.com/watch?v=VhCRokYVF1I)、[小幸运官方MV](https://www.youtube.com/watch?v=_sQSXwdtxlY)。

访问问题：Bilibili搜索API两次超时，改用公开网页搜索得到URL后probe；YouTube公开probe受限，已有只读Cookie探测成功。心墙YouTube媒体传输超时（0字节，预算保守计入声明大小），保留失败目录和台账；小幸运YouTube流传输缓慢，另探测Bilibili备用MV。具体逐项证据在reports/evidence/media-events/20261018*。不改Cookie、不改系统网络设置，不升级依赖。

代码仅沿用已验证本地环境；2026-10-18读取锁定Seed-VC README，commit 51383efd921027683c89e5348211d93ff12ac2a8。歌声F0启用、autoF0关闭、0半音、CFG0.7、FP32、随机种子20261016。新编排脚本限定两位歌手，生成时逐项验证，未授权其余五位。

CLI首次把--public放在doctor子命令后导致argparse错误，按help移到全局位置/使用全局--cookies后doctor成功；该命令未联网或下载，不涉及媒体错误重试。

## 素材已获取

两首YouTube媒体流最终均超时，改用已探测Bilibili MV后成功。实际来源：[心墙](https://www.bilibili.com/video/BV1cE411a7us/)（金曲奖吧官方频道）、[小幸运](https://www.bilibili.com/video/BV16v41157MC/)（墟桓）。名称中的“官方”或MV标题不作为上传者认证。下载流分别4,824,772和4,676,805 bytes，许可证unknown；原始流、派生WAV和receipt均保留在work/acquisition/stage10-source-*-bili/。无新增模型/依赖下载。

《心墙》首次副歌选65.3–96.7秒，共31.4秒。ASR在65秒识别副歌起点；200ms人声RMS显示65.2秒低能量间隙、65.4秒后起声，末句在95.6秒后衰减、96.6秒已近静音。边界证据：reports/evidence/stage10/xinqiang-boundary-rms.json。未以机器转写计算字错率。

《小幸运》首段完整副歌选98.2–152.0秒，共53.8秒。ASR副歌起点约98.6秒；200ms RMS显示98.2秒仍低能量、98.4秒进入起声；末句150.8秒开始衰减、151.8秒低于-68dB。保留上下两段及末句，不强切到30秒。边界证据：reports/evidence/stage10/xiaoxingyun-boundary-rms.json。两首生成时使用相同15秒参考，源区间在同曲两位歌手之间完全一致。

分离与ASR阶段完成，详细命令、实际耗时和进程RSS见reports/evidence/stage10/stage10-*-{separate,asr}.json。分离MPS峰值未测；进程RSS不是GPU显存，不能替代峰值报告。

| 源曲 | 阶段 | 耗时/s | 子进程RSS峰值/bytes |
|---|---|---:|---:|
| 心墙 | separate | 14.389 | 2202402816 |
| 心墙 | asr | 14.664 | 918339584 |
| 小幸运 | separate | 13.778 | 2342797312 |
| 小幸运 | asr | 12.392 | 896434176 |

## 编排验证

默认单版契约4项测试通过（tests/test_generation_defaults.py）。新分组播放器沿用同进度切换逻辑，支持当前两人及历史七人页面。生成入口已检查重复执行：对已完成《心墙》再次调用仅核验文件，不启动模型，也不改配置哈希、原始时间和耗时。最终另核对两首各仅angela/elva两个run目录，防止提前生成其余五位。
