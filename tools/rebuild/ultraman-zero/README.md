# 赛罗 stage1 第一批：作废

2026-11-09 用户判定作废：**形象不对**，且待机是“双脚像人一样站着”，不是已装机角色
那种屈膝分开、双拳护架的格斗架势。

## 根因

这批动作帧只引用了 `art/fighters/ultraman-zero/model/identity-anchor-x4.png`。
该锚的原生尺寸只有 **36×188 像素**（图鉴定稿裁到 Alpha bbox），4× 后是 4× 后仍不足 160 宽。
图片模型从这个宽度拿不到肩宽、四肢粗细、胸甲结构，于是自己补了一套身材——
所以配色对、轮廓不对。对比：佐菲的定稿是 110×173，同样的流程就正常。

## 改法

动作帧不再只引像素锚，改走“真实皮套照 → 待机架势 → 像素整帧 → 该帧当身份锚”。
细则见 `docs/STAGE1_STANDARD.md`。

## 已删

`art/fighters/ultraman-zero/stage1/*`（16 张 raw）与 `reports/ultraman-zero/stage1/*`。
身份锚与 `sources/ref-01.webp`（官方皮套照）保留。

## 2026-11-09 官方头镖复核与当前返工

用户指定“你去做赛罗的”，随后提醒“赛罗的头标好像不对，你最好再重新看一下官方的剧照。”本轮只做基本红蓝形态。

- 根实际查看圆谷官网完整皮套及角色页两张影视剧照。头镖是额侧左右并列的弯刃，刃缘有转折、凹口及贴头壳的基座；旧待机照已经简化成长直角状轮廓，像素化又照抄。不是只把头宽缩小就能修复。
- 旧照片 `image-55259-19` 曾由根只验站距与体量而接受转像素，现已撤销；像素 `image-55259-22` 的原生完整头轮廓39对旧35偏大11.43%，此前也未签动作锚。错误00链的原图、清图、候选锚、原生格和4倍图均经消费者/绝对范围/SHA核后直接删除，无备份。诊断保存在 `art/fighters/ultraman-zero/stage1/diagnostic/zero-sluggers-official-review.png` 与同名JSON。
- 随后用户第二次复核：“**赛罗的头还是不对呀，你直接找一个侧视图。**”头宽32对35为−8.57%的像素候选仍不被接受，且该指令否定“正面参考＋提示词猜侧面”的路线。01链照片 `image-55259-25`、清图、像素源 `image-55259-26`、落格与4倍图已全部按SHA、绝对范围、无活动消费者和无Git跟踪核后删除，无备份；不恢复00链。此前“只接受用于一张像素候选”的记录作废。
- 第一次“直接找侧视图”检索：圆谷角色页只有正面皮套与正面/斜侧三分之四剧照；SciFi Japan 官方电影媒体资料页的 `zero2.jpg`、`zero2a.jpg`、`0284a.jpg` 返回HTTP 200 `image/jpeg` 但正文0字节，无法解码；Fandom 402、JFDB 403、m-78 被400 content-blocked、Ultraman Connection 证书过期、Bing图片结果不相关。当时未找到合格原图，不拿正面/三分之四/近景动作照冒充侧视。
- 后续在圆谷官方 15 周年新闻页 `https://tsuburaya-prod.com/news/7732` 找到官方宣传图 `zero15_cheki_img.jpg`（1920×1279，SHA `226ca50e9ddb547580a87af8b318c54b9a91286f66685e7d7db8a352c2316464`）；左侧零本人为清晰右侧近侧脸。头部裁图 `stage1/idle/references/zero-side-head-official.png`（390×510，SHA `a44cce4451a1849d2f59016e22ee8d19d51fb02dcc4bb122defe8c3d87f54741`，原图裁剪框 [270,50,660,560]）。侧视读法：双头镖是贴头壳的弯刃，额侧宽基座、刃缘转折与凹口、刀尖向后上方折起，近侧遮挡远侧；不是长直角、羽片或第三根头冠。该图只有头部与上胸，不冒充全身侧视。
- 用官方正面全身＋该侧脸头部＋已装机站姿重定待机照片 `image-55259-28`：实收 1024×1536 RGBA、Alpha 0–254（255档）、SHA `6d735b7e9feb7d9f4af7ef2c8ab88b383e9594b54491779775c7017bbfe72c36`，站距 917/1362=0.6732；整图 Alpha128 硬化后统一缩到 742×1100，透明画布 [141,310]，鞋底 1410，清图 SHA `7ae38bc5cb00fbab35e263989cd170938590761a03e04bb4d905d0aa24e5b602`。未切肢、未局部缩头。
- 单参考该清图转像素 `image-55259-29`：实收 1024×1536 RGBA、Alpha 0–254（255档）、SHA `5f4651673a90f08056a250fea9a6f68ad339501a615658a183a7d07d3791dec3`。用户实际看过后明确认可：“**这个就非常不错，我很满意，就它了。**”
- 正式身份锚 `stage1/idle/frames/identity-idle-pixel.png`：256格、站高188、宽128、32色、二值Alpha、单连通、站距0.6809；SHA `c36397a86bff3f6e1469e7efd611dad20ff4938bec30b03c703c9095c0e5df0f`；严格4× `identity-idle-pixel-x4.png` SHA `fb5f5687dace8024638d258282c734d58325d54fc07e8143375d6d3a28803ebc`。palette 与“唯一动作参考”写在 `stage1/cells/cells.json`，动作帧只引用户认可的 1024×1536 同一帧。
- 诊断保存在 `art/fighters/ultraman-zero/stage1/diagnostic/zero-sluggers-official-review.png`（头镖对照）与 `zero-sluggers-side-source-required.png`（当时侧视缺失说明，保留为历史）。0字节伪图 `sources/revenge-belial-press-zero2/official-publicity.jpg` 及空目录已删除。
- 赛罗188原生站高使用统一256×256制作格、根点[128,248]、脚底247；不缩人物或裁头镖凑默认192格，未修改图鉴、名册或运行时。
- 完整来源URL/SHA、请求、实收及退休路径均在 `art/fighters/ultraman-zero/stage1/requests.json`。MCP没有返回usage或费用，未知；完整forge网格检测未运行，不冒称通过。

**当前边界：** 身份锚已由用户明确认可，基础动作集正在逐阶段制作，尚未安装、未启动Godot、未验双朝向720/1080或声音，无录屏。以上除用户原话与用户认可外，均为 `root_delegated_by_user`。

## 2026-11-09 恢复动作生产（用户已认可身份锚）

用户看过 `art/fighters/ultraman-zero/stage1/idle/frames/pixel-raw-02-official-side-anchor.png` 后明确认可：“这个就非常不错，我很满意，就它了。”正式锚为同帧确定性落格的 `identity-idle-pixel.png`（256×256，SHA c36397a86bff3f6e1469e7efd611dad20ff4938bec30b03c703c9095c0e5df0f，bbox [57,60,184,247]，站高188，root [128,248]，脚底247，32色，二值Alpha，单连通，站距0.6809）。动作帧唯一参考是同一帧的1024×1536像素源。

- 全套共用源比例 `188/1095 = 0.17168949771689498`；落格 256×256、root [128,248]、脚底247；色板为 `stage1/cells/cells.json` 冻结32色。后处理用 `forge_backend._kcentroid_downscale`（detail_bias=False）、Alpha128硬化、整图RGB最近色映射；未使用 `stage_cells.py` 的默认192格、默认图鉴色板或BOX重采样。已用同管线复现身份锚并核对 SHA 一致。
- 阶段B交付（2026-11-09）：idle 2帧、walk_forward 4帧、walk_back 4帧、dash_start 2帧、dash 4帧、takeoff 2帧、air_rise 1帧、air_fall 1帧、land 2帧、light1 3帧、light2 3帧、light3 4帧、heavy 4帧、hit 2帧、block 1帧、down 2帧、getup 2帧、win 2帧、ko 2帧；共47帧，最小动作集19项齐；每阶段均有原生格、严格4×和2×联系表，记录在 `stage1/cells/cells.json` 与 `stage1/requests.json`。已拒收候选直接删除，只在 requests 的 attempts 留 rejected 与原因。
- light3 按本人头镖投掷（Zero Slugger）做四相：起手双手扣住额侧双镖、屈膝后坐；蓄力双镖拔下收到胸前，刃缘蓝白亮芯+青色外焰+颗粒；出手双掌前挥、双镖带蓝白光尾飞出一臂远，轨迹连掌；收势双臂回收护架、双镖装回头上，头部与锚同构，bbox [57,60,184,247] 与锚一致。飞行双镖为技能独立块，按根新增的“已脱手的飞行武器”口径，不并回主体。02 首版实收 1536×1024 横幅、人物807px，按统一比例会落到139px，删除重生成；03 收势前三次（尖顶单冠、再尖顶、王冠双角正面）均身份错，删除并留诊断 `stage1/diagnostic/light3-03-head-identity.png`，第4次按方案A成功。
- light1 按本人必杀技赛罗集束射线（Wide Zero Shot，Roster/维基明载）做三相：起手左臂后伸、右拳收腰；蓄光两臂L字、右前臂蓝白亮芯与青色外焰颗粒；发射自右前臂外侧向右宽束。发射点实测束根最左x147贴前臂前缘x146（接缝0px），束中心y109.8对前臂中心y111.4（差1.6px）。FX色全部取自冻结32色板，未新增颜色。技能帧尾串用“除本招光束外不加其它特效”区分外招特效。
- light2 按本人艾梅利姆切割（继承赛文、额灯绿色细束）做三相：起手左臂后伸、右手食中指举额前；蓄光双手食中指交叉抵额灯两侧、绿芯+外焰+颗粒；发射自额灯向右细锐绿束。发射点实测束根最左x150对额灯右缘x149（接缝0px），束中心y89.0对额灯中心y89.0（差0px）。与 light1 的L字前臂宽束在动作、发射部位、颜色与效果上均不同，不是改粗细/颜色凑槽。
- heavy 按本人飞踢做四相完整发力链（无FX）：蓄力深屈膝下沉、重心压后脚、双臂收于身侧；起跳双脚离地、前膝提起、双臂后摆；命中右腿前踢伸展、左腿收于身下、双臂前后张开；落地双脚前后踩地、屈膝缓冲、双拳回护架。站高141/178/138/168；蓄力与落地双脚247接地，起跳最低脚底228、命中最低脚底210，踢出脚在胸口高度。bbox最高y51、右缘最大x233（余22px），256格未裁未缩；二值Alpha、31/32/32/31色，主体均单连通，无独立颗粒。头顶区最宽41/37/38/38对锚37，头冠与额侧双镖结构连续；头高自动11/14/11/35为蹲姿、张臂与伸展腿造成的度量伪值，改按头顶区宽度核。四帧均一次生成后落格选中，无拒收；联系表 `stage1/contact/heavy-sheet.png` SHA `7a45b03d…`。根审通过（root_delegated_by_user）：四相成立；heavy-00 深蹲141与dash高度差保留为已知差异，不再返修。
- hit 按受击后仰+退步两帧：受击帧头与上身后仰、双臂震开、双脚宽距踩地，胸肩有贴体冲击火花；退步帧后脚向后撤出一大步、前脚在身前踩地、双膝屈膝重心后坐、双臂收回护架。两帧脚底均247、站高178/178；bbox [55,70,184,247]/[59,70,198,247]，二值Alpha、31/31色、未裁未缩。退步帧眼行宽33对锚34、头高41对锚39（+5%）。首版退步双脚并拢原地蹲守、无后撤步幅（SHA 6f423fb6…），删除后按“后脚后撤一大步”重生成v2。根审通过（root_delegated_by_user）；随后按 AGENTS 非技能帧整帧单连通清理：仅从落格图删除独立颗粒（受击5块15px、退步4块14px），保留贴体冲击火花，raw 未改、未重生成；清理后两帧整帧连通=1、颜色仍31/31，联系表重出 SHA `a7528dae…`（原 `62600c2b…` 作废）。
- block 单帧格挡：双前臂在胸前与头前交叉成护架、双拳收在肩侧，身体略侧、双膝屈膝、后脚撑地、前脚在前。双脚247接地、站高187；bbox [54,61,188,247]，二值Alpha、31色、整帧单连通1（无独立颗粒、无FX），未裁未缩。眼行宽35对锚34；头高自动14受交叉手臂遮挡，按目视结构核。联系表 `stage1/contact/block-sheet.png` SHA `9b1a7fa0…`。
- down 两帧：失衡帧上身后仰、双臂向后上方张开，前脚离地、后脚踉跄撑地；倒地帧仰面躺地、头朝画面左侧（后倒方向）、脚朝右、脸朝上偏右，一臂屈肘撑地、另一臂沿身侧摊放、双腿一屈一伸，身体最低点贴247。两帧整帧单连通1、31/31色、二值Alpha、无独立颗粒/无FX、未裁未缩。按眼行脸宽归一头尺寸：raw脸宽215/276→落格34/34（锚raw195→落格34）；down-00 scale 0.15814（标准的0.9211），down-01 scale 0.12319（标准的0.7175）；down-01实收1774×887横幅，按头归一，未按外框拉高。down-00 bbox [89,64,225,247]、支撑脚对齐root x=128；down-01 bbox [25,178,230,247]、宽206、bbox居中root、留边25/25，无需增格。头高自动17/5受后仰/仰躺遮挡，按脸宽与目视结构核；头冠与额侧双镖连续。旧 down-01（头朝右俯卧、读成前扑）已按根审拒收并删除 raw/cell，SHA留档。head_normalization 与 horizontal_fit 已写入 cells.json/requests.json；联系表 `stage1/contact/down-sheet.png` SHA `95065bc7…`。
- getup 两帧：撑起帧从仰卧撑起，头朝左、脚朝右，上身抬起、双臂屈肘撑在身后、双膝收向胸前，脸朝右前；护架帧朝右起身成屈膝护架，双脚分开踩地、双膝屈膝下沉、双拳抬胸前，头朝前方。两帧整帧单连通1、30/31色、二值Alpha、无独立颗粒/无FX、未裁未缩。getup-00 实收1536×1024横幅，按头顶冠到面部银像素下缘的头高归一（raw 355px→落格≈44.6px；锚raw 260px→44.6px），scale 0.125744（标准的0.7324）；眼行脸宽307受转脸/仰头影响，按脸宽34归一会缩到119×98、头高约41px，不采用；落格脸宽39、bbox [60,136,194,247]、135×112、最低点（双手与脚跟）贴247、bbox居中root x=128。getup-01 实收1024×1536与锚同源分辨率，按统一比例0.171689（眼行脸宽203对锚195，+4.1%），bbox [71,77,178,247]、108×171、双脚247接地、支撑脚带对齐root、留边71/77。head_normalization 与 scale_note 已写入 cells.json/requests.json；联系表 `stage1/contact/getup-sheet.png` SHA `fec8458d…`。根审通过（root_delegated_by_user，不是用户亲审）：顺序、头向、手撑地/脚底247、头高归一、30/31色、二值Alpha、整帧单连通均过。
- win 两帧：举拳帧朝右、双脚前后分开屈膝，一臂高举过头顶、另一拳收腰，抬头挺胸；收势帧双拳收腰、拳心向内，挺胸抬头。两帧按统一源比例0.171689，眼行宽36/34对锚34；bbox [48,17,195,247]/[57,55,184,247]，站高231（含高举臂）/193，拳顶留17px未裁；脚底247/246接地，支撑脚带对齐root。32/31色、二值Alpha、整帧单连通1、无独立颗粒/无FX、未裁未缩。举拳落在远侧臂、近侧拳收腰，与提示词左右手相反但姿势成立，按实画记录；头高自动30/41受高举臂与抬头影响，按脸宽与目视结构核。联系表 `stage1/contact/win-sheet.png` SHA `83ded5e6…`。根审通过（root_delegated_by_user，不是用户亲审）：举拳/收势成立，拳顶未裁、脚底247/246、眼行36/34在8%内；win-00 提示词与实画臂侧不同按实画记录，不重生成。
- ko 两帧：砸地帧仰面、头朝左、脚朝右，背部着地、一臂甩开撑地、一臂举拳、一腿屈膝抬起、一腿伸展，脸朝上偏右；败姿帧仰面摊平、双臂放松、一腿屈一腿伸，头后仰。两帧实收1774×887/2172×724横幅，按眼行脸宽归一头尺寸：raw260/288→落格35（锚34），scale 0.130769/0.118056（标准的0.7617/0.6876），未按外框拉伸。bbox [22,173,234,247]/[6,177,249,247]，宽213/244、高75/71，最低点均247；ko-01 宽244未超256、留边6/6，无需增格。29/31色、二值Alpha、整帧单连通1、无独立颗粒/无FX、未裁未缩。头高自动6/5受仰躺遮挡，不可用。联系表 `stage1/contact/ko-sheet.png` SHA `203b5227…`。根审通过（root_delegated_by_user，不是用户亲审）：仰面砸地/摊平败姿成立，头左脚右、按脸宽归一、最低点247、ko-01宽244留边6/6完整在格、两帧单连通。
- 最小动作集19项齐：idle(2)、walk_forward(4)、walk_back(4)、dash_start(2)、dash(4)、takeoff(2)、air_rise(1)、air_fall(1)、land(2)、light1(3)、light2(3)、light3(4)、heavy(4)、hit(2)、block(1)、down(2)、getup(2)、win(2)、ko(2)，共47帧；均有原生格、严格4×、2×联系表与 cells.json/requests.json 记录。getup、win、ko 已根审通过（root_delegated_by_user）。未安装、未启动Godot、未提交、无录屏；后续等新指令。
- 连通块口径（2026-11-09 根统一）：技能帧只判人物主体（含贴体光焰/光束）单连通，独立颗粒与已脱手的飞行武器允许。light1-01整帧5块、light1-02整帧14块，light2-01整帧3块、light2-02整帧6块，light3-01整帧3块、light3-02整帧2块，主体均单连通。
- 已拒收：walk_forward-03 首版高抬膝像正步（SHA 153b6de5…，删除后低摆重生成）；dash_start-01 首版后腿跨幅过大、人物贴右边缘（SHA 30e7a021…，删除后收小步幅重生成）；dash-01、dash-03 首版高抬膝且横向偏移约30px（SHA e9c817f4…、2b60a41d…为旧版记录，删除后低摆重生成）；dash-00 首版为离群帧（前倾代理8.9对19–21、与03循环IoU 0.398，删除后重生成）。
- dash-00 现帧前倾代理21.9、03→00 IoU 0.471，站高155比dash-02的169低14px，记为已知差异待实速/实机观察，本轮不再改。land-00 站高182、land-01 屈膝缓冲站高171（−11px，6%），脚底均247接地，护架保持、身体未折叠、非深蹲；land 联系表 SHA `f7bc34a0…`。
- 触地与腾空按实测核对：takeoff-01 后脚掌接地、前脚离地约13px；air_rise 脚底205、air_fall 脚底232，均未触地；land 两帧脚底247。
- 未安装、未接运行时、未启动Godot；720/1080、实速、声音、实机与录屏均未验。root_delegated_by_user 的看片结论不冒充用户亲审。

## 2026-11-10 阶段C 第一批：air_special / taunt / timeout

用户选择“继续加动作/技能”后，从最小动作集19项47帧继续；本批只做 art 与记录，未安装、未启动 Godot、未提交、无录屏。三组共8帧，阶段累计22动作/55帧，本批待根审。

- 身份锚与尺度：仍用 `stage1/idle/frames/pixel-raw-02-official-side-anchor.png` 单参考，256×256、root [128,248]、脚底247、冻结32色、统一源比例0.171689。协调指令中的“standing 223”与赛罗图鉴188、锚188、既有47帧落格基准188冲突；223是奥王原生站高。根已确认 `root_correction_2026_11_10`：223系指令错误，赛罗保持188，身份锚、既有55帧与图鉴均不改，不重落。
- air_special 3帧：起手/蓄光/发射，空中集束射线（游戏改编，不冒充原剧逐帧）。`stage1/air_special/frames/air_special-00-raw.png`…`02-raw.png`；原生格 `stage1/cells/air_special-00-cell.png`…`02-cell.png`。bbox [90,65,178,225]/[117,68,197,225]/[112,73,244,225]，脚底行225（腾空，不贴247），眼行35/35/34对锚34；01主体含贴臂光焰单连通+12颗粒，02主体含光束单连通+15颗粒；02束根接右前臂/拳，接缝0px，束中心y≈138对前臂中心y≈138（差≤1px）。30/32/31色、二值Alpha、未裁未缩。联系表 `stage1/contact/air_special-sheet.png` SHA `0ed01e5e1fc74275e3006e8a8f4b1b66b89af8d271f8d61ec168cbe9d2f33d6c`。
- taunt 3帧：指手挑衅→翻掌招呼→收势回架；原剧口头挑衅“还差两万年呢”。`stage1/taunt/frames/taunt-00-raw.png`…`02-raw.png`；原生格 `stage1/cells/taunt-00-cell.png`…`02-cell.png`。v1头部为双直立尖角+中央冠、v2头部偏小（落格眼行29）均拒收删除；v3眼行35、头高47通过。bbox [56,60,200,247]/[55,65,191,247]/[57,62,186,247]，站高188/183/186，脚底247；taunt-01眼行31对34（-8.8%，转头/侧脸读数偏窄），记已知差异。31/32/31色、二值Alpha、整帧单连通1、无FX。联系表 `stage1/contact/taunt-sheet.png` SHA `da13bb4b8c7c25ec43509e3ec7f98a24017767195df15d628f69b23cc132e023`。
- timeout 2帧：看计时器→低头失战意；非KO，仍站立。`stage1/timeout/frames/timeout-00-raw.png`/`01-raw.png`；原生格 `stage1/cells/timeout-00-cell.png`/`01-cell.png`。bbox [76,60,174,247]/[82,60,175,247]，站高188/188，脚底247；timeout-00眼行30受低头/手挡影响，timeout-01眼行41为低头时头壳最宽读数、不作脸宽；目视头身连续。30/31色、二值Alpha、整帧单连通1、无FX。联系表 `stage1/contact/timeout-sheet.png` SHA `e6c59652c531ef6f7f783a16451fefe522a89f8d8786735adfee09b0783f2d89`。
- 三格能量技能与 special 槽：根确认现有 light1/2/3 实为 special1/2/3（Wide Zero Shot / Emerium Slash / Zero Slugger），保留文件不改名；矩阵的 light1/2/3 语义是轻击一段/二段/三段，另起 `light_combo1/2/3`（3+3+4），不覆盖现有文件。映射写在 `action_expansion.game_slot_mapping`。
- 内容缺口：`content/fighters/ultraman-zero/` 只有 `catalogue_profile.json`，无 MOVES.md、SOUNDS.md、moves/*.json、production_plan.json；`content/combat/skill_library.json` 的 ultraman-zero 为 `skill_ids: []`，status=技能与逐集动作待整理。因此本批“实际招式”依据为既有 README/requests 已签技能、原剧设定与矩阵动作格，不是现成 Zero 招式数据；未写/未改 content。声音不合成，原剧来源任务留在声音批次；`source_kind=episode` 仅用于原剧/电影实际音轨，未核到不冒称。
- 下一步：先做 throw_forward/back（3+3）、intro（3），light_combo1/2/3（3+3+4）另起一批；再按矩阵补普攻/空中普攻/追打/冲刺攻击/反击/起身攻击/爆气/蓄能。每批产出后停根审；同一检查连续3帧不过按返工刹车出诊断。
- 本批未安装、未接运行时、未启动Godot、未提交、无录屏；720/1080、实速、声音、实机均未验。

### 根审与两项确认（2026-11-10）

- 本批 air_special 3、taunt 3、timeout 2 共8帧根审通过，`review_authority=root_delegated_by_user`（不是用户亲审）。已知差异保留：taunt-01 眼行31对锚34（转头/侧脸）、timeout 眼行受低头/手挡影响，不返修；air_special 的独立颗粒按技能帧口径允许。
- `root_correction_2026_11_10`：standing 223 系指令错误，223是奥王站高；赛罗保持188，身份锚、既有55帧与图鉴不改。后续动作继续按188、256格、root [128,248]、脚底247、同一32色板、二值Alpha。
- `game_slot_mapping`：现有 light1/2/3 → special1/2/3（Wide Zero Shot / Emerium Slash / Zero Slugger），保留文件不改名；矩阵 light1/2/3 轻击链 → `light_combo1/2/3`，3+3+4另做，不覆盖现有文件。
- 声音不合成；原剧来源任务留在声音批次。MOVES/SOUNDS/moves/production_plan 的内容缺口先记在本 README，不写/不改 content。

## 2026-11-10 阶段C 第二批：throw_forward / throw_back / intro

根指定的下一批为 throw_forward/back 3+3、intro 3；light_combo 另起一批。本批只做 art 与记录，未安装、未启动 Godot、未提交、无录屏；阶段累计25动作/64帧，本批完成后送根审（结论见下，root_delegated_by_user，不是用户亲审）。

- 身份锚与尺度：仍用 `stage1/idle/frames/pixel-raw-02-official-side-anchor.png` 单参考，256×256、root [128,248]、脚底247、冻结32色、统一源比例0.171689；standing 188 按 `root_correction_2026_11_10`。九帧均二值 Alpha、cropped_pixels=0、整帧4连通=1、无FX；非技能帧整帧单连通。已看严格4×与2×联系表。
- throw_forward 3帧：抓握→收抱蓄力→前送。`stage1/throw_forward/frames/throw_forward-00-raw.png`…`02-raw.png`；原生格 `stage1/cells/throw_forward-00-cell.png`…`02-cell.png`。bbox [54,66,210,247]/[62,65,186,247]/[52,95,210,247]，站高182/183/153，脚底均247；眼行36/35/33对锚34；31色。00双手前伸抓握、01双拳收抱胸前上方、02上身前压双臂向前下方甩出；均不画对手。01 v1（SHA `98edbf55125e66db6dc2a0fcfb317a26e56a049fb3fe65560a7b5343316d6907`，正面构图、眼行头宽301对锚195）、v2（SHA `9d07749fe42f50950438acc70f4f9c134e3605d941135c8e5cd026bf8b8fdf4c`，仍正面、268）拒收删除；按返工刹车改用侧视收抱蓄力方案v3（SHA `fe56d2a5cf2aaccb26d68c489b4fed786f399b1d56e79a13c2f18e3b36d86e63`）通过。
- throw_back 3帧：抓握→转身背起→后送。`stage1/throw_back/frames/throw_back-00-raw.png`…`02-raw.png`；原生格 `stage1/cells/throw_back-00-cell.png`…`02-cell.png`。bbox [45,79,197,247]/[56,75,197,247]/[50,98,183,247]，站高169/173/150，脚底247；眼行37/37/32；31/31/30色。01转身顶点躯干向左后方扭转、胸灯可见，头保持右向侧脸，属身体旋转而非镜头改变，按实画记录不重生成；02上身后仰、双臂向左后方甩出。均不画对手。
- intro 3帧：单膝落地→起身→屈膝护架，末尾与 idle 护架衔接。`stage1/intro/frames/intro-00-raw.png`…`02-raw.png`；原生格 `stage1/cells/intro-00-cell.png`…`02-cell.png`。bbox [71,135,186,247]/[62,84,192,247]/[58,87,186,247]，站高113/164/161，脚底247；intro-00 实收1536×1024横构图，按眼行脸宽273→落格34归一头尺寸（scale 0.124542=标准的0.7254），未按外框拉伸；眼行34/35/32；31/30/29色。intro-01 v1（SHA `62764d23875dfdde71ea723c5757b1b760a1a8b6667b834182eab6545e6e542c`）输出4×4共16格拼图，不是单帧整身人物，拒收删除；v2（SHA `090ca6d2c5722e556dbb398cd6d341d18c09c4a8c5edaf9f0665eee6f85de257`）通过。
- 联系表：`stage1/contact/throw_forward-sheet.png` SHA `43002acc96debf967dd589ffd6e514f27ed87284cf7a84715a2f61eae33606e7`、`throw_back-sheet.png` SHA `4365775db807b1217d5186d74469ae35eb3f7986abc388a4e956e8f2a6aa3ddf`、`intro-sheet.png` SHA `0989c3177467693a95e2d3f9e9cf88dd40b5a4e95898bd57033d21eef811465c`；每帧另有严格4×。
- 记录：`stage1/cells/cells.json`（action_frames 64、action_set_status 25、stage_status=phase_c_batch2_throw_intro_approved）与 `stage1/requests.json`（attempts 85、delivered 25、action_production.status=phase_c_batch2_approved）。拒收项只在 attempts 留 status/reason/SHA，raw 已删除，无备份。
- 未变：light1/2/3 仍为 special1/2/3，不改名；light_combo1/2/3（3+3+4）另起批次，不覆盖现有文件。content 的 MOVES/SOUNDS/moves/production_plan 缺口不变，不写/不改 content；声音不合成，原剧来源任务留在声音批次。
- 下一步：light_combo1/2/3 另起一批；其余矩阵普攻/空中普攻/追打/冲刺攻击/反击/起身攻击/爆气/蓄能按后续批次。每批产出后停根审；同一检查连续3帧不过按返工刹车出诊断。
- 本批未安装、未接运行时、未启动Godot、未提交、无录屏；720/1080、实速、声音、实机均未验。

### 根审通过（2026-11-10，第二批）

- throw_forward 00–02、throw_back 00–02、intro 00–02 共9帧根审通过，`review_authority=root_delegated_by_user`（不是 user_approved，不是用户亲审）。三组三相成立；256格、root x≈128、脚底247、同一32色板、二值Alpha、非技能帧整帧单连通均过。
- 已知差异保留、不返修：throw_back-00/01 眼行37对锚34（+8.8%，低头/拧身侧脸读数偏宽）；throw_back-01 转身顶点躯干向左后方扭转、胸灯可见，头保持右向侧脸，属身体旋转而非镜头改变；intro-00 实收1536×1024横构图，按眼行脸宽273→落格34归一，scale 0.124542（标准的0.7254），未按外框拉伸。
- 状态已写入 `stage1/cells/cells.json`（9帧 review_status=approved、review_authority=root_delegated_by_user；stage_status=phase_c_batch2_throw_intro_approved；action_expansion.status=batch2_approved）与 `stage1/requests.json`（delivered 三项 review_status=approved；action_production.status=phase_c_batch2_approved；batch.review_status=approved）。
- 下一批 light_combo1/2/3（3+3+4），与已映射为 special1/2/3 的现有 light1/2/3 分开，不覆盖旧文件；之后其余矩阵普攻、空中普攻、追打、冲刺攻击、反击、起身攻击、爆气、蓄能按后续批次。content 缺口与原剧声音任务不变，不合成声音。
- 未安装、未启动Godot、未提交、无录屏；720/1080、实速、声音、实机均未验。

## 2026-11-10 阶段C 第三批：light_combo1/2/3（轻击链）

根指定的轻击链：light_combo1/2/3 共10帧（3+3+4），语义为轻击一段/二段/三段；非技能帧，整帧单连通，不加光效或独立颗粒。与已映射为 special1/2/3 的现有 light1/2/3 分开，不覆盖旧文件。本批只做 art 与记录，未安装、未启动 Godot、未提交、无录屏；阶段累计28动作/74帧，本批已根审通过（review_status=approved，root_delegated_by_user，不是用户亲审）。

- 身份锚与尺度：仍用 `stage1/idle/frames/pixel-raw-02-official-side-anchor.png` 单参考，256×256、root [128,248]、脚底247、同一32色板、二值Alpha、统一源比例0.171689；standing 188 按 `root_correction_2026_11_10`。十帧均 cropped_pixels=0、整帧4连通=1、无FX/颗粒；已看严格4×与2×联系表。
- light_combo1 3帧：起手→直拳→收拳。`stage1/light_combo1/frames/light_combo1-00-raw.png`…`02-raw.png`；原生格 `stage1/cells/light_combo1-00-cell.png`…`02-cell.png`。bbox [56,63,185,247]/[50,61,196,247]/[57,60,184,247]，站高185/187/188，脚底均247；眼行34/36/34对锚34；32/29/31色。前手直拳完全伸展、肩髋前送，收拳回护架。
- light_combo2 3帧：换架→直拳→收拳。`stage1/light_combo2/frames/light_combo2-00-raw.png`…`02-raw.png`；原生格 `stage1/cells/light_combo2-00-cell.png`…`02-cell.png`。bbox [56,61,187,247]/[49,66,197,247]/[58,59,186,247]，站高187/182/189，脚底247；眼行31/34/35；31/32/32色。后手直拳随转体前送；2-00 眼行31对34（−8.8%，转头/护拳贴近读数偏窄）记已知差异。
- light_combo3 4帧：蓄力→转髋起拳→上勾拳→收势。`stage1/light_combo3/frames/light_combo3-00-raw.png`…`03-raw.png`；原生格 `stage1/cells/light_combo3-00-cell.png`…`03-cell.png`。bbox [58,103,184,247]/[57,55,182,247]/[54,50,179,247]/[56,60,183,247]，站高145/193/198/188，脚底247；眼行34/35/37/34；30/32/31/30色。3-02 眼行37对34（+8.8%，上勾拳贴近头部读数偏宽），头高自动77为同因伪值；记已知差异，目视头冠与双镖连续。
- 联系表：`stage1/contact/light_combo1-sheet.png` SHA `2b5f147c2dfd334545efa9cc737f89999111792f6672377f0564aecea6a59c67`、`light_combo2-sheet.png` SHA `84901c9d5c9f1937c9489aa36e6f90dc7f208b67ed03e27918d5ac668b59e213`、`light_combo3-sheet.png` SHA `58b00ae0568c07a68d9d6c12cd63af4fb2d059a839cea6b20bca693b0cb1f69c`；每帧另有严格4×。
- 记录：`stage1/cells/cells.json`（action_frames 74、action_set_status 28、stage_status=phase_c_batch3_light_combo_approved；`game_slot_mapping.light_combo1/2/3` 已更新为 approved_root_delegated_by_user_2026_11_10）与 `stage1/requests.json`（attempts 95、delivered 28、action_production.status=phase_c_batch3_approved）。现有 light1/2/3（special1/2/3）文件未改、未覆盖。
- 未变：content 的 MOVES/SOUNDS/moves/production_plan 缺口不变，不写/不改 content；声音不合成，原剧来源任务留在声音批次。
- 下一步：按矩阵顺序做普攻（launcher 7、spin_heavy 7、crush 9、tackle 8）、空中普攻（vertical_light 4、vertical_heavy 5、diagonal_light 4、diagonal_heavy 5、air_crush 6、dive 5）、冲刺攻击（dash_light 5、dash_heavy 6），组数与帧数按矩阵。每批产出后停根审；同一检查连续3帧不过按返工刹车出诊断。
- 本批未安装、未接运行时、未启动Godot、未提交、无录屏；720/1080、实速、声音、实机均未验。

### 根审通过（2026-11-10，第三批）

- light_combo1 00–02、light_combo2 00–02、light_combo3 00–03 共10帧根审通过，`review_authority=root_delegated_by_user`（不是 user_approved，不是用户亲审）。三组轻击链起手/直拳/收拳、换架/直拳/收拳、蓄力/转髋起拳/上勾拳/收势成立；256格、root x≈128、脚底247、同一32色板、二值Alpha、非技能帧整帧单连通均过。
- 已知差异保留、不返修：light_combo2-00 眼行31对锚34（−8.8%，转头/护拳贴近读数偏窄）；light_combo3-02 眼行37（+8.8%，上勾拳贴近头部读数偏宽），头高自动77为同因伪值。
- 状态已写入 `stage1/cells/cells.json`（10帧 review_status=approved、review_authority=root_delegated_by_user；stage_status=phase_c_batch3_light_combo_approved；action_expansion.status=batch3_approved；`game_slot_mapping.light_combo1/2/3`=approved_root_delegated_by_user_2026_11_10）与 `stage1/requests.json`（delivered 三项 review_status=approved；action_production.status=phase_c_batch3_approved；batch.review_status=approved）。
- 下一批按矩阵顺序做普攻、空中普攻、冲刺攻击；现有 light1/2/3（special1/2/3）不覆盖。content 缺口与原剧声音任务不变，不合成声音。
- 未安装、未启动Godot、未提交、无录屏；720/1080、实速、声音、实机均未验。
## 2026-11-10 阶段C 第四批：矩阵普攻 / 空中普攻 / 冲刺攻击

根指定的下一批：按矩阵顺序做普攻、空中普攻、冲刺攻击，组数与帧数按矩阵。本批12组71帧：launcher 7、spin_heavy 7、crush 9、tackle 8；vertical_light 4、vertical_heavy 5、diagonal_light 4、diagonal_heavy 5、air_crush 6、dive 5；dash_light 5、dash_heavy 6。只做 art 与记录，未安装、未启动 Godot、未提交、无录屏；阶段累计40动作/145帧，出2×联系表后停根审；本批已根审通过（见下）。

- 身份锚与尺度：仍用 `stage1/idle/frames/pixel-raw-02-official-side-anchor.png` 单参考，256×256、root [128,248]、同一冻结32色板、二值Alpha、非技能帧整帧4连通=1、无FX/颗粒；落格后仅清除≤3px独立杂点，人物未改。launcher/spin_heavy 按眼行脸宽逐帧归一到锚34；其余组因拳/臂贴近头部使脸宽读数失真，改用组内固定比例：crush 0.13765、tackle 0.1441、vertical_light 0.14561、vertical_heavy 0.14079、diagonal_light 0.14687、diagonal_heavy 0.1425、air_crush 0.136、dive 0.1323、dash_light 0.145、dash_heavy 0.1453。接地组脚底247；空中组（vertical_light/heavy、diagonal_light/heavy、air_crush、dive）与 dash_heavy-02..04 行225。

- 普攻·升击，7相：起手蓄力→蹬地起势→升拳→命中顶点→随势上扬→收拳回落→回护架。`stage1/launcher/frames/launcher-00-raw.png`…`launcher-06-raw.png`；原生格 `stage1/cells/launcher-00-cell.png`…`launcher-06-cell.png`。bbox [67,79,210,247]/[52,89,193,247]/[69,78,174,247]/[120,57,212,247]/[60,18,170,247]/[67,65,197,247]/[76,64,185,247]，高度169/159/170/191/230/183/184，脚底247/247/247/247/247/247/247；眼行脸宽34/34/34/34/34/34/35对锚34；27/28/26/26/25/26/25色。比例 0.131274/0.157407/0.116438/0.130769/0.155963/0.144068/0.145923（逐帧眼行脸宽归一）。
- 普攻·回旋重击，7相：起手蓄力→转体甩拳→横扫→命中→随势回旋→收势→回护架。`stage1/spin_heavy/frames/spin_heavy-00-raw.png`…`spin_heavy-06-raw.png`；原生格 `stage1/cells/spin_heavy-00-cell.png`…`spin_heavy-06-cell.png`。bbox [46,43,218,247]/[54,73,195,247]/[33,50,216,247]/[51,77,241,247]/[41,84,206,247]/[55,82,199,247]/[74,66,201,247]，高度205/175/198/171/164/166/182，脚底247/247/247/247/247/247/247；眼行脸宽34/34/35/34/34/34/34对锚34；25/25/26/30/29/28/26色。比例 0.165049/0.136/0.154545/0.170854/0.141079/0.141079/0.14346（逐帧眼行脸宽归一）。
- 普攻·超重击，9相：起手→举臂→蓄满→下砸→砸中→砸低→触底→起身→回护架。`stage1/crush/frames/crush-00-raw.png`…`crush-08-raw.png`；原生格 `stage1/cells/crush-00-cell.png`…`crush-08-cell.png`。bbox [60,74,191,247]/[83,72,187,247]/[79,79,191,247]/[93,73,228,247]/[80,71,212,247]/[57,101,213,247]/[95,101,211,247]/[91,77,182,247]/[67,71,192,247]，高度174/176/169/175/177/147/147/171/177，脚底247/247/247/247/247/247/247/247/247；眼行脸宽35/30/57/60/64/79/66/33/35对锚34；24/22/23/23/27/26/28/26/23色。比例 0.13765/0.13765/0.13765/0.13765/0.13765/0.13765/0.13765/0.13765/0.13765（组内固定）。
- 普攻·突进撞击，8相：起手蓄力→蹬地前冲→前冲→撞击→冲势前送→刹停→回正→回护架。`stage1/tackle/frames/tackle-00-raw.png`…`tackle-07-raw.png`；原生格 `stage1/cells/tackle-00-cell.png`…`tackle-07-cell.png`。bbox [40,103,204,247]/[52,106,227,247]/[30,104,230,247]/[44,110,238,247]/[8,112,199,247]/[52,64,193,247]/[85,63,192,247]/[55,71,197,247]，高度145/142/144/138/136/184/185/177，脚底247/247/247/247/247/247/247/247；眼行脸宽69/58/80/70/84/34/34/37对锚34；24/26/23/24/26/22/24/25色。比例 0.1441/0.1441/0.1441/0.1441/0.1441/0.1441/0.1441/0.1441（组内固定）。
- 空中普攻·垂直跳轻击，4相：空中收腿起手→出拳→拳到位→收拳。`stage1/vertical_light/frames/vertical_light-00-raw.png`…`vertical_light-03-raw.png`；原生格 `stage1/cells/vertical_light-00-cell.png`…`vertical_light-03-cell.png`。bbox [80,81,166,225]/[102,58,249,225]/[88,53,249,225]/[104,45,165,225]，高度145/168/173/181，脚底225/225/225/225；眼行脸宽29/37/40/31对锚34；26/27/28/24色。比例 0.14561/0.14561/0.14561/0.14561（组内固定）。
- 空中普攻·垂直跳重击，5相：空中举拳→蓄力→下砸→砸中→收势。`stage1/vertical_heavy/frames/vertical_heavy-00-raw.png`…`vertical_heavy-04-raw.png`；原生格 `stage1/cells/vertical_heavy-00-cell.png`…`vertical_heavy-04-cell.png`。bbox [110,67,181,225]/[86,66,180,225]/[116,57,249,225]/[119,59,239,225]/[97,31,169,225]，高度159/160/169/167/195，脚底225/225/225/225/225；眼行脸宽63/49/72/86/36对锚34；25/25/29/26/25色。比例 0.14079/0.14079/0.14079/0.14079/0.14079（组内固定）。
- 空中普攻·斜跳轻击，4相：起跳收腿→膝撞→顶点→收势。`stage1/diagonal_light/frames/diagonal_light-00-raw.png`…`diagonal_light-03-raw.png`；原生格 `stage1/cells/diagonal_light-00-cell.png`…`diagonal_light-03-cell.png`。bbox [105,46,251,225]/[123,36,239,225]/[96,39,251,225]/[92,17,175,225]，高度180/190/187/209，脚底225/225/225/225；眼行脸宽39/33/35/32对锚34；28/29/27/26色。比例 0.14687/0.14687/0.14687/0.14687（组内固定）。
- 空中普攻·斜跳重击，5相：起跳→踢出→飞踢→命中→收腿。`stage1/diagonal_heavy/frames/diagonal_heavy-00-raw.png`…`diagonal_heavy-04-raw.png`；原生格 `stage1/cells/diagonal_heavy-00-cell.png`…`diagonal_heavy-04-cell.png`。bbox [101,51,251,225]/[27,81,243,225]/[36,83,251,225]/[8,98,251,225]/[96,57,169,225]，高度175/145/143/128/169，脚底225/225/225/225/225；眼行脸宽73/30/33/31/31对锚34；26/26/29/26/26色。比例 0.1425/0.1425/0.1425/0.1425/0.1425（组内固定）。
- 空中普攻·空中超重击，6相：空中举拳→蓄力→下砸→砸中→触底→收势。`stage1/air_crush/frames/air_crush-00-raw.png`…`air_crush-05-raw.png`；原生格 `stage1/cells/air_crush-00-cell.png`…`air_crush-05-cell.png`。bbox [94,40,175,225]/[46,57,181,225]/[118,93,251,225]/[111,59,226,225]/[57,72,174,225]/[106,28,188,225]，高度186/169/133/167/154/198，脚底225/225/225/225/225/225；眼行脸宽46/34/75/64/87/33对锚34；30/25/27/28/28/28色。比例 0.136/0.136/0.136/0.136/0.136/0.136（组内固定）。
- 空中普攻·俯冲踢，5相：起跳→俯冲→踢出→命中→收腿。`stage1/dive/frames/dive-00-raw.png`…`dive-04-raw.png`；原生格 `stage1/cells/dive-00-cell.png`…`dive-04-cell.png`。bbox [102,65,174,225]/[4,60,163,225]/[4,94,198,225]/[4,91,197,225]/[70,65,163,225]，高度161/166/132/135/161，脚底225/225/225/225/225；眼行脸宽34/71/85/81/38对锚34；26/27/28/28/25色。比例 0.1323/0.1323/0.1323/0.1323/0.1323（组内固定）。
- 冲刺攻击·冲刺轻击，5相：冲刺起手→出拳→命中→收拳→回护架。`stage1/dash_light/frames/dash_light-00-raw.png`…`dash_light-04-raw.png`；原生格 `stage1/cells/dash_light-00-cell.png`…`dash_light-04-cell.png`。bbox [17,102,207,247]/[36,102,238,247]/[18,104,236,247]/[33,102,211,247]/[69,61,182,247]，高度146/146/144/146/187，脚底247/247/247/247/247；眼行脸宽73/36/91/102/32对锚34；26/24/26/25/22色。比例 0.145/0.145/0.145/0.145/0.145（组内固定）。
- 冲刺攻击·冲刺重击，6相：起跑→蹬地→飞踢→命中→收腿→落地。`stage1/dash_heavy/frames/dash_heavy-00-raw.png`…`dash_heavy-05-raw.png`；原生格 `stage1/cells/dash_heavy-00-cell.png`…`dash_heavy-05-cell.png`。bbox [34,102,232,247]/[81,65,251,247]/[34,82,251,225]/[33,81,251,225]/[91,41,194,225]/[66,78,196,247]，高度146/183/144/145/185/170，脚底247/247/225/225/225/247；眼行脸宽103/33/33/36/70/72对锚34；28/28/30/29/29/25色。比例 0.1453/0.1453/0.1453/0.1453/0.1453/0.1453（组内固定）。

- 联系表（每帧另有严格4×）：
  - `stage1/contact/launcher-sheet.png` SHA `ba00125cb6c54342c8bf44dbdb6985b40969b5306d3c8c62b73d569bfff6c66a`。
  - `stage1/contact/spin_heavy-sheet.png` SHA `da49b4c11465c106bc825cee8441cc6aa00a06e89dc55d8cef433abd0556424e`。
  - `stage1/contact/crush-sheet.png` SHA `cbfe907f111a8b324e163c5b69bb4ece9c1635025f682fbe622ac0abf40f91c6`。
  - `stage1/contact/tackle-sheet.png` SHA `296aa7848ace62116b6fdce06f32ef9f0083d1d0cf03662a1ca08931e194701e`。
  - `stage1/contact/vertical_light-sheet.png` SHA `45f27c07ad4d5c29849b45fd74bd202468ea2514b1796ef769d43b166927c391`。
  - `stage1/contact/vertical_heavy-sheet.png` SHA `4d25112833f9af6f5a40f1d0e2467d5437982eaf388f3d86ea54cc4884f65b27`。
  - `stage1/contact/diagonal_light-sheet.png` SHA `78baae747fd38542d0b94af11d634f8ecc36146553fac805575eb7531fc83a5e`。
  - `stage1/contact/diagonal_heavy-sheet.png` SHA `f9c751373b5f487ebaf0b9db5a813d5abcb3cd506db45cccb10178586a5ef095`。
  - `stage1/contact/air_crush-sheet.png` SHA `a50ebdae0a32ccb6100c6f150a7414dfcd80e4cb2ea9c915aa5131a7703b0a88`。
  - `stage1/contact/dive-sheet.png` SHA `a85f32c2169523f84302e75ca4071b04d2a30cb04e4b013028cc5a77c295a474`。
  - `stage1/contact/dash_light-sheet.png` SHA `eb0a19d196a21057f977a2197f119c0428714845ab07de942af5005eb6a46fa8`。
  - `stage1/contact/dash_heavy-sheet.png` SHA `daf0d9f9c6fb94b60bafc0fe9730406cca37fbe4bf9e8c0ee0ea95200736f383`。

- 记录：`stage1/cells/cells.json`（action_frames 145、action_set_status 40、stage_status=phase_c_batch4_normal_air_dash_approved；action_expansion.status=batch4_approved）与 `stage1/requests.json`（attempts 181、delivered 40、action_production.status=phase_c_batch4_approved；batch.review_status=approved）。本批新增 accepted attempts 71 条、rejected 15 条；MCP 实收尺寸/Alpha/SHA 均按实际返回记录。dash_heavy-02 的 MCP 调用直接返回保存路径、未返回生成编号，已注明。
- 拒收候选（均已按SHA记录后删除/覆盖，无备份）：launcher-05 v1 `7d523a780eb2cace0d08c4bc243ce13150c8feed85bb68dcf8a6b4168454de04`（瘦长/腿长）、launcher-06 v1 `2e6d81e3149bb5d3b78735f29799c1346b86b389d468d6a4b9f94c3306746d72`、spin_heavy-03 v1 `0ca64dc667b2…`、spin_heavy-05 v1/v2、spin_heavy-06 v1–v4、vertical_heavy-00 v1 `2281ee4a4e893093aa3ac77c19d0b339028d32ff988c9e057baa2ece43f2eeb0`（顶部裁切）/v2 `5492b8d0b9b8def3f25e8611e02d8a480d40137a0489113556b938f22f77440a`（过小）、dive-00..03 v1（俯冲角度不足）。完整SHA与理由见 requests.json attempts。
- 已知差异保留、不返修：自动眼行脸宽在拳/臂贴近头部时读数偏大（如 crush-02..06、tackle-00..04、diagonal_heavy-00、air_crush-00/02/03/04、dive-01/02/03、dash_light-00/02/03、dash_heavy-00/04/05），不作为头宽比较；目视联系表头冠与双镖连续、体量连续。宽姿态帧按4px边距水平限位（diagonal_light-00/02、diagonal_heavy-00/02/03、air_crush-02、dive-01/02/03、dash_heavy-01/02/03 等），root x不为128，人物完整未裁，已在各帧 flags/horizontal_fit 记录。launcher/spin_heavy 首版瘦长或过深蹲、vertical_heavy-00 v1/v2、dive-00..03 v1 已拒收重生成。
- 未变：现有 light1/2/3（special1/2/3）与 light_combo1/2/3 文件不改不覆盖；content 的 MOVES/SOUNDS/moves/production_plan 缺口不变，不写/不改 content；声音不合成，原剧来源任务留在声音批次。
- 下一步：本批已根审通过（见下）；剩余矩阵动作（追打、反击、起身攻击、爆气、蓄能等）按下一批。同一检查连续3帧不过按返工刹车出诊断。
- 本批未安装、未接运行时、未启动Godot、未提交、无录屏；720/1080、实速、声音、实机均未验。

### 根审通过（2026-11-10，第四批）

- 第四批12组71帧根审通过，`review_authority=root_delegated_by_user`（不是 user_approved，不是用户亲审）。launcher 7、spin_heavy 7、crush 9、tackle 8；vertical_light 4、vertical_heavy 5、diagonal_light 4、diagonal_heavy 5、air_crush 6、dive 5；dash_light 5、dash_heavy 6 均成立；256格、同一32色板、二值Alpha、非技能帧整帧单连通均过。
- 已知差异保留、不返修：手臂贴近头部时自动眼行脸宽读数偏大，不作头宽比较；宽姿态帧按4px边距水平限位、root x不为128，人物完整未裁；dash_heavy-02 MCP未返回生成编号；均不缩头、不重生成。
- 状态已写入 `stage1/cells/cells.json`（71帧 review_status=approved、review_authority=root_delegated_by_user；stage_status=phase_c_batch4_normal_air_dash_approved；action_expansion.status=batch4_approved；game_slot_mapping.batch4_matrix_actions=approved_root_delegated_by_user_2026_11_10）与 `stage1/requests.json`（delivered 12项 review_status=approved；action_production.status=phase_c_batch4_approved；batch.review_status=approved）。
- 下一批按矩阵补追打、反击、起身攻击、爆气、蓄能；每批产出后停根审。现有 light1/2/3（special1/2/3）与 light_combo1/2/3 不覆盖；content 缺口与原剧声音任务不变，不合成声音。
- 未安装、未启动Godot、未提交、无录屏；720/1080、实速、声音、实机均未验。

## 第五批：追打、反击、起身攻击、爆气、蓄能（2026-11-10）

- 用户 2026-11-10 指示：评审自动通过，不再逐批停等根审；每批机器门通过后直接按 `root_delegated_by_user` 签署并继续，不是 user_approved，不是用户亲审。本批 13 组 59 帧按此签署：追打 4 组 17 帧（chase_takeoff 3、chase_light1 4、chase_light2 4、chase_end 6）、反击 3 组 17 帧（back_counter 6、dodge_counter 5、guard_counter 6）、起身攻击 2 组 11 帧（wake_low 5、wake_mid 6）、爆气 1 组 5 帧（burst）、蓄能 3 组 9 帧（charge_start 3、charge 4、charge_stop 2）。
- 身份锚仍为 `stage1/idle/frames/pixel-raw-02-official-side-anchor.png`（SHA `5f4651673a90f08056a250fea9a6f68ad339501a615658a183a7d07d3791dec3`，1024×1536），每帧只引该一张；256×256 格、root [128,248]、脚底 247（腾空相 225）、冻结 32 色板、二值 Alpha；`forge_backend._kcentroid_downscale(detail_bias=False)` + Alpha128 硬化 + 整图最近色映射；4px 边距水平限位，`cropped_pixels=0`。
- 组内统一固定比例，按本组原生眼行脸宽 34px 归一，不逐帧缩放：chase_takeoff 34/218=0.1559633028、chase_light1 34/201=0.1691542289、chase_light2 34/199=0.1708542714、chase_end 34/218=0.1559633028、back_counter 34/201=0.1691542289、dodge_counter 34/197=0.1725888325、guard_counter 34/195=0.1743589744、wake_low 34/197=0.1725888325、wake_mid 34/197=0.1725888325、burst 34/203=0.1674876847、charge_start 34/199=0.1708542714、charge 34/199=0.1708542714、charge_stop 34/197=0.1725888325。
- 落格实测（bbox 含端点 / 高度 / 脸宽 / 色数）：chase_takeoff [81,118,171,247]/[123,45,235,225]/[103,92,170,225]，h130/181/134，脚底247/225/225，脸宽34/35/29，31/29/30色；chase_light1 [96,88,176,225]/[102,75,196,225]/[118,47,251,225]/[89,81,173,225]，h138/151/179/145，脚底225，脸宽34/35/34/34，32/31/31/32色，02触发4px限位；chase_light2 [80,78,177,225]/[122,49,241,225]/[122,58,215,225]/[97,74,178,225]，h148/177/168/152，脚底225，脸宽35/34/33/34，32/30/30/31色；chase_end [69,71,163,225]/[95,91,162,225]/[67,115,234,225]/[4,109,184,225]/[87,82,161,225]/[67,96,184,247]，h155/135/111/117/144/152，脚底225×5后247，脸宽30/45/64/34/48/35，31/31/31/31/30/31色，03触发限位；back_counter [72,72,196,247]/[116,59,208,247]/[113,65,251,247]/[87,77,226,247]/[106,62,179,247]/[57,63,182,247]，h176/189/183/171/186/185，脚底247，脸宽35/33/34/35/34/33，32/30/31/31/31/31色，02触发限位；dodge_counter [74,92,175,247]/[56,58,184,247]/[55,58,190,247]/[54,63,192,247]/[87,58,166,247]，h156/190/190/185/190，脚底247，脸宽34/34/35/32/35，30/32/31/30/31色；guard_counter [55,57,186,247]/[50,80,187,247]/[52,58,187,247]/[54,60,186,247]/[54,57,186,247]/[57,57,186,247]，h191/168/190/188/191/191，脚底247，脸宽34/34/36/37/35/35，32/30/30/32/32/31色；wake_low [43,121,237,247]/[25,109,248,247]/[64,134,200,247]/[70,109,221,247]/[61,58,184,247]，h127/139/114/139/190，脚底247，脸宽44/42/36/34/34，31/30/31/30/31色；wake_mid [46,87,204,247]/[63,112,199,247]/[101,30,204,247]/[105,63,250,247]/[80,58,171,247]/[63,60,182,247]，h161/136/218/185/190/188，脚底247，脸宽46/39/39/34/36/34，32/31/32/31/29/29色；burst [93,72,170,247]/[52,41,190,247]/[39,69,198,247]/[38,65,194,247]/[59,64,184,247]，h176/207/179/183/184，脚底247，脸宽45/40/37/34/34，31/32/31/30/31色；charge_start [57,61,185,247]/[57,60,184,247]/[61,61,184,247]，h187/188/187，脚底247，脸宽35/35/34，30/31/31色；charge [58,61,186,247]/[62,61,181,247]/[67,44,184,247]/[57,68,185,247]，h187/187/204/180，脚底247，脸宽34/34/35/35，31/32/31/31色；charge_stop [57,58,186,247]/[57,59,185,247]，h190/189，脚底247，脸宽34/35，31/29色。
- 2×联系表（SHA-256）：chase_takeoff `b38f8ff190fa3382e206d741d0716baa0c0dcb28d48c9a711ee5bfa351947023`、chase_light1 `c584225c581b6771edc5d2faffe6d2580318988ce1baabb99e4410b4191f9f7c`、chase_light2 `d67a4763ac8606131c7d467cac9c0573ec3e399e5950872c1efac00d6d7e72b6`、chase_end `46875cac74d1412f98e957687aa4300e1ecf2600ccb2b5acbde95ebdbec19acf`、back_counter `22065146336a178f8c3a1d503da152e39966b8757cd92fbef20450444c260a17`、dodge_counter `2c8a770e03ba21652adb3e846e898a0a198c53bd8f5482520d70e740bef2d483`、guard_counter `aeb584ac611401db4120ee47994c0a5bd69de03331e1e1f841a63839331cbc1f`、wake_low `d8544c64de01d59c4c449a00fab9142a0e250673e6d61e91f7b6060bbec72d44`、wake_mid `5b94e4ff8523622f3c0a431d8d748be6268e48749ba159d7000244b13cc590d8`、burst `262a295650dfe502ec00c2dc494b7b51b14fb38fa141d92d39374fdcce2aad31`、charge_start `0dfd9073a333fc31eed9151aab143618d9ab54295863af7cf7bd093ba7f647c9`、charge `25e650331a9cfc7f44d7be21f96ef49790ab21af8a157ad4cf5ef6231cf716a2`、charge_stop `12f52444ab7bb9c7b97b9cae4a92928334c47bd0b272b62b49780e04d9191af2`。
- 拒收与失败（已记录 SHA/原因并删除或覆盖，无备份）：charge-01 v1 与 charge-02 v1 输出为多格拼图（16/24 个字符块），SHA `9ac597d885ec0558cb9443adc278a95568077832a6bd8c4ca19fb6c8ad59186a` / `707d829ddb03825ddf65a0c401c897af33ab016559ecc2c8141b5f9b7df70a93`，加“只画单帧、不拼网格”后重生成；guard_counter-02/03 v1 读作双手交叉格挡，SHA `8dfcd6106e353eb71942c6ec856d4cffbbcaf5f0db769faafcea20563e1d611a` / `d19de00218ac2ed2c4751c18223f70eca72bc409506b400b75fbe3d6ed647e96`，改为单臂肘/前臂推进的提示后重生成；charge_start-02 首调 MCP 超时返回 b64_json 无文件（id image-65174-562），记为失败后重生成。guard_counter-02/03 v2 仍实际读作前臂横推反击，非字面肘尖，属同一问题两种修法后的保留差异。
- 已知差异保留、不返修：自动眼行脸宽在拳/臂贴近头部时读数偏大（chase_end-01/02/04、wake_low-00/01、wake_mid-00/01/02、burst-00/01/02 等），不作头宽比较；chase_takeoff-02 读数 29（−14.7%）为前景手臂遮挡，目视头身正常。chase_end-02/03 是水平扑击式下砸；wake_low-01 读作侧向撑起而非“前腿收在身下”；charge-02 高 204 为蓄能循环的直立高相。均完整未裁、未缩头、未重生成。
- 已写入 `stage1/cells/cells.json`（action_frames 204、action_set_status 53；59 帧 review_status=approved、review_authority=root_delegated_by_user；stage_status=phase_c_batch5_approach_counter_wake_burst_charge_approved；action_expansion.status=batch5_approved）与 `stage1/requests.json`（attempts 245、delivered 53 项；action_production.status=phase_c_batch5_approved；batch 为 phase_c_batch5，rejected_count=4、failed_count=1；batch1–batch4 保留）。
- 爆气与蓄能只做人物整帧；Q 蓄气圈、爆气冲击波按已装机约定为独立运行时附加效果，未烘焙进本批人物帧，因此非技能帧整帧 4 连通=1。
- 未安装、未启动Godot、未提交、无录屏；720/1080、实速、声音、实机均未验。content 与声音未改。
- 下一批按矩阵：下蹲攻击 4 组 24 帧（下段轻击4/扫腿7/滑铲8/低姿光弹5）、空中投技6、空中光弹5、冲刺擒抱6；机器门通过后按同一授权签署继续。

## 第六批：下蹲攻击、空中投技/光弹、冲刺擒抱（2026-11-10）

- 按用户 2026-11-10“评审自动通过、机器门通过后直接按 `root_delegated_by_user` 签署并继续”的指示，本批 7 组 41 帧签署为 approved；`review_authority=root_delegated_by_user`，不是 user_approved，不是用户亲审。分组：下蹲 4 组 24 帧（crouch_light 4、sweep 7、slide 8、low_pulse 5）、air_throw 6、air_pulse 5、dash_throw 6。
- 身份锚仍为 `stage1/idle/frames/pixel-raw-02-official-side-anchor.png`（SHA `5f4651673a90f08056a250fea9a6f68ad339501a615658a183a7d07d3791dec3`），每帧只引该一张；256×256 格、root [128,248]、接地组脚底 247、腾空组（air_throw/air_pulse）脚底 225、冻结 32 色板、二值 Alpha；`forge_backend._kcentroid_downscale(detail_bias=False)` + Alpha128 硬化 + 整图最近色映射；4px 边距水平限位，`cropped_pixels=0`。
- 组内统一固定比例，按各组原始眼行脸宽归一：crouch_light 34/201=0.1691542289、sweep 34/225=0.1511111111、slide 34/232=0.1465517241、low_pulse 34/209=0.1626794258、air_throw 34/207=0.1642512077、air_pulse 34/205=0.1658536585、dash_throw 34/221=0.1538461538。整组共用同一 scale，不逐帧缩放。
- 落格实测（bbox 含端点 / 高度 / 脸宽 / 色数）：crouch_light [56,108,183,247]/[60,109,204,247]/[58,100,190,247]/[69,93,176,247]，h140/139/148/155，脚底247，脸宽37/33/35/35，31/29/31/32色；sweep [70,126,184,247]/[46,120,220,247]/[40,120,228,247]/[51,128,236,247]/[53,118,251,247]/[74,126,175,247]/[89,112,172,247]，h122/128/128/120/130/122/136，脚底247，脸宽31/36/37/39/34/31/34，30/32/31/31/31/31/31色，04触发4px限位；slide [45,136,179,247]/[22,139,209,247]/[28,131,226,247]/[20,131,224,247]/[30,141,232,247]/[66,133,194,247]/[44,107,183,247]/[62,118,180,247]，h112/109/117/117/107/115/141/130，脚底247，脸宽38/97/37/35/36/32/32/32，31/31/31/30/31/30/31/31色；low_pulse [78,96,179,247]/[54,97,185,247]/[60,122,194,247]/[46,108,210,247]/[56,99,182,247]，h152/151/126/140/149，脚底247，脸宽39/34/34/36/34，31/28/31/31/30色；air_throw [75,72,251,225]/[75,74,166,225]/[94,66,207,225]/[64,77,251,225]/[123,67,241,225]/[110,78,177,225]，h154/152/160/149/159/148，脚底225，脸宽40/36/34/34/35/34，32/30/30/31/30/31色，00/03触发限位；air_pulse [108,72,181,225]/[102,49,214,225]/[117,73,227,225]/[114,54,251,225]/[113,83,177,225]，h154/177/153/172/143，脚底225，脸宽34/33/31/36/33，31/29/31/32/30色，03触发限位；dash_throw [15,106,224,247]/[42,114,228,247]/[60,101,179,247]/[43,112,245,247]/[64,114,249,247]/[71,110,210,247]，h142/134/147/136/134/138，脚底247，脸宽34/34/32/33/55/32，31/30/31/32/32/30色。全部 4 连通=1、未裁、未缩。
- 2×联系表（SHA-256）：crouch_light `f927e3a3a800fedce91f50add6a003ccf998dbab37da05c2b3d646791ab7c150`、sweep `8c9346d7653e544126ea1d78c68e342faf5faec77cc37b838cb411464ced82da`、slide `23ae2c77a49273cd56353025faa461df8c3eb62f306016663f862f7ace1b2110`、low_pulse `c6e47d72b98995e8554017c59ccebc1bc77401f07fc789ac6b64887276e4562d`、air_throw `ce39a23c84d26dec6769fabc547190062ae544b0fcb29b9450fad67fa581c3ad`、air_pulse `499adfed47ca89453cd64915671e47ad74c98cde07d5777b75d9b565bf7a781f`、dash_throw `9bf606ddc51bd08b748df5f2eb3f4d64b74785ab46f608793cf9ef31b3134daf`。
- 拒收：air_pulse-01 v1 的“收手蓄势”实画为手臂前伸并在手里带一枚青色能量球，落格后为 2 个连通块，与蓄势相和后续发射相断连；SHA `64361ab935186368e3dd820ee4cbe3cec6f62622695618eed00ce5ee8eaf6cc1`，生成编号 image-65174-665，已删除。重生成 v2（image-65174-687）为屈肘收手、无能量球，单连通通过；本批无其它拒收或失败。
- 已知差异保留、不返修：自动眼行脸宽在手臂/拳贴近头部时读数偏大——crouch_light-00 37、sweep-03 39、low_pulse-00 39、air_throw-00 40、air_pulse-03 36、dash_throw-04 55，slide-01 读到 97 属红色纹路/手臂混入，均不作头宽比较；crouch_light-01/02 实画为低位前冲直击、后腿伸展，不是全程深蹲；sweep-04 按 4px 边距水平限位、root x 不为 128，人物完整未裁；slide 低姿帧高 107–117、起身相高 130–141，全组同一 scale，不逐帧放大；air_throw-03 为水平送出去手相，无对手时近似俯冲；air_pulse-01 v2 读作拳收肩侧蓄势而非掌心朝前；dash_throw-02 为屈膝合抱承重，不是字面过顶提起。均完整、未裁、未缩头、未重生成。
- 本批全部为人物帧，无 FX/颗粒；low_pulse 与 air_pulse 的光弹按已装机约定由运行时独立效果承载，未烘焙进人物帧。落地后仅清除 ≤3px 独立杂点，人物未改。
- 已写入 `stage1/cells/cells.json`（action_frames 245、action_set_status 60；本批 41 帧 review_status=approved、review_authority=root_delegated_by_user；stage_status=phase_c_batch6_crouch_air_dash_throw_approved；action_expansion.status=batch6_approved，batch5 记录保留）与 `stage1/requests.json`（attempts 287、delivered 60 项；action_production.status=phase_c_batch6_approved；batch 为 phase_c_batch6，rejected_count=1、failed_count=0；batch1–batch5 保留）。
- 未安装、未启动Godot、未提交、无录屏；720/1080、实速、声音、实机均未验。content 与声音未改，不合成声音。
- 下一批按矩阵：空中受身4/击飞上升3/击飞下落3/弹地3/前滚起身5/后滚起身5；拆投4与被投受方3/4/4/4；站立转身3/后撤5/闪避6/破绽眩晕6/防御硬直站2/蹲2/破防4；专属技与空中必杀、三槽必杀核对。机器门通过后按同一授权签署继续。

## 第七批：空中受身、击飞、弹地、前后滚起身（2026-11-10）

- 按用户 2026-11-10“评审自动通过、机器门通过后直接按 `root_delegated_by_user` 签署并继续”的指示，本批 6 组 23 帧签署为 approved；`review_authority=root_delegated_by_user`，不是 user_approved，不是用户亲审。分组：air_recover 4、hit_air_rise 3、hit_air_fall 3、bounce 3、getup_forward 5、getup_back 5。
- 身份锚仍为 `stage1/idle/frames/pixel-raw-02-official-side-anchor.png`（SHA `5f4651673a90f08056a250fea9a6f68ad339501a615658a183a7d07d3791dec3`），每帧只引该一张；256×256 格、root [128,248]、接地相脚底 247、腾空相脚底 225、冻结 32 色板、二值 Alpha；`forge_backend._kcentroid_downscale(detail_bias=False)` + Alpha128 硬化 + 整图最近色映射；4px 边距水平限位，`cropped_pixels=0`。脚底行按相分配：air_recover 00–02 腾空225、03 接地247；hit_air_rise 全组225；hit_air_fall 全组225；bounce 00/02 腾空225、01 砸地247；getup_forward/getup_back 全组247。
- 组内统一固定比例，基准取该组干净帧的原始眼行脸宽，不逐帧缩放：air_recover 34/199=0.1708542714、hit_air_rise 34/234=0.1452991453、hit_air_fall 34/190=0.1789473684、bounce 34/249=0.1365461847、getup_forward 34/197=0.1725888325、getup_back 34/197=0.1725888325。整组共用同一 scale。
- 落格实测（bbox 含端点 / 高度 / 脚底 / 脸宽 / 色数）：air_recover [74,80,155,225]/[34,37,157,225]/[55,2,204,225]/[58,101,183,247]，h146/189/224/147，脚底225/225/225/247，脸宽41/34/37/34，31色×4；hit_air_rise [67,92,188,225]/[99,55,206,225]/[110,91,240,225]，h134/171/135，脚底225，脸宽34/30/26，31/31/30色；hit_air_fall [19,48,164,225]/[61,117,251,225]/[79,103,215,225]，h178/109/123，脚底225，脸宽34/72/75，30/29/31色，01触发4px水平限位；bounce [106,112,186,225]/[16,166,181,247]/[85,87,172,225]，h114/82/139，脚底225/247/225，脸宽41/34/35，31/31/30色；getup_forward [52,106,206,247]/[77,121,188,247]/[77,137,185,247]/[82,85,189,247]/[57,59,186,247]，h142/127/111/163/189，脚底247，脸宽51/99/78/34/35，32/31/31/32/32色；getup_back [45,164,217,247]/[99,113,212,247]/[73,119,177,247]/[47,110,225,247]/[58,67,186,247]，h84/135/129/138/181，脚底247，脸宽45/37/60/46/35，31/31/30/29/31色。全部 4 连通=1、未裁、未缩。
- 2×联系表（SHA-256）：air_recover `13c4bd8e6f13b2473a022a96d35e6e7f6fd60f2a061cd68cc08eddc5d898e7b5`、hit_air_rise `50d0c5cf371b27a48f1f7fb8957f73418373f264e4ed40afc26c4cffb15c1674`、hit_air_fall `fe7f7ea0c68590e7b8c7f38129e5a0dc65706251ac63f19264f72739a910faf8`、bounce `d5a0b141200ac1f105c4f3ec8a05a090ee31f8b3f446c433eb70702fcf60fbf8`、getup_forward `1895c669afb4780adb35ab46a44d86c4b9c6a94479049e77bae60a5441e4aff6`、getup_back `8e0ccc2930b763e062c91f28afa4827e4048eb798d31a998cf5d8119730caebe`。
- 拒收（已记录 SHA/尺寸/原因并删除，无备份）：hit_air_fall-00 v1 输出为 24 格角色拼图（1536×1024），SHA `0aad73a4159089b555d645eb1af0e7dffec157314b9100de0a84c08084ff6336`，拒收；v2 单帧但头大身短（脸宽312、身高992，约3.2头身），SHA `f178d1853073cc2c04d3fe30a83d8a2f9e36f545e2c2166a3081e00e02590c1b`，加“不要放大头、保持成年人头身比”后由 v3 替换（image-65174-770，SHA `aedbd56ba5b8c725a278d163fb402b338bafbb8bcbc7b1dff30c1d348cc775ee`，脸宽190、身高996）。hit_air_fall-01 v1 横向展开过宽（1774×887，原始横向跨度1613），按 34/190 落格会超出 256 画布被裁；该文件被 v2 覆盖后删除，完整 SHA 未留存，仅存 12 位前缀 `bd580fd2e843`；重生成收臂屈膝的紧凑 v2（image-65174-777，SHA `58abc1fa549eb23bb61be542b005cae60ff651568d1dd9059b29f4b59e13d088`）。getup_back-01 v1 输出为 12 格序列条（2172×724），SHA `82c239cec799dde5238ac737ae2d6365533313c4970fbe66520390c4b9311b06`，拒收；v2 单帧（image-65174-763，SHA `ea9d06d9b6aa402a89302011e41b9a06eef2ccd38c28fc2d34bf17516b882a39`）。本批无失败调用。
- 已知差异保留、不返修：自动眼行脸宽在手臂/蜷姿贴近头部时读数偏大——air_recover-00 41、hit_air_fall-01 72/02 75、bounce-00 41、getup_forward-00 51/01 99/02 78、getup_back-00 45/02 60/03 46；hit_air_rise-01 30/02 26 偏小。均不作头宽比较，未缩头、未逐帧改比例。air_recover-02 为伸腿迎地高相（h224）；hit_air_fall 全组为紧凑翻转姿态（h178/109/123），01 按 4px 边距水平限位、root x 不为 128，人物完整未裁；getup_forward/getup_back 中段为蜷团滚翻低相（最低 h84），不放大凑站高；bounce-01 为砸地相、脚底 247，00/02 为腾空相。均不重生成。
- 本批全部为人物帧，无 FX/颗粒；受击位移、弹地与起身过程按已装机约定由运行时模拟承载，未烘焙进人物帧，因此非技能帧整帧 4 连通=1。落地后仅清除 ≤3px 独立杂点，人物未改。
- 已写入 `stage1/cells/cells.json`（action_frames 268、action_set_status 66；本批 23 帧 review_status=approved、review_authority=root_delegated_by_user；stage_status=phase_c_batch7_air_recover_hit_fall_bounce_getup_approved；action_expansion.status=batch7_approved，batch6 记录保留）与 `stage1/requests.json`（attempts 314、delivered 66 项；action_production.status=phase_c_batch7_approved；batch 为 phase_c_batch7，rejected_count=4、failed_count=0；batch1–batch6 保留）。
- 未安装、未启动Godot、未提交、无录屏；720/1080、实速、声音、实机均未验。content 与声音未改，不合成声音。
- 下一批按矩阵：拆投4与被投受方3/4/4/4；随后站立转身3/后撤5/闪避6/破绽眩晕6/防御硬直站2/蹲2/破防4；最后核对专属技、空中必杀与三槽必杀。机器门通过后按同一授权签署继续，同一问题连续 3 帧拒收或两种修法用尽即停并出诊断。

## 第八批：拆投与被投受方（2026-11-10）

- 按用户 2026-11-10“评审自动通过、机器门通过后直接按 `root_delegated_by_user` 签署并继续”的指示，本批 5 组 19 帧签署为 approved；`review_authority=root_delegated_by_user`，不是 user_approved，不是用户亲审。分组：throw_tech（拆投）4、thrown_forward（被前投）3、thrown_back（被后投）4、thrown_air（被空投）4、thrown_dash（被擒抱）4。
- 身份锚仍为 `stage1/idle/frames/pixel-raw-02-official-side-anchor.png`（SHA `5f4651673a90f08056a250fea9a6f68ad339501a615658a183a7d07d3791dec3`），每帧只引该一张；256×256 格、root [128,248]、接地相脚底 247、腾空相脚底 225、冻结 32 色板、二值 Alpha；`forge_backend._kcentroid_downscale(detail_bias=False)` + Alpha128 硬化 + 整图最近色映射；4px 边距水平限位，`cropped_pixels=0`。脚底行按相分配：throw_tech 全组247；thrown_forward 00/01 腾空225、02 落地247；thrown_back 00–02 腾空225、03 落地247；thrown_air 00–02 腾空225、03 落地247；thrown_dash 00–02 腾空225、03 落地247。
- 组内统一固定比例，基准取该组干净帧的原始眼行脸宽，不逐帧缩放：throw_tech 34/200=0.17、thrown_forward 34/205=0.1658536585、thrown_back 34/220=0.1545454545、thrown_air 34/220=0.1545454545、thrown_dash 34/215=0.1581395349。整组共用同一 scale。
- 落格实测（bbox 含端点 / 高度 / 脚底 / 脸宽 / 色数）：throw_tech [54,61,187,247]/[57,65,185,247]/[57,62,198,247]/[58,62,184,247]，h187/183/186/186，脚底247，脸宽34/36/34/35，31/30/30/29色；thrown_forward [50,71,251,225]/[84,79,188,225]/[5,139,251,247]，h155/147/109，脚底225/225/247，脸宽34/81/96，30/32/32色；thrown_back [32,45,156,225]/[61,116,251,225]/[4,84,213,225]/[6,146,251,247]，h181/110/142/102，脚底225/225/225/247，脸宽34/118/41/193，31/31/29/32色；thrown_air [9,111,190,225]/[38,121,160,225]/[88,71,172,225]/[4,120,238,247]，h115/105/155/128，脚底225/225/225/247，脸宽36/34/30/52，30/31/30/31色；thrown_dash [68,67,195,225]/[39,90,251,225]/[4,74,208,225]/[64,125,244,247]，h159/136/152/123，脚底225/225/225/247，脸宽36/41/119/102，30/30/32/30色。全部 4 连通=1、未裁、未缩。
- 2×联系表（SHA-256）：throw_tech `730bf9005720c6b5bce34ab67bcef0cc2e872d4ae1c7be7be3fa5b7ed9623aa1`、thrown_forward `5f29ef7fdae0dcaad9ff8725c5fdf37588a8144dc9fda0f9f19068c2551be71e`、thrown_back `f9da298271176d959551079c84477345b77c50d4a83511f4fc29847ed981f5b3`、thrown_air `56c7adb174c4cd6ff788e0fc0b982c399e4548dcc00f987c06a25d11bdbb90e2`、thrown_dash `ef8bd25c308d6a5d915e4dbfadb86e2557ba8b2ffe1a583210f29cdbcc8c74bb`。
- 拒收（删除前已记录完整 SHA-256，无备份）：thrown_forward-01 v1 横向展开过宽，原始宽1636，在 34/205 比例下落格宽256且 clamped_no_margin、cropped_pixels=-167，左右被裁，SHA `1d8b1556a0254cf405db3a7ffd98094072fe315bf8c1eb6ec83093035025ee1b`（1774×887，生成编号 image-65174-803），删除后重生成收身屈膝的紧凑 v2（image-65174-834，SHA `849f754eca9f83db9e47ce93dcc6e83538b3afe3bac0993018d129e05e36abad`，1312×1199）。thrown_dash-03 v1 落格 bbox [2,132,255,247] 宽254、右缘 0px 边距，不满足 4px 限位，SHA `5ed04a56c6e68e2691ac471794b4aa451057197a75d38d1e518525682759033e`（1774×887，image-65174-824），删除后重生成侧身蜷贴地面的紧凑 v2（image-65174-836，SHA `fca494ed5b06c12f4a9c0a61287cda8bdc958162979ce4c190f915ba9aaa524e`，1536×1024）。本批无失败调用。
- 已知差异保留、不返修：自动眼行脸宽在横躺/撑地手臂贴近头部时读数偏大——thrown_forward-01 81/02 96、thrown_back-01 118/03 193、thrown_air-03 52、thrown_dash-02 119/03 102，均不作头宽比较，未缩头、未逐帧改比例。thrown_forward-02、thrown_back-01/02/03、thrown_air-03、thrown_dash-01/02/03 按 4px 边距水平限位，root x 不为 128，人物完整未裁；横躺相高度 102–155 属真实姿态，不放大凑站高。thrown_forward-01 v2 实画为空中收身蜷腿，不是字面“水平甩出”；thrown_back-01 读作俯身横身而非“横扛肩上”；thrown_dash-02 为前扑撑地而非“向上翻转”。均按实画记录，不重生成。
- 本批全部为人物帧，无 FX/颗粒，不画对手；投技双方逐帧对齐所需的被投位置与姿势编号待运行时/数据层接入，本批未改 content。落地后仅清除 ≤3px 独立杂点，人物未改。
- 已写入 `stage1/cells/cells.json`（action_frames 287、action_set_status 71；本批 19 帧 review_status=approved、review_authority=root_delegated_by_user；stage_status=phase_c_batch8_throw_tech_thrown_receivers_approved；action_expansion.status=batch8_approved，batch7 记录保留）与 `stage1/requests.json`（attempts 335、delivered 71 项；action_production.status=phase_c_batch8_approved；batch 为 phase_c_batch8，rejected_count=2、failed_count=0；batch1–batch7 保留）。
- 未安装、未启动Godot、未提交、无录屏；720/1080、实速、声音、实机均未验。content 与声音未改，不合成声音。
- 下一批按矩阵：站立转身3/后撤5/闪避6/破绽眩晕6/防御硬直站2/蹲2/破防4；最后核对专属技、空中必杀与三槽必杀。机器门通过后按同一授权签署继续，同一问题连续 3 帧拒收或两种修法用尽即停并出诊断。

## 第九批：站立转身、后撤、闪避、破绽眩晕、防御硬直、破防（2026-11-10）

- 按用户 2026-11-10“评审自动通过、机器门通过后直接按 `root_delegated_by_user` 签署并继续”的指示，本批 7 组 28 帧签署为 approved；`review_authority=root_delegated_by_user`，不是 user_approved，不是用户亲审。分组：turn 3、backstep 5、dodge 6、stun 6、blockstun 2、crouch_blockstun 2、guardbreak 4。
- 身份锚仍为 `stage1/idle/frames/pixel-raw-02-official-side-anchor.png`（SHA `5f4651673a90f08056a250fea9a6f68ad339501a615658a183a7d07d3791dec3`），每帧只引该一张；256×256 格、root [128,248]、接地相脚底 247、腾空相脚底 225、冻结 32 色板、二值 Alpha；`forge_backend._kcentroid_downscale(detail_bias=False)` + Alpha128 硬化 + 整图最近色映射；4px 边距水平限位，`cropped_pixels=0`。脚底行：turn/stun/blockstun/crouch_blockstun/guardbreak 全组247；backstep 00/03/04 接地247、01/02 腾空225；dodge 02 腾空225、其余接地247。
- 组内统一固定比例，基准取该组干净帧的原始眼行脸宽，不逐帧缩放：turn 34/200=0.17、backstep 34/195=0.1743589744、dodge 34/195=0.1743589744、stun 34/203=0.1674876847、blockstun 34/205=0.1658536585、crouch_blockstun 34/210=0.1619047619、guardbreak 34/192=0.1770833333。整组共用同一 scale。
- 落格实测（bbox 含端点 / 高度 / 脚底 / 脸宽 / 色数）：turn [55,61,183,247]/[103,48,164,247]/[57,62,184,247]，h187/200/186，脚底247，脸宽32/34/34，30/31/31色；backstep [83,69,174,247]/[63,45,154,225]/[86,74,168,225]/[105,67,211,247]/[58,57,187,247]，h179/181/152/181/191，脚底247/225/225/247/247，脸宽37/36/37/35/33，31/32/31/32/30色；dodge [59,97,181,247]/[119,66,236,247]/[122,58,206,225]/[82,77,186,247]/[62,49,183,247]/[60,93,184,247]，h151/182/168/171/199/155，脚底247/247/225/247/247/247，脸宽34/33/37/36/35/36，31/32/31/31/30/29色；stun [55,74,185,247]/[60,73,181,247]/[79,69,190,247]/[91,76,180,247]/[66,65,182,247]/[58,66,183,247]，h174/175/179/172/183/182，脚底247，脸宽40/57/33/54/41/34，30/29/30/30/30/31色；blockstun [62,74,194,247]/[87,57,166,247]，h174/191，脚底247，脸宽34/35，31/31色；crouch_blockstun [64,104,173,247]/[72,91,176,247]，h144/157，脚底247，脸宽35/36，31/31色；guardbreak [55,56,188,247]/[50,63,196,247]/[41,76,183,247]/[59,57,184,247]，h192/185/172/191，脚底247，脸宽34/37/46/49，31/31/30/30色。全部 4 连通=1、未裁、未缩。
- 2×联系表（SHA-256）：turn `92d1aa27ae78665a48f5b2562435b675a2ef2be123264b9b68f6f9f44e70dcff`、backstep `4d7e8ec8e9c8ea7f89228779c85f65441d596d30fd12844b6b21a726571dd634`、dodge `275de9de2723a3a78048fce29ccf875092a53903e9be0388214b429fb484ac4f`、stun `5f46cbc1099da11b5c01c213215d27dbbf2b7134d24617c8375814dbc4fbcc73`、blockstun `872c7b26c4d70db0abe96b8afd1841d4606701fc3dac516936341cdf8518cd12`、crouch_blockstun `ae4fe1f9430fd50f13b11e80ad4a24d06c713ffe049857341861344211c638ce`、guardbreak `78783f006bcd523ed71ae03503cbbd36302a3d7cc1c2b60821a1e2ce748f3f43`。
- 拒收（删除前已记录完整 SHA-256，无备份）：turn-01 v1 输出为 4×6 共 24 格角色拼图，不是单帧整身人物，SHA `bc02b2db8da06818cec3334c4b4662fb417ec08f01beacf346aadee4fd31277c`（1024×1536，生成编号 image-65174-849），删除后加“只画单个完整人物的单独一帧、不拼网格”重生成 v2（image-65174-893，SHA `dbcf58c13a6f9d86f249a44622e43249716980d5e5a4aee2cd0c4f1a53a69d39`）。本批无失败调用。
- 已知差异保留、不返修：自动眼行脸宽在低头/仰头/手臂遮挡时读数偏大或偏小——stun-01 57、stun-03 54、stun-04 41、guardbreak-02 46/03 49、turn-00 32，均不作头宽比较，未缩头、未逐帧改比例。turn-01 v2 实画为侧身站立相，不是明显扭身；backstep-01/02 与 dodge-02 为腾空相、其余接地；crouch_blockstun 高 144/157 属真实蹲姿，不放大凑站高；stun 全组读作摇晃/低头/扶额，无眩晕星特效；blockstun-00 双臂交叉护架、01 回稳；guardbreak 从护架崩开、门户大开到护架散开。均完整、未裁、未重生成。
- 本批全部为人物帧，无 FX/颗粒；眩晕星、格挡火花等由运行时独立效果承载，未烘焙进人物帧，因此非技能帧整帧 4 连通=1。落地后仅清除 ≤3px 独立杂点，人物未改。
- 已写入 `stage1/cells/cells.json`（action_frames 315、action_set_status 78；本批 28 帧 review_status=approved、review_authority=root_delegated_by_user；stage_status=phase_c_batch9_turn_backstep_dodge_stun_block_guardbreak_approved；action_expansion.status=batch9_approved，batch8 记录保留）与 `stage1/requests.json`（attempts 364、delivered 78 项；action_production.status=phase_c_batch9_approved；batch 为 phase_c_batch9，rejected_count=1、failed_count=0；batch1–batch8 保留）。
- 未安装、未启动Godot、未提交、无录屏；720/1080、实速、声音、实机均未验。content 与声音未改，不合成声音。
- 下一批按矩阵：核对专属技、空中必杀与三槽必杀。机器门通过后按同一授权签署继续，同一问题连续 3 帧拒收或两种修法用尽即停并出诊断。

## 第十批：专属技、空中必杀与三槽必杀核对（2026-11-10）

- 本轮只核对既有帧与内容依据，未生成新图、未改任何像素；签署 `review_authority=root_delegated_by_user`（不是 user_approved，不是用户亲审）。
- 三槽必杀（现有 light1/2/3 即 special1/2/3，保留文件名不改）：
  - special1 Wide Zero Shot → light1 3帧，起手左臂后伸右拳收腰、蓄光两臂L字右前臂蓝白亮芯+青外焰+颗粒、发射自右前臂外侧向右宽束；光束块 x148–220，束根接前臂（接缝0px），束中心 y110.5 对前臂中心 y107.5，差 3px。
  - special2 Emerium Slash → light2 3帧，双手食中指抵额灯两侧蓄绿光、发射自额灯向右细锐绿束；光束块 x139–192，接缝0px，束中心 y89.0 对额灯中心 y83.5，差 5.5px。
  - special3 Zero Slugger → light3 4帧，双手扣额侧双镖、拔下收胸前蓄蓝白刃光、双掌前挥掷出双镖带光尾、收势双镖装回头上；飞行双镖与光尾属技能独立块，主体单连通。
  - 结论：三个不同技能、不同发射部位（前臂/额灯/双镖）、不同颜色与形态（宽蓝束/细绿束/实体飞行刃），不是同束改粗细或换色凑槽。
- 空中必杀 air_special 3帧：起手腾空收膝、蓄光右前臂蓝白亮芯+青外焰、发射向右宽束；脚底行225，主体含光束单连通，独立颗粒15块（最大3px），右缘244留11px未裁；束根接右前臂、接缝0px，束中心 y140.0 对前臂中心 y118.5，差 21.5px（自动测量按前臂竖直中段取值，束实际从拳/前臂下端发出；未重生成）。
- 机器门复核：light1/2/3 与 air_special 全部 256×256、二值 Alpha、色数≤32 且属冻结色板、脚底行正确、2×联系表 SHA 与记录一致。按技能帧口径只判人物主体单连通，独立颗粒与已脱手飞行武器允许。
- 专属技：矩阵 command_40（236□）、command_41（623△）、command_42（214I）、command_43（22○）均写“角色专属（见各角色MOVES.md）”，但 `content/fighters/ultraman-zero/` 只有 `catalogue_profile.json`，无 MOVES.md、`moves/*.json`，`content/combat/skill_library.json` 的 ultraman-zero 无条目。没有可核实的具体招式、形态与版本依据，按规则不自行编造，本轮不生成，登记为内容缺口（未完成项）。
- 已写入 `cells.json` 与 `requests.json` 的 `special_check`（三槽 pass、空中必杀 pass、专属技 blocked_missing_data），并为既有 light1/2/3 帧补签 `root_delegated_by_user`；未改图。
- 未安装、未启动Godot、未提交、无录屏；720/1080、实速、声音、实机均未验。content 与声音未改。
- 下一步：赛罗矩阵动作已全部补齐；剩余为 content 侧专属技依据、MOVES/SOUNDS/moves/production_plan 缺口与原剧声音任务，以及实机验证。需用户或内容侧补齐后再继续。

## 2026-11-12 纯人物整帧落格与招式帧序对齐（本机批次）

- 范围：special / special2 / special3 / air_special 四组纯人物整帧落格、装机并重映射招式；沿用身份锚 `stage1/idle/frames/pixel-raw-02-official-side-anchor.png`，比例 0.158767、目标站高 172、256 格、根点 [128,248]、接地脚底 247、air_special 腾空脚底 225。
- air_special 斜下前伸臂超宽，单独用 288×288 格、根点 [128,248]（其余仍 256）；重装只走 `--only air_special --merge`，避免 288 格被其它组 256 格压回。
- 落格实测：special 16 帧高 164–175、special2 16 帧 174–178、special3 16 帧 160–174、air 8 帧 151–183；全部 32 色、二值 Alpha、主体单连通、四边留白、无裁切。逐帧 bbox/SHA 见 `stage1/cells/cells.json` 的 frames 记录。
- 招式：special 16→72 tick（24/32/16，发射 tick 24 sprite 08）、special2 16→80（32/32/16，tick 32）、special3 16→96（32/48/16，tick 32）、air 8→24（10/1/13，命中 tick 10 sprite 03）；sprite 映射与事件/判定保留，镜头/暂停键照旧。超杀三槽仍用 pending FX id，待本角色特效家族接替，未复用他角色特效。
- 安装：`assets/fighters/ultraman-zero/animations/` 113 clip；四组 atlas SHA 见 manifest。hurtboxes 按新图集整招重算（`tools/art/recalc_move_hurtboxes.py`）。
- 验证：锁内 `tools/verify.py` 全量 57 项 PASS（含 roster_data_integrity、catalogue_animation、main-startup）。签署 root_delegated_by_user，不是用户亲审；无录屏，720/1080 双向实机画面未验。

## 2026-11-12 赛罗专属特效家族、Q 蓄气与发射点对齐

- 新建 `fx-family-pixelfx-20261112-v1/bake.mjs` + `install.py`：PixelFX 离线烘焙 11 段自绘原创像素，不读他人特效图集；上游 `third_party/pixelfx` 固定 commit `a8415968`、MIT，许可复制到 `assets/effects/ultraman-zero/fx-family-pixelfx-20261112-v1/PIXELFX-LICENSE.txt`。每段写 `provenance.json`（请求、形状来源、上游 commit、逐帧 PNG SHA、atlas SHA）与 `effect.json`。
- 技能段：`zero_fx_wide_beam`（420×96 亮白芯+青蓝层+刃状锯边+周期十字闪+枪口/束端星芒）、`zero_fx_wide_hit`；`zero_fx_emerium_beam`（420×72 青绿细束+四道新月刃波）、`zero_fx_emerium_hit`；`zero_fx_slugger_flight`（64×48 旋翼新月刃）、`zero_fx_slugger_trail`、`zero_fx_slugger_hit`、`zero_fx_slugger_catch`（收束环+双刃亮闪）。全部硬 Alpha（alpha<128→0）、≤8 色板、相位逐帧变化。
- Q 蓄气三态：`zero_fx_q_charge_start` 9 帧、`zero_fx_q_charge` 24 帧、`zero_fx_q_charge_stop` 9 帧，384×256、锚 [192,246]；两侧上升流带+头镖形短竖刃光+三道横向断弧+环顶汇聚，只在真实 Q 起势/保持/收势出现；已写入 `charge_overlay_policy.json` 的 `placements.ultraman-zero` 并加入 `charge_only_effects`。
- 三招接线：special→`zero_fx_wide_beam`、special2→`zero_fx_emerium_beam`、special3→`zero_fx_slugger_flight`+`_trail`+`_catch`+`_hit`、air_special 从不可见 strike 判定改为 projectile 运行时束体（spawn [126,162]、life 8）；名称改为赛罗集束射线/艾梅利姆切割/赛罗头镖/空中集束射线（游戏改编）。人物帧未改，帧内无烘焙特效。
- 发射点按当帧手部像素重核，九处全部 0.00 px：special [18,138]、special2 [22,158]、air_special [126,162] 原已贴手；special3 双镖 [57,151]/[57,113]→[59,132]/[33,133]；pulse [60,143]→[54,130]、low_pulse [82,91]→[58,81]、air_pulse [123,110]→[87,78]、ranged_forward [62,143]→[65,132]。
- special3 实体镖修复：原 `integer_path` 只有 `[[0,0]]`，实体镖实际不飞出；`return_anchor_by_tick` 只有 `"0"`，运行时按 `owner.move_tick` 取锚，回收首 tick 查不到即 `missing_current_return_anchor` 清除。改为 31 点外飞折线（30 tick 飞 330 px，双镖上下分开 ±8 px）、`return_anchor` [12,118]/[0,120]、tick 32–95 逐 tick 双手锚（按各精灵帧实手位），24 tick 回收，接刃闪光落在手上。
- 锁内全量 `tools/verify.py` 57 项 PASS（含 roster_data_integrity、catalogue_animation、main-startup）。未实机、未听审、无录屏；720/1080 双朝向未验。基础光弹仍用运行时通用 `pulse` 弹体，不是他角色专属家族。
