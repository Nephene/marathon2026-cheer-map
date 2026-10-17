import json, math, urllib.request, time
OUT="/Users/dorukhanyesilli/dev/marathon2026/docs/data/routes.json"
def hav(a,b):
    R=6371000; p1,p2=math.radians(a[0]),math.radians(b[0]); dp=p2-p1; dl=math.radians(b[1]-a[1])
    return 2*R*math.asin(math.sqrt(math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2))
def dp_simplify(pts, eps):
    if len(pts)<3: return pts
    a,b=pts[0],pts[-1]; kx=68000; ky=111200
    def pd(p):
        ax,ay,bx,by,px,py=a[1]*kx,a[0]*ky,b[1]*kx,b[0]*ky,p[1]*kx,p[0]*ky
        dx,dy=bx-ax,by-ay; L=dx*dx+dy*dy
        if L==0: return math.hypot(px-ax,py-ay)
        t=max(0,min(1,((px-ax)*dx+(py-ay)*dy)/L)); return math.hypot(px-ax-t*dx,py-ay-t*dy)
    i,dm=max(((i,pd(p)) for i,p in enumerate(pts[1:-1],1)), key=lambda t:t[1])
    if dm>eps: return dp_simplify(pts[:i+1],eps)[:-1]+dp_simplify(pts[i:],eps)
    return [a,b]
# marathon course
raw=json.load(open("route_raw2.json"))
cum=[0]
for i in range(1,len(raw)): cum.append(cum[-1]+hav(raw[i-1],raw[i]))
scale=42195/cum[-1]
kms=[]; k=1
for i in range(1,len(raw)):
    while k<=42 and cum[i]*scale>=k*1000:
        kms.append({"km":k,"lat":round(raw[i][0],5),"lon":round(raw[i][1],5)}); k+=1
course=[[round(p[0],5),round(p[1],5)] for p in dp_simplify(raw,4)]
# places
S={"Zuid":(52.3389,4.8730),"RAI":(52.3370,4.8902),"Overamstel":None,"Spaklerweg":None,"Amstel":(52.3465,4.9176),"Wibautstraat":(52.35522,4.91129),"Weesperplein":(52.3614,4.9074)}
for e in json.load(open("stations.json"))["elements"]:
    n=e["tags"].get("name","")
    if n in ("Overamstel","Spaklerweg") and S[n] is None: S[n]=(e["lat"],e["lon"])
KF=json.load(open("kmfix.json")); P={k:tuple(v) for k,v in KF["spots"].items()}
line=["Zuid","RAI","Overamstel","Spaklerweg","Amstel","Wibautstraat","Weesperplein"]
ride={("Zuid","RAI"):2,("RAI","Amstel"):6,("Amstel","Weesperplein"):3,("Weesperplein","Zuid"):13,("Amstel","Zuid"):9}
metro=[]
for (a,b),mins in ride.items():
    i,j=line.index(a),line.index(b); seq=line[i:j+1] if i<j else line[j:i+1][::-1]
    pts=[list(S[s]) for s in seq]; dist=sum(hav(pts[t],pts[t+1]) for t in range(len(pts)-1))
    metro.append({"id":f"{a}-{b}","from":a,"to":b,"line":"Metro 51" + (" / 53 / 54" if {a,b}=={"Amstel","Weesperplein"} else "") + (" (or 50 / train)" if {a,b}=={"Zuid","RAI"} else ""),
                  "stops":len(seq)-1,"via":seq,"km":round(dist/1000,1),"min":mins,"path":[[round(x,5) for x in p] for p in pts]})
walks=[]
for a,b in [("Zuid","km6"),("km6","Zuid"),("RAI","km12"),("RAI","km13"),("RAI","km14"),("km12","RAI"),("km13","RAI"),("km14","RAI"),("Amstel","km32"),("km32","Amstel"),("Weesperplein","km37"),("km37","Weesperplein"),("Zuid","finish")]:
    A=S.get(a) or P[a]; B=S.get(b) or P[b]
    u=f"https://routing.openstreetmap.de/routed-foot/route/v1/foot/{A[1]},{A[0]};{B[1]},{B[0]}?overview=full&geometries=geojson"
    r=json.load(urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"marathon-cheer-map"}),timeout=60))["routes"][0]
    path=[[c[1],c[0]] for c in r["geometry"]["coordinates"]]
    walks.append({"id":f"{a}-{b}","from":a,"to":b,"km":round(r["distance"]/1000,2),"min":round(r["distance"]/1000/4.8*60),"path":[[round(x,5) for x in p] for p in dp_simplify(path,2)]})
    time.sleep(1)
data={"_note":"course = trace of the red line in the official PDF, georeferenced (approx +-50 m). walk = OSM foot routing at 4.8 km/h. metro = station-to-station line, ride times approx.",
      "course":course,"km_markers":[{"km":int(k),"lat":v[0],"lon":v[1]} for k,v in sorted(KF["kms"].items(), key=lambda t:int(t[0])) if int(k)%5==0 and int(k)<=40],"spots":{k:list(v) for k,v in P.items()},"stations":{k:[round(v[0],5),round(v[1],5)] for k,v in S.items()},"metro":metro,"walks":walks}
json.dump(data, open(OUT,"w"), separators=(",",":"))
print("course pts", len(course), "kms", len(kms), "metro", [(m["id"],m["km"],m["min"]) for m in metro]); print([(w["id"],w["km"],w["min"]) for w in walks])
import os; print(os.path.getsize(OUT))
