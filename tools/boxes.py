#!/usr/bin/env python3
"""art/boxes.txt 의 상자 부품을 3/4 시점 스프라이트로 만든다.  사용: python3 tools/boxes.py
출력: art/out/sprites/<이름>.png, art/out/sheet_boxes.png"""
import math, os, re, sys
from PIL import Image, ImageDraw
import render

OUTLINE = (26, 22, 32, 255)
SK, SS = 0.5, 0.5   # 깊이 1당 화면에서 (오른쪽 SK, 위쪽 SS)만큼 이동 = 비스듬한 시점. SK=0 이면 옆면 없이 앞면+윗면만 보인다

def load_boxes(path):
    items, cur = [], None
    for n, raw in enumerate(open(path, encoding='utf-8'), 1):
        line = raw.split('#')[0].rstrip() if not raw.startswith('[') else raw.rstrip()
        if not line.strip():
            continue
        m = re.match(r'^\[(\w+)\]\s*(.*)$', line)
        if m:
            cur = {'name': m.group(1), 'desc': m.group(2), 'parts': []}
            items.append(cur)
            continue
        p = line.split()
        if p[0] == 'box' and len(p) in (8, 9):
            cur['parts'].append(('box', *[float(v) for v in p[1:7]], p[7], len(p) == 9 and p[8] == 'noside'))
        elif p[0] == 'decal' and len(p) == 7:
            cur['parts'].append(('decal', *[float(v) for v in p[1:6]], p[6]))
        else:
            sys.exit(f'{path}:{n}: 읽을 수 없는 줄: {line!r}')
    return items

def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c[:3]) + (255,)

def build(item, pal):
    parts = item['parts']
    maxx = max((p[1] + p[4] + SK * (p[2] + p[5]) if p[0] == 'box' else p[1] + p[4]) for p in parts)
    maxz = max((p[3] + p[6] + SS * (p[2] + p[5]) if p[0] == 'box' else p[3] + p[5] + SS * p[2]) for p in parts)
    W, H = int(math.ceil(maxx)) + 2, int(math.ceil(maxz)) + 2
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    def pt(x, y, z):
        return (1 + x + SK * y, H - 2 - z - SS * y)
    order = sorted(parts, key=lambda p: (-p[2] if p[0] == 'box' else -p[2] + 0.001, p[3] if p[0] == 'box' else p[3]))
    for p in order:
        if p[0] == 'box':
            _, x, y, z, w, dd, h, col, noside = p
            c = pal[col]
            d.polygon([pt(x, y, z + h), pt(x + w, y, z + h), pt(x + w, y + dd, z + h), pt(x, y + dd, z + h)], fill=shade(c, 1.28))   # 윗면
            if not noside and SK:
                d.polygon([pt(x + w, y, z), pt(x + w, y + dd, z), pt(x + w, y + dd, z + h), pt(x + w, y, z + h)], fill=shade(c, 0.66))  # 옆면
            d.polygon([pt(x, y, z), pt(x + w, y, z), pt(x + w, y, z + h), pt(x, y, z + h)], fill=shade(c, 1.0))                     # 앞면
        else:
            _, x, y, z, w, h, col = p
            d.polygon([pt(x, y, z), pt(x + w, y, z), pt(x + w, y, z + h), pt(x, y, z + h)], fill=pal[col])
    src, out = img.load(), img.copy()
    dst = out.load()
    for y in range(H):
        for x in range(W):
            if src[x, y][3] == 0:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < W and 0 <= ny < H and src[nx, ny][3]:
                        dst[x, y] = OUTLINE
                        break
    return out

def load_all(root):
    pal = render.load_palette()
    path = os.path.join(root, 'boxes.txt')
    return {it['name']: build(it, pal) for it in load_boxes(path)}

def main():
    root = render.ROOT
    sprites = load_all(root)
    os.makedirs(os.path.join(root, 'out', 'sprites'), exist_ok=True)
    S, PAD = 6, 10
    cw = max(i.width for i in sprites.values()) * S + PAD * 2
    ch = max(i.height for i in sprites.values()) * S + PAD * 2 + 14
    sheet = Image.new('RGBA', (cw * 5, ch * math.ceil(len(sprites) / 5)), (74, 68, 80, 255))
    dr = ImageDraw.Draw(sheet)
    for i, (name, im) in enumerate(sprites.items()):
        im.save(os.path.join(root, 'out', 'sprites', name + '.png'))
        big = im.resize((im.width * S, im.height * S), Image.NEAREST)
        cx, cy = (i % 5) * cw, (i // 5) * ch
        sheet.alpha_composite(big, (cx + PAD, cy + ch - 14 - PAD - big.height))
        dr.text((cx + PAD, cy + ch - 14), name, fill=(216, 207, 192, 255))
    sheet.save(os.path.join(root, 'out', 'sheet_boxes.png'))
    print(f'boxes: {len(sprites)}개 → art/out/sheet_boxes.png')

if __name__ == '__main__':
    main()
