# ProjekFiskom

Kode awal kelompok tersedia pada `KodeKelompok2.py`.

## Penugasan 1 Optik Modern

Hasil tugas disimpan dalam [Tugas Optik/Penugasan 1](Tugas%20Optik/Penugasan%201).

- [Laporan analisis dan simulasi terbaru](Tugas%20Optik/Penugasan%201/Analisis%20dan%20Simulasi/Laporan_Analisis_dan_Simulasi.pdf): enam halaman, termasuk anggota kelompok, rumus, grafik, analisis, dan penjelasan kode.
- [Paket laporan dan kode](Tugas%20Optik/Penugasan%201/Analisis%20dan%20Simulasi/Paket_Laporan_dan_Kode.zip).
- [Petunjuk simulasi](Tugas%20Optik/Penugasan%201/BACA_DULU.md).
- [Presentasi](Tugas%20Optik/Penugasan%201/Presentasi_Penugasan_1.pptx).

### Menjalankan simulasi Python

```sh
cd "Tugas Optik/Penugasan 1"
python -m pip install -r kode/requirements_interaktif.txt
python kode/simulasi_interaktif.py
```

Pemeriksaan perhitungan tanpa membuka jendela:

```sh
python kode/simulasi_interaktif.py --periksa
```

Untuk versi web, unduh atau clone repo, lalu buka `Simulasi_Interaktif.html` dari folder tugas. Simpan folder `kode` bersamanya agar skrip dan rumus dapat dimuat.

Model menggunakan pandu planar TE simetris tanpa rugi. Parameter merupakan contoh pembelajaran; hasil belum dibandingkan dengan pengukuran eksperimen.
