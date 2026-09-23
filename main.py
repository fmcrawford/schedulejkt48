import os
import datetime
import json
import requests

# Ambil Webhook URL dari Environment Variables Cloud
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
SENT_SHOWS_FILE = "sent_shows.json"

def load_sent_shows():
    """Membaca daftar ID show yang sudah pernah dinotifikasi agar tidak spam."""
    if os.path.exists(SENT_SHOWS_FILE):
        try:
            with open(SENT_SHOWS_FILE, "r") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_sent_shows(sent_shows):
    """Menyimpan daftar ID show yang sudah dinotifikasi."""
    with open(SENT_SHOWS_FILE, "w") as f:
        json.dump(list(sent_shows), f, indent=2)

def send_discord_notification(show, members_found, ref_code, detail_data):
    """Mengirim pesan notifikasi berformat Embed ke Discord."""
    if not DISCORD_WEBHOOK_URL:
        print("❌ Error: DISCORD_WEBHOOK_URL belum diatur!")
        return

    title = show.get("title", "Theater Show")
    date_str = show.get("date")
    start_time = show.get("start_time", "-")
    end_time = show.get("end_time", "-")
    schedule_id = show.get("schedule_id")
    member_type = show.get("jkt48_member_type", "SHOW")
    
    oshi_str = " & ".join(members_found)
    show_url = f"https://jkt48.com/theater/schedule/id/{schedule_id}"
    
    # Ambil seluruh daftar member line-up
    all_members = [m["name"] for m in detail_data.get("jkt48_member", [])]
    member_list_text = ", ".join(all_members) if all_members else "Belum ada informasi"

    # Discord Embed Card
    embed = {
        "title": f"🎭 {title}",
        "description": f"✨ **Oshi Kamu Tampil!** ({oshi_str})",
        "url": show_url,
        "color": 0xFF69B4, # Warna Pink Hot
        "fields": [
            {
                "name": "📅 Tanggal Pertunjukan",
                "value": f"`{date_str}`",
                "inline": True
            },
            {
                "name": "⏰ Jam",
                "value": f"`{start_time} - {end_time} WIB`",
                "inline": True
            },
            {
                "name": "🏷️ Kategori",
                "value": f"`{member_type}`",
                "inline": True
            },
            {
                "name": "👥 Member Tampil (Line-up)",
                "value": member_list_text[:1000], # Batas karakter Discord field
                "inline": False
            }
        ],
        "footer": {
            "text": f"JKT48 Schedule Bot • Ref Code: {ref_code}"
        },
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

    payload = {
        "content": "📢 **ALERT JADWAL OSHI TERDETEKSI!** @everyone",
        "embeds": [embed]
    }

    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    if response.status_code in [200, 204]:
        print(f"✅ Notifikasi berhasil dikirim ke Discord untuk Show ID: {schedule_id}")
    else:
        print(f"❌ Gagal mengirim notifikasi: {response.status_code} - {response.text}")

def check_schedules():
    sent_shows = load_sent_shows()
    now = datetime.datetime.now()
    
    # Cek bulan ini dan bulan depan (jika mendekati akhir bulan)
    months_to_check = [(now.month, now.year)]
    if now.day > 20:
        next_month = 1 if now.month == 12 else now.month + 1
        next_year = now.year + 1 if now.month == 12 else now.year
        months_to_check.append((next_month, next_year))

    for month, year in months_to_check:
        url = f"https://jkt48.com/api/v1/schedules?lang=id&month={month}&year={year}"
        try:
            res = requests.get(url, timeout=10)
            data = res.json()
            
            if not data.get("status"):
                continue

            schedules = data.get("data", [])
            for show in schedules:
                if show.get("type") != "SHOW":
                    continue

                show_id = str(show.get("schedule_id"))
                ref_code = show.get("reference_code")

                # Skip jika sudah pernah dinotifikasi atau tidak ada ref_code
                if show_id in sent_shows or not ref_code:
                    continue

                show_date_str = show.get("date")
                if not show_date_str:
                    continue

                show_date = datetime.datetime.strptime(show_date_str, "%Y-%m-%d").date()
                
                # Cek jadwal dari hari ini hingga 14 hari ke depan
                if now.date() <= show_date <= now.date() + datetime.timedelta(days=14):
                    detail_url = f"https://jkt48.com/api/v1/theater-shows/{ref_code}?lang=id"
                    detail_res = requests.get(detail_url, timeout=10)
                    detail_data = detail_res.json()

                    if detail_data.get("status") and "data" in detail_data:
                        members = detail_data["data"].get("jkt48_member", [])
                        member_names = [m["name"] for m in members]

                        found = []
                        if "Grace Octaviani" in member_names:
                            found.append("Gracie 🦖")
                        if "Michelle Alexandra" in member_names:
                            found.append("Michie 🐰")

                        if found:
                            send_discord_notification(show, found, ref_code, detail_data["data"])
                            sent_shows.add(show_id)

        except Exception as e:
            print(f"Error fetching schedule: {e}")

    save_sent_shows(sent_shows)

if __name__ == "__main__":
    check_schedules()
