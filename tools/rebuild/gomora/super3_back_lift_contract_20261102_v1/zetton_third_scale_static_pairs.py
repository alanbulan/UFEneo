"""根授权免费整组1/3与修订时序的完整双人静态候选；不修改模拟或产品。"""
from zetton_board_forge_candidate import *
OUT3=ROOT/'reports/review/2026-11-02/gomora-super3-zetton-third-scale-static-pairs-v2'
REG=ROOT/'reports/review/2026-11-02/gomora-super3-back-lift-registration-v1/registered18-v1/registration-candidate.json'
SURFACES={'A':[362,321],'B':[275,327],'C':[390,247],'D':[300,247]}
def rnd(x):return int(math.floor(x+.5))
def main():
 assert not OUT3.exists();OUT3.mkdir();(OUT3/'native').mkdir()
 frozen={p:sha(p)for p in SRC.rglob('*')if p.is_file()}
 for p in OUT.rglob('*'):
  if p.is_file():frozen[p]=sha(p)
 source=SRC/'rejected/candidate.png';assert sha(source)=='ba8b537b0de8c54521a735676487ce60afda65b5efbefc4057ae17b9b0526642'
 palette=ROOT/'content/fighters/zetton/palette.json';frozen[palette]=sha(palette);colors=read(palette)['colors'];board=Image.open(source).convert('RGBA')
 reg=read(REG);frozen[REG]=sha(REG);records={r['phase']:r for r in reg['phases']};frames={};rows=[]
 for name,(x,y)in zip('ABCD',[(0,0),(512,0),(0,512),(512,512)]):
  cell=board.crop((x,y,x+512,y+512));pad=Image.new('RGBA',(513,513));pad.paste(cell,(0,0))
  down=forge.binarize_alpha(pad);down=forge._kcentroid_downscale(down,171,171);forge.binarize_alpha(down)
  with forge.palette_mode('rgb'):forge.apply_palette(down,colors)
  native=Image.new('RGBA',(256,256));native.paste(down,(42,42));p=OUT3/f'native/{name}.png';native.save(p);frames[name]=native
  surface=SURFACES[name];salpha=int(np.asarray(cell)[surface[1],surface[0],3]);assert salpha>=128
  npoint=[v//3+42 for v in surface];nalpha=int(np.asarray(native)[npoint[1],npoint[0],3]);assert nalpha==255,(name,npoint,nalpha)
  rows.append(dict(cell=name,native=rec(p),common_scale=[1,3],source_padding_right_bottom=[1,1],common_native_paste_origin=[42,42],native_bbox=native.getbbox(),
   visible_surface_source=surface,visible_surface_source_alpha=salpha,integer_visible_surface_native=npoint,native_surface_alpha=nalpha,
   point_role='可见腹面轮廓/表面读点，静态作图坐标，不是waist、抓点或模拟根'))
 master=ROOT/'assets/fighters/zetton/model-native.png';frozen[master]=sha(master)
 fullpage([Image.open(master).convert('RGBA')]+list(frames.values()),['ACTUAL MODEL 166px','A / common 1/3','B / common 1/3','C / common 1/3','D / common 1/3'],OUT3/'master-ABCD-whole-native-dark-light.jpg')
 pair_specs=[dict(label='A raw20-23 / Gomora05',cell='A',phase=5,gap=[0,0]),
  dict(label='B raw28-31 / Gomora07',cell='B',phase=7,gap=[0,0]),dict(label='B raw32-35 / Gomora09',cell='B',phase=9,gap=[0,0]),
  dict(label='C raw36-39 / Gomora08',cell='C',phase=8,gap=[-6,-14]),dict(label='D raw40-43 / Gomora10',cell='D',phase=10,gap=[-20,-30])]
 pairs=[]
 for spec in pair_specs:
  r=records[spec['phase']];sp=ROOT/r['source']['path'];npth=ROOT/r['native']['path'];assert sha(sp)==r['source']['sha256']and sha(npth)==r['native']['sha256'];frozen[sp]=sha(sp);frozen[npth]=sha(npth)
  sourceim=Image.open(sp).convert('RGBA');a=np.asarray(sourceim);x=640;ys=np.flatnonzero(a[:,x,3]>=128);yp=int(ys[0])+2
  # x640 was visually read as the upper dorsal plate edge for these sources; not a search over possible grip locations.
  gp=[x,yp];assert a[yp,x,3]>=128
  gn=[rnd(x/4)+r['paste_origin'][0],rnd(yp/4)+r['paste_origin'][1]]
  g=Image.open(npth).convert('RGBA');assert g.getpixel(tuple(gn))[3]==255,(spec,gn)
  worldg=[0,144];back=[gn[0],gn[1]+144];target=[back[i]+spec['gap'][i]for i in range(2)]
  nr=next(z for z in rows if z['cell']==spec['cell']);vs=nr['integer_visible_surface_native'];v_origin=[target[i]-vs[i]for i in range(2)]
  v=frames[spec['cell']];gl=Image.new('RGBA',(512,480));vl=Image.new('RGBA',(512,480));gl.paste(g,tuple(worldg));vl.paste(v,tuple(v_origin))
  assert np.sum(np.asarray(gl)[...,3]>0)==np.sum(np.asarray(g)[...,3]>0)
  assert np.sum(np.asarray(vl)[...,3]>0)==np.sum(np.asarray(v)[...,3]>0)
  overlap=int(np.sum((np.asarray(gl)[...,3]>0)&(np.asarray(vl)[...,3]>0)))
  combo=Image.alpha_composite(vl,gl)
  pair=dict(**spec,gomora_source=rec(sp),gomora_registered_native=rec(npth),gomora_actual_dorsal_surface_source=gp,gomora_actual_surface_alpha=int(a[yp,x,3]),
   gomora_surface_registered_native=gn,gomora_world_cell_origin=worldg,gomora_integer_world_root=[256,448],gomora_world_back_surface=back,
   receiver_visible_surface_source=SURFACES[spec['cell']],receiver_integer_surface_native=vs,receiver_world_cell_origin=v_origin,receiver_world_surface=target,
   receiver_integer_draw_root_candidate_world=target,receiver_root_semantics='整图可见腹面作图参考点，不改角色模拟根/碰撞；C/D为离背后的独立可见点',
   relative_draw_origin_to_gomora_root=[v_origin[0]-256,v_origin[1]-448],separation_from_read_back_px=spec['gap'],
   full_layer_order='receiver then whole Gomora, no limb masks',receiver_covered_pixels=overlap,receiver_covered_fraction=overlap/int(np.sum(np.asarray(v)[...,3]>0)),
   visible_surface_contact_only=spec['cell']in'AB',collision_verified=False,runtime_pairing_passed=False)
  pairs.append((pair,combo))
  # Whole high source with a single surface cross, not a cropped torso.
  bg=Image.new('RGBA',sourceim.size,'#242934');bg.alpha_composite(sourceim);dd=ImageDraw.Draw(bg);dd.ellipse((x-5,yp-5,x+5,yp+5),outline='#63f7c9',width=3);dd.text((x-150,yp+8),f'dorsal surface {gp}',fill='white')
  jpg(bg.convert('RGB').resize((720,720)),OUT3/f'gomora{spec["phase"]:02d}-whole-source-back-surface.jpg')
 def pairpage(items,path):
  page=Image.new('RGB',(768,388*len(items)),'#242934');d=ImageDraw.Draw(page)
  for j,(record,combo)in enumerate(items):
   for k,color in enumerate(['#242934','#dedcd1']):
    x=k*384;y=j*388;d.rectangle((x,y,x+383,y+387),fill=color);d.text((x+4,y+4),record['label']+' / full pair',fill='white'if k==0 else '#242934')
    bg=Image.new('RGBA',(512,480),color);bg.alpha_composite(combo);page.paste(bg.convert('RGB').resize((384,360),Image.Resampling.NEAREST),(x,y+24))
  jpg(page,path)
 pairpage(pairs[:1],OUT3/'pair-A-G05-full-dark-light.jpg');pairpage(pairs[1:3],OUT3/'pair-B-G07-G09-full-dark-light.jpg')
 pairpage(pairs[3:4],OUT3/'pair-C-G08-full-dark-light.jpg');pairpage(pairs[4:],OUT3/'pair-D-G10-full-dark-light.jpg')
 for p,digest in frozen.items():assert sha(p)==digest,str(p)
 save(OUT3/'third-scale-static-pair-plan.json',dict(source=rec(source),palette=rec(palette),phases=rows,pairs=[p[0]for p in pairs],
  actual_backend=forge.backend_info(),common_scale=[1,3],whole_source_padding=[513,513],downsample_size=[171,171],common_paste_origin=[42,42],
  revised_timing_proposal=[dict(raw=[20,23],receiver='A',role='落背'),dict(raw=[24,35],receiver='B',role='保持横伏负重'),dict(raw=[36,39],receiver='C',role='开始离背上抬'),dict(raw=[40,43],receiver='D',role='后翻')],
  original_contract_unchanged=True,old_candidates_preserved=True,integer_translation_only=True,per_phase_scale_fit=False,rotation=False,mirror=False,body_part_masks=False,
  strict_head_size_passed=False,C_far_arm_complete_visibility_proven=False,static_pair_plan_accepted=False,continuous_pair_motion_passed=False,
  collision_changed=False,simulation_root_changed=False,runtime_installed=False,godot_run=False,post_submitted=False,new_budget_reserved=False,
  frozen_inputs=[rec(p)for p in frozen]))
 print(json.dumps(dict(report=str(OUT3),pairs=[x[0]for x in pairs]),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
