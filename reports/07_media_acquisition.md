# cc-media 音视频获取能力迁移

查阅与实测日期：2026-10-16，Asia/Shanghai。状态：**搜索与 Bilibili 音视频下载可用；YouTube 测试流下载仍被拒绝。** 本轮范围是调研、移植和验证来源工具，不代表歌声 PoC 已跑通。

## 来源和迁移选择

只读查阅 `/Users/yinshawnrao/explorer/cc-media`，来源 commit：`5614c7ac6eef7e4c3300a0b42d202cb4af65c2c0`。对应源文件工作区无修改，迁移后再次比对 SHA256 一致；完整源文件/移植文件哈希见 [provenance](evidence/media-port-provenance.json)。没有修改 cc-media，也没有把它的凭据或已有素材复制进本仓库。

| 来源 | 本仓库复用 | 取舍 |
|---|---|---|
| `tools/video/yt_dlp_readonly.py` | `scripts/media_support/yt_dlp_readonly.py` | 保留 Cookie 元数据/竞态校验、仓库外私有快照、清理与 YouTube 默认参数；调整入口文案 |
| `tools/video/bili_search.py` | `scripts/media_support/bili_search.py` | 保留 WBI 搜索和错误分类；作为库调用，移除旧 CLI 与全局暂停提示，搜索结果不直接打印 |
| `tools/video/tests/test_yt_dlp_readonly.py` | `tests/test_yt_dlp_readonly.py` | 移植 15 项 Cookie 保护测试，使用纯合成凭据 |
| `check_yt_cookie.py` / `check_source_access.py` | 参考分层验证与脱敏思路 | 未照搬“双平台登录和搜索全部通过才能制作”的视频规则；本仓库允许独立来源继续，不自动要求用户确认 |
| `bili_dl.py` | 调研后未复制 | 原入口有临时流自动删除、输出覆盖及不共享本仓库下载预算等行为；当前 yt-dlp 能解析 Bilibili，无需页面解析备用路径 |
| `operations.md` / `README.md` | 保留版本稳定、IPv4、搜索不等于下载成功等约定 | curl TLS 兼容办法是特定故障的备选，未默认引入，也未关闭 TLS 验证 |

原仓库根未发现 LICENSE/COPYING；这是用户授权的本地内部复用，没有擅自宣称其代码为 MIT 或其他许可证。工具上游许可与下载媒体许可分别记录。

本机沿用 **yt-dlp 2026.06.09**，安装包记录的 release commit 为 `821bef0f00178916d60dbc86bc0bcb8cc3bae8d5`；FFmpeg/FFprobe 8.1.1。没有升级或全局安装。查阅了 [官方 README](https://github.com/yt-dlp/yt-dlp)、[对应 release](https://github.com/yt-dlp/yt-dlp/releases/tag/2026.06.09) 和本机 `--help`，核对配置隔离、JSON 探测、搜索、格式选择、插件与远程组件开关；固定版本文档见 [commit README](https://github.com/yt-dlp/yt-dlp/blob/821bef0f00178916d60dbc86bc0bcb8cc3bae8d5/README.md)。

## 本仓库适配

入口是 `python3 scripts/media.py`，支持 `doctor`、`search`、`probe`、`download`。YouTube 关键词搜索走 yt-dlp；Bilibili 走移植的 WBI API；其他平台可以先用网页搜索取得公开 URL，再由 yt-dlp 的提取器解析。未声称所有站点已经验证。

下载分两层：yt-dlp 负责页面解析、格式选择与鉴权；本仓库使用有字节上限的 HTTP(S) 传输器获取选中的完整流，然后调用 FFmpeg 本地提取 WAV 或合并 MKV。这样能共用 `download.py` 的锁、台账和中断预留。它并非对 cc-media 原下载 CLI 的逐字复制，也没有开放任意 yt-dlp 参数来绕过预算。

- 每流默认 500,000,000 bytes，最高 5,000,000,000；与模型/依赖共用累计 30,000,000,000 bytes。先用提取器精确 `filesize`，没有则 HEAD 取 Content-Length；不把 `filesize_approx` 当精确大小。GET 再核对长度，读取不超过预留字节。
- 已开始但失败的传输按预留量保守计费；异常中断保留预算。未知大小、HLS 分片、直播、播放列表跳过。DASH 的独立 HTTP 完整文件可用。该适配暂时不支持 HTTP Range 分块或断点续传。
- `--kind audio` 优先独立最佳音频，保留原始流并转 PCM16 WAV，不改变采样率/声道；`--kind video` 选最高 1080p，保留音画原始流并无损封装 MKV。
- Cookie 使用 `--cookies` / `SVC_LAB_COOKIE_FILE` / 本仓库根 jar；`--public` 强制无 Cookie。只把私有临时快照交给 yt-dlp；不导出浏览器、不更新用户 jar、不输出密钥。服务器 Cookie 有效性没有单独以登录页面验证。
- 所有实际媒体处理在本地；FFmpeg/FFprobe 输入协议限制为本地文件。没有上传音频。探测原始 JSON、请求头、签名流 URL 只存在于内存；证据仅保存白名单字段。
- 默认 `--role reference` 保存至 `work/acquisition/<run-id>/`。选定用于实验时才用 `--role target|source` 另写 `data/<role>/<run-id>.wav`。保留原始来源和衍生链；不覆盖，不把普通下载素材标成 AI 成品。

已同步更新 AGENTS、README、状态脚本和 Git 忽略规则。用户本轮的搜索下载授权替代初始“只能手动放素材”约束；模型权重官方来源与禁止第三方明星模型的规则继续适用。

## 真实验证

Cookie 指向 cc-media 现有 jar，仅通过只读快照消费。事件的时间为 UTC，以下耗时是各命令墙钟时间；不表示模型推理性能。GPU/显存占用：N/A，未运行模型或 GPU 处理。

| 检查 | 结果 | 耗时 | 证据 |
|---|---|---:|---|
| doctor | yt-dlp / FFmpeg / FFprobe 可用 | 0.395s | [事件](evidence/media-events/20261016T080546940348Z.json) |
| YouTube 公开搜索“周杰倫 晴天 官方 MV” | 3 个结果，包含周杰伦频道官方 MV | 1.510s | [事件](evidence/media-events/20261016T080605576550Z.json) |
| Bilibili 搜索“陶喆 爱很简单 官方 MV” | 3 个结果；结果是候选，不能仅凭标题认定为官方/无损 | 1.075s | [事件](evidence/media-events/20261016T080610874076Z.json) |
| YouTube 官方《晴天》探测 | format 251、Opus、精确大小 4,960,069 bytes | 5.229s | [事件](evidence/media-events/20261016T080728432302Z.json) |
| Bilibili 候选视频探测 | 1080p AV1 + FLAC 两个完整 HTTP 流 | 1.716s | [事件](evidence/media-events/20261016T080803712014Z.json) |
| Bilibili 视频下载 + MKV 合并 | **PASS**，262.065s，1920×1080，音频 48kHz/双声道 | 22.239s | [事件](evidence/media-events/20261016T081008622594Z.json) |
| Bilibili 音频下载 + WAV 提取 | **PASS**，262.063729s，PCM16 / 48kHz / 双声道 | 9.926s | [事件](evidence/media-events/20261016T081206439722Z.json) |
| 自动测试 | **33 项通过**，含原有 8 项、移植 15 项、新增 10 项 | 约 0.03s | `python3 -m unittest discover -s tests -v` |

验证素材来源：[Bilibili 候选 BV1wjBjYDEgF](https://www.bilibili.com/video/BV1wjBjYDEgF/)，上传者“唯一8090”，标题含“4K修复/HiRes”。本轮只验证获取与本地转封装；没有证明修复质量、音频真实无损或适合训练，也没有主观试听。许可在元数据中未明确，记 `unknown`。

实际文件：

- 音频：[work/acquisition/smoke-bilibili-audio/audio.wav](../work/acquisition/smoke-bilibili-audio/audio.wav)，50,316,314 bytes。
- 视频：[work/acquisition/smoke-bilibili-video/video.mkv](../work/acquisition/smoke-bilibili-video/video.mkv)，85,276,539 bytes。
- 两个目录均保留原始流和 `receipt.json`。这次没有放入 `data/target` 或 `data/source`，没有新翻唱成品。

关键复现命令（重跑请更换 run-id）：

```bash
export SVC_LAB_COOKIE_FILE="$HOME/explorer/cc-media/all_cookies.txt"
python3 scripts/media.py --public search '周杰倫 晴天 官方 MV' --limit 3
python3 scripts/media.py search '陶喆 爱很简单 官方 MV' --platform bilibili --limit 3
python3 scripts/media.py probe 'https://www.bilibili.com/video/BV1wjBjYDEgF/' --kind video
python3 scripts/media.py download 'https://www.bilibili.com/video/BV1wjBjYDEgF/' \
  --kind video --run-id another-bili-video --purpose '视频链路复核' --max-bytes 100000000
python3 scripts/media.py download 'https://www.bilibili.com/video/BV1wjBjYDEgF/' \
  --kind audio --run-id another-bili-audio --purpose '音频链路复核' --max-bytes 100000000
```

## 失败与边界

1. W3C 托管 Sintel 测试片 URL 在提取阶段被拒绝，未传输媒体。未继续排查该无关测试站点：[事件](evidence/media-events/20261016T080730767052Z.json)。
2. YouTube《晴天》format 251 初始 HEAD 返回 403。改用提取器精确大小后，实际 GET 仍为 403；再将实际媒体连接限定 IPv4，仍 403。共一次初测、两种适配，停止继续尝试此流。没有升级 yt-dlp、更换 Cookie、调整系统代理/DNS、关闭 TLS 或尝试付费访问。不能据此断言整个 YouTube 不可用或 Cookie 失效；当前证据只覆盖这个候选/格式/环境组合。
3. 两次 GET 尝试实际媒体正文均 0 bytes，但每次保守计入 4,960,069 bytes；HEAD 前失败未预留媒体预算。对应 [HEAD](evidence/media-events/20261016T080800596652Z.json)、[GET](evidence/media-events/20261016T081131983990Z.json)、[IPv4 GET](evidence/media-events/20261016T081250137051Z.json)，脱敏失败副本也保存在 `logs/media/`。
4. 素材获取路径测试成功不等于完成数据清理。后续仍需选定合适版本、分离人声、切片、抽听。第三方修复转载仅作为本轮链路测试候选。

## 下载和空间

本轮实际媒体下载 **139,328,782 bytes**（视频两流 + 独立音频重复测试）；含失败保守计费为 **149,248,920 bytes**。加上原依赖，本仓库累计预算已计入 **456,743,302 / 30,000,000,000 bytes**，未结束预留 0。

本轮快照 `work/` **274,926,122 bytes**，`outputs/` **0 bytes**。没有删除原始流、中间文件或成品。完整证据见 [空间与预算快照](evidence/media-validation.json) 和 [共享下载台账](downloads.md)。

目前 Agent 可自行搜索、选择版本、探测和下载可用来源，无需逐次向用户确认。后续人工参与主要是听感核对，以及已有 Cookie 真正失效时由用户维护；当前迁移工作不因此暂停。
