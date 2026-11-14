#!/usr/bin/env python3
"""maps/*.txt 배치도를 PNG로 바꾼다.  사용: python3 tools/render_maps.py
출력: maps/out/<이름>.png, <이름>_dream.png (원본 크기), maps/out/preview_all.png (전체 미리보기)"""
import glob, os, sys
from PIL import Image, ImageDraw
import render

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
T, SCALE, PAD = 16, 2, 12

def load_library():
    pal, lib = render.load_palette(), {}
    for name in ('objects', 'tiles'):
        path = os.path.join(render.ROOT, name + '.txt')
        for sp in render.load_sprites(path):
            lib[sp['name']] = render.to_image(sp, pal, path)
    return lib

def load_map(path):
    m = {'title': '', 'dream': {}, 'legend': {}, 'rows': []}
    section = None
    for n, raw in enumerate(open(path, encoding='utf-8'), 1):
        line = raw.rstrip('\n')
        if not line.strip():
            continue
        if line.startswith('title:'):
            m['title'] = line[6:].strip()
        elif line.startswith('dream:'):
            m['dream'] = dict(p.split('=') for p in line[6:].split())
        elif line.strip() in ('legend:', 'map:'):
            section = line.strip()[:-1]
        elif section == 'legend':
            parts = line.split()
            m['legend'][parts[0]] = (parts[1], parts[2:])
        elif section == 'map':
            m['rows'].append(line)
        else:
            sys.exit(f'{path}:{n}: 읽을 수 없는 줄: {line!r}')
    w = len(m['rows'][0])
    for y, row in enumerate(m['rows']):
        if len(row) != w:
            sys.exit(f'{path}: 맵 {y+1}번째 줄 폭이 {len(row)} (기대값 {w})')
        for ch in row:
            if ch not in m['legend']:
                sys.exit(f'{path}: legend 에 없는 글자 {ch!r} (맵 {y+1}번째 줄)')
    return m

def draw_map(m, lib, path, dream):
    def sprite(name):
        if dream:
            name = m['dream'].get(name, name)
        if name not in lib:
            sys.exit(f'{path}: 없는 타일/사물 이름 {name!r}')
        return lib[name]
    img = Image.new('RGBA', (len(m['rows'][0]) * T, len(m['rows']) * T))
    for y, row in enumerate(m['rows']):
        for x, ch in enumerate(row):
            img.alpha_composite(sprite(m['legend'][ch][0]), (x * T, y * T))
    for y, row in enumerate(m['rows']):          # 사물은 칸의 아래쪽에 맞춰 놓는다. 이름^N 은 N점 위로 올림.
        for x, ch in enumerate(row):
            for obj in m['legend'][ch][1]:
                name, _, lift = obj.partition('^')
                sp = sprite(name)
                img.alpha_composite(sp, (x * T, max(0, (y + 1) * T - sp.height - int(lift or 0))))
    return img

def main():
    lib, out = load_library(), os.path.join(BASE, 'maps', 'out')
    os.makedirs(out, exist_ok=True)
    pairs = []
    for path in sorted(glob.glob(os.path.join(BASE, 'maps', '*.txt'))):
        base = os.path.splitext(os.path.basename(path))[0]
        m = load_map(path)
        real = draw_map(m, lib, path, False)
        real.save(os.path.join(out, base + '.png'))
        dream = None
        if m['dream']:
            dream = draw_map(m, lib, path, True)
            dream.save(os.path.join(out, base + '_dream.png'))
        pairs.append((m['title'], real, dream))
        print(f"{base}: {m['title']}")
    cw, ch = max(r.width for _, r, _ in pairs) * SCALE, max(r.height for _, r, _ in pairs) * SCALE
    sheet = Image.new('RGBA', (cw * 2 + PAD * 3, (ch + PAD + 14) * len(pairs) + PAD), (40, 36, 46, 255))
    d = ImageDraw.Draw(sheet)
    for i, (title, real, dream) in enumerate(pairs):
        y = PAD + i * (ch + PAD + 14)
        d.text((PAD, y), f'{i}  real', fill=(216, 207, 192, 255))
        for j, im in enumerate((real, dream)):
            if im:
                if j:
                    d.text((PAD * 2 + cw, y), f'{i}  dream', fill=(216, 207, 192, 255))
                sheet.alpha_composite(im.resize((im.width * SCALE, im.height * SCALE), Image.NEAREST), (PAD + j * (cw + PAD), y + 14))
    sheet.save(os.path.join(out, 'preview_all.png'))

if __name__ == '__main__':
    main()
