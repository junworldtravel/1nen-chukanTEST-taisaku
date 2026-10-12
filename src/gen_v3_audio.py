# 続編4問題のセリフ（字幕）と声（青山龍星＝問題、ずんだもん＝○✕）を作る
# python3 gen_v3_audio.py D kana   … 全セリフの読み（カナ）を表示して確認
# python3 gen_v3_audio.py D build  … 音声を作って v3_audio.json に保存
import sys, io, wave, subprocess, json, base64, os, hashlib
import numpy as np
D = sys.argv[1]; MODE = sys.argv[2] if len(sys.argv) > 2 else "build"
R, Z = 13, 3
WHO = {R: "龍星", Z: "ずんだもん"}
Q = json.load(open(D + "/quizzes_v3.json"))

# 読みまちがいの直し（表示はそのまま、読み上げだけ書きかえる）
SPEAK_FIX = {"、平原、": "、へいげん、", "冷帯": "れいたい", "何問題": "なに問題", "日本の": "にほんの"}
KANA_FIX = {}   # 文 → AquesTalk風カナ（どうしても直らないとき）
def sp(t):
    for a, b in SPEAK_FIX.items(): t = t.replace(a, b)
    return t

def strip_ng(t):
    return t[len("ざんねん！"):] if t.startswith("ざんねん！") else t

def quiz_lines(qz):
    """key -> (speaker, 字幕, 読み上げ文)"""
    L = {}
    N = sum(len(it["steps"]) for it in qz["items"])
    ismap = qz["type"] == "map"
    L["intro_t"] = (R, f"これから、{qz['speakTitle']}の問題を始める。", None)
    L["intro_v"] = (Z, "地図の番号を見て、声で答えるのだ！" if ismap else "問題を聞いて、声で答えるのだ！", None)
    L["intro_x"] = (Z, "地図の番号を見て、答えを文字で入力するのだ！" if ismap else "問題を聞いて、答えを文字で入力するのだ！", None)
    L["mic"] = (Z, "マイクのマークが緑になったら、はっきり話すのだ。わからないときは、わからない、と言えばいいのだ。", None)
    L["kbd"] = (Z, "ひらがなでも、カタカナでも、漢字でもいいのだ。わからないときは、わからないボタンを押すのだ。", None)
    L["count"] = (R, f"全部で{N}問だ。", None)
    L["go"] = (R, "では、始めよう。", None)
    for i, t in enumerate(["いいね！その調子なのだ！", "ぐっじょぶなのだ！", "せいかい！すごいのだ！", "かんぺきなのだ！", "大正解なのだ！やったのだ！"], 1):
        L[f"praise{i}"] = (Z, t, None)
    L["streak"] = (Z, "連続正解なのだ！のってるのだ！", None)
    L["retry"] = (Z, "よく聞こえなかったのだ。もう一回、言ってほしいのだ。", None)
    L["manual"] = (Z, "うまく聞き取れなかったのだ。画面のボタンで、答え合わせしてほしいのだ。", None)
    L["ng0"] = (Z, "ざんねん！", None)
    L["close0"] = (Z, "おしい！あと少しなのだ。", None)
    L["end"] = (R, "これで、全部おわりだ。よくがんばった。", None)
    L["end2"] = (R, "これで、おわりだ。よくがんばった。", None)
    L["resPerfect"] = (Z, "全問正解なのだ！天才なのだ！", "ぜんもん正解なのだ！天才なのだ！")
    L["resGood"] = (Z, "よくできたのだ！まちがえたところを、もう一回チャレンジするのだ！", None)
    L["resMore"] = (Z, "まちがえた問題を、もう一回練習するのだ。次はもっとできるのだ！", None)
    L["retryIntro"] = (R, "まちがえた問題だけ、もう一度いくぞ。", None)
    for i, it in enumerate(qz["items"]):
        for j, s in enumerate(it["steps"]):
            L[f"q{i}_{j}"] = (R, s["q"], s["qs"])
            L[f"a{i}_{j}"] = (Z, strip_ng(s["ng"]), strip_ng(s["ngs"]))
    return L

ALL = {qz["id"]: quiz_lines(qz) for qz in Q}

from voicevox_core.blocking import Onnxruntime, OpenJtalk, Synthesizer, VoiceModelFile
ort = Onnxruntime.load_once(filename=D + "/vv/voicevox_onnxruntime-linux-x64-1.17.3/lib/libvoicevox_onnxruntime.so")
syn = Synthesizer(ort, OpenJtalk(D + "/vv/open_jtalk_dic_utf_8-1.11"))
for f in ("0", "15"):
    with VoiceModelFile.open(f"{D}/vv/{f}.vvm") as m: syn.load_voice_model(m)

if MODE == "kana":
    seen = set()
    for qid, L in ALL.items():
        for key, (spk, sub, say) in L.items():
            t = sp(say or sub)
            if t in seen: continue
            seen.add(t)
            print(qid, key, "|", t, "|", KANA_FIX.get(t) or syn.create_audio_query(t, spk).kana)
    sys.exit()

SR = 24000
CL = D + "/v3clips"; os.makedirs(CL, exist_ok=True)
def synth_mp3(t, spk):
    h = hashlib.md5(f"{spk}|{t}|{KANA_FIX.get(t, '')}".encode()).hexdigest()[:16]
    mp3 = f"{CL}/{h}.mp3"
    if not os.path.exists(mp3):
        q = syn.create_audio_query_from_kana(KANA_FIX[t], spk) if t in KANA_FIX else syn.create_audio_query(t, spk)
        q.speed_scale = 1.0 if spk == Z else 0.97
        q.pre_phoneme_length = 0.05; q.post_phoneme_length = 0.08; q.output_sampling_rate = SR
        with wave.open(io.BytesIO(syn.synthesis(q, spk))) as w:
            a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)
        thr = 0.01 * np.abs(a).max(); idx = np.where(np.abs(a) > thr)[0]
        a = a[max(idx[0] - int(0.02 * SR), 0): idx[-1] + int(0.05 * SR)]
        a = a / np.abs(a).max() * 0.89 * 32767
        wav = mp3[:-4] + ".wav"
        with wave.open(wav, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(a.astype(np.int16).tobytes())
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-ac", "1", "-ar", "24000", "-b:a", "48k", mp3], check=True)
        os.remove(wav)
    return base64.b64encode(open(mp3, "rb").read()).decode()

OUT = {}
for qid, L in ALL.items():
    clips, subs = {}, {}
    for key, (spk, sub, say) in L.items():
        clips[key] = synth_mp3(sp(say or sub), spk)
        subs[key] = {"who": WHO[spk], "text": sub}
    OUT[qid] = {"clips": clips, "subs": subs}
    print(qid, "clips", len(clips), "KB", sum(len(v) for v in clips.values()) * 3 // 4 // 1024)
json.dump(OUT, open(D + "/v3_audio.json", "w"), ensure_ascii=False)
print("v3_audio.json KB", os.path.getsize(D + "/v3_audio.json") // 1024)
