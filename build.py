"""
스팀 프로필 스타일 GitHub 프로필 README 생성기.

사용법:
    python build.py

아래 CONFIG만 고치고 다시 실행하면 img/*.svg 와 README.md 가 새로 만들어집니다.
(별 개수·최근 업데이트 날짜는 GitHub API에서 자동으로 가져옵니다. 인터넷이 없으면 0으로 표시)
"""
import base64
import sys
import datetime as dt
import json
import pathlib
import urllib.request
from xml.sax.saxutils import escape

ROOT = pathlib.Path(__file__).parent
IMG = ROOT / "img"

# ─────────────────────────── CONFIG ───────────────────────────
CONFIG = {
    "user": "O3O-2022",
    "display_name": "Yogurt-Kr",
    "tagline": "게임 개발 · 3D 모델링 · 레벨 디자인",
    "since": "2022-06-10",  # GitHub 가입일 → 레벨(년차) 계산
    "avatar": "assets/avatar.jpg",
    # 헤더의 "현재 게임 중" 칸에 번갈아 표시될 프로그램들
    "now_playing": ["Blender", "Unity", "Unreal Engine", "Visual Studio"],
    "about": [
        "컴퓨터에 관심있음.",
        "블렌더로 모델링하고 애니메이션을 만들고, 게임 엔진으로 옮겨서",
        "레벨을 짜고 기획합니다. 만든 건 영상으로 편집해서 남겨요.",
    ],
    # 배지 쇼케이스: (이름, 설명, 아이콘, 색)
    "badges": [
        ("블렌더 모델링", "Blender Modeling", "cube", "#e87d0d"),
        ("블렌더 애니메이팅", "Blender Animation", "keys", "#f5a742"),
        ("레벨 디자인", "Level Design", "map", "#90ba3c"),
        ("게임 기획", "Game Design", "doc", "#c7d5e0"),
        ("영상 편집", "Video Editing", "film", "#d45bd0"),
        ("Unity", "Game Engine", "pad", "#c7d5e0"),
        ("Unreal Engine", "Game Engine", "ue", "#66c0f4"),
        ("C / C++", "Programming", "code", "#5b8fd4"),
    ],
    # 최근 활동(레포 카드): (레포 이름, 한 줄 설명, 캡슐 색 2개)
    "repos": [
        ("MiSide-PeaceMode", "MiSide 비공식 평화 모드 · BepInEx 6 플러그인", ("#5a1f3c", "#d4547f")),
        ("PeoplePlayground-Korean", "People Playground 비공식 한국어 패치", ("#3a2a12", "#d49a3a")),
        ("AnimeFlow", "RIFE 프레임 보간으로 애니를 더 부드럽게", ("#12304a", "#3fa3e0")),
        ("workspace-2", "Claude Code 스킬 · 서브세션 자동 배정", ("#1f2a1a", "#7fbf3f")),
    ],
    # 기술 배지 (shields.io): (표시 이름, simple-icons 로고 이름)
    "stack": [
        ("Blender", "blender"),
        ("Unity", "unity"),
        ("Unreal Engine", "unrealengine"),
        ("C", "c"),
        ("C++", "cplusplus"),
        ("C#", "dotnet"),
        ("Python", "python"),
        ("Git", "git"),
    ],
}
# ───────────────────────────────────────────────────────────────

# 스팀 프로필 색
BG_TOP = "#171a21"
BG = "#1b2838"
PANEL = "#16202d"
PANEL_HI = "#1f2c3c"
BLUE = "#66c0f4"
TEXT = "#c7d5e0"
DIM = "#8f98a0"
ONLINE = "#57cbde"
INGAME = "#90ba3c"
FONT = "'Motiva Sans','Segoe UI','Malgun Gothic','Apple SD Gothic Neo','Noto Sans KR',Arial,sans-serif"


def x(s):
    return escape(str(s))


def svg(w, h, body, label):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-label="{x(label)}" font-family="{FONT}">\n{body}\n</svg>\n'
    )


def panel_bg(w, h, rid="p"):
    return f"""
  <defs>
    <linearGradient id="{rid}bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{PANEL_HI}"/>
      <stop offset="1" stop-color="{PANEL}"/>
    </linearGradient>
  </defs>
  <rect width="{w}" height="{h}" rx="4" fill="url(#{rid}bg)"/>
  <rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="4" fill="none" stroke="#2a3f55"/>"""


def title_bar(w, title, right=""):
    r = f'<text x="{w-16}" y="27" text-anchor="end" font-size="13" fill="{DIM}">{x(right)}</text>' if right else ""
    return f"""
  <rect x="0" y="0" width="{w}" height="40" rx="4" fill="#000" opacity="0.25"/>
  <text x="16" y="27" font-size="15" fill="{TEXT}" letter-spacing="0.5">{x(title)}</text>
  {r}"""


# ─────────────── API (별, 업데이트 날짜) ───────────────
def fetch_repo(user, name):
    try:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{user}/{name}",
            headers={"User-Agent": "profile-readme-builder"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            d = json.load(r)
        return d.get("stargazers_count", 0), d.get("language") or "", (d.get("pushed_at") or "")[:10]
    except Exception:
        return 0, "", ""


# ─────────────── 헤더 ───────────────
def build_header(c):
    w, h = 900, 290
    avatar_b64 = base64.b64encode((ROOT / c["avatar"]).read_bytes()).decode()
    since = dt.date.fromisoformat(c["since"])
    level = max(1, (dt.date.today() - since).days // 365)

    n = len(c["now_playing"])
    dur = n * 3
    cyc = []
    for i, name in enumerate(c["now_playing"]):
        cyc.append(
            f'<text x="0" y="0" font-size="15" fill="{INGAME}" opacity="0">{x(name)}'
            f'<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.03;{1/n-0.03:.3f};{1/n:.3f};1" '
            f'dur="{dur}s" begin="{i*3}s" repeatCount="indefinite"/></text>'
        )
    cycling = "\n      ".join(cyc)

    # 떠다니는 먼지 입자
    import random
    random.seed(7)
    dots = []
    for _ in range(26):
        cx, cy, r = random.randint(0, w), random.randint(0, h), random.choice([1, 1, 1.5, 2])
        d = random.randint(6, 14)
        dots.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{BLUE}" opacity="0.0">'
            f'<animate attributeName="opacity" values="0;0.5;0" dur="{d}s" begin="{random.random()*d:.1f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="cy" values="{cy};{cy-30}" dur="{d}s" repeatCount="indefinite"/></circle>'
        )

    body = f"""
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{BG_TOP}"/>
      <stop offset="0.55" stop-color="{BG}"/>
      <stop offset="1" stop-color="#2a475e"/>
    </linearGradient>
    <radialGradient id="glow" cx="0.18" cy="0.5" r="0.5">
      <stop offset="0" stop-color="{BLUE}" stop-opacity="0.18"/>
      <stop offset="1" stop-color="{BLUE}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="frame" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{BLUE}"/>
      <stop offset="0.5" stop-color="#1a5c8a"/>
      <stop offset="1" stop-color="{ONLINE}"/>
      <animateTransform attributeName="gradientTransform" type="rotate" values="0 .5 .5;360 .5 .5" dur="6s" repeatCount="indefinite"/>
    </linearGradient>
    <clipPath id="av"><rect x="40" y="53" width="184" height="184"/></clipPath>
  </defs>
  <rect width="{w}" height="{h}" rx="6" fill="url(#bg)"/>
  <rect width="{w}" height="{h}" rx="6" fill="url(#glow)"/>
  {''.join(dots)}

  <!-- 아바타 + 움직이는 프레임 -->
  <rect x="34" y="47" width="196" height="196" fill="url(#frame)"/>
  <rect x="38" y="51" width="188" height="188" fill="#000"/>
  <image href="data:image/jpeg;base64,{avatar_b64}" x="40" y="53" width="184" height="184" clip-path="url(#av)" preserveAspectRatio="xMidYMid slice"/>

  <!-- 이름 -->
  <text x="258" y="88" font-size="30" fill="#ffffff">{x(c["display_name"])}</text>
  <text x="258" y="114" font-size="14" fill="{DIM}">@{x(c["user"])}</text>
  <text x="258" y="150" font-size="15" fill="{TEXT}">{x(c["tagline"])}</text>
  <rect x="258" y="166" width="300" height="1" fill="#3a4b5c"/>
  <text x="258" y="192" font-size="13" fill="{DIM}">github.com/{x(c["user"])}</text>

  <!-- 레벨 -->
  <text x="672" y="72" font-size="22" fill="{TEXT}">레벨</text>
  <g transform="translate(752,64)">
    <circle r="22" fill="none" stroke="{BLUE}" stroke-width="2.5">
      <animate attributeName="stroke-opacity" values="1;0.45;1" dur="2.4s" repeatCount="indefinite"/>
    </circle>
    <text y="8" text-anchor="middle" font-size="22" fill="#fff">{level}</text>
  </g>

  <!-- 접속 상태 (스팀 '게임 중' 박스) -->
  <g transform="translate(616,112)">
    <rect width="252" height="84" rx="3" fill="#000" opacity="0.35"/>
    <rect width="3" height="84" fill="{INGAME}"/>
    <text x="18" y="28" font-size="17" fill="{INGAME}">현재 게임 중</text>
    <circle cx="232" cy="22" r="5" fill="{INGAME}">
      <animate attributeName="opacity" values="1;0.2;1" dur="1.6s" repeatCount="indefinite"/>
    </circle>
    <g transform="translate(18,60)">
      {cycling}
    </g>
  </g>

  <!-- 버튼 -->
  <g transform="translate(616,214)">
    <rect width="252" height="34" rx="2" fill="#2a3f5a"/>
    <rect width="252" height="34" rx="2" fill="none" stroke="{BLUE}" stroke-opacity="0.35"/>
    <text x="126" y="22" text-anchor="middle" font-size="14" fill="{BLUE}">저장소 보기 ▸</text>
  </g>
"""
    return svg(w, h, body, f"{c['display_name']} — 프로필 헤더")


# ─────────────── 소개 ───────────────
def build_about(c):
    lines = c["about"]
    w, h = 900, 64 + 26 * len(lines)
    t = "".join(
        f'<text x="20" y="{70 + i*26}" font-size="15" fill="{TEXT}">{x(l)}</text>' for i, l in enumerate(lines)
    )
    return svg(w, h, panel_bg(w, h, "a") + title_bar(w, "소개") + t, "소개")


# ─────────────── 배지 아이콘 ───────────────
def icon(kind, col):
    s = f'stroke="{col}" stroke-width="2.4" fill="none" stroke-linejoin="round" stroke-linecap="round"'
    if kind == "cube":
        return (f'<path d="M0,-18 L16,-9 L16,9 L0,18 L-16,9 L-16,-9 Z" {s}/>'
                f'<path d="M-16,-9 L0,0 L16,-9 M0,0 L0,18" {s}/>')
    if kind == "keys":
        return (f'<path d="M-18,10 C-8,10 -6,-12 4,-12 S14,4 18,4" {s}/>'
                + "".join(f'<rect x="{px-4}" y="{py-4}" width="8" height="8" transform="rotate(45 {px} {py})" fill="{col}"/>'
                          for px, py in [(-18, 10), (4, -12), (18, 4)]))
    if kind == "map":
        cells = "".join(f'<rect x="{-18+i*12}" y="{-18+j*12}" width="12" height="12" stroke="{col}" stroke-opacity="0.45" fill="none"/>'
                        for i in range(3) for j in range(3))
        return cells + f'<path d="M-12,12 L-12,0 L0,0 L0,-12 L12,-12" {s}/><circle cx="12" cy="-12" r="3" fill="{col}"/>'
    if kind == "doc":
        return (f'<path d="M-13,-18 L7,-18 L14,-11 L14,18 L-13,18 Z" {s}/>'
                f'<path d="M-7,-6 L8,-6 M-7,2 L8,2 M-7,10 L2,10" {s}/>')
    if kind == "film":
        holes = "".join(f'<rect x="{-17+i*9}" y="-14" width="4" height="3" fill="{col}"/><rect x="{-17+i*9}" y="11" width="4" height="3" fill="{col}"/>' for i in range(4))
        return f'<rect x="-20" y="-17" width="40" height="34" rx="2" {s}/>' + holes + f'<path d="M-5,-7 L8,0 L-5,7 Z" fill="{col}"/>'
    if kind == "pad":
        return (f'<path d="M-20,4 C-20,-10 -12,-10 -6,-8 L6,-8 C12,-10 20,-10 20,4 C20,14 14,16 10,10 L-10,10 C-14,16 -20,14 -20,4 Z" {s}/>'
                f'<path d="M-12,-1 L-12,5 M-15,2 L-9,2" {s}/><circle cx="9" cy="0" r="1.8" fill="{col}"/><circle cx="13" cy="4" r="1.8" fill="{col}"/>')
    if kind == "ue":
        return f'<text y="7" text-anchor="middle" font-size="20" font-weight="bold" fill="{col}">UE</text>'
    if kind == "code":
        return f'<text y="7" text-anchor="middle" font-size="20" font-weight="bold" fill="{col}">{{ }}</text>'
    return ""


def build_badges(c):
    badges = c["badges"]
    cols = 4
    rows = (len(badges) + cols - 1) // cols
    cw, ch = 214, 116
    w, h = 900, 56 + rows * ch + 8
    out = [panel_bg(w, h, "b"), title_bar(w, "배지 쇼케이스", f"{len(badges)}개")]
    for i, (name, sub, kind, col) in enumerate(badges):
        gx = 16 + (i % cols) * (cw + 4)
        gy = 52 + (i // cols) * ch
        delay = (i * 0.37) % 3
        out.append(f"""
  <g transform="translate({gx},{gy})">
    <rect width="{cw}" height="{ch-8}" rx="3" fill="#000" opacity="0.22"/>
    <g transform="translate(46,54)">
      <circle r="31" fill="{col}" opacity="0.10"/>
      <circle r="31" fill="none" stroke="{col}" stroke-opacity="0.55" stroke-width="1.5"/>
      <g>
        <animateTransform attributeName="transform" type="translate" values="0 0;0 -3;0 0" dur="3s" begin="{delay:.2f}s" repeatCount="indefinite"/>
        {icon(kind, col)}
      </g>
    </g>
    <text x="88" y="48" font-size="14" fill="#fff">{x(name)}</text>
    <text x="88" y="70" font-size="12" fill="{DIM}">{x(sub)}</text>
  </g>""")
    return svg(w, h, "".join(out), "배지 쇼케이스")


# ─────────────── 레포 카드 (최근 활동) ───────────────
def build_repo_card(c, name, desc, colors):
    stars, lang, pushed = fetch_repo(c["user"], name)
    w, h = 440, 132
    c1, c2 = colors
    initials = "".join(p[0] for p in name.replace("_", "-").split("-") if p)[:3].upper()
    meta = " · ".join(filter(None, [lang, f"★ {stars}"]))
    upd = f"최근 업데이트 {pushed.replace('-', '.')}" if pushed else ""
    title = name if len(name) <= 24 else name[:23] + "…"
    body = f"""{panel_bg(w, h, "r")}
  <defs>
    <linearGradient id="cap" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/>
    </linearGradient>
    <linearGradient id="shine" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#fff" stop-opacity="0"/>
      <stop offset="0.5" stop-color="#fff" stop-opacity="0.25"/>
      <stop offset="1" stop-color="#fff" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="capc"><rect x="14" y="14" width="150" height="104" rx="2"/></clipPath>
  </defs>
  <rect x="14" y="14" width="150" height="104" rx="2" fill="url(#cap)"/>
  <text x="89" y="78" text-anchor="middle" font-size="34" font-weight="bold" fill="#fff" fill-opacity="0.9">{x(initials)}</text>
  <rect x="-60" y="14" width="50" height="104" fill="url(#shine)" clip-path="url(#capc)" transform="skewX(-15)">
    <animate attributeName="x" values="-60;260" dur="4s" repeatCount="indefinite"/>
  </rect>
  <text x="180" y="40" font-size="16" fill="#fff">{x(title)}</text>
  <text x="180" y="64" font-size="12.5" fill="{TEXT}">{x(desc)}</text>
  <text x="180" y="92" font-size="12.5" fill="{BLUE}">{x(meta)}</text>
  <text x="180" y="112" font-size="12" fill="{DIM}">{x(upd)}</text>
"""
    return svg(w, h, body, f"{name} 저장소")


# ─────────────── 구분선 / 섹션 제목 ───────────────
def build_divider():
    w, h = 900, 18
    body = f"""
  <defs>
    <linearGradient id="ln" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{BLUE}" stop-opacity="0"/>
      <stop offset="0.5" stop-color="{BLUE}" stop-opacity="0.6"/>
      <stop offset="1" stop-color="{BLUE}" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect x="0" y="8" width="{w}" height="1.5" fill="url(#ln)"/>
  <circle cx="0" cy="8.75" r="2.5" fill="#fff">
    <animate attributeName="cx" values="60;840;60" dur="7s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0;1;0;1;0" dur="7s" repeatCount="indefinite"/>
  </circle>"""
    return svg(w, h, body, "")


def build_title(text, right=""):
    w, h = 900, 40
    return svg(w, h, title_bar(w, text, right).replace('opacity="0.25"', f'opacity="1" fill-opacity="0.35"'), text)


# ─────────────── README ───────────────
def build_readme(c):
    u = c["user"]
    badge = lambda label, logo: (
        f'<img src="https://img.shields.io/badge/{label.replace(" ", "_").replace("-", "--").replace("+", "%2B").replace("#", "%23")}'
        f'-1b2838?style=for-the-badge&logo={logo}&logoColor=66c0f4" alt="{label}"/>'
    )
    stack = "\n".join(badge(n, l) for n, l in c["stack"])
    cards = "\n".join(
        f'<a href="https://github.com/{u}/{n}"><img src="img/repo-{n}.svg" width="49%" alt="{n}"/></a>'
        for n, _, _ in c["repos"]
    )
    streak = (
        f"https://streak-stats.demolab.com/?user={u}&background=16202D&border=2A3F55&ring=66C0F4&fire=90BA3C"
        f"&currStreakNum=FFFFFF&sideNums=C7D5E0&currStreakLabel=66C0F4&sideLabels=8F98A0&dates=8F98A0&locale=ko"
    )
    raw = f"https://raw.githubusercontent.com/{u}/{u}"
    return f"""<div align="center">

<a href="https://github.com/{u}?tab=repositories"><img src="img/header.svg" width="100%" alt="{c['display_name']} 프로필"/></a>

<img src="img/divider.svg" width="100%" alt=""/>

<img src="img/about.svg" width="100%" alt="소개"/>

<img src="img/badges.svg" width="100%" alt="배지 쇼케이스"/>

<img src="img/title-activity.svg" width="100%" alt="최근 활동"/>

{cards}

<img src="img/title-stack.svg" width="100%" alt="사용 도구"/>

{stack}

<img src="img/divider.svg" width="100%" alt=""/>

<details>
<summary><b>📊 활동 통계 펼치기</b></summary>
<br/>

<img src="{streak}" width="100%" alt="연속 기여"/>

<img src="{raw}/main/profile-3d-contrib/profile-night-view.svg" width="100%" alt="3D 기여 그래프"/>

<img src="{raw}/main/profile-summary-card-output/github_dark/0-profile-details.svg" width="100%" alt="프로필 요약"/>
<img src="{raw}/main/profile-summary-card-output/github_dark/1-repos-per-language.svg" width="49%" alt="언어별 저장소"/>
<img src="{raw}/main/profile-summary-card-output/github_dark/2-most-commit-language.svg" width="49%" alt="커밋 많은 언어"/>

</details>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="{raw}/output/snake-dark.svg"/>
  <source media="(prefers-color-scheme: light)" srcset="{raw}/output/snake.svg"/>
  <img alt="기여 스네이크" src="{raw}/output/snake.svg" width="100%"/>
</picture>

</div>
"""


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    c = CONFIG
    IMG.mkdir(exist_ok=True)
    files = {
        "header.svg": build_header(c),
        "about.svg": build_about(c),
        "badges.svg": build_badges(c),
        "divider.svg": build_divider(),
        "title-activity.svg": build_title("최근 활동", f"공개 저장소 {len(c['repos'])}개"),
        "title-stack.svg": build_title("사용 도구"),
    }
    for name, desc, cols in c["repos"]:
        files[f"repo-{name}.svg"] = build_repo_card(c, name, desc, cols)
    for fn, content in files.items():
        (IMG / fn).write_text(content, encoding="utf-8")
    (ROOT / "README.md").write_text(build_readme(c), encoding="utf-8")
    print(f"생성 완료: README.md + img/ {len(files)}개")


if __name__ == "__main__":
    main()
