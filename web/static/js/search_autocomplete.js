(function () {
    const input = document.querySelector('.search-form input[name="name"]');
    if (!input) return;

    const suggestions = document.getElementById('search-suggestions');
    if (!suggestions) return;

    let debounceTimer;
    let selectedIdx = -1;

    input.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        const q = input.value.trim();
        if (q.length < 2) {
            suggestions.classList.remove('active');
            selectedIdx = -1;
            return;
        }
        debounceTimer = setTimeout(() => {
            fetch(`/api/player_search?q=${encodeURIComponent(q)}`)
                .then(r => r.json())
                .then(data => {
                    if (!data.players || !data.players.length) {
                        suggestions.classList.remove('active');
                        return;
                    }
                    selectedIdx = -1;
                    suggestions.innerHTML = data.players
                        .map(p => `<div class="search-suggestion">${p}</div>`)
                        .join('');
                    suggestions.classList.add('active');

                    suggestions.querySelectorAll('.search-suggestion').forEach(el => {
                        el.addEventListener('mousedown', (e) => {
                            e.preventDefault();
                            window.location.href = `/player?name=${encodeURIComponent(el.textContent)}`;
                        });
                    });
                })
                .catch(() => suggestions.classList.remove('active'));
        }, 200);
    });

    // Arrow key navigation + Enter
    input.addEventListener('keydown', e => {
        if (!suggestions.classList.contains('active')) return;
        const items = suggestions.querySelectorAll('.search-suggestion');
        if (!items.length) return;

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            selectedIdx = (selectedIdx + 1) % items.length;
            items.forEach(el => el.classList.remove('selected'));
            items[selectedIdx].classList.add('selected');
            input.value = items[selectedIdx].textContent;
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            selectedIdx = selectedIdx <= 0 ? items.length - 1 : selectedIdx - 1;
            items.forEach(el => el.classList.remove('selected'));
            items[selectedIdx].classList.add('selected');
            input.value = items[selectedIdx].textContent;
        } else if (e.key === 'Escape') {
            suggestions.classList.remove('active');
            selectedIdx = -1;
        }
    });

    // Close on blur
    input.addEventListener('blur', () => {
        setTimeout(() => suggestions.classList.remove('active'), 150);
    });
})();
