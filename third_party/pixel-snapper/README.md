# Pixel Snapper离线研究工具

- 官方仓库：https://github.com/Hugo-Dz/spritefusion-pixel-snapper
- 许可：MIT，原文见本目录LICENSE。
- 版本：1.0.0，固定提交`02f9315d73d3219274d17767b36d9a231a6b1f4b`。
- 本机使用范围：本地网格校正和母图色板对比，不调用上游在线生成服务。
- 安装来源、Git blob及SHA-256：`reports/tooling/pixel-snapper-source-v001.json`。
- 已用真实GPT腕部和原生分层对照实测。它保留软Alpha且会调整原生对照的网格尺寸，因此未设为生产默认，也没有替换sprite-gen的component-row提取。

工具仅位于`.tools/external/pixel-snapper/`，不进入Godot运行资源。原始素材、current入口和参考均不改写。
