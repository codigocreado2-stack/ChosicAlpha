"""Modelos de datos para la API de Chosic.

Incluye dataclasses para tracks, artistas, features, géneros, playlists, etc.
y sus colecciones correspondientes.
"""

from __future__ import annotations

import json
from pathlib import Path
from dataclasses import dataclass
from typing import Any

import requests

# --- 1. MODELOS BASE ---

@dataclass
class BaseItem:
    """Modelo base para items con id, nombre e imagen."""

    id: str
    name: str
    image: str | None

@dataclass
class SimpleArtist:
    """
    Representa un artista simplificado dentro de la lista 'artists' de un TRACK.
    En info01.json los artistas dentro de un track solo tienen id y name.
    """
    id: str
    name: str

# --- 2. MODELOS DE ARTISTAS ---

@dataclass
class ArtistItem(BaseItem):
    """
    Representa un artista básico con imagen.
    Usado cuando la API devuelve datos resumidos.
    """
    pass

@dataclass
class ArtistDetail(ArtistItem):
    """
    Representa la información completa de un artista.
    Hereda de ArtistItem para ser compatible con listas de artistas.
    Incluye popularidad, seguidores, géneros, etc.
    """

    popularity: int
    followers: int
    updated_date: str
    genres: list[str]
    cached: int

    @property
    def followers_int(self) -> int:
        """Retorna los seguidores como entero (ya es int)."""
        return int(self.followers or 0)

    @classmethod
    def from_dict(cls, data: dict) -> ArtistDetail:
        def _to_int(v):
            if v is None:
                return 0
            try:
                return int(str(v).replace(',', ''))
            except Exception:
                try:
                    return int(v)
                except Exception:
                    return 0

        return cls(
            id=str(data.get('id') or ''),
            name=str(data.get('name') or ''),
            image=str(data.get('image') or ''),
            popularity=_to_int(data.get('popularity')),
            followers=_to_int(data.get('followers')),
            updated_date=str(data.get('updated_date') or ''),
            genres=data.get('genres') or [],
            cached=_to_int(data.get('cached'))
        )

    def resolved_genres(self, genre_map: GenreMap | dict[str, str] | None = None) -> list[str]:
        """Devuelve la lista de géneros resuelta usando `genre_map`.

        - Si `genre_map` es `None`, retorna `self.genres` tal cual.
        - `genre_map` puede ser una instancia de `GenreMap` o un `dict`.
        """
        if not self.genres:
            return []
        if genre_map is None:
            return list(self.genres)

        resolved: list[str] = []
        if isinstance(genre_map, dict):
            for g in self.genres:
                resolved.append(genre_map.get(g, g))
            return resolved

        # Asumir objeto con método `resolve`
        try:
            for g in self.genres:
                val = genre_map.resolve(g, g)  # type: ignore[attr-defined]
                resolved.append(val if val is not None else g)
            return resolved
        except Exception:
            return list(self.genres)

# --- 3. MODELOS DE TRACKS Y ALBUMS ---

@dataclass
class AlbumItem:
    """Representa el objeto 'album' dentro de un track."""

    id: str
    name: str
    album_type: str
    release_date: str
    release_date_precision: str
    image_default: str | None
    image_large: str | None

    @classmethod
    def from_dict(cls, data: dict | None) -> AlbumItem | None:
        if not data:
            return None
        return cls(
            id=str(data.get('id', '') or ''),
            name=str(data.get('name', '') or ''),
            album_type=str(data.get('album_type', '') or ''),
            release_date=str(data.get('release_date', '') or ''),
            release_date_precision=str(data.get('release_date_precision', '') or ''),
            image_default=data.get('image_default') or data.get('image') or None,
            image_large=data.get('image_large') or None,
        )

@dataclass
class TrackItem(BaseItem):
    """
    Representa una canción completa.
    La imagen base se rellena con la imagen por defecto del álbum.
    """

    artists: list[SimpleArtist]
    album: AlbumItem | None
    preview_url: str | None
    duration_ms: int
    popularity: int

    @property
    def artist_display(self) -> str:
        """Retorna los nombres de los artistas unidos por coma."""
        return ", ".join(a.name for a in self.artists)

    @classmethod
    def from_dict(cls, data: dict) -> TrackItem:
        # parse artists
        raw_artists = data.get('artists') or []
        parsed_artists: list[SimpleArtist] = []
        if isinstance(raw_artists, (list, tuple)):
            for a in raw_artists:
                try:
                    parsed_artists.append(SimpleArtist(id=a.get('id', '') or '', name=a.get('name', '') or ''))
                except Exception:
                    # skip malformed artist entries
                    continue
        # fallback: single 'artist' string
        if not parsed_artists and 'artist' in data and isinstance(data.get('artist'), str):
            parsed_artists = [SimpleArtist(id='', name=data.get('artist', ''))]

        # album
        alb = AlbumItem.from_dict(data.get('album') or {})

        # image selection: track image or album image_default
        current_image = data.get('image') or (alb.image_default if alb and alb.image_default else None)

        def _to_int(v):
            if v is None:
                return 0
            try:
                return int(str(v).replace(',', ''))
            except Exception:
                try:
                    return int(v)
                except Exception:
                    return 0

        return cls(
            id=str(data.get('id') or ''),
            name=str(data.get('name') or ''),
            image=current_image,
            artists=parsed_artists,
            album=alb,
            preview_url=data.get('preview_url'),
            duration_ms=_to_int(data.get('duration_ms')),
            popularity=_to_int(data.get('popularity')),
        )


# --- 4. MODELO DE FEATURES (AUDIO FEATURES) ---
@dataclass
class Features:
    """Modelo para las características de audio devueltas por el endpoint de Chosic.
    Ejemplo JSON:
    {
        "id": "...",
        "duration_ms": 326467,
        "danceability": 0.692,
        "energy": 0.744,
        ...
    }
    """
    id: str
    duration_ms: int
    danceability: float
    energy: float
    speechiness: float
    acousticness: float
    instrumentalness: float
    liveness: float
    valence: float
    loudness: float
    tempo: float
    key: int
    mode: int
    time_signature: int

    @classmethod
    def from_dict(cls, data: dict) -> Features:
        """Crea una instancia de Features a partir de un dict."""

        def _f(k, default=0):
            v = data.get(k, default)
            try:
                return float(v)
            except Exception:
                try:
                    return float(str(v).replace(',', '.'))
                except Exception:
                    return float(default)

        def _i(k, default=0):
            try:
                return int(data.get(k, default) or default)
            except Exception:
                try:
                    return int(float(str(data.get(k, default))))
                except Exception:
                    return int(default)

        return cls(
            id=str(data.get('id', '')),
            duration_ms=_i('duration_ms'),
            danceability=_f('danceability'),
            energy=_f('energy'),
            speechiness=_f('speechiness'),
            acousticness=_f('acousticness'),
            instrumentalness=_f('instrumentalness'),
            liveness=_f('liveness'),
            valence=_f('valence'),
            loudness=_f('loudness'),
            tempo=_f('tempo'),
            key=_i('key'),
            mode=_i('mode'),
            time_signature=_i('time_signature')
        )


# --- 5. GÉNEROS / MAPEOS ---
@dataclass
class GenreMap:
    """Carga y resuelve el diccionario de géneros.

    Soporta JSON con una lista (se mapea cada elemento a sí mismo)
    o un objeto/dict con mapeos explícitos.
    """

    mapping: dict[str, str]

    @classmethod
    def from_dict(cls, data: Any) -> GenreMap:
        """Crea un GenreMap a partir de un diccionario o lista."""
        if isinstance(data, dict):
            return cls(mapping={str(k): str(v) for k, v in data.items()})
        if isinstance(data, list):
            return cls(mapping={str(x): str(x) for x in data})
        raise TypeError('Unsupported data type for GenreMap')

    @classmethod
    def from_file(cls, path: str | Path) -> GenreMap:
        """Crea un GenreMap a partir de un archivo JSON."""
        p = Path(path)
        with p.open('r', encoding='utf-8') as fh:
            data = json.load(fh)
        return cls.from_dict(data)

    @classmethod
    def from_url(cls, url: str, timeout: int = 10) -> GenreMap:
        """Crea un GenreMap a partir de una URL."""
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        return cls.from_dict(data)

    def resolve(self, key: str, default: str | None = None) -> str | None:
        """Resuelve una clave de género a su valor mapeado."""
        return self.mapping.get(key) if key in self.mapping else default


# --- 5. RELEASES POR GÉNERO ---
@dataclass
class GenreReleaseItem:
    """Representa un lanzamiento dentro de una colección por género."""

    album_id: str
    album_name: str
    album_url: str | None
    album_img: str | None
    release_date: str | None
    artist_name: str | None
    album_type: str | None

    @classmethod
    def from_dict(cls, data: dict) -> GenreReleaseItem:
        if not data:
            return cls(album_id='', album_name='', album_url=None, album_img=None, release_date=None, artist_name=None, album_type=None)

        # Normalizar distintos nombres de campo que puedan venir desde el endpoint
        return cls(
            album_id=str(data.get('albumId') or data.get('album_id') or data.get('id') or ''),
            album_name=str(data.get('albumName') or data.get('album_name') or data.get('name') or ''),
            album_url=data.get('albumUrl') or data.get('album_url') or None,
            album_img=data.get('albumImg') or data.get('album_img') or data.get('image') or None,
            release_date=data.get('release_date') or data.get('releaseDate') or None,
            artist_name=data.get('artistName') or data.get('artist_name') or data.get('artist') or None,
            album_type=data.get('album_type') or data.get('albumType') or None,
        )


@dataclass
class GenreReleasesCollection:
    """Colección de lanzamientos por género."""

    items: list[GenreReleaseItem]


# --- 6. TOP PLAYLISTS (top-playlists endpoint) ---
@dataclass
class TopPlaylistItem:
    """Representa un top playlist."""

    id: str
    name: str
    url: str | None
    image: str | None
    description: str | None
    tracks_count: int | None
    followers: int | None
    parent_genre: str | None

    @classmethod
    def from_dict(cls, data: dict) -> TopPlaylistItem:
        if not data:
            return cls(id='', name='', url=None, image=None, description=None, tracks_count=None, followers=None, parent_genre=None)

        def _to_int(v):
            if v is None:
                return None
            try:
                return int(str(v).replace(',', ''))
            except Exception:
                try:
                    return int(v)
                except Exception:
                    return None

        return cls(
            id=str(data.get('id') or data.get('playlist_id') or data.get('playlistId') or data.get('uri') or ''),
            name=str(data.get('name') or data.get('playlistName') or ''),
            url=data.get('playlist_url') or data.get('playlistUrl') or data.get('url') or None,
            image=data.get('image') or data.get('playlist_img') or data.get('playlistImage') or None,
            description=data.get('description') or data.get('desc') or None,
            tracks_count=_to_int(data.get('tracks_count') or data.get('num_tracks') or data.get('track_count')),
            followers=_to_int(data.get('followers') or data.get('followers_count')),
            parent_genre=data.get('parent_genre') or data.get('genre_name') or None,
        )


@dataclass
class TopPlaylistsCollection:
    """Colección de top playlists."""

    items: list[TopPlaylistItem]


# --- 4. COLECCIONES ---


@dataclass
class ArtistsCollection:
    """Colección de artistas (puede contener ArtistItem o ArtistDetail gracias a la herencia)."""

    items: list[ArtistItem]


@dataclass
class TracksCollection:
    """Colección de pistas."""

    items: list[TrackItem]

# --- 5. RESPUESTA PRINCIPAL ---

@dataclass
class ChosicResponse:
    """Respuesta principal unificada de la API de Chosic."""

    tracks: TracksCollection | None = None
    artists: ArtistsCollection | None = None
    features: Features | None = None
    genre_releases: GenreReleasesCollection | None = None
    top_playlists: TopPlaylistsCollection | None = None

    @classmethod
    def from_dict(cls, data: dict) -> ChosicResponse:
        """Mapea un diccionario a una respuesta de Chosic."""
        tracks_obj = None
        artists_obj = None

        # --- A. PROCESAR TRACKS ---
        if 'tracks' in data and data['tracks'] is not None:
            raw_data = data['tracks']
            items_list = []
            
            # Manejar si es lista directa o objeto paginado
            if isinstance(raw_data, list):
                items_list = raw_data
            elif isinstance(raw_data, dict):
                items_list = raw_data.get('items', [])

            # Usar el constructor centralizado para parsear cada track
            parsed_items = [TrackItem.from_dict(x) for x in items_list if isinstance(x, dict) and x]

            tracks_obj = TracksCollection(items=parsed_items)

        # --- B. PROCESAR ARTISTS ---
        if 'artists' in data and data['artists'] is not None:
            raw_data = data['artists']
            items_list = []
            
            if isinstance(raw_data, list):
                items_list = raw_data
            elif isinstance(raw_data, dict):
                items_list = raw_data.get('items', [])

            parsed_items = []
            for x in items_list:
                # Lógica para detectar si es un Artista Detallado o Simple
                # Si tiene campos extra como 'popularity' o 'followers', usamos ArtistDetail
                if 'popularity' in x or 'followers' in x or 'genres' in x:
                    item = ArtistDetail.from_dict(x)
                else:
                    item = ArtistItem(
                        id=x.get('id', ''), 
                        name=x.get('name', ''), 
                        image=x.get('image', '')
                    )
                parsed_items.append(item)
            
            artists_obj = ArtistsCollection(items=parsed_items)

        # Si no vino bajo 'artists' pero el body parece ser un artista único, mapearlo
        if artists_obj is None:
            if isinstance(data, dict) and ('popularity' in data or 'followers' in data or 'genres' in data) and data.get('id'):
                try:
                    artists_obj = ArtistsCollection(items=[ArtistDetail.from_dict(data)])
                except Exception:
                    artists_obj = None

        # --- C. PROCESAR FEATURES ---
        features_obj = None

        # El endpoint puede devolver las features directamente en el body
        # o bajo una clave 'features'. Soportamos ambos casos.
        raw_features = None
        if 'features' in data and data['features'] is not None:
            raw_features = data['features']
        else:
            # Detectar si el dict raíz contiene claves típicas de features
            feature_keys = {'danceability', 'energy', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence', 'loudness', 'tempo', 'key', 'mode', 'time_signature'}
            if any(k in data for k in feature_keys):
                raw_features = data

        if isinstance(raw_features, dict):
            features_obj = Features.from_dict(raw_features)

        # --- D. PROCESAR GENRE RELEASES ---
        genre_releases_obj: GenreReleasesCollection | None = None
        raw_genre_releases = None

        if 'genre_releases' in data and data['genre_releases'] is not None:
            raw_genre_releases = data['genre_releases']
        else:
            # Si el body es una lista directa de releases
            if isinstance(data, list):
                if data and isinstance(data[0], dict) and ('albumId' in data[0] or 'album_id' in data[0] or 'albumName' in data[0]):
                    raw_genre_releases = data
            # O si viene paginado bajo 'items'
            elif isinstance(data, dict) and 'items' in data and isinstance(data['items'], list):
                first = data['items'][0] if data['items'] else None
                if isinstance(first, dict) and ('albumId' in first or 'albumName' in first):
                    raw_genre_releases = data['items']

        if isinstance(raw_genre_releases, list):
            parsed_releases = [GenreReleaseItem.from_dict(x) for x in raw_genre_releases if isinstance(x, dict)]
            genre_releases_obj = GenreReleasesCollection(items=parsed_releases)

        # --- E. PROCESAR TOP PLAYLISTS ---
        top_playlists_obj: TopPlaylistsCollection | None = None
        raw_top = None

        if 'top_playlists' in data and data['top_playlists'] is not None:
            raw_top = data['top_playlists']
        else:
            # Si el body es una lista directa de playlists
            if isinstance(data, list):
                if data and isinstance(data[0], dict) and ('playlist_id' in data[0] or 'parent_genre' in data[0] or 'playlistName' in data[0]):
                    raw_top = data
            # O si viene paginado bajo 'items'
            elif isinstance(data, dict) and 'items' in data and isinstance(data['items'], list):
                first = data['items'][0] if data['items'] else None
                if isinstance(first, dict) and ('playlist_id' in first or 'parent_genre' in first or 'playlistName' in first):
                    raw_top = data['items']

        if isinstance(raw_top, list):
            parsed_top = [TopPlaylistItem.from_dict(x) for x in raw_top if isinstance(x, dict)]
            top_playlists_obj = TopPlaylistsCollection(items=parsed_top)

        return cls(tracks=tracks_obj, artists=artists_obj, features=features_obj, genre_releases=genre_releases_obj, top_playlists=top_playlists_obj)