"""Export docs/concept_note.md and docs/lean_canvas.md to clean, styled PDF documents."""
import os
import re
import pymupdf

CSS = """
<style>
body {
    font-family: Helvetica, Arial, sans-serif;
    color: #1e293b;
    line-height: 1.5;
    font-size: 10.5pt;
    margin: 0;
    padding: 0;
}
h1 {
    color: #0f172a;
    font-size: 20pt;
    border-bottom: 2px solid #3b82f6;
    padding-bottom: 6px;
    margin-top: 0;
    margin-bottom: 14px;
}
h2 {
    color: #1e40af;
    font-size: 13pt;
    margin-top: 14px;
    margin-bottom: 8px;
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 4px;
}
p {
    margin-top: 6px;
    margin-bottom: 8px;
}
strong {
    color: #0f172a;
}
ul, ol {
    margin-top: 4px;
    margin-bottom: 8px;
    padding-left: 20px;
}
li {
    margin-bottom: 4px;
}
.header-tag {
    display: inline-block;
    background-color: #dbeafe;
    color: #1e40af;
    font-size: 8.5pt;
    font-weight: bold;
    padding: 3px 8px;
    border-radius: 4px;
    margin-bottom: 12px;
}
.footer {
    font-size: 8pt;
    color: #64748b;
    margin-top: 20px;
    border-top: 1px solid #cbd5e1;
    padding-top: 6px;
}
</style>
"""

def md_to_html(md_text: str, tag: str) -> str:
    html = md_text
    # Escape HTML special chars inside text if any
    # Convert headings
    html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.M)
    html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.M)
    html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.M)
    # Bold and italics
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)
    # Numbered items at line starts
    html = re.sub(r"^(\d+)\.\s+(.+)$", r"<p><strong>\1.</strong> \2</p>", html, flags=re.M)
    # Unordered list items
    html = re.sub(r"^[-*]\s+(.+)$", r"<li>\1</li>", html, flags=re.M)
    # Wrap lines that are plain text paragraphs
    lines = html.split("\n")
    processed = []
    in_ul = False
    for line in lines:
        s = line.strip()
        if not s:
            if in_ul:
                processed.append("</ul>")
                in_ul = False
            continue
        if s.startswith("<li>"):
            if not in_ul:
                processed.append("<ul>")
                in_ul = True
            processed.append(s)
        elif s.startswith("<h") or s.startswith("<p"):
            if in_ul:
                processed.append("</ul>")
                in_ul = False
            processed.append(s)
        else:
            if in_ul:
                processed.append("</ul>")
                in_ul = False
            processed.append(f"<p>{s}</p>")
    if in_ul:
        processed.append("</ul>")
    
    body = "\n".join(processed)
    full_html = f"""
    <html>
    <head>{CSS}</head>
    <body>
    <div class="header-tag">{tag}</div>
    {body}
    <div class="footer">DocuSense | IBM SkillsBuild Internship 2026 | Verified Academic Deliverable</div>
    </body>
    </html>
    """
    return full_html

def convert_md_to_pdf(md_path: str, pdf_path: str, tag: str):
    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()
    html = md_to_html(md_content, tag)
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)  # US Letter
    margin = 40
    rect = pymupdf.Rect(margin, margin, 612 - margin, 792 - margin)
    page.insert_htmlbox(rect, html)
    doc.save(pdf_path)
    doc.close()
    print(f"Generated {pdf_path}")

if __name__ == "__main__":
    docs_dir = os.path.join(os.path.dirname(__file__), "..", "docs")
    convert_md_to_pdf(
        os.path.join(docs_dir, "concept_note.md"),
        os.path.join(docs_dir, "concept_note.pdf"),
        "IBM SkillsBuild-AICTE-BharatCares Internship 2026 | Project Concept Note"
    )
    convert_md_to_pdf(
        os.path.join(docs_dir, "lean_canvas.md"),
        os.path.join(docs_dir, "lean_canvas.pdf"),
        "IBM SkillsBuild-AICTE-BharatCares Internship 2026 | Lean Canvas"
    )
