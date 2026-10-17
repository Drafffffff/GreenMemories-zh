from pathlib import Path
import ctypes as C
P=Path(__file__).resolve().parents[2];D=P/'analysis/world_graphics';c=C.CDLL(str(P/'build/runtime_bridge.dylib'));c.anguna_open.argtypes=[C.c_char_p];c.anguna_read.restype=C.c_uint;c.anguna_open(str(P/'output/green_memories_zh.gba').encode())
def run(n,k=0):c.anguna_frame(k,n)
def press(k,n=180):run(15,k);run(n)
run(1200);press(1);press(8);press(1)
for i in range(65):press(1,90)
for i in range(8):press(16,60)
press(2);press(2)
for name,base,size in [('vram',0x6000000,0x18000),('palette',0x5000000,1024),('oam',0x7000000,1024),('regs',0x4000000,0x60)]:
 (D/(name+'.bin')).write_bytes(bytes(c.anguna_read(base+i,1) for i in range(size)))
