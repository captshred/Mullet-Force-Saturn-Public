"""Original native-resolution diagonal torch flame, with a continuous hot core."""
from PIL import Image,ImageDraw
KEY=(255,0,255)
def flame(frame):
    im=Image.new('RGB',(192,104),KEY);d=ImageDraw.Draw(im);a=96
    # Nozzle (34,52), floor (74,92): down is vertical, never street depth.
    end=74;flick=[0,2,-1,1][frame]
    d.ellipse((a+62,90,a+86,96),fill='#583020')
    d.ellipse((a+67,91,a+81,94),fill='#986038')
    d.polygon([(a+34,51),(a+43,57),(a+53,66),(a+65,77),(a+79+flick,88),
               (a+83,95),(a+72,94),(a+65,87),(a+54,79),(a+44,65),(a+33,53)],fill='#d84820')
    d.polygon([(a+34,52),(a+46,62),(a+59,73),(a+76+flick,89),(a+78,93),
               (a+69,90),(a+57,79),(a+45,66)],fill='#f89028')
    d.line((a+34,52,a+73,91),fill='#ffd868',width=4)
    d.line((a+34,52,a+73,91),fill='#fff0c0',width=2)
    # Fixed cap of three floor embers per frame, baked into shared textures.
    for j in range(3):
        x=a+64+(frame*5+j*7)%22;y=84+(frame*3+j*5)%10
        d.line((x,y,x+1,y-2),fill='#ffc050')
    return im
def ember(frame):
    im=Image.new('RGB',(8,12),KEY);d=ImageDraw.Draw(im)
    for x,y in ([(1,9),(4,5),(6,10)] if frame==0 else [(2,6),(5,2),(6,8)]):
        d.line((x,y,x,y-2),fill='#e86020');d.point((x,y-2),fill='#ffd868')
    return im
def cue():
    im=Image.new('RGB',(8,8),KEY);d=ImageDraw.Draw(im)
    d.line((1,4,6,4),fill='#c09050');d.line((4,1,4,6),fill='#c09050')
    d.rectangle((3,3,4,4),fill='#fff0c0');return im
