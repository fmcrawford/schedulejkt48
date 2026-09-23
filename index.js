// index.js
const WEBHOOK_URL = process.env.DISCORD_WEBHOOK_URL;
const ROLE_ID = process.env.DISCORD_ROLE_ID || ""; // Kosongkan jika tidak ingin mention role tertentu

// Ganti URL ini dengan Endpoint API jadwal yang sesungguhnya
const SCHEDULE_API_URL = "https://api.example.com/jkt48-schedule"; 

async function fetchSchedules() {
    try {
        // Uncomment blok ini saat API sudah siap:
        /*
        const response = await fetch(SCHEDULE_API_URL);
        const apiData = await response.json();
        const schedules = apiData.data;
        */
        
        // --- MOCK DATA SEBAGAI CONTOH ---
        const schedules = [
            {
                schedule_id: 7332,
                date: "2026-09-24",
                start_time: "19:00:00",
                title: "Sambil Menggandeng Erat Tanganku",
                jkt48_member_type: "DREAM"
            }
        ];

        // FILTER: Gracie (Misalnya memfilter berdasarkan setlist/tim)
        const gracieShows = schedules.filter(show => 
            show.jkt48_member_type === "DREAM" || show.title.includes("Pajama Drive")
        );

        if (gracieShows.length === 0) {
            console.log("Belum ada jadwal terbaru untuk Gracie saat ini.");
            return;
        }

        for (const show of gracieShows) {
            await sendToDiscord(show);
        }

    } catch (error) {
        console.error("Gagal mengambil data jadwal:", error);
    }
}

async function sendToDiscord(show) {
    if (!WEBHOOK_URL) {
        console.error("DISCORD_WEBHOOK_URL belum diset! Masukkan ke GitHub Secrets.");
        return;
    }

    const mention = ROLE_ID ? `<@&${ROLE_ID}>\n` : "";
    const detailUrl = `https://jkt48.com/theater/schedule/id/${show.schedule_id}`;

    const payload = {
        content: `${mention}📢 **Jadwal Show Terbaru Gracie JKT48!** 📢\nAyo ramaikan teater dan dukung Gracie!`,
        embeds: [
            {
                title: "🎭 " + show.title,
                color: 16758465, // Pink Color Pastel
                fields: [
                    { name: "🗓️ Tanggal", value: show.date, inline: true },
                    { name: "⏰ Waktu", value: `${show.start_time} WIB`, inline: true },
                    { name: "🎟️ Tiket & Detail", value: `[Klik di sini](${detailUrl})`, inline: false }
                ],
                footer: { text: "JKT48 Theater Schedule Bot" },
                timestamp: new Date().toISOString()
            }
        ]
    };

    try {
        const res = await fetch(WEBHOOK_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            console.log(`Berhasil mengirim jadwal ${show.title} ke Discord!`);
        } else {
            console.error(`Gagal mengirim ke Discord: ${res.status} ${res.statusText}`);
        }
    } catch (error) {
        console.error("Error webhook:", error);
    }
}

fetchSchedules();
