# 02 项目调研

查阅日期：2026-10-16（Asia/Shanghai）。本次从官方 GitHub 网页/固定 SHA 原始文件、releases、issues 获取；GitHub API 返回 403 后使用网页内嵌元数据，不用搜索引擎缓存星数当作当前精确值。完整快照见 `evidence/upstream-snapshot.json`。

最后更新时间使用默认分支 HEAD 的提交时间（原始时区），不混用网页活动时间；star 是本次网页快照。Release 栏为 releases 页面首个标签，空白写“未列出”，不推断为没有任何版本。代码许可证不自动适用于外部模型。

| 项目 | Stars | HEAD 日期 | Commit | 归档 | Release | 代码许可证 |
|---|---:|---|---|---|---|---|
| [seed-vc](https://github.com/Plachtaa/seed-vc) | 3,897 | 2025-04-20T13:27:04.000+08:00 | [51383efd921027683c89e5348211d93ff12ac2a8](https://github.com/Plachtaa/seed-vc/commit/51383efd921027683c89e5348211d93ff12ac2a8) | 是 | 未列出 | GPL-3.0 |
| [applio](https://github.com/IAHispano/Applio) | 3,837 | 2026-10-15T23:01:50.000+02:00 | [e95ec175db434011854efc3b1bd66088b4d1e379](https://github.com/IAHispano/Applio/commit/e95ec175db434011854efc3b1bd66088b4d1e379) | 否 | [3.6.6](https://github.com/IAHispano/Applio/releases/tag/3.6.6) | MIT + Terms of Use |
| [rvc](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI) | 38,761 | 2026-08-04T15:47:05.000+08:00 | [81eed5e8f68b6bed1789f682fe78cdd324495afc](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI/commit/81eed5e8f68b6bed1789f682fe78cdd324495afc) | 否 | [2.3.260718](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI/releases/tag/2.3.260718) | MIT |
| [so-vits-svc](https://github.com/svc-develop-team/so-vits-svc) | 28,074 | 2023-10-03T23:54:19.000+08:00 | [730930d337d171479eadf305f96cbed4bb393e77](https://github.com/svc-develop-team/so-vits-svc/commit/730930d337d171479eadf305f96cbed4bb393e77) | 是 | 未列出 | AGPL-3.0 |
| [so-vits-svc-fork](https://github.com/voicepaw/so-vits-svc-fork) | 9,333 | 2026-10-14T13:47:41.000Z | [6cf76556c8afc1ba0c9109ea289c8f34b2eb4519](https://github.com/voicepaw/so-vits-svc-fork/commit/6cf76556c8afc1ba0c9109ea289c8f34b2eb4519) | 否 | [v4.2.30](https://github.com/voicepaw/so-vits-svc-fork/releases/tag/v4.2.30) | MIT |
| [soulx-singer](https://github.com/Soul-AILab/SoulX-Singer) | 1,008 | 2026-05-29T11:46:12.000+08:00 | [81aeb3ae772c70093c3de74dc23c92d983801ae4](https://github.com/Soul-AILab/SoulX-Singer/commit/81aeb3ae772c70093c3de74dc23c92d983801ae4) | 否 | 未列出 | Apache-2.0 |
| [gpt-sovits](https://github.com/RVC-Boss/GPT-SoVITS) | 62,886 | 2026-10-09T00:27:04.000+08:00 | [1b47ca07ef43a284e0b8bd7f29d3e1e3ff76082a](https://github.com/RVC-Boss/GPT-SoVITS/commit/1b47ca07ef43a284e0b8bd7f29d3e1e3ff76082a) | 否 | [20250606v2pro](https://github.com/RVC-Boss/GPT-SoVITS/releases/tag/20250606v2pro) | MIT |
| [reflow-vae-svc](https://github.com/yxlllc/ReFlow-VAE-SVC) | 162 | 2025-02-06T19:50:21.000+08:00 | [0550d0efd84027e4547f698b49c58f19c52ab984](https://github.com/yxlllc/ReFlow-VAE-SVC/commit/0550d0efd84027e4547f698b49c58f19c52ab984) | 否 | 未列出 | MIT |
| [demucs](https://github.com/facebookresearch/demucs) | 10,388 | 2023-11-16T07:32:35.000-05:00 / 2023-11-16T13:32:35.000+01:00 | [e976d93ecc3865e5757426930257e200846a520a](https://github.com/facebookresearch/demucs/commit/e976d93ecc3865e5757426930257e200846a520a) | 是 | 未列出 | MIT |
| [applio-app](https://github.com/IAHispano/Applio-App) | 11 | 2026-10-15T23:01:57.000+02:00 | [5de02daa276c93e089f7aebdd292cd59edaab80f](https://github.com/IAHispano/Applio-App/commit/5de02daa276c93e089f7aebdd292cd59edaab80f) | 否 | [v0.2.9](https://github.com/IAHispano/Applio-App/releases/tag/v0.2.9) | MIT + Terms of Use |
# 路线、输入与本机匹配

以下最低显存未有明确上游数字的一律写“未明确”，不能把 48GB 统一内存换算为 CUDA 显存。当前未做任何模型推理速度/质量实测。

| 项目 | 路线 | 输入/素材量 | MIDI | 硬件与 M4 Pro 匹配判断 |
|---|---|---|---|---|
| Seed-VC | 零样本 SVC，支持微调；V1 44.1kHz F0 模型 | 源人声 + 1–30 秒目标参考；微调要求片段 1–30 秒 | 不需要 | README 明确支持 Mac M 系列/Python 3.10；最低内存未明确。首选短片段验证 |
| Applio | RVC 家族，目标歌手需训练和检索索引 | 干净目标人声 + 源人声；本实验以 ≥10 分钟为训练优先线，非宣称所有架构统一硬下限 | 不需要 | 有 Darwin 安装路径；训练/推理仍要分别验证 MPS。默认脚本会装 Homebrew/faiss，须改为环境内依赖 |
| RVC 原版 | 检索增强、训练型 SVC | README 推荐至少 10 分钟低噪素材 | 不需要 | 当前主分支 Python 3.12 x64、Windows/Linux；CPU 文件固定 torch 2.4.1+cpu 和国内镜像，无原样 macOS arm64 路线 |
| so-vits-svc | ContentVec/HuBERT + VITS，训练型 SVC | 单音色干净人声；README 建议 5–15 秒切片，未给本机最小总时长 | 不需要 | README 测试 Python 3.8.9；老依赖和 MPS double 算子风险，优先级低 |
| so-vits-svc-fork | 基于 4.0 系模型的训练型 SVC | 数据预处理/目标模型/源人声；不要误用不兼容的 4.1 模型 | 不需要 | README 建议 Python 3.11；称 MPS “probably supported”，GPU 推理至少 4GB，支持 CPU。HEAD 依赖已更新，仍须实测 |
| SoulX-Singer | 零样本 SVS，另有独立 SVC 路线 | SVS：参考歌声及歌词/音高或音符对齐 metadata；SVC：源/参考 wav 和 F0；参考最低秒数 README 未明确 | SVS 可用 F0 或音符；SVC 不需要 | Python 3.10；CLI 默认 CUDA。torch 2.2、torchcodec 0.10、sageattention/NeMo 等组合需单独解耦核验，不能声称现成 MPS 支持 |
| GPT-SoVITS | 零样本/少样本语音 TTS | 文本 + 约 5 秒参考；少样本约 1 分钟语音（README 功能说明） | 无旋律/MIDI 控制契约 | README 有 Apple Silicon 测试与 MPS/CPU 安装；同时提醒 Mac GPU 训练质量下降、暂用 CPU。适合作 TTS 旁支，不等同保旋律翻唱 |
| ReFlow-VAE-SVC | Rectified Flow + VAE，训练型 SVC | 目标训练集、源人声；常规模式需内容编码器，VAE sid→tid 模式依赖已训练说话人 | 不需要 | README 沿用 DDSP-SVC 准备；无本机 MPS/最小显存承诺，最近默认分支更新较早，备选 |
| Applio-App | Applio 桌面应用，复用 RVC 引擎 | 同 Applio；不是新的独立音质算法 | 不需要 | 近期发布活跃；开发依赖 Node 22+/pnpm 11/Python 3.12/FFmpeg，Install/Repair 会自动下载，需先审计依赖/模型流程 |
| Demucs | 人声/伴奏分离前处理，无音色克隆 | 用户原始混音 | 不需要 | CPU 可用；本机最终安装单独 torch/torchaudio 2.2.2 环境。MPS 模型算子尚未验证 |

## 影响尝试顺序的当前事实

1. **先 Demucs/UVR5 前处理，再 Seed-VC V1 F0。** Seed 的 `--f0-condition True` 才选择歌声模型，README 推荐 30–50 diffusion steps；`--auto-f0-adjust False`、`--length-adjust 1.0` 保留原旋律节奏。V2 主要新增音色/口音转换，不能因为版本号较新就默认更适合唱歌。[固定版本 README](https://github.com/Plachtaa/seed-vc/blob/51383efd921027683c89e5348211d93ff12ac2a8/README.md)
2. **Applio 第二。** 有 macOS 安装分支，但不能直接运行带 `brew install` 的脚本。当前 README 说转为安全/依赖维护；新发现的 Applio-App 活跃，但只作为后续界面选项，不重复计算成另一个模型分数。[安装脚本](https://github.com/IAHispano/Applio/blob/e95ec175db434011854efc3b1bd66088b4d1e379/run-install.sh)
3. **fork 第三，原版 RVC 第四，原版 so-vits-svc 第五。** fork 的 README 仍写 No Longer Maintained，当前 SHA/4.2.30 又有新维护活动；只据此说“有维护提交”，不宣称恢复全面积极开发。原版 RVC 新主分支平台契约变化大，不照抄旧 macOS 教程。so-vits-svc 已归档。
4. **SoulX 第六，ReFlow 第七。** SoulX 已于 2026-03-16 加入无需歌词/MIDI 的 SVC；优先评估这一条，不先做复杂 SVS 转录。HF 查询 `model-svc.pt=2,793,965,154 bytes`、SVS `model.pt=2,818,092,278 bytes`，各自小于 5GB；尚未把全部预处理权重计入预计总量，未下载。ReFlow 是额外候选，但没有证据称其近期活跃。[SoulX README](https://github.com/Soul-AILab/SoulX-Singer/blob/81aeb3ae772c70093c3de74dc23c92d983801ae4/README.md)
5. **GPT-SoVITS 只保留为 TTS/UVR 工具旁支。** 不制造与 SVC 同口径的唱歌输出，未发现可直接替代本任务 F0/旋律保持的 README 契约。[README](https://github.com/RVC-Boss/GPT-SoVITS/blob/1b47ca07ef43a284e0b8bd7f29d3e1e3ff76082a/README.md)

## issues 与兼容性证据

所有下述 issue 都是上游报告；本次没有素材，均未复现其音频现象。旧 issue 不自动说明当前版本仍有同一缺陷。

- Seed-VC [#210](https://github.com/Plachtaa/seed-vc/issues/210)：CPU 推理慢的报告，没有本机速度证据；README 还列出 Mac 实时 GUI 的 `_tkinter` 缺失。当前仅计划 CLI，避免把 GUI 缺 Tk 当 SVC 不可用。列表 [#218](https://github.com/Plachtaa/seed-vc/issues/218) 是 `dac.nn` 缺失线索，正文未用于确定修复。
- Applio：当前公开 issues 首屏仅见 [#1005 AMD 9070](https://github.com/IAHispano/Applio/issues/1005)，非本机硬件；本次未找到足以确认当前 Mac 歌声问题的正文，不能写“没有兼容问题”。安装脚本的 Homebrew 安装、取消 MPS watermark 上限属于已核对源码行为，本项目不执行这些全局安装/资源设置。
- RVC [#2864](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI/issues/2864)：报告索引 nprobe 问题造成检索静默失效、音频断续；后续检索率对照须验证索引实际生效，而非只记录 UI 数字。
- so-vits-svc [#170](https://github.com/svc-develop-team/so-vits-svc/issues/170)：Apple Silicon 上 float64/cumsum 与 MPS 不兼容，讨论过 float32 改法；不能直接把修改作为已验证方案。列表另有 NumPy 冲突、fairseq/pyworld 安装问题。
- fork [#1237](https://github.com/voicepaw/so-vits-svc-fork/issues/1237)：Mac MPS 训练 `view size ... stride` 报错；训练和推理支持必须拆开验证。
- SoulX [#13](https://github.com/Soul-AILab/SoulX-Singer/issues/13)：上游报告 HF Hub 版本、NeMo/依赖和 16GB GPU OOM，维护者承认跨环境覆盖不足。issues 首屏另有 [#41](https://github.com/Soul-AILab/SoulX-Singer/issues/41) LlamaConfig 参数不兼容、[#25](https://github.com/Soul-AILab/SoulX-Singer/issues/25) 短音频耗时问题，后两条仅作为后续排查线索。
- GPT-SoVITS [#2815](https://github.com/RVC-Boss/GPT-SoVITS/issues/2815)：自动安装缺 funasr 依赖；README 的 Mac GPU 训练质量提示与之分开记录。
- ReFlow [#9](https://github.com/yxlllc/ReFlow-VAE-SVC/issues/9)：报告输出音色/音高过尖或过低；需对照移调参数与源 F0，不能直接判断模型优劣。
- Demucs [#620](https://github.com/facebookresearch/demucs/issues/620)：issues 列表有离线模型使用需求；模型自动下载必须替换为已审计的本地 repo。归档 README 指向作者 [adefossez/demucs](https://github.com/adefossez/demucs)，并说明仅处理重要修复；本轮使用官方 PyPI 4.0.1，分发包 SHA256 单独记录。

## 下载和部署判断

- Seed 主 SVC 权重实际代码默认是 `_ft_ema_v2.pth`（820,865,494 bytes），而 README 模型表链接为 `_ft_ema.pth`。后续必须显式锁定选择，不能悄悄变换版本。
- `inference.py` 还自动访问 RMVPE、CAMPPlus、BigVGAN 和 Whisper。单独下载主权重不足以构成可离线运行的安装；需逐项建立 README→官方模型仓库证据链及许可证。尚未满足者不自动下载。
- Demucs 默认权重来自 `dl.fbaipublicfiles.com`，不是本次约定的 GitHub releases/官方 HF/PyPI/conda 下载入口；本轮保留环境安装，未扩大下载白名单。下一阶段优先核验 UVR5 README 指向的官方 HF 权重路径。
- 未安装其余完整模型环境的条目标为准备待办，不冒称已失败三次或硬件绝对不支持。没有训练步数、推理 RTF、显存峰值和主观质量的本机数据。

调研为交错执行：各仓库抓取时间见 metadata 的 checked_at；没有单独计时整个人工分析阶段，耗时 N/A；模型 GPU 占用 N/A。遗留：完整模型依赖/权重来源审计、MPS 端到端、真实素材与人类抽听。
