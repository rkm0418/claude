#!/usr/bin/env python3
"""나무 머리 11번(가시 가지) 수정판: 끝 가지가 더 불규칙, 반짝이 없음, 왼팔은 드문드문하되 이어진 구슬 팔, 오른팔은 정상 팔, 팔 끝 회색 없음.
사용: python3 tools/gen_t11.py && python3 tools/variants.py t11   (시드만 바꾼 4종)"""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(__file__))
import gen_gross  # 48x84
from gen_shadow import C
from gen_creep import tube, chaikin
from gen_treehead import trunk

def branch(c, x, y, ang, L, depth, rng, spread=1.0):
    if depth <= 0 or L < 1.5: return
    k1, k2 = rng.uniform(-.4, .4), rng.uniform(-.4, .4)
    mx, my = x + math.cos(ang + k1) * L * .5, y + math.sin(ang + k1) * L * .5
    ex, ey = mx + math.cos(ang + k2) * L * .5, my + math.sin(ang + k2) * L * .5
    c.line(x, y, mx, my, 2 if depth >= 5 else 1, 1, ch='l'); c.line(mx, my, ex, ey, 1, 1, ch='l')
    if depth == 1:                                   # 끝 가시
        for _ in range(rng.randint(1, 3)):
            a = ang + rng.uniform(-1.2, 1.2); l = rng.uniform(1.5, 4)
            c.line(ex, ey, ex + math.cos(a) * l, ey + math.sin(a) * l, 1, ch='l')
        return
    if depth <= 3 and rng.random() < .3: return    # 중간에 끊긴 가지
    n = rng.choice((1, 2, 2)) if depth > 3 else rng.choice((1, 1, 2))
    for _ in range(n):
        branch(c, ex, ey, ang + rng.uniform(-1, 1) * spread * (1.2 if depth <= 3 else 1.0), L * rng.uniform(.6, 1.0), depth - 1, rng, spread)
    if rng.random() < .15:                           # 몸통에서 곁가지
        branch(c, mx, my, ang + rng.choice((-1, 1)) * rng.uniform(.6, 1.3), L * rng.uniform(.3, .6), depth - 2, rng, spread)

def dome(c, x, y, ang, L, depth, rng):
    if depth <= 0 or L < 1.4: return
    k = rng.uniform(-.15, .15)
    ex, ey = x + math.cos(ang + k) * L, y + math.sin(ang + k) * L
    c.line(x, y, ex, ey, 2 if depth >= 5 else 1, 1, ch='l')
    if depth == 1:
        for _ in range(rng.randint(1, 3)):                       # 끝 가시: 길이와 방향이 제각각
            a = ang + rng.uniform(-1.3, 1.3); l = rng.uniform(1.5, 4.5)
            c.line(ex, ey, ex + math.cos(a) * l, ey + math.sin(a) * l, 1, ch='l')
        return
    if depth <= 2 and rng.random() < .12: return
    n = rng.choice((2, 2, 2, 3))
    for i in range(n):
        off = math.radians(rng.uniform(-1, 1) * 30 + (i - (n - 1) / 2) * 34)
        dome(c, ex, ey, ang + off, L * rng.uniform(.6, .8), depth - 1, rng)

def trunk2(c, n=5, y0=49, y1=34):
    # 줄기 가닥: 아래(어깨)에서 넓게 벌어져 박히고, 몸으로 들어갈수록 색이 어두워진다
    for k in range(n):
        off = k - (n - 1) / 2
        for t in range(0, 31):
            f = t / 30; y = y0 + (y1 - y0) * f
            x = 24 + off * (1.45 + 1.4 * max(0, (f_lo := (1 - f) - .55)) * 2.2) * 1.0
            ch = 'l' if y < y0 - 7 else 'm' if y < y0 - 4 else 'd' if y < y0 - 2 else 's'
            c.put(x, y, ch)
            if t % 2 == 0: c.put(x, y + .5, ch)

def beaded(c, pts, wmin=0.4, wmax=4.2, period=7):
    P = chaikin(pts, 3)
    for i, (x, y) in enumerate(P):
        w = wmin + (wmax - wmin) * (.5 + .5 * math.sin(i * 6.28 / period))
        c.disc(x, y, w / 2, 's')

def root(c, x, y, ang, L, depth, rng):
    if depth <= 0 or L < 1.5: return
    ang += (math.pi / 2 - ang) * .22 + rng.uniform(-.5, .5)          # 아래로 흘러내리며 구불거림
    ex, ey = x + math.cos(ang) * L, y + math.sin(ang) * L
    ch = 'l' if depth >= 4 else 'm' if depth >= 2 else 'd'            # 끝으로 갈수록 어두워짐
    c.line(x, y, ex, ey, 1, 1, ch=ch)
    for _ in range(rng.choice((1, 1, 2))):
        root(c, ex, ey, ang + rng.uniform(-.8, .8), L * rng.uniform(.65, .95), depth - 1, rng)

def root2(c, x, y, ang, L, depth, rng):
    # 몸 윤곽에 맞춘 뿌리: 척추 쪽으로 모이며 세로로 흐르고, 끝으로 갈수록 몸색에 묻힌다
    if depth <= 0 or L < 1.5: return
    ang += (math.pi / 2 - ang) * .45 + rng.uniform(-.28, .28)
    ex, ey = x + math.cos(ang) * L, y + math.sin(ang) * L
    c.line(x, y, ex, ey, 2 if depth >= 6 else 1, 1, ch='l' if depth >= 3 else 'm')
    for _ in range(rng.choice((1, 1, 2))):
        root2(c, ex, ey, ang + rng.uniform(-.55, .55), L * rng.uniform(.75, 1.0), depth - 1, rng)

def chain(c, pts, gap=4.2, ry=3.4, rx=2.5):
    """사슬 팔: 고리가 번갈아 세로/가로로 꿰어진 모양. 고리 안쪽은 비워 둔다."""
    P = chaikin(pts, 3); acc = 0.0; i = 0; last = P[0]
    links = [P[0]]
    for p in P[1:]:
        acc += math.hypot(p[0] - last[0], p[1] - last[1]); last = p
        if acc >= gap: links.append(p); acc = 0.0
    for i, (x, y) in enumerate(links):
        a, b = (rx, ry) if i % 2 == 0 else (ry * .78, rx * .8)
        c.ell(x, y, a, b, 's')
    for i, (x, y) in enumerate(links):
        a, b = (rx, ry) if i % 2 == 0 else (ry * .78, rx * .8)
        for yy in range(int(y - b), int(y + b) + 1):
            for xx in range(int(x - a), int(x + a) + 1):
                if ((xx - x) / max(.1, a - 1.3)) ** 2 + ((yy - y) / max(.1, b - 1.3)) ** 2 <= 1: c.g[yy][xx] = '.'
    return links

def figure(seed):
    import gen_shadow as G
    G.W, G.H = 48, 104
    c = C(); rng = random.Random(seed)
    tube(c, [(24, 50), (24, 74)], 15, 8, .03); c.ell(24, 52, 11, 3.6, 's'); tube(c, [(24, 44), (24, 53)], 7, 10)
    tube(c, [(22, 66), (20, 88), (21, 103)], 6, 2.4); tube(c, [(26, 66), (28, 88), (27, 103)], 6, 2.4)
    r2 = random.Random(seed + 100); tmp = C()
    for sx, a0 in [(20, 105), (28, 75), (16, 115), (32, 65), (24, 90), (22, 98), (30, 80)]:
        root2(tmp, sx, 54, math.radians(a0), 9, 5, r2)
    for sx, a0 in [(21, 95), (28, 80)]:
        root2(tmp, sx, 74, math.radians(a0), 7, 3, r2)
    for y in range(104):
        for x in range(48):
            if tmp.g[y][x] != '.' and c.g[y][x] != '.' and 14 <= x <= 34 and y >= 49 and y <= 98: c.g[y][x] = tmp.g[y][x]
    hx, hy = 25.5, 64                                                  # 심장 쪽(보는 사람 기준 오른쪽 가슴)이 뚫림
    for y in range(104):
        for x in range(48):
            th = math.atan2(y - hy, x - hx); d = (((x - hx) / 3.0) ** 2 + ((y - hy) / 5.8) ** 2) / (1 + .28 * math.sin(3 * th + seed) + .15 * math.sin(5 * th)) ** 2
            if d <= 1: c.g[y][x] = '.'
            elif d <= 1.7 and c.g[y][x] != '.': c.g[y][x] = 'l' if d <= 1.35 else 'm'   # 구멍 가장자리 테두리
    for a0 in (200, 340, 270):                              # 구멍 가장자리에서 안쪽으로 뻗은 뿌리 잔가지
        a = math.radians(a0); sx, sy = hx + math.cos(a) * 3.6, hy + math.sin(a) * 4.6
        c.line(sx, sy, sx - math.cos(a) * r2.uniform(1.5, 3), sy - math.sin(a) * r2.uniform(1.5, 3.5), 1, ch='m')
    L = chain(c, [(12, 53), (10, 72), (10, 94)])
    tube(c, [(36, 53), (37, 70), (37, 90)], 4.2, 3.4); c.ell(37, 93, 2.6, 3.4, "s")
    trunk2(c, 5, 51, 31)
    for i in range(4):
        dome(c, 24 + (i - 1.5) * 1.6, 31, math.radians(-90 + (i - 1.5) * rng.uniform(32, 40)), 7.5, 5, rng)
    return c

def main():
    root = os.path.join(os.path.dirname(__file__), '..', 'art', 'variants')
    lines = ['# 나무 머리 11번 수정판 (tools/gen_t11.py 가 생성함)', '']
    for i, seed in enumerate((11, 12, 13, 14)):
        lines.append(f'[a_{i + 1:02d}] 가시 가지 수정판 시드 {seed} | {i + 1}'); lines += figure(seed).finish(); lines.append('')
    open(os.path.join(root, 't11_pixels.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
if __name__ == '__main__': main()
