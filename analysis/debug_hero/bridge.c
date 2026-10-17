/* Test-only mGBA access. Never linked into the distributed ROM. */
#include <mgba/core/core.h>
#include <mgba/core/log.h>
#include <mgba/internal/arm/arm.h>
#include <mgba/internal/arm/isa-inlines.h>
#include <mgba-util/vfs.h>
#include <string.h>
struct mCore *GBACoreCreate(void);
static struct mCore *core;
static color_t pixels[240*160];
static unsigned last_result;
static void quiet(struct mLogger*l,int cat,enum mLogLevel level,const char*fmt,va_list args) {
    (void)l;(void)cat;(void)level;(void)fmt;(void)args;
}
static struct mLogger logger={quiet,0};
int anguna_open(const char *rom) {
    mLogSetDefaultLogger(&logger);
    core=GBACoreCreate();if(!core->init(core))return 0;
    mCoreInitConfig(core,0);core->setVideoBuffer(core,pixels,240);
    if(!core->loadROM(core,VFileOpen(rom,0)))return 0;
    core->reset(core);return 1;
}
void anguna_frame(unsigned keys,unsigned frames) {
    core->setKeys(core,keys);for(unsigned i=0;i<frames;i++)core->runFrame(core);
}
const void *anguna_pixels(void) {return pixels;}
unsigned anguna_read(unsigned addr,unsigned size) {
    return size==1?core->busRead8(core,addr):size==2?core->busRead16(core,addr):core->busRead32(core,addr);
}
void anguna_write(unsigned addr,unsigned value,unsigned size) {
    if(size==1)core->busWrite8(core,addr,value);else if(size==2)core->busWrite16(core,addr,value);else core->busWrite32(core,addr,value);
}
void anguna_jump(unsigned addr,unsigned r0,unsigned r1,unsigned r2) {
    struct ARMCore *a=core->cpu;
    _ARMSetMode(a,MODE_THUMB);a->gprs[0]=r0;a->gprs[1]=r1;a->gprs[2]=r2;
    a->gprs[14]=0x0203f001;
    core->busWrite16(core,0x0203f000,0xe7fe);
    a->gprs[15]=addr&~1;ThumbWritePC(a);
}
/* Execute a nonblocking ROM routine and resume the original game context. */
int anguna_call(unsigned addr,unsigned r0,unsigned r1,unsigned r2) {
    struct ARMCore *a=core->cpu;
    int regs[16];memcpy(regs,a->gprs,sizeof(regs));
    unsigned cpsr=a->cpsr.packed;unsigned prefetch[2];memcpy(prefetch,a->prefetch,sizeof(prefetch));
    enum ExecutionMode mode=a->executionMode;
    anguna_jump(addr,r0,r1,r2);
    unsigned i;
    for(i=0;i<2000000;i++) {
        if(a->gprs[15]==0x0203f002)break;
        core->step(core);
    }
    last_result=a->gprs[0];
    memcpy(a->gprs,regs,sizeof(regs));a->cpsr.packed=cpsr;
    _ARMSetMode(a,mode);a->memory.setActiveRegion(a,regs[15]);
    memcpy(a->prefetch,prefetch,sizeof(prefetch));
    return i<2000000 ? (int)i : -1;
}
unsigned anguna_pc(void){struct ARMCore*a=core->cpu;return a->gprs[15];}
unsigned anguna_result(void){return last_result;}
void anguna_close(void){core->deinit(core);}
unsigned anguna_reg(unsigned reg){struct ARMCore*a=core->cpu;return a->gprs[reg&15];}
void anguna_step(unsigned steps){for(unsigned i=0;i<steps;i++)core->step(core);}
#include <stdio.h>
void trace_keys(unsigned keys){core->setKeys(core,keys);}
int trace_stack(unsigned low,unsigned steps,const char*file){
 struct ARMCore*a=core->cpu;unsigned ring[256][5],pos=0;
 for(unsigned i=0;i<steps;i++){
  ring[pos%256][0]=a->gprs[15];ring[pos%256][1]=a->gprs[13];ring[pos%256][2]=a->gprs[14];ring[pos%256][3]=a->cpsr.packed;ring[pos%256][4]=a->gprs[0];pos++;
  unsigned sp=a->gprs[13];unsigned mode=a->cpsr.packed&31;
  if(sp<low&&sp>=0x03000000&&(mode==0x1f||mode==0x10)){
   FILE*f=fopen(file,"w");fprintf(f,"steps %u regs\n",i);for(unsigned j=0;j<16;j++)fprintf(f,"r%u 0x%08x\n",j,a->gprs[j]);fprintf(f,"cpsr %x\nring pc sp lr cpsr r0\n",a->cpsr.packed);
   unsigned start=pos>256?pos-256:0;for(unsigned j=start;j<pos;j++){unsigned*r=ring[j%256];fprintf(f,"%08x %08x %08x %08x %08x\n",r[0],r[1],r[2],r[3],r[4]);}
   fclose(f);return i;
  }core->step(core);
 }return -1;
}
int trace_mem(unsigned steps,const char*file){
 struct ARMCore*a=core->cpu;FILE*f=fopen(file,"w");unsigned calls=0;
 for(unsigned i=0;i<steps;i++){
  unsigned pc=a->gprs[15];
  if(pc==0x0809288a||pc==0x080928ba||pc==0x0809288c||pc==0x080928bc){
   fprintf(f,"step %u pc %08x lr %08x r0 %08x r1 %08x r2 %08x sp %08x\n",i,pc,a->gprs[14],a->gprs[0],a->gprs[1],a->gprs[2],a->gprs[13]);calls++;
   if((unsigned)a->gprs[2]>0x100000){for(unsigned j=0;j<16;j++)fprintf(f,"r%u %08x\n",j,a->gprs[j]);fclose(f);return i;}
  }
  core->step(core);
 }fprintf(f,"calls %u",calls);fclose(f);return -1;
}
