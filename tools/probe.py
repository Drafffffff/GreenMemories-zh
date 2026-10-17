from pathlib import Path
import ctypes as C
from PIL import Image
R=Path(__file__).resolve().parents[1]
c=C.CDLL(str(R.parent/'ANGUNA/build/runtime_bridge.dylib'))
c.anguna_open.argtypes=[C.c_char_p];c.anguna_pixels.restype=C.c_void_p;c.anguna_read.argtypes=[C.c_uint,C.c_uint];c.anguna_read.restype=C.c_uint
c.anguna_open(str(R/'original/Green-Memories-v1.5.0.gba').encode())
def shot(n):
 im=Image.frombytes('RGB',(240,160),C.string_at(c.anguna_pixels(),240*160*2),'raw','BGR;16',0);im.resize((720,480),Image.Resampling.NEAREST).save(R/'analysis'/f'{n}.png')
c.anguna_frame(0,1200);shot('direct_title')
for k in [8,1,2,4,8]:
 c.anguna_frame(k,30);c.anguna_frame(0,120);shot('direct_'+str(k))
print(hex(c.anguna_pc()))
