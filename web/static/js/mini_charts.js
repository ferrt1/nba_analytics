// Mini tracking charts: Potential Assists & Rebound Chances
(function () {
    let pastChartInstance = null;
    let rbcChartInstance = null;

    const BAR_COLOR = '#777777';

    function buildMiniChart(containerId, labels, values, avgElId) {
        const container = document.getElementById(containerId);
        if (!container) return null;

        const nums = values.filter(v => v != null);
        const avg = nums.length ? (nums.reduce((a, b) => a + b, 0) / nums.length) : 0;
        const avgEl = document.getElementById(avgElId);
        if (avgEl) avgEl.textContent = `Avg: ${avg.toFixed(1)}`;

        const maxVal = nums.length ? Math.max(...nums) : 10;
        const yMax = Math.ceil(maxVal * 1.2);

        const n = values.length;
        const isMobile = window.innerWidth <= 768;
        const containerWidth = container.offsetWidth;
        const yAxisWidth = 30;

        // Dynamic barWidth — same logic as main chart but scaled down
        const maxBarSpace = (containerWidth - yAxisWidth - 10) / Math.max(n, 1);
        const barWidth = isMobile
            ? Math.max(6, Math.min(16, Math.floor(maxBarSpace * 0.7)))
            : Math.max(10, Math.min(24, Math.floor(maxBarSpace * 0.7)));
        const gap = Math.max(2, Math.floor(barWidth * 0.25));

        // Center bars, pin y-axis to left
        const totalBarsWidth = n * (barWidth + gap);
        const maxGridWidth = containerWidth - yAxisWidth - 10;
        const gridWidth = Math.min(totalBarsWidth, maxGridWidth);
        const centerOffset = Math.floor((maxGridWidth - gridWidth) / 2);
        const gridLeft = yAxisWidth + centerOffset;

        const instance = echarts.init(container, null, { renderer: 'canvas' });
        instance.setOption({
            animation: false,
            grid: {
                left: gridLeft,
                right: 8,
                top: 20,
                bottom: 28,
                containLabel: false,
                width: gridWidth,
            },
            xAxis: {
                type: 'category',
                data: labels,
                axisLine: { show: false },
                axisTick: { show: false },
                axisLabel: {
                    color: 'rgba(255,255,255,0.4)',
                    fontSize: isMobile ? (n > 20 ? 6 : 8) : 9,
                    rotate: (isMobile && n > 8) || n > 12 ? 45 : 0,
                    interval: isMobile ? (n > 20 ? 2 : n > 12 ? 1 : 0) : (n > 20 ? 1 : 0),
                },
            },
            yAxis: {
                type: 'value',
                min: 0,
                max: yMax,
                splitLine: {
                    lineStyle: { color: 'rgba(255,255,255,0.04)', type: 'dashed' }
                },
                axisLabel: {
                    color: 'rgba(255,255,255,0.35)',
                    fontSize: 9,
                    margin: centerOffset + 6,
                },
                axisLine: { show: false },
                axisTick: { show: false },
            },
            tooltip: {
                trigger: 'axis',
                backgroundColor: 'rgba(17, 17, 17, 0.95)',
                borderColor: 'rgba(38, 38, 38, 0.8)',
                borderWidth: 1,
                textStyle: { color: '#d4d4d4', fontSize: 12 },
                formatter: function(params) {
                    const bar = params[0];
                    if (!bar) return '';
                    return `<b>${labels[bar.dataIndex]}</b><br/>${bar.value}`;
                }
            },
            series: [{
                type: 'bar',
                data: values.map(v => v != null ? v : 0),
                barWidth: barWidth,
                barCategoryGap: gap + 'px',
                itemStyle: {
                    color: BAR_COLOR,
                    borderRadius: [3, 3, 0, 0],
                },
                label: {
                    show: !(isMobile && n > 15),
                    position: 'insideTop',
                    color: '#ffffff',
                    fontSize: isMobile ? 7 : (n > 20 ? 8 : 10),
                    fontWeight: 600,
                    offset: [0, 2],
                    formatter: function(params) {
                        return values[params.dataIndex] != null ? values[params.dataIndex] : '';
                    }
                },
            }]
        });

        window.addEventListener('resize', function() {
            if (instance && !instance.isDisposed()) instance.resize();
        });

        return instance;
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
            const hasPast = pastData.values && pastData.values.some(v => v != null);
            const hasRbc = rbcData.values && rbcData.values.some(v => v != null);

            if (!hasPast && !hasRbc) {
                row.style.display = 'none';
                return;
            }

            row.style.display = 'grid';

            if (pastChartInstance) { pastChartInstance.dispose(); pastChartInstance = null; }
            if (rbcChartInstance) { rbcChartInstance.dispose(); rbcChartInstance = null; }

            // Small delay so the container has dimensions before ECharts inits
            setTimeout(() => {
            if (hasPast) {
                pastChartInstance = buildMiniChart('pastChart', pastData.labels, pastData.values, 'past-avg');
            }
            if (hasRbc) {
                rbcChartInstance = buildMiniChart('rbcChart', rbcData.labels, rbcData.values, 'rbc-avg');
            }
            }, 50);
        }).catch(err => {
            console.error('Mini charts error:', err);
            row.style.display = 'none';
        });
    };

    window.hideMiniCharts = function () {
        const row = document.getElementById('mini-charts-row');
        if (row) row.style.display = 'none';
        if (pastChartInstance) { pastChartInstance.dispose(); pastChartInstance = null; }
        if (rbcChartInstance) { rbcChartInstance.dispose(); rbcChartInstance = null; }
    };
})();
