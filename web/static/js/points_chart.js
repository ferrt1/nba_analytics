let chart;
let _chartValues = [];

const BAR_GREEN = "#34a853";
const BAR_RED = "#ff4d4d";

function updateChartLine(threshold) {
    if (!chart) return;
    const colors = _chartValues.map(v =>
        (typeof v === 'number' && !isNaN(v) && v >= threshold) ? BAR_GREEN : BAR_RED
    );
    chart.setOption({
        series: [
            { id: 'bars', itemStyle: { color: function(params) { return colors[params.dataIndex]; } } },
            { id: 'line', data: _chartValues.map(() => threshold) }
        ]
    });
}

let _tooltipLabels = [];

function renderPointsChart(labels, values, dates, threshold, stat, tooltipLabels) {
    const container = document.getElementById("pointsChart");
    if (!container) return;

    _chartValues = values;
    _tooltipLabels = tooltipLabels || labels;

    if (chart) chart.dispose();
    chart = echarts.init(container, null, { renderer: 'canvas' });

    const statLabels = {
        points: 'Pts', rebounds: 'Reb', assists: 'Ast', pra: 'PRA',
        pa: 'PA', pr: 'PR', ra: 'RA', sb: 'S+B',
        minutes: 'Min', steals: 'Stl', blocks: 'Blk', fgm: 'FGM',
        fga: 'FGA', fg3m: '3PM', fg3a: '3PA', ftm: 'FTM', fta: 'FTA',
        turnovers: 'TO', fouls: 'Fouls',
        reb_chances: 'RBC', potential_ast: 'PAST', usage_pct: 'USG%'
    };
    const statLabel = statLabels[stat] || 'Val';

    const colors = values.map(v =>
        (typeof v === 'number' && !isNaN(v) && v >= threshold) ? BAR_GREEN : BAR_RED
    );

    const numericVals = values.filter(v => typeof v === 'number' && !isNaN(v));
    const maxVal = numericVals.length ? Math.max(...numericVals, threshold) : threshold;
    const yMax = Math.ceil((maxVal + maxVal * 0.15) * 2) / 2;

    const n = values.length;
    const isMobile = window.innerWidth <= 768;
    const containerWidth = container.offsetWidth;
    const maxBarSpace = (containerWidth - 56) / Math.max(n, 1);
    const barWidth = isMobile
        ? Math.max(10, Math.min(24, Math.floor(maxBarSpace * 0.7)))
        : Math.max(16, Math.min(36, Math.floor(maxBarSpace * 0.7)));
    const gap = Math.max(4, Math.floor(barWidth * 0.25));
    const yAxisWidth = 40;
    const totalBarsWidth = n * (barWidth + gap);
    const maxGridWidth = containerWidth - yAxisWidth - 16;
    const gridWidth = Math.min(totalBarsWidth, maxGridWidth);
    const centerOffset = Math.floor((maxGridWidth - gridWidth) / 2);
    const gridLeft = yAxisWidth + centerOffset;

    chart.setOption({
        animation: false,
        grid: {
            left: gridLeft,
            top: 28,
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
                color: 'rgba(255,255,255,0.5)',
                fontSize: isMobile ? (n > 20 ? 7 : 9) : (n > 20 ? 9 : 11),
                rotate: (isMobile && n > 10) || n > 15 ? 45 : 0,
                interval: isMobile ? (n > 25 ? 2 : n > 15 ? 1 : 0) : (n > 25 ? 1 : 0),
            },
        },
        yAxis: {
            type: 'value',
            min: 0,
            max: yMax,
            splitNumber: 4,
            splitLine: {
                lineStyle: { color: 'rgba(255,255,255,0.04)', type: 'dashed' }
            },
            axisLabel: {
                color: 'rgba(255,255,255,0.4)',
                fontSize: 11,
                margin: centerOffset + 8,
            },
            axisLine: { show: false },
            axisTick: { show: false },
        },
        tooltip: {
            trigger: 'axis',
            backgroundColor: 'rgba(17, 17, 17, 0.95)',
            borderColor: 'rgba(38, 38, 38, 0.8)',
            borderWidth: 1,
            textStyle: { color: '#d4d4d4', fontSize: 13 },
            formatter: function(params) {
                const bar = params.find(p => p.seriesId === 'bars');
                if (!bar) return '';
                const idx = bar.dataIndex;
                const original = _chartValues[idx];
                const display = Number.isInteger(original) ? original : (original ?? 0).toFixed(1);
                const date = dates && dates[idx] ? dates[idx] : '';
                const location = _tooltipLabels[idx] || labels[idx];
                return `<b>${location}</b>` + (date ? ` — ${date}` : '') + `<br/>${statLabel}: ${display}`;
            }
        },
        series: [
            {
                id: 'bars',
                type: 'bar',
                data: values.map(v => (typeof v === 'number' && !isNaN(v)) ? v : 0),
                barWidth: barWidth,
                barCategoryGap: gap + 'px',
                itemStyle: {
                    color: function(params) { return colors[params.dataIndex]; },
                    borderRadius: [4, 4, 0, 0],
                },
                label: {
                    show: !(isMobile && n > 20),
                    position: 'insideTop',
                    color: '#ffffff',
                    fontWeight: 700,
                    fontSize: isMobile ? (n > 15 ? 7 : 10) : (n > 25 ? 9 : n > 20 ? 10 : 13),
                    formatter: function(params) {
                        const original = _chartValues[params.dataIndex];
                        if (typeof original !== 'number' || isNaN(original)) return '';
                        return Number.isInteger(original) ? original : original.toFixed(1);
                    },
                    offset: [0, 4],
                },
                z: 2,
            },
            {
                id: 'line',
                type: 'line',
                data: values.map(() => threshold),
                symbol: 'none',
                lineStyle: {
                    color: 'rgba(52, 168, 83, 0.45)',
                    width: 1.5,
                    type: 'dashed',
                },
                z: 3,
            }
        ]
    });

    window.addEventListener('resize', function() {
        if (chart) chart.resize();
    });
}
