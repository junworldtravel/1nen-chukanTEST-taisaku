"""③ 基本例文集③ の通しテスト
使い方: python3 test_reibun3.py <作業フォルダ>   （site/reibun3.html と site/index.html を使う）
"""
import sys, asyncio, json
from playwright.async_api import async_playwright
D = sys.argv[1]
SUBLOG = r"""
window.__QUIZ_FAST = %s; window.__subs = [];
document.addEventListener('DOMContentLoaded', () => {
  const el = document.getElementById('subCur');
  if (el) new MutationObserver(() => { const t = el.textContent; if (t) window.__subs.push(t); }).observe(el, {childList: true, subtree: true, characterData: true});
});
"""
def hira(s): return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s)
def reading(lat): return hira("".join(a[1] if len(a) > 1 else a[0] for a in lat))
def drop_letter(s):  # 1文字ちがい（おしい）
    i = len(s) // 2
    while not s[i].isalpha(): i += 1
    return s[:i] + s[i + 1:]

async def open_page(b, path, fast=True):
    pg = await b.new_page(viewport={"width": 393, "height": 852}, device_scale_factor=2)
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    await pg.add_init_script(SUBLOG % ("true" if fast else "false"))
    await pg.goto("file://" + D + "/site/" + path)
    return pg, errs

async def current_no(pg):
    await pg.wait_for_function("/^プリント No\\.\\d+/.test(document.getElementById('meta').textContent) && !document.getElementById('playCard').hidden")
    return int((await pg.inner_text("#meta")).split("No.")[1].split("（")[0])

async def answer(pg, text):
    await pg.fill("#ans", text); await pg.press("#ans", "Enter")

async def wait_judged(pg, n, prev_meta):
    await pg.wait_for_function("(n) => window.__reibunState().res[n] !== undefined", arg=n)
    await pg.wait_for_function("(m) => document.getElementById('meta').textContent !== m || !document.getElementById('resCard').hidden", arg=prev_meta)

async def full_run(pg, mode, items, plan):
    """plan(q, it) -> (入力 or None=わからない, 期待する正誤)"""
    await pg.click("#d-" + mode); await pg.click("#startBtn")
    expect = {}
    for q in range(20):
        n = await current_no(pg); meta = await pg.inner_text("#meta"); it = items[n - 1]
        text, ok = plan(q, it)
        if text is None: await pg.click("#passBtn")
        else: await answer(pg, text)
        expect[n] = ok
        await wait_judged(pg, n, meta)
    await pg.wait_for_selector("#resCard:not([hidden])", timeout=20000)
    st = await pg.evaluate("window.__reibunState()")
    mism = [(n, e, st["res"][str(n)]) for n, e in expect.items() if st["res"][str(n)]["ok"] != e]
    return expect, mism

async def main():
    data = json.load(open(D + "/reibun3_v1.json", encoding="utf-8")); items = data["items"]
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
        pg, errs = await open_page(b, "reibun3.html#ja2en")
        await pg.wait_for_function("!document.getElementById('startBtn').disabled", timeout=90000)
        print("loaded: title", await pg.inner_text("#ttl"), "| range:", await pg.inner_text("#range"),
              "| ja2en preselected:", await pg.get_attribute("#d-ja2en", "aria-pressed"))
        # ---------- 判定（ページ内） ----------
        self_ok = await pg.evaluate("""(items) => items.filter(it => window.__textJudgeSentence('en',[it.enAns],it.en).status==='correct'
            && window.__textJudgeSentence('ja',[it.jaAns],it.ja).status==='correct').length""", items)
        print("in-page judge: print text correct for", self_ok, "/ 20 items (both directions)")
        # ---------- 和文→英作：通し ----------
        def plan_en(q, it):
            k = q % 5
            if k == 0: return it["en"], True
            if k == 1: return it["en"].lower().replace(".", "").replace("?", "").replace(",", ""), True
            if k == 2: return "I like dogs.", False
            if k == 3: return None, False
            return drop_letter(it["en"]), False
        expect, mism = await full_run(pg, "ja2en", items, plan_en)
        subs = await pg.evaluate("window.__subs")
        q_subs = sum(1 for it in items if any(s == "めたん" + it["ja"] for s in subs))
        a_subs = sum(1 for it in items if any(s == "英語" + it["en"] for s in subs))
        intro = [s for s in subs if s.startswith("めたんこれから") or s.startswith("ずんだもんピリオド") or s.startswith("めたん問題は")]
        fb = sum(1 for s in subs if s.startswith("ずんだもん") and ("ざんねん" in s or "おしい" in s or "のだ" in s or "いいね" in s))
        close_shown = any("おしい" in s for s in subs)
        print("① 和文→英作: judged as expected:", not mism, mism[:3], "| score:", await pg.inner_text("#rs"), "/", await pg.inner_text("#rn"),
              "| subtitles: question(めたん・日本語)", q_subs, "/20, answer(英語)", a_subs, "/20, intro", len(intro), "/3, feedback lines", fb,
              "| おしい shown:", close_shown, "| errors:", errs)
        await pg.screenshot(path=D + "/r3_res_ja2en.png", full_page=True)
        # まちがえた問題だけ
        wrong = [n for n, e in expect.items() if not e]
        await pg.click("#retryBtn")
        for _ in wrong:
            n = await current_no(pg); meta = await pg.inner_text("#meta")
            await answer(pg, items[n - 1]["en"]); await wait_judged(pg, n, meta)
        await pg.wait_for_selector("#resCard:not([hidden])", timeout=20000)
        print("① retry wrong-only:", await pg.inner_text("#rs"), "/", await pg.inner_text("#rn"), "(expected", len(wrong), "/", len(wrong), ")",
              "| retry button now:", await pg.inner_text("#retryBtn"))
        # ○✕ の手なおし
        await pg.click("#rt tr:first-child td.mk button")
        print("① tap ○✕ toggles score:", await pg.inner_text("#rs"), "/", await pg.inner_text("#rn"))
        # ---------- 英文→和訳：通し ----------
        await pg.click("#setBtn"); await pg.evaluate("window.__subs = []")
        def plan_ja(q, it):
            k = q % 5
            if k == 0: return it["ja"], True
            if k == 1: return reading(it["jaAns"]), True
            if k == 2: return "わかりません", False
            if k == 3: return "東京に行きます。", False
            return it["ja"].replace("。", "").replace("、", ""), True
        expect, mism = await full_run(pg, "en2ja", items, plan_ja)
        subs = await pg.evaluate("window.__subs")
        q_subs = sum(1 for it in items if any(s == "英語" + it["en"] for s in subs))
        a_subs = sum(1 for it in items if any(s == "ずんだもん" + it["ja"] for s in subs))
        print("② 英文→和訳: judged as expected:", not mism, mism[:3], "| score:", await pg.inner_text("#rs"), "/", await pg.inner_text("#rn"),
              "| subtitles: question(英語)", q_subs, "/20, answer(ずんだもん・日本語)", a_subs, "/20 | intro:",
              any(s.startswith("めたんこれから、英語") for s in subs), any(s.startswith("ずんだもんひらがな") for s in subs), "| errors:", errs)
        await pg.screenshot(path=D + "/r3_res_en2ja.png", full_page=True)
        # ---------- 画面（キーボードで隠れないか）・日本語入力中の Enter ----------
        await pg.click("#setBtn"); await pg.click("#d-ja2en"); await pg.click("#startBtn")
        n = await current_no(pg)
        while n != 5:   # 一番長い No.5 の画面を確認
            meta = await pg.inner_text("#meta"); await pg.click("#passBtn"); await wait_judged(pg, n, meta); n = await current_no(pg)
        await pg.fill("#ans", "Does your mother cook Chinese food? Yes, she does. No, she does"); await pg.dispatch_event("#ans", "input")
        geo = await pg.evaluate("""() => { const r = id => document.getElementById(id).getBoundingClientRect();
            return {q: Math.round(r('q').bottom), subs: Math.round(r('subCur').bottom), ans: Math.round(r('ans').bottom), hint: document.getElementById('hint').textContent,
                    scrollW: document.documentElement.scrollWidth}; }""")
        print("screen 393px, No.5: bottoms(px) question", geo["q"], "subtitle", geo["subs"], "input", geo["ans"],
              "| keyboard-safe (input above 470px):", geo["ans"] < 470, "| hint:", geo["hint"], "| no sideways scroll:", geo["scrollW"] <= 393)
        await pg.screenshot(path=D + "/r3_play_no5.png", full_page=False)
        await pg.evaluate("""() => { const e = new KeyboardEvent('keydown', {key: 'Enter', isComposing: true, bubbles: true, cancelable: true});
            document.getElementById('ans').dispatchEvent(e); }""")
        await pg.wait_for_timeout(200)
        print("Enter while IME converting does not submit:", "5" not in (await pg.evaluate("window.__reibunState()"))["res"])
        await pg.click("#stopBtn"); await pg.close()
        # ---------- 本番の速さ（音あり／音なし）で1問ずつ ----------
        for sound in (True, False):
            pg, errs = await open_page(b, "reibun3.html#en2ja", fast=False)
            await pg.wait_for_function("!document.getElementById('startBtn').disabled", timeout=90000)
            if (await pg.is_checked("#sound")) != sound: await pg.click(".opt .switch")
            if await pg.is_checked("#intro"): await pg.click("label[for=intro] .switch")
            await pg.click("#startBtn")
            n = await current_no(pg); meta = await pg.inner_text("#meta")
            await pg.wait_for_timeout(400)
            sub_q = await pg.inner_text("#subCur")
            await answer(pg, items[n - 1]["ja"])
            t0 = await pg.evaluate("performance.now()")
            await pg.wait_for_function("(m) => document.getElementById('meta').textContent !== m", arg=meta, timeout=30000)
            t1 = await pg.evaluate("performance.now()")
            print(f"real speed, sound {'on ' if sound else 'off'}: question subtitle shown: {sub_q[:30]!r} | moved to next question after {round((t1 - t0) / 1000, 1)} s | chip: {await pg.inner_text('#soundChip')} | errors: {errs}")
            if sound:
                await pg.fill("#ans", "かれは")
                await pg.screenshot(path=D + "/r3_play_en2ja.png", full_page=False)
            await pg.close()
        # ---------- メニュー ----------
        pg, errs = await open_page(b, "index.html")
        links = await pg.evaluate("[...document.querySelectorAll('a')].map(a=>a.getAttribute('href'))")
        await pg.screenshot(path=D + "/r3_menu.png", full_page=True)
        print("menu links:", links, "| errors:", errs)
        pg2, errs2 = await open_page(b, "reibun3.html#en2ja")
        print("menu → en2ja preselected:", await pg2.get_attribute("#d-en2ja", "aria-pressed"))
        await b.close()
asyncio.run(main())
