import sys
from PIL import Image
P=sys.argv[1]
a=Image.open("work/new.png").convert("RGB")
cxs=(168,474,765,1380)
o=Image.new("RGB",(680*4,760*2+8),(190,190,190))
for k,cx in enumerate(cxs):
    o.paste(a.crop((cx-85,75,cx+85,265)).resize((680,760),Image.LANCZOS),(k*680,0))
for k,n in enumerate(("headfront","headback","headleft","head34")):
    i=Image.open("work/%s%s.png"%(P,n)).convert("RGBA"); bg=Image.new("RGBA",i.size,(190,190,190,255)); bg.alpha_composite(i)
    r=bg.convert("RGB").resize((int(i.width*322/760),int(i.height*322/760)),Image.LANCZOS)
    o.paste(r,(k*680+(680-r.width)//2,768-29))
o.resize((2040,1146),Image.LANCZOS).save("work/cmp_heads.png")
b=a.crop((20,60,1480,650))
def mine(n,h=590):
    i=Image.open("work/%s%s.png"%(P,n)).convert("RGBA"); bg=Image.new("RGBA",i.size,(175,175,175,255)); bg.alpha_composite(i)
    return bg.convert("RGB").resize((int(i.width*h/i.height),h),Image.LANCZOS)
ms=[mine(n) for n in ("front","back","left","threeq")]
o=Image.new("RGB",(b.width,b.height+598),(175,175,175)); o.paste(b,(0,0)); x=10
for m in ms: o.paste(m,(x,b.height+8)); x+=m.width+30
o.save("work/cmp_body.png")
