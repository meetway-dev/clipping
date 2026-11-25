import io
import re
import json
import zipfile
import xml.sax.saxutils
from typing import List, Dict, Any, Optional

def escape_xml(text: Any) -> str:
    """Escapes string for safe XML inclusion."""
    return xml.sax.saxutils.escape(str(text or ""))

def format_timestamp(seconds: float) -> str:
    """Formats seconds as MM:SS."""
    try:
        s = max(0.0, float(seconds))
        mins = int(s // 60)
        secs = int(s % 60)
        return f"{mins:02d}:{secs:02d}"
    except Exception:
        return "00:00"

def extract_clip_metadata(clip: Dict[str, Any], index: int = 1) -> Dict[str, Any]:
    """
    Extracts and normalizes metadata (topic, titles, hashtags, hook, caption, etc.)
    from a clip object in any state (DB row, pipeline output, or job result).
    """
    raw_topic = (
        clip.get("topic")
        or clip.get("topic_headline")
        or clip.get("title")
        or f"Clip {index}"
    )
    # Clean topic string
    topic = str(raw_topic).strip()

    title = clip.get("title") or topic
    filename = clip.get("filename") or f"clip_{index}.mp4"
    hook = clip.get("hook") or ""
    start_sec = float(clip.get("start_sec") or clip.get("start") or 0.0)
    end_sec = float(clip.get("end_sec") or clip.get("end") or (start_sec + float(clip.get("duration") or 30.0)))
    duration = float(clip.get("duration") or max(1.0, end_sec - start_sec))
    part_info = clip.get("part_info") or ""

    # Parse social kit if present
    raw_sk = clip.get("social_kit")
    social_kit: Dict[str, Any] = {}
    if isinstance(raw_sk, dict):
        social_kit = raw_sk
    elif isinstance(raw_sk, str) and raw_sk.strip():
        try:
            social_kit = json.loads(raw_sk)
        except Exception:
            social_kit = {}

    # Extract titles
    titles = social_kit.get("titles") or []
    if not titles:
        # Fallback titles if social kit was not generated
        clean_kw = re.sub(r"[^\w\s]", "", topic).strip().title()
        titles = [
            {"type": "Curiosity Hook", "text": f"Why Nobody Talks About {clean_kw} 🤯"},
            {"type": "Warning / Mistake", "text": f"Stop Making This Costly {clean_kw} Mistake ⚠️"},
            {"type": "Action / Rule", "text": f"The 1 Rule For {clean_kw} You Need To Know 🚀"}
        ]

    # Extract hashtags
    raw_tags = social_kit.get("hashtags") or social_kit.get("viral_hashtags")
    tags_list: List[str] = []
    if isinstance(raw_tags, list):
        tags_list = [str(t).strip() for t in raw_tags if str(t).strip()]
    elif isinstance(raw_tags, str) and raw_tags.strip():
        tags_list = [t.strip() for t in raw_tags.split() if t.strip()]

    if not tags_list:
        # Generate hashtags from topic keywords
        clean_words = [w for w in re.sub(r"[^\w\s]", "", topic).split() if len(w) > 2]
        topic_tag = "#" + "".join(w.title() for w in clean_words[:3]) if clean_words else "#Podcast"
        tags_list = [
            topic_tag,
            "#Shorts",
            "#Reels",
            "#TikTok",
            "#Viral",
            "#PodcastClips",
            "#GrowthMindset",
            "#Trending"
        ]

    hashtags_str = social_kit.get("hashtags_string") or " ".join(tags_list)
    transcript = clip.get("full_transcript") or clip.get("transcript") or ""
    caption = social_kit.get("full_caption") or (
        f"{title}\n\n"
        f"Key Takeaway: {hook or topic}\n\n"
        f"{hashtags_str}"
    )

    return {
        "index": index,
        "filename": filename,
        "topic": topic,
        "title": title,
        "part_info": part_info,
        "start_sec": start_sec,
        "end_sec": end_sec,
        "duration": duration,
        "hook": hook,
        "transcript": transcript,
        "titles": titles,
        "hashtags": tags_list,
        "hashtags_string": hashtags_str,
        "caption": caption
    }

def generate_session_docx(clips: List[Dict[str, Any]], session_title: str = "ClipForge Session") -> bytes:
    """
    Generates a valid OpenXML Microsoft Word (.docx) document containing
    every video's topic, title, CTR hooks, hashtags, and social captions.
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as docx:
        content_types = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
            '  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
            '  <Default Extension="xml" ContentType="application/xml"/>\n'
            '  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>\n'
            '</Types>'
        )
        rels = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
            '  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>\n'
            '</Relationships>'
        )
        docx.writestr('[Content_Types].xml', content_types.encode('utf-8'))
        docx.writestr('_rels/.rels', rels.encode('utf-8'))

        doc_parts = [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">',
            '<w:body>'
        ]

        # Document Header
        doc_parts.append(
            '<w:p><w:pPr><w:jc w:val="center"/><w:spacing w:before="120" w:after="160"/></w:pPr>'
            '<w:r><w:rPr><w:b/><w:sz w:val="44"/><w:color w:val="0D47A1"/></w:rPr>'
            f'<w:t>{escape_xml(session_title)}</w:t></w:r></w:p>'
        )
        doc_parts.append(
            '<w:p><w:pPr><w:jc w:val="center"/><w:spacing w:after="360"/></w:pPr>'
            '<w:r><w:rPr><w:sz w:val="22"/><w:color w:val="546E7A"/></w:rPr>'
            f'<w:t>ClipForge AI Studio • Session Video Clips &amp; Social Publishing Guide • {len(clips)} Total Clips</w:t></w:r></w:p>'
        )

        for i, raw_clip in enumerate(clips, 1):
            m = extract_clip_metadata(raw_clip, i)

            # Section Header (Box banner)
            doc_parts.append(
                '<w:p><w:pPr><w:spacing w:before="360" w:after="120"/><w:shd w:val="clear" w:color="auto" w:fill="E3F2FD"/></w:pPr>'
                f'<w:r><w:rPr><w:b/><w:sz w:val="28"/><w:color w:val="0D47A1"/></w:rPr>'
                f'<w:t>Clip {i}: {escape_xml(m["filename"])}</w:t></w:r></w:p>'
            )

            # Topic
            doc_parts.append(
                '<w:p><w:pPr><w:spacing w:after="80"/></w:pPr>'
                '<w:r><w:rPr><w:b/><w:sz w:val="22"/><w:color w:val="263238"/></w:rPr><w:t>📌 Topic: </w:t></w:r>'
                f'<w:r><w:rPr><w:b/><w:sz w:val="22"/><w:color w:val="C2185B"/></w:rPr><w:t>{escape_xml(m["topic"])}</w:t></w:r>'
                + (f'<w:r><w:rPr><w:b/><w:sz w:val="20"/><w:color w:val="00897B"/></w:rPr><w:t> [{escape_xml(m["part_info"])}]</w:t></w:r>' if m["part_info"] else '')
                + '</w:p>'
            )

            # Video Title
            doc_parts.append(
                '<w:p><w:pPr><w:spacing w:after="80"/></w:pPr>'
                '<w:r><w:rPr><w:b/><w:sz w:val="22"/><w:color w:val="263238"/></w:rPr><w:t>🎬 Video Title: </w:t></w:r>'
                f'<w:r><w:rPr><w:sz w:val="22"/><w:color w:val="212121"/></w:rPr><w:t>{escape_xml(m["title"])}</w:t></w:r></w:p>'
            )

            # Duration & Time
            t_str = f"{format_timestamp(m['start_sec'])} - {format_timestamp(m['end_sec'])} ({int(round(m['duration']))}s)"
            doc_parts.append(
                '<w:p><w:pPr><w:spacing w:after="100"/></w:pPr>'
                '<w:r><w:rPr><w:b/><w:sz w:val="20"/><w:color w:val="546E7A"/></w:rPr><w:t>⏱ Timestamp: </w:t></w:r>'
                f'<w:r><w:rPr><w:sz w:val="20"/><w:color w:val="546E7A"/></w:rPr><w:t>{escape_xml(t_str)}</w:t></w:r></w:p>'
            )

            # Title Hooks
            if m["titles"]:
                doc_parts.append(
                    '<w:p><w:pPr><w:spacing w:before="60" w:after="40"/></w:pPr>'
                    '<w:r><w:rPr><w:b/><w:sz w:val="20"/><w:color w:val="E65100"/></w:rPr><w:t>🔥 High-CTR Title Hooks:</w:t></w:r></w:p>'
                )
                for t in m["titles"]:
                    t_type = t.get("type", "Hook") if isinstance(t, dict) else "Hook"
                    t_text = t.get("text", str(t)) if isinstance(t, dict) else str(t)
                    doc_parts.append(
                        '<w:p><w:pPr><w:ind w:left="360"/><w:spacing w:after="40"/></w:pPr>'
                        f'<w:r><w:rPr><w:b/><w:sz w:val="18"/><w:color w:val="E65100"/></w:rPr><w:t>• [{escape_xml(t_type)}] </w:t></w:r>'
                        f'<w:r><w:rPr><w:sz w:val="18"/><w:color w:val="212121"/></w:rPr><w:t>{escape_xml(t_text)}</w:t></w:r></w:p>'
                    )

            # Hashtags
            doc_parts.append(
                '<w:p><w:pPr><w:spacing w:before="80" w:after="80"/></w:pPr>'
                '<w:r><w:rPr><w:b/><w:sz w:val="22"/><w:color w:val="2E7D32"/></w:rPr><w:t>🏷 Hashtags: </w:t></w:r>'
                f'<w:r><w:rPr><w:b/><w:sz w:val="20"/><w:color w:val="2E7D32"/></w:rPr><w:t>{escape_xml(m["hashtags_string"])}</w:t></w:r></w:p>'
            )

            # Hook Line
            if m["hook"]:
                doc_parts.append(
                    '<w:p><w:pPr><w:spacing w:after="80"/></w:pPr>'
                    '<w:r><w:rPr><w:b/><w:sz w:val="20"/><w:color w:val="455A64"/></w:rPr><w:t>💬 Spoken Hook: </w:t></w:r>'
                    f'<w:r><w:rPr><w:i/><w:sz w:val="20"/><w:color w:val="455A64"/></w:rPr><w:t>"{escape_xml(m["hook"])}"</w:t></w:r></w:p>'
                )

            # Full Social Caption
            if m["caption"]:
                doc_parts.append(
                    '<w:p><w:pPr><w:spacing w:before="60" w:after="40"/></w:pPr>'
                    '<w:r><w:rPr><w:b/><w:sz w:val="20"/><w:color w:val="37474F"/></w:rPr><w:t>📋 Ready-To-Post Social Caption:</w:t></w:r></w:p>'
                )
                for line in m["caption"].splitlines():
                    doc_parts.append(
                        '<w:p><w:pPr><w:ind w:left="360"/><w:spacing w:after="30"/></w:pPr>'
                        f'<w:r><w:rPr><w:sz w:val="18"/><w:color w:val="616161"/></w:rPr><w:t>{escape_xml(line)}</w:t></w:r></w:p>'
                    )

            # Card Divider
            doc_parts.append(
                '<w:p><w:pPr><w:spacing w:before="160" w:after="240"/>'
                '<w:pBdr><w:bottom w:val="single" w:sz="6" w:space="1" w:color="CFD8DC"/></w:pBdr></w:pPr></w:p>'
            )

        doc_parts.append('</w:body></w:document>')
        docx.writestr('word/document.xml', "".join(doc_parts).encode('utf-8'))

    return buf.getvalue()

def generate_session_text(clips: List[Dict[str, Any]], session_title: str = "ClipForge Session") -> str:
    """Generates a clean, plain text document with all metadata."""
    lines = [
        "=" * 70,
        f"  {session_title.upper()} - VIDEO CLIPS & SOCIAL METADATA",
        f"  Generated by ClipForge AI Studio • {len(clips)} Total Clips",
        "=" * 70,
        ""
    ]

    for i, raw_clip in enumerate(clips, 1):
        m = extract_clip_metadata(raw_clip, i)
        lines.append(f"[{i}] VIDEO FILE: {m['filename']}")
        lines.append(f"    Topic:     {m['topic']}" + (f" ({m['part_info']})" if m['part_info'] else ""))
        lines.append(f"    Title:     {m['title']}")
        lines.append(f"    Timestamp: {format_timestamp(m['start_sec'])} - {format_timestamp(m['end_sec'])} ({int(round(m['duration']))}s)")
        if m["hook"]:
            lines.append(f"    Hook:      \"{m['hook']}\"")
        if m.get("transcript"):
            lines.append(f"    Transcript: \"{m['transcript']}\"")
        lines.append(f"    Hashtags:  {m['hashtags_string']}")

        if m["titles"]:
            lines.append("    High-CTR Titles:")
            for t in m["titles"]:
                t_type = t.get("type", "Hook") if isinstance(t, dict) else "Hook"
                t_text = t.get("text", str(t)) if isinstance(t, dict) else str(t)
                lines.append(f"      • [{t_type}] {t_text}")

        if m["caption"]:
            lines.append("    Social Caption (Copy & Paste):")
            for c_line in m["caption"].splitlines():
                lines.append(f"      {c_line}")

        lines.append("-" * 70)
        lines.append("")

    return "\n".join(lines)

def generate_session_markdown(clips: List[Dict[str, Any]], session_title: str = "ClipForge Session") -> str:
    """Generates a GitHub-flavored Markdown document with all metadata."""
    lines = [
        f"# 🎬 {session_title} — Video Clips & Social Metadata",
        f"> **Generated by ClipForge AI Studio** • {len(clips)} Total Clips",
        "",
        "---",
        ""
    ]

    for i, raw_clip in enumerate(clips, 1):
        m = extract_clip_metadata(raw_clip, i)
        lines.append(f"## 🎥 Clip {i}: `{m['filename']}`")
        lines.append(f"- **📌 Topic:** `{m['topic']}`" + (f" *({m['part_info']})*" if m['part_info'] else ""))
        lines.append(f"- **🎬 Video Title:** **{m['title']}**")
        lines.append(f"- **⏱ Timing:** `{format_timestamp(m['start_sec'])}` – `{format_timestamp(m['end_sec'])}` ({int(round(m['duration']))}s)")
        if m["hook"]:
            lines.append(f"- **💬 Hook:** *\"{m['hook']}\"*")
        if m.get("transcript"):
            lines.append(f"- **📝 Transcript:** *\"{m['transcript']}\"*")
        lines.append(f"- **🏷 Hashtags:** `{m['hashtags_string']}`")
        lines.append("")

        if m["titles"]:
            lines.append("### 🔥 High-CTR Title Hooks:")
            for t in m["titles"]:
                t_type = t.get("type", "Hook") if isinstance(t, dict) else "Hook"
                t_text = t.get("text", str(t)) if isinstance(t, dict) else str(t)
                lines.append(f"- **[{t_type}]** {t_text}")
            lines.append("")

        if m["caption"]:
            lines.append("### 📋 Ready-To-Post Caption:")
            lines.append("```text")
            lines.append(m["caption"])
            lines.append("```")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)

def add_session_docs_to_zip(
    zf: zipfile.ZipFile,
    clips: List[Dict[str, Any]],
    session_title: str = "ClipForge Session"
) -> None:
    """
    Appends session docs files (.docx, .txt, and .md) into an existing open ZipFile.
    """
    if not clips:
        return

    # 1. Word Document (.docx)
    try:
        docx_bytes = generate_session_docx(clips, session_title)
        zf.writestr("session_clips_info.docx", docx_bytes)
    except Exception as e:
        print(f"[DocsGenerator] Failed to write docx: {e}")

    # 2. Plain Text Document (.txt)
    try:
        text_content = generate_session_text(clips, session_title)
        zf.writestr("session_clips_info.txt", text_content.encode("utf-8"))
    except Exception as e:
        print(f"[DocsGenerator] Failed to write txt: {e}")

    # 3. Markdown Document (.md)
    try:
        md_content = generate_session_markdown(clips, session_title)
        zf.writestr("session_clips_info.md", md_content.encode("utf-8"))
    except Exception as e:
        print(f"[DocsGenerator] Failed to write md: {e}")

def generate_clip_docx(clip: Dict[str, Any]) -> bytes:
    """Generates a dedicated Word (.docx) document for a single clip."""
    m = extract_clip_metadata(clip, 1)
    title = m.get("title") or m.get("topic") or "Podcast Clip"
    return generate_session_docx([clip], session_title=f"Clip: {title}")

def generate_clip_text(clip: Dict[str, Any]) -> str:
    """Generates a dedicated plain text (.txt) document for a single clip."""
    m = extract_clip_metadata(clip, 1)
    title = m.get("title") or m.get("topic") or "Podcast Clip"
    return generate_session_text([clip], session_title=f"Clip: {title}")

def generate_clip_markdown(clip: Dict[str, Any]) -> str:
    """Generates a dedicated Markdown (.md) document for a single clip."""
    m = extract_clip_metadata(clip, 1)
    title = m.get("title") or m.get("topic") or "Podcast Clip"
    return generate_session_markdown([clip], session_title=f"Clip: {title}")

def create_clip_docs_files(clip: Dict[str, Any], output_dir: Any, base_name: str) -> Dict[str, Any]:
    """
    Creates and saves .docx, .txt, and .md files specifically for this single clip
    inside its dedicated topic folder.
    """
    from pathlib import Path
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    paths = {}
    try:
        docx_path = out_dir / f"{base_name}_docs.docx"
        docx_bytes = generate_clip_docx(clip)
        docx_path.write_bytes(docx_bytes)
        paths["docx"] = str(docx_path)
    except Exception as e:
        print(f"[DocsGenerator Error] Single clip docx failed: {e}")

    try:
        txt_path = out_dir / f"{base_name}_docs.txt"
        txt_content = generate_clip_text(clip)
        txt_path.write_text(txt_content, encoding="utf-8")
        paths["txt"] = str(txt_path)
    except Exception as e:
        print(f"[DocsGenerator Error] Single clip txt failed: {e}")

    try:
        md_path = out_dir / f"{base_name}_docs.md"
        md_content = generate_clip_markdown(clip)
        md_path.write_text(md_content, encoding="utf-8")
        paths["md"] = str(md_path)
    except Exception as e:
        print(f"[DocsGenerator Error] Single clip md failed: {e}")

    return paths
