/**
 * Dashboard chart rendering with Chart.js.
 *
 * Data is read from a hidden #chart-data element's data-* attributes,
 * parsed via JSON.parse(), and passed to the render functions below.
 */

/* Shared color palette */
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

/* All parsed data, shared across render functions and the custom block */
let allData = {};

/* Track Chart.js instance in the custom block for cleanup */
let customChartInstance = null;

/**
 * Render a horizontal bar chart for top users.
 */
function renderTopUsers(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !data.length) return null;

    return new Chart(canvas, {
        type: "bar",
        data: {
            labels: data.map(d => d.display_name),
            datasets: [{
                data: data.map(d => d.count),
                backgroundColor: COLORS.bars.slice(0, data.length),
                borderRadius: 4,
            }],
        },
        options: {
            indexAxis: "y",
            scales: {
                x: {
                    grid: { display: false },
                    title: { display: true, text: "Messages Sent", color: COLORS.text },
                },
                y: { grid: { display: false } },
            },
        },
    });
}

/**
 * Render a line chart for daily activity over time.
 */
function renderActivity(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !data.length) return null;

    return new Chart(canvas, {
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
                x: {
                    grid: { display: false },
                    ticks: { maxTicksLimit: 10 },
                },
                y: {
                    beginAtZero: true,
                    grid: { color: COLORS.grid },
                    title: { display: true, text: "Messages per Day", color: COLORS.text },
                },
            },
        },
    });
}

/**
 * Render a vertical bar chart for top words.
 */
function renderTopWords(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !data.length) return null;

    return new Chart(canvas, {
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
}

/**
 * Render a horizontal bar chart for profanity leaderboard.
 */
function renderProfanity(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !data.length) return null;

    return new Chart(canvas, {
        type: "bar",
        data: {
            labels: data.map(d => d.display_name),
            datasets: [{
                data: data.map(d => d.count),
                backgroundColor: COLORS.bars.slice(0, data.length),
                borderRadius: 4,
            }],
        },
        options: {
            indexAxis: "y",
            scales: {
                x: {
                    grid: { display: false },
                    title: { display: true, text: "Occurrences", color: COLORS.text },
                },
                y: { grid: { display: false } },
            },
        },
    });
}

/**
 * Render an activity heatmap (day-of-week x hour) using DOM elements.
 */
function renderHeatmap(containerId, data) {
    const container = document.getElementById(containerId);
    if (!container || !data.length) return null;

    container.innerHTML = "";

    const dayLabels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
    const grid = {};
    let maxCount = 0;
    for (const d of data) {
        if (!grid[d.dow]) grid[d.dow] = {};
        grid[d.dow][d.hour] = d.count;
        if (d.count > maxCount) maxCount = d.count;
    }

    const corner = document.createElement("div");
    corner.className = "heatmap-label";
    container.appendChild(corner);

    for (let h = 0; h < 24; h++) {
        const label = document.createElement("div");
        label.className = "heatmap-label";
        label.textContent = h;
        container.appendChild(label);
    }

    const dowOrder = [1, 2, 3, 4, 5, 6, 0];
    for (const dow of dowOrder) {
        const rowLabel = document.createElement("div");
        rowLabel.className = "heatmap-label";
        rowLabel.textContent = dayLabels[dow];
        container.appendChild(rowLabel);

        for (let h = 0; h < 24; h++) {
            const cell = document.createElement("div");
            cell.className = "heatmap-cell";
            const count = (grid[dow] && grid[dow][h]) || 0;
            const intensity = maxCount > 0 ? count / maxCount : 0;
            const r = Math.round(233 * intensity);
            const g = Math.round(69 * intensity);
            const b = Math.round(96 * intensity);
            cell.style.backgroundColor = `rgba(${r}, ${g}, ${b}, ${Math.max(intensity, 0.08)})`;
            cell.title = `${dayLabels[dow]} ${h}:00 PT — ${count} messages`;
            container.appendChild(cell);
        }
    }
    return null;
}

/**
 * Render a horizontal bar chart for vocabulary diversity (TTR).
 */
function renderVocabularyDiversity(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !data.length) return null;

    return new Chart(canvas, {
        type: "bar",
        data: {
            labels: data.map(d => d.display_name),
            datasets: [{
                data: data.map(d => d.ttr),
                backgroundColor: COLORS.bars.slice(0, data.length),
                borderRadius: 4,
            }],
        },
        options: {
            indexAxis: "y",
            scales: {
                x: {
                    grid: { display: false },
                    title: { display: true, text: "Type-Token Ratio", color: COLORS.text },
                    min: 0,
                    max: 1,
                },
                y: { grid: { display: false } },
            },
        },
    });
}

/**
 * Render a vertical bar chart for peak hours (messages per hour of day).
 */
function renderPeakHours(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !data.length) return null;

    return new Chart(canvas, {
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
}

/**
 * Render a horizontal bar chart for reaction time kings.
 */
function renderReactionTime(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !data.length) return null;

    return new Chart(canvas, {
        type: "bar",
        data: {
            labels: data.map(d => d.display_name),
            datasets: [{
                data: data.map(d => d.avg_seconds),
                backgroundColor: COLORS.bars.slice(0, data.length),
                borderRadius: 4,
            }],
        },
        options: {
            indexAxis: "y",
            scales: {
                x: {
                    grid: { display: false },
                    title: { display: true, text: "Avg Response Time (seconds)", color: COLORS.text },
                },
                y: { grid: { display: false } },
            },
        },
    });
}

/**
 * Render a line chart for server growth (unique active users per day).
 */
function renderGrowthTimeline(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !data.length) return null;

    return new Chart(canvas, {
        type: "line",
        data: {
            labels: data.map(d => d.day),
            datasets: [{
                data: data.map(d => d.unique_users),
                borderColor: "#00b4d8",
                backgroundColor: "rgba(0, 180, 216, 0.1)",
                fill: true,
                tension: 0.3,
                pointRadius: 2,
            }],
        },
        options: {
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { maxTicksLimit: 10 },
                },
                y: {
                    beginAtZero: true,
                    grid: { color: COLORS.grid },
                    title: { display: true, text: "Unique Users", color: COLORS.text },
                },
            },
        },
    });
}

/**
 * Render a word cloud using wordcloud2.js.
 */
function renderWordCloud(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !data.length) return null;

    const maxCount = Math.max(...data.map(d => d.count));
    const list = data.map(d => [d.word, Math.max((d.count / maxCount) * 64, 12)]);

    // Defer rendering so the browser finishes layout (needed for dynamic containers)
    requestAnimationFrame(() => {
        const parent = canvas.parentElement;
        const width = parent.clientWidth - 48; // account for card padding
        canvas.width = width > 0 ? width : 700;
        canvas.height = 350;

        WordCloud(canvas, {
            list: list,
            gridSize: 8,
            weightFactor: 1,
            color: function () {
                return COLORS.bars[Math.floor(Math.random() * COLORS.bars.length)];
            },
            backgroundColor: "transparent",
            fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
            rotateRatio: 0.3,
        });
    });
    return null;
}

/**
 * Render a dual-line chart for sentiment trend.
 */
function renderSentimentTrend(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !data.length) return null;

    return new Chart(canvas, {
        type: "line",
        data: {
            labels: data.map(d => d.day),
            datasets: [
                {
                    label: "Positive",
                    data: data.map(d => d.positive),
                    borderColor: "#90be6d",
                    backgroundColor: "rgba(144, 190, 109, 0.1)",
                    fill: true,
                    tension: 0.3,
                    pointRadius: 2,
                },
                {
                    label: "Negative",
                    data: data.map(d => d.negative),
                    borderColor: COLORS.accent,
                    backgroundColor: "rgba(233, 69, 96, 0.1)",
                    fill: true,
                    tension: 0.3,
                    pointRadius: 2,
                },
            ],
        },
        options: {
            plugins: {
                legend: { display: true, labels: { color: COLORS.text } },
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { maxTicksLimit: 10 },
                },
                y: {
                    beginAtZero: true,
                    grid: { color: COLORS.grid },
                    title: { display: true, text: "Keyword Hits", color: COLORS.text },
                },
            },
        },
    });
}

/**
 * Render a conversation network as an adjacency heatmap grid.
 */
function renderConversationNetwork(containerId, data) {
    const container = document.getElementById(containerId);
    if (!container || !data.length) return null;

    container.innerHTML = "";

    // Collect unique users
    const userSet = new Set();
    for (const d of data) {
        userSet.add(d.from_user);
        userSet.add(d.to_user);
    }
    const users = Array.from(userSet);

    // Build lookup
    const lookup = {};
    let maxCount = 0;
    for (const d of data) {
        const key = `${d.from_user}|${d.to_user}`;
        lookup[key] = d.count;
        if (d.count > maxCount) maxCount = d.count;
    }

    // Build grid table
    const table = document.createElement("table");
    table.style.cssText = "width:100%; border-collapse:collapse; font-size:0.75rem;";

    // Header row
    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");
    const emptyTh = document.createElement("th");
    emptyTh.style.cssText = "padding:4px; min-width:60px;";
    headerRow.appendChild(emptyTh);
    for (const user of users) {
        const th = document.createElement("th");
        th.textContent = user.length > 8 ? user.substring(0, 7) + "\u2026" : user;
        th.title = user;
        th.style.cssText = "padding:4px; color:var(--text-secondary); font-weight:600; text-align:center; writing-mode:vertical-lr; transform:rotate(180deg); max-width:32px;";
        headerRow.appendChild(th);
    }
    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Body rows
    const tbody = document.createElement("tbody");
    for (const fromUser of users) {
        const row = document.createElement("tr");
        const labelCell = document.createElement("td");
        labelCell.textContent = fromUser.length > 10 ? fromUser.substring(0, 9) + "\u2026" : fromUser;
        labelCell.title = fromUser;
        labelCell.style.cssText = "padding:4px; color:var(--text-secondary); font-weight:600; white-space:nowrap;";
        row.appendChild(labelCell);

        for (const toUser of users) {
            const cell = document.createElement("td");
            const count = lookup[`${fromUser}|${toUser}`] || 0;
            const intensity = maxCount > 0 ? count / maxCount : 0;
            const r = Math.round(233 * intensity);
            const g = Math.round(69 * intensity);
            const b = Math.round(96 * intensity);
            cell.style.cssText = `padding:4px; text-align:center; min-width:28px; min-height:28px; border-radius:3px; background:rgba(${r},${g},${b},${Math.max(intensity, 0.05)});`;
            if (count > 0) {
                cell.textContent = count;
                cell.style.color = intensity > 0.5 ? "#fff" : "var(--text-secondary)";
                cell.style.fontSize = "0.7rem";
            }
            cell.title = `${fromUser} \u2192 ${toUser}: ${count} replies`;
            row.appendChild(cell);
        }
        tbody.appendChild(row);
    }
    table.appendChild(tbody);
    container.appendChild(table);
    return null;
}

/* ─── Catchphrase / meme lifespans ─── */

function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
}

function renderCatchphraseLifespans(containerId, data) {
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

    /* Card grid */
    const grid = document.createElement("div");
    grid.style.cssText = "display:grid; grid-template-columns:repeat(auto-fill, minmax(220px, 1fr)); gap:0.75rem; margin-bottom:1rem;";

    /* Timeline chart area (hidden until a card is clicked) */
    const chartWrapper = document.createElement("div");
    chartWrapper.style.display = "none";
    const canvas = document.createElement("canvas");
    canvas.id = containerId + "-timeline";
    chartWrapper.appendChild(canvas);

    for (const p of phrases) {
        const card = document.createElement("div");
        card.style.cssText = "background:var(--bg-card, #1a1a2e); border-radius:8px; padding:0.75rem; cursor:pointer; border:2px solid transparent; transition:border-color 0.2s;";

        const usersText = p.unique_users != null ? `${p.total_uses} uses by ${p.unique_users} users` : `${p.total_uses} uses`;
        const safeStatus = escapeHtml(p.status);
        card.innerHTML =
            `<div style="font-weight:700; font-size:0.95rem; margin-bottom:0.3rem;">\u201c${escapeHtml(p.phrase)}\u201d</div>` +
            `<span style="display:inline-block; padding:0.15rem 0.5rem; border-radius:4px; font-size:0.7rem; font-weight:600; color:#fff; background:${statusColors[p.status] || "#666"};">${safeStatus}</span>` +
            `<div style="font-size:0.8rem; color:var(--text-secondary, #aaa); margin-top:0.4rem;">${usersText}</div>` +
            `<div style="font-size:0.75rem; color:var(--text-secondary, #aaa);">${p.first_seen} \u2192 ${p.last_seen}</div>`;

        card.addEventListener("click", () => {
            /* Highlight selected card */
            grid.querySelectorAll(":scope > div").forEach(c => { c.style.borderColor = "transparent"; });
            card.style.borderColor = COLORS.accent;

            /* Render timeline chart */
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
}

/* ─── Conversation flow view toggle ─── */
function toggleConvView(view) {
    const networkEl = document.getElementById("networkGrid");
    const tableEl = document.getElementById("convFlowTable");
    const networkBtn = document.getElementById("network-btn");
    const tableBtn = document.getElementById("table-btn");
    if (!networkEl || !tableEl) return;

    if (view === "network") {
        networkEl.style.display = "";
        tableEl.style.display = "none";
        networkBtn.classList.add("active");
        tableBtn.classList.remove("active");
    } else {
        networkEl.style.display = "none";
        tableEl.style.display = "";
        networkBtn.classList.remove("active");
        tableBtn.classList.add("active");
    }
}

/**
 * Render a stacked horizontal bar chart for brainrot leaderboard.
 */
function renderBrainrotLeaderboard(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !data.length) return null;

    return new Chart(canvas, {
        type: "bar",
        data: {
            labels: data.map(d => d.display_name),
            datasets: [
                {
                    label: "Keyword Hits",
                    data: data.map(d => d.keyword_count),
                    backgroundColor: COLORS.accent,
                    borderRadius: 4,
                },
                {
                    label: "Copypasta",
                    data: data.map(d => d.copypasta_count),
                    backgroundColor: COLORS.accentAlt,
                    borderRadius: 4,
                },
            ],
        },
        options: {
            indexAxis: "y",
            plugins: {
                legend: { display: true, labels: { color: COLORS.text } },
            },
            scales: {
                x: {
                    stacked: true,
                    grid: { display: false },
                    title: { display: true, text: "Brainrot Score", color: COLORS.text },
                },
                y: { stacked: true, grid: { display: false } },
            },
        },
    });
}

/**
 * Render a vertical bar chart for top brainrot terms.
 */
function renderBrainrotTerms(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !data.length) return null;

    return new Chart(canvas, {
        type: "bar",
        data: {
            labels: data.map(d => d.term),
            datasets: [{
                data: data.map(d => d.count),
                backgroundColor: COLORS.bars.slice(0, data.length),
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
}

/**
 * Render a line chart for brainrot usage trend over time.
 */
function renderBrainrotTrend(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !data.length) return null;

    return new Chart(canvas, {
        type: "line",
        data: {
            labels: data.map(d => d.day),
            datasets: [{
                label: "Brainrot Hits",
                data: data.map(d => d.count),
                borderColor: COLORS.accentAlt,
                backgroundColor: "rgba(83, 52, 131, 0.1)",
                fill: true,
                tension: 0.3,
                pointRadius: 2,
            }],
        },
        options: {
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { maxTicksLimit: 10 },
                },
                y: {
                    beginAtZero: true,
                    grid: { color: COLORS.grid },
                    title: { display: true, text: "Daily Brainrot Hits", color: COLORS.text },
                },
            },
        },
    });
}

/* ─── Custom View Block (VIZ_REGISTRY) ─── */
const VIZ_REGISTRY = {
    "word-cloud":     { label: "Word Cloud",           dataKey: "wordCloud",         render: renderWordCloud,           type: "canvas" },
    "growth":         { label: "Server Growth",        dataKey: "growth",            render: renderGrowthTimeline,      type: "canvas" },
    "sentiment":      { label: "Sentiment Trend",      dataKey: "sentiment",         render: renderSentimentTrend,      type: "canvas" },
    "top-words":      { label: "Top Words",            dataKey: "topWords",          render: renderTopWords,            type: "canvas" },
    "peak-hours":     { label: "Peak Hours",           dataKey: "peakHours",         render: renderPeakHours,           type: "canvas" },
    "vocabulary":     { label: "Vocabulary Diversity",  dataKey: "vocabulary",        render: renderVocabularyDiversity, type: "canvas" },
    "profanity":      { label: "Profanity Board",      dataKey: "profanity",         render: renderProfanity,           type: "canvas" },
    "reaction-time":  { label: "Reaction Time Kings",  dataKey: "reactionTime",      render: renderReactionTime,        type: "canvas" },
    "heatmap":        { label: "Activity Heatmap",     dataKey: "heatmap",           render: renderHeatmap,             type: "div" },
    "network":        { label: "Who Talks to Whom",    dataKey: "conversationFlow",  render: renderConversationNetwork, type: "div" },
    "catchphrases":   { label: "Catchphrase Lifespans", dataKey: "catchphrases",      render: renderCatchphraseLifespans, type: "div" },
    "brainrot":       { label: "Brainrot Leaderboard",  dataKey: "brainrot",          render: renderBrainrotLeaderboard,  type: "canvas" },
    "brainrot-terms": { label: "Top Brainrot Terms",    dataKey: "brainrotTerms",     render: renderBrainrotTerms,        type: "canvas" },
    "brainrot-trend": { label: "Brainrot Trend",        dataKey: "brainrotTrend",     render: renderBrainrotTrend,        type: "canvas" },
};

function initCustomBlock() {
    const selectEl = document.getElementById("custom-viz-select");
    const container = document.getElementById("custom-viz-container");
    const heading = document.getElementById("custom-block-heading");
    if (!selectEl || !container) return;

    // Populate options
    for (const [key, viz] of Object.entries(VIZ_REGISTRY)) {
        const opt = document.createElement("option");
        opt.value = key;
        opt.textContent = viz.label;
        selectEl.appendChild(opt);
    }

    // Init Tom Select
    const ts = new TomSelect(selectEl, {
        allowEmptyOption: true,
        placeholder: "Choose a visualization...",
    });

    // Restore saved preference
    const saved = localStorage.getItem("dashboard-custom-viz") || "word-cloud";
    ts.setValue(saved, true);
    renderCustomViz(saved, container);
    if (heading && VIZ_REGISTRY[saved]) heading.textContent = VIZ_REGISTRY[saved].label;

    ts.on("change", (value) => {
        if (!value) {
            if (heading) heading.textContent = "Custom View";
            return;
        }
        localStorage.setItem("dashboard-custom-viz", value);
        renderCustomViz(value, container);
        if (heading && VIZ_REGISTRY[value]) heading.textContent = VIZ_REGISTRY[value].label;
    });
}

function renderCustomViz(key, container) {
    // Cleanup previous
    if (customChartInstance) {
        customChartInstance.destroy();
        customChartInstance = null;
    }
    container.innerHTML = "";

    const viz = VIZ_REGISTRY[key];
    if (!viz) return;

    const data = allData[viz.dataKey];
    if (!data || (Array.isArray(data) && data.length === 0)) {
        container.innerHTML = '<p class="empty-state">No data available for this visualization.</p>';
        return;
    }

    const elId = "custom-viz-" + key;
    if (viz.type === "canvas") {
        const canvas = document.createElement("canvas");
        canvas.id = elId;
        container.appendChild(canvas);
        customChartInstance = viz.render(elId, data);
    } else {
        const div = document.createElement("div");
        div.id = elId;
        if (key === "heatmap") div.className = "heatmap-grid";
        container.appendChild(div);
        viz.render(elId, data);
    }
}

/* Initialize charts once the DOM is ready */
document.addEventListener("DOMContentLoaded", () => {
    const dataEl = document.getElementById("chart-data");

    allData = {
        topUsers:         JSON.parse(dataEl.dataset.topUsers),
        activity:         JSON.parse(dataEl.dataset.activity),
        topWords:         JSON.parse(dataEl.dataset.topWords),
        profanity:        JSON.parse(dataEl.dataset.profanity),
        heatmap:          JSON.parse(dataEl.dataset.heatmap),
        vocabulary:       JSON.parse(dataEl.dataset.vocabulary),
        peakHours:        JSON.parse(dataEl.dataset.peakHours),
        reactionTime:     JSON.parse(dataEl.dataset.reactionTime),
        growth:           JSON.parse(dataEl.dataset.growth),
        wordCloud:        JSON.parse(dataEl.dataset.wordCloud),
        sentiment:        JSON.parse(dataEl.dataset.sentiment),
        conversationFlow: JSON.parse(dataEl.dataset.conversationFlow),
        catchphrases:     JSON.parse(dataEl.dataset.catchphrases),
        brainrot:         JSON.parse(dataEl.dataset.brainrot),
        brainrotTerms:    JSON.parse(dataEl.dataset.brainrotTerms),
        brainrotTrend:    JSON.parse(dataEl.dataset.brainrotTrend),
    };

    /* Render static charts */
    renderActivity("activityChart", allData.activity);
    renderTopUsers("topUsersChart", allData.topUsers);

    /* Initialize custom view block */
    initCustomBlock();

    /* Sticky range bar */
    const stickyBar = document.getElementById("sticky-range-bar");
    const rangePicker = document.querySelector(".range-picker");
    if (stickyBar && rangePicker) {
        const rangeObserver = new IntersectionObserver(
            ([entry]) => {
                if (!entry.isIntersecting) {
                    stickyBar.classList.add("visible");
                } else {
                    stickyBar.classList.remove("visible");
                }
            },
            { threshold: 0 }
        );
        rangeObserver.observe(rangePicker);
    }
});
