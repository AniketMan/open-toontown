import sys
from PIL import Image
out=sys.argv[1]; h=int(sys.argv[2]); names=sys.argv[3:]
ims=[]
for n in names:
    i=Image.open(n).convert('RGBA'); bg=Image.new('RGBA',i.size,(190,190,190,255)); bg.alpha_composite(i)
    ims.append(bg.convert('RGB').resize((int(i.width*h/i.height),h)))
o=Image.new('RGB',(sum(i.width for i in ims)+8*len(ims),h),(255,255,255)); x=0
for i in ims: o.paste(i,(x,0)); x+=i.width+8
o.save(out); print(o.size)
