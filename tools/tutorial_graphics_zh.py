"""Translate raw Butano BG items; patch explicit item spans/maps, not aliases.
Original assets: 4bpp, 32x32 tile maps, no compression. Palette/navigation retained.
"""
from pathlib import Path
import struct,json,hashlib
from collections import Counter
from PIL import Image
P=Path(__file__).resolve().parents[1]; ROOT=P.parent
D=P/'analysis/tutorial_graphics'; A=P/'assets/tutorial_graphics'
NEEDED=set(Path(__file__).read_text())
def font_bitmaps(path,size,baseline):
 result={}
 for block in path.read_text().split('STARTCHAR ')[1:]:
  lines=block.splitlines();cp=int(next(x for x in lines if x.startswith('ENCODING ')).split()[1])
  if cp>127 and chr(cp) not in NEEDED:continue
  w,h,xo,yo=map(int,next(x for x in lines if x.startswith('BBX ')).split()[1:]);pos=lines.index('BITMAP')+1;rows=[[0]*size for _ in range(size)]
  for y,row in enumerate(lines[pos:pos+h]):
   bits=int(row,16)
   for x in range(w):
    xx=x+xo;yy=y+baseline-h-yo
    if bits&(1<<(len(row)*4-x-1)) and 0<=xx<size and 0<=yy<size:rows[yy][xx]=1
  result[chr(cp)]=rows
 return result
fonts={n:font_bitmaps(A/f'fonts/fusion-pixel-{n}px-monospaced-zh_hans.bdf',n,{8:7,10:8,12:10}[n]) for n in [8,10,12]}

def unpack(rom,desc):
 t,e,bpp,pa,pe,pc,mp,w,h,n=struct.unpack_from('<10I',rom,desc)
 t-=0x08000000;e-=0x08000000;pa-=0x08000000;mp-=0x08000000
 assert bpp==0 and w*h<=65536 and n in [1,0x1000001] and pe-0x08000000-pa==32
 pal=struct.unpack_from('<16H',rom,pa);maps=struct.unpack_from('<'+str(w*h)+'H',rom,mp)
 p=[[0]*(w*8) for _ in range(h*8)]
 for y in range(h*8):
  for x in range(w*8):
   v=maps[y//8*w+x//8];xx=7-x%8 if v&0x400 else x%8;yy=7-y%8 if v&0x800 else y%8
   p[y][x]=(rom[t+(v&1023)*32+yy*4+xx//2]>>(xx%2*4))&15
 return p,pal,(t,e,mp)
INK={}
def fill(p,box,v):
 v=INK.get(v,v)
 x0,y0,x1,y1=box
 for y in range(y0,y1):p[y][x0:x1]=[v]*(x1-x0)
def width(s,n):return sum(n if ord(c)>127 else n//2 for c in s)
def text(p,s,x,y,n=12,ink=3):
 ink=INK.get(ink,ink)
 for c in s:
  assert c in fonts[n],repr(c)
  for yy,row in enumerate(fonts[n][c]):
   for xx,v in enumerate(row):
    if v and 0<=x+xx<len(p[0]) and 0<=y+yy<len(p):p[y+yy][x+xx]=ink
  x+=n if ord(c)>127 else n//2

def centered(p,s,y,n=12,ink=3,center=128):text(p,s,center-width(s,n)//2,y,n,ink)
def pack(p):
 # Include flipped aliases to match GBA map encoding and reduce tile allocation.
 table={};tiles=[];maps=[]
 for ty in range(len(p)//8):
  for tx in range(len(p[0])//8):
   rows=tuple(tuple(p[ty*8+y][tx*8:tx*8+8]) for y in range(8))
   if rows not in table:
    i=len(tiles);tiles.append(rows);table[rows]=i
    table.setdefault(tuple(tuple(reversed(row)) for row in rows),i|0x400)
    table.setdefault(tuple(reversed(rows)),i|0x800)
    table.setdefault(tuple(tuple(reversed(row)) for row in reversed(rows)),i|0xc00)
   maps.append(table[rows])
 out=bytearray()
 for rows in tiles:
  for row in rows:
   for x in range(0,8,2):out.append(row[x]|row[x+1]<<4)
 assert len(tiles)<1024
 return out,struct.pack('<'+str(len(maps))+'H',*maps),len(tiles)

def tutorial(p,page):
 # Original diagrams, status icons, navigation dots and page numbers remain.
 fill(p,(34,54,221,66),14);centered(p,'教程：'+('天气影响' if page<5 else '武器'),54,12)
 if page==0:
  fill(p,(25,76,236,114),1)
  for y,s in [(77,'留意天气带来的影响！'),(91,'状态生效时，画面左上角'),(105,'会显示对应的图标。')]:centered(p,s,y)
 elif page==1:
  fill(p,(18,100,242,187),1)
  for y,s,ink in [(110,'白天会出现酷热。',3),(125,'暴晒会使生命值缓慢下降。',7),(140,'在云影或树荫下可免受影响。',3),(155,'饮用清凉饮料可暂时抵御酷热。',3)]:centered(p,s,y,12,ink)
 elif page==2:
  fill(p,(18,100,242,187),1)
  for y,s,ink in [(112,'夜间会出现霜冻。',3),(128,'霜冻会降低移动速度。',7),(144,'饮用咖啡可暂时抵御霜冻。',3)]:centered(p,s,y,12,ink)
 elif page==3:
  fill(p,(18,84,242,124),1);fill(p,(18,164,242,188),1)
  centered(p,'生命值不会自动恢复。',86,12,7);centered(p,'需要从土壤中取水恢复生命。',103)
  centered(p,'在物品栏选择水壶，',163);centered(p,'按 A 键使用。',177)
 elif page==4:
  fill(p,(18,79,242,132),1);fill(p,(18,165,242,188),1)
  centered(p,'时钟下方的图标显示',90);centered(p,'在当前土壤中取水的成功率。',106)
  centered(p,'注意：取水会消耗体力。',171,12,7)
 elif page==5:
  fill(p,(18,76,242,130),1);fill(p,(18,165,242,189),1)
  for y,s in [(77,'使用武器击败敌人。'),(91,'在物品栏中选武器，按 A 使用。'),(105,'最初拥有以下两种武器：')]:centered(p,s,y)
  centered(p,'砍刀',166,12,6,89);centered(p,'手枪',166,12,6,167)
  centered(p,'注意：使用武器会消耗体力！',179,10,7)
 elif page==6:
  fill(p,(18,113,242,188),1)
  for y,s in [(120,'砍刀是一种近战武器。'),(136,'伤害较高，能击退部分敌人。'),(152,'还能弹开某些飞来的投射物。')]:centered(p,s,y)
 elif page==7:
  fill(p,(18,113,242,188),1)
  for y,s in [(119,'手枪是一种远程武器。'),(135,'伤害较低，但能快速连续射击。'),(151,'朝目标方向按住 R 可锁定瞄准。'),(167,'瞄准时无法奔跑。')]:centered(p,s,y)

# English item addresses followed by their Portuguese equivalent at +0x28.
TUTORIALS=[0x827d48,0x827cf8,0x827ca8,0x827c58,0x827c08,0x827bb8,0x827b68,0x827b18]

def apply_graphics(rom):
 original=(P/'original/Green-Memories-v1.5.0.gba').read_bytes()
 assert hashlib.sha256(original).hexdigest()=='a5bf6ba5d6f78912e35986ba21cf034c65677cc66c3f97022606069dbaafb202'
 D.mkdir(parents=True,exist_ok=True);A.mkdir(parents=True,exist_ok=True)
 report=[]
 def save(desc,p,pal,old,kind):
  assert bytes(rom[desc:desc+40])==original[desc:desc+40],hex(desc)
  b,m,count=pack(p);t,e,mp=old
  if len(b)<=e-t:
   rom[t:e]=b+bytes(e-t-len(b));rom[mp:mp+len(m)]=m;newt=t;newmp=mp;allocation=(e-t)//32
  else:
   while len(rom)%4:rom.append(0)
   newt=len(rom);rom.extend(b);newmp=len(rom);rom.extend(m);allocation=count
   struct.pack_into('<II',rom,desc,newt+0x08000000,newt+len(b)+0x08000000);struct.pack_into('<I',rom,desc+24,newmp+0x08000000)
  im=Image.new('RGB',(len(p[0]),len(p)));im.putdata([tuple(((pal[v]>>s)&31)*255//31 for s in [0,5,10]) for row in p for v in row]);im.save(A/f'{desc:x}_zh.png');im.crop((8,48,248,208)).resize((720,480),Image.Resampling.NEAREST).save(D/f'{desc:x}_zh_3x.png')
  report.append(dict(descriptor=hex(desc),kind=kind,old_tiles=(e-t)//32,unique_tiles=count,allocated_tiles=allocation,tiles=hex(newt),map=hex(newmp),relocated=newt!=t,pixel_sha256=hashlib.sha256(bytes(v for row in p for v in row)).hexdigest()))
 for page,desc in enumerate(TUTORIALS):
  p,pal,old=unpack(original,desc)
  def near(rgb):return min(range(1,16),key=lambda i:sum((((pal[i]>>sh)&31)-target)**2 for sh,target in zip([0,5,10],rgb)))
  INK.update({1:near((0,0,0)),3:near((31,31,31)),6:near((31,26,0)),7:near((31,0,0)),14:Counter(v for row in p[54:66] for v in row[34:221]).most_common(1)[0][0]})
  tutorial(p,page);save(desc,p,pal,old,f'tutorial_{page+1}')
  pt,ptpal,ptold=unpack(original,desc+0x28)
  mapping={i:min(range(16),key=lambda j:sum((((pal[i]>>sh)&31)-((ptpal[j]>>sh)&31))**2 for sh in [0,5,10])) for i in range(16)}
  pt=[[mapping[v] for v in row] for row in p];save(desc+0x28,pt,ptpal,ptold,f'tutorial_{page+1}_pt_branch')
 INK.clear()
 apply_ui(original,save)
 apply_atlases(original,save)
 for item in report:
  desc=int(item['descriptor'],16);pixels,palette,_=unpack(rom,desc)
  assert hashlib.sha256(bytes(v for row in pixels for v in row)).hexdigest()==item['pixel_sha256'],hex(desc)
  assert rom[desc+8:desc+24]==original[desc+8:desc+24] and rom[desc+28:desc+40]==original[desc+28:desc+40]
 (D/'patch_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 return dict(resources=report,count=len(report),font='Fusion Pixel 12/10/8px',encoding='raw 4bpp tiles + variable-size tilemaps (32x32, 32x160, 192x32); explicit item span/map pointers')
apply_tutorials=apply_graphics

def apply_ui(original,save):
 entries=json.loads((D/'inventory.json').read_text())
 tutorials={x+y for x in TUTORIALS for y in [0,0x28]}
 for index,ent in enumerate(entries):
  if index%2:continue
  desc=ent['desc']
  if desc in tutorials:continue
  p,pal,old=unpack(original,desc)
  white=min(range(1,16),key=lambda i:sum((31-((pal[i]>>sh)&31))**2 for sh in [0,5,10]))
  black=min(range(1,16),key=lambda i:sum(((pal[i]>>sh)&31)**2 for sh in [0,5,10]))
  def label(box,s,n=10,ink=None,bg=None):
   x0,y0,x1,y1=box
   if bg is None:bg=Counter(v for row in p[y0:y1] for v in row[x0:x1]).most_common(1)[0][0]
   fill(p,box,bg)
   centered(p,s,y0+(y1-y0-n)//2,n,white if ink is None else ink,(x0+x1)//2)
  def back(confirm=False):
   if confirm:label((149,198,190,206),'确定',8,bg=p[199][238])
   label((205,198,234,206),'返回',8,bg=p[199][238])
  def head(box,s):label(box,s,10)
  if desc<=0x827190:
   if desc in [0x827028,0x827050]:
    fill(p,(16,92,29,174),Counter(v for row in p[94:172] for v in row[16:29]).most_common(1)[0][0])
    for k,c in enumerate('日志'):text(p,c,17,118+k*14,12,white)
   else:
    selected={0x827078:3,0x8270c8:2,0x827118:1,0x827168:0}[desc]
    for row,(y,word) in enumerate([(100,'保存游戏'),(116,'操作说明'),(132,'教程'),(148,'返回标题')]):
     bg=p[y+2][14];fill(p,(14,y,190 if row==selected else 158,y+13),bg)
     text(p,word,190-width(word,12) if row==selected else 16,y,12,white)
  elif desc in [0x827258,0x827280]:
   head((21,82,65,92),'属性');head((21,133,98,145),'饰品');head((17,187,70,196),'金币')
  elif desc in [0x8272f8,0x827320]:head((117,55,154,67),'任务');back()
  elif desc in [0x827348,0x827370]:
   for box,word in [((49,55,89,67),'状态'),((94,80,148,91),'成长'),((178,91,212,102),'属性'),((159,140,202,149),'攻击'),((159,154,202,164),'体力'),((39,171,81,181),'希特拉')]:head(box,word)
   back()
  elif desc in [0x827398,0x8273c0,0x8273e8,0x827410,0x827618,0x827640,0x827668,0x827690]:
   head((69,55,123,67),'物品栏');label((58,79,100,88),'物品',8,bg=p[79][58]);label((154,79,208,88),'装备',8,bg=p[79][154]);back()
  elif desc in [0x827438,0x827460,0x827488,0x8274b0,0x8274d8,0x827500]:
   head((137,55,178,67),'系统')
   for y,word in [(100,'保存游戏'),(133,'操作说明'),(166,'返回标题')]:label((78,y,181,y+13),word,12)
   back(True)
  elif desc in [0x827528,0x827550,0x827578,0x8275a0,0x8275c8,0x8275f0]:
   head((102,55,125,67),'地图');back(desc in [0x827528,0x827550])
   if desc in [0x8275c8,0x8275f0]:
    bg=p[123][65];label((43,124,212,154),'',10,bg=bg)
    centered(p,'未知区域',124,12,white);centered(p,'地图不可用',140,12,white)
  elif desc in [0x8276b8,0x8276e0]:
   bg=p[117][50];label((24,122,179,152),'',10,bg=bg);centered(p,'未知区域',123,12,white,101);centered(p,'地图不可用',139,12,white,101)
  elif 0x827708<=desc<=0x827820:
   # L/R button glyphs and selected/unselected colored panels retained.
   label((42,52,100,68),'存入' if desc<0x8277a8 else '取出',12,bg=p[53][43])
   label((101,53,130,66),'原料',10)
  elif 0x827848<=desc<=0x8278c0:label((34,52,100,68),'制作',12)
  elif 0x8278e8<=desc<=0x827a00:
   buy_selected=desc in [0x827938,0x8279d8]
   pink=min(range(1,16),key=lambda i:sum((((pal[i]>>sh)&31)-v)**2 for sh,v in zip([0,5,10],[31,8,15])))
   green=p[65][43] if not buy_selected else p[65][101]
   label((43,55,77,66),'购买',10,bg=pink if buy_selected else green);label((87,55,128,66),'出售',10,bg=green if buy_selected else pink)
  elif desc in [0x827a28,0x827a50]:
   label((10,49,247,69),'游戏结束',12,bg=black)
   label((11,187,247,208),'烈日惩罚了希特拉的疏忽。',12,bg=black)
  elif desc in [0x827a78,0x827aa0]:
   label((52,53,208,67),'感谢游玩！',12,ink=black)
   for y,word in [(77,'导演'),(90,'美术'),(102,'音效'),(115,'关卡设计'),(128,'程序')]:label((56,y,124,y+9),word,8,ink=black)
   label((56,179,175,192),'开发工具：butano lib',8,ink=black)
  elif desc in [0x827ac8,0x827af0]:
   # Restore plain color from surrounding ground before overprinting the ending.
   label((62,178,199,196),'未完待续……',12,ink=black)
  elif desc in [0x827d98,0x827dc0]:
   for box,word in [((22,84,97,94),'上个物品'),((173,84,232,94),'下个物品'),((24,98,75,120),'常用武器'),((174,96,229,106),'锁定瞄准'),((33,133,64,144),'移动'),((177,124,231,134),'使用物品'),((183,136,229,146),'确定'),((38,161,68,173),'菜单'),((97,164,148,184),'常用物品'),((173,159,202,170),'奔跑'),((150,173,227,184),'选择物品')]:label(box,word,8,bg=black)
  else:raise AssertionError(hex(desc))
  save(desc,p,pal,old,'baked_ui')
  pt,ptpal,ptold=unpack(original,desc+0x28)
  mapping={i:min(range(16),key=lambda j:sum((((pal[i]>>sh)&31)-((ptpal[j]>>sh)&31))**2 for sh in [0,5,10])) for i in range(16)}
  pt=[[mapping[v] for v in row] for row in p];save(desc+0x28,pt,ptpal,ptold,'baked_ui_pt_branch')

def apply_atlases(original,save):
 for desc in [0x8271b8,0x8271e0,0x827208,0x827230,0x8272a8,0x8272d0]:
  p,pal,old=unpack(original,desc)
  white=min(range(1,16),key=lambda i:sum((31-((pal[i]>>sh)&31))**2 for sh in [0,5,10]))
  if len(p[0])>256:
   for page,word in enumerate(['状态','物品栏','地图','任务','档案','系统']):
    bg=p[50][page*256+100];start=[80,72,100,92,97,86][page]
    fill(p,(page*256+start,52,page*256+200,74),bg)
    text(p,word,page*256+start,53,12,white)
  else:
   bg=p[0][18];fill(p,(17,0,34,len(p)),bg)
   for page,word in enumerate(['消耗品','材料','关键物品','饰品','武器']):
    y=page*256+128-len(word)*7
    for k,c in enumerate(word):text(p,c,19,y+k*14,12,white)
  save(desc,p,pal,old,'legacy_menu_atlas')

if __name__=='__main__':
 rom=bytearray((P/'original/Green-Memories-v1.5.0.gba').read_bytes());print(json.dumps(apply_graphics(rom),ensure_ascii=False,indent=2));(A/'graphics_probe.gba').write_bytes(rom)
