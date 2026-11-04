#!/usr/bin/env python3
"""Exercise the actual main.c VBlank callback alongside live co-op simulation.
Saturn I/O uses the street loader mocks. This is not an emulator test.
"""
from pathlib import Path
import re,subprocess,tempfile
root=Path(__file__).resolve().parents[1]
main=(root/'src/main.c').read_text()
callback=re.search(r'static void clock_tick\(void\)\n\{.*?\n\}',main,re.S).group(0)
assert 'mf_street_animate(vblanks);' in callback
assert 'jo_core_add_vblank_callback(clock_tick);' in main
source=r'''
#define main street_loader_suite
#include "street_test.c"
#undef main
#include "game.h"
static volatile unsigned vblanks;
'''+callback+r'''
int main(void)
{
    mf_game game,control,before;unsigned i,c,changes=0;
    unsigned short previous[256],initial[256];
    unsigned char cells_before[131072],map_before[131072];
    int sprites[5]={0};jo_palette palette={1,colors};
    nbg1_bitmap=(jo_color *)street_a0;
    assert(mf_street_load(&palette,sprites));
    memcpy(initial,colors,sizeof(colors));memcpy(previous,colors,sizeof(colors));
    memcpy(cells_before,street_a0,sizeof(street_a0));
    memcpy(map_before,street_b0,sizeof(street_b0));
    mf_game_init(&game);control=game;
    for(i=0;i<2048;i++) {
        unsigned held[2]={0,0},pressed[2]={0,0};
        if(i==0)pressed[0]=pressed[1]=MF_START;
        else {
            unsigned f=i%240;
            held[0]=f<120?MF_RIGHT:MF_LEFT;held[1]=f<120?MF_LEFT:MF_RIGHT;
            if(f==1 || f==3 || f==121 || f==123)pressed[0]=held[0],pressed[1]=held[1];
            if(f==2 || f==122)held[0]=held[1]=0;
            if(i%20==4){pressed[0]|=MF_A;pressed[1]|=MF_A;held[0]|=MF_A;held[1]|=MF_A;}
            if(i%180==40){pressed[0]|=MF_B;pressed[1]|=MF_B;held[0]|=MF_B;held[1]|=MF_B;}
        }
        before=game;clock_tick();assert(!memcmp(&before,&game,sizeof(game)));
        mf_game_step_inputs(&game,held,pressed,3);
        mf_game_step_inputs(&control,held,pressed,3);
        assert(game.started && !game.paused && game.players[0].active && game.players[1].active);
        assert(!memcmp(&game,&control,sizeof(game)));
        if(memcmp(previous,colors,sizeof(colors)))changes++;
        memcpy(previous,colors,sizeof(colors));
        for(c=0;c<256;c++)if(c<239 || c>246)assert(colors[c]==initial[c]);
    }
    assert(changes>100 && vblanks==2048 && game.ticks>0);
    assert(reads==3 && uploads==3 && !sprite_uploads && !sprite_draws);
    assert(!memcmp(cells_before,street_a0,sizeof(street_a0)));
    assert(!memcmp(map_before,street_b0,sizeof(street_b0)));
    puts("PASS actual VBlank callback during 2048 live co-op updates: neon changes in gameplay, immutable gameplay state, no gallery dependency, isolated CRAM/no uploads");
    return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='mf-city-gameplay-') as temp:
    path=Path(temp);(path/'test.c').write_text(source)
    flags=['MF_CITY_NEON','MF_PUNCH_COMBO','MF_FAST_RUNNING_BAT','MF_JAB_COHESION',
           'MF_ATTACK_SEQUENCE','MF_BAT_MOMENTUM','MF_RUN_BAT','MF_DASH_ENABLED']
    subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror',*[f'-D{f}=1' for f in flags],
                    '-I'+str(root/'tests/street_mock'),'-I'+str(root/'tests'),'-I'+str(root/'src'),
                    str(path/'test.c'),str(root/'src/game.c'),'-o',str(path/'test')],check=True,cwd=root)
    subprocess.run([str(path/'test')],check=True,cwd=root)
