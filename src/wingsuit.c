#include "wingsuit.h"
#include <string.h>
#define S MF_WS_SCALE
static int clamp(int v,int lo,int hi){return v<lo?lo:(v>hi?hi:v);}
static int near(int x,int y,int a,int b,int rx,int ry)
{return x>=a-rx*S && x<=a+rx*S && y>=b-ry*S && y<=b+ry*S;}
static int emit(mf_ws_shot *pool,int count,int x,int y,int owner)
{
    int i;for(i=0;i<count;i++)if(!pool[i].active){
        pool[i]=(mf_ws_shot){1,x,y,owner,120,0};return 1;
    }return 0;
}
/* Allocate complete bursts atomically: no half fan, overwrite or heap fallback.
   The attached flame has no projectiles and does not consume this pool. */
static int player_fire(mf_wingsuit *g,const mf_ws_player *p,int owner)
{
    int i,n=0,needed=3,slots[3];
    for(i=0;i<MF_WS_SHOTS && n<needed;i++)if(!g->shots[i].active)slots[n++]=i;
    if(n!=needed)return 0;
    for(i=0;i<needed;i++){
        int offset=(i-1)*4;
        int vx=(i-1)*S;
        g->shots[slots[i]]=(mf_ws_shot){1,p->x+offset*S,p->y-15*S,owner,120,vx};
    }
    return 1;
}
static void join(mf_ws_player *p,int i)
{*p=(mf_ws_player){1,(i?190:130)*S,200*S,3,MF_WS_INVULNERABLE,0,0,0,0};}
void mf_ws_init(mf_wingsuit *g,int coop)
{memset(g,0,sizeof(*g));join(&g->players[0],0);if(coop)join(&g->players[1],1);g->spawn=60;}
static int damage(mf_ws_player *p,int i)
{
    if(p->invulnerable || p->respawn || p->lives<=0)return 0;
    --p->lives;p->invulnerable=MF_WS_INVULNERABLE;p->respawn=p->lives?60:0;
    p->x=(i?190:130)*S;p->y=200*S;p->cooldown=p->shot_hold=0;return 1;
}
int mf_ws_beam_active(const mf_wingsuit *g,int i)
{
    const mf_ws_player *p=&g->players[i];
    return p->active && p->lives>0 && !p->respawn && p->shot_hold==MF_WS_FOCUS_TICKS && !g->game_over;
}
void mf_ws_step(mf_wingsuit *g,const unsigned held[2],const unsigned pressed[2],unsigned connected)
{
    int i,j,alive=0,pulse[2]={0,0};
    g->deaths=0;
    if(g->game_over){if((connected&1) && (pressed[0]&MF_START))mf_ws_init(g,g->players[1].active && (connected&2));return;}
    if((connected&2) && !g->players[1].active && (pressed[1]&MF_START))join(&g->players[1],1);
    if((connected&1) && (pressed[0]&MF_START))g->paused=!g->paused;
    if(g->paused)return;
    ++g->ticks;g->scroll=(g->scroll+1)&511;
    for(i=0;i<2;i++){
        mf_ws_player *p=&g->players[i];int dx,dy,speed,focused,tapped;
        unsigned h=(connected&(1u<<i))?held[i]:0;
        unsigned edge=(connected&(1u<<i))?pressed[i]:0;
        if(!p->active || p->lives<=0)continue;
        if(p->respawn){--p->respawn;continue;}
        if(p->invulnerable)--p->invulnerable;
        if(p->cooldown)--p->cooldown;
        if(h&MF_A){if(p->shot_hold<MF_WS_FOCUS_TICKS)++p->shot_hold;}
        else p->shot_hold=0;
        focused=p->shot_hold==MF_WS_FOCUS_TICKS;
        tapped=p->shot_hold==1 || (edge&MF_A);
        dx=!!(h&MF_RIGHT)-!!(h&MF_LEFT);dy=!!(h&MF_DOWN)-!!(h&MF_UP);
        speed=(dx && dy)?MF_WS_DIAGONAL_SPEED:MF_WS_MOVE_SPEED;
        if(focused)speed=speed*MF_WS_FOCUS_PERCENT/100;
        p->x=clamp(p->x+dx*speed,64*S,255*S);p->y=clamp(p->y+dy*speed,16*S,223*S);
        if(focused){
            if(g->beam_wait[i])--g->beam_wait[i];
            if(!g->beam_wait[i]){pulse[i]=1;g->beam_wait[i]=MF_WS_BEAM_TICKS;}
        }else {g->beam_wait[i]=0;if(tapped && !p->cooldown && player_fire(g,p,i))p->cooldown=MF_WS_FIRE_TICKS;}
    }
    if(--g->spawn<=0){
        for(i=0;i<MF_WS_ENEMIES;i++)if(!g->enemies[i].active && !g->enemies[i].explosion){
            g->enemies[i]=(mf_ws_enemy){1,(72+(int)(g->wave*47u%176u))*S,-12*S,0,0};++g->wave;break;
        }g->spawn=MF_WS_SPAWN_TICKS;
    }
    for(i=0;i<MF_WS_ENEMIES;i++){
        mf_ws_enemy *e=&g->enemies[i];if(e->explosion)--e->explosion;
        if(!e->active)continue;
        e->y+=320;++e->age;
        if(e->age==80)emit(g->hostile,MF_WS_HOSTILE,e->x,e->y+10*S,0);
        if(e->y>256*S)e->active=0;
    }
    for(i=0;i<2;i++)if(pulse[i])for(j=0;j<MF_WS_ENEMIES;j++){
        mf_ws_player *p=&g->players[i];mf_ws_enemy *e=&g->enemies[j];
        if(e->active && e->x>=p->x-22*S && e->x<=p->x+22*S &&
           e->y+10*S>=p->y-(15+MF_WS_BEAM_LENGTH)*S && e->y-10*S<=p->y-15*S){
            e->active=0;e->explosion=12;p->score+=100;++g->deaths;
        }
    }
    for(i=0;i<MF_WS_SHOTS;i++){
        mf_ws_shot *s=&g->shots[i];if(!s->active)continue;
        s->x+=s->vx;s->y-=6*S;
        if(--s->ttl<=0 || s->y < -8*S || s->x<52*S || s->x>267*S){s->active=0;continue;}
        for(j=0;j<MF_WS_ENEMIES;j++){
            mf_ws_enemy *e=&g->enemies[j];if(e->active && near(s->x,s->y,e->x,e->y,12,13)){
                e->active=0;e->explosion=12;++g->deaths;s->active=0;g->players[s->owner].score+=100;break;
            }
        }
    }
    for(i=0;i<MF_WS_HOSTILE;i++){
        mf_ws_shot *s=&g->hostile[i];if(!s->active)continue;
        s->y+=3*S;if(--s->ttl<=0 || s->y>248*S){s->active=0;continue;}
        for(j=0;j<2;j++){
            mf_ws_player *p=&g->players[j];if(p->active && p->lives && !p->respawn && near(s->x,s->y,p->x,p->y,7,10)){
                g->deaths+=damage(p,j);s->active=0;break;
            }
        }
    }
    for(i=0;i<2;i++){
        mf_ws_player *p=&g->players[i];if(!p->active || p->lives<=0)continue;
        alive=1;if(p->respawn)continue;
        for(j=0;j<MF_WS_ENEMIES;j++)if(g->enemies[j].active && near(p->x,p->y,g->enemies[j].x,g->enemies[j].y,15,18))g->deaths+=damage(p,i);
    }
    g->game_over=!alive;
}
