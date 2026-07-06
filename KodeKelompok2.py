import numpy as np
import random
import threading
import time
import tkinter as tk
from tkinter import ttk
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


LEBAR_AREA = 0.05
TINGGI_AREA = 0.05
JUMLAH_TITIK_X = 50
JUMLAH_TITIK_Y = 50
DELTA_X = LEBAR_AREA / (JUMLAH_TITIK_X - 1)
DELTA_Y = TINGGI_AREA / (JUMLAH_TITIK_Y - 1)

DELTA_WAKTU = 0.0001
LANGKAH_VISUAL_DEFAULT = 1.0

SUHU_LINGKUNGAN = 25.0
DAYA_CPU_WATT = 50.0
VOLUME_CPU = (0.02 * 0.005 * 0.02)

ID_UDARA = 0
ID_CPU = 1
ID_PASTA_TERMAL = 2
ID_PENDINGIN = 3

SIFAT_MATERIAL = {
    ID_UDARA:        (0.026,  1.225,  1005.0),
    ID_CPU:          (149.0,  2330.0,  710.0),
    ID_PASTA_TERMAL: (5.0,    2200.0, 1000.0),
    ID_PENDINGIN:    (237.0,  2700.0,  900.0),
}

PILIHAN_CPU = {
    "Silikon":                (149.0, 2330.0, 710.0),
    "Tembaga (Heatspreader)": (400.0, 8960.0, 385.0),
}
PILIHAN_PASTA = {
    "Pasta Murah (2 W/mK)":    (2.0,  2200.0, 1000.0),
    "Pasta Standar (5 W/mK)":  (5.0,  2200.0, 1000.0),
    "Pasta Premium (10 W/mK)": (10.0, 2500.0,  900.0),
    "Liquid Metal (73 W/mK)":  (73.0, 6280.0,  145.0),
}
PILIHAN_PENDINGIN = {
    "Aluminium": (237.0, 2700.0, 900.0),
    "Tembaga":   (400.0, 8960.0, 385.0),
}
EFISIENSI_TIM = {
    "TIM Ideal (100%)":       1.00,
    "TIM Standar (85%)":      0.85,
    "TIM Terdegradasi (50%)": 0.50,
}

MODE_BEBAN_LIST = ["Konstan", "Manual (Skenario)", "Random"]
SKENARIO_BEBAN_CPU = [
    (40.0, 0.20), (60.0, 0.70), (60.0, 1.00), (40.0, 0.20),
]
TAU_RAMP_BEBAN  = 3.0
T_AMBIENT_MIN   = 25.0
T_AMBIENT_MAX   = 27.0
PERIODE_AMBIENT = 120.0
H_KONVEKSI      = 25.0

WARNA_MARKER = {
    "cpu":      "#e74c3c",  
    "pasta":    "#9b59b6",  
    "heatsink": "#2ecc71",   
    "kualitas": "#f39c12",   
    "manual":   "#1abc9c",   
}


def buat_peta_material(nx=JUMLAH_TITIK_X, ny=JUMLAH_TITIK_Y, dx=None, dy=None, ketebalan_pasta=0.001):
    if dx is None:
        dx = LEBAR_AREA / (nx - 1)
    if dy is None:
        dy = TINGGI_AREA / (ny - 1)

    peta = np.full((ny, nx), ID_UDARA)
    titik_tebal_pasta = max(1, int(ketebalan_pasta / dy))

    lebar_cpu = 0.02
    titik_lebar_cpu = max(1, int(lebar_cpu / dx))
    mulai_x_cpu = (nx - titik_lebar_cpu) // 2
    akhir_x_cpu = mulai_x_cpu + titik_lebar_cpu
    tinggi_cpu = 0.005
    titik_tinggi_cpu = max(1, int(tinggi_cpu / dy))
    peta[0:titik_tinggi_cpu, mulai_x_cpu:akhir_x_cpu] = ID_CPU

    mulai_y_pasta = titik_tinggi_cpu
    akhir_y_pasta = mulai_y_pasta + titik_tebal_pasta
    peta[mulai_y_pasta:akhir_y_pasta, mulai_x_cpu:akhir_x_cpu] = ID_PASTA_TERMAL

    lebar_dasar_pendingin = 0.04
    titik_lebar_dasar = max(1, int(lebar_dasar_pendingin / dx))
    mulai_x_dasar = (nx - titik_lebar_dasar) // 2
    akhir_x_dasar = mulai_x_dasar + titik_lebar_dasar
    tebal_dasar = 0.005
    titik_tebal_dasar = max(1, int(tebal_dasar / dy))
    akhir_y_dasar = min(akhir_y_pasta + titik_tebal_dasar, ny)
    peta[akhir_y_pasta:akhir_y_dasar, mulai_x_dasar:akhir_x_dasar] = ID_PENDINGIN

    jumlah_sirip = 10
    lebar_sirip = 0.002
    titik_lebar_sirip = max(1, int(lebar_sirip / dx))
    jarak_antar_sirip = max(0, (titik_lebar_dasar - (jumlah_sirip * titik_lebar_sirip)) // max(1, (jumlah_sirip - 1)))

    mulai_x_sirip = mulai_x_dasar
    for i in range(jumlah_sirip):
        akhir_x_sirip_ini = min(mulai_x_sirip + titik_lebar_sirip, nx)
        if akhir_y_dasar < ny:
            peta[akhir_y_dasar:ny, mulai_x_sirip:akhir_x_sirip_ini] = ID_PENDINGIN
        mulai_x_sirip += titik_lebar_sirip + jarak_antar_sirip

    return peta


def target_beban_manual(t, skenario=None):
    if skenario is None:
        skenario = SKENARIO_BEBAN_CPU
    total_durasi = sum(d for d, _ in skenario)
    if total_durasi <= 0:
        return 1.0
    t_mod = t % total_durasi
    kumulatif = 0.0
    for durasi, fraksi in skenario:
        kumulatif += durasi
        if t_mod <= kumulatif:
            return fraksi
    return skenario[-1][1]


def suhu_ambient(t, t_min=T_AMBIENT_MIN, t_max=T_AMBIENT_MAX, periode=PERIODE_AMBIENT):
    tengah    = (t_min + t_max) / 2.0
    amplitudo = (t_max - t_min) / 2.0
    return tengah - amplitudo * np.cos(2 * np.pi * t / periode)


def buat_sifat_material(nama_cpu, nama_pasta, nama_heatsink, nama_kualitas):
    k_pasta, rho_pasta, cp_pasta = PILIHAN_PASTA[nama_pasta]
    efisiensi       = EFISIENSI_TIM[nama_kualitas]
    k_pasta_efektif = k_pasta * efisiensi
    return {
        ID_UDARA:        SIFAT_MATERIAL[ID_UDARA],
        ID_CPU:          PILIHAN_CPU[nama_cpu],
        ID_PASTA_TERMAL: (k_pasta_efektif, rho_pasta, cp_pasta),
        ID_PENDINGIN:    PILIHAN_PENDINGIN[nama_heatsink],
    }


def hitung_difusivitas(peta_material, sifat_material):
    alpha_matriks = np.zeros_like(peta_material, dtype=float)
    for id_mat, (k, rho, cp) in sifat_material.items():
        alpha_matriks[peta_material == id_mat] = k / (rho * cp)
    return alpha_matriks


def hitung_rho_cp(peta_material, sifat_material):
    rho_cp_matriks = np.zeros_like(peta_material, dtype=float)
    for id_mat, (k, rho, cp) in sifat_material.items():
        rho_cp_matriks[peta_material == id_mat] = rho * cp
    return rho_cp_matriks


def hitung_pembangkit_panas(peta_material, sifat_material):
    q_matriks = np.zeros_like(peta_material, dtype=float)
    k_cpu, rho_cpu, cp_cpu = sifat_material[ID_CPU]
    q_gen = DAYA_CPU_WATT / VOLUME_CPU
    suhu_tambahan_per_detik = q_gen / (rho_cpu * cp_cpu)
    q_matriks[peta_material == ID_CPU] = suhu_tambahan_per_detik
    return q_matriks


def pembaruan_suhu(suhu_lama, alpha_matriks, rho_cp_matriks, matriks_sumber_panas,
                   dt, dx, dy, t_ambient, h=H_KONVEKSI):
    suhu_baru = suhu_lama.copy()
    ny, nx = suhu_lama.shape

    d2T_dx2 = (suhu_lama[1:-1, 2:] - 2*suhu_lama[1:-1, 1:-1] + suhu_lama[1:-1, :-2]) / (dx**2)
    d2T_dy2 = (suhu_lama[2:, 1:-1] - 2*suhu_lama[1:-1, 1:-1] + suhu_lama[:-2, 1:-1]) / (dy**2)
    suhu_baru[1:-1, 1:-1] = suhu_lama[1:-1, 1:-1] + dt * (
        alpha_matriks[1:-1, 1:-1] * (d2T_dx2 + d2T_dy2) + matriks_sumber_panas[1:-1, 1:-1]
    )

    suhu_baru[0, :] = suhu_baru[1, :]  

    alpha_atas, rho_cp_atas = alpha_matriks[-1, :], rho_cp_matriks[-1, :]
    d2T_dx2_atas = np.zeros(nx)
    d2T_dx2_atas[1:-1] = (suhu_lama[-1,2:] - 2*suhu_lama[-1,1:-1] + suhu_lama[-1,:-2]) / (dx**2)
    suhu_baru[-1, :] = suhu_lama[-1, :] + dt * (
        alpha_atas * (2.0*(suhu_lama[-2,:] - suhu_lama[-1,:])/(dy**2) + d2T_dx2_atas)
        - (2.0*h/(rho_cp_atas*dy)) * (suhu_lama[-1,:] - t_ambient)
        + matriks_sumber_panas[-1, :]
    )

    alpha_kiri, rho_cp_kiri = alpha_matriks[:, 0], rho_cp_matriks[:, 0]
    d2T_dy2_kiri = np.zeros(ny)
    d2T_dy2_kiri[1:-1] = (suhu_lama[2:,0] - 2*suhu_lama[1:-1,0] + suhu_lama[:-2,0]) / (dy**2)
    suhu_baru[:, 0] = suhu_lama[:, 0] + dt * (
        alpha_kiri * (2.0*(suhu_lama[:,1] - suhu_lama[:,0])/(dx**2) + d2T_dy2_kiri)
        - (2.0*h/(rho_cp_kiri*dx)) * (suhu_lama[:,0] - t_ambient)
        + matriks_sumber_panas[:, 0]
    )

    alpha_kanan, rho_cp_kanan = alpha_matriks[:, -1], rho_cp_matriks[:, -1]
    d2T_dy2_kanan = np.zeros(ny)
    d2T_dy2_kanan[1:-1] = (suhu_lama[2:,-1] - 2*suhu_lama[1:-1,-1] + suhu_lama[:-2,-1]) / (dy**2)
    suhu_baru[:, -1] = suhu_lama[:, -1] + dt * (
        alpha_kanan * (2.0*(suhu_lama[:,-2] - suhu_lama[:,-1])/(dx**2) + d2T_dy2_kanan)
        - (2.0*h/(rho_cp_kanan*dx)) * (suhu_lama[:,-1] - t_ambient)
        + matriks_sumber_panas[:, -1]
    )

    return suhu_baru


def cek_dt_aman(sifat_material, dx=DELTA_X, dy=DELTA_Y, h_konveksi=H_KONVEKSI):
    alpha_maks  = max(k / (rho * cp) for k, rho, cp in sifat_material.values())
    rho_cp_min  = min(rho * cp for _, rho, cp in sifat_material.values())
    dt_maks_difusi    = 0.5 / (alpha_maks * (1/dx**2 + 1/dy**2))
    dt_maks_konveksi  = rho_cp_min * min(dx, dy) / (2.0 * h_konveksi)
    dt_maks = min(dt_maks_difusi, dt_maks_konveksi)
    return DELTA_WAKTU if DELTA_WAKTU <= dt_maks else dt_maks * 0.9


def uji_konvergensi_grid(daftar_nx, t_akhir, nama_cpu, nama_tim, nama_heatsink, nama_kualitas, callback_progress=None):
    hasil = []
    for nx in daftar_nx:
        ny = nx
        dx = LEBAR_AREA / (nx - 1)
        dy = TINGGI_AREA / (ny - 1)
        peta = buat_peta_material(nx=nx, ny=ny, dx=dx, dy=dy)
        sifat = buat_sifat_material(nama_cpu, nama_tim, nama_heatsink, nama_kualitas)
        alpha = hitung_difusivitas(peta, sifat)
        rho_cp = hitung_rho_cp(peta, sifat)
        q = hitung_pembangkit_panas(peta, sifat)
        dt = cek_dt_aman(sifat, dx=dx, dy=dy)
        suhu = np.full((ny, nx), suhu_ambient(0.0))
        t = 0.0
        while t < t_akhir:
            t_amb = suhu_ambient(t)
            suhu = pembaruan_suhu(suhu, alpha, rho_cp, q, dt, dx, dy, t_ambient=t_amb)
            t += dt
        suhu_maks_cpu = float(np.max(suhu[peta == ID_CPU]))
        hasil.append((nx, dx, suhu_maks_cpu))
        if callback_progress is not None:
            callback_progress(nx, suhu_maks_cpu)
    return hasil


def hitung_galat_relatif(hasil):
    galat = []
    if not hasil:
        return galat
    referensi = hasil[-1][2]
    for nx, dx, suhu in hasil:
        if abs(referensi) > 1e-12:
            g = abs(suhu - referensi) / abs(referensi) * 100.0
        else:
            g = float('nan')
        galat.append((nx, dx, suhu, g))
    return galat


class StateSimulasiLive:
    def __init__(self):
        self.lock = threading.Lock()

        self.nama_cpu         = "Silikon"
        self.nama_tim         = "Pasta Standar (5 W/mK)"
        self.nama_heatsink    = "Aluminium"
        self.nama_kualitas_tim = "TIM Standar (85%)"

        self.mode_beban      = "Manual (Skenario)"
        self.beban_konstan   = 0.6
        self.rentang_random  = (0.10, 1.00)
        self.interval_random = 3.0

        self.langkah_visual_detik = LANGKAH_VISUAL_DEFAULT

        self.berjalan      = True
        self.reset_diminta = False

        self.beban_aktual                  = 0.2
        self.target_random                 = 0.2
        self.waktu_ganti_random_berikutnya = 0.0

        self.waktu_sekarang      = 0.0
        self.suhu_terbaru        = None
        self.peta_material       = buat_peta_material()
        self.suhu_maks_cpu_histori = []
        self.beban_histori         = []
        self.frame_baru_tersedia   = False

        self.marker_antrian  = []  
        self.marker_pending  = [] 

    def baca_param(self):
        with self.lock:
            return dict(
                nama_cpu       = self.nama_cpu,
                nama_tim       = self.nama_tim,
                nama_heatsink  = self.nama_heatsink,
                nama_kualitas_tim = self.nama_kualitas_tim,
                mode_beban     = self.mode_beban,
                beban_konstan  = self.beban_konstan,
                rentang_random = self.rentang_random,
                interval_random = self.interval_random,
                langkah_visual_detik = self.langkah_visual_detik,
                berjalan       = self.berjalan,
            )

    def tulis_frame(self, t, suhu, suhu_maks_cpu, beban_persen):
        with self.lock:
            self.waktu_sekarang = t
            self.suhu_terbaru   = suhu
            self.suhu_maks_cpu_histori.append((t, suhu_maks_cpu))
            self.beban_histori.append((t, beban_persen))
            if len(self.suhu_maks_cpu_histori) > 3000:
                self.suhu_maks_cpu_histori = self.suhu_maks_cpu_histori[-3000:]
                self.beban_histori         = self.beban_histori[-3000:]
            self.frame_baru_tersedia = True

    def ambil_frame_untuk_gui(self):
        with self.lock:
            if not self.frame_baru_tersedia:
                return None
            self.frame_baru_tersedia = False
            markers = list(self.marker_pending)
            self.marker_pending = []
            return (
                self.waktu_sekarang,
                self.suhu_terbaru.copy(),
                list(self.suhu_maks_cpu_histori),
                list(self.beban_histori),
                markers,
            )

    def tambah_marker(self, label, kategori="manual"):
        with self.lock:
            self.marker_antrian.append((label, kategori))

    def flush_marker_antrian(self, t):
        with self.lock:
            for label, kat in self.marker_antrian:
                self.marker_pending.append((t, label, kat))
            self.marker_antrian = []


def thread_fisika(state: StateSimulasiLive):
    nx, ny = JUMLAH_TITIK_X, JUMLAH_TITIK_Y
    dx, dy = DELTA_X, DELTA_Y

    suhu         = np.full((ny, nx), suhu_ambient(0.0))
    peta_material = state.peta_material
    t = 0.0

    nama_cpu_lama = nama_tim_lama = nama_heatsink_lama = nama_kualitas_lama = None
    sifat_material_aktif = None
    alpha_matriks = rho_cp_matriks = q_matriks_penuh = None
    dt = DELTA_WAKTU

    waktu_visual_berikutnya = 0.0

    while True:
        p = state.baca_param()

        if not p['berjalan']:
            time.sleep(0.05)
            continue

        with state.lock:
            nama_cpu      = state.nama_cpu
            nama_tim      = state.nama_tim
            nama_heatsink = state.nama_heatsink
            nama_kualitas = state.nama_kualitas_tim
            reset_diminta = state.reset_diminta
            state.reset_diminta = False

        if reset_diminta:
            suhu = np.full((ny, nx), suhu_ambient(0.0))
            t    = 0.0
            waktu_visual_berikutnya = 0.0
            with state.lock:
                state.suhu_maks_cpu_histori = []
                state.beban_histori         = []
                state.marker_pending        = []
                state.marker_antrian        = []

        material_berubah = (
            nama_cpu      != nama_cpu_lama or
            nama_tim      != nama_tim_lama or
            nama_heatsink != nama_heatsink_lama or
            nama_kualitas != nama_kualitas_lama
        )

        if material_berubah or sifat_material_aktif is None:
            sifat_material_aktif = buat_sifat_material(nama_cpu, nama_tim, nama_heatsink, nama_kualitas)
            alpha_matriks   = hitung_difusivitas(peta_material, sifat_material_aktif)
            rho_cp_matriks  = hitung_rho_cp(peta_material, sifat_material_aktif)
            q_matriks_penuh = hitung_pembangkit_panas(peta_material, sifat_material_aktif)
            dt = cek_dt_aman(sifat_material_aktif)

            if nama_cpu_lama is not None:
                perubahan = []
                if nama_cpu      != nama_cpu_lama:      perubahan.append(("cpu",      f"CPU: {nama_cpu}"))
                if nama_tim      != nama_tim_lama:      perubahan.append(("pasta",    f"Pasta: {nama_tim}"))
                if nama_heatsink != nama_heatsink_lama: perubahan.append(("heatsink", f"HS: {nama_heatsink}"))
                if nama_kualitas != nama_kualitas_lama: perubahan.append(("kualitas", f"TIM: {nama_kualitas}"))
                for kat, lbl in perubahan:
                    state.tambah_marker(lbl, kat)

            nama_cpu_lama      = nama_cpu
            nama_tim_lama      = nama_tim
            nama_heatsink_lama = nama_heatsink
            nama_kualitas_lama = nama_kualitas

        mode_beban = p['mode_beban']
        if mode_beban == "Konstan":
            target = p['beban_konstan']
        elif mode_beban == "Random":
            with state.lock:
                if t >= state.waktu_ganti_random_berikutnya:
                    mn, mx = state.rentang_random
                    state.target_random = random.uniform(mn, mx)
                    state.waktu_ganti_random_berikutnya = t + state.interval_random
                target = state.target_random
        else:
            target = target_beban_manual(t)

        with state.lock:
            state.beban_aktual += (target - state.beban_aktual) * (dt / TAU_RAMP_BEBAN)
            state.beban_aktual  = min(1.0, max(0.0, state.beban_aktual))
            beban_aktual = state.beban_aktual

        q_matriks = q_matriks_penuh * beban_aktual
        t_amb     = suhu_ambient(t)

        suhu = pembaruan_suhu(suhu, alpha_matriks, rho_cp_matriks, q_matriks,
                              dt, dx, dy, t_ambient=t_amb, h=H_KONVEKSI)
        t += dt

        if t >= waktu_visual_berikutnya:
            state.flush_marker_antrian(t)
            suhu_maks_cpu = float(np.max(suhu[peta_material == ID_CPU]))
            state.tulis_frame(t, suhu, suhu_maks_cpu, beban_aktual * 100.0)
            waktu_visual_berikutnya = t + max(p['langkah_visual_detik'], dt)


class AplikasiSimulasiLive:
    def __init__(self, master):
        self.master = master
        self.master.title("Simulasi Difusi Panas 2D CPU & Heatsink")
        self.master.geometry("1280x760")

        self.state = StateSimulasiLive()

        self._nama_cpu_prev      = self.state.nama_cpu
        self._nama_tim_prev      = self.state.nama_tim
        self._nama_heatsink_prev = self.state.nama_heatsink
        self._nama_kualitas_prev = self.state.nama_kualitas_tim

        self._marker_list = []  

        panel_kontrol = tk.Frame(master, padx=12, pady=12)
        panel_kontrol.pack(side="left", fill="y")

        tk.Label(panel_kontrol, text="Kontrol Live",
                 font=("Helvetica", 14, "bold")).pack(pady=(0, 4))
        tk.Label(panel_kontrol,
                 text="Ubah apa saja di bawah ini,\nlangsung berpengaruh ke simulasi.",
                 font=("Helvetica", 9, "italic"), justify="left").pack(pady=(0, 8))

        frame_mat = tk.LabelFrame(panel_kontrol, text="Material", padx=8, pady=8)
        frame_mat.pack(fill="x", pady=4)

        self.cb_cpu      = self._combo(frame_mat, "Bahan CPU:",    PILIHAN_CPU,      0, self._on_ubah_material)
        self.cb_tim      = self._combo(frame_mat, "Pasta Termal:", PILIHAN_PASTA,    1, self._on_ubah_material)
        self.cb_heatsink = self._combo(frame_mat, "Heatsink:",     PILIHAN_PENDINGIN,0, self._on_ubah_material)
        self.cb_kualitas = self._combo(frame_mat, "Kualitas TIM:", EFISIENSI_TIM,    1, self._on_ubah_material)

        frame_beban = tk.LabelFrame(panel_kontrol, text="Beban CPU", padx=8, pady=8)
        frame_beban.pack(fill="x", pady=4)

        tk.Label(frame_beban, text="Mode:").pack(anchor="w")
        self.cb_mode_beban = ttk.Combobox(frame_beban, values=MODE_BEBAN_LIST,
                                           state="readonly", width=22)
        self.cb_mode_beban.current(1)
        self.cb_mode_beban.bind("<<ComboboxSelected>>", self._on_ubah_beban)
        self.cb_mode_beban.pack(pady=3, fill="x")

        tk.Label(frame_beban, text="Beban Konstan (%):").pack(anchor="w", pady=(6, 0))
        self.slider_konstan = tk.Scale(frame_beban, from_=0, to=100,
                                        orient="horizontal", command=self._on_ubah_beban)
        self.slider_konstan.set(60)
        self.slider_konstan.pack(fill="x")

        tk.Label(frame_beban, text="Rentang Random (%):").pack(anchor="w", pady=(6, 0))
        sub = tk.Frame(frame_beban); sub.pack(fill="x")
        self.slider_random_min = tk.Scale(sub, from_=0, to=100, orient="horizontal",
                                           label="Min", command=self._on_ubah_beban, length=110)
        self.slider_random_min.set(10); self.slider_random_min.pack(side="left")
        self.slider_random_max = tk.Scale(sub, from_=0, to=100, orient="horizontal",
                                           label="Maks", command=self._on_ubah_beban, length=110)
        self.slider_random_max.set(100); self.slider_random_max.pack(side="left")

        tk.Label(frame_beban, text="Interval Ganti Random (detik):").pack(anchor="w", pady=(6,0))
        self.entry_interval = tk.Entry(frame_beban, width=8)
        self.entry_interval.insert(0, "3")
        self.entry_interval.bind("<Return>",   self._on_ubah_beban)
        self.entry_interval.bind("<FocusOut>", self._on_ubah_beban)
        self.entry_interval.pack(anchor="w", pady=3)

        frame_tampil = tk.LabelFrame(panel_kontrol, text="Tampilan", padx=8, pady=8)
        frame_tampil.pack(fill="x", pady=4)

        tk.Label(frame_tampil, text="Langkah Visual / Gap (detik):").pack(anchor="w")
        self.entry_langkah_visual = tk.Entry(frame_tampil, width=8)
        self.entry_langkah_visual.insert(0, str(LANGKAH_VISUAL_DEFAULT))
        self.entry_langkah_visual.bind("<Return>",   self._on_ubah_tampilan)
        self.entry_langkah_visual.bind("<FocusOut>", self._on_ubah_tampilan)
        self.entry_langkah_visual.pack(anchor="w", pady=3)

        frame_btn = tk.Frame(panel_kontrol)
        frame_btn.pack(fill="x", pady=8)

        self.btn_pause = tk.Button(frame_btn, text="⏸ Pause", width=13,
                                    bg="#3498db", fg="white", font=("Helvetica", 9, "bold"),
                                    command=self._toggle_pause)
        self.btn_pause.grid(row=0, column=0, padx=3, pady=3)

        tk.Button(frame_btn, text="🔄 Reset Simulasi", width=13,
                  bg="#e74c3c", fg="white", font=("Helvetica", 9, "bold"),
                  command=self._reset).grid(row=0, column=1, padx=3, pady=3)

        tk.Button(frame_btn, text="📊 Reset Grafik", width=13,
                  bg="#e67e22", fg="white", font=("Helvetica", 9, "bold"),
                  command=self._reset_grafik).grid(row=1, column=0, padx=3, pady=3)

        tk.Button(frame_btn, text="📌 Tandai Sekarang", width=13,
                  bg="#27ae60", fg="white", font=("Helvetica", 9, "bold"),
                  command=self._tandai_manual).grid(row=1, column=1, padx=3, pady=3)

        tk.Button(frame_btn, text="🧪 Uji Konvergensi", width=13,
                  bg="#8e44ad", fg="white", font=("Helvetica", 9, "bold"),
                  command=self._jalankan_uji_konvergensi).grid(row=2, column=0, columnspan=2, padx=3, pady=3, sticky="ew")

        frame_legend = tk.LabelFrame(panel_kontrol, text="Legenda Marker", padx=6, pady=4)
        frame_legend.pack(fill="x", pady=4)
        info = [
            ("CPU",      WARNA_MARKER["cpu"]),
            ("Pasta",    WARNA_MARKER["pasta"]),
            ("Heatsink", WARNA_MARKER["heatsink"]),
            ("Kualitas TIM", WARNA_MARKER["kualitas"]),
            ("Manual",   WARNA_MARKER["manual"]),
        ]
        for nama, warna in info:
            baris = tk.Frame(frame_legend); baris.pack(anchor="w")
            tk.Label(baris, text="━━", fg=warna, font=("Courier", 10, "bold")).pack(side="left")
            tk.Label(baris, text=f" {nama}", font=("Helvetica", 9)).pack(side="left")

       
        self.label_status = tk.Label(
            panel_kontrol,
            text="t = 0.0 s | Beban = 0% | Suhu Maks CPU = 25.0°C",
            font=("Helvetica", 10, "bold"), fg="darkgreen",
            justify="left", wraplength=250
        )
        self.label_status.pack(pady=6)

        panel_grafik = tk.Frame(master)
        panel_grafik.pack(side="right", fill="both", expand=True)

        self.fig = Figure(figsize=(9, 6.5))
        self.ax_heatmap = self.fig.add_subplot(1, 2, 1)
        self.ax_grafik  = self.fig.add_subplot(1, 2, 2)
        self.ax_grafik2 = self.ax_grafik.twinx()

        cmap = plt.cm.jet
        cmap.set_bad(color='white')
        suhu_awal = np.full((JUMLAH_TITIK_Y, JUMLAH_TITIK_X), SUHU_LINGKUNGAN, dtype=float)
        suhu_awal[self.state.peta_material == ID_UDARA] = np.nan
        self.im_heatmap = self.ax_heatmap.imshow(
            suhu_awal, cmap=cmap, origin='lower',
            vmin=SUHU_LINGKUNGAN, vmax=SUHU_LINGKUNGAN + 40
        )
        self.fig.colorbar(self.im_heatmap, ax=self.ax_heatmap, label="Suhu (°C)")
        self.judul_heatmap = self.ax_heatmap.set_title("Distribusi Suhu (t = 0.0 s)")

        self.garis_suhu,  = self.ax_grafik.plot([], [], color='tab:red',  lw=1.5, label='Suhu Maks CPU')
        self.garis_beban, = self.ax_grafik2.plot([], [], color='tab:blue', lw=1.2, alpha=0.6, label='Beban (%)')
        self.ax_grafik.set_xlabel("Waktu (detik)")
        self.ax_grafik.set_ylabel("Suhu Maks. CPU (°C)", color='tab:red')
        self.ax_grafik2.set_ylabel("Beban CPU (%)", color='tab:blue')
        self.ax_grafik2.set_ylim(0, 105)
        self.ax_grafik.set_title("Live: Suhu & Beban CPU")
        self.ax_grafik.grid(True, alpha=0.3)

        self.canvas = FigureCanvasTkAgg(self.fig, master=panel_grafik)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.canvas.draw()

        self.thread = threading.Thread(target=thread_fisika, args=(self.state,), daemon=True)
        self.thread.start()

        self._terapkan_semua_kontrol()
        self.master.after(150, self._loop_refresh_gui)


    def _combo(self, frame, label, pilihan_dict, idx_default, callback):
        tk.Label(frame, text=label).pack(anchor="w")
        cb = ttk.Combobox(frame, values=list(pilihan_dict.keys()),
                           state="readonly", width=22)
        cb.current(idx_default)
        cb.bind("<<ComboboxSelected>>", callback)
        cb.pack(pady=2, fill="x")
        return cb

    def _gambar_marker(self, t, label, kategori):
        warna = WARNA_MARKER.get(kategori, "#888888")
        line = self.ax_grafik.axvline(x=t, color=warna, linewidth=1.2,
                                       linestyle="--", alpha=0.85, zorder=5)
        idx   = len(self._marker_list)
        y_pos = self.ax_grafik.get_ylim()[1] * 0.97
        txt   = self.ax_grafik.text(
            t, y_pos, f" {label}", color=warna,
            fontsize=6.5, rotation=90, va="top", ha="right",
            clip_on=True, zorder=6
        )
        self._marker_list.append((t, label, kategori, line, txt))

    def _on_ubah_material(self, *_):
        with self.state.lock:
            self.state.nama_cpu          = self.cb_cpu.get()
            self.state.nama_tim          = self.cb_tim.get()
            self.state.nama_heatsink     = self.cb_heatsink.get()
            self.state.nama_kualitas_tim = self.cb_kualitas.get()

    def _on_ubah_beban(self, *_):
        try:    interval = float(self.entry_interval.get())
        except: interval = 3.0
        with self.state.lock:
            self.state.mode_beban    = self.cb_mode_beban.get()
            self.state.beban_konstan = self.slider_konstan.get() / 100.0
            mn = self.slider_random_min.get() / 100.0
            mx = self.slider_random_max.get() / 100.0
            self.state.rentang_random  = (min(mn, mx), max(mn, mx))
            self.state.interval_random = max(0.1, interval)

    def _on_ubah_tampilan(self, *_):
        try:    nilai = float(self.entry_langkah_visual.get())
        except: nilai = LANGKAH_VISUAL_DEFAULT
        with self.state.lock:
            self.state.langkah_visual_detik = max(0.05, nilai)

    def _terapkan_semua_kontrol(self):
        self._on_ubah_material()
        self._on_ubah_beban()
        self._on_ubah_tampilan()

    def _toggle_pause(self):
        with self.state.lock:
            self.state.berjalan = not self.state.berjalan
            sedang_jalan = self.state.berjalan
        self.btn_pause.config(
            text="⏸ Pause" if sedang_jalan else "▶ Lanjutkan",
            bg="#3498db" if sedang_jalan else "#7f8c8d"
        )

    def _reset(self):
        with self.state.lock:
            self.state.reset_diminta = True
        self._bersihkan_marker_grafik()
        self.garis_suhu.set_data([], [])
        self.garis_beban.set_data([], [])
        self.canvas.draw_idle()

    def _reset_grafik(self):
        with self.state.lock:
            self.state.suhu_maks_cpu_histori = []
            self.state.beban_histori         = []
            self.state.marker_pending        = []
            self.state.marker_antrian        = []
        self._bersihkan_marker_grafik()
        self.garis_suhu.set_data([], [])
        self.garis_beban.set_data([], [])
        self.canvas.draw_idle()

    def _bersihkan_marker_grafik(self):
        for _, _, _, line, txt in self._marker_list:
            try: line.remove()
            except: pass
            try: txt.remove()
            except: pass
        self._marker_list.clear()

    def _tandai_manual(self):
        self.state.tambah_marker("Tandai", "manual")

    def _jalankan_uji_konvergensi(self):
        with self.state.lock:
            nama_cpu      = self.state.nama_cpu
            nama_tim      = self.state.nama_tim
            nama_heatsink = self.state.nama_heatsink
            nama_kualitas = self.state.nama_kualitas_tim

        jendela = tk.Toplevel(self.master)
        jendela.title("Uji Konvergensi Grid")
        jendela.geometry("760x560")

        label_info = tk.Label(jendela, text="Menjalankan uji konvergensi, mohon tunggu...",
                               font=("Helvetica", 10, "bold"))
        label_info.pack(pady=8)

        fig_konv = Figure(figsize=(7.2, 4.6))
        ax1 = fig_konv.add_subplot(1, 2, 1)
        ax2 = fig_konv.add_subplot(1, 2, 2)
        canvas_konv = FigureCanvasTkAgg(fig_konv, master=jendela)
        canvas_konv.get_tk_widget().pack(fill="both", expand=True)

        daftar_nx = [13, 25, 50, 100, 150]
        t_akhir   = 0.6

        antrian_progress = []
        lock_progress = threading.Lock()

        def callback_progress(nx, suhu):
            with lock_progress:
                antrian_progress.append((nx, suhu))

        def kerja_thread():
            hasil = uji_konvergensi_grid(daftar_nx, t_akhir, nama_cpu, nama_tim,
                                          nama_heatsink, nama_kualitas,
                                          callback_progress=callback_progress)
            galat = hitung_galat_relatif(hasil)
            with lock_progress:
                antrian_progress.append(("selesai", (hasil, galat)))

        thread_konv = threading.Thread(target=kerja_thread, daemon=True)
        thread_konv.start()

        def perbarui():
            with lock_progress:
                item_baru = list(antrian_progress)
                antrian_progress.clear()

            for item in item_baru:
                if item[0] == "selesai":
                    hasil, galat = item[1]
                    label_info.config(
                        text="Uji konvergensi selesai. Semakin halus grid, "
                             "suhu maksimum CPU harus mendekati nilai stabil "
                             "(garis galat mendekati 0%)."
                    )

                    nx_list   = [h[0] for h in hasil]
                    suhu_list = [h[2] for h in hasil]
                    galat_list = [g[3] for g in galat]

                    ax1.clear()
                    ax1.plot(nx_list, suhu_list, marker='o', color='tab:red')
                    ax1.set_xlabel("Jumlah Titik Grid (Nx = Ny)")
                    ax1.set_ylabel("Suhu Maks. CPU (°C)")
                    ax1.set_title("Konvergensi Suhu vs Resolusi Grid")
                    ax1.grid(True, alpha=0.3)

                    ax2.clear()
                    ax2.plot(nx_list, galat_list, marker='s', color='tab:blue')
                    ax2.set_xlabel("Jumlah Titik Grid (Nx = Ny)")
                    ax2.set_ylabel("Galat Relatif (%)")
                    ax2.set_title("Galat Relatif terhadap Grid Tertinggi")
                    ax2.grid(True, alpha=0.3)

                    fig_konv.tight_layout()
                    canvas_konv.draw_idle()
                else:
                    nx, suhu = item
                    label_info.config(
                        text=f"Menghitung grid Nx=Ny={nx} ... Suhu Maks CPU sementara = {suhu:.2f}°C"
                    )

            if thread_konv.is_alive() or item_baru:
                jendela.after(200, perbarui)
            else:
                jendela.after(500, perbarui)

        jendela.after(200, perbarui)

    def _loop_refresh_gui(self):
        frame = self.state.ambil_frame_untuk_gui()
        if frame is not None:
            t, suhu, histori_suhu_maks, histori_beban, markers = frame
            peta_material = self.state.peta_material

            suhu_tampil = suhu.astype(float).copy()
            suhu_tampil[peta_material == ID_UDARA] = np.nan
            self.im_heatmap.set_data(suhu_tampil)
            batas_atas = max(SUHU_LINGKUNGAN + 5, float(np.nanmax(suhu_tampil)) + 2)
            self.im_heatmap.set_clim(SUHU_LINGKUNGAN, batas_atas)
            self.judul_heatmap.set_text(f"Distribusi Suhu (t = {t:.1f} s)")

            if histori_suhu_maks:
                wkt = [w for w, _ in histori_suhu_maks]
                sm  = [s for _, s in histori_suhu_maks]
                bb  = [b for _, b in histori_beban]
                self.garis_suhu.set_data(wkt, sm)
                self.garis_beban.set_data(wkt, bb)
                self.ax_grafik.set_xlim(max(0, wkt[0]), max(wkt[-1], wkt[0] + 1))
                self.ax_grafik.set_ylim(SUHU_LINGKUNGAN - 2, max(sm) + 5)

                suhu_maks_terbaru = sm[-1]
                beban_terbaru     = bb[-1]
                self.label_status.config(
                    text=f"t = {t:.1f} s | Beban = {beban_terbaru:.0f}% | "
                         f"Suhu Maks CPU = {suhu_maks_terbaru:.1f}°C"
                )

            for mt, mlabel, mkat in markers:
                self._gambar_marker(mt, mlabel, mkat)

            self.canvas.draw_idle()

        self.master.after(150, self._loop_refresh_gui)


if __name__ == "__main__":
    root = tk.Tk()
    app = AplikasiSimulasiLive(root)
    root.mainloop()
