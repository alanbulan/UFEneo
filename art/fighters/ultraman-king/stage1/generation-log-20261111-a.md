# ultraman-king 动作原始帧生成日志（2026-11-11-a）

- 参考：art/fighters/ultraman-king/stage1/idle/frames/pixel-raw-01-v18.png（唯一参考）
- 模型 codex/gpt-image-2，quality high，请求 1024x1536；本服务对本角色确定实收 1094x1438（requests.json policy 同口径），按实收判定
- 自检：RGBA、alpha 0-255、身体(alpha>=128)宽高比 0.35-0.85、红眼>=100、披风>=5000；站姿帧 bbox 高与锚 1411 差>10% 判败，蹲/躺/被投/腾空/超时泄气组只登记
- 受投/团身/平躺/立正等姿势宽高比天然出界，目检形态正确后按姿势特性接受并登记，注明原因
- 任务标题 89 张，分组明细合计 101 帧，按明细执行，101 帧全部完成

## burst
- burst-00-raw.png | ID image-35600-10 | 尺寸 1094x1438 | 宽高比 0.778 | bbox高 1173 | 红眼 20982 | 披风 40653 | alpha [0,255] | 重掷 0 | SHA256 6462ca4da8eda7c41a6edd4a6670503f5ebfaeeed3b03d42b42bf758b49252b6
- burst-01-raw.png | ID image-35600-40 | 尺寸 1094x1438 | 宽高比 0.633 | bbox高 1414 | 红眼 52657 | 披风 75887 | alpha [0,255] | 重掷 0 | SHA256 6c6288f7ccbb299285b65109b16374df58753c55abac06d5da92caa98b0eb851
- burst-02-raw.png | ID image-35600-45 | 尺寸 1094x1438 | 宽高比 0.628 | bbox高 1423 | 红眼 40117 | 披风 71767 | alpha [0,255] | 重掷 0 | SHA256 545213bcc17c19ac5a04e9fc44bbe0d541aed808cc1e9e319a77e8e3bd918db8
- burst-03-raw.png | ID image-35600-47 | 尺寸 1094x1438 | 宽高比 0.736 | bbox高 1392 | 红眼 83107 | 披风 95969 | alpha [0,255] | 重掷 0 | SHA256 11757b7fe4814a82814835a6be7f5d5064753a621dee7d66d1c419783fbdcfe7
- burst-04-raw.png | ID image-35600-51 | 尺寸 1094x1438 | 宽高比 0.675 | bbox高 1309 | 红眼 39159 | 披风 63576 | alpha [0,255] | 重掷 0 | SHA256 7f501f7c0c8886e1d162084b063300a1464f1540769af91fb3d681e643ca39eb

## charge
- charge-00-raw.png | ID image-35600-52 | 尺寸 1094x1438 | 宽高比 0.708 | bbox高 1385 | 红眼 44100 | 披风 66103 | alpha [0,255] | 重掷 0 | SHA256 a63496b1d1a64845e335828008ae51f3457f5407ef0322278eb7c40aa41ead87
- charge-01-raw.png | ID image-35600-56 | 尺寸 1094x1438 | 宽高比 0.691 | bbox高 1409 | 红眼 50333 | 披风 65659 | alpha [0,255] | 重掷 0 | SHA256 f19bf5a4775d215c160f1a25b9e9f6a5c049dcf566406797408e82cff15954cb
- charge-02-raw.png | ID image-35600-58 | 尺寸 1094x1438 | 宽高比 0.696 | bbox高 1410 | 红眼 43150 | 披风 66778 | alpha [0,255] | 重掷 0 | SHA256 e41ce9422c21d991be77dbe057505728ede604969b734723bacc0abe90853c1d
- charge-03-raw.png | ID image-35600-61 | 尺寸 1094x1438 | 宽高比 0.701 | bbox高 1404 | 红眼 50543 | 披风 68443 | alpha [0,255] | 重掷 0 | SHA256 2edd59b63f6e11a8a3bc0f1e8659e636ea5d33cafc7dabb13e1a4109c7826224

## charge_start
- charge_start-00-raw.png | ID image-35600-63 | 尺寸 1094x1438 | 宽高比 0.745 | bbox高 1335 | 红眼 34897 | 披风 65891 | alpha [0,255] | 重掷 0 | SHA256 a8ae723c9f6dd66fa104bdf9d729643eb5610032610a820c52d5f8dbfe2d9e45
- charge_start-01-raw.png | ID image-35600-67 | 尺寸 1094x1438 | 宽高比 0.681 | bbox高 1410 | 红眼 26041 | 披风 62916 | alpha [0,255] | 重掷 0 | SHA256 b8e72073b82c1a27fd0838fd9916adf27ea8f32a3ee7c52f9a162c6cb374c375
- charge_start-02-raw.png | ID image-35600-68 | 尺寸 1094x1438 | 宽高比 0.644 | bbox高 1403 | 红眼 44346 | 披风 71733 | alpha [0,255] | 重掷 0 | SHA256 d289298c16a02d34a82290f797443da861af43ccde7af851a3b964f4be931f7e

## charge_stop
- charge_stop-00-raw.png | ID image-35600-70 | 尺寸 1094x1438 | 宽高比 0.694 | bbox高 1414 | 红眼 16609 | 披风 64084 | alpha [0,255] | 重掷 0 | SHA256 25836dd9eae35827224e7f25d0deb63127a7679ec1144420d621c8ac515659d5
- charge_stop-01-raw.png | ID image-35600-72 | 尺寸 1094x1438 | 宽高比 0.694 | bbox高 1413 | 红眼 56555 | 披风 76484 | alpha [0,255] | 重掷 0 | SHA256 530294748d90e4ce253676ac038046f24ff05027ca094bb18b875d710f6dcba1

## dash_throw
- dash_throw-00-raw.png | ID image-35600-79 | 尺寸 1094x1438 | 宽高比 0.831 | bbox高 1280 | 红眼 63974 | 披风 72847 | alpha [0,255] | 重掷 1 | SHA256 62cc078f2d7ba75a036fd76e6f410807ab1d1e97227d69b7a272047e12c1bfa2
- dash_throw-01-raw.png | ID image-35600-76 | 尺寸 1094x1438 | 宽高比 0.961（抓抱相深蹲前倾姿势特性，超门接受并登记） | bbox高 1115 | 红眼 54389 | 披风 58182 | alpha [0,255] | 重掷 0 | SHA256 ad95a968ba706e1ce0d56a7326ffa6ba2aa3ea39ec8ad10eeffff3b75dd58b9c
- dash_throw-02-raw.png | ID image-35600-82 | 尺寸 1094x1438 | 宽高比 0.703 | bbox高 1410 | 红眼 57284 | 披风 84120 | alpha [0,255] | 重掷 0 | SHA256 0176e090a4bf2f92f5ac0a32f76b3496c943c8879dfcbeff0bfc85889e41e454
- dash_throw-03-raw.png | ID image-35600-83 | 尺寸 1094x1438 | 宽高比 0.733 | bbox高 1414 | 红眼 45391 | 披风 83959 | alpha [0,255] | 重掷 0 | SHA256 719aefb2c337c19c036752b2d897f617c2eab838701d4fc209ed34961b3612e3
- dash_throw-04-raw.png | ID image-35600-89 | 尺寸 1094x1438 | 宽高比 0.730 | bbox高 1376 | 红眼 49588 | 披风 58143 | alpha [0,255] | 重掷 1 | SHA256 f3a611ccab0c870ddba1bdf2f445d480ff384bdb18746cba3f1144e514959564
- dash_throw-05-raw.png | ID image-35600-87 | 尺寸 1094x1438 | 宽高比 0.411 | bbox高 1414 | 红眼 15168 | 披风 54129 | alpha [0,255] | 重掷 0 | SHA256 654c1dd9ce04f2f455edf4957470cfbf252645dc484eb5c8c1dcc4ed669cbc7e

## grabbed
- grabbed-00-raw.png | ID image-35600-92 | 尺寸 1094x1438 | 宽高比 0.688 | bbox高 1412 | 红眼 32487 | 披风 64710 | alpha [0,255] | 重掷 0 | SHA256 ed0a15d65a4c242513c3d7d2dda303b05a3bc4e961d08d011f29a8b38ef36feb
- grabbed-01-raw.png | ID image-35600-94 | 尺寸 1094x1438 | 宽高比 0.692 | bbox高 1413 | 红眼 49317 | 披风 76069 | alpha [0,255] | 重掷 0 | SHA256 a8403562f058c56e1d1539c56074f1c394387c5225cd513567c512378c6ba159
- grabbed-02-raw.png | ID image-35600-97 | 尺寸 1094x1438 | 宽高比 0.741 | bbox高 1295 | 红眼 58145 | 披风 78652 | alpha [0,255] | 重掷 0 | SHA256 f6f95a7c8175f4f0aa0dc8f990c802ed1033221d7350147eb9cf03fc47292234

## intro
- intro-00-raw.png | ID image-35600-98 | 尺寸 1094x1438 | 宽高比 0.359 | bbox高 1416 | 红眼 42320 | 披风 50244 | alpha [0,255] | 重掷 0 | SHA256 7f2119832767451402ec7117411b90ddfceeef93b139038f0bf367c35a3fad76
- intro-01-raw.png | ID image-35600-101 | 尺寸 1094x1438 | 宽高比 0.564 | bbox高 1407 | 红眼 35399 | 披风 60225 | alpha [0,255] | 重掷 0 | SHA256 686d325efab85346f2396e8c076089cca833c9d1305eb8a170ea7203a065a2fc
- intro-02-raw.png | ID image-35600-102 | 尺寸 1094x1438 | 宽高比 0.659 | bbox高 1411 | 红眼 26678 | 披风 65345 | alpha [0,255] | 重掷 0 | SHA256 1912594911b117989121076d54bab08d0cb8a68f2c706c4ad07080592d75f84b
- intro-03-raw.png | ID image-35600-105 | 尺寸 1094x1438 | 宽高比 0.333（登场立正垂手侧视姿势特性，超门接受并登记） | bbox高 1418 | 红眼 43783 | 披风 58130 | alpha [0,255] | 重掷 0 | SHA256 0ad7674907c9ff86a66673a8f638fa79a12827aaf5e0919faf84438e1df70d99
- intro-04-raw.png | ID image-35600-108 | 尺寸 1094x1438 | 宽高比 0.648 | bbox高 1411 | 红眼 65624 | 披风 77247 | alpha [0,255] | 重掷 0 | SHA256 72dcdf867af67f33a2d12d97dc13490baa56728901b3c905fcda426aa5182a19
- intro-05-raw.png | ID image-35600-115 | 尺寸 1094x1438 | 宽高比 0.694 | bbox高 1412 | 红眼 48074 | 披风 74453 | alpha [0,255] | 重掷 0 | SHA256 ccdf80c6376d21771ba8c2c1a2b31f03edda9cb89f7da51650cc5a0837f38718
- intro-06-raw.png | ID image-35600-116 | 尺寸 1094x1438 | 宽高比 0.694 | bbox高 1363 | 红眼 53415 | 披风 73519 | alpha [0,255] | 重掷 0 | SHA256 80d5473047a36de0a8cf8ff5fdbf1fea60a1e6ccabb781cc711f13a3a5f21ec9
- intro-07-raw.png | ID image-35600-119 | 尺寸 1094x1438 | 宽高比 0.688 | bbox高 1414 | 红眼 52949 | 披风 76410 | alpha [0,255] | 重掷 0 | SHA256 b8c1439110d2e66477f13bb468d8236b3366e361af3581f4afd33b69e7217d58

## motion_214
- motion_214-00-raw.png | ID image-35600-123 | 尺寸 1094x1438 | 宽高比 0.674 | bbox高 1407 | 红眼 57398 | 披风 74773 | alpha [0,255] | 重掷 0 | SHA256 b51a5e03b878b3c4a79698f5f7702db3a64dd97a8ce1260eb5d55b47149767e9
- motion_214-01-raw.png | ID image-35600-130 | 尺寸 1094x1438 | 宽高比 0.759 | bbox高 1413 | 红眼 41480 | 披风 82286 | alpha [0,255] | 重掷 0 | SHA256 abe6237812e2762c57825c5c208601a685d9ad59873dd9c270b1712babb924e4
- motion_214-02-raw.png | ID image-35600-132 | 尺寸 1094x1438 | 宽高比 0.730 | bbox高 1413 | 红眼 47598 | 披风 62027 | alpha [0,255] | 重掷 0 | SHA256 5ff1f815d575c23fbccc8a74a6c06d1917dcf1cfc320b29f6da3c076618a49d3
- motion_214-03-raw.png | ID image-35600-139 | 尺寸 1094x1438 | 宽高比 0.827 | bbox高 1292 | 红眼 73030 | 披风 77012 | alpha [0,255] | 重掷 0 | SHA256 ac89147316bceeb0965d40e90c1108484eceef7b1a814a4e2ecb55d9635957a4
- motion_214-04-raw.png | ID image-35600-142 | 尺寸 1094x1438 | 宽高比 0.689 | bbox高 1415 | 红眼 44309 | 披风 66802 | alpha [0,255] | 重掷 0 | SHA256 3be35162ae1b32bde704f37765bee6ffaa06cc78fe6bf0e0e52a7f840417f17a
- motion_214-05-raw.png | ID image-35600-148 | 尺寸 1094x1438 | 宽高比 0.439 | bbox高 1416 | 红眼 44778 | 披风 58995 | alpha [0,255] | 重掷 0 | SHA256 21dc2c5ec5554126eb4cfe9d229afbeb93680df98d17688e9f631ebdb65137e1
- motion_214-06-raw.png | ID image-35600-150 | 尺寸 1094x1438 | 宽高比 0.607 | bbox高 1411 | 红眼 60407 | 披风 80838 | alpha [0,255] | 重掷 0 | SHA256 00b9f91f24f6d85c6a8578638a9ffaa95335b537f0ceda88270894b84afba19e
- motion_214-07-raw.png | ID image-35600-156 | 尺寸 1094x1438 | 宽高比 0.693 | bbox高 1414 | 红眼 60850 | 披风 79564 | alpha [0,255] | 重掷 0 | SHA256 8fb1cdfe00294ef80ea5ef756cb0bfa172f45ccae7dbf593a7848925b9cb208b

## motion_22
- motion_22-00-raw.png | ID image-35600-160 | 尺寸 1094x1438 | 宽高比 0.692 | bbox高 1415 | 红眼 52599 | 披风 73206 | alpha [0,255] | 重掷 0 | SHA256 998e76e7cc4cf5c7674552a83a6cb4974822a5bd44ea134b9214991f94213d30
- motion_22-01-raw.png | ID image-35600-165 | 尺寸 1094x1438 | 宽高比 0.696 | bbox高 1413 | 红眼 64347 | 披风 81126 | alpha [0,255] | 重掷 0 | SHA256 229fc046d788b714a497b8095d245651c6ffe4f5d1a0b297c84b55b8eee22e5c
- motion_22-02-raw.png | ID image-35600-169 | 尺寸 1094x1438 | 宽高比 0.694 | bbox高 1414 | 红眼 4539 | 披风 75780 | alpha [0,255] | 重掷 0 | SHA256 e9f70728ba5b9eb47bfb0f8d6a015e68a15e95efeeb61de8aea32589777b3c24
- motion_22-03-raw.png | ID image-35600-175 | 尺寸 1094x1438 | 宽高比 0.710 | bbox高 1414 | 红眼 54508 | 披风 75741 | alpha [0,255] | 重掷 0 | SHA256 92b060dffe7cb609219b18abd4503075cef6e1c5c682b05588092ee54403278b
- motion_22-04-raw.png | ID image-35600-179 | 尺寸 1094x1438 | 宽高比 0.694 | bbox高 1415 | 红眼 41159 | 披风 74717 | alpha [0,255] | 重掷 0 | SHA256 85cfd823eb462eb7f0afdfb7a09e5331b6a633f9a99ee7034d4d74d721a87500
- motion_22-05-raw.png | ID image-35600-186 | 尺寸 1094x1438 | 宽高比 0.707 | bbox高 1387 | 红眼 47794 | 披风 81012 | alpha [0,255] | 重掷 0 | SHA256 9eba8405a799beca1b06c374dc5baae36c11119e165d09f2410154dbc57444bd
- motion_22-06-raw.png | ID image-35600-191 | 尺寸 1094x1438 | 宽高比 0.690 | bbox高 1414 | 红眼 50056 | 披风 63223 | alpha [0,255] | 重掷 0 | SHA256 0d0ebb27b410532aafc426abf080505fe04281efef9ccf7f472e9b162aba0e7a
- motion_22-07-raw.png | ID image-35600-198 | 尺寸 1094x1438 | 宽高比 0.686 | bbox高 1417 | 红眼 53589 | 披风 78914 | alpha [0,255] | 重掷 0 | SHA256 5e76d63c7131632a45ab625cc75750f003701d0facb2648d9ae44577800316f1

## motion_41236
- motion_41236-00-raw.png | ID image-35600-202 | 尺寸 1094x1438 | 宽高比 0.803 | bbox高 1228 | 红眼 49186 | 披风 70759 | alpha [0,255] | 重掷 0 | SHA256 476777bfc1b88af3dad954a1a0cf3dcd8f055b2a031258fc3582ecae0cce6056
- motion_41236-01-raw.png | ID image-35600-206 | 尺寸 1094x1438 | 宽高比 0.731 | bbox高 1277 | 红眼 50385 | 披风 74898 | alpha [0,255] | 重掷 0 | SHA256 38ca8615f2c60f6cdea6c3b28ed5f26b9071d9002be0b469833ada61ca9b87b4
- motion_41236-02-raw.png | ID image-35600-209 | 尺寸 1094x1438 | 宽高比 0.669 | bbox高 1414 | 红眼 61696 | 披风 75054 | alpha [0,255] | 重掷 0 | SHA256 b2500ea9f336bd9eeeb6ad05495bec00d67681f95337caffe258a6823362f051
- motion_41236-03-raw.png | ID image-35600-213 | 尺寸 1094x1438 | 宽高比 0.587 | bbox高 1414 | 红眼 40190 | 披风 57895 | alpha [0,255] | 重掷 0 | SHA256 f093e6b9388c5eb111387f9b893d026d8e63dd54eb3b0fcab7e6fe6aceb93434
- motion_41236-04-raw.png | ID image-35600-214 | 尺寸 1094x1438 | 宽高比 0.824 | bbox高 1292 | 红眼 60018 | 披风 76783 | alpha [0,255] | 重掷 0 | SHA256 2565ef48459748b35b6d0dcc4abb88da886a4d73c4c200384bd75d80cf6a514d
- motion_41236-05-raw.png | ID image-35600-226 | 尺寸 1094x1438 | 宽高比 0.731 | bbox高 1324 | 红眼 26746 | 披风 47370 | alpha [0,255] | 重掷 1 | SHA256 2e1cb1df573626313c159608f6d224254a6dbba9372325e77e9d68271b858ac0
- motion_41236-06-raw.png | ID image-35600-221 | 尺寸 1094x1438 | 宽高比 0.364 | bbox高 1414 | 红眼 43025 | 披风 58647 | alpha [0,255] | 重掷 0 | SHA256 3c1efc3bc9aab07d513ec49f6586f75dbf75ee2fe193a8eaa275f0b038820446
- motion_41236-07-raw.png | ID image-35600-230 | 尺寸 1094x1438 | 宽高比 0.694 | bbox高 1413 | 红眼 64302 | 披风 81181 | alpha [0,255] | 重掷 0 | SHA256 3bc12219e0411f16ae6da25d1264438d7791a9d396e7727a67553d687f104e77

## motion_623
- motion_623-00-raw.png | ID image-35600-232 | 尺寸 1094x1438 | 宽高比 0.757 | bbox高 1109 | 红眼 33769 | 披风 53198 | alpha [0,255] | 重掷 0 | SHA256 5b5b6cc3037b44a8314b7224e4adbe31910b9a8cbd62c953c4ef463a0375de78
- motion_623-01-raw.png | ID image-35600-241 | 尺寸 1094x1438 | 宽高比 0.690 | bbox高 1414 | 红眼 46794 | 披风 72131 | alpha [0,255] | 重掷 0 | SHA256 f036c78ba4c14e4709bf40ba68d221bfad0616b9fbd9f83c8abcf0042e0c0bbc
- motion_623-02-raw.png | ID image-35600-243 | 尺寸 1094x1438 | 宽高比 0.708 | bbox高 1413 | 红眼 72839 | 披风 91793 | alpha [0,255] | 重掷 0 | SHA256 d55bbb05cde11e6b1defa3e86b338a35099a58233ae3c68e3e4ce0a54301af84
- motion_623-03-raw.png | ID image-35600-248 | 尺寸 1094x1438 | 宽高比 0.576 | bbox高 1420 | 红眼 56670 | 披风 77323 | alpha [0,255] | 重掷 0 | SHA256 fd1cf2a51603d4b9b3e56300e3fa08848c08149e2576ddb55517c4d5794ae137
- motion_623-04-raw.png | ID image-35600-254 | 尺寸 1094x1438 | 宽高比 0.687 | bbox高 1414 | 红眼 54181 | 披风 72498 | alpha [0,255] | 重掷 1 | SHA256 dbce08b678b293edd24c81ecc3ba6fa17647bfc1485c767e6095638e02faff51
- motion_623-05-raw.png | ID image-35600-258 | 尺寸 1094x1438 | 宽高比 0.469 | bbox高 1415 | 红眼 52184 | 披风 57445 | alpha [0,255] | 重掷 0 | SHA256 45f7f6a1318cca0362c342050cd80322b85a2f39d246801694d816bce5eae9d9
- motion_623-06-raw.png | ID image-35600-261 | 尺寸 1094x1438 | 宽高比 0.599 | bbox高 1380 | 红眼 40886 | 披风 70076 | alpha [0,255] | 重掷 0 | SHA256 0d5b78dc25e0d715c8a26c97179fed616513e88f2e50b3c5ba5540dbe0267240
- motion_623-07-raw.png | ID image-35600-265 | 尺寸 1094x1438 | 宽高比 0.691 | bbox高 1415 | 红眼 66173 | 披风 77589 | alpha [0,255] | 重掷 0 | SHA256 c610afd35d75c33b7bc731aee0a0a07ca4dad3c8d84f408ad33713dc9c9d41c2

## taunt
- taunt-00-raw.png | ID image-35600-276 | 尺寸 1094x1438 | 宽高比 0.685 | bbox高 1414 | 红眼 58816 | 披风 76990 | alpha [0,255] | 重掷 0 | SHA256 dde20ba3c4aef52c74c9f93e0076484c4827611a838df6565127cf38f8b86c8d
- taunt-01-raw.png | ID image-35600-278 | 尺寸 1094x1438 | 宽高比 0.694 | bbox高 1413 | 红眼 61522 | 披风 75843 | alpha [0,255] | 重掷 0 | SHA256 420f99d6c56daa8e6b823ad52de8e2f881ead09d216688d42a7b2bd514f20224
- taunt-02-raw.png | ID image-35600-282 | 尺寸 1094x1438 | 宽高比 0.691 | bbox高 1413 | 红眼 51993 | 披风 75232 | alpha [0,255] | 重掷 0 | SHA256 a11c5b573c156eab3d08445b9d9e3ce6c34632419316223877513e7cd0678124
- taunt-03-raw.png | ID image-35600-283 | 尺寸 1094x1438 | 宽高比 0.579 | bbox高 1414 | 红眼 30115 | 披风 62281 | alpha [0,255] | 重掷 0 | SHA256 7ff2c3acf8c9dab1b621bed2a6dedbde188fa3a28bf69113c87b37e677bf8231
- taunt-04-raw.png | ID image-35600-286 | 尺寸 1094x1438 | 宽高比 0.710 | bbox高 1381 | 红眼 58435 | 披风 79567 | alpha [0,255] | 重掷 0 | SHA256 02c6fbd262e4b968bb5dd42dddf4c322d162f69cee2c7c6fa6e4467013373f06
- taunt-05-raw.png | ID image-35600-287 | 尺寸 1094x1438 | 宽高比 0.693 | bbox高 1415 | 红眼 62283 | 披风 76681 | alpha [0,255] | 重掷 0 | SHA256 949ee35dd72038a18b8d4942eff227a45f5786ca499160eb7967b88264fd1549

## throw_tech
- throw_tech-00-raw.png | ID image-35600-289 | 尺寸 1094x1438 | 宽高比 0.679 | bbox高 1412 | 红眼 53160 | 披风 70064 | alpha [0,255] | 重掷 0 | SHA256 eb8d827bc3d4f7c3e7b42db63c06e753b79fd77ebb4c4b3a4f05fa155113a92a
- throw_tech-01-raw.png | ID image-35600-290 | 尺寸 1094x1438 | 宽高比 0.753 | bbox高 1342 | 红眼 40951 | 披风 90889 | alpha [0,255] | 重掷 0 | SHA256 75d916d330f67ea2925498ef6c881f79e765b595b9d4d87ae79f0731eb810802
- throw_tech-02-raw.png | ID image-35600-297 | 尺寸 1094x1438 | 宽高比 0.488 | bbox高 1413 | 红眼 42692 | 披风 57744 | alpha [0,255] | 重掷 1 | SHA256 7a34087a3ed1c4358609d2c6fc57775a7c039f05e2a4f5a4384db3ae2c14336c
- throw_tech-03-raw.png | ID image-35600-294 | 尺寸 1094x1438 | 宽高比 0.694 | bbox高 1413 | 红眼 66836 | 披风 80727 | alpha [0,255] | 重掷 0 | SHA256 1d128d8a8f3e92043d8c45cd0870a73d5b22f533e441970e7399df745d47ccf1

## thrown_air
- thrown_air-00-raw.png | ID image-35600-300 | 尺寸 1094x1438 | 宽高比 0.801 | bbox高 1325 | 红眼 53383 | 披风 65629 | alpha [0,255] | 重掷 0 | SHA256 310c8a56e2cf16375a2761e88095f5c0a5a55514b85f05044ee3a4bb5133a46a
- thrown_air-01-raw.png | ID image-35600-302 | 尺寸 1094x1438 | 宽高比 0.675 | bbox高 1395 | 红眼 45580 | 披风 72483 | alpha [0,255] | 重掷 0 | SHA256 c67ace151b4b52c86c03f026c296eef9f603952323886346e2cfa92e840b3f34
- thrown_air-02-raw.png | ID image-35600-304 | 尺寸 1094x1438 | 宽高比 0.802 | bbox高 1079 | 红眼 74270 | 披风 83560 | alpha [0,255] | 重掷 0 | SHA256 112a5d6f57f00b0bb1d2fa78983e54b38a5ffbf212f825907a6c60fc9bae58a1
- thrown_air-03-raw.png | ID image-35600-306 | 尺寸 1094x1438 | 宽高比 0.743 | bbox高 1398 | 红眼 34341 | 披风 79832 | alpha [0,255] | 重掷 0 | SHA256 5eea4f7376365b2665bcb794eb76f082983d53d19fe1c748c1b89944885ba6ee

## thrown_back
- thrown_back-00-raw.png | ID image-35600-309 | 尺寸 1094x1438 | 宽高比 0.775 | bbox高 1348 | 红眼 54442 | 披风 59993 | alpha [0,255] | 重掷 0 | SHA256 b01b514db854e774812fc1fea63be0d7106b46cab970dfbcf6abe67ad11d6a56
- thrown_back-01-raw.png | ID image-35600-311 | 尺寸 1094x1438 | 宽高比 0.800 | bbox高 1274 | 红眼 69715 | 披风 81059 | alpha [0,255] | 重掷 0 | SHA256 14e8de7f2021361b9bbfa973e2965536d2ea3333b44cc6e2ab2a3c5b4f1f06bc
- thrown_back-02-raw.png | ID image-35600-313 | 尺寸 1094x1438 | 宽高比 1.189（水平倒向后方姿势特性，超门接受并登记） | bbox高 890 | 红眼 34093 | 披风 72739 | alpha [0,255] | 重掷 0 | SHA256 06f270f8f39339456c2a7d19d013c3b0d640672fe380b627dd7526ce113012b8
- thrown_back-03-raw.png | ID image-35600-314 | 尺寸 1094x1438 | 宽高比 1.036（蜷身团身姿势特性，超门接受并登记） | bbox高 909 | 红眼 45969 | 披风 56123 | alpha [0,255] | 重掷 0 | SHA256 eaf5714dfdf7689fee4cb52ca7aa325d4d558ab9260edf447df5ad44a1d41fa2

## thrown_dash
- thrown_dash-00-raw.png | ID image-35600-316 | 尺寸 1094x1438 | 宽高比 1.044（后仰双脚前踢姿势特性，超门接受并登记） | bbox高 1014 | 红眼 61407 | 披风 68525 | alpha [0,255] | 重掷 0 | SHA256 4c5e3dfb513cbfde2cc997c41e7ecefda896069e22375652298aaaa1d3163763
- thrown_dash-01-raw.png | ID image-35600-318 | 尺寸 1094x1438 | 宽高比 1.142（水平后倒双腿前伸姿势特性，超门接受并登记） | bbox高 951 | 红眼 43671 | 披风 66580 | alpha [0,255] | 重掷 0 | SHA256 27651f05b0bd8379df760e085239c8893a7021089e59766c54ef755951f85ac6
- thrown_dash-02-raw.png | ID image-35600-320 | 尺寸 1094x1438 | 宽高比 1.706（贴地滑出平躺姿势特性，超门接受并登记） | bbox高 630 | 红眼 20927 | 披风 25925 | alpha [0,255] | 重掷 0 | SHA256 2aa2cffda697dd6059634af8d7c9b3431af499d6f1b61246af2ca0bb3ae221aa
- thrown_dash-03-raw.png | ID image-35600-321 | 尺寸 1094x1438 | 宽高比 0.931（蜷身缓冲团姿姿势特性，超门接受并登记） | bbox高 844 | 红眼 1080 | 披风 34639 | alpha [0,255] | 重掷 0 | SHA256 693bb363727df93c187203d30cdd833f94bd824fd87e96f0f693f5e2a48fbc6f

## thrown_forward
- thrown_forward-00-raw.png | ID image-35600-324 | 尺寸 1094x1438 | 宽高比 0.868（前倾失衡加披风后扬姿势特性，超门接受并登记） | bbox高 1226 | 红眼 24898 | 披风 69770 | alpha [0,255] | 重掷 0 | SHA256 0bad74ac4ce4e472322c5c30891aa564cd2db510eccd2b9ef8db51a214a62554
- thrown_forward-01-raw.png | ID image-35600-325 | 尺寸 1094x1438 | 宽高比 1.041（低位前扑加披风后扬姿势特性，超门接受并登记） | bbox高 1020 | 红眼 42281 | 披风 45559 | alpha [0,255] | 重掷 0 | SHA256 ac0f7beb8931b572c0d60f233f47506f56e7bbfff10c2e162934bce316a47497
- thrown_forward-02-raw.png | ID image-35600-327 | 尺寸 1094x1438 | 宽高比 1.530（水平前扑姿势特性，超门接受并登记） | bbox高 693 | 红眼 43375 | 披风 54093 | alpha [0,255] | 重掷 0 | SHA256 3d7a9ed7bdf38e885fee6e01b6f789a41ac48f14c3642b41fd707c1b1332b59f
- thrown_forward-03-raw.png | ID image-35600-329 | 尺寸 1094x1438 | 宽高比 0.932（蜷身前滚团姿姿势特性，超门接受并登记） | bbox高 894 | 红眼 50149 | 披风 59209 | alpha [0,255] | 重掷 0 | SHA256 fe493df78b6266c2d86cf8a4a9c1f1b4845257d9d505af4a9def59beff48aa5a

## timeout
- timeout-00-raw.png | ID image-35600-331 | 尺寸 1094x1438 | 宽高比 0.457 | bbox高 1395 | 红眼 33554 | 披风 50831 | alpha [0,255] | 重掷 0 | SHA256 20a9c9be0e1b2d69c002b72db154f12658c223c970cab746e9b25ff44ada1213
- timeout-01-raw.png | ID image-35600-332 | 尺寸 1094x1438 | 宽高比 0.759 | bbox高 1292 | 红眼 30951 | 披风 65045 | alpha [0,255] | 重掷 0 | SHA256 99d246856687eda1083bff1464e86a9bfa92141be101aad0fa7ada703742e4c2
- timeout-02-raw.png | ID image-35600-334 | 尺寸 1094x1438 | 宽高比 0.715 | bbox高 1233 | 红眼 56280 | 披风 69147 | alpha [0,255] | 重掷 0 | SHA256 d4045887b79acf2c931c1daf7204710d7d6639b78613394454e9299246eaf5b5
- timeout-03-raw.png | ID image-35600-335 | 尺寸 1094x1438 | 宽高比 0.727 | bbox高 1328 | 红眼 49006 | 披风 65971 | alpha [0,255] | 重掷 0 | SHA256 a262818570b64b7c6d7b3e7a814695e9a82b701ff30732642b1e02ff33fbbb59

## victory
- victory-00-raw.png | ID image-35600-337 | 尺寸 1094x1438 | 宽高比 0.407 | bbox高 1414 | 红眼 47626 | 披风 53403 | alpha [0,255] | 重掷 0 | SHA256 1e8145782781434bcd4db82ae7dd7eb91ffa50b11a4a07ee597a2d75e664ff5a
- victory-01-raw.png | ID image-35600-339 | 尺寸 1094x1438 | 宽高比 0.688 | bbox高 1418 | 红眼 53325 | 披风 69938 | alpha [0,255] | 重掷 0 | SHA256 461fae922f85eedbe72fcaf883db041098c0d237eca7abd21ea91ba0512900cb
- victory-02-raw.png | ID image-35600-341 | 尺寸 1094x1438 | 宽高比 0.687 | bbox高 1419 | 红眼 49558 | 披风 72916 | alpha [0,255] | 重掷 0 | SHA256 4f9619b9ad45a5c085df6cf7c573e5065c94a2635c31cc2f031577b970db8b59
- victory-03-raw.png | ID image-35600-342 | 尺寸 1094x1438 | 宽高比 0.450 | bbox高 1421 | 红眼 15246 | 披风 58251 | alpha [0,255] | 重掷 0 | SHA256 3d516eb8e6ca47fd43a22cc1e221adce5105e7814aa654babfbd3db1f2d5a41a
- victory-04-raw.png | ID image-35600-344 | 尺寸 1094x1438 | 宽高比 0.512 | bbox高 1411 | 红眼 61776 | 披风 74200 | alpha [0,255] | 重掷 0 | SHA256 735bffabf17a77f80a39ffb6a9505fa8e1d5529a2959e80894eb19515e899048
- victory-05-raw.png | ID image-35600-345 | 尺寸 1094x1438 | 宽高比 0.431 | bbox高 1416 | 红眼 38370 | 披风 62642 | alpha [0,255] | 重掷 0 | SHA256 a8859cbd25bd2ef97d1269a92e5d88059256c8be709a669f2d22e38da8acd1e7
- victory-06-raw.png | ID image-35600-347 | 尺寸 1094x1438 | 宽高比 0.689 | bbox高 1415 | 红眼 50342 | 披风 73390 | alpha [0,255] | 重掷 0 | SHA256 e3018f4850fe40574c877acb11a7269c48947104be2b9405147d0407fdb48387
- victory-07-raw.png | ID image-35600-348 | 尺寸 1094x1438 | 宽高比 0.693 | bbox高 1412 | 红眼 61095 | 披风 77413 | alpha [0,255] | 重掷 0 | SHA256 cce5ec24579e1fcdffc4f69fb65453fe4039b246b1887931f1dc58a2c93e8751

## getup
- getup-00-raw.png | ID image-35600-352 | 尺寸 1094x1438 | 宽高比 1.210（仰卧撑起半坐姿势特性，超门接受并登记） | bbox高 890 | 红眼 26140 | 披风 30350 | alpha [0,255] | 重掷 0 | SHA256 1c0527bf35e8eb07584151eb951ddfcedc9866cb9a44c66e276794117bba9b89

- getup-01-raw.png | ID image-35600-353 | 尺寸 1094x1438 | 宽高比 0.756 | bbox高 1266（单膝跪地姿势，低于站立属跪姿特性，登记） | 红眼 43028 | 披风 54735 | alpha [0,255] | 重掷 0 | SHA256 8525c4179157582b1fc14edbf2d09bb1b12c533e39488fd01411050d8485d866

## ko
- ko-00-raw.png | ID image-35600-354 | 尺寸 1094x1438 | 宽高比 0.866（KO 仰面击飞摊开姿势特性，超门接受并登记） | bbox高 1212 | 红眼 60106 | 披风 80917 | alpha [0,255] | 重掷 0 | SHA256 acfdd18c7300ba3f4f0fabdc34926174300de6580360c0c28a115fd42f481a78

- ko-01-raw.png | ID image-35600-355 | 尺寸 1094x1438 | 宽高比 2.814（KO 仰躺平摊姿势特性，超门接受并登记） | bbox高 377 | 红眼 14129 | 披风 22117 | alpha [0,255] | 重掷 0 | SHA256 cefc140abec07beccdcda1f58993e6d88b22b121f9884f837372863cb1549b0f

## win
- win-00-raw.png | ID image-35600-357 | 尺寸 1094x1438 | 宽高比 0.375 | bbox高 1403 | 红眼 40107 | 披风 57887 | alpha [0,255] | 重掷 0 | SHA256 792e2215134e4169ca5b125fdf575cd1ad2ebc879a4d7eabdc45aeaeb101cd51
- win-01-raw.png | ID image-35600-358 | 尺寸 1094x1438 | 宽高比 0.376 | bbox高 1410 | 红眼 40665 | 披风 53373 | alpha [0,255] | 重掷 0 | SHA256 9d0e84fd466017ecfe1b6ea86b0f9d25b858d9ae2a7b840d485a0f32992faae8
合计 107 帧
