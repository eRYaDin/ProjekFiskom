"""Penugasan 1 Optik Modern: slab TE dan directional coupler simetris.

Jalankan: python simulasi_optik.py
Dependensi: numpy, reportlab. Semua panjang internal dalam mikrometer.
Tidak memakai konstanta kopling tebakan atau data eksperimen.
"""
from pathlib import Path
import math, json, csv
import numpy as np
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parents[1]
DATA, FIG = ROOT/'data', ROOT/'grafik'
NC, NS, LAM, D = 1.51, 1.50, 1.55, 2.0
COLORS = ['#146078','#d06429','#66864c','#795a96']

def bisect(f, a, b, tol=1e-13):
    fa, fb = f(a), f(b)
    if fa*fb > 0: raise ValueError('Akar tidak terkurung')
    for _ in range(180):
        c = (a+b)/2; fc=f(c)
        if abs(b-a) < tol: return c
        if fa*fc <= 0: b=c
        else: a,fa=c,fc
    return (a+b)/2

def slab_modes(d=D, lam=LAM, nc=NC, ns=NS):
    """Akar fase tanpa kutub: V sqrt(1-b) = m pi + 2 atan sqrt(b/(1-b))."""
    k=2*math.pi/lam; V=k*d*math.sqrt(nc*nc-ns*ns)
    out=[]
    for m in range(int(V/math.pi)+1):
        if V <= m*math.pi+1e-12: continue  # cutoff tepat bukan mode terikat
        f=lambda b: V*math.sqrt(1-b)-m*math.pi-2*math.atan(math.sqrt(b/(1-b)))
        b=bisect(f,1e-15,1-1e-15)
        ne=math.sqrt(ns*ns+b*(nc*nc-ns*ns)); beta=k*ne
        h=k*math.sqrt(nc*nc-ne*ne); q=k*math.sqrt(ne*ne-ns*ns)
        out.append(dict(m=m,b=b,neff=ne,beta=beta,h=h,q=q,V=V,residual=abs(f(b))))
    return out

def slab_field(x, mode, d=D):
    h,q,m=mode['h'],mode['q'],mode['m']; a=d/2
    if m%2==0:
        return np.where(abs(x)<=a,np.cos(h*x),math.cos(h*a)*np.exp(-q*(abs(x)-a)))
    return np.where(abs(x)<=a,np.sin(h*x),np.sign(x)*math.sin(h*a)*np.exp(-q*(abs(x)-a)))

def coupling_residual(ne, g, parity, d=D):
    """Transfer medan dan turunannya dari pusat celah ke tepi teras kanan.
    Pada selubung luar E'=-q E. Syarat TE E dan E' kontinu (mu konstan).
    """
    k=2*math.pi/LAM; q=k*math.sqrt(ne*ne-NS*NS); h=k*math.sqrt(NC*NC-ne*ne)
    t=q*g/2
    if parity=='even': e,v=math.cosh(t),q*math.sinh(t)
    else: e,v=math.sinh(t)/q,math.cosh(t)
    end=e*math.cos(h*d)+v*math.sin(h*d)/h
    der=-e*h*math.sin(h*d)+v*math.cos(h*d)
    return der+q*end

def coupler(g, samples=4001):
    roots={}
    grid=np.linspace(NS+1e-10,NC-1e-10,samples)
    for parity in ['even','odd']:
        f=lambda ne:coupling_residual(ne,g,parity)
        hits=[]; last=float(grid[0]); fl=f(last)
        for v in grid[1:]:
            fv=f(float(v))
            if fl*fv<0: hits.append(bisect(f,last,float(v)))
            last,fl=float(v),fv
        if len(hits)!=1: raise RuntimeError(f'g={g}: {parity} roots={hits}')
        roots[parity]=hits[0]
    k=2*math.pi/LAM; be=k*roots['even']; bo=k*roots['odd']
    kap=(be-bo)/2
    return dict(g=g,ne_even=roots['even'],ne_odd=roots['odd'],beta_even=be,beta_odd=bo,
                kappa=kap,Lc=math.pi/(2*kap),L50=math.pi/(4*kap))

def writecsv(name, header, rows):
    with (DATA/name).open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f); w.writerow(header); w.writerows(rows)

def font_setup():
    # Unicode bila font tersedia, fallback Helvetica agar kode portabel.
    global FONT
    choices=[Path('C:/Windows/Fonts/arial.ttf'),Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')]
    FONT='Helvetica'
    for p in choices:
        if p.exists():
            pdfmetrics.registerFont(TTFont('PlotFont',str(p))); FONT='PlotFont'; break

def plot(name, title, xlabel, ylabel, lines, xlim, ylim, legend=True, vlines=()):
    """Grafik vektor berbasis ReportLab, bukan gambar tangan atau data ilustratif."""
    c=canvas.Canvas(str(FIG/(name+'.pdf')),pagesize=(720,405))
    c.setTitle(title); c.setFont(FONT,14); c.drawString(75,378,title)
    x0,y0,w,h=78,64,606,280
    xx=lambda x:x0+(x-xlim[0])/(xlim[1]-xlim[0])*w
    yy=lambda y:y0+(y-ylim[0])/(ylim[1]-ylim[0])*h
    c.setFont(FONT,10)
    for x in np.linspace(*xlim,6):
        c.setStrokeColor(HexColor('#e2e6e8')); c.line(xx(x),y0,xx(x),y0+h)
        c.setFillColor(HexColor('#333333')); c.drawCentredString(xx(x),y0-17,f'{x:.3g}')
    for y in np.linspace(*ylim,5):
        c.setStrokeColor(HexColor('#e2e6e8')); c.line(x0,yy(y),x0+w,yy(y))
        c.setFillColor(HexColor('#333333')); c.drawRightString(x0-10,yy(y)-3,f'{y:.5g}')
    for xv in vlines:
        c.setStrokeColor(HexColor('#aaaaaa')); c.setDash(4,3); c.line(xx(xv),y0,xx(xv),y0+h);c.setDash()
    for j,(label,x,y) in enumerate(lines):
        c.setStrokeColor(HexColor(COLORS[j%len(COLORS)])); c.setLineWidth(1.8)
        path=c.beginPath(); active=False
        for a,b in zip(x,y):
            if not np.isfinite(b): active=False; continue
            if not active: path.moveTo(xx(float(a)),yy(float(b)));active=True
            else:path.lineTo(xx(float(a)),yy(float(b)))
        c.drawPath(path)
        if legend:
            lx=x0+16; ly=y0+h-18-j*17
            c.line(lx,ly,lx+25,ly); c.setFillColor(HexColor('#222222'));c.setFont(FONT,10)
            c.drawString(lx+33,ly-3,label)
    c.setStrokeColor(HexColor('#333333'));c.setLineWidth(.7);c.rect(x0,y0,w,h,stroke=1,fill=0)
    c.setFont(FONT,11);c.drawCentredString(x0+w/2,19,xlabel)
    c.saveState();c.translate(19,y0+h/2);c.rotate(90);c.drawCentredString(0,0,ylabel);c.restoreState()
    c.save()

def geometry():
    c=canvas.Canvas(str(FIG/'01_geometri.pdf'),pagesize=(720,360));c.setFont(FONT,15)
    c.drawString(40,331,'Geometri slab tunggal dan directional coupler')
    c.setFont(FONT,11);c.drawString(40,297,'Slab tunggal');c.drawString(390,297,'Dua teras identik')
    c.setFillColor(HexColor('#eef2f4'));c.rect(40,90,275,180,fill=1,stroke=0);c.rect(390,90,275,180,fill=1,stroke=0)
    c.setFillColor(HexColor('#b9d6df'));c.rect(40,155,275,48,fill=1,stroke=0)
    c.rect(390,211,275,35,fill=1,stroke=0);c.rect(390,120,275,35,fill=1,stroke=0)
    c.setFillColor(HexColor('#203640'))
    for x,y,t in [(53,236,'Selubung n1 = 1,50'),(53,175,'Teras n2 = 1,51; d = 2 µm'),(53,112,'Selubung n3 = 1,50'),(404,224,'Pandu a; d = 2 µm'),(404,168,'Celah g = 2, 4, 6 µm'),(404,133,'Pandu b; d = 2 µm')]:c.drawString(x,y,t)
    c.setStrokeColor(HexColor('#203640'));c.line(40,65,315,65);c.line(390,65,665,65)
    c.drawString(230,45,'z, propagasi');c.drawString(580,45,'z, propagasi')
    c.drawString(40,20,'Skema tidak berskala. Arah x melintang; arah y dianggap tak berhingga.');c.save()

def main():
    DATA.mkdir(exist_ok=True); FIG.mkdir(exist_ok=True);font_setup()
    modes=slab_modes(); m=modes[0]; x=np.linspace(-15,15,1801); e=slab_field(x,m)
    # Integral analitik TE0: cos² di teras dan dua ekor eksponensial.
    icore=D/2+math.sin(m['h']*D)/(2*m['h'])
    itail=math.cos(m['h']*D/2)**2/m['q']; gamma=icore/(icore+itail)
    ds=np.linspace(.2,12,180); branches=[[] for _ in range(3)]; nums=[]
    for d in ds:
        ms=slab_modes(float(d));nums.append(len(ms))
        for j in range(3):branches[j].append(ms[j]['neff'] if len(ms)>j else float('nan'))
    gaps=[2.,4.,6.]; cp=[coupler(g) for g in gaps]; ref=cp[1]
    z=np.linspace(0,2*ref['Lc'],401)
    pa=np.cos(ref['kappa']*z)**2;pb=np.sin(ref['kappa']*z)**2
    gscan=np.linspace(2,6,41); cscan=[coupler(float(g),samples=1201) for g in gscan]
    gridcheck=[coupler(4.,samples=n) for n in [801,1601,4001]]
    power_error=float(np.max(abs(pa+pb-1)))
    mm=slab_modes(8.0);ex0=slab_field(x,mm[0],8.0);ex1=slab_field(x,mm[1],8.0)
    orth=float(abs(np.trapezoid(ex0*ex1,x))/math.sqrt(np.trapezoid(ex0*ex0,x)*np.trapezoid(ex1*ex1,x)))
    assert len(modes)==1 and NS<m['neff']<NC
    assert power_error<1e-12 and orth<1e-10
    assert max(c['Lc'] for c in gridcheck)-min(c['Lc'] for c in gridcheck)<1e-5
    assert cp[0]['kappa']>cp[1]['kappa']>cp[2]['kappa']
    result=dict(parameters=dict(ncore=NC,nclad=NS,d_um=D,lambda_um=LAM),
       single=m,confinement=gamma,decay_um=1/m['q'],d_TE1_cutoff=LAM/(2*math.sqrt(NC*NC-NS*NS)),
       couplers=cp,checks=dict(power_error=power_error,orthogonality=orth,bracket_checks=gridcheck),
       P_b_at_reference_Lc=[math.sin(c['kappa']*ref['Lc'])**2 for c in cp])
    (DATA/'hasil.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    writecsv('profil_TE0.csv',['x_um','Ey_rel'],zip(x,e))
    writecsv('variasi_tebal.csv',['d_um','N_TE','neff_TE0','neff_TE1','neff_TE2'],zip(ds,nums,*branches))
    writecsv('daya_g4.csv',['z_um','Pa_P0','Pb_P0'],zip(z,pa,pb))
    writecsv('variasi_celah.csv',['g_um','kappa_per_um','Lc_um','L50_um'],[(c['g'],c['kappa'],c['Lc'],c['L50']) for c in cscan])
    geometry()
    # Rentang visual terpisah dari rentang data CSV.
    xx=np.linspace(-10,10,1201)
    plot('02_profil_TE0','Profil medan TE0 dan ekor evanescent','x (µm)','Ey / max |Ey|',[('TE0, d = 2 µm',xx,slab_field(xx,m))],(-10,10),(0,1.05),vlines=(-1,1))
    plot('03_dispersi_tebal','Indeks bias efektif terhadap tebal teras','d (µm)','n efektif (tanpa satuan)',[(f'TE{j}',ds,branches[j]) for j in range(3)],(.2,12),(NS,NC))
    plot('04_jumlah_modus','Jumlah modus TE terikat','d (µm)','Jumlah modus TE', [('N TE',ds,nums)],(.2,12),(0,3.5),vlines=(result['d_TE1_cutoff'],2*result['d_TE1_cutoff']))
    plot('05_daya_kopler','Pertukaran daya pada celah g = 4 µm','z (µm)','Daya / P0',[('Pandu a',z,pa),('Pandu b',z,pb)],(0,float(z[-1])),(0,1.05),vlines=(ref['L50'],ref['Lc']))
    plot('06_pengaruh_celah','Panjang transfer penuh terhadap celah','Celah g (µm)','Lc (µm)',[('Model supermode TE',gscan,[c['Lc'] for c in cscan])],(2,6),(0,math.ceil(cscan[-1]['Lc']/100)*100))
    plot('07_perbandingan_daya','Pengaruh celah pada perpindahan daya','z (µm)','Pb / P0',[(f'g = {c["g"]:g} µm',z,np.sin(c['kappa']*z)**2) for c in cp],(0,float(z[-1])),(0,1.05))
    # Data ringkas yang dipakai grafik native PowerPoint.
    chart=dict(x_field=xx[::10].tolist(),field=slab_field(xx,m)[::10].tolist(),
       thickness=ds.tolist(),branches=[[None if not np.isfinite(v) else v for v in branch] for branch in branches],
       counts=nums,z=z[::4].tolist(),pa=pa[::4].tolist(),pb=pb[::4].tolist(),
       gaps=gscan.tolist(),Lc=[c['Lc'] for c in cscan],
       pb_gaps=[(np.sin(c['kappa']*z[::4])**2).tolist() for c in cp])
    (DATA/'grafik_ppt.json').write_text(json.dumps(chart),encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
