"""주인공 7차 시안: 6차와 같은 몸/머리에 어두운 계열 옷 색만 여러 개 (tools/gen_child7.py)"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import gen_child6 as G6
from gen_child6 import build, K
G6.SHADE.update({'B': 'D', 'E': 'F', 'H': 'I', 'z': 'x', 'm': 'd', 'v': 'j', 'T': 'K', 'j': 'k', 'x': 'k'})

def shoes(c, col='k', skin_foot=False):
    c.ell(9.2, 37.2, 2.2, .9, col); c.ell(14.8, 37.2, 2.2, .9, col); return c.finish()

OUT = [  # 라벨: (윗옷, 바지, 설명)
    ('A', 'B', 'd', '남색 긴소매, 짙은 보라회색 긴바지'),
    ('B', 'E', 'd', '와인색 긴소매, 짙은 긴바지'),
    ('C', 'z', 'd', '짙은 숲초록 긴소매, 짙은 긴바지'),
    ('D', 'm', 'j', '숯회색 긴소매, 짙은 자두색 긴바지'),
    ('E', 'H', 'd', '어두운 겨자색 긴소매, 짙은 긴바지'),
    ('F', 'v', 'd', '짙은 보라 긴소매, 짙은 긴바지'),
    ('G', 'T', 'd', '어두운 청록 긴소매, 짙은 긴바지'),
    ('H', 'd', 'B', '거의 검은 긴소매, 남색 긴바지'),
]

def main():
    root = os.path.join(os.path.dirname(__file__), '..', 'art', 'variants')
    lines = ['# 주인공 7차 시안: 어두운 옷 색 8종 (tools/gen_child7.py 가 생성함)', '']
    for v, sh, pa, note in OUT:
        if pa not in G6.SHADE: G6.SHADE[pa] = 's'
        c = build(sh, pa); lines.append(f'[child_{v}] {note} | {v}'); lines += shoes(c); lines.append('')
    open(os.path.join(root, 'child7_pixels.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
if __name__ == '__main__': main()
