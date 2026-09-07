import json
import os
import sqlite3
import threading
import urllib.error
import urllib.request
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

APP_NAME = "CreatorAI Studio"
MODEL = "qwen3:0.6b-q4_K_M"
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"

DATA_DIR = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
    "CreatorAI"
)

DB_PATH = os.path.join(DATA_DIR, "creatorai.db")

os.makedirs(DATA_DIR, exist_ok=True)


# -------------------------------------------------
# DATABASE
# -------------------------------------------------

def database():
    return sqlite3.connect(DB_PATH)


def initialize_database():
    con = database()

    con.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            niche TEXT,
            content TEXT,
            created_at TEXT NOT NULL
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS calendar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_title TEXT,
            publish_date TEXT,
            status TEXT
        )
    """)

    con.commit()
    con.close()


def save_project(title, niche, content):
    con = database()

    con.execute(
        """
        INSERT INTO projects
        (title, niche, content, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            title,
            niche,
            content,
            datetime.now().strftime("%Y-%m-%d %H:%M")
        )
    )

    con.commit()
    con.close()


def projects():
    con = database()

    rows = con.execute(
        """
        SELECT id, title, niche, content, created_at
        FROM projects
        ORDER BY id DESC
        """
    ).fetchall()

    con.close()

    return rows


def add_calendar_item(title, date, status):
    con = database()

    con.execute(
        """
        INSERT INTO calendar
        (video_title, publish_date, status)
        VALUES (?, ?, ?)
        """,
        (title, date, status)
    )

    con.commit()
    con.close()


def calendar_items():
    con = database()

    rows = con.execute(
        """
        SELECT video_title, publish_date, status
        FROM calendar
        ORDER BY publish_date
        """
    ).fetchall()

    con.close()

    return rows


# -------------------------------------------------
# LOCAL AI
# -------------------------------------------------

def ask_ai(prompt):
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are CreatorAI Studio, a professional YouTube "
                    "content assistant. Create useful, engaging and "
                    "original content. Never invent statistics or claims "
                    "that are presented as facts."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": False,
        "options": {
            "temperature": 0.8,
            "num_predict": 1200,
            "num_ctx": 4096
        }
    }

    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json"
        }
    )

    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            result = json.loads(
                response.read().decode("utf-8")
            )

            return result["message"]["content"]

    except urllib.error.URLError:
        return (
            "CreatorAI cannot connect to Ollama.\n\n"
            "Please make sure Ollama is installed and running, "
            "and that the Qwen3 0.6B model is installed."
        )

    except Exception as error:
        return f"AI error:\n{error}"


# -------------------------------------------------
# APPLICATION
# -------------------------------------------------

class CreatorAI(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title(APP_NAME)
        self.geometry("1200x760")
        self.minsize(950, 620)
        self.configure(bg="#0F172A")

        self.current_output = None

        self.setup_styles()
        self.create_interface()
        self.dashboard()

    # -------------------------------------------------
    # STYLE
    # -------------------------------------------------

    def setup_styles(self):

        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "TButton",
            font=("Segoe UI", 10, "bold"),
            padding=9
        )

        style.configure(
            "Title.TLabel",
            background="#0F172A",
            foreground="#FFFFFF",
            font=("Segoe UI", 25, "bold")
        )

        style.configure(
            "Subtitle.TLabel",
            background="#0F172A",
            foreground="#94A3B8",
            font=("Segoe UI", 11)
        )

    # -------------------------------------------------
    # INTERFACE
    # -------------------------------------------------

    def create_interface(self):

        sidebar = tk.Frame(
            self,
            bg="#020617",
            width=235
        )

        sidebar.pack(
            side="left",
            fill="y"
        )

        sidebar.pack_propagate(False)

        tk.Label(
            sidebar,
            text="✦ CreatorAI",
            bg="#020617",
            fg="#A78BFA",
            font=("Segoe UI", 22, "bold")
        ).pack(pady=(28, 8))

        tk.Label(
            sidebar,
            text="YouTube Creator Studio",
            bg="#020617",
            fg="#64748B",
            font=("Segoe UI", 9)
        ).pack(pady=(0, 25))

        self.navigation(
            sidebar,
            "Dashboard",
            self.dashboard
        )

        self.navigation(
            sidebar,
            "💡  AI Ideas",
            self.ideas
        )

        self.navigation(
            sidebar,
            "🔎  Research",
            self.research
        )

        self.navigation(
            sidebar,
            "🧩  Outline",
            self.outline
        )

        self.navigation(
            sidebar,
            "📝  Script Writer",
            self.script
        )

        self.navigation(
            sidebar,
            "🎯  Titles",
            self.titles
        )

        self.navigation(
            sidebar,
            "📄  Description",
            self.description
        )

        self.navigation(
            sidebar,
            "🖼️  Thumbnail",
            self.thumbnail
        )

        self.navigation(
            sidebar,
            "📅  Calendar",
            self.calendar
        )

        self.navigation(
            sidebar,
            "📁  Projects",
            self.project_list
        )

        self.main = tk.Frame(
            self,
            bg="#0F172A"
        )

        self.main.pack(
            side="left",
            fill="both",
            expand=True
        )

    def navigation(self, parent, text, command):

        button = tk.Button(
            parent,
            text=text,
            command=command,
            bg="#020617",
            fg="#CBD5E1",
            activebackground="#312E81",
            activeforeground="#FFFFFF",
            relief="flat",
            anchor="w",
            padx=22,
            pady=10,
            font=("Segoe UI", 10)
        )

        button.pack(fill="x")

    # -------------------------------------------------
    # HELPERS
    # -------------------------------------------------

    def clear(self):

        for widget in self.main.winfo_children():
            widget.destroy()

        self.current_output = None

    def header(self, title, subtitle):

        tk.Label(
            self.main,
            text=title,
            bg="#0F172A",
            fg="#FFFFFF",
            font=("Segoe UI", 25, "bold")
        ).pack(
            anchor="w",
            padx=35,
            pady=(30, 5)
        )

        tk.Label(
            self.main,
            text=subtitle,
            bg="#0F172A",
            fg="#94A3B8",
            font=("Segoe UI", 11)
        ).pack(
            anchor="w",
            padx=35,
            pady=(0, 18)
        )

    def entry(self, default=""):

        box = tk.Entry(
            self.main,
            bg="#1E293B",
            fg="#FFFFFF",
            insertbackground="#FFFFFF",
            relief="flat",
            font=("Segoe UI", 12)
        )

        box.pack(
            fill="x",
            padx=35,
            pady=8,
            ipady=9
        )

        if default:
            box.insert(0, default)

        return box

    def output(self):

        box = tk.Text(
            self.main,
            bg="#1E293B",
            fg="#E2E8F0",
            insertbackground="#FFFFFF",
            selectbackground="#4C1D95",
            relief="flat",
            wrap="word",
            font=("Consolas", 10)
        )

        box.pack(
            fill="both",
            expand=True,
            padx=35,
            pady=10
        )

        self.current_output = box

        return box

    def button_row(self):

        frame = tk.Frame(
            self.main,
            bg="#0F172A"
        )

        frame.pack(
            fill="x",
            padx=35,
            pady=5
        )

        return frame

    def generate(self, prompt, output):

        output.delete("1.0", "end")
        output.insert(
            "1.0",
            "CreatorAI is working...\n\n"
        )

        def worker():

            result = ask_ai(prompt)

            self.after(
                0,
                lambda: self.finish_generation(
                    output,
                    result
                )
            )

        threading.Thread(
            target=worker,
            daemon=True
        ).start()

    def finish_generation(self, output, result):

        output.delete(
            "1.0",
            "end"
        )

        output.insert(
            "1.0",
            result
        )

    def copy_output(self):

        if not self.current_output:
            return

        text = self.current_output.get(
            "1.0",
            "end"
        ).strip()

        if text:

            self.clipboard_clear()
            self.clipboard_append(text)

            messagebox.showinfo(
                "CreatorAI",
                "Copied to clipboard."
            )

    def export_output(self):

        if not self.current_output:
            return

        text = self.current_output.get(
            "1.0",
            "end"
        ).strip()

        if not text:
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )

        if filename:

            with open(
                filename,
                "w",
                encoding="utf-8"
            ) as file:

                file.write(text)

            messagebox.showinfo(
                "CreatorAI",
                "Export complete."
            )

    # -------------------------------------------------
    # DASHBOARD
    # -------------------------------------------------

    def dashboard(self):

        self.clear()

        self.header(
            "Welcome to CreatorAI Studio",
            "Create YouTube content from idea to publishing."
        )

        cards = [
            ("💡", "Ideas", "Find your next video"),
            ("📝", "Scripts", "Write complete scripts"),
            ("🎯", "Titles", "Create strong titles"),
            ("🖼️", "Thumbnails", "Plan thumbnail designs")
        ]

        row = tk.Frame(
            self.main,
            bg="#0F172A"
        )

        row.pack(
            fill="x",
            padx=28
        )

        for icon, title, description in cards:

            card = tk.Frame(
                row,
                bg="#1E293B",
                height=145
            )

            card.pack(
                side="left",
                fill="both",
                expand=True,
                padx=7
            )

            tk.Label(
                card,
                text=icon,
                bg="#1E293B",
                fg="#FFFFFF",
                font=("Segoe UI", 25)
            ).pack(pady=(18, 5))

            tk.Label(
                card,
                text=title,
                bg="#1E293B",
                fg="#FFFFFF",
                font=("Segoe UI", 12, "bold")
            ).pack()

            tk.Label(
                card,
                text=description,
                bg="#1E293B",
                fg="#94A3B8"
            ).pack(pady=5)

        tk.Label(
            self.main,
            text="● LOCAL AI",
            bg="#0F172A",
            fg="#34D399",
            font=("Segoe UI", 11, "bold")
        ).pack(
            anchor="w",
            padx=35,
            pady=(40, 5)
        )

        tk.Label(
            self.main,
            text=(
                "Your CreatorAI projects are stored on your computer. "
                "AI generation uses your local Ollama installation."
            ),
            bg="#0F172A",
            fg="#94A3B8",
            font=("Segoe UI", 10)
        ).pack(
            anchor="w",
            padx=35
        )

    # -------------------------------------------------
    # IDEAS
    # -------------------------------------------------

    def ideas(self):

        self.clear()

        self.header(
            "AI Video Ideas",
            "Generate ideas based on your niche, audience and goal."
        )

        niche = self.entry(
            "Technology"
        )

        output = self.output()

        buttons = self.button_row()

        ttk.Button(
            buttons,
            text="Generate 15 Ideas",
            command=lambda: self.generate(
                f"""
Generate 15 YouTube video ideas for the niche:

{niche.get()}

For each idea provide:
1. Title
2. Viewer problem or desire
3. Why someone would click
4. Suggested video format

Make the ideas diverse and realistic.
""",
                output
            )
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            buttons,
            text="Copy",
            command=self.copy_output
        ).pack(side="left", padx=8)

        ttk.Button(
            buttons,
            text="Export",
            command=self.export_output
        ).pack(side="left", padx=8)

    # -------------------------------------------------
    # RESEARCH
    # -------------------------------------------------

    def research(self):

        self.clear()

        self.header(
            "Research Assistant",
            "Build a research checklist and factual content plan."
        )

        topic = self.entry(
            "Enter your video topic"
        )

        output = self.output()

        buttons = self.button_row()

        ttk.Button(
            buttons,
            text="Create Research Plan",
            command=lambda: self.generate(
                f"""
Create a research plan for a YouTube video about:

{topic.get()}

Provide:
- Key questions to answer
- Important concepts
- Facts that should be verified
- Possible sources to investigate
- Viewer questions
- Common misconceptions
- Suggested structure

Do not invent facts.
""",
                output
            )
        ).pack(side="left")

    # -------------------------------------------------
    # OUTLINE
    # -------------------------------------------------

    def outline(self):

        self.clear()

        self.header(
            "Video Outline",
            "Turn an idea into a strong structure before writing."
        )

        topic = self.entry(
            "Enter video topic"
        )

        output = self.output()

        buttons = self.button_row()

        ttk.Button(
            buttons,
            text="Create Outline",
            command=lambda: self.generate(
                f"""
Create a YouTube video outline for:

{topic.get()}

Include:
- Hook
- Introduction
- 5-8 main sections
- Key points under every section
- Pattern interrupts
- Conclusion
- Call to action

Make the pacing engaging.
""",
                output
            )
        ).pack(side="left")

    # -------------------------------------------------
    # SCRIPT
    # -------------------------------------------------

    def script(self):

        self.clear()

        self.header(
            "AI Script Writer",
            "Create a complete YouTube script."
        )

        topic = self.entry(
            "Enter video topic"
        )

        output = self.output()

        buttons = self.button_row()

        ttk.Button(
            buttons,
            text="Write Script",
            command=lambda: self.generate(
                f"""
Write a complete YouTube script about:

{topic.get()}

Use this structure:

HOOK
INTRO
MAIN CONTENT
EXAMPLES
TRANSITIONS
CONCLUSION
CALL TO ACTION

Style:
- Natural spoken language
- Strong opening
- Short paragraphs
- Engaging pacing
- Useful information
- No fake statistics
- No unnecessary filler
""",
                output
            )
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            buttons,
            text="Copy",
            command=self.copy_output
        ).pack(side="left", padx=8)

        ttk.Button(
            buttons,
            text="Export",
            command=self.export_output
        ).pack(side="left", padx=8)

    # -------------------------------------------------
    # TITLES
    # -------------------------------------------------

    def titles(self):

        self.clear()

        self.header(
            "YouTube Title Generator",
            "Generate different title angles for the same video."
        )

        topic = self.entry(
            "Enter video topic"
        )

        output = self.output()

        buttons = self.button_row()

        ttk.Button(
            buttons,
            text="Generate Titles",
            command=lambda: self.generate(
                f"""
Generate 25 YouTube title options for:

{topic.get()}

Create different styles:
- Curiosity
- Benefit
- Number-based
- Beginner
- Story
- Mistake
- Challenge
- Contrarian

Avoid misleading clickbait.
""",
                output
            )
        ).pack(side="left")

    # -------------------------------------------------
    # DESCRIPTION
    # -------------------------------------------------

    def description(self):

        self.clear()

        self.header(
            "YouTube Description",
            "Create a complete publishing package."
        )

        topic = self.entry(
            "Enter video topic"
        )

        output = self.output()

        buttons = self.button_row()

        ttk.Button(
            buttons,
            text="Generate Package",
            command=lambda: self.generate(
                f"""
Create a YouTube publishing package for:

{topic.get()}

Include:

1. Video description
2. 15 relevant keywords
3. 10 hashtags
4. Suggested chapters
5. Call to action
6. Pinned-comment idea

Keep it natural and avoid keyword stuffing.
""",
                output
            )
        ).pack(side="left")

    # -------------------------------------------------
    # THUMBNAIL
    # -------------------------------------------------

    def thumbnail(self):

        self.clear()

        self.header(
            "Thumbnail Studio",
            "Create a professional thumbnail plan without heavy image AI."
        )

        topic = self.entry(
            "Enter video topic"
        )

        output = self.output()

        buttons = self.button_row()

        ttk.Button(
            buttons,
            text="Create Thumbnail Plan",
            command=lambda: self.generate(
                f"""
Design a high-click-potential YouTube thumbnail concept for:

{topic.get()}

Provide:

1. Main thumbnail text
2. Secondary text if needed
3. Background concept
4. Main subject
5. Facial expression or emotion
6. Color palette
7. Composition
8. Lighting
9. Objects/visual elements
10. What should NOT be included
11. A short image-generation description

Keep thumbnail text extremely short.
Design for mobile viewing.
Do not use misleading imagery.
""",
                output
            )
        ).pack(side="left")

    # -------------------------------------------------
    # CALENDAR
    # -------------------------------------------------

    def calendar(self):

        self.clear()

        self.header(
            "Content Calendar",
            "Plan your upcoming YouTube videos."
        )

        form = tk.Frame(
            self.main,
            bg="#0F172A"
        )

        form.pack(
            fill="x",
            padx=35
        )

        tk.Label(
            form,
            text="Video title",
            bg="#0F172A",
            fg="#CBD5E1"
        ).grid(row=0, column=0, sticky="w")

        title = tk.Entry(
            form,
            bg="#1E293B",
            fg="white",
            insertbackground="white",
            relief="flat"
        )

        title.grid(
            row=1,
            column=0,
            padx=(0, 10),
            pady=5,
            ipadx=80,
            ipady=7
        )

        tk.Label(
            form,
            text="Date (YYYY-MM-DD)",
            bg="#0F172A",
            fg="#CBD5E1"
        ).grid(row=0, column=1, sticky="w")

        date = tk.Entry(
            form,
            bg="#1E293B",
            fg="white",
            insertbackground="white",
            relief="flat"
        )

        date.grid(
            row=1,
            column=1,
            padx=10,
            pady=5,
            ipady=7
        )

        def add():

            if not title.get().strip():
                return

            add_calendar_item(
                title.get(),
                date.get(),
                "Planned"
            )

            title.delete(0, "end")
            date.delete(0, "end")

            self.calendar()

        ttk.Button(
            form,
            text="Add Video",
            command=add
        ).grid(
            row=1,
            column=2,
            padx=10
        )

        items = calendar_items()

        for video_title, publish_date, status in items:

            tk.Label(
                self.main,
                text=f"{publish_date}   |   {status}   |   {video_title}",
                bg="#1E293B",
                fg="#E2E8F0",
                anchor="w",
                padx=15,
                pady=10
            ).pack(
                fill="x",
                padx=35,
                pady=4
            )

    # -------------------------------------------------
    # PROJECTS
    # -------------------------------------------------

    def project_list(self):

        self.clear()

        self.header(
            "Saved Projects",
            "Your projects are stored locally on this computer."
        )

        rows = projects()

        if not rows:

            tk.Label(
                self.main,
                text="No projects saved yet.",
                bg="#0F172A",
                fg="#94A3B8"
            ).pack(
                anchor="w",
                padx=35
            )

            return

        for project_id, title, niche, content, created in rows:

            frame = tk.Frame(
                self.main,
                bg="#1E293B"
            )

            frame.pack(
                fill="x",
                padx=35,
                pady=4
            )

            tk.Label(
                frame,
                text=title,
                bg="#1E293B",
                fg="#FFFFFF",
                font=("Segoe UI", 11, "bold")
            ).pack(
                side="left",
                padx=15,
                pady=12
            )

            tk.Label(
                frame,
                text=created,
                bg="#1E293B",
                fg="#64748B"
            ).pack(
                side="right",
                padx=15
            )


# -------------------------------------------------
# START
# -------------------------------------------------

if __name__ == "__main__":

    initialize_database()

    app = CreatorAI()

    app.mainloop()
