#!/usr/bin/env python3
"""진짜 고양이(네발, 사람형 아님) 시안: 자세 4종 x 털색 4종. 이웃집 고양이: 목걸이에 빨간 목줄과 금색 방울(키우는 집이 있다는 단서).
눈은 둥근 점(안광/눈썹 없음), 입은 일자(ㅡ). 사용: python3 tools/gen_realcat.py && python3 tools/variants.py realcat"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import gen_shadow as G
from gen_shadow import C
from gen_creep import tube
from gen_helpers import tri
G.W, G.H = 36, 26

COATS = {   # 이름: (바탕, 줄무늬/무늬, 배/양말, 눈)
    'orange': ('o', 'a', 'q', 'k'), 'black': ('d', 's', 'd', 'y'), 'calico': ('q', 'o', 'q', 'k'), 'gray': ('l', 'm', 'w', 'k')}

def face(c, cx, cy, coat, spread=3.6, look=0):
    base, mark, belly, eye = COATS[coat]
    for sx in (-1, 1):
        ex = int(cx + sx * spread / 2 + (-.5 if sx < 0 else .5))
        c.put(ex, cy, eye); c.put(ex + 1, cy, eye); c.put(ex, cy + 1, eye); c.put(ex + 1, cy + 1, eye)
    c.put(cx, cy + 3, 'p'); c.put(cx - 1, cy + 3, 'p')
    for x in range(int(cx - 1.5), int(cx + 1.5) + 1): c.put(x, cy + 5, 'k')            # 입은 일자
    for sx in (-1, 1):
        for k, dy in enumerate((2, 4)): c.line(cx + sx * 4.5, cy + dy, cx + sx * 7.5, cy + dy + (k - .5), 1, ch='W')   # 수염

def collar(c, x, y, rx=4.4, ry=1.0):
    c.ell(x, y, rx, ry, 'R'); c.put(x, y + 1.4, 'y'); c.put(x + 1, y + 1.4, 'y'); c.put(x, y + 2.4, 'y')

def patches(c, coat, spots):
    base, mark, belly, eye = COATS[coat]
    if coat == 'calico':
        for (x, y, rx, ry, ch) in spots: c.ell(x, y, rx, ry, 'o' if ch == 0 else 'd')

def sit(coat):
    base, mark, belly, eye = COATS[coat]; c = C()
    tube(c, [(21, 25), (26, 22), (27, 17)], 2.8, 2.2, 0, 0, base)
    c.ell(16, 20, 6.6, 6.2, base); c.ell(16, 22, 3.6, 4.0, belly)
    c.ell(12.6, 24.6, 1.9, 1.5, belly if coat != 'black' else base); c.ell(19.4, 24.6, 1.9, 1.5, belly if coat != 'black' else base)
    c.ell(16, 10, 7.6, 6.4, base)
    tri(c, 10, 1, 5, 5, base); tri(c, 22, 1, 5, 5, base); c.put(10, 3, 'i'); c.put(22, 3, 'i')
    if coat in ('orange', 'gray'):
        for x, y0 in ((16, 4), (13.5, 5), (18.5, 5)): c.line(x, y0, x, y0 + 2, 1, ch=mark)
        for y in (17, 20): c.line(10, y, 12.5, y + .8, 1, ch=mark); c.line(22, y, 19.5, y + .8, 1, ch=mark)
    if coat == 'calico': patches(c, coat, [(11.5, 6, 3.2, 2.8, 0), (21.5, 8, 3, 3.4, 1), (20, 21, 3, 3.6, 0), (11, 19, 2.6, 2.6, 1)])
    face(c, 16, 9, coat); collar(c, 16, 15.7, 5.2, 1.0)
    return c

def stand(coat, walk=False):
    base, mark, belly, eye = COATS[coat]; c = C()
    far = mark if coat in ('orange', 'gray') else ('d' if coat == 'calico' else 's')
    tube(c, [(7, 10), (3, 8), (3, 2)] if not walk else [(7, 10), (3, 6), (6, 1)], 2.6, 2.0, 0, 0, base)
    c.line(9, 18, 9, 23, 2.2, ch=far); c.line(23, 18, 23, 23, 2.2, ch=far)                           # 안쪽 다리(그늘색)
    c.ell(15, 12, 9.4, 4.8, base); c.ell(15, 14.6, 6.4, 2.0, belly)
    sw = 3 if walk else 0
    c.line(11, 14, 11 - sw, 23, 2.4, ch=base); c.line(20, 14, 20 + sw, 22.5 - (2 if walk else 0), 2.4, ch=base)
    for x in (11 - sw, 20 + sw): c.ell(x, 23.2 - (1.6 if (walk and x > 15) else 0), 1.8, 1.0, belly if coat != 'black' else base)
    c.ell(25, 11, 4.0, 3.6, base); c.ell(28.4, 8.6, 5.4, 5.0, base)
    tri(c, 25, 0, 4, 4, base); tri(c, 31, 0, 4, 4, base)
    if coat in ('orange', 'gray'):
        for x in (9, 13, 17): c.line(x, 8, x + 1, 10.5, 1, ch=mark)
        c.line(29, 3, 29, 5, 1, ch=mark); c.line(27, 4, 27, 5.5, 1, ch=mark); c.line(31, 4, 31, 5.5, 1, ch=mark)
    if coat == 'calico': patches(c, coat, [(10, 10, 3.6, 2.6, 0), (17, 13, 3, 2.2, 1), (29, 5, 2.8, 2.4, 0)])
    face(c, 29, 8, coat, spread=3.4); collar(c, 24.4, 12, 1.1, 3.0)
    return c

def loaf(coat):
    base, mark, belly, eye = COATS[coat]; c = C()
    tube(c, [(26, 22), (21, 24.5), (13, 24.5)], 2.8, 2.2, 0, 0, base)
    c.ell(16, 18, 10.5, 5.8, base); c.ell(16, 20, 6.4, 3, belly)
    c.ell(16, 10, 7.4, 6, base); tri(c, 10, 1, 5, 5, base); tri(c, 22, 1, 5, 5, base)
    c.ell(11.6, 22.8, 2.4, 1.6, belly if coat != 'black' else base); c.ell(20.4, 22.8, 2.4, 1.6, belly if coat != 'black' else base)
    if coat in ('orange', 'gray'):
        for x in (16, 13.5, 18.5): c.line(x, 4, x, 6, 1, ch=mark)
        for x in (8, 13, 19, 24): c.line(x, 14, x + 1.4, 16.6, 1, ch=mark)
    if coat == 'calico': patches(c, coat, [(10.5, 6, 3.2, 2.8, 0), (22, 17, 4, 3, 1), (12, 17, 3, 2.4, 0)])
    face(c, 16, 9, coat); collar(c, 16, 15.2, 5.0, 1.0)
    return c

POSES = [('sit', lambda k: sit(k)), ('stand', lambda k: stand(k)), ('loaf', lambda k: loaf(k)), ('walk', lambda k: stand(k, True))]

def main():
    root = os.path.join(os.path.dirname(__file__), '..', 'art', 'variants')
    lines = ['# 진짜 고양이 시안 (tools/gen_realcat.py 가 생성함)', '']
    names = {'sit': '앉은 정면', 'stand': '서 있는 옆모습', 'loaf': '식빵 자세', 'walk': '걷는 옆모습'}
    cn = {'orange': '치즈 태비', 'black': '검은 고양이(노란 눈)', 'calico': '삼색', 'gray': '회색 태비'}
    for coat in COATS:
        for pose, fn in POSES:
            lines.append(f'[{coat}_{pose}] {cn[coat]} {names[pose]} | {pose}'); lines += fn(coat).finish(); lines.append('')
    open(os.path.join(root, 'realcat_pixels.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
if __name__ == '__main__': main()
