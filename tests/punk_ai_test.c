/* Exercise production collision and AI, including stage-default input flags. */
#include <assert.h>
#include <stdio.h>
#include "../src/game.c"
static void setup(mf_game *g,int actor,int facing)
{
    int i;mf_game_init(g);g->started=1;g->stage=MF_STAGE_LEVEL1;
    for(i=0;i<2;i++){
        g->players[i]=(mf_player){0};g->players[i].active=1;
        g->players[i].health=100;g->players[i].x=(300+i*100)*256;
        g->players[i].y=200*256;g->players[i].facing=facing;
        g->enemies[i]=(mf_enemy){0};g->enemies[i].state=MF_ENEMY_ABSENT;
    }
    g->players[1-actor].active=0;
    g->enemies[0].hp=6;g->enemies[0].state=MF_ENEMY_IDLE;
    g->enemies[0].x=g->players[actor].x+facing*30*256;
    g->enemies[0].y=200*256;g->enemies[0].target=actor;
    g->enemies[0].facing=-facing;
    for(i=0;i<3;i++)g->drums[i].hp=0;
}
static void punch(mf_game *g,int actor)
{
    mf_player *p=&g->players[actor];mf_enemy *e=&g->enemies[0];
    e->x=p->x+p->facing*30*256;e->hp=6;
    p->attack=6;p->bat=p->attack_air=0;p->hit_mask=0;
    player_hits(g,p);
}
int main(void)
{
    mf_game g;int actor,f,i,n;
    for(actor=0;actor<2;actor++)for(f=-1;f<=1;f+=2){
        setup(&g,actor,f);g.players[actor].attack=1;
        enemy_step(&g,0);assert(g.enemies[0].state==MF_ENEMY_WINDUP);
        assert(g.enemies[0].timer==18); /* Active player, no idle gate. */
        for(i=1;i<=5;i++){
            punch(&g,actor);assert(g.punk[0].punches==i);
            player_hits(&g,&g.players[actor]);assert(g.punk[0].punches==i);
            assert(g.enemies[0].timer==(i<3?18:i<5?12:6));
            g.enemies[0].vx=0;
            for(n=0;n<(i<3?42:i<5?20:8);n++)enemy_step(&g,0);
            assert(g.enemies[0].state==MF_ENEMY_IDLE);
            enemy_step(&g,0);assert(g.enemies[0].state==MF_ENEMY_WINDUP);
            assert(g.enemies[0].timer==(i<5?18:10));
        }
        /* Counter is an opportunity, not damage or armor. Next jab interrupts. */
        assert(g.players[actor].health==100);
        punch(&g,actor);g.enemies[0].vx=0;
        /* Thirteen simulation ticks is the repeat-jab cadence. A recovering
           fifth-hit punk gets a windup, but the next accurate jab beats it. */
        for(n=0;n<13;n++)enemy_step(&g,0);
        assert(g.enemies[0].state==MF_ENEMY_WINDUP && g.enemies[0].timer>0);
        punch(&g,actor);assert(g.enemies[0].state==MF_ENEMY_HURT && g.punk[0].punches==5);
        /* Missed specials keep pressure; connected specials clear only their slot. */
        for(i=0;i<2;i++){
            mf_player *p=&g.players[actor];
            g.punk[0].punches=5;g.punk[0].expiry=180;g.punk[1].punches=4;
            p->attack=i?4:6;p->bat=i?MF_BAT_RUNNING:0;p->attack_air=!i;p->hit_mask=0;
            g.enemies[0].x=p->x+f*200*256;player_hits(&g,p);assert(g.punk[0].punches==5);
            g.enemies[0].x=p->x+f*30*256;player_hits(&g,p);
            assert(!g.punk[0].punches && !g.punk[0].expiry && g.punk[1].punches==4);
        }
        setup(&g,actor,f);g.punk[0].punches=5;g.punk[0].expiry=1;
        enemy_step(&g,0);assert(!g.punk[0].punches && g.enemies[0].timer==18);
        setup(&g,actor,f);g.punk[0].punches=5;g.punk[0].expiry=180;
        g.enemies[0].state=MF_ENEMY_RECOVER;g.enemies[0].timer=5;
        enemy_step(&g,0);assert(g.enemies[0].state==MF_ENEMY_RECOVER);
        g.enemies[0].state=MF_ENEMY_IDLE;g.enemies[0].grace=20;
        enemy_step(&g,0);assert(g.enemies[0].state==MF_ENEMY_IDLE);
        g.enemies[0].grace=0;g.enemies[0].x+=f*200*256;
        enemy_step(&g,0);assert(g.enemies[0].state==MF_ENEMY_WALK);
        /* Both slots commit, but shared protection permits only one impact. */
        setup(&g,actor,f);g.enemies[1]=g.enemies[0];
        g.punk[0].punches=5;g.punk[0].expiry=180;
        enemy_step(&g,0);enemy_step(&g,1);
        assert(g.enemies[0].state==MF_ENEMY_WINDUP && g.enemies[1].state==MF_ENEMY_WINDUP);
        assert(g.enemies[0].timer==10 && g.enemies[1].timer==18);
        g.players[actor].attack=8;g.players[actor].bat=1;g.running_bat[actor].pending=1;
        for(i=0;i<18;i++){enemy_step(&g,0);enemy_step(&g,1);}
        assert(g.players[actor].health==88 && g.players[actor].hurt==12);
        assert(!g.players[actor].attack && !g.players[actor].bat && !g.running_bat[actor].pending);
        assert(g.players[actor].invulnerable==60);
        for(i=0;i<12;i++)player_step(&g,actor,0,0);
        assert(!g.players[actor].hurt && g.players[actor].invulnerable==48);
        g.enemies[0].state=MF_ENEMY_ACTIVE;g.enemies[0].timer=6;g.enemies[0].hit_done=0;
        enemy_step(&g,0);assert(g.players[actor].health==88);
        player_step(&g,actor,0,MF_A);assert(g.players[actor].attack); /* responsive recovery */
    }
    puts("PASS punk AI: both actors/facings, active-player aggression, distinct punches, thresholds/recovery/range/grace, interruptible counters, landed/missed specials, expiry, two commitments and protected responsive recoil");
    return 0;
}
