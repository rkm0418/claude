#!/usr/bin/env python3
"""art/*.txt 의 텍스트 격자를 PNG로 바꾼다.  사용: python3 tools/render.py
출력: art/out/sprites/<이름>.png (원본 크기), art/out/sheet_<파일>.png (확대 미리보기)"""
import glob, os, re, sys
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'art')
SCALE, PAD, BG = 6, 10, (74, 68, 80, 255)

def load_palette():
    pal = {'.': (0, 0, 0, 0)}
    for line in open(os.path.join(ROOT, 'palette.txt'), encoding='utf-8'):
        m = re.match(r'^(\S)\s+([0-9a-fA-F]{6})', line)
        if m and not line.startswith('#'):
            h = m.group(2)
            pal[m.group(1)] = (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)
    return pal

def load_sprites(path):
    sprites, cur = [], None
    for n, raw in enumerate(open(path, encoding='utf-8'), 1):
        line = raw.rstrip('\n')
        if not line.strip() or line.startswith('#'):
            continue
        m = re.match(r'^\[(\w+)\]\s*(.*)$', line)
        if m:
            desc, _, kind = m.group(2).partition('|')
            cur = {'name': m.group(1), 'desc': desc.strip(), 'kind': kind.strip() or 'real', 'rows': [], 'line': n}
            sprites.append(cur)
            continue
        m = re.match(r'^(\S+)(?:\s+\*(\d+))?\s*$', line)
        if not m or cur is None:
            sys.exit(f'{path}:{n}: 읽을 수 없는 줄: {line!r}')
        cur['rows'] += [m.group(1)] * int(m.group(2) or 1)
    return sprites

def to_image(sp, pal, path):
    w = len(sp['rows'][0])
    img = Image.new('RGBA', (w, len(sp['rows'])))
    for y, row in enumerate(sp['rows']):
        if len(row) != w:
            sys.exit(f"{path}: [{sp['name']}] {y+1}번째 줄 폭이 {len(row)} (기대값 {w})")
        for x, ch in enumerate(row):
            if ch not in pal:
                sys.exit(f"{path}: [{sp['name']}] 팔레트에 없는 글자 {ch!r}")
            img.putpixel((x, y), pal[ch])
    return img

def main():
    pal = load_palette()
    os.makedirs(os.path.join(ROOT, 'out', 'sprites'), exist_ok=True)
    for path in sorted(glob.glob(os.path.join(ROOT, '*.txt'))):
        base = os.path.splitext(os.path.basename(path))[0]
        if base in ('palette', 'lights'):
            continue
        items = [(sp, to_image(sp, pal, path)) for sp in load_sprites(path)]
        for sp, img in items:
            img.save(os.path.join(ROOT, 'out', 'sprites', sp['name'] + '.png'))
        rows = [[i for i in items if i[0]['kind'] == k] for k in ('real', 'dream')]
        rows = [r for r in rows if r]
        cell_w = max(i.width for _, i in items) * SCALE + PAD * 2
        heights = [max(i.height for _, i in r) * SCALE + PAD * 2 + 14 for r in rows]
        sheet = Image.new('RGBA', (cell_w * max(len(r) for r in rows), sum(heights)), BG)
        draw, y0 = ImageDraw.Draw(sheet), 0
        for r, h in zip(rows, heights):
            for cx, (sp, img) in enumerate(r):
                big = img.resize((img.width * SCALE, img.height * SCALE), Image.NEAREST)
                sheet.alpha_composite(big, (cx * cell_w + PAD, y0 + h - 14 - PAD - big.height))
                draw.text((cx * cell_w + PAD, y0 + h - 14), sp['name'], fill=(216, 207, 192, 255))
            y0 += h
        sheet.save(os.path.join(ROOT, 'out', f'sheet_{base}.png'))
        print(f'{base}: {len(items)}개 → art/out/sheet_{base}.png')

if __name__ == '__main__':
    main()
