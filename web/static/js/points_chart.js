let chart;
let _chartValues = [];
let _chartStubHeight = 0;

// Darker greens/reds for better white text contrast
const BAR_GREEN = "#15803d";
const BAR_RED = "#b91c1c";

// Update only the threshold line and bar colors — no chart recreation, no animation
function updateChartLine(threshold) {
    if (!chart) return;
    const len = chart.data.labels.length;
    const colors = _chartValues.map(v =>
        (typeof v === 'number' && !isNaN(v) && v >= threshold) ? BAR_GREEN : BAR_RED
    );
    chart.data.datasets[2].data = Array(len).fill(threshold);
    chart.data.datasets[1].backgroundColor = colors;
    chart.update('none');
}

function renderPointsChart(labels, values, dates, threshold, stat) {
    const ctx = document.getElementById("pointsChart");

    if (chart) chart.destroy();

    // Store values for updateChartLine()
    _chartValues = values;

    const thresholdLine = Array(values.length).fill(threshold);

    const numericVals = values.filter(v => typeof v === 'number' && !isNaN(v));
    const maxVal = numericVals.length ? Math.max(...numericVals, threshold) : threshold;
    const margin = Math.max(0.5, maxVal * 0.12);
    const suggestedMax = Math.ceil((maxVal + margin) * 2) / 2;

    // Stub height: small gray base at the bottom of each bar
    const stubHeight = Math.max(0.5, Math.round(maxVal * 0.025 * 2) / 2);
    _chartStubHeight = stubHeight;
    const mainValues = values.map(v =>
        typeof v === 'number' && !isNaN(v) ? Math.max(0, v - stubHeight) : v
    );
    const colors = values.map(v => (v >= threshold ? BAR_GREEN : BAR_RED));

    // Fixed bar thickness — same pixel width always, gaps stay minimal
    const chartWidth = ctx.parentElement ? ctx.parentElement.offsetWidth : 800;
    const idealBarWidth = Math.floor((chartWidth - 60) / Math.max(values.length, 1)) - 4;
    const barThickness = Math.max(12, Math.min(idealBarWidth, 42));

    const statLabels = {
        points: 'Pts', rebounds: 'Reb', assists: 'Ast', pra: 'PRA',
        pa: 'PA', pr: 'PR', ra: 'RA', sb: 'S+B',
        minutes: 'Min', steals: 'Stl', blocks: 'Blk', fgm: 'FGM',
        fga: 'FGA', fg3m: '3PM', fg3a: '3PA', turnovers: 'TO', fouls: 'Fouls'
    };
    const statLabel = statLabels[stat] || 'Val';

    const sharedBarOpts = {
        barThickness: barThickness,
        stack: 'g'
    };

    // Responsive x-axis: hide labels when too many bars for the width
    const n = values.length;
    const isMobile = window.innerWidth <= 768;
    const tooMany = (isMobile && n > 15) || (!isMobile && n > 25);
    const xTickOpts = tooMany
        ? { padding: 4, color: 'rgba(255,255,255,0.45)', maxRotation: 90, minRotation: 45, font: { size: 9 }, autoSkip: true, maxTicksLimit: isMobile ? 10 : 20 }
        : { padding: 8, color: 'rgba(255,255,255,0.5)', maxRotation: 45, minRotation: 0, autoSkip: false };

    chart = new Chart(ctx, {
        type: "bar",
        data: {
            labels,
            datasets: [
                {
                    // Gray stub at the base of each bar
                    type: 'bar',
                    label: '_base',
                    data: values.map(v => typeof v === 'number' && !isNaN(v) ? stubHeight : null),
                    backgroundColor: 'rgba(255,255,255,0.08)',
                    borderRadius: 0,
                    ...sharedBarOpts
                },
                {
                    // Main colored bars
                    type: 'bar',
                    label: statLabel,
                    data: mainValues,
                    backgroundColor: colors,
                    borderRadius: { topLeft: 5, topRight: 5 },
                    borderSkipped: 'bottom',
                    ...sharedBarOpts
                },
                {
                    // Dashed threshold line
                    type: 'line',
                    label: 'Linea',
                    data: thresholdLine,
                    borderColor: 'rgba(34, 197, 94, 0.4)',
                    borderWidth: 1.5,
                    borderDash: [6, 4],
                    fill: false,
                    pointRadius: 0,
                    tension: 0,
                    stack: undefined
                }
            ]
        },
        options: {
            animation: false,
            responsive: true,
            layout: { padding: { top: 10, right: 6, left: 6, bottom: 4 } },
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(21, 25, 33, 0.95)',
                    borderColor: 'rgba(37, 45, 61, 0.8)',
                    borderWidth: 1,
                    cornerRadius: 12,
                    titleColor: '#e2e4e9',
                    bodyColor: '#e2e4e9',
                    padding: 10,
                    filter: item => item.dataset.label !== '_base',
                    callbacks: {
                        title: function(items) {
                            return labels[items[0].dataIndex];
                        },
                        label: function(item) {
                            if (item.dataset.label === '_base') return null;
                            const idx = item.dataIndex;
                            const original = _chartValues[idx];
                            const display = Number.isInteger(original) ? original : (original ?? 0).toFixed(1);
                            const date = dates && dates[idx] ? dates[idx] : '';
                            return `${statLabel}: ${display}` + (date ? ` — ${date}` : '');
                        }
                    }
                },
                datalabels: {
                    display: function(context) {
                        return context.dataset.label === statLabel;
                    },
                    clip: false,
                    color: "#ffffff",
                    anchor: "end",
                    align: "start",
                    backgroundColor: "transparent",
                    borderRadius: 0,
                    padding: { top: 4, bottom: 0, left: 0, right: 0 },
                    font: function() {
                        const mob = window.innerWidth <= 768;
                        if (mob && n > 20) return { weight: "700", size: 7 };
                        if (mob && n > 10) return { weight: "700", size: 9 };
                        if (mob) return { weight: "700", size: 11 };
                        if (n > 25) return { weight: "700", size: 9 };
                        if (n > 20) return { weight: "700", size: 10 };
                        return { weight: "700", size: 13 };
                    },
                    formatter: (value, context) => {
                        const original = _chartValues[context.dataIndex];
                        if (typeof original !== 'number' || isNaN(original)) return '';
                        return Number.isInteger(original) ? original : original.toFixed(1);
                    },
                    offset: 2
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    suggestedMax: suggestedMax,
                    stacked: true,
                    grid: { display: true, color: 'rgba(255,255,255,0.04)', borderDash: [4], drawBorder: false },
                    ticks: { stepSize: 0.5, color: 'rgba(255,255,255,0.4)' }
                },
                x: {
                    stacked: true,
                    grid: { display: false },
                    offset: true,
                    ticks: xTickOpts
                }
            }
        },
        plugins: [ChartDataLabels]
    });
}
