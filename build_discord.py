"""
디스코드 스타일 GitHub 프로필 시안 생성기.

    python build_discord.py

discord/ 폴더에 SVG와 미리보기(preview.html)를 만듭니다. README는 건드리지 않아요.
CONFIG·아이콘·API는 build.py(스팀 버전)의 것을 그대로 씁니다.
"""
import base64
import datetime as dt
import pathlib
import sys

from build import CONFIG, ROOT, api, icon, ko_date, x

OUT = ROOT / "discord"

# ── 디스코드 다크 테마 색 ──
RAIL = "#1e1f22"
SIDE = "#2b2d31"
CHAT = "#313338"
POP = "#232428"
POP_IN = "#111214"
HOVER = "#404249"
INPUT = "#383a40"
TEXT = "#dbdee1"
HEAD = "#f2f3f5"
MUTED = "#949ba4"
CHAN = "#80848e"
BLURPLE = "#5865f2"
LINK = "#00a8fc"
ONLINE = "#23a55a"
FONT = "'gg sans','Noto Sans KR','Malgun Gothic','Apple SD Gothic Neo','Segoe UI',Arial,sans-serif"


def svg(w, h, body, label=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{x(label)}" font-family="{FONT}">\n{body}\n</svg>\n')


def avatar_b64(c):
    return base64.b64encode((ROOT / c["avatar"]).read_bytes()).decode()


def avatar(cid, b64, cx, cy, r, ring_col, status=True):
    """둥근 아바타 + 오른쪽 아래 온라인 점(배경색 테두리)."""
    s = ""
    if status:
        sr = max(5, r * 0.32)
        sx, sy = cx + r * 0.72, cy + r * 0.72
        s = (f'<circle cx="{sx}" cy="{sy}" r="{sr + r * 0.12 + 1.5}" fill="{ring_col}"/>'
             f'<circle cx="{sx}" cy="{sy}" r="{sr}" fill="{ONLINE}"/>')
    return (f'<defs><clipPath id="{cid}"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath></defs>'
            f'<image href="data:image/jpeg;base64,{b64}" x="{cx-r}" y="{cy-r}" width="{r*2}" height="{r*2}" '
            f'clip-path="url(#{cid})" preserveAspectRatio="xMidYMid slice"/>{s}')


def cycle(items, x0, y0, attrs, dur_each=3):
    """여러 글자를 번갈아 보여주는 SMIL 애니메이션."""
    n = len(items)
    total = n * dur_each
    out = []
    for i, t in enumerate(items):
        a, b = i / n, (i + 1) / n
        kt = f"0;{a:.4f};{a+0.02:.4f};{b-0.02:.4f};{b:.4f};1"
        vals = "0;0;1;1;0;0"
        if i == 0:
            kt, vals = f"0;{b-0.02:.4f};{b:.4f};{1-0.02:.4f};1", "1;1;0;0;1"
        out.append(f'<text x="{x0}" y="{y0}" {attrs} opacity="{1 if i == 0 else 0}">{x(t)}'
                   f'<animate attributeName="opacity" values="{vals}" keyTimes="{kt}" dur="{total}s" '
                   f'repeatCount="indefinite"/></text>')
    return "".join(out)


def hashtag(px, py, col):
    return (f'<path d="M{px+3},{py-7} L{px+1},{py+7} M{px+9},{py-7} L{px+7},{py+7} '
            f'M{px-1},{py-2.5} L{px+12},{py-2.5} M{px-2},{py+2.5} L{px+11},{py+2.5}" '
            f'stroke="{col}" stroke-width="1.6" fill="none" stroke-linecap="round"/>')


def speaker(px, py, col):
    return (f'<path d="M{px},{py-3} L{px+3},{py-3} L{px+7},{py-7} L{px+7},{py+7} L{px+3},{py+3} L{px},{py+3} Z" fill="{col}"/>'
            f'<path d="M{px+10},{py-4} Q{px+13},{py} {px+10},{py+4}" stroke="{col}" stroke-width="1.6" fill="none"/>')


# ─────────────── 서버 창 (976 x 560) ───────────────
SERVERS = [("cube", "#e87d0d"), ("keys", "#f5a742"), ("map", "#90ba3c"), ("doc", "#c7d5e0"),
           ("film", "#d45bd0"), ("pad", "#c7d5e0"), ("ue", "#66c0f4"), ("code", "#5b8fd4")]
CHANNELS = [
    ("정보", ["환영", "공지"]),
    ("블렌더", ["모델링", "애니메이팅"]),
    ("게임 개발", ["unity", "unreal-engine", "c-cpp", "레벨디자인", "기획"]),
    ("영상", ["영상편집"]),
]


def build_server(c, stats, b64):
    W, H = 976, 600
    b = [f'<rect width="{W}" height="{H}" rx="10" fill="{CHAT}"/>']
    # 서버 레일
    b.append(f'<path d="M10,0 H72 V{H} H10 A10,10 0 0 1 0,{H-10} V10 A10,10 0 0 1 10,0 Z" fill="{RAIL}"/>')
    b.append(f'<rect x="12" y="12" width="48" height="48" rx="16" fill="{BLURPLE}"/>'
             f'<text x="36" y="43" text-anchor="middle" font-size="20" font-weight="700" fill="#fff">Y</text>'
             f'<rect x="20" y="70" width="32" height="2" rx="1" fill="#35363c"/>')
    for i, (kind, col) in enumerate(SERVERS):
        cy = 106 + i * 56
        active = i == 0
        b.append(f'<rect x="12" y="{cy-24}" width="48" height="48" rx="{16 if active else 24}" '
                 f'fill="{col if active else "#313338"}" fill-opacity="{0.25 if active else 1}"/>'
                 f'<g transform="translate(36,{cy})">{icon(kind, col, 0.62)}</g>')
        if active:
            b.append(f'<rect x="-4" y="{cy-20}" width="8" height="40" rx="4" fill="#fff"/>')
    # 채널 목록
    sx = 72
    b.append(f'<rect x="{sx}" width="240" height="{H}" fill="{SIDE}"/>'
             f'<rect x="{sx}" width="240" height="48" fill="{SIDE}"/>'
             f'<rect x="{sx}" y="48" width="240" height="1" fill="#1f2023"/>'
             f'<text x="{sx+16}" y="30" font-size="15" font-weight="700" fill="{HEAD}">{x(c["display_name"])}의 작업실</text>'
             f'<path d="M{sx+214},22 l4,4 l4,-4" stroke="{HEAD}" stroke-width="2" fill="none"/>')
    y = 72
    for cat, chans in CHANNELS:
        b.append(f'<path d="M{sx+8},{y-6} l3,3 l3,-3" stroke="{MUTED}" stroke-width="1.5" fill="none"/>'
                 f'<text x="{sx+18}" y="{y}" font-size="12" font-weight="700" fill="{MUTED}" '
                 f'letter-spacing=".4">{x(cat.upper())}</text>')
        y += 24
        for ch in chans:
            sel = ch == "환영"
            if sel:
                b.append(f'<rect x="{sx+8}" y="{y-17}" width="224" height="32" rx="4" fill="{HOVER}"/>')
            col = "#fff" if sel else CHAN
            b.append(hashtag(sx + 18, y - 1, col)
                     + f'<text x="{sx+40}" y="{y+4}" font-size="15" font-weight="{600 if sel else 500}" '
                       f'fill="{col if sel else MUTED}">{x(ch)}</text>')
            y += 30
        y += 6
    # 음성 채널 + 말하는 중(초록 링 깜빡임)
    b.append(speaker(sx + 18, y - 1, CHAN)
             + f'<text x="{sx+40}" y="{y+4}" font-size="15" font-weight="500" fill="{MUTED}">작업 중</text>')
    y += 28
    b.append(f'<circle cx="{sx+52}" cy="{y}" r="11" fill="none" stroke="{ONLINE}" stroke-width="2">'
             f'<animate attributeName="stroke-opacity" values="1;0.15;1;1;0.2;1" dur="2.4s" repeatCount="indefinite"/></circle>'
             + avatar("va", b64, sx + 52, y, 9, SIDE, status=False)
             + f'<text x="{sx+70}" y="{y+5}" font-size="14" fill="{TEXT}">{x(c["display_name"])}</text>')
    # 사용자 패널
    py = H - 52
    b.append(f'<path d="M{sx},{py} H{sx+240} V{H} H{sx} Z" fill="{POP}"/>'
             + avatar("ua", b64, sx + 24, py + 26, 16, POP)
             + f'<text x="{sx+50}" y="{py+22}" font-size="14" font-weight="600" fill="{HEAD}">{x(c["display_name"])}</text>'
             + cycle([f"{n} 하는 중" for n in c["now_playing"]], sx + 50, py + 39, f'font-size="12" fill="{MUTED}"'))
    for i, ic in enumerate(["mic", "head", "gear"]):
        ix = sx + 160 + i * 26
        if ic == "mic":
            g = (f'<rect x="{ix-3}" y="{py+18}" width="6" height="10" rx="3" fill="{MUTED}"/>'
                 f'<path d="M{ix-6},{py+25} a6,6 0 0 0 12,0 M{ix},{py+31} v3" stroke="{MUTED}" stroke-width="1.6" fill="none"/>')
        elif ic == "head":
            g = (f'<path d="M{ix-7},{py+31} v-5 a7,7 0 0 1 14,0 v5" stroke="{MUTED}" stroke-width="1.8" fill="none"/>'
                 f'<rect x="{ix-8}" y="{py+26}" width="4" height="7" rx="1.5" fill="{MUTED}"/>'
                 f'<rect x="{ix+4}" y="{py+26}" width="4" height="7" rx="1.5" fill="{MUTED}"/>')
        else:
            g = (f'<circle cx="{ix}" cy="{py+26}" r="6" stroke="{MUTED}" stroke-width="3" fill="none" stroke-dasharray="3 2"/>'
                 f'<circle cx="{ix}" cy="{py+26}" r="2.5" fill="{MUTED}"/>')
        b.append(g)

    # 채팅 영역
    cx0 = 312
    cw = W - cx0
    b.append(f'<rect x="{cx0}" y="48" width="{cw}" height="1" fill="#26282c"/>'
             + hashtag(cx0 + 18, 24, CHAN)
             + f'<text x="{cx0+40}" y="30" font-size="15" font-weight="700" fill="{HEAD}">환영</text>'
             f'<rect x="{cx0+92}" y="14" width="1" height="20" fill="#3f4147"/>'
             f'<text x="{cx0+106}" y="30" font-size="13" fill="{MUTED}">어서 오세요! 여기는 {x(c["display_name"])}의 GitHub 작업실입니다.</text>')
    today = dt.date.today()
    # 메시지 1: 본인
    my = 84
    b.append(avatar("m1", b64, cx0 + 36, my + 20, 20, CHAT, status=False)
             + f'<text x="{cx0+72}" y="{my+12}" font-size="15" font-weight="600" fill="#f5a742">{x(c["display_name"])}</text>'
             f'<text x="{cx0+72+len(c["display_name"])*8.6+10}" y="{my+12}" font-size="12" fill="{MUTED}">'
             f'{today.year}. {today.month}. {today.day}. 오후 9:41</text>')
    lines = ["안녕하세요! 게임 만드는 " + c["display_name"] + " 입니다 👋"] + c["summary"] + [
        l for l in c["info"] if l]
    for i, t in enumerate(lines[:5]):
        b.append(f'<text x="{cx0+72}" y="{my+36+i*22}" font-size="15" fill="{TEXT}">{x(t)}</text>')
    # 메시지 2: 봇 + 임베드
    my2 = my + 36 + 5 * 22 + 12
    b.append(f'<circle cx="{cx0+36}" cy="{my2+20}" r="20" fill="{BLURPLE}"/>'
             f'<g transform="translate({cx0+36},{my2+20})">{icon("code", "#fff", 0.55)}</g>'
             f'<text x="{cx0+72}" y="{my2+12}" font-size="15" font-weight="600" fill="{HEAD}">GitHub 봇</text>'
             f'<rect x="{cx0+150}" y="{my2}" width="30" height="16" rx="3" fill="{BLURPLE}"/>'
             f'<text x="{cx0+165}" y="{my2+12}" text-anchor="middle" font-size="10" font-weight="700" fill="#fff">앱</text>'
             f'<text x="{cx0+188}" y="{my2+12}" font-size="12" fill="{MUTED}">오늘 오후 9:41</text>')
    ex, ey, ew, eh = cx0 + 72, my2 + 24, 520, 150
    b.append(f'<rect x="{ex}" y="{ey}" width="{ew}" height="{eh}" rx="4" fill="{SIDE}"/>'
             f'<path d="M{ex+4},{ey} H{ex} a4,4 0 0 0 -0,0 V{ey+eh}" />'
             f'<rect x="{ex}" y="{ey}" width="4" height="{eh}" rx="2" fill="{BLURPLE}"/>'
             f'<text x="{ex+16}" y="{ey+26}" font-size="16" font-weight="700" fill="{LINK}">{x(c["user"])} 님의 GitHub 통계</text>')
    fields = [("저장소", stats["repos"]), ("받은 스타", stats["stars"]), ("팔로워", stats["followers"]),
              ("가입", ko_date(c["since"])), ("레벨", f'{stats["level"]}년차'), ("주력", "Blender · Unity")]
    for i, (k, v) in enumerate(fields):
        fx = ex + 16 + (i % 3) * 168
        fy = ey + 54 + (i // 3) * 46
        b.append(f'<text x="{fx}" y="{fy}" font-size="13" font-weight="700" fill="{HEAD}">{x(k)}</text>'
                 f'<text x="{fx}" y="{fy+20}" font-size="14" fill="{TEXT}">{x(v)}</text>')
    b.append(f'<text x="{ex+16}" y="{ey+eh-12}" font-size="12" fill="{MUTED}">github.com/{x(c["user"])}</text>')
    # 입력창 + 입력 중
    iy = H - 68
    b.append(f'<rect x="{cx0+16}" y="{iy}" width="{cw-32}" height="44" rx="8" fill="{INPUT}"/>'
             f'<circle cx="{cx0+40}" cy="{iy+22}" r="10" fill="#b5bac1"/>'
             f'<path d="M{cx0+40},{iy+16} v12 M{cx0+34},{iy+22} h12" stroke="{INPUT}" stroke-width="2.2"/>'
             f'<text x="{cx0+62}" y="{iy+27}" font-size="15" fill="#6d6f78">#환영에 메시지 보내기</text>')
    ty = H - 12
    dots = "".join(
        f'<circle cx="{cx0+24+i*7}" cy="{ty-4}" r="2.6" fill="{TEXT}">'
        f'<animate attributeName="opacity" values="0.3;1;0.3" dur="1.2s" begin="{i*0.2}s" repeatCount="indefinite"/></circle>'
        for i in range(3))
    b.append(dots + f'<text x="{cx0+50}" y="{ty}" font-size="12" fill="{TEXT}"><tspan font-weight="700">'
             f'{x(c["display_name"])}</tspan>님이 입력하고 있어요...</text>')
    return svg(W, H, "\n".join(b), f'{c["display_name"]} 디스코드 서버')


# ─────────────── 프로필 팝업 (300 x ?) ───────────────
def build_profile(c, stats, b64):
    W = 300
    b = []
    y = 0
    # 배너
    b.append(f'<defs><linearGradient id="bn" x1="0" y1="0" x2="1" y2="1">'
             f'<stop offset="0" stop-color="#5865f2"/><stop offset="1" stop-color="#eb459e"/></linearGradient>'
             f'<clipPath id="pc"><rect width="{W}" height="H_PLACE" rx="10"/></clipPath></defs>')
    body = [f'<rect width="{W}" height="H_PLACE" fill="{POP}"/>',
            f'<rect width="{W}" height="106" fill="url(#bn)"/>',
            avatar("pa", b64, 62, 106, 40, POP).replace(f'r="{40*0.32+40*0.12+1.5}"', f'r="{40*0.32+6}"'),
            f'<circle cx="62" cy="106" r="46" fill="none" stroke="{POP}" stroke-width="6"/>']
    # 배지 (스킬 아이콘 작게)
    bx = W - 16 - 8 * 21
    body.append(f'<rect x="{bx-6}" y="118" width="{8*21+10}" height="30" rx="8" fill="{POP_IN}"/>')
    for i, (_, kind, col) in enumerate(c["skills"]):
        body.append(f'<g transform="translate({bx+8+i*21},133)">{icon(kind, col, 0.36)}</g>')
    y = 162
    inner_top = y
    parts = []
    parts.append(f'<text x="28" y="{y+30}" font-size="20" font-weight="700" fill="{HEAD}">{x(c["display_name"])}</text>'
                 f'<text x="28" y="{y+52}" font-size="14" fill="{TEXT}">{x(c["user"].lower())}</text>')
    yy = y + 70
    parts.append(f'<rect x="28" y="{yy}" width="{W-56}" height="1" fill="#2e2f34"/>')
    yy += 26
    parts.append(f'<text x="28" y="{yy}" font-size="12" font-weight="700" fill="{HEAD}">자기소개</text>')
    for i, t in enumerate(c["summary"]):
        parts.append(f'<text x="28" y="{yy+22+i*19}" font-size="13.5" fill="{TEXT}">{x(t)}</text>')
    yy += 22 + len(c["summary"]) * 19 + 16
    parts.append(f'<text x="28" y="{yy}" font-size="12" font-weight="700" fill="{HEAD}">가입 시기</text>'
                 f'<circle cx="36" cy="{yy+17}" r="8" fill="{HEAD}"/>'
                 f'<text x="36" y="{yy+21}" text-anchor="middle" font-size="9" font-weight="700" fill="{POP_IN}">G</text>'
                 f'<text x="52" y="{yy+22}" font-size="13.5" fill="{TEXT}">{x(ko_date(c["since"]))}</text>')
    yy += 48
    parts.append(f'<text x="28" y="{yy}" font-size="12" font-weight="700" fill="{HEAD}">역할</text>')
    # 역할 칩 줄바꿈
    rx, ry = 28, yy + 12
    for name, _, col in c["skills"]:
        w = 26 + len(name.encode("utf-8")) * 3.3 + (len(name) - len(name.encode("utf-8")) // 3) * 0
        w = 26 + sum(12 if ord(ch) > 127 else 6.6 for ch in name)
        if rx + w > W - 28:
            rx, ry = 28, ry + 30
        parts.append(f'<rect x="{rx}" y="{ry}" width="{w}" height="24" rx="5" fill="{POP}"/>'
                     f'<circle cx="{rx+12}" cy="{ry+12}" r="5" fill="{col}"/>'
                     f'<text x="{rx+22}" y="{ry+16.5}" font-size="12" font-weight="500" fill="{TEXT}">{x(name)}</text>')
        rx += w + 6
    yy = ry + 46
    # 활동 카드
    parts.append(f'<text x="28" y="{yy}" font-size="12" font-weight="700" fill="{HEAD}">게임 하는 중</text>')
    ay = yy + 12
    parts.append(f'<rect x="28" y="{ay}" width="64" height="64" rx="8" fill="#e87d0d" fill-opacity="0.18"/>'
                 f'<g transform="translate(60,{ay+32})">{icon("cube", "#e87d0d", 0.9)}</g>'
                 + cycle(c["now_playing"], 104, ay + 22, f'font-size="14" font-weight="700" fill="{HEAD}"')
                 + f'<text x="104" y="{ay+42}" font-size="13" fill="{TEXT}">무언가 만드는 중</text>')
    # 경과 시간: 분 단위로 올라가는 척 (0~59 반복)
    parts.append(f'<path d="M104,{ay+54} m0,0" />'
                 f'<circle cx="109" cy="{ay+57}" r="5" fill="none" stroke="{ONLINE}" stroke-width="1.6"/>'
                 f'<path d="M109,{ay+54} v3 h2.5" stroke="{ONLINE}" stroke-width="1.4" fill="none"/>'
                 + cycle([f"{h}:{m:02d} 경과" for h, m in [(1, 12), (1, 13), (1, 14), (1, 15)]], 120, ay + 61,
                         f'font-size="12" font-weight="600" fill="{ONLINE}"', dur_each=4))
    yy = ay + 64 + 18
    # 버튼
    parts.append(f'<rect x="28" y="{yy}" width="{W-56}" height="36" rx="8" fill="{BLURPLE}"/>'
                 f'<text x="{W/2}" y="{yy+23}" text-anchor="middle" font-size="14" font-weight="600" fill="#fff">GitHub 프로필 보기</text>')
    yy += 36 + 16
    inner_h = yy - inner_top
    body.append(f'<rect x="16" y="{inner_top}" width="{W-32}" height="{inner_h}" rx="8" fill="{POP_IN}"/>')
    body.extend(parts)
    H = yy + 16
    out = "\n".join(b) + f'<g clip-path="url(#pc)">' + "\n".join(body) + "</g>"
    return svg(W, H, out.replace("H_PLACE", str(H)), f'{c["display_name"]} 프로필')


# ─────────────── 프로젝트 채널 (652) ───────────────
def build_projects_top(c):
    W, H = 652, 56
    b = (f'<path d="M10,0 H{W-10} A10,10 0 0 1 {W},10 V{H} H0 V10 A10,10 0 0 1 10,0 Z" fill="{CHAT}"/>'
         + hashtag(18, 28, CHAN)
         + f'<text x="40" y="34" font-size="15" font-weight="700" fill="{HEAD}">프로젝트</text>'
         f'<rect x="120" y="18" width="1" height="20" fill="#3f4147"/>'
         f'<text x="134" y="34" font-size="13" fill="{MUTED}">최근에 작업한 저장소 · 눌러서 열기</text>'
         f'<rect y="{H-1}" width="{W}" height="1" fill="#26282c"/>')
    return svg(W, H, b, "프로젝트 채널")


def build_repo_embed(c, name, desc, colors, info, last=False):
    W, H = 652, 132
    lang = info.get("language") or "—"
    stars = info.get("stargazers_count", 0)
    upd = ko_date(info.get("pushed_at", ""))
    bg = (f'<path d="M0,0 H{W} V{H-10} A10,10 0 0 1 {W-10},{H} H10 A10,10 0 0 1 0,{H-10} Z" fill="{CHAT}"/>'
          if last else f'<rect width="{W}" height="{H}" fill="{CHAT}"/>')
    ex, ey, ew, eh = 16, 12, 620, 108
    gid = "g" + "".join(ch for ch in name if ch.isalnum())
    b = (bg
         + f'<rect x="{ex}" y="{ey}" width="{ew}" height="{eh}" rx="4" fill="{SIDE}"/>'
         f'<rect x="{ex}" y="{ey}" width="4" height="{eh}" rx="2" fill="{colors[1]}"/>'
         f'<text x="{ex+16}" y="{ey+22}" font-size="12" fill="{MUTED}">GitHub</text>'
         f'<text x="{ex+16}" y="{ey+44}" font-size="16" font-weight="700" fill="{LINK}">{x(c["user"])}/{x(name)}</text>'
         f'<text x="{ex+16}" y="{ey+66}" font-size="14" fill="{TEXT}">{x(desc)}</text>'
         f'<text x="{ex+16}" y="{ey+92}" font-size="12.5" fill="{MUTED}">★ {stars}   ·   {x(lang)}   ·   {x(upd)} 업데이트</text>'
         f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{colors[0]}"/>'
         f'<stop offset="1" stop-color="{colors[1]}"/></linearGradient></defs>'
         f'<rect x="{ex+ew-96}" y="{ey+16}" width="80" height="80" rx="4" fill="url(#{gid})"/>'
         f'<text x="{ex+ew-56}" y="{ey+64}" text-anchor="middle" font-size="26" font-weight="700" fill="#fff" '
         f'fill-opacity=".9">{x(name[:2].upper())}</text>')
    return svg(W, H, b, name)


def build_readme(c):
    u = c["user"]
    rows = "".join(
        f'<a href="https://github.com/{u}/{n}"><img src="discord/repo-{n}.svg" width="66.8%" alt="{n}"/></a><br/>\n'
        for n, _, _ in c["repos"])
    streak = (f"https://streak-stats.demolab.com/?user={u}&background=2B2D31&border=1E1F22&ring=5865F2&fire=23A55A"
              f"&currStreakNum=F2F3F5&sideNums=DBDEE1&currStreakLabel=5865F2&sideLabels=949BA4&dates=949BA4&locale=ko")
    raw = f"https://raw.githubusercontent.com/{u}/{u}"
    return f"""<a href="https://github.com/{u}"><img src="discord/server.svg" width="100%" alt="{c['display_name']}의 작업실"/></a>

<div>
<a href="https://github.com/{u}"><img src="discord/profile.svg" align="right" width="30.7%" alt="프로필"/></a>
<a href="https://github.com/{u}?tab=repositories"><img src="discord/projects-top.svg" width="66.8%" alt="프로젝트"/></a><br/>
{rows}</div>

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
    OUT.mkdir(exist_ok=True)
    user = api(f'users/{c["user"]}')
    repos = api(f'users/{c["user"]}/repos?per_page=100') or []
    rinfo = {r["name"]: r for r in repos if isinstance(r, dict)}
    since = dt.date.fromisoformat(c["since"])
    stats = {
        "repos": sum(1 for r in rinfo.values() if not r.get("fork") and r.get("name") != c["user"])
        or len(c["repos"]),
        "stars": sum(r.get("stargazers_count", 0) for r in rinfo.values()),
        "followers": user.get("followers", 0),
        "level": (dt.date.today() - since).days // 365,
    }
    b64 = avatar_b64(c)
    files = {
        "server.svg": build_server(c, stats, b64),
        "profile.svg": build_profile(c, stats, b64),
        "projects-top.svg": build_projects_top(c),
    }
    for i, (name, desc, cols) in enumerate(c["repos"]):
        files[f"repo-{name}.svg"] = build_repo_embed(c, name, desc, cols, rinfo.get(name, {}),
                                                     last=i == len(c["repos"]) - 1)
    for f, s in files.items():
        (OUT / f).write_text(s, encoding="utf-8")

    # README에 들어갈 모양 그대로 미리보기 (GitHub 다크 화면 흉내)
    repo_imgs = "\n".join(
        f'<a href="https://github.com/{c["user"]}/{n}"><img src="repo-{n}.svg" width="66.8%"/></a><br/>'
        for n, _, _ in c["repos"])
    html = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<title>디스코드 시안</title>
<style>body{{background:#0d1117;margin:0;padding:24px;font-family:sans-serif}}
.box{{max-width:976px;margin:0 auto;line-height:0}} img{{max-width:100%}}</style></head>
<body><div class="box">
<img src="server.svg" width="100%"/><br/><br/>
<img src="profile.svg" align="right" width="30.7%"/>
<img src="projects-top.svg" width="66.8%"/><br/>
{repo_imgs}
<br clear="all"/>
</div></body></html>"""
    (OUT / "preview.html").write_text(html, encoding="utf-8")
    (ROOT / "README.md").write_text(build_readme(c), encoding="utf-8")
    print("만든 파일:", ", ".join(files), "+ preview.html + README.md", stats)


if __name__ == "__main__":
    main()
