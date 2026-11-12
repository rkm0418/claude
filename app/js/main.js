/* 앱 시작: 모듈 연결 */
import { $, initButtonEffects, initFullscreen } from "./util.js";
import { initSettings } from "./settings.js";
import { initDrawer } from "./drawer.js";
import { initSession, startSession } from "./session.js";
import { initNotes } from "./notes.js";

initButtonEffects();
initFullscreen($("btnFull"));
initSettings();
initDrawer({ onStart: startSession });
document.getElementById("dock").inert = true;
initSession();
initNotes();

if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(() => {});
