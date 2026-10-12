# Ekspor Anki

Berkas di folder ini **dibuat ulang** oleh `python tools/build_exports.py` dari
`data/*.json`. Jangan menyuntingnya langsung; sunting datanya lalu jalankan
ulang skripnya.

Semuanya berupa CSV UTF-8 tanpa baris judul, dengan tiga baris pengarah di
awal berkas:

```
#separator:Comma
#html:false
#tags column:N
```

Baris pengarah itu dikenali Anki 2.1.55 ke atas. Bila versi Anki Anda menolak
berkasnya, hapus ketiga baris tersebut lalu atur pemisah dan kolom tag secara
manual di jendela impor.

## Pemetaan kolom

| Berkas | Kolom |
|:-------|:------|
| `hangeul.csv` | 1 huruf · 2 alih huruf dan nama · 3 keterangan bunyi · 4 contoh kata · 5 tag |
| `kosakata.csv` | 1 kata Korea (dengan lafal dalam kurung siku bila berbeda) · 2 arti · 3 alih huruf · 4 contoh kalimat · 5 catatan · 6 tag |
| `tatabahasa.csv` | 1 soal · 2 jawaban · 3 penjelasan · 4 topik · 5 tag |
| `angka.csv` | 1 angka atau penggolong · 2 jawaban · 3 catatan · 4 tag |
| `lafal.csv` | 1 tulisan · 2 lafal · 3 arti dan alih huruf · 4 aturan yang bekerja · 5 tag |
| `kesantunan.csv` | 1 bentuk biasa · 2 bentuk hormat · 3 arti dan arah kesantunan · 4 contoh dan catatan · 5 tag |

Tag selalu diawali `korea`, lalu nama modul, kategori, dan tahap. Contoh:
`korea kosakata 음식 tahap4`. Dengan begitu Anda bisa membuat deck tersaring
(filtered deck) per modul atau per tahap.

## Cara impor

1. Di Anki: **File → Import**, pilih berkasnya.
2. Pastikan tipe catatan punya kolom sebanyak yang tertera di tabel di atas.
3. Pastikan "Allow HTML in fields" **mati** (sudah diatur oleh baris pengarah).
4. Pilih deck tujuan, lalu impor.

## Peringatan

Bila Anda memakai Anki, pakailah penjadwalan Anki dan **jangan** menjalankan
`quiz.py` untuk materi yang sama. `progress.json` dan koleksi Anki tidak saling
tahu, sehingga satu kartu akan dijadwalkan oleh dua sistem sekaligus dan
keduanya menjadi tidak berguna.

Font: pastikan Anki memakai font yang memuat Hangeul (misalnya Noto Sans KR
atau Malgun Gothic). Di Windows biasanya sudah tersedia.
