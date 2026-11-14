#!/usr/bin/env python3
"""검은 인간 2차 시안 (불쾌함 중심). 사용: python3 tools/gen_creep.py && python3 tools/variants.py creep
원칙: 좌우 비대칭, 사람과 비슷한 부분(눈, 이, 손가락, 얼굴)만 남기고 나머지는 어긋나게. 곡선 팔다리."""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(__file__))
from gen_shadow import C, W, H

def chaikin(pts, n=2):
    for _ in range(n):
        out = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            out += [(a[0] * .75 + b[0] * .25, a[1] * .75 + b[1] * .25), (a[0] * .25 + b[0] * .75, a[1] * .25 + b[1] * .75)]
        out.append(pts[-1]); pts = out
    return pts

def tube(c, pts, w0, w1=None, wob=0.0, seed=0, ch='s'):
    w1 = w0 if w1 is None else w1
    P = chaikin(pts)
    for i, (x, y) in enumerate(P):
        f = i / max(1, len(P) - 1)
        w = (w0 + (w1 - w0) * f) * (1 + wob * math.sin(i * .22 + seed))
        c.disc(x, y, max(.5, w / 2), ch)

def fingers(c, x, y, ang=90, n=5, L=8, spread=60, ch='l', seed=1):
    r = random.Random(seed)
    n = min(n, 4); spread = min(spread, 38); L = min(L, 8) if ang > 45 and ang < 135 else L
    for k in range(n):
        a = math.radians(ang + (k - (n - 1) / 2) * spread / max(1, n - 1))
        l = L * (0.8 + r.random() * .4); b = math.radians(r.choice((-28, 28)))
        p1 = (x + math.cos(a) * l * .55, y + math.sin(a) * l * .55)
        p2 = (p1[0] + math.cos(a + b) * l * .5, p1[1] + math.sin(a + b) * l * .5)
        c.line(x, y, *p1, 1, ch=ch); c.line(*p1, *p2, 1, ch=ch)

def eye(c, x, y, r=1.6, px=0, py=0, sq=1.0):
    c.ell(x, y, r * 1.5, r * sq, 'w'); c.put(x + px, y + py, 'k')
    if r > 1.7: c.put(x + px + 1, y + py, 'k')
    for i in range(int(-r * 1.5), int(r * 1.5) + 1): c.put(x + i, y - r * sq - 1, 'k')   # 눈꺼풀 선

def jag(c, x0, x1, y, seed=3, up=False):
    r = random.Random(seed)
    for x in range(x0, x1 + 1):
        if (x - x0) % 2 == 0:
            for j in range(r.randint(1, 3)): c.put(x, y - j if up else y + j, 'w')
        else: c.put(x, y, 'k')

def legs2(c, bend=1):
    tube(c, [(14, 36), (12, 46), (14, 55)], 2.4, 1.6); tube(c, [(18, 36), (20, 46), (18, 55)], 2.4, 1.6)

def d01():  # 꺾인 목
    c = C(); tube(c, [(17, 19), (16, 36)], 6, 4, .1); tube(c, [(14, 19), (9, 22), (8, 25)], 3.2)
    c.ell(8, 28, 4.2, 5.4); eye(c, 6, 27, 1.7, -1, 0); eye(c, 11, 29, 1.2, 0, 1); jag(c, 6, 11, 33, 5)
    tube(c, [(13, 22), (10, 40), (11, 47)], 2.2, 1.4, .15, 1); tube(c, [(20, 21), (25, 38), (23, 47)], 2.2, 1.3, .15, 2)
    legs2(c); fingers(c, 11, 47, 95, 5, 9, 70, seed=2); fingers(c, 23, 47, 85, 5, 11, 70, seed=4)
    return c, '꺾인 목: 머리가 어깨 옆에 매달려 옆으로 얼굴을 보임'

def d02():  # 게걸음, 얼굴이 거꾸로
    c = C(); c.ell(16, 29, 7, 3.6); c.ell(16, 35, 5, 3.4)
    tube(c, [(11, 29), (6, 33), (5, 44), (3, 54)], 2.2, 1.5, .12); tube(c, [(21, 29), (26, 33), (27, 44), (29, 54)], 2.2, 1.5, .12)
    tube(c, [(14, 37), (9, 40), (8, 48), (7, 54)], 2.4, 1.6); tube(c, [(18, 37), (23, 40), (24, 48), (25, 54)], 2.4, 1.6)
    tube(c, [(16, 30), (16, 38), (16, 42)], 3); c.ell(16, 47, 4.4, 4.8)
    jag(c, 13, 19, 43, 7, up=False); eye(c, 13, 47, 1.6, 0, 1); eye(c, 19, 48, 1.3, 1, 1)
    fingers(c, 3, 55, 90, 5, 5, 80, seed=3); fingers(c, 29, 55, 90, 5, 5, 80, seed=5)
    return c, '게걸음: 몸을 뒤로 젖히고 거꾸로 매달린 얼굴이 정면을 봄'

def d03():  # 손으로 얼굴 가림
    c = C(); c.ell(16, 9, 4, 5.2); tube(c, [(16, 13), (16, 19)], 2.6); tube(c, [(16, 19), (16, 36)], 7, 4, .08)
    tube(c, [(20, 22), (25, 16), (20, 9)], 2.2, 1.6); tube(c, [(12, 22), (8, 40), (9, 47)], 2.2, 1.3, .15, 2); legs2(c)
    eye(c, 14, 9, 1.3, -1, 0)
    fingers(c, 19, 11, 215, 5, 12, 80, seed=6); fingers(c, 9, 47, 90, 5, 11, 70, seed=8)
    return c, '손가락 사이: 한 손의 긴 손가락이 얼굴을 가리고, 틈으로 눈 하나가 보임'

def d04():  # 입이 귀까지
    c = C(); c.ell(16, 10, 7.5, 7.5)
    for x in range(8, 25):
        y = int(16 - 7 * ((x - 16) / 8.5) ** 2)
        c.put(x, y, 'k')
        for j in range(1, random.Random(x).randint(2, 4)): c.put(x, y + j, 'w' if x % 2 == 0 else 'k')
    eye(c, 12, 6, 1.9, 0, 0); eye(c, 20, 9, 1.2, 1, 1, .8)
    tube(c, [(16, 17), (16, 23)], 3); tube(c, [(16, 22), (16, 38)], 5, 3.4, .1)
    tube(c, [(13, 24), (8, 40), (9, 47)], 2, 1.3, .15, 1); tube(c, [(19, 24), (24, 38), (23, 47)], 2, 1.3, .15, 3); legs2(c)
    fingers(c, 9, 47, 90, 5, 10, 60, seed=9); fingers(c, 23, 47, 90, 5, 10, 60, seed=10)
    return c, '찢어진 웃음: 입꼬리가 얼굴 가장자리까지 올라가고 눈 크기가 서로 다름'

def d05():  # 몸 곳곳의 눈
    c = C(); c.ell(16, 8, 3.8, 5); tube(c, [(16, 12), (16, 20)], 3); tube(c, [(16, 19), (16, 37)], 7, 4.4, .1)
    tube(c, [(12, 22), (7, 38), (8, 47)], 2.4, 1.4, .1, 1); tube(c, [(20, 22), (26, 36), (24, 47)], 2.4, 1.4, .1, 2); legs2(c)
    for x, y, r, px, py in [(14, 7, 1.5, 0, 0), (19, 9, 1.0, 1, 0), (16, 23, 1.2, 0, 1), (14, 29, 1.0, -1, 0), (19, 27, 1.6, 0, 0),
                            (8, 38, 1.0, 0, 1), (25, 40, 1.1, 0, 0), (13, 44, 1.0, 0, 0), (19, 36, 0.9, 0, 0)]:
        eye(c, x, y, r, px, py)
    fingers(c, 8, 47, 90, 5, 9, 60, seed=11); fingers(c, 24, 47, 90, 5, 9, 60, seed=12)
    return c, '눈투성이: 머리와 몸, 팔다리 곳곳에 크기가 다른 사람 눈이 박혀 있음'

def d06():  # 머리카락
    c = C(); rng = random.Random(6)
    c.ell(16, 8, 4.4, 5.6); tube(c, [(16, 13), (16, 22)], 3); tube(c, [(16, 20), (16, 36)], 7, 5)
    for sx, sy, ex in [(12, 3, 7), (14, 2, 11), (18, 2, 22), (20, 3, 26), (11, 6, 5), (21, 6, 28), (16, 2, 15)]:
        tube(c, [(sx, sy), (sx - 1, 18), (ex, 38), (ex + rng.randint(-2, 2), 55)], 2.6, 1.6, .2, sx)
    for x in (9, 12, 20, 23): c.line(x, 14, x + (x - 16) // 3, 50, 1, ch='k')
    eye(c, 17, 9, 1.9, 0, 0); c.put(15, 14, 'k')
    tube(c, [(11, 22), (5, 38), (7, 47)], 1.7, 1.1, .1, 3); tube(c, [(21, 22), (27, 36), (25, 47)], 1.7, 1.1, .1, 4)
    fingers(c, 7, 47, 95, 5, 12, 60, seed=13); fingers(c, 25, 47, 85, 5, 12, 60, seed=14)
    return c, '머리카락: 땅까지 늘어진 머리카락 사이로 눈 하나, 가는 팔이 빠져나옴'

def d07():  # 녹아내림
    c = C(); c.ell(16, 47, 12, 8); tube(c, [(16, 48), (16, 22)], 13, 5, .08)
    c.ell(14, 14, 3.8, 4.8); tube(c, [(15, 18), (16, 24)], 3)
    eye(c, 12, 13, 1.6, 0, 1); eye(c, 17, 16, 1.3, 0, 1)
    c.ell(14, 20, 1.4, 2.4, 'k'); jag(c, 13, 15, 18, 8)
    for x in (6, 10, 22, 26): c.line(x, 50, x, 55, 1.6, .8)
    tube(c, [(11, 24), (4, 38), (3, 47)], 2.6, 1.8, .15, 1); tube(c, [(21, 24), (28, 36), (28, 47)], 2.6, 1.8, .15, 2)
    fingers(c, 3, 47, 100, 5, 9, 60, seed=15); fingers(c, 28, 47, 80, 5, 9, 60, seed=16)
    return c, '녹아내림: 아래로 퍼지는 몸에 늘어진 얼굴, 벌어진 입이 세로로 늘어남'

def d08():  # 고릴라 자세
    c = C(); c.ell(16, 27, 10, 6); tube(c, [(16, 22), (16, 38)], 9, 4, .08)
    c.ell(16, 20, 3.8, 3.8)
    for x in (13, 14): c.put(x, 19, 'w')
    for x in (18, 19): c.put(x, 19, 'w')
    c.put(13, 18, 'k'); c.put(19, 18, 'k'); jag(c, 14, 18, 22, 4)
    tube(c, [(8, 26), (3, 40), (4, 54)], 4, 2, .1); tube(c, [(24, 26), (29, 40), (28, 54)], 4, 2, .1)
    tube(c, [(13, 38), (9, 46), (12, 55)], 3, 2); tube(c, [(19, 38), (23, 46), (20, 55)], 3, 2)
    fingers(c, 4, 54, 90, 5, 6, 90, seed=17); fingers(c, 28, 54, 90, 5, 6, 90, seed=18)
    return c, '짐승 자세: 등이 크게 굽고 머리가 어깨 사이에 박혀 위로 노려봄'

def d09():  # 웃는 얼굴만 사람
    c = C(); tube(c, [(16, 19), (15, 12), (13, 7)], 1.8, 1.8); tube(c, [(16, 19), (16, 36)], 4.4, 3, .06)
    tube(c, [(14, 20), (9, 38), (10, 47)], 1.6, 1.1, .12, 1); tube(c, [(18, 20), (23, 38), (22, 47)], 1.6, 1.1, .12, 2)
    c.line(14, 36, 13, 55, 1.6, 1.2); c.line(18, 36, 19, 55, 1.6, 1.2)
    c.ell(13, 6, 4.2, 5.2, 'w')
    for x in range(9, 18): c.put(x, 2, 's')
    c.ell(11, 5, 1.2, 1.8, 'k'); c.ell(16, 5, 1.2, 1.8, 'k'); c.put(11, 4, 'w'); c.put(16, 4, 'w')
    c.ell(13.5, 9, 3.2, 1.7, 'k')
    for x in range(11, 17): c.put(x, 8, 'w')
    fingers(c, 10, 47, 90, 5, 11, 60, seed=19); fingers(c, 22, 47, 90, 5, 11, 60, seed=20)
    return c, '웃는 얼굴: 몸은 가늘고 새까만데 얼굴만 창백한 사람, 눈이 크고 웃음이 굳어 있음'

def d10():  # 등 보이고 머리만 정면
    c = C(); tube(c, [(16, 17), (16, 36)], 10, 6, .05); c.ell(16, 9, 4, 5.2, 'w'); tube(c, [(16, 13), (16, 18)], 3)
    for y in range(3, 8):
        for x in range(11, 22):
            if c.g[y][x] == 'w': c.put(x, y, 's')
    eye(c, 14, 9, 1.5, 0, 0); eye(c, 19, 9, 1.5, 0, 0)
    for x in range(14, 19): c.put(x, 13, 'k')
    c.put(13, 12, 'k'); c.put(19, 12, 'k')
    for y in range(20, 34, 2): c.put(16, y, 'k')
    tube(c, [(11, 20), (7, 38), (8, 47)], 2.4, 1.4, .1, 1); tube(c, [(21, 20), (25, 38), (24, 47)], 2.4, 1.4, .1, 2); legs2(c)
    fingers(c, 8, 47, 90, 5, 8, 60, seed=21); fingers(c, 24, 47, 90, 5, 8, 60, seed=22)
    return c, '뒤돌아선 자: 등을 보이는데 머리만 정면으로 돌아 사람 얼굴이 이쪽을 봄'

def main():
    root = os.path.join(os.path.dirname(__file__), '..', 'art', 'variants')
    lines = ['# 검은 인간 불쾌 시안 (tools/gen_creep.py 가 생성함)', '']
    fns = [d01, d02, d03, d04, d05, d06, d07, d08, d09, d10]
    for i, fn in enumerate(fns):
        c, desc = fn()
        lines.append(f'[{"ab"[i // 5]}_{i + 1:02d}] {desc} | {i + 1}'); lines += c.finish(); lines.append('')
    open(os.path.join(root, 'creep_pixels.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
if __name__ == "__main__":
    main()
