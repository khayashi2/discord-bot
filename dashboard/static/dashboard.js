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

/**
 * Render a horizontal bar chart for top users.
 */
function renderTopUsers(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !data.length) return;

    new Chart(canvas, {
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
    if (!canvas || !data.length) return;

    new Chart(canvas, {
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
    if (!canvas || !data.length) return;

    new Chart(canvas, {
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
    if (!canvas || !data.length) return;

    new Chart(canvas, {
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
    if (!container || !data.length) return;

    const dayLabels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
    // Build lookup: grid[dow][hour] = count
    const grid = {};
    let maxCount = 0;
    for (const d of data) {
        if (!grid[d.dow]) grid[d.dow] = {};
        grid[d.dow][d.hour] = d.count;
        if (d.count > maxCount) maxCount = d.count;
    }

    // Top-left empty corner
    const corner = document.createElement("div");
    corner.className = "heatmap-label";
    container.appendChild(corner);

    // Hour labels across top
    for (let h = 0; h < 24; h++) {
        const label = document.createElement("div");
        label.className = "heatmap-label";
        label.textContent = h;
        container.appendChild(label);
    }

    // Rows: reorder to Mon-Sun (1,2,3,4,5,6,0)
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
            // Interpolate from transparent dark to accent color
            const r = Math.round(233 * intensity);
            const g = Math.round(69 * intensity);
            const b = Math.round(96 * intensity);
            cell.style.backgroundColor = `rgba(${r}, ${g}, ${b}, ${Math.max(intensity, 0.08)})`;
            cell.title = `${dayLabels[dow]} ${h}:00 — ${count} messages`;
            container.appendChild(cell);
        }
    }
}

/**
 * Render a horizontal bar chart for vocabulary diversity (TTR).
 */
function renderVocabularyDiversity(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !data.length) return;

    new Chart(canvas, {
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
    if (!canvas || !data.length) return;

    new Chart(canvas, {
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
                    title: { display: true, text: "Hour (UTC)", color: COLORS.text },
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
    if (!canvas || !data.length) return;

    new Chart(canvas, {
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

/* Initialize charts once the DOM is ready */
document.addEventListener("DOMContentLoaded", () => {
    /* Parse data from HTML data attributes (avoids inline script XSS) */
    const dataEl = document.getElementById("chart-data");
    const topUsersData = JSON.parse(dataEl.dataset.topUsers);
    const activityData = JSON.parse(dataEl.dataset.activity);
    const topWordsData = JSON.parse(dataEl.dataset.topWords);
    const profanityData = JSON.parse(dataEl.dataset.profanity);
    const heatmapData = JSON.parse(dataEl.dataset.heatmap);
    const vocabularyData = JSON.parse(dataEl.dataset.vocabulary);
    const peakHoursData = JSON.parse(dataEl.dataset.peakHours);
    const reactionTimeData = JSON.parse(dataEl.dataset.reactionTime);

    renderTopUsers("topUsersChart", topUsersData);
    renderActivity("activityChart", activityData);
    renderTopWords("topWordsChart", topWordsData);
    renderProfanity("profanityChart", profanityData);
    renderHeatmap("heatmapGrid", heatmapData);
    renderVocabularyDiversity("vocabularyChart", vocabularyData);
    renderPeakHours("peakHoursChart", peakHoursData);
    renderReactionTime("reactionTimeChart", reactionTimeData);
});
