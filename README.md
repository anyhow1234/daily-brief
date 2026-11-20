# Daily Brief — 每日英文新闻播客

AI 每天自动：抓新闻 → 写英文稿 → 微软 Neural TTS 转语音 → 发布到 GitHub Pages → App 订阅收听。

## 现在的状态

| 环节 | 方案 | 验证 |
|---|---|---|
| RSS | `https://anyhow1234.github.io/daily-brief/feed.xml` | ✅ HTTP 200，App 解析器解析通过 |
| 音频 | GitHub Pages `audio/YYYY-MM-DD.mp3` | ✅ HTTP 200，596KB / 1:39 |
| 仓库 | `github.com/anyhow1234/daily-brief`（公开） | ✅ Pages 已启用 |
| TTS | `edge-tts`（微软 Neural，`en-US-AriaNeural`） | ✅ 99 秒音频 5 秒生成 |
| App | 底部「播客」标签页 | 待真机确认播放 |

## 目录

```
podcast-demo/
├── feed.xml          # RSS，App 订阅的就是它
├── audio/            # 每天的 mp3
├── transcripts/      # 每天的逐字稿
├── publish.py        # 发布脚本：复制音频 + 更新 feed + git push
├── script.txt        # 当天稿件（可覆盖）
└── episode.mp3       # 当天音频（可覆盖）
```

## 手动出一集（验证用）

```bash
cd ~/CodexSpace/临时/chores/podcast-demo
export PATH="$HOME/Library/Python/3.9/bin:$PATH"

# 1. 写稿（或用编辑器写 script.txt）
cat > script.txt <<'EOF'
Welcome to Daily Brief. It's ...
EOF

# 2. 转语音
edge-tts --voice en-US-AriaNeural --rate=+5% \
  --text "$(cat script.txt)" --write-media episode.mp3

# 3. 发布
./publish.py --audio episode.mp3 \
  --title "Nov 21: ..." \
  --desc "Three stories: ..." \
  --transcript script.txt
```

## 做成 DSH 定时任务

大方向：**不用写代码流水线**，让 AI 每天在会话里跑一遍上面的流程。

在 DSH 里建一个定时任务，`rrule` 每天早上 7 点：

```
DTSTART;TZID=Asia/Shanghai:20261121T070000
RRULE:FREQ=DAILY;BYHOUR=7;BYMINUTE=0
```

`prompt` 建议这样写（可直接复制）：

```
跑今天的 Daily Brief 英文新闻播客，输出一集真实可播放的节目。

步骤：
1. 用 web_search 找过去 24 小时的 3-4 条国际要闻（政治/经济/科技各选）
2. 写成 300 词左右的英文播客稿，口语化、适合听力练习；
   开头报日期、报三条主题，结尾一句收束。不要用列表，要连成段落
3. 把稿子写到 ~/CodexSpace/临时/chores/podcast-demo/script.txt
4. 用 edge-tts 合成音频：
   export PATH="$HOME/Library/Python/3.9/bin:$PATH"
   cd ~/CodexSpace/临时/chores/podcast-demo
   edge-tts --voice en-US-AriaNeural --rate=+5% \
     --text "$(cat script.txt)" --write-media episode.mp3
5. 发布：
   ./publish.py --audio episode.mp3 \
     --title "<日期>: <三条主题一句话概括>" \
     --desc "<80 字以内英文摘要>" --transcript script.txt
6. 确认 feed 已更新：curl -s https://anyhow1234.github.io/daily-brief/feed.xml | grep -c "<item>"
   条目数应比昨天多 1
7. 汇报：这集的标题、时长、RSS 条目数；如果任何一步失败，把报错原文贴出来

约束：
- 只报道事实，不要编造具体数字和引语；不确定的用"据媒体报道"这类措辞
- 音频控制在 1.5-3 分钟（200-400 词）
- 不要改 feed.xml 的结构，只用 publish.py
```

## 注意事项

1. **GitHub Pages 国内访问**：`*.github.io` 在国内可能不稳。如果手机上拉不动，
   备选是把 `feed.xml` 里的音频地址换成 jsDelivr：
   `https://cdn.jsdelivr.net/gh/anyhow1234/daily-brief@main/audio/YYYY-MM-DD.mp3`
   需要改 `publish.py` 里的 `BASE_URL`，或者让 App 走自定义地址。
2. **仓库体积**：每集约 0.5-2MB，一年 200-700MB。GitHub 单仓库推荐 <1GB，
   一年内没问题；第二年可以考虑把老音频转存别处或删旧集。
3. **edge-tts 是非官方接口**：稳定、免费，但微软随时可能调整。失效时的备选是 macOS
   自带 `say`（音质差一些）或 Azure 付费 TTS（需要 Key）。
4. **内容版权**：稿子是 AI 改写的摘要，不是原文转载；引用具体报道时保留媒体名。
