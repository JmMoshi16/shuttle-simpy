"""
Case E: Shuttle Loading Area — SimPy Discrete-Event Simulation
=============================================================
Sections:
  1. Imports & Config
  2. Data Collector
  3. Shuttle Dual-Trigger Logic
  4. Passenger Generator
  5. Environment Setup
  6. Replication Runner
  7. Verification Mode
  8. Main Entry Point
"""

# ─────────────────────────────────────────────
# 1. IMPORTS & CONFIG
# ─────────────────────────────────────────────
import simpy
import random
import statistics
from dataclasses import dataclass

@dataclass
class Config:
    sim_time     : float = 480.0   # minutes (8-hour day)
    capacity     : int   = 14      # max passengers per shuttle
    schedule_int : float = 15.0    # scheduled departure interval (minutes)
    mean_interarr: float = 1.5     # mean inter-arrival time (minutes)

SEEDS = [42, 7, 123, 256, 999]


# ─────────────────────────────────────────────
# 2. DATA COLLECTOR
# ─────────────────────────────────────────────
class DataCollector:
    """Accumulates per-trip and per-passenger metrics."""
    def __init__(self):
        self.wait_times  = []
        self.left_behind = []
        self.occupancies = []
        self.trips       = 0

    def record_trip(self, capacity, boarded, left, board_times, depart_time):
        self.trips += 1
        self.left_behind.append(left)
        self.occupancies.append(boarded / capacity)
        for arr_time in board_times:
            self.wait_times.append(depart_time - arr_time)

    def summary(self):
        return {
            "avg_wait"      : statistics.mean(self.wait_times)  if self.wait_times  else 0.0,
            "avg_left"      : statistics.mean(self.left_behind) if self.left_behind else 0.0,
            "avg_occupancy" : statistics.mean(self.occupancies) if self.occupancies else 0.0,
            "trips"         : self.trips,
        }


# ─────────────────────────────────────────────
# 3. SHUTTLE DUAL-TRIGGER LOGIC
# ─────────────────────────────────────────────
class ShuttleController:
    """
    Runs shuttle cycles with dual-trigger departure logic:
      - Capacity trigger : queue length reaches cfg.capacity
      - Schedule trigger : cfg.schedule_int minutes elapse since last departure
    Whichever fires first causes an immediate departure.
    """
    def __init__(self, env, cfg, collector, verbose=False):
        self.env            = env
        self.cfg            = cfg
        self.collector      = collector
        self.verbose        = verbose
        self.queue          = []           # passenger arrival timestamps (FIFO)
        self.capacity_event = env.event()  # signalled when queue hits capacity

    def _log(self, msg):
        if self.verbose:
            print(f"  t={self.env.now:7.3f} | {msg}")

    def passenger_arrives(self, pid):
        """Enqueue a passenger; fire capacity event if threshold reached."""
        self.queue.append(self.env.now)
        self._log(f"Passenger {pid:4d} arrives  — queue size: {len(self.queue)}")
        if len(self.queue) >= self.cfg.capacity and not self.capacity_event.triggered:
            self.capacity_event.succeed()

    def run(self):
        """Main shuttle cycle loop — runs until sim_time is exceeded."""
        trip = 0
        while self.env.now < self.cfg.sim_time:
            trip += 1
            self.capacity_event = self.env.event()   # fresh event each cycle

            # ── DUAL TRIGGER (AnyOf): capacity OR scheduled timeout ──
            timer   = self.env.timeout(self.cfg.schedule_int)
            yield self.capacity_event | timer        # blocks until first fires

            # ── DEPARTURE ──
            depart_time = self.env.now
            boarded     = min(len(self.queue), self.cfg.capacity)
            board_times = [self.queue.pop(0) for _ in range(boarded)]
            left        = len(self.queue)

            # When both fire simultaneously, capacity takes logical priority
            reason = "CAPACITY" if self.capacity_event.triggered else "SCHEDULE"
            self._log(
                f"Trip {trip:3d} departs [{reason}] — "
                f"boarded={boarded}, left_behind={left}, "
                f"occupancy={boarded/self.cfg.capacity:.0%}"
            )
            self.collector.record_trip(
                self.cfg.capacity, boarded, left, board_times, depart_time
            )


# ─────────────────────────────────────────────
# 4. PASSENGER GENERATOR
# ─────────────────────────────────────────────
def passenger_generator(env, cfg, shuttle, rng):
    """Poisson arrival process: exponential inter-arrival times."""
    pid = 0
    while True:
        yield env.timeout(rng.expovariate(1.0 / cfg.mean_interarr))
        if env.now > cfg.sim_time:
            break
        pid += 1
        shuttle.passenger_arrives(pid)


# ─────────────────────────────────────────────
# 5. ENVIRONMENT SETUP
# ─────────────────────────────────────────────
def run_simulation(seed, cfg=None, verbose=False):
    """
    Initialises SimPy environment and runs one replication.
    Returns a summary dict of performance metrics.
    """
    if cfg is None:
        cfg = Config()

    env       = simpy.Environment()
    rng       = random.Random(seed)
    collector = DataCollector()
    shuttle   = ShuttleController(env, cfg, collector, verbose=verbose)

    env.process(passenger_generator(env, cfg, shuttle, rng))
    env.process(shuttle.run())
    # Run slightly past sim_time so the last scheduled cycle can complete
    env.run(until=cfg.sim_time + cfg.schedule_int)

    return collector.summary()


# ─────────────────────────────────────────────
# 6. REPLICATION RUNNER
# ─────────────────────────────────────────────
def run_replications(cfg=None):
    """Runs 5 independent replications and prints a formatted summary table."""
    if cfg is None:
        cfg = Config()

    results = [run_simulation(seed, cfg) for seed in SEEDS]

    metrics = [
        ("avg_wait",      "Avg Wait Time (min)"),
        ("avg_left",      "Avg Left-Behind / Trip"),
        ("avg_occupancy", "Avg Occupancy Rate"),
        ("trips",         "Total Completed Trips"),
    ]

    print("\n" + "=" * 65)
    print("  REPLICATION SUMMARY  (5 independent runs)")
    print("=" * 65)
    print(f"  {'Metric':<28} {'Mean':>8}  {'Min':>8}  {'Max':>8}")
    print("-" * 65)

    for key, label in metrics:
        vals = [r[key] for r in results]
        mean, mn, mx = statistics.mean(vals), min(vals), max(vals)
        if key == "trips":
            print(f"  {label:<28} {mean:>8.1f}  {mn:>8.0f}  {mx:>8.0f}")
        elif key == "avg_occupancy":
            print(f"  {label:<28} {mean:>7.1%}  {mn:>7.1%}  {mx:>7.1%}")
        else:
            print(f"  {label:<28} {mean:>8.3f}  {mn:>8.3f}  {mx:>8.3f}")

    print("=" * 65)
    print(f"\n  {'Rep':<5} {'Seed':<6} {'AvgWait':>9} {'AvgLeft':>9} {'Occupancy':>10} {'Trips':>7}")
    print("  " + "-" * 48)
    for i, (seed, r) in enumerate(zip(SEEDS, results), 1):
        print(
            f"  {i:<5} {seed:<6} "
            f"{r['avg_wait']:>9.3f} "
            f"{r['avg_left']:>9.3f} "
            f"{r['avg_occupancy']:>9.1%} "
            f"{r['trips']:>7}"
        )
    print()


# ─────────────────────────────────────────────
# 7. VERIFICATION MODE
# ─────────────────────────────────────────────
def run_verification():
    """
    Controlled trace: capacity=1 forces every single arrival to immediately
    trigger a CAPACITY departure, making the dual-trigger logic trivially
    verifiable line-by-line. Runs 10 simulated minutes with seed=42.
    """
    vcfg = Config(sim_time=10.0, capacity=1, schedule_int=15.0, mean_interarr=1.5)

    print("\n" + "=" * 65)
    print("  VERIFICATION MODE  (capacity=1, sim_time=10 min, seed=42)")
    print("  Each arrival must trigger an immediate CAPACITY departure.")
    print("=" * 65)
    result = run_simulation(seed=42, cfg=vcfg, verbose=True)
    print(f"\n  Summary: {result}")
    print("=" * 65)


# ─────────────────────────────────────────────
# 8. MAIN ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    run_verification()
    run_replications()
