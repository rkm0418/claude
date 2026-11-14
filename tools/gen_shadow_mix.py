#!/usr/bin/env python3
"""검은 인간 조합 생성기: 머리 x 몸통 x 팔 x 다리를 조합해 시안을 만든다.
사용: python3 tools/gen_shadow_mix.py && python3 tools/variants.py shadow3 (shadow4)
새 조합은 아래 COMBOS 에 (머리, 몸통, 팔, 다리) 한 줄을 추가하면 된다."""
import os, sys, math
sys.path.insert(0, os.path.dirname(__file__))
from gen_shadow import C, hand, teeth

HN = dict(oval='얼굴 없는 긴 달걀 머리', long='위로 길게 늘어난 머리', round_big='몸에 비해 거대한 머리', eye1='외눈',
          teeth='이빨 얼굴', grin_wide='찢어진 큰 웃음', antler='가지 뿔', drip='흘러내리는 얼굴', tiny='아주 작은 머리',
          two='머리 둘', slit='가로 눈 하나', mouth_vert='세로로 벌린 입', cracked='금 간 머리', hood='뾰족한 두건 머리',
          veil='길게 늘어진 머리카락', eyes5='눈 다섯 개')
TN = dict(thin='가는 몸', broad='넓은 어깨', bloat='부푼 몸', bell='종 모양 치마 하체', ribs='드러난 갈비뼈', bmouth='배의 입')
AN = dict(long='긴 팔', drag='바닥에 끌리는 팔', four='팔 넷', six='팔 여섯', raised='치켜든 팔', spindly='실처럼 가는 팔', none='짧은 팔')
LN = dict(two='두 다리', stilt='죽마 같은 다리', bent='거꾸로 꺾인 다리', four='네 다리', wide='벌린 다리', none='다리 없음')

def head(c, k):
    if k == 'oval': c.ell(16, 7, 3.2, 5); return 12
    if k == 'long': c.ell(16, 10, 2.6, 8); return 18
    if k == 'round_big':
        c.ell(16, 11, 8.5, 9)
        for x in (12, 20):
            for y in (7, 8, 9, 10): c.put(x, y, 'w')
        return 20
    if k == 'eye1':
        c.ell(16, 7, 4.5, 5); c.ell(16, 7, 2.6, 2.6, 'w'); c.ell(16, 7, 1.2, 1.8, 'k'); c.put(16, 6, 'r'); return 12
    if k == 'teeth':
        c.ell(16, 7, 4.8, 4.6); c.put(14, 5, 'w'); c.put(18, 5, 'w'); teeth(c, 12, 20, 8, 2); return 12
    if k == 'grin_wide':
        c.ell(16, 9, 7, 6.5); c.put(13, 6, 'w'); c.put(19, 6, 'w')
        for x in range(10, 23): c.put(x, 10, 'k'); c.put(x, 11, 'w' if x % 2 == 0 else 'k')
        return 15
    if k == 'antler':
        c.ell(16, 9, 3.2, 4.8)
        for pts in ([(14, 6), (9, 2), (6, -1)], [(11, 3), (9, -1)], [(18, 6), (23, 2), (26, -1)], [(21, 3), (23, -1)]): c.path(pts, 1.2, .8)
        c.put(15, 9, 'w'); c.put(17, 9, 'w'); return 13
    if k == 'drip':
        c.ell(16, 8, 4, 5)
        for x in (13, 16, 19): c.line(x, 10, x, 22 + x % 3 * 3, 1.4, .8)
        for x in (13, 19): c.ell(x, 7, 1.6, 2, 'w'); c.put(x, 8, 'k')
        return 12
    if k == 'tiny': c.ell(16, 5, 2.2, 2.6); c.put(15, 5, 'w'); c.put(17, 5, 'w'); return 8
    if k == 'two':
        c.ell(10, 8, 3.2, 4.6); c.ell(22, 10, 3.2, 4.6); c.line(10, 12, 14, 19, 2.2); c.line(22, 14, 18, 19, 2.2)
        teeth(c, 8, 12, 9, 2); c.put(9, 6, 'w'); c.put(12, 6, 'w')
        for x, y in [(21, 11), (22, 11), (23, 11), (21, 12), (23, 12), (21, 13), (22, 13), (23, 13)]: c.put(x, y, 'w')
        c.put(22, 12, 'k'); c.put(21, 8, 'w'); c.put(24, 8, 'r'); return 16
    if k == 'slit':
        c.ell(16, 8, 3.8, 5)
        for x in range(13, 20): c.put(x, 8, 'w')
        c.put(16, 8, 'r'); return 13
    if k == 'mouth_vert':
        c.ell(16, 8, 3.5, 5.5); c.ell(16, 10, 1.9, 3, 'w'); c.ell(16, 10, 1, 2.2, 'k'); c.put(15, 5, 'w'); c.put(17, 5, 'w'); return 13
    if k == 'cracked':
        c.ell(16, 8, 3.5, 5.5)
        for x, y in [(16, 3), (16, 4), (15, 5), (15, 6), (16, 7), (16, 8), (15, 9), (14, 10), (14, 11)]: c.put(x, y, 'w')
        return 13
    if k == 'hood':
        for y in range(1, 15):
            w = (y - 1) * 0.42 + .6
            for x in range(int(16 - w), int(16 + w) + 1): c.put(x, y, 's')
        c.put(14, 10, 'r'); c.put(18, 10, 'r'); return 15
    if k == 'veil':
        c.ell(16, 8, 3.5, 4.8)
        for x0, x1 in ((13, 11), (16, 16), (19, 21)): c.line(x0, 10, x1, 26 + abs(x0 - 16), 1.8, 1)
        return 12
    if k == 'eyes5':
        c.ell(16, 9, 2.6, 8)
        for i, y in enumerate((3, 6, 9, 12, 15)): c.put(15 if i % 2 else 17, y, 'w'); c.put(16, y, 'w')
        c.put(16, 9, 'r'); return 18

def torso(c, k, ny):
    if k in ('thin', 'ribs'):
        c.line(16, ny, 16, 36, 5, 4)
        if k == 'ribs':
            for y in range(ny + 2, 34, 2):
                for x in (14, 16, 18): c.put(x, y, 'w')
        return 3
    if k == 'broad': c.line(16, ny, 16, 36, 11, 6); return 6
    if k in ('bloat', 'bmouth'):
        c.ell(16, (ny + 38) / 2, 8, (38 - ny) / 2)
        if k == 'bmouth':
            my = (ny + 38) // 2
            for x in range(11, 22): c.put(x, my + int(2 * math.sin((x - 11) / 10 * math.pi)), 'k')
            teeth(c, 12, 20, my + 1, 3)
        return 8
    if k == 'bell':
        c.line(16, ny, 16, 28, 6, 5)
        for y in range(28, 56):
            w = 3 + (y - 28) * .5
            for x in range(int(16 - w), int(16 + w) + 1): c.put(x, y, 's')
        return 3

def arms(c, k, sw, sy):
    for sx in (-1, 1):
        X = lambda d: 16 + sx * d
        if k == 'long': c.path([(X(sw), sy), (X(sw + 5), 36), (X(sw + 4), 52)], 2.3, 1.3); hand(c, X(sw + 4), 52)
        elif k == 'drag': c.path([(X(sw), sy), (X(sw + 8), 40), (X(sw + 12), 55)], 2.1, 1.2); hand(c, X(sw + 12), 55, 90 + sx * 12)
        elif k == 'four':
            c.path([(X(sw), sy), (X(sw + 5), 36), (X(sw + 4), 52)], 2.2, 1.2); hand(c, X(sw + 4), 52)
            c.path([(X(sw - 1), sy + 5), (X(sw + 8), 34), (X(sw + 10), 46)], 1.8, 1); hand(c, X(sw + 10), 46)
        elif k == 'six':
            for i in range(3):
                c.path([(X(sw - 1), sy + i * 3), (X(sw + 6 + i * 2), 32 + i * 4), (X(sw + 8 + i * 4), 42 + i * 4)], 1.6, .9)
                hand(c, X(sw + 8 + i * 4), 42 + i * 4)
        elif k == 'raised': c.path([(X(sw), sy), (X(sw + 6), sy - 4), (X(sw + 9), sy - 14)], 2, 1.2); hand(c, X(sw + 9), sy - 14, 270)
        elif k == 'spindly': c.path([(X(sw), sy), (X(sw + 6), 38), (X(sw + 7), 54)], 1.1, .8); hand(c, X(sw + 7), 54)
        elif k == 'none': c.path([(X(sw), sy), (X(sw + 2), sy + 7)], 2, 1.4); hand(c, X(sw + 2), sy + 7)

def legs(c, k):
    if k == 'two': c.line(14, 36, 13, 55, 2.4, 1.6); c.line(18, 36, 19, 55, 2.4, 1.6)
    elif k == 'stilt': c.line(14, 36, 13, 55, 1.2, 1); c.line(18, 36, 19, 55, 1.2, 1)
    elif k == 'bent':
        c.path([(14, 36), (9, 45), (13, 55)], 2.2, 1.4); c.path([(18, 36), (23, 45), (19, 55)], 2.2, 1.4)
    elif k == 'four':
        c.line(14, 36, 12, 55, 2, 1.3); c.line(18, 36, 20, 55, 2, 1.3)
        c.path([(13, 38), (7, 46), (6, 55)], 1.8, 1.1); c.path([(19, 38), (25, 46), (26, 55)], 1.8, 1.1)
    elif k == 'wide': c.path([(14, 36), (8, 46), (6, 55)], 2.2, 1.4); c.path([(18, 36), (24, 46), (26, 55)], 2.2, 1.4)

def build(h, t, a, l):
    c = C()
    hb = head(c, h)
    c.line(16, hb - 2, 16, hb + 5, 2.6)
    if h == 'two': c.ell(16, 20, 10, 3)
    sw = torso(c, t, hb + 4)
    if h == 'two': sw = max(sw, 9)
    legs(c, l if t != 'bell' else 'none')
    arms(c, a, sw, hb + 6)
    return c

COMBOS = [('oval','thin','long','two'), ('teeth','broad','drag','two'), ('eye1','bloat','spindly','stilt'),
 ('grin_wide','thin','four','two'), ('long','ribs','six','two'), ('tiny','bloat','long','stilt'),
 ('veil','bell','raised','none'), ('antler','ribs','drag','bent'), ('drip','broad','long','two'),
 ('mouth_vert','thin','raised','stilt'), ('cracked','thin','long','bent'), ('slit','broad','drag','two'),
 ('hood','thin','long','two'), ('round_big','thin','spindly','stilt'), ('eyes5','bloat','four','four'),
 ('two','broad','four','two'), ('veil','thin','long','two'), ('teeth','bloat','six','stilt'),
 ('oval','bmouth','drag','bent'), ('tiny','broad','raised','wide'), ('cracked','bloat','spindly','four'),
 ('eye1','thin','six','bent'), ('hood','broad','drag','wide'), ('antler','thin','four','stilt'),
 ('mouth_vert','bloat','long','two'), ('slit','ribs','raised','bent'), ('grin_wide','broad','long','wide'),
 ('round_big','bmouth','spindly','two'), ('veil','ribs','drag','stilt'), ('drip','thin','six','four')]

def main():
    root = os.path.join(os.path.dirname(__file__), '..', 'art', 'variants')
    for b in range(2):
        lines = ['# 검은 인간 조합 시안 (tools/gen_shadow_mix.py 가 생성함)', '']
        for r in range(3):
            for i in range(5):
                n = b * 15 + r * 5 + i
                h, t, a, l = COMBOS[n]
                c = build(h, t, a, l)
                desc = f'{HN[h]}, {TN[t]}, {AN[a]}, {LN[l] if t != "bell" else LN["none"]}'
                lines.append(f'[{"N" + "-=~"[r] if False else "row" + str(r)}_{n + 1:02d}] {desc} | {n + 1}')
                lines += c.finish(); lines.append('')
        open(os.path.join(root, f'shadow{3 + b}_pixels.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
main()
