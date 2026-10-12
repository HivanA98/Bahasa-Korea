# Yang perlu ditinjau manusia

Isi `data/*.json` disusun oleh model bahasa dan diperiksa otomatis hanya pada
hal-hal yang bisa diperiksa mesin: bentuk Hangeul, ketaatan pada aturan
pelafalan, keselarasan kunci jawaban dengan data, dan kelengkapan skema.
**Kewajaran bahasanya belum ditinjau penutur asli atau pengajar.**

Berkas ini mendaftar hal-hal yang paling perlu diperiksa lebih dahulu.

## Yang TIDAK diperiksa mesin

- Apakah arti Bahasa Indonesia sudah tepat dan wajar.
- Apakah contoh kalimat terdengar alami bagi penutur Korea, bukan sekadar
  benar secara tata bahasa.
- Apakah tingkat kesopanan setiap contoh cocok dengan keadaan yang dibayangkan.
- Apakah catatan pemakaian (`note`) menyederhanakan secara menyesatkan.
- Apakah pilihan kata untuk pemula memang kata yang paling sering dipakai.

## Butir yang sudah diketahui perlu perhatian

| Tempat | Hal yang perlu ditinjau |
|:-------|:------------------------|
| `vocab.json` v014 (당신) | Catatan sudah memperingatkan bahwa 당신 tidak dipakai seperti "Anda" dalam Bahasa Indonesia. Perlu dipastikan peringatannya cukup tegas untuk pemula. |
| `vocab.json` v061 (차) dan v101 (사과) | Dua kata Sino-Korea berbeda yang bunyinya sama. Field `hanja` memuat dua aksara dipisah garis miring; bila Anda ingin memisahkannya menjadi dua entri, keduanya perlu id berbeda. |
| `vocab.json` v145 (맛없다) | Lafal bakunya [마덥따], berbeda pola dari 맛있다 [마시따]. Mesin pelafalan menghasilkan bentuk yang berbeda untuk kedua kata ini karena memang aturannya berbeda; perlu dipastikan catatannya tidak membingungkan. |
| `numbers.json` c18 (인분) | Bentuk baku 이 인분, tetapi 두 인분 sangat umum terdengar. Catatan sudah menyebutkan keduanya. |
| `numbers.json` num-q12 | Nama bulan Juni (유월) dan Oktober (시월) tidak beraturan. Belum ada kartu tersendiri untuk nama bulan; bila ingin ditambah, tempatnya di modul angka. |
| `speech.json` sp12 (진지) | Sudah ditandai kuno. Perlu dipastikan masih layak diajarkan kepada pemula, atau sebaiknya dipindah ke tahap paling akhir. |
| `hangeul.json` h30/h32 (ㅐ dan ㅔ) | Keterangan bahwa keduanya hampir menyatu dalam ucapan masa kini perlu diperiksa terhadap keadaan sekarang, khususnya untuk penutur muda Seoul. |

## Batas mesin pelafalan

`koreadrill/pronounce.py` menerapkan sembilan aturan baku. Yang **tidak**
diterapkannya, dan karena itu perlu diperiksa manusia bila Anda menambah data:

- **Sisipan ㄴ (ㄴ 첨가).** Pemicunya batas morfem yang tidak terlihat dari
  tulisan. Kata semacam ini didaftar satu per satu di `EXCEPTIONS`. Bila Anda
  menambahkan kata gabungan baru, periksa lafalnya sendiri.
- **Pengerasan karena akhiran tata bahasa** (할 것 → 할 껀) dan **di dalam frasa
  yang melekat erat** (몇 시 → 멷 씨). Pemicunya jenis akhiran dan kedekatan
  makna, bukan hurufnya.
- **Panjang vokal.** 눈 (mata) dan 눈 (salju) dibedakan panjang vokalnya dalam
  ucapan baku, dan itu sama sekali tidak tertulis.
- **Perbedaan daerah dan perorangan.** Semua lafal di sini adalah ragam baku
  Seoul.

## Cara menambah atau memperbaiki data

```bash
# 1. sunting data/*.json
python -m pytest                      # 2. pastikan data masih sah
python tools/build_exports.py         # 3. buat ulang CSV dan Anki
python tools/build_worksheets.py      # 4. buat ulang lembar kerja
python tools/build_web.py             # 5. buat ulang data aplikasi web
python -m pytest                      # 6. pastikan semua hasil mutakhir
```

Bila Anda seorang penutur Korea atau pengajar dan menemukan kesalahan,
perbaikan paling berguna adalah pada `example` dan `note`: di situlah
kewajaran bahasa paling terasa.
