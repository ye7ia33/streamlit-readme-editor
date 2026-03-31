import streamlit as st
import hashlib
import json
import os
import time
import re

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="README Studio",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Storage helpers (file-based, works on Streamlit Cloud) ─────────────────────
def md_to_html(text: str) -> str:
    """
    Convert markdown to HTML with a minimal hand-rolled parser.
    Handles: headings, bold, italic, inline code, fenced code blocks,
    blockquotes, unordered/ordered lists, tables, hr, links, images, paragraphs.
    Returns a single HTML string safe to inject inside a <div>.
    """
    lines = text.split("\n")
    out = []
    i = 0
    in_ul = in_ol = in_table = False

    def close_lists():
        nonlocal in_ul, in_ol
        if in_ul:  out.append("</ul>"); in_ul = False
        if in_ol:  out.append("</ol>"); in_ol = False

    def close_table():
        nonlocal in_table
        if in_table: out.append("</tbody></table>"); in_table = False

    def inline(s: str) -> str:
        # Images before links
        s = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1">', s)
        s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', s)
        s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
        s = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', s)
        s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
        s = re.sub(r'__(.+?)__', r'<strong>\1</strong>', s)
        s = re.sub(r'\*(.+?)\*', r'<em>\1</em>', s)
        s = re.sub(r'_(.+?)_', r'<em>\1</em>', s)
        s = re.sub(r'~~(.+?)~~', r'<del>\1</del>', s)
        return s

    while i < len(lines):
        line = lines[i]

        # Fenced code block
        if line.strip().startswith("```"):
            close_lists(); close_table()
            lang = line.strip()[3:].strip()
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i].replace("&","&amp;").replace("<","&lt;").replace(">","&gt;"))
                i += 1
            lang_cls = f' class="language-{lang}"' if lang else ""
            out.append(f'<pre><code{lang_cls}>{chr(10).join(code_lines)}</code></pre>')
            i += 1
            continue

        # Headings
        m = re.match(r'^(#{1,6})\s+(.*)', line)
        if m:
            close_lists(); close_table()
            lvl = len(m.group(1))
            out.append(f'<h{lvl}>{inline(m.group(2))}</h{lvl}>')
            i += 1; continue

        # HR
        if re.match(r'^[-*_]{3,}\s*$', line):
            close_lists(); close_table()
            out.append('<hr>'); i += 1; continue

        # Blockquote
        if line.startswith(">"):
            close_lists(); close_table()
            content = re.sub(r'^>\s?', '', line)
            out.append(f'<blockquote>{inline(content)}</blockquote>')
            i += 1; continue

        # Unordered list
        if re.match(r'^[\*\-\+]\s+', line):
            close_table()
            if not in_ul:
                if in_ol: out.append("</ol>"); in_ol = False
                out.append("<ul>"); in_ul = True
            content = re.sub(r'^[\*\-\+]\s+', '', line)
            out.append(f'<li>{inline(content)}</li>')
            i += 1; continue

        # Ordered list
        if re.match(r'^\d+\.\s+', line):
            close_table()
            if not in_ol:
                if in_ul: out.append("</ul>"); in_ul = False
                out.append("<ol>"); in_ol = True
            content = re.sub(r'^\d+\.\s+', '', line)
            out.append(f'<li>{inline(content)}</li>')
            i += 1; continue

        # Table
        if "|" in line:
            close_lists()
            cols = [c.strip() for c in line.strip().strip("|").split("|")]
            if i + 1 < len(lines) and re.match(r'^[\|\s\-:]+$', lines[i+1]):
                if not in_table:
                    out.append('<table><thead><tr>')
                    for c in cols: out.append(f'<th>{inline(c)}</th>')
                    out.append('</tr></thead><tbody>')
                    in_table = True
                i += 2; continue
            elif in_table:
                out.append('<tr>')
                for c in cols: out.append(f'<td>{inline(c)}</td>')
                out.append('</tr>')
                i += 1; continue

        # Blank line
        if line.strip() == "":
            close_lists(); close_table()
            out.append('<br>'); i += 1; continue

        # Paragraph
        close_lists(); close_table()
        out.append(f'<p>{inline(line)}</p>')
        i += 1

    close_lists(); close_table()
    return "\n".join(out)

def preview_block(content: str) -> None:
    """Render markdown inside a styled preview div as a SINGLE st.markdown call."""
    html = md_to_html(content)
    st.markdown(f'<div class="readme-preview">{html}</div>', unsafe_allow_html=True)

STORE_DIR = "/tmp/readme_studio_shares"
os.makedirs(STORE_DIR, exist_ok=True)

def save_share(content: str, title: str) -> str:
    """Save content to disk, return a short 8-char ID."""
    share_id = hashlib.sha256((content + str(time.time())).encode()).hexdigest()[:8]
    path = os.path.join(STORE_DIR, f"{share_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"content": content, "title": title, "ts": time.time()}, f)
    return share_id

def load_share(share_id: str) -> dict | None:
    """Load a previously saved share by ID."""
    path = os.path.join(STORE_DIR, f"{share_id}.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Syne:wght@400;700;800&display=swap');

/* ══ THEME TOKENS — dark (default) ══ */
:root {
  --bg:          #0d0f14;
  --bg-2:        #13151c;
  --bg-3:        #181b24;
  --border:      #2a2d38;
  --text:        #e8e6df;
  --text-2:      #c5c2b8;
  --text-3:      #8a8780;
  --text-muted:  #4a4840;
  --text-faint:  #2e2c28;
  --accent:      #4a6cf7;
  --accent-soft: #7da9f7;
  --green:       #7fd1ae;
  --code-fg:     #7fd1ae;
  --pre-fg:      #cdd6f4;
  --btn-bg:      #e8e6df;
  --btn-fg:      #0d0f14;
  --tab-active-bg: #181b24;
}

/* ══ LIGHT MODE OVERRIDES ══ */
@media (prefers-color-scheme: light) {
  :root {
    --bg:          #f7f8fc;
    --bg-2:        #ffffff;
    --bg-3:        #eef0f6;
    --border:      #d0d4e4;
    --text:        #1a1c24;
    --text-2:      #3a3d4a;
    --text-3:      #6b6e80;
    --text-muted:  #9099b0;
    --text-faint:  #c0c4d4;
    --accent:      #3558e8;
    --accent-soft: #2a46c8;
    --green:       #1a7a50;
    --code-fg:     #1a6640;
    --pre-fg:      #2a3a8a;
    --btn-bg:      #1a1c24;
    --btn-fg:      #f7f8fc;
    --tab-active-bg: #eef0f6;
  }
}

/* ══ Also respect Streamlit's data-theme attribute ══ */
[data-theme="light"] {
  --bg:          #f7f8fc;
  --bg-2:        #ffffff;
  --bg-3:        #eef0f6;
  --border:      #d0d4e4;
  --text:        #1a1c24;
  --text-2:      #3a3d4a;
  --text-3:      #6b6e80;
  --text-muted:  #9099b0;
  --text-faint:  #c0c4d4;
  --accent:      #3558e8;
  --accent-soft: #2a46c8;
  --green:       #1a7a50;
  --code-fg:     #1a6640;
  --pre-fg:      #2a3a8a;
  --btn-bg:      #1a1c24;
  --btn-fg:      #f7f8fc;
  --tab-active-bg: #eef0f6;
}

html, body, [class*="css"] { font-family: 'Syne', sans-serif; }
.stApp { background-color: var(--bg) !important; color: var(--text) !important; }

[data-testid="stSidebar"] {
  background-color: var(--bg-2) !important;
  border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text-2) !important; }
h1,h2,h3 { font-family:'Syne',sans-serif !important; color: var(--text) !important; }

.stButton > button {
  background: var(--btn-bg) !important;
  color: var(--btn-fg) !important;
  font-family:'Syne',sans-serif !important; font-weight:700 !important;
  border:none !important; border-radius:4px !important;
  padding:0.45rem 1.2rem !important; letter-spacing:.04em !important;
  transition:opacity .15s !important;
}
.stButton > button:hover { opacity:.75 !important; }

[data-testid="stDownloadButton"] > button {
  background: var(--accent) !important; color:#fff !important;
  font-family:'Syne',sans-serif !important; font-weight:700 !important;
  border:none !important; border-radius:4px !important;
  padding:0.45rem 1.2rem !important;
}

.stTextArea textarea {
  background-color: var(--bg-3) !important;
  color: var(--text) !important;
  font-family:'JetBrains Mono',monospace !important; font-size:13.5px !important;
  border:1px solid var(--border) !important; border-radius:6px !important;
  line-height:1.6 !important;
}
.stTextInput > div > div > input {
  background-color: var(--bg-3) !important;
  color: var(--text) !important;
  border:1px solid var(--border) !important; border-radius:4px !important;
}
[data-testid="stFileUploader"] {
  background: var(--bg-3) !important;
  border:1.5px dashed var(--border) !important;
  border-radius:8px !important; padding:.6rem !important;
}

/* ── Preview pane ── */
.readme-preview {
  background: var(--bg-3);
  border:1px solid var(--border);
  border-radius:8px;
  padding:2rem 2.6rem; min-height:460px; font-size:15px; line-height:1.8;
  color: var(--text-2);
}
.readme-preview h1 { font-size:2rem; border-bottom:2px solid var(--border); padding-bottom:.4rem; margin:0 0 1.2rem; color:var(--text); font-family:'Syne',sans-serif; }
.readme-preview h2 { font-size:1.4rem; border-bottom:1px solid var(--border); padding-bottom:.25rem; margin:1.8rem 0 .8rem; color:var(--text); font-family:'Syne',sans-serif; }
.readme-preview h3 { font-size:1.1rem; margin:1.4rem 0 .6rem; color:var(--text-2); font-family:'Syne',sans-serif; }
.readme-preview h4,.readme-preview h5,.readme-preview h6 { color:var(--text-2); font-family:'Syne',sans-serif; margin:1rem 0 .4rem; }
.readme-preview p  { margin:.5rem 0 1rem; }
.readme-preview code {
  background: var(--bg);
  padding:2px 6px; border-radius:4px;
  font-family:'JetBrains Mono',monospace; font-size:12.5px; color:var(--code-fg);
}
.readme-preview pre {
  background: var(--bg);
  padding:1.1rem 1.3rem; border-radius:6px;
  overflow-x:auto; border-left:3px solid var(--accent); margin:1rem 0;
}
.readme-preview pre code { background:transparent; padding:0; color:var(--pre-fg); font-size:13px; }
.readme-preview blockquote {
  border-left:3px solid var(--accent); margin:1rem 0; padding:.6rem 1rem;
  color:var(--text-3); font-style:italic; background:var(--bg-2); border-radius:0 4px 4px 0;
}
.readme-preview a { color:var(--accent-soft); }
.readme-preview hr { border:none; border-top:1px solid var(--border); margin:1.5rem 0; }
.readme-preview table { width:100%; border-collapse:collapse; font-size:14px; margin:1rem 0; }
.readme-preview th { background:var(--bg); padding:8px 12px; text-align:left; border:1px solid var(--border); color:var(--text); }
.readme-preview td { padding:8px 12px; border:1px solid var(--border); color:var(--text-2); }
.readme-preview tr:nth-child(even) td { background:var(--bg-2); }
.readme-preview img { max-width:100%; border-radius:6px; }
.readme-preview ul { padding-left:1.5rem; margin:.4rem 0; list-style:disc; }
.readme-preview ol { padding-left:1.5rem; margin:.4rem 0; list-style:decimal; }
.readme-preview li { margin:.25rem 0; }
.readme-preview strong { color:var(--text); font-weight:700; }
.readme-preview em { font-style:italic; color:var(--text-3); }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] { gap:2px; border-bottom:1px solid var(--border) !important; }
.stTabs [data-baseweb="tab"] {
  background:transparent !important; color:var(--text-muted) !important;
  font-family:'Syne',sans-serif !important; font-weight:700 !important;
  font-size:12px !important; letter-spacing:.07em !important;
  border-radius:4px 4px 0 0 !important; padding:.4rem 1.1rem !important; border:none !important;
}
.stTabs [aria-selected="true"] {
  background: var(--tab-active-bg) !important;
  color: var(--text) !important;
  border-bottom:2px solid var(--accent) !important;
}

/* ── Badges ── */
.badge { display:inline-block; padding:3px 9px; border-radius:100px; font-size:10px; font-weight:700; letter-spacing:.05em; text-transform:uppercase; }
.badge-upload { background:#1a2a3a; color:#5fb3cb; }
.badge-live   { background:#2a1a3a; color:#a07afa; }
.badge-shared { background:#1a3a2a; color:#7fd1ae; }

hr.subtle { border:none; border-top:1px solid var(--border); margin:1rem 0; }

/* ── Welcome ── */
.welcome-card {
  background: var(--bg-2); border:1px solid var(--border); border-radius:12px;
  padding:2.4rem; text-align:center; max-width:520px; margin:2.5rem auto;
}
.welcome-card .icon { font-size:2.8rem; margin-bottom:.8rem; }
.welcome-card h2 { font-size:1.35rem; color:var(--text); margin-bottom:.4rem; }
.welcome-card p  { font-size:.88rem; color:var(--text-3); line-height:1.65; margin-bottom:1rem; }
.step { background:var(--bg); border-radius:7px; padding:.7rem .9rem; margin:.45rem 0; text-align:left; font-size:.83rem; color:var(--text-2); }
.step strong { color:var(--text); }

.stats { color:var(--text-faint); font-size:11.5px; font-family:'JetBrains Mono',monospace; margin-top:.5rem; }
</style>
""", unsafe_allow_html=True)

# ── Session defaults ────────────────────────────────────────────────────────────
for k, v in {
    "content": "",
    "source_name": "README.md",
    "source_mode": None,
    "show_share": False,
    "share_id": None,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Handle ?share=ID on first load ─────────────────────────────────────────────
qp = st.query_params
share_id_param = qp.get("share", "")
if share_id_param and st.session_state.source_mode is None:
    data = load_share(share_id_param)
    if data:
        st.session_state.content     = data["content"]
        st.session_state.source_name = data.get("title", "shared-readme.md")
        st.session_state.source_mode = "shared"
        st.session_state.share_id    = share_id_param
    else:
        st.warning("⚠️ Share link expired or not found. Start a new README below.")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📝 README Studio")
    st.markdown('<hr class="subtle">', unsafe_allow_html=True)

    st.markdown("### 📤 Upload")
    uploaded = st.file_uploader("Drop a .md / .txt file", type=["md", "txt"], label_visibility="collapsed")
    if uploaded:
        raw = uploaded.read().decode("utf-8")
        if raw != st.session_state.content or st.session_state.source_mode != "upload":
            st.session_state.update(content=raw, source_name=uploaded.name, source_mode="upload", show_share=False, share_id=None)
            st.query_params.clear()
            st.rerun()

    st.markdown('<hr class="subtle">', unsafe_allow_html=True)
    st.markdown("### ✍️ New README")
    live_title = st.text_input("Project name", placeholder="My Awesome Project", label_visibility="collapsed")
    if st.button("✨ Generate template", use_container_width=True):
        title = live_title.strip() or "My Project"
        slug  = title.lower().replace(" ", "-")
        mod   = title.lower().replace(" ", "_")
        tpl = f"""# {title}

> Short description of what this project does and who it's for.

## 🚀 Features

- ✅ Feature one
- ✅ Feature two
- ✅ Feature three

## 📦 Installation

```bash
pip install {slug}
```

## 🛠 Usage

```python
import {mod}

result = {mod}.run()
print(result)
```

## 🤝 Contributing

Pull requests are welcome! Please open an issue first for major changes.

## 📄 License

[MIT](LICENSE) © {title}
"""
        st.session_state.update(content=tpl, source_name=f"{slug}-README.md", source_mode="live", show_share=False, share_id=None)
        st.query_params.clear()
        st.rerun()

    st.markdown('<hr class="subtle">', unsafe_allow_html=True)
    if st.session_state.source_mode:
        if st.button("🗑 Clear", use_container_width=True):
            st.session_state.update(content="", source_name="README.md", source_mode=None, show_share=False, share_id=None)
            st.query_params.clear()
            st.rerun()

    st.markdown('<hr class="subtle">', unsafe_allow_html=True)
    st.markdown('<div style="font-size:11px;color:#2e2c28;text-align:center">README Studio</div>', unsafe_allow_html=True)

# ── Header row ─────────────────────────────────────────────────────────────────
c_title, c_badge, c_btns = st.columns([4.5, 1.8, 2.2])

with c_title:
    st.markdown("# README Studio")

if st.session_state.source_mode:
    with c_badge:
        bmap = {"upload":"badge-upload ⬆ Uploaded","live":"badge-live ✍ Live","shared":"badge-shared 🔗 Shared"}
        cls, label = bmap[st.session_state.source_mode].split(" ", 1)
        st.markdown(f'<div style="padding-top:1.55rem"><span class="badge {cls}">{label}</span></div>', unsafe_allow_html=True)

    with c_btns:
        dl_name = st.session_state.source_name
        b1, b2 = st.columns(2)
        with b1:
            st.download_button("⬇ .md", data=st.session_state.content.encode(),
                               file_name=dl_name, mime="text/markdown", use_container_width=True)
        with b2:
            if st.button("🔗 Share", use_container_width=True, key="share_btn"):
                sid = save_share(st.session_state.content, st.session_state.source_name)
                st.session_state.share_id   = sid
                st.session_state.show_share = True
                st.rerun()

    st.markdown(f'<div style="font-family:JetBrains Mono,monospace;font-size:11px;color:#3a3830;margin-bottom:4px">📄 {st.session_state.source_name}</div>', unsafe_allow_html=True)

    # ── Share panel — auto-copy on appearance ──────────────────────────────
    if st.session_state.show_share and st.session_state.share_id:
        sid = st.session_state.share_id
        import streamlit.components.v1 as components
        components.html(f"""
        <style>
          @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400&family=Syne:wght@700&display=swap');
          :root {{
            --bg:       #0d0f14; --bg-2: #13151c; --border: #2a2d38;
            --text:     #e8e6df; --text-3: #4a4840;
            --accent:   #4a6cf7; --url-fg: #7da9f7; --green: #5fcb8a;
            --green-bg: #1a3a2a;
          }}
          @media (prefers-color-scheme: light) {{
            :root {{
              --bg:     #f7f8fc; --bg-2: #eef0f6; --border: #d0d4e4;
              --text:   #1a1c24; --text-3: #9099b0;
              --accent: #3558e8; --url-fg: #2a46c8; --green: #1a7a50;
              --green-bg: #d0f0e0;
            }}
          }}
          body {{ margin:0; padding:0; background:transparent; font-family:'Syne',sans-serif; }}
          .share-box {{
            background:var(--bg); border:1px solid var(--accent); border-radius:8px;
            padding:.9rem 1.1rem;
          }}
          .share-label {{ font-size:11px; font-weight:700; letter-spacing:.08em; color:var(--accent); text-transform:uppercase; margin-bottom:.5rem; }}
          .share-row {{ display:flex; align-items:center; gap:.5rem; }}
          .share-url {{
            font-family:'JetBrains Mono',monospace; font-size:12px; color:var(--url-fg);
            background:var(--bg-2); padding:.4rem .7rem; border-radius:4px;
            border:1px solid var(--border); word-break:break-all; flex:1;
          }}
          .copy-btn {{
            background:var(--accent); color:#fff; border:none; border-radius:4px;
            padding:5px 14px; font-size:11px; font-weight:700; cursor:pointer;
            font-family:'Syne',sans-serif; letter-spacing:.04em; white-space:nowrap;
            transition:background .2s, color .2s;
          }}
          .feedback {{ font-size:11px; color:var(--green); margin-top:.4rem; display:none; }}
          .share-note {{ font-size:11px; color:var(--text-3); margin-top:.5rem; }}
        </style>
        <div class="share-box">
          <div class="share-label">🔗 Share link</div>
          <div class="share-row">
            <div class="share-url" id="share-url">building link…</div>
            <button class="copy-btn" id="copy-btn" onclick="doCopy()">Copy</button>
          </div>
          <div class="feedback" id="feedback">✓ Copied to clipboard!</div>
          <div class="share-note">Anyone with this link sees the rendered preview.</div>
        </div>
        <script>
          var sid = "{sid}";
          var origin = (window.location.ancestorOrigins && window.location.ancestorOrigins[0])
            ? window.location.ancestorOrigins[0]
            : window.location.origin;
          var fullUrl = origin + "/?share=" + sid;

          document.getElementById("share-url").textContent = fullUrl;

          navigator.clipboard && navigator.clipboard.writeText(fullUrl).then(function() {{
            document.getElementById("feedback").style.display = "block";
          }}).catch(function(){{}});

          function doCopy() {{
            navigator.clipboard && navigator.clipboard.writeText(fullUrl).then(function() {{
              var btn = document.getElementById("copy-btn");
              var fb  = document.getElementById("feedback");
              btn.textContent = "Copied!";
              btn.style.background = "var(--green-bg)";
              btn.style.color = "var(--green)";
              fb.style.display = "block";
              setTimeout(function() {{
                btn.textContent = "Copy";
                btn.style.background = "var(--accent)";
                btn.style.color = "#fff";
              }}, 2000);
            }});
          }}
        </script>
        """, height=115)

st.markdown('<hr class="subtle">', unsafe_allow_html=True)

# ── Welcome ────────────────────────────────────────────────────────────────────
if not st.session_state.source_mode:
    st.markdown("""
    <div class="welcome-card">
      <div class="icon">📝</div>
      <h2>Welcome to README Studio</h2>
      <p>Edit, preview, and share Markdown files — right in your browser.</p>
      <div class="step"><strong>📤 Upload</strong> — drag &amp; drop any <code>.md</code> file</div>
      <div class="step"><strong>✍️ New README</strong> — generate from a smart template</div>
      <div class="step"><strong>🔗 Share</strong> — get a short link for a read-only preview</div>
      <div class="step"><strong>⬇ Download</strong> — save your edited file back to disk</div>
    </div>
    """, unsafe_allow_html=True)

# ── Shared / read-only view ────────────────────────────────────────────────────
elif st.session_state.source_mode == "shared":
    st.markdown("#### 👁 Shared README Preview")
    preview_block(st.session_state.content)

# ── Editor tabs ────────────────────────────────────────────────────────────────
else:
    tab_e, tab_p, tab_s = st.tabs(["EDITOR", "PREVIEW", "SPLIT"])

    with tab_e:
        new_val = st.text_area("ed", value=st.session_state.content,
                               height=560, label_visibility="collapsed", key="main_ed")
        if new_val != st.session_state.content:
            st.session_state.content = new_val
            st.rerun()

    with tab_p:
        if st.session_state.content.strip():
            preview_block(st.session_state.content)
        else:
            st.markdown('<div style="text-align:center;padding:4rem 0;color:#2e2c28"><div style="font-size:2rem">👁</div><div style="margin-top:.5rem;font-size:.88rem">Nothing yet — write something in the Editor tab.</div></div>', unsafe_allow_html=True)

    with tab_s:
        l, r = st.columns(2, gap="medium")
        with l:
            st.markdown('<div style="font-size:11px;font-weight:700;letter-spacing:.08em;color:#4a4840;margin-bottom:.3rem">✏️ EDITOR</div>', unsafe_allow_html=True)
            sv = st.text_area("sp", value=st.session_state.content,
                              height=500, label_visibility="collapsed", key="split_ed")
            if sv != st.session_state.content:
                st.session_state.content = sv
                st.rerun()
        with r:
            st.markdown('<div style="font-size:11px;font-weight:700;letter-spacing:.08em;color:#4a4840;margin-bottom:.3rem">👁 PREVIEW</div>', unsafe_allow_html=True)
            if st.session_state.content.strip():
                preview_block(st.session_state.content)
            else:
                st.markdown('<div style="color:#2e2c28;padding:2rem .5rem;font-size:.85rem">Start typing…</div>', unsafe_allow_html=True)

    # Stats
    w = len(st.session_state.content.split())
    c = len(st.session_state.content)
    ln = st.session_state.content.count("\n") + 1
    st.markdown(f'<div class="stats">Lines: {ln} &nbsp;·&nbsp; Words: {w} &nbsp;·&nbsp; Chars: {c}</div>', unsafe_allow_html=True)
