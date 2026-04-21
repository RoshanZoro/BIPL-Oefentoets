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
#     "correct": 2,           ← int  OR  list of ints  e.g. [0,2,4]
#     "topic": "...",
#     "dragging": true }      ← optional; renders drag-to-select UI
#
# Filename → button label conversion:
#   Hyphens become spaces, digits stay as-is EXCEPT lone digits
#   surrounded by other digits get joined with " t/m ".
#   e.g. "Netwerken-en-Platformen-Week-1-2.json"
#        → "Netwerken en Platformen Week 1 t/m 2"
# ─────────────────────────────────────────────────────────────────

QUESTIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "questions")


def filename_to_label(filename):
    name = os.path.splitext(filename)[0]
    name = name.replace("-", " ")
    name = re.sub(
        r'\b(\d+)((?:\s+\d+)+)\b',
        lambda m: m.group(1) + " t/m " + m.group(0).split()[-1],
        name,
    )
    return name


def load_question_sets():
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
                sets.append((filename_to_label(fname), data))
        except Exception:
            pass
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

        self.questions            = []
        self._question_pool       = []
        self.active_label         = ""
        self.current              = 0
        self.score                = 0
        self._num_q               = self.NUM_QUESTIONS
        self.answered_flags       = [False]
        self.option_buttons       = []
        self.results              = []
        self.questions_per_screen = 1
        self._shuffled_options    = []
        self._multi_vars          = []
        self._drag_states         = []
        self._slot_buttons_full   = {}

        self.dual_mode_var = tk.BooleanVar(value=False)
        self.all_q_var     = tk.BooleanVar(value=False)

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

        tk.Frame(self.root, bg=self.SIDEBAR, height=8).pack(fill="x")

        outer = tk.Frame(self.root, bg=self.BG)
        outer.pack(expand=True)

        card = tk.Frame(outer, bg=self.CARD,
                        highlightthickness=1,
                        highlightbackground=self.BORDER)
        card.pack(padx=60, pady=30, ipadx=40, ipady=30)

        hdr = tk.Frame(card, bg=self.SIDEBAR)
        hdr.pack(fill="x")
        tk.Label(hdr, text="BIPL  Toets Oefening",
                 font=("Segoe UI", 20, "bold"),
                 bg=self.SIDEBAR, fg=self.NAVY_TXT,
                 padx=28, pady=18).pack(side="left")

        body = tk.Frame(card, bg=self.CARD)
        body.pack(padx=28, pady=20)

        if not question_sets:
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

        # ── Toggle options ────────────────────────────────────────
        toggles_row = tk.Frame(body, bg=self.CARD)
        toggles_row.pack(fill="x", pady=(0, 14))

        for text, var in (
            ("2 vragen tegelijk weergeven", self.dual_mode_var),
            ("Alle vragen (geen limiet van 20)", self.all_q_var),
        ):
            tk.Checkbutton(
                toggles_row,
                text=f"  {text}",
                variable=var,
                font=("Segoe UI", 11),
                bg=self.CARD, fg=self.TEXT,
                activebackground=self.CARD,
                activeforeground=self.TEXT,
                selectcolor=self.CARD,
                relief="flat",
                cursor="hand2",
            ).pack(side="left", padx=(0, 24))

        # ── One button per question set ───────────────────────────
        for label, questions in question_sets:
            row = tk.Frame(body, bg=self.CARD)
            row.pack(fill="x", pady=5)

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
                f.config(bg=self.ACCENT_HV); l.config(bg=self.ACCENT_HV)

            def _on_leave(e, f=btn_frame, l=btn_lbl):
                f.config(bg=self.ACCENT); l.config(bg=self.ACCENT)

            def _on_click(e, lbl=label, qs=questions):
                self._start_quiz(lbl, qs)

            for widget in (btn_frame, btn_lbl):
                widget.bind("<Enter>", _on_enter)
                widget.bind("<Leave>", _on_leave)
                widget.bind("<Button-1>", _on_click)

            tk.Label(row,
                     text=f"{len(questions)} vragen",
                     font=("Segoe UI", 10),
                     bg=self.CARD, fg=self.SUBTEXT,
                     padx=12).pack(side="left")

    # ──────────────────────────────────────────────────────────────
    # QUIZ LOGIC
    # ──────────────────────────────────────────────────────────────
    def _start_quiz(self, label, question_pool):
        self.questions_per_screen = 2 if self.dual_mode_var.get() else 1
        self._question_pool = list(question_pool)
        pool = list(self._question_pool)
        random.shuffle(pool)
        self.questions    = pool if self.all_q_var.get() else pool[:self.NUM_QUESTIONS]
        self._num_q       = len(self.questions)
        self.active_label = label
        self.current      = 0
        self.score        = 0
        self.results      = []
        self._build_quiz_ui()
        self._load_question()

    def _build_quiz_ui(self):
        self._clear()

        topbar = tk.Frame(self.root, bg=self.SIDEBAR)
        topbar.pack(fill="x")
        tk.Label(topbar, text=self.active_label,
                 font=("Segoe UI", 11, "bold"),
                 bg=self.SIDEBAR, fg=self.NAVY_TXT,
                 padx=20, pady=10).pack(side="left")
        self.lbl_score = tk.Label(topbar, text="",
                                  font=("Segoe UI", 11, "bold"),
                                  bg=self.SIDEBAR, fg="#93C5FD", padx=20)
        self.lbl_score.pack(side="right")
        self.lbl_progress = tk.Label(topbar, text="",
                                     font=("Segoe UI", 10),
                                     bg=self.SIDEBAR, fg="#93C5FD", padx=6)
        self.lbl_progress.pack(side="right")

        self.progress_bar = ttk.Progressbar(
            self.root,
            style="Quiz.Horizontal.TProgressbar",
            mode="determinate",
            maximum=self._num_q)
        self.progress_bar.pack(fill="x")

        canvas = tk.Canvas(self.root, bg=self.BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical",
                                  command=canvas.yview,
                                  style="Thin.Vertical.TScrollbar")
        self._scroll_inner = tk.Frame(canvas, bg=self.BG)
        self._scroll_inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self._scroll_inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(
                            int(-1 * (e.delta / 120)), "units"))
        self._quiz_canvas = canvas

        # Dynamic content area — rebuilt each question
        self._questions_frame = tk.Frame(self._scroll_inner, bg=self.BG)
        self._questions_frame.pack(fill="x", padx=30, pady=20)

    def _load_question(self):
        for w in self._questions_frame.winfo_children():
            w.destroy()

        slots_on_page = min(self.questions_per_screen, self._num_q - self.current)

        self.answered_flags    = [False] * self.questions_per_screen
        self._shuffled_options = [None]  * self.questions_per_screen
        self._multi_vars       = [None]  * self.questions_per_screen
        self._drag_states      = [None]  * self.questions_per_screen
        self.option_buttons    = [[]     for _ in range(self.questions_per_screen)]
        self._slot_buttons_full = {}
        self.lbl_topic         = []
        self.lbl_question      = []
        self.lbl_feedback      = []

        # Auto-answer padding slots (odd question count + dual mode)
        for s in range(slots_on_page, self.questions_per_screen):
            self.answered_flags[s] = True

        last_shown = self.current + slots_on_page
        if self.questions_per_screen == 2 and slots_on_page == 2:
            progress_text = f"Vragen {self.current + 1}-{last_shown} / {self._num_q}"
        else:
            progress_text = f"Vraag {self.current + 1} / {self._num_q}"

        self.lbl_progress.config(text=progress_text)
        self.lbl_score.config(text=f"Score: {self.score}")
        self.progress_bar["value"] = self.current

        next_text = (
            "Bekijk resultaten  →" if last_shown >= self._num_q else "Volgende vraag  →"
        )

        # Layout: side-by-side only when truly 2 slots
        if self.questions_per_screen == 2 and slots_on_page == 2:
            q_row = tk.Frame(self._questions_frame, bg=self.BG)
            q_row.pack(fill="x")
            panel_parents = []
            for s in range(2):
                col = tk.Frame(q_row, bg=self.BG)
                col.pack(side="left", expand=True, fill="both",
                         padx=(0, 8) if s == 0 else (8, 0))
                panel_parents.append(col)
        else:
            panel_parents = [self._questions_frame]

        for slot in range(slots_on_page):
            q      = self.questions[self.current + slot]
            parent = panel_parents[slot] if slot < len(panel_parents) else panel_parents[0]

            # Topic badge
            lbl_topic = tk.Label(parent, text=f"  {q.get('topic', '')}  ",
                                 font=("Segoe UI", 9, "bold"),
                                 bg=self.ACCENT, fg="white", padx=10, pady=4)
            lbl_topic.pack(anchor="w", pady=(0, 10))
            self.lbl_topic.append(lbl_topic)

            # Question card
            qcard = tk.Frame(parent, bg=self.CARD,
                             highlightthickness=1, highlightbackground=self.BORDER)
            qcard.pack(fill="x")
            tk.Frame(qcard, bg=self.ACCENT, width=5).pack(side="left", fill="y")
            lbl_q = tk.Label(qcard, text=q["question"], wraplength=800,
                             font=("Segoe UI", 13), bg=self.CARD, fg=self.TEXT,
                             justify="left", padx=20, pady=20)
            lbl_q.pack(fill="x", expand=True)
            self.lbl_question.append(lbl_q)

            lbl_feedback = tk.Label(parent, text="",
                                    font=("Segoe UI", 11, "bold"),
                                    bg=self.BG, fg=self.TEXT,
                                    wraplength=860, justify="left", pady=6)
            self.lbl_feedback.append(lbl_feedback)

            if q.get("dragging", False):
                self._build_drag_slot(parent, slot, q, lbl_feedback)
            elif isinstance(q.get("correct"), list):
                self._build_multi_slot(parent, slot, q, lbl_feedback)
            else:
                self._build_single_slot(parent, slot, q, lbl_feedback)

        # Next button
        self._btn_next_frame = tk.Frame(self._questions_frame, bg=self.BORDER, cursor="hand2")
        self._btn_next_frame.pack(anchor="e", pady=(14, 30))
        self.btn_next = tk.Label(
            self._btn_next_frame,
            text=next_text,
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

        self._quiz_canvas.yview_moveto(0)

    # ──────────────────────────────────────────────────────────────
    # SLOT BUILDERS
    # ──────────────────────────────────────────────────────────────

    def _build_single_slot(self, parent, slot, q, lbl_feedback):
        options = q["options"]
        indexed = list(enumerate(options))
        random.shuffle(indexed)
        self._shuffled_options[slot] = indexed

        opts_pad = tk.Frame(parent, bg=self.BG)
        opts_pad.pack(fill="x", pady=(12, 0))

        slot_buttons = []
        for i, (orig_idx, text) in enumerate(indexed):
            row = tk.Frame(opts_pad, bg=self.CARD,
                           highlightthickness=1, highlightbackground=self.BORDER,
                           cursor="hand2")
            row.pack(fill="x", pady=5)

            badge = tk.Label(row, text=chr(65 + i),
                             font=("Segoe UI", 11, "bold"),
                             bg=self.BORDER, fg=self.SUBTEXT,
                             width=3, pady=14)
            badge.pack(side="left", fill="y")

            lbl = tk.Label(row, text=text,
                           font=("Segoe UI", 11),
                           bg=self.CARD, fg=self.TEXT,
                           anchor="w", justify="left",
                           wraplength=750, padx=14, pady=14)
            lbl.pack(side="left", fill="x", expand=True)

            for widget in (row, badge, lbl):
                widget.bind("<Button-1>",
                            lambda e, idx=i, s=slot: self._select_answer(idx, s))
                widget.bind("<Enter>",
                            lambda e, r=row, b=badge, lb=lbl:
                                self._opt_hover(r, b, lb, True))
                widget.bind("<Leave>",
                            lambda e, r=row, b=badge, lb=lbl:
                                self._opt_hover(r, b, lb, False))

            slot_buttons.append((row, badge, lbl))

        self.option_buttons[slot] = slot_buttons
        lbl_feedback.pack(anchor="w", pady=(10, 0))

    def _build_multi_slot(self, parent, slot, q, lbl_feedback):
        options     = q["options"]
        correct_set = set(q["correct"]) if isinstance(q["correct"], list) else {q["correct"]}
        indexed     = list(enumerate(options))
        random.shuffle(indexed)
        self._shuffled_options[slot] = indexed

        opts_pad = tk.Frame(parent, bg=self.BG)
        opts_pad.pack(fill="x", pady=(12, 0))

        n = len(correct_set)
        tk.Label(opts_pad,
                 text=f"Selecteer {n} antwoord{'en' if n > 1 else ''}:",
                 font=("Segoe UI", 10, "italic"),
                 bg=self.BG, fg=self.SUBTEXT).pack(anchor="w", pady=(0, 4))

        vars_list   = []
        slot_buttons = []

        for i, (orig_idx, text) in enumerate(indexed):
            var = tk.BooleanVar(value=False)
            vars_list.append(var)

            row = tk.Frame(opts_pad, bg=self.CARD,
                           highlightthickness=1, highlightbackground=self.BORDER,
                           cursor="hand2")
            row.pack(fill="x", pady=5)

            badge = tk.Label(row, text=chr(65 + i),
                             font=("Segoe UI", 11, "bold"),
                             bg=self.BORDER, fg=self.SUBTEXT,
                             width=3, pady=14)
            badge.pack(side="left", fill="y")

            chk_lbl = tk.Label(row, text="☐",
                               font=("Segoe UI", 15),
                               bg=self.CARD, fg=self.SUBTEXT,
                               padx=6, pady=14)
            chk_lbl.pack(side="left")

            lbl = tk.Label(row, text=text,
                           font=("Segoe UI", 11),
                           bg=self.CARD, fg=self.TEXT,
                           anchor="w", justify="left",
                           wraplength=700, padx=10, pady=14)
            lbl.pack(side="left", fill="x", expand=True)

            def _toggle(e, v=var, ci=chk_lbl, r=row, b=badge, lb=lbl, s=slot):
                if self.answered_flags[s]:
                    return
                v.set(not v.get())
                if v.get():
                    ci.config(text="☑", fg=self.ACCENT)
                    r.config(bg=self.OPT_HOVER, highlightbackground=self.ACCENT)
                    b.config(bg=self.ACCENT, fg="white")
                    lb.config(bg=self.OPT_HOVER)
                else:
                    ci.config(text="☐", fg=self.SUBTEXT)
                    r.config(bg=self.CARD, highlightbackground=self.BORDER)
                    b.config(bg=self.BORDER, fg=self.SUBTEXT)
                    lb.config(bg=self.CARD)

            for widget in (row, badge, chk_lbl, lbl):
                widget.bind("<Button-1>", _toggle)

            slot_buttons.append((row, badge, lbl, chk_lbl))

        self._multi_vars[slot]            = vars_list
        self._slot_buttons_full[slot]     = slot_buttons
        self.option_buttons[slot]         = [(r, b, l) for r, b, l, _ in slot_buttons]

        cf = tk.Frame(opts_pad, bg=self.ACCENT, cursor="hand2")
        cf.pack(anchor="w", pady=(10, 0))
        cl = tk.Label(cf, text="Bevestig antwoorden",
                      font=("Segoe UI", 11, "bold"),
                      bg=self.ACCENT, fg="white", padx=20, pady=8, cursor="hand2")
        cl.pack()

        def _confirm(e=None, s=slot, _q=q):
            if not self.answered_flags[s]:
                self._confirm_multi(s, _q)

        for w in (cf, cl):
            w.bind("<Button-1>", _confirm)
            w.bind("<Enter>", lambda e, f=cf, lb=cl: (f.config(bg=self.ACCENT_HV), lb.config(bg=self.ACCENT_HV)))
            w.bind("<Leave>", lambda e, f=cf, lb=cl: (f.config(bg=self.ACCENT), lb.config(bg=self.ACCENT)))

        lbl_feedback.pack(anchor="w", pady=(10, 0))

    def _build_drag_slot(self, parent, slot, q, lbl_feedback):
        options     = q["options"]
        indexed     = list(enumerate(options))
        random.shuffle(indexed)
        self._shuffled_options[slot] = indexed

        correct_val = q["correct"]
        correct_set = set(correct_val) if isinstance(correct_val, list) else {correct_val}
        n           = len(correct_set)

        tk.Label(parent,
                 text=f"Sleep of klik de juiste optie{'s' if n > 1 else ''} naar rechts"
                      f"  ({n} {'antwoorden' if n > 1 else 'antwoord'}):",
                 font=("Segoe UI", 10, "italic"),
                 bg=self.BG, fg=self.SUBTEXT).pack(anchor="w", pady=(8, 2))

        outer = tk.Frame(parent, bg=self.BG)
        outer.pack(fill="x", pady=(4, 0))

        # Left panel
        left_outer = tk.Frame(outer, bg=self.BORDER)
        left_outer.pack(side="left", fill="both", expand=True, padx=(0, 4))
        tk.Label(left_outer, text="  Beschikbare opties",
                 font=("Segoe UI", 9, "bold"),
                 bg=self.BORDER, fg=self.SUBTEXT,
                 pady=5, anchor="w").pack(fill="x")
        left_frame = tk.Frame(left_outer, bg=self.CARD)
        left_frame.pack(fill="both", expand=True, padx=1, pady=(0, 1))

        # Right panel
        right_outer = tk.Frame(outer, bg=self.BORDER)
        right_outer.pack(side="left", fill="both", expand=True, padx=(4, 0))
        right_hdr = tk.Label(right_outer,
                             text="  Jouw selectie  (klik om te verwijderen)",
                             font=("Segoe UI", 9, "bold"),
                             bg=self.BORDER, fg=self.SUBTEXT,
                             pady=5, anchor="w")
        right_hdr.pack(fill="x")
        right_frame = tk.Frame(right_outer, bg=self.CARD)
        right_frame.pack(fill="both", expand=True, padx=1, pady=(0, 1))

        # State: orig_idx → {"text": str, "side": "left"|"right", "widget": Frame}
        state = {}
        self._drag_states[slot] = state

        def _make_widget(frame, orig_idx, text, side):
            is_left  = side == "left"
            bg_c     = self.BORDER if is_left else self.ACCENT
            fg_c     = self.TEXT   if is_left else "white"
            arrow    = "→" if is_left else "✕"

            f = tk.Frame(frame, bg=bg_c, cursor="hand2")
            f.pack(fill="x", padx=4, pady=2)

            lbl = tk.Label(f, text=f"  {text}",
                           font=("Segoe UI", 10),
                           bg=bg_c, fg=fg_c,
                           wraplength=185, justify="left",
                           padx=6, pady=7, anchor="w")
            lbl.pack(side="left", fill="x", expand=True)

            arr = tk.Label(f, text=arrow,
                           font=("Segoe UI", 11, "bold"),
                           bg=bg_c, fg=fg_c, padx=8, pady=7)
            arr.pack(side="right")

            hover_bg = "#C8D0E0" if is_left else self.ACCENT_HV

            def _on_enter(e):
                f.config(bg=hover_bg); lbl.config(bg=hover_bg); arr.config(bg=hover_bg)

            def _on_leave(e):
                f.config(bg=bg_c); lbl.config(bg=bg_c); arr.config(bg=bg_c)

            def _on_click(e, oi=orig_idx, t=text, s=side):
                if self.answered_flags[slot]:
                    return
                _move(oi, t, s)

            for w in (f, lbl, arr):
                w.bind("<Enter>", _on_enter)
                w.bind("<Leave>", _on_leave)
                w.bind("<Button-1>", _on_click)

            return f

        def _move(orig_idx, text, current_side):
            if orig_idx in state and state[orig_idx]["widget"].winfo_exists():
                state[orig_idx]["widget"].destroy()

            if current_side == "left":
                w = _make_widget(right_frame, orig_idx, text, "right")
                state[orig_idx] = {"text": text, "side": "right", "widget": w}
            else:
                w = _make_widget(left_frame, orig_idx, text, "left")
                state[orig_idx] = {"text": text, "side": "left", "widget": w}

        for orig_idx, text in indexed:
            w = _make_widget(left_frame, orig_idx, text, "left")
            state[orig_idx] = {"text": text, "side": "left", "widget": w}

        # Confirm button
        cf = tk.Frame(parent, bg=self.ACCENT, cursor="hand2")
        cf.pack(anchor="w", pady=(10, 0))
        cl = tk.Label(cf, text="Bevestig antwoorden",
                      font=("Segoe UI", 11, "bold"),
                      bg=self.ACCENT, fg="white", padx=20, pady=8, cursor="hand2")
        cl.pack()

        def _confirm(e=None, s=slot, _q=q):
            if not self.answered_flags[s]:
                self._confirm_drag_answer(s, _q, right_outer, right_hdr)

        for w in (cf, cl):
            w.bind("<Button-1>", _confirm)
            w.bind("<Enter>", lambda e, f=cf, lb=cl: (f.config(bg=self.ACCENT_HV), lb.config(bg=self.ACCENT_HV)))
            w.bind("<Leave>", lambda e, f=cf, lb=cl: (f.config(bg=self.ACCENT), lb.config(bg=self.ACCENT)))

        lbl_feedback.pack(anchor="w", pady=(10, 0))

    # ──────────────────────────────────────────────────────────────
    # ANSWER HANDLERS
    # ──────────────────────────────────────────────────────────────

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

    def _select_answer(self, idx, q_slot=0):
        if self.answered_flags[q_slot]:
            return
        self.answered_flags[q_slot] = True

        q       = self.questions[self.current + q_slot]
        options = q["options"]
        correct = q["correct"]

        correct_shuffled = next(
            i for i, (orig, _) in enumerate(self._shuffled_options[q_slot])
            if orig == correct)

        is_correct = (idx == correct_shuffled)

        def colour_opt(i, bg, badge_bg, badge_fg, text_fg):
            row, badge, lbl = self.option_buttons[q_slot][i]
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
            self.lbl_feedback[q_slot].config(
                text="  ✓  Correct!", fg=self.CORRECT, bg=self.CORRECT_BG)
        else:
            colour_opt(idx, self.WRONG_BG, self.WRONG, "white", self.WRONG)
            colour_opt(correct_shuffled, self.CORRECT_BG, self.CORRECT, "white", self.CORRECT)
            self.lbl_feedback[q_slot].config(
                text=f"  ✗  Fout.  Juist antwoord: {options[correct]}",
                fg=self.WRONG, bg=self.WRONG_BG)

        for i in range(len(self.option_buttons[q_slot])):
            if i != idx and i != correct_shuffled:
                colour_opt(i, self.CARD, self.BORDER, self.SUBTEXT, self.SUBTEXT)

        self.results.append({
            "question":    q["question"],
            "topic":       q.get("topic", ""),
            "correct":     is_correct,
            "your_answer": self._shuffled_options[q_slot][idx][1],
            "right_answer": options[correct],
        })

        if all(self.answered_flags):
            self._set_next_btn(enabled=True)

    def _confirm_multi(self, slot, q):
        self.answered_flags[slot] = True

        correct_set = set(q["correct"]) if isinstance(q["correct"], list) else {q["correct"]}
        indexed     = self._shuffled_options[slot]
        vars_list   = self._multi_vars[slot]
        slot_btns   = self._slot_buttons_full.get(slot, [])

        selected_orig = {orig for i, (orig, _) in enumerate(indexed) if vars_list[i].get()}
        is_correct    = (selected_orig == correct_set)
        if is_correct:
            self.score += 1

        for i, (orig_idx, _) in enumerate(indexed):
            if i >= len(slot_btns):
                break
            row, badge, lbl, chk = slot_btns[i]
            is_sel = vars_list[i].get()
            is_c   = orig_idx in correct_set

            for widget in (row, badge, lbl, chk):
                widget.unbind("<Button-1>")
                widget.unbind("<Enter>")
                widget.unbind("<Leave>")

            if is_c:
                row.config(bg=self.CORRECT_BG, highlightbackground=self.CORRECT, cursor="")
                badge.config(bg=self.CORRECT, fg="white")
                lbl.config(bg=self.CORRECT_BG, fg=self.CORRECT)
                chk.config(text="☑", bg=self.CORRECT_BG, fg=self.CORRECT)
            elif is_sel:
                row.config(bg=self.WRONG_BG, highlightbackground=self.WRONG, cursor="")
                badge.config(bg=self.WRONG, fg="white")
                lbl.config(bg=self.WRONG_BG, fg=self.WRONG)
                chk.config(text="☑", bg=self.WRONG_BG, fg=self.WRONG)
            else:
                row.config(bg=self.CARD, highlightbackground=self.BORDER, cursor="")
                badge.config(bg=self.BORDER, fg=self.SUBTEXT)
                lbl.config(bg=self.CARD, fg=self.SUBTEXT)
                chk.config(text="☐", bg=self.CARD, fg=self.SUBTEXT)

        if is_correct:
            self.lbl_feedback[slot].config(
                text="  ✓  Alle antwoorden correct!", fg=self.CORRECT, bg=self.CORRECT_BG)
        else:
            correct_texts = [q["options"][i] for i in sorted(correct_set)]
            self.lbl_feedback[slot].config(
                text=f"  ✗  Fout.  Juiste antwoorden: {', '.join(correct_texts)}",
                fg=self.WRONG, bg=self.WRONG_BG)

        your_answers  = [q["options"][orig] for i, (orig, _) in enumerate(indexed)
                         if vars_list[i].get()]
        right_answers = [q["options"][i] for i in sorted(correct_set)]
        self.results.append({
            "question":    q["question"],
            "topic":       q.get("topic", ""),
            "correct":     is_correct,
            "your_answer": ", ".join(your_answers) or "(geen)",
            "right_answer": ", ".join(right_answers),
        })

        if all(self.answered_flags):
            self._set_next_btn(enabled=True)

    def _confirm_drag_answer(self, slot, q, right_outer, right_hdr):
        self.answered_flags[slot] = True
        state = self._drag_states[slot]

        correct_val   = q["correct"]
        correct_set   = set(correct_val) if isinstance(correct_val, list) else {correct_val}
        selected_orig = {oi for oi, info in state.items() if info["side"] == "right"}
        is_correct    = (selected_orig == correct_set)

        if is_correct:
            self.score += 1

        border_c = self.CORRECT if is_correct else self.WRONG
        right_outer.config(bg=border_c)
        right_hdr.config(bg=border_c, fg="white",
                         text=f"  Jouw selectie  {'✓' if is_correct else '✗'}")

        for oi, info in state.items():
            w = info["widget"]
            if not w.winfo_exists():
                continue
            in_correct = oi in correct_set
            on_right   = info["side"] == "right"
            if in_correct and on_right:
                c = self.CORRECT
            elif in_correct:        # missed — still on left
                c = self.WARN
            elif on_right:          # wrong item selected
                c = self.WRONG
            else:
                c = self.SUBTEXT
            try:
                w.config(bg=c, cursor="")
                for child in w.winfo_children():
                    child.config(bg=c)
                for widget in [w] + list(w.winfo_children()):
                    widget.unbind("<Button-1>")
                    widget.unbind("<Enter>")
                    widget.unbind("<Leave>")
            except Exception:
                pass

        if is_correct:
            self.lbl_feedback[slot].config(
                text="  ✓  Correct!", fg=self.CORRECT, bg=self.CORRECT_BG)
        else:
            correct_texts = [q["options"][i] for i in sorted(correct_set)]
            self.lbl_feedback[slot].config(
                text=f"  ✗  Fout.  Juiste antwoorden: {', '.join(correct_texts)}",
                fg=self.WRONG, bg=self.WRONG_BG)

        your_answers  = [q["options"][oi] for oi, info in sorted(state.items())
                         if info["side"] == "right"]
        right_answers = [q["options"][i] for i in sorted(correct_set)]
        self.results.append({
            "question":    q["question"],
            "topic":       q.get("topic", ""),
            "correct":     is_correct,
            "your_answer": ", ".join(your_answers) or "(geen)",
            "right_answer": ", ".join(right_answers),
        })

        if all(self.answered_flags):
            self._set_next_btn(enabled=True)

    def _set_next_btn(self, enabled, text=None):
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
        slots_on_page = min(self.questions_per_screen, self._num_q - self.current)
        self.current += slots_on_page
        if self.current >= self._num_q:
            self._show_results()
        else:
            self._load_question()

    # ──────────────────────────────────────────────────────────────
    # RESULTS SCREEN
    # ──────────────────────────────────────────────────────────────
    def _show_results(self):
        self._clear()

        pct          = round(self.score / self._num_q * 100)
        passed       = pct >= 55
        result_color = self.CORRECT if passed else self.WRONG
        result_bg    = self.CORRECT_BG if passed else self.WRONG_BG
        emoji        = "🏆" if pct >= 80 else ("👍" if passed else "📝")
        status_text  = "Geslaagd!" if passed else "Niet geslaagd – blijf oefenen!"

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
                 text=f"{self.score} / {self._num_q}   ({pct}%)",
                 font=("Segoe UI", 22, "bold"),
                 bg=result_bg, fg=result_color).pack(anchor="w")
        tk.Label(right, text=status_text,
                 font=("Segoe UI", 12),
                 bg=result_bg, fg=result_color).pack(anchor="w")

        tk.Label(self.root,
                 text="Overzicht van jouw antwoorden",
                 font=("Segoe UI", 11, "bold"),
                 bg=self.BG, fg=self.TEXT).pack(
                     anchor="w", padx=30, pady=(16, 4))

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
                           highlightthickness=1, highlightbackground=c)
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

        btn_row = tk.Frame(self.root, bg=self.BG)
        btn_row.pack(pady=14)

        def _make_btn(parent, text, bg, fg, hover_bg, callback):
            f = tk.Frame(parent, bg=bg, cursor="hand2")
            f.pack(side="left", padx=8)
            l = tk.Label(f, text=text, font=("Segoe UI", 12, "bold"),
                         bg=bg, fg=fg, padx=24, pady=11, cursor="hand2")
            l.pack()
            for w in (f, l):
                w.bind("<Enter>",    lambda e, f=f, l=l, c=hover_bg: (f.config(bg=c), l.config(bg=c)))
                w.bind("<Leave>",    lambda e, f=f, l=l, c=bg:       (f.config(bg=c), l.config(bg=c)))
                w.bind("<Button-1>", lambda e, cb=callback: cb())

        _make_btn(btn_row, "Opnieuw spelen  →",
                  self.ACCENT, "white", self.ACCENT_HV,
                  lambda: self._start_quiz(self.active_label, self._question_pool))

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
