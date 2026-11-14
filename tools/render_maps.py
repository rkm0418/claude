#!/usr/bin/env python3
"""maps/*.txt 배치도를 PNG로 바꾼다.  사용: python3 tools/render_maps.py
출력: maps/out/<이름>.png, <이름>_dream.png (원본 크기), maps/out/preview_all.png (전체 미리보기)"""
import glob, math, os, re, sys
from PIL import Image, ImageChops, ImageDraw, ImageFilter
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
    import boxes
    lib.update(boxes.load_all(render.ROOT))      # 입체 가구가 같은 이름의 평면 스프라이트를 대체
    return lib

def load_lights():
    lights = {}
    for line in open(os.path.join(render.ROOT, 'lights.txt'), encoding='utf-8'):
        p = line.split()
        if p and not line.startswith('#'):
            lights[p[0]] = (float(p[1]), float(p[2]), hexrgb(p[3]))
    return lights

def load_map(path):
    m = {'title': '', 'tone': None, 'ambient': 1.0, 'dream': {}, 'dream_add': [], 'legend': {}, 'rows': [], 'dream_rows': []}
    section = None
    for n, raw in enumerate(open(path, encoding='utf-8'), 1):
        line = raw.rstrip('\n')
        if not line.strip():
            continue
        if line.startswith('title:'):
            m['title'] = line[6:].strip()
        elif line.startswith('tone:'):
            m['tone'] = tuple(int(v) for v in line[5:].split())
        elif line.startswith('ambient:'):
            m['ambient'] = float(line[8:])
        elif line.startswith('dream:'):
            m['dream'] = dict(p.split('=') for p in line[6:].split())
        elif line.startswith('dream_add:'):
            for p in line[10:].split():
                mm = re.match(r'^(\w+)@(\d+),(\d+)(?:\^(\d+))?$', p)
                if not mm:
                    sys.exit(f'{path}:{n}: dream_add 형식은 이름@x,y: {p!r}')
                m['dream_add'].append((mm.group(1), int(mm.group(2)), int(mm.group(3)), int(mm.group(4) or 0)))
        elif line.strip() in ('legend:', 'map:', 'dream_map:'):
            section = line.strip()[:-1]
        elif section == 'legend':
            parts = line.split()
            m['legend'][parts[0]] = (parts[1], parts[2:])
        elif section == 'map':
            m['rows'].append(line)
        elif section == 'dream_map':
            m['dream_rows'].append(line)
        else:
            sys.exit(f'{path}:{n}: 읽을 수 없는 줄: {line!r}')
    w = len(m['rows'][0])
    for y, row in enumerate(m['rows'] + m['dream_rows']):
        if len(row) != w:
            sys.exit(f'{path}: 맵 {y+1}번째 줄(dream_map 포함 순서) 폭이 {len(row)} (기대값 {w})')
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
            level = round(min(1.0, level) * 9) / 9
            r, g, b, _ = px[x, y]
            c = [v * level + n * (1 - level) * 0.5 + t * 0.12 for v, n, t in zip((r, g, b), NIGHT, (tr, tg, tb))]
            if dream:
                c = [v * 0.84 + t * 0.16 for v, t in zip(c, DREAM_TINT)]
            px[x, y] = tuple(min(255, int(v)) for v in c) + (255,)
    return img

# 드림코어 파스텔 램프: 어두운 곳은 연보라, 중간은 분홍, 밝은 곳은 복숭아와 크림.
RAMP = [(0.0, (150, 128, 200)), (0.35, (226, 160, 214)), (0.65, (255, 200, 190)), (1.0, (255, 248, 235))]
SKY_TOP, SKY_BOTTOM = (176, 205, 255), (255, 205, 225)

def ramp(l):
    for (l0, c0), (l1, c1) in zip(RAMP, RAMP[1:]):
        if l <= l1:
            f = (l - l0) / (l1 - l0)
            return tuple(c0[i] * (1 - f) + c1[i] * f for i in range(3))
    return RAMP[-1][1]

def dream_grade(img, emitters):
    """드림코어: 밝기를 파스텔 램프에 대응시키고, 번지는 빛, 약한 스캔라인과 노이즈를 얹는다."""
    px, W, H = img.load(), img.width, img.height
    for y in range(H):
        t = y / H
        sky = tuple(SKY_TOP[i] * (1 - t) + SKY_BOTTOM[i] * t for i in range(3))
        for x in range(W):
            r, g, b, _ = px[x, y]
            if (r, g, b) == (106, 76, 147):          # void_dream 하늘 칸
                c = list(sky)
            else:
                lum = (0.3 * r + 0.59 * g + 0.11 * b) / 255
                lum = 0.18 + lum * 0.95
                c = [ramp(min(1.0, lum))[i] * 0.72 + (r, g, b)[i] * 0.28 for i in range(3)]
            glow = 0.0
            for ex, ey, rad, power, col in emitters:
                d = math.hypot(x - ex, y - ey)
                if d < rad * 1.6:
                    glow += (1 - d / (rad * 1.6)) ** 2 * power * 0.55
            glow = min(0.6, glow)
            c = [v + (255 - v) * glow * 0.8 for v in c]
            edge = min(x, y, W - 1 - x, H - 1 - y)
            k = 0.92 + 0.08 * min(1.0, edge / 24)
            if y % 3 == 0:
                k *= 0.97
            noise = (((x * 73856093) ^ (y * 19349663)) % 9 - 4)
            px[x, y] = tuple(max(0, min(255, int(round((v * k + noise) / 6) * 6))) for v in c) + (255,)
    return img

OUTLINE = (26, 22, 32)
OUTER_STRENGTH = 0.45   # 바깥 외곽선 진하기(0~1). 1이면 완전한 검정, 0이면 없음
NO_OUTLINE_PREFIX = ()   # 이 이름으로 시작하는 사물은 바깥 외곽선과 입체 음영을 넣지 않는다
OUTER_OUTLINE = True   # 사물 바깥 1점 외곽선(조명 뒤에 그림). 끄려면 False
RUGS = {'rug', 'rug_big', 'rug_small', 'rug_living', 'runner', 'blanket'}   # 바닥 타일 밖에는 그리지 않는다
FLAT = {'rug', 'blanket', 'slipper', 'frame_down', 'puddle', 'bottles', 'shoes'}
WALL_MOUNTED = {'clock', 'clock_bird', 'bulb', 'drawing', 'shelf', 'coats', 'coats_dream', 'moon', 'window_eye'}
WALLISH = {'wall_base_cozy', 'wall_base', 'brick', 'brick_lit', 'facade', 'facade_window', 'balcony_body'}
FLOORISH = {'floor_cozy', 'floor_wood', 'floor_kitchen', 'carpet', 'pavement', 'puddle', 'balcony_floor'}
_bevel_cache = {}

def bevel(key, sp):
    """입체감: 위는 밝게, 아래는 어둡게(세로 그라데이션) + 윗면 하이라이트, 아랫면 그늘. 모든 사물에 자동 적용."""
    if key in _bevel_cache:
        return _bevel_cache[key]
    W, H, src = sp.width, sp.height, sp.load()
    ys = [y for y in range(H) for x in range(W) if src[x, y][3]]
    top, bot = (min(ys), max(ys)) if ys else (0, 0)
    out, dst = sp.copy(), None
    dst = out.load()
    def edge(x, y):
        if not (0 <= x < W and 0 <= y < H):
            return True
        c = src[x, y]
        return c[3] == 0 or c[:3] == OUTLINE
    for y in range(H):
        for x in range(W):
            r, g, b, a = src[x, y]
            if not a or (r, g, b) == OUTLINE:
                continue
            f = 1.10 - 0.30 * (y - top) / max(1, bot - top)
            if edge(x, y - 1): f *= 1.14
            if edge(x - 1, y): f *= 1.06
            if edge(x, y + 1): f *= 0.86
            if edge(x + 1, y): f *= 0.90
            dst[x, y] = (min(255, int(r * f)), min(255, int(g * f)), min(255, int(b * f)), a)
    _bevel_cache[key] = out
    return out

def cast_shadow(img, sp, left, foot_y, lights, floor_mask):
    """바닥에 눕는 방향성 그림자: 가장 가까운 '다른' 광원에서 멀어지는 방향으로, 발자국 모양이 사물 높이에 비례해 늘어난다.
    광원에서 가까울수록 짧고, 멀수록 길다. 광원이 없으면 바로 아래로 짧게."""
    W, H, src = sp.width, sp.height, sp.load()
    rows = [y for y in range(H) if any(src[x, y][3] for x in range(W))]
    if not rows:
        return
    last = rows[-1]
    xs = [x for y in range(max(rows[0], last - 5), last + 1) for x in range(W) if src[x, y][3]]
    x0, x1 = min(xs), max(xs)
    cx, cy = left + (x0 + x1) / 2, foot_y - (H - 1 - last) - 2
    height = last - rows[0]
    near = [l for l in lights if math.hypot(l[0] - cx, l[1] - cy) > 10]   # 사물 자신이 광원이면 제외
    if near:
        lx, ly = min(near, key=lambda l: math.hypot(l[0] - cx, l[1] - cy))
        dist = max(1.0, math.hypot(cx - lx, cy - ly))
        nx, ny = (cx - lx) / dist, (cy - ly) / dist
    else:
        dist, nx, ny = 40.0, 0.0, 1.0
    length = min(34, height * 0.6 * max(0.25, min(1.0, dist / 60)))
    ax, ay = (x1 - x0) / 2 + 2, 3
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for t in range(int(length) + 1):
        ex, ey = cx + nx * t, cy + ny * t * 0.6
        d.ellipse((ex - ax, ey - ay, ex + ax, ey + ay), fill=(0, 0, 0, 72))
    layer.putalpha(ImageChops.multiply(layer.getchannel('A'), floor_mask))   # 그림자는 바닥에만
    img.alpha_composite(layer)

def grad_tile(kind):
    t = Image.new('RGBA', (T, T), (0, 0, 0, 0))
    for y in range(T):
        a = int(110 * max(0, 1 - y / 9)) if kind == 'ao' else int(70 * (1 - y / T))
        for x in range(T):
            t.putpixel((x, y), (0, 0, 0, a))
    return t
GRAD_AO, GRAD_WALL = grad_tile('ao'), grad_tile('wall')

def draw_map(m, lib, lights, path, dream):
    emitters = []
    rows = m['dream_rows'] if dream and m['dream_rows'] else m['rows']
    light_pts = []
    for yy, row in enumerate(rows):
        for xx, ch in enumerate(row):
            for nm in [m['legend'][ch][0]] + [o.partition('^')[0].rstrip('!') for o in m['legend'][ch][1]]:
                if (m['dream'].get(nm, nm) if dream else nm) in lights:
                    light_pts.append((xx * T + 8, (yy + 1) * T))
    def place(img, name, x, y, lift=0, base=False):
        flip = name.endswith('!')
        name = name.rstrip('!')
        if dream:
            name = m['dream'].get(name, name)
        if name not in lib:
            sys.exit(f'{path}: 없는 타일/사물 이름 {name!r}')
        sp = lib[name]
        if flip:
            sp = sp.transpose(Image.FLIP_TOP_BOTTOM)
        if not base and not name.startswith(NO_OUTLINE_PREFIX):
            sp = bevel(name + str(flip), sp)
        top = y * T if base else max(0, (y + 1) * T - sp.height - lift)
        if not base and lift == 0 and name not in WALL_MOUNTED and name not in FLAT and sp.height > 10:
            cast_shadow(img, sp, x * T, top + sp.height, light_pts, floor_mask)
        if not base and name in RUGS:
            rug_clip = floor_mask.crop((x * T, top, x * T + sp.width, top + sp.height))
            sp = sp.copy()
            sp.putalpha(ImageChops.multiply(sp.getchannel('A'), rug_clip))
        img.alpha_composite(sp, (x * T, top))
        if not base and not name.startswith(NO_OUTLINE_PREFIX):
            sil.paste(255, (x * T, top), sp.getchannel('A').point(lambda v: 255 if v else 0))
        if base and name in FLOORISH:
            floor_mask.paste(255, (x * T, y * T, x * T + T, y * T + T))
        if base and name in ('wall', 'wall_cozy'):
            img.alpha_composite(GRAD_WALL, (x * T, y * T))
        if base and name in FLOORISH and y > 0 and m['legend'][rows[y - 1][x]][0] in WALLISH:
            img.alpha_composite(GRAD_AO, (x * T, y * T))
        if name in lights:
            emitters.append((x * T + sp.width / 2, top + min(8, sp.height / 2)) + lights[name])
    img = Image.new('RGBA', (len(rows[0]) * T, len(rows) * T))
    floor_mask = Image.new('L', img.size, 0)
    sil = Image.new('L', img.size, 0)     # 사물 실루엣 합집합(바깥 외곽선용)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            place(img, m['legend'][ch][0], x, y, base=True)
    things = [(y, x, obj) for y, row in enumerate(rows) for x, ch in enumerate(row) for obj in m['legend'][ch][1]]
    if dream:
        things += [(y, x, f'{name}^{lift}') for name, x, y, lift in m['dream_add']]
    for y, x, obj in sorted(things, key=lambda t: (t[0], 0 if t[2].split('^')[0] in ('rug', 'rug_big', 'blanket') else 1)):     # 위쪽 줄부터 그려서 아래 사물이 앞에 온다
        name, _, lift = obj.partition('^')
        place(img, name, x, y, int(lift or 0))
    img = shade(img, emitters, m['ambient'], False)   # 꿈도 현실과 같은 색. 달라지는 건 배치뿐
    if m['tone']:                                      # tone: R G B -> 장소의 지배색(리미널 톤)
        px = img.load()
        for y in range(img.height):
            for x in range(img.width):
                r, g, b, a = px[x, y]
                px[x, y] = (r * m['tone'][0] // 255, g * m['tone'][1] // 255, b * m['tone'][2] // 255, a)
    if OUTER_OUTLINE:                                  # 조명 처리 뒤에 그려서 어두운 곳에서도 또렷한 바깥 외곽선
        ring = ImageChops.subtract(sil.filter(ImageFilter.MaxFilter(3)), sil)
        img.paste((16, 10, 14, 255), mask=ring.point(lambda v: int(v * OUTER_STRENGTH)))
    return img

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
        if m['dream'] or m['dream_add'] or m['dream_rows']:
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
