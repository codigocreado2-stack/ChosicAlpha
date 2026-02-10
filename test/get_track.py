"""
Script para obtener información de una pista en la API de Chosic y guardar resultados en JSON.
Uso: python get_track.py "track_id_o_uri" [--output archivo.json]
"""

import json
import argparse
import sys
from pathlib import Path
from datetime import datetime

# Agregar el parent directory al path para importar ChosicAlpha
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ChosicAlpha.Busqueda import get_track_auto


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
        description='Obtener información de una pista en Chosic API'
    )
    parser.add_argument('track_id', help='ID o URI de Spotify de la pista')
    parser.add_argument('--output', help='Archivo de salida JSON (default: track_FECHA.json)')
    parser.add_argument('--base-url', default='https://www.chosic.com/api/tools', help='Base URL de la API')
    parser.add_argument('--timeout', type=float, default=None, help='Timeout en segundos')
    
    args = parser.parse_args()
    
    # Crear nombre de archivo por defecto
    if not args.output:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        args.output = f'track_{timestamp}.json'
    
    output_path = Path(__file__).parent / args.output
    
    print(f"🔍 Obteniendo información de pista: '{args.track_id}'...")
    print(f"   Archivo: {output_path.name}")
    
    try:
        result = get_track_auto(
            args.track_id,
            base_url=args.base_url,
            timeout=args.timeout,
            read_env=True,
            exit_on_fail=False
        )
        
        # Guardar resultado
        save_json(result, str(output_path))
        
        # Mostrar summary
        if hasattr(result, 'name') and result.name:
            print(f"\n📊 Información de pista:")
            print(f"   Nombre: {result.name}")
            if hasattr(result, 'artist_display'):
                print(f"   Artista: {result.artist_display}")
            if hasattr(result, 'release_date'):
                print(f"   Fecha de lanzamiento: {result.release_date}")
            if hasattr(result, 'popularity'):
                print(f"   Popularidad: {result.popularity}")
        elif isinstance(result, dict):
            print(f"\n📊 Información de pista:")
            if 'name' in result:
                print(f"   Nombre: {result.get('name')}")
            if 'artist_display' in result:
                print(f"   Artista: {result.get('artist_display')}")
            if 'release_date' in result:
                print(f"   Fecha de lanzamiento: {result.get('release_date')}")
            if 'popularity' in result:
                print(f"   Popularidad: {result.get('popularity')}")
        
        return 0
    
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
