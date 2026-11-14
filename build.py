"""
스팀 커뮤니티 프로필 레이아웃을 따라 만든 GitHub 프로필 README 생성기.

사용법:
    python build.py

아래 CONFIG만 고치고 다시 실행하면 img/*.svg 와 README.md 가 새로 만들어집니다.
(스타·팔로워·업데이트 날짜는 GitHub API에서 자동으로 가져옵니다. 인터넷이 없으면 0으로 표시)

치수와 색은 실제 스팀 프로필(기본 테마) 페이지에서 측정한 값입니다.
  전체 976px = 헤더 / 본문(왼쪽 652px 쇼케이스 + 오른쪽 288px 사이드바)
"""
import base64
import datetime as dt
import json
import pathlib
import sys
import urllib.request
from xml.sax.saxutils import escape

ROOT = pathlib.Path(__file__).parent
IMG = ROOT / "img"

# ─────────────────────────── CONFIG ───────────────────────────
CONFIG = {
    "user": "O3O-2022",
    "display_name": "Yogurt-Kr",
    "since": "2022-06-10",  # GitHub 가입일 → 레벨(년차)
    "avatar": "assets/avatar.jpg",
    # 헤더 요약(스팀의 '요약' 칸)
    "summary": [
        "컴퓨터에 관심있음.",
        "게임 개발 · 3D 모델링 · 레벨 디자인",
    ],
    # 헤더 오른쪽 '대표 배지'
    "featured_badge": ("블렌더 모델링", "대표 스킬", "cube", "#e87d0d"),
    # 사이드바 '현재 게임 중'에 번갈아 표시
    "now_playing": ["Blender", "Unity", "Unreal Engine", "Visual Studio"],
    # 정보 상자(Custom Info Box)
    "info_title": "정보 상자",
    "info": [
        "블렌더로 모델링하고 애니메이션을 만든 다음 게임 엔진으로 옮겨서",
        "레벨을 짜고 기획합니다. 만든 건 영상으로 편집해서 남겨요.",
        "",
        "Unity · Unreal Engine · C / C++ 로 게임을 만들고 있어요.",
    ],
    # 스킬 쇼케이스(희귀 도전 과제 쇼케이스 자리): (이름, 아이콘, 색)
    "skills": [
        ("블렌더 모델링", "cube", "#e87d0d"),
        ("블렌더 애니메이팅", "keys", "#f5a742"),
        ("레벨 디자인", "map", "#90ba3c"),
        ("게임 기획", "doc", "#c7d5e0"),
        ("영상 편집", "film", "#d45bd0"),
        ("Unity", "pad", "#c7d5e0"),
        ("Unreal Engine", "ue", "#66c0f4"),
        ("C / C++", "code", "#5b8fd4"),
    ],
    # 최근 활동(레포): (레포 이름, 한 줄 설명, 캡슐 색 2개)
    "repos": [
        ("MiSide-PeaceMode", "MiSide 비공식 평화 모드 · BepInEx 플러그인", ("#5a1f3c", "#d4547f")),
        ("PeoplePlayground-Korean", "People Playground 비공식 한국어 패치", ("#3a2a12", "#d49a3a")),
        ("AnimeFlow", "RIFE 프레임 보간으로 애니를 더 부드럽게", ("#12304a", "#3fa3e0")),
        ("workspace-2", "Claude Code 스킬 · 서브세션 자동 배정", ("#1f2a1a", "#7fbf3f")),
    ],
    # 사이드바 '사용 도구'(스팀의 '그룹' 자리): (이름, 설명, 약자, 색)
    "tools": [
        ("Blender", "모델링 · 애니메이션", "B", "#e87d0d"),
        ("Unity", "게임 엔진", "U", "#c7d5e0"),
        ("Unreal Engine", "게임 엔진 · 레벨 디자인", "UE", "#66c0f4"),
        ("C / C++", "프로그래밍", "C", "#5b8fd4"),
        ("C#", "Unity 스크립트 · 모딩", "C#", "#9b6bd6"),
        ("Python", "도구 · 자동화", "Py", "#e0c341"),
    ],
}
# ───────────────────────────────────────────────────────────────

# ── 스팀 기본 테마에서 측정한 값 ──
PAGE = "#000000"            # 페이지 배경 (점무늬 텍스처)
CONTENT = "#20212d"         # rgba(34,35,48,.93) 를 검정 위에 합성
BLOCK = "#16171f"           # 그 위 rgba(0,0,0,.3)  (쇼케이스 / 사이드바)
INNER = "#0f1016"           # 한 번 더 rgba(0,0,0,.3) (쇼케이스 안쪽 / 최근 활동 행)
WHITE = "#ffffff"
NAME = "#ebebeb"
SUB = "#c4c4c4"
GRAY = "#969696"
COUNT = "#9b9b9b"
OFFLINE = "#898989"
ONLINE = "#57cbde"
INGAME = "#90ba3c"
LINK = "#ebebeb"
FONT = "'Motiva Sans','Segoe UI','Malgun Gothic','Apple SD Gothic Neo','Noto Sans KR',Arial,sans-serif"
LIGHT = 'font-weight="300"'

LEFT_W, RIGHT_W, FULL_W = 652, 288, 976
LEVEL_COLORS = ["#9b9b9b", "#c02942", "#d95b43", "#fecc23", "#467a3c",
                "#4e8ddb", "#7652c9", "#c252c9", "#542437", "#997c52"]


def x(s):
    return escape(str(s))


def svg(w, h, body, label=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-label="{x(label)}" font-family="{FONT}">\n{body}\n</svg>\n'
    )


def dots(rid, w, h, opacity=0.05):
    """스팀 프로필 배경의 점무늬 텍스처."""
    return (f'<defs><pattern id="{rid}" width="4" height="4" patternUnits="userSpaceOnUse">'
            f'<rect x="1" y="1" width="1" height="1" fill="#fff" opacity="{opacity}"/></pattern></defs>'
            f'<rect width="{w}" height="{h}" fill="url(#{rid})"/>')


def showcase_header(w, title, right=""):
    """스팀 쇼케이스 제목 바: linear-gradient(90deg, rgba(115,173,184,.247), rgba(43,45,68,.93) 90%), 16px/200."""
    r = (f'<text x="{w-10}" y="26" text-anchor="end" font-size="13" fill="{GRAY}">{x(right)}</text>'
         if right else "")
    return f"""
  <defs>
    <linearGradient id="sh" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#73adb8" stop-opacity="0.247"/>
      <stop offset="0.9" stop-color="#2b2d44" stop-opacity="0.93"/>
    </linearGradient>
  </defs>
  <rect width="{w}" height="40" fill="url(#sh)"/>
  <text x="10" y="26" font-size="16" {LIGHT} fill="{WHITE}">{x(title)}</text>
  {r}"""


# ─────────────── API ───────────────
def api(path):
    try:
        req = urllib.request.Request(f"https://api.github.com/{path}",
                                     headers={"User-Agent": "profile-readme-builder"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.load(r)
    except Exception:
        return {}


def ko_date(iso):
    if not iso:
        return ""
    d = dt.date.fromisoformat(iso[:10])
    return f"{d.year}년 {d.month}월 {d.day}일"


# ─────────────── 아이콘 ───────────────
def icon(kind, col, scale=1.0):
    s = f'stroke="{col}" stroke-width="2.4" fill="none" stroke-linejoin="round" stroke-linecap="round"'
    g = ""
    if kind == "cube":
        g = (f'<path d="M0,-18 L16,-9 L16,9 L0,18 L-16,9 L-16,-9 Z" {s}/>'
             f'<path d="M-16,-9 L0,0 L16,-9 M0,0 L0,18" {s}/>')
    elif kind == "keys":
        g = (f'<path d="M-18,10 C-8,10 -6,-12 4,-12 S14,4 18,4" {s}/>'
             + "".join(f'<rect x="{px-4}" y="{py-4}" width="8" height="8" transform="rotate(45 {px} {py})" fill="{col}"/>'
                       for px, py in [(-18, 10), (4, -12), (18, 4)]))
    elif kind == "map":
        g = "".join(f'<rect x="{-18+i*12}" y="{-18+j*12}" width="12" height="12" stroke="{col}" stroke-opacity="0.45" fill="none"/>'
                    for i in range(3) for j in range(3))
        g += f'<path d="M-12,12 L-12,0 L0,0 L0,-12 L12,-12" {s}/><circle cx="12" cy="-12" r="3" fill="{col}"/>'
    elif kind == "doc":
        g = (f'<path d="M-13,-18 L7,-18 L14,-11 L14,18 L-13,18 Z" {s}/>'
             f'<path d="M-7,-6 L8,-6 M-7,2 L8,2 M-7,10 L2,10" {s}/>')
    elif kind == "film":
        g = f'<rect x="-20" y="-17" width="40" height="34" rx="2" {s}/>'
        g += "".join(f'<rect x="{-17+i*9}" y="-14" width="4" height="3" fill="{col}"/>'
                     f'<rect x="{-17+i*9}" y="11" width="4" height="3" fill="{col}"/>' for i in range(4))
        g += f'<path d="M-5,-7 L8,0 L-5,7 Z" fill="{col}"/>'
    elif kind == "pad":
        g = (f'<path d="M-20,4 C-20,-10 -12,-10 -6,-8 L6,-8 C12,-10 20,-10 20,4 C20,14 14,16 10,10 L-10,10 C-14,16 -20,14 -20,4 Z" {s}/>'
             f'<path d="M-12,-1 L-12,5 M-15,2 L-9,2" {s}/><circle cx="9" cy="0" r="1.8" fill="{col}"/><circle cx="13" cy="4" r="1.8" fill="{col}"/>')
    elif kind == "ue":
        g = f'<text y="7" text-anchor="middle" font-size="20" font-weight="bold" fill="{col}">UE</text>'
    elif kind == "code":
        g = f'<text y="7" text-anchor="middle" font-size="20" font-weight="bold" fill="{col}">{{ }}</text>'
    return f'<g transform="scale({scale})">{g}</g>' if scale != 1 else g


def badge_tile(cx, cy, size, kind, col, frame=True):
    """스팀 배지/도전 과제 아이콘처럼 보이는 정사각 타일."""
    h = size / 2
    fr = (f'<rect x="{cx-h}" y="{cy-h}" width="{size}" height="{size}" fill="none" stroke="{col}" stroke-opacity="0.6"/>'
          if frame else "")
    return (f'<rect x="{cx-h}" y="{cy-h}" width="{size}" height="{size}" fill="{col}" fill-opacity="0.12"/>{fr}'
            f'<g transform="translate({cx},{cy})">{icon(kind, col, size/64)}</g>')


# ─────────────── 헤더 (976 x 224) ───────────────
def build_header(c, stats):
    w, h = FULL_W, 224
    av = base64.b64encode((ROOT / c["avatar"]).read_bytes()).decode()
    level = max(1, (dt.date.today() - dt.date.fromisoformat(c["since"])).days // 365)
    lvl_col = LEVEL_COLORS[min(level // 10, 9)]
    fb_name, fb_sub, fb_icon, fb_col = c["featured_badge"]
    summary = "".join(f'<text x="228" y="{126 + i*20}" font-size="13" fill="{SUB}">{x(t)}</text>'
                      for i, t in enumerate(c["summary"]))
    body = f"""
  <defs>
    <radialGradient id="g1" cx="1" cy="1" r="0.9">
      <stop offset="0" stop-color="#6d262c" stop-opacity="0.3"/><stop offset="1" stop-color="#6d262c" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="g2" cx="0" cy="1" r="0.9">
      <stop offset="0" stop-color="#32ffc1" stop-opacity="0.1"/><stop offset="1" stop-color="#32ffc1" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="frame" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0.05" stop-color="#8fb93b"/><stop offset="0.95" stop-color="#6e8c31"/>
    </linearGradient>
    <clipPath id="av"><rect x="26" y="36" width="164" height="164"/></clipPath>
  </defs>
  <rect width="{w}" height="{h}" fill="{PAGE}"/>
  {dots("hd", w, h)}
  <rect width="{w}" height="{h}" fill="{CONTENT}" opacity="0.93"/>
  <rect width="{w}" height="{h}" fill="url(#g1)"/>
  <rect width="{w}" height="{h}" fill="url(#g2)"/>

  <!-- 아바타: '게임 중' 상태의 초록 테두리 -->
  <rect x="24" y="34" width="168" height="168" fill="url(#frame)"/>
  <image href="data:image/jpeg;base64,{av}" x="26" y="36" width="164" height="164" clip-path="url(#av)" preserveAspectRatio="xMidYMid slice"/>

  <!-- 이름 / 실명 자리 / 요약 -->
  <text x="228" y="62" font-size="24" {LIGHT} fill="{WHITE}">{x(c["display_name"])}<tspan font-size="12" dx="6" dy="-3" fill="{SUB}">▾</tspan></text>
  <text x="228" y="88" font-size="13" fill="{SUB}">@{x(c["user"])}</text>
  {summary}

  <!-- 레벨 -->
  <text x="676" y="62" font-size="24" {LIGHT} fill="{WHITE}">레벨</text>
  <circle cx="752" cy="54" r="15" fill="none" stroke="{lvl_col}" stroke-width="2"/>
  <text x="752" y="60" text-anchor="middle" font-size="16" {LIGHT} fill="{WHITE}">{level}</text>

  <!-- 대표 배지 -->
  <rect x="676" y="87" width="288" height="70" fill="#000" opacity="0.2"/>
  {badge_tile(711, 122, 54, fb_icon, fb_col, frame=False)}
  <text x="746" y="118" font-size="12" fill="{WHITE}">{x(fb_name)}</text>
  <text x="746" y="135" font-size="12" fill="{NAME}">{x(fb_sub)}</text>
"""
    return svg(w, h, body, f"{c['display_name']} 프로필 헤더")


# ─────────────── 사이드바 (288 x ?) ───────────────
def build_sidebar(c, stats):
    w = RIGHT_W
    y = 10
    out = []
    n = len(c["now_playing"])
    dur = n * 3
    cyc = "".join(
        f'<text x="10" y="{y+52}" font-size="14" fill="{INGAME}" opacity="0">{x(g)}'
        f'<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.03;{1/n-0.03:.3f};{1/n:.3f};1" '
        f'dur="{dur}s" begin="{i*3}s" repeatCount="indefinite"/></text>'
        for i, g in enumerate(c["now_playing"]))
    out.append(f'<text x="10" y="{y+22}" font-size="20" {LIGHT} fill="{INGAME}">현재 게임 중</text>{cyc}')
    y += 90

    def count(label, total, yy):
        return (f'<text x="10" y="{yy}" font-size="14" fill="{LINK}">{x(label)}'
                f'<tspan dx="8" font-size="24" {LIGHT} fill="{COUNT}">{x(total)}</tspan></text>')

    out.append(count("배지", len(c["skills"]), y + 14))
    y += 30
    for i, (_, kind, col) in enumerate(c["skills"]):
        cx = 10 + 27 + (i % 4) * 66
        cy = y + 27 + (i // 4) * 62
        out.append(badge_tile(cx, cy, 54, kind, col, frame=False))
    y += ((len(c["skills"]) + 3) // 4) * 62 + 24

    for label, total in [("저장소", stats["repos"]), ("받은 스타", stats["stars"]),
                         ("팔로워", stats["followers"]), ("팔로잉", stats["following"])]:
        out.append(count(label, total, y + 14))
        y += 30
    y += 20

    out.append(count("사용 도구", len(c["tools"]), y + 14))
    y += 34
    for name, sub, abbr, col in c["tools"]:
        out.append(
            f'<rect x="10" y="{y}" width="32" height="32" fill="{col}" fill-opacity="0.15" stroke="{col}" stroke-opacity="0.5"/>'
            f'<text x="26" y="{y+21}" text-anchor="middle" font-size="12" font-weight="bold" fill="{col}">{x(abbr)}</text>'
            f'<text x="52" y="{y+14}" font-size="13" fill="{NAME}">{x(name)}</text>'
            f'<text x="52" y="{y+30}" font-size="12" fill="{GRAY}">{x(sub)}</text>')
        y += 44
    h = y + 10
    body = f'<rect width="{w}" height="{h}" fill="{CONTENT}"/><rect width="{w}" height="{h}" fill="{BLOCK}"/>' + "".join(out)
    return svg(w, h, body, "사이드바")


# ─────────────── 스킬 쇼케이스 (희귀 도전 과제 쇼케이스 형식) ───────────────
def build_skills(c, stats):
    w = LEFT_W
    skills = c["skills"]
    tile, gap = 64, 12
    n = len(skills)
    row_w = n * tile + (n - 1) * gap
    x0 = (w - row_w) / 2
    tiles = []
    for i, (name, kind, col) in enumerate(skills):
        cx = x0 + tile / 2 + i * (tile + gap)
        tiles.append(badge_tile(cx, 90, tile, kind, col))
        parts = name.split(" ", 1) if len(name) > 6 and " " in name and name != "C / C++" else [name]
        for j, part in enumerate(parts):
            tiles.append(f'<text x="{cx}" y="{140 + j*14}" text-anchor="middle" font-size="11" fill="{GRAY}">{x(part)}</text>')
    stat_items = [(len(skills), "스킬"), (stats["repos"], "공개 저장소"), (stats["stars"], "받은 스타")]
    st = "".join(
        f'<text x="{18 + i*150}" y="210" font-size="34" {LIGHT} fill="{WHITE}">{v}</text>'
        f'<text x="{18 + i*150}" y="234" font-size="17" fill="{COUNT}">{x(l)}</text>'
        for i, (v, l) in enumerate(stat_items))
    h = 254
    body = (f'<rect width="{w}" height="{h}" fill="{CONTENT}"/><rect width="{w}" height="{h}" fill="{BLOCK}"/>'
            + showcase_header(w, "스킬 쇼케이스")
            + f'<rect x="10" y="50" width="{w-20}" height="114" fill="{INNER}"/>'
            + "".join(tiles)
            + f'<rect x="10" y="170" width="{w-20}" height="76" fill="{INNER}"/>' + st)
    return svg(w, h, body, "스킬 쇼케이스")


# ─────────────── 정보 상자 ───────────────
def build_info(c):
    w = LEFT_W
    lines = c["info"]
    h = 40 + 16 + len(lines) * 20 + 16
    t = "".join(f'<text x="18" y="{72 + i*20}" font-size="13" fill="{SUB}">{x(l)}</text>' for i, l in enumerate(lines))
    body = (f'<rect width="{w}" height="{h}" fill="{CONTENT}"/><rect width="{w}" height="{h}" fill="{BLOCK}"/>'
            + showcase_header(w, c["info_title"])
            + f'<rect x="10" y="48" width="{w-20}" height="{h-56}" fill="{INNER}"/>' + t)
    return svg(w, h, body, c["info_title"])


# ─────────────── 최근 활동 ───────────────
def build_activity_top(c, stats):
    w, h = LEFT_W, 48
    body = (f'<rect width="{w}" height="{h}" fill="{CONTENT}"/><rect width="{w}" height="{h}" fill="{BLOCK}"/>'
            + showcase_header(w, "최근 활동", f"공개 저장소 {stats['repos']}개"))
    return svg(w, h, body, "최근 활동")


def build_repo_row(c, name, desc, colors, info):
    """스팀 recent_game 행: 캡슐 184x69, 이름 14px, 오른쪽 정렬 2줄 13px."""
    w, h = LEFT_W, 93
    c1, c2 = colors
    initials = "".join(p[0] for p in name.replace("_", "-").split("-") if p)[:3].upper()
    lang = info.get("language") or ""
    stars = info.get("stargazers_count", 0)
    pushed = ko_date(info.get("pushed_at", ""))
    body = f"""
  <defs>
    <linearGradient id="cap" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/>
    </linearGradient>
    <linearGradient id="shine" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.5" stop-color="#fff" stop-opacity="0.22"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="cc"><rect x="18" y="8" width="184" height="69"/></clipPath>
  </defs>
  <rect width="{w}" height="{h}" fill="{CONTENT}"/><rect width="{w}" height="{h}" fill="{BLOCK}"/>
  <rect x="10" y="0" width="{w-20}" height="85" fill="{INNER}"/>
  <rect x="18" y="8" width="184" height="69" fill="url(#cap)"/>
  <text x="110" y="54" text-anchor="middle" font-size="28" font-weight="bold" fill="#fff" fill-opacity="0.9">{x(initials)}</text>
  <g clip-path="url(#cc)">
    <rect x="-40" y="8" width="40" height="69" fill="url(#shine)" transform="skewX(-15)">
      <animate attributeName="x" values="-40;300" dur="5s" repeatCount="indefinite"/>
    </rect>
  </g>
  <text x="214" y="28" font-size="14" fill="{WHITE}">{x(name)}</text>
  <text x="214" y="48" font-size="12" fill="{GRAY}">{x(desc)}</text>
  <text x="{w-20}" y="54" text-anchor="end" font-size="13" fill="{GRAY}">{x(lang)}{' · ' if lang else ''}★ {stars} 스타</text>
  <text x="{w-20}" y="72" text-anchor="end" font-size="13" fill="{GRAY}">최근 업데이트 {x(pushed)}</text>
"""
    return svg(w, h, body, f"{name} 저장소")


def build_activity_bottom(c):
    w, h = LEFT_W, 40
    body = (f'<rect width="{w}" height="{h}" fill="{CONTENT}"/><rect width="{w}" height="{h}" fill="{BLOCK}"/>'
            f'<text x="{w-10}" y="24" text-anchor="end" font-size="13" fill="{GRAY}">보기 '
            f'<tspan fill="{LINK}">모든 저장소</tspan><tspan fill="#555">  |  </tspan>'
            f'<tspan fill="{LINK}">스타</tspan><tspan fill="#555">  |  </tspan>'
            f'<tspan fill="{LINK}">팔로워</tspan></text>')
    return svg(w, h, body, "모든 저장소 보기")


# ─────────────── README ───────────────
def build_readme(c):
    u = c["user"]
    lw = f"{LEFT_W / FULL_W * 100:.1f}%"
    rw = f"{RIGHT_W / FULL_W * 100:.1f}%"
    rows = "".join(
        f'<a href="https://github.com/{u}/{n}"><img src="img/repo-{n}.svg" width="{lw}" alt="{n}"/></a><br/>\n'
        for n, _, _ in c["repos"])
    streak = (f"https://streak-stats.demolab.com/?user={u}&background=16171F&border=2B2D44&ring=57CBDE&fire=90BA3C"
              f"&currStreakNum=FFFFFF&sideNums=EBEBEB&currStreakLabel=57CBDE&sideLabels=969696&dates=969696&locale=ko")
    raw = f"https://raw.githubusercontent.com/{u}/{u}"
    return f"""<a href="https://github.com/{u}?tab=repositories"><img src="img/header.svg" width="100%" alt="{c['display_name']} 프로필"/></a>

<div>
<img src="img/sidebar.svg" align="right" width="{rw}" alt="사이드바"/>
<img src="img/skills.svg" width="{lw}" alt="스킬 쇼케이스"/><br/>
<img src="img/info.svg" width="{lw}" alt="정보 상자"/><br/>
<img src="img/activity-top.svg" width="{lw}" alt="최근 활동"/><br/>
{rows}<a href="https://github.com/{u}?tab=repositories"><img src="img/activity-bottom.svg" width="{lw}" alt="모든 저장소 보기"/></a>
</div>

<br clear="all"/>

<details>
<summary><b>활동 통계 펼치기</b></summary>
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
"""


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    c = CONFIG
    u = c["user"]
    user = api(f"users/{u}")
    repo_info = {n: api(f"repos/{u}/{n}") for n, _, _ in c["repos"]}
    all_repos = api(f"users/{u}/repos?per_page=100") or []
    stats = {
        "repos": sum(1 for r in all_repos if isinstance(r, dict) and not r.get("fork") and r.get("name") != u)
        or len(c["repos"]),
        "stars": sum(r.get("stargazers_count", 0) for r in all_repos if isinstance(r, dict)),
        "followers": user.get("followers", 0),
        "following": user.get("following", 0),
    }
    IMG.mkdir(exist_ok=True)
    for old in IMG.glob("*.svg"):
        old.unlink()
    files = {
        "header.svg": build_header(c, stats),
        "sidebar.svg": build_sidebar(c, stats),
        "skills.svg": build_skills(c, stats),
        "info.svg": build_info(c),
        "activity-top.svg": build_activity_top(c, stats),
        "activity-bottom.svg": build_activity_bottom(c),
    }
    for n, desc, cols in c["repos"]:
        files[f"repo-{n}.svg"] = build_repo_row(c, n, desc, cols, repo_info.get(n, {}))
    for fn, content in files.items():
        (IMG / fn).write_text(content, encoding="utf-8")
    (ROOT / "README.md").write_text(build_readme(c), encoding="utf-8")
    print(f"생성 완료: README.md + img/ {len(files)}개 · stats={stats}")


if __name__ == "__main__":
    main()
