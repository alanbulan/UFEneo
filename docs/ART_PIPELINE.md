# 当前美术制作入口

本轮只有清理和交接，不恢复生产。收到用户新的开发指令后，先读AGENTS的整帧、预算和验收规则。

1. 定位本人当前model和具体动作；旧路径先查art/source-index.json，不能因路径变化重发生图。
2. 人物使用项目tools/art_pipeline.py中的generate_image，官方路由、high、1024方图、透明背景；凭据及费用账本只读本机配置。
3. 图像返回后实际检查身份、Alpha、完整四肢/武器、身体连续与大小。完整源只保留一份，当前拒收原因写在动作metadata中，不复制整个工程作为历史。
4. 整图处理经tools/rebuild/shared/forge_backend.py。旧颜色兼容palette_mode('rgb')，同一动作统一尺度和根点；禁止拼肢或以静止图加FX代替动作。
5. 当前PixelFX脚本仍在tools/rebuild/<id>，上游固定代码和MIT许可在third_party/pixelfx；只离线导出透明整帧。人物不使用库骨架。
6. 运行资源安装到assets，招式/事件到content。主游戏两个朝向、720/1080、实际输入和独立原InputFrame回放分开核验；逻辑检查不替代画面或听感。

现用源库存储：model保留当前人可读入口；stage目录保留正在接续的动作；已装来源去重后在sources目录，SHA文件名对应art/source-index.json。冻结JSON仍可包含当时原路径；不要为了美化路径改写原始请求与usage。

需要重新制作的未完成动作在docs/HANDOFF.md。旧大规模生成worker、历史审片安装器与废弃批次已经清理，不能把运行代码中的历史来源字符串当成它们仍然存在。
