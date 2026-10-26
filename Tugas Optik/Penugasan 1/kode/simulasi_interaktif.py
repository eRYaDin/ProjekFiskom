"""Simulasi Optik native: Python + NumPy + Tkinter + Matplotlib.
Jalankan: python simulasi_interaktif.py
Pemeriksaan numerik dan render tanpa jendela: python simulasi_interaktif.py --periksa
"""
from pathlib import Path
import argparse
import csv
import json
import math
import time
import sys

try:
    import numpy as np
    import matplotlib
except ImportError:
    raise SystemExit('Pasang dependensi: python -m pip install -r requirements_interaktif.txt')

from matplotlib.figure import Figure
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import FormatStrFormatter
from optik_model import slab_modes, slab_field, coupler, basis, intensity, intensity_max, powers, NC, NS

ROOT = Path(__file__).resolve().parents[1]
BG, PANEL, FG, MUTED = '#0c1420', '#121e2d', '#e8eef5', '#a9b9c9'
COLORS = ['#67dbd0','#ffb76b','#b9a0ff','#8fbfff','#f58eb9','#cddd84']
matplotlib.rcParams.update({'font.family':'DejaVu Sans','font.size':9,
    'figure.facecolor':PANEL,'axes.facecolor':PANEL,'axes.edgecolor':'#65758a',
    'axes.labelcolor':FG,'text.color':FG,'xtick.color':MUTED,'ytick.color':MUTED,
    'grid.color':'#344459','grid.alpha':.5,'legend.facecolor':PANEL,
    'legend.edgecolor':'#344459','savefig.facecolor':PANEL,'mathtext.fontset':'dejavusans'})
SIGNED = LinearSegmentedColormap.from_list('medan',['#284cbb','#101926','#ffba66'])
INTENSITY = LinearSegmentedColormap.from_list('intensitas',['#101926','#126586','#58d3bd','#f4e7a3'])


def figure():
    return Figure(figsize=(10.8,5.6),dpi=95,layout='constrained')


def decorate(ax, title, xlabel, ylabel, grid=True):
    ax.set(title=title,xlabel=xlabel,ylabel=ylabel)
    if grid:
        ax.grid(True,linewidth=.6)


def build_b(d=2., lam=1.55, selected=0, phase=0.):
    modes = slab_modes(d,lam)
    selected = min(selected,len(modes)-1)
    mode = modes[selected]
    extent = max(d/2+3,min(40,d/2+4/mode['q']))
    x = np.linspace(-extent,extent,401)
    z = np.linspace(0,8,701)
    profile = slab_field(x,mode)
    fig = figure()
    axes = fig.subplots(2,1,gridspec_kw={'height_ratios':[2,1.25]})
    ax, field_ax = axes
    image = ax.imshow(profile[:,None]*np.cos(mode['beta']*z[None,:]-phase),
        origin='lower',extent=(0,8,-extent,extent),aspect='auto',cmap=SIGNED,vmin=-1,vmax=1)
    for edge in [-d/2,d/2]:
        ax.axhline(edge,color='#d8e5ee',lw=.65,alpha=.8)
    decorate(ax,f"Medan sesaat TE{selected} | d = {d:.2f} µm | λ₀ = {lam:.2f} µm",
        'Propagasi z (µm)','Posisi melintang x (µm)',False)
    cb = fig.colorbar(image,ax=ax,pad=.015,ticks=[-1,0,1])
    cb.set_label(r'$E_y/E_0$')
    field_ax.axvspan(-d/2,d/2,color=COLORS[3],alpha=.12,label='Teras')
    field_ax.plot(x,profile,color=COLORS[0],label=r'$\psi_m(x)$ · amplitudo')
    field_ax.plot(x,profile**2,color=COLORS[1],label=r'$|\psi_m(x)|^2$ · intensitas')
    field_ax.set_xlim(-extent,extent)
    field_ax.set_ylim(-1.08,1.08)
    decorate(field_ax,'Profil mode melintang','Posisi x (µm)','Nilai relatif')
    field_ax.legend(loc='upper right',ncol=3,fontsize=8)
    fig._optik = dict(image=image,profile=profile,z=z,mode=mode)
    result = {'Peta medan & profil':fig}
    for label,xx,variable in [('Indeks efektif vs ketebalan',np.linspace(.5,12,180),'d'),
                              ('Indeks efektif vs panjang gelombang',np.linspace(.8,2.2,141),'lam')]:
        f = figure()
        a = f.subplots()
        ms = [slab_modes(float(v),lam) if variable=='d' else slab_modes(d,float(v)) for v in xx]
        for j in range(max(map(len,ms))):
            a.plot(xx,[m[j]['neff'] if len(m)>j else np.nan for m in ms],
                color=COLORS[j%6],label=rf'$\mathrm{{TE}}_{j}$')
        current = d if variable=='d' else lam
        a.axvline(current,color=FG,lw=1,ls='--')
        a.scatter([current],[mode['neff']],s=35,color=COLORS[selected%6],zorder=5)
        a.set(xlim=(xx[0],xx[-1]),ylim=(NS,NC))
        a.yaxis.set_major_formatter(FormatStrFormatter('%.4f'))
        title = f'λ₀ = {lam:.2f} µm' if variable=='d' else f'd = {d:.2f} µm; indeks bahan konstan'
        decorate(a,title,'Ketebalan penuh d (µm)' if variable=='d' else 'Panjang gelombang vakum λ₀ (µm)',
                 r'$n_{\mathrm{eff}}$ (tanpa satuan)')
        a.legend(loc='upper left',ncol=3)
        result[label] = f
    return result, mode, modes


def build_c(gap=4., position=0.):
    cp = coupler(float(gap))
    maximum = intensity_max(cp)
    xs, zs = np.linspace(-12,12,401), np.linspace(0,1400,701)
    values = intensity(xs[:,None],zs[None,:],cp)/maximum
    fig = figure()
    gs = fig.add_gridspec(2,2,height_ratios=[1.4,1])
    ax = fig.add_subplot(gs[0,:])
    image = ax.imshow(values,origin='lower',extent=(0,1400,-12,12),aspect='auto',cmap=INTENSITY,vmin=0,vmax=1)
    for edge in [-gap/2-2,-gap/2,gap/2,gap/2+2]:
        ax.axhline(edge,lw=.65,color='#d8e5ee',alpha=.7)
    cursor = ax.axvline(position,color=FG,ls='--',lw=1.1)
    ax.text(.015,.82,'Pandu b',transform=ax.transAxes,color=FG,fontsize=8)
    ax.text(.015,.14,'Pandu a',transform=ax.transAxes,color=FG,fontsize=8)
    decorate(ax,f'Intensitas medan dua pandu | celah g = {gap:.2f} µm','Propagasi z (µm)','Posisi x (µm)',False)
    cb = fig.colorbar(image,ax=ax,pad=.012,ticks=[0,.5,1])
    cb.set_label('Intensitas relatif')
    slice_ax, power_ax = fig.add_subplot(gs[1,0]),fig.add_subplot(gs[1,1])
    for lo,hi in [(-gap/2-2,-gap/2),(gap/2,gap/2+2)]:
        slice_ax.axvspan(lo,hi,color=COLORS[3],alpha=.13)
    slice_line, = slice_ax.plot(xs,intensity(xs,position,cp)/maximum,color=COLORS[0])
    decorate(slice_ax,f'Irisan z = {position:.1f} µm','Posisi x (µm)','Intensitas relatif')
    slice_ax.set(xlim=(-12,12),ylim=(0,1.05))
    pa,pb = powers(zs,cp)
    power_ax.plot(zs,pa,color=COLORS[0],label='Pandu a')
    power_ax.plot(zs,pb,color=COLORS[1],label='Pandu b')
    power_cursor = power_ax.axvline(position,color=FG,ls='--',lw=1)
    decorate(power_ax,'Daya modal sepanjang pandu','Propagasi z (µm)',r'$P/P_0$')
    power_ax.set(xlim=(0,1400),ylim=(0,1.05))
    power_ax.legend(loc='upper right',fontsize=8,ncol=2)
    fig._optik = dict(cursor=cursor,power_cursor=power_cursor,slice_line=slice_line,
                     slice_ax=slice_ax,x=xs,cp=cp,maximum=maximum)
    compare = figure()
    a = compare.subplots()
    for j,g in enumerate([2.,4.,6.]):
        c = coupler(g)
        a.plot(zs,powers(zs,c)[1],color=COLORS[j],label=f'g = {g:.0f} µm; Lc = {c["Lc"]:.2f} µm')
    compare_cursor = a.axvline(position,color=FG,ls='--',lw=1)
    decorate(a,'Perbandingan celah; d = 2 µm; λ₀ = 1,55 µm','Propagasi z (µm)',r'$P_b/P_0$')
    a.set(xlim=(0,1400),ylim=(0,1.05))
    a.legend(loc='upper right')
    compare._optik = dict(cursor=compare_cursor)
    return {'Peta intensitas & daya':fig,'Perbandingan celah':compare},cp


# MathText merender subset LaTeX tanpa instalasi TeX terpisah.
EQUATIONS_B = [r'$E_y(x,z,t)=E_0\,\psi_m(x)\cos(\beta_m z-\varphi_t)$',
    r'$\beta_m=\frac{2\pi n_{\mathrm{eff},m}}{\lambda_0},\qquad \lambda_z=\frac{\lambda_0}{n_{\mathrm{eff},m}}$']
EQUATIONS_C = [r'$P_a/P_0=\cos^2(\kappa z),\qquad P_b/P_0=\sin^2(\kappa z)$',
    r'$\kappa=\frac{\beta_e-\beta_o}{2},\qquad L_c=\frac{\pi}{2\kappa},\qquad L_{50:50}=\frac{L_c}{2}$']


def formula_figure(lines):
    f = Figure(figsize=(10.5,.85),dpi=90,facecolor=PANEL)
    for i,line in enumerate(lines):
        f.text(.025,.68-i*.49,line,fontsize=13,color=FG)
    return f


def export_csv(path, part, d=2., lam=1.55, selected=0, gap=4., position=0.):
    with Path(path).open('w',newline='',encoding='utf-8-sig') as stream:
        writer = csv.writer(stream)
        if part=='B':
            mode = slab_modes(d,lam)[selected]
            writer.writerow(['jenis','d_um','lambda_um','mode','x_um','psi','intensitas_rel','neff'])
            extent = max(d/2+3,min(40,d/2+4/mode['q']))
            for x in np.linspace(-extent,extent,601):
                e = float(slab_field(x,mode))
                writer.writerow(['profil',d,lam,selected,x,e,e*e,mode['neff']])
            for dd in np.linspace(.5,12,180):
                for m in slab_modes(float(dd),lam):
                    writer.writerow(['sweep_d',dd,lam,m['m'],'','','',m['neff']])
            for ll in np.linspace(.8,2.2,141):
                for m in slab_modes(d,float(ll)):
                    writer.writerow(['sweep_lambda',d,ll,m['m'],'','','',m['neff']])
        else:
            writer.writerow(['jenis','g_um','d_um','lambda_um','z_um','x_um','intensitas_rel','Pa_P0','Pb_P0','kappa_per_um','Lc_um'])
            for g in sorted(set([2.,4.,6.,gap])):
                c = coupler(g)
                for z in np.linspace(0,1400,701):
                    a,b = powers(z,c)
                    writer.writerow(['daya',g,2,1.55,z,'','',float(a),float(b),c['kappa'],c['Lc']])
            c = coupler(gap)
            mx = intensity_max(c)
            for x in np.linspace(-12,12,601):
                writer.writerow(['irisan',gap,2,1.55,position,x,float(intensity(x,position,c))/mx,'','',c['kappa'],c['Lc']])


HELP_B = """Biru = medan listrik negatif; jingga = positif; gelap = mendekati nol. Warna merupakan kode nilai medan.
Dua garis mendatar adalah batas teras x = ±d/2. Arah z ke kanan adalah arah rambat; arah x melintang.
ψm(x): profil amplitudo mode, maksimum |ψ| = 1. TE0 tanpa simpul di teras; TEm memiliki m simpul.
β: konstanta propagasi (rad/µm). λ₀: panjang gelombang vakum (µm). λz: periode spasial sepanjang z.
φt = ωt: fase waktu (rad); animasi diperlambat. E₀: amplitudo acuan listrik (V/m), tidak ditetapkan absolut.
Medan di selubung meluruh eksponensial. Panjang peluruhan amplitudo adalah 1/q (µm).
Untuk satu mode pada pandu ideal tanpa rugi, intensitas rata-rata waktu ∝ |ψ|² tetap sepanjang z.
Pada grafik dispersi, tiap kurva menunjukkan satu mode. Garis tegak menandai parameter saat ini.
Indeks bahan dijaga tetap: perubahan n efektif terhadap λ₀ merupakan dispersi geometri pandu.
Mode di cutoff tidak dihitung sebagai mode terikat. Nilai n efektif berada di antara 1,50 dan 1,51."""
HELP_C = """Pandu a berada pada x negatif (bawah peta), pandu b pada x positif (atas). Celah g diukur tepi-ke-tepi.
Teras identik d = 2 µm; λ₀ = 1,55 µm; n teras = 1,51; n selubung = 1,50.
Gelap = intensitas rendah; hijau–kuning = lebih tinggi. Skala 0–1 sama untuk seluruh peta pada celah terpilih.
Peta memakai superposisi dua supermode TE, bukan gambar lintasan foton. Skala x dan z berbeda.
Animasi menggeser irisan z pada pola keadaan tunak; tidak menunjukkan kecepatan sebuah pulsa.
βe dan βo: konstanta propagasi supermode genap dan ganjil. κ: koefisien kopling (µm⁻¹).
Lc: jarak transfer penuh pertama (µm). L50:50: jarak pembagian daya sama besar pertama (µm).
Pa/P₀ dan Pb/P₀: rasio daya modal, tidak berdimensi. Model tanpa rugi memenuhi Pa + Pb = P₀.
Persentase mengacu ke basis modal, termasuk ekor evanescent; bukan integral hanya di inti teras.
Kombinasi dua supermode terlokalisasi terutama di pandu a; lokalisasi kurang sempurna saat celah kecil.
Celah lebih besar memperlemah kopling dan memperpanjang Lc. Daya pada z tetap dapat berubah nonmonoton.
Model mengasumsikan bahan isotropik, indeks tetap, tak berhingga pada y, dan seragam sepanjang z.
Rugi bahan, fabrikasi, radiasi port, dan transien pulsa tidak dimodelkan."""


def launch():
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

    class App:
        def __init__(self, root):
            self.root=root
            root.title('Simulasi Optik Modern — Python')
            root.geometry('1240x860')
            root.minsize(980,730)
            root.configure(bg=BG)
            style=ttk.Style(root)
            style.theme_use('clam')
            style.configure('.',background=BG,foreground=FG,font=('Segoe UI',10))
            style.configure('TFrame',background=BG)
            style.configure('TLabel',background=BG,foreground=FG)
            style.configure('TNotebook',background=BG,borderwidth=0)
            style.configure('TNotebook.Tab',background=PANEL,foreground=FG,padding=(16,8))
            style.map('TNotebook.Tab',background=[('selected',COLORS[0])],foreground=[('selected',BG)])
            style.configure('TButton',background=PANEL,foreground=FG,padding=(10,6))
            style.map('TButton',background=[('active','#294455')])
            style.configure('TCombobox',fieldbackground=PANEL,background=PANEL,foreground=FG)
            style.map('TCombobox',fieldbackground=[('readonly',PANEL)],foreground=[('readonly',FG)])
            style.configure('Horizontal.TScale',background=BG,troughcolor=PANEL)
            self.d=tk.DoubleVar(value=2)
            self.lam=tk.DoubleVar(value=1.55)
            self.gap=tk.DoubleVar(value=4)
            self.phase=tk.DoubleVar(value=0)
            self.z=tk.DoubleVar(value=0)
            self.mode=tk.StringVar(value='TE0')
            self.pending=None
            self.playing=False
            self.last=time.perf_counter()
            self.figures={}
            self.canvases={}
            self.readings={}
            self.viewbooks={}
            self.viewframes={}
            self.syncing=False
            ttk.Label(root,text='OPTIKA MODERN / PENUGASAN 1',foreground=COLORS[0],font=('Segoe UI',10)).pack(anchor='w',padx=18,pady=(12,2))
            ttk.Label(root,text='Melihat cahaya di dalam pandu',font=('Segoe UI',20,'bold')).pack(anchor='w',padx=18,pady=(0,10))
            self.book=ttk.Notebook(root)
            self.book.pack(fill='both',expand=True,padx=12,pady=(0,10))
            self.frames={}
            for part,title in [('B','B · Pandu tunggal'),('C','C · Directional coupler')]:
                frame=ttk.Frame(self.book,padding=8)
                self.book.add(frame,text=title)
                self.frames[part]=frame
                self.make_part(part)
            self.make_help()
            self.book.bind('<<NotebookTabChanged>>',lambda e:self.pause())
            root.protocol('WM_DELETE_WINDOW',self.close)
            self.rebuild('B')
            self.rebuild('C')
            root.after(100,self.tick)

        def active(self):
            return 'B' if self.book.index(self.book.select())==0 else 'C' if self.book.index(self.book.select())==1 else 'help'

        def slider(self,parent,label,var,lo,hi,step,col,width=180,handler=None):
            box=ttk.Frame(parent)
            box.grid(row=0,column=col,padx=8,sticky='ew')
            parent.columnconfigure(col,weight=1)
            text=tk.StringVar()
            ttk.Label(box,textvariable=text).pack(anchor='w')
            def update(value):
                if self.syncing:return
                number=round(round(float(value)/step)*step,6)
                var.set(number)
                text.set(f'{label}: {number:.2f}')
                if handler:handler()
                else:self.schedule()
            scale=ttk.Scale(box,from_=lo,to=hi,variable=var,command=update,length=width)
            scale.pack(fill='x',pady=(5,2))
            text.set(f'{label}: {var.get():.2f}')
            return text

        def make_part(self,part):
            parent=self.frames[part]
            parent.columnconfigure(0,weight=1)
            parent.rowconfigure(3,weight=1)
            controls=ttk.Frame(parent)
            controls.grid(row=0,column=0,sticky='ew')
            if part=='B':
                self.slider(controls,'Tebal penuh d (µm)',self.d,.5,12,.1,0)
                self.slider(controls,'Panjang gelombang λ₀ (µm)',self.lam,.8,2.2,.05,1)
                box=ttk.Frame(controls)
                box.grid(row=0,column=2,padx=8)
                ttk.Label(box,text='Mode terikat').pack(anchor='w')
                self.mode_box=ttk.Combobox(box,textvariable=self.mode,values=['TE0'],state='readonly',width=8)
                self.mode_box.pack(pady=4)
                self.mode_box.bind('<<ComboboxSelected>>',lambda e:self.schedule())
            else:
                self.slider(controls,'Celah tepi-ke-tepi g (µm)',self.gap,2,6,.1,0)
                self.zlabel=self.slider(controls,'Posisi z (µm)',self.z,0,1400,.1,1,handler=self.position_changed)
            actions=ttk.Frame(parent)
            actions.grid(row=1,column=0,sticky='ew',pady=(6,2))
            play=ttk.Button(actions,text='▶ Jalankan fase' if part=='B' else '▶ Ikuti propagasi',command=self.toggle)
            play.pack(side='left',padx=4)
            setattr(self,'play_'+part,play)
            if part=='C':
                ttk.Button(actions,text='Ke 50:50',command=lambda:self.jump(.5)).pack(side='left',padx=4)
                ttk.Button(actions,text='Ke transfer penuh',command=lambda:self.jump(1)).pack(side='left',padx=4)
            else:
                ttk.Button(actions,text='Fase awal',command=self.reset_phase).pack(side='left',padx=4)
            ttk.Button(actions,text='Simpan grafik PNG',command=self.save_png).pack(side='right',padx=4)
            ttk.Button(actions,text='Simpan data CSV',command=self.save_csv).pack(side='right',padx=4)
            reading=tk.StringVar()
            self.readings[part]=reading
            ttk.Label(parent,textvariable=reading,foreground=COLORS[0],wraplength=1150).grid(row=2,column=0,sticky='ew',padx=6,pady=5)
            vb=ttk.Notebook(parent)
            vb.grid(row=3,column=0,sticky='nsew')
            self.viewbooks[part]=vb
            self.viewframes[part]={}
            vb.bind('<<NotebookTabChanged>>',lambda e:self.pause())
            helptext=('Biru: medan negatif · Jingga: medan positif · Gelap: mendekati nol. Dua garis mendatar: batas teras. '
                      'Intensitas rata-rata mode tunggal tetap sepanjang z.' if part=='B' else
                      'Gelap: intensitas rendah · Hijau–kuning: lebih tinggi. Pandu a di bawah, b di atas. '
                      'Persentase menunjukkan daya modal; animasi menggeser irisan pengamatan.')
            ttk.Label(parent,text=helptext,wraplength=1150).grid(row=4,column=0,sticky='ew',padx=8,pady=(5,1))
            formula=formula_figure(EQUATIONS_B if part=='B' else EQUATIONS_C)
            fc=FigureCanvasTkAgg(formula,master=parent)
            fc.get_tk_widget().configure(height=77)
            fc.get_tk_widget().grid(row=5,column=0,sticky='ew')
            fc.draw()

        def make_help(self):
            page=ttk.Frame(self.book,padding=15)
            self.book.add(page,text='Keterangan & rumus')
            tabs=ttk.Notebook(page)
            tabs.pack(fill='both',expand=True)
            for part,content in [('B',HELP_B),('C',HELP_C)]:
                frame=ttk.Frame(tabs,padding=12)
                tabs.add(frame,text='Bagian '+part)
                text=tk.Text(frame,wrap='word',height=15,bg=PANEL,fg=FG,insertbackground=FG,
                             relief='flat',font=('Segoe UI',11),padx=14,pady=12)
                scroll=ttk.Scrollbar(frame,command=text.yview)
                text.configure(yscrollcommand=scroll.set)
                scroll.pack(side='right',fill='y')
                text.pack(fill='both',expand=True)
                text.insert('1.0',content)
                text.configure(state='disabled')
                extra=EQUATIONS_B+[r'$\psi_0(x)=\cos(hx)\quad (|x|\leq d/2)$',
                    r'$\psi_0(x)=\cos(hd/2)\,e^{-q(|x|-d/2)}\quad (|x|>d/2)$',
                    r'$h=\sqrt{k_0^2n_{\mathrm{core}}^2-\beta_0^2},\quad q=\sqrt{\beta_0^2-k_0^2n_{\mathrm{clad}}^2}$'] if part=='B' else EQUATIONS_C
                formula=Figure(figsize=(10,2.3),dpi=90,facecolor=PANEL)
                for i,line in enumerate(extra):formula.text(.03,.84-i*.18,line,fontsize=13,color=FG)
                canvas=FigureCanvasTkAgg(formula,master=frame)
                canvas.get_tk_widget().pack(fill='x')
                canvas.draw()

        def schedule(self):
            self.pause()
            if self.pending:self.root.after_cancel(self.pending)
            part=self.active()
            if part in ('B','C'):self.pending=self.root.after(180,lambda:self.rebuild(part))

        def rebuild(self,part):
            self.pending=None
            if part=='B':
                selected=int(self.mode.get()[2:])
                figs,self.bmode,modes=build_b(self.d.get(),self.lam.get(),selected,self.phase.get())
                self.mode_box.configure(values=[f'TE{m["m"]}' for m in modes])
                self.mode.set(f'TE{self.bmode["m"]}')
            else:
                figs,self.cp=build_c(self.gap.get(),self.z.get())
            vb=self.viewbooks[part]
            old=vb.index(vb.select()) if vb.tabs() else 0
            # Dispose Tk canvases before forgetting old figure references.
            for widget in vb.winfo_children():widget.destroy()
            self.figures[part]=figs
            self.canvases[part]={}
            for title,fig in figs.items():
                frame=ttk.Frame(vb)
                vb.add(frame,text=title)
                cv=FigureCanvasTkAgg(fig,master=frame)
                toolbar=NavigationToolbar2Tk(cv,frame,pack_toolbar=False)
                toolbar.update()
                toolbar.pack(side='bottom',fill='x')
                cv.get_tk_widget().pack(fill='both',expand=True)
                cv.draw()
                self.canvases[part][title]=cv
            vb.select(min(old,len(figs)-1))
            self.update_reading(part)

        def update_reading(self,part):
            if part=='B':
                m=self.bmode
                self.readings[part].set(f"TE{m['m']} | n efektif = {m['neff']:.6f} | β = {m['beta']:.5f} rad/µm | "
                    f"λz = {m['lam']/m['neff']:.3f} µm | 1/q = {1/m['q']:.3f} µm | fase = {self.phase.get():.2f} rad")
            else:
                a,b=powers(self.z.get(),self.cp)
                self.readings[part].set(f"κ = {self.cp['kappa']:.7f} µm⁻¹ | L50:50 = {self.cp['Lc']/2:.2f} µm | "
                    f"Lc = {self.cp['Lc']:.2f} µm | z = {self.z.get():.1f} µm | Pa = {a*100:.1f}% | Pb = {b*100:.1f}%")

        def pause(self):
            self.playing=False
            for part in ('B','C'):
                button=getattr(self,'play_'+part,None)
                if button:button.configure(text='▶ Jalankan fase' if part=='B' else '▶ Ikuti propagasi')

        def toggle(self):
            if self.active() not in ('B','C'):return
            if self.pending:
                self.root.after_cancel(self.pending)
                self.rebuild(self.active())
            if self.playing:self.pause();return
            part=self.active()
            self.viewbooks[part].select(0)
            # Notebook event settles before starting animation.
            self.root.after_idle(lambda:self.start_animation(part))

        def start_animation(self,part):
            if self.active()!=part:return
            if part=='C' and self.z.get()>=1400:self.z.set(0)
            self.playing=True
            self.last=time.perf_counter()
            getattr(self,'play_'+part).configure(text='Ⅱ Jeda')

        def tick(self):
            now=time.perf_counter()
            dt=min(.15,now-self.last)
            self.last=now
            if self.playing:
                part=self.active()
                if part=='B':
                    self.phase.set((self.phase.get()+dt*1.5)%(2*math.pi))
                    self.update_phase()
                elif part=='C':
                    self.z.set(min(1400,self.z.get()+dt*100))
                    self.update_position()
                    if self.z.get()>=1400:self.pause()
            self.root.after(65,self.tick)

        def update_phase(self):
            fig=next(iter(self.figures['B'].values()))
            v=fig._optik
            v['image'].set_data(v['profile'][:,None]*np.cos(v['mode']['beta']*v['z'][None,:]-self.phase.get()))
            next(iter(self.canvases['B'].values())).draw_idle()
            self.update_reading('B')

        def reset_phase(self):
            self.pause()
            self.phase.set(0)
            self.update_phase()

        def position_changed(self):
            self.pause()
            if hasattr(self,'cp'):self.update_position()

        def update_position(self):
            if not self.figures.get('C'):return
            fig=next(iter(self.figures['C'].values()))
            v=fig._optik
            z=self.z.get()
            v['cursor'].set_xdata([z,z])
            v['power_cursor'].set_xdata([z,z])
            v['slice_line'].set_ydata(intensity(v['x'],z,self.cp)/v['maximum'])
            v['slice_ax'].set_title(f'Irisan z = {z:.1f} µm')
            compare=list(self.figures['C'].values())[1]
            compare._optik['cursor'].set_xdata([z,z])
            book=self.viewbooks['C']
            title=list(self.figures['C'])[book.index(book.select())]
            self.canvases['C'][title].draw_idle()
            self.zlabel.set(f'Posisi z (µm): {z:.2f}')
            self.update_reading('C')

        def jump(self,fraction):
            self.pause()
            if self.pending:
                self.root.after_cancel(self.pending)
                self.rebuild('C')
            self.z.set(self.cp['Lc']*fraction)
            self.update_position()

        def selected_figure(self):
            part=self.active()
            if part not in ('B','C'):return None
            vb=self.viewbooks[part]
            return list(self.figures[part].values())[vb.index(vb.select())]

        def save_png(self):
            self.pause()
            if self.pending:
                self.root.after_cancel(self.pending)
                self.rebuild(self.active())
            fig=self.selected_figure()
            if fig is None:return
            folder=ROOT/'grafik'/'python'
            folder.mkdir(parents=True,exist_ok=True)
            dest=filedialog.asksaveasfilename(title='Simpan grafik aktif',initialdir=str(folder),
                initialfile=f'simulasi_{self.active()}.png',defaultextension='.png',filetypes=[('Gambar PNG','*.png')])
            if dest:
                fig.savefig(dest,dpi=180)
                messagebox.showinfo('Grafik tersimpan',dest)

        def save_csv(self):
            self.pause()
            if self.pending:
                self.root.after_cancel(self.pending)
                self.rebuild(self.active())
            part=self.active()
            folder=ROOT/'data'/'python'
            folder.mkdir(parents=True,exist_ok=True)
            dest=filedialog.asksaveasfilename(title='Simpan data simulasi',initialdir=str(folder),
                initialfile=f'data_bagian_{part}.csv',defaultextension='.csv',filetypes=[('Data CSV','*.csv')])
            if dest:
                export_csv(dest,part,self.d.get(),self.lam.get(),int(self.mode.get()[2:]),self.gap.get(),self.z.get())
                messagebox.showinfo('Data tersimpan',dest)

        def close(self):
            self.pause()
            if self.pending:self.root.after_cancel(self.pending)
            self.root.destroy()

    root=tk.Tk()
    App(root)
    root.mainloop()


def verify():
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    ref=json.loads((ROOT/'data/hasil.json').read_text(encoding='utf-8'))
    assert abs(slab_modes()[0]['neff']-ref['single']['neff'])<1e-11
    for row in ref['couplers']:
        c=coupler(row['g'])
        assert abs(c['Lc']-row['Lc'])<1e-6
        assert abs(float(powers(c['Lc'],c)[1])-1)<1e-12
        assert abs(float(powers(c['Lc']/2,c)[1])-.5)<1e-12
        x=np.linspace(-70,70,40001)
        e,o=basis(x,c)
        assert abs(np.trapezoid(e*e,x)*c['be']-1)<1e-7
        assert abs(np.trapezoid(o*o,x)*c['bo']-1)<1e-7
        assert np.max(abs(intensity(x,0,c)-intensity(-x,c['Lc'],c)))<1e-12
    cutoff=1.55/(2*math.sqrt(NC**2-NS**2))
    assert len(slab_modes(cutoff))==1 and len(slab_modes(cutoff+.001))==2
    dest=ROOT/'grafik/python'
    dest.mkdir(parents=True,exist_ok=True)
    b,_,_=build_b()
    c,_=build_c(4,coupler(4)['Lc']/2)
    for i,fig in enumerate(list(b.values())+list(c.values()),1):
        FigureCanvasAgg(fig).draw()
        fig.savefig(dest/f'python_{i:02d}.png',dpi=130)
    for lines in [EQUATIONS_B,EQUATIONS_C]:FigureCanvasAgg(formula_figure(lines)).draw()
    # Render the TE0 help formulas as well.
    help_formula=formula_figure([r'$\psi_0(x)=\cos(hx)\quad (|x|\leq d/2)$',
        r'$\psi_0(x)=\cos(hd/2)e^{-q(|x|-d/2)}\quad (|x|>d/2)$'])
    FigureCanvasAgg(help_formula).draw()
    data=ROOT/'data/python'
    data.mkdir(parents=True,exist_ok=True)
    export_csv(data/'bagian_B.csv','B')
    export_csv(data/'bagian_C.csv','C',position=coupler(4)['Lc']/2)
    for p in data.glob('bagian_*.csv'):
        with p.open(encoding='utf-8-sig') as f:assert len(list(csv.reader(f)))>1000
    print('LULUS: angka acuan, cutoff, normalisasi, transfer 50:50/penuh, pertukaran profil, 5 gambar, rumus MathText, dan CSV.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Simulasi Optik Modern Python')
    parser.add_argument('--periksa',action='store_true',help='Uji model dan ekspor acuan tanpa membuka jendela')
    args=parser.parse_args()
    if args.periksa:verify()
    else:launch()
