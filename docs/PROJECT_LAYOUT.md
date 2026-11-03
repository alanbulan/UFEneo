# 项目目录与唯一归属

2026-11-03 清理后采用下列结构。执行准则只在根AGENTS，游戏规格只在REBUILD_2D_PLAN，当前状态只在PROGRESS，具体接手步骤只在HANDOFF。不要继续往多份文件追加同一条用户指令。

| 目录 | 内容 |
| --- | --- |
| app/、app/scenes/ | 主游戏装配、流程和入口场景 |
| core/ | 整数60 tick确定性模拟、状态和规则 |
| input/ | 设备输入与电脑控制；现存主游戏审片驱动另列tests/review |
| presentation/ | 只读画面、镜头、特效和声音 |
| ui/kit/、ui/theme/ | 正式界面组件和像素主题 |
| content/fighters/<id>/ | 本人运行定义、招式、状态帧、形态、资料 |
| content/catalogs/、roster/、templates/ | 查询门面、名册、公共数据模板 |
| assets/{fighters,effects,audio,ui,stages,app,fx}/ | 已装资源、动态路径使用的资源、来源和许可；fx是仍被当前注册表引用的旧接口目录 |
| art/fighters/<id>/model/ | 当前定稿与测量，不重复存历史定稿 |
| art/fighters/<id>/sources/ | 已装资源仍有用的唯一源文件，SHA文件名；原用途由source-index和原始metadata说明 |
| art/fighters/<id>/stage<N>/ | 当前未完成动作、请求、候选和有效交接收据 |
| art/shared/sources/ | 无法归属单角的当前源材料 |
| art/source-index.json | 现用源SHA、字节数和旧路径到唯一实体的索引；不是备份 |
| tools/runtime/ | 启动、Godot定位与短临时录制 |
| tools/rebuild/shared/、tools/rebuild/<id>/ | 复用制作模块、仍需接续的动作处理器、PixelFX烘焙脚本 |
| tools/maintenance/ | 只读仓库审计与冻结路径解析 |
| tests/、tests/fixtures/、tests/review/ | 功能回归、必要输入夹具、主游戏内审片驱动 |
| third_party/、addons/ | 实际采用的上游代码与许可 |
| docs/ | 当前规范、交接、验证结果摘要 |
| reports/ | 新运行产生的日志、截图、回放与临时视频；忽略上传 |

art、tools、reports带.gdignore，不进入游戏资源导入。二进制源与运行资源使用Git LFS；Godot的.uid和.import是源文件侧车，必须上传，.godot导入缓存不上传。

原始来源收据内的旧路径保留字节。离线工具通过tools/maintenance/layout_runtime.py和art/source-index.json读取现有源；未列入索引的旧候选、审片、录屏和无用源已经删除，不能将这些历史文字当作运行依赖。实际主游戏仅加载assets/content等正式层。

本机环境、下载缓存和游戏个人存档不属于仓库。三个旧目录整理工作树及原Git历史直接清理，未新建备份。
