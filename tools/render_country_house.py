#!/usr/bin/env python3
"""가을 시골의 집 안: 평범한 한국 시골집 안방(온돌방). 사선 3차원 시점(도시·시골과 같은 투영).
왼쪽 벽에 창호지 미닫이문, 뒤쪽 벽에 자개 장롱·벽시계·가족사진·달력, 노란 장판 바닥, 밥상과 방석, 낡은 텔레비전, 천장에 매달린 전구.
사용: python3 tools/render_country_house.py -> maps/out/country_house.png (+_x4)"""
import math, os, random, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from render_city3d import Scene, dk, OUT

def noise(x, d, s=0): return ((int(x * 12.9898 + d * 78.233 + s * 37.7) * 2654435761) >> 7) % 100 / 100.0
PAPER, PAPER_D = (232, 214, 176), (216, 196, 156); WOOD, WOOD_D = (120, 78, 48), (86, 54, 34); HANJI = (246, 238, 214)
W, D, H = 112, 84, 66

def build():
    sc = Scene(W, D, H); rng = random.Random(21); sc.img.paste((30, 22, 24), (0, 0, sc.CW, sc.CH)); sc.d = ImageDraw.Draw(sc.img)
    # 장판 바닥: 노란 갈색, 긴 이음선이 세로로(깊이 방향) 나 있고 얼룩이 약간
    def floor(x, d):
        n = noise(x, d); c = (222 + int(n * 10), 176 + int(n * 10), 92 + int(n * 8))
        if x % 28 < 1: return (190, 142, 70)
        if (x * .3 + d) % 19 < .8 and noise(x, d, 4) < .35: return (206, 160, 80)
        return c
    sc.floor(floor)
    sc.poly([(0, 0, -6), (W, 0, -6), (W, 0, 0), (0, 0, 0)], (90, 62, 40)); sc.poly([(W, 0, -6), (W, D, -6), (W, D, 0), (W, 0, 0)], (66, 44, 30))
    # 벽지(왼쪽·뒤): 연한 크림색 + 가는 세로 줄 + 아래 나무 걸레받이 + 위 나무 띠
    def paper(a, b, plane):
        for k in range(a, b):
            c = PAPER if (k // 4) % 2 == 0 else PAPER_D
            if plane == 'L': sc.poly([(0, k, 0), (0, k + 1, 0), (0, k + 1, H), (0, k, H)], c)
            else: sc.poly([(k, D, 0), (k + 1, D, 0), (k + 1, D, H), (k, D, H)], c)
    paper(0, D, 'L'); paper(0, W, 'B')
    for pl in ('L', 'B'):
        for z0, z1, col in ((0, 5, WOOD), (5, 6, WOOD_D), (H - 5, H, WOOD), (H - 6, H - 5, WOOD_D)):
            if pl == 'L': sc.poly([(0, 0, z0), (0, D, z0), (0, D, z1), (0, 0, z1)], col)
            else: sc.poly([(0, D, z0), (W, D, z0), (W, D, z1), (0, D, z1)], col)
    # 왼쪽 벽: 창호지 미닫이 문(나무 살 격자) 두 짝
    for d0 in (12, 38):
        sc.poly([(0, d0, 8), (0, d0 + 24, 8), (0, d0 + 24, 52), (0, d0, 52)], WOOD)
        sc.poly([(0, d0 + 1.5, 9.5), (0, d0 + 22.5, 9.5), (0, d0 + 22.5, 50.5), (0, d0 + 1.5, 50.5)], HANJI)
        for k in range(1, 4): sc.poly([(0, d0 + 1.5 + k * 5.25, 9.5), (0, d0 + 2.3 + k * 5.25, 9.5), (0, d0 + 2.3 + k * 5.25, 50.5), (0, d0 + 1.5 + k * 5.25, 50.5)], (170, 124, 78))
        for k in range(1, 8): sc.poly([(0, d0 + 1.5, 9.5 + k * 5.1), (0, d0 + 22.5, 9.5 + k * 5.1), (0, d0 + 22.5, 10.3 + k * 5.1), (0, d0 + 1.5, 10.3 + k * 5.1)], (170, 124, 78))
        sc.poly([(0, d0 + 20, 24), (0, d0 + 21.5, 24), (0, d0 + 21.5, 30), (0, d0 + 20, 30)], (60, 40, 28))     # 손잡이 홈
    sc.glow(8, 36, 40, col=(255, 236, 196), power=.35)                       # 창호지로 들어오는 바깥 빛(바닥에 번짐)
    # 뒤쪽 벽: 자개 장롱(왼쪽), 벽시계, 가족사진, 달력
    def front(x0, x1, z0, z1, col, d=D): sc.poly([(x0, d, z0), (x1, d, z0), (x1, d, z1), (x0, d, z1)], col)
    sc.box(10, D - 14, 44, 14, 46, (96, 58, 40), (108, 66, 44), (74, 44, 30))
    for a, b in ((12, 31), (33, 52)):
        front(a, b, 3, 44, (76, 46, 32), d=D - 14.2)
        for k in range(3):                                                  # 자개 꽃 무늬(작은 점)
            cx, cz = (a + b) / 2, 12 + k * 11
            for dx, dz in ((0, 0), (-3, 1), (3, 1), (0, 3), (0, -3)):
                front(cx + dx - .8, cx + dx + .8, cz + dz - .8, cz + dz + .8, (188, 214, 206), d=D - 14.3)
        front(a + 15 if a < 20 else a + 1, a + 16.5 if a < 20 else a + 2.5, 20, 26, (214, 178, 80), d=D - 14.4)     # 놋 손잡이
    sc.box(14, D - 12, 14, 8, 6, (236, 232, 222), (218, 212, 200), (182, 176, 164), z0=46)                       # 장롱 위 개킨 이불
    sc.box(30, D - 12, 18, 8, 5, (214, 120, 126), (196, 104, 110), (160, 82, 88), z0=46)
    # 벽시계(둥근, 시침·분침) / 가족사진 액자 셋 / 달력
    cx, cy = sc.P(66, D, 42); sc.d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=(236, 230, 214), outline=(60, 44, 32)); sc.d.line([(cx, cy), (cx, cy - 4)], fill=(40, 30, 24)); sc.d.line([(cx, cy), (cx + 3, cy + 1)], fill=(40, 30, 24))
    for i, (xa, w, h, col) in enumerate(((76, 10, 8, (150, 170, 190)), (89, 8, 10, (170, 150, 130)), (99, 9, 8, (160, 176, 150)))):
        front(xa, xa + w, 36 - h / 2 + (i % 2) * 2, 36 + h / 2 + (i % 2) * 2, WOOD_D); front(xa + 1, xa + w - 1, 37 - h / 2 + (i % 2) * 2, 35 + h / 2 + (i % 2) * 2, col)
    front(60, 70, 20, 33, (240, 236, 224)); front(60, 70, 29, 33, (190, 70, 60)); [front(61 + (k % 3) * 3, 62 + (k % 3) * 3, 21 + (k // 3) * 2.5, 22 + (k // 3) * 2.5, (110, 100, 90)) for k in range(9)]
    # 가구: 낡은 텔레비전과 받침, 밥상, 방석 둘
    sc.box(76, D - 12, 24, 10, 12, (140, 96, 62), (154, 106, 70), (104, 70, 46))
    sc.box(78, D - 11, 20, 9, 14, (58, 56, 60), (70, 68, 72), (44, 42, 46), z0=12); front(80, 96, 14, 24, (28, 36, 34), d=D - 11.1)
    sc.box(80, D - 10, 10, 6, 1, (236, 230, 214), (236, 230, 214), (216, 210, 196), z0=26)                        # 레이스 덮개
    sc.box(48, 34, 24, 16, 7, (138, 86, 52), (150, 96, 58), (108, 66, 40))                                       # 밥상
    sc.box(54, 38, 4, 4, 3, (232, 228, 216), (220, 216, 204), (190, 186, 176), z0=7); sc.box(62, 40, 3, 3, 2, (232, 228, 216), (220, 216, 204), (190, 186, 176), z0=7)
    for x, d, col in ((34, 30, (196, 74, 70)), (78, 42, (70, 100, 160)), (62, 16, (210, 160, 70))):               # 방석(누빈)
        sc.box(x, d, 10, 10, 2, col, dk(col, .85), dk(col, .7))
        for k in range(1, 3): sc.poly([(x + k * 3.3, d, 2), (x + k * 3.3 + .5, d, 2), (x + k * 3.3 + .5, d + 10, 2), (x + k * 3.3, d + 10, 2)], dk(col, .78))
    # 천장 전구와 불빛: 전구 아래 따뜻한 빛 웅덩이, 벽에도 번진다
    b = sc.P(56, 40, H - 4); sc.d.line([(b[0], 2), (b[0], b[1] - 2)], fill=(40, 34, 30)); sc.d.rectangle([b[0] - 2, b[1] - 2, b[0] + 2, b[1] + 3], fill=(255, 238, 180)); sc.d.rectangle([b[0] - 1, b[1] - 4, b[0] + 1, b[1] - 3], fill=(120, 110, 100))
    sc.glow(56, 40, 56, col=(255, 224, 150), power=.45)
    ov = Image.new('RGB', sc.img.size, (255, 200, 130)); sc.img = Image.blend(sc.img, ov, .05)
    return sc

def main():
    sc = build(); out = os.path.join(OUT, 'country_house.png'); sc.img.save(out)
    sc.img.resize((sc.CW * 4, sc.CH * 4), Image.NEAREST).save(out.replace('.png', '_x4.png')); print(out, sc.img.size)
if __name__ == '__main__': main()
