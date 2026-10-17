"""Compare native rich-text helper returns and OAM x pitch in original/old/fixed ROMs."""
from pathlib import Path
import ctypes as C,json,struct,hashlib
from PIL import Image
P=Path(__file__).resolve().parents[1];D=P/'analysis/qa_spacing';D.mkdir(exist_ok=True)
c=C.CDLL(str(P/'build/runtime_bridge.dylib'));c.anguna_open.argtypes=[C.c_char_p];c.anguna_pixels.restype=C.c_void_p;c.anguna_read.restype=C.c_uint
original=(P/'original/Green-Memories-v1.5.0.gba').read_bytes();cps=[struct.unpack_from('<I',original,0x82d1b4+8*i)[0] for i in range(17)]
codes=json.loads((P/'analysis/code_map.json').read_text());samples={ch:chr(int(codes[ch],16)).encode() for ch in '这个星球'}
report={}
for label,rom in [('original',P/'original/Green-Memories-v1.5.0.gba'),('before',P/'analysis/prereview/green_memories_zh.gba'),('after',P/'output/green_memories_zh.gba')]:
 assert c.anguna_open(str(rom).encode())
 def run(n,k=0):c.anguna_frame(k,n)
 def press(k,n=180):run(15,k);run(n)
 run(1200);press(1);press(8);press(1)
 def width(packed):
  c.anguna_write(0x203f100,packed,4);assert c.anguna_call(0x8016628,0x203f100,0,0)>=0;return c.anguna_result()
 latin=[width(cp) for cp in cps];han={ch:width(int.from_bytes(seq+b'\0'*(4-len(seq)),'little')) for ch,seq in samples.items()}
 im=Image.frombytes('RGB',(240,160),C.string_at(c.anguna_pixels(),240*160*2),'raw','BGR;16',0);im.resize((720,480),Image.Resampling.NEAREST).save(D/(label+'_opening_3x.png'))
 oam=[]
 for i in range(128):
  a,b,t=(c.anguna_read(0x7000000+i*8+k,2) for k in (0,2,4))
  if a&0x300!=0x200:oam.append(dict(index=i,x=b&511,y=a&255,a0=hex(a),a1=hex(b),tile=hex(t)))
 row2=sorted(x['x'] for x in oam if x['y']==138);report[label]={'sha256':hashlib.sha256(rom.read_bytes()).hexdigest(),'original_latin_widths':latin,'chinese_widths':han,'row2_x':row2,'oam':oam};c.anguna_close()
assert report['original']['original_latin_widths']==report['before']['original_latin_widths']==report['after']['original_latin_widths']
assert set(report['before']['chinese_widths'].values())=={7}
assert set(report['after']['chinese_widths'].values())=={12}
assert all(b-a==12 for a,b in zip(report['after']['row2_x'],report['after']['row2_x'][1:]))
report['ascii_width_table_unchanged']=original[0x82d144:0x82d1a3]==(P/'output/green_memories_zh.gba').read_bytes()[0x82d144:0x82d1a3]
assert report['ascii_width_table_unchanged']
(D/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('17 original Latin widths unchanged; Chinese fallback 7 → 12; row2 OAM pitch 12; ASCII table unchanged')
