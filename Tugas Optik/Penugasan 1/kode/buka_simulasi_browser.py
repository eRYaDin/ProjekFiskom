"""Buka simulasi B dan C offline di browser (Python 3.10+, tanpa pip).

Perhitungan interaktif berjalan di model_optik.js, sehingga slider tetap
berfungsi ketika HTML dibuka langsung. Kode numerik Python untuk grafik
statis ada di simulasi_optik.py. Simpan struktur folder paket tetap utuh.
"""
from pathlib import Path
import webbrowser


def main():
    target = Path(__file__).resolve().parents[1] / 'Simulasi_Interaktif.html'
    needed = [target, target.parent/'kode/model_optik.js', target.parent/'kode/tampilan_optik.js',
              target.parent/'kode/keterangan_optik.js',
              target.parent/'kode/vendor/katex/katex.min.js',
              target.parent/'kode/vendor/katex/katex.min.css']
    missing = [str(p) for p in needed if not p.is_file()]
    if missing:
        raise SystemExit('Berkas simulasi belum lengkap:\n' + '\n'.join(missing))
    print('Membuka simulasi B dan C: ' + str(target))
    if not webbrowser.open(target.as_uri()):
        print('Buka Simulasi_Interaktif.html dengan klik dua kali.')


if __name__ == '__main__':
    main()
