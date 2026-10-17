#!/usr/bin/env python3
"""Hash-guarded UTF-8 sprite-font expansion and Chinese text relocation."""
from pathlib import Path
import re,struct,json,hashlib,sys
R=Path(__file__).resolve().parents[1];BASE=0x08000000
EXPECTED='a5bf6ba5d6f78912e35986ba21cf034c65677cc66c3f97022606069dbaafb202'
def bitmap_font():
 result={}
 for blk in (R/'assets/fonts/fusion-pixel-12px-monospaced-zh_hans.bdf').read_text().split('STARTCHAR ')[1:]:
  ls=blk.splitlines();cp=int(next(l for l in ls if l.startswith('ENCODING ')).split()[1]);w,h,xo,yo=map(int,next(l for l in ls if l.startswith('BBX ')).split()[1:]);idx=ls.index('BITMAP')+1;rows=[[0]*16 for _ in range(16)]
  for y,row in enumerate(ls[idx:idx+h]):
   bits=int(row,16)
   for x in range(w):
    xx=x+xo;yy=y+12-h-yo
    if bits&(1<<(len(row)*4-x-1)) and 0<=xx<16 and 0<=yy<16:rows[yy][xx]=11
  result[chr(cp)]=rows
 return result
def main():
 original=(R/'original/Green-Memories-v1.5.0.gba').read_bytes();assert hashlib.sha256(original).hexdigest()==EXPECTED
 b=bytearray(original);translations={}
 for tsv in sorted((R/'translations').glob('*.tsv')):
  for line in tsv.read_text().splitlines():
   if not line or line.startswith('#'):continue
   off,zh=line.split('\t',1);translations[int(off,16)]=zh
 if '--ui-only' in sys.argv:translations={o:t for o,t in translations.items() if o in (0x81989c,0x8198a4,0x80d144,0x80d18c,0x80d174,0x80d160)}
 if '--story-only' in sys.argv:translations={o:t for o,t in translations.items() if 0x80d1a4<=o<=0x819848 or o in (0x81989c,0x8198a4,0x80d144,0x80d18c,0x80d174,0x80d160)}
 if '--clip' in sys.argv:
  k=sys.argv.index('--clip');lo,hi=map(lambda x:int(x,16),sys.argv[k+1:k+3]);translations={o:t for o,t in translations.items() if lo<=o<=hi or o in (0x81989c,0x8198a4,0x80d144,0x80d18c,0x80d174,0x80d160)}
 items=json.loads((R/'translations/items.json').read_text())
 for i,lines in enumerate([] if '--ui-only' in sys.argv or '--no-items' in sys.argv or '--story-only' in sys.argv or '--clip' in sys.argv else items):
  for j in range(5):
   text=lines[j] if j<len(lines) else ''
   for base in (0x81c2e0,0x8217e0):translations[base+i*170+j*34]=text
 short_fields={}
 if not any(x in sys.argv for x in ('--ui-only','--no-items','--story-only','--clip')):
  names=[lines[0] for lines in items]+['护符1','护符2','护符3','护符4']
  for i,name in enumerate(names):
   for base,stride in ((0x82dc54,13),(0x82d5d4,13),(0x82e2d6,40)):
    o=base+i*stride;translations[o]=name;short_fields[o]=13
 font=bitmap_font();chars=sorted(set(''.join(translations.values()))-set(chr(i) for i in range(127)))
 assert not(set(chars)-font.keys()),set(chars)-font.keys()
 compact='--utf8-three-byte' not in sys.argv
 codes={c:chr(0x100+i) for i,c in enumerate(chars)} if compact else {c:c for c in chars}
 assert len(codes)<1792
 (R/'analysis/code_map.json').write_text(json.dumps({c:hex(ord(a)) for c,a in codes.items()},ensure_ascii=False,indent=2)+'\n')
 def append(data,align=4):
  b.extend(b'\xff'*((-len(b))%align));addr=BASE+len(b);b.extend(data);return addr
 # Find original pointers before appending, including unaligned pointers in data.
 refs={}
 for off in translations:
  needle=struct.pack('<I',BASE+off);refs[off]=[];start=0
  while True:
   pos=original.find(needle,start)
   if pos<0:break
   refs[off].append(pos);start=pos+4
 relocated=[]
 for off,zh in sorted(translations.items()):
  end=original.index(0,off);old=original[off:end];new=''.join(codes.get(c,c) for c in zh).encode()
  if (0x81c2e0<=off<0x81dd70 or 0x8217e0<=off<0x823270) or off in short_fields:refs[off]=[]
  if refs[off]:
   addr=append(new+b'\0')
   for pos in refs[off]:struct.pack_into('<I',b,pos,addr)
   for pos in refs[off]:
    if struct.unpack_from('<I',original,pos+4)[0]==BASE+end:struct.pack_into('<I',b,pos+4,addr+len(new))
   relocated.append({'offset':hex(off),'old':old.decode('utf8'),'zh':zh,'refs':list(map(hex,refs[off])),'new':hex(addr)})
  else:
   capacity=short_fields[off] if off in short_fields else 34 if (0x81c2e0<=off<0x81dd70 or 0x8217e0<=off<0x823270) else len(old)+1
   assert len(new)<capacity,(hex(off),zh,len(new),capacity)
   b[off:off+capacity]=new+b'\0'*(capacity-len(new))
   relocated.append({'offset':hex(off),'old':old.decode('utf8'),'zh':zh,'inline':True})
 fonts=json.loads((R/'analysis/fonts.json').read_text());reports=[]
 for f in fonts:
  off=int(f['offset'],16);tiles=int(f['tiles'],16);n=f['count'];mp=int(f['map'],16);w=int(f['width'],16)
  unicode_map={}
  for i in range(f['mask']+1):
   cp,val=struct.unpack_from('<II',original,mp+i*8)
   if val&0x80000000:unicode_map[chr(cp)]=val&0x7fffffff
  extra=[c for c in chars if codes[c] not in unicode_map]
  assert not set(codes.values())&set(unicode_map), 'Custom encoding collision with original Latin glyphs'
  for c in extra:unicode_map[codes[c]]=len(unicode_map)
  new_count=94+len(unicode_map);graphics=bytearray()
  for i in range(n):
   # Original 8x16 has two vertically stacked tiles; pad each row to 16px.
   graphics.extend(original[tiles+i*64:tiles+i*64+32]);graphics.extend(bytes(32));graphics.extend(original[tiles+i*64+32:tiles+i*64+64]);graphics.extend(bytes(32))
  shadow=12 if off==0x82f694 else 1
  for c in extra:
   pix=[row[:] for row in font[c]]
   for y in range(15):
    for x in range(15):
     if font[c][y][x]:
      for xx,yy in ((x+1,y),(x,y+1)):
       if not pix[yy][xx]:pix[yy][xx]=shadow
   for ty in range(2):
    for tx in range(2):
     graphics.extend(pix[ty*8+y][tx*8+x]|pix[ty*8+y][tx*8+x+1]<<4 for y in range(8) for x in range(0,8,2))
  assert len(graphics)==new_count*128
  ga=append(graphics);mask=1
  while mask<len(unicode_map)*2:mask*=2
  table=bytearray(mask*8)
  for c,i in unicode_map.items():
   slot=(ord(c)^0x050c5d1f)&(mask-1)
   while struct.unpack_from('<I',table,slot*8+4)[0]&0x80000000:slot=(slot+1)&(mask-1)
   struct.pack_into('<II',table,slot*8,ord(c),i|0x80000000)
  ma=append(table);widths=original[w:w+n+1]+bytes([12]*len(extra));wa=append(widths)
  struct.pack_into('<IIHBB',b,off,ga,ga+len(graphics),new_count,4,0)
  b[off+24:off+28]=bytes([0,1,0,0]) # square 16x16 font canvas
  struct.pack_into('<IiiII',b,off+28,ma,mask-1,len(unicode_map),wa,wa+len(widths))
  reports.append({'descriptor':hex(off),'graphics':new_count,'new_hanzi':len(extra),'canvas':'16x16','ink_px':12,'tiles':hex(ga),'map':hex(ma),'widths':hex(wa)})
 # Game-specific rich-text width helper recognizes only 17 original UTF-8 glyphs.
 # Its fallback is reached by non-ASCII callers; Chinese aliases need 12px, not 7px.
 assert original[0x1663c:0x16640]==bytes.fromhex('07207047')
 b[0x1663c:0x1663e]=bytes.fromhex('0c20')
 engine_patch={'offset':'0x1663c','before':'0720','after':'0c20','routine':'0x08016628','effect':'Unknown non-ASCII width fallback 7px to 12px; original 17 mapped glyph widths and ASCII paths preserved'}
 import tutorial_graphics_zh, world_graphics_zh
 graphic_report=tutorial_graphics_zh.apply_graphics(b)
 world_report=world_graphics_zh.apply_graphics(b)
 b[0xbd]=(-sum(b[0xa0:0xbd])-0x19)&255
 assert len(b)<=32*1024*1024
 out=R/'output/green_memories_zh.gba';out.write_bytes(b)
 report={'source_sha256':EXPECTED,'sha256':hashlib.sha256(b).hexdigest(),'size':len(b),'translations':len(relocated),'characters':len(chars),'encoding':'2-byte UTF-8 aliases U+0100..U+07FF mapped to Chinese glyphs' if compact else 'diagnostic 3-byte UTF-8','fonts':reports,'records':relocated,'engine_patch':engine_patch,'graphics':graphic_report,'world_graphics':world_report}
 (R/'analysis/build.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('records','fonts','graphics','world_graphics')},indent=2))
if __name__=='__main__':main()
