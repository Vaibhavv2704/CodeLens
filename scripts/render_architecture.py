"""Render the architecture diagram using Pillow (optional documentation dependency)."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parents[1]
canvas = Image.new("RGB", (1440, 1000), "#f5f8fa")
draw = ImageDraw.Draw(canvas)
font_path = Path("C:/Windows/Fonts/segoeui.ttf")
bold_path = Path("C:/Windows/Fonts/seguisb.ttf")


def font(size, bold=False):
    target = bold_path if bold else font_path
    return ImageFont.truetype(str(target), size) if target.exists() else ImageFont.load_default(size=size)


def label(x, y, text, size=20, fill="#273f49", bold=False):
    draw.text((x, y), text, font=font(size, bold), fill=fill, anchor="mm")


def box(x, y, width, text, sub="", dark=False):
    draw.rounded_rectangle((x-width/2,y-38,x+width/2,y+38),radius=12,
                           fill="#123c3e" if dark else "#ffffff",outline="#c7dcd9",width=2)
    label(x,y-10 if sub else y,text,19,"#ffffff" if dark else "#273f49",True)
    if sub:
        label(x,y+16,sub,14,"#a6d4c9" if dark else "#71858d")


def arrow(start,end):
    draw.line([start,end],fill="#7a9c96",width=3)
    x,y=end
    if start[1] < y:
        draw.polygon([(x,y),(x-6,y-10),(x+6,y-10)],fill="#7a9c96")
    elif start[0] < x:
        draw.polygon([(x,y),(x-10,y-6),(x-10,y+6)],fill="#7a9c96")
    else:
        draw.polygon([(x,y),(x+10,y-6),(x+10,y+6)],fill="#7a9c96")


label(720,54,"Autonomous GitHub Code Review Agent",32,bold=True)
label(720,93,"Explicit plans. Bounded tools. Validated evidence. Observable recovery.",18,fill="#71858d")
for y1,y2 in [(188,222),(298,342),(418,467),(543,602),(678,737),(813,862)]:
    arrow((720,y1),(720,y2))
box(720,150,500,"React dashboard","Repository + goal / replayable SSE events")
box(720,260,500,"FastAPI + bounded job executor","Validated REST / shared bearer authentication")
box(720,380,500,"Agent orchestrator","Planner + state + allowlisted tool router",True)
for x,title,sub in [(175,"GitHub","Commit-pinned snapshot"),(445,"Inspector + AST","No source execution"),
                    (720,"Docker tests","Opt-in / no network"),(995,"Source verifier","File + line + evidence"),
                    (1265,"LLM","Optional explanations")]:
    draw.line([(720,445),(x,445),(x,467)],fill="#7a9c96",width=2)
    box(x,505,245,title,sub)
    draw.line([(x,543),(x,573),(720,573)],fill="#7a9c96",width=2)
box(720,640,500,"Result validator + recovery engine","Retry twice / fall back / stop safely",True)
draw.line([(970,640),(1410,640),(1410,380),(970,380)],fill="#c69e58",width=3)
arrow((1010,380),(970,380))
label(1180,615,"Bounded retry",16,fill="#9d7b3e")
box(720,775,500,"Structured report","Findings / provenance / test status / limitations")
box(720,900,500,"SQLAlchemy persistence","Reviews / steps / calls / issues / repositories / events")
label(720,967,"PostgreSQL in deployment | SQLite locally | Repository code never executes on the host",16,fill="#71858d")
canvas.save(root / "docs" / "architecture.png")
print("Rendered docs/architecture.png")
