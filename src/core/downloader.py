import threading
import queue
from typing import Optional, Dict, Any, Callable, List, Union
from utils.logger import get_logger

logger = get_logger(__name__)

class DownloadManager:
    """yt-dlp の呼び出し、オプション構築、ダウンロード進捗管理を行うクラス"""
    
    def __init__(self, progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
                 postprocessor_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
                 error_callback: Optional[Callable[[Exception], None]] = None) -> None:
        self.download_queue: queue.Queue = queue.Queue()
        self.downloading: bool = False
        self.progress_callback = progress_callback
        self.postprocessor_callback = postprocessor_callback
        self.error_callback = error_callback

    def build_options(self, save_path: str, filename_tmpl: str, browser: str, resolution: str, 
                      is_audio: bool, embed_thumbnail: bool, only_thumbnail: bool, 
                      add_metadata: bool, extension: str,
                      start_time: Optional[float] = None, end_time: Optional[float] = None) -> Dict[str, Any]:
        """GUIの入力値から yt-dlp のオプション辞書を生成する。"""
        res_val = str(resolution) if resolution and resolution != "best" else None
        
        # 基本フォーマット設定
        if is_audio:
            fmt = "bestaudio/best"
        elif extension == "webm":
            if not res_val:
                fmt = "bestvideo[ext=webm]/bestvideo+bestaudio/best[ext=mp4]"
            else:
                fmt = f"best[ext=webm]/bestvideo[height<={res_val}]+bestaudio/best[ext=mp4]"
        else:
            if not res_val:
                fmt = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo[ext=mp4]+bestaudio/best[ext=mp4]"
            else:
                fmt = f"bestvideo[ext=mp4][height<={res_val}]+bestaudio[ext=m4a]/bestvideo[ext=mp4][height<={res_val}]+bestaudio/best[ext=mp4]"

        opts = {
            "format": fmt,
            "outtmpl": f"{save_path}/{filename_tmpl or '%(title)s'}.%(ext)s",
            "ignoreerrors": "only_download",
            "progress_hooks": [self._progress_hook],
            "postprocessor_hooks": [self._postprocessor_hook],
            "postprocessors": []
        }
        
        if browser:
            opts["cookiesfrombrowser"] = (browser,)
            
        if embed_thumbnail:
            opts["writethumbnail"] = True
            opts["postprocessors"].append({"key": "EmbedThumbnail"})
            
        if only_thumbnail:
            opts["writethumbnail"] = True
            opts["skip_download"] = True
            
        if add_metadata:
            opts["postprocessors"].append({"key": "FFmpegMetadata", "add_metadata": True})
            
            opts["postprocessors"].append({
                "key": "FFmpegExtractAudio",
                "preferredcodec": extension,
            })
        
        if not is_audio and extension == "webm":
            opts["postprocessors"].append({
                "key": "FFmpegVideoConvertor",
                "preferedformat": "webm",
            })

        if start_time is not None and end_time is not None:
            opts["download_ranges"] = lambda *args: [{
                "start_time": start_time,
                "end_time": end_time,
            }]
            
        return opts

    def add_to_queue(self, url: str, options: Dict[str, Any]) -> None:
        """ダウンロードをキューに追加し、スレッドが動いていなければ開始する。"""
        self.download_queue.put((url, options))
        
        if not self.downloading:
            thread = threading.Thread(target=self._download_loop, daemon=True)
            thread.start()

    def _download_loop(self) -> None:
        """キュー内の項目を順番にダウンロードするループ。"""
        self.downloading = True
        while not self.download_queue.empty():
            url, opt = self.download_queue.get()
            with yt_dlp.YoutubeDL(opt) as ydl:
                try:
                    ydl.download([url])
                except Exception as e:
                    logger.error(f"Download error: {e}")
                    if self.error_callback:
                        self.error_callback(e)
        self.downloading = False

    def _progress_hook(self, d: Dict[str, Any]) -> None:
        """yt-dlp からの進捗情報を受け取り、コールバックを呼ぶ。"""
        if self.progress_callback:
            self.progress_callback(d)

    def _postprocessor_hook(self, d: Dict[str, Any]) -> None:
        """yt-dlp の後処理完了時などに呼ばれる。"""
        if self.postprocessor_callback:
            self.postprocessor_callback(d)

    def get_queue_size(self) -> int:
        return self.download_queue.qsize()
