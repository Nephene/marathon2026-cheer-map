import urllib.error, json, math, urllib.request, time, numpy as np
segs=json.load(open("red_segs.json")); main=[s for s in segs if s["n"]>100]
S3=[s for s in main if s["start"][0]==595.76][0]["pts"][::-1]; S4=[s for s in main if s["start"][0]==579.71][0]["pts"]; S1=[s for s in main if s["start"][0]==1075.39][0]["pts"]
g=json.load(open("geofit.json")); c=[np.array(g["c"][0]),np.array(g["c"][1])]
def ap(x,y): x/=1000;y/=1000; v=np.array([1,x,y,x*x,x*y,y*y]); return [float(v@c[0]),float(v@c[1])]
ll=[ap(x,y) for x,y in S3+S4+S1]
def hav(a,b):
    R=6371000; p1,p2=math.radians(a[0]),math.radians(b[0]); dp=p2-p1; dl=math.radians(b[1]-a[1])
    return 2*R*math.asin(math.sqrt(math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2))
print("raw km", round(sum(hav(ll[i],ll[i+1]) for i in range(len(ll)-1))/1000,2))
json.dump(ll, open("route_raw2.json","w"))
samp=[ll[0]]; acc=0
for i in range(1,len(ll)):
    acc+=hav(ll[i-1],ll[i])
    if acc>=60: samp.append(ll[i]); acc=0
samp.append(ll[-1]); print("samples", len(samp))
out=[]; CH=25; matched=0
for s in range(0,len(samp)-1,CH-1):
    ch=samp[s:s+CH]
    coords=";".join(f"{lo:.6f},{la:.6f}" for la,lo in ch); rad=";".join(["40"]*len(ch))
    u=f"https://routing.openstreetmap.de/routed-foot/match/v1/foot/{coords}?radiuses={rad}&geometries=geojson&overview=full&gaps=ignore"
    
    try: r=json.load(urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"marathon-cheer-map"}),timeout=60))
    except urllib.error.HTTPError as e: print("ERR",s,e.read()[:200]); continue
    tp=r.get("tracepoints") or []
    nm=sum(1 for t in tp if t); matched+=nm
    print(s, r.get("code"), "matchings", len(r.get("matchings",[])), "tracepoints matched", nm, "/", len(ch), [round(m["confidence"],2) for m in r.get("matchings",[])])
    out.append({"chunk":s,"matchings":[[[q[1],q[0]] for q in m["geometry"]["coordinates"]] for m in r.get("matchings",[])]})
    time.sleep(1)
json.dump(out, open("route_matched2.json","w"))
