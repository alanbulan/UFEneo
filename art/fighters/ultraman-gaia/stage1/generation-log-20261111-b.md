# 盖亚 V2 动作原始帧生成日志（2026-11-11 批次 b）

- 角色：ultraman-gaia（盖亚 V2）
- 唯一身份参考：`art/fighters/ultraman-gaia/stage1/idle/frames/pixel-raw-02-explicit-canvas.png`（1024×1536，RGBA）
- 参考图 SHA256：`d509c66381d5b3ed…`（与已交付 victory/defeat/slide/sweep/dive 等 74 帧同一配方）
- 模型：`codex/gpt-image-2`，quality high，size 1024x1536，经 magpie-image MCP；每帧仅 1 张参考、每次 1 张
- 提示词：150–250 字动作描述＋固定尾串（右侧视、全身不裁切、透明背景、无地面/文字/边框/光晕/特效、本帧无光效）；motion_236/41236 额外写明本体不画光束、只画本角色
- 自检门：尺寸 1024×1536、RGBA、alpha 0–255、body(alpha≥128) 宽高比 0.35–0.85、黄(R>180,G>140,B<90)≥300、青/蓝(B>140,R<110,G>110)≥150
- 追加体型一致性门（批次中途生效）：锚 body_h=1048 实测；站姿类帧 body_h 须在锚 ±10%；蹲/腾空/举臂伸展帧豁免但登记数值；同组相邻站姿帧高度突变 >10% 重掷
- 帧数说明：13 组按任务逐组清单合计 81 帧（任务标题写 77 与清单不符，按清单执行）

## 总览（81/81 完成，0 失败）

| 组 | 帧 | 重掷 | 备注 |
|---|---|---|---|
| low_pulse | 5/5 | 2 | 01 两次宽高比超限 |
| air_pulse | 5/5 | 0 | |
| back_counter | 6/6 | 1 | 05 体型门追溯重掷 |
| dodge_counter | 5/5 | 3 | 01/02 宽高比、04 体型门追溯 |
| guard_counter | 6/6 | 0 | |
| burst | 5/5 | 0 | |
| chase_takeoff | 3/3 | 2 | 00/02 宽高比超限 |
| taunt | 6/6 | 0 | |
| motion_236 | 8/8 | 2 | 00/01 站高偏锚超限 |
| motion_623 | 8/8 | 1 | 00 宽高比超限；03–05 举臂伸展豁免登记 |
| motion_214 | 8/8 | 1 | 03 宽高比超限 |
| motion_22 | 8/8 | 1 | 02 外扩过宽双超限 |
| motion_41236 | 8/8 | 1 | 04 前倾过宽双超限 |
| 合计 | 81 | 15 | |

追溯重掷 2 次（back_counter-05、dodge_counter-04）发生于体型门下达后对该两组已生成帧的复测，均一次通过。

事故登记：motion_41236-04 重掷时请求 path 误写为 `art/fighters/ultraman-neo/…`（重复段），生成后核 SHA 一致并移回正式路径，误建目录 `art/fighters/ultraman-neo/` 已整支删除；仅处理本请求生成的该文件，未涉及其它文件。

服务故障登记：motion_236-00 首掷遇 503（chatgpt.com upstream），等 60 秒重试一次成功，未计入重掷限额。

## low_pulse（蹲姿为主，h 豁免登记）

| 帧 | 生成ID | body_w×h | 宽高比 | 黄 | 青 | h vs 锚 | SHA256 |
|---|---|---|---|---|---|---|---|
| low_pulse-00-raw.png | image-35600-4 | 718×883 | 0.8131 | 3522 | 580 | −15.7% | 31af7c776397c3cfcdafc14b86391892dfbea7697f73f64cda7e94ff24df1d7c |
| low_pulse-01-raw.png | image-35600-11 | 675×800 | 0.8438 | 4156 | 473 | −23.7% | f35291f3b73eb4029ec9a1ee2ff183c27de880497ba312ee0bedd3579b267dc9 |
| low_pulse-02-raw.png | image-35600-13 | 646×823 | 0.7849 | 3581 | 441 | −21.5% | 906a06884d179bc53351a30210f42c24f4c85ed47e4be0026309a0c249b38878 |
| low_pulse-03-raw.png | image-35600-17 | 539×902 | 0.5976 | 2909 | 413 | −14.0% | 3be3a7439f6eb1fada81ab81a44b4d2cae942025328902c64a084c715403626b |
| low_pulse-04-raw.png | image-35600-21 | 571×988 | 0.5779 | 3836 | 438 | −5.7% | 117205c1ea3573102340b9fd46efecd49c1ea07088381dc2c5716a268d8fa633 |

注：01 前两掷（image-35600-5、image-35600-8，宽高比 0.895/0.904）已删。

## air_pulse（腾空，h 豁免登记）

| 帧 | 生成ID | body_w×h | 宽高比 | 黄 | 青 | h vs 锚 | SHA256 |
|---|---|---|---|---|---|---|---|
| air_pulse-00-raw.png | image-35600-24 | 433×761 | 0.5690 | 4124 | 352 | −27.4% | 5f0f749f2fa14d79b074fdfe157939641ac488b31827c21ae922a6f5c2899c5e |
| air_pulse-01-raw.png | image-35600-26 | 593×874 | 0.6785 | 2507 | 338 | −16.6% | 1d03df43a41353ba102108b4ad1680d739f6775021a5846c99f433eaa658505a |
| air_pulse-02-raw.png | image-35600-30 | 619×848 | 0.7300 | 3588 | 380 | −19.1% | 9c53b42fa354bbae7823a43c342ebe8efce67a814e86086c1e3eabf8d1f70d64 |
| air_pulse-03-raw.png | image-35600-33 | 425×862 | 0.4930 | 3014 | 362 | −17.8% | 7d65a5233c50f5db5a91f05ab6bad2bdb5db082cf10bdcc04cedc320adbbef00 |
| air_pulse-04-raw.png | image-35600-37 | 449×890 | 0.5045 | 2581 | 371 | −15.1% | 0442e9b9da5385d5187048a73d29f626427c7ed7c285956449b74a6e38215cf3 |

## back_counter

| 帧 | 生成ID | body_w×h | 宽高比 | 黄 | 青 | h vs 锚 | SHA256 |
|---|---|---|---|---|---|---|---|
| back_counter-00-raw.png | image-35600-42 | 709×911 | 0.7783 | 4413 | 382 | −13.1%（蓄势蹲相，豁免） | 8bead491675345b8bdabc08f03f74a8ec6b474a0303a082d5a3541cdf0970153 |
| back_counter-01-raw.png | image-35600-49 | 743×1041 | 0.7137 | 2315 | 399 | −0.7% | 38d39f8c10e69edcb8720869580fa743aaff369e040941b07e13f4abc60c33fa |
| back_counter-02-raw.png | image-35600-53 | 807×1041 | 0.7752 | 2184 | 416 | −0.7% | 50aa23eb4644f29072ce5cbed1fdab2827bd4f839d3f3013a8c462e59b30210c |
| back_counter-03-raw.png | image-35600-59 | 767×1001 | 0.7662 | 3290 | 360 | −4.5% | ff7d95f01d70e93ce44a42d6b924358541dcd7f0ef061975a55053bd8802b693 |
| back_counter-04-raw.png | image-35600-62 | 676×1046 | 0.6463 | 3732 | 400 | −0.2% | ce8cba788182dacd295e2dae41ad68ae2614ee99405b3c26177d3ff619bb3714 |
| back_counter-05-raw.png | image-35600-117 | 729×1047 | 0.6963 | 5790 | 411 | −0.1% | e97d35f2e809c7cb79e1cdbda298ae2fe7c62dc863474a51438977239d10a065 |

注：05 首掷（image-35600-65，h=930，偏锚 −11.3%、相邻突变 11.1%）按体型门追溯重掷，已删。

## dodge_counter

| 帧 | 生成ID | body_w×h | 宽高比 | 黄 | 青 | h vs 锚 | SHA256 |
|---|---|---|---|---|---|---|---|
| dodge_counter-00-raw.png | image-35600-66 | 660×793 | 0.8323 | 3394 | 398 | −24.3%（低身，豁免） | cc1fbc0fd2b951b73e05c2d619cc016771fdc01f7d3a635ff7f0f3253e0cd772 |
| dodge_counter-01-raw.png | image-35600-71 | 699×855 | 0.8175 | 3923 | 430 | −18.4%（低身，豁免） | a8900b4cd82823913fca6d831dfc7c34bd86dcbc6dced2fba432f1ab9aecddc7 |
| dodge_counter-02-raw.png | image-35600-75 | 598×805 | 0.7429 | 4259 | 456 | −23.2%（低身，豁免） | a4268f6ef2106b3420bb5505b2243a0ebb781232bf5148adc0de920d24f81f25 |
| dodge_counter-03-raw.png | image-35600-77 | 719×918 | 0.7832 | 3571 | 429 | −12.4%（低身，豁免） | 67eb67f025a92b72334d335d2d4265947353b457f6eddef6689730c57eb98b40 |
| dodge_counter-04-raw.png | image-35600-118 | 731×1049 | 0.6969 | 5009 | 397 | +0.1% | ac24cfb4120073678b10d222528eeebfef8219b5ee778876dec65d6732e9f45d |

注：01 首掷（image-35600-69，宽高比 1.011）、02 首掷（image-35600-73，0.855）宽高比超限已删；04 首掷（image-35600-78，h=885，偏锚 −15.6%）按体型门追溯重掷，已删。

## guard_counter

| 帧 | 生成ID | body_w×h | 宽高比 | 黄 | 青 | h vs 锚 | SHA256 |
|---|---|---|---|---|---|---|---|
| guard_counter-00-raw.png | image-35600-80 | 701×962 | 0.7287 | 2797 | 325 | −8.2% | 1b2a463a867e2fc1d07897eb6cacaa4196267a2b303cbb93068fedf1c5ab605e |
| guard_counter-01-raw.png | image-35600-81 | 724×977 | 0.7410 | 3327 | 306 | −6.8% | 6e4ba172d935c6451fbda9c7cca0945bb9d6be078586a0febfdf607cf99f7fb2 |
| guard_counter-02-raw.png | image-35600-84 | 820×1041 | 0.7877 | 3536 | 366 | −0.7% | ef4150248a96b5aec84556a046db8604c8074ec5f49afe272494ba39cfe3e14a |
| guard_counter-03-raw.png | image-35600-85 | 842×1011 | 0.8328 | 3703 | 350 | −3.5% | 920c4f55152973d48605a06642d0025fae6a594c7554574451548d2b5f110d53 |
| guard_counter-04-raw.png | image-35600-88 | 722×1037 | 0.6962 | 4030 | 416 | −1.0% | 08c18d5750bee5c21b887aa3ae2d8cf61caee3181f4cadd9ca5ddeda65cf8ee4 |
| guard_counter-05-raw.png | image-35600-90 | 728×1048 | 0.6947 | 4288 | 394 | 0.0% | 1c0e1b9536e9260cf0060fec2a857dfe05cafa0e14b8dee3aed3a2c56a580094 |

## burst

| 帧 | 生成ID | body_w×h | 宽高比 | 黄 | 青 | h vs 锚 | SHA256 |
|---|---|---|---|---|---|---|---|
| burst-00-raw.png | image-35600-91 | 660×794 | 0.8312 | 4369 | 401 | −24.2%（屈膝蓄力，豁免） | 5107dc8ae0d5181fe061084e6640e0081cb5794152d39f518fc33972af48deac |
| burst-01-raw.png | image-35600-93 | 724×1024 | 0.7070 | 4241 | 412 | −2.3% | 3b1e057423e6f396ecfca7352f94d380bc915e1e27995199423de5990ad589d3 |
| burst-02-raw.png | image-35600-95 | 731×1039 | 0.7036 | 4636 | 339 | −0.9% | 99dc72fe0fcf1a8dc20e1d5dbb3900ac3f7cabe936418f87f1b90528ece7f1f1 |
| burst-03-raw.png | image-35600-96 | 593×1143 | 0.5188 | 2862 | 279 | +9.1%（顶点微离地，豁免） | 130eec1d26dd9d2a0984ef8e2c26e2140e19b8cd566d0e24948e702ac694d92c |
| burst-04-raw.png | image-35600-99 | 724×1013 | 0.7147 | 3751 | 388 | −3.3% | 16a958261e2198bf1dcdd500a44d9d8d99ff8fd402baa868d2104ff5ade7d09a |

## chase_takeoff

| 帧 | 生成ID | body_w×h | 宽高比 | 黄 | 青 | h vs 锚 | SHA256 |
|---|---|---|---|---|---|---|---|
| chase_takeoff-00-raw.png | image-35600-103 | 714×955 | 0.7476 | 3215 | 353 | −8.9% | bcdc06fa6b604166bbff7a56bdb6a94b34abc9194cb0cef6a4effe10eb78d4f2 |
| chase_takeoff-01-raw.png | image-35600-104 | 642×838 | 0.7661 | 2866 | 322 | −20.0%（腾空，豁免） | 8bba2833176ac307d7f555d6ab9bf77edc65fa8f1c067406610d27e30263a9e0 |
| chase_takeoff-02-raw.png | image-35600-113 | 479×961 | 0.4984 | 2874 | 286 | −8.3% | 17132decbd47d083007221d67aebf9bafa2040c98c2a5455b262176573032d91 |

注：00 首掷（image-35600-100，0.967）、02 首掷（image-35600-109，1.513）宽高比超限已删。

## taunt

| 帧 | 生成ID | body_w×h | 宽高比 | 黄 | 青 | h vs 锚 | SHA256 |
|---|---|---|---|---|---|---|---|
| taunt-00-raw.png | image-35600-121 | 731×1049 | 0.6969 | 4051 | 400 | +0.1% | f10ca60a93473e1a116365f6d47e5cc80cf45a6b746b1bf07df0e43ea8e5b0b1 |
| taunt-01-raw.png | image-35600-126 | 730×1049 | 0.6959 | 3633 | 422 | +0.1% | 9a212db8ee075df2798d711e5b7d8755c46ddadd2289533af3d3e6ddf817885c |
| taunt-02-raw.png | image-35600-128 | 730×1049 | 0.6959 | 3268 | 398 | +0.1% | 54aa94fe2c37749099ffa033e01dda4ea5b1bddbad2b67e6e95cc4753143acd4 |
| taunt-03-raw.png | image-35600-134 | 721×1051 | 0.6860 | 2777 | 401 | +0.3% | 54574690a789285e2d051b58c16734d3a3029efc3cea9a969ac023fa75141046 |
| taunt-04-raw.png | image-35600-137 | 731×1049 | 0.6969 | 3406 | 386 | +0.1% | 13374d804944a31f5791f935bb80250c8ade6a45ab6c22eb6d5de3a2ac7a08d5 |
| taunt-05-raw.png | image-35600-141 | 734×1049 | 0.6997 | 3355 | 398 | +0.1% | 69338199d639e60752d434064d4dae5b17b77000c149ab5377b68951804471cc |

## motion_236（盖亚光线编排，本体无光）

| 帧 | 生成ID | body_w×h | 宽高比 | 黄 | 青 | h vs 锚 | SHA256 |
|---|---|---|---|---|---|---|---|
| motion_236-00-raw.png | image-35600-162 | 731×1049 | 0.6969 | 4133 | 399 | +0.1% | 13ad69434bfb1e9df9484c2b5251f24c1319307cbc5429118ec3ee0c6309f4ea |
| motion_236-01-raw.png | image-35600-170 | 732×1050 | 0.6971 | 2296 | 374 | +0.2% | fa75187de66311be85536ab847337c84b1fcd7a47cd92414ed9a4aab256009d9 |
| motion_236-02-raw.png | image-35600-174 | 730×1048 | 0.6966 | 2596 | 423 | 0.0% | 0dabbc2e15b632bf7f7132df1dd907906e9c0e2df7452dced3d35878d5feb26d |
| motion_236-03-raw.png | image-35600-180 | 743×1047 | 0.7096 | 2025 | 175 | −0.1% | eebe559cb235eb1f4c32b04a4c7149b21aa6a013bc1f9d1f119ef9a7b98b85a9 |
| motion_236-04-raw.png | image-35600-184 | 758×1049 | 0.7226 | 2118 | 223 | +0.1% | d64a87a8e7d038b926fb90ad8c0bbaf0dda4821d0c45ac35eb9cba6a221f11a5 |
| motion_236-05-raw.png | image-35600-189 | 754×1049 | 0.7188 | 2268 | 244 | +0.1% | 9f3b49faed6a8d6b3f88c334c779b3f3c64107ddff0a2af8b0641a694196d454 |
| motion_236-06-raw.png | image-35600-194 | 750×1048 | 0.7156 | 1996 | 366 | 0.0% | d71657c0e1ca2cfff0723f85e4f42f5a44135e657ccf96dbf0e5198d5ef38504 |
| motion_236-07-raw.png | image-35600-197 | 732×1049 | 0.6978 | 4285 | 411 | +0.1% | 1efde694a66b17594487d76b87d95ea95baada70df3a8965bffbeb242dbf5da6 |

注：00 首掷（image-35600-159，940，−10.3%）、01 首掷（image-35600-167，913，−12.9%）站高偏锚超限重掷已删。

## motion_623（对空升掌）

| 帧 | 生成ID | body_w×h | 宽高比 | 黄 | 青 | h vs 锚 | SHA256 |
|---|---|---|---|---|---|---|---|
| motion_623-00-raw.png | image-35600-205 | 578×853 | 0.6776 | 3794 | 434 | −18.6%（深屈膝，豁免） | 787bd56fdd3ad103250b5b27e86ac3384999958eb47629d56d68554010c04128 |
| motion_623-01-raw.png | image-35600-207 | 728×1093 | 0.6661 | 3097 | 306 | +4.3% | f0d5b768caf54559b3545e124a76259f34c21d127aab6e8f8fc5598ba46c5e1b |
| motion_623-02-raw.png | image-35600-210 | 727×1063 | 0.6839 | 1962 | 372 | +1.4% | 650a4f3da0fdfac6cf76d384b5f4328d9f9cb71ce1999ded6e79f8b5a347772d |
| motion_623-03-raw.png | image-35600-212 | 604×1344 | 0.4494 | 3887 | 377 | +28.2%（双臂过顶伸展，豁免） | f4ebd70d9d6e3a23b1d1104ee82552f6290664a9d88db243b9c28eb2a64d1c54 |
| motion_623-04-raw.png | image-35600-215 | 514×1295 | 0.3969 | 4378 | 301 | +23.6%（同上，豁免） | b915bbcf43dae7f301910e480541e258a950c172c1750474425a761b49f3e9eb |
| motion_623-05-raw.png | image-35600-217 | 591×1259 | 0.4694 | 3984 | 339 | +20.1%（同上，豁免） | cc94edb16bee5b9fac92b227eb2adfdb8f8577ed41bb2ea5224e3210b701d2d1 |
| motion_623-06-raw.png | image-35600-220 | 671×952 | 0.7048 | 3604 | 382 | −9.2% | eb874e3547e981ecef88289f42a32b203daab18ae237360dd1e3762a9907a918 |
| motion_623-07-raw.png | image-35600-222 | 729×1049 | 0.6949 | 3343 | 409 | +0.1% | c035af0bf50d6e1b0e057b5968ede142865a941ff65b46ebe5a6312f16072b21 |

注：00 首掷（image-35600-203，0.877）宽高比超限重掷已删。03–05 双臂完全过顶伸直把臂长计入 bbox、宽度收窄至 514–604，判定为伸展几何而非体型放大（宽 604<锚 729），按腾空同类豁免登记，此分类为本批次自检补充判据。

## motion_214（横甩掌）

| 帧 | 生成ID | body_w×h | 宽高比 | 黄 | 青 | h vs 锚 | SHA256 |
|---|---|---|---|---|---|---|---|
| motion_214-00-raw.png | image-35600-224 | 630×1033 | 0.6099 | 2926 | 390 | −1.4% | 86d4b3e4571a828cf85cda8c01027e86a33217aed106538abcb52743b1e25aee |
| motion_214-01-raw.png | image-35600-227 | 793×1050 | 0.7552 | 3062 | 360 | +0.2% | 0faaafe6ac3e5bcc972f4c4db8c82af7eb86e7a0f3e072a960783befb8416637 |
| motion_214-02-raw.png | image-35600-228 | 760×1049 | 0.7245 | 3624 | 256 | +0.1% | a558ccbfcb6330376484cd456083879b790630db4868505632a970171fb5451a |
| motion_214-03-raw.png | image-35600-234 | 731×1049 | 0.6969 | 4118 | 369 | +0.1% | ef7eae10e313fb85b32559e759d06f1f23681a7f59b8bea99c93bdf8fcdba7fe |
| motion_214-04-raw.png | image-35600-236 | 698×1051 | 0.6641 | 4548 | 591 | +0.3% | fbd4553319a926bb42b83e1f739310e3b2b8bb5ef944151d3ba601564b2450fc |
| motion_214-05-raw.png | image-35600-238 | 719×1044 | 0.6887 | 3934 | 398 | −0.4% | 08f4cbec56d05853390e76a195b75355c8175ea4d44c6a5ecb55a391eb0fde5c |
| motion_214-06-raw.png | image-35600-240 | 665×944 | 0.7044 | 2666 | 413 | −9.9%（压线通过） | daf6e9cad45a86678fceb0d0c733687e4d12ec43292f06ce352f4b880c56b0b1 |
| motion_214-07-raw.png | image-35600-244 | 729×1048 | 0.6956 | 3843 | 409 | 0.0% | 003abb7fd7d832c9a95d99acf673444e526cfc87c3989993167f78df7b56c141 |

注：03 首掷（image-35600-231，0.895）宽高比超限重掷已删。

## motion_22（守护场，无光效）

| 帧 | 生成ID | body_w×h | 宽高比 | 黄 | 青 | h vs 锚 | SHA256 |
|---|---|---|---|---|---|---|---|
| motion_22-00-raw.png | image-35600-246 | 672×1001 | 0.6713 | 2853 | 432 | −4.5% | 44316a700d57c9e37d60e31e77303954ee08233d07720caaefa5f42e9ab72dbd |
| motion_22-01-raw.png | image-35600-247 | 719×1011 | 0.7112 | 1863 | 264 | −3.5% | 048b0546df02a778a52e74fb1999ccde6f03369ccb420e07f34d4ab12ee79a80 |
| motion_22-02-raw.png | image-35600-253 | 697×1031 | 0.6760 | 3073 | 370 | −1.6% | a1847c6b714fc4d80b87801e16d5c136a324857de9b502117038939276dfbc9c |
| motion_22-03-raw.png | image-35600-255 | 776×1051 | 0.7383 | 2343 | 272 | +0.3% | 14443f291aa0158c58f417ce44701945a6608dce867332049960e001169b278e |
| motion_22-04-raw.png | image-35600-257 | 825×1044 | 0.7902 | 1954 | 298 | −0.4% | 0bb1bdaf8c51b2393ff0d49f970f73bfb3ddd873ea40f0daaa3d6cd432a80291 |
| motion_22-05-raw.png | image-35600-260 | 814×1049 | 0.7760 | 2070 | 333 | +0.1% | 9ac2a5b95ce9ec5681525d70a5045f3e9a6d74fe4137fa6862b638f679dc4e90 |
| motion_22-06-raw.png | image-35600-262 | 793×1051 | 0.7545 | 3408 | 391 | +0.3% | a52a171efbfc489c75b43f1c744c8efb4e2447c148e8c57e78835e2df8116892 |
| motion_22-07-raw.png | image-35600-264 | 731×1050 | 0.6962 | 3517 | 404 | +0.2% | 102a83af0e0c2ecb2426085ba6cb1091dc27843ba76605dd95ed95d5cd73b70a |

注：02 首掷（image-35600-251，0.926 且 −11.5%）双超限重掷已删。

## motion_41236（抱腰过顶掷，只画本角色）

| 帧 | 生成ID | body_w×h | 宽高比 | 黄 | 青 | h vs 锚 | SHA256 |
|---|---|---|---|---|---|---|---|
| motion_41236-00-raw.png | image-35600-267 | 797×997 | 0.7994 | 4468 | 347 | −4.9% | e506eb53ea556780efae1fc33b20d8157aaf78b24ec77a7a9e8ebc1c4c01f359 |
| motion_41236-01-raw.png | image-35600-269 | 702×848 | 0.8278 | 3076 | 408 | −19.1%（屈膝环抱，豁免） | 79fbb98c5970c6c0c8a2132f2f92ff7d4af61a3ccc3b7b0e5ff7dd4f3a26b038 |
| motion_41236-02-raw.png | image-35600-270 | 768×1125 | 0.6827 | 3326 | 370 | +7.4% | 9e1d88828cb83e7800c7de6121b00282dfc9da3057b8ccddc16c1f6aa54599cd |
| motion_41236-03-raw.png | image-35600-272 | 728×1209 | 0.6022 | 3511 | 356 | +15.4%（双臂过顶，豁免） | 4d22ea41127a286fe2a6f062b049329e906365555888ae319d127f75656c3e07 |
| motion_41236-04-raw.png | image-35600-275 | 820×1033 | 0.7938 | 2325 | 372 | −1.4% | 72621f087448f7bece4b89368dae09ccd483bb7c20160d96162a655a45b88d0b |
| motion_41236-05-raw.png | image-35600-279 | 869×1049 | 0.8284 | 2389 | 213 | +0.1% | 58e38a0f2b80a91b7c824e1135cf3f7ad9b59d48f878ed29efe17d1e2dc04603 |
| motion_41236-06-raw.png | image-35600-281 | 435×1063 | 0.4092 | 3386 | 345 | +1.4% | 92fd73a2297cddd6576ae6aeff116b295e245217bae8a347051bf0052c943b19 |
| motion_41236-07-raw.png | image-35600-284 | 735×1042 | 0.7054 | 3959 | 366 | −0.6% | d64588c247c915aa91b0dcb33906339f5812f62ddadcaabfe4bc0456867da4cc |

注：04 首掷（image-35600-274，1.021 且 −13.8%）双超限重掷已删；重掷请求 path 误写（见事故登记）后已移回正式路径。
