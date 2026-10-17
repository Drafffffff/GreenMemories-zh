from pathlib import Path
import struct,json
from PIL import Image,ImageDraw
P=Path(__file__).parent;R=P.parents[1];r=(R/'original/Green-Memories-v1.5.0.gba').read_bytes()
def asset(desc):
 a,e,bpp,pa,pe,pc,mp,w,h,n=struct.unpack_from('<10I',r,desc);a-=0x08000000;e-=0x08000000;pa-=0x08000000;pe-=0x08000000;mp-=0x08000000
 if not(0<=a<e<len(r) and bpp==0 and pe-pa==32 and w==32 and h==32 and n==1 and 0<=mp<len(r)-2048 and e-a<=32768):return
 pix=[[0]*256 for _ in range(256)];maps=struct.unpack_from('<1024H',r,mp);palette=struct.unpack_from('<16H',r,pa)
 if max(v&1023 for v in maps)>=(e-a)//32:return
 for y in range(256):
  for x in range(256):
   v=maps[y//8*32+x//8];xx=x%8;yy=y%8
   if v&0x400:xx=7-xx
   if v&0x800:yy=7-yy
   at=a+(v&1023)*32+yy*4+xx//2;pix[y][x]=(r[at]>>(xx%2*4))&15
 im=Image.new('RGB',(256,256));im.putdata([tuple(((palette[v]>>s)&31)*255//31 for s in [0,5,10]) for row in pix for v in row])
 return dict(desc=desc,tiles=a,tile_end=e,map=mp,palette=pa,count=(e-a)//32),pix,im
entries=[]
for desc in range(0x826000,0x828000,4):
 v=asset(desc)
 if v:
  item,pix,im=v;entries.append(item);im.save(P/f"asset_{desc:x}.png")
(P/'inventory.json').write_text(json.dumps(entries,indent=2));out=Image.new('RGB',(256*6,256*((len(entries)+5)//6)))
for i,v in enumerate(entries):out.paste(Image.open(P/f"asset_{v['desc']:x}.png"),(i%6*256,i//6*256));ImageDraw.Draw(out).text((i%6*256,i//6*256),hex(v['desc']),fill='red')
out.save(P/'assets_contact.png');print('count',len(entries))
print('palette',[(i,hex(v)) for i,v in enumerate(struct.unpack_from('<16H',r,0x276f38))])
