#!/usr/bin/env python3
"""조력자 기괴한 동물 시안 12종 (마스코트 탈 방식 위에 기괴함을 얹음). 옷과 소지품의 정체 힌트는 그대로.
사용: python3 tools/gen_grotesque.py && python3 tools/variants.py grotesque   (28x44)"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import gen_shadow as G
from gen_shadow import C
from gen_helpers import rect, tri
from gen_mascot import body, head, HY
G.W, G.H = 28, 44

def cover_eyes(c, fur):
    for sx in (-1, 1): c.ell(14 + sx * 3.6, HY - 2, 3.6, 4.4, fur)

def button_eye(c, x, y):
    c.ell(x, y, 2.6, 2.6, 'k'); c.ell(x, y, 1.8, 1.8, 'b')
    for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)): c.put(x + dx, y + dy, 'w')

def stitch_mouth(c, x0, x1, y):
    for x in range(x0, x1 + 1): c.put(x, y, 'k')
    for x in range(x0, x1 + 1, 2): c.put(x, y - 1, 'w'); c.put(x, y + 1, 'w')

def human_hand(c, x, y):
    c.ell(x, y, 2.4, 2.2, 'i')
    for k in range(4): c.line(x - 1.5 + k, y + 1, x - 2 + k * 1.3, y + 5, 1, ch='i')

def teeth_row(c, x0, x1, y, h=2):
    for x in range(x0, x1 + 1):
        for j in range(h): c.put(x, y + j, 'w' if (x - x0) % 2 == 0 else 'k')

def region(c, x0, y0, x1, y1):
    return [c.g[y][x0:x1 + 1] for y in range(y0, y1 + 1)]

def paste(c, blk, x0, y0, transparent=True):
    for j, row in enumerate(blk):
        for i, ch in enumerate(row):
            if (ch != '.' or not transparent) and 0 <= y0 + j < 44 and 0 <= x0 + i < 28: c.g[y0 + j][x0 + i] = ch

def clear(c, x0, y0, x1, y1):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1): c.g[y][x] = '.'

def rabbit(v):
    c = C()
    if v == 'A':                                                       # 바닥까지 늘어진 귀, 단추 눈, 꿰맨 입
        for sx in (-1, 1): c.line(14 + sx * 6, 9, 14 + sx * 11, 40, 2.6, 2, ch='w'); c.line(14 + sx * 6, 12, 14 + sx * 10.5, 38, 1, ch='i')
        body(c, 'j', 'd'); head(c, 'w', 'q', 'smile'); cover_eyes(c, 'w'); button_eye(c, 10, HY - 2); button_eye(c, 18, HY - 1)
        rect(c, 9, 20, 19, 21, 'q'); stitch_mouth(c, 9, 19, HY + 5)
        rect(c, 8, 7, 19, 9, 'j'); rect(c, 7, 10, 20, 10, 'k'); c.put(14, 8, 'y')
    if v == 'B':                                                       # 눈이 머리 양옆 끝으로 벌어진 초식동물 눈 + 사람 이빨
        for sx in (9, 19): c.ell(sx, 3, 2.3, 6, 'w'); c.ell(sx, 3.5, 1.2, 4.6, 'i')
        body(c, 'j', 'd'); head(c, 'w', 'q', 'smile'); cover_eyes(c, 'w')
        for ex in (5, 23): c.ell(ex, HY - 1, 2, 3, 'k'); c.ell(ex, HY - 1, 1.2, 2.2, 'r'); c.put(ex, HY - 1, 'k')
        c.ell(14, HY + 5, 6, 2.6, 'k'); teeth_row(c, 9, 19, HY + 4, 2); teeth_row(c, 10, 18, HY + 6, 1)
        rect(c, 6, 6, 17, 8, 'j'); rect(c, 5, 9, 18, 9, 'k'); c.put(11, 7, 'y'); rect(c, 22, 33, 26, 38, 'q')
    if v == 'C':                                                       # 머리가 옆으로 꺾임, 한쪽 눈은 빈 구멍
        body(c, 'j', 'd'); rect(c, 9, 26, 18, 36, 'o'); rect(c, 9, 30, 18, 30, 'q'); rect(c, 9, 34, 18, 34, 'q')
        t = C(); [t.ell(sx, 3, 2.3, 6, 'w') for sx in (9, 19)]; head(t, 'w', 'q', 'o'); t.ell(10.4, HY - 2, 3.4, 4.2, 'k')
        blk = region(t, 3, 0, 25, 24); rot = [''.join(blk[len(blk) - 1 - j][i] for j in range(len(blk))) for i in range(len(blk[0]))]
        clear(c, 0, 0, 27, 23); paste(c, rot, 2, 0); rect(c, 22, 33, 23, 40, 'k'); c.put(22, 32, 'y')
    if v == 'D':                                                       # 주둥이 자리에 사람의 입술과 작은 사람 눈
        for sx in (9, 19): c.ell(sx, 3, 2.3, 6, 'w'); c.ell(sx, 3.5, 1.2, 4.6, 'i')
        body(c, 'j', 'd'); head(c, 'w', 'i', 'smile'); cover_eyes(c, 'w')
        for ex in (11, 17): c.ell(ex, HY - 2, 3.2, 3.6, 'k'); c.ell(ex, HY - 2, 1.4, 1, 'w'); c.put(ex, HY - 2, 'k')
        for x in range(11, 18): c.put(x, HY + 5, 'r'); c.put(x, HY + 6, 'r' if 12 <= x <= 16 else 'i')
        c.put(14, HY + 2, 'a'); rect(c, 6, 5, 21, 9, 'j'); rect(c, 6, 8, 21, 8, 'y'); rect(c, 5, 10, 22, 10, 'k')
    return c

def cat(v):
    c = C()
    if v != 'C': tri(c, 8, 3, 7, 8, 'o'); tri(c, 20, 3, 7, 8, 'o')
    cloth = {'A': 'h', 'B': 'i', 'C': 'a', 'D': 'h'}[v]
    body(c, cloth, {'A': 'q', 'B': 'i', 'C': 'd', 'D': 'b'}[v])
    if v == 'A':                                                       # 노란 세로 동공의 큰 눈, 귀까지 찢어진 입
        head(c, 'o', 'q', 'smile', nose='p'); cover_eyes(c, 'o')
        for ex in (10.4, 17.6): c.ell(ex, HY - 2, 3.2, 3.8, 'k'); c.ell(ex, HY - 2, 2.4, 3, 'y'); c.line(ex, HY - 4, ex, HY, 1, ch='k')
        for x in range(5, 24): c.put(x, HY + 5 - (2 if x < 8 or x > 20 else 0), 'k')
        teeth_row(c, 7, 21, HY + 6, 1); rect(c, 10, 28, 17, 37, 'q'); rect(c, 22, 33, 26, 36, 't')
    if v == 'B':                                                       # 작은 눈 네 개
        head(c, 'o', 'q', 'smile', nose='p'); cover_eyes(c, 'o')
        for ex, ey in ((9, HY - 4), (19, HY - 4), (11, HY - 1), (17, HY - 1)): c.ell(ex, ey, 1.8, 1.8, 'k'); c.ell(ex, ey, 1, 1, 'w'); c.put(ex, ey, 'k')
        for x in (8, 11, 14, 17, 20): c.ell(x, 7, 1.6, 1.6, 'a')
    if v == 'C':                                                       # 머리가 위아래로 뒤집힘(귀가 아래, 입이 위)
        t = C(); tri(t, 8, 3, 7, 8, 'o'); tri(t, 20, 3, 7, 8, 'o'); head(t, 'o', 'q', 'open', nose='p')
        blk = region(t, 0, 0, 27, 24); paste(c, blk[::-1], 0, 0)
        rect(c, 22, 35, 27, 40, 'n'); rect(c, 22, 35, 27, 35, 'u')
    if v == 'D':                                                       # 눈과 입의 자리가 바뀜(입이 위, 눈이 아래)
        c.ell(14, HY, 10, 8.5, 'o'); c.ell(14, HY + 3, 7, 5, 'q')
        c.ell(14, HY - 3, 4.4, 2.2, 'k'); teeth_row(c, 11, 17, HY - 4, 1)
        for ex in (10.5, 17.5): c.ell(ex, HY + 3, 2.6, 2.8, 'k'); c.ell(ex, HY + 3, 1.8, 2, 'w'); c.put(ex, HY + 3, 'k')
        c.ell(14, HY - 7, 1.4, 1, 'p'); c.line(6, HY, 4, 28, 1, ch='y')
    return c

def bear(v):
    c = C()
    for sx in (6, 22): c.ell(sx, 7, 3.2, 3.2, 'n'); c.ell(sx, 7, 1.6, 1.6, 'u')
    cloth = {'A': 'h', 'B': 'd', 'C': 'j', 'D': 'q'}[v]
    body(c, cloth, {'A': 'b', 'B': 'd', 'C': 'd', 'D': 'b'}[v])
    if v == 'A':                                                       # 얼굴을 가로지르는 바늘땀, 단추 눈, 어깨 솜이 터짐
        head(c, 'n', 'u', 'smile'); cover_eyes(c, 'n'); button_eye(c, 10, HY - 2); button_eye(c, 18, HY - 3)
        for x in range(5, 24): c.put(x, HY + (x % 2), 'k')
        for y in range(HY - 8, HY + 8): c.put(14 + (y % 2), y, 'k')
        c.ell(19, 26, 3, 2.4, 'w'); c.put(18, 25, 'q'); c.put(20, 27, 'q'); rect(c, 22, 33, 26, 38, 'r')
    if v == 'B':                                                       # 가슴까지 벌어진 입, 사람 이빨 두 줄
        head(c, 'n', 'u', 'smile'); c.ell(14, HY + 7, 6, 6, 'k'); teeth_row(c, 9, 19, HY + 2, 2); teeth_row(c, 9, 19, HY + 11, 2)
        c.ell(14, HY + 8, 2.4, 2.6, 'p'); rect(c, 22, 35, 24, 38, 'w')
    if v == 'C':                                                       # 깨진 안경 아래로 흘러내리는 눈
        head(c, 'n', 'u', 'grin')
        for ex in (10.4, 17.6):
            c.ell(ex, HY - 2, 4.2, 5, 'k'); c.ell(ex, HY - 2, 3.4, 4.2, 'w'); c.put(ex + 1, HY - 1, 'k'); c.put(ex + 1, HY - 2, 'k')
            for k in (0, 1): c.line(ex + k, HY + 1, ex + k, HY + 5 + k * 2, 1, ch='k')
        c.line(16, HY - 5, 19, HY + 1, 1, ch='k'); c.line(11, 25, 14, 35, 1, ch='y'); c.line(17, 25, 14, 35, 1, ch='y'); rect(c, 22, 32, 27, 40, 'u')
    if v == 'D':                                                       # 장갑 대신 사람 맨손, 눈은 너무 작고 높음
        head(c, 'n', 'u', 'o'); cover_eyes(c, 'n')
        for ex in (12, 16): c.put(ex, HY - 5, 'k'); c.put(ex, HY - 4, 'k')
        for sx in (6, 21): c.ell(sx, 37.5, 2.7, 3.1, '.'); human_hand(c, sx, 37)
        rect(c, 9, 25, 18, 28, 'a'); rect(c, 22, 30, 26, 33, 't')
    return c

def main():
    root = os.path.join(os.path.dirname(__file__), '..', 'art', 'variants')
    notes = {'rabbit': {'A': '바닥까지 늘어진 귀, 단추 눈, 꿰맨 입 (경찰 모자)', 'B': '머리 양끝의 붉은 눈, 사람 이빨 (기울어진 모자)', 'C': '옆으로 꺾인 머리, 빈 눈구멍 (반사 조끼)', 'D': '주둥이 자리의 사람 입술과 작은 사람 눈 (큰 모자)'},
             'cat': {'A': '세로 동공의 노란 눈, 귀까지 찢어진 입 (앞치마)', 'B': '작은 눈 넷 (헤어롤)', 'C': '위아래로 뒤집힌 머리 (숄과 바구니)', 'D': '입과 눈의 자리가 바뀜 (안경 줄)'},
             'bear': {'A': '바늘땀, 단추 눈, 터진 어깨 솜 (책)', 'B': '가슴까지 벌어진 입과 이빨 두 줄 (넥타이)', 'C': '깨진 안경, 흘러내리는 눈 (명찰과 서류판)', 'D': '사람 맨손, 작고 높은 눈 (목도리와 머그컵)'}}
    lines = ['# 조력자 기괴한 동물 시안 (tools/gen_grotesque.py 가 생성함)', '']
    for animal, fn in (('rabbit', rabbit), ('cat', cat), ('bear', bear)):
        for v in 'ABCD':
            lines.append(f'[{animal}_{v}] {notes[animal][v]} | {v}'); lines += fn(v).finish(); lines.append('')
    open(os.path.join(root, 'grotesque_pixels.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
if __name__ == '__main__': main()
