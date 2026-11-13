# Ultraman Justice (杰斯提斯奥特曼 · 标准型) — Stage 1 Rework Diagnosis

- **Date:** 2026-11-12
- **Scope:** Existing workspace state only. No assets generated, installed, or mutated except audit artifacts written to `art/fighters/ultraman-justice/stage1/rework-20261112/` (`clip_audit.json`, `diagnosis.md`). One accidental overwrite of `art/fighters/ultraman-justice/stage1/cells/idle-candidate-04-cell.png` during evidence extraction was immediately restored to its prior working-tree bytes/SHA (`f9de9f2d…`, 5924 B, 256×256).
- **Authority / limits:** Local workspace audit only. No runtime recording, no in-game screenshot, no Godot/verify run, no user visual approval, no hearing. This is **asset/manifest/cells/reference evidence diagnosis**, not in-engine acceptance.
- **Inputs consulted:** `AGENTS.md`, `REBUILD_2D_PLAN.md`, `docs/PROGRESS.md`, `docs/STAGE1_STANDARD.md`, `art/STYLE.md`, `tools/rebuild/shared/SEVEN_CHARACTER_REWORK_BRIEF.md`, `tools/rebuild/ultraman-justice/README.md`, installed `assets/fighters/ultraman-justice/animations/{manifest.json,*/atlas.png}`, `art/fighters/ultraman-justice/stage1/cells/cells.json`, `art/fighters/ultraman-justice/stage1/cells/*`, `art/fighters/ultraman-justice/stage1/idle/{frames,references}/*`, `art/fighters/ultraman-justice/sources/**`, `art/fighters/ultraman-justice/model/identity-anchor-x4.png`, existing rework artifacts (`identity_card.json`, `frozen_palette.json`, `identity_ready.json`, `source_audit.md`, `clip_audit.json`).

## 1. Executive summary

- **Installed clips audited:** 108 (all present in manifest; all atlas files exist, manifest `atlas_sha256` matches actual SHA, all rects in-bounds, all atlases binary-alpha RGBA).
- **Critical identity/pipeline blockers remain:** signed action identity anchor recorded as `art/fighters/ultraman-justice/stage1/cells/idle-candidate-04-cell.png` SHA `e1dbeeabb86a8256de833b92b5f24b30fffc45a8b91b121ff06d5594156df00d` (192×192, 4707 B, 32 visible colors, teal markers present) is **not present as that byte-exact file in the art working tree**; current art copy is `f9de9f2d193bc0dd57a5eee3bb9402647ca444e98b6fd47368040897a6ba628b` (5924 B, 256×256, 20 colors, no teal). Signed 192 bytes are recoverable from `.git/lfs/objects/e1/db/e1dbeeabb86a8256de833b92b5f24b30fffc45a8b91b121ff06d5594156df00d` and match `idle-candidate-04-x4.png` downscaled by nearest to 192 (SHA-equal reconstruction).
- **Installed animation identity drift:** 104/108 clips contain **zero** teal-hue identity pixels (Justice's canonical cyan/teal chest/head accents per signed anchor and 4×: RGB `(2,177,172),(14,204,199),(15,143,127)`); only 4 clips have sparse teal (`chase_takeoff` 13 px, `victory` 14 px, `defeat` 19 px, `vertical_jump` 35 px) vs 128 px in signed 192 anchor / 2048 px in faithful 4×.
- **Grid/policy inconsistency:** 4 clips still use legacy 192-cell / anchor `[96,184]` (`air_throw`, `back_dash`, `throw_tech`, `victory`); 103 clips use 256-cell / `[128,248]`; `air_special` uses 288-cell / `[128,248]`. Manifest global `cell=[288,288], anchor=[128,248]` but per-clip fields differ (mixed policy surface).
- **Bookkeeping/source-of-truth drift:** `art/fighters/ultraman-justice/stage1/cells/cells.json` sets `approved_sha256` to `assets/fighters/ultraman-justice/catalogue/model-native.png` (`924c2aab…`, 96×96) — catalogue identity, not the recorded action identity anchor (`e1dbee…`). `cells.json` has 58 frame entries covering a subset of clip stems; installed manifest has 108 clips, so traceability from installed clip atlases back to per-frame cell/source records is incomplete.
- **Readiness:** existing `rework-20261112/identity_ready.json` and `frozen_palette.json` correctly report `ready=false` / `blocked_not_ready`. No clip is diagnosable as visually approved from workspace assets alone; all require rework planning against a restored frozen identity anchor/palette and then new production passes (outside this diagnosis task).

## 2. Identity anchor and palette evidence

| Artifact | Path | SHA256 | Bytes | Size | Mode | Visible colors | Alpha | Teal identity px (hue heuristic) | Notes |
|---|---|---|---|---:|---:|---|---:|---|---:|---|
| Signed 192 anchor (recorded, LFS object) | `.git/lfs/objects/e1/db/e1dbeeabb86a8256de833b92b5f24b30fffc45a8b91b121ff06d5594156df00d` | `e1dbeeabb86a8256de833b92b5f24b30fffc45a8b91b121ff06d5594156df00d` | 4707 | 192×192 | RGBA | 32 | binary 0/255 | 128 (exact canonical `(2,177,172),(14,204,199),(15,143,127)`) | Action identity anchor recorded in `requests.json` `identity_anchor_for_actions` and `tools/rebuild/ultraman-justice/README.md`; bbox `[71,87,179,247]`. |
| Faithful 4× preview | `art/fighters/ultraman-justice/stage1/cells/idle-candidate-04-x4.png` | `d13bcf04d4b3211d73bd63147facd76b44652fb172c68f19b9968e4fad352d2d` | 10626 | 768×768 | RGBA | 32 | binary | 2048 | Nearest-downscale to 192 reproduces signed SHA/bytes exactly. |
| Art working-tree idle cell (current, drift) | `art/fighters/ultraman-justice/stage1/cells/idle-candidate-04-cell.png` | `f9de9f2d193bc0dd57a5eee3bb9402647ca444e98b6fd47368040897a6ba628b` | 5924 | 256×256 | RGBA | 20 | binary | 0 | **Not** the signed 192 anchor; larger canvas, palette collapsed, teal lost. Identity drift / stale copy. |
| Installed idle atlas (runtime asset) | `assets/fighters/ultraman-justice/animations/idle/atlas.png` | `d2ab7f803efb15b8ef92fc2ab92a2ca10ab9d369791054db9be99850b7c1c34b` | 6390 | 256×256 | RGBA | 20 | binary | 0 | Alpha IoU vs signed 192 ≈ 0.9998 but RGB differs broadly (same-RGB on shared visible pixels 1318/5763); teal accents absent. |
| Model identity anchor 4× | `art/fighters/ultraman-justice/model/identity-anchor-x4.png` | `4c8a1d841dc585e0a07e2b52a1eaf364f753616eb4d2dbbf59915d1052d3342a` | 8459 | 384×384 | RGBA | 23 | binary | 448 | Separate model/cast anchor; teal present. |
| Catalogue model-native (cells approved_sha256 target) | `assets/fighters/ultraman-justice/catalogue/model-native.png` | `924c2aab9395217364600579ffdd23f44fc262f2865f3ec44ef2ebe539991989` | 1654 | 96×96 | RGBA | 23 | binary | 112 | Catalogue identity; **not** action motion anchor despite being referenced by `cells.json.approved_sha256`. |
| Contact sheet | `art/fighters/ultraman-justice/stage1/cells/idle-candidate-04-contact.png` | `15b2217e1c89584d04ea7f6427583090d3970fe138cfe53bf9b573a725f0d90a` | 139174 | 1421×822 | RGBA | 22240 | alpha all 255 | n/a | Review composite, not pixel production source. |

**Key findings:** canonical teal identity markers exist in signed/faithful references but are absent from current art idle cell and from 104/108 installed clip atlases. `frozen_palette.json` and `identity_ready.json` already mark `ready=false` / `blocked_not_ready`; diagnosis confirms palette/anchor readiness cannot be claimed from installed state.

## 3. Source and provenance evidence (available)

- `art/fighters/ultraman-justice/sources/ref-01.webp` (324×899, SHA `1e59c68d…`, from `ref-01.json` / Ultra Fandom) — general form reference; not strict side-view anchor.
- `art/fighters/ultraman-justice/sources/tsuburaya-justice-2019/official-standard-01..04.png` (`source.json` SHA-verified) — official standard-mode suit photos/watermarked media reprints per source records; `official-standard-03` head crop used for side-verify head/neck reference (`justice-side-head-official-03.png`, 340×370, SHA `45d99aec…`).
- `art/fighters/ultraman-justice/sources/side-verify-2026-11-12/justice-standard-ugf-tac-group-right-profile-01.jpg` and `source.json` — independent side/profile verification material (head/neck crop `justice-side-head-ugf-head-neck.png`, 152×616, SHA `f53797ff…`). No direct official 90° full-body side photo confirmed in available records; `source_audit.md` documents search limits.
- `art/fighters/ultraman-justice/stage1/idle/references/*` — pose/reference canvases and side-head crops used for the recorded idle anchor workflow (`ref-01-wide-canvas.png` 2240×1408, `stance-04-wide-canvas.png` 1344×768, plus head crops above).
- `tools/rebuild/ultraman-justice/README.md` and `stage1/requests.json` record the candidate-04 approval/signing trail: signed native 192 anchor SHA `e1dbee…`, strict 4× `d13bcf…`, contact `15b2217…`; later records also show rescale/cleanup and drift risk. These are historical/process evidence, not runtime visual approval.

## 4. Manifest, cells, and policy consistency

- **Manifest:** `assets/fighters/ultraman-justice/animations/manifest.json` — 108 clips, `reviewed=false`, `identity_revision="root_delegated_by_user_2026-11-10"`, global `cell=[288,288]`, `anchor=[128,248]`. Per-clip fields: 103 clips `cell=256, anchor=[128,248]`; 4 clips `cell=192, anchor=[96,184]`; 1 clip `cell=288, anchor=[128,248]` (`air_special`). Atlas texture paths all under `res://assets/fighters/ultraman-justice/animations/<clip>/atlas.png`; actual files exist and SHA-match manifest entries.
- **Grid groups (from clip audit):**
  - `cell=192 anchor=[96, 184] rect=[[192, 192]]` — **4** clips: `chase_takeoff, defeat, vertical_jump, victory`
  - `cell=256 anchor=[128, 248] rect=[[256, 256]]` — **103** clips: `air_apex, air_crush, air_fall, air_pulse, air_rise, air_tech, air_throw, back_counter, backstep, block, blockstun, bounce, bounce_crush, bounce_sweep, burst, charge, charge_start, charge_stop, chase_end, chase_light1, chase_light2, crouch, crouch_blockstun, crouch_guard, crouch_light, crouch_light2, crouch_rise, crouch_start, crouch_sweep, crouch_turn, crush, dash, dash_heavy, dash_light, dash_start, dash_stop, dash_throw, diagonal_heavy, diagonal_light, dive, dodge, dodge_counter, down, flip_back, flip_forward, getup, grabbed, guard, guard_counter, guardbreak, heavy, hit, hit_air, hit_crouch, hit_high, hit_mid, idle, intro, ko, land, launch_fall, launch_rise, launcher, light1, light2, light3, low_pulse, motion_214, motion_22, motion_236, motion_41236, motion_623, pulse, ranged_forward, roll_back, roll_forward, slide, special, special2, special3, spin_heavy, stun, sweep, tackle, takeoff, taunt, throw_back, throw_forward, throw_tech, thrown_air, thrown_back, thrown_dash, thrown_forward, timeout, turn, vertical_heavy, vertical_light, wake, wake_low, wake_mid, walk_back, walk_forward, win`
  - `cell=288 anchor=[128, 248] rect=[[288, 288]]` — **1** clips: `air_special`
- **cells.json:** `art/fighters/ultraman-justice/stage1/cells/cells.json` — `approved_sha256=924c2aab…` (`catalogue/model-native.png`, mismatch vs action anchor), `scale=0.161972273`, `target_standing=161`, `target_head=21`, global `cell=256`, `anchor=[128,248]`, 58 frame entries (subset). Frame scale is uniform at ~0.161972 in sampled entries; standing/height metrics recorded per processed cell but not a substitute for visual/runtime review.
- **Definition mismatch:** `art/fighters/ultraman-justice/stage1/definition.json` not found; `identity_card.json` previously flagged presentation `288/184` vs installed `256/161` from historical definition context — cannot re-verify definition file contents now, but absence/inconsistency remains a traceability issue.
- **Atlas integrity:** 108/108 unique atlas hashes (one per clip), sizes vary by sheet packing (256×256 up to 4096×256 and `air_special` 2304×288); 0 missing, 0 SHA mismatch, 0 OOB rects, 0 non-binary alpha. Packing/transport integrity is good; visual/identity integrity is not established.

## 5. Defect classification (evidence-based)

### D1 — Signed action identity anchor missing/drifted in art working tree (blocking)
- **Evidence:** recorded signed anchor SHA `e1dbee…` (192×192, 4707 B, 32 colors, teal 128 px) exists in LFS object and is reconstructable from `idle-candidate-04-x4.png`; current art cell file is `f9de9f2d…` (256×256, 5924 B, 20 colors, teal 0). `identity_ready.json.required_next_step` and `frozen_palette.json.status` already require restoring/rebuilding from signed/new whole idle with complete ≤32 palette.
- **Impact:** no trustworthy in-tree pixel identity anchor for action-frame parity checks; downstream palette/identity decisions are blocked.
- **Affected:** `art/fighters/ultraman-justice/stage1/cells/idle-candidate-04-cell.png` (art source record), any process relying on it as motion identity anchor.

### D2 — Canonical teal identity accents absent from nearly all installed clips (high)
- **Evidence:** `clip_audit.json` — 104/108 clips `teal_hue_px==0`; only `chase_takeoff`(13), `victory`(14), `defeat`(19), `vertical_jump`(35) have sparse teal. Signed anchor has 128 teal px / 32-color palette including canonical teal triplet; faithful 4× has 2048 px.
- **Impact:** high risk of character identity loss/inconsistency in-engine (Justice’s distinguishing cyan markers likely missing or inconsistent). Also indicates palette was not frozen/applied from canonical identity source across clip set.
- **Affected (no teal, 104):** `air_apex`, `air_crush`, `air_fall`, `air_pulse`, `air_rise`, `air_special`, `air_tech`, `air_throw`, `back_counter`, `backstep`, `block`, `blockstun`, `bounce`, `bounce_crush`, `bounce_sweep`, `burst`, `charge`, `charge_start`, `charge_stop`, `chase_end`, `chase_light1`, `chase_light2`, `crouch`, `crouch_blockstun`, `crouch_guard`, `crouch_light`, `crouch_light2`, `crouch_rise`, `crouch_start`, `crouch_sweep`, `crouch_turn`, `crush`, `dash`, `dash_heavy`, `dash_light`, `dash_start`, `dash_stop`, `dash_throw`, `diagonal_heavy`, `diagonal_light`, `dive`, `dodge`, `dodge_counter`, `down`, `flip_back`, `flip_forward`, `getup`, `grabbed`, `guard`, `guard_counter`, `guardbreak`, `heavy`, `hit`, `hit_air`, `hit_crouch`, `hit_high`, `hit_mid`, `idle`, `intro`, `ko`, `land`, `launch_fall`, `launch_rise`, `launcher`, `light1`, `light2`, `light3`, `low_pulse`, `motion_214`, `motion_22`, `motion_236`, `motion_41236`, `motion_623`, `pulse`, `ranged_forward`, `roll_back`, `roll_forward`, `slide`, `special`, `special2`, `special3`, `spin_heavy`, `stun`, `sweep`, `tackle`, `takeoff`, `taunt`, `throw_back`, `throw_forward`, `throw_tech`, `thrown_air`, `thrown_back`, `thrown_dash`, `thrown_forward`, `timeout`, `turn`, `vertical_heavy`, `vertical_light`, `wake`, `wake_low`, `wake_mid`, `walk_back`, `walk_forward`, `win`
- **Affected (sparse teal, likely inconsistent, 4):** `chase_takeoff`(13 px), `defeat`(19 px), `vertical_jump`(35 px), `victory`(14 px)

### D3 — Legacy grid/anchor policy on 4 clips (medium-high, integration/consistency)
- **Evidence:** manifest per-clip `cell=192, anchor=[96,184]` for `air_throw`, `back_dash`, `throw_tech`, `victory`; all others 256 or 288 with anchor `[128,248]`. Manifest global is `[288,288]/[128,248]`. `identity_card.json`/`frozen_palette.json` note 4 legacy 192-grid clips and root/anchor mismatch.
- **Impact:** inconsistent baseline/cell contract, harder shared QA, risk of alignment/scale mismatch if reworked clips assume 256 standard; may reflect old pipeline generation.
- **Affected:** `air_throw` (6 rects, 960×192), `back_dash` (4 rects, 768×256 sheet but 192-cell rects), `throw_tech` (14 rects, 3584×256 sheet, 192 rects), `victory` (2 rects, 384×192).

### D4 — Source-of-truth / traceability drift (medium, blocking clean rework planning)
- **Evidence:** `cells.json.approved_sha256` = `924c2aab…` catalogue model-native, not action anchor `e1dbee…`; `cells.json` contains 58 frame records but manifest has 108 installed clips (many installed clips have no corresponding `cells.json` frame entry). `stage1/definition.json` absent; historical definition/presentation mismatch noted in existing identity card cannot be fully revalidated from file.
- **Impact:** cannot reliably map installed clip frames back to source generation/cell decisions; increases risk of accidental overwrite or wrong baseline during rework.
- **Affected:** global bookkeeping (`cells.json`, manifest/global policy metadata, missing definition artifact), and all installed clips lacking per-frame provenance in `cells.json`.

### D5 — Runtime/visual defects unknown (unverified)
- **Evidence:** no in-engine run, no clip playback capture, no hit/hurt/animation timing review performed in this workspace-only diagnosis.
- **Impact:** motion readability, silhouette, limb continuity, timing, VFX/gameplay presentation issues may exist but are **not evidenced here**; absence from this report is not a pass.
- **Affected:** potentially all clips; must be covered in a later runtime/visual diagnosis pass per rework brief step 1/3.

## 6. Recommended fix approach (per affected group/clip)

> All recommendations below are planning guidance for subsequent rework phases. This diagnosis made no asset changes.

### R0. Restore/freeze identity baseline before any redraw (prerequisite for all)
- Restore byte-exact signed 192 action anchor (`e1dbee…`) into the canonical art cell path and/or explicitly record it as immutable source of truth; keep `idle-candidate-04-x4.png` (`d13bcf…`) as strict 4× preview.
- Freeze a complete ≤32 palette derived from the signed/whole-idle identity source **including canonical teal markers** `(2,177,172),(14,204,199),(15,143,127)`; update `frozen_palette.json`/`identity_ready.json` only when machine checks pass (SHA/bytes/size/binary alpha/teal presence/4× consistency).
- Reconcile bookkeeping: set `cells.json` approved/action-anchor references to the actual action identity anchor (or separate fields clearly), document catalogue vs action anchor, and reintroduce/align `definition.json` or equivalent presentation contract for Justice.

### R1. Clips with no teal identity pixels (104 clips) — identity recolor/redraw pass after R0
- **Group:** all installed clips except `chase_takeoff`, `defeat`, `vertical_jump`, `victory` (see D2 list).
- **Approach:** do **not** bulk-apply blind recolor. First classify per-clip from source frames/contact sheets/runtime captures (future pass): `keep/fix/redraw/data-fix`. For clips whose silhouette/timing is acceptable, re-render or carefully remap to frozen ≤32 palette ensuring Justice’s teal markers appear in anatomically/pose-consistent locations; for clips with motion/readability issues, full or partial redraw from restored identity anchor.
- **Acceptance checks per clip:** palette ⊆ frozen set, binary alpha, correct cell/anchor/baseline, teal markers present where pose allows, side-view consistency, and later runtime contact-sheet/playback review.

### R2. Sparse-teal clips (4 clips) — targeted identity audit then fix/redraw
- **Group:** `chase_takeoff` (13 px), `victory` (14 px), `defeat` (19 px), `vertical_jump` (35 px) — teal exists but far below signed-anchor density and may be misplaced/noisy.
- **Approach:** compare each atlas against frozen anchor for marker placement and hue exactness; if markers are incidental/wrong, treat as D2/D1 identity issue and include in redraw/remap pass. `victory` also has legacy grid (D3) — prioritize combined fix.

### R3. Legacy 192-grid / anchor [96,184] clips (4 clips) — normalize to standard pipeline contract
- **Group:** `air_throw`, `back_dash`, `throw_tech`, `victory`.
- **Approach:** decide target standard (project expects consistent 256-cell baseline for most clips, with exceptions only when justified like `air_special` 288). Re-cell/re-export these clips to the agreed `cell/anchor/rect` contract with baseline aligned to current Justice standing/foot policy; update `manifest.json` per-clip fields, atlas packing, and `cells.json` frame records together. Because these are gameplay-relevant motions (throw/tech/back dash/victory), include runtime alignment/timing verification after asset replacement.
- **Note:** `victory` combines D2(partial)/D3 — handle as a full normalization case.

### R4. air_special (288-cell exception) — verify exception is intentional and documented
- **Group:** `air_special` (`cell=288`, anchor `[128,248]`, atlas 2304×288, 8 rects, no teal).
- **Approach:** keep 288 only if wide silhouette genuinely requires it per style/pipeline rules; document exception in manifest/cells/definition consistently. Regardless, fix identity/palette (D2) and validate in-engine footprint/alignment.

### R5. Provenance and coverage gaps (all installed clips, process fix)
- Rebuild per-clip/per-frame provenance mapping in `cells.json` (or equivalent) for every installed clip: source frame(s), output SHA, cell/anchor/scale, standing/head/baseline metrics, and relation to frozen anchor/palette revision.
- Ensure every installed clip can be traced from manifest atlas SHA -> cell record -> source/reference/review evidence. Prioritize clips missing from current 58-entry subset.
- Add/update `definition.json` (or confirm canonical runtime definition source) so presentation/cell/anchor/scale expectations are explicit and consistent with installed data.

### R6. Mandatory follow-up diagnosis (not done here)
- Perform runtime/visual audit: per-clip playback, loop/contact points, silhouette readability, baseline/foot slide, facing, VFX layering, and gameplay-facing states (idle/walk/jump/attacks/hurt/throw/victory/defeat etc.) with captures/evidence as required by `SEVEN_CHARACTER_REWORK_BRIEF.md`.
- Produce per-clip keep/fix/redraw/data-fix matrix and only then schedule regeneration/installation. Current diagnosis supports **identity/grid/provenance rework candidacy for all 108 installed clips**, but cannot rank visual motion quality.

## 7. Evidence index (paths / SHAs / key values)

- Manifest: `assets/fighters/ultraman-justice/animations/manifest.json` (108 clips, reviewed false, identity_revision `root_delegated_by_user_2026-11-10`, global cell `[288,288]`, anchor `[128,248]`).
- Clip-level measured audit: `art/fighters/ultraman-justice/stage1/rework-20261112/clip_audit.json` (this run).
- Signed action anchor (LFS): `.git/lfs/objects/e1/db/e1dbeeabb86a8256de833b92b5f24b30fffc45a8b91b121ff06d5594156df00d` — SHA/bytes/size as above.
- 4× anchor: `art/fighters/ultraman-justice/stage1/cells/idle-candidate-04-x4.png` — `d13bcf04…`, 768×768.
- Drifted art idle cell (restored to prior working state after accidental touch): `art/fighters/ultraman-justice/stage1/cells/idle-candidate-04-cell.png` — `f9de9f2d…`, 256×256.
- Installed idle: `assets/fighters/ultraman-justice/animations/idle/atlas.png` — `d2ab7f80…`, 256×256.
- Cells record: `art/fighters/ultraman-justice/stage1/cells/cells.json` — approved_sha256 `924c2aab…` (catalogue), scale `0.161972273`, target_standing 161, 58 frames.
- Existing rework state: `identity_card.json`, `frozen_palette.json` (`blocked_not_ready`), `identity_ready.json` (`ready=false`), `source_audit.md` in same rework dir.
- Key prior records: `tools/rebuild/ultraman-justice/README.md`, `art/fighters/ultraman-justice/stage1/requests.json`.

## 8. Bottom line

Justice is **not ready** for production motion reuse as-is. Installed assets have strong file/packing integrity but weak identity/provenance consistency against the recorded signed anchor: teal identity markers are missing from 104/108 clips, 4 clips remain on legacy 192 grid/anchors, the art-tree action anchor is drifted from the signed SHA, and bookkeeping (`cells.json` approved anchor, incomplete frame coverage, missing definition artifact) is insufficient for safe rework. Next step is to restore/freeze the canonical identity anchor+palette and complete a runtime/visual per-clip diagnosis matrix before any regeneration/install.
