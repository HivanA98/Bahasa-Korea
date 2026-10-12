# Latihan Bahasa Korea dari Nol

Bahan latihan Bahasa Korea (한국어) untuk pelajar penutur Bahasa Indonesia yang
**belum mengenal satu huruf pun**.

Materi ini berangkat dari titik paling awal: mengenali huruf Hangeul, menyusun
blok suku kata, lalu naik ke kosakata, tata bahasa, angka, pelafalan, dan
tingkat tutur. Sasarannya tingkat A1 menuju A2.

| | |
|:--|:--|
| Huruf Hangeul | 40 huruf, 8 kelompok batchim, 10 aturan pelafalan |
| Kosakata | 180 entri, 6 tahap |
| Topik tata bahasa | 12 topik, 60 soal |
| Angka dan penggolong | 22 angka, 18 penggolong, 2 sistem |
| Membaca dan pelafalan | 12 teks, 26 soal, 3 level |
| Tingkat tutur | 16 pasangan bentuk hormat, 12 soal |
| Total kartu | 597 |
| Lembar kerja tertulis | 12 lembar + 12 kunci jawaban |
| Pengujian otomatis | 449 |

Sebagian kartu **dibuat otomatis dari data**, bukan ditulis tangan: soal
pemilihan partikel (93 kartu), soal penyusunan blok suku kata (40 kartu), dan
soal angka + penggolong (18 kartu). Kuncinya dihitung oleh mesin bahasa di
`koreadrill/`, sehingga tidak mungkin menyimpang dari datanya.

## Dua cara memakai

### 1. Aplikasi kartu di browser

Buka `index.html`. Tidak perlu memasang apa pun, dan tidak perlu peladen:
datanya dimuat lewat tag `<script>`, bukan `fetch()`, sehingga berkasnya bisa
dibuka langsung (`file://`) maupun diunggah ke GitHub Pages.

Untuk menjalankannya dengan peladen lokal:

```bash
python -m http.server 8766
```

lalu buka <http://localhost:8766>.

Enam modul dalam bentuk kartu bolak-balik: Hangeul, kosakata (dua arah), tata
bahasa (pilihan ganda), angka dan penggolong, baca dan lafal, serta
kesantunan. Progres memakai lima kotak Leitner yang sama dengan versi terminal
dan tersimpan di `localStorage` peramban Anda sendiri.

Pintasan papan ketik: `Spasi` balik kartu &middot; `&larr;` `&rarr;` navigasi
&middot; `1`&ndash;`4` pilih jawaban &middot; `H` sudah hafal &middot; `B` belum
hafal &middot; `S` acak &middot; `R` alih huruf &middot; `P` lafal &middot; `/` cari.

### 2. Latihan di terminal

`python quiz.py` memberi hal yang tidak ada di versi web: jawaban yang **ditulis
sendiri** (bukan pilihan ganda), sesi berbatas waktu, interleaving antar modul,
pembatasan materi baru per sesi, dan pengenalan materi menurut urutan tahap.

Progres kedua versi terpisah: aplikasi web memakai `localStorage`, versi
terminal memakai `progress.json`. Keduanya tidak saling tahu, jadi pilih salah
satu untuk materi yang sama.

## Yang TIDAK ada di sini

- **Tidak ada rekaman suara.** Pelafalan dijelaskan dengan tulisan dan dengan
  lafal dalam Hangeul (`[한궁말]`), bukan dengan audio. Untuk menyamakan telinga,
  Anda tetap perlu mendengarkan penutur asli.
- **Tidak ada alih huruf Latin secara bawaan.** Alih huruf hanya muncul bila
  Anda menyalakannya. Alasannya: penyangga Latin membuat mata berhenti membaca
  Hangeul, padahal Hangeul justru bagian termudah dari Bahasa Korea dan bisa
  dikuasai dalam hitungan hari.
- **Tidak ada hanja sebagai bahan hafalan.** Aksara Tionghoa hanya dicantumkan
  sebagai keterangan asal-usul kata.
- **Tidak ada dialek.** Hanya ragam baku Seoul.
- **Tidak ada janji hasil.** Kecepatan belajar setiap orang berbeda-beda.

## Persyaratan

Python 3.10 atau lebih baru. Tidak ada pustaka pihak ketiga yang perlu dipasang
untuk menjalankan latihannya; `pytest` hanya diperlukan untuk menjalankan
pengujian.

Terminal Anda perlu bisa menampilkan Hangeul. Di Windows, Windows Terminal
menampilkannya jauh lebih baik daripada `cmd.exe` lama.

## Mulai cepat

```bash
python quiz.py
```

Sesi bawaan: 20 menit, campuran semua modul, 8 kartu baru. Progres tersimpan di
`progress.json`.

Hari pertama sebaiknya dibatasi pada hurufnya saja:

```bash
python quiz.py --mode hangeul --stage 1
```

Ringkasan kemajuan:

```bash
python quiz.py --stats
```

## Bendera baris perintah

| Bendera | Arti |
|:--------|:-----|
| `--mode MODE` | Batasi mode. Boleh diulang atau dipisah koma. Bawaan: semua. |
| `--stage N` | Batasi materi sampai tahap N (1-6). |
| `--minutes M` | Lama sesi dalam menit (bawaan 20). Sesi berhenti saat waktunya habis. |
| `--limit N` | Batas jumlah soal dalam satu sesi. |
| `--new N` | Kartu baru per sesi (bawaan 8). `--new 0` berarti hanya mengulang. |
| `--romaja` | Tampilkan alih huruf Latin di bawah teks Hangeul. |
| `--seed N` | Nilai awal pengacak, untuk mengulang susunan sesi yang sama. |
| `--progress BERKAS` | Lokasi berkas progres selain `progress.json`. |
| `--stats` | Tampilkan ringkasan kemajuan lalu keluar. |
| `--reset` | Hapus berkas progres (meminta konfirmasi). |
| `--no-color` | Matikan warna. |

Mode yang tersedia:

| Mode | Isi |
|:-----|:----|
| `hangeul` | Huruf, nama huruf, batchim, penyusunan blok suku kata, dan aturan pelafalan. Sebagian jawaban **ditulis** (alih huruf Latin). |
| `kosakata-ko` | Korea ke Indonesia. Jawaban **ditulis** (bukan pilihan ganda). |
| `kosakata-id` | Indonesia ke Korea. Pilihan ganda. |
| `tatabahasa` | Tata bahasa, pemilihan partikel, dan kesantunan. |
| `angka` | Dua sistem angka dan penggolongnya. |
| `baca` | Membaca kalimat dan menentukan lafal yang benar. |

Di dalam sesi: ketik nomor untuk pilihan ganda, `l` untuk melewati, `k` untuk
keluar, `?` untuk melihat jawaban pada soal yang jawabannya ditulis (dihitung
salah).

Jawaban yang ditulis selalu berupa **huruf Latin** (arti Bahasa Indonesia atau
alih huruf), tidak pernah Hangeul, supaya Anda tidak perlu memasang papan ketik
Korea lebih dahulu. Kartu yang jawabannya berupa tulisan Korea memakai cara
periksa sendiri: lihat jawabannya, lalu nilai sendiri benar atau salah.

## Isi materi

### Modul 1 — Hangeul (`data/hangeul.json`)

Titik masuk bagi yang belum mengenal satu huruf pun.

- **40 huruf**: 14 huruf mati dasar, 5 huruf kembar (ㄲ ㄸ ㅃ ㅆ ㅉ), 10 vokal
  dasar, dan 11 vokal gabungan. Setiap huruf memuat keterangan bunyi dalam
  Bahasa Indonesia, nama hurufnya (기역, 니은, …), alih huruf, dan contoh kata.
- **Struktur blok suku kata**: huruf awal + vokal + batchim, beserta aturan
  peletakannya (vokal tegak di kanan, vokal rebah di bawah).
- **8 kelompok batchim**: tujuh bunyi akhir yang mungkin, ditambah batchim
  ganda.
- **10 aturan pelafalan**: penyambungan bunyi, penghilangan ㅎ, penetralan
  batchim, penyederhanaan batchim ganda, penyengauan, pengerasan,
  pengaspiratan, peleburan ke ㄹ, palatalisasi, dan sisipan ㄴ.

Soal "mana blok suku kata dari ㄱ + ㅏ + ㄴ" **dibuat otomatis** dengan
`koreadrill/hangeul.py`, termasuk pengecohnya, sehingga semua pilihan pasti
blok Hangeul yang sah dan kuncinya tidak mungkin keliru.

### Modul 2 — Kosakata inti (`data/vocab.json`)

180 entri dalam 6 tahap: sapaan, kata ganti, kata tanya, keluarga, orang,
benda, tempat, waktu, makanan, kata kerja, kata sifat, kata keterangan, dan
cuaca.

Setiap entri memuat kata dalam Hangeul, arti Indonesia, kelas kata, bentuk
해요 (untuk kata kerja dan kata sifat), hanja bila ada, satu contoh kalimat
pendek dalam bentuk sopan, dan catatan pemakaian.

Lafal dan alih huruf **tidak disimpan** di berkas data. Keduanya dihitung oleh
`koreadrill/pronounce.py` dan `koreadrill/romaja.py`, sehingga tidak ada dua
sumber yang bisa saling bertentangan.

### Modul 3 — Tata bahasa dasar (`data/grammar.json`)

| Topik | Isi |
|:------|:----|
| g01 | Kalimat 'A adalah B': 이에요 / 예요 |
| g02 | Partikel topik: 은 / 는 |
| g03 | Partikel subjek: 이 / 가, dan bedanya dengan 은/는 |
| g04 | Partikel objek: 을 / 를 dan urutan kata |
| g05 | Tempat dan waktu: 에 dan 에서 |
| g06 | Bentuk sopan 해요체: akhiran 아요 / 어요 |
| g07 | Bentuk lampau: 았어요 / 었어요 |
| g08 | Penafian: 안, 못, dan -지 않다 |
| g09 | Keberadaan dan tempat: 있어요 / 없어요 |
| g10 | Bertanya: kata tanya, 몇, dan nada bicara |
| g11 | Menggabungkan: 하고 / 와 / 과, 도, dan 만 |
| g12 | Keinginan dan kemampuan: -고 싶어요, -(으)ㄹ 수 있어요 |

Setiap topik memiliki field `caveats` yang memuat pengecualian dan batas
berlakunya aturan. Hal-hal itu sengaja ditulis sebagai catatan, bukan sebagai
aturan mutlak — khususnya perbedaan 은/는 dan 이/가, yang memang tidak bisa
diselesaikan oleh satu aturan.

Selain 60 soal tulisan tangan, modul ini memuat **93 soal pemilihan partikel
yang dibuat otomatis** dari daftar kata benda: "partikel mana untuk 책?"
Kuncinya dihitung dari ada tidaknya batchim oleh `hangeul.particle()`.

### Modul 4 — Angka dan penggolong (`data/numbers.json`)

Bahasa Korea memakai dua sistem angka berdampingan, dan memilih yang salah
adalah kesalahan pemula yang paling mudah dikenali.

- **Angka asli Korea** (하나, 둘, 셋 …) untuk jumlah benda, orang, umur, jam,
  dan berapa kali.
- **Angka Sino-Korea** (일, 이, 삼 …) untuk uang, tanggal, menit, nomor, dan
  lantai.

18 penggolong, masing-masing dengan sistem angkanya: 개, 명, 분, 마리, 권, 장,
대, 잔, 병, 그릇, 살, 시, 시간, 번, 분 (menit), 원, 층, 인분. Perhatikan 분 yang
muncul dua kali: "orang (hormat)" dengan angka asli Korea, dan "menit" dengan
angka Sino-Korea.

Soal "bagaimana mengatakan 2 apel" **dibuat otomatis** dari data angka dan
penggolong, termasuk bentuk tak beraturan 하나 → 한 dan 스물 → 스무.

### Modul 5 — Membaca dan pelafalan (`data/reading.json`)

Keterampilan penghubung: dari membaca huruf satu per satu menjadi membaca
kalimat dengan bunyi yang benar.

| Level | Isi |
|:------|:----|
| 1 | Lafal sama dengan tulisannya |
| 2 | Hanya penyambungan bunyi dan penghilangan ㅎ |
| 3 | Dua aturan atau lebih bekerja sekaligus |

Level setiap butir **tidak ditulis bebas**: pengujian otomatis memeriksa bahwa
level yang tertulis cocok dengan aturan yang benar-benar bekerja menurut mesin
pelafalan. Begitu pula kunci soal "bagaimana ini dibunyikan": kuncinya wajib
sama persis dengan keluaran `pronounce()`.

### Modul 6 — Tingkat tutur dan bentuk hormat (`data/speech.json`)

Catatan, bukan latihan utama. Memuat tiga tingkat tutur (합니다체, 해요체,
반말) dan 16 pasangan bentuk hormat yang paling sering dipakai: 먹다 → 드시다,
자다 → 주무시다, 있다 → 계시다, 주다 → 드리다, 이름 → 성함, dan seterusnya.

Modul ini juga menegaskan satu hal yang sering disalahpahami: bentuk hormat
dipakai untuk **meninggikan orang lain**, sedangkan bentuk merendah dipakai
untuk **merendahkan diri sendiri**. Keduanya berlawanan arah, dan memakai
bentuk hormat untuk diri sendiri adalah kesalahan.

## Bagaimana lafal dihitung

`koreadrill/pronounce.py` menerapkan sembilan aturan baku (표준 발음법) dalam
urutan tetap. Urutannya menentukan hasil: 못해요 harus melewati penetralan
batchim (ㅅ menjadi ㄷ) sebelum pengaspiratan, supaya hasilnya 모태요 dan bukan
몯해요.

```
palatalisasi → pengaspiratan → penghilangan ㅎ → penyambungan bunyi →
penyederhanaan batchim ganda → penetralan batchim → penyengauan →
peleburan ke ㄹ → pengerasan
```

Mesin ini dipakai oleh terminal, aplikasi web, lembar kerja, dan ekspor Anki
sekaligus, sehingga tidak ada dua tempat yang bisa memberi lafal berbeda untuk
kata yang sama.

Yang **tidak** diterapkannya, dan karena itu perlu diperiksa manusia:

- Sisipan ㄴ pada kata gabungan (십육 → 심뉵). Pemicunya batas morfem yang tidak
  terlihat dari tulisan, jadi kata semacam itu didaftar satu per satu.
- Pengerasan karena akhiran tata bahasa (할 것 → 할 껀) dan di dalam frasa yang
  melekat erat (몇 시 → 멷 씨).
- Panjang vokal, yang membedakan 눈 (mata) dan 눈 (salju) tetapi sama sekali
  tidak tertulis.

Pembatasan yang disengaja: penyambungan bunyi, pengerasan, dan peleburan ke ㄹ
hanya berlaku **di dalam satu kata**. Karena itu 한국 사람 tetap dibaca 한국
사람, bukan 한국 싸람. Penyengauan tetap berlaku antar kata (밥 먹어요 →
밤 머거요).

## Cara kerja penjadwalan

Lima kotak Leitner. Jawaban benar menaikkan kartu satu kotak, jawaban salah
mengembalikannya ke kotak 1.

| Kotak | Jeda sebelum diulang |
|------:|---------------------:|
| 1 | hari itu juga |
| 2 | 1 hari |
| 3 | 3 hari |
| 4 | 7 hari |
| 5 | 16 hari |

Angka-angka itu adalah pilihan praktis yang lazim dipakai pada kartu Leitner,
**bukan hasil pengukuran**. Ubah `INTERVALS` di `koreadrill/leitner.py` bila
jadwal lain lebih cocok.

Empat hal lain yang diterapkan penjadwal:

- **Ulangan didahulukan.** Selama masih ada kartu jatuh tempo, materi baru
  dibatasi paling banyak 45% dari satu sesi. Tanpa pembatasan ini materi baru
  memakan seluruh sesi dan kartu lama tidak pernah naik kotak.
- **Interleaving.** Soal dari modul berbeda disilang bergantian, dan materi
  lama disisipkan di antara materi baru kira-kira 2 lama : 1 baru. Mencampur
  materi umumnya menghasilkan ingatan yang lebih tahan lama daripada
  mengerjakan satu blok materi sejenis berturut-turut, meski terasa lebih
  sulit saat dikerjakan.
- **Materi baru masuk menurut urutan tahap**, bukan acak dari seluruh materi,
  walaupun `--stage` tidak diberikan.
- **Lintasan kedua.** Pada hari-hari awal, ketika belum ada kartu jatuh tempo,
  kartu baru diulang sekali lagi di akhir sesi. Pengulangan itu tidak menaikkan
  kotak Leitner dua kali.

Jatah kartu baru dibagi antar modul dengan bobot (kosakata 3, Hangeul 2, tata
bahasa 2, angka 1, baca 1) memakai metode sisa terbesar, sehingga jumlahnya
**tepat** sebanyak `--new` dan modul yang tidak kebagian pada satu sesi akan
kebagian pada sesi berikutnya.

## Jadwal 12 minggu

Dengan pengaturan bawaan (20 menit per sesi, 8 kartu baru, 5 sesi per minggu),
penjadwal memperkenalkan **40 kartu baru per minggu**, yang berarti sekitar
**12 kata baru per minggu** ditambah huruf, soal tata bahasa, angka, dan
latihan baca.

| Minggu | Kartu dikenal | Hangeul | Kosakata | Tata bahasa | Angka | Baca |
|-------:|--------------:|--------:|---------:|------------:|------:|-----:|
| 1 | 40 | 10 | 10 | 10 | 5 | 5 |
| 2 | 80 | 20 | 20 | 20 | 10 | 10 |
| 4 | 160 | 40 | 40 | 40 | 20 | 20 |
| 6 | 240 | 60 | 60 | 60 | 30 | 30 |
| 8 | 318 | 80 | 80 | 80 | 40 | 38 |
| 10 | 388 | 100 | 100 | 100 | 50 | 38 |
| 12 | 458 | 120 | 120 | 120 | 60 | 38 |

Pada akhir minggu ke-8 dengan pengaturan bawaan, **seluruh latihan baca sudah
diperkenalkan**, sedangkan kosakata mencapai 80 dari 180 kata. Memperkenalkan
seluruh 597 kartu pada kecepatan yang sama memerlukan sekitar **18 minggu**
(kira-kira 91 sesi).

Bila Anda ingin lebih cepat, naikkan `--new` — tetapi beban ulangannya ikut
naik dan sesi 20 menit menjadi tidak cukup.

### Dari mana angka-angka itu

Angka di tabel berasal dari **simulasi penjadwal**, bukan dari pengamatan
pembelajar nyata: 60 sesi berurutan, 5 sesi per minggu, dengan asumsi
ketepatan jawaban 85%. Pada simulasi itu, tunggakan soal jatuh tempo mencapai
sekitar 120 soal pada minggu ke-8 dan terus naik ke sekitar 220 pada minggu
ke-12, karena materi baru masih terus masuk. Dengan ketepatan 95%, angkanya
sekitar 50 dan 120.

Kecepatan setiap orang berbeda, dan tidak ada yang menjamin angka ini berlaku
untuk Anda.

### Bila tunggakan menumpuk

Bila `--stats` menunjukkan kartu jatuh tempo jauh lebih banyak daripada yang
bisa Anda kerjakan:

```bash
python quiz.py --new 0            # satu sesi khusus mengulang, tanpa materi baru
python quiz.py --new 4            # perlambat laju materi baru
python quiz.py --minutes 30       # sesi lebih panjang
```

Memperlambat materi baru lebih baik daripada menumpuk kartu yang tidak pernah
diulang.

## Lembar kerja

12 lembar kerja Markdown di `worksheets/`, dua lembar per tahap, dengan kunci
jawaban **terpisah** di `worksheets/answers/`. Setiap lembar memuat tujuh
bagian: huruf dan blok suku kata, arti kata, menulis kata Korea, tata bahasa,
partikel, angka dan penggolong, serta pelafalan.

Lembar kerja dibuat dari data oleh skrip, bukan ditulis tangan, sehingga
kuncinya selalu sejalan dengan datanya. Jangan menyuntingnya langsung.

```bash
python tools/build_worksheets.py
```

Menulis Hangeul dengan tangan bukan hiasan: bentuk blok suku kata baru
benar-benar masuk setelah tangan ikut menyusunnya.

## Anki

Ekspor CSV untuk Anki ada di `anki/`, beserta pemetaan kolom ke field di
`anki/README.md`.

```bash
python tools/build_exports.py
```

Catatan: bila Anda memakai Anki, pakailah penjadwalan Anki dan jangan
menjalankan `quiz.py` untuk materi yang sama. `progress.json` dan koleksi Anki
tidak saling tahu, sehingga satu kartu akan dijadwalkan oleh dua sistem
sekaligus.

## Pengujian

```bash
python -m pytest
```

449 pengujian. Yang diperiksa:

| Berkas | Isi |
|:-------|:----|
| `test_schema.py` | Id unik di seluruh modul, format id, tidak ada field kosong atau null yang tidak diizinkan, kelas kata sah, kata kerja punya bentuk 해요, setiap tahap dan setiap level terisi, jumlah huruf Hangeul lengkap (19 + 21). |
| `test_hangeul.py` | Komposisi dan dekomposisi bolak-balik untuk **seluruh 11.172 blok suku kata Hangeul**, penolakan huruf yang salah tempat, nama huruf, pemilihan partikel menurut batchim, bentuk NFC, tidak ada huruf Latin di field Korea, tidak ada huruf tunggal yang tercecer di dalam kata. |
| `test_pronounce.py` | 49 kasus lafal yang dipatok dari 표준 발음법, urutan aturan, kestabilan hasil bila diproses ulang, pembatasan antar kata, dan keselarasan contoh aturan di data dengan mesinnya. |
| `test_romaja.py` | Kasus alih huruf RR yang dipatok, ㄹㄹ ditulis `ll`, pengerasan tidak dituliskan, tidak ada Hangeul yang tertinggal. |
| `test_keys.py` | Setiap soal punya tepat satu jawaban benar, tidak ada pilihan kembar, kunci soal lafal sama dengan mesin, level butir baca cocok dengan aturan yang bekerja, kunci soal partikel dihitung dari batchim, kunci soal penggolong memakai sistem angka yang benar, pengecoh kosakata tidak ikut benar. |
| `test_leitner.py` | Kenaikan dan penurunan kotak, jeda sesuai tabel, jatuh tempo, simpan dan muat ulang, berkas rusak tidak merusak pemuatan, penulisan atomik. |
| `test_session.py` | Batas kartu baru, ulangan tidak tergeser habis oleh materi baru, kartu belum jatuh tempo tidak muncul, interleaving mencampur mode, satu kata dilatih dua arah, materi baru masuk menurut urutan tahap, sesi dapat diulang dengan seed sama. |
| `test_exports.py` | Semua hasil ekspor mutakhir terhadap data (CSV, Anki, lembar kerja, dan `webdata.js`), format Anki benar, kunci soal di `webdata.js` sama dengan di `data/`, lafal di `webdata.js` sama dengan mesin, dan aplikasi web tidak memakai `fetch()` sehingga tetap jalan di `file://`. |
| `test_worksheets.py` | Kunci berada di berkas terpisah, semua bagian ada, jawaban tidak bocor ke lembar soal, kunci partikel dan kunci pelafalan dihitung mesin, dan setiap butir berasal dari data. |

### Apa yang TIDAK bisa diuji mesin

Pengujian di atas memeriksa **bentuk**, bukan **kebenaran isi bahasa**. Yang
tidak diperiksa mesin:

- Apakah arti Bahasa Indonesia sudah tepat dan wajar.
- Apakah contoh kalimat terdengar alami bagi penutur Korea, bukan sekadar benar
  secara tata bahasa.
- Apakah tingkat kesopanan setiap contoh cocok dengan keadaannya.
- Apakah penjelasan tata bahasa tidak menyederhanakan secara menyesatkan.
- Apakah catatan budaya (misalnya tentang 당신 dan tentang bertanya umur) masih
  sesuai dengan keadaan sekarang.

**Periksalah isinya dengan kamus rujukan atau dengan pengajar** sebelum
menghafalkannya. Hal-hal yang sudah diketahui perlu ditinjau didaftar di
`data/NEEDS_REVIEW.md`.

## Menyunting data

`data/*.json` adalah **satu-satunya sumber data**. Berkas di `data/csv/`,
`anki/`, `worksheets/`, dan `webdata.js` adalah turunan yang dibuat ulang oleh
skrip.

```bash
# 1. sunting data/vocab.json (atau modul lain)
python -m pytest                      # 2. pastikan data masih sah
python tools/build_exports.py         # 3. buat ulang CSV dan Anki
python tools/build_worksheets.py      # 4. buat ulang lembar kerja
python tools/build_web.py             # 5. buat ulang data aplikasi web
python -m pytest                      # 6. pastikan semua hasil mutakhir
```

Pengujian `test_exports.py` akan gagal bila data sudah berubah tetapi
ekspornya belum dibuat ulang.

### Aturan penulisan teks Korea di data

| Aturan | Alasan |
|:-------|:-------|
| Semua teks Korea berbentuk **NFC** (suku kata tergabung) | Teks NFD tampak sama di layar tetapi gagal dibandingkan dan dicari. |
| Tidak boleh ada **huruf Latin** di dalam field Korea | Field itu dipakai untuk menghitung lafal dan alih huruf. |
| Tidak boleh ada **huruf tunggal** (ㄱ, ㅏ) di dalam kata | Pengecualiannya hanya field yang memang membahas huruf, yaitu daftar huruf dan daftar batchim. |
| Lafal dan alih huruf **tidak ditulis di data** | Keduanya dihitung mesin; menuliskannya berarti menciptakan sumber kedua yang bisa bertentangan. |

## Struktur folder

```
index.html            aplikasi kartu di browser (GitHub Pages)
style.css             tiga tema: hanji, bam, cheong
app.js                kartu, saringan, Leitner di localStorage
webdata.js            data aplikasi web (dibuat ulang)
.nojekyll             agar GitHub Pages tidak memproses berkas lewat Jekyll
data/                 sumber data JSON + NEEDS_REVIEW.md
  csv/                ekspor CSV (dibuat ulang)
koreadrill/           paket inti
  hangeul.py          komposisi suku kata, batchim, partikel, validator
  pronounce.py        sembilan aturan pelafalan + daftar pengecualian
  romaja.py           alih huruf Revisi (RR), dihitung dari lafal
  leitner.py          lima kotak + jadwal + berkas progres
  dataio.py           pemuat data
  questions.py        pembuat soal per mode, termasuk soal buatan otomatis
  session.py          penyusun sesi (jatuh tempo, materi baru, interleaving)
quiz.py               antarmuka baris perintah
tools/                build_exports.py, build_worksheets.py, build_web.py
anki/                 ekspor Anki (dibuat ulang) + pemetaan field
worksheets/           lembar kerja (dibuat ulang)
  answers/            kunci jawaban
tests/                pengujian otomatis
progress.json         progres Anda (dibuat saat latihan pertama)
```

## Catatan keterbatasan

- Materi ini disusun oleh model bahasa dan diperiksa secara otomatis hanya pada
  hal-hal yang bisa diperiksa mesin. Isi bahasanya belum ditinjau penutur asli
  atau pengajar.
- Tingkat A1-A2 berarti kalimat pendek dan kosakata sehari-hari. Membaca berita
  Korea dengan lancar memerlukan kosakata yang jauh lebih banyak daripada yang
  ada di sini.
- Modul pelafalan melatih penentuan bunyi pada kata dan kalimat pendek yang
  kosakatanya sudah Anda kenal. Teks nyata lebih sulit karena memuat kata yang
  belum dikenal dan dibaca dengan kecepatan penutur asli.
- Tidak ada latihan menyimak dan berbicara di proyek ini. Keduanya memerlukan
  suara dan lawan bicara, bukan kartu.
