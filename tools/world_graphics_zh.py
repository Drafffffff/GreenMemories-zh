"""Translate only the two identical CAMP 8bpp world-sign tile pairs."""
from pathlib import Path
import hashlib,json
from PIL import Image
P=Path(__file__).resolve().parents[1];D=P/'analysis/world_graphics'
OFFSETS=(0x151898,0x39a3b8)

def glyphs():
 path=P/'assets/tutorial_graphics/fonts/fusion-pixel-8px-monospaced-zh_hans.bdf';out={}
 for block in path.read_text().split('STARTCHAR ')[1:]:
  lines=block.splitlines();cp=int(next(x for x in lines if x.startswith('ENCODING ')).split()[1])
  if chr(cp) not in '营地':continue
  w,h,xo,yo=map(int,next(x for x in lines if x.startswith('BBX ')).split()[1:]);p=[[0]*8 for _ in range(8)];pos=lines.index('BITMAP')+1
  for y,row in enumerate(lines[pos:pos+h]):
   for x in range(w):
    xx=x+xo;yy=y+7-h-yo
    if int(row,16)&(1<<(len(row)*4-x-1)) and 0<=xx<8 and 0<=yy<8:p[yy][xx]=1
  out[chr(cp)]=p
 assert len(out)==2
 return out

def apply_graphics(rom:bytearray)->dict:
 original=(P/'original/Green-Memories-v1.5.0.gba').read_bytes()
 assert hashlib.sha256(original).hexdigest()=='a5bf6ba5d6f78912e35986ba21cf034c65677cc66c3f97022606069dbaafb202'
 old=original[OFFSETS[0]:OFFSETS[0]+128]
 assert original.find(old)==OFFSETS[0] and original.find(old,OFFSETS[0]+1)==OFFSETS[1] and original.find(old,OFFSETS[1]+1)<0
 assert all(bytes(rom[o:o+128])==old for o in OFFSETS),'CAMP asset was modified'
 f=glyphs();new=bytes(0x06 if f[c][y][x] else 0x17 for c in '营地' for y in range(8) for x in range(8))
 for o in OFFSETS:rom[o:o+128]=new
 D.mkdir(exist_ok=True,parents=True)
 for name,b in [('original',old),('zh',new)]:
  im=Image.new('RGB',(16,8))
  colors={0x06:(104,8,88),0x17:(255,160,144),0x0f:(200,64,112),0x0d:(200,64,112)}
  for y in range(8):
   for x in range(16):im.putpixel((x,y),colors.get(b[x//8*64+y*8+x%8],(200,64,112)))
  im.resize((384,192),Image.Resampling.NEAREST).save(D/f'camp_{name}.png')
 report={'label':'CAMP → 营地','offsets':[hex(o) for o in OFFSETS],'format':'two horizontal 8bpp 8×8 tiles per copy','font':'Fusion Pixel zh_Hans 8px, SIL OFL1.1','changed_tiles':4,'palette_unchanged':True,'layout_unchanged':True,'source_asset_sha256':hashlib.sha256(old).hexdigest()}
 (D/'patch_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 return report
if __name__=='__main__':
 r=bytearray((P/'output/green_memories_zh.gba').read_bytes());print(json.dumps(apply_graphics(r),ensure_ascii=False,indent=2));(D/'camp_probe.gba').write_bytes(r)
