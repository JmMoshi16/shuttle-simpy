# Shuttle Logic — Code Explanation
**Baclig, Kheil Davies | Co-Coder (Shuttle Logic)**

---

## What This File Does

`shuttle_logic.py` is the core engine of the shuttle simulation. It controls how the shuttle loads passengers and decides when to depart, using **SimPy** — a Python-based discrete-event simulation library.

---

## Parameters

|       Parameter     | Value |              Meaning                        |
|---------------------|-------|---------------------------------------------|
| `CAPACITY`          |   14  | Max passengers per shuttle trip             |
| `SCHEDULE_INTERVAL` |   15  | Minutes before a scheduled forced departure |
| `SIM_DURATION`      |   120 | Total simulation runtime in minutes         |
| `ARRIVAL_RATE`      |   1.5 | Minutes between each passenger arrival      |

---

## How the Code Works

### 1. `passenger_arrival(env, queue, log)`

This process runs continuously throughout the simulation. Every **1.5 minutes**, a new passenger is generated and placed into the queue.

- Passengers are added to a `simpy.Store`, which is a **FIFO (First-In, First-Out)** queue — meaning the first passenger to arrive is the first to board.
- Each passenger's ID and arrival time are saved into `log["arrivals"]` for later analysis by the data collection module.

```python
yield env.timeout(ARRIVAL_RATE)   # wait 1.5 min
yield queue.put({"id": pid, "arrival_time": arrival_time})  # join queue
```

---

### 2. `shuttle_process(env, queue, log)`

This is the main shuttle logic. It runs in a loop — each iteration represents **one shuttle trip**.

#### Dual-Departure Trigger (Step 2)

At the start of every trip, a **15-minute countdown timer** is created:

```python
timer = env.timeout(SCHEDULE_INTERVAL)
```

The shuttle then waits for passengers using a **conditional event**:

```python
result = yield passenger_event | timer
```

This line means: *"Wait for the next passenger OR the timer — whichever happens first."*

- If a **passenger arrives first** → they board the shuttle.
- If the **timer expires first** → the shuttle departs immediately, even if not full.
- If the shuttle reaches **14 passengers** before the timer → it also departs immediately.

This is the dual-departure trigger: **capacity (14 seats) OR timer (15 min)**.

#### FIFO Boarding (Step 3)

Because `simpy.Store` preserves insertion order, passengers always board in the order they arrived — no priority jumping. After each departure, the timer resets automatically because a **new `env.timeout()`** is created at the top of the next loop iteration.

#### Trip Logging

After each departure, the trip details are saved:

```python
log["trips"].append({
    "trip": trip_number,
    "depart_time": env.now,
    "boarded": len(boarded),
    "reason": departure_reason,   # "capacity" or "timer"
    "left_behind": len(queue.items),
})
```

This data feeds directly into Terrenal's metrics module for calculating wait times, occupancy rates, and left-behind counts.

---

### 3. `run_simulation()`

Sets up the SimPy environment, creates the shared queue and log, starts both processes, and runs the simulation for 120 minutes.

```python
env = simpy.Environment()
queue = simpy.Store(env)
env.process(passenger_arrival(env, queue, log))
env.process(shuttle_process(env, queue, log))
env.run(until=SIM_DURATION)
```

At the end, it prints a summary and returns the full log for further processing.

---

## Sample Console Output

```
[t= 15.00] Trip   1 departed | Boarded:  10/14 | Reason: timer    | Left behind: 0
[t= 21.00] Trip   2 departed | Boarded:  14/14 | Reason: capacity | Left behind: 3
```

- Trip 1 departed because the 15-min timer expired before 14 passengers arrived.
- Trip 2 departed because the shuttle filled up before the timer ran out.

---

## How This Connects to the Group's Work

| Module          | How It Uses This File |
|-----------------|---|
| **Jurado**      | Merges this file into the main executable script |
| **Terrenal**    | Reads `log["trips"]` and `log["arrivals"]` to compute metrics |
| **Pauli**       | Calls `run_simulation()` 5 times for the replications experiment |
| **Liscano**     | Uses `CAPACITY` and `SCHEDULE_INTERVAL` parameters to desig controlled test cases |
