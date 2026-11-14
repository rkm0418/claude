#!/usr/bin/env python3
"""검은 인간 3차 시안 (역겨움 중심, 48x84). 사용: python3 tools/gen_gross.py && python3 tools/variants.py gross
요소: 젖은 광택, 침, 혀, 사람 이빨, 눈알의 핏줄, 혹, 살 주름, 벗겨진 피부, 마디진 몸, 여분의 얼굴."""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(__file__))
import gen_shadow as G
G.W, G.H = 48, 84
from gen_shadow import C
from gen_creep import tube, fingers, chaikin
CX = 24

def bigeye(c, x, y, r=3, px=0, py=0, seed=0):
    rng = random.Random(seed)
    c.ell(x, y, r * 1.2, r, 'w')
    for _ in range(int(r * 2)):
        a = rng.random() * 6.28; d = r * (.5 + rng.random() * .5)
        c.put(x + math.cos(a) * d * 1.2, y + math.sin(a) * d, 'r')
    c.put(x + px, y + py, 'k'); c.put(x + px + 1, y + py, 'k')
    for i in range(int(-r * 1.2), int(r * 1.2) + 1): c.put(x + i, y - r - 1, 'k')

def mouth(c, x0, y0, x1, y1, seed=0, tongue=True):
    rng = random.Random(seed)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1): c.put(x, y, 'k')
    for x in range(x0, x1 + 1, 3):
        for j in range(rng.randint(2, 4)): c.put(x, y0 + 1 + j, 'w'); c.put(x + 1, y0 + 1 + j, 'w')
        c.put(x, y0, 'r'); c.put(x + 1, y0, 'r')
        for j in range(rng.randint(2, 3)): c.put(x + 1, y1 - 1 - j, 'w'); c.put(x + 2, y1 - 1 - j, 'w')
    if tongue: c.ell((x0 + x1) / 2, y1 - 2, (x1 - x0) / 3, 2, 'p')

def drool(c, x, y, n, seed=0):
    for i in range(n): c.put(x + (1 if i % 7 == 6 else 0), y + i, 'c')
    c.put(x, y + n, 'c'); c.put(x, y + n + 1, 'c'); c.put(x - 1, y + n + 1, 'c')

def lump(c, x, y, r):
    c.disc(x, y, r, 'd'); c.disc(x + .5, y + .5, max(.6, r - 1), 's')
    c.put(x - r * .4, y - r * .4, 'm'); c.put(x - r * .4 + 1, y - r * .4, 'l')

def limbs(c, reach=70, wsh=7, sy=26, seed=1):
    for sx in (-1, 1):
        tube(c, [(CX + sx * wsh, sy), (CX + sx * (wsh + 8), 46), (CX + sx * (wsh + 5 + seed % 3), reach)], 3, 1.8, .1, seed + sx)
        fingers(c, CX + sx * (wsh + 5 + seed % 3), reach, 90 + sx * 8, 4, 10, 36, seed=seed + 5 + sx)
    tube(c, [(20, 58), (18, 70), (20, 82)], 4, 2.4); tube(c, [(28, 58), (30, 70), (28, 82)], 4, 2.4)

def d01():
    c = C(); tube(c, [(CX, 28), (CX, 60)], 14, 8, .06); limbs(c, 70, 8, 30, 1)
    c.ell(CX, 12, 8, 10); bigeye(c, 19, 10, 3.4, 0, 1, 1); bigeye(c, 29, 12, 2.4, 1, 1, 2)
    c.ell(CX, 25, 6.5, 6, 'k'); c.ell(CX, 38, 6, 12); mouth(c, 19, 24, 29, 36, 3, False)
    tube(c, [(CX, 27), (CX - 1, 50), (CX - 3, 64)], 6, 4, .08, 3, 'p'); tube(c, [(CX, 30), (CX - 1, 50)], 1, 1, ch='r')
    for x, n in ((19, 16), (22, 20), (28, 13)): drool(c, x, 38, n)
    return c, '턱이 빠진 자: 아래턱이 가슴까지 늘어지고 혀가 흘러내림, 핏줄 선 눈'

def d02():
    c = C(); rng = random.Random(2)
    c.ell(CX, 45, 15, 22); c.ell(CX, 10, 5, 6); bigeye(c, 22, 9, 2, 0, 0, 3); bigeye(c, 27, 11, 1.5, 0, 0, 4)
    tube(c, [(CX, 14), (CX, 26)], 4)
    for sx in (-1, 1):
        tube(c, [(CX + sx * 13, 34), (CX + sx * 20, 54), (CX + sx * 18, 70)], 2.4, 1.6, .1, sx)
        fingers(c, CX + sx * 18, 70, 90, 4, 9, 36, seed=sx + 9)
    tube(c, [(20, 64), (18, 76), (20, 83)], 3, 2); tube(c, [(28, 64), (30, 76), (28, 83)], 3, 2)
    for i in range(34):
        x, y = CX + rng.uniform(-13, 13), 45 + rng.uniform(-19, 19)
        if ((x - CX) / 14) ** 2 + ((y - 45) / 21) ** 2 < 1: lump(c, x, y, rng.choice((1.6, 2.2, 3, 3.6)))
    for x, y in ((18, 36), (30, 52), (21, 58)):
        c.ell(x, y, 2, 1.4, 'k'); c.put(x - 1, y, 'w'); c.put(x + 1, y, 'w')
    return c, '혹투성이: 부푼 몸 전체에 젖은 혹이 박혀 있고 일부는 작은 입이 열림'

def d03():
    c = C(); tube(c, [(CX, 24), (CX, 58)], 10, 7, .06); limbs(c, 70, 6, 28, 3)
    c.ell(CX, 13, 7.5, 9.5, 'w')
    for y in range(3, 9):
        for x in range(CX - 8, CX + 9):
            if c.g[y][x] == 'w': c.put(x, y, 's')
    c.ell(20, 12, 2.6, 1.6, 'w'); c.ell(29, 12, 2.6, 1.6, 'w'); c.put(20, 11, 'k'); c.put(29, 11, 'k')
    for x in range(17, 33): c.put(x, 10, 'k')
    c.ell(CX, 20, 4.2, 4.4, 'k'); tube(c, [(CX, 19), (CX + 1, 40), (CX + 3, 66), (CX + 8, 82)], 6, 8, .06, 2, 'p')
    tube(c, [(CX, 22), (CX + 1, 40), (CX + 3, 66), (CX + 7, 81)], 1, 1, ch='r'); c.ell(CX + 8, 82, 9, 2, 'p')
    return c, '혀: 창백한 얼굴의 입에서 혀가 몸을 타고 바닥까지 늘어져 고임'

def d04():
    c = C(); tube(c, [(CX, 20), (CX, 58)], 16, 10, .04); limbs(c, 72, 9, 28, 4)
    c.ell(CX, 10, 5, 6.5)
    mouth(c, 18, 26, 30, 52, 5, True)
    # 세로 입: 이빨을 좌우로 돌린다
    for y in range(26, 53): c.put(18, y, 'k'); c.put(30, y, 'k')
    for y in range(27, 52, 3):
        for x in (19, 20): c.put(x, y, 'w'); c.put(x, y + 1, 'w')
        for x in (28, 29): c.put(x, y + 1, 'w'); c.put(x, y + 2, 'w')
    c.ell(CX, 40, 2.4, 11, 'p'); tube(c, [(CX, 29), (CX, 50)], 1, 1, ch='r')
    drool(c, 21, 53, 10); drool(c, 27, 53, 7)
    return c, '배의 입: 머리는 매끈하고 몸통 전체가 세로로 갈라진 입'

def d05():
    c = C(); rng = random.Random(5)
    c.ell(CX, 12, 5, 6); c.put(21, 11, 'w'); c.put(27, 11, 'w'); tube(c, [(CX, 16), (CX, 24)], 4)
    for i, y in enumerate(range(22, 66, 7)):
        w = 11 + (i % 3) * 3 + i
        c.ell(CX, y + 4, w, 5)
        for x in range(CX - w, CX + w + 1): c.put(x, y + 9 + int(1.5 * math.sin(x * .6)), 'k')
        for x in range(CX - w + 3, CX + w - 3, 4): c.put(x, y, 'm')
    for sx in (-1, 1):
        tube(c, [(CX + sx * 11, 28), (CX + sx * 20, 50), (CX + sx * 16, 74)], 2.2, 1.5, .1, sx)
        fingers(c, CX + sx * 16, 74, 90, 4, 9, 36, seed=sx + 12)
    tube(c, [(19, 66), (18, 76), (20, 83)], 5, 3); tube(c, [(29, 66), (30, 76), (28, 83)], 5, 3)
    for y in (30, 40, 52): drool(c, rng.randint(18, 30), y, 3)
    return c, '살 주름: 겹겹이 처진 살덩이 위에 작은 머리가 파묻힘'

def d06():
    c = C(); tube(c, [(CX, 24), (CX, 60)], 12, 8, .06); limbs(c, 72, 7, 28, 6)
    for hx, hy, r in ((CX, 11, 6), (11, 30, 4), (36, 38, 3.6), (17, 50, 4), (32, 24, 3.2)):
        if (hx, hy) != (CX, 11): tube(c, [(CX + (hx - CX) * .3, hy + 10), (hx, hy + 3)], 3)
        c.ell(hx, hy, r, r * 1.25, 'w')
        c.put(hx - r * .4, hy - 1, 'k'); c.put(hx + r * .4, hy - 1, 'k'); c.put(hx - r * .4 + 1, hy - 1, 'k')
        c.ell(hx, hy + r * .55, r * .45, r * .4, 'k')
    return c, '여러 얼굴: 몸 곳곳에서 사람 얼굴이 돋아나 모두 입을 벌리고 있음'

def d07():
    c = C(); tube(c, [(CX, 22), (CX, 58)], 8, 6, .06)
    for sx in (-1, 1):
        tube(c, [(CX + sx * 5, 24), (CX + sx * 14, 46), (CX + sx * 12, 66)], 3, 2, .1, sx)
        fingers(c, CX + sx * 12, 66, 90, 9, 16, 110, seed=sx + 3)
    tube(c, [(20, 58), (18, 70), (20, 82)], 3, 2); tube(c, [(28, 58), (30, 70), (28, 82)], 3, 2)
    c.ell(CX, 11, 6.5, 8.5); bigeye(c, 20, 10, 3.6, 0, 0, 5); bigeye(c, 29, 10, 3.6, 0, 0, 6)
    for x in range(20, 29): c.put(x, 19, 'k')
    return c, '아홉 손가락: 눈꺼풀 없는 큰 눈, 입은 없고 손가락이 아홉 개로 늘어남'

def d08():
    c = C(); tube(c, [(CX, 22), (CX, 58)], 11, 7, .04); limbs(c, 72, 7, 28, 8)
    for y in range(26, 56):
        for x in range(CX - 7, CX + 8):
            if c.g[y][x] != '.': c.put(x, y, 'i' if (x + y) % 5 else 'r')
    for sx in (-1, 1):
        tube(c, [(CX + sx * 7, 24), (CX + sx * 9, 40), (CX + sx * 6, 58)], 3.6, 2, .1, sx)
    c.ell(CX, 11, 6.5, 8, 'w'); c.ell(CX - 3, 10, 3.5, 7, 's'); c.put(CX + 2, 9, 'k'); c.put(CX + 5, 9, 'k')
    c.ell(CX + 3, 15, 2.6, 1.6, 'k'); c.put(CX + 2, 14, 'w'); c.put(CX + 4, 14, 'w')
    c.ell(CX - 4, 11, 2, 2.2, 'i'); bigeye(c, CX - 4, 11, 1.6, 0, 0, 7)
    return c, '벗겨진 피부: 검은 피부가 띠처럼 늘어져 분홍 속살이 드러나고 얼굴 절반도 벗겨짐'

def d09():
    c = C(); rng = random.Random(9)
    for y in range(24, 80, 5):
        cx = CX + 6 * math.sin((y - 20) / 14); w = 9 + 3 * math.sin((y - 24) / 9) - (y - 24) * .06
        c.ell(cx, y + 2, w, 4)
        for x in range(int(cx - w), int(cx + w) + 1): c.put(x, y + 6, 'k')
        c.put(cx - w * .5, y, 'm'); c.put(cx - w * .5 + 1, y, 'l')
    c.ell(CX - 2, 12, 6.5, 8, 'w'); tube(c, [(CX - 2, 18), (CX, 28)], 5)
    c.put(CX - 5, 10, 'k'); c.put(CX - 4, 10, 'k'); c.put(CX + 1, 10, 'k'); c.put(CX, 10, 'k')
    c.ell(CX - 2, 16, 3.4, 2, 'k'); [c.put(CX - 4 + i, 15, 'w') for i in range(5)]
    for y in range(30, 76, 7):
        cx = CX + 6 * math.sin((y - 20) / 14)
        for sx in (-1, 1):
            tube(c, [(cx + sx * 7, y), (cx + sx * 12, y + 5), (cx + sx * 11, y + 10)], 1.6, 1)
            fingers(c, cx + sx * 11, y + 10, 90, 4, 4, 40, seed=y + sx)
    return c, '마디진 몸: 구더기처럼 마디진 몸에 사람 얼굴이 달리고 옆구리에 작은 팔이 줄지어 있음'

def d10():
    c = C(); tube(c, [(14, 36), (14, 60)], 11, 8, .04)
    for sx in (-1, 1):
        tube(c, [(14 + sx * 6, 38), (14 + sx * 11, 54), (14 + sx * 8, 70)], 2.6, 1.6, .1, sx)
        fingers(c, 14 + sx * 8, 70, 90, 4, 9, 36, seed=sx + 14)
    tube(c, [(10, 58), (9, 70), (11, 82)], 3.6, 2); tube(c, [(18, 58), (19, 70), (17, 82)], 3.6, 2)
    path = [(14, 38), (12, 20), (22, 6), (34, 14), (37, 40), (36, 62)]
    tube(c, path, 6, 5, .0)
    P = chaikin(path)
    for i in range(0, len(P), 3):
        x, y = P[i]; c.disc(x, y, 3.4, 'd'); c.disc(x + .3, y + .3, 2.4, 's'); c.put(x - 1, y - 1, 'm')
    c.ell(36, 72, 7.5, 9, 'w'); c.ell(32, 69, 2.4, 1.6, 'k'); c.ell(40, 69, 2.4, 1.6, 'k'); c.put(31, 68, 'w'); c.put(39, 68, 'w')
    c.ell(36, 77, 5, 2.6, 'k'); [c.put(32 + i, 76, 'w') for i in range(9)]
    return c, '늘어난 목: 주름진 긴 목이 아치를 그리며 내려와 머리가 바닥 가까이에서 올려다봄'

def wet(rows, seed):
    rng = random.Random(seed); out = [list(r) for r in rows]
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch in 'sd':
                up = rows[y - 1][x] if y else '.'
                if up in '.k' and rng.random() < .35: out[y][x] = 'm'
                elif rng.random() < .012: out[y][x] = 'l'
    return [''.join(r) for r in out]

def main():
    root = os.path.join(os.path.dirname(__file__), '..', 'art', 'variants')
    lines = ['# 검은 인간 역겨움 시안 (tools/gen_gross.py 가 생성함)', '']
    for i, fn in enumerate([d01, d02, d03, d04, d05, d06, d07, d08, d09, d10]):
        c, desc = fn()
        lines.append(f'[{"ab"[i // 5]}_{i + 1:02d}] {desc} | {i + 1}'); lines += wet(c.finish(), i); lines.append('')
    open(os.path.join(root, 'gross_pixels.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
if __name__ == '__main__':
    main()
