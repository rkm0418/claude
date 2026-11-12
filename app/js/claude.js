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
수식 규칙: 수식은 표준 LaTeX로 쓴다. 인라인 수식은 $ 하나로, 블록 수식은 $$ 두 개로 감싼다. 수식 안에 한글을 직접 쓰지 말고 필요하면 \\text{한글}로 감싼다. 유니코드 수학기호(×, ÷, √, ² 등)를 쓰지 말고 \\frac, \\sqrt, \\times, \\div 같은 정확한 LaTeX 명령만 쓴다.
첫 번째 답변만 JSON 하나로 출력한다(코드블록 금지, JSON 문자열 안의 백슬래시는 \\\\처럼 두 개로 이스케이프):
{"reply":"질문에 대한 답","problem":"사진 문제일 때만: 인쇄된 문제 본문과 보기만 수식 포함 글로 옮긴 것. 손글씨(풀이, 메모, 체크, 밑줄, 동그라미)는 절대 넣지 않는다","figures":[{"x":0.1,"y":0.2,"w":0.4,"h":0.3}]}
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
      body: JSON.stringify({ model, max_tokens: 1500, system: buildSystem(), messages }),
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
