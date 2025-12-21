import sys
import os

# src ディレクトリをパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from core.config import ConfigManager
from utils.i18n import setup_i18n
from utils.logger import setup_logger

# ロガーのセットアップ
setup_logger()

from ui.main_window import App

if __name__ == "__main__":
    # 設定の初期化
    conf = ConfigManager()
    lang = conf.get("Option", "language", "jp")
    
    # 多言語対応のセットアップ
    _ = setup_i18n(lang)
    import builtins
    builtins._ = _ # グローバルに _ を登録
    
    # アプリケーションの実行
    app = App()
    
    app.protocol("WM_DELETE_WINDOW", lambda: app.write_config(False))
    app.mainloop()
