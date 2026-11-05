# 210背掀主游戏内存候选

## 范围

候选只在创建对局时替换内存special3、受方专用state_frames和表现clips，不写正式content/assets、不替换正式三级。实例化app/scenes/main.tscn，保留正式输入路由、模拟、HUD、镜头和完整Alpha取景。不创建独立预览场景，不设置开局位置、高度、能量、HP或朝向。

R02第五版、收臂过渡、展开R03统一210×105；先检查固定髋点名义解，保留各原源±50px估计不确定性。原32释放，32/33收臂，34–39展开R03；40/44分别用旧04/05完整相，再接现装thrown_back四完整相和down。根目标来自整数骨盆积分，不用线性release目标。唯一撞地impact68，伤害490。mode=root离背不等于已覆盖throw_released机制。

00/01仍是已知失败的旧完整帧，用来暴露实际入口至承重的缺相问题，不把整个动作美术标通过。倒立/翻滚后四相髋点也是待审估计，不能只据成功落地就签收接相。

## 生成候选合同

固定Forge环境下先运行review_builtin_bridge.py --width 210，再运行build_memory_candidate.py。输出reports/gomora-builtin/main-candidate210/contract.json及两幅整帧atlas，绑定源SHA。

可选--air-body-subregion只用于复现普通前跳入口诊断：原初代没有diagonal_air，添加现有flip_forward四完整帧的可见胸腹子区为索引1，同时完整保留原fallback索引0；子区全部包含于原框，hurtbox并集不扩大。正式数据不改，成功背后垂直路线不依赖此补丁。

## 真实输入路线

普通正面前跳路线已确认被当前几何拒绝：一条轨迹越背后太远，另一条因正式推挤留在前方；末下降高度45→31又跳过旧R00允许的36–39高度交集。保留失败回执，不宣称全局任何输入都不可能。

rear_vertical_hit路线全用真实物理键：哥莫拉持续Q蓄满并保持朝向，初代先斜跳越过、落地后从背后走近并转向，再作垂直跳；哥莫拉直接从charge按P，避免idle自动转身。原合同gap68、second-jump-delay16已有真实命中记录：相对根约[-44,45]，入口差[13,5]在14上限内；不用注入朝向或扩大捕获框。它证明背后垂直来者可抓，不代表普通前跳路线也通过。

## 主游戏与回放入口

全部Godot命令经tools/godot_lock.py。runtime_run.py负责隔离用户数据、冻结源SHA及检查引擎错误；main只支持真实云桌面图形显示，headless不冒充画面。

示例参数：main --contract reports/gomora-builtin/main-candidate210/contract.json --out reports/<新目录> --case rear_vertical_hit --owner 0 --gap 68 --jump-delay 16 --size 1280x720。反向owner1，1080使用1920x1080。输出目录必须不存在，不能覆盖旧结果。

独立replay进程不运行输入driver，读取已记录原始输入包逐tick比较hash；保存format6后另建模拟再次重放。拆投1/2/3/4使用rear_vertical_tech1等明确case，判据仍是正式3tick边界。

## 尚未验收

图形720/1080双向与完整接相结果以实际新回执为准，本入口本身不代表截图已产生或通过。前00/01头肩穿角、髋点敏感性及后相人工读点限制始终保留。未安装，无真人键盘验收；未生成录像时不得声称有录像。
