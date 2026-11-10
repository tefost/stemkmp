"""
ЕТАП 2. Багатоканальна імітаційна модель: до 5 кас зі спільною необмеженою чергою.

"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import smo_model as m

RES, FIG = "results/", "figures/"
N_RUNS = 100
LAM = m.lambda_vector()                   

plt.rcParams.update({"font.size": 10, "axes.grid": True, "grid.alpha": 0.3})
BLUE, ORANGE, GREEN, RED, GRAY = "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#7f7f7f"


def evaluate(per_period):
    dfs, logs = m.run_many(m.schedule_vector(per_period), LAM, N_RUNS)
    return m.period_summary(dfs, logs), dfs, logs


def optimize(limit, search_log=None):
    n = len(m.PERIODS)
    sched = [m.MAX_REGISTERS] * n
    for p in range(n):
        for c in range(1, m.MAX_REGISTERS + 1):
            trial = sched.copy()
            trial[p] = c
            ps, _, _ = evaluate(trial)
            share = ps.share_wait_gt_10[p]
            if search_log is not None:
                search_log.append({"limit": limit, "period": m.PERIOD_NAMES[p], "registers": c,
                                   "share_wait_gt_10": share, "mean_wait": ps.mean_wait[p],
                                   "utilization": ps.utilization[p], "ok": share <= limit})
            if share <= limit:
                sched[p] = c
                break
    while True:                              
        ps, _, _ = evaluate(sched)
        bad = [p for p in range(n) if ps.share_wait_gt_10[p] > limit and sched[p] < m.MAX_REGISTERS]
        if not bad:
            return sched
        sched[bad[0]] += 1



search = []
sched5 = optimize(0.05, search)
sched1 = optimize(0.01, search)
pd.DataFrame(search).to_csv(RES + "s2_search_log.csv", index=False)
print("Оптимальний графік (вимога 5 %):", sched5)
print("Суворіший графік (вимога 1 %):  ", sched1)

hours = [p[2] - p[1] for p in m.PERIODS]
sched_df = pd.DataFrame({
    "period": m.PERIOD_NAMES,
    "from": [p[1] for p in m.PERIODS], "to": [p[2] for p in m.PERIODS],
    "lambda_step": [p[3] for p in m.PERIODS],
    "registers_5pct": sched5, "registers_1pct": sched1,
})
sched_df.to_csv(RES + "optimal_schedule.csv", index=False)


scenarios = {
    "1 каса постійно": [1] * 5,
    "3 каси постійно": [3] * 5,
    "5 кас постійно": [5] * 5,
    "Оптимальний графік (5 %)": sched5,
    "Суворіший графік (1 %)": sched1,
}
rows, per_period = [], {}
for name, sc in scenarios.items():
    ps, dfs, logs = evaluate(sc)
    ds = m.daily_summary(dfs, logs).mean()
    rows.append({"scenario": name, "schedule": str(sc), "register_hours": ds.register_hours,
                 "mean_wait": ds.mean_wait, "max_wait": ds.max_wait,
                 "share_wait_gt_10": ds.share_wait_gt_10, "queue_max": ds.queue_max,
                 "utilization": ds.utilization, "customers": ds.customers})
    per_period[name] = ps
    ps.to_csv(RES + "s2_period_" + str(len(per_period)) + ".csv", index=False)
sc_df = pd.DataFrame(rows)
sc_df.to_csv(RES + "s2_scenarios.csv", index=False)
print(sc_df.round(3).to_string())


ps_opt, dfs_opt, logs_opt = evaluate(sched5)
ds_opt = m.daily_summary(dfs_opt, logs_opt)
ps_opt.to_csv(RES + "s2_period_summary.csv", index=False)
ds_opt.to_csv(RES + "s2_daily_summary.csv", index=False)
print(ps_opt.round(3).to_string())


df1, log1 = m.simulate(m.schedule_vector(sched5), LAM, seed=1)
df1.to_csv(RES + "s2_run_customers.csv", index=False)
log1.to_csv(RES + "s2_run_log_steps.csv", index=False)
print("Один прогін: обслужено", len(df1), "; середнє очікування %.2f хв; макс. черга %d"
      % (df1.wait.mean(), log1.queue_end.max()))


x = log1.step * m.STEP / 60
fig, ax = plt.subplots(3, 1, figsize=(9, 7.5), sharex=True)
ax[0].bar(x, log1.arrived, width=m.STEP / 60 * 0.9, color=BLUE, align="edge")
ax[0].set_ylabel("Прийшло покупців\nза крок")
ax[0].set_title("Етап 2, один прогін: потік, відкриті каси та черга")
ax[1].step(x, log1.registers, where="post", color=GREEN, lw=2)
ax[1].set_ylabel("Відкрито кас")
ax[1].set_yticks(range(0, 6))
ax[2].step(x, log1.queue_end, where="post", color=RED)
ax[2].set_ylabel("Довжина черги\nна кінець кроку")
ax[2].set_xlabel("Година доби")
ax[2].set_xticks(range(0, 25, 2))
for a in ax:
    for h in (6, 10, 16, 21):
        a.axvline(h, color="gray", ls=":", lw=1)
plt.tight_layout()
plt.savefig(FIG + "s2_run.png", dpi=150)
plt.close()

fig, ax = plt.subplots(figsize=(9, 3.8))
edges = [p[1] for p in m.PERIODS] + [24]          
ax.step(edges, sched5 + [sched5[-1]], where="post", color=GREEN, lw=2.5,
        label="кількість відкритих кас (вимога 5 %)")
ax.step(edges, sched1 + [sched1[-1]], where="post", color=ORANGE, lw=1.8,
        ls="--", label="кількість кас при вимозі 1 %")
ax.set_ylim(0, 5.6)
ax.set_xlim(0, 24)
ax.set_xticks(range(0, 25, 2))
ax.set_xlabel("Година доби")
ax.set_ylabel("Відкрито кас")
ax2 = ax.twinx()
ax2.bar([(p[1] + p[2]) / 2 for p in m.PERIODS], [p[3] for p in m.PERIODS],
        width=[(p[2] - p[1]) * 0.9 for p in m.PERIODS], color=BLUE, alpha=0.25,
        label="E[покупців за 20 хв]")
ax2.set_ylabel("Покупців за крок (середнє)")
ax2.grid(False)
h1, l1 = ax.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=3, fontsize=8)
ax.set_title("Графік роботи кас, знайдений моделюванням")
plt.tight_layout()
plt.savefig(FIG + "s2_schedule.png", dpi=150)
plt.close()

fig, ax = plt.subplots(1, 2, figsize=(11, 3.8))
names = ["3 каси постійно", "Оптимальний графік (5 %)", "Суворіший графік (1 %)", "5 кас постійно"]
colors = [GRAY, GREEN, ORANGE, BLUE]
w = 0.2
idx = np.arange(5)
for i, (nm, col) in enumerate(zip(names, colors)):
    ax[0].bar(idx + (i - 1.5) * w, per_period[nm].share_wait_gt_10 * 100, w, label=nm, color=col)
    ax[1].bar(idx + (i - 1.5) * w, per_period[nm].utilization * 100, w, color=col)
ax[0].axhline(5, color=RED, ls="--", lw=1)
ax[0].set_ylabel("Частка очікувань > 10 хв, %")
ax[0].set_title("Виконання вимоги по періодах (червона лінія - 5 %)")
ax[1].set_ylabel("Завантаженість кас, %")
ax[1].set_title("Завантаженість відкритих кас")
for a in ax:
    a.set_xticks(idx)
    a.set_xticklabels(m.PERIOD_NAMES, rotation=20)
ax[0].legend(fontsize=7)
plt.tight_layout()
plt.savefig(FIG + "s2_scenarios.png", dpi=150)
plt.close()

fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
ax[0].bar(ps_opt.period, ps_opt.mean_wait, yerr=ps_opt.mean_wait_std_between_runs, color=BLUE, capsize=4)
ax[0].set_ylabel("Середній час очікування, хв")
ax[0].set_title("Очікування (середнє за 100 прогонів, ± σ)")
ax[1].bar(ps_opt.period, ps_opt.queue_max, color=RED)
ax[1].set_ylabel("Макс. довжина черги, покупців")
ax[1].set_title("Максимальна черга по періодах")
for a in ax:
    a.tick_params(axis="x", rotation=25)
plt.tight_layout()
plt.savefig(FIG + "s2_100_periods.png", dpi=150)
plt.close()

fig, ax = plt.subplots(1, 3, figsize=(11, 3.4))
ax[0].hist(ds_opt.mean_wait, bins=15, color=BLUE, edgecolor="white")
ax[0].set_title("Середнє очікування за добу")
ax[0].set_xlabel("хв")
ax[1].hist(ds_opt.max_wait, bins=15, color=ORANGE, edgecolor="white")
ax[1].set_title("Максимальне очікування за добу")
ax[1].set_xlabel("хв")
ax[2].hist(ds_opt.queue_max, bins=12, color=RED, edgecolor="white")
ax[2].set_title("Максимальна черга")
ax[2].set_xlabel("покупців")
ax[0].set_ylabel("кількість прогонів")
plt.tight_layout()
plt.savefig(FIG + "s2_100_hist.png", dpi=150)
plt.close()

fig, ax = plt.subplots(1, 2, figsize=(10, 3.6))
allc = pd.concat(dfs_opt, ignore_index=True)
ax[0].hist(allc.wait, bins=40, color=BLUE, edgecolor="white", log=True)
ax[0].axvline(m.MAX_WAIT, color=RED, ls="--")
ax[0].set_xlabel("Час очікування, хв")
ax[0].set_ylabel("Кількість покупців (лог. шкала)")
ax[0].set_title("Розподіл очікування (усі 100 прогонів)")
reg = allc.groupby("register").size() / N_RUNS
ax[1].bar(reg.index.astype(str), reg.values, color=GREEN)
ax[1].set_xlabel("Номер каси")
ax[1].set_ylabel("Обслуговано за добу (середнє)")
ax[1].set_title("Навантаження на каси")
plt.tight_layout()
plt.savefig(FIG + "s2_wait_dist.png", dpi=150)
plt.close()
print("Етап 2 завершено.")
