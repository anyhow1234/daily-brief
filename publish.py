#!/usr/bin/env python3
"""把一集音频发布到 Daily Brief 的 GitHub Pages。

用法：
  ./publish.py --audio episode.mp3 --title "标题" --desc "描述" [--date 2026-11-20]
               [--duration 1:39] [--transcript script.txt]

做的事：
  1. 音频复制为 audio/<date>.mp3
  2. 在 feed.xml 顶部插入新 item（幂等：同日期会替换）
  3. git add / commit / push

环境：
  edge-tts 生成的 mp3 直接传进来即可；不需要任何密钥。
"""
import argparse
import datetime
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
FEED = os.path.join(ROOT, "feed.xml")
AUDIO_DIR = os.path.join(ROOT, "audio")
BASE_URL = "https://anyhow1234.github.io/daily-brief"
AUDIO_MIME = "audio/mpeg"


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--desc", default="")
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--duration", default="")
    ap.add_argument("--transcript", default="")
    args = ap.parse_args()

    if not os.path.isfile(args.audio):
        print(f"找不到音频：{args.audio}", file=sys.stderr)
        return 1
    os.makedirs(AUDIO_DIR, exist_ok=True)

    name = f"{args.date}.mp3"
    dest = os.path.join(AUDIO_DIR, name)
    shutil.copyfile(args.audio, dest)
    size = os.path.getsize(dest)

    duration = args.duration
    if not duration:
        try:
            out = subprocess.run(
                ["afinfo", dest], capture_output=True, text=True, timeout=30
            ).stdout
            m = re.search(r"estimated duration:\s*([\d.]+)", out)
            if m:
                total = int(float(m.group(1)))
                duration = f"{total // 60}:{total % 60:02d}"
        except Exception:
            pass
    duration = duration or "0:00"

    # 北京时间 07:00 发布
    pub = datetime.datetime.now() + datetime.timedelta(days=0)
    pubdate = datetime.datetime.now().strftime("%a, %d %b %Y 07:00:00 +0800")

    item = f"""    <item>
      <title>{esc(args.title)}</title>
      <description><![CDATA[{args.desc}]]></description>
      <pubDate>{pubdate}</pubDate>
      <guid isPermaLink="false">{args.date}</guid>
      <enclosure url="{BASE_URL}/audio/{name}" length="{size}" type="{AUDIO_MIME}"/>
      <itunes:duration>{duration}</itunes:duration>
    </item>
"""

    with open(FEED, encoding="utf-8") as f:
        xml = f.read()

    # 同一日期重复发布时先移除旧条目
    xml = re.sub(
        r"\s*<item>(?:(?!</item>).)*?<guid isPermaLink=\"false\">" + re.escape(args.date) +
        r"</guid>.*?</item>",
        "", xml, flags=re.S,
    )
    xml = xml.replace("  </channel>", item + "  </channel>")

    # 校验插入后能被解析
    import xml.etree.ElementTree as ET
    try:
        ET.fromstring(xml)
    except ET.ParseError as e:
        print(f"feed.xml 结构非法，已中止：{e}", file=sys.stderr)
        return 1

    with open(FEED, "w", encoding="utf-8") as f:
        f.write(xml)

    # 同时留一份逐字稿，方便以后做 transcript 页
    if args.transcript and os.path.isfile(args.transcript):
        with open(args.transcript, encoding="utf-8") as f:
            text = f.read()
        with open(os.path.join(ROOT, f"transcripts/{args.date}.txt"), "w", encoding="utf-8") as f:
            f.write(text)

    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    msg = f"{args.date}: {args.title}"
    r = subprocess.run(
        ["git", "-c", "user.name=anyhow1234", "-c", "user.email=wanghanxiao@lechun.cc",
         "commit", "-m", msg], cwd=ROOT, capture_output=True, text=True
    )
    if r.returncode != 0 and "nothing to commit" not in (r.stdout + r.stderr):
        print(r.stdout, r.stderr, file=sys.stderr)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)

    print(f"✅ 已发布 {args.date}")
    print(f"   音频：{BASE_URL}/audio/{name}  ({size/1024:.0f} KB, {duration})")
    print(f"   RSS ：{BASE_URL}/feed.xml")
    return 0


if __name__ == "__main__":
    sys.exit(main())
