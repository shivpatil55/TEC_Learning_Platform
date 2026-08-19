"""
generate_images.py
Generates simple, clean illustrative images for chart patterns and
candlestick patterns used in the Trading section lessons.
Run once: python3 generate_images.py
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import os

OUT = os.path.join(os.path.dirname(__file__), "static", "images")
os.makedirs(OUT, exist_ok=True)

BLUE = "#0288D1"
GREEN = "#2E7D32"
RED = "#C62828"
GRID = "#B3E5FC"


def base_ax(figsize=(6, 3.2)):
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_facecolor("#F0FAFF")
    fig.patch.set_facecolor("white")
    ax.grid(color=GRID, linewidth=0.6)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color("#81D4FA")
    return fig, ax


def save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, name), dpi=140)
    plt.close(fig)


def chart_basics():
    fig, ax = base_ax()
    x = np.linspace(0, 10, 100)
    y = np.cumsum(np.random.randn(100)) + 20
    ax.plot(x, y, color=BLUE, linewidth=2)
    ax.set_title("Example Price Chart", color="#01579B")
    save(fig, "chart_basics.png")


def head_shoulders():
    fig, ax = base_ax()
    x = np.linspace(0, 10, 200)
    y = (10 + 2*np.exp(-((x-2)**2)/0.3) + 3.5*np.exp(-((x-5)**2)/0.3)
         + 2*np.exp(-((x-8)**2)/0.3) + x*0.1)
    ax.plot(x, y, color=BLUE, linewidth=2)
    ax.axhline(11.2, color=RED, linestyle="--", linewidth=1.2, label="Neckline")
    ax.legend(loc="upper left", frameon=False)
    ax.set_title("Head & Shoulders Pattern", color="#01579B")
    save(fig, "head_shoulders.png")


def double_top_bottom():
    fig, ax = base_ax()
    x = np.linspace(0, 10, 200)
    y = 10 + 3*np.exp(-((x-3)**2)/0.4) + 3*np.exp(-((x-7)**2)/0.4)
    ax.plot(x, y, color=BLUE, linewidth=2)
    ax.axhline(10.3, color=RED, linestyle="--", linewidth=1.2, label="Support")
    ax.legend(loc="upper left", frameon=False)
    ax.set_title("Double Top Pattern", color="#01579B")
    save(fig, "double_top_bottom.png")


def triangle():
    fig, ax = base_ax()
    x = np.linspace(0, 10, 10)
    top = 15 - x*0.3
    bottom = 8 + x*0.3
    ax.plot(x, top, color=RED, linewidth=1.5, linestyle="--")
    ax.plot(x, bottom, color=GREEN, linewidth=1.5, linestyle="--")
    zig = 8 + x*0.3 + np.abs(np.sin(x*1.5))*(top-bottom)*0.5
    ax.plot(x, zig, color=BLUE, linewidth=2)
    ax.set_title("Symmetrical Triangle Pattern", color="#01579B")
    save(fig, "triangle.png")


def candle(ax, x, o, c, h, l, width=0.4):
    color = GREEN if c >= o else RED
    ax.plot([x, x], [l, h], color=color, linewidth=1.2)
    bottom = min(o, c)
    height = max(abs(c - o), 0.05)
    ax.add_patch(plt.Rectangle((x - width/2, bottom), width, height, color=color))


def doji():
    fig, ax = base_ax((4, 3.2))
    candle(ax, 1, 10, 10.05, 11.5, 8.5)
    ax.set_xlim(0, 2)
    ax.set_ylim(8, 12)
    ax.set_title("Doji Candlestick", color="#01579B")
    save(fig, "doji.png")


def hammer():
    fig, ax = base_ax((4, 3.2))
    candle(ax, 1, 10.8, 11, 11.2, 8.5)
    ax.set_xlim(0, 2)
    ax.set_ylim(8, 12)
    ax.set_title("Hammer Candlestick", color="#01579B")
    save(fig, "hammer.png")


def engulfing():
    fig, ax = base_ax((4, 3.2))
    candle(ax, 1, 11, 10.3, 11.1, 10.2)
    candle(ax, 1.6, 10.1, 11.3, 11.4, 10.0)
    ax.set_xlim(0, 2.6)
    ax.set_ylim(9.8, 11.6)
    ax.set_title("Bullish Engulfing", color="#01579B")
    save(fig, "engulfing.png")


def color_wheel():
    fig, ax = plt.subplots(figsize=(4, 4), subplot_kw={"projection": "polar"})
    fig.patch.set_facecolor("white")
    n = 12
    theta = np.linspace(0, 2*np.pi, n, endpoint=False)
    colors = plt.cm.hsv(np.linspace(0, 1, n))
    ax.bar(theta, np.ones(n), width=2*np.pi/n, color=colors, edgecolor="white")
    ax.set_yticks([])
    ax.set_xticks([])
    ax.set_title("Color Wheel", color="#01579B", pad=15)
    save(fig, "color_wheel.png")


if __name__ == "__main__":
    np.random.seed(7)
    chart_basics()
    head_shoulders()
    double_top_bottom()
    triangle()
    doji()
    hammer()
    engulfing()
    color_wheel()
    print("Images generated in", OUT)
