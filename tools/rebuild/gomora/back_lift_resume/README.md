# 哥莫拉背掀接续

本入口重建了环境回退后丢失的接续工具，按当前原源和当前代码重新验证，不沿用旧运行结果。只处理已有完整人物源，不收费生成、不操作用户Codex，不替换正式三级。

## 源审计与几何

```sh
python tools/rebuild/gomora/back_lift_resume/resume.py audit
python tools/rebuild/gomora/back_lift_resume/resume.py geometry
```

审计18张哥莫拉完整源与初代六张179候选的冻结SHA、解码及RGBA。phase12按历史签收指向 `rejected/candidate.png`，不能因目录名误判。Git LFS指针报告为待取实体，不当坏图重生。

18相root来自保留的明确足底读点，重核当前完整源近足宽底。初代A/E校正到179候选真实腹侧外缘，修正0–3px且在原读点误差内；phase01原取整A点透明，改同列[106,89]。这些是待配准候选，不是实际接触验收。

源图轨迹另比较把本动作source02从起手移至07→09之间的方案，18张各用一次，无肢体/root插值。先前几何最大骨盆步长38.04→24.23px，重建环境必须复跑取得当前结果。候选把01保持8tick，保留20tick开始捕获，总时长72→76tick。起手变化、卸重、倒立接续仍需动态验证，方案未自动安装。

## 固定Forge整帧注册

上游 `https://github.com/0x0funky/agent-sprite-forge` 固定提交 `5324342fdfab72430f4e9604f3fe427009f8596d`。运行已获准的固定工具前，入口再次核三个文件的历史SHA，不自动下载或换版本。

```sh
UFENEO_FORGE_ROOT=/path/to/agent-sprite-forge python tools/rebuild/gomora/back_lift_resume/resume.py register
```

通过项目forge_backend/RGB兼容调色、Alpha128和整图kCentroid，将18张1024源统一1/4，使用512×320透明画布和[256,304]锚点。六张现有179候选不重采样，完整置于192画布[6,6]，锚点[96,184]。全部内存核完无裁切后，才写唯一art候选及收据；不写assets/content。支持先完成18相攻击方，待初代LFS到齐再补受方；重入时核原源/色板/后端与全部已写候选SHA，不重复处理或覆盖攻击方，不制作历史副本。

## 根点能力与验证

新增root_overrides仅让指定受方有独立root偏移，hold/root/release共用解析；缺字段/缺身份/空表沿原默认，加载、捕获前和运行期拒绝非法表。无覆盖的旧内容保持原指纹；实际使用覆盖的双方或开放可达形态才绑定语义版本，锁定形态不误触发。

```sh
python tools/godot_lock.py -- python tools/verify.py --skip-import --only throw_root_overrides logic_2d throw_hold_point_overrides phase3_throws
```

测试覆盖schema、双向/空中root、floor-safe、release、异常退出、指纹兼容、24组真实输入和隔离文件逐tick独立重放。它不等于哥莫拉背掀真实输入、画面或美术完成。环境回退后的代码已重新静态复审，运行结果须从新日志取得。

普通主游戏哥莫拉三级仍是全力超振动波。最后接入前，还需完成实际空接保相、拆投、落空、离背、唯一落地伤害与主游戏双向720/1080及持久回放。不执行历史安装器，不抄杰顿grip/root，不修改历史user_approved。

## 本次重建实测

新环境锁内四项回归通过：throw_root_overrides、logic_2d、throw_hold_point_overrides、phase3_throws；见docs/verification/gomora-root-resume.json。已生成并实际看18相完整攻击方注册候选，初代六相也已到齐、不重采样注册并实看双向完整帧。背部测点在Forge结果上与源图投影误差0至0.5px，均为真实可见上缘；受方配对已实看双向及两种绘制顺序，末两相的头/臂与头角重叠，明确未通过；主游戏画面未验收。


## 实际注册像素的配对复现

运行 `python tools/rebuild/gomora/back_lift_resume/contact_review.py`，输出 reports/gomora-resume/contact-review 的双向完整人物检查页及 measurement.json。使用当前收据SHA和真实可见背部上缘，受方A/E必须是腹侧实际下缘；不修改任何注册像素。两种绘制顺序同时展示，不能用遮挡掩盖穿体。

重新测得候选相序骨盆最大步长38.04→23.28px（此前源投影估算24.23px不作为现注册结果）。07→02→09候选只减轻突跳，尚未批准。末两相不能继续将腹缘固定在背部：整轮廓保守检验中，若仅末帧突然平移，在前移/上移各0–80px搜索范围内，04最小约56.6px、05约76.5px才能完全无重叠（不是任意方向全局下界），因此不能采用末端瞬移修补。下一步应从03卸重阶段设计整数、独立离背轨迹，按接续速度和实际头臂/头角轮廓验证，再接既有倒立/落地动作。轮廓零重叠是保守诊断，不是所有真实遮挡都错误。

普通三级保持不变。源及候选是生产材料，不是已安装资产；此目录不运行旧安装器。无录屏。

## 03起整数离背候选（未通过）

`python tools/rebuild/gomora/back_lift_resume/departure_review.py` 用02末帧实测骨盆作初值，从tick32的03起，以每tick `[6,15-n]` 的整数速度独立抬离，不再将受方腹缘吸附背缘。仅移动完整注册帧，不改其像素、尺寸或源；输出在 `reports/gomora-resume/departure-review`。`python -m unittest discover -s tools/rebuild/gomora/back_lift_resume -p 'test_departure_review.py' -v` 验证整数连续积分、双向镜像交叠一致、末两相零交叠、早段问题不隐藏及重复结果一致。

本轮实际结果：骨盆最大逐tick位移16.16px；04/05的tick40–47整Alpha交叠为0。但03的tick32–39仍从2113降至117像素交叠，实际查看tick35双向及两种绘制顺序，角/臂关系仍未通过。因此这是定位离背问题的候选，不是解决完成，也不接入正式三级。

另对第一次03（攻击方02）做root x[-100,100]、y[0,200]的有界整轮廓零交叠诊断，最小骨盆跳变86.98px。这个范围内的保守诊断不能当作任意方向全局下界，也不意味着真实遮挡都错误；仅说明不能以第一帧大平移作为修补。下一步仍要逐部位核03之前承重/卸重关系，再决定现有完整源的相序和离背时机。未接现装倒立/落地，未做主游戏双向720/1080或录屏。

## 通用空接保相能力（不等于哥莫拉安装）

新增显式 `throw_current_capture` 选择项，抓中前保存受方完整相、朝向、root、速度与状态；`capture_current`阶段只读保留，进入首承重hold/root、拆投或异常退出后清理。表现层复用捕获前角色快照的现有动画算法，不重写跳跃相位。无选择项的旧内容不加入新语义指纹；普通哥莫拉三级、assets和content保持不变。

v1仅允许地面攻击方接空中受方，保相至首承重段必须静止且不改变投技高度，首承重必须为固定sprite（无variants/floor_variants）。捕获要求实际躯干框相交，入口root差按实际 `root_overrides` 和 `hold_point_overrides` 解析后受限，不扩判定、不吸附、不添加无敌。

最终快照已通过 `throw_current_capture`、`throw_root_overrides`、`throw_hold_point_overrides`、`phase3_throws`；补跑 `logic_2d`、`review_inputs`、`throw_current_capture` 也通过。专用测试包含12组双向真实输入、拆投1/2/3与4边界、落空、唯一落地伤害、独立文件逐tick回放、原整相一致、异常清理及schema/指纹兼容。回执：`docs/verification/gomora-current-capture.json`。这些是通用能力测试，哥莫拉03穿体和主游戏双向720/1080美术验收仍未完成，无录屏。

最新承重缺口与已有替代源核查见 [RECEIVER_GAP.md](RECEIVER_GAP.md)：00–02本身头肩/角冠关系也未通过，不能靠提前卸重绕过。未找到可直接替换承重的保留整帧；若继续新增，先仅解决02最低承重母相，成功后再补00/01/03，当前未发起生成。
