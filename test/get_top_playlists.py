"""
Script para obtener top playlists de la API de Chosic y guardar resultados en JSON.
Uso: python get_top_playlists.py [--artist-id ID] [--genre-name GENRE] [--limit 10] [--output archivo.json]
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ChosicAlpha.Busqueda import get_top_playlists_auto
from ChosicAlpha.json_utils import dump_json


def main():
    parser = argparse.ArgumentParser(
        description='Obtener top playlists de Chosic API',
        epilog='Ejemplos:\n'
               '  python get_top_playlists.py\n'
               '  python get_top_playlists.py --artist-id "0C0XlULifJtAgn6ZNCW2eu"\n'
               '  python get_top_playlists.py --genre-name "rock"\n'
               '  python get_top_playlists.py --artist-id "0C0XlULifJtAgn6ZNCW2eu" --limit 20\n',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--artist-id', default=None, help='ID o URI del artista para filtrar (opcional)')
    parser.add_argument('--genre-name', default=None, help='Nombre del género para filtrar (opcional)')
    parser.add_argument('--limit', type=int, default=None, help='Número máximo de resultados (opcional)')
    parser.add_argument('--output', help='Archivo de salida JSON (default: top_playlists_FECHA.json)')
    parser.add_argument('--base-url', default='https://www.chosic.com/api/tools', help='Base URL de la API')
    parser.add_argument('--timeout', type=float, default=None, help='Timeout en segundos')
    
    args = parser.parse_args()
    
    # Validar que se especifique al menos un filtro (opcional - se puede llamar sin filtros)
    if not args.artist_id and not args.genre_name and not args.limit:
        print("ℹ️  Sin filtros especificados, obteniendo todas las top playlists...")
    
    # Crear nombre de archivo por defecto
    if not args.output:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        args.output = f'top_playlists_{timestamp}.json'
    
    output_path = Path(__file__).parent / args.output
    
    # Preparar información de filtros para mostrar
    filters_info = []
    if args.artist_id:
        filters_info.append(f"Artista: {args.artist_id}")
    if args.genre_name:
        filters_info.append(f"Género: {args.genre_name}")
    if args.limit:
        filters_info.append(f"Límite: {args.limit}")
    
    filter_str = " | ".join(filters_info) if filters_info else "Sin filtros"
    
    print(f"🎵 Obteniendo top playlists...")
    print(f"   {filter_str}")
    print(f"   Archivo: {output_path.name}")
    
    try:
        result = get_top_playlists_auto(
            artist_id=args.artist_id,
            genre_name=args.genre_name,
            limit=args.limit,
            base_url=args.base_url,
            timeout=args.timeout,
            read_env=True,
            exit_on_fail=False
        )
        
        # Guardar resultado
        dump_json(result, str(output_path))
        
        # Mostrar summary
        if hasattr(result, 'top_playlists') and result.top_playlists:
            playlists = result.top_playlists.items
            print(f"\n📊 Top Playlists encontradas:")
            print(f"   Total: {len(playlists)}")
            for i, playlist in enumerate(playlists[:5], 1):
                name = getattr(playlist, 'name', 'Unknown')
                parent_genre = getattr(playlist, 'parent_genre', 'N/A')
                tracks = getattr(playlist, 'tracks_count', 'N/A')
                print(f"   {i}. {name} ({parent_genre}) - {tracks} tracks")
            if len(playlists) > 5:
                print(f"   ... y {len(playlists) - 5} más")
        else:
            print("⚠️  No se encontraron playlists")
        
        return 0
    
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
