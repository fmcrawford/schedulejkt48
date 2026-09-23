import os
import datetime
import json
from curl_cffi import requests

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
SENT_SHOWS_FILE = "sent_shows.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://jkt48.com/"
}

def load_sent_shows():
    if os.path.exists(SENT_SHOWS_FILE):
        try:
            with open(SENT_SHOWS_FILE, "r") as f:
                return set(json.load(f))
        except Exception as e:
            print(f"⚠️ Gagal membaca {SENT_SHOWS_FILE}: {e}")
            return set()
    return set()

def save_sent_shows(sent_shows):
    try:
        with open(SENT_SHOWS_FILE, "w") as f:
            json.dump(list(sent_shows), f, indent=2)
    except Exception as e:
        print(f"⚠️ Gagal menyimpan {SENT_SHOWS_FILE}: {e}")

def send_discord_status(message):
    if not DISCORD_WEBHOOK_URL:
        print("❌ WARNING: DISCORD_WEBHOOK_URL belum diset di GitHub Secrets!")
        return

    payload = {
        "embeds": [{
            "title": "🔍 JKT48 Oshi Checker Active",
            "description": message,
            "color": 0x3498DB,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }]
    }
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload, impersonate="chrome")
    except Exception as e:
        print(f"❌ Gagal mengirim status ke Discord: {e}")

def send_discord_notification(show, members_found, ref_code, detail_data):
    if not DISCORD_WEBHOOK_URL:
        print("❌ WARNING: DISCORD_WEBHOOK_URL belum diset di GitHub Secrets!")
        return

    title = show.get("title", "Theater Show")
    date_str = show.get("date")
    start_time = show.get("start_time", "-")
    end_time = show.get("end_time", "-")
    schedule_id = show.get("schedule_id")
    member_type = show.get("jkt48_member_type", "SHOW")
    
    oshi_str = " & ".join(members_found)
    show_url = f"https://jkt48.com/theater/schedule/id/{schedule_id}"
    
    all_members = [m["name"] for m in detail_data.get("jkt48_member", [])]
    member_list_text = ", ".join(all_members) if all_members else "Belum ada informasi"

    embed = {
        "title": f"🎭 {title}",
        "description": f"✨ **Oshi Kamu Tampil!** ({oshi_str})",
        "url": show_url,
        "color": 0xFF69B4,
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
                "value": member_list_text[:1000],
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

    try:
        res = requests.post(DISCORD_WEBHOOK_URL, json=payload, impersonate="chrome")
        if res.status_code in [200, 204]:
            print(f"✅ Notifikasi dikirim ke Discord untuk Show ID: {schedule_id}")
        else:
            print(f"❌ Gagal kirim notifikasi Discord: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"❌ Exception saat kirim notifikasi: {e}")

def check_schedules():
    if not DISCORD_WEBHOOK_URL:
        print("❌ CRITICAL ERROR: Secret 'DISCORD_WEBHOOK_URL' tidak ditemukan di GitHub Actions Settings!")
        return

    sent_shows = load_sent_shows()
    now = datetime.datetime.now()
    
    print("🚀 Memulai pemeriksaan jadwal JKT48...")
    send_discord_status(f"Mulai mengecek API JKT48 untuk periode `{now.strftime('%d %B %Y')}` hingga 14 hari ke depan...")

    months_to_check = [(now.month, now.year)]
    if now.day > 20:
        next_month = 1 if now.month == 12 else now.month + 1
        next_year = now.year + 1 if now.month == 12 else now.year
        months_to_check.append((next_month, next_year))

    found_any = False
    scanned_shows_count = 0

    for month, year in months_to_check:
        url = f"https://jkt48.com/api/v1/schedules?lang=id&month={month}&year={year}"
        try:
            res = requests.get(url, headers=HEADERS, impersonate="chrome", timeout=15)
            
            if res.status_code != 200:
                print(f"⚠️ Gagal akses API bulanan (Status Code: {res.status_code})")
                continue

            data = res.json()
            if not data.get("status"):
                continue

            schedules = data.get("data", [])
            for show in schedules:
                if show.get("type") != "SHOW":
                    continue

                show_id = str(show.get("schedule_id"))
                ref_code = show.get("reference_code")
                show_date_str = show.get("date")

                if not ref_code or not show_date_str:
                    continue

                show_date = datetime.datetime.strptime(show_date_str, "%Y-%m-%d").date()
                
                if now.date() <= show_date <= now.date() + datetime.timedelta(days=14):
                    scanned_shows_count += 1
                    
                    detail_url = f"https://jkt48.com/api/v1/theater-shows/{ref_code}?lang=id"
                    detail_res = requests.get(detail_url, headers=HEADERS, impersonate="chrome", timeout=15)
                    
                    if detail_res.status_code != 200:
                        continue

                    detail_data = detail_res.json()

                    if detail_data.get("status") and "data" in detail_data:
                        members = detail_data["data"].get("jkt48_member", [])
                        
                        found = []
                        for m in members:
                            m_name = m.get("name", "").lower()
                            if "grace octaviani" in m_name or "gracie" in m_name:
                                if "Gracie 🦖" not in found:
                                    found.append("Gracie 🦖")
                            if "michelle alexandra" in m_name or "michie" in m_name:
                                if "Michie 🐰" not in found:
                                    found.append("Michie 🐰")

                        if found:
                            found_any = True
                            print(f"🎯 Ditemukan Oshi ({', '.join(found)}) pada show: {show.get('title')} ({show_date_str})")
                            
                            if show_id not in sent_shows:
                                send_discord_notification(show, found, ref_code, detail_data["data"])
                                sent_shows.add(show_id)
                            else:
                                print(f"ℹ️ Show ID {show_id} sudah pernah dinotifikasi sebelumnya.")

        except Exception as e:
            print(f"❌ Terjadi kesalahan pada proses scan: {e}")

    save_sent_shows(sent_shows)
    
    print(f"📊 Selesai memindai {scanned_shows_count} show pertunjukan.")
    if not found_any:
        print("ℹ️ Tidak ada jadwal Gracie atau Michie yang ditemukan untuk 14 hari ke depan.")

if __name__ == "__main__":
    check_schedules()
