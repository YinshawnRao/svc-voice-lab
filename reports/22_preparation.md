# 《手心的太阳》补齐四位准备

日期：2026-10-18。用户认可前轮萧亚轩、王心凌“效果还挺好”，并明确授权在同一目录补齐另外四位；其后中断并要求继续。认可仅针对前轮两位，本轮新增四位尚待试听。

保持 `outputs/stage14-seven-shouxindetaiyang/`，新增孙燕姿《我怀念的》、蔡依林《天空》、梁静茹《崇拜》、杨丞琳《雨爱》。原唱张韶涵不做转换，最终六位。前轮两位的纯人声、混音、输入和runs均保留不重跑。

本轮配置 `config/experiments/stage15-shouxin.json`；原stage14配置保留。冻结全局阵容配置与SHA256，逐份验证参考歌、原区间、15秒长度和SHA256，不重新挑片。源素材沿用stage14同一副歌109.4–144.9秒，35.5秒；人声、伴奏和原曲片段逐字节复用。沿用前轮定位依据，不重新下载或分离。参考候选素材各不足10分钟，使用15秒零样本参考，不训练；未经人工确认的干净总时长N/A，自动筛选不保证无混响、和声或伴奏残留。

557个既有数据、成品、历史实验配置、全局规范和下载台账已记录大小与SHA256。可更新的试听页、根manifest、README、状态和总报告原件已保存到 `work/stage15-before/`；证据见 `reports/evidence/stage15/`。中断后复查557个保护文件及5个备份全部匹配，尚无新增推理进程或音频，不重复初始化。

本次复核锁定的Seed-VC README歌声参数，commit `51383efd921027683c89e5348211d93ff12ac2a8`；30步单版，F0=true、autoF0=false、0半音、CFG0.7、FP32、seed20261016。MPS扩散/Whisper/音色编码器，CPU BigVGAN/RMVPE/频谱。重模型串行、本地离线、不上传音频、不启用可选F0修复、不新增依赖或权重；执行脚本哈希已冻结。

```sh
.envs/demucs/bin/python scripts/extend_shouxin_experiment.py prepare
python3 scripts/extend_shouxin_experiment.py generate
.envs/demucs/bin/python scripts/extend_shouxin_experiment.py validate
python3 scripts/finalize_shouxin_extension.py
```

准备阶段只做文件核验和复制，不使用GPU，显存N/A。生成耗时、MPS统一内存采样和输出见 `22_shouxin.md`；不把统一内存当独立显存。CER=N/A，无独立校对歌词。

## 用户追加目录命名要求

生成期间用户明确要求目录带seven且歌名拼音完整；为避免中途移动正在写入的文件，全部生成并通过首次校验后，使用scripts/rename_shouxin_outputs.py迁移到outputs/stage14-seven-shouxindetaiyang/，再校验所有音频和原runs内容及试听链接。seven为系列命名，本曲实际六位转换。历史生成时路径保留在原收据，由迁移台账映射；当前配置和导航更新。
