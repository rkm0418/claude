#!/usr/bin/env python3
"""web/ 을 파일 하나(web/yeoksang.html)로 합친다: data.js·game.js 를 안에 넣고, 장면 바로가기 버튼을 단다. 사용: python3 tools/export_web.py && python3 tools/build_single.py"""
import os
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'web'); r = lambda n: open(os.path.join(W, n)).read()
h = r('index.html'); btn = ''.join('<button class="go" data-k="%s">%s</button>' % kv for kv in (('snow', '눈 숲길'), ('lake', '얼음 호수'), ('house', '집 안'), ('park', '놀이공원'), ('reed', '갈대밭'), ('woods', '어두운 숲'), ('ridge', '능선'), ('roofs', '옥상'), ('hall', '복도'), ('tree', '나무 속'), ('cabin', '통나무집'), ('library', '도서관'), ('office', '매표소'), ('snowx', '눈+'), ('lakex', '호수+'), ('parkx', '놀이공원+'), ('reedx', '갈대+'), ('woodsx', '숲+'), ('ridgex', '능선+'), ('roofsx', '옥상+'), ('hallx', '복도+'), ('cabinx', '통나무집+'), ('libraryx', '도서관+'), ('officex', '매표소+'), ('treex', '나무집+')))
css = '<style>#bar{position:fixed;left:6px;top:6px;display:flex;gap:4px;flex-wrap:wrap;max-width:70%}.go,.pv{font:12px sans-serif;color:#cbb;background:#0006;border:1px solid #655;border-radius:6px;padding:5px 8px}</style>'
btn += '<span style="color:#a99;font:12px sans-serif;align-self:center;margin-left:6px">등장</span>' + ''.join('<button class="pv" data-k="%d">%d</button>' % (k, k) for k in range(1, 12))
css = css.replace('</style>', '#bar,#dbg{display:none}body.dev #bar{display:flex}body.dev #dbg{display:block}</style>')
h = h.replace('</body>', '<script>if(/dev/.test(location.hash))document.body.classList.add("dev")</script></body>')
h = h.replace('</head>', css + '</head>').replace('<button id="dbg">', '<div id="bar">' + btn + '</div><button id="dbg">')
h = h.replace('<script src="data.js"></script><script src="game.js"></script>', '<script>' + r('data.js') + '</script><script>' + r('game.js') + '</script><script>document.querySelectorAll(".go").forEach(b=>b.addEventListener("click",e=>{e.stopPropagation();window.__game&&window.__game.start(b.dataset.k)}));document.querySelectorAll(".pv").forEach(b=>b.addEventListener("click",e=>{e.stopPropagation();window.__game&&window.__game.preview(+b.dataset.k)}));</script>')
open(os.path.join(W, 'yeoksang.html'), 'w').write(h); print('web/yeoksang.html', len(h) // 1024, 'KB')
