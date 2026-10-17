exec(open('GREEN_MEMORIES/tools/check_runtime.py').read().split('run(1200)')[0])
run(1200);press(1);press(8);press(1)
for i in range(44):
 if i<40:press(1,90);continue
 run(15,1)
 for j in range(90):
  run(1)
  if j%5==0:print(i,j,hex(c.anguna_pc()),hex(c.anguna_reg(13)&0xffffffff),hex(c.anguna_reg(14)&0xffffffff))
 if i==40:
  Path('GREEN_MEMORIES/analysis/ram40.bin').write_bytes(bytes(c.anguna_read(0x3000000+k,1) for k in range(0x8000)))
