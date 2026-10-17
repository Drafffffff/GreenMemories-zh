exec(open('GREEN_MEMORIES/tools/check_runtime.py').read().split('run(1200)')[0])
run(1200);press(1);press(8);press(1);shot('qa_spacing')
for i in range(128):
 a,b,d=(c.anguna_read(0x7000000+i*8+k,2) for k in (0,2,4))
 if a&0x300==0x200:continue
 print(i,hex(a),hex(b),hex(d),'xy',b&511,a&255)
