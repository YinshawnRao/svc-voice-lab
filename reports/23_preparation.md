# 六人《我要的幸福》准备

日期：2026-10-18。新建独立实验 stage16-xingfu，成品目录 outputs/stage16-six-xingfu/。按用户“其他6个人”排除原唱孙燕姿，制作蔡依林、萧亚轩、梁静茹、张韶涵、杨丞琳、王心凌。

完整默认阵容冻结于 reports/evidence/stage16/default-roster.json，SHA256见独立manifest。六份既有15秒参考已逐一核验歌手、歌曲、原区间与SHA256，不换曲、不重新挑片。每人零样本参考，不训练；各参考候选不足10分钟，未经人工确认的干净总时长N/A。

复核本地官方Seed-VC README与锁定commit 51383efd921027683c89e5348211d93ff12ac2a8。使用歌声专用V1，30步单版，F0=true、autoF0=false、0半音、CFG0.7、FP32、seed20261016。MPS扩散/Whisper/CAMPPlus；CPU BigVGAN、RMVPE及频谱。没有安装依赖或新增权重；推理前原入口校验已审计模型并禁网。显存峰值未测项目写N/A；MPS分配与驱动读数分别报告，不能视作独立显存。

盘点到另一个stage15《手心的太阳》批次正在运行，保留其进程和文件。新脚本在分离、冒烟、生成前等待既有重模型任务结束；排队证据单独保存。557个已完成数据/成品/历史配置/全局规范文件已记录大小与SHA256，排除明确仍在变化的前轮manifest及进度文件。shared README/状态/总报告暂不修改，结束时基于最新内容更新；不回写历史实验。

统一媒体入口doctor通过。沙箱内搜索transport_unresolved，在授权网络上下文重复同一最小搜索后通过。B站公开搜索-101，现有只读Cookie快照搜索通过。YouTube公开probe受访问限制，同一现有只读会话probe通过：Timeless Music候选MV（标题自称official，未独立核实上传者身份），213秒，EC-3 m4a精确10,239,259 bytes。备用B站BV1NZ421m7rL仅探测，未下载；许可证均unknown。

选一段完整副歌，使用离线ASR、原曲与人声能量辅助定位，保留乐句与自然收尾。选定起止和依据将写入manifest；CER=N/A，ASR不是经用户核对的歌词。先4秒30步技术冒烟，再串行生成六位共同副歌；技术通过不代表人工听感。

## 素材已取得

YouTube候选MV经审计入口下载成功，耗时112.977秒。原始EC-3流10,239,259 bytes，SHA256=4dbd9111870ceeefece2f56680067880d275a4c591c932d86c0f704b6c7ccd38；派生原始WAV122,830,950 bytes，48kHz、6声道、213.248秒，SHA256=2f438bdbb02269b70dc3aead3c74053dd2ea3edc83f50189bcbd565a2ded26e4。原始流、WAV与回执均保留，许可证unknown。没有下载备用素材。

本次源为6声道。当前Demucs输入适配器对多声道只取前两路（demucs/audio.py convert_audio_channels），会遗漏中置声道；因此分离前在work/用FFmpeg默认声道矩阵显式下混成44100Hz双声道float32，再送入Demucs，保留中置人声对立体声的贡献。原始6声道WAV不变，下混命令与派生哈希写入本轮manifest；试听原曲也由同一原文件正常下混。该适配发生在新脚本首次执行前，执行脚本哈希已冻结。

## 副歌定位与预处理

选定第一段完整副歌68.4–95.3秒，共26.9秒。64.3秒候选经5.8秒与10秒人声短窗口确认仍含前句，予以放弃；最终68.4秒起8秒窗口识别为完整副歌首句并接下一句。87–97秒尾窗识别完整最后一句，时间戳约至94秒；人声尾音RMS在94.6秒后低于0.001，保留至95.3秒。长窗口ASR发生时间戳漂移，不直接采纳其逐句起点。非人工听音/歌词真值，CER=N/A。

分离使用UVR_Demucs_Model_1，MPS，two-stems vocals、shifts1、overlap0.25、segment7、float32。原曲完整人声/伴奏均保留，六位共用同一副歌；片段44100Hz PCM16，人声单声道、伴奏/原曲双声道。六份target为既有15秒原WAV的逐字节复制。

排队450.929秒，前轮批次完成后才开始本轮重模型。分离13.017秒，初始ASR12.540秒，其余短窗口ASR各约3–5秒；实际命令、耗时与RSS见reports/evidence/stage16/。分离MPS峰值未采样=N/A；ASR末尾MPS读数不是峰值，RSS不是显存。

4秒30步MPS技术冒烟通过，外层耗时35.383秒；输入、输出、参考哈希与有限非静音、时长检查通过，证据smoke-validation.json。此短片段不替代正式副歌；接续串行生成六人26.9秒交付。

## 并行目录迁移复核

整批首次校验发现前轮 outputs/stage14-shouxin/ 已在其他授权任务中改名。前轮output-relocation.json记录“用户要求目录名带seven且歌名拼音完整”，迁移至outputs/stage14-seven-shouxindetaiyang/。本轮保护清单中26项按前轮映射逐字节核验，大小和SHA256全部一致；本轮没有移动、恢复或修改其文件。原始保护清单与首次失败日志保留。仅调整本轮validator读取明确迁移映射、报告区分内容保持与路径迁移；生成函数及六份音频不变，脚本修订及前后哈希记录于execution-scripts.json。
