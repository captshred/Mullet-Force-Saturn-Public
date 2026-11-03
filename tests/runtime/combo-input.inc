/* Physical input only, no save-state writes or game hooks. */
 if(getenv("MF_COMBO_SCENARIO")) {
  int mirror=atoi(getenv("MF_COMBO_SCENARIO"));unsigned delay=port?4:0;
  if(!controls || port>1 || device!=RETRO_DEVICE_JOYPAD)return 0;
  if(getenv("MF_COMBO_SINGLE") && port==1)return 0;
  if(id==RETRO_DEVICE_ID_JOYPAD_START && ((!port && ((tick>=300 && tick<304)||(tick>=320 && tick<324))) || (port==1 && tick>=340 && tick<344)))return 1;
  if(mirror && id==RETRO_DEVICE_ID_JOYPAD_LEFT && tick==380)return 1;
  if(id==RETRO_DEVICE_ID_JOYPAD_B && (tick==400+delay || tick==409+delay || tick==421+delay || tick==437+delay || tick==449+delay || tick==461+delay || tick==600+delay))return 1;
  return 0;
 }
