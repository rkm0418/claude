/* 앱 시작: 모듈 연결 */
import { $, initButtonEffects, initFullscreen } from "./util.js";
import { initCharacter, loadSavedFace } from "./character.js";
import { initFaceEditor, openFaceEditor } from "./face.js";
import { initSettings } from "./settings.js";
import { initDrawer } from "./drawer.js";
import { initSession, startSession } from "./session.js";
import { initNotes } from "./notes.js";

initButtonEffects();
initFullscreen($("btnFull"));
initCharacter();
initFaceEditor();
initSettings({ onFaceEdit: openFaceEditor });
initDrawer({ onStart: startSession });
initSession();
initNotes();
$("emptyHead").onclick = openFaceEditor;
loadSavedFace();

if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(() => {});
