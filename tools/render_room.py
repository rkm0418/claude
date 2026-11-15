#!/usr/bin/env python3
"""사선 시점의 방 렌더러 (사용자 스케치): 바닥 평행사변형 + 뒷벽 + 왼쪽 벽, 가구는 boxes.py 와 같은 각도.
사용: python3 tools/render_room.py maps/2_child_room_kr.txt   -> maps/out/<이름>_oblique.png
맵 파일 헤더에 `left_wall: kr`(왼쪽 벽 타일 묶음) 과 `left_add: 사물@깊이칸^높이 ...` 를 쓴다."""
import math, os, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render, boxes
import render_maps as R

SK, SS, T, WALLH, PAD = boxes.SK, boxes.SS, 16, 40, 12

def render_room(path, scale=1):
    m = R.load_map(path); lib = R.load_library(); lights = R.load_lights(); boxset = set(boxes.load_all(render.ROOT))
    rows, leg = m['rows'], m['legend']
    tile = lambda ch: leg[ch][0]
    floor_rows = [i for i, r in enumerate(rows) if any(tile(c).startswith('floor') for c in r)]
    wall_rows = [i for i, r in enumerate(rows) if any(tile(c).startswith('wall') for c in r) and i not in floor_rows]
    top_row, mid_row, base_row = wall_rows[0], wall_rows[1], wall_rows[2]
    c0 = min(c for i in floor_rows for c, ch in enumerate(rows[i]) if tile(ch).startswith('floor'))
    c1 = max(c for i in floor_rows for c, ch in enumerate(rows[i]) if tile(ch).startswith('floor'))
    ncols, nrows = c1 - c0 + 1, len(floor_rows)
    W, D = ncols * T, nrows * T
    CW, CH = int(PAD * 2 + W + SK * D), int(PAD * 2 + WALLH + SS * D)
    X0, Y0 = PAD, PAD + WALLH + SS * D
    img = Image.new('RGBA', (CW, CH), (0, 0, 0, 0)); px = img.load()
    tex = lambda name: lib[name].load()
    def get(name, x, y): return tex(name)[x % 16, y % 16]
    extra = m.get('extra', {}); kind = extra.get('left_wall', 'kr')
    names = {'top': f'wall_top_{kind}', 'mid': f'wall_{kind}', 'base': f'wall_base_{kind}'}
    # 바닥: 화면 한 점마다 (x, 깊이 d)를 거꾸로 계산해 타일 무늬를 찍는다
    for Y in range(int(Y0 - SS * D), int(Y0) + 1):
        d = (Y0 - Y - .5) / SS
        if not (0 <= d < D): continue
        for X in range(int(X0), int(X0 + W + SK * D) + 1):
            x = X + .5 - X0 - SK * d
            if not (0 <= x < W): continue
            fr = nrows - 1 - int(d // T); ch = rows[floor_rows[fr]][c0 + int(x // T)]
            if not tile(ch).startswith('floor'): continue
            px[X, Y] = get(tile(ch), int(x), 15 - int(d % T))
    # 왼쪽 벽
    for X in range(int(X0), int(X0 + SK * D) + 1):
        d = (X + .5 - X0) / SK
        if not (0 <= d < D): continue
        for Y in range(int(Y0 - SS * D - WALLH), int(Y0) + 1):
            z = (Y0 - SS * d) - (Y + .5)
            if not (0 <= z < WALLH): continue
            nm, ty = (names['base'], 15 - int(z)) if z < 16 else (names['mid'], 15 - int(z - 16)) if z < 32 else (names['top'], int(WALLH - 1 - z))
            r, g, b, a = get(nm, int(d), ty); px[X, Y] = (int(r * .82), int(g * .82), int(b * .86), a)
    # 뒷벽
    by = Y0 - SS * D
    for X in range(int(X0 + SK * D), int(X0 + SK * D + W)):
        x = X + .5 - X0 - SK * D; c = c0 + int(x // T)
        for Y in range(int(by - WALLH), int(by)):
            z = by - (Y + .5)
            if z < 16: nm, ty = tile(rows[base_row][c]), 15 - int(z)
            elif z < 32: nm, ty = tile(rows[mid_row][c]), 15 - int(z - 16)
            else: nm, ty = tile(rows[top_row][c]), int(WALLH - 1 - z)
            if nm in lib: px[X, Y] = get(nm, int(x), ty)
    emitters = []
    def stamp(name, left, bottom):                           # 정면 스프라이트 (왼쪽 아래 모서리 기준)
        sp = lib[name]; img.alpha_composite(sp, (int(round(left)), int(round(bottom - sp.height))))
        if name in lights: emitters.append((left + sp.width / 2, bottom - sp.height / 2) + lights[name])
        return sp
    # 뒷벽의 사물
    for r_i, zb in ((base_row, 0), (mid_row, 16), (top_row, 32)):
        for c in range(c0, c1 + 1):
            for obj in leg[rows[r_i][c]][1]:
                nm, _, lift = obj.partition('^'); stamp(nm, X0 + SK * D + (c - c0) * T, by - zb - int(lift or 0))
    # 왼쪽 벽의 사물: 세로 선은 그대로, 깊이 방향은 SK 배로 눌리고 SS 만큼 올라가는 기울임
    for tok in extra.get('left_add', '').split():
        nm, at = tok.split('@'); dc, _, lift = at.partition('^'); d0 = int(dc) * T; sp = lib[nm]
        for u in range(sp.width):
            for v in range(sp.height):
                p = sp.getpixel((u, v))
                if p[3] == 0: continue
                d = d0 + u; X = int(X0 + SK * d); Y = int(Y0 - SS * d - int(lift or 0) - (sp.height - 1 - v)) - 1
                if 0 <= X < CW and 0 <= Y < CH: px[X, Y] = (int(p[0] * .82), int(p[1] * .82), int(p[2] * .86), 255)
    # 바닥의 사물: 뒤(깊이가 큰 쪽)부터 앞으로
    things = []
    for fr, ri in enumerate(floor_rows):
        for c in range(c0, c1 + 1):
            for obj in leg[rows[ri][c]][1]:
                nm, _, lift = obj.partition('^'); d0 = D - T * (fr + 1)
                things.append((-d0, 0 if nm.startswith('rug') else 1, c, nm, int(lift or 0), d0))
    for _, _, c, nm, lift, d0 in sorted(things):
        gx, gy = X0 + (c - c0) * T + SK * d0, Y0 - SS * d0
        if nm == 'ceiling_light':
            emitters.append((gx + 8, gy - 18) + lights[nm]); continue
        sp = lib[nm]
        if nm in boxset: img.alpha_composite(sp, (int(round(gx - 1)), int(round(gy - (sp.height - 2) - lift))))
        else: stamp(nm, gx, gy - lift)
    # 조명과 톤
    bg = Image.new('RGBA', img.size, (8, 6, 12, 255)); bg.alpha_composite(img); img = R.shade(bg, emitters, m['ambient'], False)
    if m['tone']:
        p2 = img.load()
        for y in range(img.height):
            for x in range(img.width):
                r, g, b, a = p2[x, y]; p2[x, y] = (r * m['tone'][0] // 255, g * m['tone'][1] // 255, b * m['tone'][2] // 255, a)
    return img.resize((img.width * scale, img.height * scale), Image.NEAREST)

if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'maps/2_child_room_kr.txt'
    out = os.path.join(os.path.dirname(path), 'out', os.path.splitext(os.path.basename(path))[0] + '_oblique.png')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    render_room(path, int(sys.argv[2]) if len(sys.argv) > 2 else 5).save(out); print(out)
