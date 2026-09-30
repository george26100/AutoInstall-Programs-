import subprocess
import os
import threading
import tkinter as tk
import sys
from tkinter import ttk, filedialog, messagebox




# ============ ЦВЕТОВАЯ СХЕМА ============
COLORS = {
    "bg":          "#1e1f2b",   # основной фон
    "bg_light":    "#282a3a",   # панели
    "bg_card":     "#2f3147",   # карточки / поля ввода
    "fg":          "#e6e8f0",   # основной текст
    "fg_dim":      "#9aa0b5",   # приглушённый текст
    "accent":      "#6c8cff",   # акцент (синий)
    "accent_hover":"#8aa3ff",
    "success":     "#4ade80",   # зелёный
    "error":       "#f87171",   # красный
    "warning":     "#fbbf24",   # жёлтый
    "border":      "#3a3d54",   # границы
    "select":      "#3b4a7a",   # выделение строки
}

def get_base_dir():
    """Возвращает папку, где лежит .exe (или .py в режиме разработки)."""
    if getattr(sys, 'frozen', False):
        # Запущено из .exe, собранного PyInstaller
        return os.path.dirname(sys.executable)
    else:
        # Запущено как обычный .py
        return os.path.dirname(os.path.abspath(__file__))



def install_from_file(file_path, install_args, log_func):
    """Устанавливает EXE-файл в тихом режиме."""
    if not os.path.isfile(file_path):
        log_func(f"❌ Файл не найден: {file_path}\n", "error")
        return False

    log_func(f"▶ Установка {os.path.basename(file_path)}...\n", "info")
    try:
        subprocess.run([file_path] + install_args, check=True, shell=False)
        log_func(f"✅ Успешно: {os.path.basename(file_path)}\n", "success")
        return True
    except subprocess.CalledProcessError as e:
        log_func(f"❌ Ошибка установки {os.path.basename(file_path)}: код {e.returncode}\n", "error")
        return False
    except PermissionError:
        log_func(f"⛔ Нет прав для запуска {file_path}. Запустите от имени администратора.\n", "error")
        return False


class InstallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Автоустановка приложений")
        self.root.geometry("900x680")
        self.root.minsize(1000, 800)
        self.root.configure(bg=COLORS["bg"])

        BASE_DIR = get_base_dir()

        def p(*parts):
            """Удобный хелпер: p('dist', '7z.exe') → полный путь."""
            return os.path.join(BASE_DIR, *parts)

        self.installers = [
            #{"path": p( "7z.exe"), "args": ["/S"]},
            #{"path": p( "DWG.exe"), "args": ["/S"]},
            #{"path": p( "DWF.exe"), "args": ["/S"]},
            #{"path": p( "AnyDesk.exe"), "args": ["/S"]},
            #{"path": p( "Chrome.exe"), "args": ["/S"]},
            #{"path": p( "PDF24.exe"), "args": ["/S"]},
            #{"path": p( "Assistent-6.3.exe"), "args": ["/S"]},
            #{"path": p( "CPUZ.exe"), "args": ["/S"]},
            #{"path": p( "OFFICE-2019", "Office", "setup64.exe"), "args": ["/S"]},
        ]

        # Drag & drop
        self._drag_item = None
        self._drag_start_y = 0
        self._dragging = False

        self._setup_styles()
        self._build_ui()
        self._refresh_list()

    # ---------- Стили ----------
    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Фон
        style.configure(".", background=COLORS["bg"], foreground=COLORS["fg"],
                        fieldbackground=COLORS["bg_card"], borderwidth=0)
        style.configure("TFrame", background=COLORS["bg"])
        style.configure("Card.TFrame", background=COLORS["bg_light"])

        # Заголовки
        style.configure("Title.TLabel",
                        background=COLORS["bg"], foreground=COLORS["fg"],
                        font=("Segoe UI Semibold", 15))
        style.configure("Subtitle.TLabel",
                        background=COLORS["bg"], foreground=COLORS["fg_dim"],
                        font=("Segoe UI", 9))
        style.configure("Card.TLabel",
                        background=COLORS["bg_light"], foreground=COLORS["fg"],
                        font=("Segoe UI", 10))
        style.configure("CardDim.TLabel",
                        background=COLORS["bg_light"], foreground=COLORS["fg_dim"],
                        font=("Segoe UI", 9))
        style.configure("Status.TLabel",
                        background=COLORS["bg_light"], foreground=COLORS["fg_dim"],
                        font=("Segoe UI", 9))

        # Кнопки
        style.configure("TButton",
                        background=COLORS["bg_card"], foreground=COLORS["fg"],
                        borderwidth=0, focuscolor=COLORS["bg_card"],
                        padding=(14, 8), font=("Segoe UI", 10))
        style.map("TButton",
                  background=[("active", COLORS["border"]), ("pressed", COLORS["border"])])

        style.configure("Accent.TButton",
                        background=COLORS["accent"], foreground="#ffffff",
                        borderwidth=0, focuscolor=COLORS["accent"],
                        padding=(18, 10), font=("Segoe UI Semibold", 11))
        style.map("Accent.TButton",
                  background=[("active", COLORS["accent_hover"]), ("pressed", COLORS["accent"])],
                  foreground=[("disabled", "#8890a8")])

        style.configure("Danger.TButton",
                        background=COLORS["bg_card"], foreground=COLORS["error"],
                        borderwidth=0, padding=(14, 8), font=("Segoe UI", 10))
        style.map("Danger.TButton",
                  background=[("active", COLORS["border"])])

        # Список (Treeview)
        style.configure("Treeview",
                        background=COLORS["bg_card"], foreground=COLORS["fg"],
                        fieldbackground=COLORS["bg_card"], borderwidth=0,
                        rowheight=30, font=("Segoe UI", 10))
        style.configure("Treeview.Heading",
                        background=COLORS["bg_light"], foreground=COLORS["fg_dim"],
                        borderwidth=0, font=("Segoe UI Semibold", 10), padding=(8, 8))
        style.map("Treeview.Heading",
                  background=[("active", COLORS["border"])])
        style.map("Treeview",
                  background=[("selected", COLORS["select"])],
                  foreground=[("selected", "#ffffff")])

        # Прогресс-бар
        style.configure("TProgressbar",
                        background=COLORS["accent"], troughcolor=COLORS["bg_card"],
                        borderwidth=0, thickness=10)
        style.configure("Horizontal.TProgressbar",
                        background=COLORS["accent"], troughcolor=COLORS["bg_card"],
                        borderwidth=0, thickness=10)

        # Scrollbar
        style.configure("Vertical.TScrollbar",
                        background=COLORS["bg_light"], troughcolor=COLORS["bg"],
                        bordercolor=COLORS["bg"], arrowcolor=COLORS["fg_dim"],
                        borderwidth=0)
        style.map("Vertical.TScrollbar",
                  background=[("active", COLORS["border"])])

    # ---------- Построение интерфейса ----------
    def _build_ui(self):
        # ----- Шапка -----
        header = tk.Frame(self.root, bg=COLORS["bg"], padx=22, pady=18)
        header.pack(fill=tk.X)

        tk.Label(header, text="🚀 Автоустановка приложений",
                 bg=COLORS["bg"], fg=COLORS["fg"],
                 font=("Segoe UI Semibold", 17)).pack(anchor="w")
        tk.Label(header, text="Расставьте порядок и установите всё одним нажатием",
                 bg=COLORS["bg"], fg=COLORS["fg_dim"],
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(2, 0))

        # ----- Панель действий -----
        toolbar = tk.Frame(self.root, bg=COLORS["bg"], padx=22)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(toolbar, text="➕  Добавить", command=self.add_installer).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(toolbar, text="✏  Аргументы", command=lambda: self._edit_args(None)).pack(side=tk.LEFT, padx=6)
        ttk.Button(toolbar, text="➖  Удалить", style="Danger.TButton",
                   command=self.remove_selected).pack(side=tk.LEFT, padx=6)
        ttk.Button(toolbar, text="🧹  Очистить", command=self.clear_list).pack(side=tk.LEFT, padx=6)

        # ----- Карточка со списком -----
        card = tk.Frame(self.root, bg=COLORS["bg_light"], padx=14, pady=14)
        card.pack(fill=tk.BOTH, expand=False, padx=22, pady=(0, 14))

        title_row = tk.Frame(card, bg=COLORS["bg_light"])
        title_row.pack(fill=tk.X, pady=(0, 10))
        tk.Label(title_row, text="Очередь установки",
                 bg=COLORS["bg_light"], fg=COLORS["fg"],
                 font=("Segoe UI Semibold", 11)).pack(side=tk.LEFT)
        tk.Label(title_row, text="перетаскивайте строки, чтобы менять порядок",
                 bg=COLORS["bg_light"], fg=COLORS["fg_dim"],
                 font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(10, 0))

        tree_wrap = tk.Frame(card, bg=COLORS["bg_light"])
        tree_wrap.pack(fill=tk.BOTH, expand=True)

        columns = ("num", "path", "args")
        self.tree = ttk.Treeview(tree_wrap, columns=columns, show="headings", height=9)
        self.tree.heading("num", text="#")
        self.tree.heading("path", text="Установщик")
        self.tree.heading("args", text="Аргументы")
        self.tree.column("num", width=45, anchor="center", stretch=False)
        self.tree.column("path", width=620)
        self.tree.column("args", width=160)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll = ttk.Scrollbar(tree_wrap, orient="vertical", command=self.tree.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y, padx=(6, 0))
        self.tree.configure(yscrollcommand=scroll.set)

        # Чередование строк
        self.tree.tag_configure("even", background=COLORS["bg_card"])
        self.tree.tag_configure("odd", background="#333652")

        # События
        self.tree.bind("<Double-1>", self._edit_args)
        self.tree.bind("<ButtonPress-1>", self._on_drag_start)
        self.tree.bind("<B1-Motion>", self._on_drag_motion)
        self.tree.bind("<ButtonRelease-1>", self._on_drag_drop)

        # ----- Панель управления установкой -----
        ctrl_card = tk.Frame(self.root, bg=COLORS["bg_light"], padx=14, pady=12)
        ctrl_card.pack(fill=tk.X, padx=22, pady=(0, 14))

        self.install_btn = ttk.Button(ctrl_card, text="🚀  Установить всё",
                                      style="Accent.TButton", command=self.start_install)
        self.install_btn.pack(side=tk.LEFT)

        progress_wrap = tk.Frame(ctrl_card, bg=COLORS["bg_light"])
        progress_wrap.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=14)

        self.status_var = tk.StringVar(value="Готово к работе")
        tk.Label(progress_wrap, textvariable=self.status_var,
                 bg=COLORS["bg_light"], fg=COLORS["fg_dim"],
                 font=("Segoe UI", 9), anchor="w").pack(fill=tk.X, pady=(0, 4))

        self.progress = ttk.Progressbar(progress_wrap, orient="horizontal", mode="determinate")
        self.progress.pack(fill=tk.X)

        # ----- Лог -----
        log_card = tk.Frame(self.root, bg=COLORS["bg_light"], padx=14, pady=14)
        log_card.pack(fill=tk.BOTH, expand=True, padx=22, pady=(0, 20))

        log_head = tk.Frame(log_card, bg=COLORS["bg_light"])
        log_head.pack(fill=tk.X, pady=(0, 8))
        tk.Label(log_head, text="Лог установки",
                 bg=COLORS["bg_light"], fg=COLORS["fg"],
                 font=("Segoe UI Semibold", 11)).pack(side=tk.LEFT)
        ttk.Button(log_head, text="Очистить лог",
                   command=self._clear_log).pack(side=tk.RIGHT)

        log_wrap = tk.Frame(log_card, bg=COLORS["bg_card"])
        log_wrap.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(
            log_wrap, wrap=tk.WORD, height=9, state=tk.DISABLED,
            bg=COLORS["bg_card"], fg=COLORS["fg"],
            insertbackground=COLORS["fg"], borderwidth=0,
            font=("Consolas", 9), padx=12, pady=10
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        log_scroll = ttk.Scrollbar(log_wrap, orient="vertical", command=self.log_text.yview)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=log_scroll.set)

        # Цветные теги для лога
        self.log_text.tag_configure("success", foreground=COLORS["success"])
        self.log_text.tag_configure("error",   foreground=COLORS["error"])
        self.log_text.tag_configure("info",    foreground=COLORS["fg"])
        self.log_text.tag_configure("header",  foreground=COLORS["accent"],
                                    font=("Consolas", 9, "bold"))

    # ---------- Работа со списком ----------
    def _refresh_list(self, select_index=None):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for idx, item in enumerate(self.installers, start=1):
            args_str = " ".join(item["args"]) if isinstance(item["args"], list) else item["args"]
            tag = "even" if idx % 2 == 0 else "odd"
            self.tree.insert("", tk.END, iid=str(idx - 1),
                             values=(idx, item["path"], args_str), tags=(tag,))

        if select_index is not None and 0 <= select_index < len(self.installers):
            iid = str(select_index)
            self.tree.selection_set(iid)
            self.tree.focus(iid)
            self.tree.see(iid)

    def add_installer(self):
        path = filedialog.askopenfilename(
            title="Выберите установщик",
            filetypes=[("Исполняемые файлы", "*.exe"), ("Все файлы", "*.*")]
        )
        if not path:
            return

        self._ask_args_dialog(
            title="Аргументы установки",
            filename=os.path.basename(path),
            initial="/VERYSILENT",
            on_save=lambda args: self._add_after_dialog(path, args)
        )

    def _add_after_dialog(self, path, args):
        self.installers.append({"path": path, "args": args})
        self._refresh_list(select_index=len(self.installers) - 1)

    def remove_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        indexes = sorted((self.tree.index(i) for i in selected), reverse=True)
        for idx in indexes:
            del self.installers[idx]
        self._refresh_list()

    def clear_list(self):
        if messagebox.askyesno("Подтверждение", "Очистить весь список?", parent=self.root):
            self.installers.clear()
            self._refresh_list()

    # ---------- Drag & Drop ----------
    def _on_drag_start(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.tree.focus(item)
        self._drag_item = item if item else None
        self._drag_start_y = event.y
        self._dragging = False

    def _on_drag_motion(self, event):
        if not self._drag_item:
            return
        if not self._dragging:
            if abs(event.y - self._drag_start_y) < 8:
                return
            self._dragging = True

        target = self.tree.identify_row(event.y)
        if target and target != self._drag_item:
            src_idx = self.tree.index(self._drag_item)
            dst_idx = self.tree.index(target)
            item = self.installers.pop(src_idx)
            self.installers.insert(dst_idx, item)
            self._refresh_list(select_index=dst_idx)
            self._drag_item = str(dst_idx)

    def _on_drag_drop(self, event):
        self._drag_item = None
        self._dragging = False

    # ---------- Редактирование аргументов ----------
    def _edit_args(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        idx = self.tree.index(sel[0])
        item = self.installers[idx]
        current = " ".join(item["args"]) if isinstance(item["args"], list) else item["args"]

        def save(args):
            item["args"] = args
            self._refresh_list(select_index=idx)

        self._ask_args_dialog(
            title="Изменить аргументы",
            filename=os.path.basename(item["path"]),
            initial=current,
            on_save=save
        )

    def _ask_args_dialog(self, title, filename, initial, on_save):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("480x250")
        win.configure(bg=COLORS["bg"])
        win.transient(self.root)
        win.grab_set()
        win.resizable(False, False)

        tk.Label(win, text="Файл", bg=COLORS["bg"], fg=COLORS["fg_dim"],
                 font=("Segoe UI", 9)).pack(anchor="w", padx=20, pady=(16, 0))
        tk.Label(win, text=filename, bg=COLORS["bg"], fg=COLORS["fg"],
                 font=("Segoe UI Semibold", 10)).pack(anchor="w", padx=20)

        tk.Label(win, text="Аргументы (например: /S или /VERYSILENT)",
                 bg=COLORS["bg"], fg=COLORS["fg_dim"],
                 font=("Segoe UI", 9)).pack(anchor="w", padx=20, pady=(12, 0))

        entry = tk.Entry(win, bg=COLORS["bg_card"], fg=COLORS["fg"],
                         insertbackground=COLORS["fg"], relief=tk.FLAT,
                         font=("Consolas", 10))
        entry.pack(fill=tk.X, padx=20, pady=(4, 0), ipady=7)
        entry.insert(0, initial)
        entry.focus()
        entry.select_range(0, tk.END)

        btn_row = tk.Frame(win, bg=COLORS["bg"])
        btn_row.pack(fill=tk.X, padx=20, pady=14)

        def confirm():
            args_str = entry.get().strip()
            args = args_str.split() if args_str else []
            on_save(args)
            win.destroy()

        ttk.Button(btn_row, text="Отмена", command=win.destroy).pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Button(btn_row, text="Сохранить", style="Accent.TButton",
                   command=confirm).pack(side=tk.RIGHT)

        win.bind("<Return>", lambda e: confirm())
        win.bind("<Escape>", lambda e: win.destroy())

    # ---------- Логирование ----------
    def log(self, text, tag="info"):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, text, tag)
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _clear_log(self):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)

    # ---------- Установка ----------
    def start_install(self):
        if not self.installers:
            messagebox.showwarning("Пусто", "Список приложений пуст.", parent=self.root)
            return

        self.install_btn.configure(state=tk.DISABLED)
        self.progress["value"] = 0
        self.progress["maximum"] = len(self.installers)
        self._clear_log()
        self.log("=== Начало установки ===\n", "header")
        self.log(f"Порядок: {' → '.join(os.path.basename(i['path']) for i in self.installers)}\n\n", "info")

        thread = threading.Thread(target=self._install_worker, daemon=True)
        thread.start()

    def _install_worker(self):
        success = 0
        failed = 0
        queue = list(self.installers)

        for i, item in enumerate(queue, start=1):
            name = os.path.basename(item["path"])
            self.root.after(0, lambda n=name, idx=i: self.status_var.set(
                f"[{idx}/{len(queue)}] {n}"
            ))

            args = item["args"]
            if isinstance(args, str):
                args = args.split()

            ok = install_from_file(item["path"], args, self.log)
            if ok:
                success += 1
            else:
                failed += 1

            self.root.after(0, lambda v=i: self.progress.configure(value=v))

        self.root.after(0, lambda: self._finish(success, failed))

    def _finish(self, success, failed):
        self.log(f"\n=== Итог: успешно — {success}, ошибок — {failed} ===\n", "header")
        self.status_var.set(f"Завершено:  ✅ {success}   ❌ {failed}")
        self.install_btn.configure(state=tk.NORMAL)
        messagebox.showinfo("Готово",
                            f"Установка завершена.\n\nУспешно: {success}\nОшибок: {failed}",
                            parent=self.root)


if __name__ == "__main__":
    root = tk.Tk()
    app = InstallerApp(root)
    root.mainloop()