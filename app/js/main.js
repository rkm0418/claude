/* 앱 시작: 모듈 연결 */
import { $, initButtonEffects, initFullscreen, initDialogs } from "./util.js";
import { initSettings } from "./settings.js";
import { initDrawer } from "./drawer.js";
import { initSession, startSession } from "./session.js";
import { initNotes } from "./notes.js";
import { initChips } from "./rich.js";

initButtonEffects();
initDialogs();
initFullscreen($("btnFull"));
initSettings();
initDrawer({ onStart: startSession });
document.getElementById("dock").inert = true;
initSession();
initNotes();
initChips();

if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(() => {});
