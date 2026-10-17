import pymupdf, sys, json
p = pymupdf.open(sys.argv[1])[0]
segs=[]
for d in p.get_drawings():
    c=d.get("color")
    if c and abs(c[0]-0.93)<0.01 and abs(c[1]-0.111)<0.01 and round(d.get("width") or 0,2) in (5.03,5.3):
        pts=[]
        for it in d["items"]:
            if it[0]=="l": a,b=it[1],it[2]; pts+= [a,b]
            elif it[0]=="c":
                P0,P1,P2,P3=it[1:5]
                for t in [i/8 for i in range(9)]:
                    x=(1-t)**3*P0.x+3*(1-t)**2*t*P1.x+3*(1-t)*t*t*P2.x+t**3*P3.x
                    y=(1-t)**3*P0.y+3*(1-t)**2*t*P1.y+3*(1-t)*t*t*P2.y+t**3*P3.y
                    pts.append(pymupdf.Point(x,y))
            elif it[0]=="re": pass
        # dedupe consecutive, and record subpath breaks
        out=[]
        for q in pts:
            if not out or abs(out[-1][0]-q.x)+abs(out[-1][1]-q.y)>0.05: out.append((round(q.x,2),round(q.y,2)))
        L=sum(((out[i+1][0]-out[i][0])**2+(out[i+1][1]-out[i][1])**2)**.5 for i in range(len(out)-1))
        segs.append({"w":d["width"],"n":len(out),"len":round(L),"start":out[0],"end":out[-1],"items":len(d["items"]),"pts":out})
for s in segs: print(s["w"], s["n"], s["len"], s["start"], s["end"], s["items"])
json.dump(segs, open("red_segs.json","w"))
