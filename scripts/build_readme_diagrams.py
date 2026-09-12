"""Generate editable README diagrams from the implemented Replay workflow.

SVG assets have no external resources, scripts, personal photographs or fonts.
Render the SVGs to PNG when updating the README previews.
"""

from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "architecture"
INK, MUTED = "#203646", "#526976"
TEAL, BLUE, AMBER = "#187b70", "#396f9a", "#a66b27"


class Diagram:
    """Small SVG authoring surface with explicit geometry and accessible labels."""

    def __init__(self, title: str, description: str, height: int):
        self.parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="{height}" viewBox="0 0 1440 {height}" role="img" aria-labelledby="title desc">',
            f'<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>',
            f'<rect width="1440" height="{height}" rx="24" fill="#f5f3eb"/>',
            '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10Z" fill="#6a8790"/></marker></defs>',
        ]

    def rect(self, x, y, w, h, fill="#ffffff", radius=18, stroke="none"):
        self.parts.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}"/>'
        )

    def text(self, x, y, value, size=24, color=INK, weight=400):
        self.parts.append(
            f'<text x="{x}" y="{y}" font-family="DejaVu Sans, sans-serif" font-size="{size}" font-weight="{weight}" fill="{color}">{escape(value)}</text>'
        )

    def path(self, value, stroke=TEAL, width=3, fill="none", arrow=False, dashed=False):
        dash = ' stroke-dasharray="8 7"' if dashed else ""
        marker = ' marker-end="url(#arrow)"' if arrow else ""
        self.parts.append(
            f'<path d="{value}" stroke="{stroke}" stroke-width="{width}" fill="{fill}" stroke-linecap="round" stroke-linejoin="round"{marker}{dash}/>'
        )

    def circle(self, x, y, radius, fill, stroke="none", width=2):
        self.parts.append(
            f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>'
        )

    def label(self, x, y, number, text):
        self.circle(x + 18, y - 8, 18, TEAL)
        self.text(x + 11, y, str(number), 21, "#ffffff", 700)
        self.text(x + 50, y, text, 26, INK, 700)

    def save(self, name: str):
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / name).write_text("\n".join(self.parts + ["</svg>"]), encoding="utf-8")


def introduction() -> None:
    """Illustrate how exported camera and watch data become reviewable evidence."""
    d = Diagram(
        "RaceTime Replay at a glance",
        "Runners import video and workout exports, align both on one video clock, then review candidate stops and sensor disagreements. The screens and values are illustrative, not actual workout results.",
        700,
    )
    d.text(40, 48, "RACETIME REPLAY  /  THE PRODUCT", 18, TEAL, 700)
    d.text(40, 104, "See the run behind the numbers.", 40, INK, 700)
    d.text(
        40,
        145,
        "For runners, coaches and crews who want to revisit what happened along the way.",
        23,
        MUTED,
    )
    for x in [40, 520, 1000]:
        d.rect(x, 185, 400, 390)
    d.path("M458 375 H500", "#6a8790", arrow=True)
    d.path("M938 375 H980", "#6a8790", arrow=True)
    d.label(62, 230, 1, "Capture the run")
    d.label(542, 230, 2, "Align the evidence")
    d.label(1022, 230, 3, "Review the moment")
    # Generic camera footage and watch, deliberately without personal photos.
    d.rect(70, 262, 340, 190, "#dceaf0", 12)
    d.circle(113, 299, 16, "#efc879")
    d.path("M75 410 L151 309 L214 375 L283 288 L405 419 Z", "none", 0, "#83afa9")
    d.path("M75 432 L154 356 L209 411 L301 346 L405 432 Z", "none", 0, "#386c72")
    d.path("M128 438 C262 433 188 398 296 365", "#f7df9b", 5)
    d.rect(321, 296, 40, 156, "#becbd2", 12)
    d.rect(300, 326, 84, 101, INK, 20)
    d.rect(308, 336, 68, 80, "#ffffff", 14)
    d.path("M315 380 H328 L335 363 L344 394 L352 373 H369", TEAL, 3)
    d.text(70, 490, "Camera + workout export", 23, INK, 700)
    d.text(70, 524, "GoPro · Insta360 · iPhone", 21, MUTED)
    d.text(70, 553, "Meta glasses + watch data", 21, MUTED)
    # Two illustrative measurements share a timeline after an explicit offset.
    d.rect(550, 262, 340, 190, "#eaf0f5", 12)
    d.text(568, 297, "ONE VIDEO CLOCK", 18, BLUE, 700)
    d.rect(729, 310, 30, 105, "#d7e7df", 4)
    d.text(568, 334, "Speed", 17, MUTED)
    d.path("M636 328 H672 L690 322 L707 331 H729 L738 352 H751 L763 328 H870", BLUE, 3)
    d.text(568, 390, "Heart rate", 17, MUTED)
    d.path(
        "M665 385 L686 379 L707 383 L728 374 L749 377 L770 369 L791 375 L812 367 L833 370 H870",
        TEAL,
        3,
    )
    d.path("M568 428 H870", "#bdcbd0", 5)
    d.circle(744, 428, 9, AMBER)
    d.text(550, 490, "Replay both in sync", 24, INK, 700)
    d.text(550, 524, "Set the offset. Keep gaps visible.", 20, MUTED)
    d.text(550, 553, "Compare signals at each moment.", 19, MUTED)
    # Evidence is a candidate for review, not a causal or medical conclusion.
    d.rect(1030, 262, 340, 190, "#e6f1ea", 12)
    for y, title, detail, color in [
        (279, "Stop candidate", "Open the timestamped frame", TEAL),
        (359, "Sensor disagreement", "Compare video and watch", AMBER),
    ]:
        d.rect(1047, y, 305, 68, "#ffffff", 8)
        d.circle(1065, y + 22, 6, color)
        d.text(1081, y + 28, title, 20, color, 700)
        d.text(1060, y + 53, detail, 17, MUTED)
    d.text(1030, 490, "Watch. Inspect. Decide.", 24, INK, 700)
    d.text(1030, 524, "Review events and cited answers.", 20, MUTED)
    d.text(1030, 553, "Confirm or reject after replay.", 21, MUTED)
    d.text(40, 624, "Video + watch data → moments worth reviewing", 29, TEAL, 700)
    d.text(
        40,
        666,
        "Illustrative screens. Camera motion is not running speed. The bundled demo uses synthetic data.",
        20,
        MUTED,
    )
    d.save("replay-readme-intro.svg")


def architecture() -> None:
    """Separate the local measurement path from optional cloud and lab features."""
    d = Diagram(
        "RaceTime Replay architecture overview",
        "Exported video and watch data enter local OpenCV measurements and validated parsers, then offset alignment produces candidate events. A bounded LangGraph investigator retrieves and verifies evidence. Streamlit serves synchronized browser replay and human review. Optional Gemini or Nebius receives redacted text only; optional Braintrust exports restricted metadata for synthetic demos only. Files are local and graph checkpoints are in memory.",
        1260,
    )
    d.text(40, 48, "RACETIME REPLAY  /  IMPLEMENTED PYTHON WORKFLOW", 18, TEAL, 700)
    d.text(40, 101, "From separate recordings to shared evidence", 37, INK, 700)
    d.text(
        40,
        143,
        "Core analysis runs on the app host. The bundled demo works without an API key.",
        23,
        MUTED,
    )
    for x in [40, 520, 1000]:
        d.rect(x, 190, 400, 215)
    d.label(62, 232, 1, "Exported files")
    d.text(64, 280, "Camera video  ·  MP4 / MOV", 22)
    d.text(64, 318, "Watch  ·  CSV / GPX / XML", 22, BLUE)
    d.text(64, 354, "Apple Health XML supported", 20, MUTED)
    d.text(64, 384, "File import; no device API", 20, MUTED)
    d.label(542, 232, 2, "Local measurements")
    d.text(544, 280, "OpenCV: flow, frames, quality", 21)
    d.text(544, 318, "Parsers: time, units, samples", 21, BLUE)
    d.text(544, 354, "Speed · heart rate · route", 20, MUTED)
    d.text(544, 384, "Keep missing values explicit", 20, MUTED)
    d.label(1022, 232, 3, "Align + detect")
    d.text(1024, 280, "Manual offset + time tolerance", 21)
    d.text(1024, 318, "Stops · repeats · disagreements", 20, BLUE)
    d.text(1024, 354, "Candidate events + coverage", 20, MUTED)
    d.text(1024, 384, "Evidence frames + timestamps", 20, MUTED)
    d.path("M458 300 H500", "#6a8790", arrow=True)
    d.path("M938 300 H980", "#6a8790", arrow=True)
    d.path("M1200 405 V437 H480 V468", "#6a8790", arrow=True)
    d.rect(40, 480, 880, 360, "#e4edf3")
    d.text(65, 522, "BOUNDED LANGGRAPH INVESTIGATOR", 25, BLUE, 700)
    for x, title, first, second in [
        (65, "Guard + route", "Input policy checks", "Choose investigation"),
        (350, "Retrieve + inspect", "Events and knowledge", "Local evidence tools"),
        (635, "Answer + verify", "Citations and schema", "Return checked answer"),
    ]:
        d.rect(x, 550, 255, 140)
        d.text(x + 15, 587, title, 22, BLUE, 700)
        d.text(x + 15, 629, first, 19)
        d.text(x + 15, 663, second, 19, MUTED)
    d.path("M323 620 H342", "#6a8790", 2, arrow=True)
    d.path("M608 620 H627", "#6a8790", 2, arrow=True)
    d.text(65, 733, "Local TF-IDF retrieval; optional MiniLM hybrid search", 22, BLUE)
    d.text(65, 770, "Optional NeMo input action + Guardrails AI schema checks", 21, MUTED)
    d.rect(65, 790, 825, 32, "#ffffff", 8)
    d.text(
        80,
        813,
        "Blocked inputs stop before tools or models. Local evidence remains primary.",
        19,
        TEAL,
        700,
    )
    d.rect(1000, 480, 400, 360, "#fbefd9")
    d.text(1025, 522, "OPTIONAL TEXT DRAFT", 24, AMBER, 700)
    d.text(1025, 570, "Gemini / Nebius Token Factory", 21, INK, 700)
    d.text(1025, 616, "Opt-in, redacted text evidence", 21)
    d.text(1025, 652, "No video, frames or raw GPS", 21)
    d.text(1025, 697, "Draft returns for validation", 20, AMBER, 700)
    d.text(1025, 733, "Failure keeps local evidence", 20, MUTED)
    d.text(1025, 779, "Dashed arrows: opt-in calls", 20, MUTED)
    d.text(1025, 810, "Credentials required", 20, MUTED)
    d.path("M923 596 H996", "#6a8790", arrow=True, dashed=True)
    d.path("M996 665 H923", "#6a8790", arrow=True, dashed=True)
    # UI is browser-side; computation and runtime files stay on the app host.
    for x in [40, 520, 1000]:
        d.rect(x, 910, 400, 220)
    d.path("M240 840 V901", "#6a8790", arrow=True)
    d.path("M720 840 V901", "#6a8790", arrow=True)
    d.text(64, 951, "Replay + human review", 25, TEAL, 700)
    d.text(64, 992, "Streamlit + browser video clock", 21)
    d.text(64, 1027, "Charts, route and cited answers", 21)
    d.text(64, 1062, "Confirm or reject event candidates", 20)
    d.text(64, 1103, "Review does not certify a cause.", 19, MUTED)
    d.text(544, 951, "Local session state", 25, BLUE, 700)
    d.text(544, 992, "Files, index and review JSON", 21)
    d.text(544, 1027, "Graph checkpoints: in memory", 21)
    d.text(544, 1062, "Delete control + retention cleanup", 20)
    d.text(544, 1103, "Host storage under .runtime/", 19, MUTED)
    d.text(1024, 951, "Evaluation + tracing", 25, BLUE, 700)
    d.text(1024, 992, "Local timings and synthetic evals", 20)
    d.text(1024, 1027, "Optional Braintrust metadata", 21)
    d.text(1024, 1062, "Synthetic demo sessions only", 21, AMBER, 700)
    d.text(1024, 1103, "No upload-session cloud tracing", 19, MUTED)
    d.text(40, 1180, "FUTURE EXTENSIONS", 18, TEAL, 700)
    d.text(
        40,
        1219,
        "Visual scene summaries + terrain understanding + watch-informed optimization need further validation.",
        21,
        MUTED,
    )
    d.save("replay-readme-architecture.svg")


if __name__ == "__main__":
    introduction()
    architecture()
