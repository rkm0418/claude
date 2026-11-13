/* Anthropic API를 브라우저에서 직접 호출 */
import { getSettings } from "./settings.js";

const API_URL = "https://api.anthropic.com/v1/messages";

export class ApiError extends Error {
  constructor(code, message) { super(message); this.code = code }
}

/** 시스템 프롬프트: 묻는 것에만 짧게 답하고, 첫 답변만 JSON */
export function buildSystem() {
  const { level, style } = getSettings();
  return `너는 1:1 과외 선생님이다. 학생은 ${level}이고, 말투는 ${style}.
학생이 문제(사진 또는 글)를 올리고, 그 문제에서 궁금한 점을 묻는다. 묻는 것에만 짧고 정확하게 답한다. 요청하지 않았으면 문제 전체를 풀지 않는다. 인사, 맞장구, 칭찬, 격려, 감탄, 되묻기, 반복 설명, 군더더기 말은 절대 쓰지 않는다. 이모지·마크다운 금지.
학생이 문제의 풀이나 설명을 요청하면(예: "풀어줘", "설명해줘", "어떻게 풀어") 답을 다음 순서의 구역으로 나눈다. 각 구역은 그 줄에 제목만 쓴 [사용된 개념], [조건 해석], [풀이 방향], [풀이], [빠른 풀이], [검산], [자주 하는 실수], [한 줄 정리] 순서로 시작한다. [사용된 개념]에는 이 문제에 쓰이는 개념·공식을 한 줄에 하나씩, 줄 맨 앞에 (공식1), (공식2)처럼 번호를 붙여 쓴다. 교과 과정 밖의 공식이면 번호 뒤에 [교과 외]를 붙인다. [조건 해석]에는 문제의 조건을 하나씩 수식이나 말로 해석하고 구하려는 것이 무엇인지 밝히고, [풀이 방향]에는 왜 이 방법을 고르는지 한두 문장, [풀이]에는 단계별 풀이와 결론을 한 단계에 한 줄씩, [빠른 풀이]에는 [풀이]보다 짧고 빠른 방법(교과 과정 밖의 공식이나 요령도 가능)을 쓰고 그런 방법이 없으면 이 구역을 생략한다. [검산]에는 답을 대입하거나 다른 방법으로 확인한 과정, [자주 하는 실수]에는 이 유형에서 학생이 자주 틀리는 점 한두 가지, [한 줄 정리]에는 비슷한 문제를 만났을 때 기억할 핵심 한 문장을 쓴다. 어느 구역의 어느 줄이든 [사용된 개념]에 적은 공식을 실제로 썼으면 그 줄 끝에 (공식1)처럼 해당 번호를 붙여 어디에 썼는지 알 수 있게 한다. 해당 없는 구역은 생략한다. 특정 부분이나 한 단계만 물으면 그것만 짧게 답하고 이 구조를 쓰지 않는다. 이 여덟 제목과 (공식N), [교과 외] 표시 말고는 마크다운 금지.
수식 규칙: 수식은 표준 LaTeX로 쓴다. 인라인 수식은 $ 하나로, 블록 수식은 $$ 두 개로 감싼다. 수식 안에 한글을 직접 쓰지 말고 필요하면 \\text{한글}로 감싼다. 유니코드 수학기호(×, ÷, √, ² 등)를 쓰지 말고 \\frac, \\sqrt, \\times, \\div 같은 정확한 LaTeX 명령만 쓴다.
첫 번째 답변만 JSON 하나로 출력한다(코드블록 금지, JSON 문자열 안의 백슬래시는 \\\\처럼 두 개로 이스케이프):
{"reply":"질문에 대한 답(줄바꿈은 \\n)","problem":"사진 문제일 때만: 인쇄된 문제 본문과 보기만 수식 포함 글로 옮긴 것. 손글씨(풀이, 메모, 체크, 밑줄, 동그라미)는 절대 넣지 않는다","figures":[{"x":0.1,"y":0.2,"w":0.4,"h":0.3}]}
figures: 사진 문제일 때만, 문제에 인쇄된 그림·도형·그래프·표의 위치를 사진 전체 대비 0~1 비율(왼쪽 위 기준 x,y와 너비 w, 높이 h)로 최대 4개. 없으면 빈 배열. 손글씨는 그림으로 치지 않는다.
두 번째 답변부터는 JSON 없이 평문으로만 답한다. 사진이 흐려 읽을 수 없으면 reply에 다시 찍어달라고만 쓴다.`;
}

const toBase64 = blob => new Promise(r => { const f = new FileReader(); f.onload = () => r(String(f.result).split(",")[1]); f.readAsDataURL(blob) });

export async function imageBlock(blob) {
  return { type: "image", source: { type: "base64", media_type: blob.type || "image/jpeg", data: await toBase64(blob) } };
}

/** messages를 보내고 답변 글을 돌려줌 */
export async function callClaude(messages, signal) {
  const { apiKey, model } = getSettings();
  if (!apiKey) throw new ApiError("no_key", "설정에서 API 키를 먼저 넣어주세요.");
  let res;
  try {
    res = await fetch(API_URL, {
      method: "POST", signal,
      headers: {
        "content-type": "application/json",
        "x-api-key": apiKey,
        "anthropic-version": "2023-06-01",
        "anthropic-dangerous-direct-browser-access": "true",
      },
      body: JSON.stringify({ model, max_tokens: 3000, system: buildSystem(), messages }),
    });
  } catch (e) {
    if (e.name === "AbortError") throw e;
    throw new ApiError("network", "인터넷 연결을 확인해 주세요.");
  }
  if (!res.ok) {
    let detail = ""; try { detail = (await res.json()).error?.message || "" } catch {}
    if (res.status === 401 || res.status === 403) throw new ApiError("auth", "API 키가 올바르지 않아요. 설정에서 다시 확인해 주세요.");
    if (res.status === 429 || res.status === 529) throw new ApiError("busy", "요청이 많거나 사용 한도에 걸렸어요. 잠시 뒤에 다시 질문해 주세요.");
    throw new ApiError("http", "요청에 실패했어요 (" + res.status + "). " + detail);
  }
  const data = await res.json();
  return (data.content || []).filter(b => b.type === "text").map(b => b.text).join("");
}

/** 첫 답변(JSON) 해석. 실패하면 통째로 reply로 */
export function parseFirst(text) {
  const m = text.match(/\{[\s\S]*\}/);
  try { const o = JSON.parse(m ? m[0] : text); if (typeof o.reply === "string") return o } catch {}
  return { reply: text, problem: "", figures: [] };
}

/** 이스케이프가 깨진 LaTeX 보정 + 마크다운 기호 제거 */
export function cleanReply(t) {
  return String(t || "")
    .replace(/\x0c/g, "\\f").replace(/\x08/g, "\\b").replace(/\t(?=[a-zA-Z])/g, "\\t").replace(/\r(?=[a-zA-Z])/g, "\\r")
    .replace(/\*\*|__|`+/g, "").replace(/^#+\s*/gm, "").replace(/^\s*[-*]\s+/gm, "· ").trim();
}
