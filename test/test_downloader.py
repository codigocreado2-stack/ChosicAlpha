"""Script para probar el endpoint de descarga de track assets (preview e imágenes).

Utiliza el CLI de Downloader para descargar previews de audio e imágenes 
de diferentes pistas desde la API de Chosic.

Los tracks se organizan en carpetas con estructura: {track_name} - {artist_name} ({id})
Dentro de cada carpeta se guardan:
- image_default.jpg: Versión pequeña del cover (thumbnail)
- image_large.jpg: Versión grande del cover
- {track_name}.{ext}: Preview de audio en MP3 (si está disponible)

⚠️ NOTA: No todos los tracks tienen preview disponible. La API de Spotify (que usa
Chosic) solo proporciona previews para algunos tracks. Los tracks sin preview
descargará solo las imágenes.

Uso:
  python test_downloader.py

Resultado esperado:
- ✅ 2/3 tracks con preview (Piano Sonata, Mr. Brightside tiene preview en algunos casos)
- ⚠️  1/3 tracks sin preview (algunos IDs de canciones populares no tienen preview en la API)
"""

import subprocess
import sys
from pathlib import Path


def run_downloader_cli(track_id: str, out_root: Path) -> tuple[bool, int]:
    """Ejecuta el CLI de Downloader para descargar una pista.
    
    Returns:
        Tupla (éxito, número de archivos descargados)
    """
    workspace_root = Path(__file__).parent.parent.parent  # /media/usuario/PORNO
    test_dir = Path(__file__).parent  # /media/usuario/PORNO/ChosicAlpha/test
    
    # Usar ruta absoluta para out_root
    out_absolute = (test_dir / out_root).absolute()
    out_absolute.mkdir(parents=True, exist_ok=True)
    
    # Contar archivos antes de la descarga 
    files_before = sum(1 for _ in out_absolute.glob('**/*') if _.is_file())
    
    # Utilizar python -m para ejecutar como módulo del paquete
    cmd = [
        sys.executable,
        "-m",
        "ChosicAlpha.Downloader",
        track_id,
        "--out", str(out_absolute),
    ]
    
    try:
        # Ejecutar desde el directorio del workspace
        result = subprocess.run(
            cmd,
            cwd=str(workspace_root),
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        success = result.returncode == 0
        
        # Contar archivos después de la descarga
        files_after = sum(1 for _ in out_absolute.glob('**/*') if _.is_file())
        files_created = max(0, files_after - files_before)
        
        if success:
            # Mostrar primeras líneas del output
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                # Mostrar la línea de "Hecho" si existe
                for line in lines:
                    if 'Hecho:' in line:
                        print(f"   ✅ {line.strip()}")
                        break
        else:
            # Error en la descarga
            if result.stderr:
                print(f"   ❌ Error: {result.stderr[:200]}")
        
        return success, files_created
        
    except subprocess.TimeoutExpired:
        print(f"   ❌ Timeout descargando {track_id}")
        return False, 0
    except Exception as e:
        print(f"   ❌ Excepción: {e}")
        return False, 0


def main():
    """Prueba descargas de varios track IDs."""
    
    print("🎵 Test de descarga de track assets (preview + imágenes)")
    print("=" * 70)
    
    # Track IDs de prueba
    test_tracks = [
        {
            "id": "1301WleyT98MSxVHPZCA6M",
            "name": "Piano Sonata - Chopin (con preview)",
        },
        {
            "id": "2takcwgKJvtQcYtbuMFOH7",
            "name": "Blinding Lights - The Weeknd",
        },
        {
            "id": "3n3Ppam7vgaVa1iaRUc9Lp",
            "name": "Mr. Brightside - The Killers",
        },
    ]
    
    out_root = Path("mis_descargas")
    
    results = []
    
    for track in test_tracks:
        track_id = track["id"]
        track_name = track["name"]
        
        print(f"\n📥 Descargando: {track_name}")
        print(f"   ID: {track_id}")
        
        success, files_count = run_downloader_cli(track_id, out_root)
        
        if success and files_count > 0:
            print(f"   📁 Archivos descargados: {files_count}")
        elif success:
            print(f"   ⚠️  Sin archivos descargados (preview no disponible)")
        
        results.append({
            "track": track_name,
            "status": "✅ OK" if success else "❌ FALLÓ",
            "success": success,
            "files": files_count,
        })
    
    # Resumen final
    print("\n" + "=" * 70)
    print("📊 Resumen de pruebas:")
    print("=" * 70)
    
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful
    total_files = sum(r["files"] for r in results)
    
    for i, result in enumerate(results, 1):
        status_str = result['status']
        files_str = f"({result['files']} archivos)" if result['files'] > 0 else ""
        print(f"{i}. {result['track']}: {status_str} {files_str}")
    
    out_absolute = (Path(__file__).parent / out_root).absolute()
    
    print("\n" + "=" * 70)
    print(f"✅ Éxito: {successful}/{len(results)} tracks")
    print(f"❌ Fallos: {failed}/{len(results)} tracks")
    print(f"📦 Total de archivos descargados: {total_files}")
    print(f"\n📂 Descargas guardadas en: {out_absolute}")
    print("=" * 70)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
