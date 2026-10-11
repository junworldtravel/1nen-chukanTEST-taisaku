import sys, json, base64
D = sys.argv[1]
tj = open(D + "/textjudge.js", encoding="utf-8").read()
# ① drill
dv = json.load(open(D + "/drill_v2.json"))
s = json.dumps(dv, ensure_ascii=False); assert "</script" not in s
t = open(D + "/drill_template.html", encoding="utf-8").read().replace("__TEXTJUDGE__", tj).replace("__DATA__", s)
open(D + "/site/drill.html", "w", encoding="utf-8").write(t)
# ② map
order = json.load(open(D + "/out/whitemap_order.json")); m = json.load(open(D + "/out/app_map.json")); au = json.load(open(D + "/map_v2_audio.json"))
data = {"items": [{"no": o["no"], "code": o["code"], "country": o["country"], "capital": o["capital"]} for o in order], "map": m,
        "mapImg": "data:image/webp;base64," + base64.b64encode(open(D + "/out/app_map.webp", "rb").read()).decode(),
        "clips": au["clips"], "subs": au["subs"]}
s = json.dumps(data, ensure_ascii=False); assert "</script" not in s
t = open(D + "/map_template.html", encoding="utf-8").read().replace("__TEXTJUDGE__", tj).replace("__DATA__", s)
open(D + "/site/map.html", "w", encoding="utf-8").write(t)
import os
for f in ("index.html", "drill.html", "map.html"): print(f, round(os.path.getsize(D + "/site/" + f) / 1e6, 2), "MB")
