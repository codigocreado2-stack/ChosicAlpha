"""
Script para obtener características de audio de una pista en la API de Chosic y guardar resultados en JSON.
Uso: python fetch_audio_features.py "track_id" [--output archivo.json]
"""

import json
import argparse
import sys
from pathlib import Path
from datetime import datetime

# Agregar el parent directory al path para importar ChosicAlpha
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ChosicAlpha.Busqueda import fetch_audio_features_auto


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
        description='Obtener características de audio de una pista en Chosic API'
    )
    parser.add_argument('track_id', help='ID o URI de Spotify de la pista')
    parser.add_argument('--output', help='Archivo de salida JSON (default: audio_features_FECHA.json)')
    parser.add_argument('--base-url', default='https://www.chosic.com/api/tools', help='Base URL de la API')
    parser.add_argument('--timeout', type=float, default=15.0, help='Timeout en segundos (default: 15.0)')
    
    args = parser.parse_args()
    
    # Crear nombre de archivo por defecto
    if not args.output:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        args.output = f'audio_features_{timestamp}.json'
    
    output_path = Path(__file__).parent / args.output
    
    print(f"🎵 Obteniendo características de audio para: '{args.track_id}'...")
    print(f"   Archivo: {output_path.name}")
    
    try:
        result = fetch_audio_features_auto(
            args.track_id,
            save_path=str(output_path),
            base_url=args.base_url,
            timeout=args.timeout,
            read_env=True,
            exit_on_fail=False
        )
        
        # Mostrar summary de características
        if hasattr(result, 'acousticness') or isinstance(result, dict):
            print(f"\n📊 Características de audio:")
            
            if hasattr(result, '__dataclass_fields__'):
                # Es un dataclass Features
                print(f"   Acousticness:     {getattr(result, 'acousticness', 'N/A')}")
                print(f"   Danceability:     {getattr(result, 'danceability', 'N/A')}")
                print(f"   Energy:           {getattr(result, 'energy', 'N/A')}")
                print(f"   Instrumentalness: {getattr(result, 'instrumentalness', 'N/A')}")
                print(f"   Liveness:         {getattr(result, 'liveness', 'N/A')}")
                print(f"   Loudness (dB):    {getattr(result, 'loudness', 'N/A')}")
                print(f"   Speechiness:      {getattr(result, 'speechiness', 'N/A')}")
                print(f"   Tempo (BPM):      {getattr(result, 'tempo', 'N/A')}")
                print(f"   Valence:          {getattr(result, 'valence', 'N/A')}")
            elif isinstance(result, dict):
                # Es un dict
                features = {
                    'acousticness': 'Acousticness',
                    'danceability': 'Danceability',
                    'energy': 'Energy',
                    'instrumentalness': 'Instrumentalness',
                    'liveness': 'Liveness',
                    'loudness': 'Loudness (dB)',
                    'speechiness': 'Speechiness',
                    'tempo': 'Tempo (BPM)',
                    'valence': 'Valence'
                }
                for key, label in features.items():
                    if key in result:
                        print(f"   {label:20} {result[key]}")
        
        return 0
    
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
