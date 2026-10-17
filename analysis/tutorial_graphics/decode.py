from pathlib import Path
import struct
from PIL import Image
P=Path(__file__).parent
for page in [0,1]:
 v=(P/f'card{page}_vram.bin').read_bytes();pal=struct.unpack('<256H',(P/f'card{page}_pal.bin').read_bytes()[:512])
 for n,cnt in [(2,0x1108),(3,0x1383)]:
  tilebase=((cnt>>2)&3)*0x4000;mp=((cnt>>8)&31)*0x800;entries=struct.unpack_from('<1024H',v,mp);print(page,n,hex(tilebase),hex(mp),'tiles',min(e&1023 for e in entries),max(e&1023 for e in entries),'banks',set(e>>12 for e in entries))
  im=Image.new('RGB',(256,256));ix=Image.new('L',(256,256))
  for y in range(256):
   for x in range(256):
    e=entries[y//8*32+x//8];tx=x%8;ty=y%8
    if e&0x400:tx=7-tx
    if e&0x800:ty=7-ty
    off=tilebase+(e&1023)*32+ty*4+tx//2
    col=((v[off]>>(tx%2*4))&15)+(e>>12)*16;rgb=pal[col];im.putpixel((x,y),tuple(((rgb>>s)&31)*255//31 for s in [0,5,10]));ix.putpixel((x,y),col)
  im.resize((768,768),Image.Resampling.NEAREST).save(P/f'card{page}_bg{n}.png');ix.save(P/f'card{page}_bg{n}_indices.png')
