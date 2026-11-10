"""
Аналіз чутливості знайденого графіка кас до зміни інтенсивності потоку покупців

"""
import pandas as pd

import smo_model as m

sched = pd.read_csv("results/optimal_schedule.csv")
c_list = sched.registers_5pct.tolist()
rows = []
for scale in (0.9, 1.0, 1.1, 1.2, 1.3):
    dfs, logs = m.run_many(m.schedule_vector(c_list), m.lambda_vector(scale=scale), 100)
    ps = m.period_summary(dfs, logs)
    ds = m.daily_summary(dfs, logs).mean()
    row = {"scale": scale, "mean_wait_day": ds.mean_wait, "share_day": ds.share_wait_gt_10}
    for p, name in enumerate(m.PERIOD_NAMES):
        row["share_" + str(p)] = ps.share_wait_gt_10[p]
        row["wait_" + str(p)] = ps.mean_wait[p]
    rows.append(row)
out = pd.DataFrame(rows)
out.to_csv("results/s2_sensitivity.csv", index=False)
print(out.round(3).to_string())



rows = []
for p in range(len(c_list)):
    if c_list[p] == 1:
        continue                             
    trial = c_list.copy()
    trial[p] -= 1
    dfs, logs = m.run_many(m.schedule_vector(trial), m.lambda_vector(), 100)
    ps = m.period_summary(dfs, logs)
    rows.append({"changed_period": m.PERIOD_NAMES[p], "schedule": str(trial),
                 "share_in_changed": ps.share_wait_gt_10[p],
                 "max_share": ps.share_wait_gt_10.max(),
                 "ok": bool((ps.share_wait_gt_10 <= m.ALLOWED_SHARE).all())})
loc = pd.DataFrame(rows)
loc.to_csv("results/s2_local_check.csv", index=False)
print(loc.round(3).to_string())
