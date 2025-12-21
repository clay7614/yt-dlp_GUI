import os
import requests
from bs4 import BeautifulSoup
from packaging import version
from utils.logger import get_logger

logger = get_logger(__name__)

class UpdateManager:
    """GitHub API またはスクレイピングを使用してアップデート情報を取得するクラス"""
    
    RELEASES_URL = "https://github.com/okata-t/yt-dlp_GUI/releases"
    LATEST_API_URL = "https://api.github.com/repos/okata-t/yt-dlp_GUI/releases/latest"
    LOG_FILE = "log.txt"


    def get_latest_version(self) -> str:
        """最新バージョンをGitHubから取得する。"""
        try:
            r = requests.get(self.LATEST_API_URL, timeout=5)
            if r.status_code == 200:
                return str(r.json()["tag_name"])
            raise KeyError("API limit or other error")
        except Exception:
            # APIがダメな場合はスクレイピング
            try:
                response = requests.get(f"{self.RELEASES_URL}/latest", timeout=5)
                soup = BeautifulSoup(response.text, "html.parser")
                # セレクタは main.py の既存ロジックを参考
                tag = soup.find(class_="d-inline mr-3")
                if tag:
                    return str(tag.text[11:])
                return "v0.0.0"
            except Exception:
                return "v0.0.0"

    def fetch_release_notes(self, current_log_version: str) -> str:
        """変更履歴（リリースノート）を取得して log.txt に保存する。"""
        # 最新バージョンを取得
        latest_version = self.get_latest_version()
        
        # logファイルが存在しない、空、またはアプリ側の記録より新しいバージョンがある場合に取得
        if not os.path.exists(self.LOG_FILE) or os.path.getsize(self.LOG_FILE) == 0 or \
           version.parse(current_log_version) < version.parse(latest_version):
            
            try:
                # ページ数を取得
                response = requests.get(self.RELEASES_URL, timeout=5)
                soup = BeautifulSoup(response.text, "html.parser")
                page_num = 1
                pagination = soup.find_all(class_="pagination")
                for p in pagination:
                    # テキストから数字を抽出 (例: "Next 1 2 3 ... 5 Previous")
                    try:
                        page_num = int(p.text.strip()[-6:-5])
                    except:
                        page_num = 1
                    break

                log_entries = []
                for i in range(page_num):
                    url = f"{self.RELEASES_URL}?page={i + 1}"
                    response = requests.get(url, timeout=5)
                    soup = BeautifulSoup(response.text, "html.parser")
                    notes = soup.find_all(class_="Box-body")

                    for note in notes:
                        vers = note.find_all(class_="Link--primary Link")
                        changes = note.find_all(class_="markdown-body my-3")

                        for v in vers:
                            v_text = v.text.strip()
                            if v_text:
                                log_entries.append(v_text + "\n")
                        for ch in changes:
                            ch_text = ch.text.strip()
                            if ch_text:
                                log_entries.append(ch_text + "\n\n---\n")

                with open(self.LOG_FILE, "w", encoding="utf-8") as f:
                    f.write("".join(log_entries))
                
                return latest_version # 更新されたバージョンを返す
            except Exception as e:
                logger.error(f"Error fetching release notes: {e}")
        
        return current_log_version

