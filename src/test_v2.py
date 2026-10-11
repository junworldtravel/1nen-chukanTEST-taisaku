import sys, asyncio, json
from playwright.async_api import async_playwright
D = sys.argv[1]
SUBLOG = r"""
window.__QUIZ_FAST = true; window.__subs = [];
document.addEventListener('DOMContentLoaded', () => {
  const el = document.getElementById('subCur');
  new MutationObserver(() => { const t = el.textContent; if (t) window.__subs.push(t); }).observe(el, {childList: true, subtree: true, characterData: true});
});
"""
TJ = [("k","THA","ばんこく","correct"),("k","THA","バンコク","correct"),("k","THA","ﾊﾞﾝｺｸ","correct"),("k","PRK","ピョンヤン","correct"),("k","PRK","平壌","correct"),
 ("k","PRK","へいじょう","correct"),("k","CHN","ぺきん","correct"),("k","CHN","北京","correct"),("k","IND","でりー","correct"),("k","IND","ニューデリー","correct"),
 ("k","MMR","ねぴどー","correct"),("k","MMR","ネーピードー","correct"),("k","MYS","クアラルンプル","close"),("k","IRQ","バグダード","close"),
 ("c","IND","インドネシア","wrong"),("c","IDN","インド","wrong"),("c","IRN","イラク","wrong"),("c","KOR","かんこく","correct"),("c","KOR","大韓民国","correct"),
 ("c","CHN","ちゅうごく","correct"),("c","ARE","あらぶしゅちょうこくれんぽう","correct"),("c","ARE","アラブ首長国連邦","correct"),("c","BGD","バングラディシュ","close"),
 ("c","NPL","ネパル","close"),("c","THA","たい","correct"),("k","KWT","クウェート","correct"),("c","KWT","くうぇーと","correct"),("k","KOR","そうる","correct"),
 ("k","TUR","アンカラです","correct"),("c","MNG","もんごる","correct"),("k","IDN","じゃかるた","correct"),("c","KOR","わからない","pass"),("c","KOR","ソウル","wrong"),
 ("c","SGP","シンガポール","correct"),("k","SGP","しんがぽーる","correct"),("k","ARE","あぶだび","correct"),("c","BTN","ぶーたん","correct"),("k","BTN","ティンプー","correct"),
 ("c","PRK","北朝鮮","correct"),("c","PRK","韓国","wrong"),("k","KAZ","あすたな","correct"),("k","AFG","カブル","close"),("c","SAU","サウジアラビア","correct"),("k","ISR","えるされむ","correct")]

async def page(b, path, init=SUBLOG, mock_sr=False):
    pg = await b.new_page(viewport={"width": 393, "height": 852}, device_scale_factor=2)
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    await pg.add_init_script(init)
    if mock_sr:
        await pg.add_init_script(open(D + "/scripts/mock_sr.js").read())
    await pg.goto("file://" + D + "/site/" + path)
    return pg, errs

async def type_answer(pg, text):
    await pg.wait_for_function("document.activeElement && document.activeElement.id==='ans' || true")
    await pg.fill("#ans", text); await pg.press("#ans", "Enter")

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
        # ---------- text judge ----------
        pg, errs = await page(b, "drill.html")
        await pg.wait_for_function("!document.getElementById('startBtn').disabled", timeout=90000)
        bad = []
        for kind, code, inp, exp in TJ:
            r = await pg.evaluate("([k,c,i]) => window.__textJudge(k,c,i)", [kind, code, inp])
            if r["status"] != exp: bad.append((kind, code, inp, exp, r["status"]))
        print("text judge cases:", len(TJ), "failures:", bad)
        # ---------- ① drill: text mode c2k ----------
        await pg.click("#m-text"); await pg.click("#startBtn")
        pairs = await pg.evaluate("JSON.parse(document.getElementById('ddata').textContent).pairs")
        expect = {}
        for q in range(24):
            await pg.wait_for_function("window.__drillState().list.length===24 && document.getElementById('q').textContent && document.getElementById('q').textContent!=='説明を聞いてね'")
            qtext = await pg.inner_text("#q")
            i = next(k for k, pp in enumerate(pairs) if pp["country"] == qtext)
            cap = pairs[i]["capital"]
            ans = cap.split("（")[1].rstrip("）") if "（" in cap else cap
            if q % 4 == 0:
                # hiragana input
                kana = "".join(chr(ord(ch) - 0x60) if "ァ" <= ch <= "ヶ" else ch for ch in ans)
                await type_answer(pg, kana); expect[i] = True
            elif q % 4 == 1: await type_answer(pg, "とうきょう"); expect[i] = False
            elif q % 4 == 2: await pg.click("#passBtn"); expect[i] = False
            else: await type_answer(pg, ans); expect[i] = True
            await pg.wait_for_function("(n) => window.__drillState().res[n] !== undefined", arg=i)
            if q % 4 == 1:
                rr = (await pg.evaluate("window.__drillState()"))["res"][str(i)]; assert rr["you"] == "とうきょう" and not rr["ok"], rr
            await pg.wait_for_function("(t) => document.getElementById('q').textContent !== t || !document.getElementById('resCard').hidden", arg=qtext)
        await pg.wait_for_selector("#resCard:not([hidden])", timeout=20000)
        stt = await pg.evaluate("window.__drillState()")
        ok = all(stt["res"][str(i)]["ok"] == e for i, e in expect.items())
        subs = await pg.evaluate("window.__subs")
        names_q = sum(1 for p_ in pairs if any(s.endswith(p_["country"]) and s.startswith("めたん") for s in subs))
        names_a = sum(1 for p_ in pairs if any(p_["capital"] in s and s.startswith("ずんだもん") for s in subs))
        print("① text c2k: results match:", ok, "| score:", await pg.inner_text("#rs"), "/", await pg.inner_text("#rn"),
              "| subtitles: questions", names_q, "/24, answers", names_a, "/24 | intro subs:", sum(1 for s in subs if "文字で入力" in s or "ひらがな" in s), "| errors:", errs)
        await pg.screenshot(path=D + "/v2_drill_res.png", full_page=True)
        # retry wrong only
        wrong = [i for i, e in expect.items() if not e]
        await pg.click("#retryBtn")
        for _ in range(len(wrong)):
            await pg.wait_for_function("document.getElementById('q').textContent && !document.getElementById('playCard').hidden")
            qtext = await pg.inner_text("#q"); i = next(k for k, pp in enumerate(pairs) if pp["country"] == qtext)
            await type_answer(pg, pairs[i]["capital"].split("（")[0])
            await pg.wait_for_function("(t) => document.getElementById('q').textContent !== t || !document.getElementById('resCard').hidden", arg=qtext)
        await pg.wait_for_selector("#resCard:not([hidden])", timeout=20000)
        print("① retry wrong-only:", await pg.inner_text("#rs"), "/", await pg.inner_text("#rn"))
        # ---------- ① drill: k2c text, mid-question screenshot ----------
        await pg.click("#setBtn"); await pg.click("#d-k2c"); await pg.click("#startBtn")
        await pg.wait_for_function("document.getElementById('q').textContent && document.getElementById('q').textContent!=='説明を聞いてね'")
        await pg.fill("#ans", "たい")
        await pg.screenshot(path=D + "/v2_drill_text.png", full_page=False)
        qtext = await pg.inner_text("#q"); i = next(k for k, pp in enumerate(pairs) if pp["capital"] == qtext)
        await type_answer(pg, pairs[i]["country"]); await pg.wait_for_function("(n) => window.__drillState().res[n] !== undefined", arg=i)
        print("① k2c first answer judged correct:", (await pg.evaluate("window.__drillState()"))["res"][str(i)]["ok"])
        # ---------- ① drill: recite mode ----------
        await pg.click("#stopBtn"); await pg.click("#m-recite"); await pg.click("#d-c2k"); await pg.click("#startBtn")
        await pg.wait_for_timeout(800)
        info = await pg.evaluate("""() => { const a = document.getElementById('audio'); return {dur: a.duration, hidden: a.hidden}; }""")
        # seek through and check subtitles track the audio
        checks = []
        for tsec in [1.0, 20.0, 60.0, 120.0, info["dur"] - 2]:
            await pg.evaluate("(t) => { const a=document.getElementById('audio'); a.pause(); a.currentTime=t; }", tsec)
            await pg.wait_for_timeout(250)
            checks.append(((await pg.inner_text("#count")).replace("\n", " "), (await pg.inner_text("#subCur"))[:24]))
        print("① recite: audio sec", round(info["dur"], 1), "| subtitle samples:", checks)
        await pg.evaluate("() => { const a=document.getElementById('audio'); a.currentTime=40; }"); await pg.wait_for_timeout(300)
        await pg.screenshot(path=D + "/v2_drill_recite.png", full_page=False)
        await pg.close()
        # ---------- ② map: text mode ----------
        pg, errs = await page(b, "map.html#text")
        await pg.wait_for_function("!document.getElementById('startBtn').disabled", timeout=90000)
        items = json.load(open(D + "/out/whitemap_order.json"))
        await pg.click("#startBtn")
        exp2 = {}
        for o in items:
            n = o["no"]; cap = o["capital"]
            await pg.wait_for_function("(n) => document.getElementById('qtext').textContent.indexOf('の国の名前は') > 0 && document.getElementById('qno').textContent.indexOf('" + "') >= 0", arg=n)
            await pg.wait_for_function("(c) => !document.getElementById('ansForm').hidden", arg=n)
            # country
            if n % 5 == 0: await pg.fill("#ans", "わからない"); c_ok = False
            elif n % 5 == 1: await pg.fill("#ans", "".join(chr(ord(ch) - 0x60) if "ァ" <= ch <= "ヶ" else ch for ch in o["country"])); c_ok = True
            elif n % 5 == 2: await pg.fill("#ans", "日本"); c_ok = False
            else: await pg.fill("#ans", o["country"]); c_ok = True
            await pg.press("#ans", "Enter")
            await pg.wait_for_function("(c) => document.getElementById('qtext').textContent.indexOf('の首都は') > 0", arg=n)
            k_ok = n % 3 != 0
            await pg.fill("#ans", cap if k_ok else "東京"); await pg.press("#ans", "Enter")
            exp2[n] = (c_ok, k_ok)
            await pg.wait_for_function("(n) => { const s = window.__quizState(); return s.res[n] && s.res[n].k; }", arg=n)
        await pg.wait_for_selector("#resCard:not([hidden])", timeout=20000)
        res = (await pg.evaluate("window.__quizState()"))["res"]
        good = all(res[str(n)]["c"]["ok"] == e[0] and res[str(n)]["k"]["ok"] == e[1] for n, e in exp2.items())
        subs = await pg.evaluate("window.__subs")
        print("② text mode: all 24 judged as expected:", good, "| score:", await pg.inner_text("#rc"), "/24 国名,", await pg.inner_text("#rk"), "/24 首都",
              "| subtitle lines shown:", len(subs), "| has qc/okc/ngc/ngk/praise:",
              any(s.startswith("龍星") and "番の国の名前は" in s for s in subs), any("の首都は？" in s for s in subs),
              any(s.startswith("ずんだもん") and "ざんねん" in s for s in subs), any("なのだ！" in s for s in subs), "| errors:", errs)
        await pg.screenshot(path=D + "/v2_map_res.png", full_page=False)
        await pg.click("#toStart"); await pg.select_option("#from", "6"); await pg.click("#startBtn")
        await pg.wait_for_function("document.getElementById('qtext').textContent.indexOf('の国の名前は') > 0")
        await pg.fill("#ans", "ちゅうごく")
        await pg.screenshot(path=D + "/v2_map_text.png", full_page=False)
        await pg.close()
        # ---------- menu ----------
        pg, errs = await page(b, "index.html", init="")
        await pg.screenshot(path=D + "/v2_menu.png", full_page=True)
        links = await pg.evaluate("[...document.querySelectorAll('a')].map(a=>a.getAttribute('href'))")
        print("menu links:", links, "| errors:", errs)
        await b.close()
asyncio.run(main())
