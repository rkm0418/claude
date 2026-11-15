#!/usr/bin/env python3
"""주인공(7살 아이) 시안 4종. 말랑한 스타일(둥근 점 눈, 안광/눈썹 없음, 입 일자). 학대는 직접 그리지 않고 소품으로만 간접 암시:
긴 소매, 밴드, 한 짝만 신은 슬리퍼, 눈을 가린 앞머리, 손을 덮은 소매. 24x38.
사용: python3 tools/gen_child.py && python3 tools/variants.py child"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import gen_shadow as G
from gen_shadow import C
from gen_creep import tube
G.W, G.H = 24, 38

SKIN = 'q'

def rect(c, x0, y0, x1, y1, ch):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1): c.put(x, y, ch)

def base(c, shirt, shorts, sleeves_over_hands=False, shade='w'):
    c.ell(12, 26.4, 6.4, 5.6, shirt)                                                                       # 몸통(둥글게)
    c.ell(9.2, 33, 3.0, 2.4, shorts); c.ell(14.8, 33, 3.0, 2.4, shorts)                                     # 반바지
    c.ell(9.2, 35.4, 1.7, 2.0, SKIN); c.ell(14.8, 35.4, 1.7, 2.0, SKIN)                                     # 다리
    for sgn in (-1, 1):                                                                                    # 긴 소매
        tube(c, [(12 + sgn * 5.6, 22.6), (12 + sgn * 7.4, 28.6)], 2.8, 2.8, 0, 0, shirt)
        if not sleeves_over_hands: c.ell(12 + sgn * 7.6, 30.6, 1.5, 1.6, SKIN)
    c.ell(12, 20.2, 2.6, 1.2, SKIN)                                                                        # 목

def head(c, blush=True):
    c.ell(3.4, 13.4, 1.5, 2.0, SKIN); c.ell(20.6, 13.4, 1.5, 2.0, SKIN)                                     # 귀
    c.ell(12, 12, 8.8, 8.2, SKIN)                                                                          # 둥근 머리
    if blush:
        for sx in (-1, 1): c.ell(12 + sx * 5.8, 15.6, 1.9, 1.2, 'i')

def face(c, eyes=(9, 15.2), dy=13.6, covered=None):
    for ex in eyes:
        if covered and abs(ex - covered) < 1: continue
        c.ell(ex, dy, 1.0, 1.1, 'k')
    c.put(12, 15.4, 'a')
    for x in range(11, 14): c.put(x, 17, 'k')

def hair_cap(c, col, front=6.2, top=7.4):
    c.ell(12, top, 9.2, front, col)
    c.ell(12, 14.4, 7.2, 5.4, SKIN)                                                                         # 얼굴 아래는 피부로 되돌림

def A():   # 단발 + 하늘색 긴소매 + 올리브 반바지 + 무릎 밴드 + 한 짝만 신은 슬리퍼
    c = C(); base(c, 'c', 'h'); head(c); hair_cap(c, 's', 6.8, 7.2)
    c.ell(12, 9.4, 8.6, 2.4, 's')
    face(c); c.line(8.4, 35.4, 10.4, 35.4, 1, ch='W'); c.put(9.4, 34.6, 'W'); c.put(9.4, 36.2, 'W')      # 무릎 밴드
    c.ell(9.2, 37.4, 2.4, .9, 'p'); c.ell(14.8, 37.2, 1.8, .8, SKIN)                                         # 한쪽만 슬리퍼
    for x in range(8, 11): c.put(x, 25.4, 'l')                                                             # 셔츠 주름
    return c.finish()

def B():   # 부스스한 갈색 머리 + 민트 후드티 + 볼 밴드
    c = C(); base(c, 't', 'd'); head(c); hair_cap(c, 'b', 6.4, 7.0)
    for x, y in ((8, 2), (12, 1.4), (16, 2)): c.ell(x, y + 2.2, 1.6, 2.2, 'b')
    c.line(12, 3, 14, 1, 1, ch='b')
    c.ell(12, 9.4, 8.4, 2.4, 'b'); face(c)
    rect(c, 5, 15, 7, 16, 'W'); c.put(6, 14, 'W'); c.put(6, 17, 'W')                                       # 볼 밴드
    c.ell(9.2, 37.2, 2.0, .9, 'k'); c.ell(14.8, 37.2, 2.0, .9, 'k')                                         # 운동화
    return c.finish()

def C_():  # 양 갈래 + 노란 긴소매 + 한쪽 내려간 양말
    c = C(); base(c, 'y', 'a'); head(c)
    c.ell(2.6, 10.6, 2.2, 3.2, 's'); c.ell(21.4, 10.6, 2.2, 3.2, 's')
    hair_cap(c, 's', 6.8, 7.2); c.ell(12, 9.4, 8.6, 2.4, 's'); face(c)
    c.put(3.4, 7.8, 'R'); c.put(20.6, 7.8, 'R')
    c.ell(9.2, 36.0, 1.9, 1.2, 'W'); c.ell(14.8, 35.2, 1.9, 2.2, 'W')                                       # 한쪽 양말만 위로, 한쪽은 내려감
    c.ell(9.2, 37.3, 2.0, .8, 'd'); c.ell(14.8, 37.3, 2.0, .8, 'd')
    return c.finish()

def D():   # 앞머리로 한쪽 눈을 가림 + 손을 덮은 큰 회색 후드 + 맨발
    c = C(); base(c, 'l', 'd', sleeves_over_hands=True); head(c); hair_cap(c, 's', 6.8, 7.2)
    c.ell(12, 9.4, 8.6, 2.4, 's'); c.ell(15.6, 12.0, 3.4, 2.6, 's')
    face(c, covered=15.2)
    for sgn in (-1, 1): c.ell(12 + sgn * 7.6, 30.4, 1.9, 1.7, 'l')                                          # 손을 덮은 소매
    c.ell(9.2, 37.2, 1.8, .9, SKIN); c.ell(14.8, 37.2, 1.8, .9, SKIN)
    return c.finish()

def main():
    root = os.path.join(os.path.dirname(__file__), '..', 'art', 'variants')
    notes = {'A': '단발, 하늘색 긴소매, 올리브 반바지, 무릎 밴드, 슬리퍼 한 짝만', 'B': '부스스한 갈색 머리, 민트 후드티, 볼 밴드', 'C': '양 갈래, 노란 긴소매, 한쪽만 내려간 양말', 'D': '앞머리로 가린 한쪽 눈, 손을 덮은 큰 회색 후드, 맨발'}
    lines = ['# 주인공 시안 (tools/gen_child.py 가 생성함)', '']
    for v, fn in zip('ABCD', (A, B, C_, D)): lines.append(f'[child_{v}] {notes[v]} | {v}'); lines += fn(); lines.append('')
    open(os.path.join(root, 'child_pixels.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
if __name__ == '__main__': main()
