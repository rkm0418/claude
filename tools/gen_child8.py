"""주인공 8차 시안: 짙은 초록 계열 변주 (tools/gen_child8.py)"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import gen_child6 as G6
from gen_child6 import build, K
G6.SHADE.update({'N': 'S', 'M': 'U', 'V': 'G', 'J': 'z', 'Z': 'k', 'z': 'x', 'B': 'D', 'b': 'd', 'h': 'O', 'm': 'd', 'd': 's'})
def shoes(c, col='k'):
    c.ell(9.2, 37.2, 2.2, .9, col); c.ell(14.8, 37.2, 2.2, .9, col); return c.finish()
def slipper(c):
    c.ell(9.2, 37.4, 2.4, .9, 'p'); c.ell(14.8, 37.2, 1.8, .8, K.SKIN); return c.finish()
def sock(c):
    c.ell(9.2, 36.0, 2.0, 1.3, 'W'); c.ell(9.2, 37.3, 2.2, .8, 'd'); c.ell(14.8, 37.3, 2.2, .8, 'd'); return c.finish()
OUT = [
    ('A', 'z', 'B', shoes, '숲초록 긴소매, 남색 긴바지'),
    ('B', 'N', 'd', shoes, '소나무 초록 긴소매, 짙은 긴바지'),
    ('C', 'M', 'b', shoes, '이끼색 긴소매, 짙은 갈색 긴바지'),
    ('D', 'V', 'd', shoes, '회청록 긴소매, 짙은 긴바지'),
    ('E', 'J', 'd', shoes, '중간 숲초록 긴소매, 짙은 긴바지'),
    ('F', 'Z', 'm', shoes, '거의 검은 초록 긴소매, 회색 긴바지'),
    ('G', 'z', 'd', slipper, '숲초록 긴소매, 짙은 긴바지, 슬리퍼 한 짝'),
    ('H', 'N', 'h', sock, '소나무 초록 긴소매, 올리브 긴바지, 한쪽 바짓단 접힘'),
]
def main():
    root = os.path.join(os.path.dirname(__file__), '..', 'art', 'variants')
    lines = ['# 주인공 8차 시안: 짙은 초록 계열 (tools/gen_child8.py 가 생성함)', '']
    for v, sh, pa, fn, note in OUT:
        c = build(sh, pa); lines.append(f'[child_{v}] {note} | {v}'); lines += fn(c); lines.append('')
    open(os.path.join(root, 'child8_pixels.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
if __name__ == '__main__': main()
