import sys, io, wave, subprocess, json, base64, os
import numpy as np
from voicevox_core.blocking import Onnxruntime, OpenJtalk, Synthesizer, VoiceModelFile
D = sys.argv[1]; MODE = sys.argv[2] if len(sys.argv) > 2 else "build"
SR = 24000; MET, ZUN, RYU = 2, 3, 13
NAME = {MET: "めたん", ZUN: "ずんだもん", RYU: "龍星"}
ort = Onnxruntime.load_once(filename=D+"/vv/voicevox_onnxruntime-linux-x64-1.17.3/lib/libvoicevox_onnxruntime.so")
syn = Synthesizer(ort, OpenJtalk(D+"/vv/open_jtalk_dic_utf_8-1.11"))
for f in ("0", "15"):
    with VoiceModelFile.open(f"{D}/vv/{f}.vvm") as m: syn.load_voice_model(m)

def synth_b64(text, sp, key):
    q = syn.create_audio_query(text, sp)
    q.speed_scale = 1.0; q.pre_phoneme_length = 0.05; q.post_phoneme_length = 0.08; q.output_sampling_rate = SR
    with wave.open(io.BytesIO(syn.synthesis(q, sp))) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)
    thr = 0.01*np.abs(a).max(); idx = np.where(np.abs(a) > thr)[0]
    a = a[max(idx[0]-int(0.02*SR), 0): idx[-1]+int(0.05*SR)]; a = a/np.abs(a).max()*0.89*32767
    os.makedirs(D+"/v2clips", exist_ok=True); p = f"{D}/v2clips/{key}.wav"
    with wave.open(p, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(a.astype(np.int16).tobytes())
    subprocess.run(["ffmpeg","-y","-loglevel","error","-i",p,"-ac","1","-ar","24000","-b:a","48k",p[:-4]+".mp3"], check=True)
    return base64.b64encode(open(p[:-4]+".mp3","rb").read()).decode()

# ===== ① 暗記ドリル（Excelの24組） =====
old = json.load(open(D + "/web_data.json"))
pairs = old["pairs"]
drill_new = {
  # 暗唱モード（国名→首都）
  "rc_c2k_1": (MET, "これから、アジアの国の、首都を覚える練習をします。"),
  "rc_c2k_2": (MET, "はじめに、国の名前を言います。"),
  "rc_c2k_3": (MET, "そのあと、3秒間、時間をあけます。そのあいだに、その国の首都を、頭の中で答えてください。"),
  "rc_c2k_4": (MET, "3秒たったら、正解の首都を、別の声で言います。"),
  "rc_c2k_5": (MET, "問題は、全部で24問です。順番は、スタートするたびに、ばらばらに変わります。それでは、始めます。"),
  # 暗唱モード（首都→国名）
  "rc_k2c_1": (MET, "これから、アジアの首都が、どの国の首都なのかを覚える練習をします。"),
  "rc_k2c_2": (MET, "はじめに、首都の名前を言います。"),
  "rc_k2c_3": (MET, "そのあと、3秒間、時間をあけます。そのあいだに、どの国の首都なのかを、頭の中で答えてください。"),
  "rc_k2c_4": (MET, "3秒たったら、正解の国の名前を、別の声で言います。"),
  "rc_k2c_5": (MET, "問題は、全部で24問です。順番は、スタートするたびに、ばらばらに変わります。それでは、始めます。"),
  # 文字入力モード
  "tx_c2k_1": (MET, "これから、国の名前を言います。その国の首都を、文字で入力してください。"),
  "tx_k2c_1": (MET, "これから、首都の名前を言います。どの国の首都なのかを、文字で入力してください。"),
  "tx_2":     (ZUN, "ひらがなでも、カタカナでも、漢字でもいいのだ。わからないときは、わからないボタンを押すのだ。"),
  "tx_3":     (MET, "問題は、全部で24問です。それでは、始めます。"),
  # 終わり・判定
  "end_1": (MET, "これで、24問おわりです。"),
  "end_2": (MET, "おつかれさまでした。"),
  "end_3": (MET, "答えられなかった問題は、もう一度、確認しておきましょう。"),
  "end_tx": (MET, "これで、おわりです。結果を見てみましょう。"),
  "praise1": (ZUN, "せいかい！いいね！"),
  "praise2": (ZUN, "ぐっじょぶなのだ！"),
  "praise3": (ZUN, "すごいのだ！その調子なのだ！"),
  "close":   (ZUN, "おしい！もうちょっとなのだ。正解は、"),
  "ngpre":   (ZUN, "ざんねん！正解は、"),
}
if MODE == "kana":
    for k, (sp, t) in drill_new.items(): print(k, "|", syn.create_audio_query(t, sp).kana)
    for k, (sp, t) in {"m_tx2": (ZUN, "地図の番号の国の名前を、文字で入力するのだ！"), "m_tx4": (ZUN, "ひらがなでも、カタカナでも、漢字でもいいのだ。わからないときは、わからないボタンを押すのだ。")}.items():
        print(k, "|", syn.create_audio_query(t, sp).kana)
    sys.exit()

dclips, dsubs = {}, {}
for k, (sp, t) in drill_new.items():
    dclips[k] = synth_b64(t, sp, "d_"+k); dsubs[k] = {"who": NAME[sp], "text": t}
for i, p in enumerate(pairs):   # 既存の名前の音声（問題=めたん、答え=ずんだもん）を再利用
    for kind, name in (("cty", p["country"]), ("cap", p["capital"])):
        dclips[f"{kind}{i}_q"] = old["clips"][f"{kind}{i}_q"]; dsubs[f"{kind}{i}_q"] = {"who": "めたん", "text": name}
        dclips[f"{kind}{i}_a"] = old["clips"][f"{kind}{i}_a"]; dsubs[f"{kind}{i}_a"] = {"who": "ずんだもん", "text": name}
json.dump({"pairs": pairs, "clips": dclips, "subs": dsubs}, open(D + "/drill_v2.json", "w"), ensure_ascii=False)
print("drill clips", len(dclips), "KB", os.path.getsize(D + "/drill_v2.json")//1024)

# ===== ② 白地図クイズ：字幕（表示用の名前）と文字入力用の説明 =====
qa = json.load(open(D + "/quiz_audio.json"))
order = json.load(open(D + "/out/whitemap_order.json"))
R, Z = "龍星", "ずんだもん"
S = {"intro1": (R, "これから、アジアの国と首都のクイズを始める。"), "intro2": (Z, "地図の番号の国の名前を、声で答えるのだ！"),
     "intro3": (R, "国の名前のあとは、その国の首都も答えてもらう。全部で24か国だ。"),
     "intro4": (Z, "マイクのマークが出たら、はっきり話すのだ。わからないときは、わからない、と言えばいいのだ。"),
     "intro5": (R, "では、始めよう。"),
     "praise1": (Z, "いいね！その調子なのだ！"), "praise2": (Z, "ぐっじょぶなのだ！"), "praise3": (Z, "せいかい！すごいのだ！"),
     "praise4": (Z, "かんぺきなのだ！"), "praise5": (Z, "大正解なのだ！やったのだ！"),
     "retry": (Z, "よく聞こえなかったのだ。もう一回、言ってほしいのだ。"),
     "manual": (Z, "うまく聞き取れなかったのだ。画面のボタンで、答え合わせしてほしいのだ。"),
     "streak": (Z, "連続正解なのだ！のってるのだ！"), "end": (R, "これで24か国、全部おわりだ。よくがんばった。"),
     "end2": (R, "これで、おわりだ。よくがんばった。"), "resPerfect": (Z, "全問正解なのだ！天才なのだ！"),
     "resGood": (Z, "よくできたのだ！まちがえたところを、もう一回チャレンジするのだ！"),
     "resMore": (Z, "まちがえた問題を、もう一回練習するのだ。次はもっとできるのだ！"),
     "retryIntro": (R, "まちがえた問題だけ、もう一度いくぞ。")}
DISP = {"平壌": "平壌（ピョンヤン）", "北京": "北京（ペキン）"}
for o in order:
    n, c, k = o["no"], o["country"], DISP.get(o["capital"], o["capital"])
    S[f"qc{n}"] = (R, f"{n}番の国の名前は？"); S[f"okc{n}"] = (R, f"{n}番は、{c}。では、{c}の首都は？")
    S[f"ngc{n}"] = (Z, f"ざんねん！{n}番は、{c}なのだ。"); S[f"qk{n}"] = (R, f"では、{c}の首都は？")
    S[f"ngk{n}"] = (Z, f"ざんねん！{c}の首都は、{k}なのだ。")
assert set(S) == set(qa["clips"]), set(qa["clips"]) ^ set(S)
mclips = dict(qa["clips"])
for k, t in {"txintro2": "地図の番号の国の名前を、文字で入力するのだ！", "txintro4": "ひらがなでも、カタカナでも、漢字でもいいのだ。わからないときは、わからないボタンを押すのだ。"}.items():
    mclips[k] = synth_b64(t, ZUN, "m_"+k); S[k] = (Z, t)
msubs = {k: {"who": v[0], "text": v[1]} for k, v in S.items()}
json.dump({"clips": mclips, "subs": msubs}, open(D + "/map_v2_audio.json", "w"), ensure_ascii=False)
print("map clips", len(mclips), "subs", len(msubs))
