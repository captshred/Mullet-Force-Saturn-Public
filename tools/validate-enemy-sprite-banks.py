#!/usr/bin/env python3
"""Phase 5 scope lock plus immutable original tests and actual current tests."""
from pathlib import Path
import io,subprocess,sys,tarfile,tempfile
R=Path(__file__).resolve().parents[1]
BASE='1dfe2197828890d9aae9131c95ede2ad9aaece6f'
allowed={'Makefile','make/saturn.mk','src/main.c','src/corporate_animation.c','src/animation_preview.c','tools/build-native.sh','tools/build-source-complete.sh','tools/audit-sprite-memory.py'}
if subprocess.run(['git','cat-file','-e',BASE+'^{commit}'],cwd=R,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:
 subprocess.run(['git','fetch','--no-tags','--depth=1','origin',BASE],cwd=R,check=True)
with tempfile.TemporaryDirectory(prefix='enemy-bank-reference-') as d:
 ref=Path(d)
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',BASE],cwd=R))) as t:t.extractall(ref,filter='data')
 for p in ref.rglob('*'):
  if p.is_file() and str(p.relative_to(ref)) not in allowed:assert (R/p.relative_to(ref)).read_bytes()==p.read_bytes(),str(p.relative_to(ref))
 text=(R/'src/main.c').read_text()
 text=text.replace('#include "enemy_sprite_bank.h"\n','')
 text=text.replace('#if MF_CORPORATE_PUNK && !MF_ENEMY_SPRITE_BANKS','#if MF_CORPORATE_PUNK')
 text=text.replace('#if !MF_ENEMY_SPRITE_BANKS\n    for(i=0;i<255;i++) {\n        unsigned c=enemy_palette.data[i];unsigned r=(c&31)+10,g=((c>>5)&31)+3,b=((c>>10)&31)/2;\n        if(r>31)r=31;\n        if(g>31)g=31;\n        burn_palette.data[i]=0x8000|r|(g<<5)|(b<<10);\n    }\n#endif\n','    for(i=0;i<255;i++) {\n        unsigned c=enemy_palette.data[i];unsigned r=(c&31)+10,g=((c>>5)&31)+3,b=((c>>10)&31)/2;\n        if(r>31)r=31;\n        if(g>31)g=31;\n        burn_palette.data[i]=0x8000|r|(g<<5)|(b<<10);\n    }\n')
 text=text.replace('MF_FX_DEFINITIONS-(MF_ENEMY_SPRITE_BANKS?MF_ENEMY_CP_DEFS:0)','MF_FX_DEFINITIONS')
 text=text.replace('MF_FX_TEXTURE_BYTES-MF_ENEMY_DEFERRED_BYTES','MF_FX_TEXTURE_BYTES')
 text=text.replace('#if MF_ENEMY_SPRITE_BANKS\n    if(!asset_error && !mf_enemy_bank_boot(&mf_corporate_bank_spec,&enemy_palette))\n        asset_failure(732,"ENEMY BANK",mf_enemy_bank_diagnostics()->error);\n    if(!asset_error) {\n    for(i=0;i<255;i++) {\n        unsigned c=enemy_palette.data[i];unsigned r=(c&31)+10,g=((c>>5)&31)+3,b=((c>>10)&31)/2;\n        if(r>31)r=31;\n        if(g>31)g=31;\n        burn_palette.data[i]=0x8000|r|(g<<5)|(b<<10);\n    }\n        if(jo_get_last_sprite_id()+1!=MF_FX_DEFINITIONS || mf_animation_texture_bytes()!=MF_FX_TEXTURE_BYTES)\n            asset_failure(733,"BANK BUDGET",0);\n    }\n#endif\n','')
 text=text.replace('#if MF_ENEMY_SPRITE_BANKS\n    if(!asset_error && !mf_enemy_bank_ready() && !stage2_owned) {\n        unsigned state=mf_enemy_bank_service(now);\n        now=vblanks;last_vblank=now;pending[0]=pending[1]=0;\n        mf_music_update(game.started,game.paused,0,now);\n        if(state!=MF_BANK_READY) {\n            if(state==MF_BANK_FAILED)jo_printf(3,12,"ENEMY BANK FAILED E%u",mf_enemy_bank_diagnostics()->error);\n            return; /* No sprite submissions while draining/loading/failed. */\n        }\n    }\n#endif\n','')
 text=text.replace('#if MF_ENEMY_SPRITE_BANKS\n            mf_enemy_bank_retire();\n#endif\n','')
 assert text==(ref/'src/main.c').read_text(),'change outside reviewed bank integrations: src/main.c'
 text=(R/'src/corporate_animation.c').read_text()
 text=text.replace('#include "enemy_sprite_bank.h"\n#if MF_ENEMY_SPRITE_BANKS\ntypedef char bank_count_matches[(MF_CP_RESOURCES+MF_CPHQ_NEW==MF_ENEMY_CP_DEFS)?1:-1];\ntypedef char bank_bytes_match[(MF_CP_TEXTURE_BYTES+MF_CPHQ_BYTES==MF_ENEMY_CP_BYTES)?1:-1];\nstatic int cp_resident;\n#endif\n','')
 text=text.replace('    jo_set_tga_default_palette(JO_NULL);\n#if MF_ENEMY_SPRITE_BANKS\n    cp_resident=1;\n#endif\n    return 1;','    jo_set_tga_default_palette(JO_NULL);return 1;')
 text=text.replace('#if MF_ENEMY_SPRITE_BANKS\nstatic void invalidate(void)\n{\n    int r;cp_resident=0;\n    for(r=0;r<MF_CP_RESOURCES;r++)cp_ids[r]=-1;\n    for(r=0;r<MF_CPHQ_NEW;r++)cphq_ids[r]=-1;\n}\nstatic int validate(int first)\n{\n    int r,id;unsigned end=0x10000u+MF_ENEMY_PREFIX_BYTES;\n    for(r=0;r<MF_CP_RESOURCES+MF_CPHQ_NEW;r++) {\n        const mf_cp_resource *p=r<MF_CP_RESOURCES?&cp_resources[r]:&cphq_resources[r-MF_CP_RESOURCES];\n        id=r<MF_CP_RESOURCES?cp_ids[r]:cphq_ids[r-MF_CP_RESOURCES];\n        if(id!=first+r || jo_sprite_get_width(id)!=p->width || jo_sprite_get_height(id)!=p->height ||\n           __jo_sprite_pic[id].color_mode!=COL_256 ||\n           (unsigned long)jo_sprite_get_raw_data(id)-JO_VDP1_VRAM!=end)return 0;\n        end+=(p->width*p->height+31u)&~31u;\n    }\n    return cp_resident && end==0x10000u+MF_ENEMY_PREFIX_BYTES+MF_ENEMY_CP_BYTES;\n}\nconst mf_enemy_bank_spec mf_corporate_bank_spec={MF_ENEMY_BANK_CORPORATE,MF_ENEMY_CP_DEFS,MF_ENEMY_CP_BYTES,mf_corporate_load,invalidate,validate};\n#endif\n','')
 text=text.replace('#if MF_ENEMY_SPRITE_BANKS\n    /* Consume the path without falling back to invalid legacy enemy IDs. */\n    if(!cp_resident || !mf_enemy_bank_ready())return 1;\n#endif\n','')
 assert text==(ref/'src/corporate_animation.c').read_text(),'change outside reviewed bank integrations: src/corporate_animation.c'
 text=(R/'src/animation_preview.c').read_text()
 text=text.replace('#include "enemy_sprite_bank.h"\n','')
 text=text.replace('-MF_ENEMY_DEFERRED_BYTES','')
 text=text.replace('unsigned mf_animation_texture_bytes(void){return texture_bytes\n#if MF_ENEMY_SPRITE_BANKS\n    +mf_enemy_bank_bytes()\n#endif\n    ;}','unsigned mf_animation_texture_bytes(void){return texture_bytes;}')
 text=text.replace('jo_printf(2,6,"VDP1 %u / 458488 BYTES",mf_animation_texture_bytes())','jo_printf(2,6,"VDP1 %u / 458488 BYTES",texture_bytes)')
 assert text==(ref/'src/animation_preview.c').read_text(),'change outside reviewed bank integrations: src/animation_preview.c'
 assert (R/'make/saturn.mk').read_text().replace('corporate_animation.c enemy_sprite_bank.c','corporate_animation.c')==(ref/'make/saturn.mk').read_text()
 for n in ('.git','.deps'):(ref/n).symlink_to(R/n,target_is_directory=True)
 (ref/'build').mkdir()
 for p in (R/'build').iterdir():
  if p.suffix not in ('.h','.c'):(ref/'build'/p.name).symlink_to(p,target_is_directory=p.is_dir())
 (ref/'build/build-info.h').write_text((R/'build/build-info.h').read_text().replace('#define MF_ENEMY_SPRITE_BANKS 1','#define MF_ENEMY_SPRITE_BANKS 0'))
 subprocess.run(['python3','tools/validate-hud-panel-memory.py',*[x for x in sys.argv[1:] if x in ('--test','--disc')]],cwd=ref,check=True)
print('PASS enemy-bank scope: exact original renderer/AI/input/gameplay/audio/Level2/assets; only reviewed order/lifetime/accounting hooks',flush=True)
if '--disc' in sys.argv or '--test' in sys.argv:
 for script in ('tools/test-enemy-bank-render.py','tools/test-enemy-sprite-banks.py'):subprocess.run(['python3',script],cwd=R,check=True)
