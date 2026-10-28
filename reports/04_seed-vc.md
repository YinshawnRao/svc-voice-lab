# 04 Seed-VC 本机歌声 PoC

最新新增：孙燕姿《我不难过》、萧亚轩《最熟悉的陌生人》、梁静茹《崇拜》、王心凌《变成陌生人》，四个独立目录的《听海》30秒A/B均完成，详见 [14_four_singers.md](14_four_singers.md)。前轮三位指定参考结果保留，见 [13_requested_references.md](13_requested_references.md)。以下保留历史阶段记录。

## 最新：完整歌曲 A/B 已完成

2026-10-16按用户要求生成完整《爱很简单》约4分22秒，两版都包含干声和伴奏混音。[完整试听页](../outputs/stage3-seed-full/listen.html)，[完整阶段报告](09_full_song.md)。参数沿用短版，仅30/50步不同；A约25.25分钟，B约29.78分钟。四个完整音频通过文件与时长检查，尚无完整听感认可。下文保留此前20秒阶段记录。

日期：2026-10-16。官方仓库 [Plachtaa/seed-vc](https://github.com/Plachtaa/seed-vc)，固定 commit `51383efd921027683c89e5348211d93ff12ac2a8`。状态：**POC_PASSED（20 秒，A/B）**。此前只有核心依赖的状态已更新；没有执行全曲或训练。

## 结果

Seed-VC V1、44.1kHz 歌声 F0 模式，在 M4 Pro/48GiB 上完成《爱很简单》60–80 秒转换；目标参考来自《晴天》182.730–196.017 秒的人声候选。零样本，无训练步数/训练成本。参考选择按长度、非静音率、削波率和 RMS，非人工鉴定，3 个候选与路径见 [数据报告](03_data.md)。

[本地试听页](../outputs/stage2-seed20/listen.html) 包含源人声、参考人声、A/B 干人声与混音。

| 版本 | 参数 | 转换耗时 | 干人声 | 混音 |
|---|---|---:|---|---|
| A | 30 diffusion steps | 115.778s，含初次加载 | [A_AI.wav](../outputs/stage2-seed20/seed-vc_A_AI.wav) | [A_mix_AI.wav](../outputs/stage2-seed20/seed-vc_A_mix_AI.wav) |
| B | 50 diffusion steps | 152.543s，模型已加载 | [B_AI.wav](../outputs/stage2-seed20/seed-vc_B_AI.wav) | [B_mix_AI.wav](../outputs/stage2-seed20/seed-vc_B_mix_AI.wav) |

其余一致：F0=True、auto-F0=False、移调=0、CFG=0.7、length=1.0、FP32、seed=20261016。同一次进程复用模型，随机种子每组重置；MPS 未开启强制确定性，固定种子不保证跨硬件逐位相同。计划中的 C=-2 半音本轮未运行。

## 真实环境与 Mac 适配

- Python 3.10.20 独立 `.envs/seed-vc/`；Torch/Torchaudio 2.5.1、Torchvision 0.20.1、NumPy 1.26.4、Librosa 0.10.2、Transformers 4.46.3、DAC 1.0.0。完整锁文件和实际安装版本已保存。
- 原 README 命令为 `pip install -r requirements-mac.txt`。这里安装固定 requirements 的 CLI 所需子集，排除未调用的 GUI/Gradio、FunASR/ModelScope；稳定配对 Torch 替代 nightly。没有宣称完整 Web UI 环境原样安装成功。
- 主权重与 RMVPE/CAMPPlus/Whisper/BigVGAN 共 9 文件、2,486,313,240 bytes，来自上游指定官方 HF 仓库，固定 revision、大小、SHA256、许可证逐项登记。CLI 依赖 99 文件、239,781,809 bytes（包含缓存命中，不能当作新增网络字节）。所有模型已预下载，运行拒绝 Python 网络连接并设置库离线标志。
- 扩散、Whisper FP32、CAMPPlus 使用 MPS；BigVGAN、RMVPE、mel/fbank 使用 CPU。FP32 时关闭 autocast，F0 数组转 float32。上游文件未修改，入口副本和本地配置写入每次 work/runtime。
- BigVGAN 原生 MPS 首次失败，固定 CPU 的第 1 种修复即通过；其余问题见 [修复记录](failures.md)。源码 checkpoint 的跳键警告已审计，没有遗漏有效学习参数。

## 复现与验证

```bash
python3 scripts/download.py config/seed-vc-cli-downloads.json
python3 scripts/download.py config/seed-vc-models.json
python3 scripts/bootstrap.py seed-vc-cli
python3 scripts/run_stage2_poc.py --run-id new-seed20 --device mps
```

需要固定源码和 `work/stage2-clips/` 的源人声、对应伴奏、目标参考；分离/切片和 fresh checkout 源码恢复见 [阶段报告](08_short_poc.md)。一键入口本轮实际执行的 run-id 是 `stage2-seed20`。不覆盖现有目录。

离线 `pip check`、实际导入、5 秒/2 步冒烟、20 秒 A/B、混音/指标全部通过。正式转换外层进程 271.656s，评测/混音外层进程 5.834s。采样 MPS allocated/driver 峰值分别 3.54/5.87GiB；进程 RSS 峰值 4.31GiB。不是 CUDA 独立显存，不可相加，采样可能漏过瞬时峰值。

## 效果和限制

自动指标：A/B 对目标参考的 CAMPPlus cosine 为 0.7937/0.8050，F0 Pearson 为 0.9978/0.9936；详细方法和源基线见 [评测](05_eval.md)。CAMPPlus 同时是条件编码器，不是独立身份验证。干声接近满幅比例为 0.0811%/0.0422%，混音最终峰值限制约 0.98，不能抹去声码器已发生的限幅。

本轮没有实际听到输出，不写音色“像不像”、咬字清晰度或高音破音的主观结论。没有校对歌词，CER=N/A。当前推荐把 A/30 步作为后续成本基线，同时保留 B/50 步试听；不能仅凭这点分数差断言 B 音质更好。目标候选只有约 3.68 分钟且洁净度未审核，全曲、不同参考和训练路线均仍待验证。
