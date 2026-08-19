"""
database.py
Handles SQLite database connection, schema creation, and seeding of
course content for TEC - The Learning Platform.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "tec.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    profile_photo TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    letter TEXT NOT NULL,
    description TEXT,
    icon TEXT
);

CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    section_id INTEGER NOT NULL REFERENCES sections(id),
    title TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    description TEXT,
    icon TEXT
);

CREATE TABLE IF NOT EXISTS lessons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL REFERENCES courses(id),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    code_example TEXT,
    image_url TEXT,
    video_url TEXT,
    sort_order INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    lesson_id INTEGER NOT NULL REFERENCES lessons(id),
    completed_at TEXT DEFAULT (datetime('now')),
    UNIQUE(user_id, lesson_id)
);

CREATE TABLE IF NOT EXISTS certificates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    course_id INTEGER NOT NULL REFERENCES courses(id),
    certificate_code TEXT UNIQUE NOT NULL,
    issued_at TEXT DEFAULT (datetime('now')),
    UNIQUE(user_id, course_id)
);

CREATE TABLE IF NOT EXISTS login_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    logged_in_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS page_views (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    visited_at TEXT DEFAULT (datetime('now'))
);
"""


def init_db():
    conn = get_db()
    conn.executescript(SCHEMA)
    conn.commit()
    # Lightweight migration for databases created before a column was added.
    cols = [r["name"] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
    if "profile_photo" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN profile_photo TEXT")
        conn.commit()
    conn.close()


def seeded():
    conn = get_db()
    row = conn.execute("SELECT COUNT(*) c FROM sections").fetchone()
    conn.close()
    return row["c"] > 0


def yt(query):
    return "https://www.youtube.com/results?search_query=" + query.replace(" ", "+")


def seed_db():
    """Populate sections / courses / lessons with TEC content."""
    if seeded():
        return
    conn = get_db()
    cur = conn.cursor()

    sections = [
        ("Trading", "trading", "T", "Master the markets: charts, patterns, forex, crypto & commodities.", "📈"),
        ("Editing", "editing", "E", "Creative editing skills: graphics, video, animation & photo editing.", "🎬"),
        ("Coding", "coding", "C", "Learn programming languages from the ground up.", "💻"),
    ]
    sec_ids = {}
    for name, slug, letter, desc, icon in sections:
        cur.execute(
            "INSERT INTO sections (name, slug, letter, description, icon) VALUES (?,?,?,?,?)",
            (name, slug, letter, desc, icon),
        )
        sec_ids[slug] = cur.lastrowid

    # ---------------- TRADING ----------------
    trading_courses = [
        dict(
            title="Trading Course (Basics)", slug="trading-basics", icon="📊",
            description="A foundational course covering what trading is, market types, and risk management.",
            lessons=[
                ("What is Trading?",
                 "Trading is the act of buying and selling financial instruments — stocks, currencies, "
                 "commodities, or crypto — with the goal of making a profit from price movements. Traders "
                 "differ from long-term investors in that they usually hold positions for shorter periods, "
                 "from minutes (scalping) to weeks (swing trading).",
                 None, "chart_basics.png", yt("what is trading for beginners")),
                ("Types of Markets",
                 "There are four major markets traders participate in: the Stock Market (company shares), "
                 "the Forex Market (currency pairs), the Crypto Market (digital assets), and the Commodities "
                 "Market (gold, oil, agricultural products). Each has its own trading hours, volatility, and "
                 "liquidity characteristics.",
                 None, None, yt("types of financial markets explained")),
                ("Risk Management Basics",
                 "The golden rule of trading is protecting your capital. Key tools include Stop-Loss orders "
                 "(automatically exit a losing trade), Position Sizing (never risk more than 1-2% of your "
                 "account per trade), and a Risk:Reward Ratio (aim for at least 1:2, risking $1 to make $2).",
                 None, None, yt("risk management in trading")),
            ],
        ),
        dict(
            title="Chart Patterns", slug="chart-patterns", icon="📐",
            description="Learn to identify the most reliable chart patterns used by professional traders.",
            lessons=[
                ("Head & Shoulders",
                 "A reversal pattern with three peaks — a higher middle peak (head) between two lower peaks "
                 "(shoulders). It signals a trend reversal from bullish to bearish when price breaks below "
                 "the 'neckline' connecting the two lows.",
                 None, "head_shoulders.png", yt("head and shoulders chart pattern")),
                ("Double Top & Double Bottom",
                 "A Double Top forms two peaks at roughly the same price level and signals a bearish "
                 "reversal. A Double Bottom is the mirror image — two troughs at a similar level — and "
                 "signals a bullish reversal.",
                 None, "double_top_bottom.png", yt("double top double bottom pattern")),
                ("Triangles (Ascending / Descending / Symmetrical)",
                 "Triangles are continuation patterns formed as price consolidates between converging "
                 "trendlines. An Ascending Triangle (flat top, rising bottom) is usually bullish; a "
                 "Descending Triangle is usually bearish; a Symmetrical Triangle can break either way.",
                 None, "triangle.png", yt("triangle chart patterns trading")),
                ("Flags & Pennants",
                 "Short-term continuation patterns that appear after a sharp price move (the 'flagpole'), "
                 "followed by a small consolidation (the 'flag'). A breakout in the direction of the prior "
                 "trend is the typical continuation signal.",
                 None, None, yt("flag and pennant chart pattern")),
            ],
        ),
        dict(
            title="Candlestick Patterns", slug="candlestick-patterns", icon="🕯️",
            description="Understand what individual candles and candle groups reveal about market psychology.",
            lessons=[
                ("Doji",
                 "A Doji forms when the open and close price are almost equal, creating a thin cross-like "
                 "candle. It signals indecision in the market and often precedes a reversal, especially "
                 "after a strong trend.",
                 None, "doji.png", yt("doji candlestick pattern explained")),
                ("Hammer & Hanging Man",
                 "Both have a small body with a long lower wick. A Hammer appears after a downtrend and "
                 "signals a bullish reversal; a Hanging Man appears after an uptrend and signals a possible "
                 "bearish reversal.",
                 None, "hammer.png", yt("hammer candlestick pattern")),
                ("Bullish / Bearish Engulfing",
                 "A two-candle pattern where the second candle's body completely 'engulfs' the first. A "
                 "Bullish Engulfing after a downtrend signals buyers taking control; a Bearish Engulfing "
                 "after an uptrend signals sellers taking control.",
                 None, "engulfing.png", yt("engulfing candlestick pattern")),
                ("Morning Star & Evening Star",
                 "Three-candle reversal patterns. A Morning Star (large bearish candle, small indecisive "
                 "candle, large bullish candle) signals a bullish reversal at the bottom of a downtrend. An "
                 "Evening Star is the bearish mirror image at the top of an uptrend.",
                 None, None, yt("morning star evening star candlestick")),
            ],
        ),
        dict(
            title="Currency Market (Forex)", slug="currency-market", icon="💱",
            description="Introduction to the world's largest financial market — foreign exchange.",
            lessons=[
                ("What is Forex?",
                 "The Foreign Exchange (Forex/FX) market is where currencies are traded against each "
                 "other, 24 hours a day, 5 days a week. It is the largest and most liquid financial market "
                 "in the world, with trillions of dollars traded daily.",
                 None, None, yt("what is forex trading for beginners")),
                ("Major Currency Pairs",
                 "Currencies are traded in pairs, e.g. EUR/USD, GBP/USD, USD/JPY. The 'major pairs' all "
                 "include the US Dollar and are the most heavily traded, offering the tightest spreads and "
                 "highest liquidity.",
                 None, None, yt("major currency pairs forex")),
                ("Pips, Lots & Leverage",
                 "A Pip is the smallest standard price movement in forex (usually 0.0001). A Lot is a "
                 "standardized trade size (Standard = 100,000 units). Leverage lets traders control a large "
                 "position with a small deposit — it magnifies both profit and risk.",
                 None, None, yt("pips lots leverage forex explained")),
            ],
        ),
        dict(
            title="Crypto Market", slug="crypto-market", icon="🪙",
            description="Learn the fundamentals of cryptocurrency trading and blockchain technology.",
            lessons=[
                ("What is Cryptocurrency?",
                 "Cryptocurrency is a digital asset secured by cryptography and typically built on a "
                 "decentralized network called a blockchain. Bitcoin (BTC), launched in 2009, was the "
                 "first and remains the largest cryptocurrency by market cap.",
                 None, None, yt("what is cryptocurrency for beginners")),
                ("Blockchain Basics",
                 "A blockchain is a distributed, tamper-resistant ledger where transactions are grouped "
                 "into 'blocks' and cryptographically linked in a chain. This removes the need for a "
                 "central authority like a bank to verify transactions.",
                 None, None, yt("how does blockchain work")),
                ("Popular Coins & Trading Basics",
                 "Beyond Bitcoin, major coins include Ethereum (ETH — smart contracts), and various "
                 "altcoins. Crypto markets trade 24/7 and are known for high volatility, so risk management "
                 "is even more critical than in traditional markets.",
                 None, None, yt("how to trade cryptocurrency basics")),
            ],
        ),
        dict(
            title="Commodities Market", slug="commodities-market", icon="🛢️",
            description="Explore trading in physical goods — metals, energy, and agriculture.",
            lessons=[
                ("What are Commodities?",
                 "Commodities are raw materials or primary agricultural products that can be bought and "
                 "sold, such as gold, oil, natural gas, and wheat. They are typically traded via futures "
                 "contracts on exchanges.",
                 None, None, yt("what are commodities trading")),
                ("Gold & Silver (Precious Metals)",
                 "Gold and Silver are considered 'safe-haven' assets — investors flock to them during "
                 "economic uncertainty. Gold prices are often inversely correlated with the US Dollar and "
                 "interest rates.",
                 None, None, yt("gold trading for beginners")),
                ("Oil & Energy",
                 "Crude Oil (WTI and Brent) is one of the most actively traded commodities, heavily "
                 "influenced by OPEC decisions, geopolitical events, and global supply-demand balance.",
                 None, None, yt("oil trading basics explained")),
            ],
        ),
    ]

    trading_courses.append(dict(
        title="Trading Roadmap: Step-by-Step Guide", slug="trading-roadmap", icon="🗺️",
        description="A complete 6-step path from market basics to trading psychology — the full journey to becoming a trader.",
        lessons=[
            ("Step 1: Understand Market Basics & Mechanics",
             "Before looking at charts, you need to understand how financial markets operate and "
             "what trading actually is.\n\n"
             "• Trading vs. Investing — trading is short-term speculation on price moves, while "
             "investing is building wealth over the long term.\n"
             "• Asset Classes — the markets you can trade include Stocks, Forex, Cryptocurrencies, "
             "Commodities, and Derivatives such as Futures & Options.\n"
             "• Market Participants & Brokers — orders are routed to the market through a broker; "
             "key terms to know are Bid/Ask price, Spread, and Liquidity.\n"
             "• Order Types — Market Orders (execute immediately), Limit Orders (execute at a set "
             "price), Stop-Loss Orders (exit automatically), and Good-Til-Cancelled (GTC) orders "
             "that stay open until filled or cancelled.",
             None, "chart_basics.png", yt("trading market basics for beginners")),

            ("Step 2: Master Technical Analysis (Reading Charts)",
             "Technical analysis involves studying historical price movements to predict future "
             "direction — critical for short-term trading.\n\n"
             "• Candlestick Charts — read the Open, High, Low, and Close of each candle, and "
             "recognise common patterns like Doji, Hammer, and Engulfing.\n"
             "• Support and Resistance — identify price levels where an asset tends to stop "
             "falling (support) or stop rising (resistance).\n"
             "• Trend Identification — spot uptrends, downtrends, and sideways markets using "
             "trendlines and moving averages.\n"
             "• Technical Indicators — momentum and volume tools such as RSI (Relative Strength "
             "Index), MACD, and Bollinger Bands help filter and confirm signals.",
             None, "engulfing.png", yt("technical analysis trading for beginners")),

            ("Step 3: Learn Fundamental Analysis & Macroeconomics",
             "You need to know what drives the price of an asset beyond just the charts.\n\n"
             "• Economic Indicators — interest rates, inflation data, employment reports, and "
             "central bank policy all move markets.\n"
             "• Company Financials (for Stocks) — understand the basics of Balance Sheets, Income "
             "Statements, and Earnings Reports.\n"
             "• News Sentiment — learn to read breaking financial news and gauge market psychology "
             "and reaction to global events.",
             None, None, yt("fundamental analysis trading macroeconomics")),

            ("Step 4: Develop a Trading Strategy",
             "A strategy stops you from guessing and gives you clear rules for when to enter and "
             "exit.\n\n"
             "• Trading Styles — choose one that fits your schedule: Scalping (dozens of trades in "
             "minutes for tiny gains), Day Trading (open and close within the same day), or Swing "
             "Trading (hold for days or weeks to catch medium-term trends).\n"
             "• Strategy Types — study basic setups such as Trend Following, Breakout Trading, and "
             "Mean Reversion.",
             None, "triangle.png", yt("how to develop a trading strategy")),

            ("Step 5: Master Risk Management",
             "Risk management dictates how long you survive in the market — even the best strategy "
             "will fail without it. This is arguably the most critical step of all.\n\n"
             "• Capital Preservation — never risk more than a small percentage (e.g. 1% to 2%) of "
             "your total trading capital on a single trade.\n"
             "• Risk-to-Reward Ratio — aim for setups where your potential profit is at least 2x or "
             "3x your potential loss (e.g. risking $50 to make $150).\n"
             "• Stop-Loss Discipline — always define your exit point before entering a trade, so "
             "losses are cut automatically if the market moves against you.",
             None, None, yt("risk management for traders")),

            ("Step 6: Trading Psychology & Emotional Control",
             "Greed and fear are a trader's worst enemies — managing your mindset is what separates "
             "profitable traders from losing ones.\n\n"
             "• Emotional Discipline — accept losses gracefully, without revenge trading (trying to "
             "win back lost money immediately).\n"
             "• Patience — wait for high-probability setups instead of forcing trades out of "
             "boredom.\n"
             "• Trading Journal — keep a detailed log of every trade (entry reason, exit, emotion, "
             "and outcome) to review mistakes and refine your edge over time.",
             None, None, yt("trading psychology and discipline")),
        ],
    ))

    # ---------------- EDITING ----------------
    editing_courses = [
        dict(
            title="Graphic Design", slug="graphic-design", icon="🎨",
            description="Core principles behind creating clean, effective visual designs.",
            lessons=[
                ("Design Principles",
                 "Great design rests on core principles: Balance (visual weight distribution), Contrast "
                 "(making elements stand out), Alignment (creating order), Repetition (consistency), and "
                 "Proximity (grouping related items together).",
                 None, None, yt("graphic design principles for beginners")),
                ("Color Theory",
                 "Color theory studies how colors interact. The color wheel groups colors into primary, "
                 "secondary, and tertiary. Complementary colors (opposite on the wheel) create high "
                 "contrast, while analogous colors (next to each other) create harmony.",
                 None, "color_wheel.png", yt("color theory for graphic designers")),
                ("Typography Basics",
                 "Typography is the art of arranging text. Key concepts include Serif vs Sans-Serif fonts, "
                 "Font Pairing (combining 2-3 complementary fonts), Hierarchy (using size/weight to guide "
                 "the eye), and Kerning/Spacing.",
                 None, None, yt("typography basics for beginners")),
            ],
        ),
        dict(
            title="Video Editing", slug="video-editing", icon="🎞️",
            description="Learn the essential workflow and techniques of professional video editing.",
            lessons=[
                ("Video Editing Basics",
                 "Editing is the process of assembling video clips into a final sequence. The core "
                 "workflow is: Import footage → Rough cut (arrange clips) → Fine cut (trim precisely) → "
                 "Add audio/effects → Export.",
                 None, None, yt("video editing basics for beginners")),
                ("Transitions & Effects",
                 "Transitions (cuts, fades, dissolves, wipes) control how one shot moves to the next. Use "
                 "them purposefully — a simple 'cut' is best for most edits, while fades/dissolves suit "
                 "scene or time changes.",
                 None, None, yt("video transitions and effects tutorial")),
                ("Color Grading",
                 "Color grading adjusts a video's color and tone to set mood and ensure visual consistency "
                 "across shots. It involves adjusting exposure, contrast, white balance, and applying a "
                 "stylistic 'look' (e.g. warm, cool, cinematic).",
                 None, None, yt("color grading tutorial for beginners")),
            ],
        ),
        dict(
            title="Animation", slug="animation", icon="🧩",
            description="Understand the fundamentals that bring motion graphics and characters to life.",
            lessons=[
                ("12 Principles of Animation",
                 "Disney animators established 12 principles — including Squash & Stretch, Anticipation, "
                 "Timing, and Follow-Through — that remain the foundation of believable motion in both 2D "
                 "and 3D animation.",
                 None, None, yt("12 principles of animation explained")),
                ("2D vs 3D Animation",
                 "2D animation works in a flat, two-dimensional space (traditional or vector-based, e.g. "
                 "Toon Boom). 3D animation builds and animates models in a three-dimensional space (e.g. "
                 "Blender, Maya) using rigs and keyframes.",
                 None, None, yt("2d vs 3d animation difference")),
                ("Keyframes & Timelines",
                 "A Keyframe marks a specific value (position, rotation, scale) at a point in time. "
                 "Software interpolates the frames between keyframes automatically, which is the basis of "
                 "all digital animation timelines.",
                 None, None, yt("keyframe animation basics")),
            ],
        ),
        dict(
            title="Photo Editing", slug="photo-editing", icon="🖼️",
            description="Techniques for enhancing and retouching photographs professionally.",
            lessons=[
                ("Photo Editing Basics",
                 "Basic edits include adjusting Exposure (brightness), Contrast, White Balance (color "
                 "temperature), and Cropping/Straightening for composition. These form the base layer of "
                 "almost every edit.",
                 None, None, yt("photo editing basics for beginners")),
                ("Retouching Techniques",
                 "Retouching removes blemishes or distractions using tools like the Healing Brush, Clone "
                 "Stamp, and Frequency Separation (for skin smoothing) while preserving natural texture.",
                 None, None, yt("photo retouching tutorial")),
                ("Filters & Presets",
                 "Filters/presets apply a consistent set of adjustments (color grade, contrast curve, "
                 "grain) with one click, useful for maintaining a consistent style across a batch of "
                 "photos.",
                 None, None, yt("photo filters and presets tutorial")),
            ],
        ),
    ]

    # ---------------- CODING ----------------
    coding_courses = [
        dict(title="Java", slug="java", icon="☕",
             description="Object-oriented programming with Java.",
             lessons=[
                 ("Introduction to Java",
                  "Java is a class-based, object-oriented, platform-independent language — code compiles "
                  "to bytecode that runs on the Java Virtual Machine (JVM), following the 'write once, run "
                  "anywhere' philosophy.",
                  'public class Main {\n    public static void main(String[] args) {\n        System.out.println("Hello, TEC!");\n    }\n}',
                  None, yt("java programming for beginners")),
                 ("Variables & Data Types",
                  "Java is statically typed: every variable's type is declared. Primitive types include "
                  "int, double, boolean, and char.",
                  'int age = 20;\ndouble price = 19.99;\nboolean isActive = true;\nString name = "TEC";',
                  None, yt("java variables and data types")),
             ]),
        dict(title="Python", slug="python", icon="🐍",
             description="The versatile, beginner-friendly language behind data science, web, and automation.",
             lessons=[
                 ("Introduction to Python",
                  "Python is a high-level, interpreted language known for readable syntax. It's used in "
                  "web development, data science, automation, and AI.",
                  'print("Hello, TEC!")',
                  None, yt("python programming for beginners")),
                 ("Variables & Functions",
                  "Python is dynamically typed — no need to declare types. Functions are defined with the "
                  "'def' keyword.",
                  'def greet(name):\n    return f"Hello, {name}!"\n\nprint(greet("Trader"))',
                  None, yt("python functions tutorial")),
             ]),
        dict(title="C", slug="c-language", icon="🔧",
             description="The foundational procedural language behind modern computing.",
             lessons=[
                 ("Introduction to C",
                  "C is a low-level, procedural language that gives direct control over memory. It's the "
                  "foundation for operating systems and embedded programming.",
                  '#include <stdio.h>\n\nint main() {\n    printf("Hello, TEC!\\n");\n    return 0;\n}',
                  None, yt("c programming for beginners")),
                 ("Variables & Pointers",
                  "A pointer stores the memory address of another variable, giving C its power for direct "
                  "memory manipulation.",
                  'int age = 20;\nint *p = &age;\nprintf("%d", *p);',
                  None, yt("pointers in c explained")),
             ]),
        dict(title="C++", slug="cpp", icon="➕",
             description="C with object-oriented programming — used in games, systems, and performance apps.",
             lessons=[
                 ("Introduction to C++",
                  "C++ extends C with object-oriented features like classes and objects, while keeping "
                  "low-level performance control.",
                  '#include <iostream>\nusing namespace std;\n\nint main() {\n    cout << "Hello, TEC!";\n    return 0;\n}',
                  None, yt("c++ programming for beginners")),
                 ("Classes & Objects",
                  "A class is a blueprint; an object is an instance of that class, bundling data (members) "
                  "and behavior (methods).",
                  'class Trader {\npublic:\n    string name;\n    void greet() { cout << "Hi " << name; }\n};',
                  None, yt("c++ classes and objects")),
             ]),
        dict(title=".NET (C#)", slug="dotnet", icon="🟣",
             description="Microsoft's framework for building web, desktop, and cloud apps with C#.",
             lessons=[
                 ("Introduction to .NET & C#",
                  ".NET is a free, cross-platform framework from Microsoft. C# is its primary language — "
                  "modern, type-safe, and object-oriented.",
                  'using System;\n\nclass Program {\n    static void Main() {\n        Console.WriteLine("Hello, TEC!");\n    }\n}',
                  None, yt("c# dotnet for beginners")),
                 ("Variables & Methods",
                  "C# methods are declared with a return type, name, and parameters, similar to Java.",
                  'static int Add(int a, int b) {\n    return a + b;\n}',
                  None, yt("c# methods tutorial")),
             ]),
        dict(title="JavaScript", slug="javascript", icon="🟨",
             description="The language of the web — powers interactivity in every modern browser.",
             lessons=[
                 ("Introduction to JavaScript",
                  "JavaScript runs in the browser (and on servers via Node.js) to make web pages "
                  "interactive — handling clicks, animations, and dynamic content.",
                  'console.log("Hello, TEC!");',
                  None, yt("javascript for beginners")),
                 ("Functions & DOM",
                  "Functions in JS can be declared or written as arrow functions. The DOM (Document Object "
                  "Model) lets JS read and modify HTML elements dynamically.",
                  'const greet = (name) => `Hello, ${name}!`;\ndocument.getElementById("demo").innerText = greet("Trader");',
                  None, yt("javascript dom manipulation tutorial")),
             ]),
        dict(title="HTML", slug="html", icon="🌐",
             description="The markup language that structures every web page.",
             lessons=[
                 ("Introduction to HTML",
                  "HTML (HyperText Markup Language) structures web content using nested 'tags' like "
                  "headings, paragraphs, links, and images.",
                  '<!DOCTYPE html>\n<html>\n<body>\n  <h1>Hello, TEC!</h1>\n  <p>Learn to code.</p>\n</body>\n</html>',
                  None, yt("html for beginners")),
                 ("Forms & Links",
                  "Forms collect user input via <input>, <select>, and <button> elements; <a> tags create "
                  "hyperlinks between pages.",
                  '<a href="/courses">View Courses</a>\n<form>\n  <input type="text" placeholder="Your name">\n</form>',
                  None, yt("html forms tutorial")),
             ]),
        dict(title="CSS", slug="css", icon="🎨",
             description="The styling language that controls layout, color, and design on the web.",
             lessons=[
                 ("Introduction to CSS",
                  "CSS (Cascading Style Sheets) styles HTML — controlling color, spacing, fonts, and "
                  "layout. Selectors target elements, and properties define their appearance.",
                  'body {\n  background-color: #E0F7FA;\n  font-family: sans-serif;\n}',
                  None, yt("css for beginners")),
                 ("Flexbox Layout",
                  "Flexbox is a one-dimensional layout system that makes it easy to align and distribute "
                  "space among items in a container.",
                  '.container {\n  display: flex;\n  justify-content: center;\n  align-items: center;\n}',
                  None, yt("css flexbox tutorial")),
             ]),
    ]

    def insert_course(section_slug, c):
        cur.execute(
            "INSERT INTO courses (section_id, title, slug, description, icon) VALUES (?,?,?,?,?)",
            (sec_ids[section_slug], c["title"], c["slug"], c["description"], c["icon"]),
        )
        course_id = cur.lastrowid
        for i, (title, content, code, image, video) in enumerate(c["lessons"]):
            cur.execute(
                """INSERT INTO lessons (course_id, title, content, code_example, image_url, video_url, sort_order)
                   VALUES (?,?,?,?,?,?,?)""",
                (course_id, title, content, code, image, video, i),
            )

    for c in trading_courses:
        insert_course("trading", c)
    for c in editing_courses:
        insert_course("editing", c)
    for c in coding_courses:
        insert_course("coding", c)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    seed_db()
    print("Database initialized and seeded at", DB_PATH)
