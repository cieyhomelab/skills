#!/usr/bin/env python3
"""Deterministic calculations for the mk-estimate skill.

Usage:
  python3 scripts/estimate.py estimate  --input <file.json> [--config <estimate.config.json>]
  python3 scripts/estimate.py calibrate --input <file.json> [--config <estimate.config.json>]

The script reads the default values from references/default-config.md and the
prices from references/model-prices.md (the first JSON block in each file).
It writes one JSON object to stdout. On an input error it writes a message to
stderr and exits with code 2. It needs Python 3.9 or later and no packages.
"""
import argparse
import json
import math
import re
import statistics
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SIZES = ("S", "M", "L")
PHASES = ("setup", "discovery", "backlog", "designSystem", "prototype")
CALENDAR_DAYS_PER_MONTH = 20  # working days in one month of a subscription


def fail(message):
    sys.stderr.write(f"mk-estimate: {message}\n")
    sys.exit(2)


def json_block(path):
    text = path.read_text(encoding="utf-8")
    match = re.search(r"```json\n(.*?)\n```", text, re.S)
    if not match:
        fail(f"no JSON block in {path}")
    return json.loads(match.group(1))


def merge(base, override):
    result = dict(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(config_path):
    defaults = json_block(SKILL_DIR / "references" / "default-config.md")
    user = {}
    if config_path:
        path = Path(config_path)
        if path.exists():
            user = json.loads(path.read_text(encoding="utf-8"))
    used_defaults = sorted(k for k in defaults if k not in user)
    return merge(defaults, user), used_defaults


def r2(value):
    return round(value + 0.0, 4)


def size_hours(cfg, target, size):
    if size not in SIZES:
        fail(f"size '{size}' is not one of {', '.join(SIZES)}")
    mvp = cfg["hours"]["mvp"][size]
    poc_table = cfg["hours"].get("poc")
    if target == "mvp":
        return dict(mvp)
    if poc_table and size in poc_table:
        return dict(poc_table[size])
    return {
        "human": mvp["human"] * cfg["poc"]["humanFactor"],
        "agent": mvp["agent"] * cfg["poc"]["agentFactor"],
        "spec": mvp["spec"] * cfg["poc"]["humanFactor"],
    }


# --------------------------------------------------------------------- estimate

def work_item_rows(cfg, target, items):
    rows, split_first = [], []
    for item in items:
        item_id = str(item.get("id", "")).strip()
        if not item_id:
            fail("a work item has no 'id'")
        size = item.get("size")
        in_flight = bool(item.get("inFlight"))
        if size == "XL" and not in_flight:
            split_first.append(item_id)
            continue
        cost_size = "L" if size == "XL" else size
        hours = size_hours(cfg, target, cost_size)
        if in_flight:
            human = hours["human"] - hours["spec"]
            agent = cfg["finishing"]["agentShare"] * hours["agent"]
            kind = "inFlight"
        else:
            spec_done = bool(item.get("fix")) or bool(item.get("specMerged"))
            human = hours["human"] - (hours["spec"] if spec_done else 0)
            agent = hours["agent"]
            kind = "offBacklog" if item.get("offBacklog") else "backlog"
        rows.append({
            "id": item_id, "size": size, "costedAs": cost_size, "kind": kind,
            "human": r2(human), "agent": r2(agent),
        })
    return rows, split_first


def phase_rows(cfg, target, todo, open_epics):
    rows = []
    for name in todo:
        if name not in PHASES:
            fail(f"phase '{name}' is not one of {', '.join(PHASES)}")
        human = cfg["phases"][name][target]
        agent = human * cfg["phases"]["agentShare"].get(name, 0)
        rows.append({"id": f"phase:{name}", "human": r2(human), "agent": r2(agent)})
    if open_epics:
        human = cfg["phases"]["perEpic"][target] * open_epics
        rows.append({"id": "phase:perEpic", "human": r2(human), "agent": 0.0})
    return rows


def question_rows(cfg, questions, by_id, subtotal):
    rows = []
    for question in questions:
        blocks = question.get("blocks") or []
        missing = [b for b in blocks if b not in by_id]
        if missing:
            fail(f"question {question.get('id')} blocks unknown ids {missing}; known: {sorted(by_id)}")
        if blocks:
            share = cfg["buffer"]["perBlockingQuestion"]
            human = share * sum(by_id[b]["human"] for b in blocks)
            agent = share * sum(by_id[b]["agent"] for b in blocks)
            scoped = True
        else:
            share = cfg["buffer"]["perUnscopedQuestion"]
            human, agent = share * subtotal["human"], share * subtotal["agent"]
            scoped = False
        rows.append({"id": question.get("id"), "blocks": blocks, "scoped": scoped,
                     "human": r2(human), "agent": r2(agent)})
    return rows


def resolve_prices(cfg, given):
    if given == "none":
        return None
    if isinstance(given, dict):
        source = dict(given)
        source.setdefault("source", "interview")
        return source
    catalog = json_block(SKILL_DIR / "references" / "model-prices.md")
    return {"source": "catalog", "asOf": catalog["asOf"], "currency": catalog["currency"],
            "models": catalog["models"], "seatPrice": catalog["seats"].get(cfg["seat"]),
            "seat": cfg["seat"]}


def cost(cfg, agent_hours, sprints, devs, prices):
    tok = cfg["tokens"]
    factor = 1 + tok["reviewOverhead"]
    tokens_in = agent_hours * tok["inputPerAgentHour"] * factor
    tokens_out = agent_hours * tok["outputPerAgentHour"] * factor
    result = {"apiTokens": round(tokens_in + tokens_out), "api": None, "apiByTier": {},
              "subscription": None, "months": math.ceil(sprints * cfg["sprint"]["days"] / CALENDAR_DAYS_PER_MONTH)}
    if prices is None:
        return result
    total, priced = 0.0, True
    for tier, model in cfg["models"].items():
        p = (prices.get("models") or {}).get(model["id"])
        if not p:
            result["apiByTier"][tier] = None
            priced = False
            continue
        share = model["share"]
        cached = tokens_in * share * tok["cachedShare"]
        uncached = tokens_in * share * (1 - tok["cachedShare"])
        out = tokens_out * share
        value = (cached * p["cachedInput"] + uncached * p["input"] + out * p["output"]) / 1_000_000
        result["apiByTier"][tier] = round(value, 2)
        total += value
    result["api"] = round(total, 2) if priced else None
    seat = prices.get("seatPrice")
    if seat is not None:
        result["subscription"] = round(devs * result["months"] * seat, 2)
    return result


def run_estimate(cfg, data):
    target = data.get("target")
    if target not in ("poc", "mvp"):
        fail("'target' must be 'poc' or 'mvp'")
    mode = data.get("mode", "artifacts")
    devs = int(data.get("devs", cfg["team"]["devs"]))
    if not 1 <= devs <= 50:
        fail("'devs' must be an integer from 1 to 50")
    epic_scoped = bool(data.get("epicScoped"))

    items, split_first = work_item_rows(cfg, target, data.get("workItems", []))
    phases = phase_rows(cfg, target, data.get("phasesToDo", []), int(data.get("openEpics", 0)))
    by_id = {row["id"]: row for row in items + phases}

    def total(rows, clock):
        return sum(row[clock] for row in rows)

    subtotal = {clock: total(items, clock) + total(phases, clock) for clock in ("human", "agent")}
    base_share = cfg["buffer"][target] + (cfg["buffer"]["earlyExtra"] if mode == "early" else 0)
    base = {clock: base_share * subtotal[clock] for clock in subtotal}
    questions = question_rows(cfg, data.get("blockingQuestions", []), by_id, subtotal)
    qbuf = {clock: total(questions, clock) for clock in subtotal}
    after_buffer = {clock: subtotal[clock] + base[clock] + qbuf[clock] for clock in subtotal}

    share = cfg["unplanned"]["share"]
    if share is None or epic_scoped:
        allowance = {"human": 0.0, "agent": 0.0}
    else:
        allowance = {clock: share * after_buffer[clock] for clock in subtotal}
    grand = {clock: after_buffer[clock] + allowance[clock] for clock in subtotal}

    cap_human = cfg["sprint"]["days"] * cfg["sprint"]["focusHoursPerDay"] * devs
    cap_agent = cfg["agents"]["parallelPerDev"] * cfg["agents"]["hoursPerDay"] * cfg["sprint"]["days"] * devs
    ratio = {"human": grand["human"] / cap_human, "agent": grand["agent"] / cap_agent}
    binding = "human" if ratio["human"] >= ratio["agent"] else "agent"
    sprints = max(1, math.ceil(max(ratio.values()) - 1e-9))

    chain = data.get("chain", [])
    unknown = [c for c in chain if c not in by_id]
    if unknown:
        fail(f"chain has unknown ids {unknown}")
    floor_days = sum(by_id[c]["agent"] for c in chain) / cfg["agents"]["hoursPerDay"]
    floor_sprints = math.ceil(floor_days / cfg["sprint"]["days"] - 1e-9) if floor_days else 0
    floor_binds = floor_sprints > sprints
    if floor_binds:
        sprints = floor_sprints

    prices = resolve_prices(cfg, data.get("prices"))
    money = cost(cfg, grand["agent"], sprints, devs, prices)

    result = {
        "target": target, "mode": mode, "devs": devs,
        "sprints": sprints, "weeks": sprints * 2, "bindingClock": "dependency" if floor_binds else binding,
        "ratio": {k: r2(v) for k, v in ratio.items()},
        "capacity": {"human": cap_human, "agent": cap_agent},
        "workItems": items, "splitFirst": split_first, "phases": phases, "questions": questions,
        "human": {"phases": r2(total(phases, "human")), "items": r2(total(items, "human")),
                  "baseBuffer": r2(base["human"]), "questionBuffer": r2(qbuf["human"]),
                  "unplanned": r2(allowance["human"]), "total": r2(grand["human"])},
        "agent": {"phases": r2(total(phases, "agent")), "items": r2(total(items, "agent")),
                  "baseBuffer": r2(base["agent"]), "questionBuffer": r2(qbuf["agent"]),
                  "unplanned": r2(allowance["agent"]), "total": r2(grand["agent"])},
        "baseBufferShare": r2(base_share),
        "dependencyFloor": {"chain": chain, "days": r2(floor_days), "binds": floor_binds},
        "cost": money,
        "prices": prices and {k: v for k, v in prices.items() if k != "models"} | {
            "models": {cfg["models"][t]["id"]: (prices.get("models") or {}).get(cfg["models"][t]["id"]) for t in cfg["models"]}},
        "hoursUsed": {"hours": cfg["hours"], "finishing": cfg["finishing"], "buffer": cfg["buffer"]},
    }
    if mode == "early":
        spread = cfg["buffer"]["earlyRange"]
        result["range"] = {clock: [r2(grand[clock] * (1 - spread)), r2(grand[clock] * (1 + spread))] for clock in grand}
    return result


# -------------------------------------------------------------------- calibrate

def round_half(value):
    return round(value * 2) / 2


def calibrate_clock(cfg, clock, items, sprints, target):
    cal = cfg["calibration"]
    damping, low, high = cal["damping"], cal["clamp"][0], cal["clamp"][1]
    sized = [i for i in items if not i.get("inFlight") and i.get(f"{clock}Actual") is not None]
    points = len(sized) + (len(sprints) if clock == "human" else 0)
    out = {"points": points, "factors": {}, "proposed": {}, "outOfClamp": [], "basis": None}
    if points < cal["minSamplesGlobal"]:
        out["basis"] = "none"
        return out

    def ratio(item):
        return item[f"{clock}Actual"] / item[f"{clock}Estimated"]

    weights, ratios = [], []
    for item in sized:
        weights.append(item[f"{clock}Estimated"] * (0.5 if item.get("approx") else 1))
        ratios.append(ratio(item))
    if clock == "human":
        for sprint in sprints:
            weights.append(sprint["estimated"])
            ratios.append(sprint["capacity"] / sprint["estimated"])
    global_factor = sum(w * r for w, r in zip(weights, ratios)) / sum(weights)

    out["basis"] = "global"
    for size in SIZES:
        exact = [ratio(i) for i in sized if i["size"] == size and not i.get("approx")]
        if len(exact) >= cal["minSamples"]:
            factor = statistics.median([ratio(i) for i in sized if i["size"] == size])
            out["basis"] = "per-size"
        else:
            factor = global_factor
        out["factors"][size] = r2(factor)
        current = size_hours(cfg, target, size)[clock]
        if factor < low or factor > high:
            out["outOfClamp"].append({"size": size, "factor": r2(factor),
                                      "items": [i["id"] for i in sized if i["size"] == size]})
            continue
        out["proposed"][size] = {"current": current, "proposed": round_half(current * (1 + damping * (factor - 1)))}
        if clock == "human":
            spec = cfg["hours"]["mvp"][size]["spec"] if target == "mvp" else size_hours(cfg, target, size)["spec"]
            out["proposed"][size]["specProposed"] = round_half(spec * (1 + damping * (factor - 1)))
    return out


def run_calibrate(cfg, data):
    target = data.get("target", "mvp")
    items = data.get("items", [])
    sprints = data.get("sprints", [])
    for item in items:
        if item.get("size") not in SIZES:
            fail(f"calibration item {item.get('id')} has size {item.get('size')}; use the costed size S, M or L")
    result = {"target": target,
              "human": calibrate_clock(cfg, "human", items, sprints, target),
              "agent": calibrate_clock(cfg, "agent", items, sprints, target)}

    finishing = [i["agentActual"] / i["agentEstimated"] for i in items
                 if i.get("inFlight") and i.get("agentActual") is not None]
    if len(finishing) >= cfg["calibration"]["minSamplesGlobal"]:
        current = cfg["finishing"]["agentShare"]
        factor = statistics.median(finishing)
        result["finishing"] = {"factor": r2(factor),
                               "proposed": round(current * (1 + cfg["calibration"]["damping"] * (factor - 1)), 2)}

    base = cfg["buffer"][target]
    checked = [i for i in items if not i.get("inFlight") and i.get("humanActual") is not None]
    if len(checked) >= cfg["calibration"]["minSamplesGlobal"]:
        over = [i for i in checked if i["humanActual"] > i["humanEstimated"] * (1 + base) + i.get("questionHours", 0)]
        share = len(over) / len(checked)
        change = 0.10 if share > 0.30 else (-0.05 if share < 0.10 else 0.0)
        result["bufferCheck"] = {"overShare": r2(share), "current": base, "proposed": r2(base + change) if change else None}

    unplanned = data.get("unplanned")
    if unplanned and unplanned.get("deliveredHours"):
        measured = unplanned["hours"] / unplanned["deliveredHours"]
        enough = unplanned.get("items", 0) >= 3 or unplanned.get("windows", 0) >= cfg["calibration"]["minSamplesGlobal"]
        current = cfg["unplanned"]["share"]
        proposed = measured if current is None else current + cfg["calibration"]["damping"] * (measured - current)
        result["unplanned"] = {"measured": r2(measured), "warn": measured > 0.20,
                               "proposed": round(round(proposed / 0.05) * 0.05, 2) if enough else None}

    diff = {}
    for clock in ("human", "agent"):
        for size, values in result[clock]["proposed"].items():
            node = diff.setdefault("hours", {}).setdefault(target, {}).setdefault(size, {})
            if values["proposed"] != values["current"]:
                node[clock] = values["proposed"]
                if clock == "human":
                    node["spec"] = values["specProposed"]
    if "finishing" in result:
        diff["finishing"] = {"agentShare": result["finishing"]["proposed"]}
    if result.get("bufferCheck", {}).get("proposed") is not None:
        diff["buffer"] = {target: result["bufferCheck"]["proposed"]}
    if result.get("unplanned", {}).get("proposed") is not None:
        diff["unplanned"] = {"share": result["unplanned"]["proposed"]}
    result["diff"] = {k: v for k, v in diff.items() if v and v != {target: {}}}
    if "hours" in result["diff"]:
        result["diff"]["hours"] = {t: {s: v for s, v in sizes.items() if v} for t, sizes in result["diff"]["hours"].items()}
    return result


def main():
    parser = argparse.ArgumentParser(description="mk-estimate calculations")
    parser.add_argument("command", choices=["estimate", "calibrate"])
    parser.add_argument("--input", required=True, help="path to the input JSON file")
    parser.add_argument("--config", default=".ai/estimate.config.json", help="path to the estimate config")
    args = parser.parse_args()
    try:
        data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        fail(f"cannot read the input file: {error}")
    cfg, used_defaults = load_config(args.config)
    result = run_estimate(cfg, data) if args.command == "estimate" else run_calibrate(cfg, data)
    result["defaultsUsed"] = used_defaults
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
