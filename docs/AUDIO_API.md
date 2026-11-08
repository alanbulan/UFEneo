# 音频接口

项目通过 Kits（`https://arpeggi.io/api/kits/v1`）做语音转换、人声分离和分轨。
客户端在 `tools/audio/kits_client.py`，命令行入口是 `tools/audio/pipeline.py`。

## 凭据

密钥只在本机，**不进仓库、不打印、不复制**。按优先级：

1. 环境变量 `UFE_KITS_API_KEY`
2. macOS：`~/.codex/secrets/ufeneo-music.key`（纯文本，权限必须 `0600`）

密钥文件权限过宽（组或其他用户可读）时，客户端直接拒绝发送请求。

## 连通性

```bash
.venv/bin/python tools/audio/pipeline.py doctor
.venv/bin/python tools/audio/pipeline.py models --per-page 3
```

`doctor` 只检查 ffmpeg、ffprobe 和凭据是否存在，不发网络请求。
`models` 会实际调用 API；返回模型列表说明接口打通。

2026-11-08 实测：`models` 返回 270 个音色模型、90 页，接口正常。

## 能做什么

| 子命令 | 用途 |
| --- | --- |
| `doctor` | 本地环境与凭据检查 |
| `models` | 列出可用音色模型 |
| `extract` | 从媒体文件提取音轨 |
| `prepare-voice` | 准备语音转换的输入切片 |
| `cut-cue` | 按时间点切出短事件 |
| `submit` | 提交任务（**发收费请求**） |
| `poll` | 查询任务状态 |
| `download` | 下载结果 |
| `mix` | 混音 |

`submit` 会真实计费。按 [AGENTS](../AGENTS.md) 的规则，收费请求须先读本机最新账本，
新单预占 1 美元、按真实 usage 结算，未知单不释放、不重发。

## 不在这个接口范围内

Kits 是**语音转换与分离**服务，不是文生音效或文生音乐。项目里
`content/audio/sources.json` 的 `source_kind` 只有 `original` 和 `episode`，
不声称任何音效是文本生成的。

## 当前声音缺口

见 [PROGRESS](PROGRESS.md) 的"后续优先级"：teo/arc/blazar/omega 缺通用状态音与语音表。
补齐需要新录音或新分离轨，属收费操作，须用户明确授权后才能做。
