#!/usr/bin/env python3
"""주인공 2차: 얼굴 없음(눈, 코, 입, 볼터치 없음), 숱이 많고 수북한 머리. 옷과 소품은 1차 시안(gen_child.py)과 같다.
사용: python3 tools/gen_child2.py && python3 tools/variants.py child2"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import gen_child as K
from gen_shadow import C
from gen_creep import tube

def hair_volume(c, col, spikes=(), side=0, bang=2.8):
    c.ell(12, 8.0, 11.0, 7.8, col)                                       # 수북하게 머리 폭보다 넓은 숱
    for x, y, rx, ry in spikes: c.ell(x, y, rx, ry, col)
    if side:                                                             # 옆머리가 귀와 어깨 쪽으로 흘러내림
        c.ell(3.0, 13.5, 2.4, side, col); c.ell(21.0, 13.5, 2.4, side, col)
    c.ell(12, 15.4, 6.6, 4.8, K.SKIN)                                   # 얼굴(비어 있음)은 피부로 복원
    c.ell(12, 10.6, 9.8, bang, col)                                      # 앞머리

def A():
    c = C(); K.base(c, 'c', 'h'); K.head(c, blush=False); hair_volume(c, 's')
    c.line(8.4, 35.4, 10.4, 35.4, 1, ch='W'); c.put(9.4, 34.6, 'W'); c.put(9.4, 36.2, 'W')
    c.ell(9.2, 37.4, 2.4, .9, 'p'); c.ell(14.8, 37.2, 1.8, .8, K.SKIN)
    return c.finish()

def B():
    c = C(); K.base(c, 't', 'd'); K.head(c, blush=False)
    hair_volume(c, 'b', spikes=((6, 2.4, 2.4, 2.6), (12, 1.2, 2.6, 2.6), (18, 2.4, 2.4, 2.6)))
    c.line(12, 2.6, 15, 0.6, 1, ch='b'); c.ell(9.2, 37.2, 2.0, .9, 'k'); c.ell(14.8, 37.2, 2.0, .9, 'k')
    return c.finish()

def Cc():
    c = C(); K.base(c, 'y', 'a'); K.head(c, blush=False)
    c.ell(2.4, 11.0, 2.6, 3.8, 's'); c.ell(21.6, 11.0, 2.6, 3.8, 's')   # 양 갈래 뭉치
    hair_volume(c, 's'); c.put(3.0, 7.6, 'R'); c.put(21.0, 7.6, 'R')
    c.ell(9.2, 36.0, 1.9, 1.2, 'W'); c.ell(14.8, 35.2, 1.9, 2.2, 'W'); c.ell(9.2, 37.3, 2.0, .8, 'd'); c.ell(14.8, 37.3, 2.0, .8, 'd')
    return c.finish()

def D():
    c = C(); K.base(c, 'l', 'd', sleeves_over_hands=True); K.head(c, blush=False)
    hair_volume(c, 's', side=5.2, bang=3.4)
    for sgn in (-1, 1): c.ell(12 + sgn * 7.6, 30.4, 1.9, 1.7, 'l')
    c.ell(9.2, 37.2, 1.8, .9, K.SKIN); c.ell(14.8, 37.2, 1.8, .9, K.SKIN)
    return c.finish()

def main():
    root = os.path.join(os.path.dirname(__file__), '..', 'art', 'variants')
    notes = {'A': '수북한 단발, 하늘색 긴소매, 무릎 밴드, 슬리퍼 한 짝', 'B': '수북하고 부스스한 갈색 머리, 민트 후드티', 'C': '수북한 양 갈래, 노란 긴소매, 한쪽만 내려간 양말', 'D': '옆머리가 흘러내린 긴 숱, 손을 덮은 회색 후드, 맨발'}
    lines = ['# 주인공 2차 시안: 얼굴 없음 + 수북한 머리 (tools/gen_child2.py 가 생성함)', '']
    for v, fn in zip('ABCD', (A, B, Cc, D)): lines.append(f'[child_{v}] {notes[v]} | {v}'); lines += fn(); lines.append('')
    open(os.path.join(root, 'child2_pixels.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
if __name__ == '__main__': main()
