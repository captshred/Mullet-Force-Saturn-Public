/* Production gameplay pause invariants; no emulator or sound mocks. */
#include <assert.h>
#include <string.h>
#include <stdio.h>
#include "game.h"
int main(void){mf_game g,snapshot;unsigned held[2]={MF_START,0},pressed[2]={MF_START,0};int i;
 mf_game_init(&g);mf_game_step_inputs(&g,held,pressed,1);assert(g.started);
 pressed[0]=0;held[0]=0;mf_game_step_inputs(&g,held,pressed,1);
 pressed[0]=MF_START;held[0]=MF_START;mf_game_step_inputs(&g,held,pressed,1);assert(g.paused);
 held[0]=MF_A|MF_RIGHT;pressed[0]=0;mf_game_step_inputs(&g,held,pressed,1);snapshot=g;
 for(i=0;i<14000;i++){mf_game_step_inputs(&g,held,pressed,1);assert(!memcmp(&g,&snapshot,sizeof(g)));assert(!g.events);}
 pressed[0]=MF_START;held[0]|=MF_START;mf_game_step_inputs(&g,held,pressed,1);assert(!g.paused && g.ticks>snapshot.ticks);
 puts("PASS production gameplay: entire settled game state frozen14000 paused ticks with held attack/movement; no events; normal unpause resumes ticks");return 0;}
