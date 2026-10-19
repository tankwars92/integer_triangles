from math import isqrt
import hull
from hull import segment_floor_sum

OPS = [0]

def hs(Y, L, R):
    if R < L: return 0
    n = R - L + 1
    if n <= 30000:
        OPS[0] += n
        return sum(Y // x for x in range(L, R + 1))
    s0 = hull.STEPS[0]
    r = segment_floor_sum(Y, L, R)
    OPS[0] += hull.STEPS[0] - s0
    return r

def total_tri(p):
    n = p if p % 2 == 0 else p + 3
    return (n * n + 24) // 48

def _fh(n):
    if n < 0: return 0
    m = n // 2
    return m * m - (m if n % 2 == 0 else 0) if False else (m * (m - 1) + (0 if n % 2 == 0 else m)) if False else _fh_slow(n)

def _fh_slow(n):
    return (n // 2) * ((n + 1) // 2)

def sum_floor_half(lo, hi):
    if hi < lo: return 0
    return _fh_slow(hi) - _fh_slow(lo - 1)

def factor(n):
    f = {}
    d = 2
    while d * d <= n and d < 2_000_000:
        while n % d == 0:
            f[d] = f.get(d, 0) + 1; n //= d
        d += 1 if d == 2 else 2
    if n > 1:
        r = isqrt(n)
        if r * r == n: f[r] = f.get(r, 0) + 2
        else: f[n] = f.get(n, 0) + 1
    return f

def right_count(p):
    if p % 2: return 0
    f = factor(p // 2)
    f = {q: 2 * e for q, e in f.items()}
    f[2] = f.get(2, 0) + 1
    divs = [1]
    for q, e in f.items():
        divs = [d * q ** k for d in divs for k in range(e + 1)]
    N2 = p * p // 2
    cnt = 0
    for u in divs:
        v = N2 // u
        a, b = p - u, p - v
        if a >= 1 and a <= b and p - a - b > b:
            cnt += 1
    return cnt

def acute_count(p):
    Y = (p * p - 1) // 2
    amax = p // 3
    def vlo(a): return (p + a + 1) // 2
    def vhi(a): return min(p - a, (p + 1) // 2 + a - 1)
    def nA(a):
        return max(0, min(vhi(a), Y // (p - a)) - vlo(a) + 1)
    if amax < 1: return 0
    small = 8
    s = sum(nA(a) for a in range(1, min(small, amax) + 1))
    if amax <= small: return s
    lo, hi = small, amax
    def g1_le(a): return Y // (p - a) <= vhi(a)
    if not g1_le(lo): lo = small
    L, H = small, amax
    while L < H:
        m = (L + H + 1) // 2
        if g1_le(m): L = m
        else: H = m - 1
    a0 = L
    w0, w1 = max(small + 1, a0 - 6), min(amax, a0 + 6)
    if w0 - 1 >= small + 1:
        a1, a2 = small + 1, w0 - 1
        sF = hs(Y, p - a2, p - a1)
        sV = sum_floor_half(p + a1 + 1, p + a2 + 1)
        s += sF - sV + (a2 - a1 + 1)
    s += sum(nA(a) for a in range(w0, w1 + 1))
    if w1 + 1 <= amax:
        for a in range(w1 + 1, min(amax, w1 + 1) + 1): pass
        a3, a4 = w1 + 1, amax
        switch = ((p // 2) + 1 + 1) // 2
        t1 = 0
        ra, rb = a3, min(a4, switch - 1)
        if rb >= ra:
            t1 += ((p + 1) // 2 - 1) * (rb - ra + 1) + (ra + rb) * (rb - ra + 1) // 2
        rc, rd = max(a3, switch), a4
        if rd >= rc:
            t1 += p * (rd - rc + 1) - (rc + rd) * (rd - rc + 1) // 2
        s += t1 - sum_floor_half(p + a3 + 1, p + a4 + 1) + (a4 - a3 + 1)
    return s

def tri_counts(p):
    tot = total_tri(p)
    ac = acute_count(p)
    rt = right_count(p)
    
    return tot - ac - rt, rt, ac, tot
