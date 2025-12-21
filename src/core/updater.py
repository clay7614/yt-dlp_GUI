import os
import requests
from bs4 import BeautifulSoup
from packaging import version

class UpdateManager:
    """GitHub API またはスクレイピングを使用してアップデート情報を取得するクラス"""
    
    RELEASES_URL = "https://github.com/okata-t/yt-dlp_GUI/releases"
    LATEST_API_URL = "https://api.github.com/repos/okata-t/yt-dlp_GUI/releases/latest"
    LOG_FILE = "log.txt"


    def get_latest_version(self):
        """最新バージョンをGitHubから取得する。"""
        try:
            r = requests.get(self.LATEST_API_URL, timeout=5)
            if r.status_code == 200:
                return r.json()["tag_name"]
            raise KeyError("API limit or other error")
        except Exception:
            # APIがダメな場合はスクレイピング
            try:
                response = requests.get(f"{self.RELEASES_URL}/latest", timeout=5)
                soup = BeautifulSoup(response.text, "html.parser")
                # セレクタは main.py の既存ロジックを参考
                return soup.find(class_="d-inline mr-3").text[11:]
            except Exception:
                return "v0.0.0"

    def fetch_release_notes(self, current_log_version):
        """変更履歴（リリースノート）を取得して log.txt に保存する。"""
        latest_version = self.get_latest_version()
        
        # ログが存在しないか、バージョンが古い場合に更新
        should_update = (
            not os.path.exists(self.LOG_FILE) or 
            os.stat(self.LOG_FILE).st_size == 0 or 
            version.parse(current_log_version) < version.parse(latest_version)
        )

        if not should_update:
            return latest_version

        # ページ数を取得
        try:
            response = requests.get(self.RELEASES_URL, timeout=5)
            soup = BeautifulSoup(response.text, "html.parser")
            page_tags = soup.find_all(class_="pagination")
            page_num = 1
            for pt in page_tags:
                page_num = int(pt.text[-6:-5])
                break

            log_entries = []
            for i in range(page_num):
                url = f"{self.RELEASES_URL}?page={i+1}"
                res = requests.get(url, timeout=5)
                s = BeautifulSoup(res.text, "html.parser")
                notes = s.find_all(class_="Box-body")

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
            
        except Exception as e:
            print(f"Error fetching release notes: {e}")

        return latest_version

