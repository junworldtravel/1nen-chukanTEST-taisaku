"""③ 基本例文集③：判定用データ（読みつき）と声（VOICEVOX）を作る
使い方: python3 gen_reibun3.py <作業フォルダ> [kana|build]
  作業フォルダに in/kihon-reibun-03.json と vv/（VOICEVOX core 一式）を置く
  kana  … 全セリフの読み（カナ）を表示して確認する
  build … reibun3_v1.json（問題データ＋声＋字幕）を書き出す
"""
import sys, io, wave, subprocess, json, base64, os, re
D = sys.argv[1]; MODE = sys.argv[2] if len(sys.argv) > 2 else "kana"
SRC = json.load(open(D + "/in/kihon-reibun-03.json", encoding="utf-8"))

# 和訳の判定用：{表記|読み|別表記…}。表記と読みのどちらで入力してもよい（ひらがな・カタカナ・漢字）
JA = {
 1: "{彼|カレ}は{放課後|ホウカゴ}{図書館|トショカン}に{行|イ}きます。",
 2: "{彼女|カノジョ}は{毎週|マイシュウ}{50個|ゴジュッコ|ゴジッコ|五十個|ゴジュウコ}の{英単語|エイタンゴ}を{学|マナ}んでいます。",
 3: "スミスさんは{二匹|ニヒキ|2匹}の{猫|ネコ}を{飼|カ}っています。",
 4: "{私|ワタシ}の{兄|アニ}は{音楽|オンガク}を{聴|キ}きません。",
 5: "あなたの{母|ハハ}は{中華料理|チュウカリョウリ}を{作|ツク}りますか。—— はい、{作|ツク}ります。／いいえ、{作|ツク}りません。",
 6: "{私|ワタシ}はいつも{朝食|チョウショク}に{牛乳|ギュウニュウ}を{飲|ノ}みます。",
 7: "ジャネットは{決|ケッ}して{納豆|ナットウ}を{食|タ}べない。",
 8: "{私|ワタシ}の{母|ハハ}はいつも{朝|アサ}は{忙|イソガ}しい。",
 9: "あなたはどこに{住|ス}んでいますか。",
 10: "あなたのクラスメイトはどこですか。",
 11: "あなたの{学校|ガッコウ}は{何時|ナンジ}に{始|ハジ}まりますか。",
 12: "あなたの{学校|ガッコウ}の{文化祭|ブンカサイ}はいつですか。",
 13: "この{筆箱|フデバコ}は{私|ワタシ}のものです。",
 14: "これは{誰|ダレ}の{傘|カサ}ですか。",
 15: "あの{定規|ジョウギ}はあなたのものですか。",
 16: "あなたの{兄|アニ}は{何歳|ナンサイ}ですか。",
 17: "{利根川|トネガワ}はどれくらい{長|ナガ}いですか。",
 18: "{誰|ダレ}が{野球|ヤキュウ}を{上手|ジョウズ}にしますか。",
 19: "あなたのコップはどっちですか、これですか、あれですか。",
 20: "あなたは{何|ナン|ナニ}の{教科|キョウカ}が{好|ス}きですか。",
}
def lattice(m):
    segs = []
    for part in re.split(r"(\{[^}]+\})", m):
        if not part: continue
        if part.startswith("{"): segs.append(part[1:-1].split("|"))
        else: segs.append([part])
    return segs
def surface(m): return "".join(s[0] for s in lattice(m))

items = []
for it in SRC["items"]:
    n = it["no"]; assert surface(JA[n]) == it["ja"], (n, surface(JA[n]), it["ja"])
    en_alts = [it["en"]]
    if "doesn't" in it["en"]: en_alts.append(it["en"].replace("doesn't", "does not"))
    items.append({"no": n, "lesson": it["lesson"], "en": it["en"], "ja": it["ja"], "enAns": [en_alts], "jaAns": lattice(JA[n])})

# ---------- 声 ----------
MET, ZUN = 2, 3
NAME = {MET: "めたん", ZUN: "ずんだもん"}
def say(t):  # 画面の文 → 読み上げ用（記号を区切りに）
    return t.replace("——", "。").replace("—", "。").replace("／", "。").replace(" ", "").replace("。。", "。")
L = {
 "in_ja2en_1": (MET, "これから、日本語の文を言います。その文を、英語にして、入力してください。"),
 "in_en2ja_1": (MET, "これから、英語の文を読みます。その文の意味を、日本語で入力してください。"),
 "in_ja2en_2": (ZUN, "ピリオドや、はてなマークは、なくてもいいのだ。わからないときは、わからないボタンを押すのだ。"),
 "in_en2ja_2": (ZUN, "ひらがなでも、漢字でもいいのだ。わからないときは、わからないボタンを押すのだ。"),
 "in_3":       (MET, "問題は、全部で20問です。順番は、スタートするたびに、ばらばらに変わります。それでは、始めます。"),
 "end_tx":  (MET, "これで、おわりです。結果を見てみましょう。"),
 "praise1": (ZUN, "せいかい！いいね！"),
 "praise2": (ZUN, "ぐっじょぶなのだ！"),
 "praise3": (ZUN, "すごいのだ！その調子なのだ！"),
 "close":   (ZUN, "おしい！もうちょっとなのだ。正解は、"),
 "ngpre":   (ZUN, "ざんねん！正解は、"),
}
SUB_TEXT = {}
for it in items:
    n = it["no"]
    L[f"jq{n}"] = (MET, say(it["ja"])); SUB_TEXT[f"jq{n}"] = it["ja"]   # 和文→英作の問題
    L[f"ja{n}"] = (ZUN, say(it["ja"])); SUB_TEXT[f"ja{n}"] = it["ja"]   # 英文→和訳の答え
# 読みまちがいの書きかえ（kana で確認して追加）
FIX = {"jq20": "あなたは、なんの教科が好きですか。", "ja20": "あなたは、なんの教科が好きですか。"}

from voicevox_core.blocking import Onnxruntime, OpenJtalk, Synthesizer, VoiceModelFile
ort = Onnxruntime.load_once(filename=D + "/vv/voicevox_onnxruntime-linux-x64-1.17.3/lib/libvoicevox_onnxruntime.so")
syn = Synthesizer(ort, OpenJtalk(D + "/vv/open_jtalk_dic_utf_8-1.11"))
with VoiceModelFile.open(D + "/vv/0.vvm") as m: syn.load_voice_model(m)
def spoken(k, t): return FIX.get(k, t)

if MODE == "kana":
    for k, (sp, t) in L.items():
        if k.startswith("ja"): continue   # jq と同じ文
        print(k, "|", spoken(k, t), "|", syn.create_audio_query(spoken(k, t), sp).kana)
    sys.exit()

import numpy as np
SR = 24000
def synth_b64(k, sp, t):
    q = syn.create_audio_query(spoken(k, t), sp)
    q.speed_scale = 1.0; q.pre_phoneme_length = 0.05; q.post_phoneme_length = 0.08; q.output_sampling_rate = SR
    with wave.open(io.BytesIO(syn.synthesis(q, sp))) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)
    thr = 0.01 * np.abs(a).max(); idx = np.where(np.abs(a) > thr)[0]
    a = a[max(idx[0] - int(0.02 * SR), 0): idx[-1] + int(0.05 * SR)]; a = a / np.abs(a).max() * 0.89 * 32767
    os.makedirs(D + "/r3clips", exist_ok=True); p = f"{D}/r3clips/{k}.wav"
    with wave.open(p, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(a.astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", p, "-ac", "1", "-ar", "24000", "-b:a", "48k", p[:-4] + ".mp3"], check=True)
    return base64.b64encode(open(p[:-4] + ".mp3", "rb").read()).decode()
clips, subs = {}, {}
for k, (sp, t) in L.items():
    clips[k] = synth_b64(k, sp, t); subs[k] = {"who": NAME[sp], "text": SUB_TEXT.get(k, t)}
out = {"id": SRC["id"], "title": SRC["title"], "subtitle": SRC["subtitle"], "items": items, "clips": clips, "subs": subs}
json.dump(out, open(D + "/reibun3_v1.json", "w", encoding="utf-8"), ensure_ascii=False)
print("clips", len(clips), "KB", os.path.getsize(D + "/reibun3_v1.json") // 1024)
