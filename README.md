# Gracie JKT48 Discord Announcer

Bot ini berjalan otomatis menggunakan GitHub Actions untuk mengecek jadwal teater JKT48 secara dinamis via API resmi, dan mengirimkan pengumuman show Grace Octaviani (Gracie) ke Discord server via Webhook.

## Cara Pemasangan Secret Key di GitHub

1. Masuk ke tab **Settings** di repository kamu.
2. Di menu sebelah kiri, buka **Secrets and variables** -> **Actions**.
3. Klik tombol **New repository secret**.
4. Tambahkan dua *secret* berikut:
   - `DISCORD_WEBHOOK_URL` : (Isi dengan URL Webhook dari channel Discord kamu)
   - `DISCORD_ROLE_ID` : (Opsional, isi dengan ID Role Discord jika ingin men-tag role tertentu, misalnya: `123456789012345678`)
5. Buka tab **Actions** di GitHub, pilih workflow "Gracie Schedule Announcer", lalu klik **Run workflow** untuk mengetes bot secara manual. Bot otomatis berjalan setiap pukul 12:00 WIB.
