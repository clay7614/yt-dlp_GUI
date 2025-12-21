import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name="yt-dlp_GUI", log_dir="log", log_file="app.log", level=logging.INFO):
    """
    アプリケーション全体のロガーを設定する関数。
    コンソール出力と、サイズによるローテーション付きファイル出力を設定します。
    """
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 既にハンドラが設定されている場合は重複を防ぐため何もしない
    if logger.handlers:
        return logger

    # フォーマッタの作成
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # コンソールハンドラ (標準出力)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # ファイルハンドラ (ローテーション: 1MB x 5世代)
    file_path = os.path.join(log_dir, log_file)
    file_handler = RotatingFileHandler(
        file_path, maxBytes=1*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

def get_logger(name="yt-dlp_GUI"):
    """
    設定済みのロガーを取得するためのラッパー関数。
    """
    return logging.getLogger(name)
