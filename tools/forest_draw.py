"""숲 배경 그리기 공통 함수: 잎 덩어리(참나무 잎처럼 울퉁불퉁한 가장자리), 나무 둥치(껍질 결 + 뿌리)."""
import math, random

def leafy(put, cx, cy, r, rng, dark, mid, light, wrap=None):
    """울퉁불퉁한 잎 덩어리: 반지름이 각도에 따라 출렁이고(잎 뭉치), 위·왼쪽은 밝게, 아래·오른쪽은 어둡게."""
    ph = rng.random() * 6.28; lobes = rng.choice((5, 6, 7))
    for y in range(cy - r - 2, cy + r + 3):
        for x in range(cx - r - 2, cx + r + 3):
            dx, dy = x - cx, y - cy; ang = math.atan2(dy, dx)
            rr = r * (.78 + .22 * math.sin(lobes * ang + ph)) + rng.random() * .6
            d = math.hypot(dx, dy)
            if d <= rr:
                lit = (-dx - dy) / (r * 1.4 + .1)                                   # 왼쪽 위로 갈수록 밝음
                c = light if lit > .35 and (x + y) % 3 else mid if lit > -.25 else dark
                if d > rr - 1.2 and lit < 0: c = dark
                xx = x % wrap if wrap else x; put(xx, y, c)

def trunk(put, x0, w, y0, y1, bark, hi, shade, rng, root=0, wrap=None):
    """나무 둥치: 왼쪽 밝고 오른쪽 어두운 면, 세로 껍질 결, 아래로 갈수록 뿌리처럼 넓어짐(root = 뿌리 높이)."""
    for y in range(y0, y1 + 1):
        flare = max(0, y - (y1 - root)) * 1 if root else 0
        for k in range(-flare // 2, w + (flare + 1) // 2):
            if k < 0 or k >= w: c = shade if rng.random() < .5 else bark
            elif k == 0: c = hi
            elif k >= w - 2: c = shade
            else: c = shade if (y // 2 + k * 3) % 7 == 0 else bark
            xx = x0 + k; put(xx % wrap if wrap else xx, y, c)
