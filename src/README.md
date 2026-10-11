# asia-quiz 元データ（src）

公開ページ（リポジトリ直下の index.html / drill.html / map.html）を作るための元データです。
新しいパターンを追加するときは、ここから作業を始めます。

## ページ構成
| 公開ファイル | 内容 | 元になるファイル |
|---|---|---|
| index.html | 問題集メニュー（パターンを増やしたらここにカードを追加） | リポジトリ直下の index.html を直接編集 |
| drill.html | ① 首都の暗記ドリル（Excel 24組／暗唱・文字入力） | drill_template.html + drill_v2.json + textjudge.js |
| map.html | ② 白地図クイズ（24か国／声・文字入力） | map_template.html + map_v2_audio.json + app_map.* + whitemap_order.json + textjudge.js |

## データ
- excel_24pairs.xlsx：①の出題範囲（配布Excel）
- whitemap_order.json：②の24か国（番号は東→西）
- app_map.webp / app_map.json：②の地図画像と①〜㉔の位置
- whitemap_24.pdf：印刷用白地図（地図・解答らん・答え）
- drill_v2.json / map_v2_audio.json：声（MP3をbase64で格納）と字幕テキスト
- textjudge.js：文字入力の判定（ひらがな・カタカナ・漢字対応、1文字ちがいは「おしい」）

## 作り直しの流れ（作業環境での手順）
作業フォルダ（scratchpad）に次の配置で置いて実行します。
- `scripts/` に *.py と mock_sr.js、`out/` に whitemap_order.json・app_map.*、`in/src.xlsx`
1. 声の生成：gen_v2.py（VOICEVOX core 0.16 と声モデル 0.vvm・15.vvm・open_jtalk辞書を GitHub Releases から取得）
2. 地図：whitemap.py（Natural Earth ne_50m_admin_0_countries.geojson を取得）
3. 組み立て：assemble.py → site/ に drill.html・map.html
4. テスト：test_v2.py（文字入力・字幕・通し）、test_quiz_v2.py（声モード）
5. 公開：GitHub のアップロード画面からリポジトリ直下へ（公開前に必ず確認）

## 声・地図のクレジット
- 声：VOICEVOX:四国めたん／VOICEVOX:ずんだもん（①）、VOICEVOX:青山龍星／VOICEVOX:ずんだもん（②）
- 地図：Natural Earth（パブリックドメイン）
