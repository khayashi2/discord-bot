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
 * Render a horizontal bar chart for top channels.
 */
function renderTopChannels(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !data.length) return;

    new Chart(canvas, {
        type: "bar",
        data: {
            labels: data.map(d => "#" + d.name),
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

/* Initialize charts once the DOM is ready */
document.addEventListener("DOMContentLoaded", () => {
    /* Parse data from HTML data attributes (avoids inline script XSS) */
    const dataEl = document.getElementById("chart-data");
    const topUsersData = JSON.parse(dataEl.dataset.topUsers);
    const topChannelsData = JSON.parse(dataEl.dataset.topChannels);
    const activityData = JSON.parse(dataEl.dataset.activity);
    const topWordsData = JSON.parse(dataEl.dataset.topWords);
    const profanityData = JSON.parse(dataEl.dataset.profanity);

    renderTopUsers("topUsersChart", topUsersData);
    renderTopChannels("topChannelsChart", topChannelsData);
    renderActivity("activityChart", activityData);
    renderTopWords("topWordsChart", topWordsData);
    renderProfanity("profanityChart", profanityData);
});
