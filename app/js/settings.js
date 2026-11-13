/* 설정: API 키·모델·학년·말투 (이 기기의 localStorage에만 저장) */
import { $, store, showDialog, closeDialog } from "./util.js";
import { swipeSelect } from "./picker.js";

const KEYS = { apiKey: "ft.apiKey", model: "ft.model", level: "ft.level", style: "ft.style" };
const DEFAULTS = { apiKey: "", model: "claude-haiku-5-5", level: "고등학생", style: "차분한 존댓말 선생님" };

export const getSettings = () => Object.fromEntries(Object.entries(KEYS).map(([k, key]) => [k, store.get(key, DEFAULTS[k])]));

export function openSettings() { showDialog($("setDlg")) }

export function initSettings() {
  const s = getSettings();
  for (const k of Object.keys(KEYS)) {
    const el = $(k);
    el.value = s[k];
    if (el.value !== s[k]) el.value = DEFAULTS[k]; // 목록에 없는 값이면 기본값
    el.onchange = el.oninput = () => store.set(KEYS[k], el.value.trim());
  }
  // 목록에서 누르는 대신 위아래로 쓸어서 고름
  swipeSelect($("model"), "모델 (위아래로 쓸어서 선택)");
  swipeSelect($("level"), "학년 (위아래로 쓸어서 선택)");
  swipeSelect($("style"), "말투 (위아래로 쓸어서 선택)");
  $("btnSet").onclick = openSettings;
  $("setClose").onclick = () => closeDialog($("setDlg"));
}
