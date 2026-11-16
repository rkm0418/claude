#!/usr/bin/env python3
"""어둑어둑한 숲 버전 배경 타일·사물(수미상관의 마지막 장면). art/forest/*.png 로 쓴다(이름 = 파일 이름).
방·복도·베란다와 같은 사선 렌더러가 이름으로 불러 쓴다(render_maps.load_library 가 art/forest/*.png 를 읽는다).  사용: python3 tools/gen_forest_assets.py"""
import os, random
from PIL import Image
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'art', 'forest')
os.makedirs(OUT, exist_ok=True)
C = dict(bg=(14, 22, 22), bg2=(18, 28, 26), bark=(40, 30, 24), barkl=(60, 46, 34), barkd=(24, 18, 16), leaf=(22, 40, 28), leafl=(34, 58, 38),
         moss=(36, 62, 36), dirt=(38, 31, 24), dirt2=(30, 25, 20), dirtl=(52, 42, 30), fog=(52, 68, 76), k=(12, 10, 14), warm=(236, 190, 110), warm2=(250, 226, 160))
def new(w=16, h=16): return Image.new('RGBA', (w, h), (0, 0, 0, 0))
def put(im, x, y, c):
    if 0 <= x < im.width and 0 <= y < im.height: im.putpixel((x, y), c + (255,))
BRIGHT = 1.7                                                   # 렌더러의 어둠 처리를 감안해 타일을 밝게 칠한다(등불·안개는 제외)
def save(im, name):
    if name not in ('lantern_hang', 'forest_edge', 'broken_chair', 'broken_table', 'plank_piece'):
        px = im.load()
        for y in range(im.height):
            for x in range(im.width):
                r, g, b, a = px[x, y]
                if a: px[x, y] = (min(255, int(r * BRIGHT)), min(255, int(g * BRIGHT)), min(255, int(b * BRIGHT)), a)
    im.save(os.path.join(OUT, name + '.png'))

def wall(variant, seed):
    r = random.Random(seed); im = new()
    for y in range(16):
        for x in range(16): put(im, x, y, C['bg'] if (x * 3 + y * 5) % 11 else C['bg2'])
    trunks = {'a': [(2, 5)], 'b': [(9, 5), (0, 2)], 'c': [(5, 4), (12, 3)]}[variant]
    for x0, w in trunks:
        for y in range(16):
            for k in range(w):
                x = (x0 + k) % 16
                c = C['barkl'] if k == 0 else C['barkd'] if k == w - 1 else C['bark']
                if k not in (0, w - 1) and (y + x * 3) % 7 == 0: c = C['barkd']
                put(im, x, y, c)
    for _ in range(5):                                           # 이끼·덩굴
        x, y = r.randrange(16), r.randrange(16)
        for dy in range(r.randrange(2, 6)): put(im, x, (y + dy) % 16, C['moss'] if dy % 2 == 0 else C['leaf'])
    return im
def base(variant, seed):
    r = random.Random(seed); im = new()
    for y in range(16):
        for x in range(16): put(im, x, y, C['bg'])
    for y in range(11, 16):
        for x in range(16): put(im, x, y, C['dirt'] if (x + y) % 5 else C['dirt2'])
    for x in range(0, 16, 2 if variant == 'a' else 3):          # 고사리·풀잎
        h = r.randrange(3, 8)
        for dy in range(h): put(im, (x + dy // 3) % 16, 11 - dy, C['leaf'] if dy % 2 else C['leafl'])
    for x in range(16): put(im, x, 11, C['barkd'])
    return im
def top(variant, seed):
    r = random.Random(seed); im = new()
    for y in range(16):
        for x in range(16): put(im, x, y, (8, 14, 14))
    for _ in range(18):
        cx, cy, rr = r.randrange(16), r.randrange(16), r.randrange(2, 5)
        for y in range(cy - rr, cy + rr + 1):
            for x in range(cx - rr, cx + rr + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= rr * rr: put(im, x % 16, y % 16, C['leaf'] if (x + y) % 3 else C['leafl'])
    return im
def floor(seed, path=False):
    r = random.Random(seed); im = new(); b = C['dirtl'] if path else C['dirt']
    for y in range(16):
        for x in range(16): put(im, x, y, b if r.random() > .3 else C['dirt2'])
    for _ in range(7):                                           # 낙엽·잔가지
        x, y = r.randrange(14), r.randrange(15); c = r.choice([(58, 44, 28), (46, 60, 34), (70, 52, 30)])
        for dx in range(r.randrange(2, 4)): put(im, x + dx, y, c)
    for _ in range(2):
        x, y = r.randrange(10), r.randrange(15)
        for dx in range(5): put(im, x + dx, y + dx // 3, C['barkd'])
    return im
for v, s in (('a', 1), ('b', 2), ('c', 3)):
    save(wall(v, s), f'wall_forest_{v}'); save(top(v, s + 10), f'wall_top_forest_{v}')
for v, s in (('a', 4), ('b', 5)): save(base(v, s), f'wall_base_forest_{v}')
save(wall('a', 1), 'wall_forest'); save(top('a', 11), 'wall_top_forest'); save(base('a', 4), 'wall_base_forest')
save(floor(7), 'floor_forest'); save(floor(8, True), 'floor_forest_path')

# ---- 사물 ----
def stump_lamp():                                                # 책상 대신 그루터기 + 작은 등불
    im = new(24, 24)
    for y in range(10, 22):
        for x in range(2, 22):
            if (x - 12) ** 2 / 100 + (y - 16) ** 2 / 60 <= 1:
                put(im, x, y, C['barkl'] if x < 6 else C['barkd'] if x > 17 else C['bark'])
    for y in range(8, 13):                                       # 윗면 나이테
        for x in range(2, 22):
            if ((x - 12) / 10) ** 2 + ((y - 10) / 3) ** 2 <= 1: put(im, x, y, (92, 70, 48) if ((x - 12) // 2 + y) % 3 else (110, 84, 56))
    for dy in range(4): put(im, 16, 7 - dy, C['warm2'] if dy == 0 else C['warm']); put(im, 17, 7 - dy, C['warm'])   # 등불
    put(im, 15, 3, C['k']); put(im, 18, 3, C['k']); put(im, 16, 2, C['k']); put(im, 17, 2, C['k'])
    return im
def log():
    im = new(34, 14)
    for y in range(2, 13):
        for x in range(1, 33):
            if ((y - 7) / 5.2) ** 2 <= 1:
                put(im, x, y, C['barkl'] if y < 5 else C['barkd'] if y > 9 else C['bark'])
    for x in range(4, 30, 4): put(im, x, 5, C['moss']); put(im, x + 1, 4, C['leaf'])
    for y in range(3, 12):
        for x in (1, 32): put(im, x, y, (92, 70, 48))
    return im
def hollow():                                                    # 왼쪽 벽 문 대신: 나무 둥치의 어두운 구멍
    im = new(16, 30)
    for y in range(30):
        for x in range(16): put(im, x, y, C['bark'] if x in (0, 15) or (x + y) % 6 else C['barkd'])
    for y in range(3, 30):
        w = 7 if y > 8 else 3 + (y - 3)
        for x in range(8 - w // 2 - 1, 8 + w // 2 + 2): put(im, x, y, (4, 8, 8))
    for x in range(3, 13): put(im, x, 2, C['moss'])
    return im
def lantern():
    im = new(8, 12)
    for y in range(2, 10):
        for x in range(1, 7): put(im, x, y, C['warm'] if 3 <= x <= 4 and 4 <= y <= 7 else C['k'])
    put(im, 3, 0, C['k']); put(im, 4, 0, C['k']); put(im, 3, 1, C['k']); put(im, 4, 1, C['k'])
    put(im, 3, 5, C['warm2']); put(im, 4, 5, C['warm2'])
    return im
def mist_gap():                                                  # 복도 끝: 안개 낀 숲 끝(출구)
    im = new(24, 34)
    for y in range(34):
        for x in range(24):
            t = y / 34; c = tuple(int(C['fog'][i] * (1 - t * .5)) for i in range(3))
            put(im, x, y, c if (x + y) % 9 else tuple(min(255, v + 12) for v in c))
    for x in range(24):
        put(im, x, 0, C['barkd']); put(im, x, 33, C['barkd'])
    for y in range(34): put(im, 0, y, C['barkd']); put(im, 23, y, C['barkd'])
    for x in (5, 11, 17):                                          # 안개 속 먼 나무 실루엣
        for y in range(8, 30): put(im, x, y, (34, 46, 52))
    return im
def rocks():
    im = new(14, 9)
    for (cx, cy, rr) in ((4, 6, 3), (9, 6, 3), (7, 3, 2)):
        for y in range(9):
            for x in range(14):
                if (x - cx) ** 2 + (y - cy) ** 2 <= rr * rr: put(im, x, y, (70, 76, 74) if y < cy else (40, 46, 46))
    return im
def mushrooms():
    im = new(10, 9)
    for (cx, cy) in ((3, 4), (7, 5)):
        for dx in range(-2, 3): put(im, cx + dx, cy, (150, 160, 190) if abs(dx) < 2 else (110, 120, 150))
        put(im, cx, cy + 1, (210, 210, 200)); put(im, cx, cy + 2, (190, 190, 180)); put(im, cx, cy - 1, (150, 160, 190))
    return im
for name, im in (('stump_lamp', stump_lamp()), ('fallen_log', log()), ('hollow', hollow()), ('lantern_hang', lantern()), ('forest_edge', mist_gap()), ('rocks', rocks()), ('mushrooms', mushrooms())): save(im, name)
print('forest assets ->', OUT, len(os.listdir(OUT)))

# ---- 베란다용: 부서진 나무 의자·탁자, 부러진 널빤지 ----
def broken_chair():                                              # 다리 하나가 빠져 기울고 등받이가 부러진 나무 의자(19x20)
    im = new(20, 20); W_, D_, L_ = (96, 72, 50), (60, 44, 32), (130, 100, 70)
    for y in range(8, 14):
        for x in range(3, 15): put(im, x, y, L_ if y == 8 else W_)        # 앉는 판
    for y in range(14, 19): put(im, 4, y, D_); put(im, 13, y, D_)          # 앞다리 둘
    for y in range(14, 17): put(im, 8, y, D_)                              # 부러진 뒷다리(짧게)
    for y in range(1, 8): put(im, 4, y, W_)                                # 등받이 왼쪽 기둥
    for y in range(4, 8): put(im, 13, y, W_)                               # 오른쪽 기둥은 부러져 짧음
    put(im, 12, 3, D_); put(im, 14, 3, D_)
    for x in range(4, 9): put(im, x, 3, L_)                                # 남은 가로살
    for x in range(15, 19): put(im, x, 17 + (x % 2), D_)                   # 바닥에 떨어진 부러진 다리 조각
    for (x, y) in ((6, 8), (9, 9), (7, 12)): put(im, x, y, D_)             # 갈라진 틈
    return im
def broken_table():                                              # 상판이 반쯤 쪼개져 내려앉은 나무 탁자(24x16)
    im = new(26, 16); W_, D_, L_ = (96, 72, 50), (60, 44, 32), (130, 100, 70)
    for x in range(2, 15): put(im, x, 5 + (x > 8), L_); put(im, x, 6 + (x > 8), W_); put(im, x, 7 + (x > 8), D_)   # 왼쪽 상판(기울어 내려감)
    for x in range(17, 24): put(im, x, 3, L_); put(im, x, 4, W_); put(im, x, 5, D_)                               # 오른쪽 조각은 남은 다리 위에 비스듬히
    for y in range(8, 15): put(im, 4, y, D_); put(im, 20, y + 0 if y < 14 else 14, D_)                             # 다리 둘
    for x in range(8, 13): put(im, x, 13, W_); put(im, x + 4, 14, D_)                                              # 바닥에 떨어진 널빤지
    for (x, y) in ((15, 6), (16, 7), (15, 8)): put(im, x, y, D_)                                                   # 쪼개진 틈
    return im
def plank():
    im = new(14, 4)
    for x in range(14): put(im, x, 1, (110, 84, 58)); put(im, x, 2, (74, 54, 38))
    put(im, 13, 1, (0, 0, 0, 0)[:3]) if False else None
    return im
for name, im in (('broken_chair', broken_chair()), ('broken_table', broken_table()), ('plank_piece', plank())): save(im, name)
