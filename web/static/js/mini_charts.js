// Mini tracking charts: Potential Assists & Rebound Chances
(function () {
    let pastChartInstance = null;
    let rbcChartInstance = null;

    const BAR_COLOR = '#6b7280';

    function buildMiniChart(canvasId, labels, values, avgElId) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;

        const avg = values.filter(v => v != null).length
            ? (values.filter(v => v != null).reduce((a, b) => a + b, 0) / values.filter(v => v != null).length)
            : 0;
        const avgEl = document.getElementById(avgElId);
        if (avgEl) avgEl.textContent = `Avg: ${avg.toFixed(1)}`;

        // Short labels (team tricode from matchup)
        const shortLabels = labels.map(l => {
            const parts = l.split(' vs ');
            return parts.length === 2 ? parts[0].substring(0, 3) : l.substring(0, 5);
        });

        return new Chart(canvas, {
            type: 'bar',
            data: {
                labels: shortLabels,
                datasets: [{
                    data: values,
                    backgroundColor: BAR_COLOR,
                    borderRadius: 3,
                    barThickness: Math.max(8, Math.min(20, Math.floor(canvas.parentElement.offsetWidth / values.length) - 6)),
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    datalabels: {
                        anchor: 'end',
                        align: 'end',
                        color: '#9ca3af',
                        font: { size: 10, weight: '600' },
                        formatter: v => v != null ? v : '',
                    },
                    tooltip: {
                        backgroundColor: 'rgba(21, 25, 33, 0.95)',
                        titleColor: '#e2e4e9',
                        bodyColor: '#9ca3af',
                        callbacks: {
                            title: (items) => labels[items[0].dataIndex] || '',
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: {
                            color: '#7a7f8c',
                            font: { size: 9 },
                            maxRotation: 45,
                            autoSkip: true,
                            maxTicksLimit: 10,
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(37, 45, 61, 0.4)' },
                        ticks: {
                            color: '#7a7f8c',
                            font: { size: 9 },
                            stepSize: 1,
                        }
                    }
                }
            },
            plugins: [ChartDataLabels]
        });
    }

    window.renderMiniCharts = function (player, range) {
        const row = document.getElementById('mini-charts-row');
        if (!row) return;

        const pastUrl = `/api/player_stats?player=${encodeURIComponent(player)}&stat=potential_ast&limit=${range}`;
        const rbcUrl = `/api/player_stats?player=${encodeURIComponent(player)}&stat=reb_chances&limit=${range}`;

        Promise.all([
            fetch(pastUrl).then(r => r.json()),
            fetch(rbcUrl).then(r => r.json())
        ]).then(([pastData, rbcData]) => {
            // Check if there's any real data
            const hasPast = pastData.values && pastData.values.some(v => v != null);
            const hasRbc = rbcData.values && rbcData.values.some(v => v != null);

            if (!hasPast && !hasRbc) {
                row.style.display = 'none';
                return;
            }

            row.style.display = 'grid';

            // Destroy old charts
            if (pastChartInstance) { pastChartInstance.destroy(); pastChartInstance = null; }
            if (rbcChartInstance) { rbcChartInstance.destroy(); rbcChartInstance = null; }

            if (hasPast) {
                pastChartInstance = buildMiniChart('pastChart', pastData.labels, pastData.values, 'past-avg');
            }
            if (hasRbc) {
                rbcChartInstance = buildMiniChart('rbcChart', rbcData.labels, rbcData.values, 'rbc-avg');
            }
        }).catch(err => {
            console.error('Mini charts error:', err);
            row.style.display = 'none';
        });
    };

    window.hideMiniCharts = function () {
        const row = document.getElementById('mini-charts-row');
        if (row) row.style.display = 'none';
        if (pastChartInstance) { pastChartInstance.destroy(); pastChartInstance = null; }
        if (rbcChartInstance) { rbcChartInstance.destroy(); rbcChartInstance = null; }
    };
})();
