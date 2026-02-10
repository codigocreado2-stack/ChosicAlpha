# ChosicAlpha

Cliente Python para la API de **Chosic** (Playlist Generator). Permite buscar tracks, artistas, obtener recomendaciones, caracteristicas de audio, lanzamientos por género, top playlists, descargar previews de audio e imágenes, y más.

Fue inspirado por el proyecto en "https://github.com/kkristof200/py_chosic" en un principio y repensado por mi curiosidad. Este es el resultado de mi poco conocimiento en programacion y basto uso de IA, úselo bajo su completa responsabilidad individual.

Cree un bot para scrapear la web y en base a lo obtenido se fue construyendo, puede haber fallos y codigo inutil o ambiguo sin documentar. En su mayoria funciona como se espera.


## 📋 Tabla de Contenidos

1. [Características](#características)
2. [Instalación](#instalación)
3. [Uso Rápido](#uso-rápido)
4. [Fetching de Múltiples Páginas](#fetching-de-múltiples-páginas) ⚡ **IMPORTANTE**
5. [Scripts CLI Disponibles](#scripts-cli-disponibles)
6. [Variables de Entorno](#variables-de-entorno)
7. [API Principal](#api-principal)
8. [Configuración Avanzada](#configuración-avanzada)
9. [Parámetros Soportados](#parámetros-extra-soportados)
10. [Estructura del Proyecto](#estructura-del-proyecto)
11. [Licencia](#licencia)

## Características

- ✅ Búsqueda de tracks, artistas y álbumes
- ✅ Recomendaciones personalizadas basadas en seeds
- ✅ Audio features de pistas
- ✅ Información de lanzamientos por género
- ✅ Top playlists por género/artista
- ✅ Descarga de previews e imágenes
- ✅ Paginación automática
- ✅ Utilidades para GUI (ThreadRunner)
- ✅ CLI integrada

## Instalación

### Desde el repositorio

```bash
git clone <url-del-repositorio>
cd ChosicAlpha
pip install -e .
```

### Desde PyPI (cuando esté disponible)

```bash
pip install ChosicAlpha
```

### Requisitos

- Python >= 3.12
- requests >= 2.25.0

Para instalar las dependencias manualmente:

```bash
pip install -r requirements.txt
```

## Uso Rápido

### Como módulo Python

```python
from ChosicAlpha import get_track_auto, search_auto, recommendations_auto

# Obtener una pista por ID/URI Spotify
track = get_track_auto('6r7FXNO57mlZCBY6PXcZZT')
print(f"{track.name} by {track.artist_display}")

# Buscar tracks
result = search_auto('daft punk', type='track', limit=10)
for track in result.tracks.items:
    print(f"- {track.name}")

# Obtener recomendaciones
result = recommendations_auto(seed_tracks='6r7FXNO57mlZCBY6PXcZZT', limit=5)
for track in result.tracks.items:
    print(f"- {track.name}")
```

### CLI: Búsqueda

```bash
# Búsqueda simple
python -m ChosicAlpha.Busqueda "daft punk" --type track --limit 10

# Búsqueda con descargas
python -m ChosicAlpha.Busqueda "daft punk" --download --out ./downloads

# Con parámetros extra
python -m ChosicAlpha.Busqueda "rock" --type track --limit 5 --param target_energy=80 --param min_tempo=120

# Ver parámetros soportados
python -m ChosicAlpha.Busqueda --params-info

# Descargar audio features
python -m ChosicAlpha.Busqueda --fetch-features --features-id 6r7FXNO57mlZCBY6PXcZZT --features-file features.json

# Descargar lista de géneros
python -m ChosicAlpha.Busqueda --fetch-genres --fetch-genres-file all_genres.json
```

### CLI: Descargas

```bash
# Descargar previews e imágenes de una pista
python -m ChosicAlpha.Downloader 6r7FXNO57mlZCBY6PXcZZT --out ./downloads

# Múltiples pistas
python -m ChosicAlpha.Downloader 6r7FXNO57mlZCBY6PXcZZT 3n3yCuZkMvXo4QYRLSqBNE --out ./downloads --overwrite
```

## Scripts CLI Disponibles

El proyecto incluye 8 scripts CLI especializados en la carpeta `test/` para casos de uso específicos. **Para documentación detallada, consulta [test/README.md](test/README.md)**.

### Búsqueda y Obtención de Información

| Script | Descripción | Ejemplo |
|--------|-------------|---------|
| **search_tracks.py** | Buscar pistas por término | `python test/search_tracks.py "The Killers" --limit 10` |
| **get_track.py** | Información de una pista | `python test/get_track.py "3n3Ppam7vgaVa1iaRUc9Lp"` |
| **get_artists.py** | Información de artistas | `python test/get_artists.py "0C0XlULifJtAgn6ZNCW2eu"` |
| **fetch_audio_features.py** | Características de audio | `python test/fetch_audio_features.py "70wYA8oYHoMzhRRkARoMhU"` |

### Recomendaciones y Descobrimiento

| Script | Descripción | Ejemplo |
|--------|-------------|---------|
| **recommendations.py** | Recomendaciones personalizadas | `python test/recommendations.py --seed-tracks "70wYA8oYHoMzhRRkARoMhU" --limit 10` |
| **get_genre_releases.py** | Lanzamientos por género | `python test/get_genre_releases.py "rock" --limit 20` |
| **get_top_playlists.py** | Playlists principales | `python test/get_top_playlists.py --genre-name "rock"` |

### Descargas

| Script | Descripción | Ejemplo |
|--------|-------------|---------|
| **download_tracks.py** | Descargar previews e imágenes | `python test/download_tracks.py "3n3Ppam7vgaVa1iaRUc9Lp" --out descargas` |
| **test_downloader.py** | Test de descarga con tracks de prueba | `python test/test_downloader.py` |

✅ **Todos los scripts incluyen opciones `--help` para ver parámetros disponibles**:
```bash
python test/search_tracks.py --help
python test/download_tracks.py --help
```

## Variables de Entorno

Configura credenciales y opciones mediante variables de entorno:

```bash
export CHOSIC_COOKIE="session=xxx; other=yyy"
export CHOSIC_X_WP_NONCE="nonce_value"
export CHOSIC_APP="app_value"
```

La API lee automáticamente estas variables si están presentes. Pero gracias al Handshake obtiene las cookies necesarias para todo el proceso posterior.

## � Archivo de Configuración (.chosicrc)

ChosicAlpha soporta un archivo de configuración `.chosicrc` para establecer valores por defecto sin necesidad de pasar argumentos en cada comando.

### Ubicaciones

El archivo se busca automáticamente en este orden:
1. `.chosicrc` en el **directorio actual**
2. `~/.chosicrc` en tu **directorio home**

### Crear el archivo

Copia el archivo de ejemplo:
```bash
cp .chosicrc.example .chosicrc
```

O crea uno manualmente en `~/.chosicrc`:

```ini
[search]
limit = 20
out = ./downloads
concurrency = 4

[logging]
verbose = true

[api]
timeout = 30
```

### Opciones Disponibles

```ini
[search]
limit = 20                      # Límite de resultados por defecto
type = track                    # Tipo (track, artist, album)
out = ./downloads               # Carpeta de salida para descargas
concurrency = 4                 # Descargas concurrentes
download = false                # Descargar automáticamente
overwrite = false               # Sobrescribir archivos

[logging]
verbose = false                 # Modo verbose (true/false)
debug = false                   # Modo debug (true/false)
quiet = false                   # Modo silencioso (true/false)

[api]
timeout = 30                    # Timeout en segundos
base_url = https://...          # Base URL de la API
read_env = true                 # Leer variables de entorno

[fetch]
fetch_all = false               # Descargar todas las páginas
page_size = 10                  # Tamaño de página
fetch_genres_file = all_genres.json
features_file = features.json
raw = false                     # Formato JSON sin procesar
```

### Uso

**Sin argumentos - usa defaults del archivo:**
```bash
chosic-search "query"
# Usa: limit=20, out=./downloads, verbose=true (si están en .chosicrc)
```

**Con argumentos - overridden el archivo:**
```bash
chosic-search "query" --limit 10 --quiet
# Ignora los valores del .chosicrc para estos parámetros
```

### Precedencia

La precedencia de configuración es (de menor a mayor):
1. **Valores por defecto** del programa
2. **Archivo .chosicrc** (si existe)
3. **Argumentos CLI** (siempre ganan)

Ejemplo:
```bash
# .chosicrc tiene: limit = 5
chosic-search "query"           # Usa limit=5
chosic-search "query" --limit 20  # Usa limit=20 (ignora .chosicrc)
```

### Ejemplo Completo

**~/.chosicrc:**
```ini
[search]
limit = 15
out = ~/music/downloads
concurrency = 3
download = true

[logging]
verbose = true

[api]
timeout = 45
```

**Comportamiento:**
```bash
# Búsqueda con descargas automáticas
chosic-search "The Killers"
# Ejecuta:
# - Límite: 15 (del archivo)
# - Carpeta: ~/music/downloads (del archivo)
# - Descargas: 3 concurrentes (del archivo)
# - Verbose: true (del archivo)
# - Sin descargar porque --download NO se especifica en CLI

# Sobrescribir solo el límite
chosic-search "David Bowie" --limit 25
# Usa limit=25, pero el resto del .chosicrc

# Modo silencioso ignora verbose del archivo
chosic-search "Adele" --quiet
# verbose=false (--quiet overridden el archivo)
```

## �🚀 Inicio Rápido - Casos Comunes

### 1. Buscar Tracks
```bash
cd test/
python search_tracks.py "The Killers" --limit 20
```

### 2. Obtener Recomendaciones
```bash
python recommendations.py --seed-artists "0C0XlULifJtAgn6ZNCW2eu" --limit 10
```

### 3. Descargar Previews e Imágenes
```bash
python download_tracks.py "3n3Ppam7vgaVa1iaRUc9Lp" "70wYA8oYHoMzhRRkARoMhU" --out mis_descargas
```

### 4. Analizar Características de Audio
```bash
python fetch_audio_features.py "70wYA8oYHoMzhRRkARoMhU"
```

**📖 Para muchos más ejemplos, consulta [test/README.md](test/README.md)**

## Fetching de Múltiples Páginas

### ⚡ Uso Correcto de `--fetch-all`

Cuando usas `--fetch-all` para obtener múltiples páginas de resultados, es importante entender los parámetros y cómo funcionan juntos:

### Parámetros Clave

- **`--fetch-all`**: Habilita la obtención de múltiples páginas
- **`--limit`**: Límite total de resultados que deseas
- **`--page-size`**: Resultados por página (máx. 100)

### Ejemplos Prácticos

#### ✅ Búsqueda Simple (Sin Paginación)

```bash
# Obtener solo 10 resultados (1 página)
python -m ChosicAlpha.Busqueda "deorro" --limit 10
# Resultado: ~0.5s, 10 tracks
```

#### ✅ Búsqueda con Múltiples Páginas

```bash
# Obtener 100 resultados en páginas de 20
python -m ChosicAlpha.Busqueda "deorro" --fetch-all --page-size 20 --limit 100
# Resultado: ~2.5s, 100 tracks (5 páginas × 0.5s cada una)
```

#### ✅ Búsqueda Agresiva (Muchos Resultados)

```bash
# Obtener 200 resultados en páginas de 50
python -m ChosicAlpha.Busqueda "rock" --fetch-all --page-size 50 --limit 200
# Resultado: ~2s, 200 tracks (4 páginas)
```

### 🎯 Recomendaciones de Uso

| Caso | `page_size` | `limit` | Tiempo Est. | CLI |
|------|-------------|---------|-------------|-----|
| Búsqueda rápida | 50-100 | 50-100 | <1s | `--fetch-all --page-size 50 --limit 50` |
| Búsqueda Normal | 20-50 | 100-200 | 1-3s | `--fetch-all --page-size 30 --limit 150` |
| Búsqueda Exhaustiva | 10-20 | 300+ | 5-15s | `--fetch-all --page-size 15 --limit 500` |
| **Evitar** ❌ | 1-5 | 100+ | 30-50s | `--fetch-all --page-size 1 --limit 100` (muy lento) |

### 🐍 Uso desde Python

```python
from ChosicAlpha import search_auto

# Búsqueda simple
result = search_auto('deorro', limit=10)
print(f"Obtenidos {len(result.tracks.items)} tracks")

# Búsqueda con múltiples páginas
result = search_auto('deorro', 
                     fetch_all=True, 
                     page_size=30, 
                     limit=100)
print(f"Obtenidos {len(result.tracks.items)} tracks en {len(result.tracks.items) // 30} páginas")

# Búsqueda exhaustiva
result = search_auto('rock', 
                     fetch_all=True, 
                     page_size=50, 
                     limit=500)
print(f"Total: {len(result.tracks.items)} resultados")
```

### 📊 Cómo Funciona la Paginación

1. **Primera solicitud**: Se obtienen `page_size` resultados
2. **Subsecuentes**: Se añade `time.sleep(0.5)` para evitar rate-limiting
3. **Límite**: Se detiene automáticamente cuando se alcanzan los resultados solicitados
4. **Protección**: Si el servidor no indica el total de páginas, se calcula el máximo necesario

**Nota**: Los delays entre páginas (0.5 segundos) son necesarios para evitar bloqueos de Cloudflare. No intentes eliminarlos.

### ⚠️ Errores Comunes

```bash
# ❌ INCORRECTO: Muy pocas solicitudes por página
python -m ChosicAlpha.Busqueda "query" --fetch-all --page-size 1 --limit 100
# Resultado: ~50s (100 páginas con delay = lento extremo)

# ✅ CORRECTO: Balance entre velocidad y cantidad
python -m ChosicAlpha.Busqueda "query" --fetch-all --page-size 20 --limit 100
# Resultado: ~2.5s (5 páginas con delay = óptimo)

# ✅ CORRECTO: Sin fetch_all para resultados limitados
python -m ChosicAlpha.Busqueda "query" --limit 10
# Resultado: ~0.5s (1 página, sin delay)
```

### 🔧 Configuración en `.chosicrc`

Establece valores por defecto para fetch_all:

```ini
[fetch]
fetch_all = false          # true para habilitar por defecto
page_size = 30             # Recomendado: 20-50
```

Luego puedes sobrescribir desde CLI:

```bash
python -m ChosicAlpha.Busqueda "query" --page-size 50 --limit 200
```

## API Principal

### Funciones de Búsqueda

#### `get_track(api, track_id)`
Obtiene información de una pista por ID/URI Spotify.

```python
from ChosicAlpha import ChosicAPI, get_track, create_chosic_api

api = create_chosic_api()
track = get_track(api, '6r7FXNO57mlZCBY6PXcZZT')
```

#### `search(api, q, type='track', limit=10, fetch_all=False, page_size=10)`
Realiza una búsqueda.

```python
result = search(api, 'daft punk', type='track', limit=20, fetch_all=True)
for item in result.tracks.items:
    print(item.name)
```

#### `recommendations(api, seed_tracks=None, seed_artists=None, limit=100, extra_params=None, fetch_all=False)`
Obtiene recomendaciones basadas en seeds.

```python
result = recommendations(api, 
                        seed_tracks='6r7FXNO57mlZCBY6PXcZZT,3n3yCuZkMvXo4QYRLSqBNE',
                        limit=50,
                        extra_params={'target_energy': 80})
```

#### `fetch_audio_features(api, track_id)`
Obtiene características de audio de una pista.

```python
features = fetch_audio_features(api, '6r7FXNO57mlZCBY6PXcZZT')
print(f"Danceability: {features.danceability}")
```

#### `get_top_playlists(api, artist_id=None, genre_name=None, limit=None)`
Obtiene top playlists por artista o género.

```python
result = get_top_playlists(api, genre_name='rock', limit=20)
```

#### `search_and_download(api, q, download=True, out_root='downloads', concurrency=1)`
Búsqueda con descarga paralela de previews e imágenes.

```python
result, downloads = search_and_download(api, 'daft punk', download=True, concurrency=4)
for track_id, path in downloads.items():
    if isinstance(path, Exception):
        print(f"Error descargando {track_id}: {path}")
    else:
        print(f"Descargado en {path}")
```

### Modelos de Datos

- **`TrackItem`**: Información de una pista (nombre, artistas, álbum, popularidad, etc.)
- **`ArtistDetail`**: Información completa de un artista (popularidad, seguidores, géneros, etc.)
- **`Features`**: Características de audio (danceability, energy, tempo, etc.)
- **`ChosicResponse`**: Respuesta unificada que puede contener tracks, artistas, features, etc.

### Utilidades

#### `ThreadRunner`
Executor de tareas en hilos con callbacks para aplicaciones GUI.

```python
from ChosicAlpha import ThreadRunner

runner = ThreadRunner(max_workers=4)

def my_task():
    return search_auto('test')

def on_success(result):
    print(f"Resultado: {result}")

def on_error(error):
    print(f"Error: {error}")

future = runner.submit(my_task, callback=on_success, err_callback=on_error)
runner.shutdown()
```

## Configuración Avanzada

### Cliente HTTP personalizado

```python
import requests
from ChosicAlpha import ChosicAPI, ChosicHttpClient

session = requests.Session()
# Configurar sesión con proxies, certificados, etc.

client = ChosicHttpClient(
    base_url='https://www.chosic.com/api/tools',
    session=session,
    timeout=30.0,
    user_agent='Mi-Custom-Agent/1.0'
)

api = ChosicAPI(client=client)
track = get_track(api, '6r7FXNO57mlZCBY6PXcZZT')
```

## Parámetros Extra Soportados

En búsquedas y recomendaciones, puedes pasar parámetros adicionales mediante `extra_params`:

- `target_acousticness` (0-100)
- `target_danceability` (0-100)
- `target_energy` (0-100)
- `target_instrumentalness` (0-100)
- `target_liveness` (0-100)
- `target_popularity` (0-100)
- `target_valence` (0-100)
- `min_tempo`, `max_tempo` (BPM)
- `min_duration_ms`, `max_duration_ms`

## Estructura del Proyecto

```
ChosicAlpha/
├── __init__.py               # Exports principales del paquete
├── Cliente.py                # HTTP client y API wrapper
├── Service.py                # Capa de servicio
├── Busqueda.py               # Helpers de búsqueda + CLI
├── Downloader.py             # Descarga de assets + CLI
├── models.py                 # Modelos de datos (TrackItem, ArtistDetail, etc.)
├── json_utils.py             # Utilidades JSON
├── .chosicrc.example         # Ejemplo de archivo de configuración
├── requirements.txt          # Dependencias del proyecto
├── setup.py                  # Configuración de instalación
├── LICENSE                   # Licencia GPLv2
├── README.md                 # Este archivo (documentación principal)
└── test/                     # 📁 Scripts CLI para casos de uso específicos
    ├── __init__.py
    ├── README.md             # 📖 Documentación COMPLETA de scripts CLI
    ├── search_tracks.py      # Búsqueda de pistas
    ├── get_track.py          # Info de una pista específica
    ├── get_artists.py        # Info de artistas
    ├── recommendations.py    # Recomendaciones personalizadas
    ├── fetch_audio_features.py # Características de audio
    ├── get_genre_releases.py # Lanzamientos por género
    ├── get_top_playlists.py  # Playlists principales
    ├── download_tracks.py    # Descargar previews e imágenes
    └── test_downloader.py    # Test de descargas con datos de prueba
```

**📖 Para ejemplos detallados de todos los scripts, consulta [test/README.md](test/README.md)** - Una guía completa con ejemplos, opciones y casos de uso para cada herramienta.

## Licencia

GNU General Public License v2 (GPLv2)

Este proyecto está licenciado bajo la licencia GPLv2. Consulta el archivo [LICENSE](LICENSE) para más detalles.

En resumen:
- ✅ Puedes usar, modificar y distribuir este software
- ✅ Debes compartir las mejoras con la comunidad
- ✅ Debes mantener esta licencia en derivados
- ❌ Sin garantía de ningún tipo


## ❓ Soporte

- **Scripts CLI**: Consulta [test/README.md](test/README.md) para documentación completa
- **API Python**: Ver secciones [API Principal](#api-principal) y [Configuración Avanzada](#configuración-avanzada)
- **Ayuda de script**: `python script.py --help` en cualquier script CLI

## Changelog

### v0.0.1 (2026-02-09)
- Versión inicial
- 9 scripts CLI especializados en `test/`
- Búsqueda, recomendaciones, descargas
- CLI para búsqueda y descarga con:
  - `--version` para ver versión
  - `--quiet` / `--verbose` / `--debug` para controlar logging
  - Ejemplos de uso incluidos en `--help`
- Archivo de configuración `.chosicrc` para defaults
- Modelos de datos completos
- Documentación exhaustiva
