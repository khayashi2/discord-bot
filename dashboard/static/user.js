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
let currentUserData = null;
let userCustomChartInstance = null;
let userCustomTomSelect = null;

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

    /* Init custom view block */
    initUserCustomBlock();

    /* Range switching helper — syncs both original and sticky buttons */
    function switchRange(range) {
        document.querySelectorAll("#user-range-picker button, #sticky-user-range button").forEach(b => {
            b.classList.toggle("active", b.dataset.range === range);
        });
        currentRange = range;
    }

    /* Range picker buttons (original) */
    document.querySelectorAll("#user-range-picker button").forEach(btn => {
        btn.addEventListener("click", async () => {
            switchRange(btn.dataset.range);
            if (currentUserId) {
                try {
                    await loadUserStats(currentUserId, currentRange);
                } catch (err) {
                    console.error("Failed to load user stats:", err);
                }
            }
        });
    });

    /* Sticky range buttons */
    document.querySelectorAll("#sticky-user-range button").forEach(btn => {
        btn.addEventListener("click", async () => {
            switchRange(btn.dataset.range);
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

    /* Save for custom block */
    currentUserData = data;

    /* Overview stats */
    document.getElementById("user-msg-count").textContent = data.message_count.toLocaleString();
    document.getElementById("user-total-emoji").textContent = (data.emoji_stats?.total_emoji || 0).toLocaleString();

    /* Update activity heading based on selected range */
    document.getElementById("activity-heading").textContent = RANGE_LABELS[currentRange] || "Activity (All Time)";

    renderUserActivity(data.activity || []);

    /* Re-render custom block with new user data */
    let savedViz = localStorage.getItem("user-custom-viz") || "top-words";
    if (!USER_VIZ_REGISTRY[savedViz]) savedViz = "top-words";
    renderUserCustomViz(savedViz);
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

/* ─── User Page Custom View Block ─── */

const USER_VIZ_REGISTRY = {
    "top-words": {
        label: "Top Words",
        dataKey: "top_words",
        type: "canvas",
        render(canvasId, data) {
            const canvas = document.getElementById(canvasId);
            if (!canvas || !data.length) return null;
            return new Chart(canvas, {
                type: "bar",
                data: {
                    labels: data.map(d => d.word),
                    datasets: [{ data: data.map(d => d.count), backgroundColor: COLORS.accentAlt, borderRadius: 4 }],
                },
                options: {
                    scales: {
                        x: { grid: { display: false }, ticks: { maxRotation: 45 } },
                        y: { beginAtZero: true, grid: { color: COLORS.grid } },
                    },
                },
            });
        },
    },
    "peak-hours": {
        label: "Peak Hours",
        dataKey: "peak_hours",
        type: "canvas",
        render(canvasId, data) {
            const canvas = document.getElementById(canvasId);
            if (!canvas || !data.length) return null;
            return new Chart(canvas, {
                type: "bar",
                data: {
                    labels: data.map(d => `${d.hour}:00`),
                    datasets: [{ data: data.map(d => d.count), backgroundColor: COLORS.accent, borderRadius: 4 }],
                },
                options: {
                    scales: {
                        x: { grid: { display: false }, title: { display: true, text: "Hour (Pacific)", color: COLORS.text } },
                        y: { beginAtZero: true, grid: { color: COLORS.grid } },
                    },
                },
            });
        },
    },
    "emoji": {
        label: "Top Emoji",
        dataKey: "emoji_stats",
        type: "html",
        render(containerId, data) {
            const el = document.getElementById(containerId);
            if (!el) return null;
            const emojis = data?.top_emoji || [];
            if (!emojis.length) {
                el.innerHTML = '<p class="empty-state">No emoji data.</p>';
                return null;
            }
            el.innerHTML = emojis.map(e =>
                `<div class="emoji-item"><span>${escapeHtml(e.emoji)}</span><span class="emoji-count">&times;${e.count}</span></div>`
            ).join("");
            el.style.display = "flex";
            el.style.flexWrap = "wrap";
            el.style.gap = "0.75rem";
            return null;
        },
    },
    "profanity": {
        label: "Profanity Words",
        dataKey: "profanity_words",
        type: "html",
        render(containerId, data) {
            const el = document.getElementById(containerId);
            if (!el) return null;
            if (!data || !data.length) {
                el.innerHTML = '<p class="empty-state">No profanity data.</p>';
                return null;
            }
            el.innerHTML = data.map(d =>
                `<div class="emoji-item"><span>${escapeHtml(d.word)}</span><span class="emoji-count">&times;${d.count}</span></div>`
            ).join("");
            el.style.display = "flex";
            el.style.flexWrap = "wrap";
            el.style.gap = "0.75rem";
            return null;
        },
    },
    "catchphrases": {
        label: "Catchphrase Lifespans",
        dataKey: "catchphrases",
        type: "html",
        render(containerId, data) {
            const container = document.getElementById(containerId);
            if (!container) return null;

            /* Destroy any lingering internal chart from a previous render */
            if (container._catchphraseChart) {
                container._catchphraseChart.destroy();
                container._catchphraseChart = null;
            }

            const phrases = data.phrases || [];
            const timelines = data.timelines || {};

            if (!phrases.length) {
                container.innerHTML = '<p class="empty-state">No catchphrases detected yet.</p>';
                return null;
            }

            const statusColors = { rising: "#90be6d", peaked: "#f9c74f", dead: "#666" };

            const grid = document.createElement("div");
            grid.style.cssText = "display:grid; grid-template-columns:repeat(auto-fill, minmax(220px, 1fr)); gap:0.75rem; margin-bottom:1rem;";

            const chartWrapper = document.createElement("div");
            chartWrapper.style.display = "none";
            const canvas = document.createElement("canvas");
            canvas.id = containerId + "-timeline";
            chartWrapper.appendChild(canvas);

            for (const p of phrases) {
                const card = document.createElement("div");
                card.style.cssText = "background:var(--bg-card, #1a1a2e); border-radius:8px; padding:0.75rem; cursor:pointer; border:2px solid transparent; transition:border-color 0.2s;";
                const safeStatus = escapeHtml(p.status);
                card.innerHTML =
                    `<div style="font-weight:700; font-size:0.95rem; margin-bottom:0.3rem;">\u201c${escapeHtml(p.phrase)}\u201d</div>` +
                    `<span style="display:inline-block; padding:0.15rem 0.5rem; border-radius:4px; font-size:0.7rem; font-weight:600; color:#fff; background:${statusColors[p.status] || "#666"};">${safeStatus}</span>` +
                    `<div style="font-size:0.8rem; color:var(--text-secondary, #aaa); margin-top:0.4rem;">${p.total_uses} uses</div>` +
                    `<div style="font-size:0.75rem; color:var(--text-secondary, #aaa);">${p.first_seen} \u2192 ${p.last_seen}</div>`;

                card.addEventListener("click", () => {
                    grid.querySelectorAll(":scope > div").forEach(c => { c.style.borderColor = "transparent"; });
                    card.style.borderColor = COLORS.accent;

                    const timeline = timelines[p.phrase] || [];
                    chartWrapper.style.display = "block";

                    if (container._catchphraseChart) container._catchphraseChart.destroy();
                    container._catchphraseChart = new Chart(canvas, {
                        type: "line",
                        data: {
                            labels: timeline.map(t => t.week),
                            datasets: [{
                                label: `\u201c${p.phrase}\u201d`,
                                data: timeline.map(t => t.count),
                                borderColor: COLORS.accent,
                                backgroundColor: "rgba(233, 69, 96, 0.1)",
                                fill: true,
                                tension: 0.3,
                                pointRadius: 3,
                            }],
                        },
                        options: {
                            plugins: { legend: { display: true, labels: { color: COLORS.text } } },
                            scales: {
                                x: { grid: { display: false }, title: { display: true, text: "Week", color: COLORS.text } },
                                y: { beginAtZero: true, grid: { color: COLORS.grid }, title: { display: true, text: "Uses", color: COLORS.text } },
                            },
                        },
                    });
                });

                grid.appendChild(card);
            }

            container.appendChild(grid);
            container.appendChild(chartWrapper);
            return null;
        },
    },
    "brainrot": {
        label: "Brainrot Stats",
        dataKey: "brainrot_stats",
        type: "html",
        render(containerId, data) {
            const el = document.getElementById(containerId);
            if (!el) return null;

            const terms = data?.top_terms || [];
            const copypasta = data?.repeated_msg_count || 0;
            const totalHits = data?.total_keyword_hits || 0;

            if (!terms.length && copypasta === 0 && totalHits === 0) {
                el.innerHTML = '<p class="empty-state">No brainrot data.</p>';
                return null;
            }

            let html = "";

            /* Summary stat cards */
            html += '<div style="display:flex; gap:1rem; margin-bottom:1rem;">';
            html += `<div style="flex:1; background:var(--bg-card, #1a1a2e); border-radius:8px; padding:0.75rem; text-align:center;">
                <div style="font-size:1.4rem; font-weight:700; color:#e94560;">${totalHits}</div>
                <div style="font-size:0.8rem; color:var(--text-secondary, #aaa);">Keyword Hits</div>
            </div>`;
            html += `<div style="flex:1; background:var(--bg-card, #1a1a2e); border-radius:8px; padding:0.75rem; text-align:center;">
                <div style="font-size:1.4rem; font-weight:700; color:#533483;">${copypasta}</div>
                <div style="font-size:0.8rem; color:var(--text-secondary, #aaa);">Repeated Messages</div>
            </div>`;
            html += "</div>";

            /* Term badges */
            if (terms.length) {
                html += '<div style="display:flex; flex-wrap:wrap; gap:0.75rem;">';
                html += terms.map(d =>
                    `<div class="emoji-item"><span>${escapeHtml(d.term)}</span><span class="emoji-count">&times;${d.count}</span></div>`
                ).join("");
                html += "</div>";
            }

            el.innerHTML = html;
            return null;
        },
    },
};

function initUserCustomBlock() {
    const selectEl = document.getElementById("user-custom-viz-select");
    const container = document.getElementById("user-custom-viz-container");
    const heading = document.getElementById("user-custom-block-heading");
    if (!selectEl || !container) return;

    for (const [key, viz] of Object.entries(USER_VIZ_REGISTRY)) {
        const opt = document.createElement("option");
        opt.value = key;
        opt.textContent = viz.label;
        selectEl.appendChild(opt);
    }

    userCustomTomSelect = new TomSelect(selectEl, {
        allowEmptyOption: true,
        placeholder: "Choose a visualization...",
    });

    let saved = localStorage.getItem("user-custom-viz") || "top-words";
    if (!USER_VIZ_REGISTRY[saved]) saved = "top-words";
    userCustomTomSelect.setValue(saved, true);
    renderUserCustomViz(saved);
    if (heading && USER_VIZ_REGISTRY[saved]) heading.textContent = USER_VIZ_REGISTRY[saved].label;

    userCustomTomSelect.on("change", (value) => {
        if (!value) {
            if (heading) heading.textContent = "Custom View";
            return;
        }
        localStorage.setItem("user-custom-viz", value);
        renderUserCustomViz(value, container);
        if (heading && USER_VIZ_REGISTRY[value]) heading.textContent = USER_VIZ_REGISTRY[value].label;
    });
}

function renderUserCustomViz(key, container) {
    if (!container) container = document.getElementById("user-custom-viz-container");
    if (!container) return;

    if (userCustomChartInstance) {
        userCustomChartInstance.destroy();
        userCustomChartInstance = null;
    }
    container.innerHTML = "";

    if (!currentUserData) {
        container.innerHTML = '<p class="empty-state">Select a user first.</p>';
        return;
    }

    const viz = USER_VIZ_REGISTRY[key];
    if (!viz) return;

    const data = currentUserData[viz.dataKey];
    if (!data || (Array.isArray(data) && data.length === 0)) {
        container.innerHTML = '<p class="empty-state">No data available for this visualization.</p>';
        return;
    }

    const elId = "user-custom-viz-" + key;
    if (viz.type === "canvas") {
        const canvas = document.createElement("canvas");
        canvas.id = elId;
        container.appendChild(canvas);
        userCustomChartInstance = viz.render(elId, data);
    } else {
        const div = document.createElement("div");
        div.id = elId;
        container.appendChild(div);
        viz.render(elId, data);
    }
}
