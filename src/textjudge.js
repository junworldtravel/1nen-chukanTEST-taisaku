/* ---------- 文字入力の判定（共通） ---------- */
var T_C = {
  KOR: ["韓国", "大韓民国", "かんこく", "だいかんみんこく"], PRK: ["北朝鮮", "朝鮮民主主義人民共和国", "きたちょうせん"],
  CHN: ["中国", "中華人民共和国", "ちゅうごく"], MNG: ["モンゴル", "モンゴル国"], MMR: ["ミャンマー"], THA: ["タイ", "タイ王国"],
  VNM: ["ベトナム"], MYS: ["マレーシア"], SGP: ["シンガポール"], IDN: ["インドネシア"], PHL: ["フィリピン"], IND: ["インド"],
  PAK: ["パキスタン"], BGD: ["バングラデシュ"], NPL: ["ネパール"], BTN: ["ブータン"], KAZ: ["カザフスタン"], AFG: ["アフガニスタン"],
  IRN: ["イラン"], IRQ: ["イラク"], KWT: ["クウェート"], SAU: ["サウジアラビア"], ISR: ["イスラエル"], TUR: ["トルコ"],
  ARE: ["アラブ首長国連邦", "あらぶしゅちょうこくれんぽう"]
};
var T_K = {
  KOR: ["ソウル"], PRK: ["平壌", "ピョンヤン", "へいじょう"], CHN: ["北京", "ペキン"], MNG: ["ウランバートル"],
  MMR: ["ネーピードー", "ネピドー"], THA: ["バンコク"], VNM: ["ハノイ"], MYS: ["クアラルンプール"], SGP: ["シンガポール"],
  IDN: ["ジャカルタ"], PHL: ["マニラ"], IND: ["ニューデリー", "デリー"], PAK: ["イスラマバード"], BGD: ["ダッカ"],
  NPL: ["カトマンズ"], BTN: ["ティンプー"], KAZ: ["アスタナ"], AFG: ["カブール"], IRN: ["テヘラン"], IRQ: ["バグダッド"],
  KWT: ["クウェート"], SAU: ["リヤド"], ISR: ["エルサレム"], TUR: ["アンカラ"], ARE: ["アブダビ"]
};
function tnorm(s) {
  s = String(s || "").normalize("NFKC");
  s = s.replace(/[ぁ-ゖ]/g, function (c) { return String.fromCharCode(c.charCodeAt(0) + 0x60); });
  s = s.replace(/[－―‐−\-~〜～]/g, "ー");
  s = s.replace(/[\s、。，．,.!！?？・･「」『』()（）"'”“]/g, "");
  return s.replace(/(デス|ダヨ|ダ|カナ|カモ)$/, "");
}
function lev(a, b) {
  var m = a.length, n = b.length, d = [], i, j;
  for (i = 0; i <= m; i++) { d[i] = [i]; }
  for (j = 0; j <= n; j++) d[0][j] = j;
  for (i = 1; i <= m; i++) for (j = 1; j <= n; j++)
    d[i][j] = Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
  return d[m][n];
}
var T_ALL = [];
Object.keys(T_C).forEach(function (c) { T_C[c].forEach(function (a) { T_ALL.push({ a: tnorm(a), code: c, kind: "c" }); }); });
Object.keys(T_K).forEach(function (c) { T_K[c].forEach(function (a) { T_ALL.push({ a: tnorm(a), code: c, kind: "k" }); }); });
// kind: "c"=国名, "k"=首都 / 戻り値 status: correct | close | wrong | pass | empty
function textJudge(kind, code, input) {
  var t = tnorm(input);
  if (!t) return { status: "empty" };
  if (/^(ワカラナイ|ワカンナイ|ワカリマセン|パス|シラナイ)$/.test(t)) return { status: "pass" };
  var mine = (kind === "c" ? T_C : T_K)[code].map(tnorm);
  if (mine.indexOf(t) >= 0) return { status: "correct" };
  if (T_ALL.some(function (e) { return e.a === t && !(e.code === code && e.kind === kind); })) return { status: "wrong" };
  for (var i = 0; i < mine.length; i++) {
    var a = mine[i], dist = lev(a, t);
    if (a.length >= 3 && (dist <= 1 || (a.length >= 6 && dist <= 2))) return { status: "close" };
  }
  return { status: "wrong" };
}
window.__textJudge = textJudge;
