"""
ChosicAlpha: Cliente y utilidades para la API de Chosic (Playlist Generator).

Módulos principales:
- Cliente: Gestión HTTP y autenticación con la API de Chosic
- Service: Capa de servicio con métodos para búsqueda, recomendaciones, etc.
- Busqueda: Helpers públicos para búsquedas y funciones _auto
- Downloader: Descarga de previews e imágenes de pistas
- models: Modelos de datos (TrackItem, ArtistDetail, ChosicResponse, etc.)
"""

__version__ = "0.0.1"
__author__ = "codigocreado2-stack"

# --- Cliente ---
from .Cliente import (
    ChosicAPI,
    ChosicAPIError,
    ChosicHttpClient,
    create_chosic_api,
    create_ready_api_from_args,
)

# --- Service ---
from .Service import ChosicService

# --- Models ---
from .models import (
    BaseItem,
    ChosicResponse,
    TrackItem,
    ArtistItem,
    ArtistDetail,
    AlbumItem,
    SimpleArtist,
    Features,
    GenreMap,
    GenreReleaseItem,
    GenreReleasesCollection,
    TopPlaylistItem,
    TopPlaylistsCollection,
    TracksCollection,
    ArtistsCollection,
)

# --- JSON Utils ---
from .json_utils import (
    DataclassEncoder,
    dump_json,
    dumps_json,
)

# --- Búsqueda (funciones públicas) ---
from .Busqueda import (
    get_track,
    get_track_auto,
    get_artists,
    get_artists_auto,
    recommendations,
    recommendations_auto,
    search,
    search_auto,
    fetch_audio_features,
    fetch_audio_features_auto,
    fetch_all_genres_auto,
    get_genre_releases,
    get_genre_releases_auto,
    get_top_playlists,
    get_top_playlists_auto,
    search_and_download,
    search_and_download_auto,
    ThreadRunner,
    SUPPORTED_EXTRA_PARAMS,
)

# --- Downloader ---
from .Downloader import download_track_assets

__all__ = [
    # Version
    "__version__",
    # Cliente
    "ChosicAPI",
    "ChosicAPIError",
    "ChosicHttpClient",
    "create_chosic_api",
    "create_ready_api_from_args",
    # Service
    "ChosicService",
    # Models
    "BaseItem",
    "ChosicResponse",
    "TrackItem",
    "ArtistItem",
    "ArtistDetail",
    "AlbumItem",
    "SimpleArtist",
    "Features",
    "GenreMap",
    "GenreReleaseItem",
    "GenreReleasesCollection",
    "TopPlaylistItem",
    "TopPlaylistsCollection",
    "TracksCollection",
    "ArtistsCollection",
    # JSON Utils
    "DataclassEncoder",
    "dump_json",
    "dumps_json",
    # Búsqueda
    "get_track",
    "get_track_auto",
    "get_artists",
    "get_artists_auto",
    "recommendations",
    "recommendations_auto",
    "search",
    "search_auto",
    "fetch_audio_features",
    "fetch_audio_features_auto",
    "fetch_all_genres_auto",
    "get_genre_releases",
    "get_genre_releases_auto",
    "get_top_playlists",
    "get_top_playlists_auto",
    "search_and_download",
    "search_and_download_auto",
    "ThreadRunner",
    "SUPPORTED_EXTRA_PARAMS",
    # Downloader
    "download_track_assets",
]
