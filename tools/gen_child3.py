#!/usr/bin/env python3
"""주인공 3차: 레퍼런스 머리 스타일(갈색 단발, 가르마에서 비스듬히 쓸어 내린 앞머리, 귀는 드러남) + 얼굴 없음. 옷은 1차 시안과 같다.
사용: python3 tools/gen_child3.py && python3 tools/variants.py child3"""
import os, sys, random
sys.path.insert(0, os.path.dirname(__file__))
import gen_child as K
from gen_shadow import C

def hair_ref(c):
    """머리: 위쪽이 둥글고 풍성, 앞머리가 왼쪽 위에서 오른쪽 아래로 비스듬히 내려오고 끝이 뾰족, 옆머리는 귀 위에서 멈춤."""
    c.ell(12, 8.2, 10.4, 7.8, 'n')
    for y in range(18):                                                  # 앞머리 경계 아래는 피부로 되돌린다
        for x in range(24):
            if c.g[y][x] != 'n': continue
            if x < 4.6: lim = 13.2                                       # 왼쪽 옆머리(귀 위에서 끝)
            elif x > 19.6: lim = 12.8                                    # 오른쪽 옆머리
            else: lim = 9.0 + (x - 5.0) * 0.30                           # 가르마 쪽(왼쪽)이 높고 오른쪽으로 갈수록 내려오는 앞머리선
            if y > lim: c.g[y][x] = K.SKIN
    c.put(16, 13, 'n'); c.put(17, 13, 'n'); c.put(17, 14, 'n'); c.put(16, 12, 'n')            # 앞머리 끝의 뾰족한 가닥
    for x0, y0, x1, y1 in ((9, 2.6, 6.4, 8.4), (12.4, 2.0, 10.0, 7.6), (15.4, 2.8, 14.0, 8.0), (4.5, 8.6, 4.0, 12.2)): c.line(x0, y0, x1, y1, 1, ch='b')   # 결 따라 어두운 머리카락 선
    c.line(13, 8.6, 18.4, 11.4, 1, ch='b')                                                                                  # 앞머리 아래쪽 그늘선
    for x, y in ((4, 6), (5, 5), (3, 8)): c.put(x, y, 'w')                                                                  # 왼쪽 윤기

def build(shirt, shorts, extra):
    c = C(); K.base(c, shirt, shorts, sleeves_over_hands=(extra == 'D')); K.head(c, blush=False); hair_ref(c)
    return c

def A():
    c = build('c', 'h', 'A'); c.line(8.4, 35.4, 10.4, 35.4, 1, ch='W'); c.put(9.4, 34.6, 'W'); c.put(9.4, 36.2, 'W')
    c.ell(9.2, 37.4, 2.4, .9, 'p'); c.ell(14.8, 37.2, 1.8, .8, K.SKIN); return c.finish()
def B():
    c = build('t', 'd', 'B'); c.ell(9.2, 37.2, 2.0, .9, 'k'); c.ell(14.8, 37.2, 2.0, .9, 'k'); return c.finish()
def Cc():
    c = build('y', 'a', 'C'); c.ell(9.2, 36.0, 1.9, 1.2, 'W'); c.ell(14.8, 35.2, 1.9, 2.2, 'W'); c.ell(9.2, 37.3, 2.0, .8, 'd'); c.ell(14.8, 37.3, 2.0, .8, 'd'); return c.finish()
def D():
    c = build('l', 'd', 'D')
    for sgn in (-1, 1): c.ell(12 + sgn * 7.6, 30.4, 1.9, 1.7, 'l')
    c.ell(9.2, 37.2, 1.8, .9, K.SKIN); c.ell(14.8, 37.2, 1.8, .9, K.SKIN); return c.finish()

def main():
    root = os.path.join(os.path.dirname(__file__), '..', 'art', 'variants')
    notes = {'A': '하늘색 긴소매, 올리브 반바지, 무릎 밴드, 슬리퍼 한 짝', 'B': '민트 후드티, 검은 반바지, 운동화', 'C': '노란 긴소매, 한쪽만 내려간 양말', 'D': '손을 덮은 큰 회색 후드, 맨발'}
    lines = ['# 주인공 3차 시안: 레퍼런스 머리 + 얼굴 없음 (tools/gen_child3.py 가 생성함)', '']
    for v, fn in zip('ABCD', (A, B, Cc, D)): lines.append(f'[child_{v}] {notes[v]} | {v}'); lines += fn(); lines.append('')
    open(os.path.join(root, 'child3_pixels.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
if __name__ == '__main__': main()
