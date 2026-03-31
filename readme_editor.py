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

html, body, [class*="css"] { font-family: 'Syne', sans-serif; }
.stApp { background-color: #0d0f14; color: #e8e6df; }

[data-testid="stSidebar"] { background-color: #13151c !important; border-right: 1px solid #2a2d38; }
[data-testid="stSidebar"] * { color: #c5c2b8 !important; }
h1,h2,h3 { font-family:'Syne',sans-serif !important; }

.stButton > button {
  background:#e8e6df !important; color:#0d0f14 !important;
  font-family:'Syne',sans-serif !important; font-weight:700 !important;
  border:none !important; border-radius:4px !important;
  padding:0.45rem 1.2rem !important; letter-spacing:.04em !important;
  transition:opacity .15s !important;
}
.stButton > button:hover { opacity:.78 !important; }

[data-testid="stDownloadButton"] > button {
  background:#4a6cf7 !important; color:#fff !important;
  font-family:'Syne',sans-serif !important; font-weight:700 !important;
  border:none !important; border-radius:4px !important;
  padding:0.45rem 1.2rem !important;
}

.stTextArea textarea {
  background-color:#181b24 !important; color:#e8e6df !important;
  font-family:'JetBrains Mono',monospace !important; font-size:13.5px !important;
  border:1px solid #2a2d38 !important; border-radius:6px !important;
  line-height:1.6 !important;
}
.stTextInput > div > div > input {
  background-color:#181b24 !important; color:#e8e6df !important;
  border:1px solid #2a2d38 !important; border-radius:4px !important;
}
[data-testid="stFileUploader"] {
  background:#181b24 !important; border:1.5px dashed #2a2d38 !important;
  border-radius:8px !important; padding:.6rem !important;
}

/* ── Preview pane ── */
.readme-preview {
  background:#181b24; border:1px solid #2a2d38; border-radius:8px;
  padding:2rem 2.6rem; min-height:460px; font-size:15px; line-height:1.8; color:#d4d0c8;
}
.readme-preview h1 { font-size:2rem; border-bottom:2px solid #2a2d38; padding-bottom:.4rem; margin:0 0 1.2rem; color:#f0ede6; font-family:'Syne',sans-serif; }
.readme-preview h2 { font-size:1.4rem; border-bottom:1px solid #2a2d38; padding-bottom:.25rem; margin:1.8rem 0 .8rem; color:#e8e4d9; font-family:'Syne',sans-serif; }
.readme-preview h3 { font-size:1.1rem; margin:1.4rem 0 .6rem; color:#d4d0c5; font-family:'Syne',sans-serif; }
.readme-preview h4,.readme-preview h5,.readme-preview h6 { color:#bbb8b0; font-family:'Syne',sans-serif; margin:1rem 0 .4rem; }
.readme-preview p  { margin:.5rem 0 1rem; }
.readme-preview code {
  background:#0d0f14; padding:2px 6px; border-radius:4px;
  font-family:'JetBrains Mono',monospace; font-size:12.5px; color:#7fd1ae;
}
.readme-preview pre {
  background:#0d0f14; padding:1.1rem 1.3rem; border-radius:6px;
  overflow-x:auto; border-left:3px solid #4a6cf7; margin:1rem 0;
}
.readme-preview pre code { background:transparent; padding:0; color:#cdd6f4; font-size:13px; }
.readme-preview blockquote {
  border-left:3px solid #4a6cf7; margin:1rem 0; padding:.6rem 1rem;
  color:#8a8780; font-style:italic; background:#13151c; border-radius:0 4px 4px 0;
}
.readme-preview a { color:#7da9f7; }
.readme-preview hr { border:none; border-top:1px solid #2a2d38; margin:1.5rem 0; }
.readme-preview table { width:100%; border-collapse:collapse; font-size:14px; margin:1rem 0; }
.readme-preview th { background:#0d0f14; padding:8px 12px; text-align:left; border:1px solid #2a2d38; color:#e8e4d9; }
.readme-preview td { padding:8px 12px; border:1px solid #2a2d38; }
.readme-preview tr:nth-child(even) td { background:#14161f; }
.readme-preview img { max-width:100%; border-radius:6px; }
.readme-preview ul { padding-left:1.5rem; margin:.4rem 0; list-style:disc; }
.readme-preview ol { padding-left:1.5rem; margin:.4rem 0; list-style:decimal; }
.readme-preview li { margin:.25rem 0; }
.readme-preview strong { color:#e8e6df; font-weight:700; }
.readme-preview em { font-style:italic; color:#b8b5ae; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] { gap:2px; border-bottom:1px solid #2a2d38 !important; }
.stTabs [data-baseweb="tab"] {
  background:transparent !important; color:#6b6960 !important;
  font-family:'Syne',sans-serif !important; font-weight:700 !important;
  font-size:12px !important; letter-spacing:.07em !important;
  border-radius:4px 4px 0 0 !important; padding:.4rem 1.1rem !important; border:none !important;
}
.stTabs [aria-selected="true"] { background:#181b24 !important; color:#e8e6df !important; border-bottom:2px solid #4a6cf7 !important; }

/* ── Badges ── */
.badge { display:inline-block; padding:3px 9px; border-radius:100px; font-size:10px; font-weight:700; letter-spacing:.05em; text-transform:uppercase; }
.badge-upload { background:#1a2a3a; color:#5fb3cb; }
.badge-live   { background:#2a1a3a; color:#a07afa; }
.badge-shared { background:#1a3a2a; color:#7fd1ae; }

/* ── Share box ── */
.share-box {
  background:#0d0f14; border:1px solid #4a6cf7; border-radius:8px;
  padding:.9rem 1.1rem; margin:.6rem 0 1rem;
}
.share-label { font-size:11px; font-weight:700; letter-spacing:.08em; color:#4a6cf7; text-transform:uppercase; margin-bottom:.4rem; }
.share-url {
  font-family:'JetBrains Mono',monospace; font-size:12px; color:#7da9f7;
  background:#13151c; padding:.4rem .7rem; border-radius:4px;
  border:1px solid #2a2d38; word-break:break-all; flex:1;
}
.share-note  { font-size:11px; color:#4a4840; margin-top:.4rem; }

hr.subtle { border:none; border-top:1px solid #2a2d38; margin:1rem 0; }

/* ── Welcome ── */
.welcome-card {
  background:#13151c; border:1px solid #2a2d38; border-radius:12px;
  padding:2.4rem; text-align:center; max-width:520px; margin:2.5rem auto;
}
.welcome-card .icon { font-size:2.8rem; margin-bottom:.8rem; }
.welcome-card h2 { font-size:1.35rem; color:#e8e6df; margin-bottom:.4rem; }
.welcome-card p  { font-size:.88rem; color:#6b6960; line-height:1.65; margin-bottom:1rem; }
.step { background:#0d0f14; border-radius:7px; padding:.7rem .9rem; margin:.45rem 0; text-align:left; font-size:.83rem; color:#c5c2b8; }
.step strong { color:#e8e6df; }

.stats { color:#2e2c28; font-size:11.5px; font-family:'JetBrains Mono',monospace; margin-top:.5rem; }
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
          body {{ margin:0; padding:0; background:transparent; }}
          .share-box {{
            background:#0d0f14; border:1px solid #4a6cf7; border-radius:8px;
            padding:.9rem 1.1rem; font-family:'Syne',sans-serif;
          }}
          .share-label {{ font-size:11px; font-weight:700; letter-spacing:.08em; color:#4a6cf7; text-transform:uppercase; margin-bottom:.5rem; }}
          .share-row {{ display:flex; align-items:center; gap:.5rem; }}
          .share-url {{
            font-family:'JetBrains Mono',monospace; font-size:12px; color:#7da9f7;
            background:#13151c; padding:.4rem .7rem; border-radius:4px;
            border:1px solid #2a2d38; word-break:break-all; flex:1;
          }}
          .copy-btn {{
            background:#4a6cf7; color:#fff; border:none; border-radius:4px;
            padding:5px 14px; font-size:11px; font-weight:700; cursor:pointer;
            font-family:'Syne',sans-serif; letter-spacing:.04em; white-space:nowrap;
            transition:background .2s,color .2s;
          }}
          .feedback {{ font-size:11px; color:#5fcb8a; margin-top:.4rem; display:none; }}
          .share-note {{ font-size:11px; color:#4a4840; margin-top:.5rem; }}
          code {{ background:#13151c; padding:1px 5px; border-radius:3px; color:#7fd1ae; font-family:'JetBrains Mono',monospace; }}
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
          var fullUrl = window.location.ancestorOrigins && window.location.ancestorOrigins[0]
            ? window.location.ancestorOrigins[0] + "/?share=" + sid
            : window.location.origin + "/?share=" + sid;

          document.getElementById("share-url").textContent = fullUrl;

          // Auto-copy immediately
          navigator.clipboard && navigator.clipboard.writeText(fullUrl).then(function() {{
            document.getElementById("feedback").style.display = "block";
          }}).catch(function(){{}});

          function doCopy() {{
            navigator.clipboard && navigator.clipboard.writeText(fullUrl).then(function() {{
              var btn = document.getElementById("copy-btn");
              var fb  = document.getElementById("feedback");
              btn.textContent = "Copied!";
              btn.style.background = "#1a3a2a";
              btn.style.color = "#5fcb8a";
              fb.style.display = "block";
              setTimeout(function() {{
                btn.textContent = "Copy";
                btn.style.background = "#4a6cf7";
                btn.style.color = "#fff";
              }}, 2000);
            }});
          }}
        </script>
        """, height=110)

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
