#!/usr/bin/env python3
"""터널 중간: 현실의 도시(차갑고 푸른 콘크리트)에서 판타지 세계(따뜻한 호박빛, 낙엽, 흙)로 넘어가는 긴 터널. 사선 3차원 시점.
아래(가까운 쪽)는 차가운 타일·형광등빛·아스팔트, 위로 갈수록 벽이 흙·돌로 바뀌고 낙엽이 쌓이며, 맨 끝 아치 너머로 가을 들판의 빛이 보인다.
사용: python3 tools/render_tunnel.py -> maps/out/tunnel_middle.png (+_x2)"""
import math, os, random, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from render_city3d import Scene, dk, OUT

def mix(a, b, f): f = max(0.0, min(1.0, f)); return tuple(int(a[i] + (b[i] - a[i]) * f) for i in range(3))
def noise(x, d, s=0): return ((int(x * 12.9898 + d * 78.233 + s * 37.7) * 2654435761) >> 7) % 100 / 100.0
W, D, H = 64, 300, 58
def f_of(d): return (d - D * .30) / (D * .55)                 # 0 = 도시, 1 = 가을 세계

def build():
    sc = Scene(W, D, H); rng = random.Random(7); sc.img.paste((14, 14, 24), (0, 0, sc.CW, sc.CH)); sc.d = ImageDraw.Draw(sc.img)
    ASPH = (30, 32, 46); DIRT = (122, 90, 60)
    def floor(x, d):
        f = f_of(d); n = noise(x, d)
        base = mix(ASPH, DIRT, f - .2 + (n - .5) * .5)            # 섞이며 흙이 번진다
        if x % 32 < 1 and f < .5: base = mix((90, 90, 84), base, f * 2)   # 가운데 흰 점선(도시 쪽에만)
        return base
    sc.floor(floor)
    sc.poly([(0, 0, -7), (W, 0, -7), (W, 0, 0), (0, 0, 0)], (50, 54, 70)); sc.poly([(W, 0, -7), (W, D, -7), (W, D, 0), (W, 0, 0)], (36, 38, 52))
    # 왼쪽 벽: 도시 쪽은 차가운 타일, 위로 갈수록 이끼 낀 돌/흙벽
    for d0 in range(0, D, 6):
        f = f_of(d0 + 3)
        for z0 in range(0, H, 6):
            n = noise(d0, z0, 5)
            cold = mix((70, 84, 104), (92, 110, 130), n); warm = mix((96, 66, 46), (136, 98, 62), n)
            if f > .35 and z0 > H - 14 * (f - .2): warm = mix(warm, (90, 100, 50), .5)     # 위쪽에 이끼
            c = mix(cold, warm, f)
            sc.poly([(0, d0, z0), (0, d0 + 6, z0), (0, d0 + 6, z0 + 6), (0, d0, z0 + 6)], c)
            sc.poly([(0, d0, z0), (0, d0 + 6, z0), (0, d0 + 6, z0 + .8), (0, d0, z0 + .8)], dk(c, .72)); sc.poly([(0, d0, z0), (0, d0 + .8, z0), (0, d0 + .8, z0 + 6), (0, d0, z0 + 6)], dk(c, .8))
    for d in range(0, D, 50):                                                    # 아치 리브(벽면의 굵은 세로 기둥)
        f = f_of(d); c = mix((52, 62, 80), (78, 54, 38), f)
        sc.poly([(0, d, 0), (0, d + 4, 0), (0, d + 4, H), (0, d, H)], c)
    sc.poly([(0, 0, H - 4), (0, D, H - 4), (0, D, H), (0, 0, H)], (28, 32, 46))   # 천장 가장자리 띠
    sc.poly([(0, 0, 10), (0, D, 10), (0, D, 11.5), (0, 0, 11.5)], (40, 46, 62))   # 낮은 난간선
    # 맨 끝 벽 + 아치 열린 곳(가을 들판의 빛)
    sc.poly([(0, D, 0), (W, D, 0), (W, D, H), (0, D, H)], (58, 42, 34))
    pts = [(7, D, 0)] + [(32 - 25 * math.cos(math.pi * k / 16), D, 34 + 14 * math.sin(math.pi * k / 16)) for k in range(0, 17)] + [(57, D, 0)]
    mask = Image.new('L', sc.img.size, 0); ImageDraw.Draw(mask).polygon([sc.P(*q) for q in pts], fill=255)
    lay = sc.img.copy(); ld = ImageDraw.Draw(lay)
    for z in range(0, 50): ld.polygon([sc.P(0, D, z), sc.P(W, D, z), sc.P(W, D, z + 1.2), sc.P(0, D, z + 1.2)], fill=mix((255, 222, 150), (232, 150, 110), z / 48))
    for k, (x, r, col) in enumerate(((16, 9, (190, 90, 40)), (34, 11, (226, 160, 56)), (48, 8, (170, 60, 36)))):   # 먼 나무 실루엣
        cx, cy = sc.P(x, D, 22 + (k % 2) * 3); ld.ellipse([cx - r, cy - r * .8, cx + r, cy + r * .8], fill=col); ld.rectangle([cx - 1, cy + r * .5, cx, sc.P(x, D, 0)[1]], fill=(90, 58, 40))
    ld.polygon([sc.P(0, D, 0), sc.P(W, D, 0), sc.P(W, D, 9), sc.P(0, D, 9)], fill=(150, 112, 60))
    sc.img.paste(lay, (0, 0), mask); sc.px = sc.img.load(); sc.d = ImageDraw.Draw(sc.img)
    sc.glow(32, D - 10, 70, col=(255, 200, 120), power=.8)                        # 끝에서 새어 나오는 따뜻한 빛이 바닥에 번진다
    # 벽등: 처음엔 차가운 형광등 빛, 위로 갈수록 따뜻하게(같은 간격)
    for d in (30, 90, 150, 210, 262):
        f = f_of(d); lc = mix((170, 214, 255), (255, 200, 120), f)
        def draw(d=d, lc=lc): sc.box(0, d, 3, 5, 5, lc, mix(lc, (0, 0, 0), .25), mix(lc, (0, 0, 0), .45), z0=34)
        sc.jobs.append((d, draw)); sc.glow(8, d, 34, col=lc, power=.5)
    sc.run()
    # 낙엽: 끝으로 갈수록 많아지고, 가까운 쪽엔 거의 없다(몇 장은 안쪽으로 날려 들어온다)
    LC = [(214, 104, 44), (236, 160, 60), (170, 56, 36), (246, 206, 92)]
    for _ in range(420):
        d = D * rng.random() ** .6; x = rng.uniform(1, W - 1)
        if rng.random() < f_of(d) + .08:
            X, Y = sc.P(x, d, 0); sc.px[X, Y] = rng.choice(LC); sc.px[X + 1, Y] = rng.choice(LC)
    for _ in range(26):
        d = rng.uniform(D * .55, D - 4); X, Y = sc.P(rng.uniform(4, W - 4), d, rng.uniform(4, 30)); sc.d.rectangle([X, Y, X + 1, Y + 1], fill=rng.choice(LC))
    return sc

def main():
    sc = build(); out = os.path.join(OUT, 'tunnel_middle.png'); sc.img.save(out)
    sc.img.resize((sc.CW * 3, sc.CH * 3), Image.NEAREST).save(out.replace('.png', '_x3.png')); print(out, sc.img.size)
if __name__ == '__main__': main()
