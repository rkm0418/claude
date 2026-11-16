#!/usr/bin/env python3
"""웹 엔진용 데이터 묶기: 방 그림·깊이 지도·이동 데이터(house_nav.json)·아이 8방향 스프라이트를 web/data.js 하나로(data URI) 만든다.
사용: python3 tools/render_country_house.py && python3 tools/export_web.py"""
import base64, io, json, os
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, '..', 'maps', 'out'); SPR = os.path.join(HERE, '..', 'art', 'out', 'sprites', 'child8'); WEB = os.path.join(HERE, '..', 'web')
CHILD = (18, 32)                                   # 방 비율에 맞춘 아이 크기(원본 24x42 의 0.75배, 문 높이 42 기준 7살 키)
def uri(im):
    b = io.BytesIO(); im.save(b, 'PNG'); return 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()
def main():
    nav = json.load(open(os.path.join(OUT, 'house_nav.json'))); rooms = {}
    for k, m in nav.items():
        m = dict(m); m['img'] = uri(Image.open(os.path.join(OUT, 'house_%s.png' % k)).convert('RGB')); m['depth'] = uri(Image.open(os.path.join(OUT, 'house_%s_depth.png' % k)).convert('RGB')); m['group'] = 'house'; rooms[k] = m
    for navf in ('dream_nav.json', 'dream_nav_lake.json'):                       # 꿈 구역(구간 여러 장): maps/out/area_<이름>.png
        if not os.path.exists(os.path.join(OUT, navf)): continue
        for k, m in json.load(open(os.path.join(OUT, navf))).items():
            m = dict(m); m['img'] = uri(Image.open(os.path.join(OUT, 'area_%s.png' % k)).convert('RGB')); m['depth'] = uri(Image.open(os.path.join(OUT, 'area_%s_depth.png' % k)).convert('RGB')); m['walk'] = uri(Image.open(os.path.join(OUT, 'area_%s_walk.png' % k)).convert('RGB')); m['group'] = k.split('_')[0]; rooms[k] = m
    man = json.load(open(os.path.join(SPR, 'manifest.json'))); child = {}
    for d in man['directions']:
        for f in man['frames']: child['%s_%s' % (d, f)] = uri(Image.open(os.path.join(SPR, 'child_%s_%s.png' % (d, f))).convert('RGBA').resize(CHILD, Image.NEAREST))
    os.makedirs(WEB, exist_ok=True)
    open(os.path.join(WEB, 'data.js'), 'w').write('window.GAME_DATA = ' + json.dumps({'rooms': rooms, 'child': child, 'childSize': CHILD, 'starts': {'house': {'room': 'living', 'x': 78, 'd': 8}, 'snow': {'room': 'snow_1', 'x': rooms['snow_1']['start'][0], 'd': rooms['snow_1']['start'][1]}, 'lake': {'room': 'lake_1', 'x': rooms['lake_1']['start'][0], 'd': rooms['lake_1']['start'][1]}}}) + ';\n')
    print('web/data.js', os.path.getsize(os.path.join(WEB, 'data.js')) // 1024, 'KB')
if __name__ == '__main__': main()
