# 04 so-vits-svc 准备状态

日期：2026-10-16。状态：`RESEARCHED_NOT_DEPLOYED`，另有共同阻塞 `BLOCKED_DATA`。

上游：[官方仓库](https://github.com/svc-develop-team/so-vits-svc)；查阅 SHA：`730930d337d171479eadf305f96cbed4bb393e77`。固定版本文件见 `reports/evidence/so-vits-svc/`，跨项目事实/issue 链接见 [02_research.md](02_research.md)。

## 本轮做了什么

完成 README/许可证/提交/release/issues 调研和本机适配判断。**没有建立该项目的完整环境，没有训练或推理，也没有记录为安装失败三次。**

已归档；README 稳定测试为 Python 3.8.9，本机未安装该版本；不自动下载来源未审计的解释器。MPS double 算子和旧 fairseq 依赖需要独立验证。

## 下一可执行步骤

先 5–15 秒切片、最小训练；不要与 fork 4.0 或其他 VITS/TTS 权重混用。

完整安装必须先形成官方依赖/权重清单，分配 `.envs/so-vits-svc/`，经逐文件审计后下载；保留 README 原始命令及必要适配差异。当前不存在可诚实提供的一键 PoC 脚本。

命令：本轮仅 `python3 scripts/research.py` 的官方只读快照步骤；无模型命令。项目执行耗时/显存峰值/相似度/咬字/高音听感均 N/A。成品：无；不提供虚构 outputs 路径。
