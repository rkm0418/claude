#!/usr/bin/env python3
"""주인공 6차: 새 레퍼런스 머리(짙은 갈색의 둥글고 단순한 단발. 앞머리가 중앙 왼쪽에서 뾰족하게 내려오고 오른쪽 이마가 넓게 드러남. 귀 노출). 옷은 평상복, 얼굴 없음.
사용: python3 tools/gen_child6.py && python3 tools/variants.py child6   (24x38)"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import gen_child as K
from gen_shadow import C

def lim(x):
    if x < 4.6 or x > 19.5: return 13.4                                  # 귀 위에서 멈추는 옆머리
    if x < 10.4: return 13.0 - (x - 4.6) * 0.42                         # 왼쪽: 앞머리선이 완만히 올라감
    if x < 12.4: return 12.8                                             # 중앙 왼쪽에서 뾰족하게 내려오는 가닥
    if x < 16.2: return 11.2 - (x - 12.4) * 0.75                         # 오른쪽: 이마가 넓게 드러나도록 높이 올라감
    if x < 18.4: return 12.2                                             # 오른쪽에도 삐져나온 뾰족한 가닥
    return 9.4 + (x - 18.4) * 0.8                                        # 다시 귀 쪽으로 내려감

def hair_ref2(c):
    c.ell(12, 8.6, 10.6, 8.2, 'b')
    for y in range(20):
        for x in range(24):
            if c.g[y][x] == 'b' and y > lim(x): c.g[y][x] = K.SKIN
    c.line(5, 4.6, 6.6, 2.6, 1, ch='n'); c.put(6, 3, 'n'); c.put(7, 2, 'n')                                # 왼쪽 위의 옅은 윤기

def build(shirt, shorts, hands_covered=False):
    c = C(); K.base(c, shirt, shorts, sleeves_over_hands=hands_covered); K.head(c, blush=False); hair_ref2(c); return c

def A():
    c = build('c', 'h'); c.line(8.4, 35.4, 10.4, 35.4, 1, ch='W'); c.put(9.4, 34.6, 'W'); c.put(9.4, 36.2, 'W')
    c.ell(9.2, 37.4, 2.4, .9, 'p'); c.ell(14.8, 37.2, 1.8, .8, K.SKIN); return c.finish()
def B():
    c = build('t', 'd'); c.ell(9.2, 37.2, 2.0, .9, 'k'); c.ell(14.8, 37.2, 2.0, .9, 'k'); return c.finish()
def Cc():
    c = build('y', 'a'); c.ell(9.2, 36.0, 1.9, 1.2, 'W'); c.ell(14.8, 35.2, 1.9, 2.2, 'W'); c.ell(9.2, 37.3, 2.0, .8, 'd'); c.ell(14.8, 37.3, 2.0, .8, 'd'); return c.finish()
def D():
    c = build('l', 'd', True)
    for sgn in (-1, 1): c.ell(12 + sgn * 7.6, 30.4, 1.9, 1.7, 'l')
    c.ell(9.2, 37.2, 1.8, .9, K.SKIN); c.ell(14.8, 37.2, 1.8, .9, K.SKIN); return c.finish()

def main():
    root = os.path.join(os.path.dirname(__file__), '..', 'art', 'variants')
    notes = {'A': '하늘색 긴소매, 올리브 반바지, 무릎 밴드, 슬리퍼 한 짝', 'B': '민트 후드티, 검은 반바지, 운동화', 'C': '노란 긴소매, 한쪽만 내려간 양말', 'D': '손을 덮은 큰 회색 후드, 맨발'}
    lines = ['# 주인공 6차 시안: 갈색 단순 단발(중앙 왼쪽 뾰족 앞머리) + 얼굴 없음 (tools/gen_child6.py 가 생성함)', '']
    for v, fn in zip('ABCD', (A, B, Cc, D)): lines.append(f'[child_{v}] {notes[v]} | {v}'); lines += fn(); lines.append('')
    open(os.path.join(root, 'child6_pixels.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
if __name__ == '__main__': main()
