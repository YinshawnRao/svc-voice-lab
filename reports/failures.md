# 阻塞与修复记录

日期：2026-10-16。同一根因上限 3 种修复；每项按根因计数，不把正常依赖安装步骤计为修复。

| 根因/现象 | 实际处理 | 修复种数 | 结果/证据 |
|---|---|---:|---|
| 沙箱无法访问 GitHub DNS | 在用户授权的网络执行上下文做同样只读探测 | 1 | 官方 raw/GitHub/PyPI 可访问；不是项目安装故障 |
| GitHub REST API HTTP 403 | 改用官方网页内嵌 currentOid/stargazerCount + 固定 SHA raw | 1 | 10 个仓库快照成功；未使用非官方镜像 |
| 空目录 git init 被沙箱拦截 .git 写入 | 授权上下文运行相同 git init -b main | 1 | 本地仓库建立；无 commit/push |
| 沙箱 sysctl/MPS 不可用 | 主机只读/sysctl 和微型张量探测 | 1 | 48GiB、14 核、本机 MPS=True；原沙箱结果单独保存 |
| Python 3.10 不支持 filelock 最新版本 | 按 PyPI requires_python/wheel tags 选择兼容版本 4.1.0 | 1 | `logs/core-manifest-v2.log`；不是项目 runtime 失败 |
| 离线 wheel 集缺 SymPy 所需 mpmath<1.4 | 官方 PyPI 补 1.3.0，保留下载过的 1.4.1 | 1 | `core-install-attempt1/2.log`；pip check 通过 |
| Demucs 使用 Torch 2.0.1 的内部 WHEEL 标签为 x86_64 | 换 PyPI Demucs 4.0.1 允许的 torch/torchaudio 2.2.2 | 1 | `demucs-install-attempt2.log`，arm64 标签/pip check/CLI 通过 |
| 测试临时目录 /var 与 /private/var 别名差异 | fixture 解析为真实路径，和 common.ROOT 契约一致 | 1 | 下载中断预算预留测试通过 |
| target/source 为空 | 保留空目录，完成本轮不依赖素材的准备 | 0 | BLOCKED_DATA；不制造替代音频 |
| 分离/Seed 辅助权重尚未全部建立允许来源清单 | 不触发上游首次自动下载 | 0 | 后续技术准备项；不是“下载失败三次” |

初始化阶段没有某个模型运行时故障达到 3 种修复上限；以下追加真实模型阶段结果。`logs/` 保留原安装失败及成功日志；此表保存可跟踪摘要。


## 第二阶段（20 秒 PoC）

| 根因/现象 | 实际处理 | 修复种数 | 结果/证据 |
|---|---|---:|---|
| 官方 GitHub API 查固定版本再次 HTTP 403 限流 | 官方 Git blobless/sparse checkout，只取源码/配置，锁定相同 SHA | 1 | `reports/evidence/stage2/source-checkout.json`；未下载示例音频/二进制模型 |
| randomname 0.2.1 的 PyPI JSON 漏报 setup.py 依赖 fire，离线 pip 报 No matching distribution | 阅读已审计 sdist 的 setup.py；显式补 fire，解析其 termcolor 依赖，官方 PyPI 审计下载，再离线安装 | 1 | 99 个分发文件，pip check 与 CLI 导入成功；`logs/bootstrap-seed-vc-cli-1792140418406524000.log` 失败、`logs/bootstrap-seed-vc-cli-1792140711924418000.log` 成功 |
| BigVGAN 的 grouped conv_transpose1d 在 MPS 报 Output channels > 65536 not supported；已有自动 fallback 标记仍失败 | 固定 BigVGAN 在 CPU，扩散、Whisper/CAMPPlus 保留 MPS；RMVPE/光谱特征原已显式在 CPU | 1 | 5 秒/2 步冒烟退出 0、总耗时 24.545 秒；`logs/stage2-seed-mps-smoke-fix1.log`。2 步只有技术验证用途，8.67% 接近削波，不作为质量成品 |
| 上游 strict=False 加载警告跳过 11 个键 | 增加运行时参数审计：全部实际学习参数名称/形状匹配；多余 Wavenet 分支未启用，位置索引是源码重新生成的非学习 buffer | 0 | `work/stage2-seed-smoke-fix1/runtime/checkpoint-audit.json`；不是缺少有效模型参数，不改上游文件 |

本轮没有问题达到 3 种修复上限。历史“空素材/模型未审计”阻塞已解除，素材洁净度和人类听感仍待确认；未使用其他仓库的素材或明星模型。
