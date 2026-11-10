"""
ЕТАП 3. Аналітична модель багатоканальної СМО з необмеженою чергою 
"""
from math import exp, factorial

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import smo_model as m

RES, FIG = "results/", "figures/"
plt.rcParams.update({"font.size": 10, "axes.grid": True, "grid.alpha": 0.3})
BLUE, ORANGE, GREEN, RED, GRAY = "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#7f7f7f"

MU = 60.0 / m.mean_service_time()          
CV2 = m.service_cv2()
T_LIM = m.MAX_WAIT / 60.0                  


def analytic(lam, c, mu=MU, cv2=CV2, t=T_LIM):
    a = lam / mu
    rho = a / c
    if rho >= 1:
        return None                         
    s = sum(a ** i / factorial(i) for i in range(c))
    top = a ** c / (factorial(c) * (1 - rho))
    p0 = 1.0 / (s + top)
    p_wait = top * p0                       
    lq = p_wait * rho / (1 - rho)
    wq = lq / lam
    k = (1 + cv2) / 2
    rate = c * mu - lam
    return {
        "lam": lam, "mu": mu, "c": c, "a": a, "rho": rho, "p0": p0, "p_wait": p_wait,
        "Lq": lq, "Wq_h": wq, "Wq_min": wq * 60, "Ws_min": (wq + 1 / mu) * 60, "Ls": lq + a,
        "p_gt_10_mmc": p_wait * exp(-rate * t),
        "Wq_mgc_min": wq * k * 60, "Lq_mgc": lq * k,
        "p_gt_10_mgc": p_wait * exp(-rate * t * 2 / (1 + cv2)),
    }


def state_probs(lam, c, kmax):
    a = lam / MU
    res = analytic(lam, c)
    p0 = res["p0"]
    q = []
    for k in range(kmax + 1):
        if k <= c:
            q.append(a ** k / factorial(k) * p0)
        else:
            q.append(a ** c / factorial(c) * (a / c) ** (k - c) * p0)
    return q


def lam_hour(period_index):
    return m.PERIODS[period_index][3] * 60.0 / m.STEP


print("mu = %.4f 1/год (t_обсл = %.2f хв), CV^2 = %.4f" % (MU, m.mean_service_time(), CV2))



sched = pd.read_csv(RES + "optimal_schedule.csv")
sim = pd.read_csv(RES + "s2_period_summary.csv")
rows = []
for p, name in enumerate(m.PERIOD_NAMES):
    c = int(sched.registers_5pct[p])
    r = analytic(lam_hour(p), c)
    rows.append({
        "period": name, "c": c, "lam_h": r["lam"], "rho": r["rho"], "p0": r["p0"], "p_wait": r["p_wait"],
        "Lq_mmc": r["Lq"], "Wq_mmc": r["Wq_min"], "Ws_mmc": r["Ws_min"],
        "p10_mmc": r["p_gt_10_mmc"],
        "Lq_mgc": r["Lq_mgc"], "Wq_mgc": r["Wq_mgc_min"], "p10_mgc": r["p_gt_10_mgc"],
        "sim_util": sim.utilization[p], "sim_p_wait": sim.share_wait_gt_0[p],
        "sim_Lq": sim.queue_avg[p], "sim_Wq": sim.mean_wait[p], "sim_p10": sim.share_wait_gt_10[p],
    })
an = pd.DataFrame(rows)
an.to_csv(RES + "s3_analytic_vs_sim.csv", index=False)
print(an.round(4).to_string())




rows = []
for p, name in enumerate(m.PERIOD_NAMES):
    for c in range(1, m.MAX_REGISTERS + 1):
        r = analytic(lam_hour(p), c)
        rows.append({"period": name, "c": c,
                     "rho": lam_hour(p) / MU / c,
                     "stable": r is not None,
                     "Wq_mmc": r["Wq_min"] if r else np.nan,
                     "p10_mmc": r["p_gt_10_mmc"] if r else np.nan,
                     "Wq_mgc": r["Wq_mgc_min"] if r else np.nan,
                     "p10_mgc": r["p_gt_10_mgc"] if r else np.nan})
sweep = pd.DataFrame(rows)
sweep.to_csv(RES + "s3_sweep.csv", index=False)
min_c = []
for p, name in enumerate(m.PERIOD_NAMES):
    s = sweep[sweep.period == name]
    c_mmc = s[(s.stable) & (s.p10_mmc <= m.ALLOWED_SHARE)].c.min()
    c_mgc = s[(s.stable) & (s.p10_mgc <= m.ALLOWED_SHARE)].c.min()
    min_c.append({"period": name, "c_mmc": int(c_mmc), "c_mgc": int(c_mgc),
                  "c_sim": int(sched.registers_5pct[p])})
min_c = pd.DataFrame(min_c)
min_c.to_csv(RES + "s3_min_c.csv", index=False)
print(min_c.to_string())




s1 = pd.read_csv(RES + "s1_period_summary.csv")
rows = []
for p, name in enumerate(m.PERIOD_NAMES):
    r = analytic(lam_hour(p) / 5, 1)
    rows.append({"period": name, "rho": r["rho"], "Wq_mm1": r["Wq_min"], "Wq_mg1": r["Wq_mgc_min"],
                 "sim_Wq": s1.mean_wait[p], "sim_util": s1.utilization[p]})
chk = pd.DataFrame(rows)
chk.to_csv(RES + "s3_check_one_channel.csv", index=False)
print(chk.round(3).to_string())


pk = 3
q = state_probs(lam_hour(pk), int(sched.registers_5pct[pk]), 14)
pd.DataFrame({"k": range(len(q)), "q_k": q}).to_csv(RES + "s3_states_evening.csv", index=False)



idx = np.arange(5)
w = 0.26
fig, ax = plt.subplots(1, 2, figsize=(11, 3.9))
ax[0].bar(idx - w, an.sim_Wq, w, color=BLUE, label="імітація (100 прогонів)")
ax[0].bar(idx, an.Wq_mmc, w, color=ORANGE, label="аналітика M/M/c")
ax[0].bar(idx + w, an.Wq_mgc, w, color=GREEN, label="аналітика M/G/c (наближення)")
ax[0].set_ylabel("Середній час очікування, хв")
ax[0].set_title("Середнє очікування у черзі")
ax[1].bar(idx - w, an.sim_p10 * 100, w, color=BLUE)
ax[1].bar(idx, an.p10_mmc * 100, w, color=ORANGE)
ax[1].bar(idx + w, an.p10_mgc * 100, w, color=GREEN)
ax[1].axhline(5, color=RED, ls="--", lw=1)
ax[1].set_ylabel("P(очікування > 10 хв), %")
ax[1].set_title("Частка очікувань довше 10 хв (червона - 5 %)")
for a in ax:
    a.set_xticks(idx)
    a.set_xticklabels(m.PERIOD_NAMES, rotation=20)
ax[0].legend(fontsize=8)
plt.tight_layout()
plt.savefig(FIG + "s3_compare.png", dpi=150)
plt.close()

fig, ax = plt.subplots(1, 2, figsize=(11, 3.9))
for p, name in enumerate(m.PERIOD_NAMES):
    s = sweep[(sweep.period == name) & sweep.stable]
    ax[0].plot(s.c, s.Wq_mgc, "o-", label=name)
    ax[1].plot(s.c, s.p10_mgc * 100, "o-", label=name)
ax[0].set_yscale("log")
ax[0].set_xlabel("Кількість відкритих кас c")
ax[0].set_ylabel("Wq (M/G/c), хв, лог. шкала")
ax[0].set_title("Середнє очікування залежно від кількості кас")
ax[1].axhline(5, color=RED, ls="--", lw=1)
ax[1].set_yscale("log")
ax[1].set_xlabel("Кількість відкритих кас c")
ax[1].set_ylabel("P(очікування > 10 хв), %, лог. шкала")
ax[1].set_title("Частка очікувань > 10 хв залежно від c")
ax[0].legend(fontsize=7)
for a in ax:
    a.set_xticks(range(1, 6))
plt.tight_layout()
plt.savefig(FIG + "s3_sweep.png", dpi=150)
plt.close()

fig, ax = plt.subplots(figsize=(7.5, 3.5))
ax.bar(range(len(q)), q, color=BLUE)
ax.axvline(4.5, color=GRAY, ls=":")
ax.set_ylim(0, max(q) * 1.3)
ax.text(2.2, max(q) * 1.15, "усі в обслуговуванні\n(черги немає)", ha="center", va="center", fontsize=8)
ax.text(9.5, max(q) * 1.15, "є черга", ha="center", va="center", fontsize=8)
ax.set_xlabel("Кількість покупців у системі k")
ax.set_ylabel("Ймовірність q_k")
ax.set_title("Стаціонарний розподіл, вечірній пік (c = 5)")
plt.tight_layout()
plt.savefig(FIG + "s3_states.png", dpi=150)
plt.close()
print("Етап 3 завершено.")
