extends SceneTree
var failures: Array[String] = []

func check(ok: bool, message: String) -> void:
	if not ok: failures.append(message)

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var catalog := UfeCatalogueDisplayCatalog.new()
	catalog.aliases["unit_identity_first"] = "unit_identity_second"
	catalog.aliases["unit_identity_second"] = "ultraman"
	catalog.supplemental.append({"id": "unit_identity_first", "name": "测试旧别名", "kind": "hero", "series_ids": []})
	check(catalog.canonical_id("unit_identity_first") == "ultraman", "别名链必须归同一本体")
	var seen: Dictionary = {}
	var first := catalog.query_page("", "", 0)
	for page in range(int(first.pages)):
		for row in catalog.query_page("", "", page).rows:
			check(not seen.has(row.id), "同canonical身份不得跨页重复：" + str(row.id))
			check(catalog.canonical_id(str(row.id)) == str(row.id), "分页不能返回旧别名")
			check(not str(row.name).contains("超人") and not str(row.name).contains("力霸王"), "显示名必须使用大陆译名：" + str(row.id))
			seen[row.id] = true
	var alias_search := catalog.query_page("测试旧别名", "", 0)
	check(int(alias_search.total) == 1 and str(alias_search.rows[0].id) == "ultraman", "旧别名搜索必须回到唯一正式人物")
	check(catalog.page_for_id("unit_identity_first", "测试旧别名", "") == 0, "旧ID定位必须指向归并后页码")
	for id in ["ultraman", "ultraseven", "zetton", "gomora", "neronga", "red_king"]:
		check(catalog.title_for(id) == UfeDisplayText.text(UfeFighterDisplay.title(id)), "图鉴黄字应与实际角色称号相同：" + id)
	for id in ["wiki_25575d819f946e", "wiki_56e37a4d24c493", "wiki_97032ef9e70e78"]:
		var row := catalog.row_for(id)
		check(not str(row.get("name", "")).contains("超人"), "旧地区译名不应进入图鉴标题")
	check(UfeDisplayText.text("超人之母") == "奥特之母", "奥特之母译名")
	check(catalog.title_for("wiki_1276c9e0e93e2a") == "杀手超兽", "已有来源完整别名应拆为黄色称号和姓名")
	check(UfeDisplayText.text("超人力霸王迪卡") == "迪迦奥特曼", "迪迦大陆译名")
	var url := "https://example.org/超人力霸王/奧特曼"
	check(UfeDisplayText.text("超人之父 " + url) == "奥特之父 " + url, "显示汉化不得改来源URL")
	var header := FighterName.new(16, true)
	header.set_name_and_title("超人之母", "奥特战士")
	check(header.name_label.text == "奥特之母" and header.title_label.theme_type_variation == "FighterTitle", "图鉴姓名和黄字复用正式组件")
	header.free()
	print("CATALOGUE_IDENTITY_DISPLAY " + JSON.stringify({"failures": failures, "unique_rows": seen.size()}))
	quit(0 if failures.is_empty() else 1)
