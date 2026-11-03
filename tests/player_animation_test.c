#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../src/player_animation.c"
static int calls,actor_id,pose_id,center_x,baseline,face,zkey;
int mf_animation_draw_actor(int a,int f,int x,int y,int face_arg,int z)
{calls++;actor_id=a;pose_id=f;center_x=x;baseline=y;face=face_arg;zkey=z;return 1;}
static int expected_walk(int actor,int tick)
{
#if MF_ORIGINAL_THREE_WALK
    (void)actor;return 15+(tick/MF_ORIGINAL_FRAME_HOLD)%3;
#elif MF_SWAGGER_WALK
    int first=actor?15:14,total=actor?44:42;
    tick%=total;return tick<first?12:tick<first+14?13:14;
#else
    (void)actor;
    return 4+((tick%40)*3)/20;
#endif
}
static void advance(mf_game *g,const unsigned held[2],const unsigned pressed[2])
{
    mf_game unchanged=*g;int before=g->ticks;
    mf_game_step_coop(g,held,pressed);
    mf_game_step_coop(&unchanged,held,pressed);
    if(g->ticks!=before)mf_player_animation_step(g);
    assert(!memcmp(g,&unchanged,sizeof(*g)));
}
int main(void)
{
    mf_game g,save;mf_player p;unsigned none[2]={0,0},h[2]={0,0},edge[2]={MF_START,MF_START};int a,t,f,oldcalls;
    mf_game_init(&g);advance(&g,none,edge);g.enemies[0].state=g.enemies[1].state=MF_ENEMY_ABSENT;
    g.enemies[0].timer=g.enemies[1].timer=100000;
    memset(idle_ticks,0,sizeof(idle_ticks));memset(last_mode,0,sizeof(last_mode));
    mf_player_animation_step(&g);
    for(t=0;t<720;t++) {
        for(a=0;a<2;a++){
            unsigned phase=(unsigned)t%(a?90u:80u),total=0;
            for(f=0;f<3 && phase>=total+holds[a][f];f++)total+=holds[a][f];
            assert(mf_player_animation_pose(&g,a)==f);
        }
        advance(&g,none,none);
    }
    h[0]=MF_RIGHT;h[1]=MF_LEFT|MF_UP;
    for(t=0;t<65;t++) {
        advance(&g,h,none);
        for(a=0;a<2;a++)assert(mf_player_animation_pose(&g,a)==expected_walk(a,g.players[a].walk));
        if(t==11)h[0]=MF_LEFT|MF_DOWN; /* changing axes/facing preserves clock */
    }
    h[0]=0;advance(&g,h,none);assert(mf_player_animation_pose(&g,0)==0);
    for(t=0;t<30;t++)advance(&g,h,none);
    assert(mf_player_animation_pose(&g,0)==1 && mf_player_animation_pose(&g,1)>=4);
    /* Presentation cannot change any byte of the game, including the attack root. */
    p=g.players[0];save=g;
#define FALLBACK(field,value) g.players[0]=p;g.players[0].field=value;assert(mf_player_animation_pose(&g,0)==-1)
    FALLBACK(active,0);FALLBACK(health,0);FALLBACK(hurt,4);FALLBACK(attack,1);
    FALLBACK(height,100);FALLBACK(vz,1510);FALLBACK(landing,6);FALLBACK(torch,MF_TORCH_FIRE);
#undef FALLBACK
    g=save;
    for(a=0;a<2;a++)for(t=0;t<60;t++) {
        g.players[a].moving=1;g.players[a].walk=t;g.players[a].facing=t&1?-1:1;
        save=g;assert(mf_player_animation_draw(&g,a,77,190,270));assert(!memcmp(&g,&save,sizeof(g)));
        assert(actor_id==a && pose_id==expected_walk(a,t) && center_x==77 && baseline==190 && zkey==270 && face==g.players[a].facing);
    }
    for(a=0;a<2;a++) {
#if MF_ORIGINAL_THREE_WALK
        int counts[3]={0},previous=15,total=MF_ORIGINAL_FRAME_HOLD*3;
        for(t=0;t<total*2;t++) {
            int selected;g.players[a].moving=1;g.players[a].walk=t;
            selected=mf_player_animation_pose(&g,a);
            assert(selected==previous || selected==15+(previous-15+1)%3);
            counts[selected-15]++;previous=selected;
        }
        for(f=0;f<3;f++)assert(counts[f]==MF_ORIGINAL_FRAME_HOLD*2);
#elif MF_SWAGGER_WALK
        int counts[3]={0},previous=12,total=a?44:42;
        for(t=0;t<total*2;t++) {
            int selected;
            g.players[a].moving=1;g.players[a].walk=t;
            selected=mf_player_animation_pose(&g,a);
            assert(selected==previous || selected==12+(previous-12+1)%3);
            counts[selected-12]++;previous=selected;
        }
        assert(counts[0]==(a?30:28) && counts[1]==28 && counts[2]==(a?30:28));
#else
        int counts[6]={0},previous=4;
        for(t=0;t<80;t++) {
            int selected;
            g.players[a].moving=1;g.players[a].walk=t;
            selected=mf_player_animation_pose(&g,a);
            assert(selected==previous || selected==4+(previous-4+1)%6);
            counts[selected-4]++;previous=selected;
        }
        for(f=0;f<6;f++)assert(counts[f]==(f%3==2?12:14));
#endif
        g.players[a].walk=2147483647;
        assert(mf_player_animation_pose(&g,a)==expected_walk(a,2147483647));
    }
    oldcalls=calls;g.players[0].attack=1;assert(!mf_player_animation_draw(&g,0,77,190,270) && calls==oldcalls);
    g.players[0].attack=0;
    edge[0]=MF_B;edge[1]=MF_A;advance(&g,none,edge);
    assert(mf_player_animation_pose(&g,0)==-1 && mf_player_animation_pose(&g,1)==-1);
    for(t=0;t<70;t++)advance(&g,none,none);
    assert(mf_player_animation_pose(&g,0)>=0 && mf_player_animation_pose(&g,1)>=0);
    /* Main advances presentation only when simulation ticks change. */
    edge[0]=MF_START;edge[1]=0;advance(&g,none,edge);assert(g.paused);
    t=(int)idle_ticks[0];for(f=0;f<30;f++)advance(&g,none,none);assert(idle_ticks[0]==(unsigned)t);
    advance(&g,none,edge);g.hitstop=3;t=(int)idle_ticks[0];
    for(f=0;f<3;f++){advance(&g,none,none);}assert(idle_ticks[0]==(unsigned)t);
    assert(mf_player_animation_pose(&g,-1)==-1 && mf_player_animation_pose(&g,2)==-1);
    puts("PASS playable presentation: selected swagger/six walk order, independent breaths/axes/facing, state fallback, attack/jump return, frozen pause/hitstop, immutable simulation and roots.");
    return 0;
}
