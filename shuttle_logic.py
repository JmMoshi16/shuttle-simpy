"""
shuttle_logic.py
Baclig, Kheil Davies — Co-Coder (Shuttle Logic)

Responsibilities:
  Step 1: SimPy shuttle process managing vehicle arrivals and loading loops.
  Step 2: Dual-departure trigger — depart when count == 14 OR 15-min timer expires.
  Step 3: FIFO queue boarding logic and shuttle timer reset after each departure.
"""

import simpy

CAPACITY = 14           # max seats per shuttle
SCHEDULE_INTERVAL = 15  # minutes between scheduled departures
SIM_DURATION = 120      # total simulation time (minutes)
ARRIVAL_RATE = 1.5      # minutes between passenger arrivals


def shuttle_process(env, queue, log):
    """
    Manages one shuttle cycle at a time.
    Departs when queue fills to CAPACITY or the 15-min schedule timer expires.
    Resets the timer after every departure (new timeout each loop iteration).
    """
    trip_number = 0

    while True:
        trip_number += 1
        boarded = []

        # --- Step 2: Dual-departure trigger (timer resets each trip) ---
        timer = env.timeout(SCHEDULE_INTERVAL)

        while len(boarded) < CAPACITY:
            passenger_event = queue.get()

            # Wait for next passenger OR timer expiry — whichever comes first
            result = yield passenger_event | timer

            if passenger_event in result:
                # Step 3: FIFO — passengers board in arrival order (Store is FIFO by default)
                boarded.append(result[passenger_event])
            else:
                # Timer expired before capacity reached — cancel pending get and depart
                passenger_event.cancel()
                break

            # Capacity reached — depart immediately
            if len(boarded) >= CAPACITY:
                break

        departure_reason = "capacity" if len(boarded) >= CAPACITY else "timer"

        # Log trip for Terrenal's data collection module
        log["trips"].append({
            "trip": trip_number,
            "depart_time": env.now,
            "boarded": len(boarded),
            "reason": departure_reason,
            "left_behind": len(queue.items),
        })

        print(
            f"[t={env.now:6.2f}] Trip {trip_number:>3} departed | "
            f"Boarded: {len(boarded):>2}/{CAPACITY} | "
            f"Reason: {departure_reason:<8} | "
            f"Left behind: {len(queue.items)}"
        )
        # Timer resets automatically — new timeout created at top of next loop


def passenger_arrival(env, queue, log):
    """Generates passengers at fixed inter-arrival intervals and joins the FIFO queue."""
    pid = 0
    while True:
        yield env.timeout(ARRIVAL_RATE)
        pid += 1
        arrival_time = env.now
        log["arrivals"].append({"id": pid, "arrival_time": arrival_time})
        yield queue.put({"id": pid, "arrival_time": arrival_time})


def run_simulation():
    env = simpy.Environment()
    queue = simpy.Store(env)  # unbounded FIFO store — preserves arrival order

    log = {"arrivals": [], "trips": []}

    env.process(passenger_arrival(env, queue, log))
    env.process(shuttle_process(env, queue, log))

    env.run(until=SIM_DURATION)

    print("\n--- Simulation Complete ---")
    print(f"Total passengers arrived : {len(log['arrivals'])}")
    print(f"Total trips completed    : {len(log['trips'])}")
    return log


if __name__ == "__main__":
    run_simulation()
