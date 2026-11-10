#!/usr/bin/env python3
# Generates assets/profile-card.svg : fixed ASCII photo (assets/art.png) + live GitHub stats.
import os, json, base64, struct, datetime, urllib.request
from collections import Counter

USER  = os.environ.get("USERNAME") or os.environ.get("GITHUB_REPOSITORY_OWNER") or "VertigoJang"
TOKEN = os.environ.get("GITHUB_TOKEN")
ART   = "assets/art.png"
OUT   = "assets/profile-card.svg"

def api(path):
    req = urllib.request.Request("https://api.github.com/"+path, headers={
        "Accept":"application/vnd.github+json","User-Agent":"profile-card-gen",
        **({"Authorization":f"Bearer {TOKEN}"} if TOKEN else {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def gather():
    u = api(f"users/{USER}")
    repos=[]; page=1
    while True:
        batch = api(f"users/{USER}/repos?per_page=100&type=owner&page={page}")
        repos += batch
        if len(batch) < 100: break
        page += 1
    stars = sum(r["stargazers_count"] for r in repos)
    lang = Counter()
    for r in repos:
        if r.get("fork"): continue
        for k,v in api(f"repos/{USER}/{r['name']}/languages").items(): lang[k]+=v
    langs = " · ".join(k for k,_ in lang.most_common(3)) or "—"
    c = datetime.datetime.strptime(u["created_at"], "%Y-%m-%dT%H:%M:%SZ")
    n = datetime.datetime.utcnow()
    m = (n.year-c.year)*12 + (n.month-c.month) - (1 if n.day<c.day else 0)
    y,mo = divmod(m,12)
    uptime = f"{y} year{'s' if y!=1 else ''}, {mo} month{'s' if mo!=1 else ''}"
    return [("Repos",str(u["public_repos"])),("Stars",str(stars)),
            ("Followers",str(u["followers"])),("Following",str(u["following"])),
            ("Langs",langs),("Uptime",uptime)]

def render(rows_i):
    BGHEX="#1a1b26"; BAR="#16161e"; FG="#a9b1d6"; DIM="#565f89"
    PUR="#bb9af7"; CYA="#7dcfff"; GRN="#9ece6a"; RED="#f7768e"; YEL="#e0af68"
    data=open(ART,"rb").read(); AW,AH=struct.unpack(">II",data[16:24])
    b64=base64.b64encode(data).decode()
    PAD=28; BAR_H=46; disp_h=520; disp_w=int(disp_h*AW/AH)
    FSI=18; LH=23; title=f"{USER}@github"
    maxchars=max(len(title), max(12+len(v) for _,v in rows_i))
    info_x=PAD+disp_w+50; W=info_x+maxchars*16+PAD; H=BAR_H+PAD+disp_h+int(PAD*0.6)
    y0=BAR_H+PAD+FSI
    import html
    e=lambda s: html.escape(s,quote=False)
    o=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="\'JetBrains Mono\',\'DejaVu Sans Mono\',Consolas,monospace">']
    o.append(f'<rect width="{W}" height="{H}" rx="14" fill="{BGHEX}"/>')
    o.append(f'<rect width="{W}" height="{BAR_H}" rx="14" fill="{BAR}"/><rect y="{BAR_H-14}" width="{W}" height="14" fill="{BAR}"/>')
    for i,c in enumerate([RED,YEL,GRN]): o.append(f'<circle cx="{26+i*22}" cy="{BAR_H/2}" r="7" fill="{c}"/>')
    o.append(f'<text x="{W//2}" y="{BAR_H//2+5}" text-anchor="middle" fill="{DIM}" font-size="15">{e(title)} — zsh</text>')
    o.append(f'<image x="{PAD}" y="{BAR_H+PAD}" width="{disp_w}" height="{disp_h}" href="data:image/png;base64,{b64}"/>')
    o.append(f'<text xml:space="preserve" x="{info_x}" y="{y0}" font-size="{FSI}">')
    o.append(f'<tspan x="{info_x}" dy="0" fill="{PUR}" font-weight="bold">{e(title)}</tspan>')
    o.append(f'<tspan x="{info_x}" dy="{LH}" fill="{DIM}">{"-"*len(title)}</tspan>')
    for l,v in rows_i:
        o.append(f'<tspan x="{info_x}" dy="{LH}"><tspan fill="{CYA}">{l:<10}</tspan><tspan fill="{FG}">: {e(v)}</tspan></tspan>')
    o.append(f'<tspan x="{info_x}" dy="{int(LH*1.5)}" fill="{GRN}">$ </tspan></text>')
    cy=y0+int(LH*(len(rows_i)+2.5))-FSI+4
    o.append(f'<rect x="{info_x+24}" y="{cy}" width="11" height="{FSI}" fill="{FG}"><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1.1s" repeatCount="indefinite"/></rect>')
    o.append('</svg>')
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT,"w").write("\n".join(o)); print("wrote",OUT,W,"x",H)

if __name__=="__main__":
    import sys
    if "--selftest" in sys.argv:
        rows=[("Repos","5"),("Stars","0"),("Followers","1"),("Following","0"),
              ("Langs","Shell · Python · Kotlin"),("Uptime","4 years, 1 month")]
    else:
        rows=gather()
    render(rows)
