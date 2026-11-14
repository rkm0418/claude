#!/usr/bin/env python3
"""art/variants/*.txt 시안을 사물별 A/B/C 비교 이미지로 만든다.  사용: python3 tools/variants.py batch1
출력: art/out/variants_<묶음>.png"""
import glob, os, sys
from PIL import Image, ImageDraw
import boxes, render

def main(batch):
    root = render.ROOT
    pal = render.load_palette()
    found = {}
    bx = os.path.join(root, 'variants', f'{batch}_boxes.txt')
    px = os.path.join(root, 'variants', f'{batch}_pixels.txt')
    if os.path.exists(bx):
        for it in boxes.load_boxes(bx):
            found[it['name']] = boxes.build(it, pal)
    if os.path.exists(px):
        for sp in render.load_sprites(px):
            found[sp['name']] = render.to_image(sp, pal, px)
    groups = {}
    for name, im in found.items():
        obj, _, v = name.rpartition('_')
        groups.setdefault(obj, {})[v] = im
    S, PAD, LAB = 8, 14, 16
    cw = max(i.width for i in found.values()) * S + PAD * 2
    ch = max(i.height for i in found.values()) * S + PAD * 2 + LAB
    cols = max(len(g) for g in groups.values())
    sheet = Image.new('RGBA', (cw * cols, ch * len(groups)), (74, 68, 80, 255))
    d = ImageDraw.Draw(sheet)
    for r, (obj, g) in enumerate(groups.items()):
        for c, v in enumerate(sorted(g)):
            im = g[v]
            big = im.resize((im.width * S, im.height * S), Image.NEAREST)
            x, y = c * cw, r * ch
            sheet.alpha_composite(big, (x + (cw - big.width) // 2, y + ch - LAB - PAD - big.height))
            d.text((x + PAD, y + ch - LAB), f'{obj}  {v}', fill=(236, 228, 210, 255))
        if r:
            d.line([(0, r * ch), (sheet.width, r * ch)], fill=(110, 102, 118, 255))
    out = os.path.join(root, 'out', f'variants_{batch}.png')
    sheet.save(out)
    print(f'{len(found)}개 시안 → {out}')

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'batch1')
