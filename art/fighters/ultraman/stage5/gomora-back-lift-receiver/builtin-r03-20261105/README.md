# 内置生图R03离背候选

## 本轮完成

原源由根任务按用户明确要求经内置image_gen生成，保持原字节移入本唯一生产目录。完整提示词、四张参考顺序与SHA在provenance.json；模型、high、usage、费用未返回，明确为空。没有项目收费API或用户Codex操作。

真RGBA透明，1774×887；36029个0<Alpha<128像素，原边缘非零计数1/38/1/0。固定Forge完整帧Alpha128、kCentroid到220×110后诊断，未应用运行色板，未切肢、旋转、局部缩放或滤分量。

## 怎么看

在仓库根，UFENEO_FORGE_ROOT指向固定5324342版本，依次运行：
- python tools/rebuild/gomora/back_lift_resume/review_builtin_r02.py --candidate 5
- python tools/rebuild/gomora/back_lift_resume/review_v5_neighbors.py
- python tools/rebuild/gomora/back_lift_resume/review_builtin_r03.py

输出reports/gomora-builtin/r03-review，每张保留双向、双完整层序。A02/A09-back0-up0为腹侧共点；back12-up16为整体后上平移空间对照。后者两组全Alpha零交叠，独立实看头、胸、近拳均分开，但没有认定速度、时间或动态验收。

## 已知问题

两臂连接清楚，无明显额外肢体；近臂向前下展开、远臂向后展开，屈膝保留，与R02第五版风格和身份一致。腹侧共点时A02/A09全Alpha交叠325/408px，近前臂诊断区159/230px；实际换层会吞掉近前臂、胸前区域，不能继续锁腹承重。矩形ROI不是精确人体分割，不能将全Alpha数字直接等同穿体。

统一画布原点R02(122,107)切到R03，在A07仍有20px全Alpha交叠；整图后3上8后可分离，但A02/A09角冠继续抬升，不能把A07单张通过当整段通过。后12上16是相对R03各自腹缘对齐位置的20px静态位移，不是相对R02的骨盆跳变。两版真实同源骨盆尚未独立签收。

## 下一步

先将R02末帧真实骨盆与R03对齐，逐tick核后上方运动及A02→A09角冠扫过，再判断本候选能否用或需要手臂抬高的新整帧。不先为细小脸部差异重生，也不把本次静态位置直接写进运行轨迹。accepted=false、runtime_installed=false，未写assets/content；无主游戏720/1080、空接、落地或录屏验收。
