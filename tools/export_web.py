#!/usr/bin/env python3
"""웹 엔진용 데이터 묶기: 방 그림·깊이 지도·이동 데이터(house_nav.json)·아이 8방향 스프라이트를 web/data.js 하나로(data URI) 만든다.
사용: python3 tools/render_country_house.py && python3 tools/export_web.py"""
import base64, io, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, '..', 'maps', 'out'); SPR = os.path.join(HERE, '..', 'art', 'out', 'sprites', 'child8'); WEB = os.path.join(HERE, '..', 'web')
CHILD = (14, 24)                                   # 방 비율에 맞춘 아이 크기(원본 24x42 의 0.75배, 문 높이 42 기준 7살 키)
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
    if os.path.exists(os.path.join(OUT, 'tree_nav.json')):                       # 건물 안(나무 속 방)
        for k, m in json.load(open(os.path.join(OUT, 'tree_nav.json'))).items():
            m = dict(m); m['img'] = uri(Image.open(os.path.join(OUT, 'tree_%s.png' % k)).convert('RGB')); m['depth'] = uri(Image.open(os.path.join(OUT, 'tree_%s_depth.png' % k)).convert('RGB')); m['group'] = 'tree'; rooms[k] = m
    if os.path.exists(os.path.join(OUT, 'bld_nav.json')):                         # 건물 안: 통나무집·도서관·매표소
        for k, m in json.load(open(os.path.join(OUT, 'bld_nav.json'))).items():
            m = dict(m); m['img'] = uri(Image.open(os.path.join(OUT, 'bld_%s.png' % k)).convert('RGB')); m['depth'] = uri(Image.open(os.path.join(OUT, 'bld_%s_depth.png' % k)).convert('RGB')); m['group'] = 'bld'; rooms[k] = m
    for wnav in ('world_nav.json', 'more_nav.json'):                              # 모험 구역(불규칙 지형) + 테마별 추가 공간
      if os.path.exists(os.path.join(OUT, wnav)):
        for k, m in json.load(open(os.path.join(OUT, wnav))).items():
            m = dict(m); m['img'] = uri(Image.open(os.path.join(OUT, 'world_%s.png' % k)).convert('RGB')); m['depth'] = uri(Image.open(os.path.join(OUT, 'world_%s_depth.png' % k)).convert('RGB')); m['walk'] = uri(Image.open(os.path.join(OUT, 'world_%s_walk.png' % k)).convert('RGB')); m['group'] = 'world'; rooms[k] = m
    from puzzles_data import VIEWS                                               # 두 시선 퍼즐: 건물 안 방의 옛 사물·퍼즐을 대체
    for k, v in VIEWS.items():
        if k in rooms: rooms[k]['objects'] = []; rooms[k]['puzzle'] = None; rooms[k]['views'] = v['views']; rooms[k]['vflag'] = v['flag']; rooms[k]['vreq'] = v.get('req')
    for k in ('lake_2', 'snow_3'):
        if k in rooms: rooms[k]['mood'] = 'dark'                                  # 추격 구간: 어둡고 꺼림칙한 분위기
    for name, m in rooms.items():                                              # 다른 맵으로 가는 맨홀: 도착 맵의 짝 맨홀 곁(없으면 시작점)에 선다
        for e in m['exits']:
            if e.get('spawn') is None and e.get('to') in rooms:
                tgt = rooms[e['to']]; back = [x for x in tgt['exits'] if x.get('to') == name and (x.get('manhole') or x.get('door'))]
                e['spawn'] = ([round((back[0]['zone'][0] + back[0]['zone'][1]) / 2, 1), round(back[0]['zone'][3] + 6 if back[0].get('indoor') else back[0]['zone'][2] - 6, 1)] if back[0].get('door') else [round((back[0]['zone'][0] + back[0]['zone'][1]) / 2 - 10, 1), round((back[0]['zone'][2] + back[0]['zone'][3]) / 2 + 2, 1)]) if back else list(tgt['start'])
    NAMES = {'living': '거실', 'kitchen': '주방', 'bedroom': '침실', 'study': '서재', 'tree_main': '나무집 안', 'tree_back': '나무집 뒷방', 'cabin_main': '통나무집 안', 'cabin_back': '통나무집 뒷방', 'library': '도서관', 'office': '매표소', 'park': '놀이공원', 'reed': '갈대밭', 'woods': '어두운 숲', 'ridge': '능선', 'roofs': '옥상', 'hall': '복도', 'snow_h': '눈 숲길 집', 'snow_5': '눈 숲길 5'}
    ids_p = os.path.join(HERE, 'scene_ids.json'); ids = json.load(open(ids_p)) if os.path.exists(ids_p) else {}              # 장면 번호: 한 번 붙이면 고정, 새 장면만 뒤 번호를 받는다
    for k in rooms:
        if k not in ids: ids[k] = max(ids.values(), default=0) + 1
    json.dump(ids, open(ids_p, 'w'), ensure_ascii=False, indent=0)
    for k, m in rooms.items():
        m['no'] = ids[k]
        if not m.get('label'): m['label'] = NAMES.get(k) or (('눈 숲길 ' + k.split('_')[-1]) if k.startswith('snow_') else ('얼음 호수 ' + k.split('_')[-1]) if k.startswith('lake_') else k)
    rows = ['| # | 키 | 이름 | 종류 | 연결 |', '|---|----|------|------|------|']
    for k, m in sorted(rooms.items(), key=lambda kv: ids[kv[0]]):
        ex = ', '.join('%s%s%s' % (e.get('dir') or '', '→' + e['to'] if e.get('to') else '→(막힘)', '(이어붙이기)' if e.get('type') == 'pan' else '') for e in m.get('exits', []))
        rows.append('| #%03d | %s | %s | %s | %s |' % (ids[k], k, m['label'], ('통로 ' if m.get('kind') == 'passage' else '') + (m.get('shape') or m.get('group') or ''), ex))
    open(os.path.join(HERE, '..', 'docs', 'scene-index.md'), 'w').write('# 장면 번호표\n\n게임 화면 위쪽의 `#번호`로 장면을 가리킵니다. 번호는 한번 정하면 바뀌지 않습니다(장면을 빼도 다른 번호는 그대로).\n\n' + '\n'.join(rows) + '\n')
    man = json.load(open(os.path.join(SPR, 'manifest.json'))); child = {}
    for d in man['directions']:
        for f in man['frames']: child['%s_%s' % (d, f)] = uri(Image.open(os.path.join(SPR, 'child_%s_%s.png' % (d, f))).convert('RGBA').resize(CHILD, Image.NEAREST))
    os.makedirs(WEB, exist_ok=True)
    open(os.path.join(WEB, 'data.js'), 'w').write('window.GAME_DATA = ' + json.dumps({'adult': uri(Image.open(os.path.join(SPR, '..', 'shadow_adult.png')).convert('RGBA').resize((13, 38), Image.NEAREST)), 'rooms': rooms, 'chaser': {f: uri(Image.open(os.path.join(SPR, '..', 'chaser%s.png' % ('' if f == 'idle' else '_' + f))).convert('RGBA')) for f in ('idle', 'w1', 'w2', 'w3', 'w4')}, 'child': child, 'childSize': CHILD, 'starts': {'house': {'room': 'living', 'x': 78, 'd': 8}, 'snow': {'room': 'snow_1', 'x': rooms['snow_1']['start'][0], 'd': rooms['snow_1']['start'][1]}, 'lake': {'room': 'lake_1', 'x': rooms['lake_1']['start'][0], 'd': rooms['lake_1']['start'][1]}, **{k: {'room': r, 'x': rooms[r]['start'][0], 'd': rooms[r]['start'][1]} for k, r in (('park', 'park'), ('reed', 'reed'), ('woods', 'woods'), ('ridge', 'ridge'), ('roofs', 'roofs'), ('hall', 'hall'), ('tree', 'tree_main'), ('cabin', 'cabin_main'), ('library', 'library'), ('office', 'office')) if r in rooms}, **{th + 'x': {'room': th + 'x01', 'x': rooms[th + 'x01']['start'][0], 'd': rooms[th + 'x01']['start'][1]} for th in ('snow', 'lake', 'park', 'reed', 'woods', 'ridge', 'roofs', 'hall', 'cabin', 'library', 'office', 'tree') if th + 'x01' in rooms}}}) + ';\n')
    print('web/data.js', os.path.getsize(os.path.join(WEB, 'data.js')) // 1024, 'KB')
if __name__ == '__main__': main()
