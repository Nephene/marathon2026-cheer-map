import pymupdf, json, re, math, numpy as np, sys
p=pymupdf.open(sys.argv[1])[0]
g=json.load(open("geofit.json")); c=[np.array(g["c"][0]),np.array(g["c"][1])]
def ap(x,y): x/=1000;y/=1000; v=np.array([1,x,y,x*x,x*y,y*y]); return [float(v@c[0]),float(v@c[1])]
reds=[d["rect"] for d in p.get_drawings() if d.get("fill") and abs(d["fill"][0]-0.93)<0.02 and abs(d["fill"][1]-0.11)<0.02 and 25<d["rect"].width<60 and 10<d["rect"].height<25]
raw=json.load(open("route_raw2.json"))
def snap(ll):
    i=min(range(len(raw)),key=lambda i:(raw[i][0]-ll[0])**2+((raw[i][1]-ll[1])*0.61)**2)
    return raw[i], math.hypot((raw[i][0]-ll[0])*111200,(raw[i][1]-ll[1])*68000)
kms={}
for b in p.get_text("dict")["blocks"]:
    for l in b.get("lines",[]):
        for s in l["spans"]:
            m=re.fullmatch(r"(\d+) km", s["text"].strip())
            if not m: continue
            x0,y0,x1,y1=s["bbox"]; cx,cy=(x0+x1)/2,(y0+y1)/2
            if any(r.x0-2<=cx<=r.x1+2 and r.y0-2<=cy<=r.y1+2 for r in reds) and s["size"]>13.5:
                k=int(m.group(1))
                # label box; dot is on the route nearby -> snap
                pt,dd=snap(ap(cx,cy)); kms.setdefault(k,[]).append((pt,round(dd)))
print({k:[v[1] for v in vs] for k,vs in sorted(kms.items())})
spots={"km6":(526,936),"km12":(1020.5,978),"km13":(953,1136),"km14":(939,1276),"km32":(1441,915.5),"km37":(1045,573.5),"finish":(150,1010)}
out={}
for k,(x,y) in spots.items():
    pt,dd=snap(ap(x,y)); out[k]=[round(pt[0],5),round(pt[1],5)]; print(k,out[k],"snap",round(dd))
json.dump({"kms":{k:[round(v[0][0][0],5),round(v[0][0][1],5)] for k,v in kms.items()},"spots":out}, open("kmfix.json","w"))
