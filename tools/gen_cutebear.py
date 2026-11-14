#!/usr/bin/env python3
"""말랑한 곰 캐릭터(오리지널, 초록 후드 옷) 표정 4종. 사용: python3 tools/gen_cutebear.py && python3 tools/variants.py cutebear   (24x32)"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import gen_shadow as G
from gen_shadow import C
G.W, G.H = 24, 32

def rect(c, x0, y0, x1, y1, ch):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1): c.put(x, y, ch)

class OffC(C):
    """y 를 oy 만큼 내려 그리는 캔버스(긴 귀 때문에 위쪽 여백이 필요한 토끼용). ell/line 이 내부에서 put 을 부르므로 이중 이동을 막는다."""
    oy = 0; _in = False
    def put(s, x, y, ch): super().put(x, y + (0 if s._in else s.oy), ch)
    def _wrap(s, fn, *a, **k):
        s._in = True
        try: fn(*a, **k)
        finally: s._in = False
    def ell(s, cx, cy, rx, ry, ch='s'): s._wrap(super().ell, cx, cy + s.oy, rx, ry, ch)
    def line(s, x0, y0, x1, y1, w=1.0, w1=None, ch='s'): s._wrap(super().line, x0, y0 + s.oy, x1, y1 + s.oy, w, w1, ch)

KINDS = {   # 글자 바꾸기: 곰은 그대로, 토끼는 흰 털 + 붉은 후드티 + 짙은 회색 바지
    'bear': {'Z': 'z', 'X': 'x', 'H': 'h'},
    'rabbit': {'u': 'w', 'h': 'a', 'f': 'o', 'z': 'r', 'x': 'r', 'Z': 'd', 'X': 's', 'H': 'm', 'b': 'p'},
}

def character(expr, kind='bear'):
    c = OffC(); c.oy = 8 if kind == 'rabbit' else 0
    if kind == 'bear':
        for sx in (5, 19): c.ell(sx, 4.5, 3.4, 3.2, 'u'); c.ell(sx, 4.8, 1.7, 1.5, 'i')                    # 귀
    else:
        for sx, tilt in ((7.5, -.6), (16.5, .6)):                                                           # 길고 둥근 귀 (살짝 벌어짐)
            c.ell(sx + tilt, -3, 2.9, 7.2, 'u'); c.ell(sx + tilt, -2.4, 1.4, 5.4, 'i')
    c.ell(8.2, 31.2, 3.2, 1.0, 'u'); c.ell(15.8, 31.2, 3.2, 1.0, 'u')                                       # 발
    for cx, sx in ((8.8, 10.0), (15.2, 16.6)):                                                             # 바지: 크림색, 다리마다 오른쪽 안쪽에 그늘
        c.ell(cx, 29.2, 3.5, 2.6, 'Z'); c.ell(sx, 29.6, 1.5, 2.2, 'X'); c.put(cx - 2, 28, 'H')
    c.line(12, 27, 12, 30, 1, ch='X')                                                                       # 두 다리 사이 선
    for sx, sgn in ((5.2, -1), (18.8, 1)):                                                                 # 팔
        c.ell(sx, 22, 2.9, 3.7, 'h'); c.ell(sx + sgn * .3, 25.6, 2.2, 1.9, 'u')
    c.ell(12, 22.2, 7.4, 6.2, 'h'); c.ell(8.8, 20.5, 2.6, 3.0, 'f')                                         # 둥근 후드티 몸과 하이라이트
    c.ell(12, 18.6, 8.2, 2.8, 'f'); c.ell(12, 18.6, 5.4, 1.6, 'z')                                          # 말린 후드와 안쪽 그늘
    for sx in (-1, 1): c.line(12 + sx * 1.6, 20, 12 + sx * 1.9, 23.5, 1, ch='q'); c.put(12 + sx * 1.9, 24.5, 'q')   # 후드 끈
    c.ell(12, 25.2, 4.6, 1.9, 'h'); c.line(8, 24, 16, 24, 1, ch='z')                                        # 앞주머니(몸과 같은 초록, 윗선만 그늘)
    for sx in (5.2, 18.8): c.ell(sx, 24.8, 2.4, .8, 'z')                                                   # 소매 밴드
    rect(c, 7, 27, 17, 27, 'x')                                                                            # 밑단 밴드
    c.ell(12, 11, 9.6, 8.2, 'u'); c.ell(12, 14, 5.2, 3.6, 'q')                                             # 머리와 주둥이
    for sx in (-1, 1): c.ell(12 + sx * 6.2, 14, 2.1, 1.5, 'i')                                              # 볼터치
    c.put(12, 13, 'b'); c.put(11, 13, 'b'); c.put(13, 13, 'b')                                              # 코
    if expr == 'A':
        for ex in (7, 16): c.put(ex, 11, 'k'); c.put(ex + 1, 11, 'k'); c.put(ex, 12, 'k'); c.put(ex + 1, 12, 'k')
        for x in range(10, 15): c.put(x, 16, 'k')                            # 평소 표정: 입은 일자(ㅡ)
    if expr == 'B':
        for ex in (7, 16): c.put(ex, 12, 'k'); c.put(ex + 1, 11, 'k'); c.put(ex + 2, 12, 'k')
        for x in range(10, 15): c.put(x, 15, 'k')
        for x in range(11, 14): c.put(x, 16, 'r')
    if expr == 'C':
        for ex in (7, 16): c.put(ex, 12, 'k'); c.put(ex + 1, 12, 'k'); c.put(ex, 13, 'k'); c.put(ex + 1, 13, 'k')
        c.line(6, 9, 9, 10, 1, ch='k'); c.line(18, 9, 15, 10, 1, ch='k')
        for x in range(10, 15): c.put(x, 16, 'k')
        c.ell(20, 6, 1.2, 1.8, 'c'); c.put(20, 4, 'c')
    if expr == 'D':
        for ex in (6, 15): c.line(ex, 12, ex + 3, 12, 1, ch='k')
        c.put(11, 15, 'k'); c.put(12, 16, 'k'); c.put(13, 15, 'k'); c.ell(12, 16.5, 1, 1, 'r')
        for x, y in ((19, 1), (20, 1), (21, 1), (20, 2), (19, 3), (20, 3), (21, 3)): c.put(x, y, 'w')
    if expr == 'E':                                                                                         # 화남: 가는 눈, 가파른 눈썹, 이마의 핏대, 입은 일자
        for ex in (7, 16): c.put(ex, 12, 'k'); c.put(ex + 1, 12, 'k')
        c.line(5, 8, 9, 11, 1, ch='k'); c.line(19, 8, 15, 11, 1, ch='k'); c.line(5, 9, 9, 12, 1, ch='k'); c.line(19, 9, 15, 12, 1, ch='k')
        for x in range(10, 15): c.put(x, 16, 'k')
        for x, y in ((19, 3), (20, 3), (19, 4), (21, 4), (20, 5), (21, 5)): c.put(x, y, 'r')
    rows = c.finish(); m = KINDS[kind]
    return [''.join(m.get(ch, ch) for ch in r) for r in rows]

def export_final():
    """확정안을 art/objects.txt 에 넣는다: bear_green_A..E, rabbit_red_A..E (표정 5종)."""
    root = os.path.join(os.path.dirname(__file__), '..', 'art'); path = os.path.join(root, 'objects.txt')
    notes = {'A': '기본(입 일자)', 'B': '웃음', 'C': '걱정(입 일자)', 'D': '졸림', 'E': '화남(입 일자)'}
    blocks = []
    for kind, pre, desc in (('bear', 'bear_green', '말랑한 곰(초록 후드, 짙은 초록 바지)'), ('rabbit', 'rabbit_red', '말랑한 토끼(여자, 흰 피부, 붉은 더블 트렌치코트, 줄무늬 스카프)')):
        for v in 'ABCDE':
            blocks.append(f'[{pre}_{v}] {desc} {notes[v]} | dream\n' + '\n'.join(draw(v, kind)) + '\n')
    keep, skip = [], False
    for line in open(path, encoding='utf-8').read().split('\n'):
        if line.startswith('['): skip = line.startswith('[bear_green') or line.startswith('[rabbit_red')
        if not skip: keep.append(line)
    open(path, 'w', encoding='utf-8').write('\n'.join(keep).rstrip('\n') + '\n\n' + '\n'.join(blocks))

def round_eye(c, ex):
    for dx in (0, 1):
        for dy in (10.5, 11.5, 12.5): c.put(ex + dx, dy - .5, 'k')
    c.put(ex, 10, 'W')                                                                                       # 하이라이트

def rabbit_char(expr):
    """토끼(여자 캐릭터): 레퍼런스 도트화의 비율 + 붉은 더블 트렌치코트(넓은 옷깃, 검은 단추 두 줄, 소매 끈, 주머니 덮개), 줄무늬 스카프, 둥근 귀."""
    c = OffC(); c.oy = 8
    for sx, tilt in ((7.2, -.7), (16.8, .7)):                                                               # 둥글고 부드러운 귀(끝이 각지지 않게 두 타원을 겹침)
        c.ell(sx + tilt, -2.6, 3.3, 6.4, 'W'); c.ell(sx + tilt * 1.4, -7.4, 2.5, 2.6, 'W'); c.ell(sx + tilt + .4, -2.2, 1.5, 4.8, 'i')
    c.ell(12, 11, 9.8, 8.1, 'W'); c.ell(15.8, 14.2, 4.2, 3.6, 'w'); c.ell(12, 11, 9.2, 7.5, 'W')            # 둥근 하얀 머리, 오른쪽 아래 옅은 그늘
    for sx in (-1, 1): c.ell(12 + sx * 6, 14.4, 1.9, 1.3, 'i')                                              # 옅은 볼터치
    c.put(12, 13, 'k')                                                                                     # 작은 코
    c.ell(6.2, 4.6, 2.2, 1.6, 'R'); c.ell(9.4, 5, 1.8, 1.4, 'R'); c.put(8, 5, 'Q'); c.put(7, 5, 'Q')       # 귀 밑 작은 빨간 리본
    c.ell(9.6, 34.4, 2.4, 1.0, 'd'); c.ell(14.4, 34.4, 2.4, 1.0, 'd')                                       # 짧은 부츠
    c.ell(9.8, 32.2, 1.1, 2.6, 'W'); c.ell(14.2, 32.2, 1.1, 2.6, 'W')                                       # 가늘고 하얀 다리
    for sx, sgn in ((6.0, -1), (18.0, 1)):                                                                 # 가는 소매, 하얀 손, 소매 끈
        c.ell(sx, 23.2, 1.9, 5.0, 'R'); c.ell(sx + sgn * .2, 28.2, 1.7, 1.5, 'W'); c.line(sx - 1.6, 26.4, sx + 1.6, 26.4, 1, ch='Q')
    for y in range(18, 31):                                                                                # 코트 몸통: 얇고 길게, 허리가 들어가고 아래로 살짝만 퍼짐
        half = 4.2 + (y - 18) * .22 - (.8 if 22 <= y <= 24 else 0)
        for x in range(int(12 - half + .5), int(12 + half + .5) + 1): c.put(x, y, 'R')
    for y in range(20, 31):                                                                                # 오른쪽 그늘
        half = 4.2 + (y - 18) * .22 - (.8 if 22 <= y <= 24 else 0)
        for x in range(int(12 + half - 1.6), int(12 + half + .5) + 1): c.put(x, y, 'Q')
    rect(c, 9, 31, 15, 31, 'j')                                                                            # 코트 아래로 보이는 짙은 원피스 자락
    c.line(8.6, 23.4, 15.4, 23.4, 1, ch='Q'); c.put(12, 23, 'y')                                           # 허리 벨트와 버클
    c.line(10, 19, 12, 24, 1, ch='Q'); c.line(14, 19, 12, 24, 1, ch='Q'); c.ell(9.8, 20.3, 1.4, 1.4, 'R'); c.ell(14.2, 20.3, 1.4, 1.4, 'R')    # 옷깃(라펠)
    for y in (21.5, 25.5, 28.5): c.put(10, y, 'k'); c.put(14, y, 'k')                                      # 검은 더블 단추
    c.line(12, 24, 12, 30, 1, ch='Q')                                                                      # 앞여밈
    c.ell(12, 19.4, 4.2, 1.6, 'W')                                                                         # 줄무늬 스카프
    for x in (9, 11, 13, 15): c.put(x, 19, 'k')
    rect(c, 13, 20, 14, 23, 'W'); c.line(13, 21, 14, 21, 1, ch='k'); c.line(13, 23, 14, 23, 1, ch='k')   # 늘어진 스카프 끝
    if expr == 'A':
        for ex in (7, 16): round_eye(c, ex)
        c.put(6, 10, 'k'); c.put(17, 10, 'k')                                                              # 속눈썹
        for x in range(11, 14): c.put(x, 15, 'k')
    if expr == 'B':
        for ex in (7, 16): c.put(ex, 12, 'k'); c.put(ex + 1, 11, 'k'); c.put(ex + 2, 12, 'k')
        for x in range(11, 14): c.put(x, 15, 'k')
        c.put(12, 16, 'r')
    if expr == 'C':
        for ex in (7, 16): round_eye(c, ex)
        c.line(6, 8, 9, 9, 1, ch='k'); c.line(18, 8, 15, 9, 1, ch='k')
        for x in range(11, 14): c.put(x, 15, 'k')
        c.ell(20, 6, 1.2, 1.8, 'c'); c.put(20, 4, 'c')
    if expr == 'D':
        for ex in (6, 15): c.line(ex, 12, ex + 2, 12, 1, ch='k')
        c.put(12, 15, 'k')
        for x, y in ((19, 1), (20, 1), (21, 1), (20, 2), (19, 3), (20, 3), (21, 3)): c.put(x, y, 'k')
    if expr == 'E':
        for ex in (7, 16): round_eye(c, ex)
        c.line(5, 7, 9, 10, 1, ch='k'); c.line(19, 7, 15, 10, 1, ch='k'); c.line(5, 8, 9, 11, 1, ch='k'); c.line(19, 8, 15, 11, 1, ch='k')
        for x in range(11, 14): c.put(x, 15, 'k')
        for x, y in ((19, 3), (20, 3), (19, 4), (21, 4), (20, 5), (21, 5)): c.put(x, y, 'r')
    return c.finish()

def draw(expr, kind):
    G.W, G.H = 24, (44 if kind == 'rabbit' else 32)
    return rabbit_char(expr) if kind == 'rabbit' else character(expr, kind)

def main():
    root = os.path.join(os.path.dirname(__file__), '..', 'art', 'variants')
    notes = {'A': '기본 표정(입 일자)', 'B': '웃는 표정', 'C': '걱정(땀방울, 입 일자)', 'D': '졸림', 'E': '화남(입 일자)'}
    for kind, batch in (('bear', 'cutebear'), ('rabbit', 'cuterabbit')):
        lines = [f'# 말랑한 {kind} 표정 5종 (tools/gen_cutebear.py 가 생성함)', '']
        for v in 'ABCDE':
            lines.append(f'[{kind}_{v}] {notes[v]} | {v}'); lines += draw(v, kind); lines.append('')
        open(os.path.join(root, batch + '_pixels.txt'), 'w', encoding='utf-8').write('\n'.join(lines))

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'final': export_final()
    else: main()
