#include <assert.h>
#include <stdio.h>
#include <jo/jo.h>
#include "input.h"
#include "game.h"
PerDigital peripheral_buffer[21];
PerDigital *Smpc_Peripheral=peripheral_buffer;
void jo_get_inputs_vblank(void);
typedef char per_digital_is_24_bytes[sizeof(PerDigital)==24?1:-1];
int jo_is_input_available(int p){assert(p>=0 && p<12);return jo_inputs[p].id!=255;}
int jo_get_input_type(int p){return jo_inputs[p].id==2?JoRegularGamepad:jo_inputs[p].id==0x16?JoNightsPad:jo_inputs[p].id==255?JoNotConnectedGamepad:JoRegularMouse;}
int jo_is_input_key_pressed(int p,int k){return (jo_inputs[p].data&k)==0;}
int jo_is_input_key_down(int p,int k){return (jo_inputs[p].push&k)==0;}
int main(void)
{
    mf_input a,b;mf_game g;unsigned h[2],e[2];int i;
    for(i=0;i<21;i++){peripheral_buffer[i].id=255;peripheral_buffer[i].data=peripheral_buffer[i].push=65535;}
    peripheral_buffer[0].id=2;peripheral_buffer[0].data=65535^(JO_KEY_RIGHT|JO_KEY_A);peripheral_buffer[0].push=65535^JO_KEY_A;
    jo_get_inputs_vblank();a=mf_input_read();b=mf_input_read_port(1);
    assert(a.connected && a.held==(MF_RIGHT|MF_A) && a.pressed==MF_A && a.sdk_slot==0);
    assert(!b.connected && !b.held && !b.pressed && b.sdk_slot==6);
    /* Presses in slot 1 (first physical connector's multitap) must not join. */
    peripheral_buffer[1].id=2;peripheral_buffer[1].data=peripheral_buffer[1].push=65535^JO_KEY_START;
    jo_get_inputs_vblank();b=mf_input_read_port(1);assert(!b.pressed);
    peripheral_buffer[15].id=2;peripheral_buffer[15].data=65535^(JO_KEY_LEFT|JO_KEY_B|JO_KEY_START);peripheral_buffer[15].push=65535^JO_KEY_START;
    jo_get_inputs_vblank();b=mf_input_read_port(1);a=mf_input_read_port(0);
    assert(b.connected && b.held==(MF_LEFT|MF_B|MF_START) && b.pressed==MF_START && b.sdk_slot==6);
    assert(a.held==(MF_RIGHT|MF_A) && a.pressed==MF_A);
    peripheral_buffer[0].id=255;jo_get_inputs_vblank();a=mf_input_read_port(0);
    assert(!a.connected && !a.held && !a.pressed);
    mf_game_init(&g);h[0]=a.held;h[1]=b.held;e[0]=a.pressed;e[1]=b.pressed;
    mf_game_step_inputs(&g,h,e,(a.connected?1u:0u)|(b.connected?2u:0u));
    assert(g.started && g.players[1].active && !g.paused && g.players[1].health==100);
    peripheral_buffer[15].push=65535;jo_get_inputs_vblank();b=mf_input_read_port(1);assert((b.held&MF_START) && !b.pressed);
    peripheral_buffer[15].id=0x16;jo_get_inputs_vblank();assert(mf_input_read_port(1).connected);
    peripheral_buffer[15].id=3;jo_get_inputs_vblank();assert(!mf_input_read_port(1).connected && !mf_input_read_port(1).pressed);
    peripheral_buffer[15].id=255;jo_get_inputs_vblank();assert(!mf_input_read_port(1).connected && !mf_input_read_port(1).held);
    assert(!mf_input_read_port(-1).connected && !mf_input_read_port(2).connected);
    puts("PASS physical P2 slot6 -> active-low Start -> join from inactive/title, device types, held/edge and absent pad");
}
