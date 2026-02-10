"""Cliente HTTP para la API de Chosic."""

from __future__ import annotations

import logging
import os
import sys
from typing import Any

import requests
from requests.structures import CaseInsensitiveDict

logger = logging.getLogger(__name__)


class ChosicAPIError(Exception):
    """Base exception de Chosic API errors."""
    
    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(f"{message} (Status: {status_code})" if status_code else message)


class ChosicHttpClient:
    """Responsable del transporte HTTP y manejo de errores."""

    DEFAULT_TIMEOUT = 10.0
    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    def __init__(
        self,
        base_url: str,
        *,
        session: requests.Session | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        user_agent: str = DEFAULT_USER_AGENT,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()
        self._setup_headers(user_agent)

    def _setup_headers(self, user_agent: str) -> None:
        """Configura los headers por defecto para la sesión."""
        default_headers = {
            "User-Agent": user_agent,
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            "Origin": "https://www.chosic.com",
            "Referer": "https://www.chosic.com/playlist-generator/",
            "X-Requested-With": "XMLHttpRequest",
        }
        self.session.headers.update(default_headers)

    def set_cookie(self, cookie_header: str) -> None:
        """Parsea un header de cookies tipo 'k=v; k2=v2' y lo añade al cookiejar."""
        if not cookie_header:
            return
        try:
            parts = [p.strip() for p in cookie_header.split(";") if p.strip()]
            cookie_dict: dict[str, str] = {}
            for part in parts:
                if "=" in part:
                    k, v = part.split("=", 1)
                    cookie_dict[k.strip()] = v.strip()
            if cookie_dict:
                self.session.cookies.update(cookie_dict)
        except Exception as exc:
            logger.warning(f"set_cookie: no se pudo parsear cookie: {exc}")

    def set_nonce(self, nonce: str) -> None:
        """Ajusta el header X-WP-Nonce en la sesión."""
        if not nonce:
            return
        self.session.headers["X-WP-Nonce"] = nonce

    def set_app(self, app: str) -> None:
        """Ajusta el header `app` en la sesión."""
        if not app:
            return
        self.session.headers["app"] = app

    def request(
        self,
        method: str, 
        endpoint: str,
        return_headers: bool = False,
        **kwargs: Any) -> dict[str, Any] | tuple[Any, CaseInsensitiveDict]:
        """Realiza la petición HTTP.

        Si `return_headers` es True, devuelve una tupla `(json, headers)`.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Agregar header 'app' dinámicamente para endpoints que lo requieren
        endpoint_lower = endpoint.lower()
        if any(ep in endpoint_lower for ep in ['genre-releases', 'top-playlists']):
            if 'headers' not in kwargs:
                kwargs['headers'] = {}
            kwargs['headers']['app'] = 'new_releases'
        
        if "timeout" not in kwargs:
            kwargs["timeout"] = self.timeout
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            if return_headers:
                return response.json(), response.headers
            return response.json()
        except requests.exceptions.Timeout as exc:
            logger.error(f"Timeout al conectar con {url} después de {self.timeout}s")
            raise ChosicAPIError(f"Timeout excedido ({self.timeout}s)") from exc
        except requests.exceptions.HTTPError as exc:
            status_code = exc.response.status_code if exc.response else None
            resp_text = None
            try:
                resp_text = exc.response.text if exc.response is not None else None
            except Exception:
                resp_text = None
            logger.error(f"Error HTTP {status_code} al solicitar {url}: {resp_text}")
            msg = f"Error HTTP {status_code}"
            if resp_text:
                # acortar si es muy largo
                short = resp_text[:500]
                msg = f"{msg}: {short}"
            raise ChosicAPIError(msg, status_code) from exc
        except requests.exceptions.RequestException as exc:
            logger.error(f"Error de conexión solicitando {url}: {exc}")
            raise ChosicAPIError(f"Error de conexión: {exc}") from exc
        except ValueError as exc:
            logger.error(f"Error parseando JSON de {url}: {exc}")
            raise ChosicAPIError("Respuesta JSON inválida") from exc

    def handshake(self) -> bool:
        """
        Realiza un handshake simple para verificar que la API es accesible.
        Devuelve True si el handshake fue exitoso, False si falló (sin lanzar excepción).
        Es necesario siempre antes de usar otros métodos para asegurar que la sesión está 
        configurada correctamente.
        """
        try:
            self.request("POST", "handshake/")
            logger.debug("ChosicHttpClient: handshake OK")
            return True
        except ChosicAPIError as exc:
            logger.debug(f"ChosicHttpClient: handshake falló: {exc}")
            return False




def create_chosic_api(
    base_url: str = "https://www.chosic.com/api/tools",
    *,
    session: requests.Session | None = None,
    timeout: float = ChosicHttpClient.DEFAULT_TIMEOUT,
    user_agent: str = ChosicHttpClient.DEFAULT_USER_AGENT,
    read_env: bool = True,
) -> ChosicAPI:
    """Factory para crear una instancia de ChosicAPI con configuración opcional desde variables de entorno."""
    client = ChosicHttpClient(base_url, session=session, timeout=timeout, user_agent=user_agent)
    if read_env:
        cookie_env = os.environ.get("CHOSIC_COOKIE")
        if cookie_env:
            client.set_cookie(cookie_env)
        nonce_env = os.environ.get("CHOSIC_X_WP_NONCE")
        if nonce_env:
            client.set_nonce(nonce_env)
        app_env = os.environ.get("CHOSIC_APP")
        if app_env:
            client.set_app(app_env)
    return ChosicAPI(base_url=base_url, session=session, timeout=timeout, user_agent=user_agent, client=client)


class ChosicAPI:
    """Wrapper principal para la API de Chosic."""
    
    def __init__(
        self,
        base_url: str = "https://www.chosic.com/api/tools",
        *,
        session: requests.Session | None = None,
        timeout: float = ChosicHttpClient.DEFAULT_TIMEOUT,
        user_agent: str = ChosicHttpClient.DEFAULT_USER_AGENT,
        client: ChosicHttpClient | None = None,
    ):
        # Permitir inyección de un cliente ya configurado (útil para tests/Factory)
        if client is not None:
            self.client = client
        else:
            self.client = ChosicHttpClient(
                base_url, session=session, timeout=timeout, user_agent=user_agent
            )

    def handshake(self) -> None:
        logger.info("Realizando handshake con la API...")
        # Delegar la implementación del handshake al cliente HTTP cuando esté disponible.
        try:
            if hasattr(self.client, "handshake"):
                ok = self.client.handshake()
                if ok:
                    logger.info("✅ Handshake completado exitosamente")
                else:
                    logger.warning("⚠️  Handshake falló, pero continuando")
                return

            # Compatibilidad: fallback al request directo si el cliente no implementa handshake()
            try:
                self.client.request("POST", "handshake/")
                logger.info("✅ Handshake completado exitosamente")
            except ChosicAPIError as exc:
                logger.warning(f"⚠️  Handshake falló, pero continuando: {exc}")
        except Exception as exc:
            logger.warning(f"⚠️  Error inesperado durante handshake: {exc}")


def create_ready_api_from_args(args, *, exit_on_fail: bool = True) -> "ChosicAPI":
    """Crea y deja lista una instancia de `ChosicAPI` a partir de un objeto `args`.

    Comportamiento similar al snippet del usuario:
    - `base_url` tomado de `args.base_url` si existe
    - aplica `args.timeout` si está presente
    - intenta `handshake()` y sale/lanza si falla cuando `exit_on_fail` es True
    """
    base_url = getattr(args, 'base_url', 'https://www.chosic.com/api/tools')
    read_env = getattr(args, 'read_env', True)

    api = create_chosic_api(base_url=base_url, read_env=read_env)

    # Aplicar timeout si se indicó
    if getattr(args, 'timeout', None) is not None:
        try:
            api.client.timeout = float(args.timeout)
        except Exception:
            if exit_on_fail:
                print('Valor de timeout inválido', file=sys.stderr)
                sys.exit(2)
            raise ValueError('Valor de timeout inválido')

    # Intentar handshake
    try:
        ok = False
        try:
            ok = api.client.handshake()
        except Exception:
            ok = False

        if not ok:
            if exit_on_fail:
                print('Handshake falló; abortando.', file=sys.stderr)
                sys.exit(2)
            raise ChosicAPIError('Handshake falló')

    except Exception as e:
        if exit_on_fail:
            print(f'Error inesperado: {e}', file=sys.stderr)
            sys.exit(2)
        raise

    return api