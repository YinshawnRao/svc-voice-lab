# 后续默认改为30步单版

日期：2026-10-16。用户连续反馈听不出A/B差异，明确要求后续只用原A设置，不再单独区分版本。此决定优先于早期每项目2–3组对照要求；不表示用户认可整体音色质量。

## 修改

- `config/lab.json` 的 `seed_vc_default_steps=[30]` 为默认参数来源。`seed_vc_local.py`、片段、完整歌曲、从data开始的三个入口均沿用此默认值。
- 每次默认仅生成 `seed-vc_AI.wav`、`seed-vc_mix_AI.wav` 和 `listen.html`，页面不显示A/B，也不会因复用旧输入manifest而带入“两版”说明。
- `run.json`记录`requested_steps`，单版内部标识为single；对用户只显示AI混音/AI纯人声。旧A/B文件名与数据格式继续支持。
- 校验按请求的版本数量检查，不能把只生成A的未完成双版误判为完整单版。
- 只有用户明确要求对比才使用多值`--steps`；例如`--steps 30 50`。AGENTS、README和状态配置已同步。已有音频不重跑、不覆盖、不删除。

## 验证

```bash
python3 -m compileall -q scripts
python3 -m unittest discover -s tests -p test_generation_defaults.py -v
python3 scripts/run_stage2_poc.py --run-id qa-default-single \
  --clips work/default-single-change/clips \
  --evidence-dir reports/evidence/default-single --device mps
.envs/demucs/bin/python scripts/validate_full_song.py \
  --run outputs/qa-default-single/run.json --duration 2 \
  --evidence reports/evidence/default-single/smoke-validation.json
```

4项针对性检查通过：默认只请求30步、显式比较保留30/50、单版页面4条音轨且无A/B文案、旧双版页面6条音轨。

2秒实际冒烟通过：只生成一份人声和一份混音，30步推理耗时27.757秒，评测/混音1.064秒；MPS allocated/driver采样峰值2.12/3.66GiB（统一内存计数有重叠，不相加）。音频长度、采样率、声道、哈希、有限/非静音及本地页面链接通过。

原孙燕姿30秒A/B重新经过兼容校验，仍通过；模拟缺失B的双版manifest被正确拒绝。全部93个原输出文件大小/SHA256未变。证据位于`reports/evidence/default-single/`，原脚本/配置快照位于`work/default-single-change/before/`。

本轮只实跑2秒片段入口；完整歌曲与from-data入口的参数传递经代码及语法检查，未重复长时生成。QA音频保留在`outputs/qa-default-single/`，不列入用户正式试听交付。未新增模型/依赖下载，未上传音频，未commit或push。
