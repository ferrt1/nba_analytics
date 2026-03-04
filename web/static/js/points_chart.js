let chart;
let _chartValues = [];
let _chartStubHeight = 0;

// Update only the threshold line and bar colors — no chart recreation, no animation
function updateChartLine(threshold) {
    if (!chart) return;
    const len = chart.data.labels.length;
    const colors = _chartValues.map(v =>
        (typeof v === 'number' && !isNaN(v) && v >= threshold) ? "#22c55e" : "#ef4444"
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
    const colors = values.map(v => (v >= threshold ? "#22c55e" : "#ef4444"));

    // Fixed bar sizing — bars always the same width regardless of count
    const BAR_PERCENTAGE = 0.98;
    const CATEGORY_PERCENTAGE = 0.98;
    const MAX_BAR_THICKNESS = 52;

    const statLabels = {
        points: 'Pts', rebounds: 'Reb', assists: 'Ast', pra: 'PRA',
        pa: 'PA', pr: 'PR', ra: 'RA', sb: 'S+B',
        minutes: 'Min', steals: 'Stl', blocks: 'Blk', fgm: 'FGM',
        fga: 'FGA', fg3m: '3PM', fg3a: '3PA', turnovers: 'TO', fouls: 'Fouls'
    };
    const statLabel = statLabels[stat] || 'Val';

    const sharedBarOpts = {
        barPercentage: BAR_PERCENTAGE,
        categoryPercentage: CATEGORY_PERCENTAGE,
        maxBarThickness: MAX_BAR_THICKNESS,
        stack: 'g'
    };

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
                    backgroundColor: 'rgba(255,255,255,0.12)',
                    borderRadius: 0,
                    ...sharedBarOpts
                },
                {
                    // Main colored bars — no rounding at all
                    type: 'bar',
                    label: statLabel,
                    data: mainValues,
                    backgroundColor: colors,
                    borderRadius: 0,
                    ...sharedBarOpts
                },
                {
                    // Dashed threshold line
                    type: 'line',
                    label: 'Linea',
                    data: thresholdLine,
                    borderColor: 'rgba(255,255,255,0.65)',
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
            layout: { padding: { top: 48, right: 10, left: 10, bottom: 12 } },
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
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
                        if (context.dataset.label !== statLabel) return false;
                        // On mobile with many bars, show every other label
                        if (window.innerWidth <= 768 && values.length > 15) {
                            return context.dataIndex % 2 === 0;
                        }
                        return true;
                    },
                    clip: false,
                    color: "#ffffff",
                    anchor: "end",
                    align: "end",
                    backgroundColor: "transparent",
                    borderRadius: 0,
                    padding: window.innerWidth <= 768
                        ? { top: 1, bottom: 1, left: 0, right: 0 }
                        : { top: 6, bottom: 6, left: 0, right: 0 },
                    font: function() {
                        const mobile = window.innerWidth <= 768;
                        if (mobile && values.length > 20) return { weight: "700", size: 8 };
                        if (mobile) return { weight: "700", size: 10 };
                        return { weight: "700", size: 14 };
                    },
                    formatter: (value, context) => {
                        const original = _chartValues[context.dataIndex];
                        if (typeof original !== 'number' || isNaN(original)) return '';
                        return Number.isInteger(original) ? original : original.toFixed(1);
                    },
                    offset: -8
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
                    ticks: { padding: 8, color: 'rgba(255,255,255,0.5)' }
                }
            }
        },
        plugins: [ChartDataLabels]
    });
}
