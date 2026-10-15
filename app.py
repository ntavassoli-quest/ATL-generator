"""
ATL Activity Generator - team web app.

Run locally:   streamlit run app.py
Host online:   see README.md (Streamlit Community Cloud is the easiest option).

Secrets (set as environment variables or in Streamlit's "Secrets" box):
    ANTHROPIC_API_KEY = "sk-ant-..."     # required
    APP_PASSWORD      = "choose-one"     # strongly recommended when hosted online
"""
import os
from pathlib import Path

import streamlit as st

from atl_generator import (DEFAULT_MODEL, extract_text, generate_content, render, split_for_decoding,
                           to_paragraphs, validate_content, word_count)

st.set_page_config(page_title="ATL Activity Generator", page_icon="\U0001F4D6", layout="centered")


def secret(name, default=""):
    """Read from Streamlit secrets first, then environment variables."""
    try:
        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass
    return os.environ.get(name, default)


# ---------------------------------------------------------------- password gate
APP_PASSWORD = secret("APP_PASSWORD")
if APP_PASSWORD and not st.session_state.get("authed"):
    st.title("\U0001F4D6 ATL Activity Generator")
    pw = st.text_input("Team password", type="password")
    if pw:
        if pw == APP_PASSWORD:
            st.session_state["authed"] = True
            st.rerun()
        else:
            st.error("Wrong password.")
    st.stop()

API_KEY = secret("ANTHROPIC_API_KEY")
if API_KEY:
    os.environ["ANTHROPIC_API_KEY"] = API_KEY

st.title("\U0001F4D6 ATL Activity Generator")
st.caption("Upload a class text (grades 9\u201312) and get a teacher ATL and a student ATL as Word or PDF files.")
if not API_KEY:
    st.error("No ANTHROPIC_API_KEY is set. Add it to the app's secrets or your environment, then reload.")
    st.stop()

# ---------------------------------------------------------------- 1. the text
st.subheader("1. The text")
up = st.file_uploader("Upload a PDF, Word, text or Markdown file", type=["pdf", "docx", "txt", "md"])
pasted = st.text_area("\u2026or paste the text (separate paragraphs with a blank line)", height=160)

text, read_error = "", None
if up is not None:
    try:
        text = extract_text(up.getvalue(), Path(up.name).suffix)
    except Exception as e:
        read_error = str(e)
if not text and pasted.strip():
    text = pasted
if read_error:
    st.error(read_error)

c1, c2, c3 = st.columns(3)
title = c1.text_input("Text title", value=Path(up.name).stem if up is not None else "")
grade = c2.selectbox("Grade", ["9", "10", "11", "12", "11/12"], index=1)
subject = c3.text_input("Course (optional)", placeholder="English, GloPo\u2026")

if text:
    n = word_count(text)
    st.info(f"{n} words, {len(to_paragraphs(text))} paragraphs found. Check the paragraph breaks below if you uploaded a PDF.")
    with st.expander("Preview the text"):
        st.text("\n\n".join(to_paragraphs(text))[:6000])
    decode_words = st.number_input(
        "Running-record words (0 = whole text)", min_value=0, max_value=1500, value=0 if n <= 800 else 500, step=50,
        help="The running record, vocabulary and questions use the first N words (cut at a paragraph break). "
             "The rest is read silently and supports the written responses.")

    if st.button("Generate ATL activity", type="primary", disabled=not title.strip()):
        pa, pb = split_for_decoding(to_paragraphs(text), int(decode_words))
        with st.spinner("Claude is writing the vocabulary and questions. This can take a minute\u2026"):
            try:
                content = generate_content(pa, pb, title.strip(), grade, subject.strip(), model=secret("ATL_MODEL", DEFAULT_MODEL))
            except Exception as e:
                st.error(f"Generation failed: {e}")
                st.stop()
        st.session_state.update(content=content, pa=pa, pb=pb, meta=(title.strip(), grade, subject.strip()),
                                gen=st.session_state.get("gen", 0) + 1)

# ---------------------------------------------------------------- 2. review and edit
if "content" in st.session_state:
    content, pa, pb = st.session_state["content"], st.session_state["pa"], st.session_state["pb"]
    t, g, s = st.session_state["meta"]
    gen = st.session_state["gen"]

    def edit(label, d, key, height=68, area=True):
        k = f"{gen}_{id(d)}_{key}"
        d[key] = (st.text_area(label, d.get(key, ""), key=k, height=height) if area
                  else st.text_input(label, d.get(key, ""), key=k))

    st.subheader("2. Review and edit")
    st.caption("AI-generated. Check every item against the text. Everything you edit here goes into the files.")
    for w in validate_content(content, "\n".join(pa)):
        st.warning(w)

    with st.expander("Vocabulary (5 scored words)", expanded=True):
        for i, v in enumerate(content["vocab"], 1):
            st.markdown(f"**Word {i}**")
            edit("Sentence from the text", v, "sentence")
            edit("Target word (must appear in the sentence)", v, "target", area=False)
            edit("Teacher target", v, "teacher_target", area=False)
    with st.expander("Reading comprehension", expanded=True):
        for i, q in enumerate(content["questions"], 1):
            st.markdown(f"**Question {i} \u00b7 {q.get('type', '')}**")
            edit("Question", q, "question")
            edit("Full-credit answer should include (teacher only)", q, "full_credit", 90)
            edit("Draw-a-distinction note (teacher only, optional)", q, "distinction", 90)
    with st.expander("Written responses", expanded=True):
        w = content["written"]
        edit("Summary prompt", w, "summary_prompt", area=False)
        edit("Thesis practice", w, "thesis_prompt")
        edit("Written comprehension", w, "comprehension_prompt", 90)
    with st.expander("Other"):
        pn = {"v": ", ".join(content.get("proper_nouns", []))}
        pw_ = {"v": ", ".join(content.get("preview_words", []))}
        edit("Proper nouns / technical terms to note separately (comma-separated)", pn, "v", area=False)
        edit("Unscored preview words (comma-separated)", pw_, "v", area=False)
        content["proper_nouns"] = [x.strip() for x in pn["v"].split(",") if x.strip()]
        content["preview_words"] = [x.strip() for x in pw_["v"].split(",") if x.strip()]
        edit("Estimated Lexile range (verify with a Lexile analyzer)", content, "lexile_estimate", area=False)
        edit("Short title (footer)", content, "short_title", area=False)

    # ---------------------------------------------------------------- 3. download
    st.subheader("3. Download")
    safe = "".join(ch for ch in (content.get("short_title") or t) if ch.isalnum() or ch in " -_").strip() or "ATL"
    mime = {"pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
    colT, colS = st.columns(2)
    for col, mode, label, blurb in (
        (colT, "teacher", "Teacher ATL", "Running-record copy, vocabulary targets, rubrics, full-credit answers, writing observations and score report."),
        (colS, "student", "Student ATL", "Student-facing pages with no answers or scoring. The teacher running-record copy is the last page, marked to remove before handing it out."),
    ):
        with col:
            st.markdown(f"**{label}**")
            st.caption(blurb)
            for fmt in ("pdf", "docx"):
                data = render(t, g, s, pa, pb, content, mode, fmt)
                st.download_button(f"Download {'PDF' if fmt == 'pdf' else 'Word'}", data,
                                   file_name=f"{safe} {label}.{fmt}", mime=mime[fmt], key=f"dl_{mode}_{fmt}_{gen}",
                                   use_container_width=True)
    st.caption("Use the PDF for printing; use Word when you want to edit the document itself. "
               "Only paste the class reading. Do not include student names or student work.")
