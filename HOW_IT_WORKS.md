# What Your Code Does, Step by Step

## Step 1 — Passengers Keep Showing Up
Every **~1.5 minutes**, a new passenger walks up and joins the line.
The arrivals are **random** (exponential distribution) — just like real life, sometimes 3 people show up close together, sometimes there's a gap.

---

## Step 2 — The Shuttle Waits with a Dual-Trigger Rule
The shuttle watches **two things at the same time**:

| Trigger | Condition | Action |
|---|---|---|
| Capacity Trigger | 14 people are in line | Depart immediately |
| Schedule Trigger | 15 minutes have passed | Depart anyway |

> **Whichever happens first wins.** This is the core logic of the simulation.

---

## Step 3 — When the Shuttle Leaves
- It takes up to **14 people** from the front of the line
- Anyone still in line gets counted as **left behind**
- A brand new shuttle cycle starts **immediately**

---

## Step 4 — The Code Tracks 4 Things the Whole Time

| Metric | What It Measures |
|---|---|
| Avg Wait Time | How long each person stood in line |
| Avg Left-Behind | How many people missed the shuttle per trip |
| Avg Occupancy Rate | How full each shuttle was (e.g. 69%) |
| Total Trips | How many shuttle runs happened in the 8-hour day |

---

## Step 5 — It Runs 5 Times with Different Random Seeds
- Like running the same experiment on **5 different days**
- Each run uses a different seed so the random arrivals are different
- The results are averaged to get **reliable conclusions**

```
  Rep   Seed     AvgWait   AvgLeft  Occupancy   Trips
  ------------------------------------------------
  1     42         7.067     0.000     65.6%      33
  2     7          7.046     0.000     70.8%      33
  3     123        7.461     0.000     72.7%      33
  4     256        7.398     0.000     68.0%      33
  5     999        7.140     0.000     69.9%      33
```

---

## The Bottom Line
You built a **virtual campus shuttle stop** that simulates an entire 8-hour day in seconds and measures how well it serves passengers — so you can make real decisions about improving it.
