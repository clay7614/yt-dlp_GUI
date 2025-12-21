import configparser
import os

class ConfigManager:
    """設定ファイルの管理（読み込み・書き込み・デフォルト値）を専門に行うクラス"""
    
    def __init__(self, ini_path="config.ini", version="v2.9.1"):
        self.ini_path = ini_path
        self.version = version
        self.config = configparser.ConfigParser(interpolation=None)
        
        self.default_config = [
            ("Directory", "lastdir", os.path.join(os.path.expanduser("~"), "Downloads")),
            ("Directory", "filename", ""),
            ("Option", "language", "jp"),
            ("Option", "appearance", "System"),
            ("Option", "download_audio", "0"),
            ("Option", "embed_thumbnail", "0"),
            ("Option", "only_thumbnail", "0"),
            ("Option", "add_metadata", "0"),
            ("Option", "extension", "mp4"),
            ("Option", "browser", ""),
            ("Option", "resolution", "best"),
            ("Option", "log_version", self.version),
            ("Option", "notification", "0"),
        ]
        self.load()

    def load(self):
        """INIファイルを読み込む。存在しない場合やキーが欠落している場合は補完する。"""
        if os.path.exists(self.ini_path):
            self.config.read(self.ini_path, encoding="utf-8")
        self.fix_config()

    def fix_config(self):
        """欠落しているセクションやキーを補完する。"""
        changed = False
        for section, key, value in self.default_config:
            if not self.config.has_section(section):
                self.config[section] = {}
                changed = True
            if not self.config.has_option(section, key):
                self.config[section][key] = value
                changed = True
        if changed:
            self.save()

    def save(self):
        """現在の設定をファイルに書き出す。"""
        with open(self.ini_path, "w", encoding="utf-8") as f:
            self.config.write(f)

    def get(self, section, key, fallback=None):
        """設定値を取得する（文字列で返る）。"""
        return self.config.get(section, key, fallback=fallback)

    def set(self, section, key, value):
        """設定値をセットする（まだ書き込みは行わない）。"""
        if not self.config.has_section(section):
            self.config[section] = {}
        self.config[section][key] = str(value)

    def get_boolean(self, section, key, fallback=False):
        """設定値を真偽値として取得する。"""
        val = self.get(section, key)
        if val is None:
            return fallback
        return val == "1"
