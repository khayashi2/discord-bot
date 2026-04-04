/**
 * User stats page: Tom Select initialization and dynamic chart rendering.
 *
 * When a user is selected from the dropdown, their stats are fetched
 * from /api/user/{id} and rendered as charts + emoji list.
 */

/* Shared color palette (duplicated from dashboard.js to avoid extra request) */
const COLORS = {
    accent: "#e94560",
    accentAlt: "#533483",
    blue: "#0f3460",
    grid: "rgba(255, 255, 255, 0.08)",
    text: "#aaa",
    bars: [
        "#e94560", "#533483", "#0f3460", "#00b4d8", "#90be6d",
        "#f9c74f", "#f8961e", "#f3722c", "#577590", "#43aa8b",
    ],
};

/* Chart.js global defaults for dark theme */
Chart.defaults.color = COLORS.text;
Chart.defaults.borderColor = COLORS.grid;
Chart.defaults.plugins.legend.display = false;

function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
}

/* Track chart instances for cleanup on user switch */
const charts = {};

function destroyChart(key) {
    if (charts[key]) {
        charts[key].destroy();
        charts[key] = null;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const select = new TomSelect("#user-select", {
        allowEmptyOption: true,
        placeholder: "Search for a user...",
    });

    select.on("change", async (value) => {
        if (!value) {
            document.getElementById("user-stats").style.display = "none";
            document.getElementById("user-empty").style.display = "block";
            return;
        }

        try {
            const resp = await fetch(`/api/user/${value}`);
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const data = await resp.json();
            renderUserStats(data);
        } catch (err) {
            console.error("Failed to load user stats:", err);
        }
    });
});

function renderUserStats(data) {
    document.getElementById("user-stats").style.display = "block";
    document.getElementById("user-empty").style.display = "none";

    /* Overview stats */
    document.getElementById("user-msg-count").textContent = data.message_count.toLocaleString();
    document.getElementById("user-total-emoji").textContent = (data.emoji_stats?.total_emoji || 0).toLocaleString();

    renderUserActivity(data.activity || []);
    renderUserWords(data.top_words || []);
    renderUserProfanity(data.profanity_words || []);
    renderUserEmoji(data.emoji_stats?.top_emoji || []);
}

function renderUserActivity(data) {
    destroyChart("activity");
    const canvas = document.getElementById("userActivityChart");
    const empty = document.getElementById("userActivityEmpty");
    if (data.length) {
        canvas.style.display = "block";
        empty.style.display = "none";
        charts.activity = new Chart(canvas, {
            type: "line",
            data: {
                labels: data.map(d => d.day),
                datasets: [{
                    data: data.map(d => d.count),
                    borderColor: COLORS.accent,
                    backgroundColor: "rgba(233, 69, 96, 0.1)",
                    fill: true,
                    tension: 0.3,
                    pointRadius: 2,
                }],
            },
            options: {
                scales: {
                    x: { grid: { display: false }, ticks: { maxTicksLimit: 10 } },
                    y: {
                        beginAtZero: true,
                        grid: { color: COLORS.grid },
                        title: { display: true, text: "Messages per Day", color: COLORS.text },
                    },
                },
            },
        });
    } else {
        canvas.style.display = "none";
        empty.style.display = "block";
    }
}

function renderUserWords(data) {
    destroyChart("words");
    const canvas = document.getElementById("userWordsChart");
    const empty = document.getElementById("userWordsEmpty");
    if (data.length) {
        canvas.style.display = "block";
        empty.style.display = "none";
        charts.words = new Chart(canvas, {
            type: "bar",
            data: {
                labels: data.map(d => d.word),
                datasets: [{
                    data: data.map(d => d.count),
                    backgroundColor: COLORS.accentAlt,
                    borderRadius: 4,
                }],
            },
            options: {
                scales: {
                    x: { grid: { display: false }, ticks: { maxRotation: 45 } },
                    y: {
                        beginAtZero: true,
                        grid: { color: COLORS.grid },
                        title: { display: true, text: "Occurrences", color: COLORS.text },
                    },
                },
            },
        });
    } else {
        canvas.style.display = "none";
        empty.style.display = "block";
    }
}

function renderUserProfanity(data) {
    const container = document.getElementById("userProfanityList");
    const empty = document.getElementById("userProfanityEmpty");
    if (data.length) {
        container.style.display = "flex";
        empty.style.display = "none";
        container.innerHTML = data.map(d =>
            `<div class="emoji-item"><span>${escapeHtml(d.word)}</span><span class="emoji-count">&times;${d.count}</span></div>`
        ).join("");
    } else {
        container.style.display = "none";
        empty.style.display = "block";
    }
}

function renderUserEmoji(data) {
    const container = document.getElementById("userEmojiList");
    const empty = document.getElementById("userEmojiEmpty");
    if (data.length) {
        container.style.display = "flex";
        empty.style.display = "none";
        container.innerHTML = data.map(e =>
            `<div class="emoji-item"><span>${escapeHtml(e.emoji)}</span><span class="emoji-count">&times;${e.count}</span></div>`
        ).join("");
    } else {
        container.style.display = "none";
        empty.style.display = "block";
    }
}
