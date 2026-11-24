import sqlite3
import json
import time
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

from .config import BASE_DIR, STORAGE_DIR, OUTPUTS_DIR

DB_PATH = STORAGE_DIR / "clipforge.db"

class HistoryManager:
    """
    Manages persistent project and clip history using SQLite.
    Organizes clips by source video/podcast episode so users can easily
    identify, search, and manage outputs across multiple videos.
    """

    @classmethod
    def _get_connection(cls) -> sqlite3.Connection:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def init_db(cls):
        """Initializes database tables if they do not exist."""
        with cls._get_connection() as conn:
            cursor = conn.cursor()
            # Projects Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                source_type TEXT NOT NULL,
                source_identifier TEXT,
                source_video TEXT DEFAULT '',
                thumbnail_url TEXT,
                duration REAL DEFAULT 0,
                created_at REAL NOT NULL
            )
            """)

            # Clips Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS clips (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                title TEXT NOT NULL,
                hook TEXT,
                virality_score INTEGER DEFAULT 90,
                hook_score INTEGER DEFAULT 90,
                story_score INTEGER DEFAULT 90,
                conclusion_score INTEGER DEFAULT 90,
                duration REAL DEFAULT 30.0,
                start_sec REAL DEFAULT 0.0,
                end_sec REAL DEFAULT 0.0,
                subtitle_style TEXT DEFAULT 'hormozi',
                layout_mode TEXT DEFAULT 'speaker_focus',
                social_kit TEXT DEFAULT '',
                full_transcript TEXT,
                part_info TEXT DEFAULT '',
                series_id TEXT DEFAULT '',
                created_at REAL NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
            """)

            # Safe column additions if existing DB
            for alter_sql in [
                "ALTER TABLE projects ADD COLUMN source_video TEXT DEFAULT ''",
                "ALTER TABLE projects ADD COLUMN timeline_json TEXT DEFAULT ''",
                "ALTER TABLE projects ADD COLUMN summary_json TEXT DEFAULT ''",
                "ALTER TABLE projects ADD COLUMN transcript_json TEXT DEFAULT ''",
                "ALTER TABLE clips ADD COLUMN part_info TEXT DEFAULT ''",
                "ALTER TABLE clips ADD COLUMN series_id TEXT DEFAULT ''",
                "ALTER TABLE clips ADD COLUMN start_sec REAL DEFAULT 0.0",
                "ALTER TABLE clips ADD COLUMN end_sec REAL DEFAULT 0.0",
                "ALTER TABLE clips ADD COLUMN layout_mode TEXT DEFAULT 'speaker_focus'",
                "ALTER TABLE clips ADD COLUMN social_kit TEXT DEFAULT ''",
                "ALTER TABLE clips ADD COLUMN words_json TEXT DEFAULT ''",
                "ALTER TABLE clips ADD COLUMN top_padding REAL DEFAULT 0.0",
                "ALTER TABLE clips ADD COLUMN bottom_padding REAL DEFAULT 0.0"
            ]:
                try:
                    cursor.execute(alter_sql)
                except Exception:
                    pass

            conn.commit()

    @classmethod
    def save_project_with_clips(
        cls,
        project_id: str,
        title: str,
        source_type: str,
        source_identifier: str,
        thumbnail_url: str,
        duration: float,
        clips: List[Dict[str, Any]],
        source_video: str = "",
        virality_timeline: Optional[List[Dict[str, Any]]] = None,
        podcast_summary: Optional[Dict[str, Any]] = None,
        transcript_segments: Optional[List[Dict[str, Any]]] = None
    ):
        """Saves a completed clipping project and its child clips."""
        cls.init_db()
        now = time.time()
        timeline_json = json.dumps(virality_timeline) if virality_timeline else ""
        summary_json = json.dumps(podcast_summary) if podcast_summary else ""
        transcript_json = json.dumps(transcript_segments) if transcript_segments else ""

        with cls._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO projects (
                id, title, source_type, source_identifier, source_video,
                thumbnail_url, duration, timeline_json, summary_json, transcript_json, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (project_id, title, source_type, source_identifier, source_video, thumbnail_url, duration, timeline_json, summary_json, transcript_json, now))

            # Insert clips
            for idx, c in enumerate(clips):
                clip_id = c.get("id") or f"{project_id}_clip_{idx + 1}"
                breakdown = c.get("narrative_breakdown") or {}
                raw_sk = c.get("social_kit")
                sk_json = json.dumps(raw_sk) if isinstance(raw_sk, dict) else (raw_sk or "")
                raw_words = c.get("words")
                words_json = json.dumps(raw_words) if isinstance(raw_words, list) else ""

                cursor.execute("""
                INSERT OR REPLACE INTO clips (
                    id, project_id, filename, title, hook, virality_score,
                    hook_score, story_score, conclusion_score, duration,
                    start_sec, end_sec, subtitle_style, layout_mode,
                    social_kit, full_transcript, part_info, series_id, words_json,
                    top_padding, bottom_padding, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    clip_id,
                    project_id,
                    c.get("filename", ""),
                    c.get("title", f"Viral Clip {idx + 1}"),
                    c.get("hook", ""),
                    int(c.get("virality_score", 90)),
                    int(breakdown.get("hook_score", 90)),
                    int(breakdown.get("story_score", 90)),
                    int(breakdown.get("conclusion_score", 90)),
                    float(c.get("duration", 30.0)),
                    float(c.get("start", c.get("start_sec", 0.0))),
                    float(c.get("end", c.get("end_sec", 0.0))),
                    c.get("subtitle_style", "hormozi"),
                    c.get("layout_mode", "speaker_focus"),
                    sk_json,
                    c.get("full_transcript", c.get("hook", "")),
                    c.get("part_info", ""),
                    c.get("series_id", ""),
                    words_json,
                    float(c.get("top_padding", 0.0)),
                    float(c.get("bottom_padding", 0.0)),
                    now
                ))
            conn.commit()


    @classmethod
    def get_all_projects(cls) -> List[Dict[str, Any]]:
        """Returns all projects with their associated clips, newest first."""
        cls.init_db()
        with cls._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects ORDER BY created_at DESC")
            project_rows = cursor.fetchall()

            result = []
            for p in project_rows:
                p_dict = dict(p)
                # Parse timeline_json if available
                raw_tl = p_dict.get("timeline_json")
                if raw_tl and isinstance(raw_tl, str):
                    try:
                        p_dict["virality_timeline"] = json.loads(raw_tl)
                    except Exception:
                        p_dict["virality_timeline"] = []
                else:
                    p_dict["virality_timeline"] = []

                # Parse summary_json if available
                raw_sm = p_dict.get("summary_json")
                if raw_sm and isinstance(raw_sm, str):
                    try:
                        p_dict["podcast_summary"] = json.loads(raw_sm)
                    except Exception:
                        p_dict["podcast_summary"] = None
                else:
                    p_dict["podcast_summary"] = None

                # Parse transcript_json if available
                raw_tr = p_dict.get("transcript_json")
                if raw_tr and isinstance(raw_tr, str):
                    try:
                        p_dict["transcript_segments"] = json.loads(raw_tr)
                    except Exception:
                        p_dict["transcript_segments"] = []
                else:
                    p_dict["transcript_segments"] = []

                # Fetch clips for this project
                cursor.execute("SELECT * FROM clips WHERE project_id = ? ORDER BY created_at ASC", (p["id"],))
                clip_rows = cursor.fetchall()
                clips_list = []
                for c in clip_rows:
                    c_dict = dict(c)
                    c_dict["narrative_breakdown"] = {
                        "hook_score": c_dict.get("hook_score", 90),
                        "story_score": c_dict.get("story_score", 90),
                        "conclusion_score": c_dict.get("conclusion_score", 90)
                    }
                    # Parse social_kit JSON if available
                    raw_sk = c_dict.get("social_kit")
                    if raw_sk and isinstance(raw_sk, str):
                        try:
                            c_dict["social_kit"] = json.loads(raw_sk)
                        except Exception:
                            pass

                    # Parse words_json if available
                    raw_w = c_dict.get("words_json")
                    if raw_w and isinstance(raw_w, str):
                        try:
                            c_dict["words"] = json.loads(raw_w)
                        except Exception:
                            c_dict["words"] = []
                    else:
                        c_dict["words"] = []

                    c_dict["top_padding"] = float(c_dict.get("top_padding") or 0.0)
                    c_dict["bottom_padding"] = float(c_dict.get("bottom_padding") or 0.0)

                    clips_list.append(c_dict)

                p_dict["clips"] = clips_list
                p_dict["clip_count"] = len(clips_list)
                result.append(p_dict)

            return result

    @classmethod
    def get_project_by_id(cls, project_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single project by ID with its associated clips and transcripts."""
        cls.init_db()
        with cls._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            p = cursor.fetchone()
            if not p:
                return None
            p_dict = dict(p)

            # Parse timeline_json if available
            raw_tl = p_dict.get("timeline_json")
            if raw_tl and isinstance(raw_tl, str):
                try:
                    p_dict["virality_timeline"] = json.loads(raw_tl)
                except Exception:
                    p_dict["virality_timeline"] = []
            else:
                p_dict["virality_timeline"] = []

            # Parse summary_json if available
            raw_sm = p_dict.get("summary_json")
            if raw_sm and isinstance(raw_sm, str):
                try:
                    p_dict["podcast_summary"] = json.loads(raw_sm)
                except Exception:
                    p_dict["podcast_summary"] = None
            else:
                p_dict["podcast_summary"] = None

            # Parse transcript_json if available
            raw_tr = p_dict.get("transcript_json")
            if raw_tr and isinstance(raw_tr, str):
                try:
                    p_dict["transcript_segments"] = json.loads(raw_tr)
                except Exception:
                    p_dict["transcript_segments"] = []
            else:
                p_dict["transcript_segments"] = []

            # Fetch clips for this project
            cursor.execute("SELECT * FROM clips WHERE project_id = ? ORDER BY created_at ASC", (project_id,))
            clip_rows = cursor.fetchall()
            clips_list = []
            for c in clip_rows:
                c_dict = dict(c)
                c_dict["narrative_breakdown"] = {
                    "hook_score": c_dict.get("hook_score", 90),
                    "story_score": c_dict.get("story_score", 90),
                    "conclusion_score": c_dict.get("conclusion_score", 90)
                }
                raw_sk = c_dict.get("social_kit")
                if raw_sk and isinstance(raw_sk, str):
                    try:
                        c_dict["social_kit"] = json.loads(raw_sk)
                    except Exception:
                        pass

                raw_w = c_dict.get("words_json")
                if raw_w and isinstance(raw_w, str):
                    try:
                        c_dict["words"] = json.loads(raw_w)
                    except Exception:
                        c_dict["words"] = []
                else:
                    c_dict["words"] = []

                clips_list.append(c_dict)

            p_dict["clips"] = clips_list
            p_dict["clip_count"] = len(clips_list)
            return p_dict

    @classmethod
    def get_clip_by_id(cls, clip_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single clip with its parent project information."""
        cls.init_db()
        with cls._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT c.*, p.title as project_title, p.source_video, p.source_type, p.source_identifier
            FROM clips c
            LEFT JOIN projects p ON c.project_id = p.id
            WHERE c.id = ?
            """, (clip_id,))
            row = cursor.fetchone()
            if not row:
                return None
            c_dict = dict(row)
            c_dict["narrative_breakdown"] = {
                "hook_score": c_dict.get("hook_score", 90),
                "story_score": c_dict.get("story_score", 90),
                "conclusion_score": c_dict.get("conclusion_score", 90)
            }
            raw_sk = c_dict.get("social_kit")
            if raw_sk and isinstance(raw_sk, str):
                try:
                    c_dict["social_kit"] = json.loads(raw_sk)
                except Exception:
                    pass
            raw_w = c_dict.get("words_json")
            if raw_w and isinstance(raw_w, str):
                try:
                    c_dict["words"] = json.loads(raw_w)
                except Exception:
                    c_dict["words"] = []
            else:
                c_dict["words"] = []
            c_dict["top_padding"] = float(c_dict.get("top_padding") or 0.0)
            c_dict["bottom_padding"] = float(c_dict.get("bottom_padding") or 0.0)
            return c_dict

    @classmethod
    def get_clip_by_filename(cls, filename: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single clip by its output filename."""
        cls.init_db()
        with cls._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT c.*, p.title as project_title, p.source_video, p.source_type, p.source_identifier
            FROM clips c
            LEFT JOIN projects p ON c.project_id = p.id
            WHERE c.filename = ?
            ORDER BY c.created_at DESC LIMIT 1
            """, (filename,))
            row = cursor.fetchone()
            if not row:
                return None
            c_dict = dict(row)
            c_dict["narrative_breakdown"] = {
                "hook_score": c_dict.get("hook_score", 90),
                "story_score": c_dict.get("story_score", 90),
                "conclusion_score": c_dict.get("conclusion_score", 90)
            }
            raw_sk = c_dict.get("social_kit")
            if raw_sk and isinstance(raw_sk, str):
                try:
                    c_dict["social_kit"] = json.loads(raw_sk)
                except Exception:
                    pass
            return c_dict

    @classmethod
    def update_clip(cls, clip_id: str, updates: Dict[str, Any]) -> bool:
        """Updates specific fields of a clip."""
        cls.init_db()
        allowed = [
            "filename", "title", "hook", "virality_score", "duration",
            "start_sec", "end_sec", "subtitle_style", "layout_mode",
            "social_kit", "full_transcript", "part_info", "words_json",
            "top_padding", "bottom_padding"
        ]
        set_clauses = []
        values = []
        for k, v in updates.items():
            if k in allowed:
                set_clauses.append(f"{k} = ?")
                if k == "social_kit" and isinstance(v, dict):
                    values.append(json.dumps(v))
                else:
                    values.append(v)

        if not set_clauses:
            return False

        values.append(clip_id)
        sql = f"UPDATE clips SET {', '.join(set_clauses)} WHERE id = ?"
        with cls._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, tuple(values))
            conn.commit()
            return True


    @classmethod
    def add_single_clip(cls, clip_data: Dict[str, Any]) -> bool:
        """Saves a single new or custom clip to the database."""
        cls.init_db()
        now = time.time()
        raw_sk = clip_data.get("social_kit")
        sk_json = json.dumps(raw_sk) if isinstance(raw_sk, dict) else (raw_sk or "")
        raw_words = clip_data.get("words")
        words_json = json.dumps(raw_words) if isinstance(raw_words, list) else ""
        breakdown = clip_data.get("narrative_breakdown") or {}

        with cls._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO clips (
                id, project_id, filename, title, hook, virality_score,
                hook_score, story_score, conclusion_score, duration,
                start_sec, end_sec, subtitle_style, layout_mode,
                social_kit, full_transcript, part_info, series_id, words_json,
                top_padding, bottom_padding, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                clip_data.get("id"),
                clip_data.get("project_id"),
                clip_data.get("filename", ""),
                clip_data.get("title", "Custom Clip"),
                clip_data.get("hook", ""),
                int(clip_data.get("virality_score", 90)),
                int(breakdown.get("hook_score", 90)),
                int(breakdown.get("story_score", 90)),
                int(breakdown.get("conclusion_score", 90)),
                float(clip_data.get("duration", 30.0)),
                float(clip_data.get("start", clip_data.get("start_sec", 0.0))),
                float(clip_data.get("end", clip_data.get("end_sec", 0.0))),
                clip_data.get("subtitle_style", "hormozi"),
                clip_data.get("layout_mode", "speaker_focus"),
                sk_json,
                clip_data.get("full_transcript", ""),
                clip_data.get("part_info", ""),
                clip_data.get("series_id", ""),
                words_json,
                float(clip_data.get("top_padding", 0.0)),
                float(clip_data.get("bottom_padding", 0.0)),
                now
            ))
            conn.commit()
            return True

    @classmethod
    def delete_project(cls, project_id: str) -> bool:
        """Deletes a project, its database records, and generated MP4/JPG files."""
        cls.init_db()
        with cls._get_connection() as conn:
            cursor = conn.cursor()
            # Fetch clip filenames to remove video files & thumbnails
            cursor.execute("SELECT filename FROM clips WHERE project_id = ?", (project_id,))
            rows = cursor.fetchall()
            for r in rows:
                fn = r["filename"]
                if fn:
                    for ext in [".mp4", ".jpg"]:
                        file_p = OUTPUTS_DIR / Path(fn).with_suffix(ext).name
                        if file_p.exists():
                            try:
                                file_p.unlink()
                            except Exception:
                                pass

            cursor.execute("DELETE FROM clips WHERE project_id = ?", (project_id,))
            cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            conn.commit()
            return True

    @classmethod
    def delete_single_clip(cls, clip_id: str) -> bool:
        """Deletes a single clip from database and disk (video + thumbnail)."""
        cls.init_db()
        with cls._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT filename FROM clips WHERE id = ?", (clip_id,))
            row = cursor.fetchone()
            if row and row["filename"]:
                fn = row["filename"]
                for ext in [".mp4", ".jpg"]:
                    file_p = OUTPUTS_DIR / Path(fn).with_suffix(ext).name
                    if file_p.exists():
                        try:
                            file_p.unlink()
                        except Exception:
                            pass
            cursor.execute("DELETE FROM clips WHERE id = ?", (clip_id,))
            conn.commit()
            return True

    # Alias for backwards compatibility with all call sites
    delete_clip = delete_single_clip
