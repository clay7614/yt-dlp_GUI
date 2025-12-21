import datetime
import os
import sys
import threading
import tkinter as tk
import webbrowser
from tkinter import filedialog
from tkinterdnd2 import TkinterDnD, DND_FILES

import CTkMenuBar
import CTkMessagebox
import customtkinter as ctk
import darkdetect
import pyperclip
import requests
from PIL import Image
from pystray import Icon, Menu, MenuItem
from win11toast import toast

from core.config import ConfigManager
from core.updater import UpdateManager
from core.downloader import DownloadManager
from ui import color
from utils.helpers import convert_size, version_compare

VERSION = "v2.9.1"

class App(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)

        self.config_manager = ConfigManager(version=VERSION)
        self.update_manager = UpdateManager()
        self.download_manager = DownloadManager(
            progress_callback=self.progress_hook,
            postprocessor_callback=self.postprocessor_hook,
            error_callback=self.on_download_error
        )
        
        self.color_mode = darkdetect.theme()
        ctk.set_appearance_mode("System")
        try:
            ctk.set_default_color_theme("theme.json")
        except FileNotFoundError:
            ctk.set_default_color_theme("blue")
            
        self.fonts = ("游ゴシック", 15)
        self.title("yt-dlp_GUI " + VERSION)
        self.iconbitmap("icon.ico")

        self.create_menu()
        self.setup()
        self.setup_dnd()
        self.load_option()

        self.check_version(VERSION)
        self.check_option()
        self.select_appearance(self.appearance)
        self.set_submenu_color(self.languages, self.dict_language, self.language)
        self.set_submenu_color(self.appearances, self.dict_appearance, self.appearance)
        self.set_submenu_color(self.cookies, self.dict_browser, self.browser)

    def view_release_note(self):
        new_ver = self.update_manager.fetch_release_notes(self.this_log_version)
        self.this_log_version = new_ver
        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            self.toplevel_window = ViewRelease(self)
        else:
            self.toplevel_window.focus()

    def check_version(self, this_version):
        latest_version = self.update_manager.get_latest_version()
        if version_compare(this_version, latest_version) < 0:
            msg = CTkMessagebox.CTkMessagebox(
                title=_("アップデート"),
                message=_("新しいバージョン：") + latest_version + _("\nが公開されました。\nダウンロードしますか？"),
                icon="info",
                font=self.fonts,
                option_1=_("キャンセル"),
                option_2=_("ダウンロード"),
                option_3=_("GitHubへ")
            )
            if msg.get() == _("GitHubへ"):
                webbrowser.open("https://github.com/okata-t/yt-dlp_GUI/releases/latest")
                sys.exit()
            elif msg.get() == _("ダウンロード"):
                webbrowser.open("https://github.com/okata-t/yt-dlp_GUI/releases/latest/download/yt-dlp_GUI_Setup.exe")
                sys.exit()

    def uninstall(self):
        msg = CTkMessagebox.CTkMessagebox(
            title=_("アンインストール"),
            message=_("本当にアンインストールしますか？"),
            icon="info",
            font=self.fonts,
            option_1=_("キャンセル"),
            option_2=_("アンインストール")
        )
        if msg.get() == _("アンインストール"):
            if os.path.exists("config.ini"):
                os.remove("config.ini")
            subprocess.run("start unins000.exe", shell=True)
            sys.exit()

    def enable_notification(self):
        self.notification = str(int(self.notification) + 1)

    def create_menu(self):
        self.color_selected = "#808080"
        self.color_menubar = "#242424" if self.color_mode == "Dark" else "#EBEBEB"
        self.color_edit = "#EBEBEB" if self.color_mode == "Dark" else "#242424"
        
        self.menu = CTkMenuBar.CTkMenuBar(self, bg_color=self.color_menubar)
        self.pack_propagate(0)

        menu_option = self.menu.add_cascade(_("設定"), font=self.fonts)
        menu_view = self.menu.add_cascade(_("表示"), font=self.fonts)
        menu_link = self.menu.add_cascade(_("リンクを開く"), font=self.fonts)
        menu_beta = self.menu.add_cascade(_("ベータ"), font=self.fonts)
        menu_others = self.menu.add_cascade(_("その他"), font=self.fonts)

        dropdown_option = CTkMenuBar.CustomDropdownMenu(menu_option, font=self.fonts)
        dropdown_view = CTkMenuBar.CustomDropdownMenu(menu_view, font=self.fonts)
        dropdown_link = CTkMenuBar.CustomDropdownMenu(menu_link, font=self.fonts)
        dropdown_beta = CTkMenuBar.CustomDropdownMenu(menu_beta, font=self.fonts)
        dropdown_others = CTkMenuBar.CustomDropdownMenu(menu_others, font=self.fonts)

        # Cookies
        submenu_cookie = dropdown_option.add_submenu(_("Cookie設定"))
        self.cookies = []
        self.dict_browser = {_("なし"): "", "Brave": "brave", "Google Chrome": "chrome", 
                             "Microsoft Edge": "edge", "Mozilla FireFox": "firefox", 
                             "Opera": "opera", "Vivaldi": "vivaldi"}
        for name, key in self.dict_browser.items():
            self.cookies.append(submenu_cookie.add_option(name, command=lambda k=key: self.select_cookie(k)))

        # Language
        self.submenu_language = dropdown_view.add_submenu(_("言語"))
        self.languages = []
        self.dict_language = {"日本語": "jp", "English": "en", "한국어": "kr"}
        for name, key in self.dict_language.items():
            self.languages.append(self.submenu_language.add_option(name, command=lambda k=key: self.select_language(k)))

        # Appearance
        self.submenu_appearance = dropdown_view.add_submenu(_("外観"))
        self.appearances = []
        self.dict_appearance = {_("システム(メニューバーは再起動時反映)"): "System", _("ダーク"): "Dark", _("ライト"): "Light"}
        for name, key in self.dict_appearance.items():
            self.appearances.append(self.submenu_appearance.add_option(name, command=lambda k=key: self.select_appearance(k)))

        dropdown_view.add_option(_("テーマエディタを開く"), command=lambda: color.EditTheme(self, self.color_mode, "theme.json", self.fonts, self.language))
        
        dropdown_link.add_option("GitHub", command=lambda: webbrowser.open("https://github.com/okata-t/yt-dlp_GUI"))
        dropdown_link.add_option("YouTube", command=lambda: webbrowser.open("https://www.youtube.com"))
        dropdown_link.add_option("ニコニコ動画", command=lambda: webbrowser.open("https://www.nicovideo.jp"))
        dropdown_link.add_option("Twitch", command=lambda: webbrowser.open("https://www.twitch.tv"))

        dropdown_beta.add_option(_("クイックモード"), command=self.start_quick)
        
        dropdown_beta.add_option(_("クイックモード"), command=self.start_quick)
        
        
        dropdown_others.add_option(_("変更履歴"), command=self.view_release_note)
        dropdown_others.add_option(_("通知オン"), command=self.enable_notification)
        dropdown_others.add_option(_("アンインストール"), command=self.uninstall)

    def restart(self, app):
        app.write_config(False)
        # Entry point main.py should handle restart or we need a way to re-instantiate App
        # In a separated structure, we might need a controller or just re-run main.py
        python = sys.executable
        os.execl(python, python, *sys.argv)

    def write_config(self, isQuick):
        self.config_manager.set("Directory", "lastdir", self.ent_savedir.get())
        self.config_manager.set("Directory", "filename", self.ent_filename.get())
        self.config_manager.set("Option", "language", self.language)
        self.config_manager.set("Option", "appearance", self.appearance)
        self.config_manager.set("Option", "download_audio", "1" if self.chk_audio.get() else "0")
        self.config_manager.set("Option", "embed_thumbnail", "1" if self.chk_thumbnail.get() else "0")
        self.config_manager.set("Option", "only_thumbnail", "1" if self.chk_onlythumbnail.get() else "0")
        self.config_manager.set("Option", "add_metadata", "1" if self.chk_metadata.get() else "0")
        self.config_manager.set("Option", "extension", str(self.cmb_extension.get()))
        self.config_manager.set("Option", "browser", self.browser)
        
        res = str(self.cmb_resoluion.get())
        self.config_manager.set("Option", "resolution", "best" if res == _("最高画質") else res)
        self.config_manager.set("Option", "log_version", self.this_log_version)
        self.config_manager.set("Option", "notification", str(self.notification))
        self.config_manager.save()
        
        if isQuick: self.withdraw()
        else: self.destroy()

    def load_option(self):
        self.language = self.config_manager.get("Option", "language", "jp")
        self.appearance = self.config_manager.get("Option", "appearance", "System")
        self.var_chk_audio.set(self.config_manager.get_boolean("Option", "download_audio"))
        self.var_chk_thumbnail.set(self.config_manager.get_boolean("Option", "embed_thumbnail"))
        self.var_chk_onlythumbnail.set(self.config_manager.get_boolean("Option", "only_thumbnail"))
        self.var_chk_metadata.set(self.config_manager.get_boolean("Option", "add_metadata"))
        self.cmb_extension.set(self.config_manager.get("Option", "extension", "mp4"))
        self.browser = self.config_manager.get("Option", "browser", "")
        
        res = self.config_manager.get("Option", "resolution", "best")
        self.cmb_resoluion.set(_("最高画質") if res == "best" else res)
        self.this_log_version = self.config_manager.get("Option", "log_version", VERSION)
        self.notification = self.config_manager.get("Option", "notification", "0")

    def check_option(self, *args):
        is_audio = self.var_chk_audio.get()
        self.cmb_extension.configure(values=self.dict_file["audio" if is_audio else "movie"])
        self.cmb_resoluion.configure(state="disabled" if is_audio else "normal")
        
        ext = self.cmb_extension.get()
        if (is_audio and ext == "wav") or (not is_audio and ext == "webm") or self.var_chk_onlythumbnail.get():
            self.var_chk_thumbnail.set(False)
            self.chk_thumbnail.configure(state="disabled")
        else:
            self.chk_thumbnail.configure(state="normal")
            
        dur_state = "normal" if self.var_chk_duration.get() else "disabled"
        self.ent_duration_start.configure(state=dur_state)
        self.lbl_duration_hyphen.configure(state=dur_state)
        self.ent_duration_end.configure(state=dur_state)

    def change_extension(self, mode):
        self.cmb_extension.set(self.dict_file["audio" if self.var_chk_audio.get() else "movie"][0])

    def select_cookie(self, browser):
        self.browser = browser
        self.set_submenu_color(self.cookies, self.dict_browser, self.browser)

    def select_language(self, language):
        self.language = language
        from utils.i18n import setup_i18n
        import builtins
        builtins._ = setup_i18n(language)
        # re-setup _ will be done on restart
        self.restart(self)

    def select_appearance(self, appearance):
        self.appearance = appearance or "System"
        ctk.set_appearance_mode(self.appearance)
        is_dark = (self.appearance == "Dark") or (self.appearance == "System" and self.color_mode == "Dark")
        self.color_menubar = "#242424" if is_dark else "#EBEBEB"
        self.color_edit = "#EBEBEB" if is_dark else "#242424"
        self.menu.configure(bg_color=self.color_menubar)
        self.btn_editname.configure(text_color=self.color_edit)
        self.set_submenu_color(self.appearances, self.dict_appearance, self.appearance)

    def set_submenu_color(self, submenu, dict_map, option):
        target_list = [k for k, v in dict_map.items() if v == option]
        if not target_list: return
        target = target_list[0]
        for c in submenu:
            c.configure(fg_color=self.color_selected if c.cget("option") == target else "transparent")

    def setup(self):
        self.toplevel_window = None
        self.frame_main = ctk.CTkFrame(self)
        self.frame_main.grid(row=0, column=0, padx=10, pady=(35, 10), sticky="nsew")
        self.frame_info = ctk.CTkFrame(self)
        self.frame_info.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.frame_option = ctk.CTkFrame(self)
        self.frame_option.grid(row=0, column=1, rowspan=2, padx=10, pady=(35, 10), sticky="nsew")
        self.frame_progress = ctk.CTkFrame(self)
        self.frame_progress.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        
        self.rowconfigure(2, weight=1); self.columnconfigure(0, weight=1)
        self.frame_main.columnconfigure(1, weight=1); self.frame_progress.columnconfigure(0, weight=1)

        self.ent_url = ctk.CTkEntry(self.frame_main, width=520, placeholder_text="URL", font=self.fonts)
        self.ent_url.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        
        self.btn_paste = ctk.CTkButton(self.frame_main, width=100, text=_("ペースト"), command=self.paste, font=self.fonts)
        self.btn_paste.grid(row=0, column=2, padx=10, pady=10)

        self.ent_savedir = ctk.CTkEntry(self.frame_main, placeholder_text=_("保存先フォルダ"), font=self.fonts)
        self.ent_savedir.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        lastdir = self.config_manager.get("Directory", "lastdir", "")
        if lastdir: self.ent_savedir.insert(0, lastdir)

        self.btn_savedir = ctk.CTkButton(self.frame_main, width=100, text=_("参照"), command=self.savedir, font=self.fonts)
        self.btn_savedir.grid(row=1, column=2, padx=10, pady=10)

        self.btn_editname = ctk.CTkButton(self.frame_main, width=10, text=_("編集"), font=self.fonts, text_color=self.color_edit,
                                          fg_color="transparent", border_width=2.5, command=self.edit_filename)
        self.btn_editname.grid(row=2, column=0, padx=10, pady=10)

        self.ent_filename = ctk.CTkEntry(self.frame_main, placeholder_text=_("保存ファイル名(空白ならタイトル)"), font=self.fonts)
        self.ent_filename.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        filename = self.config_manager.get("Directory", "filename", "")
        if filename: self.ent_filename.insert(0, filename)

        self.btn_download = ctk.CTkButton(self.frame_main, width=100, text=_("ダウンロード"), command=self.start_download, font=self.fonts)
        self.btn_download.grid(row=2, column=2, padx=10, pady=10)

        self.btn_info = ctk.CTkButton(self.frame_info, width=100, text=_("動画情報の取得"), font=self.fonts, command=self.start_get_info)
        self.btn_info.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.lbl_info_title = ctk.CTkLabel(self.frame_info, font=self.fonts)
        self.lbl_info_img = ctk.CTkLabel(self.frame_info, text="")
        self.lbl_duration = ctk.CTkLabel(self.frame_info, font=self.fonts)
        self.var_chk_duration = ctk.BooleanVar()
        self.chk_duration = ctk.CTkCheckBox(self.frame_info, text=_("範囲指定でダウンロード"), font=self.fonts, 
                                            variable=self.var_chk_duration, command=self.check_option)
        self.ent_duration_start = ctk.CTkEntry(self.frame_info, font=self.fonts, width=60)
        self.lbl_duration_hyphen = ctk.CTkLabel(self.frame_info, text="-", font=self.fonts)
        self.ent_duration_end = ctk.CTkEntry(self.frame_info, font=self.fonts, width=60)

        self.lbl_progress = ctk.CTkLabel(self.frame_progress, text="\n", font=self.fonts)
        self.lbl_progress.grid(row=0, column=0, padx=10, sticky="w")
        self.lbl_eta = ctk.CTkLabel(self.frame_progress, text="\n", font=self.fonts)
        self.lbl_eta.grid(row=0, column=1, padx=10, sticky="e")
        self.pbar_progress = ctk.CTkProgressBar(self.frame_progress)
        self.pbar_progress.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        self.pbar_progress.set(0)

        self.var_chk_audio = ctk.BooleanVar(); self.chk_audio = ctk.CTkCheckBox(self.frame_option, text=_("音声のみダウンロード"), font=self.fonts, command=lambda: [self.check_option(), self.change_extension(self.var_chk_audio)], variable=self.var_chk_audio)
        self.chk_audio.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.var_chk_thumbnail = ctk.BooleanVar(); self.chk_thumbnail = ctk.CTkCheckBox(self.frame_option, text=_("サムネイルを埋め込む"), font=self.fonts, variable=self.var_chk_thumbnail)
        self.chk_thumbnail.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.var_chk_onlythumbnail = ctk.BooleanVar(); self.chk_onlythumbnail = ctk.CTkCheckBox(self.frame_option, text=_("サムネイルのみダウンロード"), font=self.fonts, variable=self.var_chk_onlythumbnail, command=self.check_option)
        self.chk_onlythumbnail.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        self.var_chk_metadata = ctk.BooleanVar(); self.chk_metadata = ctk.CTkCheckBox(self.frame_option, text=_("メタデータを埋め込む"), font=self.fonts, variable=self.var_chk_metadata)
        self.chk_metadata.grid(row=3, column=0, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(self.frame_option, text=_("拡張子を選択"), font=self.fonts).grid(row=5, column=0, padx=10, pady=(5, 0), sticky="ew")
        self.dict_file = {"movie": ["mp4", "webm"], "audio": ["mp3", "wav", "m4a", "opus"]}
        self.cmb_extension = ctk.CTkComboBox(self.frame_option, values=self.dict_file["movie"], font=self.fonts, command=self.check_option)
        self.cmb_extension.grid(row=6, column=0, padx=10, pady=(0, 5), sticky="ew")

        ctk.CTkLabel(self.frame_option, text=_("解像度を選択"), font=self.fonts).grid(row=7, column=0, padx=10, pady=(5, 0), sticky="ew")
        self.resolution_size = ["144", "240", "360", "480", "720", "1080", "1440", "2160", "4320", _("最高画質")]
        self.cmb_resoluion = ctk.CTkComboBox(self.frame_option, values=self.resolution_size, font=self.fonts, command=self.check_option)
        self.cmb_resoluion.grid(row=8, column=0, padx=10, pady=(0, 5), sticky="ew")

        self.var_clipboard_monitor = tk.BooleanVar(value=False)
        self.sw_clipboard = ctk.CTkSwitch(self.frame_option, text=_("クリップボード監視"), font=self.fonts, 
                                          variable=self.var_clipboard_monitor, command=self.toggle_clipboard_monitor)
        self.sw_clipboard.grid(row=4, column=0, padx=10, pady=(10, 5), sticky="ew")

    def paste(self):
        self.ent_url.delete(0, tk.END)
        self.ent_url.insert(0, pyperclip.paste())

    def savedir(self):
        path = filedialog.askdirectory(initialdir=self.config_manager.get("Directory", "lastdir", ""))
        if path:
            self.ent_savedir.delete(0, tk.END)
            self.ent_savedir.insert(0, path)

    def start_get_info(self):
        threading.Thread(target=self.get_info, daemon=True).start()

    def get_info(self):
        url = self.ent_url.get()
        opts = {"cookiesfrombrowser": (self.browser,)} if self.browser else {}
        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                self.info = {"title": info["title"], "duration": info["duration"], "thumbnail": info["thumbnail"], "height": info["height"]}
                
                valid_res = [r for r in self.resolution_size[:-1] if int(info["height"]) >= int(r)] + [_("最高画質")]
                self.cmb_resoluion.configure(values=valid_res)
                self.lbl_info_title.configure(text=info["title"])
                self.lbl_info_title.grid(row=0, column=1, columnspan=4, padx=10, pady=10, sticky="w")
                self.frame_info.columnconfigure(1, weight=1)

                img_data = requests.get(info["thumbnail"]).content
                self.lbl_info_img.configure(image=ctk.CTkImage(dark_image=Image.open(io.BytesIO(img_data)), size=(640, 360)))
                self.lbl_info_img.grid(row=1, column=0, columnspan=5, padx=10, pady=10, sticky="w")

                dur_str = str(datetime.timedelta(seconds=round(float(info["duration"]))))
                self.lbl_duration.configure(text=dur_str)
                self.lbl_duration.grid(row=2, column=0, padx=10, pady=10, sticky="w")
                self.chk_duration.grid(row=2, column=1, padx=10, pady=10)
                self.ent_duration_start.configure(placeholder_text="0:00:00")
                self.ent_duration_start.grid(row=2, column=2, padx=10, pady=10)
                self.lbl_duration_hyphen.grid(row=2, column=3, pady=10)
                self.ent_duration_end.configure(placeholder_text=dur_str)
                self.ent_duration_end.grid(row=2, column=4, padx=10, pady=10)
            except Exception as e:
                self.on_download_error(e)

    def start_download(self):
        url = self.ent_url.get()
        if not url:
            CTkMessagebox.CTkMessagebox(title=_("エラー"), message=_("URLを入力してください"), icon="cancel", font=self.fonts)
            return
            
        if "list=" in url:
            msg = CTkMessagebox.CTkMessagebox(title=_("確認"), message=_("URLに再生リストが含まれています。\n一括ダウンロードしますか？"),
                                              icon="question", option_1="一括ダウンロード", option_2="この動画のみ", font=self.fonts)
            if msg.get() == "この動画のみ":
                url = url.split("list=")[0][:-1]

        file_path = self.ent_savedir.get()
        if not file_path:
            CTkMessagebox.CTkMessagebox(title=_("エラー"), message=_("保存フォルダを指定してください"), icon="cancel", font=self.fonts)
            return

        res = self.cmb_resoluion.get()
        
        start_time = None
        end_time = None
        if self.var_chk_duration.get():
            try:
                st = datetime.datetime.strptime(self.ent_duration_start.get(), "%X")
                et = datetime.datetime.strptime(self.ent_duration_end.get(), "%X")
                start_time = datetime.timedelta(hours=st.hour, minutes=st.minute, seconds=st.second).total_seconds()
                end_time = datetime.timedelta(hours=et.hour, minutes=et.minute, seconds=et.second).total_seconds()
            except ValueError:
                pass

        opts = self.download_manager.build_options(
            save_path=file_path,
            filename_tmpl=self.ent_filename.get(),
            browser=self.browser,
            resolution="best" if res == _("最高画質") else res,
            is_audio=self.var_chk_audio.get(),
            embed_thumbnail=self.var_chk_thumbnail.get(),
            only_thumbnail=self.var_chk_onlythumbnail.get(),
            add_metadata=self.var_chk_metadata.get(),
            extension=self.cmb_extension.get(),
            start_time=start_time,
            end_time=end_time
        )

        self.download_finished_count = 1 if self.var_chk_audio.get() else 2
        self.download_manager.add_to_queue(url, opts)

    def on_download_error(self, e):
        CTkMessagebox.CTkMessagebox(title=_("エラーが発生しました"), message=str(e), icon="cancel", font=self.fonts)

    def progress_hook(self, d):
        self.filename = d.get("filename", "***")
        if d["status"] == "downloading":
            downloading_text = _("音声") if self.download_finished_count == 1 else _("動画")
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            downloaded = d.get("downloaded_bytes", 0)
            
            p = downloaded / total if total else 0
            speed = self.convert_size(d.get("speed", 0))
            eta = str(datetime.timedelta(seconds=round(float(d.get("eta", 0))))) if d.get("eta") else "..."
            
            self.lbl_progress.configure(text=f"{self.filename}\n{downloading_text}をダウンロード中：{round(p*100, 1)}% / {self.convert_size(total or downloaded)} ({speed}/s)")
            self.lbl_eta.configure(text=_("\n残り ") + eta)
            self.pbar_progress.set(p)
        elif d["status"] == "finished":
            self.download_finished_count -= 1

    def postprocessor_hook(self, d):
        if d["status"] == "started":
            self.lbl_progress.configure(text=self.filename + _("\n処理中"))
        elif d["status"] == "finished" and d["postprocessor"] == "MoveFiles":
            self.lbl_progress.configure(text=self.filename + _("\nダウンロード完了"))
            
            app_id = "yt-dlp_GUI"
            if self.notification != "0":
                app_id += "_" + self.notification
                
            toast("yt-dlp_GUI", 
                  _("ダウンロードが完了しました") + f"({_('残り：')}{self.download_manager.get_queue_size()})\n{d['info_dict']['title']}",
                  app_id=app_id)

    def convert_size(self, size):
        return convert_size(size)

    def edit_filename(self):
        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            self.toplevel_window = EditFilename(self)
        else:
            self.toplevel_window.focus()

    def start_quick(self):
        self.write_config(True)
        threading.Thread(target=lambda: QuickMode(self), daemon=True).start()

    def setup_dnd(self):
        self.drop_target_register(DND_FILES)
        self.dnd_bind("<<Drop>>", self.drop_url)
        
    def drop_url(self, event):
        url = event.data
        if url.startswith("{") and url.endswith("}"):
            url = url[1:-1]
            
        self.ent_url.delete(0, tk.END)
        self.ent_url.insert(0, url)
        
    def toggle_clipboard_monitor(self):
        if self.var_clipboard_monitor.get():
            self.last_clipboard = pyperclip.paste()
            self.monitor_clipboard()
            
    def monitor_clipboard(self):
        if not self.var_clipboard_monitor.get():
            return
            
        try:
            current_clipboard = pyperclip.paste()
            if current_clipboard != self.last_clipboard:
                self.last_clipboard = current_clipboard
                # YouTubeなどのURLか簡易チェック
                if "http" in current_clipboard and ("youtube.com" in current_clipboard or "youtu.be" in current_clipboard or "nicovideo.jp" in current_clipboard):
                     if current_clipboard != self.ent_url.get():
                        self.ent_url.delete(0, tk.END)
                        self.ent_url.insert(0, current_clipboard)
                        toast("yt-dlp_GUI", _("URLを検知しました"), duration="short")
                        
        except Exception:
            pass
            
        self.after(1000, self.monitor_clipboard)

class ReleaseFrame(ctk.CTkScrollableFrame):
    def __init__(self, master):
        super().__init__(master)
        text = ""
        if os.path.exists("log.txt"):
            with open("log.txt", encoding="utf-8") as f:
                text = f.read().replace("---", "")
        ctk.CTkLabel(self, text=text, font=("游ゴシック", 15), justify="left", anchor="w").grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

class ViewRelease(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.fonts = ("游ゴシック", 15)
        self.title(_("変更履歴")); self.geometry("640x480")
        self.after(100, self.focus)
        ReleaseFrame(self).grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.grid_columnconfigure(0, weight=1); self.grid_rowconfigure(0, weight=1)

class EditFilename(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.fonts = ("游ゴシック", 15)
        self.title(_("ファイル名テンプレートの編集"))
        self.after(100, self.focus)

        self.dict = {
            "ID": "id",
            _("タイトル"): "title",
            "URL": "url",
            _("投稿者"): "uploader",
            _("投稿者ID"): "uploader_id",
            _("投稿日"): "upload_date",
            _("動画サイズ縦"): "width",
            _("動画サイズ横"): "height",
            "FPS": "fps",
            _("サイトドメイン"): "extractor",
            _("プレイリスト名"): "playlist",
            _("プレイリスト内番号"): "playlist_index",
        }

        self.frame_entry = ctk.CTkFrame(self)
        self.frame_entry.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.frame_option = ctk.CTkFrame(self)
        self.frame_option.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.frame_entry.columnconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(self.frame_entry, font=self.fonts)
        self.entry.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.load_text()

        self.btn_apply = ctk.CTkButton(
            self.frame_entry,
            font=self.fonts,
            text=_("適用"),
            width=30,
            command=self.apply_text,
        )
        self.btn_apply.grid(row=0, column=1, padx=10, pady=10)

        self.btn = [[None for i in range(4)] for j in range(3)]

        # テンプレートボタンの作成
        self.make_btn(0, 0, "ID")
        self.make_btn(0, 1, _("タイトル"))
        self.make_btn(0, 2, _("投稿者"))
        self.make_btn(0, 3, _("投稿者ID"))
        self.make_btn(1, 0, _("投稿日"))
        self.make_btn(1, 1, _("動画サイズ縦"))
        self.make_btn(1, 2, _("動画サイズ横"))
        self.make_btn(1, 3, "FPS")
        self.make_btn(2, 0, _("サイトドメイン"))
        self.make_btn(2, 1, _("プレイリスト名"))
        self.make_btn(2, 2, _("プレイリスト内番号"))
        
        # クリアボタン
        btn_clear = ctk.CTkButton(
            self.frame_option,
            font=self.fonts,
            fg_color="transparent",
            command=lambda: self.entry.delete(0, ctk.END),
            text=_("クリア")
        )
        btn_clear.grid(row=2, column=3, padx=10, pady=10, sticky="nsew")

        for r in range(3):
            self.frame_option.rowconfigure(r, weight=1)
        for c in range(4):
            self.frame_option.columnconfigure(c, weight=1)

    def make_btn(self, r, c, text):
        btn = ctk.CTkButton(
            self.frame_option,
            font=self.fonts,
            fg_color="transparent",
            command=lambda: self.entry.insert(ctk.END, '"' + text + '"'),
            text=text,
        )
        btn.grid(row=r, column=c, padx=10, pady=10, sticky="nsew")
        return btn

    def apply_text(self):
        text = self.entry.get()
        for key, val in self.dict.items():
            text = text.replace('"' + key + '"', "%(" + val + ")s")
        self.master.ent_filename.delete(0, tk.END)
        self.master.ent_filename.insert(0, text)
        self.destroy()

    def load_text(self):
        text = self.master.ent_filename.get()
        for key, val in self.dict.items():
            text = text.replace("%(" + val + ")s", '"' + key + '"')
        self.entry.delete(0, tk.END)
        self.entry.insert(0, text)

class QuickMode:
    def __init__(self, app):
        self.app = app
        image = Image.open("icon.ico")
        menu = Menu(MenuItem(_("ダウンロード"), self.download, default=True),
                    MenuItem(_("クイックモードを終了する"), self.quit),
                    MenuItem(_("yt-dlp_GUIを終了する"), lambda: os._exit(-1)))
        self.icon = Icon("yt-dlp_GUI", icon=image, title="yt-dlp_GUI", menu=menu)
        self.icon.run()
    def quit(self):
        self.app.deiconify()
        self.icon.stop()
    def download(self):
        self.app.paste()
        self.app.start_download()
