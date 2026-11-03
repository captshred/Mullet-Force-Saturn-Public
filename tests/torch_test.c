#include <assert.h>
#include <stdio.h>
#include "game.h"
static void tick(mf_game *g,unsigned h0,unsigned h1,unsigned p0,unsigned p1,unsigned connected)
{
    unsigned h[2]={h0,h1},p[2]={p0,p1};mf_game_step_inputs(g,h,p,connected);
}
static void input(mf_game *g,int p,unsigned held,unsigned pressed)
{
    tick(g,p?0:held,p?held:0,p?0:pressed,p?pressed:0,3);
}
static void hold(mf_game *g,int p,int n){while(n--)input(g,p,MF_A,0);}
static void wait(mf_game *g,int n){while(n--)tick(g,0,0,0,0,3);}
static void init(mf_game *g,int facing)
{
    int i;mf_game_init(g);tick(g,0,0,MF_START,MF_START,3);
    for(i=0;i<2;i++){
        g->players[i].x=200*256;g->players[i].y=200*256;g->players[i].facing=facing;g->players[i].invulnerable=0;
        g->enemies[i].hp=0;g->enemies[i].state=MF_ENEMY_ABSENT;g->enemies[i].timer=100000;
    }
    for(i=0;i<3;i++){g->drums[i].hp=0;g->drums[i].respawn=-100000;}
}
static void charge(mf_game *g,int p)
{
    input(g,p,MF_A,MF_A);hold(g,p,MF_TORCH_CHARGE_TICKS-1);
    assert(g->players[p].torch==MF_TORCH_FIRE && (g->events&MF_TORCH_IGNITE));
    assert(g->players[p].torch==MF_TORCH_FIRE && (g->events&MF_TORCH_HISS));
}
static void enemy(mf_game *g,int i,int x,int y,int hp)
{
    mf_enemy *e=&g->enemies[i];*e=(mf_enemy){0};e->x=x*256;e->y=y*256;e->hp=hp;
    e->state=MF_ENEMY_RECOVER;e->timer=10000;e->target=-1;e->grace=10000;
}
int main(void)
{
    mf_game g;int p,f,i,x,hp,score,clock;
    for(p=0;p<2;p++)for(f=-1;f<=1;f+=2){
        init(&g,f);input(&g,p,MF_A,MF_A);assert(g.players[p].attack && g.players[p].charge==1);
        hold(&g,p,MF_TORCH_CHARGE_TICKS-2);
        assert(g.players[p].charge==MF_TORCH_CHARGE_TICKS-1 && !g.players[p].torch && !g.players[p].attack);
        hold(&g,p,1);assert(g.players[p].torch==MF_TORCH_FIRE && (g.events&MF_TORCH_IGNITE));
        assert(g.players[p].torch==MF_TORCH_FIRE && (g.events&MF_TORCH_HISS));
        assert(!g.players[1-p].torch && !g.players[1-p].charge);
        x=g.players[p].x;input(&g,p,MF_A|MF_RIGHT|MF_B,MF_B|MF_A|MF_RIGHT);
        assert(!g.players[p].height && !g.players[p].attack && !g.players[p].bat);
        assert(g.players[p].x-x==MF_TORCH_WALK_SPEED && g.players[p].facing==f);
        input(&g,p,0,0);assert(g.players[p].torch==MF_TORCH_AWAY && !(g.events&MF_TORCH_HISS));
        input(&g,p,MF_A,MF_A);assert(g.players[p].attack && g.players[p].charge==1 && !g.players[p].torch);
    }
    puts("PASS both players/facings: exact 60-tick threshold, one initial punch, equip/fire/release, slow strafe, no jump/bat, fresh re-press");

    /* Charge remains continuous across idle/walk, diagonal and facing changes. */
    for(p=0;p<2;p++){
        init(&g,1);
        for(i=0;i<60;i++){
            unsigned d=i<15?MF_RIGHT:i<30?MF_LEFT|MF_UP:i<45?0:MF_RIGHT|MF_DOWN;
            int oldx=g.players[p].x,oldy=g.players[p].y;
            input(&g,p,MF_A|d,i==0?MF_A:0);
            if(i<59){
                assert(g.players[p].charge==i+1 && !g.players[p].torch);
                if(d==MF_RIGHT)assert(g.players[p].x-oldx==390);
                if(d==(MF_LEFT|MF_UP))assert(oldx-g.players[p].x==390*181/256 && g.players[p].y<oldy && g.players[p].facing==-1);
            }else assert(g.players[p].torch==MF_TORCH_FIRE && g.players[p].facing==1 && g.players[p].x-oldx==MF_TORCH_WALK_SPEED*181/256);
        }
    }
    init(&g,1);input(&g,0,MF_A,MF_A);hold(&g,0,58);
    input(&g,0,MF_A|MF_LEFT,MF_LEFT);
    assert(g.players[0].torch==MF_TORCH_FIRE && g.players[0].facing==-1);
    init(&g,1);
    for(i=0;i<70;i++){
        unsigned h0=MF_A|(i<30?MF_RIGHT:MF_LEFT),h1=i<10?0:MF_A|MF_RIGHT|MF_DOWN;
        tick(&g,h0,h1,i==0?MF_A:0,i==10?MF_A:0,3);
        if(i==58)assert(g.players[0].charge==59 && g.players[1].charge==49);
        if(i==59)assert(g.players[0].torch==MF_TORCH_FIRE && g.players[0].facing==-1 && g.players[1].charge==50);
    }
    assert(g.players[1].torch==MF_TORCH_FIRE && g.players[1].facing==1);
    init(&g,1);input(&g,0,MF_A,MF_A);hold(&g,0,58);input(&g,0,MF_LEFT,MF_LEFT);
    assert(!g.players[0].charge && !g.players[0].torch);
    puts("PASS moving/diagonal/idle/facing charge, direct firing at 60 ticks, independent staggered co-op holds, pre-threshold release");

    init(&g,1);
    for(i=0;i<20;i++){input(&g,0,MF_A,MF_A);input(&g,0,0,0);}
    wait(&g,150);assert(!g.players[0].charge && !g.players[0].torch);
    init(&g,1);input(&g,0,MF_A,MF_A);hold(&g,0,30);input(&g,0,MF_A|MF_B,MF_B);
    assert(g.players[0].height>0 && !g.players[0].charge);
    hold(&g,0,200);assert(!g.players[0].torch && !g.players[0].charge);
    input(&g,0,0,0);charge(&g,0);assert(g.players[0].torch==MF_TORCH_FIRE);
    puts("PASS quick taps do not accumulate, jump cancels charge, stale hold after landing cannot fire");

    for(i=0;i<2;i++){
        init(&g,1);if(i)charge(&g,0);else{input(&g,0,MF_A,MF_A);hold(&g,0,20);}
        tick(&g,MF_A,0,MF_START,0,3);assert(g.paused && !g.players[0].torch && !g.players[0].charge);
        tick(&g,MF_A,0,MF_START,0,3);assert(!g.paused);
        hold(&g,0,140);assert(!g.players[0].torch && !g.players[0].charge);
        input(&g,0,0,0);charge(&g,0);
        tick(&g,MF_A,0,0,0,2);assert(!g.players[0].torch && !g.players[0].charge && !(g.events&MF_TORCH_HISS));
        tick(&g,MF_A,0,MF_A,0,3);hold(&g,0,140);assert(!g.players[0].torch);
        input(&g,0,0,0);charge(&g,0);
    }
    puts("PASS pause/disconnect cancel charging and firing; held/reconnected A cannot reactivate without release");

    init(&g,1);charge(&g,0);enemy(&g,0,244,200,6);
    g.enemies[0].state=MF_ENEMY_ACTIVE;g.enemies[0].timer=6;g.enemies[0].facing=-1;
    input(&g,0,MF_A,0);assert(g.players[0].hurt && !g.players[0].torch && !(g.events&MF_TORCH_HISS));
    hold(&g,0,150);assert(!g.players[0].torch);
    init(&g,1);charge(&g,0);g.players[0].health=0;g.players[0].defeated=1;
    input(&g,0,MF_A,0);hold(&g,0,140);assert(g.players[0].health==100 && !g.players[0].torch);
    init(&g,1);g.players[0].hurt=3;wait(&g,3);
    input(&g,0,MF_A,MF_A);assert(g.players[0].charge==1);
    init(&g,1);tick(&g,0,0,MF_START,0,3);tick(&g,0,0,0,0,3);
    tick(&g,MF_A,0,MF_START|MF_A,0,3);assert(!g.paused && g.players[0].charge==1);
    puts("PASS damage/defeat stop fire and stale holds remain disarmed; observed release allows a genuinely fresh press");

    init(&g,1);input(&g,0,MF_RIGHT,MF_RIGHT);input(&g,0,0,0);input(&g,0,MF_RIGHT|MF_A,MF_RIGHT|MF_A);
    assert(g.players[0].bat && !g.players[0].charge);
    hold(&g,0,180);assert(!g.players[0].torch && !g.players[0].charge);
    input(&g,0,0,0);charge(&g,0);
    init(&g,1);charge(&g,0);input(&g,0,MF_B,MF_B);
    assert(g.players[0].height>0 && !g.players[0].torch);
    init(&g,1);charge(&g,0);input(&g,0,MF_RIGHT,MF_RIGHT);input(&g,0,0,0);
    input(&g,0,MF_RIGHT|MF_A,MF_RIGHT|MF_A);assert(g.players[0].bat && !g.players[0].torch);
    puts("PASS recognized bat wins and needs fresh A; fresh jump/bat can interrupt put-away immediately after release");

    for(p=0;p<2;p++)for(f=-1;f<=1;f+=2){
        init(&g,f);charge(&g,p);x=g.players[p].x/256;
        g.players[1-p].x=(x+f*58)*256;g.players[1-p].y=200*256;
        enemy(&g,0,x+f*58,200,6);enemy(&g,1,x+f*58,225,6);g.players[p].torch_tick=0;
        input(&g,p,MF_A,0);assert(g.enemies[0].hp==5 && g.enemies[1].hp==6 && g.enemies[0].burn<=MF_BURN_TICKS);
        assert(g.enemies[0].state==MF_ENEMY_RECOVER && !g.hitstop);
        hp=g.enemies[0].hp;hold(&g,p,MF_TORCH_DAMAGE_TICKS-1);assert(g.enemies[0].hp==hp);
        hold(&g,p,1);assert(g.enemies[0].hp==hp-1 && g.enemies[0].burn<=MF_BURN_TICKS);
        clock=g.enemies[0].burn_clock;assert(clock<MF_BURN_DAMAGE_TICKS);
        input(&g,p,0,0);hp=g.enemies[0].hp;
        wait(&g,MF_BURN_TICKS+2);assert(g.enemies[0].hp<hp && !g.enemies[0].burn);
        assert(g.enemies[1].hp==6 && g.players[1-p].health==100);
    }
    puts("PASS diagonal ground-depth-aligned 0.2s damage, no recurring stun/hit-stop, finite refreshed non-stacking burn, no friendly fire");

    init(&g,1);charge(&g,0);
    {mf_hitbox high={240,245,192,208,60,80},near={234,240,192,208,34,45},floor={270,278,192,208,0,10},lane={240,260,230,240,0,50};
     assert(!mf_torch_hits(&g.players[0],high) && mf_torch_hits(&g.players[0],near));
     assert(mf_torch_hits(&g.players[0],floor) && !mf_torch_hits(&g.players[0],lane));}
    puts("PASS visible downward slope has vertical limits; floor direction is not a different street-depth lane");

    init(&g,1);tick(&g,MF_A,MF_A,MF_A,MF_A,3);
    for(i=1;i<MF_TORCH_CHARGE_TICKS;i++)tick(&g,MF_A,MF_A,0,0,3);
    assert(g.players[0].torch==MF_TORCH_FIRE && g.players[1].torch==MF_TORCH_FIRE);
    enemy(&g,0,258,200,1);enemy(&g,1,258,225,6);
    g.drums[0].x=258*256;g.drums[0].y=200*256;g.drums[0].hp=1;g.drums[0].respawn=0;
    g.players[0].torch_tick=g.players[1].torch_tick=0;tick(&g,MF_A,MF_A,0,0,3);
    assert(!g.enemies[0].hp && g.score==MF_ENEMY_DEFEAT_SCORE+110 && g.broken==1 && !g.drums[0].hp);
    assert(g.enemies[1].hp==6 && (g.events&MF_TORCH_HISS));score=g.score;
    tick(&g,0,MF_A,0,0,3);assert(g.events&MF_TORCH_HISS);
    tick(&g,0,0,0,0,3);assert(!(g.events&MF_TORCH_HISS));wait(&g,250);
    assert(g.score==score && g.drums[0].hp==3);
    puts("PASS simultaneous torches: independent cooldowns, one defeat/barrel score, shared hiss desired-state, barrel respawn");
    return 0;
}
