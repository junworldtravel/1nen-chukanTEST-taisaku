# 続編の地図（①-1 中東・湾岸 白地図 / ②-1 欧州 地形図）をアプリ用に作る
# 出力: out/me_map.webp/.json, out/eu_map.webp/.json（pos は画像に対する割合、label で引く）
import sys, json, os, warnings
warnings.filterwarnings("ignore")
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, box, LineString
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyArrowPatch
from matplotlib.path import Path
from pyproj import Transformer
from PIL import Image

D = sys.argv[1]
sys.path.insert(0, D + "/scripts")
import content_v3 as C

for f in ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"]:
    fm.fontManager.addfont(f)
plt.rcParams["font.family"] = "Noto Sans CJK JP"
plt.rcParams["hatch.linewidth"] = 0.7

SEA, OTHER, TARGET, LINE, INK = "#E4EEF4", "#DCDCDA", "#FFFFFF", "#4A4A4A", "#111111"
SEA_TXT = "#4F7590"
CIRC = C.CIRC
G50 = gpd.read_file(D + "/map/ne_50m_admin_0_countries.geojson")
LAND = G50.geometry.union_all()

def circle_text(lab):
    return str(CIRC.index(lab) + 1) if lab in CIRC else lab

def fit_frame(tf, pts, aspect, pad=(0.03, 0.03, 0.04, 0.04)):
    xs, ys = tf.transform([p[0] for p in pts], [p[1] for p in pts])
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    w, h = x1 - x0, y1 - y0
    x0 -= pad[0] * w; x1 += pad[1] * w; y0 -= pad[2] * h; y1 += pad[3] * h
    w, h = x1 - x0, y1 - y0
    if w / h > aspect:
        nh = w / aspect; cy = (y0 + y1) / 2; y0, y1 = cy - nh / 2, cy + nh / 2
    else:
        nw = h * aspect; cx = (x0 + x1) / 2; x0, x1 = cx - nw / 2, cx + nw / 2
    return x0, y0, x1, y1

def graticule(ax, tf, lons, lats, lonr, latr):
    for lon in lons:
        xs, ys = tf.transform(np.full(80, lon), np.linspace(latr[0], latr[1], 80))
        ax.plot(xs, ys, color="#9DB3C2", lw=0.3, ls=(0, (2, 2)), zorder=0.5)
    for lat in lats:
        xs, ys = tf.transform(np.linspace(lonr[0], lonr[1], 200), np.full(200, lat))
        ax.plot(xs, ys, color="#9DB3C2", lw=0.3, ls=(0, (2, 2)), zorder=0.5)

def draw_circles(ax, tf, marks, cs, fs, lw):
    """marks: (label, anchor, circle or None, isCity)"""
    for lab, anchor, circ, city in marks:
        ax_, ay_ = tf.transform(*anchor)
        cx, cy = tf.transform(*(circ or anchor))
        if city:
            ax.plot([ax_], [ay_], "s", ms=6.5, color=INK, mec="white", mew=1.0, zorder=5.5)
        if circ:
            ax.plot([ax_, cx], [ay_, cy], color=INK, lw=0.9, zorder=4)
            if not city:
                ax.plot([ax_], [ay_], "o", ms=3.2, color=INK, zorder=5)
        ax.scatter([cx], [cy], s=cs, facecolor="white", edgecolor=INK, linewidth=lw, zorder=6)
        t = circle_text(lab)
        ax.text(cx, cy, t, fontsize=fs * (0.9 if len(t) > 1 else 1), fontweight="bold", ha="center", va="center", color=INK, zorder=7)

def save_app(fig, ax, tf, marks, name, extra=None):
    out = D + "/out"
    fig.canvas.draw()
    W, H = fig.canvas.get_width_height()
    pos = {}
    for lab, anchor, circ, city in marks:
        px, py = ax.transData.transform(tf.transform(*(circ or anchor)))
        pos[lab] = {"x": round(px / W, 5), "y": round(1 - py / H, 5)}
    png = f"{out}/{name}.png"
    fig.savefig(png, dpi=fig.dpi); plt.close(fig)
    im = Image.open(png).convert("RGB")
    im.save(f"{out}/{name}.webp", "WEBP", quality=86, method=6)
    meta = {"w": im.size[0], "h": im.size[1], "pos": pos}
    if extra: meta.update(extra)
    json.dump(meta, open(f"{out}/{name}.json", "w"), ensure_ascii=False)
    print(name, im.size, "webp KB", os.path.getsize(f"{out}/{name}.webp") // 1024)

DPI = 200
AW, AH = 11.6, 7.55   # 横長（既存のアジア地図とほぼ同じ比率）

# ================= ①-1 中東・湾岸 =================
def me_map():
    crs = "+proj=lcc +lat_1=18 +lat_2=38 +lat_0=28 +lon_0=48 +datum=WGS84 +units=m"
    tf = Transformer.from_crs(4326, crs, always_xy=True)
    codes = {"トルコ": "TUR", "イラク": "IRQ", "シリア": "SYR", "ヨルダン": "JOR", "イスラエル": "ISR", "クウェート": "KWT",
             "サウジアラビア": "SAU", "イラン": "IRN", "アラブ首長国連邦": "ARE", "オマーン": "OMN", "イエメン": "YEM",
             "カタール": "QAT", "バーレーン": "BHR", "レバノン": "LBN", "キプロス": "CYP", "アフガニスタン": "AFG"}
    targets = set(codes.values()) | {"CYN"}   # 北キプロスもキプロス島として白で塗る
    # 番号の点が、その国の中にあるか / ずらした丸が海の上か
    for lab, c, calt, k, kalt, anchor, circ in C.ME:
        if c:
            geom = G50[G50.ADM0_A3 == codes[c]].geometry.union_all()
            assert geom.contains(Point(anchor)) or geom.distance(Point(anchor)) < 0.05, (lab, c, "anchor outside")
        else:
            sau = G50[G50.ADM0_A3 == "SAU"].geometry.iloc[0]
            assert sau.contains(Point(anchor)), "Riyadh outside SAU"
        if circ:
            print("  ", lab, c or k, "circle on land:", LAND.contains(Point(circ)))
    tb = G50[G50.ADM0_A3.isin(targets)].total_bounds
    pts = [(tb[0], tb[1]), (tb[0], tb[3]), (tb[2], tb[1]), (tb[2], tb[3]), (31.5, 31.9), (tb[2], 12.0), (43.2, 11.8), (54.5, 11.9)]
    x0, y0, x1, y1 = fit_frame(tf, pts, AW / AH, pad=(0.02, 0.01, 0.03, 0.03))
    frame = box(x0, y0, x1, y1)
    gp = G50.clip(box(0, -5, 95, 60)).to_crs(crs)
    gp = gp[gp.geometry.intersects(frame)].copy()
    gp["geometry"] = gp.geometry.intersection(frame)
    fig = plt.figure(figsize=(AW, AH), dpi=DPI)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_facecolor(SEA)
    gp[~gp.ADM0_A3.isin(targets)].plot(ax=ax, color=OTHER, edgecolor="#8A8A8A", linewidth=0.45)
    gp[gp.ADM0_A3.isin(targets)].plot(ax=ax, color=TARGET, edgecolor=LINE, linewidth=0.75)
    graticule(ax, tf, range(20, 90, 10), range(10, 50, 10), (10, 90), (0, 50))
    for txt, lon, lat, rot in [("地中海", 29.0, 33.6, 0), ("黒海", 34.5, 43.0, 0), ("カスピ海", 50.8, 41.0, 0),
                               ("紅海", 38.4, 20.0, -55), ("ペルシア湾", 54.25, 26.08, -11), ("アラビア海", 62.0, 17.0, 0)]:
        x, y = tf.transform(lon, lat)
        ax.text(x, y, txt, fontsize=8.6 if txt == "ペルシア湾" else 9.5, color=SEA_TXT, ha="center", va="center", rotation=rot, style="italic", zorder=3)
    marks = [(lab, anchor, circ, c is None) for lab, c, calt, k, kalt, anchor, circ in C.ME]
    draw_circles(ax, tf, marks, cs=360, fs=12, lw=1.4)
    # ⑦ は首都（都市）の印だと分かるように凡例
    lx, ly = x0 + (x1 - x0) * 0.012, y0 + (y1 - y0) * 0.025
    ax.plot([lx + (x1 - x0) * 0.008], [ly + (y1 - y0) * 0.012], "s", ms=6.5, color=INK, mec="white", mew=1.0)
    ax.text(lx + (x1 - x0) * 0.02, ly + (y1 - y0) * 0.012, "＝首都の位置", fontsize=9, va="center", color="#333333")
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_xticks([]); ax.set_yticks([]); ax.set_aspect("equal")
    for s in ax.spines.values(): s.set_visible(False)
    save_app(fig, ax, tf, marks, "me_map")

# ================= ②-1 欧州 地形 =================
EU_COUNTRIES = [  # 教科書の地図にのっている国名（番号とぶつからない位置に置く）
 ("アイスランド", -18.6, 64.9), ("ノルウェー", 9.4, 59.7), ("スウェーデン", 14.9, 57.9), ("フィンランド", 26.6, 62.9),
 ("ロシア", 47.0, 61.5), ("アイルランド", -8.1, 53.0), ("イギリス", -1.6, 52.6), ("オランダ", 5.7, 52.6),
 ("ドイツ", 11.3, 50.6), ("ポーランド", 19.3, 52.1), ("ウクライナ", 31.3, 49.2), ("フランス", 3.2, 45.8),
 ("スイス", 6.7, 46.55), ("イタリア", 12.4, 42.5), ("スペイン", -3.0, 41.5), ("ポルトガル", -12.2, 39.6), ("ギリシャ", 22.0, 39.4),
]
MOUNTAINS = ["KJØLEN MOUNTAINS", "ALPS", "PYRENEES", "CARPATHIAN MOUNTAINS", "CAUCASUS MTS.", "URAL MOUNTAINS"]
NAC = [(-31.0, 45.0), (-24.5, 50.3), (-17.0, 55.2), (-9.0, 60.2), (0.0, 64.6), (10.0, 69.4)]   # 北大西洋海流の矢印

def eu_map():
    crs = "+proj=lcc +lat_1=42 +lat_2=64 +lat_0=52 +lon_0=16 +datum=WGS84 +units=m"
    tf = Transformer.from_crs(4326, crs, always_xy=True)
    pts = [(-24.5, 63.3), (-24.5, 66.6), (-32.0, 45.0), (-9.6, 36.0), (36.0, 34.6), (50.0, 40.5), (66.0, 68.6), (28.0, 71.2), (60.0, 51.5)]
    x0, y0, x1, y1 = fit_frame(tf, pts, AW / AH, pad=(0.01, 0.01, 0.02, 0.02))
    frame = box(x0, y0, x1, y1)
    g10 = gpd.read_file(D + "/map/ne_10m_admin_0_countries.geojson")
    gp = G50.clip(box(-60, 20, 100, 85)).to_crs(crs); gp = gp[gp.geometry.intersects(frame)].copy(); gp["geometry"] = gp.geometry.intersection(frame)
    landp = gpd.GeoSeries([LAND.intersection(box(-60, 20, 100, 85))], crs=4326).to_crs(crs).iloc[0].intersection(frame)
    fig = plt.figure(figsize=(AW, AH), dpi=DPI)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_facecolor(SEA)
    gp.plot(ax=ax, color=TARGET, edgecolor="#7A7A7A", linewidth=0.5)
    graticule(ax, tf, range(-40, 80, 20), range(30, 80, 10), (-50, 80), (25, 80))
    # 山脈（茶色の斜線）
    rg = gpd.read_file(D + "/map/ne_10m_geography_regions_polys.geojson")
    mt = rg[rg.NAME.str.upper().isin(MOUNTAINS)].to_crs(crs)
    assert len(mt) == len(MOUNTAINS), mt.NAME.tolist()
    mt["geometry"] = mt.geometry.buffer(0).intersection(landp)
    mt.plot(ax=ax, facecolor="#E9D3B4", edgecolor="#9C6B3A", linewidth=0.6, zorder=1.5)
    # 川（ライン川・ドナウ川）
    rv = gpd.read_file(D + "/map/ne_10m_rivers_lake_centerlines.geojson")
    rv = rv[rv.name.isin(["Rhein", "Rhin", "Rhine", "Danube", "Donau"])].to_crs(crs)
    rv.plot(ax=ax, color="#2F7FC1", linewidth=2.0, zorder=2)
    # 北大西洋海流（暖流＝赤の矢印）
    xs, ys = tf.transform([p[0] for p in NAC], [p[1] for p in NAC])
    verts = list(zip(xs, ys))
    path = Path(verts, [Path.MOVETO] + [Path.LINETO] * (len(verts) - 1))
    ax.add_patch(FancyArrowPatch(path=path, arrowstyle="-|>,head_length=9,head_width=5", color="#D8432E", lw=3.2, zorder=3.5))
    # 国名
    for nm, lon, lat in EU_COUNTRIES:
        x, y = tf.transform(lon, lat)
        ax.text(x, y, nm, fontsize=8.6, color="#3A3A3A", ha="center", va="center", zorder=3.8,
                bbox=dict(boxstyle="round,pad=0.12", fc=(1, 1, 1, 0.72), ec="none"))
    for txt, lon, lat in [("大西洋", -22.0, 40.5)]:
        x, y = tf.transform(lon, lat)
        ax.text(x, y, txt, fontsize=11, color=SEA_TXT, ha="center", va="center", style="italic", zorder=3)
    # 凡例
    lx, ly = x0 + (x1 - x0) * 0.75, y0 + (y1 - y0) * 0.035
    W_, H_ = x1 - x0, y1 - y0
    ax.add_patch(plt.Rectangle((lx, ly), W_ * 0.024, H_ * 0.03, facecolor="#E9D3B4", edgecolor="#9C6B3A", lw=0.6, zorder=8))
    ax.text(lx + W_ * 0.03, ly + H_ * 0.015, "山脈", fontsize=9, va="center", zorder=8)
    ax.plot([lx + W_ * 0.085, lx + W_ * 0.11], [ly + H_ * 0.015] * 2, color="#2F7FC1", lw=2.0, zorder=8)
    ax.text(lx + W_ * 0.116, ly + H_ * 0.015, "川", fontsize=9, va="center", zorder=8)
    ax.annotate("", xy=(lx + W_ * 0.175, ly + H_ * 0.015), xytext=(lx + W_ * 0.145, ly + H_ * 0.015),
                arrowprops=dict(arrowstyle="-|>", color="#D8432E", lw=2.2), zorder=8)
    ax.text(lx + W_ * 0.18, ly + H_ * 0.015, "暖流", fontsize=9, va="center", zorder=8)
    marks = [(lab, anchor, circ, False) for lab, a, cat, alt, anchor, circ in C.EU]
    for lab, anchor, circ, _ in marks:
        if circ: print("  ", lab, "circle on land:", LAND.contains(Point(circ)))
    draw_circles(ax, tf, marks, cs=330, fs=11.5, lw=1.3)
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_xticks([]); ax.set_yticks([]); ax.set_aspect("equal")
    for s in ax.spines.values(): s.set_visible(False)
    save_app(fig, ax, tf, marks, "eu_map")

if __name__ == "__main__":
    which = sys.argv[2:] or ["me", "eu"]
    if "me" in which: me_map()
    if "eu" in which: eu_map()
