"""
ЕТАП 1. Імітаційна модель одного каналу обслуговування (одна каса).

"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import smo_model as m

RES, FIG = "results/", "figures/"
N_RUNS = 100
REGS = [1] * m.N_STEPS                      
LAM1 = m.lambda_vector(divisor=5)

plt.rcParams.update({"font.size": 10, "axes.grid": True, "grid.alpha": 0.3})
BLUE, ORANGE, GREEN, RED = "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"



df1, log1 = m.simulate(REGS, LAM1, seed=1)
df1.to_csv(RES + "s1_run_customers.csv", index=False)
log1.to_csv(RES + "s1_run_log_steps.csv", index=False)
print("Один прогін: обслужено", len(df1), "клієнтів; середнє очікування %.2f хв; макс. черга %d"
      % (df1.wait.mean(), log1.queue_end.max()))

fig, ax = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
x = log1.step * m.STEP / 60
ax[0].bar(x, log1.arrived, width=m.STEP / 60 * 0.9, color=BLUE, align="edge")
ax[0].set_ylabel("Прийшло покупців за крок")
ax[0].set_title("Етап 1, один прогін: потік покупців і довжина черги до однієї каси")
ax[1].step(x, log1.queue_end, where="post", color=RED)
ax[1].set_ylabel("Довжина черги\nна кінець кроку")
ax[1].set_xlabel("Година доби")
ax[1].set_xticks(range(0, 25, 2))
for a in ax:
    for h in (6, 10, 16, 21):
        a.axvline(h, color="gray", ls=":", lw=1)
plt.tight_layout()
plt.savefig(FIG + "s1_run_queue.png", dpi=150)
plt.close()

fig, ax = plt.subplots(1, 3, figsize=(11, 3.4))
ax[0].hist(df1["items"], bins=range(0, 32), color=BLUE, edgecolor="white")
ax[0].set_title("Кількість товарів (біноміальний)")
ax[0].set_xlabel("товарів у покупця")
ax[1].hist(df1["service"], bins=20, color=GREEN, edgecolor="white")
ax[1].set_title("Час обслуговування")
ax[1].set_xlabel("хв")
ax[2].hist(df1["wait"], bins=25, color=ORANGE, edgecolor="white")
ax[2].set_title("Час очікування в черзі")
ax[2].set_xlabel("хв")
ax[0].set_ylabel("кількість покупців")
plt.tight_layout()
plt.savefig(FIG + "s1_run_hist.png", dpi=150)
plt.close()




dfs, logs = m.run_many(REGS, LAM1, N_RUNS)
ps = m.period_summary(dfs, logs)
ds = m.daily_summary(dfs, logs)
ps.to_csv(RES + "s1_period_summary.csv", index=False)
ds.to_csv(RES + "s1_daily_summary.csv", index=False)
print(ps.round(3).to_string())
print("За добу (середнє по 100 прогонах):")
print(ds.mean().round(3).to_string())

fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
ax[0].bar(ps.period, ps.mean_wait, yerr=ps.mean_wait_std_between_runs, color=BLUE, capsize=4)
ax[0].set_ylabel("Середній час очікування, хв")
ax[0].set_title("Очікування (середнє за 100 прогонів, ± σ)")
ax[1].bar(ps.period, ps.utilization * 100, color=GREEN)
ax[1].set_ylabel("Завантаженість каси, %")
ax[1].set_title("Завантаженість каси по періодах")
for a in ax:
    a.tick_params(axis="x", rotation=25)
plt.tight_layout()
plt.savefig(FIG + "s1_100_periods.png", dpi=150)
plt.close()

fig, ax = plt.subplots(1, 3, figsize=(11, 3.4))
ax[0].hist(ds.mean_wait, bins=15, color=BLUE, edgecolor="white")
ax[0].set_title("Середнє очікування за добу")
ax[0].set_xlabel("хв")
ax[1].hist(ds.queue_max, bins=12, color=RED, edgecolor="white")
ax[1].set_title("Максимальна довжина черги")
ax[1].set_xlabel("покупців")
ax[2].hist(ds.customers, bins=15, color=GREEN, edgecolor="white")
ax[2].set_title("Обслужено покупців за добу")
ax[2].set_xlabel("покупців")
ax[0].set_ylabel("кількість прогонів")
plt.tight_layout()
plt.savefig(FIG + "s1_100_hist.png", dpi=150)
plt.close()




allc = pd.concat(dfs, ignore_index=True)
checks = pd.DataFrame([
    ("Середня кількість товарів", m.ITEMS_N * m.ITEMS_P, allc["items"].mean()),
    ("Середній час обслуговування, хв", m.mean_service_time(), allc["service"].mean()),
    ("Клієнтів за добу", sum(LAM1), len(allc) / N_RUNS),
], columns=["Показник", "Теоретичне значення", "Вибіркове (100 прогонів)"])
checks.to_csv(RES + "s1_checks.csv", index=False)
print(checks.round(3).to_string())


def sweep(label, values, runner):
    rows = []
    for v in values:
        d, l = runner(v)
        s = m.daily_summary(d, l).mean()
        rows.append({label: v, "mean_wait": s.mean_wait, "share_wait_gt_10": s.share_wait_gt_10,
                     "queue_max": s.queue_max, "utilization": s.utilization, "customers": s.customers})
    return pd.DataFrame(rows)


scales = [0.5, 0.75, 1.0, 1.1, 1.25]
sw_lam = sweep("lam_scale", scales,
               lambda v: m.run_many(REGS, m.lambda_vector(scale=v, divisor=5), N_RUNS))
sw_lam.to_csv(RES + "s1_adequacy_lambda.csv", index=False)

tvals = [0.15, 0.20, 0.25, 0.30]
sw_t = sweep("t_item", tvals, lambda v: m.run_many(REGS, LAM1, N_RUNS, t_item=v))
sw_t.to_csv(RES + "s1_adequacy_titem.csv", index=False)
print(sw_lam.round(3).to_string())
print(sw_t.round(3).to_string())

fig, ax = plt.subplots(1, 2, figsize=(10, 3.6))
ax[0].plot(sw_lam.lam_scale, sw_lam.mean_wait, "o-", color=BLUE, label="середнє очікування, хв")
ax[0].plot(sw_lam.lam_scale, sw_lam.queue_max / 5, "s--", color=RED, label="макс. черга / 5")
ax[0].set_xlabel("Множник інтенсивності потоку покупців")
ax[0].set_title("Вплив інтенсивності потоку")
ax[0].legend()
ax[1].plot(sw_t.t_item * 60, sw_t.mean_wait, "o-", color=BLUE, label="середнє очікування, хв")
ax[1].plot(sw_t.t_item * 60, sw_t.queue_max / 5, "s--", color=RED, label="макс. черга / 5")
ax[1].set_xlabel("Час обслуговування одного товару, с")
ax[1].set_title("Вплив швидкості обслуговування")
ax[1].legend()
plt.tight_layout()
plt.savefig(FIG + "s1_adequacy.png", dpi=150)
plt.close()
print("Етап 1 завершено.")
