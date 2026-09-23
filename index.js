// index.js
const WEBHOOK_URL = process.env.DISCORD_WEBHOOK_URL;
const ROLE_ID = process.env.DISCORD_ROLE_ID || ""; 

// Target member yang dicari
const TARGET_NAMES = ["Grace Octaviani", "Gracie"];

async function checkGracieShows() {
    try {
        // Ambil bulan dan tahun saat script dijalankan secara dinamis
        const now = new Date();
        const currentMonth = now.getMonth() + 1;
        const currentYear = now.getFullYear();

        // 1. Endpoint List Jadwal
        const scheduleListUrl = `https://jkt48.com/api/v1/schedules?lang=id&month=${currentMonth}&year=${currentYear}`;
        
        console.log(`Mengambil data jadwal dari: ${scheduleListUrl}`);
        const resList = await fetch(scheduleListUrl);
        const resultList = await resList.json();

        if (!resultList.status || !Array.isArray(resultList.data)) {
            console.error("Gagal mengambil daftar jadwal dari API JKT48.");
            return;
        }

        // Filter hanya event bertipe "SHOW" yang memiliki reference_code dan berstatus true
        const shows = resultList.data.filter(item => item.type === "SHOW" && item.reference_code && item.status);
        console.log(`Ditemukan ${shows.length} show bulan ini. Memeriksa detail lineup member...`);

        for (const show of shows) {
            // 2. Endpoint Detail Show menggunakan reference_code
            const detailUrl = `https://jkt48.com/api/v1/theater-shows/${show.reference_code}?lang=id`;

            try {
                const resDetail = await fetch(detailUrl);
                const resultDetail = await resDetail.json();

                if (!resultDetail.status || !resultDetail.data) continue;

                const detailData = resultDetail.data;
                const members = detailData.jkt48_member || [];

                // Cek keberadaan Grace Octaviani / Gracie di lineup
                const isGraciePerforming = members.some(m =>
                    TARGET_NAMES.some(target => m.name.toLowerCase().includes(target.toLowerCase()))
                );

                if (isGraciePerforming) {
                    console.log(`[DITEMUKAN] Gracie tampil di show: ${detailData.title} (${detailData.date})`);
                    await sendToDiscord(detailData, show.schedule_id);
                }
            } catch (err) {
                console.error(`Gagal mengambil detail show ${show.reference_code}:`, err);
            }
        }
    } catch (error) {
        console.error("Gagal memproses API JKT48:", error);
    }
}

async function sendToDiscord(showDetail, scheduleId) {
    if (!WEBHOOK_URL) {
        console.error("DISCORD_WEBHOOK_URL belum diset dalam Secrets GitHub!");
        return;
    }

    const mention = ROLE_ID ? `<@&${ROLE_ID}>\n` : "";
    const detailLink = `https://jkt48.com/theater/schedule/id/${scheduleId}`;
    
    // Susun daftar lineup member yang tampil
    const memberNames = showDetail.jkt48_member.map(m => m.name).join(", ");
    const formattedMemberList = memberNames.length > 1000 
        ? memberNames.substring(0, 997) + "..." 
        : memberNames;

    const payload = {
        content: `${mention}📢 **Jadwal Show Terbaru Gracie JKT48!** 📢\nGrace Octaviani terkonfirmasi tampil di show berikut:`,
        embeds: [
            {
                title: `🎭 ${showDetail.title}`,
                color: 16758465, // Pink Pastel
                fields: [
                    { name: "🗓️ Tanggal", value: showDetail.date, inline: true },
                    { name: "⏰ Waktu", value: `${showDetail.start_time} - ${showDetail.end_time} WIB`, inline: true },
                    { name: "🏷️ Tim / Tipe", value: showDetail.jkt48_member_type || "-", inline: true },
                    { name: "👥 Lineup Member", value: formattedMemberList, inline: false },
                    { name: "🎟️ Detail & Tiket", value: `[Buka Web JKT48](${detailLink})`, inline: false }
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
            console.log(`Berhasil mengirim pengumuman ${showDetail.title} ke Discord.`);
        } else {
            console.error(`Gagal mengirim ke Discord. Status: ${res.status}`);
        }
    } catch (err) {
        console.error("Error Webhook:", err);
    }
}

checkGracieShows();
