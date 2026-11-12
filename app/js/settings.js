/* 설정: API 키·모델·학년·말투 (이 기기의 localStorage에만 저장) */
import { $, store, showDialog } from "./util.js";

const KEYS = { apiKey: "ft.apiKey", model: "ft.model", level: "ft.level", style: "ft.style" };
const DEFAULTS = { apiKey: "", model: "claude-haiku-5-5", level: "중학생", style: "다정하고 친근한 반말 선생님" };

export const getSettings = () => Object.fromEntries(Object.entries(KEYS).map(([k, key]) => [k, store.get(key, DEFAULTS[k])]));

export function openSettings() { showDialog($("setDlg")) }

export function initSettings({ onFaceEdit }) {
  const s = getSettings();
  for (const k of Object.keys(KEYS)) {
    const el = $(k);
    el.value = s[k];
    if (el.value !== s[k]) el.value = DEFAULTS[k]; // 목록에 없는 값이면 기본값
    el.onchange = el.oninput = () => store.set(KEYS[k], el.value.trim());
  }
  $("btnSet").onclick = openSettings;
  $("setClose").onclick = () => $("setDlg").close();
  $("btnFace").onclick = () => { $("setDlg").close(); onFaceEdit() };
}
