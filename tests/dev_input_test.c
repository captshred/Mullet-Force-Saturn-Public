#include <assert.h>
#include <stdio.h>
#include <jo/jo.h>
#include "input.h"
PerDigital jo_inputs[12];
int jo_is_input_available(int p){return jo_inputs[p].id==2;}
int jo_get_input_type(int p){(void)p;return JoRegularGamepad;}
int jo_is_input_key_pressed(int p,int key){return !(jo_inputs[p].data&key);}
int jo_is_input_key_down(int p,int key){return !(jo_inputs[p].push&key);}
int main(void)
{
    int i;for(i=0;i<2;i++){
        int slot=i?6:0;mf_input a;jo_inputs[slot].id=2;
        jo_inputs[slot].data=jo_inputs[slot].push=65535^JO_KEY_Z;a=mf_input_read_port(i);
#if MF_DEV_STAGE_SKIP
        assert(a.held==MF_Z && a.pressed==MF_Z);
        jo_inputs[slot].push=65535;a=mf_input_read_port(i);assert(a.held==MF_Z && !a.pressed);
#else
        assert(!a.held && !a.pressed);
#endif
    }
    puts("PASS Jo Saturn Z: active-low physical ports 0/6, press versus held, no release mapping");
}
