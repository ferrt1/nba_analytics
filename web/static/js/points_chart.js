let chart;

function renderPointsChart(labels, values, dates, threshold, stat) {
    const ctx = document.getElementById("pointsChart");

    if (chart) chart.destroy();

    const thresholdLine = Array(values.length).fill(threshold);

    const numericVals = values.filter(v => typeof v === 'number' && !isNaN(v));
    const maxVal = numericVals.length ? Math.max(...numericVals, threshold) : threshold;
    const margin = Math.max(0.5, maxVal * 0.12);
    const suggestedMax = Math.ceil((maxVal + margin) * 2) / 2;

    // Stub height: small gray base at the bottom of each bar
    const stubHeight = Math.max(0.5, Math.round(maxVal * 0.025 * 2) / 2);
    const mainValues = values.map(v =>
        typeof v === 'number' && !isNaN(v) ? Math.max(0, v - stubHeight) : v
    );
    const colors = values.map(v => (v >= threshold ? "#16a34a" : "#dc2626"));

    // Fixed bar sizing — bars always the same width regardless of count
    const BAR_PERCENTAGE = 0.98;
    const CATEGORY_PERCENTAGE = 0.98;
    const MAX_BAR_THICKNESS = 52;

    const statLabels = {
        points: 'Pts', rebounds: 'Reb', assists: 'Ast', pra: 'PRA',
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
                            const total = (mainValues[idx] ?? 0) + stubHeight;
                            const display = Number.isInteger(total) ? total : total.toFixed(1);
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
                    align: "end",
                    backgroundColor: "transparent",
                    borderRadius: 0,
                    padding: { top: 6, bottom: 6, left: 0, right: 0 },
                    font: { weight: "700", size: 14 },
                    formatter: (value) => {
                        const total = value + stubHeight;
                        return Number.isInteger(total) ? total : total.toFixed(1);
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
