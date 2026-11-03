# 2026-11-03清理验证回执

本目录保留可以随干净仓库交接的结果摘要；原始测试输出在本机忽略的reports/verification，重新运行会生成自己的输出，不上传整套日志和截图副本。

- [repository-cleanup.json](repository-cleanup.json)：清理范围、初始盘点、去重和最终全量源SHA审计。清理前记录的4710个运行二进制内容均可在原位置或119个合并目标中找到相同SHA；没有重新编码或替换画帧/音频。
- [cleanup-regression.json](cleanup-regression.json)：空缓存导入、当前全部默认回归及定点补跑结果。结果按初次执行与定点补跑合并；每项列出实际运行批次，旧断言修正及退役基线单独说明。
- [runtime-catalog.json](runtime-catalog.json)：清理时实际definition与三槽招式快照。列为可玩不代表全动作美术、声音和独立技能规范全部达标；后续改数据时须同步重导。

验证使用Godot 4.7.2.stable.steam.ed1daf0bf、Python 3.12.10、Pillow 12.3.0、NumPy 2.5.2。主游戏无缓存导入与启动通过；图形菜单用注入键盘事件触发退出，外层进程返回0，重复退出检查也通过。

没有进行新一轮全部人物双向720/1080逐动作审片、人耳听审或硬件键盘逐键测试，没有生成录屏。上述结果只说明清理后的资源、逻辑、回放及启动/退出验证结果，不表示游戏范围完成。接手步骤和已知余项见[HANDOFF](../HANDOFF.md)。
