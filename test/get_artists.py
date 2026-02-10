"""
Script para obtener información de artistas en la API de Chosic y guardar resultados en JSON.
Uso: python get_artists.py "artist_id1,artist_id2,..." [--output archivo.json]
     python get_artists.py artist_id1 artist_id2 ... [--output archivo.json]
"""

import json
import argparse
import sys
from pathlib import Path
from datetime import datetime

# Agregar el parent directory al path para importar ChosicAlpha
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ChosicAlpha.Busqueda import get_artists_auto


def save_json(data, filepath):
    """Guarda datos en JSON con formato legible."""
    with open(filepath, 'w', encoding='utf-8') as f:
        if hasattr(data, '__dataclass_fields__'):
            # Si es un dataclass, convertir a dict
            from dataclasses import asdict
            json.dump(asdict(data), f, ensure_ascii=False, indent=2, default=str)
        elif isinstance(data, list) and data and hasattr(data[0], '__dataclass_fields__'):
            # Si es una lista de dataclasses
            from dataclasses import asdict
            json.dump([asdict(item) for item in data], f, ensure_ascii=False, indent=2, default=str)
        else:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    print(f"✅ Datos guardados en: {filepath}")


def main():
    parser = argparse.ArgumentParser(
        description='Obtener información de artistas en Chosic API',
        epilog='Ejemplos:\n'
               '  python get_artists.py "1KpCi9BOfviCVhmpI4G2sY"\n'
               '  python get_artists.py "1KpCi9BOfviCVhmpI4G2sY,0C0XlULifJtAgn6ZNCW2eu"\n'
               '  python get_artists.py 1KpCi9BOfviCVhmpI4G2sY 0C0XlULifJtAgn6ZNCW2eu\n',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('artist_ids', nargs='+', help='ID(s) o URI(s) de Spotify de artistas (separados por espacios o comas)')
    parser.add_argument('--output', help='Archivo de salida JSON (default: artists_FECHA.json)')
    parser.add_argument('--base-url', default='https://www.chosic.com/api/tools', help='Base URL de la API')
    parser.add_argument('--timeout', type=float, default=None, help='Timeout en segundos')
    
    args = parser.parse_args()
    
    # Procesar IDs: pueden venir como múltiples argumentos o separados por comas
    ids = []
    for arg in args.artist_ids:
        # Si contiene comas, split por coma
        if ',' in arg:
            ids.extend([id.strip() for id in arg.split(',')])
        else:
            ids.append(arg)
    
    # Crear nombre de archivo por defecto
    if not args.output:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        args.output = f'artists_{timestamp}.json'
    
    output_path = Path(__file__).parent / args.output
    
    print(f"🔍 Obteniendo información de {len(ids)} artista(s)...")
    print(f"   IDs: {', '.join(ids[:3])}{'...' if len(ids) > 3 else ''}")
    print(f"   Archivo: {output_path.name}")
    
    try:
        result = get_artists_auto(
            ids,
            base_url=args.base_url,
            timeout=args.timeout,
            read_env=True,
            exit_on_fail=False
        )
        
        # Guardar resultado
        save_json(result, str(output_path))
        
        # Mostrar summary
        artists_list = result if isinstance(result, list) else [result] if result else []
        
        if artists_list:
            print(f"\n📊 Información de artistas:")
            for i, artist in enumerate(artists_list[:5], 1):
                if hasattr(artist, 'name'):
                    name = artist.name
                    genres = ', '.join(artist.genres) if hasattr(artist, 'genres') and artist.genres else 'N/A'
                    popularity = artist.popularity if hasattr(artist, 'popularity') else 'N/A'
                    print(f"   {i}. {name} - Géneros: {genres} - Popularidad: {popularity}")
                elif isinstance(artist, dict):
                    name = artist.get('name', 'Unknown')
                    genres = ', '.join(artist.get('genres', [])) if artist.get('genres') else 'N/A'
                    popularity = artist.get('popularity', 'N/A')
                    print(f"   {i}. {name} - Géneros: {genres} - Popularidad: {popularity}")
            
            if len(artists_list) > 5:
                print(f"   ... y {len(artists_list) - 5} más")
        else:
            print("⚠️  No se encontraron artistas")
        
        return 0
    
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
