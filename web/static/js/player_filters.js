(function () {
    // Guard: only run if there's a player on this page
    const playerNameEl = document.getElementById("player-name");
    if (!playerNameEl) return;

    const currentPlayer = playerNameEl.dataset.player;

    const lineValueEl = document.getElementById("line-value");
    const avgValueEl = document.getElementById("avg-value");
    const lineUpBtn = document.getElementById("line-up");
    const lineDownBtn = document.getElementById("line-down");
    const winRateIndicatorsEl = document.getElementById("win-rate-indicators");

    let currentStat = "points";
    let currentRange = 10;
    let currentLine = null;
    let userAdjusted = false;
    let allStatsData = {};
    let loadGen = 0; // generation counter to cancel stale fetches

    const compositeMap = {
        pa: ['points', 'assists'],
        pr: ['points', 'rebounds'],
        ra: ['rebounds', 'assists'],
        pra: ['points', 'rebounds', 'assists']
    };

    function fetchForRange(stat, range) {
        if (compositeMap[stat]) {
            const comps = compositeMap[stat];
            return Promise.all(
                comps.map(s =>
                    fetch(`/api/player_stats?player=${encodeURIComponent(currentPlayer)}&stat=${s}&limit=${range}`)
                        .then(r => r.json())
                        .catch(() => ({ labels: [], values: [], dates: [], avg: 0 }))
                )
            ).then(arr => {
                const base = arr[0];
                const combined = { labels: base.labels || [], dates: base.dates || [], values: [], avg: 0 };
                const len = base.values ? base.values.length : 0;
                for (let i = 0; i < len; i++) {
                    let sum = 0;
                    arr.forEach(a => {
                        const v = a.values && a.values[i];
                        sum += (typeof v === 'number' && !isNaN(v)) ? v : 0;
                    });
                    combined.values.push(sum);
                }
                combined.avg = arr.reduce((acc, a) => acc + (a.avg || 0), 0);
                return combined;
            });
        }
        return fetch(`/api/player_stats?player=${encodeURIComponent(currentPlayer)}&stat=${stat}&limit=${range}`)
            .then(r => r.json())
            .catch(() => ({ labels: [], values: [], dates: [], avg: 0 }));
    }

    function calculateWinRates(line) {
        const ranges = [5, 10, 20, 'h2h'];
        const winRates = {};
        ranges.forEach(range => {
            if (allStatsData[range]) {
                const values = allStatsData[range].values.filter(v => typeof v === 'number' && !isNaN(v));
                const wins = values.filter(v => v >= line).length;
                const total = values.length;
                winRates[range] = { wins, total, percentage: total > 0 ? Math.round((wins / total) * 100) : 0 };
            }
        });
        return winRates;
    }

    function updateWinRateIndicators(line) {
        const winRates = calculateWinRates(line);
        winRateIndicatorsEl.innerHTML = '';
        Object.keys(winRates).forEach(range => {
            const data = winRates[range];
            const rangeLabel = range === 'h2h' ? 'H2H' : `L${range}`;
            const item = document.createElement('div');
            item.className = 'win-rate-item';
            item.innerHTML = `
                <div class="win-rate-label">${rangeLabel}</div>
                <div class="win-rate-value ${data.percentage >= 70 ? 'good' : 'bad'}">${data.percentage}%</div>
                <div style="font-size: 9px; color: var(--muted); margin-top: 2px;">${data.wins}/${data.total}</div>
            `;
            winRateIndicatorsEl.appendChild(item);
        });
    }

    // Re-render chart with cached data — no network call
    function redrawChart() {
        const data = allStatsData[currentRange];
        if (!data) return;
        renderPointsChart(data.labels, data.values, data.dates, currentLine, currentStat);
    }

    function loadChart() {
        const gen = ++loadGen; // increment — any pending fetch with a lower gen is stale
        const ranges = [5, 10, 20, 'h2h'];
        const promises = ranges.map(range =>
            fetchForRange(currentStat, range).then(data => {
                allStatsData[range] = data;
                return data;
            })
        );

        Promise.all(promises).then(dataList => {
            if (gen !== loadGen) return; // stale — a newer loadChart() was called, ignore this

            const rangeStr = String(currentRange);
            let data;
            if (rangeStr === '5')         data = dataList[0];
            else if (rangeStr === '10')   data = dataList[1];
            else if (rangeStr === '20')   data = dataList[2];
            else if (rangeStr === 'h2h')  data = dataList[3];
            else                          data = dataList[1];

            const avgRounded = Math.round(data.avg * 2) / 2;
            avgValueEl.textContent = avgRounded.toFixed(1);

            if (!userAdjusted) currentLine = avgRounded;
            currentLine = Math.round(currentLine * 2) / 2;
            lineValueEl.textContent = currentLine.toFixed(1);

            updateWinRateIndicators(currentLine);

            if (typeof updateQuickStats === 'function') {
                updateQuickStats(dataList[0], dataList[1], dataList[2], dataList[3]);
            }

            renderPointsChart(data.labels, data.values, data.dates, currentLine, currentStat);
        }).catch(err => {
            console.error("Error cargando chart:", err);
        });
    }

    // Stat buttons
    document.querySelectorAll(".stat-buttons-row button").forEach(btn => {
        btn.addEventListener("click", () => {
            currentStat = btn.dataset.stat;
            document.querySelectorAll(".stat-buttons-row button").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            userAdjusted = false;
            loadChart();
        });
    });

    // Range buttons
    document.querySelectorAll(".range-controls button").forEach(btn => {
        btn.addEventListener("click", () => {
            currentRange = btn.dataset.range;
            document.querySelectorAll(".range-controls button").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            // Data already cached — just re-render instantly
            const data = allStatsData[currentRange];
            if (data) {
                const avgRounded = Math.round(data.avg * 2) / 2;
                avgValueEl.textContent = avgRounded.toFixed(1);
                if (!userAdjusted) {
                    currentLine = avgRounded;
                    currentLine = Math.round(currentLine * 2) / 2;
                    lineValueEl.textContent = currentLine.toFixed(1);
                }
                updateWinRateIndicators(currentLine);
                redrawChart();
            } else {
                loadChart();
            }
        });
    });

    // Line controls — only update line/colors in existing chart, no fetch, no recreation
    lineUpBtn.addEventListener('click', () => {
        if (currentLine === null) return;
        currentLine = Math.round((currentLine + 0.5) * 2) / 2;
        userAdjusted = true;
        lineValueEl.textContent = currentLine.toFixed(1);
        updateWinRateIndicators(currentLine);
        updateChartLine(currentLine);
    });

    lineDownBtn.addEventListener('click', () => {
        if (currentLine === null) return;
        currentLine = Math.round((currentLine - 0.5) * 2) / 2;
        userAdjusted = true;
        lineValueEl.textContent = currentLine.toFixed(1);
        updateWinRateIndicators(currentLine);
        updateChartLine(currentLine);
    });

    document.addEventListener("DOMContentLoaded", loadChart);
})();
