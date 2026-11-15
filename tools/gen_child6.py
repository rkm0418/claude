#!/usr/bin/env python3
"""주인공 6차: 새 레퍼런스 머리(짙은 갈색의 둥글고 단순한 단발. 앞머리가 중앙 왼쪽에서 뾰족하게 내려오고 오른쪽 이마가 넓게 드러남. 귀 노출). 옷은 평상복, 얼굴 없음.
사용: python3 tools/gen_child6.py && python3 tools/variants.py child6   (24x38)"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import gen_child as K
from gen_shadow import C

PTS = [(4.6, 13.0), (10.4, 10.6), (12.4, 10.6), (16.4, 10.0), (19.5, 11.4), (19.6, 13.4)]   # 앞머리선의 큰 흐름(조절점)

def bump(x, c, w, h):
    return h * max(0.0, 1 - ((x - c) / w) ** 2) ** .5                                    # 가닥 끝을 둥글게(반타원)

def lim(x):
    if x < 4.6 or x > 19.6: return 13.4                                                  # 귀 위에서 멈추는 옆머리
    for (x0, y0), (x1, y1) in zip(PTS, PTS[1:]):
        if x0 <= x <= x1: base = y0 + (y1 - y0) * (x - x0) / (x1 - x0); break
    return base + bump(x, 11.0, 2.0, 2.2) + bump(x, 17.4, 2.0, 1.8)                      # 왼쪽 중앙과 오른쪽의 삐져나온 가닥(끝이 둥근 곡선)

def hair_ref2(c):
    c.ell(12, 8.6, 10.6, 8.2, 'b')
    for y in range(20):
        for x in range(24):
            if c.g[y][x] != 'b': continue
            if y > lim(x): c.g[y][x] = K.SKIN
            elif y > lim(x) - 1.0: c.g[y][x] = 'u' if (x + y) % 2 == 0 else 'n'                 # 끝이 피부색으로 번지는 2단계 그라데이션(밝은 갈색, 연한 갈색)
            elif y > lim(x) - 2.0 and (x + y) % 2 == 0: c.g[y][x] = 'n'
    c.line(5, 4.6, 6.6, 2.6, 1, ch='n'); c.put(6, 3, 'n'); c.put(7, 2, 'n')                                # 왼쪽 위의 옅은 윤기

def base_round(c, shirt, shorts, covered=False):
    """둥근 몸: 어깨는 둥근 덮개, 목과 어깨 연결은 넓은 타원으로 이음, 팔은 어깨에서 부드럽게 이어짐."""
    c.ell(9.2, 32.0, 3.0, 5.2, shorts); c.ell(14.8, 32.0, 3.0, 5.2, shorts)                              # 긴바지(발목까지)
    c.line(12, 28.6, 12, 36.4, 1, ch='k')                                                                   # 두 다리 사이 선
    for sgn in (-1, 1):
        K.tube(c, [(12 + sgn * 6.4, 24.4), (12 + sgn * 7.6, 28.2)], 3.0, 2.6, 0, 0, shirt)                    # 팔
        if not covered: c.ell(12 + sgn * 7.8, 29.6, 1.5, 1.6, K.SKIN)
        c.ell(12 + sgn * 5.6, 23.6, 2.7, 2.7, shirt)                                                      # 둥근 어깨
    c.ell(12, 25.2, 6.8, 4.8, shirt); c.ell(12, 22.6, 6.4, 2.8, shirt)                                       # 몸통과 어깨 윗선
    c.ell(12, 20.8, 3.4, 1.9, K.SKIN); c.ell(12, 21.8, 4.2, 1.4, shirt)                                       # 목과 둥근 목선

def build(shirt, shorts, hands_covered=False):
    c = C(); base_round(c, shirt, shorts, hands_covered); K.head(c, blush=False); hair_ref2(c); return c

def A():
    c = build('c', 'h'); c.ell(9.2, 37.4, 2.4, .9, 'p'); c.ell(14.8, 37.2, 1.8, .8, K.SKIN); return c.finish()          # 슬리퍼 한 짝만
def B():
    c = build('t', 'd'); c.ell(9.2, 37.2, 2.2, .9, 'k'); c.ell(14.8, 37.2, 2.2, .9, 'k'); return c.finish()
def Cc():
    c = build('y', 'a'); c.ell(9.2, 36.0, 2.0, 1.3, 'W'); c.ell(9.2, 37.3, 2.2, .8, 'd'); c.ell(14.8, 37.3, 2.2, .8, 'd'); return c.finish()   # 한쪽 바짓단만 접혀 양말이 보임
def D():
    c = build('l', 'd', True)
    for sgn in (-1, 1): c.ell(12 + sgn * 7.8, 29.6, 1.9, 1.7, 'l')
    c.ell(9.2, 37.2, 1.8, .9, K.SKIN); c.ell(14.8, 37.2, 1.8, .9, K.SKIN); return c.finish()

def main():
    root = os.path.join(os.path.dirname(__file__), '..', 'art', 'variants')
    notes = {'A': '하늘색 긴소매, 올리브 긴바지, 슬리퍼 한 짝', 'B': '민트 후드티, 짙은 긴바지, 운동화', 'C': '노란 긴소매, 주황 긴바지(한쪽 바짓단만 접힘)', 'D': '손을 덮은 큰 회색 후드, 짙은 긴바지, 맨발'}
    lines = ['# 주인공 6차 시안: 갈색 단순 단발(중앙 왼쪽 뾰족 앞머리) + 얼굴 없음 (tools/gen_child6.py 가 생성함)', '']
    for v, fn in zip('ABCD', (A, B, Cc, D)): lines.append(f'[child_{v}] {notes[v]} | {v}'); lines += fn(); lines.append('')
    open(os.path.join(root, 'child6_pixels.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
if __name__ == '__main__': main()
