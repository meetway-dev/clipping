import os
import json
import time
import urllib.parse
from pathlib import Path
from typing import Dict, Any, Optional, List
import requests
from .config import BASE_DIR, OUTPUTS_DIR

CONFIG_FILE = BASE_DIR / "storage" / "gdrive_config.json"
TOKEN_FILE = BASE_DIR / "storage" / "gdrive_token.json"

OAUTH_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
USER_INFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
DRIVE_FILES_URL = "https://www.googleapis.com/drive/v3/files"
DRIVE_UPLOAD_URL = "https://www.googleapis.com/upload/drive/v3/files"

DEFAULT_SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile"
]

class GoogleDriveManager:
    """
    Production-ready Google Drive Cloud Integration Engine for ClipForge AI Studio.
    Enables 1-click cloud sync of generated 9:16 TikTok clips directly into Google Drive
    so creators can open Drive on their mobile phones and upload directly to TikTok / Reels / Shorts.
    """

    _instance: Optional["GoogleDriveManager"] = None

    def __init__(self):
        self.config: Dict[str, Any] = self._load_json(CONFIG_FILE, {
            "client_id": "",
            "client_secret": "",
            "redirect_uri": "http://localhost:8000/api/gdrive/callback",
            "folder_name": "ClipForge Clips"
        })
        self.token_data: Dict[str, Any] = self._load_json(TOKEN_FILE, {})
        self._auto_discover_credentials_file()

    def _auto_discover_credentials_file(self):
        """Auto-detects credentials.json or client_secret*.json in storage or workspace."""
        if self.config.get("client_id") and self.config.get("client_secret"):
            return

        candidates = [
            BASE_DIR / "storage" / "credentials.json",
            BASE_DIR / "credentials.json",
            BASE_DIR / "storage" / "client_secret.json",
            BASE_DIR / "client_secret.json"
        ]
        # Also check any client_secret_*.json
        for search_dir in [BASE_DIR / "storage", BASE_DIR]:
            if search_dir.exists():
                candidates.extend(list(search_dir.glob("client_secret*.json")))

        for cand in candidates:
            if cand.exists() and cand.is_file():
                try:
                    with open(cand, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    auth_info = data.get("installed") or data.get("web") or data
                    cid = auth_info.get("client_id")
                    sec = auth_info.get("client_secret")
                    if cid and sec:
                        self.config["client_id"] = cid.strip()
                        self.config["client_secret"] = sec.strip()
                        self._save_json(CONFIG_FILE, self.config)
                        print(f"[GoogleDrive] Auto-loaded credentials from: {cand.name}")
                        break
                except Exception:
                    pass

    @classmethod
    def get_instance(cls) -> "GoogleDriveManager":
        if cls._instance is None:
            cls._instance = GoogleDriveManager()
        return cls._instance

    def _load_json(self, path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return default

    def _save_json(self, path: Path, data: Dict[str, Any]):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def configure(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        folder_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Updates Google OAuth credentials and destination folder name."""
        if client_id is not None:
            self.config["client_id"] = client_id.strip()
        if client_secret is not None:
            self.config["client_secret"] = client_secret.strip()
        if redirect_uri is not None:
            self.config["redirect_uri"] = redirect_uri.strip()
        if folder_name is not None and folder_name.strip():
            self.config["folder_name"] = folder_name.strip()

        self._save_json(CONFIG_FILE, self.config)
        return self.get_status()

    def get_auth_url(self, redirect_uri: Optional[str] = None) -> str:
        """Constructs Google OAuth 2.0 authorization URL."""
        cid = self.config.get("client_id", "").strip()
        if not cid:
            raise ValueError("Google Client ID is not configured. Please enter your OAuth Client ID in Settings -> Google Drive.")

        r_uri = redirect_uri or self.config.get("redirect_uri", "http://localhost:8000/api/gdrive/callback")
        params = {
            "client_id": cid,
            "redirect_uri": r_uri,
            "response_type": "code",
            "scope": " ".join(DEFAULT_SCOPES),
            "access_type": "offline",
            "prompt": "consent"
        }
        return f"{OAUTH_AUTH_URL}?{urllib.parse.urlencode(params)}"

    def exchange_code(self, code: str, redirect_uri: Optional[str] = None) -> Dict[str, Any]:
        """Exchanges authorization code for access and refresh tokens."""
        cid = self.config.get("client_id", "").strip()
        sec = self.config.get("client_secret", "").strip()
        r_uri = redirect_uri or self.config.get("redirect_uri", "http://localhost:8000/api/gdrive/callback")

        if not cid or not sec:
            raise ValueError("Google Client ID or Client Secret missing.")

        resp = requests.post(
            OAUTH_TOKEN_URL,
            data={
                "client_id": cid,
                "client_secret": sec,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": r_uri
            },
            timeout=15
        )

        if resp.status_code != 200:
            err_msg = resp.text
            try:
                err_msg = resp.json().get("error_description", resp.text)
            except Exception:
                pass
            raise RuntimeError(f"Google Token Exchange Failed ({resp.status_code}): {err_msg}")

        data = resp.json()
        now = time.time()
        expires_in = data.get("expires_in", 3600)

        token_record = {
            "access_token": data.get("access_token"),
            "refresh_token": data.get("refresh_token") or self.token_data.get("refresh_token"),
            "token_type": data.get("token_type", "Bearer"),
            "expires_at": now + expires_in - 60
        }

        # Fetch user info
        try:
            u_resp = requests.get(
                USER_INFO_URL,
                headers={"Authorization": f"Bearer {token_record['access_token']}"},
                timeout=10
            )
            if u_resp.status_code == 200:
                u_info = u_resp.json()
                token_record["email"] = u_info.get("email", "")
                token_record["name"] = u_info.get("name", "")
                token_record["picture"] = u_info.get("picture", "")
        except Exception:
            pass

        self.token_data = token_record
        self._save_json(TOKEN_FILE, self.token_data)
        return self.get_status()

    def get_valid_access_token(self) -> str:
        """Returns active access token, automatically refreshing if expired."""
        if not self.token_data or not self.token_data.get("refresh_token"):
            raise RuntimeError("Google Drive is not connected. Please connect Google Drive first.")

        access_token = self.token_data.get("access_token")
        expires_at = self.token_data.get("expires_at", 0)

        if access_token and time.time() < expires_at:
            return access_token

        # Refresh token
        cid = self.config.get("client_id", "").strip()
        sec = self.config.get("client_secret", "").strip()
        rf_token = self.token_data.get("refresh_token")

        if not cid or not sec or not rf_token:
            raise RuntimeError("Missing refresh credentials. Please reconnect Google Drive.")

        resp = requests.post(
            OAUTH_TOKEN_URL,
            data={
                "client_id": cid,
                "client_secret": sec,
                "refresh_token": rf_token,
                "grant_type": "refresh_token"
            },
            timeout=15
        )

        if resp.status_code != 200:
            raise RuntimeError(f"Could not refresh Google access token: {resp.text}")

        data = resp.json()
        self.token_data["access_token"] = data.get("access_token")
        self.token_data["expires_at"] = time.time() + data.get("expires_in", 3600) - 60
        self._save_json(TOKEN_FILE, self.token_data)
        return self.token_data["access_token"]

    def is_connected(self) -> bool:
        return bool(self.token_data and self.token_data.get("refresh_token"))

    def disconnect(self):
        """Clears saved Google Drive connection tokens."""
        self.token_data = {}
        if TOKEN_FILE.exists():
            TOKEN_FILE.unlink(missing_ok=True)

    def get_status(self) -> Dict[str, Any]:
        """Returns connection telemetry and folder configuration."""
        connected = self.is_connected()
        has_client = bool(self.config.get("client_id") and self.config.get("client_secret"))
        return {
            "connected": connected,
            "has_credentials": has_client,
            "client_id": self.config.get("client_id", "")[:12] + "..." if self.config.get("client_id") else "",
            "folder_name": self.config.get("folder_name", "ClipForge Clips"),
            "email": self.token_data.get("email", ""),
            "name": self.token_data.get("name", ""),
            "picture": self.token_data.get("picture", "")
        }

    def get_or_create_folder(self, folder_name: Optional[str] = None) -> Dict[str, str]:
        """
        Finds or creates the designated destination folder in Google Drive.
        Returns dict with folder 'id' and 'webViewLink'.
        """
        access_token = self.get_valid_access_token()
        fname = folder_name or self.config.get("folder_name", "ClipForge Clips")
        headers = {"Authorization": f"Bearer {access_token}"}

        # Check existing folder
        q = f"mimeType='application/vnd.google-apps.folder' and name='{fname}' and trashed=false"
        resp = requests.get(
            f"{DRIVE_FILES_URL}?q={urllib.parse.quote(q)}&fields=files(id,name,webViewLink)",
            headers=headers,
            timeout=10
        )

        if resp.status_code == 200:
            files = resp.json().get("files", [])
            if files:
                return {
                    "id": files[0]["id"],
                    "name": files[0]["name"],
                    "webViewLink": files[0].get("webViewLink", f"https://drive.google.com/drive/folders/{files[0]['id']}")
                }

        # Create new folder
        create_resp = requests.post(
            f"{DRIVE_FILES_URL}?fields=id,name,webViewLink",
            headers={**headers, "Content-Type": "application/json"},
            json={
                "name": fname,
                "mimeType": "application/vnd.google-apps.folder"
            },
            timeout=12
        )

        if create_resp.status_code in [200, 201]:
            folder = create_resp.json()
            return {
                "id": folder["id"],
                "name": folder.get("name", fname),
                "webViewLink": folder.get("webViewLink", f"https://drive.google.com/drive/folders/{folder['id']}")
            }
        else:
            raise RuntimeError(f"Failed to create Google Drive folder '{fname}': {create_resp.text}")

    def upload_file(
        self,
        file_path: str,
        title: Optional[str] = None,
        folder_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Uploads a vertical MP4 clip to Google Drive in the dedicated folder.
        Uses multipart upload for fast single-turn transfer.
        """
        p = Path(file_path)
        if not p.exists() or not p.is_file():
            raise FileNotFoundError(f"Video file not found: {file_path}")

        access_token = self.get_valid_access_token()
        folder_info = self.get_or_create_folder(folder_name)
        folder_id = folder_info["id"]

        upload_title = title if title and title.strip() else p.name
        if not upload_title.lower().endswith(".mp4"):
            upload_title = f"{upload_title}.mp4"

        file_bytes = p.read_bytes()
        file_size = len(file_bytes)

        metadata = {
            "name": upload_title,
            "parents": [folder_id],
            "mimeType": "video/mp4",
            "description": "Exported by ClipForge AI Studio for mobile TikTok/Shorts/Reels publishing"
        }

        # Multipart upload boundary
        boundary = "===CLIPFORGE_DRIVE_UPLOAD_BOUNDARY==="
        body_parts = []
        body_parts.append(f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n".encode("utf-8"))
        body_parts.append(json.dumps(metadata).encode("utf-8"))
        body_parts.append(f"\r\n--{boundary}\r\nContent-Type: video/mp4\r\n\r\n".encode("utf-8"))
        body_parts.append(file_bytes)
        body_parts.append(f"\r\n--{boundary}--\r\n".encode("utf-8"))

        multipart_body = b"".join(body_parts)

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": f"multipart/related; boundary={boundary}",
            "Content-Length": str(len(multipart_body))
        }

        url = f"{DRIVE_UPLOAD_URL}?uploadType=multipart&fields=id,name,size,webViewLink,webContentLink"
        resp = requests.post(url, headers=headers, data=multipart_body, timeout=120)

        if resp.status_code not in [200, 201]:
            raise RuntimeError(f"Google Drive upload failed ({resp.status_code}): {resp.text}")

        res_data = resp.json()
        return {
            "status": "success",
            "file_id": res_data.get("id"),
            "title": res_data.get("name", upload_title),
            "size_bytes": file_size,
            "webViewLink": res_data.get("webViewLink", f"https://drive.google.com/file/d/{res_data.get('id')}/view"),
            "folder_name": folder_info["name"],
            "folder_link": folder_info["webViewLink"]
        }
