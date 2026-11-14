#!/usr/bin/env python3
"""'얼굴을 가린 손' 계열 시안 (불쾌 시안 03 기반 12종). 사용: python3 tools/gen_hand_faceless.py && python3 tools/variants.py hand
캔버스 32x56. fing() 이 긴 손가락(관절 3마디, 끝이 말림), eye() 가 사람 눈."""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(__file__))
from gen_shadow import C
from gen_creep import tube
eye = lambda *a, **k: None   # 얼굴 없음
jag = lambda *a, **k: None

def fing(c, x, y, ang, n=5, L=10, spread=70, curl=0, seed=1):
    r = random.Random(seed)
    for k in range(n):
        side = (k - (n - 1) / 2)
        a = math.radians(ang + side * spread / max(1, n - 1)); px, py = x, y
        for s in range(3):
            st = L / 3 * (.85 + r.random() * .3); nx, ny = px + math.cos(a) * st, py + math.sin(a) * st
            c.line(px, py, nx, ny, 1, ch='l'); px, py = nx, ny; a += math.radians(curl * (1 if side >= 0 else -1))

def palm(c, x, y, rx, ry): c.ell(x, y, rx, ry, 'l')

def body(c, hx=16, hy=9, torso_top=19, hips=36, hunch=False):
    c.ell(hx, hy, 4, 5.2); tube(c, [(hx, hy + 4), (16, torso_top)], 2.6)
    tube(c, [(16, torso_top), (16, hips)], 7, 4, .08)
    tube(c, [(14, hips), (12, 46), (14, 55)], 2.4, 1.6); tube(c, [(18, hips), (20, 46), (18, 55)], 2.4, 1.6)

def long_arm(c, sx=-1, seed=2):
    X = 16 + sx * 4
    tube(c, [(X, 22), (X + sx * 4, 38), (X + sx * 3, 47)], 2.2, 1.3, .15, seed); fing(c, X + sx * 3, 47, 90, 4, 9, 36, seed=seed)

def v1():
    c = C(); body(c)
    for sx in (-1, 1):
        tube(c, [(16 + sx * 4, 22), (16 + sx * 9, 17), (16 + sx * 5, 10)], 2.2, 1.6); palm(c, 16 + sx * 5, 10, 2.4, 3.6)
        fing(c, 16 + sx * 5, 8, -90 + sx * 35, 5, 10, 50, seed=sx + 3)
    eye(c, 14, 9, 1.2, 1, 0); eye(c, 18, 9, 1.2, -1, 0)
    return c, '양손 가리기: 두 손의 긴 손가락이 얼굴을 덮고 가운데 틈 사이는 어둠뿐'
def v2():
    c = C(); body(c); long_arm(c, -1)
    tube(c, [(20, 22), (26, 15), (21, 4)], 2.2, 1.6); palm(c, 21, 4, 3, 3); fing(c, 21, 5, 112, 5, 22, 56, curl=12, seed=4)
    eye(c, 13, 9, 1.3, 0, 0)
    return c, '내리덮는 손: 손가락이 얼굴을 지나 가슴까지 늘어져 갈고리처럼 휘어짐'
def v3():
    c = C(); body(c); long_arm(c, -1)
    tube(c, [(20, 22), (24, 12), (18, 2)], 2.2, 1.6); palm(c, 16, 2, 4, 2.4); fing(c, 16, 3, 90, 6, 11, 130, curl=22, seed=5)
    eye(c, 15, 9, 1.4, 0, 0)
    return c, '머리를 움켜쥔 손: 손가락이 두개골을 감싸 쥐고 틈 사이는 어둠뿐'
def v4():
    c = C(); body(c); long_arm(c, -1)
    tube(c, [(20, 22), (24, 17), (19, 14)], 2.2, 1.6); palm(c, 16, 14, 4.6, 3); fing(c, 13, 13, 200, 5, 10, 60, seed=6)
    eye(c, 13, 7, 2, 0, 0); eye(c, 19, 7, 1.4, 0, 1)
    return c, '입 가리기: 손이 입을 막고 눈 둘이 크게 뜨고 있음'
def v5():
    c = C(); body(c)
    for sx in (-1, 1):
        tube(c, [(16 + sx * 4, 22), (16 + sx * 10, 16), (16 + sx * 7, 10)], 2.2, 1.6); palm(c, 16 + sx * 8, 10, 2.6, 3.5)
        fing(c, 16 + sx * 6, 10, 90 - sx * 90 if sx > 0 else 0, 4, 6, 34, curl=18, seed=sx + 6)
    eye(c, 14, 8, 1.4, 0, -1); eye(c, 18, 8, 1.4, 0, -1); c.ell(16, 14, 1.8, 3, 'k'); jag(c, 15, 17, 12, 4)
    return c, '볼을 파고드는 손: 양손 손가락이 뺨에 박혀 얼굴을 늘림, 입이 세로로 벌어짐'
def v6():
    c = C(); body(c); long_arm(c, -1)
    tube(c, [(20, 22), (26, 14), (21, 6)], 2.2, 1.6); palm(c, 21, 6, 3, 3); fing(c, 20, 6, 200, 8, 14, 130, curl=-8, seed=7)
    eye(c, 13, 9, 1.3, 0, 0)
    return c, '부채 손가락: 손가락이 여덟 개로 부채처럼 펼쳐져 얼굴을 덮음'
def v7():
    c = C(); body(c); long_arm(c, -1)
    tube(c, [(20, 22), (27, 25), (29, 14), (23, 7), (18, 8)], 2, 1.4); palm(c, 18, 8, 2.6, 3); fing(c, 17, 8, 190, 5, 12, 60, seed=8)
    eye(c, 14, 11, 1.2, 0, 0)
    return c, '꺾인 팔: 팔꿈치가 세 번 꺾인 긴 팔이 얼굴로 감겨 올라옴'
def v8():
    c = C(); body(c, hy=11)
    tube(c, [(12, 22), (7, 12), (9, 3)], 2, 1.4); palm(c, 9, 3, 2.4, 2.6); fing(c, 9, 2, -90, 5, 8, 70, seed=9)
    tube(c, [(20, 24), (25, 18), (20, 11)], 2.2, 1.6); palm(c, 19, 11, 3, 3.5); fing(c, 18, 9, 215, 5, 11, 60, seed=10)
    eye(c, 13, 11, 1.3, 0, 0)
    return c, '한 손은 가리고 한 손은 흔듦: 얼굴 가린 손 반대편 팔이 높이 올라가 손을 흔듦'
def v9():
    c = C(); body(c)
    long_arm(c, -1); tube(c, [(20, 22), (24, 15), (20, 8)], 2.2, 1.6); palm(c, 16, 8, 5.2, 2.6)
    for x in (12, 14, 18, 20): c.line(x, 9, x + (x - 16) // 4, 18, 1, ch='l')
    jag(c, 13, 19, 14, 11); jag(c, 14, 18, 14, 3)
    return c, '손가락 틈 입: 눈은 손바닥에 가리고 벌어진 손가락 사이로 이빨이 보임'
def v10():
    c = C(); body(c); long_arm(c, -1)
    tube(c, [(20, 22), (25, 15), (20, 9)], 2.2, 1.6); palm(c, 19, 9, 3.6, 4.6); eye(c, 19, 9, 1.6, 0, 1); fing(c, 19, 5, 215, 5, 12, 70, seed=12)
    eye(c, 13, 9, 1.3, 0, 0)
    return c, '손바닥 눈: 얼굴을 덮은 손바닥에도 눈이 하나 박혀 있음'
def v11():
    c = C(); body(c, hy=14, torso_top=21, hips=38)
    for sx in (-1, 1):
        tube(c, [(16 + sx * 5, 24), (16 + sx * 9, 20), (16 + sx * 5, 15)], 2.2, 1.6); palm(c, 16 + sx * 5, 15, 3, 3.6)
        fing(c, 16 + sx * 5, 12, -90 + sx * 30, 5, 9, 46, seed=sx + 13)
    eye(c, 14, 14, 1.2, 1, 0); eye(c, 18, 14, 1.2, -1, 0)
    return c, '까꿍: 웅크린 자세로 두 손바닥 사이 틈에서 눈 둘이 올려다봄'
def v12():
    c = C(); c.ell(16, 6, 3.6, 4.6); tube(c, [(16, 9), (16, 24)], 1.8); tube(c, [(16, 24), (16, 40)], 7, 4, .08)
    tube(c, [(14, 40), (12, 48), (14, 55)], 2.4, 1.6); tube(c, [(18, 40), (20, 48), (18, 55)], 2.4, 1.6)
    tube(c, [(12, 26), (8, 40), (9, 50)], 2.2, 1.3, .15, 2); fing(c, 9, 50, 90, 4, 5, 36, seed=14)
    tube(c, [(20, 26), (26, 18), (19, 7)], 2.2, 1.6); palm(c, 19, 7, 3, 3.6); fing(c, 18, 5, 215, 5, 11, 60, seed=15)
    eye(c, 13, 6, 1.2, 0, 0)
    return c, '긴 목: 목이 길게 늘어나 머리가 높이 있고, 팔이 닿도록 올라가 얼굴을 가림'

def main():
    root = os.path.join(os.path.dirname(__file__), '..', 'art', 'variants')
    lines = ['# 얼굴 없는 손 계열 (tools/gen_hand_faceless.py 가 생성함)', '']
    for i, fn in enumerate([v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12]):
        c, desc = fn(); lines.append(f'[{"abc"[i // 4]}_{i + 1:02d}] {desc} | {i + 1}'); lines += c.finish(); lines.append('')
    open(os.path.join(root, 'faceless_pixels.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
if __name__ == '__main__': main()
