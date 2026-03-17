import tkinter as tk
from tkinter import ttk
import random
import json
import os
import re

# ─────────────────────────────────────────────────────────────────
# JSON LOADER
# Questions live in a folder called "questions/" next to this file.
# Each .json file is a list of objects:
#   { "question": "...", "options": ["A","B","C","D"],
#     "correct": 2, "topic": "..." }
#
# Filename → button label conversion:
#   Hyphens become spaces, digits stay as-is EXCEPT lone digits
#   surrounded by other digits get joined with " t/m ".
#   e.g. "Netwerken-en-Platformen-Week-1-2.json"
#        → "Netwerken en Platformen Week 1 t/m 2"
# ─────────────────────────────────────────────────────────────────

QUESTIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "questions")


def filename_to_label(filename):
    """Convert a JSON filename to a human-readable button label."""
    name = os.path.splitext(filename)[0]       # strip .json
    name = name.replace("-", " ")              # hyphens → spaces
    # Collapse consecutive standalone numbers into "X t/m Y"
    # e.g. "1 2 3" → "1 t/m 3",  "1 2" → "1 t/m 2"
    name = re.sub(
        r'\b(\d+)((?:\s+\d+)+)\b',
        lambda m: m.group(1) + " t/m " + m.group(0).split()[-1],
        name,
    )
    return name


def load_question_sets():
    """
    Scan the questions/ folder and return a sorted list of:
        (label, questions_list)
    Returns an empty list if the folder doesn't exist or is empty.
    """
    sets = []
    if not os.path.isdir(QUESTIONS_DIR):
        return sets
    for fname in sorted(os.listdir(QUESTIONS_DIR)):
        if not fname.lower().endswith(".json"):
            continue
        path = os.path.join(QUESTIONS_DIR, fname)
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list) and data:
                label = filename_to_label(fname)
                sets.append((label, data))
        except Exception:
            pass          # silently skip malformed files
    return sets


# ─────────────────────────────────────────────────────────────────
# GUI APPLICATION
# ─────────────────────────────────────────────────────────────────

class QuizApp:
    NUM_QUESTIONS = 20

    # ── Palette ──────────────────────────────────────────────────
    BG         = "#F4F6FB"
    SIDEBAR    = "#1F2D4E"
    CARD       = "#FFFFFF"
    BORDER     = "#DDE3F0"
    ACCENT     = "#3B6FE8"
    ACCENT_HV  = "#2A55C0"
    TEXT       = "#1A1D2E"
    SUBTEXT    = "#6B7280"
    NAVY_TXT   = "#FFFFFF"
    CORRECT    = "#16A34A"
    CORRECT_BG = "#ECFDF5"
    WRONG      = "#DC2626"
    WRONG_BG   = "#FEF2F2"
    OPT_HOVER  = "#EEF2FF"
    WARN       = "#D97706"
    WARN_BG    = "#FFFBEB"

    def __init__(self, root):
        self.root = root
        self.root.title("BIPL Toets Oefening")
        self.root.geometry("940x720")
        self.root.minsize(820, 600)
        self.root.configure(bg=self.BG)

        self.questions      = []
        self.active_label   = ""
        self.current        = 0
        self.score          = 0
        self.answered       = False
        self.option_buttons = []
        self.results        = []

        self._setup_styles()
        self._build_welcome()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Quiz.Horizontal.TProgressbar",
                        troughcolor=self.BORDER,
                        background=self.ACCENT,
                        bordercolor=self.BG,
                        lightcolor=self.ACCENT,
                        darkcolor=self.ACCENT,
                        thickness=6)
        style.configure("Thin.Vertical.TScrollbar",
                        troughcolor=self.BG,
                        background=self.BORDER,
                        bordercolor=self.BG,
                        arrowcolor=self.SUBTEXT)

    # ──────────────────────────────────────────────────────────────
    # WELCOME / MENU SCREEN
    # ──────────────────────────────────────────────────────────────
    def _build_welcome(self):
        self._clear()

        question_sets = load_question_sets()

        # Top navy strip
        tk.Frame(self.root, bg=self.SIDEBAR, height=8).pack(fill="x")

        outer = tk.Frame(self.root, bg=self.BG)
        outer.pack(expand=True)

        # Card
        card = tk.Frame(outer, bg=self.CARD,
                        highlightthickness=1,
                        highlightbackground=self.BORDER)
        card.pack(padx=60, pady=30, ipadx=40, ipady=30)

        # Card header strip
        hdr = tk.Frame(card, bg=self.SIDEBAR)
        hdr.pack(fill="x")
        tk.Label(hdr, text="BIPL  Toets Oefening",
                 font=("Segoe UI", 20, "bold"),
                 bg=self.SIDEBAR, fg=self.NAVY_TXT,
                 padx=28, pady=18).pack(side="left")

        body = tk.Frame(card, bg=self.CARD)
        body.pack(padx=28, pady=20)

        if not question_sets:
            # ── No JSON files found ──────────────────────────────
            tk.Label(body,
                     text="Geen vragensets gevonden.",
                     font=("Segoe UI", 13, "bold"),
                     bg=self.CARD, fg=self.WARN).pack(pady=(0, 8))
            tk.Label(body,
                     text=(f"Maak een map '{QUESTIONS_DIR}' aan\n"
                           "en voeg daarin .json-bestanden toe met vragen."),
                     font=("Segoe UI", 11),
                     bg=self.CARD, fg=self.SUBTEXT,
                     justify="center").pack()
            return

        # ── Info bullets ─────────────────────────────────────────
        tk.Label(body, text="Kies een toets om te oefenen:",
                 font=("Segoe UI", 12), bg=self.CARD,
                 fg=self.SUBTEXT).pack(pady=(0, 18))

        for bullet in (
            f"  ✦   {self.NUM_QUESTIONS} willekeurige vragen per ronde",
            "  ✦   Antwoordopties worden elke keer opnieuw geschud",
            "  ✦   Direct feedback en uitleg bij elk antwoord",
            "  ✦   Volledig scoreoverzicht aan het einde",
        ):
            tk.Label(body, text=bullet,
                     font=("Segoe UI", 11), bg=self.CARD,
                     fg=self.TEXT, anchor="w").pack(fill="x", pady=2)

        tk.Frame(body, bg=self.BORDER, height=1).pack(fill="x", pady=18)

        # ── One button per question set ──────────────────────────
        for label, questions in question_sets:
            q_count = len(questions)
            row = tk.Frame(body, bg=self.CARD)
            row.pack(fill="x", pady=5)

            # Use a Frame+Label instead of tk.Button so bg colour
            # renders correctly on macOS (which ignores Button bg).
            btn_frame = tk.Frame(row, bg=self.ACCENT, cursor="hand2")
            btn_frame.pack(side="left", fill="x", expand=True)

            btn_lbl = tk.Label(
                btn_frame,
                text=label,
                font=("Segoe UI", 12, "bold"),
                bg=self.ACCENT, fg="white",
                anchor="w", padx=24, pady=12,
                cursor="hand2",
            )
            btn_lbl.pack(fill="x")

            def _on_enter(e, f=btn_frame, l=btn_lbl):
                f.config(bg=self.ACCENT_HV)
                l.config(bg=self.ACCENT_HV)

            def _on_leave(e, f=btn_frame, l=btn_lbl):
                f.config(bg=self.ACCENT)
                l.config(bg=self.ACCENT)

            def _on_click(e, lbl=label, qs=questions):
                self._start_quiz(lbl, qs)

            for widget in (btn_frame, btn_lbl):
                widget.bind("<Enter>", _on_enter)
                widget.bind("<Leave>", _on_leave)
                widget.bind("<Button-1>", _on_click)

            tk.Label(row,
                     text=f"{q_count} vragen",
                     font=("Segoe UI", 10),
                     bg=self.CARD, fg=self.SUBTEXT,
                     padx=12).pack(side="left")

    # ──────────────────────────────────────────────────────────────
    # QUIZ LOGIC
    # ──────────────────────────────────────────────────────────────
    def _start_quiz(self, label, question_pool):
        pool = list(question_pool)
        random.shuffle(pool)
        self.questions    = pool[:self.NUM_QUESTIONS]
        self.active_label = label
        self.current      = 0
        self.score        = 0
        self.answered     = False
        self.results      = []
        self._build_quiz_ui()
        self._load_question()

    def _build_quiz_ui(self):
        self._clear()

        # ── Top bar ──────────────────────────────────────────────
        topbar = tk.Frame(self.root, bg=self.SIDEBAR)
        topbar.pack(fill="x")

        tk.Label(topbar, text=self.active_label,
                 font=("Segoe UI", 11, "bold"),
                 bg=self.SIDEBAR, fg=self.NAVY_TXT,
                 padx=20, pady=10).pack(side="left")

        self.lbl_score = tk.Label(topbar, text="",
                                  font=("Segoe UI", 11, "bold"),
                                  bg=self.SIDEBAR, fg="#93C5FD",
                                  padx=20)
        self.lbl_score.pack(side="right")

        self.lbl_progress = tk.Label(topbar, text="",
                                     font=("Segoe UI", 10),
                                     bg=self.SIDEBAR, fg="#93C5FD",
                                     padx=6)
        self.lbl_progress.pack(side="right")

        # ── Progress bar ─────────────────────────────────────────
        self.progress_bar = ttk.Progressbar(
            self.root,
            style="Quiz.Horizontal.TProgressbar",
            mode="determinate",
            maximum=self.NUM_QUESTIONS)
        self.progress_bar.pack(fill="x")

        # ── Scrollable content area ───────────────────────────────
        canvas = tk.Canvas(self.root, bg=self.BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical",
                                  command=canvas.yview,
                                  style="Thin.Vertical.TScrollbar")
        self._quiz_inner = tk.Frame(canvas, bg=self.BG)
        self._quiz_inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self._quiz_inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(
                            int(-1 * (e.delta / 120)), "units"))
        self._quiz_canvas = canvas

        pad = tk.Frame(self._quiz_inner, bg=self.BG)
        pad.pack(fill="x", padx=30, pady=20)

        # Topic badge
        self.lbl_topic = tk.Label(pad, text="",
                                  font=("Segoe UI", 9, "bold"),
                                  bg=self.ACCENT, fg="white",
                                  padx=10, pady=4)
        self.lbl_topic.pack(anchor="w", pady=(0, 10))

        # Question card
        qcard = tk.Frame(pad, bg=self.CARD,
                         highlightthickness=1,
                         highlightbackground=self.BORDER)
        qcard.pack(fill="x")
        tk.Frame(qcard, bg=self.ACCENT, width=5).pack(side="left", fill="y")
        self.lbl_question = tk.Label(
            qcard, text="", wraplength=800,
            font=("Segoe UI", 13), bg=self.CARD, fg=self.TEXT,
            justify="left", padx=20, pady=20)
        self.lbl_question.pack(fill="x", expand=True)

        # Answer options
        self.opts_pad = tk.Frame(pad, bg=self.BG)
        self.opts_pad.pack(fill="x", pady=(12, 0))

        self.option_buttons = []
        for i in range(4):
            row = tk.Frame(self.opts_pad, bg=self.CARD,
                           highlightthickness=1,
                           highlightbackground=self.BORDER,
                           cursor="hand2")
            row.pack(fill="x", pady=5)

            badge = tk.Label(row, text=chr(65 + i),
                             font=("Segoe UI", 11, "bold"),
                             bg=self.BORDER, fg=self.SUBTEXT,
                             width=3, pady=14)
            badge.pack(side="left", fill="y")

            lbl = tk.Label(row, text="",
                           font=("Segoe UI", 11),
                           bg=self.CARD, fg=self.TEXT,
                           anchor="w", justify="left",
                           wraplength=750, padx=14, pady=14)
            lbl.pack(side="left", fill="x", expand=True)

            for widget in (row, badge, lbl):
                widget.bind("<Button-1>",
                            lambda e, idx=i: self._select_answer(idx))
                widget.bind("<Enter>",
                            lambda e, r=row, b=badge, lb=lbl:
                                self._opt_hover(r, b, lb, True))
                widget.bind("<Leave>",
                            lambda e, r=row, b=badge, lb=lbl:
                                self._opt_hover(r, b, lb, False))

            self.option_buttons.append((row, badge, lbl))

        # Feedback bar
        self.lbl_feedback = tk.Label(
            pad, text="",
            font=("Segoe UI", 11, "bold"),
            bg=self.BG, fg=self.TEXT,
            wraplength=860, justify="left", pady=6)
        self.lbl_feedback.pack(anchor="w", pady=(10, 0))

        # Next button — Frame+Label for consistent colour on macOS
        self._btn_next_frame = tk.Frame(pad, bg=self.BORDER, cursor="hand2")
        self._btn_next_frame.pack(anchor="e", pady=(14, 30))

        self.btn_next = tk.Label(
            self._btn_next_frame,
            text="Volgende vraag  →",
            font=("Segoe UI", 12, "bold"),
            bg=self.BORDER, fg=self.SUBTEXT,
            padx=28, pady=12, cursor="hand2")
        self.btn_next.pack()
        self._btn_next_enabled = False

        def _next_enter(e):
            if self._btn_next_enabled:
                self._btn_next_frame.config(bg=self.ACCENT_HV)
                self.btn_next.config(bg=self.ACCENT_HV)

        def _next_leave(e):
            if self._btn_next_enabled:
                self._btn_next_frame.config(bg=self.ACCENT)
                self.btn_next.config(bg=self.ACCENT)

        def _next_click(e):
            if self._btn_next_enabled:
                self._next_question()

        for w in (self._btn_next_frame, self.btn_next):
            w.bind("<Enter>", _next_enter)
            w.bind("<Leave>", _next_leave)
            w.bind("<Button-1>", _next_click)

    def _opt_hover(self, row, badge, lbl, entering):
        if entering:
            row.config(highlightbackground=self.ACCENT, bg=self.OPT_HOVER)
            badge.config(bg=self.ACCENT, fg="white")
            lbl.config(bg=self.OPT_HOVER)
        else:
            if row.cget("bg") not in (self.CORRECT_BG, self.WRONG_BG):
                row.config(highlightbackground=self.BORDER, bg=self.CARD)
                badge.config(bg=self.BORDER, fg=self.SUBTEXT)
                lbl.config(bg=self.CARD)

    def _load_question(self):
        q = self.questions[self.current]
        q_text  = q["question"]
        options = q["options"]
        correct = q["correct"]
        topic   = q.get("topic", "")

        self.answered = False
        n = self.current + 1

        self.lbl_progress.config(text=f"Vraag {n} / {self.NUM_QUESTIONS}")
        self.lbl_score.config(text=f"Score: {self.score}")
        self.progress_bar["value"] = self.current
        self.lbl_topic.config(text=f"  {topic}  ")
        self.lbl_question.config(text=q_text)
        self.lbl_feedback.config(text="", bg=self.BG)
        next_text = "Volgende vraag  →" if n < self.NUM_QUESTIONS else "Bekijk resultaten  →"
        self._set_next_btn(enabled=False, text=next_text)

        # Shuffle options, keep track of original indices
        indexed = list(enumerate(options))
        random.shuffle(indexed)
        self._shuffled_options = indexed

        for i, (orig_idx, text) in enumerate(indexed):
            row, badge, lbl = self.option_buttons[i]
            row.config(bg=self.CARD, highlightbackground=self.BORDER,
                       cursor="hand2")
            badge.config(text=chr(65 + i), bg=self.BORDER, fg=self.SUBTEXT)
            lbl.config(text=text, bg=self.CARD, fg=self.TEXT)
            for widget in (row, badge, lbl):
                widget.bind("<Button-1>",
                            lambda e, idx=i: self._select_answer(idx))

        self._quiz_canvas.yview_moveto(0)

    def _select_answer(self, idx):
        if self.answered:
            return
        self.answered = True

        q       = self.questions[self.current]
        options = q["options"]
        correct = q["correct"]

        correct_shuffled = next(
            i for i, (orig, _) in enumerate(self._shuffled_options)
            if orig == correct)

        is_correct = (idx == correct_shuffled)

        def colour_opt(i, bg, badge_bg, badge_fg, text_fg):
            row, badge, lbl = self.option_buttons[i]
            row.config(bg=bg, highlightbackground=badge_bg, cursor="")
            badge.config(bg=badge_bg, fg=badge_fg)
            lbl.config(bg=bg, fg=text_fg)
            for widget in (row, badge, lbl):
                widget.unbind("<Button-1>")
                widget.unbind("<Enter>")
                widget.unbind("<Leave>")

        if is_correct:
            self.score += 1
            colour_opt(idx, self.CORRECT_BG, self.CORRECT, "white", self.CORRECT)
            self.lbl_feedback.config(
                text="  ✓  Correct!", fg=self.CORRECT, bg=self.CORRECT_BG)
        else:
            colour_opt(idx, self.WRONG_BG, self.WRONG, "white", self.WRONG)
            colour_opt(correct_shuffled,
                       self.CORRECT_BG, self.CORRECT, "white", self.CORRECT)
            self.lbl_feedback.config(
                text=f"  ✗  Fout.  Juist antwoord: {options[correct]}",
                fg=self.WRONG, bg=self.WRONG_BG)

        for i in range(4):
            if i != idx and i != correct_shuffled:
                colour_opt(i, self.CARD, self.BORDER, self.SUBTEXT, self.SUBTEXT)

        self.results.append({
            "question":    q["question"],
            "topic":       q.get("topic", ""),
            "correct":     is_correct,
            "your_answer": self._shuffled_options[idx][1],
            "right_answer": options[correct],
        })
        self._set_next_btn(enabled=True)

    def _set_next_btn(self, enabled, text=None):
        """Enable or disable the next button and optionally update its text."""
        self._btn_next_enabled = enabled
        if text:
            self.btn_next.config(text=text)
        if enabled:
            self._btn_next_frame.config(bg=self.ACCENT)
            self.btn_next.config(bg=self.ACCENT, fg="white")
        else:
            self._btn_next_frame.config(bg=self.BORDER)
            self.btn_next.config(bg=self.BORDER, fg=self.SUBTEXT)

    def _next_question(self):
        self.current += 1
        if self.current >= self.NUM_QUESTIONS:
            self._show_results()
        else:
            self._load_question()

    # ──────────────────────────────────────────────────────────────
    # RESULTS SCREEN
    # ──────────────────────────────────────────────────────────────
    def _show_results(self):
        self._clear()

        pct          = round(self.score / self.NUM_QUESTIONS * 100)
        passed       = pct >= 55
        result_color = self.CORRECT if passed else self.WRONG
        result_bg    = self.CORRECT_BG if passed else self.WRONG_BG
        emoji        = "🏆" if pct >= 80 else ("👍" if passed else "📝")
        status_text  = "Geslaagd!" if passed else "Niet geslaagd – blijf oefenen!"

        # Header
        banner = tk.Frame(self.root, bg=self.SIDEBAR)
        banner.pack(fill="x")
        tk.Label(banner, text="Resultaten",
                 font=("Segoe UI", 13, "bold"),
                 bg=self.SIDEBAR, fg=self.NAVY_TXT,
                 padx=20, pady=10).pack(side="left")
        tk.Label(banner, text=self.active_label,
                 font=("Segoe UI", 10),
                 bg=self.SIDEBAR, fg="#93C5FD",
                 padx=20).pack(side="right")

        # Score card
        score_outer = tk.Frame(self.root, bg=result_bg,
                               highlightthickness=1,
                               highlightbackground=result_color)
        score_outer.pack(fill="x", padx=30, pady=(20, 0))
        inner_s = tk.Frame(score_outer, bg=result_bg)
        inner_s.pack(pady=18)
        tk.Label(inner_s, text=emoji,
                 font=("Segoe UI Emoji", 36),
                 bg=result_bg).pack(side="left", padx=(20, 14))
        right = tk.Frame(inner_s, bg=result_bg)
        right.pack(side="left")
        tk.Label(right,
                 text=f"{self.score} / {self.NUM_QUESTIONS}   ({pct}%)",
                 font=("Segoe UI", 22, "bold"),
                 bg=result_bg, fg=result_color).pack(anchor="w")
        tk.Label(right, text=status_text,
                 font=("Segoe UI", 12),
                 bg=result_bg, fg=result_color).pack(anchor="w")

        # Review header
        tk.Label(self.root,
                 text="Overzicht van jouw antwoorden",
                 font=("Segoe UI", 11, "bold"),
                 bg=self.BG, fg=self.TEXT).pack(
                     anchor="w", padx=30, pady=(16, 4))

        # Scrollable answer list
        wrap = tk.Frame(self.root, bg=self.BG)
        wrap.pack(fill="both", expand=True, padx=30, pady=(0, 4))

        cv = tk.Canvas(wrap, bg=self.BG, highlightthickness=0)
        sb = ttk.Scrollbar(wrap, orient="vertical",
                           command=cv.yview,
                           style="Thin.Vertical.TScrollbar")
        inner = tk.Frame(cv, bg=self.BG)
        inner.bind("<Configure>",
                   lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.create_window((0, 0), window=inner, anchor="nw")
        cv.configure(yscrollcommand=sb.set)
        cv.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        cv.bind_all("<MouseWheel>",
                    lambda e: cv.yview_scroll(
                        int(-1 * (e.delta / 120)), "units"))

        for i, r in enumerate(self.results):
            c   = self.CORRECT if r["correct"] else self.WRONG
            cbg = self.CORRECT_BG if r["correct"] else self.WRONG_BG
            ico = "✓" if r["correct"] else "✗"

            row = tk.Frame(inner, bg=cbg,
                           highlightthickness=1,
                           highlightbackground=c)
            row.pack(fill="x", pady=3)

            tk.Label(row, text=ico,
                     font=("Segoe UI", 13, "bold"),
                     bg=c, fg="white",
                     width=3, pady=10).pack(side="left", fill="y")

            body = tk.Frame(row, bg=cbg)
            body.pack(side="left", fill="x", expand=True, padx=12, pady=8)

            tk.Label(body,
                     text=f"V{i+1}.  {r['question']}",
                     font=("Segoe UI", 10, "bold"),
                     bg=cbg, fg=c,
                     wraplength=760, justify="left").pack(anchor="w")

            if not r["correct"]:
                tk.Label(body,
                         text=f"Jouw antwoord:   {r['your_answer']}",
                         font=("Segoe UI", 9),
                         bg=cbg, fg=self.WRONG).pack(anchor="w", pady=(3, 0))
                tk.Label(body,
                         text=f"Juist antwoord:   {r['right_answer']}",
                         font=("Segoe UI", 9),
                         bg=cbg, fg=self.CORRECT).pack(anchor="w")

        # Action buttons — Frame+Label for consistent colour on macOS
        btn_row = tk.Frame(self.root, bg=self.BG)
        btn_row.pack(pady=14)

        def _make_btn(parent, text, bg, fg, hover_bg, callback, side="left"):
            f = tk.Frame(parent, bg=bg, cursor="hand2")
            f.pack(side=side, padx=8)
            l = tk.Label(f, text=text, font=("Segoe UI", 12, "bold"),
                         bg=bg, fg=fg, padx=24, pady=11, cursor="hand2")
            l.pack()
            for w in (f, l):
                w.bind("<Enter>",    lambda e, f=f, l=l, c=hover_bg: (f.config(bg=c), l.config(bg=c)))
                w.bind("<Leave>",    lambda e, f=f, l=l, c=bg:       (f.config(bg=c), l.config(bg=c)))
                w.bind("<Button-1>", lambda e, cb=callback: cb())

        _make_btn(btn_row, "Opnieuw spelen  →",
                  self.ACCENT, "white", self.ACCENT_HV,
                  lambda: self._start_quiz(self.active_label, self.questions))

        _make_btn(btn_row, "Hoofdmenu",
                  self.BORDER, self.TEXT, "#C8D0E8",
                  self._build_welcome)

    # ──────────────────────────────────────────────────────────────
    def _clear(self):
        for w in self.root.winfo_children():
            w.destroy()


# ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app = QuizApp(root)
    root.mainloop()