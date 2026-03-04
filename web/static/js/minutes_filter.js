(function () {
    const playerNameEl = document.getElementById("player-name");
    if (!playerNameEl) return;

    const player = playerNameEl.dataset.player;
    const minSlider = document.getElementById("min-minutes-slider");
    const maxSlider = document.getElementById("max-minutes-slider");
    const minVal = document.getElementById("min-minutes-val");
    const maxVal = document.getElementById("max-minutes-val");
    const avgLabel = document.getElementById("minutes-avg-label");

    if (!minSlider || !maxSlider) return;

    let debounceTimer = null;
    let playerMin = 0;
    let playerMax = 48;

    // Expose current filter values globally for player_filters.js
    window.getMinutesFilter = function () {
        const lo = parseInt(minSlider.value);
        const hi = parseInt(maxSlider.value);
        // Only apply filter if user changed from defaults
        if (lo <= playerMin && hi >= playerMax) return {};
        return { min_minutes: lo, max_minutes: hi };
    };

    // Fetch player's minutes range and set slider bounds
    fetch(`/api/player_minutes_range?player=${encodeURIComponent(player)}`)
        .then(r => r.json())
        .then(data => {
            playerMin = data.min || 0;
            playerMax = data.max || 48;
            const avg = data.avg || 0;

            minSlider.min = 0;
            minSlider.max = 48;
            minSlider.value = playerMin;
            maxSlider.min = 0;
            maxSlider.max = 48;
            maxSlider.value = playerMax;

            minVal.textContent = playerMin;
            maxVal.textContent = playerMax;
            avgLabel.textContent = `Avg: ${avg}`;
        })
        .catch(() => {});

    function onSliderChange() {
        let lo = parseInt(minSlider.value);
        let hi = parseInt(maxSlider.value);

        // Prevent crossover
        if (lo > hi) {
            if (this === minSlider) {
                minSlider.value = hi;
                lo = hi;
            } else {
                maxSlider.value = lo;
                hi = lo;
            }
        }

        minVal.textContent = lo;
        maxVal.textContent = hi;

        // Debounce reload
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            // Trigger reload in player_filters.js
            if (typeof window.reloadChartWithMinutes === 'function') {
                window.reloadChartWithMinutes();
            }
        }, 400);
    }

    minSlider.addEventListener("input", onSliderChange);
    maxSlider.addEventListener("input", onSliderChange);
})();
