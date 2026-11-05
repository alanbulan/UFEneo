# 月亮回旋三关键相几何诊断

本工具只消费已保存的蓄势第三版、展开、接触三张完整原源。`build_frames()`在内存返回三张320画布整帧与几何结果，不创建Godot场景，不注册招式、攻击框、时序或选人开关。现有三相没有完整转体轨迹与接触后回架，`runtime_candidate_accepted`固定为false，不能当可玩的回旋技能。

## 方法与边界

- `plan.json`逐项保存相对路径、源SHA、人工投影关节点、支撑鞋ROI和固定Forge模块SHA。使用项目已有Forge 5324342版本，RGB兼容色板与Alpha128，保留原源字节。
- 支撑髋→膝→踝两段总长归一到本人模型近腿参考35.749+41.976像素。每张原源只用一个等比缩放，不能分别修腿、按面积/画布撑满或旋转肢体。源尺寸不同不代表比例失败。
- 关节点被皮套和甲遮挡，每点按±18原像素保守处理。这只是投影骨长诊断，不能签精确解剖骨尺；本人模型的骨长本来也不是自动硬门。头壳顶受冠遮挡，未保存虚精确头尺。
- 原源支撑鞋Alpha128最低四行确定前掌比较锚，整图平移到[160,280]；把锚强制对齐不证明实游不滑步。栅格取整导致末行允许±1像素，未单独移动脚。
- 三整帧图可再生，`reports`仅临时诊断图，不向assets安装。报告内含采样尺寸、统一比例、测点、图像SHA、投影膝角/足向及不确定性。

## 在别的机器复核

准备Python3.12+、Pillow、NumPy与项目已批准固定Forge版本；设置`UFENEO_FORGE_ROOT`为该机器Forge源码根目录。脚本会核三模块SHA，不下载软件，也不包含本机绝对路径。

运行：

    python tools/rebuild/ultraman-arc/luna-spin-heavy-geometry/geometry.py --out reports/luna-spin-geometry-new-review
    python tools/rebuild/ultraman-arc/luna-spin-heavy-geometry/test_geometry.py

输出目录必须不存在，避免覆盖旧证据。首次未配置Forge环境会直接报缺安装路径，不绕开版本检查。当前回执在`docs/verification/luna-spin-heavy-geometry-review.json`。

## 当前结论

整图归一后，三相本人身份、全身轮廓与抬跟仍可读，支撑股胫比例接近；没有据此判整体比例失败。收膝→屈膝展开→近伸腿提供有用分段。展开脚尖上翘→接触下压可解释为伸膝伴随绷踝，不单凭脚向变化强制否决或补图。

但蓄势的攻击膝在身体左侧，展开转到右侧，肩胸也变角；没有足够的全身路径证据证明同一方向转髋。接触后同向随势、收膝、落脚回架也未建立。故本轮只止于几何诊断，不用旧侧踢、倒放或停帧拼出完整招式去跑真实输入回放。后续若必须展示大面积背甲，仍须可靠本人参考，不能猜造。

## 转髋中相增量v2

`plan-turn-v2.json`在原三相之间加入turn_mid。新相支撑髋被抬腿遮挡，只保存不可精确定位区域，不取区域中心当髋点，也不计算其股长。其整图比例改用可辨膝→踝投影尺，归一到旧三相已归一胫长中位数41.186；这是一把可比较的尺，不是四相真实骨长已精确校准。

    python tools/rebuild/ultraman-arc/luna-spin-heavy-geometry/geometry.py --plan tools/rebuild/ultraman-arc/luna-spin-heavy-geometry/plan-turn-v2.json --out reports/luna-spin-turn-new-review

旧三相采样比例、平移与像素保持不变。四相攻击膝投影x约121→160→189→195，新增相确实提供跨身分段；对齐结果只诊断横向序列，不证明身体骨盆中线或完整3D转向。当前四相仍缺接触后的随势、收膝、落脚回架，没有进入Godot输入/回放，也未安装。详见`docs/verification/luna-spin-heavy-turn-mid-candidate-review.json`。
