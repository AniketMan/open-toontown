import sys
from PIL import Image
P=sys.argv[1]
a=Image.open("work/new.png").convert("RGB")
cxs=(172,470,768,1398)
o=Image.new("RGB",(720*4,700*2+8),(190,190,190))
for k,cx in enumerate(cxs):
    o.paste(a.crop((cx-90,70,cx+90,245)).resize((720,700),Image.LANCZOS),(k*720,0))
for k,n in enumerate(("headfront","headback","headleft","head34")):
    i=Image.open("work/%s%s.png"%(P,n)).convert("RGBA"); bg=Image.new("RGBA",i.size,(190,190,190,255)); bg.alpha_composite(i)
    r=bg.convert("RGB").resize((int(i.width*283.6/450),int(i.height*283.6/450)),Image.LANCZOS)
    o.paste(r,(k*720+(720-r.width)//2,708-45))
o.resize((2160,1056),Image.LANCZOS).save("work/cmp_heads.png")
b=a.crop((20,60,1500,660))
def mine(n,h=600):
    i=Image.open("work/%s%s.png"%(P,n)).convert("RGBA"); bg=Image.new("RGBA",i.size,(175,175,175,255)); bg.alpha_composite(i)
    return bg.convert("RGB").resize((int(i.width*h/i.height),h),Image.LANCZOS)
ms=[mine(n) for n in ("front","back","left","threeq")]
o=Image.new("RGB",(b.width,b.height+608),(175,175,175)); o.paste(b,(0,0)); x=40
for m in ms: o.paste(m,(x,b.height+8)); x+=m.width+90
o.save("work/cmp_body.png")
