import json, numpy as np, math
M=[(1561,1605),(1732,1911),(449,1151),(1637,1736),(1441,1401),(1217,1343),(1232,942),(196,1157),(1722,1485),(1068,529),(989,372),(956,235),(940,60),(804,274),(778,564),(771,724),(778,1066),(1141,729),(768,1207),(1299,1138)]
NS=[(1468,541),(760,1181),(1763,755),(1231,914),(955,34),(456,1126)]
st=[(e["lat"],e["lon"],e["tags"].get("name","")) for e in json.load(open("stations.json"))["elements"]]
cp = [((448.5,1151),(52.3388,4.8732)),((760,1180),(52.33703,4.89023)),((1232,914),(52.34647,4.91756)),((1070,527),(52.36137,4.90739)),((1689,779),(52.35293,4.94832)),((135,1000),(52.34344,4.85405))]
def F(x,y,deg): return [1,x,y] + ([x*x,x*y,y*y] if deg==2 else [])
def fit(pairs,deg):
    A=np.array([F(x/1000,y/1000,deg) for (x,y),_ in pairs]); return [np.linalg.lstsq(A,np.array([c[1][i] for c in pairs]),rcond=None)[0] for i in (0,1)]
def ap(c,x,y,deg): v=np.array(F(x/1000,y/1000,deg)); return (v@c[0], v@c[1])
def d(a,b): return math.hypot((a[0]-b[0])*111200,(a[1]-b[1])*68000)
c=fit(cp,1); deg=1
for it in range(3):
    pairs=[]
    for q in M+NS:
        g=ap(c,*q,deg); best=min(st,key=lambda s:d(g,s))
        if d(g,best)<350: pairs.append((q,(best[0],best[1]),best[2]))
    # dedupe station used twice: keep closest
    c=fit([(p[0],p[1]) for p in pairs], 2 if len(pairs)>=10 else 1); deg=2 if len(pairs)>=10 else 1
    res=[d(ap(c,*p[0],deg),p[1]) for p in pairs]
    print("iter",it,"n",len(pairs),"deg",deg,"mean resid m",round(np.mean(res)),"max",round(max(res)))
for p,r in zip(pairs,res): print(p[2], p[0], round(r))
json.dump({"deg":deg,"c":[list(c[0]),list(c[1])]}, open("geofit.json","w"))
