import base64,re
d=lambda p:base64.b64encode(open(p,'rb').read()).decode()
t=open('artifact.template.html').read()
for k in ['g5','g7','l4','f4','f6','f8']:
    t=t.replace(f'__{k}__',d(f'fonts-subset/{k}.woff2'))
css=open('katex/katex.min.css').read()
css=re.sub(r'src:url\(fonts/([^)]+)\.woff2\) format\("woff2"\),url\([^)]+\) format\("woff"\),url\([^)]+\) format\("truetype"\)',
           lambda m:'src:url(data:font/woff2;base64,'+d(f'katex/fonts/{m.group(1)}.woff2')+') format("woff2")',css)
assert 'fonts/' not in css
t=t.replace('/*__KATEX_CSS__*/',css)
open('/tmp/claude-0/artifact.html','w').write(t)
print(len(t))
