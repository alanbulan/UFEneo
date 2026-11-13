import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sf_path = ROOT / "content/fighters/ultraman-zero__luna_miracle/state_frames.json"
sf = json.loads(sf_path.read_text(encoding="utf-8"))

if "form_switch" not in sf:
    idle0 = sf.get("idle", [{}])[0]
    hb = idle0.get("hurtboxes", [[-70, 0, 123, 59], [-47, 57, 72, 59], [-42, 114, 70, 60]])
    sf["form_switch"] = []
    for i in range(6):
        sf["form_switch"].append({
            "sprite": i,
            "dx": 0,
            "dy": 0,
            "hitboxes": [],
            "hurtboxes": hb,
            "cancel": [],
            "events": [],
            "impact_effect": "impact_light",
            "block_effect": "impact_guard",
        })
    print("added form_switch")
else:
    print("form_switch_exists")

sf_path.write_text(json.dumps(sf, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
