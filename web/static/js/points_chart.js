let chart;

function renderPointsChart(labels, values, dates, threshold, stat) {
    const ctx = document.getElementById("pointsChart");

    if (chart) chart.destroy();

    const colors = values.map(v => (v >= threshold ? "#16a34a" : "#dc2626"));
    const thresholdLine = Array(values.length).fill(threshold);

    // compute suggestedMax so datalabels don't get clipped; add small top margin
    const numericVals = values.filter(v => typeof v === 'number' && !isNaN(v));
    const maxVal = numericVals.length ? Math.max(...numericVals, threshold) : threshold;
    const margin = Math.max(0.5, maxVal * 0.12); // slightly larger margin to avoid clipping
    const suggestedMaxRaw = maxVal + margin;
    const suggestedMax = Math.ceil(suggestedMaxRaw * 2) / 2; // round up to nearest 0.5

    // choose bar width based on number of items (wider bars when few items)
    let barPercentage = 0.7;
    let categoryPercentage = 0.9;
    let topPadding = 40;
    let sidePadding = 8;
    if (labels.length <= 2) {
        barPercentage = 0.92;
        categoryPercentage = 0.98;
        topPadding = 110;
        sidePadding = 80;
    } else if (labels.length <= 5) {
        barPercentage = 0.9;
        categoryPercentage = 0.97;
        topPadding = 76;
        sidePadding = 40;
    } else if (labels.length <= 10) {
        barPercentage = 0.84;
        categoryPercentage = 0.95;
        topPadding = 52;
        sidePadding = 24;
    }

    const statLabels = {
        points: 'Pts',
        rebounds: 'Reb',
        assists: 'Ast',
        pra: 'PRA',
        minutes: 'Min',
        steals: 'Stl',
        blocks: 'Blk',
        fgm: 'FGM',
        fga: 'FGA',
        fg3m: '3PM',
        fg3a: '3PA',
        turnovers: 'TO',
        fouls: 'Fouls'
    };

    const statLabel = statLabels[stat] || 'Val';

    chart = new Chart(ctx, {
        type: "bar",
        data: {
            labels,
            datasets: [
                {
                    type: 'bar',
                    label: statLabel,
                    data: values,
                    backgroundColor: colors,
                    borderRadius: 8,
                    barPercentage: barPercentage,
                    categoryPercentage: categoryPercentage,
                    maxBarThickness: 64
                },
                {
                    type: 'line',
                    label: 'Linea',
                    data: thresholdLine,
                    borderColor: 'rgba(255,255,255,0.85)',
                    borderWidth: 1.5,
                    fill: false,
                    pointRadius: 0,
                    tension: 0,
                    borderDash: []
                }
            ]
        },
        options: {
            responsive: true,
            layout: { padding: { top: topPadding, right: sidePadding, left: sidePadding, bottom: 12 } },
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        title: function(items) {
                            const idx = items[0].dataIndex;
                            return labels[idx];
                        },
                        label: function(item) {
                            const idx = item.dataIndex;
                            const date = dates && dates[idx] ? dates[idx] : '';
                            return `${statLabel}: ${item.formattedValue}` + (date ? ` — ${date}` : '');
                        }
                    }
                },
                datalabels: {
                        display: function(context) {
                            return context.dataset.type === 'bar';
                        },
                        clip: false,
                        color: "#ffffff",
                        anchor: "end",
                        align: "end",
                        backgroundColor: "transparent",
                        borderRadius: 0,
                        padding: { top: 6, bottom: 6, left: 0, right: 0 },
                        font: {
                            weight: "700",
                            size: 15
                        },
                        formatter: (value) => {
                            return Number.isInteger(value) ? value : value.toFixed(1);
                        },
                        offset: -8
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    suggestedMax: suggestedMax,
                    grid: { display: true, color: 'rgba(255,255,255,0.04)', borderDash: [4], drawBorder: false },
                    ticks: {
                        stepSize: 0.5,
                        color: 'rgba(255,255,255,0.55)'
                    }
                },
                x: {
                    grid: { display: false },
                    // always offset bars from the edges to avoid clipping of first/last bars
                    offset: true,
                    ticks: { padding: 8 }
                }
            }
        },
        plugins: [ChartDataLabels]
    });
}
