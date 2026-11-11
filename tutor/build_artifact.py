import base64,sys
t=open('artifact.template.html').read()
for k in ['g5','g7','l4','f4','f6','f8']:
    t=t.replace(f'__{k}__',base64.b64encode(open(f'fonts-subset/{k}.woff2','rb').read()).decode())
open('/tmp/claude-0/artifact.html','w').write(t)
print(len(t))
