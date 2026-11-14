#!/usr/bin/env python3
"""조력자 기괴한 동물 2차(더 불쾌하게): 탈 속의 사람이 비치는 균열, 사람 눈, 침, 핏줄, 벗겨진 털, 터진 솜, 어긋난 목.
사용: python3 tools/gen_grotesque2.py && python3 tools/variants.py grotesque2   (28x44)"""
import os, sys, random
sys.path.insert(0, os.path.dirname(__file__))
import gen_shadow as G
from gen_shadow import C
from gen_helpers import rect, tri
from gen_mascot import body, head, HY
from gen_grotesque import cover_eyes, button_eye, teeth_row, stitch_mouth, human_hand
G.W, G.H = 28, 44

def drool(c, x, y, n):
    for i in range(n): c.put(x + (1 if i % 6 == 5 else 0), y + i, 'c')
    c.put(x, y + n, 'c'); c.put(x - 1, y + n + 1, 'c'); c.put(x, y + n + 1, 'c')

def human_eye(c, x, y, rx=2.4, ry=1.8, px=0, py=0, veins=True):
    c.ell(x, y, rx + 1, ry + 1, 'k'); c.ell(x, y, rx, ry, 'w'); c.put(x + px, y + py, 'k'); c.put(x + px + 1, y + py, 'k')
    if veins:
        for dx, dy in ((-2, 0), (2, -1), (-1, 1), (3, 1), (-3, -1)): c.put(x + dx, y + dy, 'r')

def crack(c, x0, y0, x1, y1, fill='i', seed=1):
    r = random.Random(seed); pts = [(x0, y0)]
    n = max(abs(x1 - x0), abs(y1 - y0)) // 2
    for i in range(1, n + 1):
        f = i / n; pts.append((x0 + (x1 - x0) * f + r.uniform(-1.2, 1.2), y0 + (y1 - y0) * f + r.uniform(-.6, .6)))
    for a, b in zip(pts, pts[1:]):
        c.line(*a, *b, 1.6, ch=fill); c.line(a[0] - 1, a[1], b[0] - 1, b[1], 1, ch='k'); c.line(a[0] + 1, a[1], b[0] + 1, b[1], 1, ch='k')

def bald(c, x, y, rx, ry):
    c.ell(x, y, rx, ry, 'i')
    for dx, dy in ((-1, 0), (1, 1), (0, -1), (-2, 1)): c.put(x + dx, y + dy, 'a')

def rabbit(v):
    c = C(); ears = lambda: [(c.ell(sx, 3, 2.3, 6, 'w'), c.ell(sx, 3.5, 1.2, 4.6, 'i')) for sx in (9, 19)]
    ears(); body(c, 'j', 'd')
    if v == 'A':                                                       # 얼굴이 세로로 갈라져 사람 피부와 사람 눈이 보임
        head(c, 'w', 'q', 'smile'); cover_eyes(c, 'w'); button_eye(c, 10, HY - 2)
        crack(c, 17, HY - 7, 18, HY + 6, 'i'); human_eye(c, 18, HY - 1, 2.2, 2.4, 1, 1)
        stitch_mouth(c, 9, 19, HY + 6); drool(c, 12, HY + 8, 7)
        rect(c, 8, 7, 19, 9, 'j'); rect(c, 7, 10, 20, 10, 'k'); c.put(14, 8, 'y')
    if v == 'B':                                                       # 핏발 선 눈, 너무 많은 이빨, 침, 찢어진 귀
        head(c, 'w', 'q', 'smile'); cover_eyes(c, 'w')
        for sx in (-1, 1): human_eye(c, 14 + sx * 3.8, HY - 2, 2.8, 2.8, 0, 0)
        c.ell(14, HY + 6, 7, 3.4, 'k'); teeth_row(c, 8, 20, HY + 4, 2); teeth_row(c, 9, 19, HY + 7, 2); teeth_row(c, 10, 18, HY + 5, 1)
        for x in (10, 14, 18): drool(c, x, HY + 9, 5 + x % 4)
        c.ell(28 - 9, 3, 2.3, 6, '.'); c.line(19, 0, 19, 8, 1, ch='k'); rect(c, 6, 6, 17, 8, 'j'); rect(c, 5, 9, 18, 9, 'k')
    if v == 'C':                                                       # 눈구멍에 사람 눈이 박히고 주둥이 대신 사람 입술
        head(c, 'w', 'i', 'smile'); cover_eyes(c, 'w')
        for sx in (-1, 1): c.ell(14 + sx * 3.8, HY - 2, 3.6, 4.6, 'k'); human_eye(c, 14 + sx * 3.8, HY - 2, 1.6, 1.4, -sx, 0, False)
        for x in range(10, 19): c.put(x, HY + 5, 'r'); c.put(x, HY + 6, 'r' if 11 <= x <= 17 else 'i')
        crack(c, 14, HY + 3, 14, HY + 5, 'i', 3); c.put(14, HY + 2, 'a'); drool(c, 13, HY + 8, 4)
        rect(c, 6, 5, 21, 9, 'j'); rect(c, 6, 8, 21, 8, 'y'); rect(c, 5, 10, 22, 10, 'k')
    if v == 'D':                                                       # 탈이 목에서 들려 올라가 사람의 목이 드러남
        t = C(); [(t.ell(sx, 3, 2.3, 6, 'w'), t.ell(sx, 3.5, 1.2, 4.6, 'i')) for sx in (9, 19)]
        head(t, 'w', 'q', 'o'); cover_eyes(t, 'w'); button_eye(t, 10, HY - 2); button_eye(t, 18, HY - 2)
        c.g = [row[:] for row in c.g]
        blk = [r[:] for r in t.g[:27]]
        for y in range(44): c.g[y] = [ch if y > 26 else '.' for ch in c.g[y]] if False else c.g[y]
        for y in range(0, 25):
            for x in range(28):
                if blk[y][x] != '.' and y - 3 >= 0: c.g[y - 3][x] = blk[y][x]
        rect(c, 11, 20, 17, 24, 'i'); rect(c, 11, 22, 17, 22, 'a'); rect(c, 10, 24, 17, 25, 'k')
        drool(c, 14, HY + 4, 8); rect(c, 8, 4, 19, 6, 'j'); rect(c, 7, 7, 20, 7, 'k')
    return c

def cat(v):
    c = C(); tri(c, 8, 3, 7, 8, 'o'); tri(c, 20, 3, 7, 8, 'o')
    cloth = {'A': 'h', 'B': 'i', 'C': 'a', 'D': 'h'}[v]; body(c, cloth, {'A': 'q', 'B': 'i', 'C': 'd', 'D': 'b'}[v])
    head(c, 'o', 'q', 'smile', nose='p'); cover_eyes(c, 'o')
    if v == 'A':                                                       # 노란 세로 눈, 귀까지 찢어진 입, 털이 빠진 얼룩, 침
        for ex in (10.4, 17.6): c.ell(ex, HY - 2, 3.2, 3.8, 'k'); c.ell(ex, HY - 2, 2.4, 3, 'y'); c.line(ex, HY - 4, ex, HY, 1, ch='k'); c.put(ex - 1, HY - 3, 'r'); c.put(ex + 1, HY - 1, 'r')
        for x in range(4, 25): c.put(x, HY + 5 - (3 if x < 7 or x > 21 else 0), 'k')
        teeth_row(c, 6, 22, HY + 6, 2); bald(c, 7, HY - 4, 2, 2); [drool(c, x, HY + 8, 4 + x % 3) for x in (9, 14, 19)]
    if v == 'B':                                                       # 사람 눈 넷, 한쪽 얼굴이 벗겨져 맨살
        bald(c, 9, HY - 1, 4, 5)
        for ex, ey, r in ((9, HY - 4, 1.8), (19, HY - 4, 1.8), (11, HY, 1.8), (17, HY, 2.2)): human_eye(c, ex, ey, r, r - .4, 0, 0)
        stitch_mouth(c, 9, 19, HY + 6)
    if v == 'C':                                                       # 눈구멍이 너무 커서 사람 눈이 헐렁하고, 입은 삐뚤게 꿰맴
        for ex in (10.4, 17.6): c.ell(ex, HY - 2, 4.2, 5.2, 'k'); human_eye(c, ex, HY - 1, 1.8, 1.6, 0, 1, False)
        for x in range(8, 21): c.put(x, HY + 5 + (x // 5) % 2, 'k')
        for x in range(8, 21, 3): c.line(x, HY + 4, x + 1, HY + 7, 1, ch='k')
        crack(c, 22, HY - 7, 20, HY + 2, 'i', 5); drool(c, 15, HY + 9, 5)
    if v == 'D':                                                       # 아래턱이 늘어져 사람 입이 보임
        c.ell(14, HY + 10, 5.6, 6, 'k'); teeth_row(c, 9, 19, HY + 4, 2); c.ell(14, HY + 11, 3, 2.4, 'p')
        for ex in (10.4, 17.6): c.ell(ex, HY - 2, 3.2, 3.8, 'k'); c.ell(ex, HY - 2, 2.4, 3, 'w'); c.put(ex, HY - 4, 'k'); c.put(ex + 1, HY - 4, 'k')
        for x in (9, 19): drool(c, x, HY + 12, 6); drool(c, 14, HY + 15, 4)
    return c

def bear(v):
    c = C()
    for sx in (6, 22): c.ell(sx, 7, 3.2, 3.2, 'n'); c.ell(sx, 7, 1.6, 1.6, 'u')
    cloth = {'A': 'h', 'B': 'd', 'C': 'j', 'D': 'q'}[v]; body(c, cloth, {'A': 'b', 'B': 'd', 'C': 'd', 'D': 'b'}[v])
    head(c, 'n', 'u', 'smile'); cover_eyes(c, 'n')
    if v == 'A':                                                       # 단추 눈 + 찢어진 눈구멍의 사람 눈 + 입에서 터진 솜
        button_eye(c, 10, HY - 2); crack(c, 18, HY - 7, 17, HY, 'i', 2); human_eye(c, 18, HY - 2, 2.2, 2.2, 0, 1)
        for x in range(5, 24): c.put(x, HY + 4 + x % 2, 'k')
        for dx, dy in ((10, 6), (12, 8), (14, 7), (16, 9), (13, 10), (15, 11)): c.ell(dx + 1, HY + dy, 1.4, 1.2, 'w')
        rect(c, 22, 33, 26, 38, 'r')
    if v == 'B':                                                       # 흰자만 보이는 눈, 가슴까지 열린 입, 침
        for ex in (10.4, 17.6): c.ell(ex, HY - 2, 4.2, 5, 'k'); c.ell(ex, HY - 2, 3.4, 4.2, 'w')
        c.ell(14, HY + 7, 6, 6, 'k'); teeth_row(c, 9, 19, HY + 2, 2); teeth_row(c, 9, 19, HY + 11, 2); c.ell(14, HY + 8, 2.4, 2.6, 'p')
        for x in (10, 18): drool(c, x, HY + 14, 5)
    if v == 'C':                                                       # 금 간 안경 + 검은 눈물 + X자로 꿰맨 입
        for ex in (10.4, 17.6):
            c.ell(ex, HY - 2, 4.4, 5.2, 'k'); c.ell(ex, HY - 2, 3.6, 4.4, 'w'); c.put(ex + 1, HY - 1, 'k'); c.put(ex + 1, HY - 2, 'k')
            for k in (0, 1): c.line(ex + k, HY + 2, ex + k, HY + 8 + k * 3, 1, ch='k')
        c.line(9, HY - 6, 13, HY + 1, 1, ch='k'); c.line(18, HY - 6, 15, HY, 1, ch='k')
        for x in range(8, 21, 3): c.line(x, HY + 4, x + 2, HY + 7, 1, ch='k'); c.line(x + 2, HY + 4, x, HY + 7, 1, ch='k')
    if v == 'D':                                                       # 눈이 검은 구멍, 장갑이 벗겨져 길고 누런 맨손
        for ex in (11, 17): c.ell(ex, HY - 4, 1.8, 2.4, 'k')
        c.ell(14, HY + 5, 3, 3, 'k'); drool(c, 14, HY + 8, 8)
        for sx in (6, 21):
            c.ell(sx, 37.5, 2.7, 3.1, '.'); c.ell(sx, 37, 2.2, 2.4, 'i')
            for k in range(4): c.line(sx - 1.5 + k, 38, sx - 2 + k * 1.3, 43, 1, ch='i'); c.put(sx - 2 + k * 1.3, 43, 'a')
    return c

def main():
    root = os.path.join(os.path.dirname(__file__), '..', 'art', 'variants')
    notes = {'rabbit': {'A': '갈라진 탈 틈의 사람 눈, 단추 눈, 꿰맨 입, 침', 'B': '핏발 선 큰 눈, 이빨 세 줄, 침, 찢어진 귀', 'C': '눈구멍의 사람 눈, 사람 입술', 'D': '탈이 목에서 들려 사람 목이 드러남, 침'},
             'cat': {'A': '세로 동공, 귀까지 찢어진 입, 털 빠진 자국, 침', 'B': '사람 눈 넷, 한쪽 얼굴이 벗겨짐, 꿰맨 입', 'C': '헐렁한 사람 눈, 삐뚤게 꿰맨 입, 갈라진 틈', 'D': '늘어진 아래턱, 이빨, 침'},
             'bear': {'A': '단추 눈과 사람 눈, 입에서 터진 솜', 'B': '흰자 눈, 가슴까지 열린 입, 침', 'C': '금 간 안경, 검은 눈물, X자로 꿰맨 입', 'D': '검은 눈구멍, 침, 길고 누런 맨손'}}
    lines = ['# 조력자 기괴한 동물 2차 시안 (tools/gen_grotesque2.py 가 생성함)', '']
    for animal, fn in (('rabbit', rabbit), ('cat', cat), ('bear', bear)):
        for v in 'ABCD':
            lines.append(f'[{animal}_{v}] {notes[animal][v]} | {v}'); lines += fn(v).finish(); lines.append('')
    open(os.path.join(root, 'grotesque2_pixels.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
if __name__ == '__main__': main()
