from pathlib import Path
import ctypes as C,json
from PIL import Image
R=Path(__file__).resolve().parents[2];D=Path(__file__).parent
c=C.CDLL(str(R/'build/runtime_bridge.dylib'));c.anguna_open.argtypes=[C.c_char_p];c.anguna_pixels.restype=C.c_void_p;c.anguna_read.argtypes=[C.c_uint,C.c_uint];c.anguna_read.restype=C.c_uint
c.anguna_open(str(R/'original/Green-Memories-v1.5.0.gba').encode())
def read(a,n=4):return c.anguna_read(a,n)
def run(n,k=0):c.anguna_frame(k,n)
def shot(n):
 im=Image.frombytes('RGB',(240,160),C.string_at(c.anguna_pixels(),240*160*2),'raw','BGR;16',0);im.save(D/(n+'.png'));im.resize((720,480),Image.Resampling.NEAREST).save(D/(n+'_3x.png'))
def dump(n):
 for addr,size,name in [(0x06000000,0x18000,'vram'),(0x05000000,0x400,'pal'),(0x04000000,0x60,'regs')]:
  b=b''.join(read(addr+i).to_bytes(4,'little') for i in range(0,size,4));(D/f'{n}_{name}.bin').write_bytes(b)
def press(k,n=180):run(15,k);run(n)
run(1200);press(1);press(8);press(1)
for i in range(55):press(1,90)
for i in range(8):press(16,120)
press(2);press(2);press(8);press(256);shot('original_item_consumable');press(64,60);shot('original_item_up');print('pc',hex(c.anguna_pc()));c.anguna_close()
