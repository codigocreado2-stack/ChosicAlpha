"""
Script para obtener recomendaciones de la API de Chosic y guardar resultados en JSON.
Uso: python recommendations.py --seed-tracks "track_id1,track_id2" [--limit 10] [--output archivo.json]
     python recommendations.py --seed-artists "artist_id1,artist_id2" [--limit 10] [--output archivo.json]
"""

import json
import argparse
import sys
from pathlib import Path
from datetime import datetime

# Agregar el parent directory al path para importar ChosicAlpha
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ChosicAlpha.Busqueda import recommendations_auto


def save_json(data, filepath):
    """Guarda datos en JSON con formato legible."""
    with open(filepath, 'w', encoding='utf-8') as f:
        if hasattr(data, '__dataclass_fields__'):
            # Si es un dataclass, convertir a dict
            from dataclasses import asdict
            json.dump(asdict(data), f, ensure_ascii=False, indent=2, default=str)
        else:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    print(f"✅ Datos guardados en: {filepath}")


def main():
    parser = argparse.ArgumentParser(
        description='Obtener recomendaciones de la API de Chosic basadas en seeds',
        epilog='Ejemplos:\n'
               '  python recommendations.py --seed-tracks "70wYA8oYHoMzhRRkARoMhU" --limit 10\n'
               '  python recommendations.py --seed-artists "0C0XlULifJtAgn6ZNCW2eu" --limit 5\n'
               '  python recommendations.py --seed-tracks "70wYA8oYHoMzhRRkARoMhU" --seed-artists "0C0XlULifJtAgn6ZNCW2eu" --limit 20\n',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--seed-tracks', help='ID(s) o URI(s) de pistas semilla (separadas por comas)')
    parser.add_argument('--seed-artists', help='ID(s) o URI(s) de artistas semilla (separadas por comas)')
    parser.add_argument('--limit', type=int, default=10, help='Número máximo de recomendaciones (default: 10, máx. 100)')
    parser.add_argument('--output', help='Archivo de salida JSON (default: recommendations_FECHA.json)')
    parser.add_argument('--fetch-all', action='store_true', help='Descargar todas las páginas')
    parser.add_argument('--page-size', type=int, default=10, help='Tamaño de página al usar --fetch-all (máx. 100)')
    parser.add_argument('--base-url', default='https://www.chosic.com/api/tools', help='Base URL de la API')
    parser.add_argument('--timeout', type=float, default=None, help='Timeout en segundos')
    parser.add_argument('--param', action='append', help='Parámetro extra en formato key=value (puede repetirse)')
    
    args = parser.parse_args()
    
    # Validar que al menos un seed esté presente
    if not args.seed_tracks and not args.seed_artists:
        print("❌ Error: Debes especificar al menos --seed-tracks o --seed-artists", file=sys.stderr)
        return 1
    
    # Crear nombre de archivo por defecto
    if not args.output:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        args.output = f'recommendations_{timestamp}.json'
    
    output_path = Path(__file__).parent / args.output
    
    # Parsear parámetros extra
    extra_params = {}
    if args.param:
        for p in args.param:
            if '=' in p:
                k, v = p.split('=', 1)
                try:
                    # Intentar convertir a número
                    if v.isdigit():
                        extra_params[k.strip()] = int(v)
                    elif '.' in v and v.replace('.', '').isdigit():
                        extra_params[k.strip()] = float(v)
                    else:
                        extra_params[k.strip()] = v.strip()
                except (ValueError, AttributeError):
                    extra_params[k.strip()] = v.strip()
    
    # Preparar información de seeds para mostrar
    seeds_info = []
    if args.seed_tracks:
        seeds_info.append(f"Pistas: {args.seed_tracks}")
    if args.seed_artists:
        seeds_info.append(f"Artistas: {args.seed_artists}")
    
    print(f"🎵 Obteniendo recomendaciones...")
    print(f"   {', '.join(seeds_info)}")
    print(f"   Límite: {args.limit}")
    if args.fetch_all:
        print(f"   Fetch all: true (página: {args.page_size})")
    print(f"   Archivo: {output_path.name}")
    
    try:
        result = recommendations_auto(
            seed_tracks=args.seed_tracks,
            seed_artists=args.seed_artists,
            limit=args.limit,
            extra_params=extra_params if extra_params else None,
            fetch_all=args.fetch_all,
            page_size=args.page_size,
            base_url=args.base_url,
            timeout=args.timeout,
            read_env=True,
            exit_on_fail=False
        )
        
        # Guardar resultado
        save_json(result, str(output_path))
        
        # Mostrar summary
        if hasattr(result, 'tracks') and result.tracks:
            print(f"\n📊 Recomendaciones:")
            print(f"   Tracks encontrados: {len(result.tracks.items)}")
            for i, track in enumerate(result.tracks.items[:5], 1):
                artists = getattr(track, 'artist_display', 'Unknown')
                print(f"   {i}. {track.name} - {artists}")
            if len(result.tracks.items) > 5:
                print(f"   ... y {len(result.tracks.items) - 5} más")
        else:
            print("⚠️  No se encontraron recomendaciones")
        
        return 0
    
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
