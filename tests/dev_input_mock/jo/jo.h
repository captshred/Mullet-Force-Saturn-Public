#ifndef MF_DEV_INPUT_MOCK_H
#define MF_DEV_INPUT_MOCK_H
/* SGL keys, raw active-low data/push and types match the pinned SDK. */
enum { JO_KEY_RIGHT=1<<15,JO_KEY_LEFT=1<<14,JO_KEY_DOWN=1<<13,JO_KEY_UP=1<<12,
       JO_KEY_X=1<<6,JO_KEY_Z=1<<4,JO_KEY_START=1<<11,JO_KEY_A=1<<10,JO_KEY_B=1<<8,JO_KEY_C=1<<9 };
enum { JoNotConnectedGamepad=-1,JoUnsupportedGamepad=0,JoRegularGamepad=1,
       JoRegularMouse=2,JoNightsPad=5 };
typedef struct { unsigned char id,ext;unsigned short data,push,pull;unsigned int dummy2[4]; } PerDigital;
extern PerDigital jo_inputs[12];
int jo_is_input_available(int port);
int jo_get_input_type(int port);
int jo_is_input_key_pressed(int port,int key);
int jo_is_input_key_down(int port,int key);
#endif
