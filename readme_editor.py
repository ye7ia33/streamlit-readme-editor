import streamlit as st
import os

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="README Studio",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Syne:wght@400;700;800&display=swap');

  html, body, [class*="css"] { font-family: 'Syne', sans-serif; }
  .stApp { background-color: #0d0f14; color: #e8e6df; }

  [data-testid="stSidebar"] { background-color: #13151c !important; border-right: 1px solid #2a2d38; }
  [data-testid="stSidebar"] * { color: #c5c2b8 !important; }

  h1, h2, h3 { font-family: 'Syne', sans-serif !important; }

  .stButton > button {
    background: #e8e6df !important; color: #0d0f14 !important;
    font-family: 'Syne', sans-serif !important; font-weight: 700 !important;
    border: none !important; border-radius: 4px !important;
    padding: 0.5rem 1.4rem !important; letter-spacing: 0.04em !important;
    transition: opacity .2s !important;
  }
  .stButton > button:hover { opacity: 0.82 !important; }

  [data-testid="stDownloadButton"] > button {
    background: #4a6cf7 !important; color: #fff !important;
    font-family: 'Syne', sans-serif !important; font-weight: 700 !important;
    border: none !important; border-radius: 4px !important;
    padding: 0.5rem 1.4rem !important; letter-spacing: 0.04em !important;
  }
  [data-testid="stDownloadButton"] > button:hover { opacity: 0.82 !important; }

  .stTextArea textarea {
    background-color: #181b24 !important; color: #e8e6df !important;
    font-family: 'JetBrains Mono', monospace !important; font-size: 13.5px !important;
    border: 1px solid #2a2d38 !important; border-radius: 6px !important;
  }

  .stSelectbox > div > div, .stTextInput > div > div > input {
    background-color: #181b24 !important; color: #e8e6df !important;
    border: 1px solid #2a2d38 !important; border-radius: 4px !important;
    font-family: 'Syne', sans-serif !important;
  }

  [data-testid="stFileUploader"] {
    background: #181b24 !important; border: 1.5px dashed #2a2d38 !important;
    border-radius: 8px !important; padding: .8rem !important;
  }

  .readme-preview {
    background: #181b24; border: 1px solid #2a2d38; border-radius: 8px;
    padding: 2rem 2.4rem; min-height: 480px; font-size: 15px; line-height: 1.75;
  }
  .readme-preview h1 { font-size:2rem; border-bottom:2px solid #2a2d38; padding-bottom:.4rem; margin-bottom:1rem; color:#f0ede6; }
  .readme-preview h2 { font-size:1.45rem; border-bottom:1px solid #2a2d38; padding-bottom:.3rem; margin-top:1.6rem; color:#e8e4d9; }
  .readme-preview h3 { font-size:1.15rem; color:#d4d0c5; }
  .readme-preview code { background:#0d0f14; padding:2px 7px; border-radius:4px; font-family:'JetBrains Mono',monospace; font-size:12.5px; color:#7fd1ae; }
  .readme-preview pre  { background:#0d0f14; padding:1.1rem; border-radius:6px; overflow-x:auto; border-left:3px solid #4a6cf7; }
  .readme-preview pre code { background:transparent; padding:0; color:#cdd6f4; font-size:13px; }
  .readme-preview blockquote { border-left:3px solid #4a6cf7; margin-left:0; padding-left:1rem; color:#8a8780; font-style:italic; }
  .readme-preview a { color:#7da9f7; }
  .readme-preview hr { border:none; border-top:1px solid #2a2d38; }
  .readme-preview table { width:100%; border-collapse:collapse; font-size:14px; }
  .readme-preview th { background:#0d0f14; padding:8px 12px; text-align:left; border:1px solid #2a2d38; color:#e8e4d9; }
  .readme-preview td { padding:8px 12px; border:1px solid #2a2d38; color:#c5c2b8; }
  .readme-preview tr:nth-child(even) td { background:#14161f; }
  .readme-preview img { max-width:100%; border-radius:6px; }
  .readme-preview ul, .readme-preview ol { padding-left:1.4rem; }
  .readme-preview li { margin:.3rem 0; }

  .stTabs [data-baseweb="tab-list"] { gap:4px; border-bottom:1px solid #2a2d38 !important; }
  .stTabs [data-baseweb="tab"] {
    background:transparent !important; color:#6b6960 !important;
    font-family:'Syne',sans-serif !important; font-weight:700 !important;
    font-size:13px !important; letter-spacing:.06em !important;
    border-radius:4px 4px 0 0 !important; padding:.45rem 1.2rem !important; border:none !important;
  }
  .stTabs [aria-selected="true"] { background:#181b24 !important; color:#e8e6df !important; border-bottom:2px solid #4a6cf7 !important; }

  .badge { display:inline-block; padding:3px 10px; border-radius:100px; font-size:11px; font-weight:700; letter-spacing:.05em; text-transform:uppercase; }
  .badge-upload  { background:#1a2a3a; color:#5fb3cb; }
  .badge-live    { background:#2a1a3a; color:#a07afa; }
  .badge-saved   { background:#1a3a2a; color:#5fcb8a; }

  .source-label { font-family:'JetBrains Mono',monospace; font-size:12px; color:#5c5a54; margin-bottom:6px; }
  hr.subtle { border:none; border-top:1px solid #2a2d38; margin:1.2rem 0; }

  .welcome-card {
    background:#13151c; border:1px solid #2a2d38; border-radius:12px;
    padding:2.5rem; text-align:center; max-width:520px; margin:3rem auto;
  }
  .welcome-card .icon { font-size:3rem; margin-bottom:1rem; }
  .welcome-card h2 { font-size:1.4rem; color:#e8e6df; margin-bottom:.5rem; }
  .welcome-card p  { font-size:.9rem; color:#6b6960; line-height:1.6; }
  .step { background:#0d0f14; border-radius:8px; padding:.8rem 1rem; margin:.6rem 0; text-align:left; font-size:.85rem; color:#c5c2b8; }
  .step strong { color:#e8e6df; }
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
defaults = {
    "content": "",
    "source_name": "",
    "source_mode": None,  # "upload" | "live"
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📝 README Studio")
    st.markdown('<hr class="subtle">', unsafe_allow_html=True)

    # ── Upload mode ─────────────────────────────────────────────────────────
    st.markdown("### 📤 Upload a file")
    uploaded = st.file_uploader(
        "Drop a .md file",
        type=["md", "txt"],
        label_visibility="collapsed",
    )
    if uploaded is not None:
        content = uploaded.read().decode("utf-8")
        if content != st.session_state.content or st.session_state.source_mode != "upload":
            st.session_state.content = content
            st.session_state.source_name = uploaded.name
            st.session_state.source_mode = "upload"
            st.rerun()

    st.markdown('<hr class="subtle">', unsafe_allow_html=True)

    # ── Live / template mode ─────────────────────────────────────────────────
    st.markdown("### ✍️ Start from scratch")
    live_title = st.text_input(
        "Project name",
        placeholder="My Awesome Project",
        label_visibility="collapsed",
    )
    if st.button("✨ New README", use_container_width=True):
        title = live_title.strip() or "My Project"
        slug = title.lower().replace(" ", "-")
        mod  = title.lower().replace(" ", "_")
        template = f"""# {title}

> A short, punchy description of what this project does.

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

# Example usage
result = {mod}.run()
print(result)
```

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first.

## 📄 License

[MIT](LICENSE) © {title}
"""
        st.session_state.content = template
        st.session_state.source_name = f"{slug}-README.md"
        st.session_state.source_mode = "live"
        st.rerun()

    st.markdown('<hr class="subtle">', unsafe_allow_html=True)

    if st.session_state.source_mode:
        if st.button("🗑 Clear / Start over", use_container_width=True):
            for k, v in defaults.items():
                st.session_state[k] = v
            st.rerun()

    st.markdown('<hr class="subtle">', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:11px;color:#3a3830;text-align:center">README Studio · Built with Streamlit</div>',
        unsafe_allow_html=True,
    )

# ── Main ───────────────────────────────────────────────────────────────────────

# Header row
col_title, col_meta, col_dl = st.columns([5, 2, 1.5])
with col_title:
    st.markdown("# README Studio")

if st.session_state.source_mode:
    with col_meta:
        mode_badge = (
            '<span class="badge badge-upload">⬆ Uploaded</span>'
            if st.session_state.source_mode == "upload"
            else '<span class="badge badge-live">✍ Live</span>'
        )
        st.markdown(
            f'<div style="padding-top:1.6rem">{mode_badge} <span class="badge badge-saved">✓ Ready</span></div>',
            unsafe_allow_html=True,
        )

    with col_dl:
        dl_name = st.session_state.source_name or "README.md"
        if not dl_name.endswith(".md"):
            dl_name += ".md"
        st.download_button(
            label="⬇ Download",
            data=st.session_state.content.encode("utf-8"),
            file_name=dl_name,
            mime="text/markdown",
            use_container_width=True,
        )

    st.markdown(
        f'<div class="source-label">📄 {st.session_state.source_name}</div>',
        unsafe_allow_html=True,
    )

st.markdown('<hr class="subtle">', unsafe_allow_html=True)

# ── Welcome screen ─────────────────────────────────────────────────────────────
if not st.session_state.source_mode:
    st.markdown("""
    <div class="welcome-card">
      <div class="icon">📝</div>
      <h2>Welcome to README Studio</h2>
      <p>Edit, preview, and download Markdown README files — right in your browser.<br>
         Choose a mode from the sidebar to get started.</p>
      <div class="step"><strong>📤 Upload</strong> — drag &amp; drop an existing <code>.md</code> file to read &amp; edit it</div>
      <div class="step"><strong>✍️ Live editor</strong> — enter a project name and start from a smart template</div>
      <div class="step"><strong>⬇ Download</strong> — save your edited README back to your computer</div>
    </div>
    """, unsafe_allow_html=True)

# ── Editor area ────────────────────────────────────────────────────────────────
else:
    tab_editor, tab_preview, tab_split = st.tabs(["EDITOR", "PREVIEW", "SPLIT VIEW"])

    with tab_editor:
        new_val = st.text_area(
            "editor",
            value=st.session_state.content,
            height=580,
            label_visibility="collapsed",
            key="main_editor",
        )
        if new_val != st.session_state.content:
            st.session_state.content = new_val
            st.rerun()

    with tab_preview:
        st.markdown('<div class="readme-preview">', unsafe_allow_html=True)
        st.markdown(st.session_state.content)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab_split:
        left, right = st.columns(2, gap="medium")
        with left:
            st.markdown('<div style="font-size:12px;font-weight:700;letter-spacing:.08em;color:#6b6960;margin-bottom:.4rem">✏️ EDITOR</div>', unsafe_allow_html=True)
            split_val = st.text_area(
                "split",
                value=st.session_state.content,
                height=520,
                label_visibility="collapsed",
                key="split_editor",
            )
            if split_val != st.session_state.content:
                st.session_state.content = split_val
                st.rerun()
        with right:
            st.markdown('<div style="font-size:12px;font-weight:700;letter-spacing:.08em;color:#6b6960;margin-bottom:.4rem">👁 PREVIEW</div>', unsafe_allow_html=True)
            st.markdown('<div class="readme-preview">', unsafe_allow_html=True)
            st.markdown(st.session_state.content)
            st.markdown('</div>', unsafe_allow_html=True)

    # Stats footer
    words = len(st.session_state.content.split())
    chars = len(st.session_state.content)
    lines = st.session_state.content.count("\n") + 1
    st.markdown(
        f'<div style="color:#3a3830;font-size:12px;font-family:JetBrains Mono,monospace;margin-top:.6rem">'
        f'Lines: {lines} &nbsp;·&nbsp; Words: {words} &nbsp;·&nbsp; Characters: {chars}'
        f'</div>',
        unsafe_allow_html=True,
    )
