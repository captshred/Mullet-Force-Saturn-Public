#ifndef MF_INPUT_H
#define MF_INPUT_H
/* Game-facing masks keep engine input details in input.c. */
enum { MF_UP=1, MF_DOWN=2, MF_LEFT=4, MF_RIGHT=8, MF_A=16, MF_START=32, MF_B=64, MF_C=128, MF_X=256 };
/* physical_port is zero-based 0/1; sdk_slot is explicitly 0/6 with SGL. */
typedef struct {
    unsigned int connected,held,pressed;
    unsigned int sdk_slot,device_id,raw,raw_pressed;
    int type;
} mf_input;
mf_input mf_input_read(void);
mf_input mf_input_read_port(int port);
#endif
