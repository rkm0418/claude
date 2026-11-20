#!/usr/bin/env python3
"""저장해 둔 소품: 기와집(스케치 그대로). 정면(창+문) 벽, 오른쪽 옆벽, 처마가 벽 밖으로 길게 나온 네모 지붕.
가을 숲 맵에서 빠졌지만 다른 장면에 다시 쓸 수 있게 따로 보관한다.
사용:  from prop_house import house;  house(sc, x, d, w, dp, h)   (sc 는 render_city3d.Scene, 먼 것부터 그리는 sc.jobs 에 등록되므로 sc.run() 전에 부른다)
미리보기:  python3 tools/prop_house.py  ->  maps/out/prop_house.png
레이어 규칙(docs/layer-rules.md): 집은 sc.box 로 그려 단단한 물체로 기록된다."""
import os, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from render_city3d import Scene, dk, OUT

def house(sc, x, d, w, dp, h):
    """스케치 그대로: 정면(창+문) 벽, 오른쪽 옆벽, 처마가 벽 밖으로 길게 나온 네모 지붕(앞면은 사다리꼴, 오른쪽은 모임지붕)."""
    def f():
        sc.box(x, d, w, dp, h, (236, 220, 190), (232, 214, 182), (196, 176, 146))
        o, o2, rh, dm = 4, w * .2, h * .75, d + dp / 2
        # 창(4칸)과 문
        wx0, wx1, wz0, wz1 = x + w * .12, x + w * .38, h * .42, h * .82
        sc.poly([(wx0, d, wz0), (wx1, d, wz0), (wx1, d, wz1), (wx0, d, wz1)], (96, 70, 48))
        sc.poly([(wx0 + 1, d, wz0 + 1), (wx1 - 1, d, wz0 + 1), (wx1 - 1, d, wz1 - 1), (wx0 + 1, d, wz1 - 1)], (74, 90, 120))
        mx, mz = (wx0 + wx1) / 2, (wz0 + wz1) / 2
        sc.poly([(mx - .5, d, wz0), (mx + .5, d, wz0), (mx + .5, d, wz1), (mx - .5, d, wz1)], (96, 70, 48)); sc.poly([(wx0, d, mz - .5), (wx1, d, mz - .5), (wx1, d, mz + .5), (wx0, d, mz + .5)], (96, 70, 48))
        dx0, dx1, dz1 = x + w * .58, x + w * .8, h * .72
        sc.poly([(dx0 - 1, d, 0), (dx1 + 1, d, 0), (dx1 + 1, d, dz1 + 1), (dx0 - 1, d, dz1 + 1)], (96, 70, 48)); sc.poly([(dx0, d, 0), (dx1, d, 0), (dx1, d, dz1), (dx0, d, dz1)], (132, 94, 62))
        # 지붕: 처마 아래 그늘 띠 -> 앞 사다리꼴 -> 오른쪽 모임면
        sc.poly([(x - o, d - o, h - 1), (x + w + o, d - o, h - 1), (x + w + o, d - o, h + 1), (x - o, d - o, h + 1)], (52, 50, 66))
        sc.poly([(x - o, d - o, h + 1), (x + w + o, d - o, h + 1), (x + w - o2, dm, h + rh), (x + o2, dm, h + rh)], (96, 94, 114))
        sc.poly([(x + w + o, d - o, h + 1), (x + w + o, d + dp + o, h + 1), (x + w - o2, dm, h + rh)], (70, 68, 88))
        for k in range(1, 5):                                                                                       # 기와 줄
            z = h + 1 + (rh - 1) * k / 5; ax = (x - o) + (o + o2) * k / 5; bx = (x + w + o) - (o + o2) * k / 5; dd = d - o + (dm - d + o) * k / 5
            sc.d.line([sc.P(ax, dd, z), sc.P(bx, dd, z)], fill=(84, 82, 102))
    sc.jobs.append((d, f))


def main():
    sc = Scene(70, 50, 52); sc.img.paste((120, 150, 90), (0, 0, sc.img.size[0], sc.img.size[1])); sc.d = ImageDraw.Draw(sc.img)
    sc.floor(lambda x, d: (116, 140, 84) if (int(x // 4) + int(d // 4)) % 2 == 0 else (108, 132, 78))
    house(sc, 14, 14, 40, 22, 16); sc.run()
    out = os.path.join(OUT, 'prop_house.png'); sc.img.save(out); sc.img.resize((sc.img.size[0] * 3, sc.img.size[1] * 3), Image.NEAREST).save(out.replace('.png', '_x3.png')); print(out, sc.img.size)
if __name__ == '__main__': main()
