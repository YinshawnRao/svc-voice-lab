# stage21 张韶涵混音替换

日期：2026-10-20；run-id：`stage21-angela-replacement-20261020T230206`。

用户指定本地训练版《一个人生活》，要求裁切后替换 stage21 张韶涵版本，并明确要求复制后处理、源文件不动。
输入是带伴奏的单声道混音；其同目录 run.log 第274–307行记录 RVC phase3 转换后与伴奏混合。
本次仅替换混音。旧版纯人声保留，试听页明确标为“旧版纯人声”，旧参考亦有标注。

- 源文件：`/Users/yinshawnrao/explorer/cc-voice/outputs/默认模型成品_phase3/一个人生活-林凡.wav`
- 处理副本：`work/stage21-angela-replacement-20261020T230206/input_copy.wav`
- 源文件 SHA256：`6601ca0455e60d4e292a1531af3e88addf87b8613a21027fd0883958f5e2be0f`
- stage21 原唱及其余六位的共同区间：78.2–111.2 秒，33 秒。
- 本次在副本中裁切：78.224217687–111.224217687 秒，33 秒。
- 原因：全曲三频带对数能量匹配识别到相同副歌，并估计训练版约晚 24.218 毫秒。
- 样本范围：[3449688, 4904988)，1455300 个样本。
- 结果：44.1kHz，16-bit PCM，保留输入单声道；不变速、不重采样、不调音量、不重新混音。
- 成品 PCM 与副本对应样本逐一相等。切段后的六个局部窗口残余偏移估计绝对值最大 1.905 毫秒。
- 成品峰值 0.731994629，无非有限值或满幅削波样本；以上是机器检测，不是人工听感验收。

成品：`outputs/stage21-seven-yigeren/张韶涵_一个人生活_mix_AI.wav`  
SHA256：`9d6e77eb8d60352d7b31df3aa9fba0688231c39a8420e8807ba312156f55778c`  
试听：`outputs/stage21-seven-yigeren/listen.html`

旧混音、旧试听页、旧 manifest/config 和旧报告备份于 `work/stage21-angela-replacement-20261020T230206/backup`。
`runs/angela/` 仍是原 Seed-VC 历史生成记录；其指标不适用于新的训练版混音。
配置与交付 manifest 同步记录了这次混音替换及旧记录，原参考配置和其他歌手不变。

证据：本 run 工作目录中的 `preflight.json`、`alignment-coarse.json`、`alignment-refined.json`、`cut-validation.json`、`audio-verification.json`、`final-validation.json`。
首次轻量分析发现 Demucs 环境未安装 SciPy，改用本仓库已安装 SciPy 的 Seed-VC 环境执行数字信号分析；未安装依赖、未运行歌声模型。
另一个 stage22 实验占用重模型，遵守串行规则，未启动本轮人声分离。
