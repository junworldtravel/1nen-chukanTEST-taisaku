import sys, asyncio, json
from playwright.async_api import async_playwright
D = sys.argv[1]
MOCK = r"""
window.__QUIZ_FAST = true;
window.__answers = [];
window.__recStarts = 0;
class MockRec {
  constructor(){ this.lang=''; }
  start(){
    window.__recStarts++;
    const a = window.__answers.shift();
    setTimeout(() => {
      if (this._aborted) return;
      if (a === undefined || a === null) { this.onerror && this.onerror({error:'no-speech'}); this.onend && this.onend(); return; }
      if (a === '__PASSBTN__') { document.getElementById('passBtn').click(); return; }
      const alts = Array.isArray(a) ? a : [a];
      const r = alts.map(t => ({transcript: t, confidence: .9}));
      r.isFinal = true;
      this.onresult && this.onresult({resultIndex: 0, results: [r]});
      this.onend && this.onend();
    }, 5);
  }
  stop(){ }
  abort(){ this._aborted = true; this.onerror && this.onerror({error:'aborted'}); this.onend && this.onend(); }
}
window.webkitSpeechRecognition = MockRec; window.SpeechRecognition = MockRec;
navigator.mediaDevices.getUserMedia = async () => ({ getTracks: () => [] });
"""
JUDGE_CASES = [
 ("c","KOR",["韓国"],True), ("c","KOR",["かんこく"],True), ("c","KOR",["大韓民国です"],True), ("c","KOR",["北朝鮮"],False),
 ("c","PRK",["北朝鮮"],True), ("c","PRK",["きたちょうせん"],True),
 ("c","IND",["インドネシア"],False), ("c","IDN",["インドネシア"],True), ("c","IND",["インド"],True), ("c","IDN",["インド"],False),
 ("c","THA",["たい"],True), ("c","THA",["鯛"],True), ("c","THA",["タイ"],True),
 ("c","IRN",["要らん"],True), ("c","IRN",["イラク"],False), ("c","IRQ",["イラク"],True),
 ("c","BGD",["バングラディシュ"],True), ("c","BTN",["ブータン"],True), ("c","SAU",["サウジアラビアです"],True),
 ("c","KWT",["クウェート"],True), ("c","SGP",["シンガポール"],True), ("c","TUR",["トルコ"],True), ("c","ISR",["イスラエル"],True),
 ("c","CHN",["中国"],True), ("c","CHN",["ちゅうごく"],True), ("c","MNG",["モンゴル"],True), ("c","MMR",["ミャンマー"],True),
 ("c","VNM",["ベトナム"],True), ("c","MYS",["マレーシア"],True), ("c","PHL",["フィリピン"],True), ("c","PAK",["パキスタン"],True),
 ("c","NPL",["ネパール"],True), ("c","KAZ",["カザフスタン"],True), ("c","AFG",["アフガニスタン"],True),
 ("k","KOR",["ソウル"],True), ("k","PRK",["平壌"],True), ("k","PRK",["ピョンヤン"],True), ("k","CHN",["北京"],True), ("k","CHN",["ペキン"],True),
 ("k","CHN",["ソウル"],False), ("k","MMR",["ネピドー"],True), ("k","MMR",["ネーピードー"],True), ("k","IND",["デリー"],True),
 ("k","IND",["ニューデリー"],True), ("k","THA",["万国"],True), ("k","THA",["バンコク"],True), ("k","KWT",["クウェート市"],True),
 ("k","BTN",["ティンプー"],True), ("k","BTN",["チンプー"],True), ("k","SGP",["シンガポール"],True), ("k","KAZ",["アスタナ"],True),
 ("k","MNG",["ウランバートル"],True), ("k","VNM",["ハノイ"],True), ("k","MYS",["クアラルンプール"],True), ("k","IDN",["ジャカルタ"],True),
 ("k","PHL",["マニラ"],True), ("k","PAK",["イスラマバード"],True), ("k","BGD",["ダッカ"],True), ("k","NPL",["カトマンズ"],True),
 ("k","AFG",["カブール"],True), ("k","IRN",["テヘラン"],True), ("k","IRQ",["バグダッド"],True), ("k","SAU",["リヤド"],True),
 ("k","ISR",["エルサレム"],True), ("k","TUR",["アンカラ"],True), ("k","IRQ",["テヘラン"],False),
 ("c","IDN",["インド","インドネシア"],True),
]
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
        pg = await b.new_page(viewport={"width": 393, "height": 852}, device_scale_factor=2)
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.add_init_script(MOCK)
        await pg.goto("file://" + D + "/site/map.html")
        await pg.wait_for_function("!document.getElementById('startBtn').disabled", timeout=90000)
        # 1) judge unit tests
        bad = []
        for kind, code, alts, exp in JUDGE_CASES:
            r = await pg.evaluate("([k,c,a]) => window.__judge(k,c,a)", [kind, code, alts])
            got = r["status"] == "hit" and r["correct"]
            if got != exp: bad.append((kind, code, alts, exp, r))
        print("judge cases:", len(JUDGE_CASES), "failures:", len(bad)); [print("  FAIL", x) for x in bad]
        for kind, alts, exp in [("c",["わからない"],"pass"),("c",["えーと"],"none"),("c",[],"none")]:
            r = await pg.evaluate("([k,a]) => window.__judge(k,'KOR',a)", [kind, alts]); print("  status", alts, r["status"], "OK" if r["status"]==exp else "FAIL")
        await pg.screenshot(path=D + "/v2_voice_start.png", full_page=True)
        # 2) full run ①→㉔ with scripted answers
        items = json.load(open(D + "/out/whitemap_order.json"))
        script, expect = [], {}
        for o in items:
            n = o["no"]
            if n % 6 == 0:      # 国名まちがい、首都正解
                script += [["ちがう国", "イラク"] if o["code"]!="IRQ" else ["トルコ"], [o["capital"]]]; expect[n] = (False, True)
            elif n % 6 == 1:    # 1回聞き取れず→国名正解、首都「わからない」
                script += [None, [o["country"]], ["わからない"]]; expect[n] = (True, False)
            elif n == 5:        # わからないボタン → 首都は正解
                script += ["__PASSBTN__", [o["capital"]]]; expect[n] = (False, True)
            elif n == 10:       # 3回聞き取れず→ボタンで○、首都正解
                script += [None, ["えーと"], None, [o["capital"]]]; expect[n] = ("manualOK", True)
            else:
                script += [[o["country"]], [o["capital"]]]; expect[n] = (True, True)
        await pg.evaluate("a => { window.__answers = a; }", script)
        await pg.click("#startBtn")
        # handle manual panel when it appears
        for _ in range(400):
            await pg.wait_for_timeout(50)
            if await pg.is_visible("#manual"):
                await pg.click("#manOk")
            if await pg.is_visible("#resCard"): break
        st = await pg.evaluate("window.__quizState()")
        res = st["res"]; ok = True
        for o in items:
            n = str(o["no"]); e = expect[o["no"]]
            gc, gk = res.get(n, {}).get("c", {}).get("ok"), res.get(n, {}).get("k", {}).get("ok")
            ec = True if e[0] == "manualOK" else e[0]
            if gc != ec or gk != e[1]: ok = False; print("  MISMATCH", n, o["country"], (gc, gk), "expected", (ec, e[1]), res.get(n))
        print("full run finished:", await pg.is_visible("#resCard"), "| all 24 judged as expected:", ok, "| answers left:", await pg.evaluate("window.__answers.length"))
        print("score shown:", await pg.inner_text("#rc"), "/", await pg.inner_text("#rn"), "国名;", await pg.inner_text("#rk"), "首都")
        await pg.screenshot(path=D + "/v2_voice_results.png", full_page=True)
        # 3) retry wrong only
        wrong = [o for o in items if not (res[str(o["no"])]["c"]["ok"] and res[str(o["no"])]["k"]["ok"])]
        print("retry button:", await pg.inner_text("#retryBtn"), "| expected wrong count:", len(wrong))
        await pg.evaluate("a => { window.__answers = a; }", sum([[[o["country"]], [o["capital"]]] for o in wrong], []))
        await pg.click("#retryBtn")
        for _ in range(300):
            await pg.wait_for_timeout(50)
            if await pg.is_visible("#resCard"): break
        st2 = await pg.evaluate("window.__quizState()")
        allok = all(st2["res"][str(o["no"])]["c"]["ok"] and st2["res"][str(o["no"])]["k"]["ok"] for o in items)
        print("after retry: all correct =", allok, "| retry list order:", [items[i]["no"] for i in st2["st"]["list"]])
        # 4) mid-quiz screenshot (start from ⑫, pause during capital question)
        await pg.click("#toStart")
        await pg.select_option("#from", "11")
        await pg.evaluate("() => { window.__answers = [['ブータン']]; }")
        await pg.click("#startBtn")
        await pg.wait_for_timeout(400)
        print("mid-quiz:", (await pg.inner_text("#qno")).replace("\n"," "), "|", await pg.inner_text("#stage"), "|", await pg.inner_text("#qtext"))
        await pg.click("#pauseBtn")
        await pg.evaluate("() => { document.getElementById('mark').innerHTML = '<span class=\"big ok\">○</span>'; document.getElementById('heard').innerHTML='聞こえた答え：<b>ブータン</b>'; }")
        await pg.screenshot(path=D + "/v2_voice_mid.png", full_page=False)
        print("page errors:", errs[:5])
        await b.close()
asyncio.run(main())
