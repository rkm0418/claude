#!/usr/bin/env python3
"""조력자 마스코트(탈 인형) 시안 12종: 사용자 레퍼런스(오래된 마스코트 탈) 방식.
몸집에 비해 큰 둥근 탈 머리, 고정된 유리 같은 큰 눈, 굳은 입, 흰 장갑, 그 아래는 평범한 사람의 옷차림.
사용: python3 tools/gen_mascot.py && python3 tools/variants.py mascot   (28x44)"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import gen_shadow as G
from gen_shadow import C
from gen_helpers import rect, tri
from gen_creep import tube
G.W, G.H = 28, 44          # (gen_helpers 가 24x38 로 바꾸므로 import 뒤에 지정)

HY = 15   # 머리 중심 y

def body(c, cloth, pants, collar='k'):
    rect(c, 11, 36, 13, 41, pants); rect(c, 15, 36, 17, 41, pants); c.ell(11.5, 42.5, 3.4, 1.6, 'k'); c.ell(16.5, 42.5, 3.4, 1.6, 'k')
    rect(c, 9, 26, 18, 37, cloth); rect(c, 10, 24, 17, 25, collar)
    for sx in (5, 20):
        rect(c, sx, 27, sx + 2, 35, cloth)
        c.ell(sx + 1, 37.5, 2.6, 3, 'w')                              # 흰 장갑
        for k in (-1, 1): c.put(sx + 1 + k, 36, 'k'); c.put(sx + 1 + k, 37, 'k')   # 손등의 세 줄 중 둘

def head(c, fur, muzzle, mouth, nose='k', pupil=(1, 1), eye_gap=3.6):
    c.ell(14, HY, 10, 8.5, fur)
    c.ell(14, HY + 3.5, 6.8, 4.6, muzzle)
    for sx in (-1, 1):
        ex = 14 + sx * eye_gap
        c.ell(ex, HY - 2, 3.5, 4.3, 'k'); c.ell(ex, HY - 2, 2.7, 3.5, 'w')                 # 링이 있는 큰 눈
        c.put(ex + pupil[0], HY - 1 + pupil[1] - 1, 'k'); c.put(ex + pupil[0] + 1, HY - 1 + pupil[1] - 1, 'k'); c.put(ex + pupil[0], HY + pupil[1] - 1, 'k'); c.put(ex + pupil[0] + 1, HY + pupil[1] - 1, 'k')
    c.ell(14, HY + 2, 2, 1.5, nose)
    y = HY + 5
    if mouth == 'open': c.ell(14, y + 1.5, 3.8, 2.2, 'k'); c.ell(14, y + 2.4, 2.4, 1.2, 'p'); c.ell(14, y + 2.6, 1.2, .8, 'r')   # 벌린 입과 혀
    if mouth == 'grin':
        for x in range(8, 21): c.put(x, y, 'k')
        for x in range(9, 20): c.put(x, y + 1, 'w' if x % 2 else 'k')
        c.put(7, y - 1, 'k'); c.put(21, y - 1, 'k')
    if mouth == 'o': c.ell(14, y + 1, 1.8, 2.2, 'k'); c.ell(14, y + 1.4, 1, 1.2, 'r')
    if mouth == 'smile':
        for x in range(10, 19): c.put(x, y + (1 if 11 < x < 17 else 0), 'k')

def rabbit(v):
    c = C()
    for sx in (9, 19): c.ell(sx, 3, 2.3, 6, 'w'); c.ell(sx, 3.5, 1.2, 4.6, 'i')
    cloth = {'A': 'j', 'B': 'j', 'C': 'j', 'D': 'j'}[v]
    body(c, cloth, 'd'); head(c, 'w', 'q', {'A': 'open', 'B': 'grin', 'C': 'o', 'D': 'smile'}[v])
    for y in (28, 31, 34): c.put(13, y, 'y'); c.put(14, y, 'y')
    if v == 'A': rect(c, 8, 7, 19, 9, 'j'); rect(c, 7, 10, 20, 10, 'k'); c.put(14, 8, 'y'); rect(c, 21, 24, 23, 28, 'k'); c.line(23, 24, 25, 18, 1, ch='k')
    if v == 'B': rect(c, 6, 6, 17, 8, 'j'); rect(c, 5, 9, 18, 9, 'k'); c.put(11, 7, 'y'); rect(c, 22, 33, 26, 38, 'q'); c.line(23, 34, 25, 34, 1, ch='k')
    if v == 'C': rect(c, 9, 26, 18, 36, 'o'); rect(c, 9, 30, 18, 30, 'q'); rect(c, 9, 34, 18, 34, 'q'); rect(c, 22, 33, 23, 40, 'k'); c.put(22, 32, 'y'); c.put(23, 32, 'y')
    if v == 'D': rect(c, 6, 5, 21, 9, 'j'); rect(c, 6, 8, 21, 8, 'y'); rect(c, 5, 10, 22, 10, 'k'); c.line(12, 25, 14, 31, 1, ch='y'); c.ell(14, 32, 1.2, 1.2, 'y')
    return c

def cat(v):
    c = C()
    tri(c, 8, 3, 7, 8, 'o'); tri(c, 20, 3, 7, 8, 'o')
    cloth = {'A': 'h', 'B': 'i', 'C': 'a', 'D': 'h'}[v]
    body(c, cloth, {'A': 'q', 'B': 'i', 'C': 'd', 'D': 'b'}[v]); head(c, 'o', 'q', {'A': 'open', 'B': 'grin', 'C': 'o', 'D': 'smile'}[v], nose='p')
    for x in (10, 18): c.line(x, HY - 6, x + (1 if x < 14 else -1), HY - 5, 1, ch='a')
    for dx in (-8, 8): c.line(14 + dx, HY + 4, 14 + dx + (3 if dx < 0 else -3), HY + 4, 1, ch='k')
    if v == 'A':
        rect(c, 10, 28, 17, 37, 'q')
        for x, y in ((11, 30), (14, 32), (16, 30), (12, 35)): c.put(x, y, 'i')
        rect(c, 22, 33, 26, 36, 't'); rect(c, 22, 33, 26, 33, 'c')
    if v == 'B':
        for x in (8, 11, 14, 17, 20): c.ell(x, 7, 1.6, 1.6, 'a')
        rect(c, 9, 31, 18, 31, 'p')
    if v == 'C':
        rect(c, 6, 26, 21, 30, 'a'); rect(c, 7, 31, 20, 32, 'a'); rect(c, 22, 35, 27, 40, 'n'); rect(c, 22, 35, 27, 35, 'u')
    if v == 'D':
        c.ell(10.5, HY - 2, 4, 4.8, 'k'); c.ell(17.5, HY - 2, 4, 4.8, 'k'); c.ell(10.5, HY - 2, 3, 3.8, 'w'); c.ell(17.5, HY - 2, 3, 3.8, 'w')
        c.put(11, HY - 1, 'k'); c.put(12, HY - 1, 'k'); c.put(18, HY - 1, 'k'); c.put(19, HY - 1, 'k'); c.line(14, HY - 2, 14, HY - 2, 1, ch='k')
        c.line(6, HY, 4, 28, 1, ch='y')
    return c

def bear(v):
    c = C()
    for sx in (6, 22): c.ell(sx, 7, 3.2, 3.2, 'n'); c.ell(sx, 7, 1.6, 1.6, 'u')
    cloth = {'A': 'h', 'B': 'd', 'C': 'j', 'D': 'q'}[v]
    body(c, cloth, {'A': 'b', 'B': 'd', 'C': 'd', 'D': 'b'}[v]); head(c, 'n', 'u', {'A': 'smile', 'B': 'open', 'C': 'grin', 'D': 'o'}[v])
    if v == 'A':
        for ex in (10.4, 17.6): c.ell(ex, HY - 2, 4.2, 5, 'k'); c.ell(ex, HY - 2, 3.4, 4.2, 'w'); c.put(ex + 1, HY - 1, 'k'); c.put(ex + 1, HY - 2, 'k')
        c.line(14, HY - 2, 14, HY - 2, 1, ch='k'); rect(c, 11, 26, 16, 36, 'q'); rect(c, 22, 33, 26, 38, 'r'); rect(c, 22, 33, 22, 38, 'k')
    if v == 'B': rect(c, 11, 26, 16, 37, 'q'); rect(c, 13, 27, 14, 33, 'a'); rect(c, 22, 35, 24, 38, 'w')
    if v == 'C':
        for ex in (10.4, 17.6): c.ell(ex, HY - 2, 4.2, 5, 'k'); c.ell(ex, HY - 2, 3.4, 4.2, 'w'); c.put(ex + 1, HY - 1, 'k'); c.put(ex + 1, HY - 2, 'k')
        c.line(11, 25, 14, 35, 1, ch='y'); c.line(17, 25, 14, 35, 1, ch='y'); rect(c, 11, 35, 17, 37, 'q'); rect(c, 22, 32, 27, 40, 'u'); rect(c, 23, 30, 25, 32, 'k')
    if v == 'D': rect(c, 9, 25, 18, 28, 'a'); rect(c, 9, 29, 12, 32, 'a'); rect(c, 22, 34, 26, 38, 't'); rect(c, 27, 35, 27, 37, 't')
    return c

def main():
    root = os.path.join(os.path.dirname(__file__), '..', 'art', 'variants')
    notes = {'rabbit': {'A': '경찰 모자, 어깨 무전기, 벌린 입', 'B': '기울어진 모자, 수첩, 굳은 큰 웃음', 'C': '반사 조끼, 손전등, 작은 O 입', 'D': '큰 모자, 호루라기, 닫힌 미소'},
             'cat': {'A': '꽃무늬 앞치마, 그릇, 벌린 입', 'B': '헤어롤, 가운, 굳은 큰 웃음', 'C': '숄, 바구니, 작은 O 입', 'D': '안경 줄, 카디건, 닫힌 미소'},
             'bear': {'A': '둥근 안경, 카디건, 책, 미소', 'B': '넥타이, 분필, 벌린 입', 'C': '안경, 목걸이 명찰, 서류판, 굳은 웃음', 'D': '목도리, 머그컵, 작은 O 입'}}
    lines = ['# 조력자 마스코트 시안 (tools/gen_mascot.py 가 생성함)', '']
    for animal, fn in (('rabbit', rabbit), ('cat', cat), ('bear', bear)):
        for v in 'ABCD':
            lines.append(f'[{animal}_{v}] {notes[animal][v]} | {v}'); lines += fn(v).finish(); lines.append('')
    open(os.path.join(root, 'mascot_pixels.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
if __name__ == '__main__': main()
