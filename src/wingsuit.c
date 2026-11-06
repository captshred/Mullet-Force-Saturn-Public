#include "wingsuit.h"
#include <string.h>
#include <stdint.h>
#define S MF_WS_SCALE
static int clamp(int v,int lo,int hi){return v<lo?lo:(v>hi?hi:v);}
int mf_ws_screen_x(const mf_wingsuit *g,int world_x)
{return world_x-g->camera_x+MF_WS_VIEW_LEFT*S;}
static int living(const mf_ws_player *p)
{return p->active && p->lives>0 && !p->respawn;}
/* Equal treatment at maximum separation: project the proposed pair onto the
   largest visible center span. Neither player can push the other offscreen. */
static void contain_players(mf_wingsuit *g,const int old_x[2])
{
    mf_ws_player *a=&g->players[0],*b=&g->players[1];
    int span=(MF_WS_VIEW_WIDTH-2*MF_WS_PLAYER_MARGIN)*S;
    if(living(a) && living(b)){
        int lo=a->x<b->x?a->x:b->x,hi=a->x>b->x?a->x:b->x;
        if(hi-lo>span){
            int left=a->x<b->x?0:1,right=1-left;
            int excess=hi-lo-span;
            int dl=old_x[left]-g->players[left].x;
            int dr=g->players[right].x-old_x[right];
            /* Consume outward movement only. A stationary partner is never
               dragged by the other player's attempt to exceed the span. */
            if(dl<0)dl=0;
            if(dr<0)dr=0;
            if(dl+dr>=excess){
                int undo_left=dl*excess/(dl+dr);
                g->players[left].x+=undo_left;
                g->players[right].x-=excess-undo_left;
            }else {
                /* Repair only externally invalid/restored state. */
                int start=clamp((lo+hi-span)/2,MF_WS_PLAYER_MIN,MF_WS_PLAYER_MAX-span);
                g->players[left].x=start;g->players[right].x=start+span;
            }
        }
    }
}
void mf_ws_camera_step(mf_wingsuit *g)
{
    int i,lo=MF_WS_STAGE_WIDTH*S,hi=0,n=0,target,lower,upper;
    g->camera_x=clamp(g->camera_x,0,MF_WS_CAMERA_MAX);
    for(i=0;i<2;i++)if(living(&g->players[i])){
        int x=g->players[i].x;if(x<lo)lo=x;if(x>hi)hi=x;++n;
    }
    if(!n)return;
    /* Nearest camera satisfying both dead-zone edges; when the pair is wider
       than the dead zone, follow its midpoint instead. */
    lower=hi-MF_WS_CAMERA_RIGHT*S;upper=lo-MF_WS_CAMERA_LEFT*S;
    target=lower<=upper?clamp(g->camera_x,lower,upper):(lo+hi-MF_WS_VIEW_WIDTH*S)/2;
    /* Visibility overrides the normal dead zone. Valid simulation movement
       keeps this feasible with the 3px camera speed (heroes move <=2.5px). */
    lower=hi-(MF_WS_VIEW_WIDTH-MF_WS_PLAYER_MARGIN)*S;
    upper=lo-MF_WS_PLAYER_MARGIN*S;
    target=clamp(clamp(target,lower,upper),0,MF_WS_CAMERA_MAX);
    g->camera_x+=clamp(target-g->camera_x,-MF_WS_CAMERA_SPEED,MF_WS_CAMERA_SPEED);
}
static int near(int x,int y,int a,int b,int rx,int ry)
{return x>=a-rx*S && x<=a+rx*S && y>=b-ry*S && y<=b+ry*S;}
/* Generic constant-velocity emission keeps future static/fan patterns separate
   from the basic drone's AIMED_SNAPSHOT targeting policy. No homing in physics. */
static int emit_hostile(mf_wingsuit *g,int x,int y,int vx,int vy,int target)
{
    int i;for(i=0;i<MF_WS_HOSTILE;i++)if(!g->hostile[i].active){
        g->hostile[i]=(mf_ws_hostile_shot){1,x,y,target,120,vx,vy};return 1;
    }return 0;
}
static uint32_t integer_sqrt(uint64_t n)
{
    uint64_t root=0,bit=UINT64_C(1)<<62;
    while(bit>n)bit>>=2;
    while(bit){
        if(n>=root+bit){n-=root+bit;root=(root>>1)+bit;}
        else root>>=1;
        bit>>=2;
    }return (uint32_t)root;
}
static void aimed_snapshot(mf_wingsuit *g,int x,int y)
{
    int i,target=-1;uint64_t best=UINT64_MAX;int64_t dx=0,dy=0;
    for(i=0;i<MF_WS_PLAYERS;i++){
        const mf_ws_player *p=&g->players[i];int64_t tx,ty;uint64_t d;
        if(!p->active || p->lives<=0 || p->respawn)continue;
        tx=(int64_t)p->x-x;ty=(int64_t)p->y-y;d=(uint64_t)(tx*tx+ty*ty);
        /* Strict comparison and ascending order give Buck exact ties. */
        if(d<best){best=d;target=i;dx=tx;dy=ty;}
    }
    if(target>=0){
        int vx=0,vy=MF_WS_HOSTILE_SPEED;
        if(best){
            /* Eight extra fractional length bits also normalize subpixel
               vectors. Legal stage coordinates keep this shift below 2^51. */
            uint32_t length=integer_sqrt(best<<16);
            vx=(int)(dx*MF_WS_HOSTILE_SPEED*256/length);
            vy=(int)(dy*MF_WS_HOSTILE_SPEED*256/length);
        } /* Coincident muzzle/hero uses deterministic straight-down fallback. */
        emit_hostile(g,x,y,vx,vy,target);
    }
}
/* One successful tap consumes one existing slot and emits one audio event. */
static int player_fire(mf_wingsuit *g,const mf_ws_player *p,int owner)
{
    int i;for(i=0;i<MF_WS_SHOTS;i++)if(!g->shots[i].active){
        g->shots[i]=(mf_ws_shot){1,p->x,p->y-15*S,owner,120,0};
        g->shots_fired|=1u<<owner;return 1;
    }return 0;
}
static void join(mf_ws_player *p,int i)
{*p=(mf_ws_player){1,(i?190:130)*S,200*S,3,MF_WS_INVULNERABLE,0,0,0,0};}
/* Home slots are symmetric about the current view: solo at center; coop
   retains the original 60px separation. Respawn never recenters the camera. */
static int home_x(const mf_wingsuit *g,int i)
{
    int partner=g->players[1-i].active && g->players[1-i].lives>0;
    return g->camera_x+(MF_WS_VIEW_WIDTH/2+(partner?(i?30:-30):0))*S;
}
void mf_ws_init(mf_wingsuit *g,int coop)
{
    memset(g,0,sizeof(*g));g->camera_x=MF_WS_CAMERA_INITIAL;
    join(&g->players[0],0);if(coop)join(&g->players[1],1);
    g->players[0].x=home_x(g,0);if(coop)g->players[1].x=home_x(g,1);
    g->spawn=60;g->enemy_rng=0x4d465332u;g->last_pattern=-1;
}
static int damage(mf_ws_player *p,int i)
{
    if(p->invulnerable || p->respawn || p->lives<=0)return 0;
    --p->lives;p->invulnerable=MF_WS_INVULNERABLE;p->respawn=p->lives?60:0;
    (void)i;p->y=200*S;p->cooldown=p->shot_hold=0;return 1;
}
int mf_ws_beam_active(const mf_wingsuit *g,int i)
{
    const mf_ws_player *p=&g->players[i];
    return p->active && p->lives>0 && !p->respawn && p->shot_hold==MF_WS_FOCUS_TICKS && !g->game_over;
}
/* Quarter-wave table, interpolated in 24.8. No floats or path histories. */
static int wave_sin(int phase)
{
    static const short q[]={0,25,50,74,98,121,142,162,181,198,213,226,237,245,251,255,256};
    unsigned p=(unsigned)phase&1023u, quadrant=p>>8, t=p&255u;int v;
    if(quadrant&1)t=256-t;
    v=t==256?256:q[t>>4]+(q[(t>>4)+1]-q[t>>4])*(int)(t&15)/16;
    return quadrant>=2?-v:v;
}
static unsigned enemy_random(mf_wingsuit *g)
{g->enemy_rng=g->enemy_rng*1664525u+1013904223u;return g->enemy_rng>>16;}
static void move_enemy(mf_ws_enemy *e)
{
    int t=e->age, offset=0;
    if(e->kind==MF_WS_CHROME_EYE){
        /* Negative local time queues the tail above the screen. Every member
           samples exactly the same immutable path at an 18-tick offset. */
        e->y=(-16*S)+t*352;
        if(e->pattern==0)offset=66*wave_sin(t*5);
        else if(e->pattern==1)offset=86*wave_sin(t*3-256);
        else offset=36*wave_sin(t*10);
        e->x=e->origin+e->direction*offset;
    }else {
        e->y+=320;
        switch(e->pattern){
        case 0: offset=e->direction*clamp(t,0,170)*S/2;break;
        case 1: offset=8*wave_sin(t*5);break;
        case 2: offset=e->direction*clamp(t,0,150)*S;break;
        case 3: offset=e->direction*72*(256-wave_sin(t*3+256))/2;break;
        default: offset=e->direction*clamp(t,0,70)*S;break;
        }
        if(e->origin || e->direction)e->x=clamp(e->origin+offset,12*S,(MF_WS_STAGE_WIDTH-12)*S);
    }
}
static void spawn_enemies(mf_wingsuit *g)
{
    int i,n=0,pattern,dir,origin,count;
    if(--g->spawn>0)return;
    /* Do not recycle a live formation or its death effects. No capacity growth. */
    for(i=0;i<MF_WS_ENEMIES;i++)if(g->enemies[i].active || g->enemies[i].explosion)++n;
    if(n){g->spawn=15;return;}
    dir=(enemy_random(g)&1)?1:-1;
    origin=g->camera_x+112*S;
    if(g->wave%4==3){
        pattern=(g->formation+1+(int)(enemy_random(g)%2))%3;
        g->formation=pattern;count=6+(int)(enemy_random(g)%3);
        for(i=0;i<count;i++){
            mf_ws_enemy *e=&g->enemies[i];
            *e=(mf_ws_enemy){.active=1,.kind=MF_WS_CHROME_EYE,.pattern=pattern,
                .origin=origin,.direction=dir,.age=-i*18};
            move_enemy(e);
        }
        g->spawn=340;
    }else {
        /* Shuffle bag: each of five patterns once, no boundary repeat. */
        if(!g->pattern_bag)g->pattern_bag=31;
        {int choices[5],available=0;
         for(i=0;i<5;i++)if((g->pattern_bag&(1u<<i)) && i!=g->last_pattern)choices[available++]=i;
         pattern=choices[enemy_random(g)%(unsigned)available];}
        g->pattern_bag&=~(1u<<pattern);g->last_pattern=pattern;
        if(pattern==0){g->diagonal_direction^=1;dir=g->diagonal_direction?1:-1;}
        count=3;
        for(i=0;i<count;i++){
            int d=pattern==2?(i&1?-1:1):dir;
            int x=origin+(i-1)*24*S;
            if(pattern==0 || pattern>=3)x=origin-d*72*S+(i-1)*16*S;
            if(pattern==2)x=origin-d*92*S;
            g->enemies[i]=(mf_ws_enemy){.active=1,.x=x,.y=-16*S,
                .pattern=pattern,.origin=x,.direction=d,.delay=i*14};
        }
        g->spawn=270;
    }
    ++g->wave;
}
void mf_ws_step(mf_wingsuit *g,const unsigned held[2],const unsigned pressed[2],unsigned connected)
{
    unsigned ready=0;
    int i,j,alive=0,pulse[2]={0,0},old_x[2]={g->players[0].x,g->players[1].x};
    g->deaths=0;g->shots_fired=0;
    if(g->game_over){if((connected&1) && (pressed[0]&MF_START))mf_ws_init(g,g->players[1].active && (connected&2));return;}
    if((connected&2) && !g->players[1].active && (pressed[1]&MF_START)){
        join(&g->players[1],1);g->players[1].x=home_x(g,1);
    }
    if((connected&1) && (pressed[0]&MF_START))g->paused=!g->paused;
    if(g->paused)return;
    ++g->ticks;g->scroll=(g->scroll+1)&511;
    for(i=0;i<2;i++){
        mf_ws_player *p=&g->players[i];int dx,dy,speed,focused;
        unsigned h=(connected&(1u<<i))?held[i]:0;
        if(!p->active || p->lives<=0)continue;
        if(p->respawn){
            if(!--p->respawn)p->x=home_x(g,i);
            continue;
        }
        ready|=1u<<i;
        if(p->invulnerable)--p->invulnerable;
        if(p->cooldown)--p->cooldown;
        if(h&MF_A){if(p->shot_hold<MF_WS_FOCUS_TICKS)++p->shot_hold;}
        else p->shot_hold=0;
        focused=p->shot_hold==MF_WS_FOCUS_TICKS;
        dx=!!(h&MF_RIGHT)-!!(h&MF_LEFT);dy=!!(h&MF_DOWN)-!!(h&MF_UP);
        speed=(dx && dy)?MF_WS_DIAGONAL_SPEED:MF_WS_MOVE_SPEED;
        if(focused)speed=speed*MF_WS_FOCUS_PERCENT/100;
        p->x=clamp(p->x+dx*speed,MF_WS_PLAYER_MIN,MF_WS_PLAYER_MAX);p->y=clamp(p->y+dy*speed,16*S,223*S);
    }
    contain_players(g,old_x);
    mf_ws_camera_step(g);
    /* Fire only after containment, from the final world-space emitter. */
    for(i=0;i<2;i++){
        mf_ws_player *p=&g->players[i];
        unsigned edge=(connected&(1u<<i))?pressed[i]:0;
        if(!(ready&(1u<<i)))continue;
        if(p->shot_hold==MF_WS_FOCUS_TICKS){
            if(g->beam_wait[i])--g->beam_wait[i];
            if(!g->beam_wait[i]){pulse[i]=1;g->beam_wait[i]=MF_WS_BEAM_TICKS;}
        }else {g->beam_wait[i]=0;if((p->shot_hold==1 || (edge&MF_A)) && !p->cooldown && player_fire(g,p,i))p->cooldown=MF_WS_FIRE_TICKS;}
    }
    spawn_enemies(g);
    for(i=0;i<MF_WS_ENEMIES;i++){
        mf_ws_enemy *e=&g->enemies[i];if(e->explosion)--e->explosion;
        if(!e->active)continue;
        if(e->delay){--e->delay;continue;}
        ++e->age;
        move_enemy(e);
        if(e->kind==MF_WS_DRONE && e->age==80)aimed_snapshot(g,e->x,e->y+10*S);
        if(e->y>256*S)e->active=0;
    }
    for(i=0;i<2;i++)if(pulse[i])for(j=0;j<MF_WS_ENEMIES;j++){
        mf_ws_player *p=&g->players[i];mf_ws_enemy *e=&g->enemies[j];
        if(e->active && !e->delay && e->x>=p->x-(MF_WS_BEAM_HALF_WIDTH+(e->kind==MF_WS_CHROME_EYE?6:10))*S && e->x<=p->x+(MF_WS_BEAM_HALF_WIDTH+(e->kind==MF_WS_CHROME_EYE?6:10))*S &&
           e->y+10*S>=MF_WS_BEAM_TOP*S && e->y-10*S<=p->y-MF_WS_BEAM_EMITTER*S){
            e->active=0;e->explosion=12;p->score+=100;++g->deaths;
        }
    }
    for(i=0;i<MF_WS_SHOTS;i++){
        mf_ws_shot *s=&g->shots[i];if(!s->active)continue;
        s->x+=s->vx;s->y-=6*S;
        if(--s->ttl<=0 || s->y < -8*S || s->x<4*S || s->x>(MF_WS_STAGE_WIDTH-4)*S){s->active=0;continue;}
        for(j=0;j<MF_WS_ENEMIES;j++){
            mf_ws_enemy *e=&g->enemies[j];if(e->active && near(s->x,s->y,e->x,e->y,e->kind==MF_WS_CHROME_EYE?7:12,e->kind==MF_WS_CHROME_EYE?7:13)){
                e->active=0;e->explosion=12;++g->deaths;s->active=0;g->players[s->owner].score+=100;break;
            }
        }
    }
    for(i=0;i<MF_WS_HOSTILE;i++){
        mf_ws_hostile_shot *s=&g->hostile[i];if(!s->active)continue;
        s->x+=s->vx;s->y+=s->vy;
        if(--s->ttl<=0 || s->x< -4*S || s->x>(MF_WS_STAGE_WIDTH+4)*S || s->y < -8*S || s->y>248*S){s->active=0;continue;}
        for(j=0;j<2;j++){
            mf_ws_player *p=&g->players[j];if(p->active && p->lives && !p->respawn && near(s->x,s->y,p->x,p->y,7,10)){
                g->deaths+=damage(p,j);s->active=0;break;
            }
        }
    }
    for(i=0;i<2;i++){
        mf_ws_player *p=&g->players[i];if(!p->active || p->lives<=0)continue;
        alive=1;if(p->respawn)continue;
        for(j=0;j<MF_WS_ENEMIES;j++)if(g->enemies[j].active && near(p->x,p->y,g->enemies[j].x,g->enemies[j].y,g->enemies[j].kind==MF_WS_CHROME_EYE?10:15,g->enemies[j].kind==MF_WS_CHROME_EYE?13:18))g->deaths+=damage(p,i);
    }
    g->game_over=!alive;
}
