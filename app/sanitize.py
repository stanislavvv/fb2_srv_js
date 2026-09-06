# -*- coding: utf-8 -*-
"""XSS sanitizing helpers for backend-rendered HTML content.

Two functions are exposed:

- ``sanitize_html(html)``: strips dangerous elements/attributes from an
  HTML string produced from FB2 (book body) or composed for OPDS entries
  (annotation + pubinfo + sequence name). It preserves regular formatting
  markup (``<p>``, ``<b>``, ``<i>``, ``<span class=...>``, ``<a href=...>``,
  ``<style>`` blocks, ``data:image/*`` URIs, etc.) so the reader interface
  keeps working.

- ``escape_html(text)``: HTML-escapes plain text (author name, publisher,
  etc.) so it can be safely embedded into an HTML fragment without being
  interpreted as markup.
"""

from html import escape as _html_escape
from bs4 import BeautifulSoup, Comment, NavigableString

# Elements that can directly execute or load arbitrary resources.
# Everything in this set is removed together with its content.
DANGEROUS_TAGS = {
    "script", "style-script", "iframe", "frame", "frameset",
    "object", "embed", "applet",
    "form", "input", "button", "textarea", "select", "option",
    "noscript", "base", "link",
    "svg", "math",  # SVG/MathML allow <script> inside
}

# Attributes that hold URLs and can therefore contain javascript: etc.
URL_ATTRS = {"href", "src", "action", "formaction", "xlink:href", "data"}

# URL schemes that are safe for the attributes above.
# Note: data: URIs are allowed ONLY for image content types (covers).
SAFE_URL_PREFIXES = (
    "http://", "https://", "mailto:", "ftp://", "ftps://",
    "tel:", "sms:", "irc:", "ircs:", "data:image/",
    "#", "/", "./", "../", "tel", "mailto",
)


def _is_safe_url(value: str) -> bool:
    """return True if URL value is safe to keep in an attribute"""
    if value is None:
        return True
    v = value.strip().lower()
    # strip common whitespace/control characters that browsers ignore
    v = v.replace("\x00", "").replace("\t", " ").replace("\n", " ").replace("\r", " ")
    v = " ".join(v.split())
    # allow empty / relative (no scheme)
    if v == "":
        return True
    # allow plain anchor or relative path
    if v.startswith("#"):
        return True
    for prefix in SAFE_URL_PREFIXES:
        if v.startswith(prefix):
            return True
    # no explicit scheme -> relative path
    if ":" not in v.split("/", 1)[0]:
        return True
    # has a scheme that is not in our safe list -> unsafe
    return False


def sanitize_html(html: str) -> str:
    """sanitize an html string: drop dangerous nodes/attrs, neutralize url attrs"""
    if html is None:
        return ""
    if not isinstance(html, str):
        html = str(html)
    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        # if it doesn't parse, escape the whole thing to be safe
        return _html_escape(html, quote=True)

    # 1) strip comments (could include conditional comments with scripts)
    for c in soup.find_all(string=lambda t: isinstance(t, Comment)):
        c.extract()

    # 2) remove dangerous tags (with their content)
    for tag in soup.find_all(lambda t: t.name and t.name.lower() in DANGEROUS_TAGS):
        tag.decompose()

    # 3) clean attributes on all remaining tags
    for tag in soup.find_all(True):
        if not tag.attrs:
            continue
        for attr, value in list(tag.attrs.items()):
            a = attr.lower()
            # remove on* event handlers (onload, onclick, onerror, ...)
            if a.startswith("on"):
                del tag[attr]
                continue
            # sanitize url-bearing attributes
            if a in URL_ATTRS:
                # value can be a list (multiple class etc) -- url attrs are scalar
                if isinstance(value, list):
                    value = " ".join(str(v) for v in value)
                if not _is_safe_url(str(value)):
                    # replace with a benign placeholder
                    tag[attr] = "#"
                else:
                    tag[attr] = str(value)
            # remove 'style' attribute? keep -- inline styles are common in
            # rendered books; browsers won't execute JS from CSS in this
            # context (we've already removed <script>). To be extra safe
            # against expression()/url(javascript:), drop only unsafe CSS.
            elif a == "style":
                css = "" if value is None else str(value)
                low = css.lower()
                if "javascript:" in low or "vbscript:" in low or "expression(" in low:
                    del tag[attr]

    return soup.decode()


def escape_html(text) -> str:
    """escape plain text so it can be embedded into HTML safely"""
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    return _html_escape(text, quote=True)