import threading
import yt_dlp
import queue

class DownloadManager:
    """yt-dlp の呼び出し、オプション構築、ダウンロード進捗管理を行うクラス"""
    
    def __init__(self, progress_callback=None, postprocessor_callback=None, error_callback=None):
        self.download_queue = queue.Queue()
        self.downloading = False
        self.progress_callback = progress_callback
        self.postprocessor_callback = postprocessor_callback
        self.error_callback = error_callback

    def build_options(self, save_path, filename_tmpl, browser, resolution, 
                      is_audio, embed_thumbnail, only_thumbnail, add_metadata, extension):
        """GUIの入力値から yt-dlp のオプション辞書を生成する。"""
        res_val = str(resolution) if resolution and resolution != "best" else None
        
        # 基本フォーマット設定
        if is_audio:
            fmt = "bestaudio/best"
        else:
            fmt = f"bestvideo[ext=mp4]{'[height<='+res_val+']' if res_val else ''}+bestaudio[ext=m4a]/best[ext=mp4]"

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
            
        if is_audio:
            opts["postprocessors"].append({
                "key": "FFmpegExtractAudio",
                "preferredcodec": extension,
                "preferredquality": "192"
            })
            
        return opts

    def add_to_queue(self, url, options):
        """ダウンロードをキューに追加し、スレッドが動いていなければ開始する。"""
        self.download_queue.put((url, options))
        
        if not self.downloading:
            thread = threading.Thread(target=self._download_loop, daemon=True)
            thread.start()

    def _download_loop(self):
        """キュー内の項目を順番にダウンロードするループ。"""
        self.downloading = True
        while not self.download_queue.empty():
            url, opt = self.download_queue.get()
            with yt_dlp.YoutubeDL(opt) as ydl:
                try:
                    ydl.download([url])
                except Exception as e:
                    if self.error_callback:
                        self.error_callback(e)
        self.downloading = False

    def _progress_hook(self, d):
        """yt-dlp からの進捗情報を受け取り、コールバックを呼ぶ。"""
        if self.progress_callback:
            self.progress_callback(d)

    def _postprocessor_hook(self, d):
        """yt-dlp の後処理完了時などに呼ばれる。"""
        if self.postprocessor_callback:
            self.postprocessor_callback(d)

    def get_queue_size(self):
        return self.download_queue.qsize()
