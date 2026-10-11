window.__answers = [];
class MockRec { constructor(){} start(){ const a = window.__answers.shift(); setTimeout(() => { if (this._ab) return; if (a == null) { this.onerror && this.onerror({error:'no-speech'}); this.onend && this.onend(); return; } const r=[{transcript:a}]; r.isFinal=true; this.onresult && this.onresult({resultIndex:0, results:[r]}); this.onend && this.onend(); }, 5); } stop(){} abort(){ this._ab=true; this.onerror && this.onerror({error:'aborted'}); this.onend && this.onend(); } }
window.webkitSpeechRecognition = MockRec;
navigator.mediaDevices.getUserMedia = async () => ({ getTracks: () => [] });
