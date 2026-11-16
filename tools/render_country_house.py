#!/usr/bin/env python3
"""가을 세계의 집 안 — 사용자 절개도: 가운데 큰 거실(앞쪽 중앙에 현관문) + 위쪽 방 + 왼쪽 방 + 오른쪽 방이 문으로 이어진다.
사선 3차원 시점, 인형의 집처럼 자른 단면(바깥 뒤·왼쪽 벽은 높고, 안쪽·오른쪽·앞 벽은 낮다). 시골 티 없는 평범한 가정집.
방: 거실(소파·TV·식탁) / 위 = 부엌 / 왼쪽 = 침실 / 오른쪽 = 서재.
사용: python3 tools/render_country_house.py -> maps/out/country_house.png (+_x3, _x4)"""
import math, os, random, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from render_city3d import Scene, dk, OUT

def noise(x, d, s=0): return ((int(x * 12.9898 + d * 78.233 + s * 37.7) * 2654435761) >> 7) % 100 / 100.0
OX = 16                                                          # 평면 좌표(스케치 기준) -> 장면 좌표 이동
ROOMS = {'M': (40, 160, 0, 80), 'L': (-13, 40, 42, 78), 'T': (73, 160, 81, 114), 'R': (160, 207, 10, 41)}
WALLC = {'M': (232, 218, 186), 'L': (206, 214, 222), 'T': (206, 224, 204), 'R': (226, 210, 206)}
WOOD, WOOD_D = (150, 104, 66), (108, 72, 46)
TALL, LOW, CUT = 34, 14, 6

def room_at(x, d):
    for k, (x0, x1, d0, d1) in ROOMS.items():
        if x0 <= x < x1 and d0 <= d < d1: return k
    return None

def build():
    W, D = 224 + OX, 116; sc = Scene(W, D, TALL + 4); sc.img.paste((30, 22, 24), (0, 0, sc.CW, sc.CH)); sc.d = ImageDraw.Draw(sc.img)
    def floor(X, d):
        x = X - OX; r = room_at(x, d)
        if r is None: return None
        n = noise(x, d)
        if r == 'T': return (200, 190, 170) if (x % 12 < 1 or d % 12 < 1) else ((226, 218, 198) if ((int(x // 12) + int(d // 12)) % 2) else (216, 208, 188))
        base = {'M': (176, 126, 82), 'L': (166, 120, 80), 'R': (160, 116, 78)}[r]; base = tuple(v + int(n * 8) for v in base)
        if d % 11 < .8: return dk(base, .72)
        if noise(int(x // 26), int(d // 11), 2) < .5 and x % 26 < .8: return dk(base, .72)
        return base
    sc.floor(floor, x0=0, x1=W)
    # 바닥 두께(앞·오른쪽 단면)
    for k, (x0, x1, d0, d1) in ROOMS.items():
        if k in ('M', 'L'): sc.poly([(x0 + OX, d0, -5), (x1 + OX, d0, -5), (x1 + OX, d0, 0), (x0 + OX, d0, 0)], (90, 62, 40)) if k == 'L' or True else None
    sc.poly([(ROOMS['L'][0] + OX, 42, -5), (ROOMS['L'][1] + OX, 42, -5), (ROOMS['L'][1] + OX, 42, 0), (ROOMS['L'][0] + OX, 42, 0)], (90, 62, 40))
    sc.poly([(40 + OX, 0, -5), (160 + OX, 0, -5), (160 + OX, 0, 0), (40 + OX, 0, 0)], (90, 62, 40))
    sc.poly([(160 + OX, 10, -5), (207 + OX, 10, -5), (207 + OX, 10, 0), (160 + OX, 10, 0)], (90, 62, 40)); sc.poly([(207 + OX, 10, -5), (207 + OX, 41, -5), (207 + OX, 41, 0), (207 + OX, 10, 0)], (66, 44, 30))
    sc.poly([(160 + OX, 41, -5), (160 + OX, 81, -5), (160 + OX, 81, 0), (160 + OX, 41, 0)], (66, 44, 30)) if False else None
    sc.poly([(160 + OX, 81, -5), (160 + OX, 114, -5), (160 + OX, 114, 0), (160 + OX, 81, 0)], (66, 44, 30))
    # --- 벽 ---
    def wall(x0, x1, d0, d1, h, room, depth=None):
        c = WALLC[room]; sc.jobs.append((d0 if depth is None else depth, lambda: sc.box(x0 + OX, d0, x1 - x0, d1 - d0, h, dk(c, .78), c, dk(c, .88))))
        # 걸레받이
        sc.jobs.append((d0 + .1 if depth is None else depth + .1, lambda: sc.poly([(x0 + OX, d0, 0), (x1 + OX, d0, 0), (x1 + OX, d0, 3), (x0 + OX, d0, 3)], (240, 236, 226)) if (x1 - x0) > (d1 - d0) else None))
    # 높은 바깥 벽
    wall(-16, -13, 42, 78, TALL, 'L'); wall(-16, 40, 78, 81, TALL, 'L'); wall(40, 73, 78, 81, TALL, 'M'); wall(37, 40, 0, 42, LOW, 'M')
    wall(73, 160, 114, 117 - 0, TALL, 'T', depth=114); wall(70, 73, 81, 114, TALL, 'T'); wall(160, 210, 41, 44, TALL, 'R', depth=41)
    # 낮은 안쪽 벽(문 틈 포함): M–T (문 x124..140), L–M (문 d55..70), M–R (문 d18..32)
    wall(73, 124, 78, 81, LOW, 'M'); wall(140, 160, 78, 81, LOW, 'M')
    wall(37, 40, 42, 55, LOW, 'M'); wall(37, 40, 70, 78, LOW, 'M')
    wall(160, 163, 10, 18, LOW, 'R'); wall(160, 163, 32, 41, LOW, 'R'); wall(160, 163, 41, 81, LOW, 'M'); wall(160, 163, 81, 114, LOW, 'T'); wall(160, 163, 0, 10, LOW, 'M')
    # 앞·오른쪽 단면(낮게): 현관 틈 x116..132
    wall(40, 116, -3, 0, CUT, 'M', depth=-3); wall(132, 160, -3, 0, CUT, 'M', depth=-3); wall(160, 210, 7, 10, CUT, 'R', depth=7); wall(-16, 40, 39, 42, CUT, 'L', depth=39); wall(207, 210, 10, 41, CUT, 'R')
    # 현관: 문틀과 발판
    def doorframe(): sc.box(114 + OX, -3, 2, 3, 36, (200, 190, 176), (214, 204, 190), (170, 160, 146)); sc.box(132 + OX, -3, 2, 3, 36, (200, 190, 176), (214, 204, 190), (170, 160, 146)); sc.box(114 + OX, -3, 20, 3, 2, (200, 190, 176), (214, 204, 190), (170, 160, 146), z0=36)
    sc.jobs.append((-4, doorframe)); sc.jobs.append((2, lambda: sc.box(118 + OX, 3, 12, 8, 1, (110, 70, 60), (96, 60, 52), (80, 50, 44))))
    # --- 가구 ---
    def bx(x, d, w, dp, h, top, front, right, z0=0): sc.jobs.append((d, lambda: sc.box(x + OX, d, w, dp, h, top, front, right, z0=z0)))
    def fr(x0, x1, z0, z1, col, d): sc.jobs.append((d - .01, lambda: sc.poly([(x0 + OX, d, z0), (x1 + OX, d, z0), (x1 + OX, d, z1), (x0 + OX, d, z1)], col)))
    # 거실: 소파·탁자·TV·식탁
    bx(52, 28, 36, 14, 10, (126, 140, 160), (140, 154, 174), (100, 112, 130)); bx(52, 40, 36, 5, 20, (118, 132, 152), (132, 146, 166), (96, 108, 126))
    sc.jobs.append((38, lambda: sc.poly([(48 + OX, 40, 0), (92 + OX, 40, 0), (92 + OX, 62, 0), (48 + OX, 62, 0)], (170, 74, 66))))                    # 러그
    bx(60, 48, 20, 10, 5, (150, 108, 72), (164, 120, 82), (120, 86, 58))
    bx(52, 70, 30, 8, 9, (140, 100, 70), (154, 112, 78), (112, 80, 54)); bx(56, 71, 22, 6, 14, (50, 52, 56), (62, 64, 70), (40, 42, 46), z0=9)
    bx(110, 40, 28, 18, 3, (176, 122, 80), (190, 134, 90), (140, 96, 62), z0=16)
    for x in (112, 134):
        for d in (42, 54): bx(x, d, 2, 2, 16, WOOD_D, WOOD_D, WOOD_D)
    for (x, d, far) in ((114, 62, True), (128, 62, True), (114, 30, False), (128, 30, False)):
        bx(x, d, 8, 8, 9, (190, 150, 100), (204, 162, 108), (150, 116, 76)); bx(x, d + (6 if far else 0), 8, 2, 13, (176, 138, 92), (190, 150, 100), (140, 106, 70), z0=9)
    # 침실(왼쪽): 침대·옷장·협탁·창
    bx(-9, 48, 30, 26, 7, (130, 96, 70), (146, 108, 76), (104, 76, 54)); bx(-8, 49, 28, 24, 4, (210, 224, 238), (190, 206, 224), (160, 178, 200), z0=7); bx(-8, 66, 12, 7, 3, (246, 246, 244), (226, 226, 224), (196, 196, 194), z0=11)
    bx(22, 66, 16, 10, 30, (134, 96, 66), (150, 108, 74), (108, 76, 52)); bx(20, 50, 8, 8, 10, (140, 100, 70), (154, 112, 78), (112, 80, 54))
    fr(2, 16, 14, 28, (244, 240, 230), 78); fr(3, 15, 15, 27, (176, 206, 226), 78)
    # 부엌(위): 냉장고·싱크대·식탁
    bx(147, 102, 12, 12, 32, (236, 238, 240), (222, 224, 228), (190, 192, 198)); bx(80, 104, 62, 10, 12, (206, 196, 176), (226, 216, 194), (170, 160, 142)); bx(80, 104, 62, 10, 2, (176, 180, 188), (176, 180, 188), (150, 154, 162), z0=12)
    bx(100, 106, 14, 5, 1, (130, 136, 146), (130, 136, 146), (110, 116, 126), z0=14); fr(96, 120, 20, 30, (244, 240, 230), 114); fr(97, 119, 21, 29, (232, 214, 170), 114)
    bx(96, 88, 24, 12, 3, (176, 122, 80), (190, 134, 90), (140, 96, 62), z0=14)
    # 서재(오른쪽): 책상·책장·의자
    bx(166, 36, 26, 5, 30, (110, 82, 58), (124, 94, 66), (90, 66, 46)); bx(188, 18, 16, 9, 2, (170, 124, 82), (184, 134, 90), (136, 98, 64), z0=14)
    for dd in (19, 25): bx(189, dd, 2, 2, 14, WOOD_D, WOOD_D, WOOD_D)
    bx(176, 16, 8, 8, 8, (190, 150, 100), (204, 162, 108), (150, 116, 76)); bx(182, 20, 6, 4, 3, (180, 60, 56), (160, 50, 48), (130, 40, 38), z0=16)
    # 천장 전구 빛(방마다 하나)
    for cx, cd, col in ((100, 36, (255, 226, 160)), (14, 60, (255, 226, 160)), (116, 98, (255, 230, 170)), (184, 26, (255, 226, 160))):
        sc.glow(cx + OX, cd, 46, col=col, power=.34)
    sc.run()
    ov = Image.new('RGB', sc.img.size, (255, 200, 130)); sc.img = Image.blend(sc.img, ov, .04)
    return sc

def main():
    sc = build(); out = os.path.join(OUT, 'country_house.png'); sc.img.save(out)
    for s in (3, 4): sc.img.resize((sc.CW * s, sc.CH * s), Image.NEAREST).save(out.replace('.png', '_x%d.png' % s))
    print(out, sc.img.size)
if __name__ == '__main__': main()
