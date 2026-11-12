import re,subprocess
subprocess.run(['python3','build_artifact.py'],check=True,stdout=subprocess.DEVNULL)
t=open('/tmp/claude-0/artifact.html').read()
def rep(a,b):
    global t
    assert a in t,a[:70]; t=t.replace(a,b,1)
# model/key inputs
t=re.sub(r'<select id="model".*?</select>','<input type="password" id="gkey" placeholder="Gemini API 키 (aistudio.google.com에서 무료 발급)" autocomplete="off" aria-label="Gemini API 키">\n  <input type="text" id="model" value="gemini-2.0-flash" aria-label="Gemini 모델 이름">\n  <div class="note">키는 이 브라우저에만 저장돼요. 모델 이름은 바꿀 수 있어요.</div>',t,count=1,flags=re.S)
# remove artifact sample init
a=t.index('let sample=null, ctl=null;'); b=t.index('function rules(){')
t=t[:a]+'let ctl=null;\n'+t[b:]
# viaSample -> Gemini
a=t.index('async function viaSample'); b=t.index('async function run(')
t=t[:a]+r'''async function viaSample(model, signal){
  const key=$("gkey").value.trim(); store.set("gkey",key); store.set("gmodel",model);
  const contents=[];
  for(let i=0;i<hist.length;i++){
    const m=hist[i], parts=[{text:m.content}];
    if(i===0&&useImg()) parts.unshift({inline_data:{mime_type:"image/jpeg",data:await b64(probBlob)}});
    contents.push({role:m.role==="assistant"?"model":"user",parts});
  }
  const r=await fetch("https://generativelanguage.googleapis.com/v1beta/models/"+encodeURIComponent(model.trim())+":generateContent",{method:"POST",signal,
    headers:{"content-type":"application/json","x-goog-api-key":key},body:JSON.stringify({contents,generationConfig:{temperature:.4}})});
  if(!r.ok){ let d=""; try{ d=(await r.json()).error.message }catch{} const e=new Error(r.status===400&&/API key/i.test(d)?"API 키가 올바르지 않아요.":r.status===429?"요청이 너무 많거나 무료 한도를 넘었어요. 잠시 뒤에 다시 해주세요.":"요청 실패 ("+r.status+") "+d.slice(0,120)); e.code="g"+r.status; throw e }
  const j=await r.json(); const text=(j.candidates?.[0]?.content?.parts||[]).map(p=>p.text||"").join("");
  if(!text) throw new Error("빈 응답이 왔어요. 다시 시도해 주세요.");
  const u=j.usageMetadata; recordUsage(hist.reduce((n,m)=>n+m.content.length,0), text.length, imgTokens(), model, u?(u.totalTokenCount||0):0);
  return text;
}
'''+t[b:]
rep('if(!sample){ $("err").textContent="Claude 연결이 없는 화면이에요. claude.ai에서 이 링크를 열어주세요."; return }','if(!$("gkey").value.trim()){ $("err").textContent="Gemini API 키를 설정에 넣어주세요."; openDrawer(true); return }')
# usage: use real token count when available
rep('function recordUsage(inC,outC,img,model){','function recordUsage(inC,outC,img,model,realTok){')
rep('EV.push({t:Date.now(),k:Math.round((inC+outC)/1.6)+img});','EV.push({t:Date.now(),k:realTok||Math.round((inC+outC)/1.6)+img});')
rep('U.calls++; U.inChars+=inC;','U.real=(U.real||0)+(realTok||0); U.calls++; U.inChars+=inC;')
rep('const estTok=u=>Math.round((u.inChars+u.outChars)/1.6)+(u.imgTok||0);','const estTok=u=>u.real||(Math.round((u.inChars+u.outChars)/1.6)+(u.imgTok||0));')
# unavail text, pickPhoto image checks, key restore
t=t.replace('이 화면에는 Claude 연결이 없어요. claude.ai에서 이 링크를 열어주세요.','')
rep('for(const id of ["tname","level","style","model"])','for(const id of ["tname","level","style","model","gkey"])')
t=t.replace('<title>얼굴 과외쌤</title>','<title>얼굴 과외쌤 (Gemini)</title>',1)
t=t.replace('구독 사용량','Gemini 사용량')
t=t.replace('토큰은 글자 수로 어림한 값이고, claude 구독의 실제 5시간 한도나 남은 양은 이 화면에서 읽을 수 없어요. 정확한 값은 claude.ai 사용량 화면에서 확인하세요.','토큰은 Gemini가 알려준 실제 값이에요. 무료 한도는 Google AI Studio에서 확인하세요.')
t='<!doctype html>\n<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"></head><body>\n'+t+'\n</body></html>'
open('gemini.html','w').write(t); print(len(t))
