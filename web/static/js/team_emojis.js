// NBA Team SVG Logo Mapping
const teamLogos = {
    // Eastern Conference
    "Hawks": "https://cdn.nba.com/logos/nba/1610612737/global/L/logo.svg",
    "Celtics": "https://cdn.nba.com/logos/nba/1610612738/global/L/logo.svg",
    "Nets": "https://cdn.nba.com/logos/nba/1610612751/global/L/logo.svg",
    "Hornets": "https://cdn.nba.com/logos/nba/1610612766/global/L/logo.svg",
    "Bulls": "https://cdn.nba.com/logos/nba/1610612741/global/L/logo.svg",
    "Cavaliers": "https://cdn.nba.com/logos/nba/1610612739/global/L/logo.svg",
    "Pistons": "https://cdn.nba.com/logos/nba/1610612765/global/L/logo.svg",
    "Pacers": "https://cdn.nba.com/logos/nba/1610612754/global/L/logo.svg",
    "Heat": "https://cdn.nba.com/logos/nba/1610612748/global/L/logo.svg",
    "Bucks": "https://cdn.nba.com/logos/nba/1610612749/global/L/logo.svg",
    "Knicks": "https://cdn.nba.com/logos/nba/1610612752/global/L/logo.svg",
    "Magic": "https://cdn.nba.com/logos/nba/1610612753/global/L/logo.svg",
    "76ers": "https://cdn.nba.com/logos/nba/1610612755/global/L/logo.svg",
    "Raptors": "https://cdn.nba.com/logos/nba/1610612761/global/L/logo.svg",
    "Wizards": "https://cdn.nba.com/logos/nba/1610612764/global/L/logo.svg",
    
    // Western Conference
    "Mavericks": "https://cdn.nba.com/logos/nba/1610612742/global/L/logo.svg",
    "Nuggets": "https://cdn.nba.com/logos/nba/1610612743/global/L/logo.svg",
    "Warriors": "https://cdn.nba.com/logos/nba/1610612744/global/L/logo.svg",
    "Rockets": "https://cdn.nba.com/logos/nba/1610612745/global/L/logo.svg",
    "Clippers": "https://cdn.nba.com/logos/nba/1610612746/global/L/logo.svg",
    "Lakers": "https://cdn.nba.com/logos/nba/1610612747/global/L/logo.svg",
    "Grizzlies": "https://cdn.nba.com/logos/nba/1610612761/global/L/logo.svg",
    "Timberwolves": "https://cdn.nba.com/logos/nba/1610612750/global/L/logo.svg",
    "Pelicans": "https://cdn.nba.com/logos/nba/1610612740/global/L/logo.svg",
    "Thunder": "https://cdn.nba.com/logos/nba/1610612760/global/L/logo.svg",
    "Suns": "https://cdn.nba.com/logos/nba/1610612756/global/L/logo.svg",
    "Trail Blazers": "https://cdn.nba.com/logos/nba/1610612757/global/L/logo.svg",
    "Kings": "https://cdn.nba.com/logos/nba/1610612762/global/L/logo.svg",
    "Spurs": "https://cdn.nba.com/logos/nba/1610612759/global/L/logo.svg",
    "Jazz": "https://cdn.nba.com/logos/nba/1610612762/global/L/logo.svg"
};

// Function to get team logo URL
function getTeamLogo(teamName) {
    return teamLogos[teamName] || "";
}

// Add logos to team names in games
document.addEventListener('DOMContentLoaded', function() {
    const gameItems = document.querySelectorAll('.today-games li');
    gameItems.forEach(item => {
        const awayTeamDiv = item.querySelector('.away-team strong');
        const homeTeamDiv = item.querySelector('.home-team strong');
        
        if (awayTeamDiv) {
            const awayTeam = awayTeamDiv.textContent.trim();
            const logoUrl = getTeamLogo(awayTeam);
            if (logoUrl) {
                awayTeamDiv.innerHTML = `<img src="${logoUrl}" alt="${awayTeam}" class="team-logo" onerror="this.style.display='none'"> <span>${awayTeam}</span>`;
            }
        }
        
        if (homeTeamDiv) {
            const homeTeam = homeTeamDiv.textContent.trim();
            const logoUrl = getTeamLogo(homeTeam);
            if (logoUrl) {
                // Put the team name to the left of the logo for the right-side team
                homeTeamDiv.innerHTML = `<span>${homeTeam}</span> <img src="${logoUrl}" alt="${homeTeam}" class="team-logo" onerror="this.style.display='none'">`;
            }
        }
    });
});
