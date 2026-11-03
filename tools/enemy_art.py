"""Original suit-wearing antagonist. All pixel geometry is authored at 1:1.
Dark tailored suit, open lapels, pale shirt, red tie, dress shoes, green mohawk.
Ground anchor: (canvas width/2,92). No source-game/cover pixels are reused.
"""
from PIL import Image,ImageDraw
KEY=(255,0,255)
FRAME_NAMES=['idle','guard','walk-L','pass-L','walk-R','pass-R','windup','punch','recover','hit','fall','defeated']
O='#101820'; SUIT='#283040'; MID='#404858'; RIM='#606878'; SHIRT='#b8b8b0'
SKIN='#c09880'; LIGHT='#e0b898'; SHADE='#886858'; GREEN='#68e848'; GH='#b0f878'; GS='#288838'
def draw_enemy(f):
    w=112 if f in (7,10,11) else 72; a=w//2
    im=Image.new('RGB',(w,96),KEY);q=ImageDraw.Draw(im)
    def poly(p,c,edge=O):
        p=[(x+a,y) for x,y in p];q.polygon(p,fill=c)
        if edge:q.line(p+[p[0]],fill=edge,width=1)
    def line(p,c,n=1):q.line([(x+a,y) for x,y in p],fill=c,width=n)
    def rect(p,c):x,y,x2,y2=p;q.rectangle((x+a,y,x2+a,y2),fill=c)
    if f==11:
        # Authored side-on floor pose with separated knees, shirt and shoes.
        poly([(-41,81),(-26,77),(-16,79),(4,80),(15,77),(30,81),(44,86),
              (47,91),(31,92),(15,89),(3,91),(-17,90),(-27,87),(-41,88)],SUIT)
        poly([(-22,79),(-14,80),(-9,87),(-20,86)],SHIRT)
        line([(-15,81),(-12,86)],'#a85860',2)
        poly([(-42,78),(-35,75),(-27,78),(-27,85),(-34,89),(-41,86)],SKIN)
        line([(-41,78),(-39,74),(-36,76),(-34,72),(-32,77),(-28,76)],GREEN,2)
        line([(-37,82),(-34,82)],O);line([(-32,84),(-29,84)],SHADE)
        poly([(30,82),(37,82),(43,86),(49,88),(48,92),(34,92)],O)
        line([(35,91),(47,91)],RIM)
        line([(-9,86),(5,87),(14,84),(29,88)],MID,2)
        poly([(-18,84),(-5,81),(9,86),(8,90),(-4,86),(-15,89)],MID)
        rect((8,86,13,89),SKIN)
        return im
    bob=1 if f in (1,3,5,8) else (8 if f==10 else 0)
    lean=-5 if f in (6,9,10) else (4 if f==7 else 0)
    def leg(h,k,foot,far=False):
        hx,hy=h;kx,ky=k;fx,fy=foot
        poly([(hx-4,hy),(hx+4,hy),(kx+4,ky),(fx+3,fy),(fx-4,fy),(kx-4,ky)],SUIT)
        line([(hx-2,hy+3),(kx-1,ky),(fx-2,fy-3)],MID if far else RIM)
        line([(kx+2,ky+2),(fx+1,fy-4)],O)
        poly([(fx-4,fy-3),(fx+3,fy-3),(fx+10,fy+2),(fx+10,fy+4),(fx-5,fy+4)],O)
        line([(fx-2,fy-1),(fx+3,fy),(fx+6,fy+1)],MID)
        line([(fx-4,fy+3),(fx+9,fy+3)],RIM)
    legs={2:((15,71),(18,88),(-13,73),(-18,88)),3:((1,69),(-6,84),(4,73),(9,88)),
          4:((-10,73),(-15,88),(15,71),(19,88)),5:((4,73),(9,88),(1,69),(-6,84))}
    k1,ft1,k2,ft2=legs.get(f,((12,72),(14,88),(-11,73),(-15,88)))
    if f==10:k1,ft1,k2,ft2=(18,79),(18,88),(-19,80),(-15,88)
    leg((5,54+bob),k1,ft1,True);leg((-6,54+bob),k2,ft2)
    # Broad but tailored shoulders and waist; alternating legs do not resize torso.
    poly([(lean-12,28+bob),(lean-3,26+bob),(lean+6,27+bob),(lean+14,31+bob),
          (lean+11,42+bob),(9,56+bob),(-11,56+bob),(lean-15,39+bob),(lean-16,32+bob)],SUIT)
    poly([(lean-2,27+bob),(lean+5,28+bob),(lean+4,45+bob),(0,50+bob),(lean-5,35+bob)],SHIRT)
    poly([(lean,29+bob),(lean+3,31+bob),(lean+1,35+bob),(lean+4,46+bob),
          (lean+1,49+bob),(lean-2,45+bob),(lean-1,34+bob)],'#984858')
    line([(lean+1,35+bob),(lean+2,44+bob)],'#c07878')
    poly([(lean-10,29+bob),(lean-4,29+bob),(lean-2,35+bob),(lean-5,39+bob),(lean-8,33+bob)],MID)
    poly([(lean+6,28+bob),(lean+11,31+bob),(lean+5,40+bob),(lean+3,35+bob)],MID)
    line([(lean-13,31+bob),(lean-10,30+bob),(lean-7,32+bob)],RIM)
    line([(lean+10,42+bob),(6,53+bob)],RIM)
    rect((1,46+bob,2,47+bob),RIM);rect((0,51+bob,1,52+bob),RIM)
    line([(-10,54+bob),(-3,53+bob),(-1,55+bob)],MID)
    # Neck and adult profile, uncovered brow and short side shave.
    poly([(lean-4,22+bob),(lean+3,22+bob),(lean+3,28+bob),(lean-1,29+bob),(lean-5,26+bob)],SHADE)
    poly([(lean-6,12+bob),(lean+3,10+bob),(lean+7,13+bob),(lean+7,17+bob),
          (lean+9,19+bob),(lean+7,20+bob),(lean+6,24+bob),(lean+2,26+bob),
          (lean-3,23+bob),(lean-6,20+bob)],SKIN)
    line([(lean+1,21+bob),(lean+4,20+bob)],LIGHT)
    line([(lean+2,23+bob),(lean+5,23+bob)],O)
    line([(lean-3,21+bob),(lean,24+bob)],SHADE)
    line([(lean+2,15+bob),(lean+5,16+bob)],O,2)
    rect((lean+4,17+bob,lean+5,17+bob),O)
    line([(lean+7,18+bob),(lean+8,19+bob)],LIGHT)
    rect((lean-7,16+bob,lean-5,20+bob),SHADE)
    line([(lean-6,17+bob),(lean-5,18+bob)],LIGHT)
    # Distinct narrow bright mohawk crest with a shaved dark side plane.
    poly([(lean-6,14+bob),(lean-7,10+bob),(lean-4,8+bob),(lean-3,4+bob),
          (lean,6+bob),(lean+1,3+bob),(lean+4,6+bob),(lean+6,5+bob),
          (lean+8,10+bob),(lean+4,12+bob),(lean-1,11+bob),(lean-4,15+bob)],GS)
    poly([(lean-4,10+bob),(lean-3,5+bob),(lean,8+bob),(lean+2,5+bob),
          (lean+4,8+bob),(lean+6,7+bob),(lean+6,10+bob),(lean,10+bob)],GREEN,None)
    line([(lean-2,6+bob),(lean-1,8+bob),(lean+1,7+bob)],GH)
    def arm(s,e,h,far=False):
        sx,sy=s;ex,ey=e;hx,hy=h
        poly([(sx-4,sy-2),(sx+4,sy-2),(ex+4,ey),(ex+3,ey+4),(ex-4,ey+4),(ex-5,ey)],SUIT)
        poly([(ex-4,ey),(ex+3,ey+3),(hx+3,hy+3),(hx+3,hy-3),(hx-3,hy-3)],SUIT)
        line([(sx-2,sy),(ex-2,ey),(hx-1,hy-1)],MID if far else RIM,2)
        line([(hx-3,hy+1),(hx+2,hy+2)],SHIRT,2)
        poly([(hx-3,hy-5),(hx+2,hy-6),(hx+5,hy-3),(hx+3,hy+1),(hx-2,hy+1),(hx-4,hy-2)],SKIN)
        line([(hx,hy-4),(hx+3,hy-3)],LIGHT)
        line([(hx,hy-1),(hx+3,hy-1)],SHADE)
    arm((lean-12,32+bob),(lean-14,43+bob),(lean-1,35+bob),True)
    if f==7:arm((lean+11,32),(27,36),(39,39))
    elif f==6:arm((lean+11,32+bob),(lean+18,43+bob),(lean+9,34+bob))
    elif f in (9,10):arm((lean+11,32+bob),(lean+17,42+bob),(lean+9,45+bob))
    else:arm((lean+11,32+bob),(lean+20,43+bob),(lean+23,32+bob))
    return im
