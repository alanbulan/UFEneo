# 月亮轻击三连接续

本工具链接续保留的16相整人物候选：light1五相、light2五相、light3六相。原source及收据保持不变；不调用生图、不收费、不开放未齐S2–S7的装甲。原脚本依赖已清理reports及Windows字体，本入口直接读取保留收据并通过source-index解析旧源。

## 素材核验

```sh
python tools/rebuild/ultraman-arc/luna-light-chain-resume/test_check.py
python tools/rebuild/ultraman-arc/luna-light-chain-resume/check.py --report reports/luna-light-chain-resume/check.json
```

核验SHA、LFS实体、1024原源、159整图、Alpha128二值、固定32色、透明RGB、边缘、表面测点和支撑鞋底。保留原攻击规则框，比较本人实体拳足与其相交。输出是整图平移建议，不自动宣告动作验收。

## 免费复现缺失派生

仅在原源已核、固定Forge安装可用时使用。`UFENEO_FORGE_ROOT`指向批准的agent-sprite-forge固定版本5324342fdfab72430f4e9604f3fe427009f8596d。脚本核对三个实际模块SHA与逐相冻结收据相同。

```sh
python tools/rebuild/ultraman-arc/luna-light-chain-resume/restore_samples.py
python tools/rebuild/ultraman-arc/luna-light-chain-resume/restore_samples.py --write
```

先Alpha128、整张159/1024的Forge兼容kCentroid、本人32色RGB兼容映射、再Alpha128。**只有输出PNG编码字节SHA完全等于原收据**才允许恢复对应LFS指针；任何漂移直接报错，不修改原收据、不以另一算法替代、不覆盖已有实体。

## 整图配准与正式main候选

`register.py --review <JSON>`要求root_delegated_by_user实际目视16相后的配准签收，含每相sample_sha256及translation。它将完整159方平移至320画布，绝不裁肢、局部修改或逐相缩放。只按本人Alpha生成三带受击框，保留原攻击框、伤害、时序、取消和费用。结果在art的在制候选目录，不写assets/content开放开关。

`main_bundle.py --manifest <manifest.json> --output reports/luna-light-chain-resume/<合同>.json`绑定已配准包及真实代码SHA。`tests/review/fighters/ultraman-arc/luna_light_chain/main_entry.gd`实例化正式app/scenes/main.tscn，以内存月亮定义进入主游戏；不建独立研究场景。支持`--contract`、`--out`、`--kind=hit|block|whiff`、`--depth=1|2|3`、`--left`和独立`--tape`。

同目录`logic_check.gd`覆盖双向、命中/防御/落空及一二三段18个用例，并用实际记录的双方InputFrame新建独立模拟重放；它不能替代图形验收。所有Godot导入、检查及图形运行必须经`python tools/godot_lock.py -- ...`串行，并隔离用户数据目录。图形入口尚需真实720/1080、两朝向完整人物、各段收招及完整三连接续验收。无录屏时不声称已录制。

## 本轮结果（2026-11-04）

16相原源及159候选已全部获取并验证；未重新生图或替换算法。已实看完整三段的双朝向静态格图及idle首帧，按共同x=80、承重足y对齐280完成320整图候选，保留独立源与冻结收据。三段实际攻击框、伤害、时序、费用和取消保持，只有受击框按本人Alpha派生。

8项Python单元测试通过。Godot 4.6.3兼容逻辑检查18组全部通过，16相全部可达；双向命中一/二/三段分别65/130/195伤害，防御和落空0伤害，独立原输入回放逐tick一致。防御只出现第一段接触，保留原命中取消条件，没有强行保连。

项目要求Godot4.7，因此上述不是4.7正式验收。当前无可用图形显示，Xorg dummy启动因本地Unix socket不可建立而失败；双向720/1080主游戏动态画面与可视回放尚未验收。无录屏，装甲未正式安装或开放。详细摘要见docs/verification/luna-light-chain-resume.json。

UI资源到齐后，main_game正式入口在4.6.3完成无诊断解析；这不是图形执行。全仓仍有缺失运行素材，因此不宣称完整游戏导入或全回归通过。

验收断言要求每段真实hit恰好一次及对应总伤害；防御必须有真实首段block，落空必须无接触，两者不得越过原命中取消条件。图形截图器保留原窗口尺寸的无损PNG与尺寸/SHA，不再使用缩小JPEG冒充720/1080像素证据；本轮尚未实际生成这些窗口截图。
