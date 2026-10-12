"""③ 基本例文集③ の公開ページを組み立てる
使い方: python3 assemble_reibun3.py <作業フォルダ>
  reibun_template.html + reibun3_v1.json + textjudge.js → site/reibun3.html
"""
import sys, json, os, html
D = sys.argv[1]
tj = open(D + "/textjudge.js", encoding="utf-8").read()
data = json.load(open(D + "/reibun3_v1.json", encoding="utf-8"))
s = json.dumps(data, ensure_ascii=False); assert "</script" not in s
t = open(D + "/reibun_template.html", encoding="utf-8").read()
t = t.replace("__TITLE__", html.escape(data["title"])).replace("__TEXTJUDGE__", tj).replace("__DATA__", s)
os.makedirs(D + "/site", exist_ok=True)
open(D + "/site/reibun3.html", "w", encoding="utf-8").write(t)
print("reibun3.html", round(os.path.getsize(D + "/site/reibun3.html") / 1e6, 2), "MB")
