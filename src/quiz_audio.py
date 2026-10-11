import sys, io, wave, subprocess, json, base64, os
import numpy as np
from voicevox_core.blocking import Onnxruntime, OpenJtalk, Synthesizer, VoiceModelFile
D = sys.argv[1]; MODE = sys.argv[2] if len(sys.argv) > 2 else "kana"
SR = 24000; R, Z = 13, 3   # 青山龍星 ノーマル / ずんだもん ノーマル
ort = Onnxruntime.load_once(filename=D+"/vv/voicevox_onnxruntime-linux-x64-1.17.3/lib/libvoicevox_onnxruntime.so")
syn = Synthesizer(ort, OpenJtalk(D+"/vv/open_jtalk_dic_utf_8-1.11"))
for f in ("0", "15"):
    with VoiceModelFile.open(f"{D}/vv/{f}.vvm") as m: syn.load_voice_model(m)

order = json.load(open(D + "/out/whitemap_order.json"))
READ = {"平壌": "ピョンヤン", "北京": "ペキン"}
rd = lambda s: READ.get(s, s)

L = {}  # key -> (speaker, text)
L["intro1"] = (R, "これから、アジアの国と首都のクイズを始める。")
L["intro2"] = (Z, "地図の番号の国の名前を、声で答えるのだ！")
L["intro3"] = (R, "国の名前のあとは、その国の首都も答えてもらう。全部で24か国だ。")
L["intro4"] = (Z, "マイクのマークが出たら、はっきり話すのだ。わからないときは、わからない、と言えばいいのだ。")
L["intro5"] = (R, "では、始めよう。")
for o in order:
    n, c, k = o["no"], rd(o["country"]), rd(o["capital"])
    L[f"qc{n}"]  = (R, f"{n}番の国の名前は？")
    L[f"okc{n}"] = (R, f"{n}番は、{c}。では、{c}の首都は？")
    L[f"ngc{n}"] = (Z, f"ざんねん！{n}番は、{c}なのだ。")
    L[f"qk{n}"]  = (R, f"では、{c}の首都は？")
    L[f"ngk{n}"] = (Z, f"ざんねん！{c}の首都は、{k}なのだ。")
for i, t in enumerate(["いいね！その調子なのだ！", "ぐっじょぶなのだ！", "せいかい！すごいのだ！", "かんぺきなのだ！", "大正解なのだ！やったのだ！"], 1):
    L[f"praise{i}"] = (Z, t)
L["retry"]   = (Z, "よく聞こえなかったのだ。もう一回、言ってほしいのだ。")
L["manual"]  = (Z, "うまく聞き取れなかったのだ。画面のボタンで、答え合わせしてほしいのだ。")
L["streak"]  = (Z, "連続正解なのだ！のってるのだ！")
L["end"]     = (R, "これで24か国、全部おわりだ。よくがんばった。")
L["end2"]    = (R, "これで、おわりだ。よくがんばった。")
L["resPerfect"] = (Z, "ぜんもん正解なのだ！天才なのだ！")
L["resGood"]    = (Z, "よくできたのだ！まちがえたところを、もう一回チャレンジするのだ！")
L["resMore"]    = (Z, "まちがえた問題を、もう一回練習するのだ。次はもっとできるのだ！")
L["retryIntro"] = (R, "まちがえた問題だけ、もう一度いくぞ。")

if MODE == "kana":
    for key, (sp, t) in L.items():
        if not (key.startswith("ngk") or key.startswith("ngc") or key in ("resPerfect",)): continue
        print(key, "|", syn.create_audio_query(t, sp).kana)
    sys.exit()

KANA_LINE = {"ngk11": "ザンネ'ン、ミャ'ンマアノ/シュ'トワ、ネエピ'イドオナ/ノダ'"}
def synth(t, sp, key=None):
    q = syn.create_audio_query_from_kana(KANA_LINE[key], sp) if key in KANA_LINE else syn.create_audio_query(t, sp)
    q.speed_scale = 1.0 if sp == Z else 0.97
    q.pre_phoneme_length = 0.05; q.post_phoneme_length = 0.08; q.output_sampling_rate = SR
    with wave.open(io.BytesIO(syn.synthesis(q, sp))) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)
    thr = 0.01*np.abs(a).max(); idx = np.where(np.abs(a) > thr)[0]
    a = a[max(idx[0]-int(0.02*SR), 0): idx[-1]+int(0.05*SR)]
    return a / np.abs(a).max() * 0.89 * 32767

CL = D + "/quizclips"; os.makedirs(CL, exist_ok=True)
clips = {}; total = 0.0
for key, (sp, t) in L.items():
    a = synth(t, sp, key); total += len(a)/SR
    p = f"{CL}/{key}.wav"
    with wave.open(p, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(a.astype(np.int16).tobytes())
    subprocess.run(["ffmpeg","-y","-loglevel","error","-i",p,"-ac","1","-ar","24000","-b:a","48k",p[:-4]+".mp3"], check=True)
    clips[key] = base64.b64encode(open(p[:-4]+".mp3","rb").read()).decode()
json.dump({"clips": clips, "lines": {k: v[1] for k, v in L.items()}}, open(D + "/quiz_audio.json", "w"), ensure_ascii=False)
print("clips", len(clips), "seconds", round(total), "json KB", os.path.getsize(D + "/quiz_audio.json")//1024)
