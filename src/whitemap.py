import sys, json, warnings, os
warnings.filterwarnings("ignore")
import geopandas as gpd
from shapely.geometry import Point, box, LineString
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.backends.backend_pdf import PdfPages
from pyproj import Transformer

D = sys.argv[1]
for f in ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"]:
    fm.fontManager.addfont(f)
plt.rcParams["font.family"] = "Noto Sans CJK JP"

# 対象24か国（ユーザー指定の表記）: コード, 国名, 首都, 地域, 番号を指す点(経度,緯度), 丸の位置(省略時=同じ点)
T = [
 ("KOR","韓国","ソウル","東アジア",(127.85,36.40),None),
 ("PRK","北朝鮮","平壌","東アジア",(127.00,40.10),None),
 ("CHN","中国","北京","東アジア",(104.00,35.00),None),
 ("MNG","モンゴル","ウランバートル","東アジア",(103.10,46.90),None),
 ("MMR","ミャンマー","ネーピードー","東南アジア",(96.30,21.50),None),
 ("THA","タイ","バンコク","東南アジア",(101.00,15.30),None),
 ("VNM","ベトナム","ハノイ","東南アジア",(105.70,21.50),None),
 ("MYS","マレーシア","クアラルンプール","東南アジア",(102.20,4.30),None),
 ("SGP","シンガポール","シンガポール","東南アジア",(103.82,1.36),(106.60,0.40)),
 ("IDN","インドネシア","ジャカルタ","東南アジア",(113.90,-0.90),None),
 ("PHL","フィリピン","マニラ","東南アジア",(121.10,16.20),None),
 ("IND","インド","ニューデリー","南アジア",(79.50,22.60),None),
 ("PAK","パキスタン","イスラマバード","南アジア",(69.20,29.90),None),
 ("BGD","バングラデシュ","ダッカ","南アジア",(90.25,23.90),None),
 ("NPL","ネパール","カトマンズ","南アジア",(84.00,28.30),None),
 ("BTN","ブータン","ティンプー","南アジア",(90.45,27.40),(92.80,30.40)),
 ("KAZ","カザフスタン","アスタナ","中央アジア",(67.30,48.40),None),
 ("AFG","アフガニスタン","カブール","西アジア",(65.90,33.80),None),
 ("IRN","イラン","テヘラン","西アジア",(54.40,32.50),None),
 ("IRQ","イラク","バグダッド","西アジア",(43.80,33.00),None),
 ("KWT","クウェート","クウェート","西アジア",(47.60,29.30),(50.60,27.50)),
 ("SAU","サウジアラビア","リヤド","西アジア",(44.70,24.00),None),
 ("ISR","イスラエル","エルサレム","西アジア",(34.80,30.90),(31.60,33.00)),
 ("TUR","トルコ","アンカラ","西アジア",(35.20,39.10),None),
]
assert len(T) == 24 and len({t[0] for t in T}) == 24
# 東→西：番号の指す点の経度が大きい順
T.sort(key=lambda t: -t[4][0])
CIRC = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳㉑㉒㉓㉔"

CRS = "+proj=lcc +lat_1=15 +lat_2=45 +lat_0=25 +lon_0=88 +datum=WGS84 +units=m"
tf = Transformer.from_crs(4326, CRS, always_xy=True)
g = gpd.read_file(D + "/map/ne_50m_admin_0_countries.geojson")
targets = {t[0] for t in T}
# 中心点が指す国の中にあるか検証
for t in T:
    geom = g[g.ADM0_A3 == t[0]].geometry.iloc[0]
    assert geom.contains(Point(t[4])), (t[0], "anchor outside")
# 丸（ずらしたもの）が陸地に乗っていないか
land = g.geometry.union_all()
for t in T:
    if t[5]: print(t[1], "offset circle on land?", land.contains(Point(t[5])))

# 地図範囲：対象24か国が収まる範囲に余白をつけ、用紙の地図枠（横:縦=AX_W:AX_H）に合わせて広げる
import numpy as np
AX = [0.035, 0.035, 0.93, 0.855]
AX_W, AX_H = 11.69*AX[2], 8.27*AX[3]
tb = g[g.ADM0_A3.isin([t[0] for t in T])].to_crs(CRS).total_bounds
bx0, by0, bx1, by1 = tb
w, h = bx1-bx0, by1-by0
bx0 -= 0.035*w; bx1 += 0.03*w; by0 -= 0.05*h; by1 += 0.04*h
w, h = bx1-bx0, by1-by0
if w/h > AX_W/AX_H:
    nh = w*AX_H/AX_W; cy = (by0+by1)/2; by0, by1 = cy-nh/2, cy+nh/2
else:
    nw = h*AX_W/AX_H; cx = (bx0+bx1)/2; bx0, bx1 = cx-nw/2, cx+nw/2
x0, y0, x1, y1 = bx0, by0, bx1, by1
frame = box(x0, y0, x1, y1)
gp = g.to_crs(CRS)
gp = gp[gp.geometry.intersects(frame)]
gp["geometry"] = gp.geometry.intersection(frame)

SEA, OTHER, TARGET, LINE, INK = "#E4EEF4", "#DCDCDA", "#FFFFFF", "#4A4A4A", "#111111"

def draw_map(ax, numbered=True, cs=175, fs2=8.0, fs1=8.8, lw=0.9):
    ax.set_facecolor(SEA)
    other = gp[~gp.ADM0_A3.isin(targets)]
    tgt = gp[gp.ADM0_A3.isin(targets)]
    other.plot(ax=ax, color=OTHER, edgecolor="#8A8A8A", linewidth=0.35)
    tgt.plot(ax=ax, color=TARGET, edgecolor=LINE, linewidth=0.55)
    # 経緯線（20度ごと）
    for lon in range(40, 160, 20):
        xs, ys = tf.transform(np.full(50, lon), np.linspace(-20, 70, 50))
        ax.plot(xs, ys, color="#9DB3C2", lw=0.3, ls=(0,(2,2)), zorder=0.5)
    for lat in range(0, 70, 20):
        xs, ys = tf.transform(np.linspace(10, 170, 200), np.full(200, lat))
        ax.plot(xs, ys, color="#9DB3C2", lw=0.3 if lat else 0.6, ls=(0,(2,2)) if lat else "-", zorder=0.5)
    ex, ey = tf.transform(140.5, 0.8)
    ax.text(ex, ey, "赤道", fontsize=7, color="#5E7F95", ha="left", va="bottom")
    for k, t in enumerate(T):
        ax_, ay_ = tf.transform(*t[4])
        cx, cy = tf.transform(*(t[5] or t[4]))
        if t[5]:
            ax.plot([ax_, cx], [ay_, cy], color=INK, lw=0.6, zorder=4)
            ax.plot([ax_], [ay_], "o", ms=2.2, color=INK, zorder=5)
        ax.scatter([cx], [cy], s=cs, facecolor="white", edgecolor=INK, linewidth=lw, zorder=6)
        ax.text(cx, cy, str(k+1), fontsize=fs2 if k+1 >= 10 else fs1, fontweight="bold",
                ha="center", va="center", color=INK, zorder=7)
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1)
    ax.set_xticks([]); ax.set_yticks([]); ax.set_xlabel(""); ax.set_ylabel("")
    for s in ax.spines.values(): s.set_linewidth(0.8); s.set_color("#333333")
    ax.set_aspect("equal")

A4L = (11.69, 8.27)
def map_page():
    fig = plt.figure(figsize=A4L)
    fig.text(0.035, 0.965, "アジアの国々　白地図（24か国）", fontsize=15, fontweight="bold", va="top")
    fig.text(0.035, 0.928, "番号は東から西の順（①がいちばん東）。白い国が出題の24か国です。", fontsize=9, color="#444444", va="top")
    fig.text(0.965, 0.96, "名前（　　　　　　　　　）", fontsize=10, ha="right", va="top")
    ax = fig.add_axes(AX)
    draw_map(ax)
    return fig

def table_page(answers):
    fig = plt.figure(figsize=(8.27, 11.69))
    title = "白地図の答え" if answers else "解答らん"
    fig.text(0.08, 0.955, title, fontsize=16, fontweight="bold", va="top")
    fig.text(0.08, 0.925, "番号は地図の①〜㉔（東から西の順）", fontsize=9, color="#444444", va="top")
    if not answers:
        fig.text(0.92, 0.955, "名前（　　　　　　　　）", fontsize=10, ha="right", va="top")
    top, rowh = 0.885, 0.0335
    cols = [0.08, 0.17, 0.43, 0.70] if answers else [0.08, 0.17, 0.55]
    heads = ["番号", "国名", "首都", "地域"] if answers else ["番号", "国名", "首都"]
    for c, h in zip(cols, heads):
        fig.text(c, top, h, fontsize=10, fontweight="bold", color="#333333", va="center")
    fig.add_artist(plt.Line2D([0.08, 0.92], [top-0.017, top-0.017], color="#333333", lw=0.9))
    for k, t in enumerate(T):
        y = top - (k+1)*rowh
        fig.text(cols[0]+0.012, y, CIRC[k], fontsize=13, va="center")
        if answers:
            fig.text(cols[1], y, t[1], fontsize=12, va="center")
            fig.text(cols[2], y, t[2], fontsize=12, va="center", color="#8A5A00")
            fig.text(cols[3], y, t[3], fontsize=10, va="center", color="#555555")
        fig.add_artist(plt.Line2D([0.08, 0.92], [y-rowh/2, y-rowh/2], color="#BBBBBB", lw=0.5))
    return fig

out = D + "/out"
with PdfPages(out + "/アジア白地図_24か国.pdf") as pdf:
    f1 = map_page(); pdf.savefig(f1); f1.savefig(out + "/アジア白地図_24か国.png", dpi=220); plt.close(f1)
    f2 = table_page(False); pdf.savefig(f2); plt.close(f2)
    f3 = table_page(True); pdf.savefig(f3); f3.savefig(out + "/アジア白地図_答え.png", dpi=150); plt.close(f3)
json.dump([{"no": k+1, "code": t[0], "country": t[1], "capital": t[2], "region": t[3], "lon": t[4][0]} for k, t in enumerate(T)],
          open(out + "/whitemap_order.json", "w"), ensure_ascii=False, indent=1)
for k, t in enumerate(T): print(CIRC[k], t[1], t[2], t[4][0])

# ---- アプリ用：地図だけの画像（番号を大きめ）と、番号の位置（画像のピクセル座標） ----
if len(sys.argv) > 2 and sys.argv[2] == "app":
    from PIL import Image
    DPI = 200
    fig = plt.figure(figsize=(AX_W, AX_H), dpi=DPI)
    ax = fig.add_axes([0, 0, 1, 1])
    draw_map(ax, cs=330, fs2=10.5, fs1=11.5, lw=1.3)
    pos = []
    fig.canvas.draw()
    W, H = fig.canvas.get_width_height()
    for k, t in enumerate(T):
        cx, cy = tf.transform(*(t[5] or t[4]))
        px, py = ax.transData.transform((cx, cy))
        pos.append({"no": k+1, "x": round(px / W, 5), "y": round(1 - py / H, 5)})
    png = out + "/app_map.png"
    fig.savefig(png, dpi=DPI); plt.close(fig)
    im = Image.open(png).convert("RGB")
    im.save(out + "/app_map.webp", "WEBP", quality=88, method=6)
    json.dump({"w": im.size[0], "h": im.size[1], "pos": pos}, open(out + "/app_map.json", "w"))
    print("app map", im.size, "webp bytes", os.path.getsize(out + "/app_map.webp"))
