#!/usr/bin/env python3
"""몽환적인 꿈(망상) 장면 간단 시안 5종 — 현실과 동떨어진 자연·비현실 공간, 추격전이 가능한 구조. 사선 3차원 시점(도시·가을과 같은 투영).
snow(눈 덮인 숲: 직선 추격) / lake(얼어붙은 호수: 갈라지는 얼음) / grass(끝없는 들판: 엄폐물) / library(거대한 도서관: 미로) / stairs(구름 위 계단: 순환).
사용: python3 tools/render_dream.py -> maps/out/dream_<이름>.png (+_x3), dream_sheet.png"""
import math, os, random, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from render_city3d import Scene, dk, OUT

def noise(x, d, s=0): return ((int(x * 12.9898 + d * 78.233 + s * 37.7) * 2654435761) >> 7) % 100 / 100.0
def mix(a, b, f): f = max(0.0, min(1.0, f)); return tuple(int(a[i] + (b[i] - a[i]) * f) for i in range(3))
W, D, H = 112, 112, 66
MARGIN = (30, 22, 30)

def base(sky_top, sky_bot, ground):
    sc = Scene(W, D, H); sc.img.paste(MARGIN, (0, 0, sc.CW, sc.CH)); sc.d = ImageDraw.Draw(sc.img)
    for z in range(H):
        c = mix(sky_bot, sky_top, z / H)
        sc.poly([(0, D, z), (W, D, z), (W, D, z + 1.2), (0, D, z + 1.2)], c); sc.poly([(0, 0, z), (0, D, z), (0, D, z + 1.2), (0, 0, z + 1.2)], c)
    sc.floor(ground)
    sc.poly([(0, 0, -7), (W, 0, -7), (W, 0, 0), (0, 0, 0)], (70, 78, 98)); sc.poly([(W, 0, -7), (W, D, -7), (W, D, 0), (W, 0, 0)], (50, 56, 76))
    return sc

def fir(sc, x, d, h, col=(46, 76, 70), snow=(240, 246, 252)):
    def draw():
        b = sc.P(x, d, 0)
        sc.d.rectangle([b[0] - 1, b[1] - 4, b[0] + 1, b[1]], fill=(70, 52, 44))
        for k in range(4):
            w = 3 + (3 - k) * 3 + (h // 12); y = b[1] - 4 - k * h // 5
            sc.d.polygon([(b[0] - w, y), (b[0] + w, y), (b[0], y - h // 4 - 2)], fill=col)
            sc.d.polygon([(b[0] - w, y), (b[0] - w + 3, y), (b[0], y - h // 4 - 2)], fill=snow)
            sc.d.polygon([(b[0] - w + 1, y), (b[0] + w - 1, y), (b[0] + w - 2, y - 1), (b[0] - w + 2, y - 1)], fill=snow)
    sc.jobs.append((d, draw))

def snow():
    def ground(x, d):
        n = noise(x, d); c = (236, 240, 248) if n > .3 else (222, 230, 244)
        return (200, 212, 232) if noise(x, d, 5) > .93 else c
    sc = base((236, 240, 250), (206, 216, 236), ground); rng = random.Random(3)
    for (x, d, h) in ((10, 22, 40), (22, 60, 46), (8, 96, 36), (40, 100, 44), (72, 98, 40), (100, 80, 44), (96, 40, 38), (86, 14, 34), (60, 70, 30), (34, 40, 30)): fir(sc, x, d, h)
    for k in range(18):                                                          # 이미 나 있는 발자국(한 사람 것): 길을 따라 번갈아
        d = 6 + k * 5.6; x = 56 + 10 * math.sin(d / 18) + (2.2 if k % 2 else -2.2); X, Y = sc.P(x, d, 0)
        sc.d.ellipse([X - 2, Y - 1, X + 2, Y + 1], fill=(158, 176, 206))
    for _ in range(90): X, Y = rng.randrange(8, sc.CW - 8), rng.randrange(8, sc.CH - 12); (sc.px[X, Y] != MARGIN) and sc.d.point((X, Y), fill=(255, 255, 255))
    sc.run(); return sc.img

def lake():
    def ground(x, d):
        edge = min(x, W - x, d, D - d); n = noise(x, d)
        if edge < 7: return (226, 234, 246) if n > .3 else (210, 222, 240)
        return (150 + int(n * 16), 196 + int(n * 12), 222)
    sc = base((52, 60, 108), (150, 160, 210), ground); rng = random.Random(8)
    for gx in range(14, W - 12, 12):                                              # 얼음 아래로 보이는 아파트 창 불빛(희미하게)
        for gd in range(14, D - 12, 12):
            if noise(gx, gd, 2) > .45:
                X, Y = sc.P(gx, gd, 0); sc.d.rectangle([X - 2, Y - 1, X + 2, Y + 1], fill=(238, 214, 150))
    pts = [(56.0, 4.0)]                                                            # 갈라진 금: 아래에서 위로 지그재그
    while pts[-1][1] < D - 10: pts.append((pts[-1][0] + rng.uniform(-9, 9), pts[-1][1] + rng.uniform(8, 14)))
    for a, b in zip(pts, pts[1:]): sc.d.line([sc.P(*a, 0), sc.P(*b, 0)], fill=(246, 252, 255), width=1)
    for a, b in zip(pts[1::2], pts[2::2]): sc.d.line([sc.P(a[0], a[1], 0), sc.P(a[0] + rng.uniform(-14, 14), a[1] + 10, 0)], fill=(226, 238, 250))
    for _ in range(40): X, Y = rng.randrange(8, sc.CW - 8), rng.randrange(8, sc.CH - 12); (sc.px[X, Y] != MARGIN) and sc.d.point((X, Y), fill=(255, 255, 255))
    X, Y = sc.P(30, D, 50); sc.d.ellipse([X - 9, Y - 9, X + 9, Y + 9], fill=(250, 246, 226)); sc.d.ellipse([X - 4, Y - 9, X + 12, Y + 7], fill=(150, 160, 210))   # 초승달
    sc.run(); return sc.img

def grass():
    def ground(x, d): return (92 + int(noise(x, d) * 12), 104 + int(noise(x, d, 2) * 14), 62)
    sc = base((120, 92, 148), (236, 170, 150), ground); rng = random.Random(11)
    blades = [(rng.uniform(2, W - 2), rng.uniform(2, D - 2)) for _ in range(900)]; blades.sort(key=lambda b: -b[1])
    def door():
        x, d = 54, 56; sc.box(x - 1, d, 20, 3, 44, (210, 196, 176), (196, 182, 162), (160, 148, 130)); sc.poly([(x + 1, d - .1, 0), (x + 17, d - .1, 0), (x + 17, d - .1, 40), (x + 1, d - .1, 40)], (130, 84, 62)); sc.poly([(x + 14, d - .2, 18), (x + 15.4, d - .2, 18), (x + 15.4, d - .2, 21), (x + 14, d - .2, 21)], (232, 200, 120))
    sc.jobs.append((56, door))
    for (x, d) in blades:
        def blade(x=x, d=d):
            b = sc.P(x, d, 0); h = 14 + int(noise(x, d, 4) * 10); c = ((86, 112, 70), (116, 146, 82), (150, 168, 96), (176, 150, 96))[int(noise(x, d, 6) * 4)]
            sway = int(noise(x, d, 8) * 3) - 1; sc.d.line([b, (b[0] + sway, b[1] - h)], fill=c)
        sc.jobs.append((d, blade))
    sc.run(); return sc.img

def library():
    def ground(x, d): return (104 + int(noise(x, d) * 8), 70, 50) if int(d // 8) % 2 == 0 else (92, 62, 44)
    sc = base((52, 38, 54), (96, 66, 70), ground)
    for z in range(0, H): pass
    walls = [(0, 22, 4, 50), (30, 0, 4, 32), (30, 46, 4, 40), (62, 20, 4, 50), (62, 80, 4, 32), (90, 0, 4, 60), (14, 90, 40, 4), (74, 60, 22, 4), (36, 64, 4, 20)]
    cols = ((176, 78, 72), (86, 112, 150), (212, 178, 96), (110, 150, 112), (150, 112, 150), (200, 120, 90))
    for (x, d, w, dp) in walls:
        def shelf(x=x, d=d, w=w, dp=dp):
            sc.box(x, d, w, dp, 50, (86, 58, 44), (110, 76, 56), (74, 50, 38))
            for z in (10, 20, 30, 40): sc.poly([(x, d - .1, z), (x + w, d - .1, z), (x + w, d - .1, z + .8), (x, d - .1, z + .8)], (60, 40, 32))
            for k in range(int(w)):
                for z in (3, 13, 23, 33, 43):
                    c = cols[int(noise(x + k, d + z, 1) * 6)]; hh = 4 + int(noise(x + k, z, 3) * 4)
                    sc.poly([(x + k, d - .2, z), (x + k + .9, d - .2, z), (x + k + .9, d - .2, z + hh), (x + k, d - .2, z + hh)], c)
        sc.jobs.append((d, shelf))
    sc.glow(46, 56, 40, col=(255, 214, 140), power=.4)
    def lamp(): X, Y = sc.P(46, 56, 36); sc.d.line([(X, 2), (X, Y)], fill=(40, 32, 30)); sc.d.rectangle([X - 2, Y, X + 2, Y + 3], fill=(255, 232, 170))
    sc.jobs.append((56, lamp)); sc.run(); return sc.img

def stairs():
    sc = base((244, 170, 190), (140, 170, 232), lambda x, d: mix((196, 200, 238), (236, 200, 226), d / D)); rng = random.Random(5)
    def cloud(x, d):
        for k in range(6):
            X, Y = sc.P(x + rng.uniform(-14, 14), d + rng.uniform(-6, 6), 0); r = rng.randint(7, 13); sc.d.ellipse([X - r, Y - r // 2, X + r, Y + r // 2], fill=(252, 250, 252)); sc.d.ellipse([X - r + 2, Y - r // 2 + 3, X + r - 2, Y + r // 2], fill=(226, 230, 246))
    for (x, d) in ((20, 14), (56, 30), (86, 14), (30, 60), (72, 70), (50, 100), (96, 96), (10, 96)): cloud(x, d)
    for k in range(12):                                                           # 올라가는 흰 계단: 한 칸씩 높아지며 오른쪽으로 휘어 순환
        a = k / 12 * math.pi * 1.5 + .3; x = 56 + 34 * math.cos(a) - 8; d = 56 + 30 * math.sin(a) - 5
        def step(x=x, d=d, k=k): sc.box(x, d, 16, 10, 3 + k * 2, (250, 248, 252), (232, 232, 244), (200, 202, 222), z0=0)
        sc.jobs.append((d, step))
    def thing(x, d, z, kind):
        def f():
            X, Y = sc.P(x, d, z)
            if kind == 0: sc.d.rectangle([X - 5, Y - 6, X + 5, Y + 6], fill=(230, 200, 150)); sc.d.rectangle([X - 4, Y - 5, X + 4, Y + 5], fill=(150, 180, 210))       # 떠다니는 액자
            else: sc.d.rectangle([X - 4, Y - 8, X + 4, Y - 4], fill=(176, 120, 90)); sc.d.rectangle([X - 4, Y - 4, X + 4, Y - 2], fill=(150, 100, 74)); sc.d.line([(X - 3, Y - 2), (X - 3, Y + 4)], fill=(120, 80, 60)); sc.d.line([(X + 3, Y - 2), (X + 3, Y + 4)], fill=(120, 80, 60))   # 떠다니는 의자
        sc.jobs.append((d, f))
    for (x, d, z, k) in ((24, 40, 34, 0), (84, 44, 40, 1), (60, 86, 30, 0), (40, 90, 38, 1)): thing(x, d, z, k)
    sc.run(); return sc.img

def reeds():
    """갈대숲: 얕은 물 위 나무 데크 길이 갈대 사이로 구불구불 이어진다. 바람에 한쪽으로 누운 갈대와 솜털 이삭. 좁은 길 추격(양옆이 막힘)."""
    cx = lambda d: 56 + 22 * math.sin(d / 20.0)
    def ground(x, d):
        n = noise(x, d); a = abs(x - cx(d))
        if a < 8: return (112, 84, 48)                                             # 데크 밑
        if noise(int(x // 6), int(d // 6), 4) > .72: return (182 + int(n * 12), 140, 78)   # 진흙 섬
        return (150 + int(n * 14), 120 + int(n * 12), 62 + int(n * 10)) if int(d // 4 + x // 9) % 3 else (184, 146, 78)   # 금빛 얕은 물(결 줄무늬)
    sc = base((244, 206, 104), (255, 232, 150), ground); rng = random.Random(12)
    for d in range(0, D, 5):                                                       # 데크 널빤지
        x = cx(d) - 6
        def plank(x=x, d=d): sc.box(x, d, 12, 4, 2.5, (176, 140, 100), (150, 116, 82), (120, 90, 64), z0=1)
        sc.jobs.append((d, plank))
    for i in range(520):                                                           # 갈대: 길 가장자리는 비우고 그 밖에 빽빽하게
        x, d = rng.uniform(1, W - 1), rng.uniform(2, D - 1)
        if abs(x - cx(d)) < 9.5: continue
        def reed(x=x, d=d, i=i):
            b = sc.P(x, d, 0); h = 22 + int(noise(x, d, 4) * 14); lean = 2 + int(noise(x, d, 9) * 3)
            stem = ((196, 150, 56), (222, 176, 66), (170, 128, 46))[i % 3]; top = (b[0] + lean, b[1] - h)
            sc.d.line([b, (b[0] + lean // 2, b[1] - h // 2), top], fill=stem)
            for dx, dy, c in ((0, 0, (252, 220, 120)), (1, -1, (255, 240, 164)), (-1, 1, (234, 190, 84)), (2, -2, (255, 232, 140)), (0, 2, (240, 204, 100))): sc.d.point((top[0] + dx, top[1] + dy), fill=c)   # 솜털 이삭
            sc.d.line([(top[0], top[1] - 1), (top[0] + 1, top[1] + 4)], fill=(244, 206, 110))
        sc.jobs.append((d, reed))
    for _ in range(30):                                                            # 날아다니는 솜털
        X, Y = rng.randrange(8, sc.CW - 8), rng.randrange(8, sc.CH - 12); (sc.px[X, Y] != MARGIN) and sc.d.point((X, Y), fill=(255, 246, 190))
    sc.run(); return sc.img

def park():
    """밤의 놀이공원: 불 꺼진 회전목마와 천천히 도는 관람차, 전구 줄. 목마 둘레를 도는 둥근 길 = 순환 추격(돌아서 따돌림)."""
    cx0, cd0 = 56, 52
    def ground(x, d):
        r = math.hypot(x - cx0, (d - cd0)); n = noise(x, d)
        if 25 < r < 38: return (96 + int(n * 8), 88 + int(n * 8), 112)           # 목마를 도는 길(밝은 포장)
        return (52 + int(n * 8), 48 + int(n * 8), 72) if noise(int(x // 8), int(d // 8)) > .4 else (46, 42, 66)
    sc = base((30, 22, 64), (112, 70, 120), ground); rng = random.Random(6)
    for _ in range(60): X, Y = rng.randrange(8, sc.CW - 8), rng.randrange(8, sc.CH - 30); (sc.px[X, Y] != MARGIN) and sc.d.point((X, Y), fill=(255, 246, 220))
    def wheel():                                                                   # 관람차(뒤 평면): 바퀴, 바큇살, 곤돌라, 다리
        X, Y = sc.P(82, D, 36); R = 27; sc.d.ellipse([X - R, Y - R, X + R, Y + R], outline=(214, 190, 226)); sc.d.ellipse([X - R + 3, Y - R + 3, X + R - 3, Y + R - 3], outline=(150, 120, 170))
        for k in range(12):
            a = k * math.pi / 6 + .2; sc.d.line([(X, Y), (X + R * math.cos(a), Y + R * math.sin(a))], fill=(170, 140, 190))
            gx, gy = X + R * math.cos(a), Y + R * math.sin(a); c = ((226, 120, 120), (240, 200, 110), (120, 170, 220))[k % 3]; sc.d.rectangle([gx - 2, gy, gx + 2, gy + 4], fill=c)
        sc.d.line([(X, Y), (X - 14, Y + 40)], fill=(130, 104, 150), width=2); sc.d.line([(X, Y), (X + 14, Y + 40)], fill=(130, 104, 150), width=2); sc.d.ellipse([X - 3, Y - 3, X + 3, Y + 3], fill=(226, 200, 230))
    sc.jobs.append((D, wheel))
    def carousel():
        X, Y = sc.P(cx0, cd0, 0); sc.d.ellipse([X - 22, Y - 11, X + 22, Y + 11], fill=(84, 66, 96)); sc.d.ellipse([X - 20, Y - 12, X + 20, Y + 9], fill=(124, 96, 130))     # 바닥판
        sc.d.ellipse([X - 20, Y - 15, X + 20, Y + 5], fill=(104, 76, 110))
        for k in range(8):                                                           # 기둥 + 목마
            a = k * math.pi / 4; px_, py_ = X + 15 * math.cos(a), Y - 5 + 7 * math.sin(a); sc.d.line([(px_, py_), (px_, py_ - 26)], fill=(226, 200, 130))
            hy = py_ - 8 - (k % 2) * 4; c = ((236, 226, 220), (226, 150, 150), (170, 190, 226), (240, 216, 130))[k % 4]
            sc.d.rectangle([px_ - 3, hy, px_ + 3, hy + 4], fill=c); sc.d.rectangle([px_ + 1, hy - 3, px_ + 4, hy], fill=c); sc.d.point((px_ + 3, hy - 2), fill=(40, 30, 40))
        sc.d.ellipse([X - 22, Y - 36, X + 22, Y - 20], fill=(206, 80, 90))                                         # 지붕(줄무늬 챙)
        for k in range(8): sc.d.polygon([(X, Y - 52), (X - 22 + k * 44 // 8, Y - 28), (X - 22 + (k + 1) * 44 // 8, Y - 28)], fill=(206, 80, 90) if k % 2 == 0 else (240, 226, 206))
        sc.d.ellipse([X - 22, Y - 34, X + 22, Y - 22], outline=(236, 214, 150)); sc.d.rectangle([X - 1, Y - 58, X + 1, Y - 52], fill=(236, 214, 150))
        for k in range(11):                                                          # 지붕 끝 전구(꺼져 있음)
            a = k * math.pi * 2 / 11; sc.d.point((X + 22 * math.cos(a), Y - 28 + 6 * math.sin(a)), fill=(236, 230, 190))
    sc.jobs.append((cd0, carousel))
    def booth(x=12, d=18):
        sc.box(x, d, 14, 10, 20, (206, 120, 110), (226, 140, 126), (166, 96, 90)); sc.poly([(x + 3, d - .1, 6), (x + 11, d - .1, 6), (x + 11, d - .1, 15), (x + 3, d - .1, 15)], (40, 30, 50))
        sc.box(x - 1, d - 2, 16, 3, 2, (240, 226, 206), (226, 212, 192), (190, 176, 158), z0=20)
    sc.jobs.append((18, booth))
    for (x, d) in ((18, 86), (96, 24), (20, 50), (96, 88)):                          # 가로등과 전구 불빛
        def lamp(x=x, d=d):
            b = sc.P(x, d, 0); t_ = sc.P(x, d, 32); sc.d.line([b, t_], fill=(70, 60, 90), width=2); sc.d.ellipse([t_[0] - 3, t_[1] - 3, t_[0] + 3, t_[1] + 3], fill=(255, 226, 150))
        sc.jobs.append((d, lamp)); sc.glow(x, d, 26, col=(255, 214, 140), power=.35)
    X, Y = sc.P(90, 46, 0)
    def balloon(): sc.d.line([(X, Y), (X + 2, Y - 22)], fill=(200, 200, 210)); sc.d.ellipse([X - 5, Y - 36, X + 7, Y - 20], fill=(236, 110, 130))
    sc.jobs.append((46, balloon)); sc.run(); return sc.img

def main():
    scenes = {'snow': snow, 'lake': lake, 'grass': grass, 'reeds': reeds, 'park': park, 'library': library, 'stairs': stairs}; imgs = {}
    for k, f in scenes.items():
        im = f(); imgs[k] = im; im.save(os.path.join(OUT, 'dream_%s.png' % k)); im.resize((im.width * 3, im.height * 3), Image.NEAREST).save(os.path.join(OUT, 'dream_%s_x3.png' % k))
    S = 2; pad = 10; w = imgs['snow'].width * S; h = imgs['snow'].height * S
    sheet = Image.new('RGB', (w * 3 + pad * 4, h * 3 + pad * 4), (40, 40, 48))
    for i, k in enumerate(scenes): sheet.paste(imgs[k].resize((w, h), Image.NEAREST), (pad + (i % 3) * (w + pad), pad + (i // 3) * (h + pad)))
    sheet.save(os.path.join(OUT, 'dream_sheet.png')); print('dream ok', imgs['snow'].size)
if __name__ == '__main__': main()
