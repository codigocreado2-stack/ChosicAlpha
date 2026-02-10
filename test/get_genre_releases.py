import argparse
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ChosicAlpha.Busqueda import get_genre_releases_auto
from ChosicAlpha.json_utils import dump_json


def main():
    parser = argparse.ArgumentParser(description='Obtener lanzamientos de un género')
    parser.add_argument('genre', help='Género (ej: rock, pop, jazz)')
    parser.add_argument('--limit', type=int, default=None, help='Límite de resultados')
    parser.add_argument('--output', help='JSON de salida')
    
    args = parser.parse_args()
    
    if not args.output:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        args.output = f'genre_releases_{timestamp}.json'
    
    output_path = Path(__file__).parent / args.output
    
    print(f"Buscando: {args.genre} (límite: {args.limit or 'sin límite'})")
    
    result = get_genre_releases_auto(args.genre, limit=args.limit, exit_on_fail=False)
    
    dump_json(result, output_path)
    
    print(f"✅ Guardado en: {output_path}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
