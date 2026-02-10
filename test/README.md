# ChosicAlpha Scripts - Documentación Completa

Esta carpeta contiene 9 scripts CLI para interactuar con la API de Chosic, obteniendo información sobre tracks, artistas, características de audio, recomendaciones, géneros, playlists y descargas de preview/imágenes.

## 📋 Tabla de Contenidos

1. [search_tracks.py](#1-search_trackspy) - Buscar pistas
2. [get_track.py](#2-get_trackpy) - Obtener información de una pista
3. [get_artists.py](#3-get_artistspy) - Obtener información de artistas
4. [recommendations.py](#4-recommendationspy) - Obtener recomendaciones
5. [fetch_audio_features.py](#5-fetch_audio_featurespy) - Obtener características de audio
6. [get_genre_releases.py](#6-get_genre_releasespy) - Obtener lanzamientos por género
7. [get_top_playlists.py](#7-get_top_playlistspy) - Obtener top playlists
8. [download_tracks.py](#8-download_trackspy) - Descargar preview e imágenes de tracks
9. [test_downloader.py](#9-test_downloaderpy) - Test de descarga de assets

---

## 1. search_tracks.py

Busca pistas en la API de Chosic usando un término de búsqueda.

### Uso básico
```bash
python search_tracks.py "The Killers"
```

### Opciones disponibles

| Opción | Tipo | Descripción | Default |
|--------|------|-------------|---------|
| `query` | string | Término de búsqueda (obligatorio) | - |
| `--limit` | int | Número máximo de resultados | 10 |
| `--output` | string | Archivo JSON de salida | search_tracks_FECHA.json |
| `--fetch-all` | flag | Descargar todas las páginas | false |
| `--page-size` | int | Tamaño de página (máx. 100) | 10 |

### Ejemplos

```bash
# Búsqueda simple
python search_tracks.py "Bohemian Rhapsody"

# Con límite personalizado
python search_tracks.py "David Bowie" --limit 20

# Especificar archivo de salida
python search_tracks.py "Arctic Monkeys" --output my_results.json

# Descargar todas las páginas
python search_tracks.py "rock" --fetch-all --page-size 50

# Combinado: límite, archivo y página
python search_tracks.py "synthwave" --limit 15 --output synthwave.json --page-size 20
```

### Salida JSON
```json
{
  "tracks": {
    "items": [
      {
        "id": "...",
        "name": "Song Name",
        "artist_display": "Artist Name",
        "popularity": 85,
        ...
      }
    ]
  }
}
```

---

## 2. get_track.py

Obtiene información detallada de una pista específica por su ID o URI de Spotify.

### Uso básico
```bash
python get_track.py "70wYA8oYHoMzhRRkARoMhU"
```

### Opciones disponibles

| Opción | Tipo | Descripción | Default |
|--------|------|-------------|---------|
| `track_id` | string | ID o URI de Spotify (obligatorio) | - |
| `--output` | string | Archivo JSON de salida | track_FECHA.json |
| `--base-url` | string | Base URL de la API | https://www.chosic.com/api/tools |
| `--timeout` | float | Timeout en segundos | - |

### Ejemplos

```bash
# Con ID de Spotify
python get_track.py "3n3Ppam7vgaVa1iaRUc9Lp"

# Con URI completo
python get_track.py "spotify:track:3n3Ppam7vgaVa1iaRUc9Lp"

# Con archivo de salida personalizado
python get_track.py "3n3Ppam7vgaVa1iaRUc9Lp" --output mi_cancion.json

# Con timeout personalizado
python get_track.py "3n3Ppam7vgaVa1iaRUc9Lp" --timeout 20

# Combinado
python get_track.py "3n3Ppam7vgaVa1iaRUc9Lp" --output track_info.json --timeout 15
```

### Salida JSON
```json
{
  "id": "70wYA8oYHoMzhRRkARoMhU",
  "name": "When You Were Young",
  "artist_display": "The Killers",
  "popularity": 79,
  "duration_ms": 220427,
  "artists": [
    {
      "id": "0C0XlULifJtAgn6ZNCW2eu",
      "name": "The Killers"
    }
  ],
  ...
}
```

---

## 3. get_artists.py

Obtiene información de uno o más artistas por sus IDs de Spotify.

### Uso básico
```bash
python get_artists.py "0C0XlULifJtAgn6ZNCW2eu"
```

### Opciones disponibles

| Opción | Tipo | Descripción | Default |
|--------|------|-------------|---------|
| `artist_ids` | string | IDs de artistas (obligatorio) | - |
| `--output` | string | Archivo JSON de salida | artists_FECHA.json |
| `--base-url` | string | Base URL de la API | https://www.chosic.com/api/tools |
| `--timeout` | float | Timeout en segundos | - |

### Formatos de entrada

El script soporta 3 formatos diferentes para los IDs de artistas:

#### Formato 1: Un único artista
```bash
python get_artists.py "0C0XlULifJtAgn6ZNCW2eu"
```

#### Formato 2: Múltiples artistas separados por comas
```bash
python get_artists.py "0C0XlULifJtAgn6ZNCW2eu,1KpCi9BOfviCVhmpI4G2sY"
```

#### Formato 3: Múltiples artistas como argumentos separados
```bash
python get_artists.py 0C0XlULifJtAgn6ZNCW2eu 1KpCi9BOfviCVhmpI4G2sY 3qm84nBvXcaddTiuWxKukm
```

### Ejemplos

```bash
# Artista único
python get_artists.py "0C0XlULifJtAgn6ZNCW2eu"

# Dos artistas con comas
python get_artists.py "0C0XlULifJtAgn6ZNCW2eu,1KpCi9BOfviCVhmpI4G2sY"

# Tres artistas como argumentos
python get_artists.py 0C0XlULifJtAgn6ZNCW2eu 1KpCi9BOfviCVhmpI4G2sY 3qm84nBvXcaddTiuWxKukm

# Con archivo de salida
python get_artists.py "0C0XlULifJtAgn6ZNCW2eu,1KpCi9BOfviCVhmpI4G2sY" --output artistas.json

# Con timeout personalizado
python get_artists.py "0C0XlULifJtAgn6ZNCW2eu" --timeout 20
```

### Salida JSON
```json
[
  {
    "id": "0C0XlULifJtAgn6ZNCW2eu",
    "name": "The Killers",
    "popularity": 81,
    "followers": 8224662,
    "genres": ["alternative rock", "dance rock", "rock"],
    "image": "https://...jpg"
  },
  {
    "id": "1KpCi9BOfviCVhmpI4G2sY",
    "name": "Tchami",
    "popularity": 58,
    "followers": 598540,
    "genres": ["bass house", "future house", "house"],
    "image": "https://...jpg"
  }
]
```

---

## 4. recommendations.py

Obtiene recomendaciones de pistas basadas en seeds (pistas o artistas como referencia).

### Uso básico
```bash
python recommendations.py --seed-tracks "70wYA8oYHoMzhRRkARoMhU" --limit 10
```

### Opciones disponibles

| Opción | Tipo | Descripción | Default |
|--------|------|-------------|---------|
| `--seed-tracks` | string | IDs de pistas semilla (opcional) | - |
| `--seed-artists` | string | IDs de artistas semilla (opcional) | - |
| `--limit` | int | Número máximo de recomendaciones | 10 |
| `--output` | string | Archivo JSON de salida | recommendations_FECHA.json |
| `--fetch-all` | flag | Descargar todas las páginas | false |
| `--page-size` | int | Tamaño de página (máx. 100) | 10 |
| `--base-url` | string | Base URL de la API | https://www.chosic.com/api/tools |
| `--timeout` | float | Timeout en segundos | - |
| `--param` | string | Parámetros extra (puede repetirse) | - |

### Parámetros extra soportados

```bash
# Target (0-100 escala percentual)
--param target_energy=80
--param target_danceability=70
--param target_valence=60
--param target_acousticness=30

# Rango de tempo (BPM)
--param min_tempo=100
--param max_tempo=180

# Rango de duración (milliseconds)
--param min_duration_ms=60000
--param max_duration_ms=300000
```

### Ejemplos

```bash
# Recomendaciones basadas en una pista
python recommendations.py --seed-tracks "70wYA8oYHoMzhRRkARoMhU" --limit 10

# Recomendaciones basadas en un artista
python recommendations.py --seed-artists "0C0XlULifJtAgn6ZNCW2eu" --limit 5

# Combinando pistas y artistas
python recommendations.py --seed-tracks "70wYA8oYHoMzhRRkARoMhU" --seed-artists "0C0XlULifJtAgn6ZNCW2eu" --limit 20

# Múltiples seeds (separadas por comas)
python recommendations.py --seed-tracks "70wYA8oYHoMzhRRkARoMhU,3n3Ppam7vgaVa1iaRUc9Lp" --limit 15

# Con parámetros de audio
python recommendations.py --seed-tracks "70wYA8oYHoMzhRRkARoMhU" --limit 10 --param target_energy=80 --param target_danceability=70

# Con rango de tempo
python recommendations.py --seed-tracks "70wYA8oYHoMzhRRkARoMhU" --limit 10 --param min_tempo=100 --param max_tempo=150

# Fetch all con página personalizada
python recommendations.py --seed-artists "0C0XlULifJtAgn6ZNCW2eu" --fetch-all --page-size 50 --output all_recommendations.json

# Combinado completo
python recommendations.py --seed-tracks "70wYA8oYHoMzhRRkARoMhU" --seed-artists "0C0XlULifJtAgn6ZNCW2eu" --limit 25 --param target_energy=85 --output recommendations_high_energy.json
```

### Salida JSON
```json
{
  "tracks": {
    "items": [
      {
        "id": "...",
        "name": "Song Name",
        "artist_display": "Artist Name",
        "popularity": 75,
        ...
      }
    ]
  }
}
```

---

## 5. fetch_audio_features.py

Obtiene las características de audio de una pista (danceability, energy, acousticness, etc.).

### Uso básico
```bash
python fetch_audio_features.py "70wYA8oYHoMzhRRkARoMhU"
```

### Opciones disponibles

| Opción | Tipo | Descripción | Default |
|--------|------|-------------|---------|
| `track_id` | string | ID o URI de Spotify (obligatorio) | - |
| `--output` | string | Archivo JSON de salida | audio_features_FECHA.json |
| `--base-url` | string | Base URL de la API | https://www.chosic.com/api/tools |
| `--timeout` | float | Timeout en segundos | 15.0 |

### Ejemplos

```bash
# Características de audio simples
python fetch_audio_features.py "70wYA8oYHoMzhRRkARoMhU"

# Con archivo personalizado
python fetch_audio_features.py "3n3Ppam7vgaVa1iaRUc9Lp" --output brightside_features.json

# Con timeout personalizado
python fetch_audio_features.py "70wYA8oYHoMzhRRkARoMhU" --timeout 10

# Combinado
python fetch_audio_features.py "70wYA8oYHoMzhRRkARoMhU" --output my_track_features.json --timeout 20
```

### Características disponibles

| Característica | Rango | Descripción |
|---|---|---|
| `acousticness` | 0.0-1.0 | Confianza en si es acústica (sin amplificación) |
| `danceability` | 0.0-1.0 | Qué bailable es la canción |
| `energy` | 0.0-1.0 | Intensidad y actividad (1.0 = máxima energía) |
| `instrumentalness` | 0.0-1.0 | Probabilidad de que no tenga voces |
| `liveness` | 0.0-1.0 | Detecta presencia de audiencia (grabación en vivo) |
| `loudness` | dB | Volumen general promedio (-60 a 0 dB) |
| `speechiness` | 0.0-1.0 | Presencia de palabras habladas |
| `tempo` | BPM | Velocidad general en pulsaciones por minuto |
| `valence` | 0.0-1.0 | Positividad musical (1.0 = alegre, 0.0 = triste) |

### Salida JSON
```json
{
  "id": "70wYA8oYHoMzhRRkARoMhU",
  "duration_ms": 220427,
  "danceability": 0.467,
  "energy": 0.988,
  "acousticness": 0.000152,
  "instrumentalness": 0.0484,
  "liveness": 0.28,
  "loudness": -3.313,
  "speechiness": 0.112,
  "tempo": 130.433,
  "valence": 0.321,
  "key": 11,
  "mode": 1,
  "time_signature": 4
}
```

---

## 6. get_genre_releases.py

Obtiene lanzamientos (álbumes) de un género específico.

### Uso básico
```bash
python get_genre_releases.py "rock"
```

### Opciones disponibles

| Opción | Tipo | Descripción | Default |
|--------|------|-------------|---------|
| `genre` | string | Nombre del género (obligatorio) | - |
| `--limit` | int | Número máximo de resultados | - |
| `--output` | string | Archivo JSON de salida | genre_releases_FECHA.json |

### ⚠️ Nota Importante
Si no hay lanzamientos recientes del género especificado en la base de datos de Chosic, el script no arrojará resultados (el campo `genre_releases` será `null`). Esto es normal y significa que la API no tiene datos disponibles para ese género en este momento. Intenta con géneros populares como `rock`, `pop`, `electronic`, `metal`, etc.

### Ejemplos

```bash
# Género simple
python get_genre_releases.py "rock"

# Con límite
python get_genre_releases.py "pop" --limit 20

# Archivo personalizado
python get_genre_releases.py "pop" --output pop_releases.json

# Combinado
python get_genre_releases.py "electronic" --limit 15 --output electronic_releases.json

# Otros géneros
python get_genre_releases.py "metal"
python get_genre_releases.py "hiphop"
python get_genre_releases.py "classical"
python get_genre_releases.py "blues"
python get_genre_releases.py "country"
python get_genre_releases.py "reggae"

# ❌ Ejemplo que NO retorna datos (sin lanzamientos recientes)
python get_genre_releases.py "jazz"  # Puede retornar null si no hay datos disponibles
```

### Salida JSON
```json
{
  "genre_releases": {
    "items": [
      {
        "album_id": "...",
        "album_name": "Album Title",
        "release_date": "2026-01-23",
        "artist_name": "Artist Name",
        "album_type": "album",
        "album_img": "https://..."
      }
    ]
  }
}
```

---

## 7. get_top_playlists.py

Obtiene las principales playlists, opcionalmente filtradas por artista y/o género.

### Uso básico
```bash
python get_top_playlists.py
```

### Opciones disponibles

| Opción | Tipo | Descripción | Default |
|--------|------|-------------|---------|
| `--artist-id` | string | ID de artista para filtrar (opcional) | - |
| `--genre-name` | string | Nombre de género para filtrar (opcional) | - |
| `--limit` | int | Número máximo de resultados (opcional) | - |
| `--output` | string | Archivo JSON de salida | top_playlists_FECHA.json |
| `--base-url` | string | Base URL de la API | https://www.chosic.com/api/tools |
| `--timeout` | float | Timeout en segundos | - |

### Ejemplos

```bash
# Obtener todas las top playlists (sin filtros)
python get_top_playlists.py

# Filtrar por artista
python get_top_playlists.py --artist-id "0C0XlULifJtAgn6ZNCW2eu"

# Filtrar por género
python get_top_playlists.py --genre-name "rock"

# Filtrar por artista Y género
python get_top_playlists.py --artist-id "0C0XlULifJtAgn6ZNCW2eu" --genre-name "rock"

# Con límite
python get_top_playlists.py --limit 20

# Artista con límite
python get_top_playlists.py --artist-id "0C0XlULifJtAgn6ZNCW2eu" --limit 10

# Género con límite
python get_top_playlists.py --genre-name "jazz" --limit 5

# Archivo personalizado
python get_top_playlists.py --artist-id "0C0XlULifJtAgn6ZNCW2eu" --output killers_playlists.json

# Completamente especificado
python get_top_playlists.py --artist-id "0C0XlULifJtAgn6ZNCW2eu" --genre-name "rock" --limit 25 --output comprehensive.json

# Timeout personalizado
python get_top_playlists.py --artist-id "0C0XlULifJtAgn6ZNCW2eu" --timeout 20
```

### Salida JSON
```json
{
  "top_playlists": {
    "items": [
      {
        "id": "...",
        "name": "Playlist Name",
        "parent_genre": "Rock",
        "tracks_count": 85,
        "followers": 288250,
        "image": "https://..."
      }
    ]
  }
}
```

---

## 8. download_tracks.py

Script para descargar **previews de audio** e **imágenes de covers** de pistas usando el CLI de Downloader. Completamente flexible y parametrizable, a diferencia de `test_downloader.py` que es un script de prueba con valores fijos.

### Uso básico
```bash
python download_tracks.py "1301WleyT98MSxVHPZCA6M"
```

### Opciones disponibles

| Opción | Tipo | Descripción | Default |
|--------|------|-------------|---------|
| `tracks` | string | ID(s) o URI(s) de Spotify (obligatorio, múltiples) | - |
| `--out` | string | Carpeta base de salida | mis_descargas |
| `--overwrite` | flag | Sobrescribir archivos existentes | false |

### Estructura de Carpetas

Cada track se descarga en su propia carpeta con nombre:
```
{track_name} - {artist_name} ({track_id})
```

Dentro de cada carpeta:
```
track_name - artist_name (track_id)/
├── image_default.jpg      # Thumbnail del cover (~1-3 KB)
├── image_large.jpg        # Versión grande del cover (~95-150 KB)
└── track_name - artist_name.mp3  # Preview de audio (si disponible, ~300-500 KB)
```

### ⚠️ Nota Importante

**No todos los tracks tienen preview disponible.** La API de Spotify (que usa Chosic) solo proporciona previews para algunos tracks. Tracks sin preview descargará solo las imágenes.

Si aparece el mensaje:
```
⚠️  Sin resultado: el track no contiene preview o datos disponibles
```

Significa que ese track no tiene datos disponibles en Chosic (puede ser porque no existe, no tiene preview, o está limitado geográficamente).

### Ejemplos

#### Descarga Única
```bash
# Descargar un único track
python download_tracks.py "1301WleyT98MSxVHPZCA6M"

# Con URI completo de Spotify
python download_tracks.py "spotify:track:1301WleyT98MSxVHPZCA6M"

# Especificando carpeta de salida
python download_tracks.py "1301WleyT98MSxVHPZCA6M" --out mis_descargas
```

#### Descargas Múltiples
```bash
# Dos tracks a la vez
python download_tracks.py 3n3Ppam7vgaVa1iaRUc9Lp 70wYA8oYHoMzhRRkARoMhU

# Tres o más tracks
python download_tracks.py 1301WleyT98MSxVHPZCA6M 3n3Ppam7vgaVa1iaRUc9Lp 70wYA8oYHoMzhRRkARoMhU --out album_tracks

# Múltiples tracks con carpeta personalizada
python download_tracks.py 2takcwgKJvtQcYtbuMFOH7 3n3Ppam7vgaVa1iaRUc9Lp --out mis_descargas
```

#### Con Sobrescritura
```bash
# Sobrescribir archivos existentes
python download_tracks.py "1301WleyT98MSxVHPZCA6M" --overwrite

# Múltiples tracks con sobrescritura
python download_tracks.py 1301WleyT98MSxVHPZCA6M 3n3Ppam7vgaVa1iaRUc9Lp --out album_tracks --overwrite
```

#### Combinaciones Completas
```bash
# Carpeta personalizada + sobrescritura
python download_tracks.py "1301WleyT98MSxVHPZCA6M" --out mi_musik --overwrite

# Múltiples tracks + carpeta + sobrescritura
python download_tracks.py 3n3Ppam7vgaVa1iaRUc9Lp 70wYA8oYHoMzhRRkARoMhU --out all_tracks --overwrite

# Desde URIs de Spotify + carteta + sobrescritura
python download_tracks.py spotify:track:1301WleyT98MSxVHPZCA6M spotify:track:3n3Ppam7vgaVa1iaRUc9Lp --out my_playlist --overwrite
```

### Output Esperado

```
🎵 Descargando assets de tracks desde Chosic
======================================================================

📥 Track 1/2: 2takcwgKJvtQcYtbuMFOH7
   ⚠️  Sin resultado: el track no contiene preview o datos disponibles

📥 Track 2/2: 3n3Ppam7vgaVa1iaRUc9Lp
   ✅ 2 archivo(s) descargado(s)

======================================================================
📊 Resumen:
======================================================================
✅ Exitosos: 1/2
❌ Fallidos: 1/2
📦 Total de archivos: 2

📂 Descargas en: /media/usuario/PORNO/ChosicAlpha/test/mis_descargas
======================================================================
```

### Casos de Uso

#### 1. Descargar Single Track
```bash
python download_tracks.py "3n3Ppam7vgaVa1iaRUc9Lp"
# Descarga Mr. Brightside en: mis_descargas/Mr. Brightside - The Killers (...)/
```

#### 2. Crear Colección de Favoritos
```bash
# IDs de tus canciones favoritas
python download_tracks.py \
  3n3Ppam7vgaVa1iaRUc9Lp \
  70wYA8oYHoMzhRRkARoMhU \
  1301WleyT98MSxVHPZCA6M \
  --out favoritos
```

#### 3. Respaldar Playlista Completa
```bash
# Después de extraer los IDs de una playlist
python download_tracks.py id1 id2 id3 id4 id5 ... --out my_playlist

# Luego puedes reproducir las imágenes o previews localmente
```

#### 4. Actualizar Descargas Existentes
```bash
# Descarcar nuevamente con sobrescritura
python download_tracks.py "3n3Ppam7vgaVa1iaRUc9Lp" --out favoritos --overwrite

# Útil si tuviste fallos anteriores o quieres asegurar archivos completos
```

#### 5. Descargar y Organizar por Artista
```bash
# Todos los tracks de The Killers
python download_tracks.py \
  3n3Ppam7vgaVa1iaRUc9Lp \
  70wYA8oYHoMzhRRkARoMhU \
  --out "The_Killers"
```

### Especificaciones Técnicas

**Audio Descargado**:
- Formato: MPEG ADTS, Layer III (MP3)
- Bitrate: 96 kbps
- Sample Rate: 44.1 kHz
- Canales: Stereo
- Duración: ~30 segundos (preview)

**Imágenes**:
- Formato: JPEG
- Tamaño default: ~1-3 KB (thumbnail)
- Tamaño large: ~95-150 KB (full resolution)

**Tipos MIME Detectados Automáticamente**:
- `audio/mpeg` → `.mp3`
- `image/jpeg` → `.jpg`
- `image/png` → `.png`

### Limitaciones

⚠️ **Expected**:
1. No todos los tracks tienen preview en Spotify
2. Algunos previews pueden estar limitados por región
3. Disponibilidad variable: El mismo track puede tener/no tener preview en diferentes momentos
4. Si un track no existe en Chosic, retorna error "empty result"

---

## 9. test_downloader.py

Script de prueba para validar el funcionamiento del módulo `Downloader`. Descarga **previews de audio** e **imágenes de covers** de pistas de Spotify usando la API de Chosic.

### Uso básico
```bash
python test_downloader.py
```

### Funcionalidad

El script descarga y organiza automáticamente:
- **image_default.jpg**: Thumbnail del cover del album (~1-3 KB)
- **image_large.jpg**: Versión grande del cover (~95-150 KB)
- **{track_name}.mp3**: Preview de audio (si está disponible, ~300-500 KB)

Cada track se organiza en su propia carpeta con estructura: `{track_name} - {artist_name} ({id})`

### Resultados Esperados

El script realiza 3 pruebas de descarga:

✅ **Tracks con Preview**:
- **Piano Sonata No. 2** (ID: 1301WleyT98MSxVHPZCA6M)
  - Descarga: 3 archivos (preview MP3 + 2 imágenes)
  - Audio: 352 KB MP3 (96 kbps, 44.1 kHz, stereo)
  
- **Mr. Brightside** (ID: 3n3Ppam7vgaVa1iaRUc9Lp)
  - Descarga: 2 archivos (solo imágenes, sin preview en esta ocasión)

⚠️ **Tracks sin Preview**:
- **Blinding Lights** (ID: 2takcwgKJvtQcYtbuMFOH7)
  - Descarga: imágenes solamente (preview_url = null)

### Estructura de Descargas

```
mis_descargas/
├── Mr. Brightside - The Killers (3n3Ppam7vgaVa1iaRUc9Lp)/
│   ├── image_default.jpg (1.8 KB)
│   └── image_large.jpg (95 KB)
└── Piano Sonata No. 2 in B-Flat Minor... (1301WleyT98MSxVHPZCA6M)/
    ├── image_default.jpg (2.5 KB)
    ├── image_large.jpg (95 KB)
    └── Piano Sonata No. 2... (352 KB MP3)
```

### Output Esperado

```
🎵 Test de descarga de track assets (preview + imágenes)
======================================================================

📥 Descargando: Piano Sonata - Chopin (con preview)
   ID: 1301WleyT98MSxVHPZCA6M
   📁 Archivos descargados: 3

📥 Descargando: Blinding Lights - The Weeknd
   ID: 2takcwgKJvtQcYtbuMFOH7
   ⚠️  Sin archivos descargados (preview no disponible)

📥 Descargando: Mr. Brightside - The Killers
   ID: 3n3Ppam7vgaVa1iaRUc9Lp
   📁 Archivos descargados: 2

======================================================================
📊 Resumen de pruebas:
======================================================================
1. Piano Sonata - Chopin (con preview): ✅ OK (3 archivos)
2. Blinding Lights - The Weeknd: ✅ OK 
3. Mr. Brightside - The Killers: ✅ OK (2 archivos)

======================================================================
✅ Éxito: 3/3 tracks
❌ Fallos: 0/3 tracks
📦 Total de archivos descargados: 5

📂 Descargas guardadas en: /media/usuario/PORNO/ChosicAlpha/test/mis_descargas
======================================================================
```

### Puntos Clave

✅ **Lo que Funciona**:
1. Descarga de imágenes de covers (siempre disponibles)
2. Descarga de previews de audio en MP3 (cuando están disponibles)
3. Organización automática por track
4. Manejo graceful de tracks sin preview
5. Detección automática de tipo MIME y extensión

⚠️ **Limitaciones** (Expected):
- No todos los tracks tienen preview: Spotify no proporciona previews para todos
- Algunos previews pueden estar limitados geográficamente
- Disponibilidad variable: A veces el mismo track puede tener/no tener preview

### Especificaciones Técnicas

**Tipos MIME Detectados**:
- Audio: `audio/mpeg` → `.mp3`
- Imagen: `image/jpeg` → `.jpg`, `image/png` → `.png`

**Codificación de Audio Descargado**:
- Formato: MPEG ADTS, Layer III (MP3)
- Bitrate: 96 kbps
- Sample Rate: 44.1 kHz
- Canales: Stereo

### Personalizar el Test

Para probar con otros tracks, edita los track IDs en el script:

```python
test_tracks = [
    {
        "id": "SPOTIFY_TRACK_ID_AQUI",
        "name": "Track Name - Artist",
    },
]
```

Luego ejecuta:
```bash
python test_downloader.py
```

---

Puedes configurar variables de entorno para personalizar la API:

```bash
export CHOSIC_COOKIE="tu_cookie_aqui"
export CHOSIC_X_WP_NONCE="tu_nonce_aqui"
export CHOSIC_APP="tu_app_aqui"
```

Luego los scripts usarán estos valores automáticamente.

---

## 🔧 Casos de Uso Comunes

### 1. Análisis de Artista
```bash
# Obtener info del artista
python get_artists.py "0C0XlULifJtAgn6ZNCW2eu"

# Obtener playlists del artista
python get_top_playlists.py --artist-id "0C0XlULifJtAgn6ZNCW2eu" --output artist_playlists.json

# Obtener recomendaciones similares
python recommendations.py --seed-artists "0C0XlULifJtAgn6ZNCW2eu" --limit 20 --output similar_artists.json
```

### 2. Análisis de Canción
```bash
# Obtener info de la pista
python get_track.py "70wYA8oYHoMzhRRkARoMhU" --output track_info.json

# Obtener características de audio
python fetch_audio_features.py "70wYA8oYHoMzhRRkARoMhU" --output track_features.json

# Obtener recomendaciones basadas en esta pista
python recommendations.py --seed-tracks "70wYA8oYHoMzhRRkARoMhU" --limit 30 --output similar_tracks.json
```

### 3. Exploración por Género
```bash
# Obtener lanzamientos del género
python get_genre_releases.py "rock" --limit 30 --output rock_releases.json

# Obtener playlists del género
python get_top_playlists.py --genre-name "rock" --limit 25 --output rock_playlists.json

# Buscar artistas del género
python search_tracks.py "rock music" --limit 20 --output rock_search.json
```

### 4. Crear Playlista Personalizada
```bash
# Buscar canciones de tu artista favorito
python search_tracks.py "The Killers" --limit 10 --output seed_songs.json

# Obtener recomendaciones energéticas
python recommendations.py --seed-artists "0C0XlULifJtAgn6ZNCW2eu" --param target_energy=85 --param target_danceability=75 --limit 30 --output high_energy.json
```

### 5. Descargar Previews e Imágenes de Tracks
```bash
# Descargar una canción individual
python download_tracks.py "3n3Ppam7vgaVa1iaRUc9Lp"

# Descargar múltiples canciones
python download_tracks.py 3n3Ppam7vgaVa1iaRUc9Lp 70wYA8oYHoMzhRRkARoMhU 1301WleyT98MSxVHPZCA6M

# Descargar y organizar en carpeta específica
python download_tracks.py "The Killers" "David Bowie" "Queen" --out rock_classics

# Primero buscar, luego descargar
python search_tracks.py "electronic music" --limit 10 --output electronic.json
# Mediante extracto de IDs del JSON y luego:
python download_tracks.py id1 id2 id3 --out electronic_tracks

# Flujo completo: buscar recomendaciones y descargar
python recommendations.py --seed-artists "0C0XlULifJtAgn6ZNCW2eu" --limit 15 --output recs.json
# Extraer IDs del JSON y descargar
python download_tracks.py tracked_id_1 tracked_id_2 ... --out killer_recommendations
```

---

## 💡 Notas Importantes

1. **IDs de Spotify**: Todos los IDs y URIs deben ser válidos de Spotify
2. **Rate Limiting**: La API tiene límites de velocidad; usa `--timeout` si tienes problemas
3. **JSON guardado**: Todos los scripts guardan automáticamente resultados en JSON
4. **Fechas**: Los archivos sin nombre se generan con timestamp: `script_YYYYMMDD_HHMMSS.json`
5. **Errores**: Revisa el mensaje de error mostrado para diagnosticar problemas
6. **Genera releases vacíos**: Si un género no tiene lanzamientos recientes en la BD de Chosic, el field `genre_releases` será `null` - esto es normal y no indica un error
7. **Previews no disponibles**: No todos los tracks tienen preview en Spotify. Si aparece `⚠️  Sin resultado: el track no contiene preview o datos disponibles`, significa que el track no tiene datos en Chosic (puede ser porque no existe, está limitado por región, o simplemente Spotify no proporciona preview). En ese caso solo se descargarán las imágenes del cover.

---

## 🆘 Ayuda

Para ver todas las opciones de cualquier script:
```bash
python script_name.py --help
```

**Ejemplos:**
```bash
python search_tracks.py --help
python get_track.py --help
python get_artists.py --help
python recommendations.py --help
python fetch_audio_features.py --help
python get_genre_releases.py --help
python get_top_playlists.py --help
python download_tracks.py --help
```

---

## 📦 Dependencias

Los scripts requieren:
- Python 3.12+
- ChosicAlpha package
- requests
- dataclasses (incluido en Python 3.7+)

---

**Última actualización**: 9 de febrero de 2026
