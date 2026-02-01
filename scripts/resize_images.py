#!/usr/bin/env python3
import argparse
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

CACHE_DIR = Path(__file__).resolve().parent / '.cache'
PILLOW_CACHE = CACHE_DIR / 'pillow'


def ensure_pillow():
    try:
        from PIL import Image
        return Image
    except ImportError:
        pass
    wheel_dir = PILLOW_CACHE / 'wheel'
    extract_dir = PILLOW_CACHE / 'extract'
    wheel_dir.mkdir(parents=True, exist_ok=True)
    if (wheel_dir / 'done').exists():
        pass
    else:
        print('Downloading Pillow...')
        subprocess.check_call([
            sys.executable,
            '-m',
            'pip',
            'download',
            'pillow',
            '-d',
            str(wheel_dir),
        ])
        (wheel_dir / 'done').write_text('')
    wheel_files = sorted(wheel_dir.glob('pillow-*.whl'))
    if not wheel_files:
        raise SystemExit('Pillow wheel not found in cache')
    wheel_file = wheel_files[-1]
    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    extract_dir.mkdir(parents=True)
    with zipfile.ZipFile(wheel_file, 'r') as zipf:
        zipf.extractall(extract_dir)
    sys.path.insert(0, str(extract_dir))
    from PIL import Image
    return Image


def parse_args():
    parser = argparse.ArgumentParser(description='Resize oversized recipe images')
    parser.add_argument('images_dir', nargs='?', default='recipes/assets/images',
                        help='Directory containing recipe image assets')
    parser.add_argument('--max-dim', type=int, default=1600,
                        help='Maximum width/height for the output images')
    parser.add_argument('--quality', type=int, default=85,
                        help='JPEG quality for resaved files')
    return parser.parse_args()


def main():
    args = parse_args()
    Image = ensure_pillow()
    images_dir = Path(args.images_dir)
    if not images_dir.is_dir():
        raise SystemExit(f'Image directory not found: {images_dir}')
    processed = []
    for path in sorted(images_dir.glob('*.jpg')):
        with Image.open(path) as img:
            width, height = img.size
            if width <= args.max_dim and height <= args.max_dim:
                continue
            ratio = min(args.max_dim / width, args.max_dim / height)
            new_size = (max(1, round(width * ratio)), max(1, round(height * ratio)))
            resized = img.resize(new_size, Image.LANCZOS)
            resized.save(path, format='JPEG', quality=args.quality, optimize=True)
            processed.append((path.name, (width, height), new_size))
    if processed:
        print('Resized images:')
        for name, old, new in processed:
            print(f'  {name}: {old} -> {new}')
    else:
        print('No images needed resizing.')


if __name__ == '__main__':
    main()
