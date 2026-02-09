const buttons = document.querySelectorAll("button");
let currentStat = "points";
let currentRange = 10;
let currentPlayer = document.getElementById("player-name").dataset.player;

const lineValueEl = document.getElementById("line-value");
const avgValueEl = document.getElementById("avg-value");
const lineUpBtn = document.getElementById("line-up");
const lineDownBtn = document.getElementById("line-down");
const winRateIndicatorsEl = document.getElementById("win-rate-indicators");

let currentLine = null;
let userAdjusted = false;
let allStatsData = {}; // Store data for all ranges

buttons.forEach(btn => {
    btn.addEventListener("click", (e) => {
        // ignore line control buttons
        if (btn.id === 'line-up' || btn.id === 'line-down') return;

        if (btn.dataset.stat) {
            currentStat = btn.dataset.stat;
            document.querySelectorAll(".stat-buttons-row button")
                .forEach(b => b.classList.remove("active"));
        }

        if (btn.dataset.range) {
            currentRange = btn.dataset.range;
            document.querySelectorAll(".range-controls button")
                .forEach(b => b.classList.remove("active"));
        }

        btn.classList.add("active");
        loadChart();
    });
});

function calculateWinRates(line) {
    // Calculate win rates for all ranges against the given line
    const ranges = [5, 10, 20, 'h2h'];
    const winRates = {};
    
    ranges.forEach(range => {
        if (allStatsData[range]) {
            const values = allStatsData[range].values.filter(v => typeof v === 'number' && !isNaN(v));
            const winsCount = values.filter(v => v >= line).length;
            const total = values.length;
            const percentage = total > 0 ? Math.round((winsCount / total) * 100) : 0;
            winRates[range] = { wins: winsCount, total: total, percentage: percentage };
        }
    });
    
    return winRates;
}

function updateWinRateIndicators(line) {
    const winRates = calculateWinRates(line);
    
    winRateIndicatorsEl.innerHTML = '';
    
    Object.keys(winRates).forEach(range => {
        const data = winRates[range];
        const isGood = data.percentage >= 70;
        const rangeLabel = range === 'h2h' ? 'H2H' : `L${range}`;
        
        const item = document.createElement('div');
        item.className = 'win-rate-item';
        item.innerHTML = `
            <div class="win-rate-label">${rangeLabel}</div>
            <div class="win-rate-value ${isGood ? 'good' : 'bad'}">${data.percentage}%</div>
            <div style="font-size: 9px; color: var(--muted); margin-top: 2px;">${data.wins}/${data.total}</div>
        `;
        winRateIndicatorsEl.appendChild(item);
    });
}

function loadChart() {
    // Load data for all ranges to have them available for win rate calculation
    const ranges = [5, 10, 20, 'h2h'];
    // If currentStat is composite, we need to fetch its components and combine
    const compositeMap = {
        pa: ['points', 'assists'],
        pr: ['points', 'rebounds'],
        ra: ['rebounds', 'assists'],
        pra: ['points', 'rebounds', 'assists']
    };

    const fetchForRange = (range) => {
        if (compositeMap[currentStat]) {
            const comps = compositeMap[currentStat];
            return Promise.all(comps.map(s => fetch(`/api/player_stats?player=${encodeURIComponent(currentPlayer)}&stat=${s}&limit=${range}`).then(r => r.json())))
                .then(arr => {
                    const base = arr[0];
                    const combined = { labels: base.labels || [], dates: base.dates || [], values: [], avg: 0 };
                    const len = base.values ? base.values.length : 0;
                    for (let i = 0; i < len; i++) {
                        let sum = 0;
                        arr.forEach(a => {
                            const v = a.values && a.values[i] ? a.values[i] : 0;
                            sum += (typeof v === 'number' && !isNaN(v)) ? v : 0;
                        });
                        combined.values.push(sum);
                    }
                    combined.avg = arr.reduce((acc, a) => acc + (a.avg || 0), 0);
                    return combined;
                });
        }
        return fetch(`/api/player_stats?player=${encodeURIComponent(currentPlayer)}&stat=${currentStat}&limit=${range}`).then(res => res.json());
    };

    const promises = ranges.map(range => fetchForRange(range).then(data => { allStatsData[range] = data; return data; }));
    
    Promise.all(promises).then(dataList => {
        let data;
        const rangeStr = String(currentRange);
        
        // Find the correct data based on currentRange
        if (rangeStr === '5') data = dataList[0];
        else if (rangeStr === '10') data = dataList[1];
        else if (rangeStr === '20') data = dataList[2];
        else if (rangeStr === 'h2h') data = dataList[3];
        else data = dataList[1]; // default to L10
        
        // set average and initial line (snap to 0.5 increments)
        const avgRounded = Math.round(data.avg * 2) / 2;
        avgValueEl.textContent = avgRounded.toFixed(1);
        // also update header avg badge if present
        const hdr = document.getElementById('avg-badge-value');
        if (hdr) hdr.textContent = avgRounded.toFixed(1);
        // if the user hasn't adjusted the line manually, start from the average
        if (!userAdjusted) {
            currentLine = avgRounded;
        }
        // ensure currentLine always sits on 0.5 grid
        currentLine = Math.round(currentLine * 2) / 2;
        lineValueEl.textContent = currentLine.toFixed(1);
        
        // Update win rate indicators
        updateWinRateIndicators(currentLine);

        renderPointsChart(
            data.labels,
            data.values,
            data.dates,
            currentLine,
            currentStat
        );
    });
}

lineUpBtn.addEventListener('click', () => {
    currentLine = Math.round((currentLine + 0.5) * 2) / 2;
    currentLine = Math.round(currentLine * 2) / 2;
    userAdjusted = true;
    lineValueEl.textContent = currentLine.toFixed(1);
    updateWinRateIndicators(currentLine);
    loadChart();
});

lineDownBtn.addEventListener('click', () => {
    currentLine = Math.round((currentLine - 0.5) * 2) / 2;
    currentLine = Math.round(currentLine * 2) / 2;
    userAdjusted = true;
    lineValueEl.textContent = currentLine.toFixed(1);
    updateWinRateIndicators(currentLine);
    loadChart();
});

document.addEventListener("DOMContentLoaded", () => {
    loadChart(); 
});