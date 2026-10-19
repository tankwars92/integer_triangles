def baseline_tri(p):
    Y2=p*p
    ob=ac=rt=0
    for a in range(1,p//3+1):
        blo=max(a,(p-2*a)//2+1); bhi=(p-a)//2
        if blo>bhi: continue
        u=p-a
        vlo=p-bhi; vhi=p-blo
        n=vhi-vlo+1
        vA=(Y2-1)//(2*u)
        nA=max(0,min(vhi,vA)-vlo+1)
        nR=1 if (Y2%(2*u)==0 and vlo<=Y2//(2*u)<=vhi) else 0
        ac+=nA; rt+=nR; ob+=n-nA-nR
    return ob,rt,ac,ob+rt+ac
