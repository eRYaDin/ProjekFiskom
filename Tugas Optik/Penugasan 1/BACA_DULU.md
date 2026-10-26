# Penugasan 1 Optik Modern

## Aplikasi Python dengan jendela sendiri

Klik dua kali `Jalankan_Simulasi_Python.pyw`, atau jalankan dari folder Penugasan 1:

```powershell
python kode/simulasi_interaktif.py
```

Aplikasi memakai Tkinter, NumPy, dan Matplotlib. Perhitungan serta tampilan berjalan langsung di Python. Jika dependensi belum tersedia:

```powershell
python -m pip install -r kode/requirements_interaktif.txt
```

Python standar untuk Windows biasanya menyertakan Tkinter. Gunakan interpreter Python yang sama untuk memasang paket dan menjalankan aplikasi.

- Bagian B memiliki slider ketebalan dan panjang gelombang, pilihan mode terikat, animasi fase medan, serta tab grafik dispersi ketebalan dan panjang gelombang.
- Bagian C memiliki slider celah dan posisi propagasi, animasi irisan, tombol 50:50/transfer penuh, dan perbandingan celah 2, 4, dan 6 µm.
- Rumus ditampilkan dengan MathText, yaitu subset LaTeX yang disertakan Matplotlib. Arti warna dan simbol tersedia pada tab Keterangan & rumus.
- Simpan grafik PNG mengekspor tampilan grafik aktif. Simpan data CSV mengekspor data beserta parameter. Kedua tombol membuka dialog pemilihan berkas.
- Mesin hitung Python terdapat di `kode/optik_model.py`. Versi pembuka browser sebelumnya disimpan sebagai `kode/buka_simulasi_browser.py`.

Pemeriksaan tanpa membuka jendela:

```powershell
python kode/simulasi_interaktif.py --periksa
```

Pemeriksaan sudah lulus untuk angka acuan, cutoff, normalisasi supermode, pembagian 50:50, transfer penuh, dan pertukaran profil. Lima gambar dan CSV acuan disimpan pada `grafik/python` dan `data/python`. Jendela awal aplikasi telah diperiksa; pemeriksaan interaksi desktop dihentikan atas permintaan pengguna. Perbaikan akhir tata letak tidak diperiksa ulang melalui kontrol desktop.

## Simulasi interaktif B dan C di browser

Klik dua kali **Simulasi_Interaktif.html** untuk membuka simulasi di browser. Tidak memerlukan internet, instalasi paket, atau server. Simpan folder `kode` di lokasi yang sama dengan HTML.

Keterangan pada setiap grafik mencakup arti warna, arah sumbu, geometri, simbol, satuan, serta cara membaca kurva. Rumus ditata dengan LaTeX menggunakan KaTeX 0.19.1 yang disertakan pada `kode/vendor/katex`, sehingga rumus tetap tampil offline. Penjelasan nilai saat ini mengikuti slider. Biru/jingga pada peta B adalah kode tanda medan listrik; peta C menggunakan warna untuk intensitas nonnegatif. Rincian profil TE0 dan intensitas rata-rata dapat dibuka pada bagian rumus di bawah peta B.

Alternatif lewat Python, dari folder Penugasan 1:

```powershell
python kode/buka_simulasi_browser.py
```

File Python tersebut adalah pembuka antarmuka browser. Mesin hitung interaktif ada di `kode/model_optik.js`; tampilan dan animasinya ada di `kode/tampilan_optik.js`. Kode numerik Python untuk keluaran statis tetap tersedia sebagai `kode/simulasi_optik.py`.

- **Bagian B:** geser ketebalan dan panjang gelombang; pilih TE0, TE1, dan seterusnya bila terikat. Peta medan listrik sesaat memperlihatkan osilasi fase sepanjang z. Grafik menampilkan profil medan dan intensitas, n efektif terhadap ketebalan, serta n efektif terhadap panjang gelombang. Indeks bahan tetap, sehingga perubahan terhadap panjang gelombang merupakan dispersi pandu.
- **Bagian C:** geser celah 2–6 µm; tekan *Ikuti propagasi*, *Ke 50:50*, atau *Ke transfer penuh*. Peta intensitas dua dimensi, irisan medan, persentase daya, dan grafik daya ikut berubah. Grafik pembanding menggunakan celah 2, 4, dan 6 µm dengan sumbu propagasi yang sama.
- **Ekspor:** tombol PNG menyimpan grafik yang sedang ditampilkan; tombol data menyimpan CSV numerik beserta parameter. Nilai dapat dibaca dengan menggerakkan penunjuk pada grafik.

Peta Bagian C dihitung dari profil supermode genap dan ganjil struktur lima lapisan, bukan ilustrasi lintasan cahaya. Profil dinormalisasi berdasarkan daya masing-masing supermode, dengan ekor eksponensial diintegralkan sampai tak berhingga. Kombinasi dua supermode berbobot daya sama menghasilkan input yang terlokalisasi terutama di pandu a. Pada celah kecil, input itu tidak terlokalisasi sempurna. Grafik sin²/cos² menunjukkan daya pada basis modal ideal; nilai 100% tidak berarti medan di seluruh inti lain pasti nol.

Peta C adalah pola spasial keadaan tunak; animasi memindahkan irisan z, bukan menunjukkan kecepatan perjalanan pulsa. Animasi fase B diperlambat agar dapat diamati. Skala geometris x dan z berbeda dan selalu diberi satuan.

Validasi baru: nilai n efektif dan panjang transfer cocok dengan keluaran Python; kontinuitas medan dan turunannya, ortogonalitas, normalisasi supermode, konservasi fluks longitudinal, titik cutoff, dan pertukaran profil a/b telah diuji. Uji model dapat diulang bila Node.js tersedia:

```powershell
node kode/uji_model_optik.cjs
```

Simulasi serta kontrol utama diperiksa di browser. PDF dan PPT yang tercantum di bawah merupakan versi laporan awal; perubahan slider dan grafik interaktif tidak otomatis memperbarui kedua dokumen itu.

## Berkas utama

- `A_Ringkasan_Bab_4.pdf`: ringkasan 7 halaman untuk dipahami dan disalin tangan sesuai instruksi dosen. Banyaknya halaman tulisan tangan akan bergantung pada ukuran tulisan dan kertas. Pertahankan seluruh pokok bahasan dan sesuaikan menjadi 5–8 halaman tulisan tangan.
- `BC_Laporan_Analisis_Simulasi.pdf`: laporan 6 halaman yang menggabungkan pemodelan slab (Bagian B) dan directional coupler (Bagian C). Memuat 5 gambar, tabel hasil, penjelasan algoritme, serta batas model.
- `Presentasi_Penugasan_1.pptx`: 16 slide dengan catatan pembicara. Alokasi pemaparan pada catatan berjumlah 16 menit, ditambah 4 menit tanya jawab. Grafik, tabel, diagram, dan teks dapat diedit. Sesuaikan identitas kelompok bila diperlukan.
- `kode/simulasi_optik.py`: kode lengkap yang sudah dijalankan. Hasilnya bukan data eksperimen.
- `grafik/`: 7 gambar dalam format PNG dan PDF vektor, termasuk geometri, medan, dispersi ketebalan, jumlah modus, serta perpindahan daya dan pengaruh celah.
- `data/`: data CSV serta hasil numerik JSON. Berkas `grafik_ppt.json` menyimpan data numerik untuk grafik presentasi.

## Menjalankan ulang

Gunakan Python 3.10 atau lebih baru. Buka terminal pada folder Penugasan 1 lalu jalankan:

```powershell
python -m pip install -r kode/requirements.txt
python kode/simulasi_optik.py
```

Kode akan menghitung ulang data dan PDF grafik, serta mengganti keluaran dengan nama yang sama pada folder `data` dan `grafik`. PDF ringkasan, laporan, dan PowerPoint yang sudah disusun tidak diperbarui otomatis ketika parameter simulasi diubah. PNG yang disertakan adalah hasil render PDF grafik pada parameter paket ini; kode utama menghasilkan grafik vektor PDF agar dapat dijalankan tanpa Poppler atau Matplotlib.

## Model dan cara membaca hasil

Teras n=1,51, selubung n=1,50, ketebalan penuh d=2 µm, dan panjang gelombang vakum 1,55 µm. Nilai ini merupakan pilihan model ideal untuk pembelajaran, bukan indeks bahan tertentu yang diukur. Seluruh panjang internal memakai µm. Analisis numerik dibatasi pada polarisasi TE.

Slab diselesaikan dari persamaan fase dengan biseksi. Kopler diselesaikan melalui kondisi genap dan ganjil dari struktur lima lapisan. Koefisien kopling dihitung dari setengah pemisahan konstanta propagasi dua supermode. Kurva daya kemudian memakai model dua keadaan modal tanpa rugi, dengan input pada pandu a.

Hasil acuan: n efektif 1,503065, beta 6,092927 per µm, satu modus TE, dan faktor pengurungan 0,500195. Pada celah 4 µm, kappa 0,002789587 per µm, panjang 50:50 sebesar 281,55 µm, dan transfer penuh pertama sebesar 563,09 µm.

Kurva daya adalah daya modal ternormalisasi, termasuk ekor evanescent. Kurva tersebut bukan integral daya yang dibatasi pada inti teras saja. Model tidak memasukkan rugi bahan, sambungan, fabrikasi, dispersi material, maupun respons aktuator sakelar.

## Pemeriksaan yang dijalankan

- Solusi memenuhi indeks selubung < indeks efektif < indeks teras.
- Residual fase slab sekitar 1,02e-14.
- Pengurungan akar supermode dengan 801, 1601, dan 4001 sampel menghasilkan panjang kopling yang konsisten.
- Deviasi konservasi daya sekitar 2,22e-16.
- Integral overlap TE0 dan TE1 yang berbeda paritas pada d=8 µm bernilai nol pada presisi numerik.

Angka presisi kecil adalah pemeriksaan algoritme, bukan ketelitian eksperimen atau estimasi galat material.

## Sumber

Sumber utama adalah dua PDF kuliah di folder Tugas Optik. Rujukan tambahan untuk interpretasi supermode adalah dokumentasi COMSOL 6.3 Directional Coupler, https://doc.comsol.com/6.3/doc/com.comsol.help.models.woptics.directional_coupler/directional_coupler.html. Parameter dan hasil numerik berasal dari kode pada paket ini. Daftar pustaka lengkap tercantum dalam kedua PDF.
