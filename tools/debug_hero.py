from pathlib import Path
import ctypes as C,sys
R=Path(__file__).resolve().parents[1];D=R/'analysis/debug_hero';c=C.CDLL(str(D/'bridge.dylib'));c.anguna_open.argtypes=[C.c_char_p];c.anguna_read.restype=C.c_uint;c.trace_stack.argtypes=[C.c_uint,C.c_uint,C.c_char_p]
rom=D/('fail.gba' if len(sys.argv)<2 else sys.argv[1]);c.anguna_open(str(rom).encode())
def run(n,k=0):c.anguna_frame(k,n)
def press(k,n=180):run(15,k);run(n)
run(1200);press(1);press(8);press(1)
for i in range(43):press(1,90)
print('before',hex(c.anguna_pc()),hex(c.anguna_reg(13)))
c.trace_keys(1);print('trace',c.trace_stack(0x03005000,50000000,str(D/'stack_trace.txt').encode()))
c.trace_mem.argtypes=[C.c_uint,C.c_char_p];print('memtrace',c.trace_mem(30000000,str(D/'mem_trace.txt').encode()))
(D/'ram_trace.bin').write_bytes(bytes(c.anguna_read(0x03000000+i,1) for i in range(0x8000)))
print('after',hex(c.anguna_pc()),hex(c.anguna_reg(13)))
c.anguna_close()
