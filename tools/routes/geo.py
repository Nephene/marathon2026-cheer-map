import json, numpy as np, math
segs=json.load(open("red_segs.json"))
main=[s for s in segs if s["n"]>100]
S3=[s for s in main if s["start"][0]==595.76][0]["pts"][::-1]
S4=[s for s in main if s["start"][0]==579.71][0]["pts"]
S1=[s for s in main if s["start"][0]==1075.39][0]["pts"]
print("gaps", S3[-1], S4[0], S4[-1], S1[0])
pts=S3+S4+S1
cp = [((448.5,1151),(52.3388,4.8732)),((760,1180),(52.33703,4.89023)),((1232,914),(52.34647,4.91756)),
      ((1070,527),(52.36137,4.90739)),((1689,779),(52.35293,4.94832)),((135,1000),(52.34344,4.85405))]
A=np.array([[x,y,1] for (x,y),_ in cp]); cl=np.linalg.lstsq(A,np.array([c[1][0] for c in cp]),rcond=None)[0]; co=np.linalg.lstsq(A,np.array([c[1][1] for c in cp]),rcond=None)[0]
ll=[(float(np.array([x,y,1])@cl), float(np.array([x,y,1])@co)) for x,y in pts]
def hav(a,b):
    R=6371000; p1,p2=math.radians(a[0]),math.radians(b[0]); dp=p2-p1; dl=math.radians(b[1]-a[1])
    return 2*R*math.asin(math.sqrt(math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2))
L=sum(hav(ll[i],ll[i+1]) for i in range(len(ll)-1)); print("raw length km", round(L/1000,2), "n", len(ll))
json.dump(ll, open("route_raw.json","w"))
