"""Compare the original menu-entry fade with the reviewed localization."""
import sys
sys.argv.append('--original')
exec(open('GREEN_MEMORIES/tools/check_runtime.py').read().split('run(1200)')[0])
run(1200);press(1);press(8);press(1)
for i in range(65):press(1,90)
for i in range(8):press(16,60)
press(2);press(2)
frames=[]
for i in range(195):
 run(1,8 if i<15 else 0);im=Image.frombytes('RGB',(240,160),C.string_at(c.anguna_pixels(),76800),'raw','BGR;16',0);frames.append(len(im.getcolors(38400)))
P=R/'analysis';review=json.loads((P/'runtime/continuous_frames.json').read_text());fixed=[z['colors'] for z in review[2]['frames']]
report={'original_start_entry_colors':frames,'fixed_start_entry_colors':fixed,'original_monochrome_frames':[i for i,x in enumerate(frames) if x==1],'fixed_monochrome_frames':[i for i,x in enumerate(fixed) if x==1],'original_min_colors':min(frames),'fixed_min_colors':min(fixed),'note':'Menu-entry monochrome fade exists in original too; no new recurring blank frames inferred from the entry fade alone.'}
(P/'qa_transition_baseline.json').write_text(json.dumps(report,indent=2)+'\n');print(report['original_monochrome_frames'],report['fixed_monochrome_frames'])
