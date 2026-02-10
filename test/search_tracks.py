"""
Script para buscar tracks en la API de Chosic y guardar resultados en JSON.
Uso: python search_tracks.py "termino de busqueda" [--limit 10] [--output archivo.json]
"""

import json
import argparse
import sys
from pathlib import Path
from datetime import datetime

# Agregar el parent directory al path para importar ChosicAlpha
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ChosicAlpha.Busqueda import search_auto


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
        description='Buscar tracks en Chosic API y guardar en JSON'
    )
    parser.add_argument('query', help='Término de búsqueda')
    parser.add_argument('--limit', type=int, default=10, help='Número máximo de resultados (default: 10)')
    parser.add_argument('--output', help='Archivo de salida JSON (default: search_tracks_FECHA.json)')
    parser.add_argument('--fetch-all', action='store_true', help='Descargar todas las páginas')
    parser.add_argument('--page-size', type=int, default=10, help='Tamaño de página')
    
    args = parser.parse_args()
    
    # Crear nombre de archivo por defecto
    if not args.output:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        args.output = f'search_tracks_{timestamp}.json'
    
    output_path = Path(__file__).parent / args.output
    
    print(f"🔍 Buscando '{args.query}'...")
    print(f"   Límite: {args.limit}")
    print(f"   Archivo: {output_path.name}")
    
    try:
        result = search_auto(
            args.query,
            type='track',
            limit=args.limit,
            fetch_all=args.fetch_all,
            page_size=args.page_size
        )
        
        # Guardar resultado
        save_json(result, str(output_path))
        
        # Mostrar summary
        if hasattr(result, 'tracks') and result.tracks:
            print(f"\n📊 Resultados:")
            print(f"   Tracks encontrados: {len(result.tracks.items)}")
            for i, track in enumerate(result.tracks.items[:5], 1):
                artists = getattr(track, 'artist_display', 'Unknown')
                print(f"   {i}. {track.name} - {artists}")
            if len(result.tracks.items) > 5:
                print(f"   ... y {len(result.tracks.items) - 5} más")
        
        return 0
    
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
