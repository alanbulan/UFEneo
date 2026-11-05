# 月亮蹲左拳→右拳RAM候选

仅现有整源离线处理，不安装assets、不开放装甲、不收费。右拳采用contact-attempt-02.raw.png，经独立远肩→腕→拳链审阅；旧wrong_arm只说明它未满足第一拳近侧左臂要求，不代表不能作右拳。

- 第一拳沿原v3注册，3/3/12、65伤；第二拳为同蹲架→完整远拳02→同蹲架，3/7/8、65伤，拳Alpha紧框[52,69,13,14]。都保留30体力、low及原全部玩法字段。第一拳cancel 3..17→第二拳，第二拳cancel 3..17→sweep原样保留，但未载sweep。
- 两招均三槽两独立源；无独立随势/中间过渡，不能称完整美术验收。固定后胫投影尺只是候选配准，不是真实骨长已证。
- 真实输入：一直下方向，在零基20/27帧LIGHT松按再按。引擎directions[0]是任意方向通配，不是中立。命中confirmed才允许取消；blocked分支先return，不设confirmed。晚按可能经招末残留buffer后起，不能称格挡或落空取消。
- 受方使用正式杰顿状态与图像，最新core恢复语义已纳入合同；旧crouch_blockstun高姿仍在，本候选没有混入新RAM两相。
- 测试均原InputFrame而非硬件键盘。无音频听审、实速或录屏验收。

## 入口

UFENEO_FORGE_ROOT指向既有Forge 5324342。register.py只新建art/fighters/ultraman-arc__luna/stage2/crouch-chain-registered-20261105-v1，不覆盖。main_bundle.py freeze只新建合同，run负责串行godot_lock、XDG隔离、主游戏original及独立replay。

本轮最终使用reports/luna-crouch-chain-resume/contract-v3.json。v1已跑首八逻辑用例；v2增加semantics_check运行依赖并修正复制旧工具的标签，图像、规则与20/27输入未改。各版本的-first-base.json只是当前代码构建一拳组件的中间来源合同，未执行它，不是完整二拳合同。

运行示例（先确保图形环境和Godot锁空闲）：

```sh
python tools/rebuild/ultraman-arc/luna-crouch-chain-resume/main_bundle.py run --contract reports/luna-crouch-chain-resume/contract-v3.json --out reports/luna-crouch-chain-resume/graphical-v3
```

加--headless只算技术/逻辑证据，不算截图。freeze和run均不修改正式数据。

## 保留的失败与真实边界

v2首个主游戏original模拟/独立回放成功，外层Python检查器对Godot JSON浮点时长使用range报TypeError，批未完成。v3只修读取整数转换并明确排除封存后离线test_check；不改图、规则或输入。原日志保留。时长冻结时严格核[3,3,12]/[3,7,8]，离线另断言trace时长为正整数且等于合同，不静默接受非整数。

命中gap75按20/27时，第一拳move_tick3于输入帧27取消到二拳，共130伤。命中gap100仍可取消，第二拳因实际间距/推退未命中，总65，未扩判定强保连中。格挡34..40晚按于41帧自然结束后buffer起二拳，落空30..37晚按于38帧后起，均is_cancel=false；命中44按已是重新起左拳，不是右拳。持续按住20..50不会生第二沿。九方向第二沿可识别，因为[0]通配。

主游戏/图形矩阵固定20/27，不覆盖晚缓存二拳格挡/空挥画面；语义矩阵提供这些路径的逻辑与独立回放，不替代图形。无录屏。
