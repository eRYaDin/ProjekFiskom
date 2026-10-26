/* Keterangan belajar dan rumus KaTeX. Tidak mengubah mesin hitung. */
(() => {
 'use strict';
 const $=id=>document.getElementById(id);
 const math=(tex,block=false)=>`<${block?'div':'span'} class="rumus${block?' rumus-blok':''}" data-tex="${tex.replaceAll('"','&quot;')}"></${block?'div':'span'}>`;
 const panel=id=>document.getElementById(id).closest('article');
 const explanation=(id,html)=>panel(id).insertAdjacentHTML('beforeend',`<div class="penjelasan">${html}</div>`);
 const fmt=(n,p=2)=>n.toLocaleString('id-ID',{minimumFractionDigits:p,maximumFractionDigits:p});

 document.querySelector('#part-b > .muted').insertAdjacentHTML('afterend',String.raw`
 <div class="panduan" aria-label="Cara membaca geometri pandu tunggal">
 <p><b>Arah mendatar ${math(String.raw`z`)}:</b> arah rambat cahaya ke kanan. <b>Arah tegak ${math(String.raw`x`)}:</b> posisi melintang terhadap pandu. Keduanya dalam µm; skala gambarnya berbeda.</p>
 <p><b>Dua garis mendatar:</b> batas teras pada ${math(String.raw`x=-d/2`)} dan ${math(String.raw`x=+d/2`)}. Bagian di antaranya adalah teras; bagian di luar adalah selubung.</p>
 <p><b>TE${math(String.raw`_m`)}:</b> mode dengan medan listrik sejajar arah ${math(String.raw`y`)}, yaitu tegak lurus bidang gambar. Angka ${math(String.raw`m=0,1,2,\ldots`)} menyatakan jumlah simpul medan di dalam teras.</p></div>`);
 const help={thickness:'Lebar teras dari batas bawah ke batas atas. Perbesar d untuk melihat munculnya mode tambahan.',wavelength:'Panjang gelombang di ruang hampa. Indeks bahan tetap selama λ₀ diubah.',mode:'Pilih bentuk mode yang masih terikat. TE0 adalah mode dasar tanpa simpul di dalam teras.'};
 for(const [id,text] of Object.entries(help)){
   const el=$(id),p=document.createElement('p');p.id=id+'-help';p.className='control-help';p.textContent=text;
   el.parentElement.append(p);el.setAttribute('aria-describedby',p.id);
 }
 const bmap=panel('map-b');
 bmap.querySelector('.topline').insertAdjacentHTML('afterend','<p class="map-intro">Peta warna menunjukkan nilai medan listrik pada satu fase waktu. Saat fase dijalankan, pola bergeser ke kanan mengikuti rambatan gelombang.</p>');
 bmap.querySelector('.scale').innerHTML='<span>−1</span><i aria-hidden="true"></i><span>+1 · medan ternormalisasi</span>';
 const bLegend=document.createElement('div');bLegend.className='arti-warna';bLegend.innerHTML='<span><i class="swatch negatif"></i><b>Biru:</b> medan negatif</span><span><i class="swatch nol"></i><b>Gelap:</b> medan mendekati nol</span><span><i class="swatch positif"></i><b>Jingga:</b> medan positif</span>';
 bmap.querySelector('.range-row').before(bLegend);
 explanation('map-b',String.raw`
 <p><b>Warna adalah kode nilai medan.</b> Tanda positif dan negatif menyatakan arah osilasi medan listrik sepanjang sumbu ${math(String.raw`y`)}. Keduanya tetap merupakan gelombang yang merambat ke kanan. Panjang gelombang yang dipakai berada di inframerah, sehingga biru dan jingga di peta adalah warna bantu.</p>
 <div class="rumus-pasang"><div>${math(String.raw`E_y(x,z,t)=E_0\,\psi_m(x)\cos(\beta_m z-\varphi_t)`,true)}</div><div>${math(String.raw`\beta_m=\frac{2\pi n_{\mathrm{eff},m}}{\lambda_0},\qquad \lambda_z=\frac{\lambda_0}{n_{\mathrm{eff},m}}`,true)}</div></div>
 <dl class="simbol"><div><dt>${math(String.raw`\psi_m(x)`)}</dt><dd>Profil amplitudo melintang, dinormalisasi agar maksimum nilai mutlaknya 1.</dd></div><div><dt>${math(String.raw`\varphi_t=\omega t`)}</dt><dd>Fase waktu (rad). Kecepatan animasi diperlambat untuk pengamatan.</dd></div><div><dt>${math(String.raw`\beta_m`)}</dt><dd>Konstanta propagasi (rad/µm); menentukan perubahan fase sepanjang z.</dd></div><div><dt>${math(String.raw`\lambda_z`)}</dt><dd>Periode spasial sepanjang z (µm), misalnya jarak jingga ke jingga berikutnya pada TE0.</dd></div></dl>
 <p id="b-bacaan" class="bacaan numbers" aria-live="polite"></p>
 <p><b>Mengapa ada medan di luar teras?</b> Medan terikat memiliki ekor evanescent yang meluruh saat menjauhi teras. Medan di selubung tetap bagian dari mode yang merambat sepanjang pandu.</p>
 <details class="rumus-detail"><summary>Profil TE0 dan intensitas rata-rata waktu</summary>
 ${math(String.raw`\psi_0(x)=\begin{cases}\cos(hx),&|x|\le d/2,\\ \cos(hd/2)\,e^{-q(|x|-d/2)},&|x|>d/2.\end{cases}`,true)}
 ${math(String.raw`h=\sqrt{k_0^2 n_{\mathrm{core}}^2-\beta_0^2},\qquad q=\sqrt{\beta_0^2-k_0^2 n_{\mathrm{clad}}^2},\qquad k_0=\frac{2\pi}{\lambda_0}`,true)}
 <p>Rumus profil ini khusus TE0. Untuk mode lain, profil di teras berupa fungsi kosinus atau sinus sesuai paritas. Simbol h dan q memiliki satuan µm⁻¹; 1/q adalah jarak peluruhan amplitudo menjadi 1/e dari nilai di tepi teras.</p>
 ${math(String.raw`\langle S_z(x)\rangle_t=\frac{\beta_m E_0^2}{2\omega\mu}\,|\psi_m(x)|^2`,true)}
 <p>E₀ adalah amplitudo acuan medan listrik (V/m); ω adalah frekuensi sudut (rad/s); μ adalah permeabilitas magnetik (H/m), dengan μ = μ₀ untuk model bahan nonmagnetik ini. Besaran ⟨S_z⟩ adalah rapat aliran daya rata-rata sepanjang z (W/m²). Karena peta dinormalisasi, simulasi tidak menetapkan nilai E₀ atau daya masukan absolut.</p>
 <p>Intensitas rata-rata waktu sebanding dengan kuadrat amplitudo profil. Pada satu mode pandu ideal tanpa rugi, profil intensitas tetap sepanjang z. Bercak bergantian di peta medan sesaat tidak berarti daya bergantian hilang dan muncul.</p>
 </details>`);
 explanation('field-b',String.raw`<p><b>Cara membaca:</b> sumbu x menunjukkan posisi melintang. Arsiran menandai teras. Kurva hijau adalah profil amplitudo ${math(String.raw`\psi_m(x)`)}; kurva jingga adalah intensitas relatif ${math(String.raw`|\psi_m(x)|^2`)}. Grafik ini menunjukkan bentuk mode, sehingga tidak berubah ketika fase waktu dijalankan.</p>`);
 explanation('disp-d',String.raw`<p>Setiap kurva adalah satu mode TE pada panjang gelombang yang sedang dipilih. Ketika ketebalan berubah, titik berwarna menandai solusi mode terpilih. Garis tegak putus-putus menunjukkan d saat ini.</p><p>${math(String.raw`n_{\mathrm{clad}}<n_{\mathrm{eff},m}<n_{\mathrm{core}}`)} untuk mode terikat. Kurva baru muncul setelah melewati cutoff; titik cutoff sendiri tidak termasuk mode terikat.</p>`);
 explanation('disp-lambda',String.raw`<p>Ketebalan d dijaga sesuai slider. Saat panjang gelombang bertambah, mode biasanya kurang terkurung dan indeks efektifnya mendekati indeks selubung. Kurva mode orde tinggi dapat berhenti ketika mode mencapai cutoff.</p><p>${math(String.raw`n_{\mathrm{eff},m}=\frac{\beta_m}{k_0}`)} tidak memiliki satuan. Indeks teras dan selubung dijaga konstan, sehingga grafik ini hanya menunjukkan dispersi akibat geometri pandu.</p>`);

 document.querySelector('#part-c > .muted').insertAdjacentHTML('afterend',String.raw`
 <div class="panduan"><p><b>Celah ${math(String.raw`g`)}:</b> jarak antara tepi dalam kedua teras, bukan jarak antarpusat. Pandu a berada di bawah peta (${math(String.raw`x<0`)}); pandu b berada di atas (${math(String.raw`x>0`)}).</p><p><b>Mulai dari sini:</b> tekan <em>Ikuti propagasi</em> untuk menggeser irisan pengamatan. Tombol <em>Ke 50:50</em> memilih pembagian daya modal sama besar; <em>Ke transfer penuh</em> memilih maksimum pertama daya modal pada pandu b.</p></div>`);
 $('gap').parentElement.insertAdjacentHTML('beforeend','<p class="control-help" id="gap-help">Perbesar celah untuk melemahkan kopling dan memperpanjang jarak transfer pertama. Rentang z peta tetap sama.</p>');$('gap').setAttribute('aria-describedby','gap-help');
 explanation('map-c',String.raw`
 <div class="arti-warna"><span><i class="swatch nol"></i><b>Gelap:</b> intensitas rendah</span><span><i class="swatch tinggi"></i><b>Hijau–kuning:</b> intensitas lebih tinggi</span></div>
 <p><b>Baca dari kiri ke kanan.</b> Di dekat masukan, medan terutama berada di pandu a. Sepanjang z, dua supermode berinterferensi sehingga intensitas bergeser ke pandu b, lalu dapat kembali ke pandu a. Garis mendatar menandai tepi teras. Garis tegak putus-putus memilih irisan yang ditampilkan pada grafik di bawah.</p>
 ${math(String.raw`\widetilde E_y(x,z)=\frac{1}{\sqrt{2}}\left[u_{\mathrm e}(x)e^{i\beta_{\mathrm e}z}+u_{\mathrm o}(x)e^{i\beta_{\mathrm o}z}\right]`,true)}
 ${math(String.raw`I_{\mathrm{rel}}(x,z)=\frac{|\widetilde E_y(x,z)|^2}{\max_{x,z}|\widetilde E_y(x,z)|^2}`,true)}
 <p>${math(String.raw`u_{\mathrm e}`)} dan ${math(String.raw`u_{\mathrm o}`)} adalah profil supermode genap dan ganjil yang masing-masing dinormalisasi terhadap daya. Tanda mode ganjil dipilih agar masukan terutama berada pada pandu a. Skala warna 0–1 memakai maksimum bersama untuk seluruh peta pada celah terpilih; setiap kolom z tidak dinormalisasi sendiri.</p>
 <p><b>Makna animasi:</b> seluruh peta menunjukkan pola spasial keadaan tunak. Garis pengamatan yang bergerak tidak mewakili kecepatan sebuah pulsa atau foton.</p>`);
 explanation('slice-c',String.raw`<p>Grafik mengambil potongan tegak peta pada posisi z yang dipilih. Puncak pada x negatif berada di pandu a; puncak pada x positif berada di pandu b. Skala intensitas sama dengan peta di atas.</p><p>Persentase pada batang dihitung dari model daya modal. Persentase itu tidak diperoleh dengan menjumlahkan piksel terang atau mengintegralkan intensitas hanya di dalam inti teras.</p><p id="c-bacaan" class="bacaan numbers"></p>`);
 explanation('power-c',String.raw`
 ${math(String.raw`\frac{P_a(z)}{P_0}=\cos^2(\kappa z),\qquad \frac{P_b(z)}{P_0}=\sin^2(\kappa z)`,true)}
 ${math(String.raw`\kappa=\frac{\beta_{\mathrm e}-\beta_{\mathrm o}}{2},\qquad L_c=\frac{\pi}{2\kappa},\qquad L_{50:50}=\frac{L_c}{2}`,true)}
 <dl class="simbol"><div><dt>${math(String.raw`P_0`)}</dt><dd>Total daya masukan; rasio P/P₀ tidak memiliki satuan.</dd></div><div><dt>${math(String.raw`\kappa`)}</dt><dd>Koefisien kopling (µm⁻¹), dihitung dari beda konstanta propagasi dua supermode.</dd></div><div><dt>${math(String.raw`L_c`)}</dt><dd>Jarak transfer penuh pertama dari basis modal a ke b (µm).</dd></div><div><dt>${math(String.raw`L_{50:50}`)}</dt><dd>Jarak pembagian daya sama besar pertama (µm).</dd></div></dl>
 <p>Total daya modal selalu memenuhi ${math(String.raw`P_a+P_b=P_0`)}. Input merupakan kombinasi dua supermode yang terutama terlokalisasi pada pandu a. Khususnya pada celah kecil, angka 100% dalam basis modal tidak berarti medan benar-benar nol di seluruh inti pandu lainnya.</p>`);
 explanation('compare-c',String.raw`<p>Tiga kurva menggunakan d = 2 µm dan λ₀ = 1,55 µm yang sama. Hanya celah g yang berbeda. Puncak pertama bergeser ke kanan saat celah diperbesar, karena overlap medan evanescent dan kopling melemah.</p><p>Bandingkan posisi puncak pertama untuk menilai panjang transfer. Untuk membandingkan daya pada satu panjang perangkat, ikuti garis tegak putus-putus dan baca kolom terakhir tabel. Daya pada z yang sama tidak harus turun monoton terhadap celah karena pertukaran daya berulang.</p>`);
 // Replace the original compact power formula with a pointer to the typeset equations.
 panel('power-c').querySelector('.caption').textContent='Garis hijau: daya modal pandu a. Garis jingga: daya modal pandu b. Titik berwarna mengikuti posisi z terpilih.';
 const style=document.createElement('style');style.textContent=`
 .panduan{border-left:3px solid var(--a);padding:1px 0 1px 16px;margin:16px 0;color:var(--muted)}
 .panduan p{margin:7px 0}.panduan b,.penjelasan b{color:var(--ink);font-weight:550}
 .control-help{font-size:13px;color:var(--muted);margin:7px 0 0;max-width:45em}
 .map-intro{color:var(--muted);margin:10px 0 4px}.penjelasan{margin-top:16px;padding-top:14px;border-top:1px solid var(--line);color:var(--muted)}
 .penjelasan p{margin:9px 0}.rumus{color:var(--ink)}.rumus-blok{overflow-x:auto;overflow-y:hidden;padding:10px 2px;max-width:100%}.rumus-blok .katex-display{margin:0;text-align:left}.rumus-blok .katex-display>.katex{text-align:left}
 .rumus-pasang{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:14px}.rumus-pasang>div{min-width:0}
 .arti-warna{display:flex;flex-wrap:wrap;gap:10px 22px;margin:14px 0;color:var(--muted);font-size:14px}.arti-warna span{display:inline-flex;align-items:center;gap:6px}.swatch{display:inline-block;width:14px;height:14px;border-radius:3px;flex-shrink:0}.swatch.negatif{background:#284cbb}.swatch.positif{background:#ffba66}.swatch.nol{background:#101926;box-shadow:inset 0 0 0 1px #68798c}.swatch.tinggi{background:linear-gradient(90deg,#58d3bd,#f4e7a3)}
 .simbol{display:grid;grid-template-columns:1fr 1fr;gap:12px 25px;margin:12px 0}.simbol>div{display:grid;grid-template-columns:minmax(55px,auto) 1fr;gap:12px;align-items:baseline}.simbol dt{color:var(--ink)}.simbol dd{margin:0;font-size:14px}.bacaan{color:var(--ink);border-left:2px solid var(--b);padding-left:12px}.rumus-detail{margin:14px 0 0;padding:12px 0 0}.katex{font-size:1.08em}
 .panel:not(.wide) .simbol{grid-template-columns:1fr}
 @media(max-width:850px){.rumus-pasang,.simbol{grid-template-columns:1fr}.arti-warna{gap:10px 16px}}
 `;document.head.append(style);
 for(const el of document.querySelectorAll('[data-tex]')){
   katex.render(el.dataset.tex,el,{displayMode:el.classList.contains('rumus-blok'),throwOnError:true,trust:false,strict:'error'});
 }
 window.OptikKeterangan={
   updateB(data,s){const m=data.mode;
     $('b-bacaan').textContent=`Saat ini: TE${m.m}; teras dari x = −${fmt(s.d/2)} sampai +${fmt(s.d/2)} µm. Periode sepanjang z = ${fmt(s.lam/m.neff,3)} µm. Panjang peluruhan amplitudo di selubung 1/q = ${fmt(1/m.q,3)} µm.`;
   },
   updateC(c,s){const pa=Math.cos(c.kappa*s.z)**2,pb=1-pa;
     $('c-bacaan').textContent=`Pada z = ${fmt(s.z,1)} µm dan celah ${fmt(c.g)} µm, daya modal a = ${fmt(100*pa,1)}% dan b = ${fmt(100*pb,1)}%. Total = 100%.`;
   }
 };
})();
