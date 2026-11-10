"""Збирає у Word лише таблиці та рисунки з готових результатів (results/ та figures/)."""
\
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_COLOR_INDEX
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

import smo_model as m

RES, FIG = "results/", "figures/"
OUT = "build_report.docx"
FONT = "Times New Roman"



s1p = pd.read_csv(RES + "s1_period_summary.csv")
s1d = pd.read_csv(RES + "s1_daily_summary.csv")
s1chk = pd.read_csv(RES + "s1_checks.csv")
s1lam = pd.read_csv(RES + "s1_adequacy_lambda.csv")
s1t = pd.read_csv(RES + "s1_adequacy_titem.csv")
s1steps = pd.read_csv(RES + "s1_run_log_steps.csv")
s1cust = pd.read_csv(RES + "s1_run_customers.csv")
sched = pd.read_csv(RES + "optimal_schedule.csv")
scen = pd.read_csv(RES + "s2_scenarios.csv")
s2p = pd.read_csv(RES + "s2_period_summary.csv")
s2d = pd.read_csv(RES + "s2_daily_summary.csv")
search = pd.read_csv(RES + "s2_search_log.csv")
s2steps = pd.read_csv(RES + "s2_run_log_steps.csv")
s2cust = pd.read_csv(RES + "s2_run_customers.csv")
an = pd.read_csv(RES + "s3_analytic_vs_sim.csv")
sweep = pd.read_csv(RES + "s3_sweep.csv")
minc = pd.read_csv(RES + "s3_min_c.csv")
chk1 = pd.read_csv(RES + "s3_check_one_channel.csv")
states = pd.read_csv(RES + "s3_states_evening.csv")
sens = pd.read_csv(RES + "s2_sensitivity.csv")
loc = pd.read_csv(RES + "s2_local_check.csv")

C5 = sched.registers_5pct.tolist()
C1 = sched.registers_1pct.tolist()
DUR = [p[2] - p[1] for p in m.PERIODS]
RH5 = sum(c * h for c, h in zip(C5, DUR))
RH1 = sum(c * h for c, h in zip(C1, DUR))
RHALL = m.MAX_REGISTERS * 24
MEAN_S = m.mean_service_time()
MU = 60 / MEAN_S
CV2 = m.service_cv2()
CAP = {c: c * m.STEP / MEAN_S for c in range(1, 6)}         


def f(x, d=2):
    """Число з десятковою комою."""
    return f"{x:.{d}f}".replace(".", ",")


def pct(x, d=1):
    return f(x * 100, d) + " %"


def clean(t):
    return t.replace("—", "-").replace("–", "-")




doc = Document()
_z = doc.settings.element.find(qn("w:zoom"))
if _z is not None:
    _z.set(qn("w:percent"), "100")
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.left_margin, sec.right_margin, sec.top_margin, sec.bottom_margin = Cm(3), Cm(1.5), Cm(2), Cm(2)
sec.different_first_page_header_footer = False


def set_style_font(style, size, bold=None):
    style.font.name = FONT
    style.font.size = Pt(size)
    if bold is not None:
        style.font.bold = bold
    style.font.color.rgb = None
    rpr = style.element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rpr.append(rf)
    for a in list(rf.attrib):
        if "Theme" in a:
            del rf.attrib[a]
    for a in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rf.set(qn(a), FONT)


set_style_font(doc.styles["Normal"], 14)
doc.styles["Normal"].paragraph_format.space_after = Pt(0)
set_style_font(doc.styles["Heading 1"], 14, True)
set_style_font(doc.styles["Heading 2"], 14, True)
for h in ("Heading 1", "Heading 2"):
    pf = doc.styles[h].paragraph_format
    pf.space_before, pf.space_after, pf.keep_with_next = Pt(14), Pt(8), True
doc.styles["Heading 1"].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER

counters = {"fig": 0, "tab": 0}
FIGN, TABN = {}, []






def add_runs(p, text, size=None, bold=False, italic=False, hl=False):
    parts = clean(text).split("**")
    for i, part in enumerate(parts):
        if not part:
            continue
        r = p.add_run(part)
        r.bold = bold or (i % 2 == 1)
        r.italic = italic
        if size:
            r.font.size = Pt(size)
        if hl:
            r.font.highlight_color = WD_COLOR_INDEX.YELLOW
    return p


def P(text, indent=True, align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=None, bold=False, italic=False,
      space_after=6, line=1.25, keep=False, hl=False):
    p = doc.add_paragraph()
    p.alignment = align
    pf = p.paragraph_format
    pf.first_line_indent = Cm(1.25) if indent else None
    pf.space_after = Pt(space_after)
    pf.line_spacing = line
    pf.keep_with_next = keep
    add_runs(p, text, size, bold, italic, hl)
    return p


def bullets(items, numbered=False):
    for i, t in enumerate(items, 1):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        pf = p.paragraph_format
        pf.left_indent = Cm(1.25)
        pf.first_line_indent = Cm(-0.6)
        pf.space_after = Pt(3)
        pf.line_spacing = 1.25
        add_runs(p, (f"{i}) " if numbered else "- ") + t)


def H1(t):
    doc.add_heading(clean(t), level=1)


def H2(t):
    doc.add_heading(clean(t), level=2)


def page_break():
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def shade(cell, color):
    tcpr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    tcpr.append(shd)


def table(header, rows, caption, widths=None, size=10, first_left=True):
    counters["tab"] += 1
    TABN.append((caption, counters["tab"]))
    cp = P(f"Таблиця {counters['tab']} - {caption}", indent=False, align=WD_ALIGN_PARAGRAPH.LEFT,
           size=12, space_after=3, line=1.0, keep=True)
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(header):
        c = t.rows[0].cells[j]
        c.text = ""
        add_runs(c.paragraphs[0], str(h), size=size, bold=True)
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        shade(c, "D9D9D9")
    trpr = t.rows[0]._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader")
    th.set(qn("w:val"), "true")
    trpr.append(th)
    for r in rows:
        cells = t.add_row().cells
        for j, v in enumerate(r):
            cells[j].text = ""
            add_runs(cells[j].paragraphs[0], str(v), size=size)
            cells[j].paragraphs[0].alignment = (WD_ALIGN_PARAGRAPH.LEFT if (j == 0 and first_left)
                                                else WD_ALIGN_PARAGRAPH.CENTER)
    for row in t.rows:
        trpr = row._tr.get_or_add_trPr()
        cs = OxmlElement("w:cantSplit")
        cs.set(qn("w:val"), "true")
        trpr.append(cs)
        for c in row.cells:
            for p in c.paragraphs:
                p.paragraph_format.space_after = Pt(1)
                p.paragraph_format.space_before = Pt(1)
    if widths:
        t.autofit = False
        for j, w in enumerate(widths):
            t.columns[j].width = Cm(w)
        for row in t.rows:
            for c, w in zip(row.cells, widths):
                c.width = Cm(w)
    sp = doc.add_paragraph()
    sp.paragraph_format.space_after = Pt(4)
    return t


def figure(path, caption, width=15.0):
    counters["fig"] += 1
    FIGN[path.split("/")[-1]] = counters["fig"]
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_before = Pt(4)
    p.add_run().add_picture(path, width=Cm(width))
    P(f"Рисунок {counters['fig']} - {caption}", indent=False, align=WD_ALIGN_PARAGRAPH.CENTER,
      size=12, space_after=10, line=1.0)






def hhmm(minutes):
    return f"{int(minutes // 60):02d}:{int(minutes % 60):02d}"



fp = sec.footer.paragraphs[0]
fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = fp.add_run()
for tag, txt in (("begin", None), (None, "PAGE"), ("end", None)):
    if tag:
        el = OxmlElement("w:fldChar")
        el.set(qn("w:fldCharType"), tag)
    else:
        el = OxmlElement("w:instrText")
        el.set(qn("xml:space"), "preserve")
        el.text = txt
    run._r.append(el)
run.font.name = FONT
run.font.size = Pt(12)






H1("Етап 1. Одна каса")
table(["Параметр", "Значення", "Пояснення"], [
    ["Крок модельного часу", "20 хв", "фіксований крок за умовою"],
    ["Тривалість моделювання", "1 доба = 72 кроки", "кожен прогін починається о 00:00 з порожньою чергою"],
    ["Кількість каналів (етап 1)", "1 каса", "працює постійно"],
    ["Кількість покупців за крок", "Пуассон(λ періоду)", "numpy.random.poisson"],
    ["Моменти приходу в межах кроку", "Рівномірний на [t; t+20)", "разом із Пуассоном дає пуассонівський потік"],
    ["Кількість товарів k", f"Біноміальний B({m.ITEMS_N}; {f(m.ITEMS_P, 1)})",
     f"M[k] = {f(m.ITEMS_N * m.ITEMS_P, 0)}, мінімум 1 товар; numpy.random.binomial"],
    ["Час обслуговування", f"t = {f(m.T0, 1)} + {f(m.T_ITEM)}·k, хв",
     f"лінійна залежність: {f(m.T0, 1)} хв на оплату + {f(m.T_ITEM * 60, 0)} с на товар; M[t] = {f(MEAN_S, 1)} хв"],
    ["Черга", "єдина, необмежена, FIFO", "клієнти не залишають чергу"],
    ["Вимога до очікування", "≤ 10 хв", f"формалізовано: частка очікувань > 10 хв не більше {pct(m.ALLOWED_SHARE, 0)}"],
    ["Кількість прогонів", "100", "незалежні прогони (різні початкові значення генератора)"],
], "Параметри імітаційної моделі", widths=[4.6, 4.4, 7.2], size=10)
table(["Період доби", "Межі", "M[покупців за 20 хв], вся система", "M[покупців за 20 хв], на одну касу",
       "Покупців за годину, вся система"],
      [[p[0], f"{p[1]:02d}:00-{p[2]:02d}:00", p[3], f(p[3] / 5, 1), p[3] * 3] for p in m.PERIODS],
      "Періоди доби та інтенсивність потоку покупців", widths=[3.6, 3.0, 3.4, 3.4, 3.0], size=10)


figure(FIG + "flow_one.png", "Блок-схема одного прогону імітаційної моделі (одна каса)", width=12.5)

n1 = len(s1cust)
pk = s1steps.loc[s1steps.queue_end.idxmax()]
figure(FIG + "s1_run_queue.png", "Етап 1, один прогін: потік покупців і довжина черги", width=14.5)
figure(FIG + "s1_run_hist.png", "Етап 1, один прогін: розподіли кількості товарів, часу обслуговування та очікування",
       width=16)
frag = s1steps[(s1steps.step >= 48) & (s1steps.step < 60)]
table(["Час", "Період", "Прийшло покупців", "Почали обслуговуватися", "Черга на кінець кроку",
       "Завантаженість каси"],
      [[r.time, r.period, int(r.arrived), int(r.started_service), int(r.queue_end), pct(r.utilization, 0)]
       for r in frag.itertuples()],
      "Етап 1, фрагмент журналу одного прогону (16:00-20:00)", widths=[1.8, 3.2, 2.6, 3.2, 2.8, 2.8], size=10)
table(["№", "Прихід, хв від 00:00", "Товарів", "Час обслуговування, хв", "Початок обслуговування, хв",
       "Очікування, хв"],
      [[int(r.id), f(r.arrival), int(r.items), f(r.service), f(r.start), f(r.wait)]
       for r in s1cust.iloc[:8].itertuples()],
      "Етап 1, початок журналу обслужених покупців (один прогін)", widths=[1.2, 3.4, 2.2, 3.6, 3.6, 2.6], size=10)

dm = s1d.mean()
dsd = s1d.std()
table(["Період", "Покупців за добу", "Сер. очікування, хв", "P95 очікування, хв", "Частка > 10 хв",
       "Завантаженість", "Сер. черга", "Макс. черга"],
      [[r.period, f(r.customers_per_run, 1), f(r.mean_wait), f(r.p95_wait), pct(r.share_wait_gt_10),
        pct(r.utilization, 0), f(r.queue_avg), f(r.queue_max, 1)] for r in s1p.itertuples()],
      "Етап 1, середні показники за 100 прогонів (по періодах приходу покупців)",
      widths=[3.0, 1.9, 2.0, 2.0, 1.9, 2.1, 1.6, 1.7], size=9)
figure(FIG + "s1_100_periods.png", "Етап 1, середні за 100 прогонів: очікування та завантаженість по періодах", width=15.5)
figure(FIG + "s1_100_hist.png", "Етап 1, розподіли добових показників за 100 прогонів", width=16)
ev = s1p.iloc[3]

table(["Показник", "Теоретичне значення", "Вибіркове (100 прогонів)"],
      [[r["Показник"], f(r["Теоретичне значення"], 3), f(r["Вибіркове (100 прогонів)"], 3)]
       for _, r in s1chk.iterrows()], "Етап 1, порівняння вибіркових і теоретичних характеристик",
      widths=[7.5, 4.2, 4.5], size=10)
table(["Множник потоку", "Сер. очікування, хв", "Частка > 10 хв", "Макс. черга", "Завантаженість"],
      [[f(r.lam_scale), f(r.mean_wait), pct(r.share_wait_gt_10), f(r.queue_max, 1), pct(r.utilization, 0)]
       for r in s1lam.itertuples()], "Етап 1, вплив інтенсивності потоку покупців (по 100 прогонів)",
      widths=[3.0, 3.2, 3.0, 3.0, 3.2], size=10)
table(["Час на один товар, с", "Сер. очікування, хв", "Частка > 10 хв", "Макс. черга", "Завантаженість"],
      [[f(r.t_item * 60, 0), f(r.mean_wait), pct(r.share_wait_gt_10), f(r.queue_max, 1), pct(r.utilization, 0)]
       for r in s1t.itertuples()], "Етап 1, вплив часу обслуговування одного товару (по 100 прогонів)",
      widths=[3.0, 3.2, 3.0, 3.0, 3.2], size=10)
figure(FIG + "s1_adequacy.png", "Етап 1, залежність очікування і черги від параметрів моделі", width=15)

H1("Етап 2. Багатоканальна система")
table(["Кількість відкритих кас c"] + [str(c) for c in range(1, 6)],
      [["Пропускна здатність за 20 хв, покупців"] + [f(CAP[c], 1) for c in range(1, 6)]],
      "Пропускна здатність кас за один крок модельного часу", widths=[5.6, 2.1, 2.1, 2.1, 2.1, 2.1], size=10)
cmin_cap = [min(c for c in range(1, 6) if CAP[c] > p[3]) for p in m.PERIODS]
table(["Період", "M[покупців за 20 хв]", "Мін. c за пропускною здатністю", "Знайдено моделюванням (c)"],
      [[p[0], p[3], cmin_cap[i], C5[i]] for i, p in enumerate(m.PERIODS)],
      "Оцінка мінімальної кількості кас: за пропускною здатністю та за результатами імітації",
      widths=[3.8, 3.8, 4.6, 4.2], size=10)

figure(FIG + "flow_multi.png", "Блок-схема одного прогону імітаційної моделі багатоканальної системи", width=12.5)

s5 = search[search.limit == 0.05]
rows = []
for c in range(1, 6):
    row = [c]
    for name in m.PERIOD_NAMES:
        sub = s5[(s5.period == name) & (s5.registers == c)]
        if len(sub):
            r = sub.iloc[0]
            row.append(pct(r.share_wait_gt_10) + (" *" if r.ok and (s5[(s5.period == name) & (s5.ok)].registers.min() == c) else ""))
        else:
            row.append("-")
    rows.append(row)
table(["c"] + m.PERIOD_NAMES, rows, "Підбір кількості кас: частка покупців з очікуванням > 10 хв (100 прогонів)",
      widths=[1.2, 3.0, 3.0, 3.0, 3.0, 3.0], size=10, first_left=False)
table(["Період", "Межі", "M[покупців за 20 хв]", "Кас (вимога 5 %)", "Кас (вимога 1 %)"],
      [[r.period, f"{r._2:02d}:00-{r.to:02d}:00", r.lambda_step, r.registers_5pct, r.registers_1pct]
       for r in sched.itertuples()] +
      [["Каса-годин за добу", "", "", RH5, RH1]],
      "Знайдений графік роботи кас", widths=[3.8, 3.2, 3.4, 3.0, 3.0], size=10)
figure(FIG + "s2_schedule.png", "Знайдений графік роботи кас і потік покупців", width=15.5)
chk_txt = "; ".join(f"{r.changed_period.lower()} - {r.schedule.replace('[', '').replace(']', '').replace(', ', '-')}: частка порушень "
                    f"{pct(r.share_in_changed, 0)}" for r in loc.itertuples())

o1 = len(s2cust)
figure(FIG + "s2_run.png", "Етап 2, один прогін: потік покупців, відкриті каси та довжина черги", width=14.5)
frag = s2steps[(s2steps.step >= 48) & (s2steps.step < 60)]
table(["Час", "Відкрито кас", "Прийшло покупців", "Почали обслуговуватися", "Черга на кінець кроку",
       "Завантаженість кас"],
      [[r.time, int(r.registers), int(r.arrived), int(r.started_service), int(r.queue_end), pct(r.utilization, 0)]
       for r in frag.itertuples()],
      "Етап 2, фрагмент журналу одного прогону (16:00-20:00)", widths=[1.8, 2.6, 3.0, 3.6, 3.0, 3.0], size=10)
table(["№", "Прихід, хв від 00:00", "Товарів", "Час обслуговування, хв", "Початок обслуговування, хв",
       "Очікування, хв", "Каса"],
      [[int(r.id), f(r.arrival), int(r.items), f(r.service), f(r.start), f(r.wait), int(r.register)]
       for r in s2cust.iloc[:8].itertuples()],
      "Етап 2, початок журналу обслужених покупців (один прогін)",
      widths=[1.0, 3.2, 1.9, 3.4, 3.4, 2.4, 1.4], size=10)

dm = s2d.mean()
dsd = s2d.std()
table(["Період", "Покупців за добу", "Сер. очікування, хв", "P95, хв", "Макс. очікування, хв", "Частка > 10 хв",
       "Завантаженість", "Сер. черга", "Макс. черга"],
      [[r.period, f(r.customers_per_run, 1), f(r.mean_wait), f(r.p95_wait), f(r.max_wait), pct(r.share_wait_gt_10),
        pct(r.utilization, 0), f(r.queue_avg), f(r.queue_max, 1)] for r in s2p.itertuples()],
      "Етап 2, середні показники за 100 прогонів для знайденого графіка",
      widths=[2.7, 1.7, 1.9, 1.5, 2.0, 1.8, 2.0, 1.4, 1.4], size=9)
figure(FIG + "s2_100_periods.png", "Етап 2, середні за 100 прогонів: очікування та черга по періодах", width=15.5)
figure(FIG + "s2_100_hist.png", "Етап 2, розподіли добових показників за 100 прогонів", width=16)
figure(FIG + "s2_wait_dist.png", "Етап 2, розподіл часу очікування та навантаження на каси", width=15)

table(["Варіант", "Графік (кас по періодах)", "Каса-годин", "Сер. очікування, хв", "Макс. очікування, хв",
       "Частка > 10 хв", "Макс. черга", "Завантаженість"],
      [[r.scenario, r.schedule.replace("[", "").replace("]", ""), f(r.register_hours, 0), f(r.mean_wait),
        f(r.max_wait, 1), pct(r.share_wait_gt_10), f(r.queue_max, 0), pct(r.utilization, 0)]
       for r in scen.itertuples()],
      "Порівняння варіантів графіка роботи кас (по 100 прогонів кожен)",
      widths=[3.2, 2.5, 1.5, 2.0, 2.0, 1.8, 1.6, 2.0], size=9)
figure(FIG + "s2_scenarios.png", "Виконання вимоги й завантаженість кас для різних варіантів графіка", width=16)
r1, r3, r5, ro, rs = [scen.iloc[i] for i in range(5)]

H1("Етап 3. Аналітична модель")
figure(FIG + "scheme_smo.png", "Схема багатоканальної СМО касової зони", width=15)

figure(FIG + "states_graph.png", "Граф станів багатоканальної СМО з необмеженою чергою (c = 5)", width=16)

table(["Період", "c", "λ, покупців/год", "μ, 1/год", "a = λ/μ", "ρ"],
      [[r.period, r.c, f(r.lam_h, 0), f(MU, 3), f(r.lam_h / MU, 3), f(r.rho, 3)] for r in an.itertuples()],
      "Параметри аналітичної моделі для знайденого графіка (ті самі вхідні дані, що на етапі 2)",
      widths=[3.8, 1.2, 3.2, 2.6, 2.6, 2.4], size=10)

table(["Період", "c", "ρ", "P0", "P_C", "L_q (M/M/c)", "W_q, хв (M/M/c)", "W_s, хв (M/M/c)", "P(W>10) (M/M/c)"],
      [[r.period, r.c, f(r.rho, 3), f(r.p0, 4), f(r.p_wait, 3), f(r.Lq_mmc, 3), f(r.Wq_mmc), f(r.Ws_mmc),
        pct(r.p10_mmc)] for r in an.itertuples()],
      "Аналітична модель M/M/c для знайденого графіка", widths=[2.8, 0.8, 1.4, 1.6, 1.4, 1.9, 2.1, 2.1, 2.4],
      size=9)
table(["Період", "c", "L_q (M/G/c)", "W_q, хв (M/G/c)", "P(W>10) (M/G/c)"],
      [[r.period, r.c, f(r.Lq_mgc, 3), f(r.Wq_mgc), pct(r.p10_mgc)] for r in an.itertuples()],
      "Наближення M/G/c (з поправкою на майже сталий час обслуговування)", widths=[3.8, 1.2, 3.2, 3.8, 3.8],
      size=10)

rows = []
for name in m.PERIOD_NAMES:
    row = [name]
    for c in range(1, 6):
        s = sweep[(sweep.period == name) & (sweep.c == c)].iloc[0]
        row.append(pct(s.p10_mgc) if s.stable else "ρ ≥ 1")
    rows.append(row)
table(["Період"] + [f"c = {c}" for c in range(1, 6)], rows,
      "Аналітична оцінка P(W>10 хв) за M/G/c залежно від кількості кас (\"ρ ≥ 1\" - режим не існує)",
      widths=[3.6, 2.4, 2.4, 2.4, 2.4, 2.4], size=10)
figure(FIG + "s3_sweep.png", "Залежність очікування та частки очікувань > 10 хв від кількості кас (M/G/c)", width=16)
qe = states.q_k
figure(FIG + "s3_states.png", "Стаціонарний розподіл кількості покупців у системі у вечірній пік", width=12)

table(["Показник", "Модель"] + m.PERIOD_NAMES,
      [["Завантаженість ρ", "імітація"] + [pct(x, 1) for x in an.sim_util],
       ["", "аналітика"] + [pct(x, 1) for x in an.rho],
       ["Ймовірність очікування", "імітація"] + [pct(x, 1) for x in an.sim_p_wait],
       ["", "M/M/c (Ерланг C)"] + [pct(x, 1) for x in an.p_wait],
       ["Сер. довжина черги", "імітація"] + [f(x) for x in an.sim_Lq],
       ["", "M/M/c"] + [f(x) for x in an.Lq_mmc],
       ["", "M/G/c"] + [f(x) for x in an.Lq_mgc],
       ["Сер. очікування, хв", "імітація"] + [f(x) for x in an.sim_Wq],
       ["", "M/M/c"] + [f(x) for x in an.Wq_mmc],
       ["", "M/G/c"] + [f(x) for x in an.Wq_mgc],
       ["Частка очікувань > 10 хв", "імітація"] + [pct(x) for x in an.sim_p10],
       ["", "M/M/c"] + [pct(x) for x in an.p10_mmc],
       ["", "M/G/c"] + [pct(x) for x in an.p10_mgc]],
      "Порівняння імітаційного та аналітичного моделювання (середні за 100 прогонів)",
      widths=[3.1, 2.4, 2.1, 2.1, 2.1, 2.1, 2.1], size=8.5)
figure(FIG + "s3_compare.png", "Порівняння середнього очікування та частки очікувань > 10 хв", width=16)
d_util = float((an.sim_util - an.rho).abs().max() * 100)
d_mgc = (an.sim_Wq - an.Wq_mgc)
ratio = an.Wq_mmc / an.sim_Wq
late = int(d_mgc.abs().idxmax())
d_pw = float((an.sim_p_wait - an.p_wait).abs().max() * 100)
d_lq = float((an.sim_Lq - an.Lq_mgc).abs().max())
table(["Період", "Мін. c за M/M/c", "Мін. c за M/G/c", "Мін. c за імітацією"],
      [[r.period, r.c_mmc, r.c_mgc, r.c_sim] for r in minc.itertuples()],
      "Мінімальна кількість кас, що забезпечує P(W>10 хв) ≤ 5 %, за різними моделями", widths=[4.0, 3.6, 3.6, 4.0],
      size=10)
extra = sum((r.c_mmc - r.c_sim) * DUR[i] for i, r in enumerate(minc.itertuples()))
table(["Період", "ρ (аналітика)", "Завантаженість (імітація)", "W_q, хв, M/M/1", "W_q, хв, M/G/1", "W_q, хв, імітація"],
      [[r.period, f(r.rho, 3), f(r.sim_util, 3), f(r.Wq_mm1), f(r.Wq_mg1), f(r.sim_Wq)] for r in chk1.itertuples()],
      "Етап 1, перевірка імітаційної моделі однієї каси аналітичними формулами",
      widths=[3.2, 2.4, 3.0, 2.4, 2.4, 2.6], size=9)

table(["Множник потоку"] + [n for n in m.PERIOD_NAMES] + ["За добу"],
      [[f(r.scale, 1)] + [pct(getattr(r, f"share_{p}")) for p in range(5)] + [pct(r.share_day)]
       for r in sens.itertuples()],
      "Частка покупців з очікуванням > 10 хв при зміні інтенсивності потоку (графік фіксований)",
      widths=[2.6, 2.4, 2.4, 2.4, 2.4, 2.4, 2.0], size=9)
s11 = sens[sens.scale == 1.1].iloc[0]
s12 = sens[sens.scale == 1.2].iloc[0]
w11 = max(s11[f"share_{p}"] for p in range(5))
w12 = max(s12[f"share_{p}"] for p in range(5))

rel_diff = float(((s1chk["Теоретичне значення"] - s1chk["Вибіркове (100 прогонів)"]).abs()
                  / s1chk["Теоретичне значення"]).max() * 100)
viol1 = [s1p.period[i] for i in range(5) if s1p.share_wait_gt_10[i] > m.ALLOWED_SHARE]
viol1_txt = ", ".join("«" + v.lower() + "»" for v in viol1)
same_c = bool((minc.c_mgc == minc.c_sim).all())
worst20 = int(np.argmax([s12[f"share_{p}"] for p in range(5)]))


h1_ok = (s2p.share_wait_gt_10.max() <= m.ALLOWED_SHARE) and bool((loc.ok == False).all()) and RH5 < RHALL
h2_ok = bool(len(viol1) > 0) and (s1p.mean_wait[3] > 3 * s2p.mean_wait[3])
h3_ok = same_c and float(ratio.min()) > 1.5 and float(d_mgc.abs().max()) < 0.5
h4_ok = (s12.share_1 > m.ALLOWED_SHARE) and (s12.share_3 > m.ALLOWED_SHARE)
V = lambda ok: "підтверджено" if ok else "не підтверджено"


doc.save(OUT)
print("Збережено", OUT, "| рисунків:", counters["fig"], "| таблиць:", counters["tab"])
