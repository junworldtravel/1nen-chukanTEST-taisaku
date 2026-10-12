# asia-quiz 元データ（src）

公開ページ（リポジトリ直下の index.html ほか）を作るための元データです。
新しいパターンを追加するときは、ここから作業を始めます。

## ページ構成
| 公開ファイル | 内容 | 元になるファイル |
|---|---|---|
| index.html | 問題集ポータル（地域ごと：アジア全域／中東・湾岸／欧州全域／英語。問題を増やしたらカードを追加） | リポジトリ直下の index.html を直接編集 |
| drill.html | アジア全域 首都-国名match（Excel 24組／暗唱・文字入力） | drill_template.html + drill_v2.json + textjudge.js |
| map.html | アジア全域 白地図から首都＆国名回答（24か国／声・文字入力） | map_template.html + map_v2_audio.json + app_map.* + whitemap_order.json + textjudge.js |
| me-map.html | ①-1 中東/湾岸 白地図から首都＆国名回答（27問） | quiz3_template.html + quizzes_v3.json + v3_audio.json + me_map.* |
| me-qa.html | ①-2 中東/湾岸 民族・宗教紛争・戦争・資源（一問一答19問） | quiz3_template.html + quizzes_v3.json + v3_audio.json |
| eu-map.html | ②-1 欧州 地図から地形の名称回答（20問） | quiz3_template.html + quizzes_v3.json + v3_audio.json + eu_map.* |
| eu-qa.html | ②-2 欧州 気候・宗教・言語（一問一答19問） | quiz3_template.html + quizzes_v3.json + v3_audio.json |
| reibun3.html | ③ 英語 基本例文集③（20文／和文→英作・英文→和訳／文字入力） | reibun_template.html + reibun3_v1.json + textjudge.js |

## データ
- excel_24pairs.xlsx：①の出題範囲（配布Excel）
- whitemap_order.json：②の24か国（番号は東→西）
- app_map.webp / app_map.json：②の地図画像と①〜㉔の位置
- whitemap_24.pdf：印刷用白地図（地図・解答らん・答え）
- drill_v2.json / map_v2_audio.json：声（MP3をbase64で格納）と字幕テキスト
- textjudge.js：文字入力の判定（ひらがな・カタカナ・漢字対応、1文字ちがいは「おしい」）。textJudgeSentence は文の判定（③で使用。英語は大文字・小文字と記号を無視、日本語は区切りごとに漢字・読みのどちらでも可）
- kihon-reibun-03.json：③の出題範囲（プリントから転記した20文）
- reibun3_v1.json：③の問題データ（判定用の読みつき）と声・字幕

## 続編（中東・欧州）の共通エンジン
- quiz3_template.html：データだけ差しかえて使える共通ページ。出題は a）声／b）文字、答えは 声／文字、順番は番号順／ランダム
- quizzes_v3.json：4問題の出題データ（content_v3.py で作成。accept＝文字入力で正解にする表記、voice＝聞きまちがい候補、kw＝キーワード判定）
- v3_audio.json：問題（龍星）と答え（ずんだもん）の声と字幕（gen_v3_audio.py で作成）
- me_map.* / eu_map.*：地図画像と番号の位置（maps_v3.py で作成）
- 組み立て：assemble_v3.py → site/ に me-map.html など4ページ。テスト：test_v3.py
- 新しい単元を足すときは、content_v3.py に問題を追加 → maps_v3.py（地図があれば）→ gen_v3_audio.py → assemble_v3.py → test_v3.py

## ③ 英語 基本例文集③
作業フォルダに in/kihon-reibun-03.json、scripts/ に gen_reibun3.py・assemble_reibun3.py・test_reibun3.py・test_judge_r3.js を置く
1. 読みの確認：`gen_reibun3.py <作業フォルダ> kana`（読みまちがいは FIX に書きかえを追加）
2. 声の生成：`gen_reibun3.py <作業フォルダ> build` → reibun3_v1.json（声モデルは 0.vvm だけでよい）
3. 組み立て：`assemble_reibun3.py <作業フォルダ>` → site/reibun3.html
4. テスト：`node test_judge_r3.js textjudge.js reibun3_v1.json`（判定）、`test_reibun3.py`（通し・字幕・画面）
- 英文の読み上げは VOICEVOX ではなく、スマホに入っている英語の音声（ブラウザの読み上げ機能）を使う

## 作り直しの流れ（作業環境での手順）
作業フォルダ（scratchpad）に次の配置で置いて実行します。
- `scripts/` に *.py と mock_sr.js、`out/` に whitemap_order.json・app_map.*、`in/src.xlsx`
1. 声の生成：gen_v2.py（VOICEVOX core 0.16 と声モデル 0.vvm・15.vvm・open_jtalk辞書を GitHub Releases から取得）
2. 地図：whitemap.py（Natural Earth ne_50m_admin_0_countries.geojson を取得）
3. 組み立て：assemble.py → site/ に drill.html・map.html
4. テスト：test_v2.py（文字入力・字幕・通し）、test_quiz_v2.py（声モード）
5. 公開：GitHub のアップロード画面からリポジトリ直下へ（公開前に必ず確認）

## 声・地図のクレジット
- 声：VOICEVOX:四国めたん／VOICEVOX:ずんだもん（首都-国名match・英語③）、VOICEVOX:青山龍星／VOICEVOX:ずんだもん（白地図・中東・欧州）
- 地図：Natural Earth（パブリックドメイン）
