# 04 applio-app 准备状态

日期：2026-10-16。状态：`RESEARCHED_NOT_DEPLOYED`，另有共同阻塞 `BLOCKED_DATA`。

上游：[官方仓库](https://github.com/IAHispano/Applio-App)；查阅 SHA：`5de02daa276c93e089f7aebdd292cd59edaab80f`。固定版本文件见 `reports/evidence/applio-app/`，跨项目事实/issue 链接见 [02_research.md](02_research.md)。

## 本轮做了什么

完成 README/许可证/提交/release/issues 调研和本机适配判断。**没有建立该项目的完整环境，没有训练或推理，也没有记录为安装失败三次。**

新发现的近期活跃桌面入口，复用 Applio，不是新的独立歌声模型。Install/Repair 自动拉依赖需审计；本轮不安装系统 .app。

## 下一可执行步骤

用户素材与已训练 RVC 模型；不下载第三方明星模型。

完整安装必须先形成官方依赖/权重清单，分配 `.envs/applio-app/`，经逐文件审计后下载；保留 README 原始命令及必要适配差异。当前不存在可诚实提供的一键 PoC 脚本。

命令：本轮仅 `python3 scripts/research.py` 的官方只读快照步骤；无模型命令。项目执行耗时/显存峰值/相似度/咬字/高音听感均 N/A。成品：无；不提供虚构 outputs 路径。
