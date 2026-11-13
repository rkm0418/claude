/* 오답노트 백업 파일(.json) 내보내기 / 불러오기. API 키 같은 설정은 넣지 않음 */
import { notes } from "./db.js";
import { saveFile } from "./util.js";

const MARK = "오답노트-백업";
const isImg = s => typeof s === "string" && s.startsWith("data:image/");

/** 백업 파일로 저장. ids가 있으면 그 문제들만. 저장한 개수를 돌려줌 */
export async function exportBackup(ids) {
  let all = await notes.all();
  if (ids) all = all.filter(n => ids.has(n.id));
  if (!all.length) throw new Error("내보낼 문제가 없어요.");
  const data = { app: MARK, version: 1, exportedAt: new Date().toISOString(), notes: all };
  const blob = new Blob([JSON.stringify(data)], { type: "application/json" });
  await saveFile(`오답노트_백업_${ids ? "선택_" : ""}${new Date().toISOString().slice(0, 10)}.json`, blob);
  return all.length;
}

const clean = n => {
  const figs = (Array.isArray(n.figs) ? n.figs : []).filter(isImg);
  return {
    id: String(n.id || "n" + Date.now() + Math.random().toString(36).slice(2, 6)),
    t: +n.t || Date.now(),
    cat: [0, 1, 2, 3, 4].includes(+n.cat) ? +n.cat : 1,
    text: String(n.text || ""), tr: String(n.tr || ""), ans: String(n.ans || ""),
    img: isImg(n.img) ? n.img : "",
    qa: (Array.isArray(n.qa) ? n.qa : []).map(x => ({ q: String(x?.q || ""), a: String(x?.a || "") })),
    figs, figs0: Array.isArray(n.figs0) ? n.figs0.filter(isImg) : figs.slice(),
  };
};

/** 백업 파일을 읽어서 검사한 문제 목록으로. 이상하면 오류 */
export async function readBackup(file) {
  let d;
  try { d = JSON.parse(await file.text()) } catch { throw new Error("백업 파일이 아니에요.") }
  if (d?.app !== MARK || !Array.isArray(d.notes)) throw new Error("오답노트 백업 파일이 아니에요.");
  const list = d.notes.filter(n => n && typeof n === "object").map(clean);
  if (!list.length) throw new Error("백업 파일에 문제가 없어요.");
  return list;
}

/** 같은 id는 백업 내용으로 바꾸고, 새 문제는 추가 */
export async function importBackup(list) {
  for (const n of list) await notes.put(n);
}
