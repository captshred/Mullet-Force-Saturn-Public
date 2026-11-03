"""Select expected allocation from durable BUILD-INFO, including downloaded ZIPs."""
import json
def texture_profile(root,build):
 info=(build/'BUILD-INFO.txt').read_text()
 for label,directory in [('HQ player death / final Chuck fix','player-death'),('HQ player hurt / Chuck cleanup','player-hurt'),('Corporate Punk HQ combat','corporate-punk-hq-combat'),('HQ jump','hq-jump'),('HQ torch','hq-torch')]:
  if f'{label}: 1' in info:return json.loads((root/f'assets/{directory}/manifest.json').read_text())
 return json.loads((root/'assets/attack-sequence/manifest.json').read_text())
