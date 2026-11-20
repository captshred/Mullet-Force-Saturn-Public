#!/usr/bin/env python3
"""Build the indexed Phase 4A apron with the existing Level 1 palette."""
import argparse
import random
import struct
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[1]
art = root / 'assets/level1-intersection'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
height, old_width, width = 368, 2560, 768
approved = np.fromfile(art / 'IXPIX.BIN', np.uint8).reshape(height, -1)[:, :old_width]
palette = np.array([[0, 0, 0]] + [[(v >> s & 31) * 255 // 31 for s in (0, 5, 10)]
    for v in struct.unpack('>255H', (root / 'assets/level1-neon-strip/NSPAL.BIN').read_bytes())])
colors = np.arange(1, 240)
rng = random.Random(4419)
im = Image.new('P', (width, height))
im.putpalette(palette.astype(np.uint8).ravel())
draw = ImageDraw.Draw(im)


@lru_cache(maxsize=None)
def index(hex_rgb):
    values = np.array(list(bytes.fromhex(hex_rgb)))
    return int(colors[np.argmin(np.sum((palette[colors] - values) ** 2, axis=1))])


def box(x0, y0, x1, y1, color):
    draw.rectangle((x0, y0, x1, y1), fill=index(color))


def line(points, color, width=1):
    draw.line(points, fill=index(color), width=width)


def poly(points, color):
    draw.polygon(points, fill=index(color))


# Night sky behind the low-rise destination, with restrained distant lights.
for y in range(height):
    t = min(1, y / 285)
    c = (11 + int(t * 15), 11 + int(t * 10), 32 + int(t * 21))
    box(0, y, width - 1, y, bytes(c).hex())
for x in range(3, width, 12):
    if rng.randrange(3) == 0:
        box(x, rng.randrange(135, 181), x, 184, '171831')
for x in range(15, width, 18):
    w, top = rng.randrange(9, 26), rng.randrange(156, 241)
    box(x, top, x+w, 270, '171a35')
    box(x, top, x+3, 270, '1c2040')
    for wy in range(top+5, 265, 6):
        for wx in range(x+4, x+w-1, 4):
            if rng.randrange(5) == 0:
                box(wx, wy, wx+1, wy+1, rng.choice(('2f465c','57465e','685259')))
for x, top, span in ((562,208,19),(592,194,23),(628,217,16),(657,202,24),(695,192,23),
                     (731,211,22),(760,200,18)):
    box(x-1, top+17, x+1, 275, '111427')
    for yc, scale in ((top+8,.55),(top+16,.82),(top+24,1)):
        w = int(span*scale)
        poly([(x-w,yc+7),(x-w+3,yc-1),(x-5,yc-5),(x,yc-11),
              (x+6,yc-6),(x+w-3,yc-2),(x+w,yc+6)], '101529')
    line([(x-7,top+5),(x-3,top),(x+1,top)], '222944')

# Long curb and asphalt. Near the old road the treatment remains darker.
for y in range(262, height):
    for x in range(0, width, 8):
        color = '21263d' if y>=289 else '383549'
        if rng.randrange(5) == 0:
            color = '26293f' if y>=289 else '403b4e'
        box(x,y,x+7,y,color)
for y,c in ((277,'4d485d'),(278,'5c5164'),(281,'242535'),(283,'5c5265'),(285,'121827'),
            (287,'34344b'),(288,'191e32')):
    box(0,y,width-1,y,c)
for x in range(10,width,29):
    line([(x+8,262),(x,282)],'28283e')
    box(x,283,x,285,'393849')
for x in range(115,width,27):
    line([(x,290),(x-7,307)],'686274')
    line([(x,291),(x-7,308)],'3c3b50')
for x,y in ((144,339),(211,326),(297,348),(421,321),(541,351),(613,335),(733,346)):
    line([(x,y),(x+10,y),(x+17,y+3),(x+31,y+3)],'161a2c')
    line([(x+15,y+3),(x+13,y+8)],'252a43')
for x,y in ((113,335),(230,304),(491,337),(607,318),(713,305)):
    draw.ellipse((x,y,x+14,y+4),fill=index('191e32'))
for _ in range(900):
    x,y=rng.randrange(width),rng.randrange(291,height)
    draw.point((x,y),fill=index(rng.choice(('293047','252940','181e33','292740'))))
for x in range(199,width,35):
    line([(x,363),(x+16,363)],'414259')


def car(x, y, body, shine):
    """Low-resolution period coupe facing right, with a squared-off cabin."""
    box(x+1,y+1,x+46,y+4,'121629')
    poly([(x,y-3),(x+3,y-9),(x+12,y-10),(x+18,y-16),(x+30,y-16),
          (x+37,y-10),(x+43,y-8),(x+45,y-4),(x+45,y),(x,y)],body)
    poly([(x+14,y-10),(x+19,y-15),(x+29,y-15),(x+35,y-10)],'202a49')
    line([(x+15,y-10),(x+20,y-15),(x+29,y-15),(x+33,y-12)],shine)
    box(x+25,y-14,x+25,y-10,'13192b')
    line([(x+4,y-8),(x+12,y-8),(x+34,y-8),(x+42,y-6)],shine)
    box(x+1,y-5,x+3,y-4,'b7365d')
    box(x+42,y-5,x+45,y-4,'d4b576')
    for tx in (x+9,x+35):
        box(tx-3,y-2,tx+3,y+3,'101321')
        box(tx-1,y,tx+1,y+1,'666579')
    box(x+1,y-1,x+4,y,'696475')
    box(x+40,y-1,x+45,y,'696475')


# Freestanding three-deck extension at the foot of the hill.
box(0,154,174,268,'343044')
box(10,146,164,154,'55455e')
box(10,146,164,147,'786477')
for x in range(14,169,20):
    box(x,140,x+1,147,'545163')
line([(13,141),(168,141)],'a56b77')
for floor,y in enumerate((154,190,226)):
    for a,b in ((9,78),(86,166)):
        box(a,y+3,b,y+30,'111427')
        box(a+3,y+5,b-3,y+26,'191d34')
        poly([(a+3,y+7),(a+17,y+12),(a+17,y+29),(a+3,y+29)],'272640')
        box(a+14,y+8,a+33,y+8,('85b39d','9bb39f','77bbc2')[floor])
    car(25+floor*6,y+28,('333c6c','702c58','51576f')[floor],
        ('537fa2','ac5277','9b92ae')[floor])
    car(100+floor*3,y+28,('68616d','344c67','784246')[floor],
        ('a29a9e','5487a0','b47869')[floor])
    for a,b in ((7,78),(86,168)):
        line([(a,y+23),(b,y+23)],'815768')
        line([(a,y+28),(b,y+28)],'634451')
        for x in range(a+6,b,19):
            box(x,y+23,x,y+29,'9a6872')
    box(0,y+31,174,y+35,'544357')
    box(0,y+31,174,y+31,'8d6b75')
    box(0,y+35,174,y+35,'26263e')
for x in (1,78,167):
    box(x,151,x+8,268,'4b4158')
    box(x,151,x+1,268,'766071')
    for y in (169,205,241):
        box(x+2,y,x+6,y+6,'6f4052')
        box(x+3,y+1,x+5,y+4,'c68e60')
        box(x+4,y+2,x+4,y+4,'ffe1a2')

# Layered late-eighties entertainment complex with a recessed vestibule.
box(180,182,536,275,'292442')
box(185,167,529,181,'3c2c54')
box(211,153,506,168,'442b5a')
box(217,149,500,152,'644270')
box(223,145,494,148,'382a52')
for x in range(197,529,12):
    line([(x,174),(x,270)],'382b52')
for x in (192,514):
    box(x,175,x+11,277,'4a315d')
    box(x+2,178,x+3,273,'775285')
    box(x+8,181,x+8,273,'54315c')
for y,c in ((159,'754579'),(167,'603558'),(182,'1a1a31'),(212,'674266'),(216,'253c61'),
            (217,'5186a6'),(221,'191e36'),(272,'59345c'),(275,'4a415e')):
    box(183,y,534,y,c)
poly([(208,174),(230,159),(487,159),(510,174),(510,209),(490,216),(230,216),(208,203)],'252139')
poly([(211,176),(231,161),(486,161),(507,176),(507,205),(488,213),(230,213),(211,202)],'762e62')
poly([(215,177),(235,164),(483,164),(503,177),(503,202),(484,210),(235,210),(215,201)],'171927')
line([(218,178),(235,166),(483,166),(499,178)],'bc427c',2)
line([(218,201),(236,207),(482,207),(499,201)],'426fba',2)
for x in range(224,497,7):
    box(x,203,x+2,203,'855085')

glyphs = {
    'M': ('10001','11011','10101','10101','10001','10001','10001'),
    'E': ('11111','10000','10000','11110','10000','10000','11111'),
    'G': ('01111','10000','10000','10111','10001','10001','01111'),
    'A': ('01110','11011','10001','11111','10001','10001','10001'),
    'R': ('11110','10001','10001','11110','10100','10010','10001'),
    'C': ('01111','10000','10000','10000','10000','10000','01111'),
    'D': ('11110','10001','10001','10001','10001','10001','11110'),
}
for text, x0 in (('MEGA',229),('ARCADE',340)):
    for i,char in enumerate(text):
        for row, pixels in enumerate(glyphs[char]):
            for col, bit in enumerate(pixels):
                if bit!='1':
                    continue
                x,y=x0+i*25+col*4,174+row*4
                box(x-1,y-1,x+4,y+4,'79335d' if text=='MEGA' else '24516e')
                box(x,y,x+3,y+3,'dc5a96' if text=='MEGA' else '63afce')
                box(x,y,x+2,y+2,'f0a9be' if text=='MEGA' else '9be0db')

for x in (209,402):
    box(x,226,x+92,265,'544064')
    box(x+2,228,x+90,262,'151a32')
    for k in range(4,90,14):
        box(x+k,237,x+k+9,256,'242b51')
        box(x+k+2,239,x+k+7,244,('387791' if k%3 else '823e72'))
        box(x+k+3,240,x+k+6,241,'8076ad')
        box(x+k+1,245,x+k+8,246,'65438b')
    for dx in (29,60):
        box(x+dx,228,x+dx+1,263,'353352')
    box(x,266,x+92,269,'72506d')

box(309,225,396,275,'151729')
poly([(309,225),(321,234),(321,268),(309,275)],'4b3257')
poly([(396,225),(383,234),(383,268),(396,275)],'302b51')
poly([(309,225),(396,225),(383,234),(321,234)],'534273')
box(322,235,382,267,'241e39')
box(328,235,377,236,'7db3c0')
for left in (327,354):
    box(left,240,left+22,267,'97567b')
    box(left+2,242,left+20,265,'294361')
    box(left+5,244,left+17,254,'344c72')
    box(left+4,260,left+18,265,'233452')
    box(left+3,244,left+3,265,'59689d')
    box(left+17,256,left+19,257,'d5be95')
for y,c in ((268,'4e507b'),(270,'69728c'),(272,'39394e'),(275,'646078')):
    box(320,y,384,y,c)
poly([(320,276),(384,276),(407,298),(296,298)],'42435c')
line([(320,276),(296,298),(406,298),(383,276)],'5b5c73')
for i in range(6):
    line([(305+i*16,291),(312+i*14,285)],'52546f')

# Edge parking and lamps, with the entire front combat lane left clear.
car(117,284,'574161','a26590')
car(584,283,'3c4d6b','6896a8')
car(675,284,'624457','a46676')
for x in (566,742):
    box(x,232,x+2,282,'33354f')
    box(x,232,x,281,'66677d')
    line([(x,232),(x+9,228),(x+19,228)],'75718b',2)
    box(x+13,229,x+20,232,'b8a480')
    box(x+15,231,x+20,231,'f5d5a0')
    box(x-3,283,x+5,285,'444355')

# Match the old end at the join, then dissipate that edge's color influence.
# This touches only new pixels and adds no repeated scenery to the world.
new = np.array(im)
for x in range(24):
    amount = (x+1) / 25
    blend = palette[approved[:, -1]] * (1-amount) + palette[new[:,x]] * amount
    dist = np.sum((blend[:,None,:] - palette[colors])**2,axis=2)
    # Preserve the old boundary at column zero, but keep the extension opaque.
    new[:,x] = colors[dist.argmin(axis=1)]
new[:,0] = np.where(approved[:,-1] != 0, approved[:,-1], new[:,0])
assert np.all(new)
args.output.write_bytes(np.concatenate([approved,new],axis=1).tobytes())
preview = Image.fromarray(palette[new].astype(np.uint8))
preview.crop((0,127,width,height)).save(args.output.with_suffix('.png'))
