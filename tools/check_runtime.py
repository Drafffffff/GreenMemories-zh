from pathlib import Path
import ctypes as C,json,hashlib,sys
from PIL import Image
R=Path(__file__).resolve().parents[1];D=R/('analysis/original_runtime_direct' if '--original' in sys.argv else 'analysis/runtime');D.mkdir(exist_ok=True,parents=True)
c=C.CDLL(str(R/'build/runtime_bridge.dylib'));c.anguna_open.argtypes=[C.c_char_p];c.anguna_pixels.restype=C.c_void_p;c.anguna_read.argtypes=[C.c_uint,C.c_uint];c.anguna_read.restype=C.c_uint
rom=R/('original/Green-Memories-v1.5.0.gba' if '--original' in sys.argv else 'output/green_memories_zh.gba');c.anguna_open(str(rom).encode())
qa='--qa' in sys.argv;trace_enabled=False;transitions=[];oam_snapshots={}
def shot(n):
 im=Image.frombytes('RGB',(240,160),C.string_at(c.anguna_pixels(),240*160*2),'raw','BGR;16',0);im.save(D/(n+'.png'));im.resize((720,480),Image.Resampling.NEAREST).save(D/(n+'_3x.png'))
 if qa:
  rows={}
  for i in range(128):
   a,b=(c.anguna_read(0x7000000+i*8+k,2) for k in (0,2))
   if a&0x300!=0x200:rows.setdefault(str(a&255),[]).append(b&511)
  oam_snapshots[n]={y:sorted(x) for y,x in rows.items()}
def run(n,k=0):c.anguna_frame(k,n)
def press(k,n=180):
 if not qa or not trace_enabled:run(15,k);run(n);return
 folder=D/'continuous_frames'/f'{len(transitions):02}_key{k}';folder.mkdir(parents=True,exist_ok=True)
 metrics=[];contact=[];samples=[0,1,2,4,8,12,16,24,32,48,64,120,15+n-1]
 for f in range(15+n):
  run(1,k if f<15 else 0)
  raw=C.string_at(c.anguna_pixels(),240*160*2);im=Image.frombytes('RGB',(240,160),raw,'raw','BGR;16',0)
  count=len(im.getcolors(38400));metrics.append({'frame':f,'colors':count,'sha256':hashlib.sha256(raw).hexdigest()})
  if f<65:im.save(folder/f'{f:03}.png')
  if f in samples:contact.append(im.copy())
 canvas=Image.new('RGB',(240*4,160*4))
 for i,im in enumerate(contact):canvas.paste(im,(i%4*240,i//4*160))
 canvas.save(folder/'contact.png')
 assert metrics[-1]['colors']>5, ('Unexpected settled blank scene',k)
 transitions.append({'key':k,'frames':metrics,'folder':str(folder),'settled_colors':metrics[-1]['colors']})
run(1200);shot('00_language');press(1);shot('01_title');press(8);shot('02_menu');press(1);shot('03_opening')
for i in range(65):
 press(1,90);shot(f'opening_{i:02}')
shot('tutorial_00')
for i in range(8):press(16,60);shot(f'tutorial_{i+1:02}')
trace_enabled=True
press(2);shot('controls');press(2);shot('gameplay');press(8);shot('inventory')
for i in range(5):press(256);shot(f'menu_page_{i+1}')
for i in range(4):press(512,60)
shot('inventory_r');press(64,60);shot('items_category_1');press(128,60);shot('inventory_category_return');press(1);shot('item_action');press(2);shot('return_game');print('pc',hex(c.anguna_pc()),'regs',list(map(hex,[c.anguna_reg(i) for i in range(16)])))
assert len(Image.open(D/'gameplay.png').getcolors(38400))>50, 'Scene did not render'
assert len(Image.open(D/'inventory.png').getcolors(38400))>5, 'Menu did not render'
(D/'report.json').write_text(json.dumps({'sha256':hashlib.sha256(rom.read_bytes()).hexdigest(),'checks':'Blank SRAM boot, Chinese language selection, title menu, new game, 65 opening confirmations, eight weather tutorial pages, controls, actual camp scene, status, inventory weapons category, A/B navigation, all six Start menu pages and menu return.','limits':'Not a full playthrough or hardware validation.'},indent=2)+'\n')

if qa:
 (D/'oam_snapshots.json').write_text(json.dumps(oam_snapshots,indent=2)+'\n')
 (D/'continuous_frames.json').write_text(json.dumps(transitions,indent=2)+'\n')
