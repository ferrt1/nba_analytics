(function () {
    const tbody   = document.getElementById('props-tbody');
    const empty   = document.getElementById('props-empty');
    const tabs    = document.getElementById('props-stat-tabs');
    const gameSelEl = document.getElementById('props-game-select');

    if (!tbody) return;

    let currentStat = localStorage.getItem('props_stat') || 'points';
    let currentGame = localStorage.getItem('props_game') || '';
    let sortCol  = 'pct_season';
    let sortDir  = -1;
    let allProps = [];

    // ── Stat tab clicks ──────────────────────────────────────────
    tabs.addEventListener('click', e => {
        const btn = e.target.closest('button[data-stat]');
        if (!btn) return;
        tabs.querySelectorAll('button').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentStat = btn.dataset.stat;
        localStorage.setItem('props_stat', currentStat);
        load();
    });

    // ── Game filter ──────────────────────────────────────────────
    gameSelEl.addEventListener('change', () => {
        currentGame = gameSelEl.value;
        localStorage.setItem('props_game', currentGame);
        load();
    });

    // ── Column sort ──────────────────────────────────────────────
    document.getElementById('props-table').addEventListener('click', e => {
        const th = e.target.closest('th.sortable');
        if (!th) return;
        const col = th.dataset.col;
        sortDir = sortCol === col ? sortDir * -1 : (col === 'player' ? 1 : -1);
        sortCol = col;
        document.querySelectorAll('.props-table th.sortable').forEach(t =>
            t.classList.remove('sort-asc', 'sort-desc'));
        th.classList.add(sortDir === 1 ? 'sort-asc' : 'sort-desc');
        render();
    });

    // ── Helpers ──────────────────────────────────────────────────
    function pctCell(val) {
        if (val === null || val === undefined) return '<td class="pct-cell"><span class="pct-pill heat-0">\u2014</span></td>';
        const heat = val >= 75 ? 'heat-5' : val >= 60 ? 'heat-4' : val >= 50 ? 'heat-3' : val >= 30 ? 'heat-2' : 'heat-1';
        return `<td class="pct-cell"><span class="pct-pill ${heat}">${val}%</span></td>`;
    }

    function toDecimal(american) {
        if (american > 0) return ((american / 100) + 1).toFixed(2);
        return ((100 / Math.abs(american)) + 1).toFixed(2);
    }

    function oddsCell(val) {
        if (val === null || val === undefined) return '<td class="odds-cell muted">—</td>';
        return `<td class="odds-cell">${toDecimal(val)}</td>`;
    }

    function streakCell(val) {
        if (!val) return '<td class="streak-cell muted">—</td>';
        const cls = val > 0 ? 'streak-hot' : 'streak-cold';
        return `<td class="streak-cell ${cls}">${val > 0 ? '+' : ''}${val}</td>`;
    }

    // ── Render ────────────────────────────────────────────────────
    function render() {
        if (!allProps.length) {
            tbody.innerHTML = '';
            empty.style.display = 'block';
            return;
        }
        empty.style.display = 'none';

        const sorted = [...allProps].sort((a, b) => {
            let av = a[sortCol], bv = b[sortCol];
            if (av === null || av === undefined) av = sortDir === -1 ? -Infinity : Infinity;
            if (bv === null || bv === undefined) bv = sortDir === -1 ? -Infinity : Infinity;
            if (typeof av === 'string') return av.localeCompare(bv) * sortDir;
            return (av - bv) * sortDir;
        });

        tbody.innerHTML = sorted.map(p => `
            <tr class="props-row" data-player="${encodeURIComponent(p.player)}">
                <td class="player-cell">
                    <span class="player-link">${p.player}</span>
                    <span class="matchup-label">${p.matchup || ''}</span>
                </td>
                <td class="line-cell">${p.line ?? '—'}</td>
                ${oddsCell(p.over_odds)}
                ${oddsCell(p.under_odds)}
                ${streakCell(p.streak)}
                ${pctCell(p.pct_season)}
                ${pctCell(p.pct_h2h)}
                ${pctCell(p.pct_l5)}
                ${pctCell(p.pct_l10)}
                ${pctCell(p.pct_l20)}
                ${pctCell(p.pct_prev)}
            </tr>
        `).join('');

        tbody.querySelectorAll('.props-row').forEach(row => {
            row.addEventListener('click', () => {
                window.location.href = `/player?name=${encodeURIComponent(decodeURIComponent(row.dataset.player))}`;
            });
        });
    }

    // ── Load from API ─────────────────────────────────────────────
    function setLoading(on) {
        tbody.style.opacity = on ? '0.4' : '1';
    }

    function populateGameSelect(matchups) {
        const saved = currentGame;
        gameSelEl.innerHTML = '<option value="">Todos los partidos</option>' +
            matchups.map(m => `<option value="${m}"${m === saved ? ' selected' : ''}>${m}</option>`).join('');
    }

    function load() {
        setLoading(true);
        const url = `/api/props?stat=${currentStat}&limit=25` +
                    (currentGame ? `&game=${encodeURIComponent(currentGame)}` : '');

        fetch(url)
            .then(r => r.json())
            .then(data => {
                allProps = data.props || [];
                if (data.matchups) populateGameSelect(data.matchups);

                // Reset sort indicator
                document.querySelectorAll('.props-table th.sortable').forEach(t =>
                    t.classList.remove('sort-asc', 'sort-desc'));
                const activeTh = document.querySelector(`.props-table th[data-col="${sortCol}"]`);
                if (activeTh) activeTh.classList.add(sortDir === 1 ? 'sort-asc' : 'sort-desc');

                setLoading(false);
                render();
            })
            .catch(err => {
                console.error('Error loading props:', err);
                setLoading(false);
                empty.style.display = 'block';
            });
    }

    document.addEventListener('DOMContentLoaded', () => {
        // Restore active stat tab from localStorage
        if (currentStat !== 'points') {
            tabs.querySelectorAll('button').forEach(b => {
                b.classList.toggle('active', b.dataset.stat === currentStat);
            });
        }
        // Restore game filter after matchups populate (handled in populateGameSelect)
        load();
    });
})();
