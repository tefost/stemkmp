"""
Спільне ядро імітаційної моделі касової зони цілодобового супермаркету

"""
from collections import deque

import numpy as np
import pandas as pd




STEP = 20                     
DAY_MIN = 24 * 60            
N_STEPS = DAY_MIN // STEP    
MAX_REGISTERS = 5            

MAX_WAIT = 10.0              
ALLOWED_SHARE = 0.05         


ITEMS_N = 30
ITEMS_P = 0.4


T0 = 0.4                     
T_ITEM = 0.25                


PERIODS = [
    ("Нічна зміна",   0,  6,  3),
    ("Ранковий пік",  6, 10, 19),
    ("Денний спад",  10, 16, 11),
    ("Вечірній пік", 16, 21, 24),
    ("Пізній вечір", 21, 24,  7),
]
PERIOD_NAMES = [p[0] for p in PERIODS]


def period_of_step(step):
    hour = (step * STEP) / 60.0
    for i, (_, h0, h1, _) in enumerate(PERIODS):
        if h0 <= hour < h1:
            return i
    return len(PERIODS) - 1


def period_of_minute(minute):
    return period_of_step(int(minute // STEP) if minute < DAY_MIN else N_STEPS - 1)


def lambda_vector(scale=1.0, divisor=1.0):
    return [PERIODS[period_of_step(s)][3] * scale / divisor for s in range(N_STEPS)]


def schedule_vector(per_period):

    return [per_period[period_of_step(s)] for s in range(N_STEPS)]


def mean_service_time():
    return T0 + T_ITEM * ITEMS_N * ITEMS_P


def service_cv2():
    var = (T_ITEM ** 2) * ITEMS_N * ITEMS_P * (1 - ITEMS_P)
    return var / mean_service_time() ** 2





class Customer:
    def __init__(self, arrival, rng, t_item=T_ITEM):
        self.arrival = arrival
        self.items = max(1, int(rng.binomial(ITEMS_N, ITEMS_P)))
        self.service_time = T0 + t_item * self.items
        self.start = None


class Statistics:
    def __init__(self):
        self.rows = []
    def add(self, cid, customer, register):
        wait = customer.start - customer.arrival
        self.rows.append((cid, customer.arrival, customer.items, customer.service_time,
                          customer.start, wait, register,
                          period_of_minute(customer.arrival)))
    def to_df(self):
        return pd.DataFrame(self.rows, columns=["id", "arrival", "items", "service",
                                                 "start", "wait", "register", "period"])


class Supermarket:

    def __init__(self, registers, lam, rng, t_item=T_ITEM):
        assert len(registers) == N_STEPS and len(lam) == N_STEPS
        assert all(1 <= c <= MAX_REGISTERS for c in registers)
        self.registers = list(registers)
        self.lam = list(lam)
        self.rng = rng
        self.t_item = t_item
        self.queue = deque()
        self.free_at = [0.0] * MAX_REGISTERS     
        self.stats = Statistics()
        self.busy = np.zeros(N_STEPS + 200)      
        self.step_log = []
        self.counter = 0

    
    def customers_arrived(self, step):
        n = int(self.rng.poisson(self.lam[step]))
        t0 = step * STEP
        times = np.sort(self.rng.uniform(t0, t0 + STEP, size=n))
        for t in times:
            self.queue.append(Customer(float(t), self.rng, self.t_item))
        return n

    def _add_busy(self, start, finish):
        s = int(start // STEP)
        while s * STEP < finish:
            lo = max(start, s * STEP)
            hi = min(finish, (s + 1) * STEP)
            if hi > lo:
                self.busy[s] += hi - lo
            s += 1

    def serve(self, step):
        t0, t1 = step * STEP, (step + 1) * STEP
        c = self.registers[min(step, N_STEPS - 1)]
        served = 0
        while self.queue:
            head = self.queue[0]
            k = min(range(c), key=lambda i: self.free_at[i])
            start = max(self.free_at[k], head.arrival, t0)
            if start >= t1:
                break                       
            self.queue.popleft()
            head.start = start
            finish = start + head.service_time
            self.free_at[k] = finish
            self._add_busy(start, finish)
            self.counter += 1
            self.stats.add(self.counter, head, k + 1)
            served += 1
        return served

    
    def run(self):
        for step in range(N_STEPS):
            arrived = self.customers_arrived(step)
            served = self.serve(step)
            self.step_log.append({
                "step": step,
                "time": f"{(step * STEP) // 60:02d}:{(step * STEP) % 60:02d}",
                "period": PERIOD_NAMES[period_of_step(step)],
                "registers": self.registers[step],
                "arrived": arrived,
                "started_service": served,
                "queue_end": len(self.queue),
            })
    
        step = N_STEPS
        while self.queue and step < N_STEPS + 190:
            self.serve(step)
            step += 1
        log = pd.DataFrame(self.step_log)
        log["busy_min"] = self.busy[:N_STEPS]
        log["utilization"] = log["busy_min"] / (log["registers"] * STEP)
        return self.stats.to_df(), log




def simulate(registers, lam, seed, t_item=T_ITEM):
    rng = np.random.default_rng(seed)
    return Supermarket(registers, lam, rng, t_item).run()


def run_many(registers, lam, n_runs=100, seed0=1000, t_item=T_ITEM):
    dfs, logs = [], []
    for i in range(n_runs):
        df, log = simulate(registers, lam, seed0 + i, t_item)
        dfs.append(df)
        logs.append(log)
    return dfs, logs


def period_summary(dfs, logs):
    allc = pd.concat(dfs, ignore_index=True)
    rows = []
    n_runs = len(dfs)
    for p, name in enumerate(PERIOD_NAMES):
        sub = allc[allc.period == p]
        
        per_run_mean = [d[d.period == p].wait.mean() for d in dfs]
        util = np.mean([l[l.period == name].busy_min.sum() /
                        (l[l.period == name].registers.sum() * STEP) for l in logs])
        qmax = np.mean([l[l.period == name].queue_end.max() for l in logs])
        qavg = np.mean([l[l.period == name].queue_end.mean() for l in logs])
        rows.append({
            "period": name,
            "customers_per_run": len(sub) / n_runs,
            "mean_wait": sub.wait.mean(),
            "mean_wait_std_between_runs": float(np.nanstd(per_run_mean, ddof=1)),
            "p95_wait": sub.wait.quantile(0.95),
            "max_wait": float(np.mean([d[d.period == p].wait.max() for d in dfs])),
            "share_wait_gt_10": float((sub.wait > MAX_WAIT).mean()),
            "share_wait_gt_0": float((sub.wait > 1e-9).mean()),
            "utilization": float(util),
            "queue_avg": float(qavg),
            "queue_max": float(qmax),
        })
    return pd.DataFrame(rows)


def daily_summary(dfs, logs):
    rows = []
    for d, l in zip(dfs, logs):
        rows.append({
            "customers": len(d),
            "mean_wait": d.wait.mean(),
            "max_wait": d.wait.max(),
            "share_wait_gt_10": float((d.wait > MAX_WAIT).mean()),
            "queue_max": int(l.queue_end.max()),
            "utilization": l.busy_min.sum() / (l.registers.sum() * STEP),
            "register_hours": l.registers.sum() * STEP / 60,
        })
    return pd.DataFrame(rows)
