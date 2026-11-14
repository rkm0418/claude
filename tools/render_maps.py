#!/usr/bin/env python3
"""maps/*.txt 배치도를 PNG로 바꾼다.  사용: python3 tools/render_maps.py
출력: maps/out/<이름>.png, <이름>_dream.png (원본 크기), maps/out/preview_all.png (전체 미리보기)"""
import glob, math, os, re, sys
from PIL import Image, ImageDraw
import render

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
T, SCALE, PAD = 16, 2, 12
NIGHT, DREAM_TINT = (18, 14, 34), (106, 76, 147)

def hexrgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def load_library():
    pal, lib = render.load_palette(), {}
    for name in ('objects', 'tiles'):
        path = os.path.join(render.ROOT, name + '.txt')
        for sp in render.load_sprites(path):
            lib[sp['name']] = render.to_image(sp, pal, path)
    return lib

def load_lights():
    lights = {}
    for line in open(os.path.join(render.ROOT, 'lights.txt'), encoding='utf-8'):
        p = line.split()
        if p and not line.startswith('#'):
            lights[p[0]] = (float(p[1]), float(p[2]), hexrgb(p[3]))
    return lights

def load_map(path):
    m = {'title': '', 'ambient': 1.0, 'dream': {}, 'dream_add': [], 'legend': {}, 'rows': []}
    section = None
    for n, raw in enumerate(open(path, encoding='utf-8'), 1):
        line = raw.rstrip('\n')
        if not line.strip():
            continue
        if line.startswith('title:'):
            m['title'] = line[6:].strip()
        elif line.startswith('ambient:'):
            m['ambient'] = float(line[8:])
        elif line.startswith('dream:'):
            m['dream'] = dict(p.split('=') for p in line[6:].split())
        elif line.startswith('dream_add:'):
            for p in line[10:].split():
                mm = re.match(r'^(\w+)@(\d+),(\d+)$', p)
                if not mm:
                    sys.exit(f'{path}:{n}: dream_add 형식은 이름@x,y: {p!r}')
                m['dream_add'].append((mm.group(1), int(mm.group(2)), int(mm.group(3))))
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

def wobble(img):
    """꿈: 줄마다 조금씩 밀어서 벽과 바닥이 일렁이게 한다."""
    out = Image.new('RGBA', img.size)
    for y in range(img.height):
        dx = round(2 * math.sin(y / 7))
        row = img.crop((0, y, img.width, y + 1))
        out.paste(row, (dx, y))
        out.paste(row, (dx - img.width if dx > 0 else dx + img.width, y))
    return out

def shade(img, emitters, ambient, dream):
    """어둠과 불빛. 밝기를 6단계로 끊어서 도트 느낌을 유지한다."""
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            level, tr, tg, tb = ambient, 0.0, 0.0, 0.0
            for ex, ey, rad, power, col in emitters:
                d = math.hypot(x - ex, y - ey)
                if d < rad:
                    f = (1 - d / rad) * power
                    level += f
                    tr += col[0] * f; tg += col[1] * f; tb += col[2] * f
            level = round(min(1.0, level) * 6) / 6
            r, g, b, _ = px[x, y]
            c = [v * level + n * (1 - level) * 0.5 + t * 0.12 for v, n, t in zip((r, g, b), NIGHT, (tr, tg, tb))]
            if dream:
                c = [v * 0.84 + t * 0.16 for v, t in zip(c, DREAM_TINT)]
            px[x, y] = tuple(min(255, int(v)) for v in c) + (255,)
    return img

def draw_map(m, lib, lights, path, dream):
    emitters = []
    def place(img, name, x, y, lift=0, base=False):
        if dream:
            name = m['dream'].get(name, name)
        if name not in lib:
            sys.exit(f'{path}: 없는 타일/사물 이름 {name!r}')
        sp = lib[name]
        top = y * T if base else max(0, (y + 1) * T - sp.height - lift)
        img.alpha_composite(sp, (x * T, top))
        if name in lights:
            emitters.append((x * T + sp.width / 2, top + min(8, sp.height / 2)) + lights[name])
    img = Image.new('RGBA', (len(m['rows'][0]) * T, len(m['rows']) * T))
    for y, row in enumerate(m['rows']):
        for x, ch in enumerate(row):
            place(img, m['legend'][ch][0], x, y, base=True)
    things = [(y, x, obj) for y, row in enumerate(m['rows']) for x, ch in enumerate(row) for obj in m['legend'][ch][1]]
    if dream:
        things += [(y, x, name) for name, x, y in m['dream_add']]
    for y, x, obj in sorted(things, key=lambda t: t[0]):     # 위쪽 줄부터 그려서 아래 사물이 앞에 온다
        name, _, lift = obj.partition('^')
        place(img, name, x, y, int(lift or 0))
    if dream:
        img = wobble(img)
    return shade(img, emitters, m['ambient'] * (0.85 if dream else 1), dream)

def main():
    lib, lights, out = load_library(), load_lights(), os.path.join(BASE, 'maps', 'out')
    os.makedirs(out, exist_ok=True)
    pairs = []
    for path in sorted(glob.glob(os.path.join(BASE, 'maps', '*.txt'))):
        base = os.path.splitext(os.path.basename(path))[0]
        m = load_map(path)
        real = draw_map(m, lib, lights, path, False)
        real.save(os.path.join(out, base + '.png'))
        dream = None
        if m['dream'] or m['dream_add']:
            dream = draw_map(m, lib, lights, path, True)
            dream.save(os.path.join(out, base + '_dream.png'))
        pairs.append((real, dream))
        print(f"{base}: {m['title']}")
    cw, ch = pairs[0][0].width * SCALE, pairs[0][0].height * SCALE
    sheet = Image.new('RGBA', (cw * 2 + PAD * 3, (ch + PAD + 14) * len(pairs) + PAD), (40, 36, 46, 255))
    d = ImageDraw.Draw(sheet)
    for i, pair in enumerate(pairs):
        y = PAD + i * (ch + PAD + 14)
        for j, (im, label) in enumerate(zip(pair, ('real', 'dream'))):
            if im:
                d.text((PAD + j * (cw + PAD), y), f'{i}  {label}', fill=(216, 207, 192, 255))
                sheet.alpha_composite(im.resize((cw, ch), Image.NEAREST), (PAD + j * (cw + PAD), y + 14))
    sheet.save(os.path.join(out, 'preview_all.png'))

if __name__ == '__main__':
    main()
