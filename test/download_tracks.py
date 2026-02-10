"""
Script para descargar preview e imágenes de tracks desde la API de Chosic.

Crea carpetas con estructura: {track_name} - {artist_name} ({id})
Dentro de cada carpeta guarda:
- audio: preview del track en MP3 (si está disponible)
- imágenes: image_default.jpg e image_large.jpg (covers)

Uso:
  python download_tracks.py <track_id> [<track_id> ...] [--out CARPETA] [--overwrite]

Ejemplos:
  python download_tracks.py 1301WleyT98MSxVHPZCA6M
  python download_tracks.py 2takcwgKJvtQcYtbuMFOH7 3n3Ppam7vgaVa1iaRUc9Lp --out mis_descargas
  python download_tracks.py spotify:track:1301WleyT98MSxVHPZCA6M --overwrite
"""

import sys
from pathlib import Path

# Agregar el parent directory al path para importar ChosicAlpha
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ChosicAlpha.Downloader import download_track_assets, _build_parser


def main():
    parser = _build_parser()
    args = parser.parse_args()

    out_root = Path(args.out)
    
    print("🎵 Descargando assets de tracks desde Chosic")
    print("=" * 70)
    
    successful = 0
    failed = 0
    total_files = 0
    
    for i, track_id in enumerate(args.tracks, 1):
        print(f"\n📥 Track {i}/{len(args.tracks)}: {track_id}")
        
        try:
            track_dir = download_track_assets(
                track_id,
                out_root=out_root,
                overwrite=args.overwrite
            )
            
            # Contar archivos descargados
            files_count = sum(1 for _ in track_dir.glob('**/*') if _.is_file())
            
            if files_count > 0:
                print(f"   ✅ {files_count} archivo(s) descargado(s)")
                total_files += files_count
            else:
                print(f"   ⚠️  No hay archivos disponibles (sin preview)")
            
            successful += 1
            
        except Exception as e:
            error_msg = str(e)
            if "empty result" in error_msg or "status 400" in error_msg:
                print(f"   ⚠️  Sin resultado: el track no contiene preview o datos disponibles")
            else:
                print(f"   ❌ Error: {e}")
            failed += 1
    
    # Resumen final
    print("\n" + "=" * 70)
    print("📊 Resumen:")
    print("=" * 70)
    print(f"✅ Exitosos: {successful}/{len(args.tracks)}")
    print(f"❌ Fallidos: {failed}/{len(args.tracks)}")
    print(f"📦 Total de archivos: {total_files}")
    print(f"\n📂 Descargas en: {out_root.absolute()}")
    print("=" * 70)
    
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
