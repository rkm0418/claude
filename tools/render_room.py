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
LIGHT_DY = {'wall_light_kr': 14}      # 아래로 빛을 쏘는 벽등은 빛의 중심을 등 아래로 내린다

def cone(img, cx, y0, h=30):
    """벽등 아래로 퍼지는 빛의 부채꼴: 벽 색을 따뜻하게 밝힌다."""
    p = img.load()
    for dy in range(h):
        half = 3 + .5 * dy; a = .38 * (1 - dy / h)
        for x in range(int(cx - half), int(cx + half) + 1):
            y = y0 + dy
            if 0 <= x < img.width and 0 <= y < img.height and p[x, y][3]:
                r, g, b, al = p[x, y]; k = a * (1 - abs(x - cx) / (half + 1))
                p[x, y] = (int(r + (255 - r) * k), int(g + (226 - g) * k), int(b + (160 - b) * k), al)

def render_room(path, scale=1):
    m = R.load_map(path); lib = R.load_library(); lights = R.load_lights(); boxset = set(boxes.load_all(render.ROOT)); bdepth = {it['name']: max(p[2] + p[5] for p in it['parts'] if p[0] == 'box') for it in boxes.load_boxes(os.path.join(render.ROOT, 'boxes.txt'))}
    rows, leg = m['rows'], m['legend']
    tile = lambda ch: leg[ch][0]
    floor_rows = [i for i, r in enumerate(rows) if any(tile(c).startswith('floor') for c in r)]
    wall_rows = [i for i, r in enumerate(rows) if any(tile(c).startswith('wall') for c in r) and i not in floor_rows]
    top_row, mid_row, base_row = wall_rows[0], wall_rows[1], wall_rows[2]
    c0 = min(c for i in floor_rows for c, ch in enumerate(rows[i]) if tile(ch).startswith('floor'))
    c1 = max(c for i in floor_rows for c, ch in enumerate(rows[i]) if tile(ch).startswith('floor'))
    ncols, nrows = c1 - c0 + 1, len(floor_rows)
    W, D = ncols * T, nrows * T
    sky = int(m.get('extra', {}).get('sky_rows', '0')); wallh = WALLH + 16 * sky      # 방지대 위에 하늘 줄을 더 쌓는다
    CW, CH = int(PAD * 2 + W + SK * D), int(PAD * 2 + wallh + SS * D)
    X0, Y0 = PAD, PAD + wallh + SS * D
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
        for Y in range(int(Y0 - SS * D - wallh), int(Y0) + 1):
            z = (Y0 - SS * d) - (Y + .5)
            if not (0 <= z < wallh): continue
            nm, ty = (names['base'], 15 - int(z)) if z < 16 else (names['mid'], 15 - int(z - 16)) if z < 32 else (names['top'], int(wallh - 1 - z))
            r, g, b, a = get(nm, int(d), ty); px[X, Y] = (int(r * .82), int(g * .82), int(b * .86), a)
    # 뒷벽
    by = Y0 - SS * D
    for X in range(int(X0 + SK * D), int(X0 + SK * D + W)):
        x = X + .5 - X0 - SK * D; c = c0 + int(x // T)
        for Y in range(int(by - wallh), int(by)):
            z = by - (Y + .5)
            if z < 16: nm, ty = tile(rows[base_row][c]), 15 - int(z)
            elif z < 32: nm, ty = tile(rows[mid_row][c]), 15 - int(z - 16)
            elif sky and tile(rows[top_row][c]).startswith('wall_rail_top_'): nm, ty = 'wall_rail_top_' + 'abcdef'[(c + 2 * int((z - 32) // 16)) % 6], 15 - int((z - 32) % 16)
            else: nm, ty = tile(rows[top_row][c]), int(wallh - 1 - z)
            if nm in lib: px[X, Y] = get(nm, int(x), ty)
    emitters = []
    def stamp(name, left, bottom):                           # 정면 스프라이트 (왼쪽 아래 모서리 기준)
        sp = lib[name]; img.alpha_composite(sp, (int(round(left)), int(round(bottom - sp.height))))
        if name in lights: emitters.append((left + sp.width / 2, bottom - sp.height / 2 + LIGHT_DY.get(name, 0)) + lights[name])
        return sp
    # 뒷벽의 사물
    for r_i, zb in ((base_row, 0), (mid_row, 16), (top_row, 32)):
        for c in range(c0, c1 + 1):
            for obj in leg[rows[r_i][c]][1]:
                nm, _, lift = obj.partition('^'); sp_ = stamp(nm, X0 + SK * D + (c - c0) * T, by - zb - int(lift or 0))
                if nm == 'wall_light_kr': cone(img, X0 + SK * D + (c - c0) * T + 10, by - zb - int(lift or 0), 30)
    # 왼쪽 벽의 사물: 세로 선은 그대로, 깊이 방향은 SK 배로 눌리고 SS 만큼 올라가는 기울임
    for tok in extra.get('left_add', '').split():
        nm, at = tok.split('@'); dc, _, lift = at.partition('^'); d0 = int(float(dc) * T); sp = lib[nm]
        if nm.endswith('_ls'):                                    # 왼쪽 벽 면에 맞춰 미리 눌러 그린 스프라이트: 가로는 그대로, 한 칸 갈 때마다 1점씩 올라가는 기울임만 준다
            for u in range(sp.width):
                for v in range(sp.height):
                    p = sp.getpixel((u, v))
                    if p[3] == 0: continue
                    X = int(X0 + SK * d0 + u); Y = int(Y0 - SS * d0 - u * SS / SK - int(lift or 0) - (sp.height - 1 - v)) - 1
                    if 0 <= X < CW and 0 <= Y < CH: px[X, Y] = (int(p[0] * .85), int(p[1] * .85), int(p[2] * .88), 255)
            continue
        painted = {}
        for u in range(sp.width):
            for v in range(sp.height):
                p = sp.getpixel((u, v))
                if p[3] == 0 or p[:3] == (26, 22, 32): continue          # 원래 테두리는 빼고, 아래에서 한 겹으로 다시 두른다
                d = d0 + u; X = int(X0 + SK * d); Y = int(Y0 - SS * d - int(lift or 0) - (sp.height - 1 - v)) - 1
                if 0 <= X < CW and 0 <= Y < CH: painted[(X, Y)] = (int(p[0] * .82), int(p[1] * .82), int(p[2] * .86), 255)   # 가로로 눌릴 때 같은 점에 겹치면 나중 것이 남는다
        for (X, Y), col in painted.items(): px[X, Y] = col
        for (X, Y) in list(painted):                        # 눌리면서 사라진 테두리를 바깥에 다시 둘러 준다
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (X + dx, Y + dy)
                if q not in painted and 0 <= q[0] < CW and 0 <= q[1] < CH: px[q] = (26, 22, 32, 255)
    # 바닥의 사물: 뒤(깊이가 큰 쪽)부터 앞으로
    things = []
    for fr, ri in enumerate(floor_rows):
        for c in range(c0, c1 + 1):
            for obj in leg[rows[ri][c]][1]:
                nm, _, lift = obj.partition('^'); d0 = D - T * (fr + 1)
                things.append((-d0, 0 if nm.startswith('rug') else 1, c, nm, int(lift or 0), d0))
    for _, _, c, nm, lift, d0 in sorted(things):
        if nm in bdepth: d0 += max(0, T - bdepth[nm])        # 상자 가구는 칸의 뒤쪽 끝에 붙인다(벽에 맞닿게)
        gx, gy = X0 + (c - c0) * T + SK * d0, Y0 - SS * d0
        if nm == 'ceiling_light':
            emitters.append((gx + 8, gy - 18) + lights[nm]); continue
        sp = lib[nm]
        if nm in boxset:
            img.alpha_composite(sp, (int(round(gx - 1)), int(round(gy - (sp.height - 2) - lift))))
            if nm in lights: emitters.append((gx + 5 + SK * 6, gy - 22 - SS * 6 - lift) + lights[nm])      # 스탠드 갓 근처에서 둥글게 퍼지는 빛
        else: stamp(nm, gx, gy - lift)
    # 앞벽(화면 아래쪽): 낮은 벽 + 출입문 틀. 복도에서 위로 나가면 이 방에서도 계속 위를 보도록, 출입문은 앞벽에 둔다
    fk = extra.get('front_wall')
    if fk:
        LOW, POST = 9, 24
        dx0, dw = [int(v) for v in extra.get('front_door', '0 20').split()]
        for xx in range(int(W + 1)):
            X = int(X0 + xx)
            in_door = dx0 <= xx < dx0 + dw
            post = dx0 <= xx < dx0 + 2 or dx0 + dw - 2 <= xx < dx0 + dw
            top = POST if post else (0 if in_door else LOW)
            for z in range(top):
                Y = int(Y0 + 1 - 1 - z) - 0
                if post: col = (247, 245, 240, 255) if 0 < z < top - 1 and xx not in (dx0, dx0 + dw - 1) else (26, 22, 32, 255)
                elif z == top - 1: col = (156, 143, 138, 255)
                else: col = get(f'wall_base_{fk}', xx, 15 - z)
                px[X, Y] = col
            if in_door and not post:                        # 문턱과 발판
                for z in range(2): px[X, int(Y0) - z] = (115, 86, 62, 255) if z == 0 else (156, 143, 138, 255)
        glow = extra.get('front_glow')
        if glow:
            emitters.append((X0 + dx0 + dw / 2, Y0 - 8, 54, float(glow), (232, 207, 106)))
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
