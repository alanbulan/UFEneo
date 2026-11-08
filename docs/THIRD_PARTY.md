# 第三方来源与许可

用途：引入、核对或交接第三方代码、素材和制作工具时读本文件。这里只记录当前实际采用的来源与许可。

本页只记录当前代码/素材采用和制作工具的来源。运行不依赖API密钥，外部制作环境和研究缓存不随仓库上传。角色、原剧画面和声音的权利不因工具开源而转移。

| 项目 | 当前使用方式 | 来源与本地许可 |
| --- | --- | --- |
| Shoto Fighter | 两个纯逻辑模块，项目类名前缀适配 | https://github.com/aminRX/shoto-fighter-godot ，MIT；third_party/shoto/LICENSE及UPSTREAM.json |
| Godot UI Components | Tween/过渡适配，固定22d2355690612978e58df559ddd4b6ba50c6887c | https://github.com/MrEliptik/godot_ui_components ，MIT；third_party/godot_ui_components |
| Godot AI | 编辑器 MCP 插件 4.4.1，开发期场景/节点/运行调试；游戏内 helper 仅在调试器通道激活时工作 | https://github.com/hi-godot/godot-ai ，MIT；addons/godot_ai/LICENSE |
| Controller Icons | Godot输入图标插件3.1.8 | https://github.com/rsubtil/controller_icons ，MIT；addons/controller_icons/LICENSE |
| PixelFX | 仅离线烘焙透明像素FX；固定a84159688af3ca37a4be05a0d422b94451b2e24e | https://github.com/patch-gg/pixelfx ，MIT；third_party/pixelfx/LICENSE、NOTICE.md、UPSTREAM.json。包含Patch及Hugo Duprez署名，人物骨架未采用 |
| Fusion Pixel Font | 正式简中12px单宽字体，最近邻显示 | https://github.com/TakWolf/fusion-pixel-font ，SIL OFL 1.1；assets/ui/fonts/LICENSE-OFL.txt及SOURCE.json |
| Kenney Pixel UI | 已注册的少量CC0组件；正式主体为本项目像素套件 | https://kenney.nl/assets/pixel-ui-pack ，assets/ui/kenney/LICENSE.txt |
| agent-sprite-forge | 可选离线整图处理，项目forge_backend统一适配 | 本机安装或UFENEO_FORGE_ROOT指定；不把技能/venv复制到仓库 |
| sprite-gen grid-range | 保留已采用提取器和显式格距覆盖层 | Apache-2.0；third_party/sprite_gen_grid_range内原文、NOTICE、UPSTREAM和补丁 |
| LibreSprite | 可选离线源稿工具，未捆绑可执行程序 | https://github.com/LibreSprite/LibreSprite ，GPL-2.0；third_party/libresprite |
| rtmlib / DWPose | 可选测量辅助，不做骨骼绑定 | https://github.com/Tau-J/rtmlib 、https://github.com/IDEA-Research/DWPose ，Apache-2.0；third_party/rtmlib |
| Pillow / NumPy | 本地图片和PCM检查 | HPND / BSD-3-Clause；tools/requirements-checks.txt，环境不入库 |
| FFmpeg / yt-dlp | 可选离线媒体获取与处理工具 | https://ffmpeg.org/ 、https://github.com/yt-dlp/yt-dlp ；不分发本机程序和下载缓存 |
| Kits AI | 可选分离、分轨与转换服务 | https://docs.kits.ai/ ；凭据只在本机，不声称文生音效能力 |
| Wikipedia文字 | 游戏资料使用带来源的简体摘录/改写 | CC BY-SA 4.0；各profile/roster条目保留原页、版本和来源；图片/IP不自动适用文本许可 |

现用每份图片/声音的来源以assets中的provenance/manifest和content/audio/sources.json为准。source_kind=episode表示原剧来源；original或转换记录不能冒称本人原声。旧审片页和下载缓存已清理，不再将它们列为需要上传的依赖。

PixelFX制作脚本保留在tools/rebuild/<id>。赛文I、布莱克王Q/热束、初代束、提欧跃击、哥莫拉与EX哥莫拉已用效果各保留实际采用的烘焙入口；Godot只消费PNG帧，未引入运行时JS。简体使用说明：https://github.com/bayshier/pixelfx-zh/blob/836f545ed8946fffc6b911ff645cad5bd8c372aa/README.zh.md 。
