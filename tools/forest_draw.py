"""숲 배경 그리기 공통 함수: 잎 덩어리, 나무 둥치, 삼각형 침엽수. 패턴(체크·빗금) 없이 3단계 명암의 면으로 단순하게 그린다."""
import math, random

def leafy(put, cx, cy, r, rng, dark, mid, light, wrap=None):
    """울퉁불퉁한 잎 덩어리: 반지름이 각도에 따라 출렁이고, 위·왼쪽은 밝게(light), 가운데 mid, 아래·오른쪽 dark. 무늬 없는 면."""
    ph = rng.random() * 6.28; lobes = rng.choice((4, 5, 6))
    for y in range(cy - r - 2, cy + r + 3):
        for x in range(cx - r - 2, cx + r + 3):
            dx, dy = x - cx, y - cy; ang = math.atan2(dy, dx)
            rr = r * (.8 + .2 * math.sin(lobes * ang + ph))
            if math.hypot(dx, dy) <= rr:
                lit = (-dx - dy) / (r * 1.4 + .1)
                put(x % wrap if wrap else x, y, light if lit > .45 else mid if lit > -.2 else dark)

def trunk(put, x0, w, y0, y1, bark, hi, shade, rng, root=0, wrap=None):
    """나무 둥치: 왼쪽 가장자리 밝고 오른쪽 어두운 두 면. 껍질 무늬는 드문 세로 선 몇 개만. 아래로 갈수록 뿌리처럼 넓어짐(root = 뿌리 높이)."""
    streaks = {x0 + 1 + (k * 7) % max(1, w - 2) for k in range(2)}
    for y in range(y0, y1 + 1):
        flare = max(0, y - (y1 - root)) if root else 0
        for k in range(-flare // 2, w + (flare + 1) // 2):
            if k < 0 or k >= w: c = shade
            elif k == 0: c = hi
            elif k >= w - 2: c = shade
            elif (x0 + k) in streaks and (y // 6) % 2 == 0: c = shade
            else: c = bark
            xx = x0 + k; put(xx % wrap if wrap else xx, y, c)

def fir(put, cx, base_y, h, w, dark, mid, light, trunk_c=None, rng=None):
    """삼각형 침엽수(전나무): 5단 가지층이 계단식으로 넓어지는 삼각형. 단이 바뀔 때마다 가장자리가 안으로 들어가 톱니 모양이 된다.
    왼쪽 면 밝게, 가운데 mid, 오른쪽 어둡게."""
    n = 5; top = base_y - h; tr = trunk_c or dark
    for y in range(int(base_y - h * .1), int(base_y) + 1):
        for x in range(cx - 1, cx + 2): put(x, y, tr)
    body = h * .92
    for y in range(int(top), int(top + body) + 1):
        u = (y - top) / body * n; tier = min(n - 1, int(u)); f = u - tier
        half = (w / 2) * (tier + .22 + .78 * f) / n
        for x in range(int(cx - half), int(cx + half) + 1):
            d = (x - cx) / max(1.0, half)
            put(x, y, light if d < -.3 else dark if d > .4 else mid)
