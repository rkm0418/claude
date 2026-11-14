#!/usr/bin/env python3
"""조력자 시안: 토끼(경찰), 고양이(이웃), 곰(교사/상담사) 각 4종. 겉모습은 인형 같은 동물, 옷과 소지품에 정체가 드러남.
사용: python3 tools/gen_helpers.py && python3 tools/variants.py helpers   (24x38, 아이 키(19px)의 2배)"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import gen_shadow as G
G.W, G.H = 24, 38
from gen_shadow import C
from gen_creep import tube

def rect(c, x0, y0, x1, y1, ch):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1): c.put(x, y, ch)

def tri(c, cx, top, w, h, ch):
    for j in range(h):
        half = (w / 2) * (j + 1) / h
        for x in range(int(cx - half + .5), int(cx + half + .5) + 1): c.put(x, top + j, ch)

def base(c, fur, cloth, pants, shoe='k', hy=12):
    rect(c, 9, 31, 11, 36, pants); rect(c, 13, 31, 15, 36, pants); rect(c, 8, 36, 11, 37, shoe); rect(c, 13, 36, 16, 37, shoe)
    rect(c, 7, 18, 16, 31, cloth); rect(c, 8, 17, 15, 17, cloth)
    for sx in (4, 17): rect(c, sx, 19, sx + 2, 28, cloth); c.ell(sx + 1, 29, 1.8, 1.8, fur)
    rect(c, 10, 16, 13, 18, fur); c.ell(12, hy, 5.8, 5.2, fur)

def face(c, hy=12, eye=10, gap=4, nose='p', mouth=True, snout=None):
    if snout: c.ell(12, hy + 2.5, 2.8, 2, snout)
    for ex in (eye, eye + gap): c.put(ex, hy - 1, 'k'); c.put(ex, hy - 2, 'k'); c.put(ex + 1, hy - 1, 'k'); c.put(ex + 1, hy - 2, 'k')
    c.put(12, hy + 1, nose)
    if mouth: c.put(11, hy + 3, 'k'); c.put(12, hy + 3, 'k'); c.put(13, hy + 3, 'k'); c.put(10, hy + 2, 'k'); c.put(14, hy + 2, 'k')

# ---------- 토끼(경찰) ----------
def rabbit(v):
    c = C(); fur = 'w'
    ears = {'A': lambda: [c.ell(9, 4, 1.9, 5.5, fur), c.ell(15, 4, 1.9, 5.5, fur), c.ell(9, 4, 1, 4.2, 'i'), c.ell(15, 4, 1, 4.2, 'i')],
            'B': lambda: [tube(c, [(8, 8), (4, 11), (4, 19)], 3.6, 2.6, ch=fur), tube(c, [(16, 8), (20, 11), (20, 19)], 3.6, 2.6, ch=fur)],
            'C': lambda: [c.ell(9, 4, 1.9, 5.5, fur), c.ell(9, 4, 1, 4.2, 'i'), tube(c, [(15, 7), (19, 4), (21, 9)], 3.2, 2.4, ch=fur)],
            'D': lambda: [c.ell(8, 6, 2.4, 2.6, fur), c.ell(16, 6, 2.4, 2.6, fur)]}[v]
    ears()
    base(c, fur, 'j', 'd'); face(c, snout='q')
    for y in (21, 25, 29): c.put(11, y, 'y'); c.put(12, y, 'y')
    if v == 'A': rect(c, 8, 5, 15, 7, 'j'); rect(c, 7, 8, 16, 8, 'k'); c.put(12, 6, 'y'); rect(c, 17, 18, 19, 21, 'k'); c.line(19, 18, 21, 12, 1, ch='k')
    if v == 'B': rect(c, 6, 4, 14, 6, 'j'); rect(c, 5, 7, 15, 7, 'k'); c.put(10, 5, 'y'); rect(c, 18, 25, 21, 29, 'q'); c.line(19, 26, 21, 26, 1, ch='k')
    if v == 'C':
        rect(c, 8, 19, 15, 29, 'o'); rect(c, 8, 23, 15, 23, 'q'); rect(c, 8, 27, 15, 27, 'q'); rect(c, 7, 7, 16, 8, 'q'); rect(c, 18, 26, 19, 31, 'k'); c.put(18, 25, 'y'); c.put(19, 25, 'y')
    if v == 'D': rect(c, 6, 3, 17, 7, 'j'); rect(c, 6, 6, 17, 6, 'y'); rect(c, 5, 8, 18, 8, 'k'); c.line(10, 18, 12, 24, 1, ch='y'); c.ell(12, 25, 1.2, 1.2, 'y')
    return c

# ---------- 고양이(이웃) ----------
def cat(v):
    c = C(); fur = 'o'
    pa = {'A': (7, 15), 'B': (8, 14), 'C': (7, 15), 'D': (8, 14)}[v]
    tri(c, pa[0], 3, 5, 6, fur); tri(c, pa[1] + 1, 3, 5, 6, fur)
    cloth = {'A': 'h', 'B': 'i', 'C': 'a', 'D': 'h'}[v]
    base(c, fur, cloth, {'A': 'q', 'B': 'i', 'C': 'd', 'D': 'b'}[v], shoe='p'); face(c, snout='q', nose='p')
    for x in (9, 15): c.line(x, 9, x + (1 if x < 12 else -1), 10, 1, ch='a')                    # 이마 줄무늬
    for dx in (-5, 5): c.line(12 + dx, 13, 12 + dx + (2 if dx < 0 else -2), 13, 1, ch='k')       # 수염
    if v == 'A':
        rect(c, 8, 20, 15, 31, 'q')
        for x, y in ((9, 22), (12, 24), (14, 22), (10, 27), (13, 28)): c.put(x, y, 'i')
        rect(c, 17, 25, 21, 28, 't'); rect(c, 17, 25, 21, 25, 'c')
    if v == 'B':
        for x in (7, 9, 11, 13, 15): c.ell(x, 5, 1.4, 1.4, 'a')
        rect(c, 8, 22, 15, 22, 'p')
    if v == 'C':
        rect(c, 5, 18, 18, 22, 'a'); rect(c, 6, 23, 17, 24, 'a'); rect(c, 17, 27, 22, 32, 'n'); rect(c, 17, 27, 22, 27, 'u')
    if v == 'D':
        c.ell(10, 11, 1.8, 1.8, 'k'); c.ell(14, 11, 1.8, 1.8, 'k'); c.ell(10, 11, .8, .8, 'w'); c.ell(14, 11, .8, .8, 'w'); c.line(10, 11, 14, 11, 1, ch='k')
        c.line(7, 12, 5, 20, 1, ch='y'); rect(c, 18, 25, 20, 28, 'q')
    return c

# ---------- 곰(교사/상담사) ----------
def bear(v):
    c = C(); fur = 'n'
    c.ell(8, 8, 2.4, 2.4, fur); c.ell(16, 8, 2.4, 2.4, fur); c.ell(8, 8, 1.1, 1.1, 'u'); c.ell(16, 8, 1.1, 1.1, 'u')
    cloth = {'A': 'h', 'B': 'd', 'C': 'j', 'D': 'q'}[v]
    base(c, fur, cloth, {'A': 'b', 'B': 'd', 'C': 'd', 'D': 'b'}[v]); face(c, snout='u', nose='k')
    rect(c, 14, 18, 17, 18, 'q') if False else None
    if v == 'A':
        c.ell(10, 11, 2, 2, 'k'); c.ell(14, 11, 2, 2, 'k'); c.ell(10, 11, 1, 1, 'w'); c.ell(14, 11, 1, 1, 'w'); c.line(12, 11, 12, 11, 1, ch='k')
        rect(c, 10, 19, 13, 28, 'q'); rect(c, 18, 25, 22, 29, 'r'); rect(c, 18, 25, 18, 29, 'k')
    if v == 'B':
        rect(c, 10, 18, 13, 30, 'q'); rect(c, 11, 19, 12, 25, 'a'); rect(c, 18, 27, 20, 29, 'w')
    if v == 'C':
        c.ell(10, 11, 2, 2, 'k'); c.ell(14, 11, 2, 2, 'k'); c.ell(10, 11, 1, 1, 'w'); c.ell(14, 11, 1, 1, 'w')
        c.line(10, 18, 12, 27, 1, ch='y'); c.line(14, 18, 12, 27, 1, ch='y'); rect(c, 10, 27, 14, 30, 'q'); rect(c, 18, 24, 22, 31, 'u'); rect(c, 19, 22, 21, 24, 'k')
    if v == 'D':
        rect(c, 7, 18, 16, 21, 'a'); rect(c, 7, 22, 9, 25, 'a'); rect(c, 18, 26, 21, 29, 't'); rect(c, 22, 27, 22, 28, 't')
    return c

def main():
    root = os.path.join(os.path.dirname(__file__), '..', 'art', 'variants')
    lines = ['# 조력자 시안 (tools/gen_helpers.py 가 생성함)', '']
    notes = {'rabbit': {'A': '경찰 모자와 어깨 무전기', 'B': '처진 귀, 기울어진 모자, 수첩', 'C': '반사 조끼와 손전등', 'D': '큰 모자와 호루라기'},
             'cat': {'A': '꽃무늬 앞치마와 그릇', 'B': '헤어롤과 실내 가운', 'C': '숄과 바구니', 'D': '안경 줄과 카디건'},
             'bear': {'A': '둥근 안경, 카디건, 책', 'B': '넥타이와 분필', 'C': '목걸이 명찰과 서류판', 'D': '목도리와 머그컵'}}
    for animal, fn in (('rabbit', rabbit), ('cat', cat), ('bear', bear)):
        for v in 'ABCD':
            lines.append(f'[{animal}_{v}] {notes[animal][v]} | {v}'); lines += fn(v).finish(); lines.append('')
    open(os.path.join(root, 'helpers_pixels.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
if __name__ == '__main__': main()
