"""Capa de servicio para la API de Chosic."""

from __future__ import annotations

import logging
import math
import time
from typing import Any

from .Cliente import ChosicAPI, ChosicAPIError
from .models import ChosicResponse, Features

logger = logging.getLogger(__name__)

MAX_PER_REQUEST = 100


class ChosicService:
    """Capa delgada de servicio que implementa búsquedas y recomendaciones
    usando una instancia de `ChosicAPI`. Mantiene la lógica de paginación
    y mapeo a modelos fuera de los helpers CLI.
    """

    def __init__(self, api: ChosicAPI):
        self.api = api
        # Callback para transformar URIs/URLs de Spotify a su ID puro.
        # Puede ser reemplazado si se desea otra lógica.
        self.id_cleaner = self._extract_spotify_id

    @staticmethod
    def _normalize_params(params: dict[str, Any]) -> dict[str, Any]:
        """Normaliza parámetros: convierte listas a strings separados por comas."""
        out: dict[str, Any] = {}
        for k, v in params.items():
            if v is None:
                continue
            if isinstance(v, (list, tuple)):
                out[k] = ",".join(str(x) for x in v)
            else:
                out[k] = v
        return out

    @staticmethod
    def _as_json(resp: Any) -> dict[str, Any]:
        """Asegurar que se pasa un dict a los parseadores de modelos; manejar tuplas (json, headers)."""
        if isinstance(resp, dict):
            return resp
        if isinstance(resp, (list, tuple)) and len(resp) > 0 and isinstance(resp[0], dict):
            return resp[0]
        return {}

    @staticmethod
    def _extract_spotify_id(value: Any) -> str:
        """Extrae el ID de Spotify a partir de una URI, URL o string.

        Ejemplos soportados:
        - spotify:track:6r7FXNO57mlZCBY6PXcZZT -> 6r7FXNO57mlZCBY6PXcZZT
        - https://open.spotify.com/track/6r7FXNO57mlZCBY6PXcZZT?si=xxx -> 6r7FXNO57mlZCBY6PXcZZT
        - 6r7FXNO57mlZCBY6PXcZZT -> 6r7FXNO57mlZCBY6PXcZZT
        """
        if value is None:
            return ''
        if not isinstance(value, str):
            try:
                return str(value)
            except Exception:
                return ''

        v = value.strip()
        if not v:
            return ''
        # spotify URI
        if v.startswith('spotify:'):
            parts = v.split(':')
            return parts[-1] if parts else v
        # URL from open.spotify.com
        if 'open.spotify.com' in v:
            # remove query params and trailing slashes
            path = v.split('?', 1)[0].rstrip('/')
            parts = path.split('/')
            # last segment is the id
            return parts[-1] if parts else path
        # plain id or other url-like string: strip query
        if '?' in v:
            return v.split('?', 1)[0]
        return v

    def get_track(self, track_id: str) -> Any:
        """Obtiene información de una pista por ID de Spotify."""
        logger.debug(f'get_track iniciado: {track_id}')
        clean_id = self.id_cleaner(track_id) if hasattr(self, 'id_cleaner') else track_id
        logger.debug(f'ID limpio: {clean_id}')
        try:
            resp = self.api.client.request('GET', f'tracks/{clean_id}')
            logger.debug(f'Respuesta recibida para track: {type(resp).__name__}')
        except Exception as e:
            logger.error(f'Error solicitando track: {e}')
            raise
        
        try:
            chosic = ChosicResponse.from_dict({'tracks': [resp]})
            if chosic.tracks and chosic.tracks.items:
                logger.info(f'✓ Track obtenido: {chosic.tracks.items[0].name}')
                return chosic.tracks.items[0]
            logger.error('Respuesta sin tracks válidos')
            raise ChosicAPIError('No se pudo mapear la respuesta a TrackItem')
        except ChosicAPIError:
            raise
        except Exception as e:
            logger.error(f'Error mapeando respuesta de get_track: {e}')
            raise ChosicAPIError('Error mapeando respuesta de get_track')

    def get_artists(self, ids: Any) -> list[Any] | ChosicResponse:
        """Obtiene información de uno o más artistas por ID de Spotify."""
        logger.debug(f'get_artists iniciado: {ids}')
        # Normalizar y extraer IDs si se pasaron URIs/URLs
        if isinstance(ids, (list, tuple)):
            cleaned = [self.id_cleaner(x) if hasattr(self, 'id_cleaner') else str(x) for x in ids]
            ids_param = ",".join(x for x in cleaned if x)
            logger.debug(f'Lista de {len(cleaned)} IDs procesada')
        else:
            # puede ser una cadena separada por comas
            if isinstance(ids, str) and ',' in ids:
                parts = [p.strip() for p in ids.split(',') if p.strip()]
                cleaned = [self.id_cleaner(p) if hasattr(self, 'id_cleaner') else p for p in parts]
                ids_param = ",".join(x for x in cleaned if x)
                logger.debug(f'Cadena de {len(cleaned)} IDs procesada')
            else:
                ids_param = self.id_cleaner(ids) if hasattr(self, 'id_cleaner') else str(ids)
                logger.debug(f'ID individual limpio: {ids_param}')

        try:
            resp = self.api.client.request('GET', 'artists', params={'ids': ids_param})
            logger.debug(f'Respuesta recibida para artistas: {type(resp).__name__}')
        except Exception as e:
            logger.error(f'Error solicitando artistas: {e}')
            raise
        
        try:
            chosic = ChosicResponse.from_dict(self._as_json(resp))
            if chosic.artists and chosic.artists.items:
                logger.info(f'✓ {len(chosic.artists.items)} artistas obtenidos')
                return chosic.artists.items
            logger.error('Respuesta sin artistas válidos')
            raise ChosicAPIError('No se pudo mapear la respuesta a ArtistsCollection')
        except ChosicAPIError:
            raise
        except Exception as e:
            logger.error(f'Error mapeando respuesta de get_artists: {e}')
            raise ChosicAPIError('Error mapeando respuesta de get_artists')

    def recommendations(self, seed_tracks: Any = None, seed_artists: Any = None, limit: int = 100, extra_params: dict[str, Any] | None = None, fetch_all: bool = False, page_size: int = 100) -> ChosicResponse:
        """Obtiene recomendaciones basadas en seeds (tracks/artists)."""
        logger.debug(f'recommendations iniciado: seed_tracks={seed_tracks is not None}, seed_artists={seed_artists is not None}, limit={limit}, fetch_all={fetch_all}')
        params: dict[str, Any] = {}
        if seed_tracks:
            if isinstance(seed_tracks, (list, tuple)):
                cleaned = [self.id_cleaner(x) if hasattr(self, 'id_cleaner') else str(x) for x in seed_tracks]
                params['seed_tracks'] = ",".join(x for x in cleaned if x)
            else:
                params['seed_tracks'] = self.id_cleaner(seed_tracks) if hasattr(self, 'id_cleaner') else str(seed_tracks)
        if seed_artists:
            if isinstance(seed_artists, (list, tuple)):
                cleaned = [self.id_cleaner(x) if hasattr(self, 'id_cleaner') else str(x) for x in seed_artists]
                params['seed_artists'] = ",".join(x for x in cleaned if x)
            else:
                params['seed_artists'] = self.id_cleaner(seed_artists) if hasattr(self, 'id_cleaner') else str(seed_artists)
        params['limit'] = min(int(limit), MAX_PER_REQUEST)
        if extra_params:
            params.update(extra_params)
            logger.debug(f'Parámetros extra: {list(extra_params.keys())}')

        params = self._normalize_params(params)
        logger.debug(f'Parámetros normalizados: {params}')

        if not fetch_all:
            logger.debug('fetch_all=False, solicitando de una sola página')
            try:
                resp = self.api.client.request('GET', 'recommendations', params=params)
                logger.debug(f'Respuesta recibida: {type(resp).__name__}')
            except Exception as e:
                logger.error(f'Error solicitando recommendations: {e}')
                raise
            
            try:
                chosic = ChosicResponse.from_dict(self._as_json(resp))
                items_count = len(chosic.tracks.items) if chosic.tracks else 0
                logger.info(f'✓ Recommendations: {items_count} tracks obtenidos')
                return chosic
            except Exception as e:
                logger.error(f'Error mapeando recommendations: {e}')
                raise ChosicAPIError('No se pudo mapear recommendations a ChosicResponse')

        logger.debug(f'fetch_all=True iniciado: limit={limit}, page_size={page_size}')
        
        params['limit'] = min(int(page_size), MAX_PER_REQUEST)
        params['page'] = 1
        logger.debug(f'Solicitando página 1 con page_size={params["limit"]}')
        
        try:
            resp_json, headers = self.api.client.request('GET', 'recommendations', params=params, return_headers=True)
            logger.debug(f'Respuesta página 1: {type(resp_json).__name__}, headers: {list(headers.keys()) if isinstance(headers, dict) else "N/A"}')
        except Exception as e:
            logger.error(f'Error en solicitud de página 1: {e}')
            raise
        
        try:
            aggregated = resp_json.copy() if isinstance(resp_json, dict) else {'tracks': []}
        except Exception as e:
            logger.warning(f'Error copiando respuesta inicial: {e}')
            aggregated = {'tracks': []}

        def _merge_into(agg, part):
            if not isinstance(part, dict):
                return
            if 'tracks' in part and part['tracks']:
                if 'tracks' not in agg or not agg['tracks']:
                    agg['tracks'] = part['tracks']
                else:
                    if isinstance(agg['tracks'], dict) and isinstance(part['tracks'], dict):
                        a_items = agg['tracks'].get('items', [])
                        p_items = part['tracks'].get('items', [])
                        agg['tracks']['items'] = a_items + p_items
                    elif isinstance(agg['tracks'], list) and isinstance(part['tracks'], list):
                        agg['tracks'] = agg['tracks'] + part['tracks']

        _merge_into(aggregated, resp_json)

        # Ensure headers is a dict-like object to avoid attribute errors when it's a string or None
        if not isinstance(headers, dict):
            headers = {}

        total_pages = None
        try:
            total_pages = int(headers.get('X-WP-TotalPages') or headers.get('x-wp-totalpages') or 0) or None
        except Exception:
            total_pages = None

        if total_pages is None:
            try:
                total_items = int(headers.get('X-WP-Total') or headers.get('x-wp-total') or 0)
                if total_items > 0:
                    total_pages = math.ceil(total_items / int(params.get('limit', page_size)))
            except Exception:
                total_pages = None

        if total_pages is not None and total_pages >= 2:
            logger.info(f'Descargando páginas 2-{total_pages} (total: {total_pages} páginas conocidas)')
            for page in range(2, total_pages + 1):
                logger.debug(f'Descargando página {page}/{total_pages}')
                params['page'] = page
                try:
                    part_json = self.api.client.request('GET', 'recommendations', params=self._normalize_params(params))
                    _merge_into(aggregated, part_json)
                    logger.debug(f'Página {page} mergeada')
                except Exception as e:
                    logger.error(f'Error descargando página {page}: {e}')
                    break
                # Agregar delay entre peticiones para evitar bloqueo de Cloudflare
                time.sleep(0.5)
        else:
            logger.info('Total de páginas desconocido, usando estrategia fallback')
            page = 2
            # Calcular máximo de páginas basado en limit y page_size para evitar infinite loop
            max_pages_to_fetch = math.ceil(limit / page_size) if page_size > 0 else 1
            pages_fetched = 1  # Ya tenemos page 1
            logger.debug(f'Máximo de páginas a solicitar: {max_pages_to_fetch}')
            
            while pages_fetched < max_pages_to_fetch:
                logger.debug(f'Descargando página {page} (fallback, límite: {max_pages_to_fetch})')
                params['page'] = page
                try:
                    part_json = self.api.client.request('GET', 'recommendations', params=self._normalize_params(params))
                except Exception as e:
                    logger.error(f'Error descargando página {page}: {e}')
                    break
                    
                had_items = False
                if isinstance(part_json, dict):
                    tr = part_json.get('tracks')
                    if tr:
                        if isinstance(tr, dict):
                            items = tr.get('items')
                            if isinstance(items, (list, tuple)) and len(items) > 0:
                                had_items = True
                        elif isinstance(tr, list) and len(tr) > 0:
                            had_items = True
                
                if not had_items:
                    logger.info(f'Página {page} sin items, deteniendo')
                    break
                
                _merge_into(aggregated, part_json)
                logger.debug(f'Página {page} mergeada')
                
                small_batch = False
                try:
                    tr = part_json.get('tracks') if isinstance(part_json, dict) else None
                    if tr:
                        if isinstance(tr, dict):
                            items = tr.get('items')
                            if isinstance(items, (list, tuple)) and len(items) < int(params.get('limit', page_size)):
                                small_batch = True
                        elif isinstance(tr, list) and len(tr) < int(params.get('limit', page_size)):
                            small_batch = True
                except Exception:
                    small_batch = False

                if small_batch:
                    logger.info(f'Página {page} tiene menos items que page_size, deteniendo')
                    break
                # Agregar delay entre peticiones para evitar bloqueo de Cloudflare
                time.sleep(0.5)
                page += 1
                pages_fetched += 1

        try:
            chosic = ChosicResponse.from_dict(aggregated)
            items_count = len(chosic.tracks.items) if chosic.tracks else 0
            logger.info(f'✓ Recommendations paginadas completadas: {items_count} tracks agregados')
            return chosic
        except Exception as e:
            logger.error(f'Error mapeando recommendations paginadas: {e}')
            raise ChosicAPIError('No se pudo mapear recommendations paginadas a ChosicResponse')

    def search(self, q: str, type_: str = 'track', limit: int = 10, extra_params: dict[str, Any] | None = None, fetch_all: bool = False, page_size: int = 10) -> ChosicResponse:
        """Realiza búsqueda de tracks, artistas o álbumes."""
        logger.debug(f'search iniciado: q="{q}", type={type_}, limit={limit}, fetch_all={fetch_all}')
        params = {'q': q, 'type': type_, 'limit': min(int(limit), MAX_PER_REQUEST)}
        if extra_params:
            params.update(extra_params)
            logger.debug(f'Parámetros extra: {list(extra_params.keys())}')

        params = self._normalize_params(params)
        logger.debug(f'Parámetros normalizados: {params}')

        if not fetch_all:
            logger.debug('fetch_all=False, solicitando búsqueda de una sola página')
            try:
                resp = self.api.client.request('GET', 'search', params=params)
                logger.debug(f'Respuesta recibida: {type(resp).__name__}')
            except Exception as e:
                logger.error(f'Error solicitando search: {e}')
                raise
            
            try:
                chosic = ChosicResponse.from_dict(self._as_json(resp))
                tracks_count = len(chosic.tracks.items) if chosic.tracks else 0
                artists_count = len(chosic.artists.items) if chosic.artists else 0
                logger.info(f'✓ Search: {tracks_count} tracks, {artists_count} artists obtenidos')
                return chosic
            except Exception as e:
                logger.error(f'Error mapeando search: {e}')
                raise ChosicAPIError('No se pudo mapear search a ChosicResponse')

        logger.debug(f'fetch_all=True iniciado: q="{q}", type={type_}, limit={limit}, page_size={page_size}')
        
        params['limit'] = min(int(page_size), MAX_PER_REQUEST)
        params['page'] = 1
        logger.debug(f'Solicitando página 1 con page_size={params["limit"]}')

        try:
            resp_json, headers = self.api.client.request('GET', 'search', params=params, return_headers=True)
            logger.debug(f'Respuesta página 1: {type(resp_json).__name__}, headers: {list(headers.keys()) if isinstance(headers, dict) else "N/A"}')
        except Exception as e:
            logger.error(f'Error en solicitud de página 1: {e}')
            raise
        
        try:
            aggregated = resp_json.copy() if isinstance(resp_json, dict) else {'tracks': []}
        except Exception as e:
            logger.warning(f'Error copiando respuesta inicial: {e}')
            aggregated = {'tracks': []}

        def _merge_into(agg, part):
            for key in ('tracks', 'artists'):
                if key in part and part[key]:
                    if key not in agg or not agg[key]:
                        agg[key] = part[key]
                    else:
                        if isinstance(agg[key], dict) and isinstance(part[key], dict):
                            a_items = agg[key].get('items', [])
                            p_items = part[key].get('items', [])
                            agg[key]['items'] = a_items + p_items
                        elif isinstance(agg[key], list) and isinstance(part[key], list):
                            agg[key] = agg[key] + part[key]

        _merge_into(aggregated, resp_json)

        # Ensure headers is a dict-like object to avoid attribute errors when it's a string or None
        if not isinstance(headers, dict):
            headers = {}

        total_pages = None
        try:
            total_pages = int(headers.get('X-WP-TotalPages') or headers.get('x-wp-totalpages') or 0) or None
        except Exception:
            total_pages = None

        if total_pages is None:
            try:
                total_items = int(headers.get('X-WP-Total') or headers.get('x-wp-total') or 0)
                if total_items > 0:
                    total_pages = math.ceil(total_items / int(params.get('limit', page_size)))
            except Exception:
                total_pages = None

        if total_pages is not None and total_pages >= 2:
            logger.info(f'Descargando páginas 2-{total_pages} (total: {total_pages} páginas conocidas)')
            for page in range(2, total_pages + 1):
                logger.debug(f'Descargando página {page}/{total_pages}')
                params['page'] = page
                try:
                    part_json = self.api.client.request('GET', 'search', params=self._normalize_params(params))
                    _merge_into(aggregated, part_json)
                    logger.debug(f'Página {page} mergeada')
                except Exception as e:
                    logger.error(f'Error descargando página {page}: {e}')
                    break
                # Agregar delay entre peticiones para evitar bloqueo de Cloudflare
                time.sleep(0.5)
        else:
            logger.info('Total de páginas desconocido, usando estrategia fallback')
            page = 2
            # Calcular máximo de páginas basado en limit y page_size para evitar infinite loop
            max_pages_to_fetch = math.ceil(limit / page_size) if page_size > 0 else 1
            pages_fetched = 1  # Ya tenemos page 1
            logger.debug(f'Máximo de páginas a solicitar: {max_pages_to_fetch}')
            
            while pages_fetched < max_pages_to_fetch:
                logger.debug(f'Descargando página {page} (fallback, límite: {max_pages_to_fetch})')
                params['page'] = page
                try:
                    part_json = self.api.client.request('GET', 'search', params=self._normalize_params(params))
                except Exception as e:
                    logger.error(f'Error descargando página {page}: {e}')
                    break
                    
                had_items = False
                if isinstance(part_json, dict):
                    for key in ('tracks', 'artists'):
                        v = part_json.get(key)
                        if v:
                            if isinstance(v, dict):
                                items = v.get('items')
                                if isinstance(items, (list, tuple)) and len(items) > 0:
                                    had_items = True
                            elif isinstance(v, (list, tuple)) and len(v) > 0:
                                had_items = True
                
                if not had_items:
                    logger.info(f'Página {page} sin items, deteniendo')
                    break
                
                _merge_into(aggregated, part_json)
                logger.debug(f'Página {page} mergeada')
                
                small_batch = False
                try:
                    tr = part_json.get('tracks') if isinstance(part_json, dict) else None
                    if tr:
                        if isinstance(tr, dict):
                            items = tr.get('items')
                            if isinstance(items, (list, tuple)) and len(items) < int(params.get('limit', page_size)):
                                small_batch = True
                        elif isinstance(tr, list) and len(tr) < int(params.get('limit', page_size)):
                            small_batch = True
                except Exception:
                    small_batch = False

                if small_batch:
                    logger.info(f'Página {page} tiene menos items que page_size, deteniendo')
                    break
                # Agregar delay entre peticiones para evitar bloqueo de Cloudflare
                time.sleep(0.5)
                page += 1
                pages_fetched += 1

        try:
            chosic = ChosicResponse.from_dict(aggregated)
            tracks_count = len(chosic.tracks.items) if chosic.tracks else 0
            artists_count = len(chosic.artists.items) if chosic.artists else 0
            logger.info(f'✓ Search paginada completada: {tracks_count} tracks, {artists_count} artists agregados')
            return chosic
        except Exception as e:
            logger.error(f'Error mapeando search paginada: {e}')
            raise ChosicAPIError('No se pudo mapear search paginada a ChosicResponse')

    def fetch_audio_features(self, track_id: str, timeout: float | None = None) -> Features:
        """Obtiene características de audio de una pista."""
        logger.debug(f'fetch_audio_features iniciado: {track_id}')
        if timeout is None:
            timeout = getattr(self.api.client, 'timeout', 15)
        clean_id = self.id_cleaner(track_id) if hasattr(self, 'id_cleaner') else track_id
        endpoint = f'audio-features/{clean_id}'
        logger.debug(f'ID limpio: {clean_id}, timeout: {timeout}s')
        
        try:
            resp = self.api.client.request('GET', endpoint, params=None, timeout=timeout)
            logger.debug(f'Respuesta recibida: {type(resp).__name__}')
        except Exception as e:
            logger.error(f'Error solicitando audio features: {e}')
            raise
        
        try:
            feats = Features.from_dict(resp if isinstance(resp, dict) else {})
            logger.info(f'✓ Audio features obtenidas para {clean_id}')
            return feats
        except Exception as e:
            logger.error(f'Error mapeando audio features: {e}')
            raise ChosicAPIError('No se pudo mapear audio features a Features')

    def get_genre_releases(self, genre: str, limit: int | None = None, extra_params: dict[str, Any] | None = None) -> ChosicResponse:
        """Obtiene lanzamientos por género."""
        logger.debug(f'get_genre_releases iniciado: genre={genre}, limit={limit}')
        params: dict[str, Any] = {'genre': genre}
        if limit is not None:
            params['limit'] = int(limit)
        if extra_params:
            params.update(extra_params)
            logger.debug(f'Parámetros extra: {list(extra_params.keys())}')

        params = self._normalize_params(params)

        try:
            resp = self.api.client.request('GET', 'genre-releases', params=params)
            logger.debug(f'Respuesta recibida: {type(resp).__name__}')
        except Exception as e:
            logger.error(f'Error solicitando genre-releases: {e}')
            raise
        
        try:
            chosic = ChosicResponse.from_dict(resp) # type: ignore
            items_count = len(chosic.tracks.items) if chosic.tracks else 0
            logger.info(f'✓ Lanzamientos del género "{genre}": {items_count} tracks')
            return chosic
        except Exception as e:
            logger.error(f'Error mapeando genre-releases: {e}')
            raise ChosicAPIError('No se pudo mapear genre-releases a ChosicResponse')

    def get_top_playlists(self, artist_id: str | None = None, genre_name: str | None = None, limit: int | None = None, extra_params: dict[str, Any] | None = None) -> ChosicResponse:
        """Obtiene top playlists filtrando por `artist_id` y/o `genre_name`.

        Devuelve un `ChosicResponse` mapeado donde `top_playlists` contendrá
        la colección si la respuesta es compatible.
        """
        logger.debug(f'get_top_playlists iniciado: artist_id={artist_id}, genre_name={genre_name}, limit={limit}')
        params: dict[str, Any] = {}
        if artist_id is not None and artist_id != '':
            params['artist_id'] = self.id_cleaner(artist_id) if hasattr(self, 'id_cleaner') else artist_id
        if genre_name is not None and genre_name != '':
            params['genre_name'] = genre_name
        if limit is not None:
            params['limit'] = int(limit)
        if extra_params:
            params.update(extra_params)
            logger.debug(f'Parámetros extra: {list(extra_params.keys())}')

        params = self._normalize_params(params)

        try:
            resp = self.api.client.request('GET', 'top-playlists', params=params)
            logger.debug(f'Respuesta recibida: {type(resp).__name__}')
        except Exception as e:
            logger.error(f'Error solicitando top-playlists: {e}')
            raise
        
        try:
            chosic = ChosicResponse.from_dict(resp) # type: ignore
            items_count = len(chosic.top_playlists.items) if chosic.top_playlists else 0
            logger.info(f'✓ Top playlists obtenidas: {items_count} playlists')
            return chosic
        except Exception as e:
            logger.error(f'Error mapeando top-playlists: {e}')
            raise ChosicAPIError('No se pudo mapear top-playlists a ChosicResponse')
