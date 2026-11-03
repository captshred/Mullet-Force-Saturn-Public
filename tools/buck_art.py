"""Original Buck pixel construction, drawn at final screen resolution.
The reference is athletic fighting anatomy, not any game's pixels or costume.
Local x=0 is the shared ground anchor. y=92 is the sole baseline.
"""
from PIL import Image, ImageDraw
FRAME_NAMES=['idle-guard','idle-breathe','walk-contact-L','walk-down-L','walk-pass-L',
             'walk-contact-R','walk-down-R','walk-pass-R','punch-coil','punch-contact',
             'punch-recover','jump-takeoff','jump-air','jump-land','jump-kick']
KEY=(255,0,255)
# Restrained shared clusters: cold silver against warm hair/skin, dark clothing.
INK='#101820'; EDGE='#283040'; DEEP='#384860'; SHADE='#586880'
SILVER='#98a8b8'; LIGHT='#c8d8e0'; GLINT='#e8f0e8'; CYAN='#80c8d0'
SKIN='#c89070'; SKIN_SH='#906050'; SKIN_HI='#e8b890'
HAIR_SH='#887850'; HAIR='#c8b078'; HAIR_HI='#f0d898'
CLOTH='#182030'; PANT='#283848'; PANT_HI='#485870'; BOOT='#182028'; SOLE='#708088'
GLOVE='#283038'; GLOVE_HI='#586068'
# Screen coordinates are y-down. These vectors turn counterclockwise through
# the actual strike, independently authored wind-up and recovery included.
BAT_GRIPS=[(4,37),(-1,40),(23,43),(27,38),(22,29),(0,28),(5,32)]
BAT_TIPS=[(-30,62),(-35,72),(68,74),(82,40),(55,7),(-36,9),(-34,25)]
BAT_REAR_ELBOWS=[(-9,49),(-10,50),(0,49),(0,46),(0,39),(-13,40),(-12,42)]
BAT_FRONT_ELBOWS=[(18,45),(13,48),(21,51),(18,50),(25,42),(13,40),(18,43)]
def draw_buck(f, chuck=False):
    # Shared skeleton and face proportions; separately authored costume/arms.
    HAIR_SH,HAIR,HAIR_HI=("#503828","#886040","#b89060") if chuck else ("#887850","#c8b078","#f0d898")
    J_SH,J_MID,J_LIGHT,J_GLINT=("#202830","#303840","#505860","#707880") if chuck else (SHADE,SILVER,LIGHT,GLINT)
    w=192 if 15<=f<=21 else (112 if f in (9,14) or f>=22 else 72)
    anchor=w//2
    im=Image.new('RGB',(w,96),KEY); d=ImageDraw.Draw(im)
    def pts(p): return [(x+anchor,y) for x,y in p]
    def poly(p,c,outline=INK):
        p=pts(p); d.polygon(p,fill=c)
        if outline: d.line(p+[p[0]],fill=outline,width=1)
    def line(p,c,width=1): d.line(pts(p),fill=c,width=width)
    def box(x0,y0,x1,y1,c): d.rectangle((x0+anchor,y0,x1+anchor,y1),fill=c)
    def ellipse(x0,y0,x1,y1,c,outline=None): d.ellipse((x0+anchor,y0,x1+anchor,y1),fill=c,outline=outline)
    # Skeleton poses: (hip shift, ribcage shift, vertical compression).
    pose={0:(0,0,0),1:(0,0,1),2:(0,-1,0),3:(-1,-2,2),4:(0,0,1),
          5:(1,1,0),6:(1,2,2),7:(0,0,1),8:(-2,-4,2),9:(2,5,0),
          10:(1,2,1),11:(-1,-2,5),12:(0,0,-1),13:(-1,-2,6),14:(1,2,0),15:(0,-3,0),16:(0,-5,0),17:(0,1,0),
          18:(0,5,0),19:(0,4,0),20:(0,0,0),21:(0,-1,0),22:(0,-2,0),23:(0,2,0),24:(0,-1,0)}
    hip,torso,bob=pose[f]
    # Leg chains are separately posed hips -> knees -> ankle, with shaped
    # calf clusters, knee caps, boot insteps and grounded soles.
    def leg(h,k,a,far=False):
        hx,hy=h; kx,ky=k; ax,ay=a
        c=DEEP if far else PANT
        poly([(hx-5,hy),(hx+5,hy+1),(kx+5,ky-2),(kx+4,ky+4),
              (ax+4,ay),(ax-4,ay),(kx-4,ky+3),(kx-5,ky-1)],c)
        poly([(hx-3,hy+2),(hx,hy+3),(kx+1,ky-2),(kx-2,ky+2),(ax-1,ay-2),(ax-3,ay-1),(kx-4,ky)],SHADE if far else PANT_HI,None)
        poly([(kx-4,ky-2),(kx+3,ky-1),(kx+3,ky+3),(kx-3,ky+4)],PANT,None)
        line([(kx-2,ky),(kx+2,ky)],SHADE)
        # Shin/boot: boot top follows ankle; heel and toe stay connected.
        poly([(ax-4,ay-6),(ax+4,ay-6),(ax+4,ay-1),(ax+10,ay+2),
              (ax+11,ay+5),(ax-5,ay+5),(ax-5,ay+1)],BOOT)
        line([(ax-3,ay-5),(ax+2,ay-5),(ax+2,ay)],SHADE)
        line([(ax-4,ay+4),(ax+10,ay+4)],SOLE)
        line([(ax-1,ay-1),(ax+4,ay)],GLOVE_HI)
        line([(ax-2,ay-3),(ax+1,ay-3)],LIGHT)
    if f in (12,14):
        leg((hip+5,53+bob),(15,64),(6,74),True)
        if f==14:
            # Long horizontal side kick; articulated thigh/knee and heel.
            poly([(-5,53),(3,49),(22,54),(31,55),(47,52),(49,60),
                  (30,64),(21,62),(2,63),(-6,60)],PANT)
            poly([(1,52),(20,57),(30,58),(45,55),(45,57),(29,61),(19,60),(2,56)],PANT_HI,None)
            line([(24,55),(27,60)],SHADE,2)
            poly([(43,51),(50,49),(51,52),(50,58),(54,61),(53,64),(43,63),(42,58)],BOOT)
            line([(51,51),(49,57),(52,62)],SOLE)
            line([(44,53),(48,53)],LIGHT)
        else:
            leg((hip-6,53+bob),(-1,65),(-14,76),False)
    else:
        # Six distinct contacts/passes, no rubber-leg horizontal translation.
        knees=[(11,70),(-10,72)]; ankles=[(14,87),(-15,87)]
        walk={2:([(14,70),(-12,72)],[(20,87),(-20,87)]),
              3:([(10,72),(-13,73)],[(15,87),(-16,87)]),
              4:([(1,71),(4,70)],[(-8,84),(9,87)]),
              5:([(-9,72),(15,70)],[(-17,87),(18,87)]),
              6:([(-9,73),(12,72)],[(-12,87),(14,87)]),
              7:([(2,70),(1,71)],[(9,87),(-6,84)])}
        if f in walk: knees,ankles=walk[f]
        if f in (11,13): knees=[(17,73),(-17,75)]
        leg((hip+5,54+bob),knees[0],ankles[0],True)
        leg((hip-6,54+bob),knees[1],ankles[1],False)
    # Light mullet tail behind raised collar. Narrow locks, no Charlie forelock.
    hx=torso+1; hy=bob
    sway=-1 if f in (3,6,8) else (1 if f in (4,7,9) else 0)
    poly([(hx-7,17+hy),(hx-11,19+hy),(hx-14+sway,27+hy),
          (hx-12+sway,34+hy),(hx-8+sway,39+hy),(hx-4+sway,35+hy),
          (hx-6,28+hy),(hx-4,21+hy)],HAIR_SH)
    poly([(hx-9,20+hy),(hx-11+sway,28+hy),(hx-8+sway,35+hy),
          (hx-7+sway,32+hy),(hx-8,25+hy),(hx-5,20+hy)],HAIR,None)
    line([(hx-11,24+hy),(hx-12+sway,29+hy),(hx-9+sway,34+hy)],HAIR_HI)
    # Rear shoulder/arm guard, warm knuckles visible through fingerless glove.
    def arm(s,e,hand,near):
        sx,sy=s; ex,ey=e; fx,fy=hand
        if chuck:
            # Exposed deltoid -> biceps -> elbow -> forearm. No sleeve/cuff.
            poly([(sx-4,sy-3),(sx+4,sy-3),(sx+6,sy+2),(ex+5,ey-3),
                  (ex+4,ey+3),(ex,ey+5),(ex-4,ey+3),(sx-5,sy+3)],SKIN if near else SKIN_SH)
            poly([(sx-2,sy-2),(sx+2,sy-1),(ex+2,ey-2),(ex-1,ey),
                  (sx-3,sy+2)],SKIN_HI if near else SKIN,None)
            line([(sx+3,sy+3),(ex+3,ey-1)],SKIN_SH)
            poly([(ex-4,ey-1),(ex+2,ey+3),(fx+3,fy+3),(fx+3,fy-2),
                  (fx-2,fy-4),(ex-4,ey-3)],SKIN if near else SKIN_SH)
            line([(ex-2,ey),(fx,fy-2)],SKIN_HI if near else SKIN,2)
            line([(ex+1,ey+3),(fx+2,fy+1)],SKIN_SH)
            # Black cut-off armhole and frayed denim edge at the shoulder.
            line([(sx-4,sy-3),(sx,sy-5),(sx+4,sy-3)],J_LIGHT,2)
            line([(sx-3,sy-2),(sx-2,sy),(sx,sy-2),(sx+2,sy)],J_MID)
            ellipse(fx-4,fy-1,fx+3,fy+4,GLOVE)
        else:
            poly([(sx-4,sy-3),(sx+5,sy-2),(ex+5,ey-2),(ex+4,ey+4),
                  (ex-4,ey+5),(ex-5,ey)],SILVER if near else SHADE)
            poly([(sx-3,sy-2),(sx+1,sy-2),(ex+1,ey),(ex-3,ey+1)],LIGHT if near else SILVER,None)
            poly([(ex-4,ey),(ex+4,ey+2),(fx+4,fy+3),(fx+3,fy-3),
                  (fx-3,fy-4),(ex-5,ey-2)],SILVER if near else DEEP)
            line([(ex-2,ey),(fx,fy-2)],GLINT if near else SILVER,2)
            line([(ex+2,ey+3),(fx+3,fy+1)],SHADE)
            # Ribbed cuff follows the wrist rather than floating away from sleeve.
            ellipse(fx-4,fy-1,fx+3,fy+4,DEEP)
            line([(fx-3,fy+2),(fx+2,fy+3)],LIGHT)
        poly([(fx-4,fy-6),(fx+2,fy-7),(fx+5,fy-4),(fx+4,fy+1),
              (fx,fy+3),(fx-4,fy)],GLOVE)
        line([(fx-2,fy-5),(fx+2,fy-5),(fx+3,fy-3)],GLOVE_HI,2)
        line([(fx,fy-6),(fx+2,fy-6)],SKIN_HI)
        line([(fx-2,fy-3),(fx+2,fy-3)],INK)
    # Athletic tapered torso: broad shoulder shelf, ribcage, narrow waist.
    poly([(torso-11,28+bob),(torso-2,26+bob),(torso+7,27+bob),
          (torso+15,32+bob),(torso+11,42+bob),(hip+9,55+bob),
          (hip-11,55+bob),(torso-15,40+bob),(torso-16,33+bob)],J_MID)
    # Dark shirt and narrow waist remain visible between open metallic panels.
    poly([(torso-3,29+bob),(torso+5,28+bob),(torso+6,38+bob),
          (hip+5,52+bob),(hip-5,52+bob),(torso-6,40+bob)],CLOTH,None)
    line([(torso-2,36+bob),(torso+3,37+bob)],J_SH)
    line([(torso-2,43+bob),(torso+2,44+bob)],EDGE)
    poly([(torso-11,30+bob),(torso-6,32+bob),(torso-7,42+bob),
          (hip-5,52+bob),(hip-10,52+bob),(torso-13,39+bob)],J_SH,None)
    poly([(torso+8,30+bob),(torso+12,32+bob),(torso+8,42+bob),
          (hip+8,52+bob),(hip+4,51+bob),(torso+5,40+bob)],J_LIGHT,None)
    # Bright shoulder, collar lapels, seam and jacket fold clusters.
    line([(torso-13,31+bob),(torso-10,29+bob),(torso-6,30+bob)],J_GLINT,2)
    poly([(torso-7,25+bob),(torso-2,29+bob),(torso-4,35+bob),
          (torso-9,30+bob)],J_LIGHT)
    poly([(torso+5,25+bob),(torso+9,28+bob),(torso+4,35+bob),
          (torso+3,29+bob)],J_GLINT)
    line([(torso-12,38+bob),(torso-9,40+bob),(torso-8,38+bob)],J_LIGHT)
    line([(torso-10,44+bob),(hip-7,46+bob),(hip-8,49+bob)],DEEP)
    line([(torso+8,41+bob),(torso+5,44+bob),(hip+7,46+bob)],J_SH)
    box(torso-12,34+bob,torso-8,37+bob,'#704058')
    line([(torso-11,35+bob),(torso-9,35+bob)],'#e8b888')
    if chuck:
        # Denim pocket flaps, flat black lapels and short raw-cut hem.
        poly([(torso-11,34+bob),(torso-6,34+bob),(torso-6,38+bob),
              (torso-9,40+bob),(torso-12,38+bob)],J_MID)
        line([(torso-11,35+bob),(torso-7,35+bob)],J_LIGHT)
        box(torso-9,37+bob,torso-9,37+bob,J_GLINT)
        line([(torso+6,35+bob),(torso+10,34+bob)],J_SH)
        for xx in range(hip-10,hip+10,3): line([(xx,51+bob),(xx+1,53+bob)],J_LIGHT)
    # Belt and hip rotation. Feet in all punch phases use the same planted pose.
    poly([(hip-10,52+bob),(hip+9,52+bob),(hip+10,56+bob),(hip-10,57+bob)],INK)
    box(hip-2,53+bob,hip+2,55+bob,'#b89860'); box(hip-1,54+bob,hip+1,54+bob,INK)
    line([(hip-8,58+bob),(hip-7,63+bob)],PANT_HI)
    if 15<=f<=21:
        # Two-handed wooden bat: shared handle axis defines both wrists.
        # The seven authored skeletons rotate shoulders over planted legs.
        import math
        grips=BAT_GRIPS
        tips=BAT_TIPS
        gx,gy=grips[f-15];tx,ty=tips[f-15]
        length=math.hypot(tx-gx,ty-gy);ux=(tx-gx)/length;uy=(ty-gy)/length
        px,py=-uy,ux
        def point(along,side):return (round(gx+along*ux+side*px),round(gy+along*uy+side*py))
        # Only two short subdued trail streaks in the active arc.
        if f in (17,18,19):
            line([(tx-13,ty+8),(tx-1,ty+6)],'#687888')
            line([(tx-20,ty+13),(tx-8,ty+11)],'#485868')
        poly([point(-12,-2),point(3,-2),point(12,-3),point(length-3,-4),
              point(length, -2),point(length,2),point(length-3,4),
              point(12,3),point(3,2),point(-12,2)],'#b88850')
        line([point(5,-1),point(length-4,-2)],'#e0b878',2)
        line([point(13,2),point(length-4,2)],'#806038')
        for wrap in (-10,-7,-4,-1):line([point(wrap,-2),point(wrap,2)],GLOVE)
        poly([point(-13,-3),point(-10,-3),point(-10,3),point(-13,3)],'#d0a068')
        # Rear wrist grips the knob side; front wrist grips the barrel side.
        rear_hand=point(-6,0);front_hand=(gx,gy)
        rear_elbows=BAT_REAR_ELBOWS
        front_elbows=BAT_FRONT_ELBOWS
        arm((torso-11,33+bob),rear_elbows[f-15],rear_hand,False)
    elif f>=22:
        # Compact welding/repair torch, held with a supporting second hand.
        shift={22:(-10,-1),23:(0,0),24:(-14,5)}[f];ox,oy=shift
        poly([(10+ox,46+oy),(17+ox,46+oy),(19+ox,50+oy),(18+ox,57+oy),
              (12+ox,59+oy),(9+ox,55+oy)],'#687860')
        line([(11+ox,49+oy),(11+ox,54+oy)],'#a8b890',2)
        line([(16+ox,50+oy),(17+ox,55+oy)],'#384838')
        box(12+ox,43+oy,16+ox,46+oy,'#b89860')
        poly([(17+ox,42+oy),(25+ox,42+oy),(28+ox,46+oy),(25+ox,48+oy),
              (23+ox,47+oy),(23+ox,52+oy),(19+ox,52+oy),(18+ox,47+oy)],GLOVE_HI)
        line([(20+ox,44+oy),(24+ox,44+oy)],LIGHT)
        poly([(25+ox,43+oy),(29+ox,44+oy),(36+ox,50+oy),(34+ox,53+oy),
              (27+ox,48+oy),(24+ox,47+oy)],SILVER)
        line([(28+ox,45+oy),(34+ox,50+oy)],GLINT)
        line([(32+ox,51+oy),(35+ox,52+oy)],INK,2)
        torch_front=(23+ox,45+oy);torch_rear=(12+ox,48+oy)
        arm((torso-11,33),(torso-7,47),torch_rear,False)
    else:
        arm((torso-11,33+bob),(torso-13,41+bob),(torso-1,35+bob),False)
    # Shared adult face in every pose: ear, cheek plane, a one-pixel bridge/
    # tip projection, mouth notch and under-jaw shadow, not a flat skin fill.
    poly([(hx-4,22+hy),(hx+3,22+hy),(hx+3,27+hy),(hx,28+hy),
          (hx-4,26+hy)],SKIN_SH)
    line([(hx,25+hy),(hx+1,27+hy)],SKIN)
    if chuck:
        # Same head envelope, blunter bridge and squarer adult jaw.
        poly([(hx-5,11+hy),(hx+3,10+hy),(hx+7,12+hy),(hx+7,17+hy),
              (hx+7,19+hy),(hx+7,20+hy),(hx+6,21+hy),(hx+6,24+hy),
              (hx+4,26+hy),(hx-1,26+hy),(hx-4,23+hy),(hx-5,19+hy)],SKIN)
    else:
        poly([(hx-5,11+hy),(hx+3,10+hy),(hx+7,12+hy),(hx+7,16+hy),
              (hx+8,18+hy),(hx+9,19+hy),(hx+7,20+hy),(hx+7,22+hy),
              (hx+5,25+hy),(hx+1,26+hy),(hx-3,23+hy),(hx-5,19+hy)],SKIN)
    poly([(hx-4,19+hy),(hx,19+hy),(hx+2,21+hy),(hx,23+hy),
          (hx+2,25+hy),(hx-1,24+hy),(hx-3,22+hy)],'#b07860',None)
    line([(hx+1,20+hy),(hx+4,20+hy),(hx+5,21+hy)],SKIN_HI)
    if chuck:
        line([(hx+6,18+hy),(hx+7,19+hy)],'#e0a880')
        line([(hx+6,20+hy),(hx+7,20+hy)],SKIN_SH)
    else:
        line([(hx+7,17+hy),(hx+7,18+hy),(hx+8,19+hy)],'#e0a880')
        line([(hx+7,20+hy),(hx+8,20+hy)],SKIN_SH)
    line([(hx+3,23+hy),(hx+6,23+hy)],'#684848')
    line([(hx+3,24+hy),(hx+5,24+hy)],'#e0a880')
    line([(hx,25+hy),(hx+3,26+hy),(hx+5,25+hy)],SKIN_SH)
    ellipse(hx-6,17+hy,hx-3,21+hy,SKIN_SH)
    line([(hx-5,18+hy),(hx-4,19+hy)],SKIN_HI)
    if chuck:
        # Flat rectangular frames, a lower straight brow and defined chin.
        line([(hx-3,13+hy),(hx+1,13+hy)],'#684848',2)
        line([(hx+4,13+hy),(hx+7,13+hy)],'#684848')
        box(hx-2,14+hy,hx+2,18+hy,EDGE)
        box(hx-1,15+hy,hx+1,17+hy,INK)
        box(hx+4,14+hy,hx+8,18+hy,EDGE)
        box(hx+5,15+hy,hx+7,17+hy,INK)
        line([(hx+2,15+hy),(hx+4,15+hy)],INK)
        line([(hx-5,15+hy),(hx-2,15+hy)],INK)
        line([(hx-1,15+hy),(hx,15+hy)],'#88a8b0')
        line([(hx+5,15+hy),(hx+6,15+hy)],'#a8b8c0')
        line([(hx+6,19+hy),(hx+7,20+hy)],SKIN_HI)
        line([(hx+6,21+hy),(hx+7,21+hy)],SKIN_SH)
        line([(hx+1,23+hy),(hx+4,23+hy)],'#684848')
        line([(hx-1,25+hy),(hx+3,25+hy),(hx+5,24+hy)],SKIN_SH)
    else:
        # Brow and round dark lenses; muted reflected pixels do not hide the nose.
        line([(hx-2,13+hy),(hx+1,13+hy)],'#685040')
        line([(hx+4,13+hy),(hx+7,14+hy)],'#685040')
        ellipse(hx-2,14+hy,hx+2,18+hy,INK,EDGE)
        ellipse(hx+4,14+hy,hx+7,18+hy,INK,EDGE)
        line([(hx+2,15+hy),(hx+4,15+hy)],EDGE)
        line([(hx-5,15+hy),(hx-2,15+hy)],INK)
        line([(hx-1,15+hy),(hx,15+hy)],'#88a8b0')
        line([(hx+5,15+hy),(hx+6,15+hy)],'#a8b8c0')
    # Swept-up, tousled front and long rear silhouette, original mullet shape.
    poly([(hx-6,20+hy),(hx-8,16+hy),(hx-8,11+hy),(hx-6,8+hy),
          (hx-2,7+hy),(hx,5+hy),(hx+4,6+hy),(hx+7,8+hy),
          (hx+10,9+hy),(hx+9,12+hy),(hx+4,12+hy),(hx+1,10+hy),
          (hx-2,12+hy),(hx-4,16+hy),(hx-4,20+hy)],HAIR)
    line([(hx-6,12+hy),(hx-3,9+hy),(hx+1,7+hy),(hx+5,8+hy)],HAIR_HI,2)
    line([(hx-2,12+hy),(hx+2,10+hy),(hx+7,11+hy)],HAIR_SH)
    line([(hx-7,15+hy),(hx-6,18+hy)],HAIR_HI)
    # Lead arm varies by actual shoulder/elbow/wrist articulation.
    if f>=22: arm((torso+11,32),(torso+10,50),torch_front,True)
    elif f>=15: arm((torso+11,32+bob),front_elbows[f-15],front_hand,True)
    elif f==8: arm((torso+11,32+bob),(torso+19,43+bob),(torso+13,32+bob),True)
    elif f==9: arm((torso+11,32),(31,39),(48,48),True)
    elif f==10: arm((torso+11,32+bob),(24,38+bob),(23,31+bob),True)
    elif f==14: arm((torso+11,32),(15,43),(22,30),True)
    elif f==12: arm((torso+11,32+bob),(21,42+bob),(26,28+bob),True)
    else:
        swing=-1 if f in (3,4) else (1 if f in (6,7) else 0)
        arm((torso+11,32+bob),(torso+20,44+bob),(torso+24+swing,31+bob),True)
    return im

def draw_air_legs(pose):
    """Dedicated compact aerial chains, shared by both costumes below the belt.
    Native anchor remains center/92; drawn relative to jump height at runtime.
    """
    im=Image.new('RGB',(96,96),KEY);d=ImageDraw.Draw(im);anchor=48
    def poly(points,color):
        pts=[(x+anchor,y) for x,y in points];d.polygon(pts,fill=color);d.line(pts+[pts[0]],fill=INK)
    def line(points,color,width=1):d.line([(x+anchor,y) for x,y in points],fill=color,width=width)
    # Hips -> bent knees -> tucked ankles; a different weight shift each phase.
    chains=[[((5,58),(18,67),(5,78)),((-6,58),(-15,70),(-24,74))],
            [((5,58),(21,64),(16,77)),((-6,58),(-4,72),(-19,78))],
            [((5,58),(13,70),(24,77)),((-6,58),(-18,65),(-22,77))]]
    for far,(hip,knee,ankle) in enumerate(chains[pose]):
        hx,hy=hip;kx,ky=knee;ax,ay=ankle;c=DEEP if not far else PANT
        poly([(hx-4,hy),(hx+4,hy),(kx+5,ky-2),(kx+4,ky+3),(ax+3,ay),
              (ax-4,ay+1),(kx-4,ky+3),(kx-5,ky-2)],c)
        line([(hx-2,hy+1),(kx-1,ky),(ax-1,ay-1)],PANT_HI,2)
        line([(kx-3,ky),(kx+2,ky)],SHADE)
        poly([(ax-4,ay-3),(ax+3,ay-3),(ax+5,ay),(ax+11,ay+1),
              (ax+12,ay+5),(ax-5,ay+5)],BOOT)
        line([(ax-4,ay+4),(ax+10,ay+4)],SOLE)
        line([(ax-2,ay-2),(ax+2,ay-2)],LIGHT)
    return im
