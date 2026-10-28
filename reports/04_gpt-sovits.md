# 04 gpt-sovits 准备状态

日期：2026-10-16。状态：`DEFERRED_TASK_MISMATCH`，另有共同阻塞 `BLOCKED_DATA`。

上游：[官方仓库](https://github.com/RVC-Boss/GPT-SoVITS)；查阅 SHA：`1b47ca07ef43a284e0b8bd7f29d3e1e3ff76082a`。固定版本文件见 `reports/evidence/gpt-sovits/`，跨项目事实/issue 链接见 [02_research.md](02_research.md)。

## 本轮做了什么

完成 README/许可证/提交/release/issues 调研和本机适配判断。**没有建立该项目的完整环境，没有训练或推理，也没有记录为安装失败三次。**

官方主要是语音 TTS，无经本次核实的保原歌 F0/旋律转换入口；作为附加 TTS/UVR5 工具研究，不与歌声 SVC 混算效果。

## 下一可执行步骤

参考语音+文本；只有后续明确找到歌声模式契约才安排唱歌 PoC。

完整安装必须先形成官方依赖/权重清单，分配 `.envs/gpt-sovits/`，经逐文件审计后下载；保留 README 原始命令及必要适配差异。当前不存在可诚实提供的一键 PoC 脚本。

命令：本轮仅 `python3 scripts/research.py` 的官方只读快照步骤；无模型命令。项目执行耗时/显存峰值/相似度/咬字/高音听感均 N/A。成品：无；不提供虚构 outputs 路径。
