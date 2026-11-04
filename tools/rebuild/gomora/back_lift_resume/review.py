"""现有注册候选的完整画布检查页；不改源/注册像素，不代表主游戏验收。"""
from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageDraw,ImageOps
from resume import ROOT,ACTOR_OUT,REPORT,read,sha

def main():
    receipt=read(ACTOR_OUT/'registration.json');out=REPORT/'registered-review';out.mkdir(parents=True,exist_ok=True)
    results=[]
    for page_index in range(3):
        page=Image.new('RGB',(1536,700),'#30343c');draw=ImageDraw.Draw(page)
        for index,row in enumerate(receipt['actor'][page_index*6:page_index*6+6]):
            im=Image.open(ROOT/row['path']).convert('RGBA');assert sha(ROOT/row['path'])==row['sha256']
            a=np.asarray(im)[...,3];assert im.size==(512,320) and set(np.unique(a))<={0,255}
            x=(index%3)*512;y=(index//3)*350
            page.paste(im,(x,y+24),im);draw.line((x,y+24+304,x+511,y+24+304),fill='#ff77aa')
            draw.text((x+8,y+6),f"SOURCE {row['phase']:02d} / 512x320 / scale1:4 / root256,304",fill='white')
            bbox=im.getbbox();results.append({'phase':row['phase'],'sha256':row['sha256'],'bbox':bbox,
                'opaque_pixels':int(np.count_nonzero(a)),'lowest_pixel_below_authored_sole':bbox[3]-1-304,
                'four_edges_transparent':not(a[0].any()or a[-1].any()or a[:,0].any()or a[:,-1].any())})
        page.save(out/f'actor-{page_index}.png')
    if len(receipt['receiver'])==6:
        page=Image.new('RGB',(1152,430),'#30343c');draw=ImageDraw.Draw(page)
        for i,row in enumerate(receipt['receiver']):
            im=Image.open(ROOT/row['path']).convert('RGBA');assert sha(ROOT/row['path'])==row['sha256']
            for facing in [0,1]:
                frame=im if facing==0 else ImageOps.mirror(im)
                page.paste(frame,(192*i,24+facing*210),frame)
                draw.text((192*i+5,facing*210+5),f"RECEIVER {i:02d} {'R' if facing==0 else 'L'}",fill='white')
        page.save(out/'receiver.png')
    data={'actor':results,'source_bytes_unchanged':all(sha(ROOT/r['source']['path'])==r['source']['sha256'] for r in receipt['actor']+receipt['receiver']),
          'visual_review_pending':True,'runtime_installed':False,'note':'整画布静态检查页，不是主游戏720/1080证据；宽足底根与最低爪尖分别报告。'}
    (out/'qa.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(out)
if __name__=='__main__':main()
