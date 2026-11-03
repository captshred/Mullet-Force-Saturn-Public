#include <jo/jo.h>
#include "input.h"

mf_input mf_input_read_port(int port)
{
    mf_input input = {0};
    int slot;
    if(port<0 || port>1)return input;
    /* Pinned SGL poller copies six devices from each physical connector.
       See Samples/demo - multitap: slots 0..5 are port 1, 6..11 port 2.
       jo_is_pad2_* means logical slot 1, NOT physical connector 2. */
    slot=port?6:0;
    input.sdk_slot=slot;input.device_id=jo_inputs[slot].id;
    input.raw=jo_inputs[slot].data;input.raw_pressed=jo_inputs[slot].push;
    input.type=jo_get_input_type(slot);
    if(!jo_is_input_available(slot) ||
       (input.type!=JoRegularGamepad && input.type!=JoNightsPad))return input;
    input.connected = 1;
    /* Held is suitable for continuous actions; down is a one-frame edge.
     * Jo updates these pad states during its existing VBlank callback. */
#define READ_BUTTON(mask,key) \
    if (jo_is_input_key_pressed(slot,key)) input.held |= mask; \
    if (jo_is_input_key_down(slot,key)) input.pressed |= mask
    READ_BUTTON(MF_UP, JO_KEY_UP);
    READ_BUTTON(MF_DOWN, JO_KEY_DOWN);
    READ_BUTTON(MF_LEFT, JO_KEY_LEFT);
    READ_BUTTON(MF_RIGHT, JO_KEY_RIGHT);
    READ_BUTTON(MF_A, JO_KEY_A);
    READ_BUTTON(MF_B, JO_KEY_B);
    READ_BUTTON(MF_C, JO_KEY_C);
    READ_BUTTON(MF_START, JO_KEY_START);
#undef READ_BUTTON
    return input;
}

/* Physical port 1 compatibility entry point. */
mf_input mf_input_read(void) { return mf_input_read_port(0); }
