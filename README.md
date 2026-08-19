# TEC — The Learning Platform

**T**rading · **E**diting · **C**oding — a Flask + SQLite learning platform.

## Features
- Sign-up / Login (passwords hashed with Werkzeug)
- Three learning sections:
  - **Trading**: Trading Basics, Chart Patterns, Candlestick Patterns, Currency Market (Forex),
    Crypto Market, Commodities, and a full 6-step Trading Roadmap — with chart images and video
    links for every topic.
  - **Editing**: Graphic Design, Video Editing, Animation, Photo Editing.
  - **Coding**: Java, Python, C, C++, .NET (C#), JavaScript, HTML, CSS — each with a working
    code example.
- Progress tracking per lesson, stored in SQLite (`progress` table).
- Auto-generated PDF **certificate** (name pulled from the user's sign-up record) once every
  lesson in a course is completed.
- User **profile page**: career path (ongoing vs completed courses) and a certificate shelf.
- Sky-blue & white theme with a **Day / Night mode** toggle (saved in the browser).

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

The SQLite database (`tec.db`) and all course/lesson content are created and seeded
automatically the first time you run `app.py`.

## Project structure
```
tec_platform/
├── app.py                 # Flask routes (auth, courses, lessons, certificates, profile)
├── database.py             # SQLite schema + course/lesson seed data
├── generate_images.py      # (already run) generates chart/candlestick illustration images
├── requirements.txt
├── static/
│   ├── css/style.css       # Sky-blue/white theme + night mode
│   ├── js/theme.js         # Theme toggle logic
│   └── images/             # Generated chart pattern illustrations
└── templates/              # Jinja2 templates (base, index, signup, login, dashboard,
                             #  section, course, lesson, profile)
```

## What's new
- **Profile photo upload** — from the Profile page, click the small camera icon on your avatar to upload a PNG/JPG/GIF/WEBP photo (max 4 MB). It appears in the navbar and on your profile.
- **Redesigned certificate** — the PDF certificate now has a bordered frame with gold accents, a TEC monogram seal, letter-spaced heading, decorative dividers, a wax-style seal, and signature/date lines — properly centred and aligned.
- **Trading Roadmap course** — a new 6-lesson course under Trading ("Trading Roadmap: Step-by-Step Guide") covering: Market Basics & Mechanics, Technical Analysis, Fundamental Analysis & Macroeconomics, Strategy Development, Risk Management, and Trading Psychology.
- **Site-wide video background** — a looping background video (`static/videos/site-bg.mp4`, web-optimized to ~2.3MB) now plays behind every page of the site (not just the homepage), fixed in place while you scroll. A poster fallback image shows instantly while it loads. All page content sits on a translucent, blurred "glass" panel (`.container` / navbar) so text stays readable over the video in both day and night mode. You can adjust how much video shows through by tweaking the opacity values in `.container`, `.navbar`, and `.site-bg-overlay` in `static/css/style.css`.
- **QR code on certificates** — every certificate PDF now includes a scannable QR code next to the Certificate ID. Scanning it opens a public verification page (`/verify/<code>`, no login required) showing the certificate holder's name, course, and issue date — useful for employers/recruiters to confirm a certificate is genuine. The QR code encodes `TEC_SITE_URL` + `/verify/<code>`; set the `TEC_SITE_URL` environment variable (e.g. on Render: Settings → Environment) to your real domain once you have one, otherwise it defaults to the `.onrender.com` URL.
- **Admin dashboard** (`/admin`) — a password-protected page showing: total users, total logins, homepage visits, lessons completed platform-wide, certificates issued, a 14-day chart of new signups vs. logins, and a full table of every user with their join date, last login time, total login count, lessons completed, courses completed (hover to see which), and courses currently in progress. Log in at `/admin/login` — the password defaults to `changeme123`, **change this immediately** by setting the `TEC_ADMIN_PASSWORD` environment variable (Render: Settings → Environment → add `TEC_ADMIN_PASSWORD` with a strong password of your choice).

## Notes
- Video links currently point to a YouTube search results page for each topic (since a live
  network connection is needed to fetch and verify individual video IDs). You can swap the
  `video_url` values in `database.py` for specific video links of your choice, then delete
  `tec.db` and restart the app to reseed.
- To add more lessons/courses, edit the `trading_courses` / `editing_courses` / `coding_courses`
  lists in `database.py`, delete `tec.db`, and restart.
