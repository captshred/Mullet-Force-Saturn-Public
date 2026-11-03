/* Test-only physical-pad sequence; no game memory writes. */
 if(getenv("MF_FAST_BAT_SCENARIO")) {
  int actor=atoi(getenv("MF_FAST_BAT_SCENARIO"));
  if(!controls || port>1 || device!=RETRO_DEVICE_JOYPAD)return 0;
  if(id==RETRO_DEVICE_ID_JOYPAD_START && ((!port && ((tick>=300 && tick<304)||(tick>=320 && tick<324))) || (port==1 && tick>=340 && tick<344)))return 1;
  if((int)port!=actor)return 0;
  if(port==1 && id==RETRO_DEVICE_ID_JOYPAD_DOWN && tick>=345 && tick<362)return 1;
  if(id==RETRO_DEVICE_ID_JOYPAD_RIGHT && (tick==380 || (tick>=384 && tick<450) || tick==465 || (tick>=469 && tick<535) || tick==610 || (tick>=614 && tick<620) || tick==660 || tick==662))return 1;
  if(id==RETRO_DEVICE_ID_JOYPAD_LEFT && (tick==540 || (tick>=544 && tick<585)))return 1;
  if(id==RETRO_DEVICE_ID_JOYPAD_A && tick==600)return 1;
  if(id==RETRO_DEVICE_ID_JOYPAD_B && (tick==(port?414:430) || tick==500 || tick==570 || tick==614 || tick==662))return 1;
  return 0;
 }
