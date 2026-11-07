# 引擎选型与分层规范

回答两个问题：底层格斗引擎该不该换成成熟方案；现在的分层是否符合通行规范。
结论是**不换引擎**，并且分层已经符合通行做法，只需把规则变成可执行检查
（`tools/check/layering.py`，已接入回归）。

## 一、成熟格斗引擎能不能直接用

| 名称 | 类型 | 语言 | 许可 | 能否用于本项目的 Godot 4.7 自研模拟 |
| --- | --- | --- | --- | --- |
| Ikemen GO | 整套引擎 | Go | MIT | 不能。Go 独立引擎，不可嵌入 |
| M.U.G.E.N | 整套引擎 | 闭源 C/C++ | 专有免费 | 不能。2013 起停更 |
| Night Sky Engine | 整套框架 | C++ | MIT | 不能。绑定 UE5 |
| Sakuga Engine | 整套框架 | C# | MIT | 不能直接调用，只可参考架构 |
| Castagne | 专用层 | GDScript（Godot 3） | MPL 2.0 | 不能。Godot 4 版未发布 |
| GGPO | 回滚库 | C++ | MIT | 不能。无 Godot 绑定，2019 停更 |
| GGRS | 回滚库 | Rust | MIT | 需自写 GDExtension；Godot 封装停在 Godot 3 |
| dsnopek godot-rollback-netcode | 回滚库 | GDScript | MIT | 理论可以，但实测在 4.7.2 加载失败 |
| Delta Rollback | 回滚库 | GDScript | MIT | 可尝试，同类调度层 |

**结论**：以上没有一个是"能被一个已有自研确定性模拟的 Godot 项目直接调用"的。
整套引擎都要求重写游戏；可插拔的那几个都是**回滚网络**库，而本项目是单机。

## 二、可插拔的只有回滚网络这一层

回滚库借的是"输入采集 + 状态快照/回滚调度 + 传输"这一层，不含模拟。
本项目 `core/` 已经是整数 60 tick 确定性模拟，恰好满足它们的全部前提
（固定 tick、逐 tick 可序列化、种子化随机、不读系统时间与渲染）。

但**现在不需要**：没有联机需求。若将来要做，优先考虑 dsnopek 或 Delta 的调度层，
并预留可序列化状态接口，而不是改动 `core` 的语义。

## 三、最值得借鉴的是什么

1. **GGPO 的"逐 tick 输入 + 状态快照 + 可重放"模型**。本项目已经是这个形状：
   `InputFrame` 是唯一输入形态，`replay_recorder` 逐 tick 记录，
   `state_hash` 可复现。回放既是功能也是自检手段，继续用它守确定性。
2. **MUGEN 的 `[Statedef]` + 控制器 + 触发器**写法，以及 **Skullgirls 的可调帧延迟**
   思路。本项目的招式 JSON（逐帧 `frames`、`cancel`、`events`、`shots`）与
   `core/states/<id>.gd` 一状态一文件，是同构的，只是用 GDScript 而非 DSL 表达。
   不建议改成 MUGEN 的 CNS 格式——那会引入一套外部解释器。
3. **Godot 官方推荐的"数据与表现分离"**。本项目 `core` / `presentation` 的边界
   就是这个模式，`presentation` 只读，图片不进模拟指纹。

## 四、分层规范

依赖方向只允许向下，实测无环：

```
tests ──→ app ──→ content
  │        │        ↑
  │        ↓        │
  └──→ presentation ─┘
          │
          ↓
        core   ←── input
```

| 层 | 允许依赖 | 禁止依赖 |
| --- | --- | --- |
| `core` | 无（只消费 `content` 传入的数据） | 渲染、`Input`、`presentation`、`ui`、`app`、随机数、系统时间 |
| `input` | 无 | 同上（但要读设备，这是它的职责） |
| `content` | 无 | 任何代码层 |
| `presentation` | `core`、`content` | `ui`、`app`；不得写活模拟 |
| `ui` | `presentation`、`content` | `app` |
| `app` | 全部（只负责装配） | — |

这套分层对应的通行规范：

- **依赖倒置 / 分层架构**（Martin Fowler 的 Presentation–Domain–Data Source 三层）
  在本项目是 `presentation`–`core`–`content`。
- **确定性锁步模拟**（GGPO / GGRS 的共同前提）在本项目是 `core` 的整数 tick 约束。
- **只读视图**（Godot 的 data-driven rendering 建议）在本项目是
  `presentation` 只读 `UfeMatchDirector` 的状态快照。

### 可执行的守卫

`tools/check/layering.py` 把这些规则变成检查，已接入 `tools/verify.py`：

- 层间反向引用 → 失败
- `core/` 出现 `randi`/`randf`/`Time.`/`OS.get_ticks`/`Input.` → 失败
- `presentation/` 写 `view.simulation`/`sim` 的角色状态 → 失败
- 指纹代码引用 `res://assets`/`res://art` 媒体路径 → 失败

演出副本（KO 慢放重建的 `scene`）属于表现层自己的数据，可以写，不算违规。

## 五、不做什么

- 不换引擎，不引入整套框架。
- 不改 `core` 的确定性语义去迁就外部库。
- 不把招式数据改成 MUGEN CNS 格式。
- 不在没有联机需求时引入回滚网络。
