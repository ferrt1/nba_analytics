# NBA Analytics

Herramienta local para analizar estadísticas de jugadores de la NBA. Descarga datos de la API oficial de la NBA, los guarda en una base de datos SQLite y los visualiza en una app web con gráficos interactivos.

## Características

- Búsqueda de jugadores por nombre
- Gráfico de barras con estadísticas por partido (PTS, REB, AST, PRA, 3PM, etc.)
- Filtros por rango: L5, L10, L20, H2H (vs rival del día)
- Línea ajustable para evaluar props
- Indicadores de hit rate por rango
- Roster del equipo en sidebar
- Partidos del día con horarios en ART

## Requisitos

- Python 3.11+
- Conexión a internet (para descargar datos de `stats.nba.com`)

## Instalación

```bash
# Clonar el repositorio
git clone <repo-url>
cd nba-analytics

# Crear entorno virtual
python -m venv .venv

# Activar entorno virtual
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

## Uso

### Primera vez

La primera ejecución descarga todos los partidos y boxscores de las temporadas 2024-25 y 2025-26. Puede tardar varios minutos.

```bash
python run.py
```

O hacer doble clic en `run.bat` (Windows).

### Ejecuciones siguientes

Cada vez que abrís la app, `run.py` actualiza automáticamente los datos nuevos y arranca el servidor en `http://localhost:5000`.

## Estructura

```
nba-analytics/
├── run.py                  # Launcher principal
├── run.bat                 # Acceso rápido en Windows
├── requirements.txt
├── scripts/
│   ├── fetch/
│   │   ├── fetch_games.py      # Descarga lista de partidos por temporada
│   │   └── fetch_boxscore.py   # Descarga boxscores de partidos finalizados
│   ├── db/
│   │   ├── load_games.py       # Inserta partidos en la DB
│   │   └── load_stats.py       # Inserta estadísticas en la DB
│   └── tools/
│       └── nba_daily.py        # Utilidades para datos del día
└── web/
    ├── app.py                  # Servidor Flask
    ├── templates/
    │   └── index.html
    └── static/
        ├── css/style.css
        └── js/
            ├── points_chart.js
            ├── player_filters.js
            ├── player_display.js
            ├── team_sidebar.js
            └── team_emojis.js
```

> `data/` y `db/` se generan localmente al ejecutar `run.py` y no están en el repositorio.

## Notas

- Los datos provienen de `stats.nba.com`. Si la API no responde, la app carga igualmente con los datos ya guardados en la DB.
- El H2H muestra los últimos partidos contra el rival del día (si el jugador tiene partido hoy).
- Los horarios se muestran en hora argentina (ART).
