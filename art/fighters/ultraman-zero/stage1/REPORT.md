# 赛罗状态动作帧交付记录（2026-11-10）

范围：普通赛罗 stage1 的 20 组缺失状态动作，共 61 帧；只做 art 帧与记录，未安装、未改 assets/content、未启动 Godot、未提交、无录屏。

## 身份与落格

- 身份锚：`art/fighters/ultraman-zero/stage1/idle/frames/identity-idle-pixel.png`（用户 2026-11-09 认可，SHA `c36397a86bff3f6e1469e7efd611dad20ff4938bec30b03c703c9095c0e5df0f`）。
- 动作帧唯一参考：`art/fighters/ultraman-zero/stage1/idle/frames/pixel-raw-02-official-side-anchor.png`（SHA `5f4651673a90f08056a250fea9a6f68ad339501a615658a183a7d07d3791dec3`），未追加其它角度或角色。
- 落格：256×256、root [128,248]、baseline 248、接地行 247、目标站高 188；冻结 32 色板、二值 Alpha。
- 统一源比例：188/1095 = 0.171689497717，全组同一比例，不按每帧外框拉高。
- 后处理：按 `tools/art/stage_cells.py` 的格/root/固定比例落格逻辑；`forge_backend._kcentroid_downscale(detail_bias=False)` + Alpha128 硬化 + 整图 RGB 最近色映射，4px 水平边距。
- 色板说明：`stage_cells.py` 默认取图鉴色板，而赛罗图鉴色板缺青蓝/绿色识别色；按 AGENTS 缺色规则显式使用 `cells.json` 冻结 32 色板，未照跑默认。

## 硬门结果

- 连通块：全部 1。
- Alpha：全部 [0,255] 二值。
- 色数：最多 32，全部 ≤32。
- 裁切：最大 cropped_pixels 0，全部完整。
- 脚底行：接地相 247；腾空相按弧线 180/190/200/215/225，未伪造接地。
- 自动头高/站高只作报告，未作唯一门限；造型以各组 2× 联系表目视核。

## 分组与联系表

### guard（2 帧）

联系表：`art/fighters/ultraman-zero/stage1/contact/guard-sheet.png`，SHA `545bc75e786d5f12d7ebd939b097c7639a25f4c649c93835892f4654426cfd22`。

| 帧 | 角色 | 脚底 | bbox | 高×宽 | 色 | 连通 | Alpha | 裁切 | 生成 ID | 源 SHA | 落格 SHA |
|---|---|---:|---|---:|---:|---:|---|---:|---|---|---|
| guard-00 | 站立护架 | 247 | [58, 60, 185, 247] | 188×128 | 31 | 1 | [0, 255] | 0 | image-65174-1223 | `aba6c147cf4d40d4778c52007f8b23ad6cbd0aeb53b9c974264f40a76b4de643` | `15fc9ac2c5de9cf5b37d7562e0f74e70e50de1247a98025754c4b6ecb6d04d9a` |
| guard-01 | 护架微沉换气 | 247 | [60, 60, 187, 247] | 188×128 | 31 | 1 | [0, 255] | 0 | image-65174-1230 | `158c4e7c40a580d4dd17562668afd6f32a5ed608d097e79952d34c5be4f4696f` | `5e2c78fe4f5a0dd74f96c55d337d3a486ac45b9d8b104016b700ee7ef6255205` |

### crouch（2 帧）

联系表：`art/fighters/ultraman-zero/stage1/contact/crouch-sheet.png`，SHA `a8df98de366c75827336dd56daa387804fc549185cc7b773c11d5f977b699aff`。

| 帧 | 角色 | 脚底 | bbox | 高×宽 | 色 | 连通 | Alpha | 裁切 | 生成 ID | 源 SHA | 落格 SHA |
|---|---|---:|---|---:|---:|---:|---|---:|---|---|---|
| crouch-00 | 深蹲护架 | 247 | [55, 98, 182, 247] | 150×128 | 30 | 1 | [0, 255] | 0 | image-65174-1233 | `b23f3ba130f824aec15c19342f9ac70b4e7b738ff54f00395af3b0f92440e92f` | `75a6e2e57269a6d959e7bae8ac66589ab2a2a8eba9e5254fe5467f1813fe09ee` |
| crouch-01 | 蹲姿重心前移 | 247 | [54, 87, 179, 247] | 161×126 | 31 | 1 | [0, 255] | 0 | image-65174-1238 | `7667ed6ffcc39b5a3a9807469c0a0bb3e8cbd4ab39dba0268d1417b91ece782d` | `373d989823b7730d0e542d38094494faa549c209b1b78ef53137652328cf1183` |

### crouch_start（2 帧）

联系表：`art/fighters/ultraman-zero/stage1/contact/crouch_start-sheet.png`，SHA `5a645483e0cd528719aacadde85b8099a4c793be1a3a1dfabf8a913291bcd8b3`。

| 帧 | 角色 | 脚底 | bbox | 高×宽 | 色 | 连通 | Alpha | 裁切 | 生成 ID | 源 SHA | 落格 SHA |
|---|---|---:|---|---:|---:|---:|---|---:|---|---|---|
| crouch_start-00 | 屈膝下沉 | 247 | [80, 67, 174, 247] | 181×95 | 30 | 1 | [0, 255] | 0 | image-65174-1243 | `16afc92bf9040ec9317aa12a62da92642636114dbfc8dcd77195ce441a6c6252` | `4f1e5b4088017474da782f5b0231ce1c9f4ef16c2cad592cdaf8270eb4fe300d` |
| crouch_start-01 | 半蹲收拳 | 247 | [55, 95, 188, 247] | 153×134 | 31 | 1 | [0, 255] | 0 | image-65174-1252 | `7fdb18f94d05679205824df7d1b3c0f3d08dc9d13a5797b76b589388512565df` | `29afcdb410d870d6818ae3925fc230c9e05fc639e99cab3e19a931aabbf99437` |

### crouch_guard（2 帧）

联系表：`art/fighters/ultraman-zero/stage1/contact/crouch_guard-sheet.png`，SHA `e4514013fb79d7230c3a46fe6cddbb72099b03c92ad65fa82a9e4b107e38eaaa`。

| 帧 | 角色 | 脚底 | bbox | 高×宽 | 色 | 连通 | Alpha | 裁切 | 生成 ID | 源 SHA | 落格 SHA |
|---|---|---:|---|---:|---:|---:|---|---:|---|---|---|
| crouch_guard-00 | 蹲姿交叉格挡 | 247 | [35, 57, 199, 247] | 191×165 | 32 | 1 | [0, 255] | 0 | image-65174-1256 | `3797b403f22974b88a6f0aacc57878d9cf504e7b9636cacee98c1f04dcc72c8f` | `5538892f83b9f9b7260cc9dca6aacb4e5a35f749ad83eb32477f1777446a8b95` |
| crouch_guard-01 | 蹲姿护架 | 247 | [45, 78, 194, 247] | 170×150 | 31 | 1 | [0, 255] | 0 | image-65174-1261 | `6711e0b844337e989b70fe4dfd6b7f96ec20962eaf568640459914db60feb358` | `42686bf1dc10d839c2c36288e0a370277463e0ed2da618a3c27d96d4be14cc62` |

### crouch_rise（2 帧）

联系表：`art/fighters/ultraman-zero/stage1/contact/crouch_rise-sheet.png`，SHA `2ef35d5566c2daa0bc7eb3620c9c38e01ee22f354338c5f2d7dc1b9a7b5f3eb1`。

| 帧 | 角色 | 脚底 | bbox | 高×宽 | 色 | 连通 | Alpha | 裁切 | 生成 ID | 源 SHA | 落格 SHA |
|---|---|---:|---|---:|---:|---:|---|---:|---|---|---|
| crouch_rise-00 | 半蹲蹬地 | 247 | [57, 89, 186, 247] | 159×130 | 30 | 1 | [0, 255] | 0 | image-65174-1279 | `d33da50910878f43fd56c1963c19d6c9023baae77febcff2b900c83081a1ad00` | `3d61a8ec428e7750a654ef041880e1a30d9a6cdd4e296b50cd021b648889031a` |
| crouch_rise-01 | 起身站立 | 247 | [64, 57, 182, 247] | 191×119 | 30 | 1 | [0, 255] | 0 | image-65174-1303 | `be840ad888643962b3224606f5eb664166792ddd1718c35fb4111fc1ffa5ce9f` | `9f62e99d7dafb0add255be1e9d3428478c2e2d51eb146064f02d634927b4724f` |

### crouch_turn（3 帧）

联系表：`art/fighters/ultraman-zero/stage1/contact/crouch_turn-sheet.png`，SHA `396d303c7d05094065fbf286adf73b84c8cc6485d4771f18309550b6e75c5f60`。

| 帧 | 角色 | 脚底 | bbox | 高×宽 | 色 | 连通 | Alpha | 裁切 | 生成 ID | 源 SHA | 落格 SHA |
|---|---|---:|---|---:|---:|---:|---|---:|---|---|---|
| crouch_turn-00 | 蹲姿移重心 | 247 | [61, 83, 183, 247] | 165×123 | 31 | 1 | [0, 255] | 0 | image-65174-1288 | `66be1edb8c0006dd04320fa55608ceba7236e472917ebe445c7975e0c7d16bae` | `d66a712e428394cea926ecd485ebbcb2da6e53c6d5fec0f257866a2054b545c6` |
| crouch_turn-01 | 蹲姿转体 | 247 | [79, 67, 172, 247] | 181×94 | 31 | 1 | [0, 255] | 0 | image-65174-1291 | `2ba64e5643ed43a10aa8d7e772effff1fc128a914dce9f486a7013131fcf5850` | `0de5ec2b3aafcfef03e321795d2cd4d60c8c636f69bf208c7406cdd10c7f9d46` |
| crouch_turn-02 | 转定护架 | 247 | [76, 78, 183, 247] | 170×108 | 31 | 1 | [0, 255] | 0 | image-65174-1307 | `97ce1713835efc8f387fcdeacddcdf1d6ae8fc7f966300e901ce5440585589ad` | `31f16628fff4613f067bcd8812c4bf529eccfbd035982866fd8525ca6565d06e` |

### hit_high（3 帧）

联系表：`art/fighters/ultraman-zero/stage1/contact/hit_high-sheet.png`，SHA `d808e51e83a8281798227b27c773ad166473aac56e4d929f141cd6a99fbf0437`。

| 帧 | 角色 | 脚底 | bbox | 高×宽 | 色 | 连通 | Alpha | 裁切 | 生成 ID | 源 SHA | 落格 SHA |
|---|---|---:|---|---:|---:|---:|---|---:|---|---|---|
| hit_high-00 | 头被打偏 | 247 | [58, 69, 184, 247] | 179×127 | 31 | 1 | [0, 255] | 0 | image-65174-1312 | `dbb9a2ca795239605b8731cd40c6c45ddc30faefc0e82ff8678301911dac2228` | `f94e25d4b4fdc18b319ff81c0b99b17032922cf8afca55eef28108beb8138f59` |
| hit_high-01 | 头猛后仰 | 247 | [54, 66, 187, 247] | 182×134 | 30 | 1 | [0, 255] | 0 | image-65174-1317 | `e6287a303d8ed1200c0e4823367b8ad72d761728cda6d3814f5e3061f93ba517` | `69de25a2c516db88f83d599cc090c9ce812c30ef2c88b71fa709dbad21e147a8` |
| hit_high-02 | 回稳护架 | 247 | [62, 60, 184, 247] | 188×123 | 32 | 1 | [0, 255] | 0 | image-65174-1331 | `f2c9caa8a1a63d1086435740118cde627bcfcc49d3fd0fb3daf618c188e35f42` | `27dc970216d144488b5b428aacc67cad70d995be174bed83ae74ce9ae1cd5a73` |

### hit_mid（3 帧）

联系表：`art/fighters/ultraman-zero/stage1/contact/hit_mid-sheet.png`，SHA `56cd7161372d743d540bbbc6e5a9c8881a9d33a80c02fc19c968b9c7e7819cfa`。

| 帧 | 角色 | 脚底 | bbox | 高×宽 | 色 | 连通 | Alpha | 裁切 | 生成 ID | 源 SHA | 落格 SHA |
|---|---|---:|---|---:|---:|---:|---|---:|---|---|---|
| hit_mid-00 | 腹部受击收腹 | 247 | [56, 72, 183, 247] | 176×128 | 31 | 1 | [0, 255] | 0 | image-65174-1334 | `28cfc01d9f729cb6b73d8bad29f581d347a2a75e8bb8b94c4707624618dfd315` | `6d397a1ef659d178562dfb05d96049026366b97edd1452c36ca4a207fc9c3f54` |
| hit_mid-01 | 上身前折 | 247 | [96, 76, 195, 247] | 172×100 | 30 | 1 | [0, 255] | 0 | image-65174-1338 | `ba4c79fb98b4514eb425335f1c51b76d6d033332e9faad7898d1dcbe2fefb17a` | `62dcf0924e2abddfd1717fae498bbc7d76f95be43f0409153f26f876f8d9de17` |
| hit_mid-02 | 回稳护架 | 247 | [58, 59, 185, 247] | 189×128 | 31 | 1 | [0, 255] | 0 | image-65174-1343 | `cae2c8a1899d776c8547adf26fe884f199500c5c80a3d8ab20e101e27ccc7101` | `bd7e150ba3f25801bcc2a61b7c5939f5c1570ad644fb20d5b7e2bcadbdd53f55` |

### hit_crouch（3 帧）

联系表：`art/fighters/ultraman-zero/stage1/contact/hit_crouch-sheet.png`，SHA `57bb65772bc2f081e4c2081b7bc186fda63b3bcb858b804643dd83759d711c82`。

| 帧 | 角色 | 脚底 | bbox | 高×宽 | 色 | 连通 | Alpha | 裁切 | 生成 ID | 源 SHA | 落格 SHA |
|---|---|---:|---|---:|---:|---:|---|---:|---|---|---|
| hit_crouch-00 | 蹲姿受击侧偏 | 247 | [54, 79, 186, 247] | 169×133 | 31 | 1 | [0, 255] | 0 | image-65174-1356 | `e7599663464b33bffc5073b2fcc8e1dca647c54d70515489a4cd32b2153f86d0` | `2c869f3c8ce88836879a748b9fef0e9e366af117bb603266bed68cd99f81084c` |
| hit_crouch-01 | 后坐撑地 | 247 | [29, 109, 207, 247] | 139×179 | 32 | 1 | [0, 255] | 0 | image-65174-1360 | `f6e32fe8054c3d8f87fd0f22015c9a69e3d4c3906cfb8903b796f8acb61415ba` | `c1bc9f0be443c777ed39b11f36fc961cca388797f7e57fc761d50e47ac9af0e8` |
| hit_crouch-02 | 蹲姿回稳 | 247 | [75, 78, 177, 247] | 170×103 | 32 | 1 | [0, 255] | 0 | image-65174-1365 | `096ef76bafb3e6f85b54528d76dc3027cbd95c4fc602b201e756da4154c67f0b` | `63de49530f768f7368f9bea54218e536473e97fedd04b8900f86c0a5a0fcf3ea` |

### hit_air（3 帧）

联系表：`art/fighters/ultraman-zero/stage1/contact/hit_air-sheet.png`，SHA `255c8a02134f6427888cbaff44efe1fe257c4849ed1ae3ce85f0bb89ae4185e1`。

| 帧 | 角色 | 脚底 | bbox | 高×宽 | 色 | 连通 | Alpha | 裁切 | 生成 ID | 源 SHA | 落格 SHA |
|---|---|---:|---|---:|---:|---:|---|---:|---|---|---|
| hit_air-00 | 空中弓身 | 225 | [59, 71, 197, 225] | 155×139 | 30 | 1 | [0, 255] | 0 | image-65174-1369 | `7719622e50ad96bfecec70e90c815058c7d031221999ba85c4044010594feb41` | `9a350dc8a01f3418a8f87d10a7b816a7282fcffbed720fbb096c0ed30a6d87d5` |
| hit_air-01 | 空中后抛 | 225 | [49, 74, 205, 225] | 152×157 | 31 | 1 | [0, 255] | 0 | image-65174-1387 | `4beab29a511c1d0f5ec3b90ede5b4d1471585a1a07acce2fe4d930efb6f5ae16` | `748a591f7f11b2511206efc3720c15154757300ab33247e128e304f533c7fdc6` |
| hit_air-02 | 空中下坠 | 225 | [66, 74, 172, 225] | 152×107 | 31 | 1 | [0, 255] | 0 | image-65174-1392 | `d9098fc73f0c7d957ec2fc9431a864a46900b74411e44c7e521b869437e15242` | `831682ba61290b939aca51e7c56fcc48dee355d5e3158c037845674d368d4828` |

### roll_forward（5 帧）

联系表：`art/fighters/ultraman-zero/stage1/contact/roll_forward-sheet.png`，SHA `dfb6fd61d472ad8f8d8c2ba41a9cc922795028919be7432192f8c63734cba630`。

| 帧 | 角色 | 脚底 | bbox | 高×宽 | 色 | 连通 | Alpha | 裁切 | 生成 ID | 源 SHA | 落格 SHA |
|---|---|---:|---|---:|---:|---:|---|---:|---|---|---|
| roll_forward-00 | 蹲身撑地 | 247 | [74, 120, 188, 247] | 128×115 | 31 | 1 | [0, 255] | 0 | image-65174-1397 | `2ec8465ee53b25ddf7048f6f2998431992d71607502c813b59052790973f4d25` | `808a2cd90242dffe554a46a43d66289794f4766cfbc387bae470f7068ba5c2e8` |
| roll_forward-01 | 团身肩背触地 | 247 | [83, 130, 194, 247] | 118×112 | 28 | 1 | [0, 255] | 0 | image-65174-1400 | `c1c5f7c8e71f9d4e7c8c7d129967253294b62d05768b4825a2555fde46ac74e1` | `07fc175bb9683982ed6e5c77554651e439179bfbfd6b96c5d943bab7c8efb85b` |
| roll_forward-02 | 倒置滚过背脊 | 247 | [61, 111, 180, 247] | 137×120 | 31 | 1 | [0, 255] | 0 | image-65174-1410 | `29dce0d94b267743b9a9c647acaaf61dfa94a7e806f8e4b3cf836051145eba46` | `c75bfc18bbbc44be39299107fae4f4499b4c598f355f110ed8a8d3f542ef1009` |
| roll_forward-03 | 蹲姿收势 | 247 | [70, 122, 193, 247] | 126×124 | 31 | 1 | [0, 255] | 0 | image-65174-1417 | `e4ffed62883a0a52d53103e9ec11ec8cd73208b89f40d494680646bbccd75fc9` | `27bb3d948c52736656b5147e108a17f072c2051a5a3caf6073495553487c3f88` |
| roll_forward-04 | 起身护架 | 247 | [56, 60, 184, 247] | 188×129 | 32 | 1 | [0, 255] | 0 | image-65174-1425 | `800e0295e78317ffe45345c90843ecdc2b9ca951f1ee1055e390f2d9870e9545` | `fe41f66132f133675d08559a3710b218bfefeb009d1ea9af80dc48d0be2e293e` |

### roll_back（5 帧）

联系表：`art/fighters/ultraman-zero/stage1/contact/roll_back-sheet.png`，SHA `0725e880a81c785e5431be9750d41a401db965581b65d5965cb884cb7494a62c`。

| 帧 | 角色 | 脚底 | bbox | 高×宽 | 色 | 连通 | Alpha | 裁切 | 生成 ID | 源 SHA | 落格 SHA |
|---|---|---:|---|---:|---:|---:|---|---:|---|---|---|
| roll_back-00 | 蹲身后撑 | 247 | [52, 105, 168, 247] | 143×117 | 32 | 1 | [0, 255] | 0 | image-65174-1432 | `a8bcb9e6953d6fdd7cbc3bbada5806da68bd1bc79ded7f051592ade00a7a286b` | `64ac91830d43098df0f3d784903fb9304a3ee616f9f895faf4c6081aa17d5f9f` |
| roll_back-01 | 团身肩背触地 | 247 | [79, 118, 197, 247] | 130×119 | 31 | 1 | [0, 255] | 0 | image-65174-1451 | `43eeb281ddccc516e14fcdd4ccea14b11a416f373ff0df88fdef0a7d4d242a67` | `c43d5a9e065c586bf8949e30f2c17e008c2c40b126c454dfeb1a332c0ae535c2` |
| roll_back-02 | 倒置后滚 | 247 | [88, 98, 239, 247] | 150×152 | 30 | 1 | [0, 255] | 0 | image-65174-1455 | `32d0a1117f4f1c53ef5ae0ff2924a8d0b61d606c40db4d372d1b313e25b952f5` | `206048761c2bea9d116962fec3e46b003b4e0cc518e2674d4c299cf551ee0a79` |
| roll_back-03 | 蹲姿收势 | 247 | [70, 115, 194, 247] | 133×125 | 32 | 1 | [0, 255] | 0 | image-65174-1462 | `adf153c5ce1980793c660b48cddf646b913c2f96daebfb3c0213399aad7ffe21` | `898b5f315775fb4f65a557eef88dde495ee64dfb6719d071076b5767c3f5753a` |
| roll_back-04 | 起身护架 | 247 | [58, 60, 185, 247] | 188×128 | 32 | 1 | [0, 255] | 0 | image-65174-1470 | `893a49d442ca01f866e63ed8cbf17945e2b47e9482db602a28d3a556ff88ed31` | `b0606a25ca64432e955303d3f5833bea483e1d127eb5ad09993bbbfc0b1b773a` |

### wake（5 帧）

联系表：`art/fighters/ultraman-zero/stage1/contact/wake-sheet.png`，SHA `6f7abef0b0d4f68f9d8a273c4f715344209b34d49195d9fae2ce25ceadc2cf4c`。

| 帧 | 角色 | 脚底 | bbox | 高×宽 | 色 | 连通 | Alpha | 裁切 | 生成 ID | 源 SHA | 落格 SHA |
|---|---|---:|---|---:|---:|---:|---|---:|---|---|---|
| wake-00 | 仰面苏醒 | 247 | [26, 126, 209, 247] | 122×184 | 29 | 1 | [0, 255] | 0 | image-65174-1528 | `5fa15f54eeb2460c140213d87830109a711382f70867a4bc5158c5fb8cb7461c` | `4e7a443aebdd80ba3dc4a747fc82ebebbbb20fafdc480e23cd795c0e3d86b0b8` |
| wake-01 | 翻身撑起 | 247 | [15, 91, 211, 247] | 157×197 | 31 | 1 | [0, 255] | 0 | image-65174-1490 | `aa3a57b2750252f24dc8021d5eae30d242d74ec85252e382795da2f60117f201` | `59f9f4ae74617d007f210a440733076571e5c82f5378a130eefe84548ed1046e` |
| wake-02 | 单膝跪起 | 247 | [62, 98, 199, 247] | 150×138 | 31 | 1 | [0, 255] | 0 | image-65174-1493 | `bfef97091f13d659323a5dd94f3de014364395d668dd90d1f176d3fbb02c9904` | `c530dd81ec77a5817deecc2a49a2f2138ed7009fd330c8e969f166b6c4f20c84` |
| wake-03 | 半蹲起身 | 247 | [71, 71, 177, 247] | 177×107 | 31 | 1 | [0, 255] | 0 | image-65174-1534 | `cbb0a8eaf6bbe101e7f2c60755e6c0b44a7a1ce5437d1a7f3dd1bafc10f7ce71` | `3716177e5171e7b2795e2d1e72184b5a18d7ec345f9665c7a45e4b5a61b90f8d` |
| wake-04 | 站立护架 | 247 | [57, 60, 185, 247] | 188×129 | 31 | 1 | [0, 255] | 0 | image-65174-1558 | `ffe1486e02bab6ef4ad4d838941fb3599f25eb376281e86e50ab2aeeace74d64` | `5be547a49d09ea009ecbfd967631e2dcfaa73f9e4b58398c84672025e22c1191` |

### dash_stop（3 帧）

联系表：`art/fighters/ultraman-zero/stage1/contact/dash_stop-sheet.png`，SHA `e4e4636430c32bbf0718c37de838d853656045d36083f97b507d0b4bb38761cf`。

| 帧 | 角色 | 脚底 | bbox | 高×宽 | 色 | 连通 | Alpha | 裁切 | 生成 ID | 源 SHA | 落格 SHA |
|---|---|---:|---|---:|---:|---:|---|---:|---|---|---|
| dash_stop-00 | 前掌刹车 | 247 | [44, 95, 251, 247] | 153×208 | 31 | 1 | [0, 255] | 0 | image-65174-1543 | `18c54d1e613bee11cabe414b3f118aa5a820e770d6e65c6afc9c4279b11832a8` | `465be57781af8a8d167b9bc671aa2f4db19601c5370e4e6c3a357ad36c4aa638` |
| dash_stop-01 | 后坐收势 | 247 | [53, 83, 174, 247] | 165×122 | 31 | 1 | [0, 255] | 0 | image-65174-1565 | `cff0771445c087577dfdcf0fb41e501169f7cef57596c8e828cc48b2cb17fd33` | `d3276011382e61a217244b51df2dc40315243d5bdb274bd99059100d7041dd0e` |
| dash_stop-02 | 站定护架 | 247 | [55, 61, 183, 247] | 187×129 | 32 | 1 | [0, 255] | 0 | image-65174-1571 | `a3a16dd19d0f27bf525f5c81595f176bb6684dc60bde797da23e232e550d5e59` | `6e625470707ac9724007925fef194943465dd063118d68adbff198fbea1e149b` |

### flip_forward（4 帧）

联系表：`art/fighters/ultraman-zero/stage1/contact/flip_forward-sheet.png`，SHA `263c5b11fd64a7229ae6a5fe92bc27c109160c3bb65cdd103ee25ae4908ff330`。

| 帧 | 角色 | 脚底 | bbox | 高×宽 | 色 | 连通 | Alpha | 裁切 | 生成 ID | 源 SHA | 落格 SHA |
|---|---|---:|---|---:|---:|---:|---|---:|---|---|---|
| flip_forward-00 | 蹬地起跳 | 247 | [105, 74, 196, 247] | 174×92 | 31 | 1 | [0, 255] | 0 | image-65174-1577 | `f3739fbcce4b64090bda32cde2ca56b1da22c6fc4bb6cd76a0c96f5f02f2d6ce` | `4ea8a8aebbca3db399400da77f6a73f69876b16c688d7b1d88f8ec30c77a4b75` |
| flip_forward-01 | 空中团身前翻 | 225 | [86, 94, 179, 225] | 132×94 | 31 | 1 | [0, 255] | 0 | image-65174-1594 | `36991d3c7d8dd9ba6b7ceddf799fffe547a1c748b4bb2de27bb00947719aa815` | `ae008d8a6bc95a0e3a14e998b61863efef08c112def7b90e5900f9ca18f01683` |
| flip_forward-02 | 空中展开 | 225 | [11, 60, 154, 225] | 166×144 | 31 | 1 | [0, 255] | 0 | image-65174-1601 | `9e4749a160f9adf6a53dbed2f0ba5d8ad3e0d86e8c5af61251e899cbf1c9bbf8` | `7b8263fa9635c194a7627208aa43cfb8bd3f17646d106ae81e174d6e2980f033` |
| flip_forward-03 | 落地缓冲 | 247 | [60, 100, 179, 247] | 148×120 | 31 | 1 | [0, 255] | 0 | image-65174-1606 | `feb37c6209ee0fde8dd515d6b35e866e85e065964791fa4a8ef4140d5ee7d869` | `82e82dc62403fd6738de6d494860f8784c573bb3292a677d82efe4f255a87466` |

### flip_back（4 帧）

联系表：`art/fighters/ultraman-zero/stage1/contact/flip_back-sheet.png`，SHA `e80c1f4588c377b216be5d899eae58ee2700f945b48b0dfd840a4f3d1d84c561`。

| 帧 | 角色 | 脚底 | bbox | 高×宽 | 色 | 连通 | Alpha | 裁切 | 生成 ID | 源 SHA | 落格 SHA |
|---|---|---:|---|---:|---:|---:|---|---:|---|---|---|
| flip_back-00 | 屈膝蓄力 | 247 | [67, 98, 169, 247] | 150×103 | 30 | 1 | [0, 255] | 0 | image-65174-1610 | `b4d20f88c839ac1d84a7c075dfcf87486d67b89809d964cccb851c099d0febd5` | `9acef00a0c6d72f8d6c90bdac0c94b2b6bb1ba04f7c14294c01d3226ff159de8` |
| flip_back-01 | 蹬地后跃 | 225 | [70, 66, 163, 225] | 160×94 | 31 | 1 | [0, 255] | 0 | image-65174-1629 | `019180333ecf4221dc0fd25dbbd0dbe9c3e771377af38f1e94e676f8b2fab501` | `3997d43745e01e368bd75d09e898893c2815e528c538a41b48ceebcf11f660ef` |
| flip_back-02 | 空中倒置后翻 | 225 | [101, 93, 187, 225] | 133×87 | 31 | 1 | [0, 255] | 0 | image-65174-1639 | `04ae5594ad531b2dfede27281db7f32f485457b5bc8bd36f6c69f553ef41c63f` | `9c5f431950b3216e0e818a22ca1d60c63fb2ce9dbb3cecb8d2b0a87359b550d0` |
| flip_back-03 | 落地缓冲 | 247 | [74, 115, 175, 247] | 133×102 | 31 | 1 | [0, 255] | 0 | image-65174-1647 | `f7dfe1229ef936de6b5566aca0dd0dc73adc096015b4aadfc40ac7e0ab58c083` | `de5bcf2d1b03bf072f30244562df4f65ccc4a6074c056df44aeedd71856ea188` |

### grabbed（3 帧）

联系表：`art/fighters/ultraman-zero/stage1/contact/grabbed-sheet.png`，SHA `c2ecfd87016e6ea3cbdcdd04ed0c902fc43439e71643bcbe9d9eb4fbf5ef7a3c`。

| 帧 | 角色 | 脚底 | bbox | 高×宽 | 色 | 连通 | Alpha | 裁切 | 生成 ID | 源 SHA | 落格 SHA |
|---|---|---:|---|---:|---:|---:|---|---:|---|---|---|
| grabbed-00 | 被抓住胸口 | 247 | [57, 63, 184, 247] | 185×128 | 31 | 1 | [0, 255] | 0 | image-65174-1655 | `028c0970e8a61cb78f7a4ea5120f9f3f964e6fa0ac785e199c6921759b562110` | `2f90322d129eb188c93590cebef5d320e5e13d5f7f2570af42989db692e078b4` |
| grabbed-01 | 被拽后仰 | 247 | [67, 59, 198, 247] | 189×132 | 32 | 1 | [0, 255] | 0 | image-65174-1672 | `935a68eeeb85c35c3d13cadb310676149f5786108be90f1ee5207ddc32e7ffca` | `1cf7703e31c0e951f0423f518a03f8d69c2781922755b9915ac74d1cc60b1e2c` |
| grabbed-02 | 被提离地 | 225 | [81, 63, 222, 225] | 163×142 | 31 | 1 | [0, 255] | 0 | image-65174-1675 | `e7b0de2414072d9622b2d26d0ade50b4091b36e8cfb85b2fbb3f175283fd4bc5` | `fa6b5661dd0817ec612cf3efcc3ee7f7835a8d31950d61788263ff2d53232cda` |

### launch_rise（3 帧）

联系表：`art/fighters/ultraman-zero/stage1/contact/launch_rise-sheet.png`，SHA `afb409baf41c506ab15a51df919b3a43f3b1e818c5f27f04563d15565c9a4ae7`。

| 帧 | 角色 | 脚底 | bbox | 高×宽 | 色 | 连通 | Alpha | 裁切 | 生成 ID | 源 SHA | 落格 SHA |
|---|---|---:|---|---:|---:|---:|---|---:|---|---|---|
| launch_rise-00 | 击飞离地 | 247 | [83, 43, 218, 247] | 205×136 | 31 | 1 | [0, 255] | 0 | image-65174-1679 | `7405944fa6a2f8e0b21781071216bf5c9b5ce1ce35a211c07262b9056b98034b` | `3aa56686a0a43a18dc8596f7588530cc7f71d3fdbf7ae0808b861c9a820d61ff` |
| launch_rise-01 | 上升 | 225 | [82, 30, 201, 225] | 196×120 | 30 | 1 | [0, 255] | 0 | image-65174-1686 | `f49c4114098a23021ac3bcfd4195d25c56a1430e860ab86ebef3c3b80d870cbd` | `ecb5fc9eb9a72142be8ae9b19defff69e3bb77906ba5ddaba0378e534d1ae7bb` |
| launch_rise-02 | 接近顶点 | 200 | [91, 14, 220, 200] | 187×130 | 31 | 1 | [0, 255] | 0 | image-65174-1699 | `b9540df160481476cbd61d62d2d7f02df340ff7be05734b73472b9b9caea4710` | `d3431dfe0fb61193f09db13d670bc58578423d8a243489f5802b7644c9396346` |

### launch_fall（3 帧）

联系表：`art/fighters/ultraman-zero/stage1/contact/launch_fall-sheet.png`，SHA `d7d0fb367e04c41604834147cbda17c9d54876cbed401a8084b1e162abb3ee71`。

| 帧 | 角色 | 脚底 | bbox | 高×宽 | 色 | 连通 | Alpha | 裁切 | 生成 ID | 源 SHA | 落格 SHA |
|---|---|---:|---|---:|---:|---:|---|---:|---|---|---|
| launch_fall-00 | 开始下坠 | 190 | [26, 31, 148, 190] | 160×123 | 32 | 1 | [0, 255] | 0 | image-65174-1705 | `d6742d9dc8eb9a118dd93b92d828c9b59af6f1216f9c805f0f09ca42fe06f4fb` | `0e3d6a270941bc4fbe38daed076f02695618d1fff04cfc8214cde5a9bb05df73` |
| launch_fall-01 | 下坠 | 215 | [108, 62, 227, 215] | 154×120 | 30 | 1 | [0, 255] | 0 | image-65174-1710 | `7f4d99cc0e59df26b5ecf6f49ccaf213d73734cd9a7ea182ad8402627a852b7d` | `fd791e8246cacf05044794a568c86b8bba4c124c9b7926857778194068a86d4a` |
| launch_fall-02 | 即将落地 | 247 | [68, 75, 219, 247] | 173×152 | 32 | 1 | [0, 255] | 0 | image-65174-1715 | `09d0fae368f744fe86004cc495b5644fc1029cbe4380d2e536d661593ad694b5` | `30a7f8120ef5358e0bbbf0c2bbef89835f9def241840568cbbb9cc79136712f3` |

### air_apex（1 帧）

联系表：`art/fighters/ultraman-zero/stage1/contact/air_apex-sheet.png`，SHA `ae19cd14bd11d37ec22c72c70d371acfeb5e1711ed7c1bc09789d28830378ba5`。

| 帧 | 角色 | 脚底 | bbox | 高×宽 | 色 | 连通 | Alpha | 裁切 | 生成 ID | 源 SHA | 落格 SHA |
|---|---|---:|---|---:|---:|---:|---|---:|---|---|---|
| air_apex-00 | 最高点团身 | 180 | [82, 58, 149, 180] | 123×68 | 31 | 1 | [0, 255] | 0 | image-65174-1734 | `928507f4a466758d1c347c07b572965bf2a3022765da8e5a04089b6a386a41ce` | `ede8bc31035877650f9bdcb7dce95b0fcbf81fbaf329c50091bbc5db768d013f` |

## 拒收与重生成

| 候选 | 生成 ID | 源 SHA | 原因 |
|---|---|---|---|
| crouch_rise-00-v1 | image-65174-1266 | `bd7bfa209f442cdcea36193fd14a77ffd16b03a9706708b5c7cddd564718ba0a` | 未保持半蹲，起身过高（落格 192）；改为明确“前膝仍弯约九十度、臀部低于站立”后重生成。 |
| crouch_rise-01-v1 | image-65174-1283 | `a59409ec80a18bf9c348f31e713503d801c4852a74c51ba20bf12ab50b862e78` | 站高 202，超出目标 188 的 3% 门；改为“身高和头身比例与参考图完全相同”后重生成。 |
| wake-00-v1 | image-65174-1485 | `5085c0364f148150f4210c91e00ddcbbdcfa459cc482a4af427c25ae3200841c` | 横躺体宽 278，固定比例落格被裁 591px；改为屈膝收拢的紧凑躺姿后重生成。 |
| wake-03-v1 | image-65174-1500 | `8daef7cea920b3242ecf9d836e086279ae1541d0e4756bb75c0fe75d934f9bb2` | 输出 9 格角色拼图，不是单帧；加“只画单个完整人物的单独一帧、不拼网格”后重生成。 |
| wake-04-v1 | image-65174-1538 | `342579e0bcc4feeae145707fa996e9054c6317750a7ef051b41e3c360d1a47f0` | 站高 198，超出目标 188 的 3% 门；改为“身高和头身比例与参考图完全相同”后重生成。 |

## 已知问题

- 自动头高在受击仰头、张臂、翻滚团身等姿势下失真，只作报告，不作门限；造型以 2× 联系表目视核。
- crouch_start-00 脚距较窄、转向过渡帧角度略偏 3/4；与参考锚的 3/4 侧视一致，未重生成。
- hit_high-00 头部偏转幅度小于后续 hit_high-01，作为受击起始相保留。
- wake-00 为紧凑仰躺相，腿部屈起以避免横躺超格裁切。
- walk/run 类未在本轮范围内。

## 未做与边界

- 帧数说明：任务清单 20 组逐项相加为 61 帧（guard 2、crouch 2、crouch_start 2、crouch_guard 2、crouch_rise 2、crouch_turn 3、hit_high 3、hit_mid 3、hit_crouch 3、hit_air 3、roll_forward 5、roll_back 5、wake 5、dash_stop 3、flip_forward 4、flip_back 4、grabbed 3、launch_rise 3、launch_fall 3、air_apex 1），本次实际交付 61 帧。
- 攻击 8 组（pulse、ranged_forward、crouch_light2、motion_236、motion_623、motion_214、motion_22、motion_41236）已由另一代理负责，本轮按要求未触碰，未改动其 raw/cell。
- 未安装、未接运行时、未启动 Godot、未提交；无录屏，720/1080、实速、双朝向与声音均未验。
- 评审按用户 2026-11-10 指示自动通过，`review_authority=root_delegated_by_user`，不是 user_approved，不是用户亲审。
