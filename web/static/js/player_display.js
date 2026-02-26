// Called by player_filters.js after it fetches all ranges — no duplicate network calls
function updateQuickStats(l5Data, l10Data, l20Data, h2hData) {
    if (document.getElementById("qs-games"))
        document.getElementById("qs-games").textContent = Math.round(l10Data.avg * 10) / 10;
    if (document.getElementById("qs-h2h"))
        document.getElementById("qs-h2h").textContent = Math.round(h2hData.avg * 10) / 10;
    if (document.getElementById("qs-l5"))
        document.getElementById("qs-l5").textContent = Math.round(l5Data.avg * 10) / 10;
    if (document.getElementById("qs-l10"))
        document.getElementById("qs-l10").textContent = Math.round(l10Data.avg * 10) / 10;
    if (document.getElementById("qs-l20"))
        document.getElementById("qs-l20").textContent = Math.round(l20Data.avg * 10) / 10;
    if (document.getElementById("total-value"))
        document.getElementById("total-value").textContent = Math.round(l10Data.avg * 10) / 10;
}
