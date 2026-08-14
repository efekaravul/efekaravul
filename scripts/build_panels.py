"""Build the three static profile panels.

Each panel is one SVG drawn at panels.PANEL_W. Keeping a panel whole - rather
than placing two images side by side in the README - is what stops the layout
from breaking: GitHub's README column is narrower than 860px on many screens,
and two separate images simply wrap onto different lines when they no longer
fit. One image scales down as a unit instead.

Usage:
    python scripts/build_panels.py
    STATIC=1 python scripts/build_panels.py    # finished frame, no animation
"""

from __future__ import annotations

import os
from pathlib import Path

import avatar
import panels as P

OUT = Path(__file__).resolve().parents[1] / "assets"

W = P.PANEL_W
BODY = P.TITLEBAR_H + 16      # first baseline row of any panel body


# --------------------------------------------------------------------------
# whoami: the avatar mosaic beside a neofetch-style identity card
# --------------------------------------------------------------------------

AVATAR_X = 18.0
AVATAR_W = 330.0
AVATAR_COLS = 84
DIVIDER_X = 372.0
INFO_X = 398.0
INFO_VALUE_X = 494.0
INFO_RIGHT = 842.0

IDENTITY = [
    ("Role", "Data Engineering & Machine Learning"),
    ("Focus", "End-to-end pipelines, predictive models"),
    ("Language", "Python 3.12"),
    ("Env", "PyCharm · Jupyter · Git"),
    ("Portfolio", "Applied-Data-Engineering-And-ML"),
    ("Kaggle", "kaggle.com/efekaravul"),
    ("Docs", "Bilingual TR / EN on every notebook"),
    ("Contact", "efekaravul@gmail.com"),
    ("Status", "Learning in public, one notebook at a time"),
]

SWATCHES = ["#ff7b72", "#ffa657", "#e3b341", "#7ee787",
            "#79c0ff", "#d2a8ff", "#f0883e", "#8b949e"]


def whoami(static: bool) -> str:
    grid = avatar.quantise(AVATAR_COLS)
    defs, mosaic, art_h = avatar.render(
        grid, AVATAR_X, BODY, AVATAR_W, "a", static
    )

    rows_top = 134.0
    row_step = 24.0
    swatch_y = rows_top + len(IDENTITY) * row_step + 6
    height = max(BODY + art_h, swatch_y + 11) + 18

    out = P.open_svg(W, height, "Efe Karavul: avatar and profile summary")
    out.append(f"<defs>{defs}</defs>")
    out.append(P.titlebar(W, "./whoami.sh"))
    out.append(mosaic)
    out.append(
        f'<line x1="{DIVIDER_X}" y1="{BODY}" x2="{DIVIDER_X}" '
        f'y2="{BODY + art_h:.1f}" stroke="{P.RULE}"/>'
    )
    out.append('<g class="mono">')

    attrs, anim = P.reveal(0, static)
    out.append(
        f"<g{attrs}>{anim}"
        f'<text x="{INFO_X}" y="78" font-size="18" font-weight="700" fill="{P.ACCENT}">'
        f"efe.karavul</text>"
        f'<text x="{INFO_X}" y="97" font-size="11" fill="{P.DIM}">'
        f"aspiring data engineer &amp; ml practitioner</text></g>"
    )

    attrs, anim = P.reveal(1, static)
    out.append(
        f"<g{attrs}>{anim}<line x1='{INFO_X}' y1='112' x2='{INFO_RIGHT}' y2='112' "
        f"stroke='{P.RULE}'/></g>"
    )

    for i, (label, value) in enumerate(IDENTITY):
        y = rows_top + i * row_step
        attrs, anim = P.reveal(i + 2, static)
        out.append(
            f"<g{attrs}>{anim}"
            f'<text x="{INFO_X}" y="{y:.0f}" font-size="11.5" fill="{P.KEY}">{P.esc(label)}</text>'
            f'<text x="{INFO_VALUE_X}" y="{y:.0f}" font-size="11.5" fill="{P.INK}">'
            f"{P.esc(value)}</text></g>"
        )

    attrs, anim = P.reveal(len(IDENTITY) + 2, static)
    swatches = "".join(
        f'<rect x="{INFO_X + i * 26:.0f}" y="{swatch_y:.0f}" width="22" height="11" '
        f'rx="2" fill="{c}"/>'
        for i, c in enumerate(SWATCHES)
    )
    out.append(f"<g{attrs}>{anim}{swatches}</g>")

    out.append("</g></svg>")
    return "".join(out)


# --------------------------------------------------------------------------
# portfolio: the featured notebooks, as a long directory listing
# --------------------------------------------------------------------------

PROJECTS = [
    (
        "sms-spam-detection",
        "MultinomialNB · 5,572 messages",
        "Bag-of-words classification; leakage-safe CountVectorizer fit, duplicate removal, stratified split.",
        "98.7% accuracy · 0.98 precision · 0.92 recall on a 13% minority class",
    ),
    (
        "diamond-price-regression",
        "SVR · ~54k records",
        "Support Vector Regression against a linear baseline, with outlier treatment, ordinal encoding and scaling.",
        "Kernel, C and epsilon tuned with GridSearchCV",
    ),
    (
        "iris-species-naive-bayes",
        "GaussianNB · 150 records",
        "Why the distributional assumption drives model choice, with the assumptions checked before modelling.",
        "Gaussian likelihood fits continuous measurements where multinomial does not",
    ),
    (
        "svm-kernel-trick",
        "SVM · polynomial vs RBF",
        "Polynomial features engineered by hand and visualised in 3D, then the same split found implicitly by a kernel.",
        "100% test accuracy with RBF against 40% with a linear kernel",
    ),
]

FOOTER = "Every notebook is documented bilingually (TR / EN) — the reasoning, not just the code."


def portfolio(static: bool) -> str:
    block = 63.0
    top = 64.0
    last = top + (len(PROJECTS) - 1) * block + 33
    rule_y = last + 16
    height = rule_y + 34

    out = P.open_svg(W, height, "Featured machine learning notebooks by Efe Karavul")
    out.append(P.titlebar(W, "ls -l ~/portfolio"))
    out.append('<g class="mono">')

    for i, (name, tag, description, metric) in enumerate(PROJECTS):
        y = top + i * block
        attrs, anim = P.reveal(i * 2, static)
        out.append(
            f"<g{attrs}>{anim}"
            f'<text x="{P.PAD_X}" y="{y:.0f}" font-size="12.5" font-weight="700" '
            f'fill="{P.ACCENT}">{P.esc(name)}</text>'
            f'<text x="{INFO_RIGHT}" y="{y:.0f}" font-size="10.5" fill="{P.FAINT}" '
            f'text-anchor="end">{P.esc(tag)}</text>'
            f'<text x="{P.PAD_X}" y="{y + 18:.0f}" font-size="11" fill="{P.INK}">'
            f"{P.esc(description)}</text>"
            f'<text x="{P.PAD_X}" y="{y + 34:.0f}" font-size="11" fill="{P.WARM}">'
            f"{P.esc(metric)}</text></g>"
        )

    attrs, anim = P.reveal(len(PROJECTS) * 2, static)
    out.append(
        f"<g{attrs}>{anim}"
        f'<line x1="{P.PAD_X}" y1="{rule_y:.0f}" x2="{INFO_RIGHT}" y2="{rule_y:.0f}" '
        f'stroke="{P.RULE}"/>'
        f'<text x="{P.PAD_X}" y="{rule_y + 20:.0f}" font-size="10.5" fill="{P.DIM}">'
        f"{P.esc(FOOTER)}</text></g>"
    )

    out.append("</g></svg>")
    return "".join(out)


# --------------------------------------------------------------------------
# focus: what the practice actually consists of
# --------------------------------------------------------------------------

FOCUS = [
    ("modeling", "regression · classification · SVM kernels · Naive Bayes · GridSearchCV tuning"),
    ("data prep", "feature engineering · ordinal & one-hot encoding · MCAR / MAR / MNAR · KNN imputation"),
    ("discipline", "train / test split · StandardScaler · leakage-safe preprocessing"),
    ("evaluation", "confusion matrix · precision / recall / F1 · imbalanced classes"),
    ("text", "CountVectorizer · bag-of-words · sparse matrices"),
    ("tooling", "pandas · NumPy · scikit-learn · Matplotlib · Seaborn · Plotly · Jupyter"),
]

NOW = ("Moving from data analysis into data engineering: scalable pipelines, "
       "leakage-safe preprocessing and honest model evaluation.")


def focus(static: bool) -> str:
    top = 66.0
    step = 25.0
    rule_y = top + (len(FOCUS) - 1) * step + 19
    height = rule_y + 44

    out = P.open_svg(W, height, "Efe Karavul's machine learning focus areas")
    out.append(P.titlebar(W, "cat ~/focus.md"))
    out.append('<g class="mono">')

    for i, (label, value) in enumerate(FOCUS):
        y = top + i * step
        attrs, anim = P.reveal(i, static)
        out.append(
            f"<g{attrs}>{anim}"
            f'<text x="{P.PAD_X}" y="{y:.0f}" font-size="11.5" fill="{P.KEY}">{P.esc(label)}</text>'
            f'<text x="128" y="{y:.0f}" font-size="11.5" fill="{P.INK}">{P.esc(value)}</text></g>'
        )

    attrs, anim = P.reveal(len(FOCUS), static)
    out.append(
        f"<g{attrs}>{anim}"
        f'<line x1="{P.PAD_X}" y1="{rule_y:.0f}" x2="{INFO_RIGHT}" y2="{rule_y:.0f}" '
        f'stroke="{P.RULE}"/>'
        f'<text x="{P.PAD_X}" y="{rule_y + 22:.0f}" font-size="11" fill="{P.ACCENT}">'
        f'<tspan fill="{P.DIM}">now  </tspan>{P.esc(NOW)}</text></g>'
    )

    out.append("</g></svg>")
    return "".join(out)


def main() -> None:
    static = os.environ.get("STATIC") == "1"
    OUT.mkdir(parents=True, exist_ok=True)
    for name, builder in (("whoami", whoami), ("portfolio", portfolio), ("focus", focus)):
        path = OUT / f"{name}.svg"
        path.write_text(builder(static), encoding="utf-8")
        print(f"wrote assets/{name}.svg  ({path.stat().st_size // 1024} KB)"
              f"{' (static)' if static else ''}")


if __name__ == "__main__":
    main()
