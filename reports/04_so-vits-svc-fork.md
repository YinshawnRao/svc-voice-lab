# 04 so-vits-svc-fork 准备状态

日期：2026-10-16。状态：`RESEARCHED_NOT_DEPLOYED`，另有共同阻塞 `BLOCKED_DATA`。

上游：[官方仓库](https://github.com/voicepaw/so-vits-svc-fork)；查阅 SHA：`6cf76556c8afc1ba0c9109ea289c8f34b2eb4519`。固定版本文件见 `reports/evidence/so-vits-svc-fork/`，跨项目事实/issue 链接见 [02_research.md](02_research.md)。

## 本轮做了什么

完成 README/许可证/提交/release/issues 调研和本机适配判断。**没有建立该项目的完整环境，没有训练或推理，也没有记录为安装失败三次。**

README 推荐 Python 3.11，本机现有 3.10/3.12、无 3.11；pyproject 支持 >=3.9，可评估 3.12 的官方依赖路线。当前 HEAD 虽有维护提交，README 仍写停止维护；MPS 训练 issue 不能忽略。

## 下一可执行步骤

官方 svc pre-resample → pre-config → pre-hubert → train → infer；自动底模下载必须先审计并转本地缓存。

完整安装必须先形成官方依赖/权重清单，分配 `.envs/so-vits-svc-fork/`，经逐文件审计后下载；保留 README 原始命令及必要适配差异。当前不存在可诚实提供的一键 PoC 脚本。

命令：本轮仅 `python3 scripts/research.py` 的官方只读快照步骤；无模型命令。项目执行耗时/显存峰值/相似度/咬字/高音听感均 N/A。成品：无；不提供虚构 outputs 路径。
