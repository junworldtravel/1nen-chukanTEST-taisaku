// 使い方: node test_judge_r3.js <textjudge.js> <reibun3_v1.json>
const fs = require("fs");
global.window = {}; eval(fs.readFileSync(process.argv[2], "utf8"));
const D = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));
const it = n => D.items[n - 1];
const C = [
 ["en", 1, "He goes to the library after school.", "correct"], ["en", 1, "he goes to the library after school", "correct"],
 ["en", 1, "He goes  to the library after school ", "correct"], ["en", 1, "He go to the library after school.", "close"],
 ["en", 1, "He goes to library after school.", "wrong"], ["en", 4, "My brother doesn’t listen to music.", "correct"],
 ["en", 4, "My brother does not listen to music", "correct"], ["en", 4, "My brother doesnt listen to music.", "close"],
 ["en", 4, "My brother don't listen to music.", "close"],
 ["en", 5, "Does your mother cook Chinese food? - Yes, she does. / No, she doesn't.", "correct"],
 ["en", 5, "Does your mother cook Chinese food? Yes, she does. No, she doesn't.", "correct"],
 ["en", 5, "does your mother cook chinese food yes she does no she does not", "correct"],
 ["en", 5, "Does your mother cook Chinese food?", "wrong"], ["en", 3, "Mr Smith has two cats", "correct"],
 ["en", 3, "Mr. Smith has 2 cats.", "wrong"], ["en", 3, "Mr. Smith have two cats.", "close"],
 ["en", 2, "She learns fifty English words every week.", "correct"], ["en", 17, "How long is the Tone river?", "correct"],
 ["en", 19, "Which is your cup, this one or that one?", "correct"], ["en", 19, "Which is your cup this one or that one", "correct"],
 ["en", 18, "Who plays baseball well?", "correct"], ["en", 18, "Who play baseball well?", "close"],
 ["en", 13, "This pencil case is mine.", "correct"], ["en", 13, "This pencilcase is mine.", "close"],
 ["en", 1, "わからない", "pass"], ["en", 1, "", "empty"], ["en", 1, "   ", "empty"], ["en", 1, "...", "empty"],
 ["ja", 1, "彼は放課後図書館に行きます。", "correct"], ["ja", 1, "かれはほうかごとしょかんにいきます", "correct"],
 ["ja", 1, "彼は放課後、図書館に行きます。", "correct"], ["ja", 1, "かれは放課後としょかんに行きます", "correct"],
 ["ja", 1, "カレハホウカゴトショカンニイキマス", "correct"],
 ["ja", 1, "彼は放課後図書館に行きました。", "close"], ["ja", 1, "彼は図書館に行きます", "wrong"],
 ["ja", 2, "彼女は毎週50個の英単語を学んでいます。", "correct"], ["ja", 2, "彼女は毎週５０個の英単語を学んでいます", "correct"],
 ["ja", 2, "かのじょはまいしゅうごじゅっこのえいたんごをまなんでいます", "correct"], ["ja", 2, "彼女は毎週五十個の英単語を学んでいます", "correct"],
 ["ja", 3, "スミスさんは2匹の猫を飼っています", "correct"], ["ja", 3, "すみすさんはにひきのねこをかっています", "correct"],
 ["ja", 3, "スミスさんは二匹の猫を持っています", "close"], ["ja", 4, "私の兄は音楽を聞きません", "close"],
 ["ja", 5, "あなたの母は中華料理を作りますか。はい、作ります。いいえ、作りません。", "correct"],
 ["ja", 5, "あなたの母は中華料理を作りますか —— はい、作ります。／いいえ、作りません。", "correct"],
 ["ja", 5, "あなたの母は中華料理を作りますか", "wrong"],
 ["ja", 7, "ジャネットは決して納豆を食べない", "correct"], ["ja", 7, "ジャネットは決して納豆を食べません", "wrong"],
 ["ja", 10, "あなたのくらすめいとはどこですか", "correct"], ["ja", 11, "あなたの学校はなんじに始まりますか", "correct"],
 ["ja", 16, "あなたの兄はなんさいですか", "correct"], ["ja", 17, "とねがわはどれくらいながいですか", "correct"],
 ["ja", 19, "あなたのコップはどっちですか、これですか、あれですか。", "correct"], ["ja", 19, "あなたのコップはどっちですかこれですかあれですか", "correct"],
 ["ja", 20, "あなたはなんのきょうかがすきですか", "correct"], ["ja", 20, "あなたは何の教科が好きですか。", "correct"],
 ["ja", 14, "これはだれの傘ですか", "correct"], ["ja", 14, "わからない", "pass"], ["ja", 14, "わかりません", "pass"],
 ["ja", 18, "誰が野球を上手にしますか", "correct"], ["ja", 13, "この筆箱は私のです", "close"], ["ja", 8, "私の母はいつも朝はいそがしい", "correct"],
];
const bad = [];
for (const [l, n, inp, exp] of C) {
  const r = textJudgeSentence(l, [l === "en" ? it(n).enAns : it(n).jaAns], inp).status;
  if (r !== exp) bad.push([l, n, inp, exp, r]);
}
console.log("sentence judge cases:", C.length, "failures:", JSON.stringify(bad));
let self = 0;
D.items.forEach(x => {
  if (textJudgeSentence("en", [x.enAns], x.en).status === "correct") self++;
  if (textJudgeSentence("ja", [x.jaAns], x.ja).status === "correct") self++;
});
console.log("print text judged correct:", self, "/ 40");
console.log("old judge still works:", textJudge("k", "THA", "ばんこく").status, textJudge("c", "BGD", "バングラディシュ").status);
process.exit(bad.length || self !== 40 ? 1 : 0);
