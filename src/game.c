#include "game.h"
/* JAB BEGIN */
#include "punch_combo.h"
#include "jab_repeat.h"
/* JAB END */
/* MOMENTUM BEGIN */
#include "bat_momentum_config.h"
/* MOMENTUM END */
static int clamp(int n,int lo,int hi) { return n<lo?lo:(n>hi?hi:n); }
static int abs_i(int n) { return n<0?-n:n; }
static int sign(int n) { return n<0?-1:(n>0?1:0); }
#if MF_DASH_ENABLED
static void dash_clear(mf_dash_state *d)
{
    d->dir=d->tap_dir=d->window=d->released=d->ready=d->anim=0;
}
static void dash_input(mf_game *g,int index,unsigned held,unsigned pressed,int live,int connected)
{
    mf_player *p=&g->players[index];mf_dash_state *d=&g->dash[index];
    int punching=MF_FAST_RUNNING_BAT && p->attack && !p->bat && !p->attack_air;
    unsigned h=held&(MF_LEFT|MF_RIGHT),edge=(pressed&h)&~d->previous;
    int dir=h==MF_RIGHT?1:h==MF_LEFT?-1:0;
    d->previous=h;
    if(!live || !connected || !p->active || !p->health || p->hurt || (p->attack && !punching) ||
       p->height || p->vz || p->landing || p->torch || (p->charge && !punching) ||
       ((pressed|p->buffered)&(punching?MF_B:(MF_A|MF_B))) || h==(MF_LEFT|MF_RIGHT)) {
        dash_clear(d);return;
    }
    /* Hit-stop freezes an established dash. Punch command recognition may
       continue without starting dash movement or advancing the attack. */
    if(g->hitstop && !punching) {
        if(d->dir && d->dir==dir)return;
        dash_clear(d);return;
    }
    /* Require fresh horizontal neutral after menus, combat, landing or recovery.
       Edges arriving on the transition itself cannot arm a stale first tap. */
    if(!d->ready) {if(!h)d->ready=1;return;}
    /* released==2 is a completed FF held during a punch, not movement dash. */
    if(d->released==2){
        if(dir==d->tap_dir){if(!punching){d->dir=dir;d->tap_dir=d->released=0;d->anim=-MF_DASH_ANIM_NUM;}return;}
        dash_clear(d);if(!h)d->ready=1;return;
    }
    if(d->window)--d->window;
    if(d->dir) {
        if(d->dir==dir)return;
        d->dir=d->tap_dir=d->window=d->released=d->anim=0;
    }
    if(!h) {if(d->window)d->released=1;return;}
    if(!edge)return;
    if(d->tap_dir==dir && d->window && d->released) {
        if(punching){d->released=2;d->window=0;return;}
        d->dir=dir;d->tap_dir=d->window=d->released=0;
#if MF_RUN_BAT
        d->anim=-MF_DASH_ANIM_NUM;
#else
        d->anim=(p->walk%(3*MF_DASH_BASE_HOLD))*MF_DASH_ANIM_DEN;
#endif
    }else {
        d->tap_dir=dir;d->window=MF_DASH_TAP_TICKS+1;d->released=0;
    }
}
#endif
static void torch_cancel(mf_player *p)
{
    p->torch=p->charge=p->torch_timer=p->torch_tick=p->torch_sound=0;
    p->a_blocked=1;p->buffered&=~MF_A;
}
int mf_boxes_overlap(mf_hitbox a,mf_hitbox b)
{
    return a.left<=b.right && a.right>=b.left && a.back<=b.front &&
        a.front>=b.back && a.bottom<=b.top && a.top>=b.bottom;
}
static mf_hitbox hurtbox(int x,int y,int height,int half,int depth,int tall)
{
    mf_hitbox b={x-half,x+half,y-depth,y+depth,height+4,height+tall}; return b;
}
static mf_hitbox attackbox(int x,int y,int h,int facing,int near,int far,int low,int high)
{
    mf_hitbox b={x+(facing>0?near:-far),x+(facing>0?far:-near),y-8,y+8,h+low,h+high}; return b;
}
mf_hitbox mf_player_hurtbox(const mf_player *p) { return hurtbox(p->x/256,p->y/256,p->height/256,12,8,84); }
mf_hitbox mf_enemy_hurtbox(const mf_enemy *e) { return hurtbox(e->x/256,e->y/256,0,13,8,84); }
mf_hitbox mf_player_attackbox(const mf_player *p)
{
    if(p->bat){
#if MF_FAST_RUNNING_BAT
        if(p->bat==MF_BAT_RUNNING)
            return attackbox(p->x/256,p->y/256,0,p->facing,6,MF_BAT_REACH,30,64);
#endif
        /* Rising screen arc: low outward sweep -> chest contact -> high lift.
           Air height translates this same volume; ground depth stays separate. */
        int low=p->attack<14?14:(p->attack<17?40:54);
        int high=p->attack<14?58:(p->attack<17?64:90);
        return attackbox(p->x/256,p->y/256,p->height/256,p->facing,6,MF_BAT_REACH,low,high);
    }
    return attackbox(p->x/256,p->y/256,p->height/256,p->facing,6,p->attack_air?54:52,p->attack_air?24:30,p->attack_air?45:58);
}
mf_hitbox mf_enemy_attackbox(const mf_enemy *e) { return attackbox(e->x/256,e->y/256,0,e->facing,8,40,36,64); }
static int player_active(const mf_player *p)
{
#if MF_FAST_RUNNING_BAT
    if(p->bat==MF_BAT_RUNNING)return p->active && p->health>0 && !p->hurt &&
        !p->height && !p->vz && !p->attack_air &&
        p->attack>=MF_FAST_BAT_ACTIVE_FIRST && p->attack<=MF_FAST_BAT_ACTIVE_LAST;
#endif
    if(p->bat)return p->active && p->health>0 && !p->hurt &&
        (p->attack_air?p->height>0:!p->height) &&
        p->attack>=MF_BAT_ACTIVE_FIRST && p->attack<=MF_BAT_ACTIVE_LAST;
    return p->active && p->health>0 && !p->hurt && p->attack && p->attack>=(p->attack_air?3:6) && p->attack<=(p->attack_air?15:10);
}
static void impact(mf_game *g,int x,int y,int z)
{
    g->hitstop=MF_HIT_STOP_TICKS;g->spark=8;g->spark_x=x;g->spark_y=y;g->spark_z=z;g->events|=MF_IMPACT;
}
static void drum_reset(mf_drum *d,int i)
{
    static const int xs[3]={260,425,565},ys[3]={199,176,218};
    *d=(mf_drum){0};d->x=xs[i]*256;d->y=ys[i]*256;d->hp=3;
}
static int living(const mf_player *p) {return p->active && p->health>0;}
static unsigned punk_roll(mf_punk_ai *a)
{
    a->rng=a->rng*1664525u+1013904223u;return a->rng;
}
static void enemy_spawn(mf_game *g,int index,int initial)
{
    mf_enemy *e=&g->enemies[index];int i,left=10000,right=10000,y=178;
    for(i=0;i<MF_PLAYERS;i++) if(living(&g->players[i])) {
        int x=g->players[i].x/256;
        if(x-26<left)left=x-26;
        if(614-x<right)right=614-x;
        y=g->players[i].y>200*256?178:218;
    }
#if MF_LEVEL1_STAGE_CLEAR
    (void)initial;
    /* Score candidate screen/street boundaries against BOTH players and the
       other slot. Never teleport into a player's attack/reaction space. */
    {
        static const int lanes[4]={168,188,209,229};
        int n,best=-1,bx=0,by=0;
        for(n=0;n<12;n++) {
            int x,cy,quality=10000,k;
            unsigned pick=g->spawn_rng=g->spawn_rng*1664525u+1013904223u;
            cy=lanes[(pick>>16)&3];
            if(n<8)x=clamp(g->camera+((n&1)?344:-24),26,614);
            else {x=clamp(g->camera+48+(int)((pick>>8)%225u),26,614);cy=(n&1)?229:168;}
            for(k=0;k<MF_PLAYERS;k++)if(living(&g->players[k])) {
                int dx=abs_i(x-g->players[k].x/256),dy=abs_i(cy-g->players[k].y/256);
                int d=dx+2*dy;
                if(dx<80 && dy<40)d=0;
                if(d<quality)quality=d;
            }
            for(k=0;k<MF_ENEMIES;k++)if(k!=index && g->enemies[k].state!=MF_ENEMY_ABSENT) {
                int d=abs_i(x-g->enemies[k].x/256)+2*abs_i(cy-g->enemies[k].y/256);
                if(d<48)quality=0;
            }
            if(quality>best){best=quality;bx=x;by=cy;}
        }
        if(best<110)return; /* Retry later; fairness wins over a deadline. */
        left=bx;right=by;
    }
#endif
    {
        mf_punk_ai *a=&g->punk[index],*other=&g->punk[1-index];
        unsigned seed=a->rng?a->rng:(0x50554e4bu^(unsigned)(index*7919));
        *a=(mf_punk_ai){0};a->rng=seed;
        a->behavior=(int)((punk_roll(a)>>16)&3u);
        if(g->enemies[1-index].state!=MF_ENEMY_ABSENT && a->behavior==other->behavior)
            a->behavior=(a->behavior+1)&3;
        a->lane=(a->rng&256u)?1:-1;
        if(g->enemies[1-index].state!=MF_ENEMY_ABSENT && other->lane)a->lane=-other->lane;
    }
    g->enemy_class[index]=MF_ENEMY_CORPORATE_PUNK;
#if MF_RICKY_ENEMY
    /* Two CP, mixed, then two Ricky are possible without consuming spawn_rng. */
    g->ricky_punch[index]=0;
    if((g->ricky_spawns++%8u)>=5u)g->enemy_class[index]=MF_ENEMY_RICKY;
#endif
    *e=(mf_enemy){0};e->x=(initial?(index?530:390):(right>=left?614:26))*256;
    e->y=(index?218:y)*256;e->hp=MF_ENEMY_MAX_HP;e->facing=g->players[0].x<e->x?-1:1;
    e->state=MF_ENEMY_IDLE;e->grace=MF_ENEMY_SPAWN_GRACE+index*30;e->target=-1;
#if MF_LEVEL1_STAGE_CLEAR
    e->x=left*256;e->y=right*256;e->grace=MF_ENEMY_SPAWN_GRACE;
    e->facing=g->players[0].x<e->x?-1:1;
#endif
}
static void recover_player(mf_game *g,int index,int joining)
{
    mf_player *p=&g->players[index],*other=&g->players[1-index];
    int x=100+index*44,y=202;
    if((joining || g->players[1].active) && living(other)) {x=clamp(other->x/256+(index?40:-40),26,614);y=other->y/256;}
    if(joining) {
        int lo=clamp(g->camera+32,26,614),hi=clamp(g->camera+288,26,614);
        if(x>hi && living(other))x=other->x/256-40;
        x=clamp(x,lo,hi);
        if(living(other))y=clamp(other->y/256+(other->y>200*256?-20:20),168,229);
    }
#if MF_PUNCH_COMBO
    mf_combo_reset(g,index);
#endif
    g->dash[index]=(mf_dash_state){0};
    g->running_bat[index]=(mf_running_bat){0};
    *p=(mf_player){0};p->active=1;p->health=100;p->x=x*256;p->y=y*256;
    p->facing=1;p->invulnerable=120;p->a_blocked=1;
    /* Recovery never resets another player, an enemy, barrels or the score. */
}
void mf_game_init(mf_game *g)
{
    int i;*g=(mf_game){0};recover_player(g,0,0);g->players[0].invulnerable=0;
    for(i=0;i<MF_DRUMS;i++)drum_reset(&g->drums[i],i);
#if MF_LEVEL1_STAGE_CLEAR
    g->spawn_rng=0x4d554c4cu;g->spawn_wait=60;
    for(i=0;i<MF_ENEMIES;i++)g->enemies[i].state=MF_ENEMY_ABSENT;
#else
    for(i=0;i<MF_ENEMIES;i++)enemy_spawn(g,i,1);
#endif
}
#if MF_LEVEL1_STAGE_CLEAR
static void stage_defeat(mf_game *g,int index)
{
    /* Called only at the live-HP -> DYING edge, never from despawn/respawn. */
    if(g->stage!=MF_STAGE_LEVEL1 || (g->enemy_class[index]!=MF_ENEMY_CORPORATE_PUNK
#if MF_RICKY_ENEMY
        && g->enemy_class[index]!=MF_ENEMY_RICKY
#endif
        ))return;
    if(++g->stage_kills==MF_STAGE_KILL_TARGET) {
        g->stage=MF_STAGE_SETTLING;g->stage_timer=MF_STAGE_SETTLE_TICKS;
        g->spawn_wait=g->spawn_pair=0;
    }
}
static void stage_spawns(mf_game *g)
{
    static const int low[4]={90,66,45,30},span[4]={61,55,46,37},pairs[4]={25,40,50,65};
    int i,phase=clamp(g->stage_kills/10,0,3),free_slots=0;
    unsigned roll;
    if(g->stage!=MF_STAGE_LEVEL1)return;
    if(g->spawn_wait>0 && --g->spawn_wait>0)return;
    for(i=0;i<MF_ENEMIES;i++)if(g->enemies[i].state==MF_ENEMY_ABSENT)++free_slots;
    if(!free_slots)return;
    for(i=0;i<MF_ENEMIES;i++)if(g->enemies[i].state==MF_ENEMY_ABSENT)break;
    enemy_spawn(g,i,0);
    if(g->enemies[i].state==MF_ENEMY_ABSENT){g->spawn_wait=15;return;}
    roll=g->spawn_rng=g->spawn_rng*1664525u+1013904223u;
    if(!g->spawn_pair && free_slots==2 && (int)((roll>>8)%100u)<pairs[phase]) {
        g->spawn_pair=1;g->spawn_wait=18+(int)((roll>>16)%19u);
    }else {
        g->spawn_pair=0;g->spawn_wait=low[phase]+(int)((roll>>16)%(unsigned)span[phase]);
    }
}
#endif
static void choose_target(mf_game *g,mf_enemy *e,int index)
{
    int i,best=-1,cost=0;
    if(e->target_lock>0)--e->target_lock;
    if(e->target>=0 && living(&g->players[e->target]) && e->target_lock)return;
    for(i=0;i<MF_PLAYERS;i++) if(living(&g->players[i])) {
        int d=abs_i(g->players[i].x-e->x)+2*abs_i(g->players[i].y-e->y);
        /* Prefer distributing attackers, but never cross the whole street
           solely to claim a different target. Stable ties favor enemy index. */
        mf_enemy *other=&g->enemies[1-index];
        if(other->hp>0 && other->target==i)d+=64*256;
        if(best<0 || d<cost || (d==cost && i==index)){best=i;cost=d;}
    }
    e->target=best;e->target_lock=120;
}
/* Audio only: all callers resolve damage before dispatching the result.
   Incoming hits use the victim's port, replacing any interrupted attack. */
static void hit_sound(mf_game *g,int actor,int health,int inorganic)
{
    if(inorganic && health<=0)g->events|=MF_WORLD_IMPACT|MF_COMBAT_DESTROY(actor);
    else g->events|=health>0?MF_COMBAT_NONKILL(actor):MF_COMBAT_CONNECT(actor);
}
static void fire_damage(mf_game *g,mf_enemy *e,int ignite,int owner)
{
#if MF_LEVEL1_STAGE_CLEAR
    if(g->stage!=MF_STAGE_LEVEL1)return;
#endif
    if(e->hp<=0 || e->state==MF_ENEMY_ABSENT || e->state==MF_ENEMY_DYING)return;
    if(ignite)g->burn_owner[e-g->enemies]=owner;
    e->hp=clamp(e->hp-(ignite?MF_TORCH_DAMAGE:MF_BURN_DAMAGE),0,MF_ENEMY_MAX_HP);e->fire_flash=4;
    hit_sound(g,owner,e->hp,0);
    if(ignite){if(!e->burn)e->burn_clock=MF_BURN_DAMAGE_TICKS;e->burn=MF_BURN_TICKS;}
    if(!e->hp){
        e->state=MF_ENEMY_DYING;e->timer=30;e->vx=0;e->burn=e->burn_clock=0;
        g->score+=MF_ENEMY_DEFEAT_SCORE;g->events|=MF_IMPACT;
#if MF_LEVEL1_STAGE_CLEAR
        stage_defeat(g,(int)(e-g->enemies));
#endif
    }
    /* No recurring HURT state: a living enemy can escape or interrupt fire. */
}
/* One legal attack gate for every approach, rush and counter. */
static int punk_attack(mf_game *g,int index)
{
    mf_enemy *e=&g->enemies[index];mf_punk_ai *a=&g->punk[index];
    mf_player *p=&g->players[e->target];int dx=p->x-e->x,dy=p->y-e->y;
    if(dx)e->facing=sign(dx);
    if(e->grace || !dx || abs_i(dx)>44*256 || abs_i(dy)>9*256)return 0;
    e->state=MF_ENEMY_WINDUP;e->timer=a->punches>=MF_PUNK_COUNTER_THRESHOLD?
        MF_PUNK_COUNTER_WINDUP_TICKS:MF_PUNK_WINDUP_TICKS;e->hit_done=0;
    a->phase=MF_PUNK_CLOSE;a->clock=0;return 1;
}
static void punk_pursue(mf_game *g,int index)
{
    mf_enemy *e=&g->enemies[index],*other=&g->enemies[1-index];
    mf_player *p=&g->players[e->target];mf_punk_ai *a=&g->punk[index];
    int dx=p->x-e->x,dy=p->y-e->y,tx=p->x,ty=p->y,sx=MF_PUNK_WALK_X,sy=MF_PUNK_WALK_Y;
    int lane=a->lane?a->lane:(index?1:-1),engaged=p->attack ||
        (other->target==e->target && (other->state==MF_ENEMY_WINDUP || other->state==MF_ENEMY_ACTIVE));
    if(a->phase==MF_PUNK_RUSH){
        /* Fixed direction captured after preparation: dodgeable, not homing. */
        e->x+=a->burst_x*(sx*MF_PUNK_RUSH_NUM/MF_PUNK_RUSH_DEN);
        e->y+=a->burst_y*(sy*MF_PUNK_RUSH_NUM/MF_PUNK_RUSH_DEN);
        if(--a->clock<=0)a->phase=MF_PUNK_CLOSE;
    }else{
        if(++a->age>=MF_PUNK_APPROACH_LIMIT)a->phase=MF_PUNK_CLOSE;
        /* A moving target cannot trap an enemy in an offset orbit forever. */
        if(abs_i(dx)>160*256 && a->age==40+(int)((a->rng>>8)%25u))a->lane=lane=-lane;
        if(clamp(p->y/256+lane*MF_PUNK_LANE,168,229)-p->y/256<12 && lane>0)lane=-1;
        if(p->y/256-clamp(p->y/256+lane*MF_PUNK_LANE,168,229)<12 && lane<0)lane=1;
        a->lane=lane;
        if(a->phase==MF_PUNK_APPROACH){
            if(a->behavior==MF_PUNK_OPPORTUNIST){
                if(!a->side)a->side=-p->facing;
                if((e->x-p->x)*a->side>=(engaged?24:40)*256)a->phase=MF_PUNK_CLOSE;
                else tx=clamp(p->x+a->side*(engaged?56:72)*256,26*256,614*256);
            }
            if(a->behavior!=MF_PUNK_BRAWLER && a->phase!=MF_PUNK_CLOSE)
                ty=clamp(p->y+lane*MF_PUNK_LANE*256,168*256,229*256);
            if(a->behavior==MF_PUNK_FLANKER && abs_i(dx)<=76*256)a->phase=MF_PUNK_CLOSE;
            if(a->behavior==MF_PUNK_AMBUSHER && abs_i(dx)<=120*256)a->phase=MF_PUNK_CLOSE;
            if(a->phase==MF_PUNK_CLOSE){
                tx=p->x;ty=p->y;
                if(abs_i(dx)>12*256 && abs_i(dy)>9*256 && !e->grace){
                    unsigned pick=punk_roll(a);
                    a->phase=MF_PUNK_PREP;e->state=MF_ENEMY_WINDUP;
                    e->timer=a->behavior==MF_PUNK_AMBUSHER?8+(int)((pick>>16)%3u):6;
                    return; /* Existing ready pose; this state cannot damage. */
                }
                a->phase=MF_PUNK_CLOSE;
            }
        }
        if(a->phase==MF_PUNK_CLOSE){tx=p->x;ty=p->y;}
        /* Small opposite depth aims reduce stacking without body collision.
           Legal attacks are checked before this optional pursuit steering. */
        if(abs_i(e->x-other->x)<18*256 && abs_i(e->y-other->y)<10*256 &&
           other->state!=MF_ENEMY_ABSENT && other->state!=MF_ENEMY_DYING)
            ty=clamp(ty+lane*6*256,168*256,229*256);
        dx=tx-e->x;dy=ty-e->y;
        /* Separate coincident roots so facing/contact cannot deadlock. */
        if(!dx){
            int side=p->x<56*256?1:p->x>584*256?-1:(index?1:-1);
            e->x+=side*sx;
        }
        if(abs_i(dx)>30*256)e->x+=sign(dx)*sx;
        else if(a->behavior==MF_PUNK_OPPORTUNIST && a->phase==MF_PUNK_APPROACH && abs_i(dx)>2*256)
            e->x+=sign(dx)*sx;
        /* Scale depth velocity to the approach vector instead of settling Y
           long before X. All arithmetic is bounded by the 588px playfield. */
        if(abs_i(dy)>3*256){
            int divisor=abs_i(dx)>abs_i(dy)?abs_i(dx):abs_i(dy);
            int step=clamp(dy*sx/divisor,-sy,sy);
            e->y+=step;
        }
    }
    e->state=MF_ENEMY_WALK;++e->walk;
    e->x=clamp(e->x,26*256,614*256);e->y=clamp(e->y,168*256,229*256);
}
#if MF_RICKY_ENEMY
/* Independent Ricky controller. Shared burn/hurt/death processing runs first.
   Attack direction is captured at commitment; neither windup nor recovery hits. */
static void ricky_step(mf_game *g,int index)
{
    mf_enemy *e=&g->enemies[index];mf_player *p;int dx,dy,i;
    if(e->state==MF_ENEMY_WINDUP) {
        if(--e->timer>0)return;
        e->state=MF_ENEMY_ACTIVE;e->timer=g->ricky_punch[index]?3:4;
        g->events|=MF_SWOOSH;
    }
    if(e->state==MF_ENEMY_ACTIVE) {
        for(i=0;i<MF_PLAYERS;i++){
            p=&g->players[i];
            if(!(e->hit_done&(1<<i)) && living(p) && !p->invulnerable && (p->x-e->x)*e->facing>0 &&
               mf_boxes_overlap(attackbox(e->x/256,e->y/256,0,e->facing,10,g->ricky_punch[index]?40:82,36,64),mf_player_hurtbox(p))){
                e->hit_done|=1<<i;p->health=clamp(p->health-MF_ENEMY_DAMAGE,0,100);
#if MF_DASH_ENABLED
                dash_clear(&g->dash[i]);
#endif
                g->running_bat[i]=(mf_running_bat){0};
/* JAB BEGIN */
#if MF_JAB_COHESION
                g->jab[i].buffer=0;
#endif
/* JAB END */
                p->invulnerable=MF_BUCK_INVULNERABLE_TICKS;p->hurt=12;p->knockback=e->facing*650;
                p->attack=p->bat=0;p->buffered=0;torch_cancel(p);impact(g,p->x/256,p->y/256,48+p->height/256);hit_sound(g,i,p->health,0);g->events|=MF_COMBAT_HURT(i);
                if(!p->health)p->defeated=MF_BUCK_RECOVERY_TICKS;
            }
        }
        if(--e->timer<=0){e->state=MF_ENEMY_RECOVER;e->timer=24;}
        return;
    }
    if(e->state==MF_ENEMY_RECOVER){if(--e->timer>0)return;e->state=MF_ENEMY_IDLE;}
    choose_target(g,e,index);if(e->target<0){e->state=MF_ENEMY_IDLE;return;}
    p=&g->players[e->target];dx=p->x-e->x;dy=p->y-e->y;
    if(dx)e->facing=sign(dx);
    if(dx && abs_i(dx)<=76*256 && abs_i(dy)<=9*256) {
        e->state=MF_ENEMY_IDLE;
        if(!e->grace) {
            g->ricky_punch[index]=abs_i(dx)<=36*256;
            e->state=MF_ENEMY_WINDUP;e->timer=g->ricky_punch[index]?12:22;
            e->hit_done=0;
        }
        return;
    }
    e->state=MF_ENEMY_WALK;++e->walk;
    if(abs_i(dx)>32*256)e->x+=sign(dx)*240;
    else if(!dx)e->x+=(index?1:-1)*240;
    if(abs_i(dy)>3*256) {
        int divisor=abs_i(dx)>abs_i(dy)?abs_i(dx):abs_i(dy);
        e->y+=clamp(dy*240/divisor,-170,170);
    }
    e->x=clamp(e->x,26*256,614*256);e->y=clamp(e->y,168*256,229*256);
}
#endif
static void enemy_step(mf_game *g,int index)
{
    mf_enemy *e=&g->enemies[index];mf_player *p;int dx,dy,i;
#if MF_LEVEL1_STAGE_CLEAR
    if(g->stage!=MF_STAGE_LEVEL1 && e->state!=MF_ENEMY_DYING)return;
#endif
    /* Count simulation ticks, including hurt/recovery, but excluding hit-stop.
       Disengagement cannot bank a counter indefinitely. */
    if(g->punk[index].expiry && --g->punk[index].expiry==0)g->punk[index].punches=0;
    if(e->state==MF_ENEMY_ABSENT || e->state==MF_ENEMY_DYING)
        g->punk[index].punches=g->punk[index].expiry=0;
    if(e->fire_flash)--e->fire_flash;
    if(e->burn && e->hp>0){
        --e->burn;if(e->burn_clock>0 && --e->burn_clock==0){fire_damage(g,e,0,g->burn_owner[index]);e->burn_clock=MF_BURN_DAMAGE_TICKS;}
        if(!e->burn)e->burn_clock=0;
    }
    if(e->state==MF_ENEMY_ABSENT){
#if !MF_LEVEL1_STAGE_CLEAR
        if(e->timer>0 && --e->timer==0)enemy_spawn(g,index,0);
#endif
        return;
    }
    if(e->flash)--e->flash;
    if(e->state==MF_ENEMY_DYING){
        e->x=clamp(e->x+e->vx,26*256,614*256);e->vx=e->vx*3/4;
        if(--e->timer<=0){e->state=MF_ENEMY_ABSENT;e->timer=MF_ENEMY_RESPAWN_TICKS;}return;
    }
    if(e->grace)--e->grace;
    if(e->state==MF_ENEMY_HURT){
        g->punk[index].phase=MF_PUNK_CLOSE;g->punk[index].clock=0;
        e->x=clamp(e->x+e->vx,26*256,614*256);e->vx=e->vx*7/8;
        if(--e->timer<=0){e->state=MF_ENEMY_RECOVER;e->timer=g->enemy_class[index]==MF_ENEMY_CORPORATE_PUNK?
            (g->punk[index].punches>=MF_PUNK_COUNTER_THRESHOLD?MF_PUNK_COUNTER_RECOVERY:
             g->punk[index].punches>=MF_PUNK_PRESSURE_BUILD?MF_PUNK_PRESSURE_RECOVERY:MF_PUNK_NORMAL_RECOVERY):24;}return;
    }
#if MF_RICKY_ENEMY
    if(g->enemy_class[index]==MF_ENEMY_RICKY){ricky_step(g,index);return;}
#endif
    if(e->state==MF_ENEMY_WINDUP && g->punk[index].phase==MF_PUNK_PREP){
        choose_target(g,e,index);
        if(e->target<0){e->state=MF_ENEMY_IDLE;g->punk[index].phase=MF_PUNK_APPROACH;return;}
        if(punk_attack(g,index))return; /* Legal opening overrides movement prep. */
        if(--e->timer<=0){
            p=&g->players[e->target];
            g->punk[index].phase=MF_PUNK_RUSH;g->punk[index].clock=10+(int)((punk_roll(&g->punk[index])>>16)%9u);
            g->punk[index].burst_x=sign(p->x-e->x);g->punk[index].burst_y=sign(p->y-e->y);
            e->state=MF_ENEMY_WALK;
        }
        return;
    }
    if(e->state==MF_ENEMY_WINDUP && --e->timer<=0){e->state=MF_ENEMY_ACTIVE;e->timer=MF_ENEMY_ACTIVE_TICKS;g->events|=MF_SWOOSH;}
    if(e->state==MF_ENEMY_ACTIVE){
        for(i=0;i<MF_PLAYERS;i++){
            p=&g->players[i];
            if(!(e->hit_done&(1<<i)) && living(p) && !p->invulnerable && (p->x-e->x)*e->facing>0 &&
               mf_boxes_overlap(mf_enemy_attackbox(e),mf_player_hurtbox(p))){
                e->hit_done|=1<<i;p->health=clamp(p->health-MF_ENEMY_DAMAGE,0,100);
#if MF_DASH_ENABLED
                dash_clear(&g->dash[i]);
#endif
                g->running_bat[i]=(mf_running_bat){0};
/* JAB BEGIN */
#if MF_JAB_COHESION
                g->jab[i].buffer=0;
#endif
/* JAB END */
                p->invulnerable=MF_BUCK_INVULNERABLE_TICKS;p->hurt=12;p->knockback=e->facing*650;
                p->attack=p->bat=0;p->buffered=0;torch_cancel(p);impact(g,p->x/256,p->y/256,48+p->height/256);hit_sound(g,i,p->health,0);g->events|=MF_COMBAT_HURT(i);
                if(!p->health)p->defeated=MF_BUCK_RECOVERY_TICKS;
            }
        }
        if(--e->timer<=0){e->state=MF_ENEMY_RECOVER;
            e->timer=g->enemy_class[index]==MF_ENEMY_CORPORATE_PUNK?MF_PUNK_ATTACK_RECOVERY+index*6:MF_ENEMY_RECOVERY_TICKS+index*12;
            g->punk[index].phase=MF_PUNK_APPROACH;g->punk[index].age=0;g->punk[index].side=0;
            g->punk[index].lane=(punk_roll(&g->punk[index])&256u)?1:-1;
        }return;
    }
    if(e->state==MF_ENEMY_WINDUP)return;
    if(e->state==MF_ENEMY_RECOVER){if(--e->timer>0)return;e->state=MF_ENEMY_IDLE;
        if(g->enemy_class[index]!=MF_ENEMY_CORPORATE_PUNK)return;
    }
    choose_target(g,e,index);if(e->target<0){e->state=MF_ENEMY_IDLE;return;}
    p=&g->players[e->target];dx=p->x-e->x;dy=p->y-e->y;
    if(dx)e->facing=sign(dx);
    if(g->enemy_class[index]==MF_ENEMY_CORPORATE_PUNK){
        if(punk_attack(g,index))return;
        if(e->grace && dx && abs_i(dx)<=44*256 && abs_i(dy)<=9*256){e->state=MF_ENEMY_IDLE;return;}
        punk_pursue(g,index);return;
    }
    if(abs_i(dx)<=44*256 && abs_i(dy)<=9*256){
        e->state=MF_ENEMY_IDLE;
        /* Both existing slots may commit independently. Shared per-player
           invulnerability still resolves simultaneous contact only once. */
        if(!e->grace){
            e->state=MF_ENEMY_WINDUP;
            e->timer=g->enemy_class[index]==MF_ENEMY_CORPORATE_PUNK?
                (g->punk[index].punches>=MF_PUNK_COUNTER_THRESHOLD?MF_PUNK_COUNTER_WINDUP_TICKS:MF_PUNK_WINDUP_TICKS):MF_ENEMY_WINDUP_TICKS;
            e->hit_done=0;
        }
    }else{
        e->state=MF_ENEMY_WALK;++e->walk;
        if(abs_i(dx)>40*256)e->x+=sign(dx)*220;
        if(abs_i(dy)>4*256)e->y+=sign(dy)*150;
        e->x=clamp(e->x,26*256,614*256);e->y=clamp(e->y,168*256,229*256);
    }
}
static void clear_gesture(mf_player *p){p->combo_dir=p->tap_window=p->bat_window=0;}
static void gesture_step(mf_player *p,unsigned held,unsigned pressed)
{
    unsigned directions=held&(MF_LEFT|MF_RIGHT);
    unsigned edges=pressed&(MF_LEFT|MF_RIGHT)&~p->previous_directions;
    int dir=edges==MF_RIGHT?1:edges==MF_LEFT?-1:0;
    p->previous_directions=directions;
    if(p->tap_window)--p->tap_window;
    if(p->bat_window)--p->bat_window;
    if(!p->active || !p->health || p->hurt || p->attack ||
       (p->torch && p->torch!=MF_TORCH_AWAY && (held&MF_A)) ||
#if MF_FAST_RUNNING_BAT
       p->height || p->vz ||
#else
       ((p->height || p->vz) && p->air_bat_used) ||
#endif
       (pressed&MF_B) || directions==(MF_LEFT|MF_RIGHT) ||
       (p->combo_dir && p->facing!=p->combo_dir)){
        clear_gesture(p);return;
    }
    if(!dir)return;
    if(dir!=p->facing){clear_gesture(p);return;}
    if(p->bat_window && p->combo_dir==dir)return; /* No third-tap extension. */
    if(p->tap_window && p->combo_dir==dir){
        p->tap_window=0;p->bat_window=MF_BAT_ATTACK_TICKS+1;
    }else{p->combo_dir=dir;p->tap_window=MF_BAT_TAP_TICKS+1;p->bat_window=0;}
}
static void torch_input(mf_player *p,unsigned held,unsigned pressed,int connected)
{
    p->torch_sound=0;
    if(!connected || !p->active || !p->health || p->hurt || p->height || p->vz){
        torch_cancel(p);
        if(connected && p->active && p->health>0 && !(held&MF_A))p->a_blocked=0;
        return;
    }
    if(!(held&MF_A)){
        p->charge=0;p->a_blocked=0;
        if(p->torch==MF_TORCH_EQUIP || p->torch==MF_TORCH_FIRE){p->torch=MF_TORCH_AWAY;p->torch_timer=MF_TORCH_AWAY_TICKS;}
    }
    if(p->torch==MF_TORCH_AWAY){
        if(((pressed&MF_A) && !p->a_blocked) || (pressed&MF_B))p->torch=0;
        else {if(--p->torch_timer<=0)p->torch=0;return;}
    }
    if(p->torch==MF_TORCH_EQUIP){if(--p->torch_timer<=0){p->torch=MF_TORCH_FIRE;p->torch_tick=0;}return;}
    if(p->torch==MF_TORCH_FIRE)return;
    if((pressed&MF_B) || p->bat || ((pressed&MF_A) && p->bat_window && p->combo_dir==p->facing)){
        p->charge=0;p->a_blocked=1;return;
    }
    if(p->a_blocked || !(held&MF_A))return;
    if((pressed&MF_A) && !p->charge)p->charge=1;
    else if(p->charge>0)++p->charge;
    if(p->charge>=MF_TORCH_CHARGE_TICKS){
        /* Sample this tick's facing before player movement: no equip delay. */
        if((held&(MF_LEFT|MF_RIGHT))==MF_LEFT)p->facing=-1;
        else if((held&(MF_LEFT|MF_RIGHT))==MF_RIGHT)p->facing=1;
        p->torch=MF_TORCH_FIRE;p->torch_timer=0;p->torch_tick=0;
        p->charge=0;p->a_blocked=1;p->torch_sound=1;p->attack=p->bat=p->attack_air=0;clear_gesture(p);
    }
}
static void torch_events(mf_game *g)
{
    int i;for(i=0;i<MF_PLAYERS;i++){
        mf_player *p=&g->players[i];
        if(p->torch==MF_TORCH_FIRE)g->events|=MF_TORCH_HISS;
        if(p->torch_sound && p->torch)g->events|=MF_TORCH_IGNITE;
    }
}
int mf_torch_hits(const mf_player *p,mf_hitbox b)
{
    int x=p->x/256,y=p->y/256,near,far,lo,hi;
    if(p->height || p->vz || p->torch!=MF_TORCH_FIRE || y+8<b.back || y-8>b.front)return 0;
    near=p->facing>0?b.left-x:x-b.right;far=p->facing>0?b.right-x:x-b.left;
    near=clamp(near,MF_TORCH_NOZZLE_X-4,MF_TORCH_END_X+4);
    if(far<MF_TORCH_NOZZLE_X-4 || (p->facing>0?b.left-x:x-b.right)>MF_TORCH_END_X+4)return 0;
    far=clamp(far,MF_TORCH_NOZZLE_X,MF_TORCH_END_X);
    near=clamp(near,MF_TORCH_NOZZLE_X,MF_TORCH_END_X);
    lo=MF_TORCH_NOZZLE_Z*(MF_TORCH_END_X-far)/(MF_TORCH_END_X-MF_TORCH_NOZZLE_X)-5;
    hi=MF_TORCH_NOZZLE_Z*(MF_TORCH_END_X-near)/(MF_TORCH_END_X-MF_TORCH_NOZZLE_X)+5;
    return b.bottom<=hi && b.top>=lo;
}
static void torch_hits(mf_game *g,mf_player *p)
{
    int i;
#if MF_LEVEL1_STAGE_CLEAR
    if(g->stage!=MF_STAGE_LEVEL1)return;
#endif
    if(p->torch!=MF_TORCH_FIRE)return;
    if(p->torch_tick>0)--p->torch_tick;
    if(p->torch_tick)return;
    p->torch_tick=MF_TORCH_DAMAGE_TICKS;
    for(i=0;i<MF_ENEMIES;i++)if(mf_torch_hits(p,mf_enemy_hurtbox(&g->enemies[i])))fire_damage(g,&g->enemies[i],1,(int)(p-g->players));
    for(i=0;i<MF_DRUMS;i++){
        mf_drum *d=&g->drums[i];
        if(d->hp && mf_torch_hits(p,hurtbox(d->x/256,d->y/256,0,12,5,46))){
            d->hp=clamp(d->hp-MF_TORCH_DAMAGE,0,3);hit_sound(g,(int)(p-g->players),d->hp,1);d->flash=4;g->score+=10;
            if(!d->hp){++g->broken;g->score+=100;g->events|=MF_IMPACT;}
        }
    }
}
static void player_step(mf_game *g,int index,unsigned held,unsigned pressed)
{
    mf_player *p=&g->players[index];int dx=0,dy=0,speed;
    if(!p->active)return;
    pressed|=p->buffered;p->buffered=0;
#if MF_FAST_RUNNING_BAT
    if(g->running_bat[index].pending){
        int transition=MF_JAB_REPEAT_COUNTER;
#if MF_PUNCH_COMBO
        if(g->combo[index].phase==2)transition+=MF_CROSS_RECOVERY_EXTRA;
#endif
        if(!p->attack || (!p->bat && !p->attack_air && p->attack>=transition)){
            p->attack=0;pressed|=MF_A;
        }
    }
#endif
/* JAB BEGIN */
#if MF_JAB_COHESION
    if(pressed&MF_B)g->jab[index].buffer=0;
    if(!(pressed&MF_B) && mf_jab_repeat_consume(g,index)) {
        p->attack=1;p->bat=p->attack_air=0;p->hit_mask=0;clear_gesture(p);
#if MF_PUNCH_COMBO
        mf_combo_begin(g,index);
#endif
        g->events|=MF_SWOOSH|MF_COMBAT_JAB(index);
    }
#endif
/* JAB END */
#if MF_RUN_BAT
    if(p->hurt || !p->health)g->running_bat[index]=(mf_running_bat){0};
#endif
    if(p->invulnerable)--p->invulnerable;
    if(!p->health){
        if(p->defeated>0 && --p->defeated==0){recover_player(g,index,0);g->players[index].a_blocked=(held&MF_A)!=0;}
        return;
    }
    if(p->landing)--p->landing;
    if(p->hurt){--p->hurt;p->x=clamp(p->x+p->knockback,26*256,614*256);p->knockback=p->knockback*3/4;}
    else{
        if(!p->torch){
        if((pressed&MF_B) && !p->height && !p->attack){
#if MF_PUNCH_COMBO
            mf_combo_reset(g,index);
#endif
            p->landing=0;p->vz=1510;p->air_bat_used=0;clear_gesture(p);torch_cancel(p);
            /* Even forward+B cannot contribute a stale grounded first tap. */
            p->previous_directions=held&(MF_LEFT|MF_RIGHT);g->events|=MF_JUMP_SOUND;
        }
        if((pressed&MF_A) && !p->attack){
#if MF_RUN_BAT
            if(g->running_bat[index].pending && !(pressed&MF_B) && !p->height && !p->vz) {
                mf_running_bat *rb=&g->running_bat[index];
                rb->active=rb->pending;rb->pending=0;rb->carry=MF_RUNNING_BAT_CARRY_TICKS;
/* MOMENTUM BEGIN */
#if MF_BAT_MOMENTUM
                rb->carry=MF_BAT_SLIDE_TICKS;
#endif
/* MOMENTUM END */
                p->bat=MF_FAST_RUNNING_BAT?MF_BAT_RUNNING:1;p->facing=rb->dir;
            }else
#endif
#if MF_FAST_RUNNING_BAT
            p->bat=0; /* Only an eligible dash may deploy the horizontal bat. */
#else
            p->bat=p->bat_window>0 && p->combo_dir==p->facing &&
                (!(p->height || p->vz) || !p->air_bat_used);
#endif
            p->attack=1;p->attack_air=MF_FAST_RUNNING_BAT?(p->height || p->vz)!=0:p->height>0;p->hit_mask=0;clear_gesture(p);
#if MF_PUNCH_COMBO
            if(!p->bat && !p->attack_air)mf_combo_begin(g,index);
            else mf_combo_reset(g,index);
#endif
            if(p->bat){p->charge=0;p->a_blocked=1;}
            if(p->bat && p->attack_air)p->air_bat_used=1;
            if(!p->bat)g->events|=MF_SWOOSH;
            if(p->bat)g->events|=MF_COMBAT_BAT(index);
            else if(!p->attack_air)g->events|=MF_COMBAT_JAB(index);
        }
        }
        if(held&MF_LEFT)dx--;
        if(held&MF_RIGHT)dx++;
        if(held&MF_UP)dy--;
        if(held&MF_DOWN)dy++;
    }
    speed=p->torch?MF_TORCH_WALK_SPEED:p->charge?390:(p->bat && p->attack && !p->attack_air?0:((p->attack && !p->attack_air)?100:390));
#if MF_DASH_ENABLED
    if(g->dash[index].dir)speed=speed*MF_DASH_SPEED_NUM/MF_DASH_SPEED_DEN;
#endif
#if MF_RUN_BAT
    if(g->running_bat[index].active) {
        mf_running_bat *rb=&g->running_bat[index];
        dx=rb->carry?rb->dir:0;dy=0;speed=MF_RUNNING_BAT_SPEED;
/* MOMENTUM BEGIN */
#if MF_BAT_MOMENTUM
        speed=MF_BAT_SLIDE_START*rb->carry/MF_BAT_SLIDE_TICKS;
#endif
/* MOMENTUM END */
        if(rb->carry)--rb->carry;
    }
#endif
    if(dx && dy)speed=speed*181/256;
    if(dx && (!p->attack || p->charge) && !p->torch)p->facing=dx;
    p->x=clamp(p->x+dx*speed,26*256,614*256);p->y=clamp(p->y+dy*speed*3/4,168*256,229*256);
    p->moving=dx||dy;if(p->moving)++p->walk;else p->walk=0;
#if MF_DASH_ENABLED
    if(g->dash[index].dir)g->dash[index].anim=(g->dash[index].anim+MF_DASH_ANIM_NUM)%
#if MF_RUN_BAT
        (4*MF_RUN_FRAME_HOLD*MF_DASH_ANIM_NUM);
#else
        MF_DASH_ANIM_CYCLE;
#endif
#endif
    if(p->height || p->vz){p->height+=p->vz;p->vz-=74;
        if(p->height<=0){
            p->height=0;p->vz=0;p->landing=6;clear_gesture(p);
            if(p->bat && p->attack_air){
                /* Never restart active frames or reset the per-target mask. */
                p->attack=MF_BAT_LAND_RECOVERY_START;p->attack_air=0;
            }else if(p->attack_air)p->attack=0;
        }}
}
static int contact_height(const mf_player *p,int target_top)
{
    mf_hitbox b=mf_player_attackbox(p);
    int bottom=b.bottom>4?b.bottom:4,top=b.top<target_top?b.top:target_top;
    return (bottom+top)/2;
}
static void player_hits(mf_game *g,mf_player *p)
{
    int i;
#if MF_LEVEL1_STAGE_CLEAR
    if(g->stage!=MF_STAGE_LEVEL1)return;
#endif
    if(!player_active(p))return;
    for(i=0;i<MF_DRUMS;i++){
        mf_drum *d=&g->drums[i];
        if(d->hp && !(p->hit_mask&(1<<i)) && (d->x-p->x)*p->facing>0 &&
           mf_boxes_overlap(mf_player_attackbox(p),hurtbox(d->x/256,d->y/256,0,12,5,46))){
            p->hit_mask|=1<<i;
#if MF_FAST_RUNNING_BAT
            if(p->bat==MF_BAT_RUNNING)d->hp=0;
            else
#endif
            d->hp=clamp(d->hp-(p->bat?MF_BAT_DAMAGE:1),0,3);
            hit_sound(g,(int)(p-g->players),d->hp,1);
            d->flash=10;d->vx=p->facing*(p->bat?MF_BAT_KNOCKBACK:850);g->score+=10;
            impact(g,d->x/256,d->y/256,p->bat?contact_height(p,46):36);if(!d->hp){++g->broken;g->score+=100;}
        }
    }
    for(i=0;i<MF_ENEMIES;i++){
        mf_enemy *e=&g->enemies[i];int bit=1<<(MF_DRUMS+i);
#if MF_LEVEL1_STAGE_CLEAR
        if(g->stage!=MF_STAGE_LEVEL1)break;
#endif
        if(e->hp>0 && e->state!=MF_ENEMY_ABSENT && !(p->hit_mask&bit) && (e->x-p->x)*p->facing>0 &&
           mf_boxes_overlap(mf_player_attackbox(p),mf_enemy_hurtbox(e))){
            p->hit_mask|=bit;
            if(g->enemy_class[i]==MF_ENEMY_CORPORATE_PUNK){
                if(p->bat || p->attack_air)g->punk[i].punches=g->punk[i].expiry=0;
                else {
                    if(g->punk[i].punches<MF_PUNK_COUNTER_THRESHOLD)++g->punk[i].punches;
                    g->punk[i].expiry=MF_PUNK_PRESSURE_EXPIRY;
                }
            }
#if MF_RUN_BAT
            if(g->running_bat[p-g->players].active && p->bat && (g->enemy_class[i]==MF_ENEMY_CORPORATE_PUNK
#if MF_RICKY_ENEMY
                || g->enemy_class[i]==MF_ENEMY_RICKY
#endif
                ))e->hp=0;
            else
#endif
            e->hp=clamp(e->hp-(p->bat?MF_BAT_DAMAGE:(p->attack_air?2:1)),0,MF_ENEMY_MAX_HP);
            hit_sound(g,(int)(p-g->players),e->hp,0);
            e->state=e->hp?MF_ENEMY_HURT:MF_ENEMY_DYING;e->timer=e->hp?
                (g->enemy_class[i]==MF_ENEMY_CORPORATE_PUNK?
                 (g->punk[i].punches>=MF_PUNK_COUNTER_THRESHOLD?MF_PUNK_COUNTER_HURT:
                  g->punk[i].punches>=MF_PUNK_PRESSURE_BUILD?MF_PUNK_PRESSURE_HURT:MF_PUNK_NORMAL_HURT):18):30;e->vx=p->facing*(p->bat?MF_BAT_KNOCKBACK:850);e->flash=10;
            impact(g,e->x/256,e->y/256,p->bat?contact_height(p,84):48);if(!e->hp){
                g->score+=MF_ENEMY_DEFEAT_SCORE;
#if MF_LEVEL1_STAGE_CLEAR
                stage_defeat(g,i);
#endif
            }
        }
    }
}
#if MF_LEVEL1_STAGE_CLEAR
static void stage_transition_step(mf_game *g)
{
    int i;
    if(g->stage==MF_STAGE_LEVEL2_ENTRY)return;
    if(g->stage==MF_STAGE_SETTLING) {
        if(g->hitstop){--g->hitstop;return;}
        ++g->ticks;if(g->spark)--g->spark;
        for(i=0;i<MF_ENEMIES;i++)if(g->enemies[i].state==MF_ENEMY_DYING)enemy_step(g,i);
        for(i=0;i<MF_PLAYERS;i++) {
            mf_player *p=&g->players[i];
            /* Finish the existing strike/landing without taking new input,
               healing players or allowing any further damage. */
            if(p->height || p->vz){p->height+=p->vz;p->vz-=74;if(p->height<=0)p->height=p->vz=0;}
            int total=p->bat==MF_BAT_RUNNING?MF_FAST_BAT_TOTAL_TICKS:(p->bat?MF_BAT_TOTAL_TICKS:24);
#if MF_PUNCH_COMBO
            if(!p->bat && !p->attack_air && g->combo[i].phase==2)total=MF_CROSS_TOTAL_TICKS;
#endif
            if(p->attack && ++p->attack>total)p->attack=p->bat=0;
        }
    }
    if(--g->stage_timer>0)return;
    if(g->stage==MF_STAGE_SETTLING) {
        g->stage=MF_STAGE_CLEAR;g->stage_timer=MF_STAGE_CLEAR_TICKS;
        for(i=0;i<MF_PLAYERS;i++) {
            mf_player *p=&g->players[i];
            p->attack=p->bat=p->attack_air=p->moving=p->buffered=0;
            torch_cancel(p);g->running_bat[i]=(mf_running_bat){0};
            g->dash[i]=(mf_dash_state){0};
        }
    }else g->stage=MF_STAGE_LEVEL2_ENTRY;
}
#endif
void mf_game_step_inputs(mf_game *g,const unsigned held[2],const unsigned pressed[2],unsigned connected)
{
    int i;
#if MF_DASH_ENABLED
    int was_live=g->started && !g->paused;
#endif
    g->events=0;
    if(pressed[0]&MF_C)g->debug^=1;
    if(pressed[0]&MF_START){if(!g->started)g->started=1;else g->paused^=1;}
    /* P2 Start only joins; never touches the P1 pause state. */
    if(!g->players[1].active && (pressed[1]&MF_START)){g->started=1;recover_player(g,1,1);}
    if(!g->started || g->paused){
        for(i=0;i<MF_PLAYERS;i++){
#if MF_DASH_ENABLED
            dash_clear(&g->dash[i]);g->dash[i].previous=held[i]&(MF_LEFT|MF_RIGHT);
#endif
            g->running_bat[i]=(mf_running_bat){0};
            torch_cancel(&g->players[i]);
/* JAB BEGIN */
#if MF_JAB_COHESION
            g->jab[i].buffer=0;g->jab[i].previous=held[i]&MF_A;
#endif
/* JAB END */
            if((connected&(1u<<i)) && !(held[i]&MF_A))g->players[i].a_blocked=0;
        }
        return;
    }
#if MF_LEVEL1_STAGE_CLEAR
    if(g->stage!=MF_STAGE_LEVEL1){stage_transition_step(g);return;}
#endif
    for(i=0;i<MF_PLAYERS;i++){
        gesture_step(&g->players[i],held[i],pressed[i]);
/* JAB BEGIN */
#if MF_JAB_COHESION
#if MF_PUNCH_COMBO
        mf_combo_tick(g,i,(connected&(1u<<i))!=0);
#endif
        mf_jab_repeat_capture(g,i,held[i],pressed[i],(connected&(1u<<i))!=0);
#endif
/* JAB END */
#if MF_FAST_RUNNING_BAT
        /* Resolve the second direction edge before classifying A. Mask only A:
           jump, recovery, disconnect and hit-stop retain their dash guards. */
        dash_input(g,i,held[i],pressed[i]&~MF_A,was_live,(connected&(1u<<i))!=0);
#endif
#if MF_RUN_BAT
        {
            mf_player *p=&g->players[i];mf_running_bat *rb=&g->running_bat[i];
            if(!(connected&(1u<<i)) || !p->health || p->hurt || (pressed[i]&MF_B))rb->pending=0;
            /* The selected fast profile includes a dash armed on this tick.
               Hit-stop may buffer an already established dash/A classification. */
            if(was_live && (connected&(1u<<i)) && p->active && p->health && !p->hurt &&
               (!p->attack || (!p->bat && !p->attack_air)) && !p->height && !p->vz && !p->landing && !p->torch &&
               (g->dash[i].dir || (g->dash[i].released==2 && g->dash[i].tap_dir)) && (pressed[i]&MF_A) && !(pressed[i]&MF_B) &&
               (held[i]&(MF_LEFT|MF_RIGHT))==((g->dash[i].dir?g->dash[i].dir:g->dash[i].tap_dir)>0?MF_RIGHT:MF_LEFT)) {
                rb->pending=1;rb->dir=g->dash[i].dir?g->dash[i].dir:g->dash[i].tap_dir;
#if MF_FAST_RUNNING_BAT
                /* Capture pose without changing the gameplay ABI or depending
                   on a previous render callback (immediate/catch-up inputs). */
                if(g->dash[i].anim>0)rb->pending+=(g->dash[i].anim/(MF_RUN_FRAME_HOLD*MF_DASH_ANIM_NUM))%4;
#endif
                p->charge=0;p->a_blocked=1;
            }
#if MF_FAST_RUNNING_BAT
            if(rb->pending)dash_clear(&g->dash[i]);
#endif
            if(!rb->pending)torch_input(p,held[i],pressed[i],(connected&(1u<<i))!=0);
        }
#else
        torch_input(&g->players[i],held[i],pressed[i],(connected&(1u<<i))!=0);
#endif
#if MF_DASH_ENABLED && !MF_FAST_RUNNING_BAT
        dash_input(g,i,held[i],pressed[i],was_live,(connected&(1u<<i))!=0);
#endif
    }
    if(g->hitstop){--g->hitstop;for(i=0;i<MF_PLAYERS;i++)if(g->players[i].active)g->players[i].buffered|=pressed[i]&(MF_A|MF_B);torch_events(g);return;}
    ++g->ticks;if(g->spark)--g->spark;
    for(i=0;i<MF_PLAYERS;i++)player_step(g,i,held[i],pressed[i]);
    /* Shared camera tether, no physical body collision or friendly fire. Both
       living players remain visible and can cross each other freely. */
    if(living(&g->players[0]) && living(&g->players[1])){
        int mid=(g->players[0].x+g->players[1].x)/2;
        for(i=0;i<MF_PLAYERS;i++)g->players[i].x=clamp(g->players[i].x,mid-130*256,mid+130*256);
    }
    for(i=0;i<MF_DRUMS;i++){
        mf_drum *d=&g->drums[i];if(d->flash)--d->flash;
        if(!d->hp){if(++d->respawn>=240)drum_reset(d,i);continue;}
        d->x=clamp(d->x+d->vx,24*256,616*256);d->vx=d->vx*7/8;if(abs_i(d->vx)<8)d->vx=0;
    }
    for(i=0;i<MF_PLAYERS;i++){player_hits(g,&g->players[i]);torch_hits(g,&g->players[i]);}
    for(i=0;i<MF_ENEMIES;i++)enemy_step(g,i);
#if MF_LEVEL1_STAGE_CLEAR
    stage_spawns(g);
#endif
    for(i=0;i<MF_PLAYERS;i++){
        mf_player *p=&g->players[i];
#if MF_FAST_RUNNING_BAT
        /* One deployment whoosh; CONNECT is emitted only by a valid hit.
           The legacy generic swoosh event remains for planted attacks. */
        int total=p->bat==MF_BAT_RUNNING?MF_FAST_BAT_TOTAL_TICKS:(p->bat?MF_BAT_TOTAL_TICKS:24);
        if(p->bat==1 && p->attack==MF_BAT_ACTIVE_FIRST)g->events|=MF_SWOOSH;
#if MF_PUNCH_COMBO
        if(!p->bat && !p->attack_air && g->combo[i].phase==2)total=MF_CROSS_TOTAL_TICKS;
#endif
        if(p->attack && ++p->attack>total)p->attack=p->bat=0;
#else
        if(p->bat && p->attack==MF_BAT_ACTIVE_FIRST)g->events|=MF_SWOOSH;
        if(p->attack && ++p->attack>(p->bat?MF_BAT_TOTAL_TICKS:24))p->attack=p->bat=0;
#endif
        if(!p->attack && !g->running_bat[i].pending)g->running_bat[i]=(mf_running_bat){0};
    }
    torch_events(g);
    if(living(&g->players[1]))g->camera=clamp((living(&g->players[0])?(g->players[0].x+g->players[1].x)/512:g->players[1].x/256)-160,0,320);
    else g->camera=clamp(g->players[0].x/256-142,0,320);
}
void mf_game_step_coop(mf_game *g,const unsigned held[2],const unsigned pressed[2])
{
    mf_game_step_inputs(g,held,pressed,3);
}
void mf_game_step(mf_game *g,unsigned held,unsigned pressed)
{
    unsigned h[2]={held,0},p[2]={pressed,0};mf_game_step_coop(g,h,p);
}
int mf_player_frame(const mf_game *g,int player)
{
    const mf_player *p=&g->players[player];
    if(!p->health)return 13;
    if(p->hurt)return 8;
    if(p->height)return p->attack?14:(p->vz>1200?11:12);
    if(p->attack)return p->attack<6?8:(p->attack<=10?9:10);
    if(p->landing)return 13;
    if(p->moving)return 2+(p->walk/5)%6;
    return (g->ticks/32)%2;
}
int mf_bat_frame(const mf_player *p)
{
    int t=p->attack;
    if(t<6)return 0;
    if(t<12)return 1;
    if(t<14)return 2;
    if(t<17)return 3;
    if(t<20)return 4;
    if(t<28)return 5;
    return 6;
}
int mf_buck_frame(const mf_game *g){return mf_player_frame(g,0);}
int mf_enemy_frame(const mf_game *g,int enemy)
{
    const mf_enemy *e=&g->enemies[enemy];
    if(e->state==MF_ENEMY_DYING)return e->timer>15?10:11;
    if(e->state==MF_ENEMY_HURT)return 9;
    if(e->state==MF_ENEMY_WINDUP)return 6;
    if(e->state==MF_ENEMY_ACTIVE)return 7;
    if(e->state==MF_ENEMY_RECOVER)return 8;
    if(e->state==MF_ENEMY_WALK)return 2+(e->walk/7)%4;
    return (g->ticks/40)%2;
}
