"""Малює схеми для звіту: схема багатоканальної СМО, граф станів, блок-схеми алгоритмів."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Ellipse, FancyBboxPatch, Polygon, Rectangle

FIG = "figures/"
K = dict(color="black", lw=1.2)


def arrow(ax, x0, y0, x1, y1, head=True):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle="-|>" if head else "-", color="black", lw=1.2, shrinkA=0, shrinkB=0))


def line(ax, pts):
    ax.plot([p[0] for p in pts], [p[1] for p in pts], **K)





def scheme():
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 8.4)
    ax.set_aspect("equal")
    ax.axis("off")
    arrow(ax, 0.2, 4.2, 1.7, 4.2)
    ax.text(0.9, 4.55, r"$\lambda$", fontsize=14, ha="center")
    ax.add_patch(Rectangle((1.7, 3.7), 2.0, 1.0, fill=False, lw=1.4))
    for i in range(1, 8):
        ax.plot([1.7 + i * 0.25] * 2, [3.7, 4.7], color="black", lw=1)
    ax.text(2.7, 5.0, "спільна черга\n(необмежена)", ha="center", fontsize=9)
    ys = [7.2, 5.7, 4.2, 2.7, 1.2]
    line(ax, [(3.7, 4.2), (4.6, 4.2)])
    line(ax, [(4.6, ys[0]), (4.6, ys[-1])])
    for i, y in enumerate(ys):
        arrow(ax, 4.6, y, 5.6, y)
        ax.add_patch(Circle((6.2, y), 0.6, fill=False, lw=1.4))
        ax.text(6.2, y, f"K{i + 1}", ha="center", va="center", fontsize=11)
        ax.text(6.95, y + 0.55, r"$\mu$", fontsize=12)
        ax.text(5.0, y + 0.12, r"$1/c$", fontsize=8)
        line(ax, [(6.8, y), (8.1, y)])
    line(ax, [(8.1, ys[0]), (8.1, ys[-1])])
    arrow(ax, 8.1, 4.2, 9.6, 4.2)
    ax.text(9.9, 4.2, r"$\mu_{заг}=c\mu$", fontsize=12, va="center")
    ax.set_title("Схема багатоканальної СМО касової зони (c = 5, необмежена спільна черга)", fontsize=10)
    plt.tight_layout()
    plt.savefig(FIG + "scheme_smo.png", dpi=150)
    plt.close()




def states():
    fig, ax = plt.subplots(figsize=(10, 2.9))
    ax.set_xlim(-0.2, 12.4)
    ax.set_ylim(0, 3.3)
    ax.axis("off")
    n = 9                                    
    xs = [0.4 + 1.25 * i for i in range(n)]
    labels = [f"$S_{i}$" for i in range(n)]
    for x, lb in zip(xs, labels):
        ax.add_patch(Rectangle((x - 0.4, 1.6), 0.8, 0.8, fill=False, lw=1.3))
        ax.text(x, 2.0, lb, ha="center", va="center", fontsize=11)
    mus = [r"$\mu$", r"$2\mu$", r"$3\mu$", r"$4\mu$", r"$5\mu$", r"$5\mu$", r"$5\mu$", r"$5\mu$"]
    for i in range(n - 1):
        arrow(ax, xs[i] + 0.4, 2.25, xs[i + 1] - 0.4, 2.25)
        arrow(ax, xs[i + 1] - 0.4, 1.75, xs[i] + 0.4, 1.75)
        ax.text((xs[i] + xs[i + 1]) / 2, 2.45, r"$\lambda$", ha="center", fontsize=11)
        ax.text((xs[i] + xs[i + 1]) / 2, 1.2, mus[i], ha="center", fontsize=11)
    ax.text(xs[-1] + 0.95, 2.0, r"$\ldots$", fontsize=16, ha="center", va="center")
    
    ax.annotate("", xy=(xs[0] - 0.45, 0.8), xytext=(xs[5] + 0.45, 0.8), arrowprops=dict(arrowstyle="-", lw=1.3))
    ax.text((xs[0] + xs[5]) / 2, 0.35, "черги немає, зайнято k кас (k ≤ 5)", ha="center", fontsize=9)
    ax.annotate("", xy=(xs[6] - 0.45, 0.8), xytext=(xs[-1] + 0.45, 0.8), arrowprops=dict(arrowstyle="-", lw=1.3))
    ax.text((xs[6] + xs[-1]) / 2, 0.35, "усі 5 кас зайняті, у черзі k - 5 покупців", ha="center", fontsize=9)
    ax.set_title("Граф станів багатоканальної СМО з необмеженою чергою (c = 5)\n"
                 r"$S_k$ - у системі k покупців", fontsize=10)
    plt.tight_layout()
    plt.savefig(FIG + "states_graph.png", dpi=150)
    plt.close()




def oval(ax, x, y, text, w=2.4, h=0.7):
    ax.add_patch(Ellipse((x, y), w, h, fill=False, lw=1.3))
    ax.text(x, y, text, ha="center", va="center", fontsize=8.5)


def box(ax, x, y, text, w=4.6, h=0.9):
    ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fill=False, lw=1.3))
    ax.text(x, y, text, ha="center", va="center", fontsize=8)


def diamond(ax, x, y, text, w=4.0, h=1.3):
    ax.add_patch(Polygon([(x - w / 2, y), (x, y + h / 2), (x + w / 2, y), (x, y - h / 2)], fill=False, lw=1.3))
    ax.text(x, y, text, ha="center", va="center", fontsize=8)


def flowchart(fname, title, params_text, select_text, many):
    fig, ax = plt.subplots(figsize=(7.6, 10.4))
    ax.set_xlim(0, 10.6)
    ax.set_ylim(0, 14.4)
    ax.axis("off")
    X = 4.4
    oval(ax, X, 13.9, "Початок")
    box(ax, X, 12.8, params_text, h=1.1)
    box(ax, X, 11.5, "Ініціалізація: черга = порожня,\nвсі каси вільні (free_at = 0),\nкрок step = 0", h=1.0)
    diamond(ax, X, 10.1, "step < 72 ?")
    box(ax, X, 8.7, "Визначити період доби за step,\nчисло покупців n ~ Пуассон(λ періоду)", h=0.9)
    box(ax, X, 7.5, "Для кожного з n покупців: час приходу ~ Рівномірний(t, t+20),\nтовари k ~ Біноміальний(30; 0,4), t_обсл = 0,4 + 0,25·k;\nпоставити в чергу", w=6.6, h=1.0)
    diamond(ax, X, 6.1, "Черга не порожня ?", w=3.6)
    diamond(ax, X, 4.6, "start < t + 20 ?\n(каса встигає почати)", w=4.2, h=1.4)
    box(ax, X, 2.9, select_text, h=1.5)
    box(ax, X, 1.0, "Записати стан кроку (черга, зайнятість),\nstep = step + 1", h=0.9)
    
    for y0, y1 in [(13.55, 13.35), (12.25, 12.0), (11.0, 10.75), (9.45, 9.15), (8.25, 8.0),
                   (7.0, 6.75), (5.45, 5.3), (3.9, 3.65)]:
        arrow(ax, X, y0, X, y1)
    ax.text(X + 0.15, 9.3, "так", fontsize=8)
    ax.text(X + 0.2, 5.25, "так", fontsize=8)
    ax.text(X + 0.2, 3.75, "так", fontsize=8)
    
    line(ax, [(X - 2.3, 2.9), (0.9, 2.9), (0.9, 6.1)])
    arrow(ax, 0.9, 6.1, X - 1.8, 6.1)
    
    line(ax, [(X + 1.8, 6.1), (7.3, 6.1), (7.3, 1.0)])
    arrow(ax, 7.3, 1.0, X + 2.3, 1.0)
    ax.text(X + 1.9, 6.2, "ні", fontsize=8)
    line(ax, [(X + 2.1, 4.6), (7.3, 4.6)])
    ax.text(X + 2.15, 4.7, "ні", fontsize=8)
    
    line(ax, [(X - 2.3, 1.0), (0.4, 1.0), (0.4, 10.1)])
    arrow(ax, 0.4, 10.1, X - 2.0, 10.1)

    arrow(ax, X + 2.0, 10.1, 8.0, 10.1)
    ax.text(X + 2.1, 10.2, "ні", fontsize=8)
    box(ax, 8.9, 9.1 + 0.9, "Дообслужити тих,\nхто лишився в черзі;\nпідсумки та графіки", w=3.0, h=1.3)
    arrow(ax, 8.9, 9.45, 8.9, 8.6)
    oval(ax, 8.9, 8.25, "Кінець", w=1.8)
    ax.set_title(title, fontsize=10)
    plt.tight_layout()
    plt.savefig(FIG + fname, dpi=150)
    plt.close()


scheme()
states()
flowchart("flow_one.png", "Блок-схема одного прогону (етап 1, одна каса)",
          "Параметри: крок 20 хв, 72 кроки, λ по періодах/5,\nT0 = 0,4 хв, T_item = 0,25 хв, B(30; 0,4)\nкількість кас c = 1",
          "Взяти першого в черзі; k = каса з мін. free_at (єдина);\nstart = max(free_at, час приходу, t);\nочікування = start - прихід; free_at = start + t_обсл;\nзаписати покупця в статистику", False)
flowchart("flow_multi.png", "Блок-схема одного прогону (етап 2, багатоканальна система)",
          "Параметри: крок 20 хв, 72 кроки, λ по періодах,\nT0 = 0,4 хв, T_item = 0,25 хв, B(30; 0,4)\nграфік кас c(step) для кожного кроку",
          "Взяти першого в черзі; k = відкрита каса (серед c(step))\nз мінімальним free_at;\nstart = max(free_at[k], час приходу, t);\nочікування = start - прихід; free_at[k] = start + t_обсл;\nзаписати покупця в статистику", True)
print("Схеми намальовано.")
