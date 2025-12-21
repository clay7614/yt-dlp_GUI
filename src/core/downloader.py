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
        self.opt = {}

    def add_to_queue(self, url, options):
        """ダウンロードをキューに追加し、スレッドが動いていなければ開始する。"""
        self.opt = options
        # フックをセット
        self.opt["progress_hooks"] = [self._progress_hook]
        self.opt["postprocessor_hooks"] = [self._postprocessor_hook]
        
        self.download_queue.put(url)
        
        if not self.downloading:
            thread = threading.Thread(target=self._download_loop, daemon=True)
            thread.start()

    def _download_loop(self):
        """キュー内の項目を順番にダウンロードするループ。"""
        self.downloading = True
        while not self.download_queue.empty():
            url = self.download_queue.get()
            with yt_dlp.YoutubeDL(self.opt) as ydl:
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
