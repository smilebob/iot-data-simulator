"""
Automated Accessibility (WCAG AA / ARIA) and Dual-Theme Consistency Tests.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX_HTML = ROOT / "app" / "static" / "index.html"
APP_JS = ROOT / "app" / "static" / "app.js"
STYLES_CSS = ROOT / "app" / "static" / "styles.css"


def test_all_modals_have_aria_and_light_theme_coverage():
    """Ensures every modal in index.html has ARIA dialog attributes and html.light styling."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    css = STYLES_CSS.read_text(encoding="utf-8")

    modal_tags = re.findall(r'<div\s+id="(modal-[^"]+)"[^>]*>', html)
    assert len(modal_tags) >= 15

    for modal_id in modal_tags:
        tag_match = re.search(rf'<div\s+id="{re.escape(modal_id)}"[^>]*>', html)
        assert tag_match is not None
        tag = tag_match.group(0)
        assert 'role="dialog"' in tag, f"{modal_id} missing role='dialog'"
        assert 'aria-modal="true"' in tag, f"{modal_id} missing aria-modal='true'"
        assert f"html.light #{modal_id} > div" in css, f"{modal_id} missing html.light override in styles.css"


def test_modal_close_buttons_have_aria_label():
    """Ensures icon-only modal close buttons expose an accessible aria-label."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    close_btns = re.findall(
        r'<button\b[^>]*>\s*(?:<i data-lucide="x"[^>]*></i>|&times;)\s*</button>',
        html,
    )
    assert len(close_btns) >= 10
    for btn in close_btns:
        assert "aria-label=" in btn, f"Close button missing aria-label: {btn}"


def test_no_backdrop_blur_performance_regression():
    """Guards against reintroducing backdrop-blur on modal overlays (GPU lag on select dropdowns)."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    js = APP_JS.read_text(encoding="utf-8")
    assert "backdrop-blur" not in html
    assert "backdrop-blur" not in js


def test_wcag_contrast_and_focus_visible_rules_present():
    """Validates presence of keyboard focus-visible ring and Light/Dark WCAG AA contrast overrides."""
    css = STYLES_CSS.read_text(encoding="utf-8")
    assert ":focus-visible" in css
    for cls in (
        "html.dark .text-slate-500",
        "html.light .text-slate-500",
        "html.light .text-slate-600",
        "html.light .text-emerald-400",
        "html.light .text-sky-400",
        "html.light .text-amber-400",
        "html.light .text-purple-400",
        "html.light button.bg-sky-600",
        "html.light button.bg-amber-600",
    ):
        assert cls in css, f"Missing WCAG contrast override '{cls}' in styles.css"
