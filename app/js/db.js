/* IndexedDB 저장소: 오답노트. 막혀 있으면 메모리로 대신함 */
const mem = { notes: new Map() };
let dbp = null;

function open() {
  if (!dbp) {
    dbp = new Promise((res, rej) => {
      try {
        const r = indexedDB.open("studyNotes", 1);
        r.onupgradeneeded = () => {
          r.result.createObjectStore("notes", { keyPath: "id" });
        };
        r.onsuccess = () => res(r.result);
        r.onerror = () => rej(r.error);
      } catch (e) { rej(e) }
    });
  }
  return dbp;
}

/** 성공하면 {v: 결과}, 실패하면 null */
async function tx(store, mode, fn) {
  try {
    const db = await open();
    return await new Promise((res, rej) => {
      const t = db.transaction(store, mode), rq = fn(t.objectStore(store));
      t.oncomplete = () => res({ v: rq && rq.result });
      t.onerror = () => rej(t.error);
      t.onabort = () => rej(t.error);
    });
  } catch { return null }
}

export const notes = {
  async put(n) { if (!(await tx("notes", "readwrite", s => s.put(n)))) mem.notes.set(n.id, n) },
  async all() { const r = await tx("notes", "readonly", s => s.getAll()); return r ? r.v : [...mem.notes.values()] },
  async del(id) { if (!(await tx("notes", "readwrite", s => s.delete(id)))) mem.notes.delete(id) },
};

