#!/usr/bin/env python3
"""
convert_templates.py — Конвертирует Jinja2-шаблоны из app/templates/ в Go templates в app_go/templates/.

Простой конвертер:
  1. {{ var }} → {{.Var}}  (прямое переименование)
  2. {% if ... %} → {{if ...}}
  3. {% for ... in ... %} → {{range ...}}
  4. {% endif %} → {{end}}
  5. {% endfor %} → {{end}}
  6. {% raw %}...{% endraw %} → {{/* raw */}}...{{/* endraw */}} (или без изменений)
  7. {# comment #} → удаляется или {{/* comment */}}

Важно: этот конвертер упрощённый и может потребовать ручной доработки.
"""

import os
import re
import glob
import sys

SRC_DIR = "app/templates"
DST_DIR = "app_go/templates"

def convert_template(src_path, dst_path):
    """Конвертировать один шаблон из Jinja2 в Go template."""
    with open(src_path, "r", encoding="utf-8") as f:
        content = f.read()

    original = content

    # Jinja2 комментарии → Go комментарии
    content = re.sub(r'\{#.*?#\}', lambda m: '{{/* ' + m.group(0)[2:-2].strip() + ' */}}', content, flags=re.DOTALL)

    # Jinja2 if → Go if
    content = re.sub(r'\{%\s*if\s+(.*?)\s*%\}', r'{{if \1}}', content)
    content = re.sub(r'\{%\s*else\s*%\}', r'{{else}}', content)
    content = re.sub(r'\{%\s*endif\s*%\}', r'{{end}}', content)

    # Jinja2 for → Go range
    content = re.sub(r'\{%\s*for\s+(.*?)\s+in\s+(.*?)\s*%\}', r'{{range \2}}', content)
    content = re.sub(r'\{%\s*endfor\s*%\}', r'{{end}}', content)

    # Jinja2 set → ignore in Go templates (use data struct instead)
    content = re.sub(r'\{%\s*set\s+.*?\s*%\}', '', content)

    # Jinja2 raw block → pass through (Go doesn't have raw, but content is fine)
    content = re.sub(r'\{%\s*raw\s*%\}', '', content)
    content = re.sub(r'\{%\s*endraw\s*%\}', '', content)

    # Jinja2 block → Go define
    content = re.sub(r'\{%\s*block\s+(\w+)\s*%\}', r'{{define "\1"}}', content)
    content = re.sub(r'\{%\s*endblock.*?%\}', r'{{end}}', content)

    # Jinja2 extends → remove (Go templates use different inheritance)
    content = re.sub(r'\{%\s*extends\s+.*?\s*%\}', '', content)

    # Jinja2 include → Go template
    content = re.sub(r'\{%\s*include\s+["\']?([^"\']+)["\']?\s*%\}', r'{{template "\1"}}', content)

    # {{ var }} → {{.Var}}  (capitalize first letter for Go exported field)
    def replace_var(m):
        expr = m.group(1).strip()
        if not expr:
            return "{{" + m.group(1) + "}}"
        # If already starts with . or is a function call, leave it
        if expr.startswith('.') or '(' in expr or '|' in expr:
            return m.group(0)
        
        # Handle data["key"] -> {{index .Data "key"}}
        # Go templates require 'index' for map/dict access with string keys
        data_key_match = re.match(r'^data\s*\[\s*["\'](.+?)["\']\s*\]\s*$', expr)
        if data_key_match:
            key = data_key_match.group(1)
            return '{{index .Data "' + key + '"}}'
        
        # Capitalize first letter
        result = expr[0].upper() + expr[1:]
        return "{{." + result + "}}"

    content = re.sub(r'\{\{\s*(.*?)\s*\}\}', replace_var, content)

    # Clean up multiple blank lines
    content = re.sub(r'\n{3,}', '\n\n', content)

    # Write output
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    with open(dst_path, "w", encoding="utf-8") as f:
        f.write(content)

    changed = original != content
    return changed

def main():
    if not os.path.isdir(SRC_DIR):
        print(f"Source directory {SRC_DIR} not found, skipping template conversion")
        return 0

    os.makedirs(DST_DIR, exist_ok=True)

    count = 0
    converted = 0
    for src_file in glob.glob(os.path.join(SRC_DIR, "*")):
        if os.path.isfile(src_file):
            basename = os.path.basename(src_file)
            dst_file = os.path.join(DST_DIR, basename)
            print(f"Converting: {src_file} -> {dst_file}")
            changed = convert_template(src_file, dst_file)
            count += 1
            if changed:
                converted += 1

    print(f"\nConverted {converted} of {count} templates (some may already be compatible)")
    return 0

if __name__ == "__main__":
    sys.exit(main())