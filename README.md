# Gracie JKT48 Discord Announcer

Bot ini berjalan otomatis menggunakan GitHub Actions untuk mengecek jadwal teater JKT48 dan mengirimkan pengumuman show Grace Octaviani (Gracie) ke Discord server via Webhook.

## Cara Pemasangan di GitHub

1. Buat repository baru di GitHub dan upload semua file dari folder ini.
2. Masuk ke tab **Settings** di repository kamu.
3. Di menu sebelah kiri, buka **Secrets and variables** -> **Actions**.
4. Klik tombol **New repository secret**.
5. Tambahkan dua *secret* berikut:
   - `DISCORD_WEBHOOK_URL` : (Isi dengan URL Webhook dari channel Discord kamu)
   - `DISCORD_ROLE_ID` : (Opsional, isi dengan ID Role Discord jika ingin men-tag role tertentu)
6. Buka tab **Actions** di GitHub, pilih workflow "Gracie Schedule Announcer", lalu klik **Run workflow** untuk mengetesnya secara manual.
