import time
import threading
import requests
from curl_cffi import requests as cffi_requests

# ==========================================
# KONFIGURASI BOT
# ==========================================
EXCLUSIVE_URL = "https://jkt48.com/purchase/exclusive?code=EX5B99"
API_URL = "https://jkt48.com/api/v1/exclusives/EX5B99/bonus?lang=id"
LOGO_URL = "https://jkt48.com/images/ogp.png"

CHECK_INTERVAL = 15
HOURLY_INTERVAL = 3600

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1551816204765757461/ZbVmJs9XuXkqmoG228EMPDaeShlCJJejftwY_DA1BL0OlW6HlL1U-flp76DK28eL3JbB"
SPECIAL_TARGETS = ["Michelle Alexandra", "Aurhel Alana", "Grace Octaviani"]

COLOR_GREEN = 0x2ECC71
COLOR_RED = 0xE74C3C
COLOR_GOLD = 0xF1C40F
COLOR_BLUE = 0x3498DB
COLOR_PURPLE = 0x9B59B6

def send_discord_embed(title, color, description=None, fields=None, content_text=None, thumbnail_url=LOGO_URL):
    if not DISCORD_WEBHOOK_URL: 
        return

    embed = {
        "title": title,
        "color": color,
        "author": {
            "name": "JKT48 2-Shot Ticket Monitor",
            "icon_url": "https://pbs.twimg.com/profile_images/2006409916005888001/g2dVU5_E_400x400.jpg"
        },
        "footer": {
            "text": "JKT48 Official Event Monitor • Real-time Notification"
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    if description:
        embed["description"] = description
    if fields:
        embed["fields"] = fields
    if thumbnail_url:
        embed["thumbnail"] = {"url": thumbnail_url}

    payload = {}
    if content_text:
        payload["content"] = content_text
    payload["embeds"] = [embed]

    def send():
        try:
            requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        except Exception as e:
            print(f"Error webhook: {e}")

    threading.Thread(target=send).start()

def fetch_api():
    try:
        r = cffi_requests.get(API_URL, impersonate="chrome", timeout=15)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"Error fetch API: {e}")
    return None

def parse_api_data(response_json):
    parsed_items = []
    if not response_json or not isinstance(response_json, dict): 
        return parsed_items
    
    sessions = response_json.get("data", [])

    for session_obj in sessions:
        if not isinstance(session_obj, dict): 
            continue
        session_name = session_obj.get("label", "-")
        
        for detail in session_obj.get("session_members", []):
            if not isinstance(detail, dict): 
                continue
            
            track = detail.get("label", "-")
            member_name = detail.get("member_name", "Unknown")
            quota = int(detail.get("available_quota", 0))
            detail_code = detail.get("session_detail_code", f"{member_name}_{session_name}_{track}")
            
            parsed_items.append({
                "id": detail_code,
                "name": member_name,
                "session": session_name,
                "track": track,
                "quota": quota
            })
            
    return parsed_items

def main_loop():
    print("Mulai inisiasi bot dan mengambil data API JKT48...\n")
    
    data = None
    while not data:
        data = fetch_api()
        if not data:
            print("⏳ Menunggu data API...")
            time.sleep(5)
            
    members = parse_api_data(data)
    if not members:
        print("❌ Gagal memetakan data. Struktur JSON API mungkin berbeda.")
        return

    prev_state = {m["id"]: m for m in members}
    restocked_this_hour = {}

    print("=== STATUS AWAL SELURUH MEMBER (SANITY CHECK) ===")
    total_quota_available = 0
    special_at_startup = []

    for m in members:
        quota_num = m["quota"]
        total_quota_available += quota_num
        status_text = f"✅ Sisa: {quota_num}" if quota_num > 0 else "❌ Sold Out"
        
        if quota_num > 0 and m["name"] in SPECIAL_TARGETS:
            special_at_startup.append(m)
        
        print(f"[{status_text}] {m['name']} | {m['session']} ({m['track']})")
        
    print("-" * 50)
    print(f"Total Slot Terbaca: {len(members)} | Total Tiket Tersedia: {total_quota_available}")
    print("-" * 50)

    if special_at_startup:
        for sp in special_at_startup:
            fields = [
                {"name": "Nama Member", "value": f"**{sp['name']}**", "inline": True},
                {"name": "Sesi / Jalur", "value": f"`{sp['session']}` • `{sp['track']}`", "inline": True},
                {"name": "Sisa Kuota", "value": f"🎫 **{sp['quota']} Tiket**", "inline": True},
                {"name": "Akses Cepat", "value": f"⚡ [**KLIK DI SINI UNTUK BELI SEKARANG**]({EXCLUSIVE_URL})", "inline": False}
            ]
            send_discord_embed(
                title="🌟 STARTUP SPECIAL OSHI ALERT",
                color=COLOR_GOLD,
                fields=fields,
                content_text="@everyone **Target Oshi kamu tersedia sejak bot aktif!**"
            )

    available_list = [m for m in members if m["quota"] > 0]
    if available_list:
        lines = [f"• **{m['name']}** — `{m['session']}` | `{m['track']}` (Sisa: **{m['quota']}**)" for m in available_list]
        chunk_str = "\n".join(lines[:20])
        if len(lines) > 20:
            chunk_str += f"\n\n*...dan {len(lines) - 20} slot lainnya.*"

        fields = [
            {"name": "Ringkasan Sistem", "value": f"Total Slot Terbuka: **{len(available_list)}**\nTotal Tiket: **{total_quota_available} Tiket**", "inline": False},
            {"name": "Daftar Slot Tersedia", "value": chunk_str, "inline": False},
            {"name": "Tautan Pembelian", "value": f"🔗 [**Buka Halaman Event JKT48**]({EXCLUSIVE_URL})", "inline": False}
        ]
        send_discord_embed(title="🚀 STATUS AWAL 2-SHOT JKT48", color=COLOR_GREEN, fields=fields)
    else:
        send_discord_embed(
            title="🚀 STATUS AWAL 2-SHOT JKT48", color=COLOR_RED,
            description="❌ Saat ini seluruh slot tercatat **Sold Out**.\nBot akan terus memantau penambahan tiket secara real-time."
        )

    print(f"\nMemasuki fase pemantauan. Mengecek restock setiap {CHECK_INTERVAL} detik...")
    last_recap_time = time.time()

    while True:
        time.sleep(CHECK_INTERVAL)
        
        data = fetch_api()
        if not data: 
            continue
        
        curr_members = parse_api_data(data)
        if not curr_members: 
            continue
        
        curr_state = {m["id"]: m for m in curr_members}
        
        for uid, curr_item in curr_state.items():
            prev_item = prev_state.get(uid)
            
            if prev_item is not None:
                prev_q = prev_item["quota"]
                curr_q = curr_item["quota"]

                if curr_q > prev_q:
                    added_qty = curr_q - prev_q
                    restocked_this_hour[uid] = added_qty

                    fields = [
                        {"name": "Nama Member", "value": f"**{curr_item['name']}**", "inline": True},
                        {"name": "Sesi / Jalur", "value": f"`{curr_item['session']}` • `{curr_item['track']}`", "inline": True},
                        {"name": "\u200B", "value": "\u200B", "inline": True},
                        {"name": "Penambahan Stok", "value": f"📈 **+{added_qty} Tiket Baru**", "inline": True},
                        {"name": "Sisa Kuota Total", "value": f"🎫 **{curr_q} Tiket** Tersedia", "inline": True},
                        {"name": "Langkah Cepat", "value": f"⚡ [**KLIK DI SINI UNTUK LANGSUNG BELI**]({EXCLUSIVE_URL})", "inline": False}
                    ]

                    if curr_item["name"] in SPECIAL_TARGETS:
                        print(f"[{time.strftime('%H:%M:%S')}] 🌟🎉 SPECIAL RESTOCK: {curr_item['name']} (+{added_qty} Tiket | Total: {curr_q})")
                        send_discord_embed(
                            title="🌟🚨 SPECIAL OSHI RESTOCK ALERT! 🚨🌟",
                            color=COLOR_GOLD, fields=fields, content_text="@everyone **OSHI KAMU BARU SAJA RESTOCK!**"
                        )
                    else:
                        print(f"[{time.strftime('%H:%M:%S')}] 🎉 RESTOCK: {curr_item['name']} (+{added_qty} Tiket | Total: {curr_q})")
                        send_discord_embed(title="🚨 TICKET RESTOCK DETECTED", color=COLOR_BLUE, fields=fields)

        if time.time() - last_recap_time >= HOURLY_INTERVAL:
            print(f"[{time.strftime('%H:%M:%S')}] 📊 Mengirim rekap 1 jam...")
            available_recap = [m for m in curr_members if m["quota"] > 0]
            
            if available_recap:
                lines = []
                for m in available_recap:
                    if m["id"] in restocked_this_hour:
                        added_amt = restocked_this_hour[m["id"]]
                        lines.append(f"• **{m['name']}** — `{m['session']}` | `{m['track']}` — Sisa: **{m['quota']}** 📈 `[+{added_amt} Stok Masuk]`")
                    else:
                        lines.append(f"• **{m['name']}** — `{m['session']}` | `{m['track']}` — Sisa: **{m['quota']}**")

                content_body = "\n".join(lines[:25])
                if len(lines) > 25:
                    content_body += f"\n\n*...dan {len(lines) - 25} slot lainnya.*"

                fields = [
                    {"name": "Daftar Slot Aktif", "value": content_body, "inline": False},
                    {"name": "Beli Tiket", "value": f"🔗 [**Halaman Pembelian Official**]({EXCLUSIVE_URL})", "inline": False}
                ]
                send_discord_embed(title="📊 REKAP KETERSEDIAAN TIKET (1 JAM)", color=COLOR_PURPLE, fields=fields)
            else:
                send_discord_embed(
                    title="📊 REKAP KETERSEDIAAN TIKET (1 JAM)", color=COLOR_RED,
                    description="❌ Saat ini seluruh kuota tiket dalam kondisi **Sold Out**."
                )

            last_recap_time = time.time()
            restocked_this_hour.clear()

        prev_state = curr_state

if __name__ == "__main__":
    main_loop()