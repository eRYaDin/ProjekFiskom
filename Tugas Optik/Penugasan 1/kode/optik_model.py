"""Mesin hitung Python: slab TE dan dua teras simetris (panjang dalam µm)."""
from functools import lru_cache
import math
import numpy as np

NC, NS = 1.51, 1.50
LAM_C, D_C = 1.55, 2.0


def bisect(f, a, b):
    fa = f(a)
    if fa * f(b) > 0:
        raise ValueError('Akar tidak terkurung.')
    for _ in range(120):
        mid = (a + b) / 2
        fm = f(mid)
        if b - a < 1e-13:
            return mid
        if fa * fm <= 0:
            b = mid
        else:
            a, fa = mid, fm
    return (a + b) / 2


def slab_modes(d=2.0, lam=1.55):
    if d <= 0 or lam <= 0:
        raise ValueError('Ketebalan dan panjang gelombang harus positif.')
    k = 2 * math.pi / lam
    v = k * d * math.sqrt(NC**2 - NS**2)
    result = []
    for m in range(int(v / math.pi) + 1):
        if v <= m * math.pi + 1e-12:
            continue
        def phase(b):
            return v * math.sqrt(1-b) - m*math.pi - 2*math.atan(math.sqrt(b/(1-b)))
        b = bisect(phase, 1e-15, 1-1e-15)
        ne = math.sqrt(NS**2 + b*(NC**2-NS**2))
        result.append(dict(m=m, d=d, lam=lam, neff=ne, beta=k*ne,
                           h=k*math.sqrt(NC**2-ne**2), q=k*math.sqrt(ne**2-NS**2)))
    return result


def slab_field(x, mode):
    x = np.asarray(x, dtype=float)
    h, q, a = mode['h'], mode['q'], mode['d']/2
    inside = np.abs(x) <= a
    # Clamp the tail exponent inside the core to avoid overflow in np.where.
    tail = np.exp(-q*np.maximum(0, np.abs(x)-a))
    if mode['m'] % 2:
        return np.where(inside, np.sin(h*x), np.sign(x)*math.sin(h*a)*tail)
    return np.where(inside, np.cos(h*x), math.cos(h*a)*tail)


def residual(ne, gap, odd):
    k = 2*math.pi/LAM_C
    q, h = k*math.sqrt(ne**2-NS**2), k*math.sqrt(NC**2-ne**2)
    t = q*gap/2
    e, v = (math.sinh(t)/q, math.cosh(t)) if odd else (math.cosh(t), q*math.sinh(t))
    end = e*math.cos(h*D_C) + v*math.sin(h*D_C)/h
    der = -e*h*math.sin(h*D_C) + v*math.cos(h*D_C)
    return der + q*end


def raw_supermode(x, ne, gap, odd):
    x = np.asarray(x, dtype=float)
    r, a = np.abs(x), gap/2
    k = 2*math.pi/LAM_C
    q, h = k*math.sqrt(ne**2-NS**2), k*math.sqrt(NC**2-ne**2)
    e0, v0 = (math.sinh(q*a)/q, math.cosh(q*a)) if odd else (math.cosh(q*a), q*math.sinh(q*a))
    # Evaluate each layer only on its own region.
    t = np.clip(r-a, 0, D_C)
    core = e0*np.cos(h*t) + v0*np.sin(h*t)/h
    gap_field = np.sinh(q*np.minimum(r,a))/q if odd else np.cosh(q*np.minimum(r,a))
    edge = e0*math.cos(h*D_C) + v0*math.sin(h*D_C)/h
    tail = edge*np.exp(-q*np.maximum(0,r-a-D_C))
    field = np.where(r<a, gap_field, np.where(r<=a+D_C, core, tail))
    return -np.sign(x)*field if odd else field


def supermode_norm(ne, gap, odd):
    # Separate Simpson integrals per layer; tails integrated analytically to infinity.
    def integral(lo, hi):
        x = np.linspace(lo, hi, 1201)
        y = raw_supermode(x, ne, gap, odd)**2
        return (hi-lo)/1200/3*(y[0]+y[-1]+4*y[1:-1:2].sum()+2*y[2:-1:2].sum())
    edge_x = gap/2+D_C
    edge = float(raw_supermode(edge_x, ne, gap, odd))
    q = 2*math.pi/LAM_C*math.sqrt(ne**2-NS**2)
    return math.sqrt(2*(integral(0,gap/2)+integral(gap/2,edge_x)) + edge**2/q)


@lru_cache(maxsize=128)
def coupler(gap=4.0):
    if not 2 <= gap <= 6:
        raise ValueError('Rentang celah kopler adalah 2–6 µm.')
    roots = []
    for odd in (False, True):
        f = lambda ne: residual(ne, gap, odd)
        grid = np.linspace(NS+1e-10, NC-1e-10, 1601)
        hits = []
        a, fa = float(grid[0]), f(float(grid[0]))
        for value in grid[1:]:
            b, fb = float(value), f(float(value))
            if fa*fb < 0:
                hits.append(bisect(f,a,b))
            a, fa = b, fb
        if len(hits) != 1:
            raise RuntimeError('Model memerlukan satu pasangan supermode terikat.')
        roots.append(hits[0])
    be, bo = [2*math.pi/LAM_C*n for n in roots]
    kappa = (be-bo)/2
    return dict(g=gap, ne=tuple(roots), be=be, bo=bo, kappa=kappa,
                Lc=math.pi/(2*kappa),
                norms=tuple(supermode_norm(n,gap,bool(i)) for i,n in enumerate(roots)))


def basis(x, cp):
    return tuple(raw_supermode(x,n,cp['g'],bool(i))/cp['norms'][i]/math.sqrt(cp['bo'] if i else cp['be'])
                 for i,n in enumerate(cp['ne']))


def intensity(x, z, cp):
    e, o = basis(x, cp)
    return np.maximum(0, (e*e+o*o+2*e*o*np.cos(2*cp['kappa']*np.asarray(z)))/2)


def intensity_max(cp):
    e, o = basis(np.linspace(-12,12,2401),cp)
    return float(np.max((np.abs(e)+np.abs(o))**2/2))


def powers(z, cp):
    pb = np.sin(cp['kappa']*np.asarray(z))**2
    return 1-pb, pb
