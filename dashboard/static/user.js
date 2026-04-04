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
let currentUserId = null;
let currentRange = "";

function destroyChart(key) {
    if (charts[key]) {
        charts[key].destroy();
        charts[key] = null;
    }
}

async function loadUserStats(userId, range) {
    const url = range
        ? `/api/user/${userId}?range=${range}`
        : `/api/user/${userId}`;
    const resp = await fetch(url);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    renderUserStats(data);
}

const RANGE_LABELS = {
    "7d": "Activity (Last 7 Days)",
    "30d": "Activity (Last 30 Days)",
    "90d": "Activity (Last 90 Days)",
    "": "Activity (All Time)",
};

document.addEventListener("DOMContentLoaded", () => {
    const select = new TomSelect("#user-select", {
        allowEmptyOption: true,
        placeholder: "Search for a user...",
    });

    /* Sticky user header */
    const stickyHeader = document.getElementById("sticky-user-header");
    const stickyName = document.getElementById("sticky-user-name");
    const selectorCard = document.getElementById("user-selector-card");

    const observer = new IntersectionObserver(
        ([entry]) => {
            if (!entry.isIntersecting && currentUserId) {
                stickyHeader.classList.add("visible");
            } else {
                stickyHeader.classList.remove("visible");
            }
        },
        { threshold: 0 }
    );
    observer.observe(selectorCard);

    select.on("change", async (value) => {
        if (!value) {
            currentUserId = null;
            document.getElementById("user-stats").style.display = "none";
            document.getElementById("user-empty").style.display = "block";
            document.getElementById("user-display-name").textContent = "--";
            stickyHeader.classList.remove("visible");
            return;
        }

        currentUserId = value;
        const option = select.options[value];
        const displayName = option ? option.text : "--";
        document.getElementById("user-display-name").textContent = displayName;
        stickyName.textContent = displayName;

        try {
            await loadUserStats(value, currentRange);
        } catch (err) {
            console.error("Failed to load user stats:", err);
        }
    });

    /* Range picker buttons */
    document.querySelectorAll("#user-range-picker button").forEach(btn => {
        btn.addEventListener("click", async () => {
            document.querySelectorAll("#user-range-picker button").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            currentRange = btn.dataset.range;
            if (currentUserId) {
                try {
                    await loadUserStats(currentUserId, currentRange);
                } catch (err) {
                    console.error("Failed to load user stats:", err);
                }
            }
        });
    });
});

function renderUserStats(data) {
    document.getElementById("user-stats").style.display = "block";
    document.getElementById("user-empty").style.display = "none";

    /* Overview stats */
    document.getElementById("user-msg-count").textContent = data.message_count.toLocaleString();
    document.getElementById("user-total-emoji").textContent = (data.emoji_stats?.total_emoji || 0).toLocaleString();

    /* Update activity heading based on selected range */
    document.getElementById("activity-heading").textContent = RANGE_LABELS[currentRange] || "Activity (All Time)";

    renderUserActivity(data.activity || []);
    renderUserWords(data.top_words || []);
    renderUserProfanity(data.profanity_words || []);
    renderUserEmoji(data.emoji_stats?.top_emoji || []);
    renderUserPeakHours(data.peak_hours || []);
    renderUserVocabulary(data.vocabulary || { ttr: 0, unique_words: 0, total_words: 0 });
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

function renderUserPeakHours(data) {
    destroyChart("peakHours");
    const canvas = document.getElementById("userPeakHoursChart");
    const empty = document.getElementById("userPeakHoursEmpty");
    if (data.length) {
        canvas.style.display = "block";
        empty.style.display = "none";
        charts.peakHours = new Chart(canvas, {
            type: "bar",
            data: {
                labels: data.map(d => `${d.hour}:00`),
                datasets: [{
                    data: data.map(d => d.count),
                    backgroundColor: COLORS.accent,
                    borderRadius: 4,
                }],
            },
            options: {
                scales: {
                    x: {
                        grid: { display: false },
                        title: { display: true, text: "Hour (Pacific)", color: COLORS.text },
                    },
                    y: {
                        beginAtZero: true,
                        grid: { color: COLORS.grid },
                        title: { display: true, text: "Messages", color: COLORS.text },
                    },
                },
            },
        });
    } else {
        canvas.style.display = "none";
        empty.style.display = "block";
    }
}

function renderUserVocabulary(data) {
    const statsEl = document.getElementById("userVocabStats");
    const empty = document.getElementById("userVocabEmpty");
    if (data.total_words > 0) {
        statsEl.style.display = "grid";
        empty.style.display = "none";
        document.getElementById("user-ttr").textContent = data.ttr.toFixed(3);
        document.getElementById("user-unique-words").textContent = data.unique_words.toLocaleString();
        document.getElementById("user-total-words").textContent = data.total_words.toLocaleString();
    } else {
        statsEl.style.display = "none";
        empty.style.display = "block";
    }
}
