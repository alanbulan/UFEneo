# rtmlib / DWPose 本机参考测量工具

- rtmlib项目：<https://github.com/Tau-J/rtmlib>，本机使用PyPI `0.0.16`，Apache-2.0。原文在本目录`LICENSE`；上游说明固定到提交`03a1693e59e4f7cd84582c0fb30459b3bf18ad42`，不将该提交视为PyPI wheel的构建证明。
- DWPose项目：<https://github.com/IDEA-Research/DWPose>，Apache-2.0，上游许可与说明分别在`DWPose-LICENSE`、`DWPose-README-upstream.md`。
- 推理模型：DWPose-s / RTMPose-s，133关键点，输入192×256。由rtmlib上游列出的OpenMMLab官方模型地址下载，完整URL、下载包、ONNX文件及计算的SHA-256见`reports/tooling/rtmlib-dwpose-source-v001.json`。此模型摘要是本机下载后计算值，不声称是官方公布摘要。
- MMPose项目：<https://github.com/open-mmlab/mmpose>，固定提交`759b39c13fea6ba094afc1fa932f51dc1b11cbf9`的许可原文在`MMPose-LICENSE`。

程序与依赖隔离在`.tools/external/rtmlib/v0.0.16/venv/`，模型放在`.tools/models/rtmlib/`；只用于离线参考测量，不放入游戏运行或发行文件。依赖版本和下载凭据另存于`reports/tooling/`。

已实测四张原剧帧及四份现有像素稿。模型在交叉手臂上会认错腕点，也会给镜头外肘点较高分；目前只采用可视化辅助用途，不作为自动绑定或改写素材的依据。生成美术继续使用GPT Image。
