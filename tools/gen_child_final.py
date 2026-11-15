"""주인공 확정안(8차 2번: 소나무 초록 윗옷 + 짙은 긴바지 + 검은 신발)을 art/objects.txt 에 넣는다.
정지 1장 + 걷기 4장(24x38), 맵용 1/2 크기(12x19) 정지 1장 + 걷기 4장.  실행: python3 tools/gen_child_final.py"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from gen_t11 import downscale
import gen_shadow
import gen_child8 as G8
import gen_child6 as G6

def still():
    gen_shadow.W, gen_shadow.H = 24, 38
    c = G6.build('N', 'd'); return G8.shoes(c)

def walk(rows, phase):
    """phase 0/2 = 정지, 1 = 왼다리를 들고 오른팔을 앞으로, 3 = 오른다리를 들고 왼팔을 앞으로."""
    g = [list(r) for r in rows]; H, W = len(g), len(g[0])
    if phase in (1, 3):
        lo, hi = (0, 12) if phase == 1 else (12, W)
        for y in range(31, H - 1):                                     # 들어 올린 다리: 한 칸 위로
            for x in range(lo, hi): g[y - 1][x] = g[y][x]
        for x in range(lo, hi): g[H - 1][x] = '.'
        a_lo, a_hi = (17, 22) if phase == 1 else (2, 7)                 # 반대쪽 팔(손)을 한 칸 아래로
        for y in range(31, 25, -1):
            for x in range(a_lo, a_hi):
                if g[y - 1][x] != '.' and g[y][x] == '.': g[y][x] = g[y - 1][x]
    return [''.join(r) for r in g]

def export_final():
    root = os.path.join(os.path.dirname(__file__), '..', 'art'); base = still()
    frames = [('child', 0, '주인공(얼굴 없음) 정지'), ('child_w1', 1, '주인공 걷기 1/4'), ('child_w2', 2, '주인공 걷기 2/4'), ('child_w3', 3, '주인공 걷기 3/4'), ('child_w4', 2, '주인공 걷기 4/4')]
    blocks = []
    for name, ph, desc in frames: blocks.append(f'[{name}] {desc} | real\n' + '\n'.join(walk(base, ph)) + '\n')
    for name, ph, desc in frames: blocks.append(f'[{name.replace("child", "child_s", 1)}] {desc} (맵 크기 12x19) | real\n' + '\n'.join(downscale(walk(base, ph))) + '\n')
    path = os.path.join(root, 'objects.txt'); keep, skip = [], False
    for line in open(path, encoding='utf-8').read().split('\n'):
        if line.startswith('['): skip = line.startswith('[child')
        if not skip: keep.append(line)
    open(path, 'w', encoding='utf-8').write('\n'.join(keep).rstrip('\n') + '\n\n' + '\n'.join(blocks))
if __name__ == '__main__': export_final()
