import streamlit as st
import os
import glob

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="README Editor",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Syne:wght@400;700;800&display=swap');

  html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
  }

  /* Dark editorial theme */
  .stApp {
    background-color: #0d0f14;
    color: #e8e6df;
  }

  /* Sidebar */
  [data-testid="stSidebar"] {
    background-color: #13151c !important;
    border-right: 1px solid #2a2d38;
  }
  [data-testid="stSidebar"] * {
    color: #c5c2b8 !important;
  }

  /* Headings */
  h1, h2, h3 { font-family: 'Syne', sans-serif !important; }

  /* Buttons */
  .stButton > button {
    background: #e8e6df !important;
    color: #0d0f14 !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 4px !important;
    padding: 0.5rem 1.4rem !important;
    letter-spacing: 0.04em !important;
    transition: opacity .2s !important;
  }
  .stButton > button:hover { opacity: 0.82 !important; }

  /* Text areas */
  .stTextArea textarea {
    background-color: #181b24 !important;
    color: #e8e6df !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 13.5px !important;
    border: 1px solid #2a2d38 !important;
    border-radius: 6px !important;
  }

  /* Select box / file input */
  .stSelectbox > div > div,
  .stTextInput > div > div > input {
    background-color: #181b24 !important;
    color: #e8e6df !important;
    border: 1px solid #2a2d38 !important;
    border-radius: 4px !important;
    font-family: 'Syne', sans-serif !important;
  }

  /* Rendered markdown pane */
  .readme-preview {
    background: #181b24;
    border: 1px solid #2a2d38;
    border-radius: 8px;
    padding: 2rem 2.4rem;
    min-height: 540px;
    font-size: 15px;
    line-height: 1.75;
  }
  .readme-preview h1 { font-size: 2rem; border-bottom: 2px solid #2a2d38; padding-bottom: .4rem; margin-bottom: 1rem; color: #f0ede6; }
  .readme-preview h2 { font-size: 1.45rem; border-bottom: 1px solid #2a2d38; padding-bottom: .3rem; margin-top: 1.6rem; color: #e8e4d9; }
  .readme-preview h3 { font-size: 1.15rem; color: #d4d0c5; }
  .readme-preview code { background: #0d0f14; padding: 2px 7px; border-radius: 4px; font-family: 'JetBrains Mono', monospace; font-size: 12.5px; color: #7fd1ae; }
  .readme-preview pre  { background: #0d0f14; padding: 1.1rem; border-radius: 6px; overflow-x: auto; border-left: 3px solid #4a6cf7; }
  .readme-preview pre code { background: transparent; padding: 0; color: #cdd6f4; font-size: 13px; }
  .readme-preview blockquote { border-left: 3px solid #4a6cf7; margin-left: 0; padding-left: 1rem; color: #8a8780; font-style: italic; }
  .readme-preview a { color: #7da9f7; }
  .readme-preview hr { border: none; border-top: 1px solid #2a2d38; }
  .readme-preview table { width: 100%; border-collapse: collapse; font-size: 14px; }
  .readme-preview th { background: #0d0f14; padding: 8px 12px; text-align: left; border: 1px solid #2a2d38; color: #e8e4d9; }
  .readme-preview td { padding: 8px 12px; border: 1px solid #2a2d38; color: #c5c2b8; }
  .readme-preview tr:nth-child(even) td { background: #14161f; }

  /* Tab strip */
  .stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    border-bottom: 1px solid #2a2d38 !important;
  }
  .stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #6b6960 !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    letter-spacing: .06em !important;
    border-radius: 4px 4px 0 0 !important;
    padding: .45rem 1.2rem !important;
    border: none !important;
  }
  .stTabs [aria-selected="true"] {
    background: #181b24 !important;
    color: #e8e6df !important;
    border-bottom: 2px solid #4a6cf7 !important;
  }

  /* Status badges */
  .badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 100px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: .05em;
    text-transform: uppercase;
  }
  .badge-saved   { background:#1a3a2a; color:#5fcb8a; }
  .badge-unsaved { background:#3a1a1a; color:#f07070; }

  /* File path label */
  .filepath-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    color: #5c5a54;
    margin-bottom: 6px;
  }

  /* Divider */
  hr.subtle { border: none; border-top: 1px solid #2a2d38; margin: 1.2rem 0; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ────────────────────────────────────────────────────────────────────

def find_readme_files(root: str = ".") -> list[str]:
    """Recursively find all README*.md files from root."""
    patterns = ["**/README.md", "**/README*.md", "**/readme.md"]
    found = set()
    for pat in patterns:
        for p in glob.glob(os.path.join(root, pat), recursive=True):
            found.add(os.path.normpath(p))
    return sorted(found)


def load_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"<!-- Error loading file: {e} -->"


def save_file(path: str, content: str) -> bool:
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception:
        return False


# ── Session state ──────────────────────────────────────────────────────────────
if "content" not in st.session_state:
    st.session_state.content = ""
if "saved_content" not in st.session_state:
    st.session_state.saved_content = ""
if "current_path" not in st.session_state:
    st.session_state.current_path = ""
if "search_root" not in st.session_state:
    st.session_state.search_root = "."


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📁 File Browser")
    st.markdown('<hr class="subtle">', unsafe_allow_html=True)

    root_input = st.text_input("Search root directory", value=st.session_state.search_root, placeholder="e.g. /home/user/projects")
    if root_input != st.session_state.search_root:
        st.session_state.search_root = root_input

    readme_files = find_readme_files(st.session_state.search_root)

    if readme_files:
        selected = st.selectbox(
            f"Found {len(readme_files)} file(s)",
            readme_files,
            index=readme_files.index(st.session_state.current_path) if st.session_state.current_path in readme_files else 0,
        )
        if st.button("Open →", use_container_width=True):
            st.session_state.current_path = selected
            st.session_state.content = load_file(selected)
            st.session_state.saved_content = st.session_state.content
            st.rerun()
    else:
        st.info("No README files found in that directory.")

    st.markdown('<hr class="subtle">', unsafe_allow_html=True)
    st.markdown("**Open by path**")
    manual_path = st.text_input("Full file path", placeholder="/path/to/README.md", label_visibility="collapsed")
    if st.button("Open file", use_container_width=True) and manual_path:
        if os.path.isfile(manual_path):
            st.session_state.current_path = manual_path
            st.session_state.content = load_file(manual_path)
            st.session_state.saved_content = st.session_state.content
            st.rerun()
        else:
            st.error("File not found.")

    st.markdown('<hr class="subtle">', unsafe_allow_html=True)
    st.markdown("**Create new README**")
    new_path = st.text_input("Save path", placeholder="/path/to/new_README.md", label_visibility="collapsed")
    if st.button("Create & Open", use_container_width=True) and new_path:
        if not new_path.endswith(".md"):
            new_path += ".md"
        default = f"# {os.path.basename(new_path).replace('.md','')}\n\nWrite your documentation here.\n"
        save_file(new_path, default)
        st.session_state.current_path = new_path
        st.session_state.content = default
        st.session_state.saved_content = default
        st.rerun()


# ── Main area ──────────────────────────────────────────────────────────────────
is_dirty = st.session_state.content != st.session_state.saved_content

# Header row
col_title, col_badge, col_save = st.columns([5, 1.2, 1.2])
with col_title:
    st.markdown("# README Editor")
with col_badge:
    if st.session_state.current_path:
        badge = '<span class="badge badge-unsaved">● Unsaved</span>' if is_dirty else '<span class="badge badge-saved">✓ Saved</span>'
        st.markdown(f"<div style='padding-top:1.6rem'>{badge}</div>", unsafe_allow_html=True)
with col_save:
    if st.session_state.current_path:
        if st.button("💾 Save", use_container_width=True):
            if save_file(st.session_state.current_path, st.session_state.content):
                st.session_state.saved_content = st.session_state.content
                st.success("Saved!")
                st.rerun()
            else:
                st.error("Save failed — check permissions.")

if st.session_state.current_path:
    st.markdown(f'<div class="filepath-label">📄 {st.session_state.current_path}</div>', unsafe_allow_html=True)

st.markdown('<hr class="subtle">', unsafe_allow_html=True)

# Tabs: Editor | Preview | Split
if not st.session_state.current_path:
    st.markdown("""
    <div style="text-align:center; padding: 5rem 0; color:#4a4840;">
        <div style="font-size:3rem; margin-bottom:1rem">📝</div>
        <div style="font-size:1.2rem; font-weight:700">No file open</div>
        <div style="font-size:.9rem; margin-top:.5rem">Select a file from the sidebar or enter a path to get started.</div>
    </div>
    """, unsafe_allow_html=True)
else:
    tab_editor, tab_preview, tab_split = st.tabs(["EDITOR", "PREVIEW", "SPLIT VIEW"])

    with tab_editor:
        new_content = st.text_area(
            "markdown_editor",
            value=st.session_state.content,
            height=600,
            label_visibility="collapsed",
            key="editor_textarea",
        )
        if new_content != st.session_state.content:
            st.session_state.content = new_content
            st.rerun()

    with tab_preview:
        st.markdown(f'<div class="readme-preview">', unsafe_allow_html=True)
        st.markdown(st.session_state.content)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab_split:
        left, right = st.columns(2)
        with left:
            st.markdown("**✏️ Editor**")
            new_content_split = st.text_area(
                "split_editor",
                value=st.session_state.content,
                height=540,
                label_visibility="collapsed",
                key="split_textarea",
            )
            if new_content_split != st.session_state.content:
                st.session_state.content = new_content_split
                st.rerun()
        with right:
            st.markdown("**👁 Preview**")
            st.markdown(f'<div class="readme-preview">', unsafe_allow_html=True)
            st.markdown(st.session_state.content)
            st.markdown('</div>', unsafe_allow_html=True)

    # Word/char stats footer
    words = len(st.session_state.content.split())
    chars = len(st.session_state.content)
    lines = st.session_state.content.count("\n") + 1
    st.markdown(
        f'<div style="color:#4a4840; font-size:12px; font-family:JetBrains Mono,monospace; margin-top:.8rem">'
        f'Lines: {lines} &nbsp;·&nbsp; Words: {words} &nbsp;·&nbsp; Characters: {chars}'
        f'</div>',
        unsafe_allow_html=True,
    )
