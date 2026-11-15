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
    extra = m.get('extra', {}); extra_dark = extra.get('recess_dark') == '1'
    rc = m.get('extra', {}).get('recess'); RD = T * int(m.get('extra', {}).get('recess_depth', '1')) if rc else 0                  # 뒷벽이 한 칸 안쪽으로 패인 부분(알코브): `recess: 시작열 끝열`
    ra, rb = [int(v) for v in rc.split()] if rc else (0, -1)
    CW, CH = int(PAD * 2 + W + SK * (D + RD)), int(PAD * 2 + wallh + SS * (D + RD))
    X0, Y0 = PAD, PAD + wallh + SS * (D + RD)
    img = Image.new('RGBA', (CW, CH), (0, 0, 0, 0)); px = img.load()
    tex = lambda name: lib[name].load()
    def get(name, x, y): return tex(name)[x % 16, y % 16]
    extra = m.get('extra', {}); kind = extra.get('left_wall', 'kr')
    names = {'top': f'wall_top_{kind}', 'mid': f'wall_{kind}', 'base': f'wall_base_{kind}'}
    # 바닥: 화면 한 점마다 (x, 깊이 d)를 거꾸로 계산해 타일 무늬를 찍는다
    for Y in range(int(Y0 - SS * (D + RD)), int(Y0) + 1):
        d = (Y0 - Y - .5) / SS
        if not (0 <= d < D + RD): continue
        for X in range(int(X0), int(X0 + W + SK * (D + RD)) + 1):
            x = X + .5 - X0 - SK * d
            if not (0 <= x < W): continue
            if d >= D and not (ra * T <= x < (rb + 1) * T): continue                # 알코브 바닥만 더 안쪽까지
            fr = max(0, nrows - 1 - int(d // T)); ch = rows[floor_rows[fr]][c0 + int(x // T)]
            if not tile(ch).startswith('floor'): continue
            col = get(tile(ch), int(x), 15 - int(d % T))
            if d >= D - 4 and rc and ra * T <= x < (rb + 1) * T and extra_dark:           # 알코브 바닥: 안쪽으로 갈수록 검게 사라진다
                k = max(.14, .6 - (d - (D - 4)) / (RD + 4) * .4); col = (int(col[0] * k), int(col[1] * k), int(col[2] * k), col[3])
            if rc and extra.get('recess_panel') == 'black':                              # 검은 면 앞 바닥: 안쪽(검은 쪽)으로 갈수록 부드럽게 어두워진다
                tt = max(0.0, min(1.0, (d - (D - 30)) / (30 + RD)))
                lo, hi = ra * T, (rb + 1) * T; hx = 1.0 if lo <= x < hi else max(0.0, 1 - (lo - x) / 10 if x < lo else 1 - (x - hi + 1) / 10)
                kk = 1 - .9 * (tt ** 1.3) * hx
                col = (int(col[0] * kk), int(col[1] * kk), int(col[2] * kk), col[3])
            px[X, Y] = col
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
    for X in range(int(X0 + SK * D), int(X0 + SK * D + W + 1)):
        x = X + .5 - X0 - SK * D; c = c0 + int(x // T)
        if ra <= c - c0 <= rb: continue                                   # 알코브 열은 아래에서 더 안쪽에 그린다
        for Y in range(int(by - wallh), int(by)):
            z = by - (Y + .5)
            if z < 16: nm, ty = tile(rows[base_row][c]), 15 - int(z)
            elif z < 32: nm, ty = tile(rows[mid_row][c]), 15 - int(z - 16)
            elif sky and tile(rows[top_row][c]).startswith('wall_rail_top_'): nm, ty = 'wall_rail_top_' + 'abcdef'[(c + 2 * int((z - 32) // 16)) % 6], 15 - int((z - 32) % 16)
            else: nm, ty = tile(rows[top_row][c]), int(wallh - 1 - z)
            if nm in lib: px[X, Y] = get(nm, int(x), ty)
    if rc:
        top_line = int(Y0 - SS * D - wallh)
        def fade_to_bg(c, t):
            t = max(0, min(1, t)); bgc = (8, 6, 12)
            return (int(c[0] * (1 - t) + bgc[0] * t), int(c[1] * (1 - t) + bgc[1] * t), int(c[2] * (1 - t) + bgc[2] * t), c[3])
        by2 = Y0 - SS * (D + RD)                                         # 알코브: 한 칸 안쪽의 뒷벽 + 왼쪽 옆벽
        for X in range(int(X0 + SK * (D + RD) + ra * T), int(min(X0 + SK * (D + RD) + (rb + 1) * T, X0 + SK * D + (rb + 1) * T))):    # 오른쪽은 앞에 있는 바깥 벽이 가리므로 그 왼쪽 끝에서 자른다
            x = X + .5 - X0 - SK * (D + RD); c = c0 + int(x // T)
            for Y in range(int(by2 - wallh) + int(SS * RD), int(by2)):        # 안쪽 면의 윗선은 바깥 벽의 윗선과 같게 맞춘다(벽이 이어지게)
                z = by2 - (Y + .5)
                if z < 16: nm, ty = tile(rows[base_row][c]), 15 - int(z)
                elif z < 32: nm, ty = tile(rows[mid_row][c]), 15 - int(z - 16)
                else: nm, ty = tile(rows[top_row][c]), int(wallh - 1 - z)
                glass = extra_dark and 16 <= z < 32 and c - c0 in (ra, ra + 1)                          # 안쪽 벽에 희미한 푸른 창: 방이 더 이어진다는 단서
                if glass: nm = 'window_kr_l' if c - c0 == ra else 'window_kr_r'
                r_, g_, b_, a_ = get(nm, int(x), ty); px[X, Y] = ((int(r_ * .38), int(g_ * .42), int(b_ * .55), a_) if glass else (int(r_ * .06), int(g_ * .06), int(b_ * .08), a_)) if extra_dark else ((int(r_ * .03), int(g_ * .03), int(b_ * .05), a_) if extra.get('recess_panel') == 'black' else (int(r_ * .9), int(g_ * .9), int(b_ * .92), a_))       # 안쪽은 어둡게(recess_dark면 거의 검정)
        for X in range(int(X0 + ra * T + SK * D), int(X0 + ra * T + SK * (D + RD)) + 1) if extra.get('recess_side') != 'none' else []:     # none: 옆벽은 시점에서 보이지 않으므로 그리지 않는다
            d = (X + .5 - X0 - ra * T) / SK
            if not (D <= d < D + RD): continue
            for Y in range(int(Y0 - SS * (D + RD) - wallh), int(Y0 - SS * D) + 1):
                z = (Y0 - SS * d) - (Y + .5)
                if not (0 <= z < wallh): continue
                nm, ty = (names['base'], 15 - int(z)) if z < 16 else (names['mid'], 15 - int(z - 16)) if z < 32 else (names['top'], int(wallh - 1 - z))
                r_, g_, b_, a_ = get(nm, int(d), ty); fk_ = .04 if extra.get('recess_side') == 'hidden' else (.38 if extra.get('recess_side') == 'dark' else (.25 if extra_dark else .72))
                px[X, Y] = (int(r_ * fk_), int(g_ * fk_), int(b_ * fk_ * 1.1), a_)
                if Y < top_line: px[X, Y] = fade_to_bg(px[X, Y], (top_line - Y) / (SS * RD + 1))
        if rc:                                                              # 검은 안쪽 면과 밝은 벽이 만나는 오른쪽 가장자리를 부드럽게
            xe = int(X0 + SK * D + (rb + 1) * T)
            for dx in range(10):
                kk = .45 + .55 * (dx / 10) ** 1.2
                for Y in range(int(by - wallh), int(by)):
                    X = xe + dx
                    if 0 <= X < CW:
                        r_, g_, b_, a_ = px[X, Y]
                        if a_: px[X, Y] = (int(r_ * kk), int(g_ * kk), int(b_ * kk), a_)
        strip_px = []
    if rc:                                                              # ㄴ 자 벽: 바깥 벽의 왼쪽 끝면(두께)을 안쪽 검은 면 오른쪽에 보이게 한다
            xm = int(X0 + SK * D + (rb + 1) * T); base_y = int(Y0 - SS * D); top_y = int(by - wallh)
            for off in range(int(SK * RD)):
                X = xm - int(SK * RD) + off; sh = 0                                  # 원래 벽 왼쪽에 붙이고, 원래 벽이 이 면보다 앞(위)에 있다
                for Y in range(top_y - (off + 1), base_y):                                     # 윗변만 오른쪽으로 갈수록 올라가는 사선(왼쪽 옆면과 평행), 아랫변은 평평
                    z = base_y - (Y + .5)
                    if z < 16: nm, ty = names['base'], 15 - int(z)
                    elif z < 32: nm, ty = names['mid'], 15 - int(z - 16)
                    else: nm, ty = names['top'], int(wallh - 1 - z)
                    r_, g_, b_, a_ = get(nm, int(off + 5), ty); px[X, Y] = (int(r_ * .34), int(g_ * .34), int(b_ * .38), a_); strip_px.append((X, Y))                       # 조명 뒤에 한 번 더 어둡게 눌러 준다
    emitters = []
    def stamp(name, left, bottom):                           # 정면 스프라이트 (왼쪽 아래 모서리 기준)
        sp = lib[name]; img.alpha_composite(sp, (int(round(left)), int(round(bottom - sp.height))))
        if name in lights: emitters.append((left + sp.width / 2, bottom - sp.height / 2 + LIGHT_DY.get(name, 0)) + lights[name])
        return sp
    # 뒷벽의 사물
    for r_i, zb in ((base_row, 0), (mid_row, 16), (top_row, 32)):
        for c in range(c0, c1 + 1):
            for obj in leg[rows[r_i][c]][1]:
                inr = ra <= c - c0 <= rb; dd = D + RD if inr else D
                nm, _, lift = obj.partition('^'); lx = X0 + SK * dd + (c - c0) * T
                if inr and c - c0 == rb and lib[nm].width > T: lx -= lib[nm].width - T          # 알코브 오른쪽 끝에 문을 붙인다
                sp_ = stamp(nm, lx, Y0 - SS * dd - zb - int(lift or 0))
                if nm == 'wall_light_kr': cone(img, X0 + SK * dd + (c - c0) * T + 10, Y0 - SS * dd - zb - int(lift or 0), 30)
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
            lintel = dx0 <= xx < dx0 + dw and not post
            top = POST if post else (0 if in_door else LOW)
            for z in range(top):
                Y = int(Y0 + 1 - 1 - z) - 0
                if post: col = (247, 245, 240, 255) if 0 < z < top - 1 and xx not in (dx0, dx0 + dw - 1) else (26, 22, 32, 255)
                elif z == top - 1: col = (156, 143, 138, 255)
                else: col = get(f'wall_base_{fk}', xx, 15 - z)
                px[X, Y] = col
            if lintel:
                for z in range(POST - 3, POST): px[X, int(Y0) - z] = (247, 245, 240, 255) if z < POST - 1 else (26, 22, 32, 255)       # 문틀 윗가로대
            if in_door and not post:                        # 문턱과 발판
                for z in range(2): px[X, int(Y0) - z] = (115, 86, 62, 255) if z == 0 else (156, 143, 138, 255)
        glow = extra.get('front_glow')
        if glow:
            emitters.append((X0 + dx0 + dw / 2, Y0 - 8, 54, float(glow), (232, 207, 106)))
    # 조명과 톤
    bg = Image.new('RGBA', img.size, (8, 6, 12, 255)); bg.alpha_composite(img); img = R.shade(bg, emitters, m['ambient'], False)
    p3 = img.load()
    for (X, Y) in strip_px:
        r_, g_, b_, a_ = p3[X, Y]; p3[X, Y] = (int(r_ * .3), int(g_ * .3), int(b_ * .36), a_)
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
