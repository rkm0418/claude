#!/usr/bin/env python3
"""검은 인간 시안 생성기. 사용: python3 tools/gen_shadow.py && python3 tools/variants.py shadow
art/variants/shadow_pixels.txt 를 만든다. 각 시안은 아래 함수 하나(본체 그리기 + 얼굴 그리기)다.
기준 크기: 32x56 (16px=1m 이므로 3.5m, 아이 키의 3배). 색: s=몸, d=테두리 빛, k=외곽선, w=흰 눈/이빨, r=붉은 점."""
import math, os
W, H = 32, 56

class C:
    def __init__(s): s.g = [['.'] * W for _ in range(H)]
    def put(s, x, y, ch):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < W and 0 <= y < H: s.g[y][x] = ch
    def disc(s, x, y, r, ch='s'):
        for j in range(int(y - r - 1), int(y + r + 2)):
            for i in range(int(x - r - 1), int(x + r + 2)):
                if (i - x) ** 2 + (j - y) ** 2 <= r * r + .3: s.put(i, j, ch)
    def ell(s, cx, cy, rx, ry, ch='s'):
        for j in range(H):
            for i in range(W):
                if ((i - cx) / rx) ** 2 + ((j - cy) / ry) ** 2 <= 1: s.put(i, j, ch)
    def line(s, x0, y0, x1, y1, w=1.0, w1=None, ch='s'):
        w1 = w if w1 is None else w1
        n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
        for t in range(n + 1):
            f = t / n
            s.disc(x0 + (x1 - x0) * f, y0 + (y1 - y0) * f, (w + (w1 - w) * f) / 2, ch)
    def path(s, pts, w=1.0, w1=None):
        for a, b in zip(pts, pts[1:]): s.line(*a, *b, w, w1)
    def finish(s):
        g = s.g
        filled = [[c != '.' for c in r] for r in g]
        def f(x, y): return 0 <= x < W and 0 <= y < H and filled[y][x]
        out = [r[:] for r in g]
        for y in range(H):
            for x in range(W):
                if filled[y][x]:
                    if not f(x + 1, y) or not f(x + 1, y - 1) and not f(x, y - 1): 
                        if g[y][x] == 's': out[y][x] = 'd'
                elif f(x - 1, y) or f(x + 1, y) or f(x, y - 1) or f(x, y + 1):
                    out[y][x] = 'k'
        return [''.join(r) for r in out]

def hand(c, x, y, ang=90):  # 가늘고 긴 손가락 4개
    for k in range(-2, 2):
        a = math.radians(ang + k * 22 + 11)
        c.line(x, y, x + math.cos(a) * 5, y + math.sin(a) * 5, 1)

def teeth(c, x0, x1, y, h=2):  # 이빨 줄
    for x in range(x0, x1 + 1):
        for j in range(h): c.put(x, y + j, 'w' if (x - x0) % 2 == 0 else 'k')

def A():
    c = C()
    c.ell(16, 7, 3.2, 5.5); c.line(16, 11, 16, 18, 2); c.line(16, 17, 16, 34, 6, 4)
    c.line(14, 34, 13, 55, 2.4, 1.6); c.line(18, 34, 19, 55, 2.4, 1.6)
    c.path([(13, 19), (8, 36), (9, 51)], 2.4, 1.4); c.path([(19, 19), (24, 36), (23, 51)], 2.4, 1.4)
    hand(c, 9, 51); hand(c, 23, 51)
    return c, '장신 무얼굴: 목이 길고 팔이 무릎 아래까지, 얼굴은 비어 있음'

def B():
    c = C()
    c.path([(11, 54), (13, 38), (14, 26), (19, 16)], 5, 3)
    c.ell(21, 13, 4.5, 3.6); c.path([(15, 22), (9, 40), (6, 55)], 2.2, 1.4); c.path([(17, 22), (13, 42), (14, 55)], 2.2, 1.4)
    c.line(11, 50, 8, 55, 2); c.line(11, 50, 14, 55, 2)
    hand(c, 6, 55, 120); hand(c, 14, 55, 60)
    teeth(c, 17, 25, 15, 2); c.put(19, 11, 'w'); c.put(23, 11, 'w')
    return c, '굽은 장신: 천장에 머리를 숙이고, 얼굴 전체가 이빨 줄'

def Cc():
    c = C()
    c.ell(16, 31, 8, 10.5); c.ell(16, 14, 3.4, 3.4); c.line(16, 15, 16, 22, 3)
    c.line(14, 40, 12, 55, 1.6); c.line(19, 40, 21, 55, 1.6)
    c.path([(9, 25), (4, 38), (6, 52)], 1.6); c.path([(23, 25), (28, 38), (26, 52)], 1.6)
    hand(c, 6, 52); hand(c, 26, 52)
    for x, y in [(14, 13), (18, 13), (16, 11)]: c.put(x, y, 'w')
    for x in range(11, 22):
        c.put(x, 29 + int(2 * math.sin((x - 11) / 10 * math.pi)), 'k')
    teeth(c, 12, 20, 30, 3)
    return c, '부푼 몸: 배에 큰 입, 머리는 작고 다리는 가느다람'

def D():
    c = C()
    c.ell(16, 9, 2.6, 8); c.line(16, 16, 16, 20, 2); c.line(16, 19, 16, 35, 6, 4)
    c.line(14, 35, 13, 55, 2.2, 1.4); c.line(18, 35, 19, 55, 2.2, 1.4)
    for sx in (-1, 1):
        c.path([(16 + sx * 3, 20), (16 + sx * 9, 35), (16 + sx * 8, 52)], 2.2, 1.2)
        c.path([(16 + sx * 3, 24), (16 + sx * 12, 32), (16 + sx * 13, 44)], 1.8, 1.0)
        hand(c, 16 + sx * 8, 52); hand(c, 16 + sx * 13, 44)
    for i, y in enumerate((3, 6, 9, 12, 15)):
        c.put(15 if i % 2 else 17, y, 'w'); c.put(16 if i % 2 else 16, y, 'w' if i == 2 else 'w')
    c.put(16, 9, 'r')
    return c, '눈 다섯 개가 세로로 박힌 긴 머리, 팔 네 개'

def E():
    c = C()
    c.ell(10, 8, 3.2, 4.6); c.ell(22, 10, 3.2, 4.6)
    c.line(10, 12, 14, 19, 2.2); c.line(22, 14, 18, 19, 2.2)
    c.ell(16, 20, 10, 3); c.line(16, 21, 16, 36, 7, 4)
    c.line(14, 36, 13, 55, 2.4, 1.6); c.line(18, 36, 19, 55, 2.4, 1.6)
    c.path([(7, 21), (4, 36), (5, 52)], 2.2, 1.3); c.path([(25, 21), (28, 36), (27, 52)], 2.2, 1.3)
    c.path([(12, 24), (9, 38), (10, 50)], 1.8, 1.1); c.path([(20, 24), (23, 38), (22, 50)], 1.8, 1.1)
    hand(c, 5, 52); hand(c, 27, 52); hand(c, 10, 50); hand(c, 22, 50)
    teeth(c, 8, 12, 9, 2); c.put(9, 6, 'w'); c.put(12, 6, 'w')   # 왼쪽: 웃는 입
    for x, y in [(21, 11), (22, 11), (23, 11), (21, 12), (23, 12), (21, 13), (22, 13), (23, 13)]: c.put(x, y, 'w')
    c.put(22, 12, 'k'); c.put(21, 8, 'w'); c.put(24, 8, 'r')       # 오른쪽: 벌린 입
    return c, '머리 둘 팔 넷: 두 부모가 한 몸으로 합쳐진 형상'

def F():
    c = C()
    c.ell(16, 24, 6, 4.5); c.ell(16, 15, 3.3, 3.5); c.line(16, 17, 16, 21, 3)
    for (x0, y0), (x1, y1), (x2, y2) in [((11, 24), (3, 6), (2, 55)), ((21, 24), (29, 6), (30, 55)),
                                         ((12, 26), (7, 14), (7, 55)), ((20, 26), (25, 14), (25, 55))]:
        c.path([(x0, y0), (x1, y1), (x2, y2)], 2.0, 1.0)
    for x in (2, 7, 25, 30): c.line(x, 55, x + (1 if x < 16 else -1), 55, 1)
    teeth(c, 13, 19, 17, 2); c.put(14, 13, 'w'); c.put(18, 13, 'w'); c.put(16, 12, 'w')
    return c, '기는 형상: 관절이 반대로 꺾인 긴 팔다리, 몸은 낮게'

def main():
    root = os.path.join(os.path.dirname(__file__), '..', 'art', 'variants')
    lines = ['# 검은 인간 시안 (tools/gen_shadow.py 가 생성함. 직접 고치려면 이 파일을 편집)', '']
    for v, fn in zip('ABCDEF', (A, B, Cc, D, E, F)):
        c, desc = fn()
        lines.append(f'[shadow_{v}] {desc} | {v}')
        lines += c.finish(); lines.append('')
    open(os.path.join(root, 'shadow_pixels.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
main()
