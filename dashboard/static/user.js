/**
 * User stats page: Tom Select initialization and dynamic chart rendering.
 *
 * When a user is selected from the dropdown, their stats are fetched
 * from /api/user/{id} and rendered as a bar chart + emoji list.
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

let userWordsChart = null;

document.addEventListener("DOMContentLoaded", () => {
    const select = new TomSelect("#user-select", {
        allowEmptyOption: true,
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
    document.getElementById("user-msg-count").textContent = data.message_count.toLocaleString();

    /* Destroy previous chart instance if it exists */
    if (userWordsChart) {
        userWordsChart.destroy();
        userWordsChart = null;
    }

    /* Render top words bar chart */
    const canvas = document.getElementById("userWordsChart");
    const wordsEmpty = document.getElementById("userWordsEmpty");
    if (data.top_words.length) {
        canvas.style.display = "block";
        wordsEmpty.style.display = "none";
        userWordsChart = new Chart(canvas, {
            type: "bar",
            data: {
                labels: data.top_words.map(d => d.word),
                datasets: [{
                    data: data.top_words.map(d => d.count),
                    backgroundColor: COLORS.accentAlt,
                    borderRadius: 4,
                }],
            },
            options: {
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { maxRotation: 45 },
                    },
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
        wordsEmpty.style.display = "block";
    }

    /* Render top emoji as HTML badges */
    const emojiContainer = document.getElementById("userEmojiList");
    const emojiEmpty = document.getElementById("userEmojiEmpty");
    if (data.top_emoji.length) {
        emojiContainer.style.display = "flex";
        emojiEmpty.style.display = "none";
        emojiContainer.innerHTML = data.top_emoji.map(e =>
            `<div class="emoji-item"><span>${escapeHtml(e.emoji)}</span><span class="emoji-count">&times;${e.count}</span></div>`
        ).join("");
    } else {
        emojiContainer.style.display = "none";
        emojiEmpty.style.display = "block";
    }
}
