#!/usr/bin/env python3
"""조력자 '수상해 보이는' 시안 12종: 귀여운 탈 모습은 유지하되 곁눈질, 반쯤 감은 눈, 눈 밑 그늘, 한쪽으로 올라간 입꼬리,
등 뒤로 숨긴 손과 삐져나온 물건, 얼굴을 가린 소지품 같은 '믿음이 안 가는' 단서를 넣었다.
사용: python3 tools/gen_suspicious.py && python3 tools/variants.py suspicious   (28x44)"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import gen_shadow as G
from gen_shadow import C
from gen_helpers import rect, tri
from gen_mascot import body, HY
G.W, G.H = 28, 44

def paste(dst, src, ox=0, oy=0):
    for y in range(44):
        for x in range(28):
            ch = src.g[y][x]; yy, xx = y + oy, x + ox
            if ch != '.' and 0 <= yy < 44 and 0 <= xx < 28: dst.g[yy][xx] = ch

def head_s(c, fur, muzzle, look=(1, 0), lid=.45, bags=True, smirk='R', brow=True, glare=False, shades=False, nose='k', ox=0, oy=0, ears=None):
    t = C()
    if ears: ears(t)
    t.ell(14, HY, 10, 8.5, fur); t.ell(14, HY + 3.5, 6.8, 4.6, muzzle)
    for sx in (-1, 1):
        ex = 14 + sx * 3.6
        t.ell(ex, HY - 2, 3.5, 4.3, 'k'); t.ell(ex, HY - 2, 2.7, 3.5, 'w')
        if glare: t.ell(ex, HY - 2, 2.7, 3.5, 'w'); t.put(ex - 1, HY - 3, 'q'); t.put(ex, HY - 3, 'q')
        else:
            for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)): t.put(ex + look[0] * 1.6 + dx - 0.5, HY - 1 + look[1] + dy - 1, 'k')
        if lid:                                                        # 반쯤 감은 눈꺼풀
            top = int(HY - 2 - 3.5 + lid * 7)
            for yy in range(int(HY - 2 - 4.3), top + 1):
                for xx in range(int(ex - 3.4), int(ex + 3.4) + 1):
                    if t.g[yy][xx] in 'w': t.g[yy][xx] = fur
            for xx in range(int(ex - 3), int(ex + 3) + 1): t.put(xx, top + 1, 'k')
        if bags:
            for xx in range(int(ex - 2), int(ex + 2) + 1): t.put(xx, HY + 3 - 1, 'a' if fur != 'n' else 'b')
        if brow: t.line(ex - 2.5, HY - 7 + (1.5 if sx > 0 else 0), ex + 2.5, HY - 6.5 - (1.5 if sx > 0 else -.5), 1, ch='k')
    if shades:
        for sx in (-1, 1): t.ell(14 + sx * 3.6, HY - 2, 3.8, 3, 'k'); t.put(14 + sx * 3.6 - 1, HY - 3, 'm')
        t.line(10, HY - 2, 18, HY - 2, 1, ch='k')
    t.ell(14, HY + 2, 2, 1.5, nose)
    y = HY + 5
    for x in range(10, 19): t.put(x, y + (0 if (x < 16 if smirk == 'R' else x > 12) else -1), 'k')          # 한쪽만 올라간 입꼬리
    t.put(17 if smirk == 'R' else 11, y + 1, 'w'); t.put(18 if smirk == 'R' else 10, y - 1, 'k')
    paste(c, t, ox, oy)

def arm_behind(c, cloth, side=1, item=None):
    sx = 20 if side == 1 else 5
    for y in range(26, 44):
        for x in range(sx - 1, sx + 4): c.g[y][x] = '.'
    ex = 18 if side == 1 else 8
    rect(c, ex, 27, ex + 1, 36, cloth)
    if item: item(c, 20 if side == 1 else 4, 33)

def cuffs(c, x, y):
    c.ell(x + 1, y + 2, 2.2, 2.2, 'm'); c.ell(x + 1, y + 2, 1.2, 1.2, '.'); c.ell(x + 4, y + 4, 2.2, 2.2, 'm'); c.ell(x + 4, y + 4, 1.2, 1.2, '.'); c.line(x + 2, y + 3, x + 3, y + 4, 1, ch='m')
def keys(c, x, y):
    c.ell(x + 1, y + 2, 1.8, 1.8, 'y'); c.ell(x + 1, y + 2, .8, .8, '.'); c.line(x + 1, y + 3, x + 1, y + 8, 1, ch='y'); c.line(x + 1, y + 7, x + 3, y + 7, 1, ch='y')
def rope(c, x, y):
    for i in range(5): c.put(x + i % 2, y + i * 1.6, 'n'); c.put(x + 1 + i % 2, y + i * 1.6, 'u')

def rabbit(v):
    c = C(); ears = lambda t: [(t.ell(sx, 3, 2.3, 6, 'w'), t.ell(sx, 3.5, 1.2, 4.6, 'i')) for sx in (9, 19)]
    body(c, 'j', 'd'); [c.put(13 + k, y, 'y') for y in (28, 31, 34) for k in (0, 1)]
    if v == 'A':                                                       # 모자를 깊이 눌러 쓰고 눈에 그늘, 허리의 수갑, 손 하나 등 뒤
        head_s(c, 'w', 'q', look=(1, 0), lid=.6, ears=ears); arm_behind(c, 'j', 1, cuffs)
        rect(c, 7, 6, 20, 11, 'j'); rect(c, 6, 12, 21, 12, 'k'); rect(c, 7, 13, 20, 13, 's'); c.put(14, 8, 'y')
        rect(c, 10, 33, 12, 34, 'm')
    if v == 'B':                                                       # 곁눈질 + 수첩으로 입을 반쯤 가림
        head_s(c, 'w', 'q', look=(-1, 0), lid=.35, ears=ears)
        rect(c, 6, 6, 17, 8, 'j'); rect(c, 5, 9, 18, 9, 'k'); c.put(11, 7, 'y'); rect(c, 12, 22, 22, 29, 'q'); c.line(13, 24, 20, 24, 1, ch='k'); c.line(13, 26, 18, 26, 1, ch='k')
    if v == 'C':                                                       # 고개를 어깨 너머로 돌려 곁눈질 + 아래서 비추는 손전등 불빛
        head_s(c, 'w', 'q', look=(1, 0), lid=.5, ears=ears, ox=2, oy=1)
        rect(c, 9, 26, 18, 36, 'o'); rect(c, 9, 30, 18, 30, 'q'); rect(c, 9, 34, 18, 34, 'q')
        for x in range(10, 21): c.put(x, 23, 'y') if c.g[23][x] in 'wq' else None
        for y in range(18, 24):
            for x in range(10, 21):
                if c.g[y][x] in 'wq': c.g[y][x] = 'y' if (x + y) % 2 else 'q'
        rect(c, 22, 33, 23, 40, 'k'); c.put(22, 32, 'y')
        rect(c, 6, 5, 21, 8, 'j'); rect(c, 5, 9, 22, 9, 'k')
    if v == 'D':                                                       # 선글라스 + 세운 옷깃 + 입에 댄 무전기
        head_s(c, 'w', 'q', shades=True, lid=0, bags=False, brow=False, ears=ears)
        rect(c, 7, 24, 11, 29, 'j'); rect(c, 17, 24, 21, 29, 'j'); rect(c, 12, 17, 15, 20, 'k')
        rect(c, 14, 20, 18, 23, 'k'); c.line(17, 20, 19, 16, 1, ch='k'); rect(c, 6, 5, 21, 9, 'j'); rect(c, 6, 8, 21, 8, 'y'); rect(c, 5, 10, 22, 10, 'k')
    return c

def cat(v):
    c = C(); ears = lambda t: (tri(t, 8, 3, 7, 8, 'o'), tri(t, 20, 3, 7, 8, 'o'))
    cloth = {'A': 'h', 'B': 'i', 'C': 'a', 'D': 'h'}[v]; body(c, cloth, {'A': 'q', 'B': 'i', 'C': 'd', 'D': 'b'}[v])
    if v == 'A':                                                       # 가늘게 뜬 눈, 등 뒤로 숨긴 열쇠 꾸러미, 앞치마 주머니의 봉투
        head_s(c, 'o', 'q', look=(1, 0), lid=.55, nose='p', ears=ears); rect(c, 10, 28, 17, 37, 'q')
        rect(c, 11, 31, 16, 34, 'w'); c.line(11, 31, 13, 33, 1, ch='k'); c.line(16, 31, 14, 33, 1, ch='k'); arm_behind(c, cloth, 1, keys)
    if v == 'B':                                                       # 스카프로 입을 가리고 눈만 곁눈질
        head_s(c, 'o', 'q', look=(-1, 0), lid=.45, nose='p', smirk='L', ears=ears)
        for x in range(8, 21):
            for y in range(HY + 3, HY + 9): c.g[y][x] = 'p' if (x + y) % 3 else 'i'
        for x in (8, 11, 14, 17, 20): c.ell(x, 7, 1.6, 1.6, 'a')
    if v == 'C':                                                       # 천 덮은 바구니 밖으로 삐져나온 밧줄, 곁눈질
        head_s(c, 'o', 'q', look=(1, 1), lid=.5, nose='p', ears=ears); rect(c, 21, 33, 27, 40, 'n'); rect(c, 21, 33, 27, 34, 'q'); rope(c, 25, 28)
        rect(c, 6, 26, 21, 30, 'a')
    if v == 'D':                                                       # 렌즈에 빛이 번쩍여 눈이 안 보이는 안경 + 귀에 전화기
        head_s(c, 'o', 'q', glare=True, lid=0, bags=False, nose='p', smirk='L', ears=ears)
        for ex in (10.4, 17.6): c.ell(ex, HY - 2, 4, 4.6, 'k'); c.ell(ex, HY - 2, 3.2, 3.8, 'q'); c.put(ex - 1, HY - 3, 'w'); c.put(ex, HY - 3, 'w')
        c.line(14, HY - 2, 14, HY - 2, 1, ch='k'); rect(c, 1, HY - 3, 3, HY + 3, 'k'); rect(c, 2, HY - 2, 2, HY + 2, 'm')
    return c

def bear(v):
    c = C()
    for sx in (6, 22): c.ell(sx, 7, 3.2, 3.2, 'n'); c.ell(sx, 7, 1.6, 1.6, 'u')
    cloth = {'A': 'h', 'B': 'd', 'C': 'j', 'D': 'q'}[v]; body(c, cloth, {'A': 'b', 'B': 'd', 'C': 'd', 'D': 'b'}[v])
    if v == 'A':                                                       # 렌즈에 빛이 번쩍이는 안경 + 수첩에 무언가 적음
        head_s(c, 'n', 'u', glare=True, lid=0, bags=False, ears=None)
        for ex in (10.4, 17.6): c.ell(ex, HY - 2, 4.2, 5, 'k'); c.ell(ex, HY - 2, 3.4, 4.2, 'q'); c.put(ex - 1, HY - 3, 'w'); c.put(ex, HY - 3, 'w')
        rect(c, 11, 26, 16, 36, 'q'); rect(c, 21, 29, 26, 36, 'q'); c.line(22, 31, 25, 31, 1, ch='k'); c.line(22, 33, 24, 33, 1, ch='k')
    if v == 'B':                                                       # 입술에 손가락을 댄 "쉿" + 곁눈질
        head_s(c, 'n', 'u', look=(-1, 0), lid=.4, smirk='L')
        rect(c, 11, 26, 16, 37, 'q'); rect(c, 13, 27, 14, 33, 'a'); rect(c, 12, 21, 15, 25, 'w'); c.line(14, 21, 14, 27, 1, ch='w')
    if v == 'C':                                                       # 서류판으로 얼굴 아래를 가리고, 명찰은 뒤집혀 있고, 곁눈질
        head_s(c, 'n', 'u', look=(1, 0), lid=.5)
        rect(c, 9, 24, 19, 36, 'u'); rect(c, 12, 22, 16, 24, 'k'); rect(c, 10, 27, 18, 27, 'k'); c.line(10, 29, 17, 29, 1, ch='k'); c.line(10, 31, 14, 31, 1, ch='k')
        c.line(11, 25, 14, 34, 1, ch='y')
    if v == 'D':                                                       # 목도리로 입을 가리고 눈을 가늘게 뜸 + 등 뒤로 숨긴 한 손
        head_s(c, 'n', 'u', look=(1, 1), lid=.6, smirk='L')
        for x in range(8, 21):
            for y in range(HY + 3, HY + 11): c.g[y][x] = 'a' if (x // 2 + y) % 3 else 'r'
        rect(c, 9, 25, 18, 28, 'a'); arm_behind(c, 'q', 1, lambda cc, x, y: cc.ell(x + 1, y + 1, 1.8, 2.4, 'w'))
        rect(c, 22, 34, 26, 38, 't') if False else None
    return c

def main():
    root = os.path.join(os.path.dirname(__file__), '..', 'art', 'variants')
    notes = {'rabbit': {'A': '모자 그늘의 눈, 등 뒤로 숨긴 손, 허리의 수갑', 'B': '곁눈질, 수첩으로 입을 가림', 'C': '어깨 너머 곁눈질, 아래서 비추는 불빛', 'D': '선글라스, 세운 옷깃, 입에 댄 무전기'},
             'cat': {'A': '가늘게 뜬 눈, 등 뒤의 열쇠 꾸러미, 앞치마 주머니의 봉투', 'B': '스카프로 입을 가리고 눈만 곁눈질', 'C': '바구니 밖으로 삐져나온 밧줄, 곁눈질', 'D': '번쩍이는 안경, 귀에 댄 전화기'},
             'bear': {'A': '번쩍이는 안경, 수첩에 무언가 적음', 'B': '"쉿" 손짓, 곁눈질', 'C': '서류판으로 얼굴 아래를 가림, 곁눈질', 'D': '목도리로 입을 가림, 등 뒤로 숨긴 한 손'}}
    lines = ['# 조력자 수상한 시안 (tools/gen_suspicious.py 가 생성함)', '']
    for animal, fn in (('rabbit', rabbit), ('cat', cat), ('bear', bear)):
        for v in 'ABCD':
            lines.append(f'[{animal}_{v}] {notes[animal][v]} | {v}'); lines += fn(v).finish(); lines.append('')
    open(os.path.join(root, 'suspicious_pixels.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
if __name__ == '__main__': main()
