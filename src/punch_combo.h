#ifndef MF_PUNCH_COMBO_H
#define MF_PUNCH_COMBO_H
#if MF_PUNCH_COMBO
static void mf_combo_reset(mf_game *g,int i)
{g->combo[i]=(mf_punch_combo){0};}
static void mf_combo_begin(mf_game *g,int i)
{
 mf_punch_combo *c=&g->combo[i];c->phase=c->next;c->next=(c->next+1)%3;c->timeout=MF_COMBO_TIMEOUT_TICKS;
}
static void mf_combo_tick(mf_game *g,int i,int connected)
{
 mf_player *p=&g->players[i];mf_punch_combo *c=&g->combo[i];
 if(!connected || !p->active || !p->health || p->hurt || p->height || p->vz || p->torch || p->bat){mf_combo_reset(g,i);return;}
 if(!g->hitstop && !g->paused && g->started && c->timeout && --c->timeout==0)mf_combo_reset(g,i);
}
#endif
#endif
