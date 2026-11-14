#!/usr/bin/env python3
"""'혀' 계열 시안 (역겨움 시안 03 기반 8종 + 불쾌 시안 03 기반 '얼굴 가린 손' 3종). 사용: python3 tools/gen_tongue.py && python3 tools/variants.py tongue"""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(__file__))
import gen_shadow as G
G.W, G.H = 48, 84
from gen_shadow import C
from gen_creep import tube, fingers, chaikin
from gen_gross import bigeye, mouth, drool, limbs, wet, CX

def face(c, eyes='roll', hair=0):
    c.ell(CX, 13, 7.5, 9.5, 'w')
    for y in range(3, 9):
        for x in range(CX - 8, CX + 9):
            if c.g[y][x] == 'w': c.put(x, y, 's')
    if hair:
        for sx, ex in ((15, 11), (33, 37), (17, 9), (31, 39)): tube(c, [(sx, 8), (sx - 1, 24), (ex, 50), (ex, 76)], 3, 2, .1, sx, 's')
    if eyes == 'roll':
        c.ell(20, 12, 2.6, 1.6, 'w'); c.ell(29, 12, 2.6, 1.6, 'w'); c.put(20, 11, 'k'); c.put(29, 11, 'k')
        for x in range(17, 33): c.put(x, 10, 'k')
    else:
        for x in (18, 19, 20, 28, 29, 30): c.put(x, 12, 'k')

def base(c, eyes='roll', hair=0, torso_w=10, mouth_h=4.4):
    tube(c, [(CX, 24), (CX, 58)], torso_w, 7, .06); limbs(c, 70, 6, 28, 3)
    face(c, eyes, hair); c.ell(CX, 20, 4.2, mouth_h, 'k')

def tg(c, pts, w0, w1=None, line=True):
    tube(c, pts, w0, w1, .06, 2, 'p')
    if line: tube(c, [(x, y + 1) for x, y in pts], 1, 1, ch='r')

def t1():
    c = C(); base(c); tg(c, [(CX, 20), (CX - 3, 50), (CX - 9, 82)], 4, 5); tg(c, [(CX, 20), (CX + 4, 50), (CX + 10, 82)], 4, 5)
    c.ell(CX - 9, 82, 6, 2, 'p'); c.ell(CX + 10, 82, 6, 2, 'p'); return c, '갈라진 혀: 혀가 둘로 갈라져 바닥까지 늘어짐'
def t2():
    c = C(); base(c); tg(c, [(CX, 20), (CX + 8, 30), (CX - 8, 38), (CX + 8, 46), (CX - 8, 54), (CX + 6, 62), (CX, 70), (CX + 2, 82)], 4, 5)
    return c, '감긴 혀: 혀가 몸을 휘감고 내려옴'
def t3():
    c = C(); base(c, torso_w=11, mouth_h=5); tg(c, [(CX, 20), (CX, 40), (CX + 1, 64)], 10, 12, False)
    for y in range(24, 62, 4): c.put(CX - 3, y, 'r'); c.put(CX + 3, y + 1, 'r'); c.put(CX, y + 2, 'r')
    for x in (CX - 4, CX, CX + 4): drool(c, x, 64, 8)
    return c, '넓은 혀: 두껍고 납작한 혀가 무릎까지 늘어져 침이 떨어짐'
def t4():
    c = C(); base(c, 'closed', 1); tg(c, [(CX, 20), (CX + 1, 44), (CX + 3, 68), (CX + 7, 82)], 5, 7); c.ell(CX + 7, 82, 8, 2, 'p')
    return c, '긴 머리 여자: 눈을 감고 머리카락이 땅까지, 혀도 땅까지'
def t5():
    c = C(); base(c, mouth_h=4.4); mouth(c, 18, 18, 30, 30, 4, False); tg(c, [(CX, 24), (CX - 1, 50), (CX - 3, 68)], 6, 5)
    for x in (20, 28): drool(c, x, 31, 12)
    return c, '벌어진 턱: 입이 목까지 열려 이빨이 드러나고 혀가 늘어짐'
def t6():
    c = C(); base(c); P = [(CX, 20), (CX, 32)]
    for k in range(13): a = k / 12 * 6.28; P.append((CX + 6 * math.sin(a), 38 + 6 * (1 - math.cos(a)) * .9))
    P += [(CX + 1, 54), (CX - 1, 70), (CX + 2, 82)]; tg(c, P, 4, 5)
    return c, '매듭 혀: 혀가 가슴 앞에서 매듭지어짐'
def t7():
    c = C(); base(c); tg(c, [(CX, 20), (CX - 1, 50), (CX - 6, 76), (CX - 18, 81), (0, 81)], 5, 6)
    return c, '끌리는 혀: 혀가 바닥을 따라 한참 뒤로 끌림'
def t8():
    c = C(); base(c); pts = [(CX, 20), (CX + 1, 44), (CX + 3, 68), (CX + 7, 82)]; tg(c, pts, 7, 9)
    for y in range(26, 78, 5):
        x = CX + (y - 20) * .1
        for dx in (-4, 3): c.put(x + dx, y, 'w'); c.put(x + dx, y + 1, 'w')
    return c, '이빨 혀: 혀 가장자리에 사람 이빨이 줄지어 박혀 있음'

def hbase(c):
    tube(c, [(CX, 24), (CX, 58)], 9, 6, .06); tube(c, [(20, 58), (18, 70), (20, 82)], 3.6, 2.2); tube(c, [(28, 58), (30, 70), (28, 82)], 3.6, 2.2)
    c.ell(CX, 13, 7.5, 9.5, 'w')
    for y in range(3, 9):
        for x in range(CX - 8, CX + 9):
            if c.g[y][x] == 'w': c.put(x, y, 's')

def h1():
    c = C(); hbase(c)
    for sx in (-1, 1):
        tube(c, [(CX + sx * 6, 28), (CX + sx * 14, 22), (CX + sx * 6, 14)], 3, 2.4, .1, sx)
        c.ell(CX + sx * 5, 13, 3.6, 7, 'l'); fingers(c, CX + sx * 5, 8, 270 + sx * 20, 4, 13, 40, seed=sx + 4)
    bigeye(c, 22, 12, 1.5, 0, 0, 1); bigeye(c, 26, 12, 1.5, 0, 0, 2)
    return c, '양손 얼굴: 긴 손가락이 얼굴을 덮고 가운데 틈으로 눈 둘이 보임'
def h2():
    c = C(); hbase(c)
    tube(c, [(CX + 6, 28), (CX + 15, 22), (CX + 9, 9)], 3, 2.4, .1, 1); c.ell(CX, 9, 8.5, 3.6, 'l'); fingers(c, CX - 8, 9, 180, 4, 12, 40, seed=7)
    tube(c, [(CX - 6, 28), (CX - 10, 46), (CX - 9, 70)], 3, 2, .1, 2); fingers(c, CX - 9, 70, 90, 4, 10, 36, seed=8)
    c.ell(CX, 19, 4.2, 4.4, 'k'); tube(c, [(CX, 18), (CX, 44), (CX + 2, 66)], 5, 6, .06, 2, 'p'); drool(c, CX - 3, 24, 6)
    return c, '한 손 얼굴: 손이 눈을 가리고 아래의 입에서 혀가 길게 늘어짐'
def h3():
    c = C(); hbase(c); c.ell(CX, 21, 9, 6, 'k'); mouth(c, 17, 17, 31, 26, 5, True)
    for sx in (-1, 1):
        tube(c, [(CX + sx * 7, 30), (CX + sx * 17, 26), (CX + sx * 9, 21)], 3, 2.4, .1, sx); fingers(c, CX + sx * 9, 21, 180 if sx > 0 else 0, 4, 7, 40, seed=sx + 9)
    bigeye(c, 20, 10, 2.4, 0, -1, 3); bigeye(c, 29, 10, 2.4, 0, -1, 4)
    return c, '입을 찢는 손: 양손 손가락을 입꼬리에 걸어 입을 벌리고 있음'

def main():
    root = os.path.join(os.path.dirname(__file__), '..', 'art', 'variants')
    lines = ['# 혀 계열 시안 (tools/gen_tongue.py 가 생성함)', '']
    for i, fn in enumerate([t1, t2, t3, t4, t5, t6, t7, t8, h1, h2, h3]):
        c, desc = fn(); lines.append(f'[{"abc"[i // 4]}_{i + 1:02d}] {desc} | {i + 1}'); lines += wet(c.finish(), i); lines.append('')
    open(os.path.join(root, 'tongue_pixels.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
if __name__ == '__main__': main()
