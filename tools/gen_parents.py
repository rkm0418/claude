#!/usr/bin/env python3
"""부모(검은 인간) 시안 4차: 평범한 사람의 몸과 옷, 얼굴만 잘못된 형태. (사용자 레퍼런스: 점토로 뭉개진 얼굴, 무표정 가면)
사용: python3 tools/gen_parents.py && python3 tools/variants.py parents
32x64 초상 크기. 게임 안에서는 아이 키(약 19px)의 1.7배인 32px 정도로 줄여 쓰거나, 컷신에서 이 크기로 쓴다."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import gen_shadow as G
G.W, G.H = 32, 64
from gen_shadow import C
from gen_creep import tube

def rect(c, x0, y0, x1, y1, ch):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1): c.put(x, y, ch)

def body_dad(c):
    rect(c, 11, 44, 15, 61, 'd'); rect(c, 17, 44, 21, 61, 'd'); rect(c, 10, 62, 15, 63, 'k'); rect(c, 17, 62, 22, 63, 'k')
    rect(c, 9, 23, 23, 45, 'j'); rect(c, 10, 22, 22, 22, 'j'); rect(c, 14, 22, 18, 41, 'q')
    c.put(13, 23, 'k'); c.put(19, 23, 'k'); c.put(14, 24, 'k'); c.put(18, 24, 'k')
    for y in (30, 36): c.put(13, y, 'y'); c.put(19, y, 'y')
    rect(c, 14, 19, 18, 22, 'w')
    for sx in (5, 23): rect(c, sx, 24, sx + 4, 46, 'j'); rect(c, sx, 47, sx + 4, 52, 'w'); c.put(sx + 1, 52, 'k'); c.put(sx + 3, 52, 'k')

def body_mom(c):
    for y in range(42, 59):
        w = 6 + (y - 42) * .3
        for x in range(int(16 - w), int(16 + w) + 1): c.put(x, y, 'a')
    rect(c, 12, 58, 14, 61, 'w'); rect(c, 18, 58, 20, 61, 'w'); rect(c, 11, 62, 15, 63, 'k'); rect(c, 17, 62, 21, 63, 'k')
    rect(c, 10, 23, 22, 42, 'q'); rect(c, 11, 22, 21, 22, 'q'); rect(c, 9, 23, 12, 43, 'h'); rect(c, 20, 23, 23, 43, 'h')
    rect(c, 14, 19, 18, 22, 'w')
    for sx in (5, 23): rect(c, sx, 24, sx + 4, 46, 'h'); rect(c, sx, 47, sx + 4, 52, 'w'); c.put(sx + 1, 52, 'k'); c.put(sx + 3, 52, 'k')

def head(c, mom=False, hair_front=False):
    c.ell(16, 10, 7.5, 9.5, 's')
    if mom:
        tube(c, [(22, 6), (27, 16), (26, 30)], 3, 2, ch='s'); rect(c, 21, 6, 23, 8, 'r')
    if not hair_front: c.ell(16, 13.5, 5.8, 7.6, 'w')
    else: c.ell(16, 18, 3, 2, 'w')

def f1(c):  # 무표정 가면: 먼 눈, 인형 같은 볼, 작은 입술
    for x in (12, 13, 19, 20): c.put(x, 11, 'k')
    c.put(16, 13, 'l'); c.put(16, 14, 'l')
    for x in (14, 15, 16, 17, 18): c.put(x, 17, 'r')
    c.put(13, 16, 'r'); c.put(19, 16, 'r')
    for p in ((12, 14), (20, 14)): c.put(*p, 'i'); c.put(p[0] + 1, p[1], 'i')

def f2(c):  # 점토로 뭉개진 얼굴
    c.ell(16, 13.5, 5.8, 7.6, 'i')
    for x, y in [(12, 8), (13, 8), (14, 9), (19, 8), (20, 9), (11, 12), (12, 13), (20, 14), (21, 13), (13, 18), (14, 19), (18, 19)]: c.put(x, y, 'a')
    for x, y in [(14, 12), (15, 13), (16, 14), (17, 15), (18, 16)]: c.put(x, y, 'l')
    c.put(18, 9, 'w'); c.put(19, 9, 'w'); c.put(13, 15, 'w'); c.put(14, 15, 'k'); c.put(19, 9, 'k')
    for x, y in [(12, 17), (13, 17), (14, 18), (15, 18)]: c.put(x, y, 'k')

def f3(c):  # 눈 없음, 감은 선, 얼굴 가로 전체로 번진 입술
    for x in (12, 13, 14, 18, 19, 20): c.put(x, 11, 'k')
    for x in range(11, 22): c.put(x, 16 - (1 if x in (11, 21) else 0), 'r')
    for x in range(12, 21): c.put(x, 17, 'r')
    for x in range(13, 20): c.put(x, 17, 'w' if x % 2 else 'r')

def f4(c):  # 너무 큰 눈이 얼굴 가장자리에, 아주 작은 입
    for cx in (12, 20):
        rect(c, cx - 1, 10, cx + 1, 13, 'k'); c.put(cx, 10, 'w')
    c.put(16, 17, 'r'); c.put(15, 17, 'r')

def f5(c):  # 머리카락이 얼굴을 덮고 아래쪽에 웃는 입만
    for x in range(14, 19): c.put(x, 17, 'r')
    c.put(13, 16, 'r'); c.put(19, 16, 'r')
    for x in (15, 17): c.put(x, 18, 'w')

def f6(c):  # 눈 네 개, 입 둘
    for x in (12, 13, 19, 20): c.put(x, 9, 'k'); c.put(x, 12, 'k')
    c.put(16, 14, 'l')
    for x in range(14, 19): c.put(x, 16, 'r'); c.put(x, 19, 'r')

def f7(c):  # 가면 이음선: 오른쪽 절반이 어긋남
    f1(c)
    for y in range(19, 4, -1):
        for x in range(21, 15, -1):
            if c.g[y][x] != '.' and y + 2 < 28: pass
    cols = {x: [c.g[y][x] for y in range(8, 22)] for x in range(16, 23)}
    for x, col in cols.items():
        for i, ch in enumerate(col):
            if 8 + i + 2 < 22 and ch != '.': c.put(x, 10 + i, ch)
    for y in range(7, 21): c.put(16, y, 'k')

def f8(c):  # 아래로 흘러내린 눈과 입
    for x in (13, 19):
        for y in range(11, 18): c.put(x, y, 'k')
    for y in range(15, 21): c.put(16, y, 'k'); c.put(15, y, 'r' if y % 2 else 'k'); c.put(17, y, 'r' if y % 2 else 'k')
    for x, y in [(11, 10), (21, 12), (12, 14), (20, 16)]: c.put(x, y, 'l')

FACES = [('무표정 가면: 눈이 멀고 볼이 인형 같음, 입술만 칠해짐', f1, 0, 0), ('점토 얼굴: 이목구비가 뭉개져 위치가 어긋남', f2, 1, 0),
         ('번진 입술: 눈은 감은 선, 입이 얼굴 가로 전체로 퍼짐', f3, 0, 0), ('큰 눈: 눈이 얼굴 끝에 크게 박히고 입은 점 하나', f4, 1, 0),
         ('머리카락 얼굴: 얼굴이 머리카락에 덮이고 입만 웃음', f5, 0, 1), ('눈 넷 입 둘: 얼굴 요소가 겹쳐 있음', f6, 1, 0),
         ('어긋난 가면: 이음선이 있고 오른쪽 절반이 내려앉음', f7, 0, 0), ('흘러내림: 눈과 입이 세로로 녹아내림', f8, 1, 0)]

def main():
    root = os.path.join(os.path.dirname(__file__), '..', 'art', 'variants')
    lines = ['# 부모 시안 (tools/gen_parents.py 가 생성함. 몸: 아빠=카디건+셔츠, 엄마=블라우스+치마)', '']
    for i, (desc, f, mom, hf) in enumerate(FACES):
        c = C(); (body_mom if mom else body_dad)(c); head(c, bool(mom), bool(hf)); f(c)
        lines.append(f'[{"ab"[i // 4]}_{i + 1:02d}] {desc} | {i + 1}'); lines += c.finish(); lines.append('')
    open(os.path.join(root, 'parents_pixels.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
if __name__ == '__main__': main()
