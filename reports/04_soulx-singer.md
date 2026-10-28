# 04 soulx-singer 准备状态

日期：2026-10-16。状态：`RESEARCHED_NOT_DEPLOYED`，另有共同阻塞 `BLOCKED_DATA`。

上游：[官方仓库](https://github.com/Soul-AILab/SoulX-Singer)；查阅 SHA：`81aeb3ae772c70093c3de74dc23c92d983801ae4`。固定版本文件见 `reports/evidence/soulx-singer/`，跨项目事实/issue 链接见 [02_research.md](02_research.md)。

## 本轮做了什么

完成 README/许可证/提交/release/issues 调研和本机适配判断。**没有建立该项目的完整环境，没有训练或推理，也没有记录为安装失败三次。**

当前已提供 SVC，优先此路线。单个 SVC 权重 2.79GB 未超限；未下载。torch 2.2.0、torchcodec 0.10.0、sageattention/NeMo 组合及 MPS 待验证；不能仅据内存够就宣称可跑。

## 下一可执行步骤

SVC 需要 prompt/target wav 与 F0，无需歌词/MIDI；SVS 则需要参考及歌词/音高/音符 metadata 和人工对齐。

完整安装必须先形成官方依赖/权重清单，分配 `.envs/soulx-singer/`，经逐文件审计后下载；保留 README 原始命令及必要适配差异。当前不存在可诚实提供的一键 PoC 脚本。

命令：本轮仅 `python3 scripts/research.py` 的官方只读快照步骤；无模型命令。项目执行耗时/显存峰值/相似度/咬字/高音听感均 N/A。成品：无；不提供虚构 outputs 路径。
