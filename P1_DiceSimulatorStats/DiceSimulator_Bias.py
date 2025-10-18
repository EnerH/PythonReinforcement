#!/usr/bin/env python3
import argparse
import random
from collections import Counter, defaultdict

# ---------- Core functions ----------
def roll_once(sides: int, bias: dict[int, float] | None = None) -> int:
    """Return one die roll in [1..sides]. If bias provided, use weighted choice."""
    if not bias:
        return random.randint(1, sides)
    # normalize weights and do a manual weighted draw
    faces = list(range(1, sides + 1))
    weights = [max(bias.get(f, 0.0), 0.0) for f in faces]
    total = sum(weights)
    if total <= 0:
        # fallback to fair if bad bias
        return random.randint(1, sides)
    thresh = random.random() * total
    acc = 0.0
    for f, w in zip(faces, weights):
        acc += w
        if thresh <= acc:
            return f
    return faces[-1]

def simulate(num_dice: int, sides: int, rolls: int, bias: dict[int, float] | None = None) -> list[tuple[int, ...]]:
    """Simulate rolls; returns list of tuples (d1, d2, ..., dN)."""
    out = []
    for _ in range(rolls):
        outcome = tuple(roll_once(sides, bias) for _ in range(num_dice))
        out.append(outcome)
    return out

def summarize(results: list[tuple[int, ...]]):
    """Return face frequencies (combined), sum frequencies, and basic stats."""
    if not results:
        return {}, {}, {"mean": 0, "min": None, "max": None}
    num_dice = len(results[0])
    # combined face counts across all dice
    face_counts = Counter()
    # per-die counts (optional; kept if you want to display them)
    per_die_counts = [Counter() for _ in range(num_dice)]
    sums = []
    for tup in results:
        face_counts.update(tup)
        for i, v in enumerate(tup):
            per_die_counts[i][v] += 1
        sums.append(sum(tup))

    sum_counts = Counter(sums)
    n_rolls = len(results)
    stats = {
        "mean": sum(sums) / n_rolls,
        "min": min(sums),
        "max": max(sums),
    }
    return face_counts, sum_counts, stats, per_die_counts

def print_histogram(freqs: dict[int, int], title: str, bar_char: str = "#"):
    print(f"\n{title}")
    if not freqs:
        print("(no data)")
        return
    max_key = max(freqs)
    min_key = min(freqs)
    max_count = max(freqs.values())
    if max_count == 0:
        max_count = 1
    for k in range(min_key, max_key + 1):
        count = freqs.get(k, 0)
        bar_len = int(50 * count / max_count)  # scale to ~50 chars
        bar = bar_char * bar_len
        print(f"{k:>2}: {bar} {count}")

def export_summary(face_counts, sum_counts, stats, rolls, num_dice, sides) -> str:
    lines = []
    lines.append(f"Dice simulation ({rolls} rolls) — {num_dice}d{sides}")
    lines.append(f"Sum stats  → mean={stats['mean']:.3f}, min={stats['min']}, max={stats['max']}")
    lines.append("\nFace frequencies (combined across dice):")
    total_faces = rolls * num_dice
    for face in range(1, sides + 1):
        c = face_counts.get(face, 0)
        pct = 100 * c / total_faces if total_faces else 0
        lines.append(f"  {face}: {c} ({pct:.2f}%)")
    lines.append("\nSum frequencies:")
    total = rolls if rolls else 1
    for s in range(num_dice, num_dice * sides + 1):
        c = sum_counts.get(s, 0)
        pct = 100 * c / total
        lines.append(f"  {s}: {c} ({pct:.2f}%)")
    return "\n".join(lines)

# ---------- CLI ----------
def parse_bias(bias_str: str | None, sides: int) -> dict[int, float] | None:
    """
    Parse bias like '1:2,6:1.5' meaning weight(face)=2 for 1, 1.5 for 6, others 1.
    Missing faces default to 1.0.
    """
    if not bias_str:
        return None
    out = {i: 1.0 for i in range(1, sides + 1)}
    for part in bias_str.split(","):
        part = part.strip()
        if not part:
            continue
        face_str, weight_str = part.split(":")
        face = int(face_str)
        weight = float(weight_str)
        if 1 <= face <= sides:
            out[face] = weight
    return out

def main():
    ap = argparse.ArgumentParser(description="Dice simulator & stats")
    ap.add_argument("-n", "--num-dice", type=int, default=2, help="number of dice")
    ap.add_argument("-s", "--sides", type=int, default=6, help="sides per die")
    ap.add_argument("-r", "--rolls", type=int, default=10000, help="number of rolls")
    ap.add_argument("--seed", type=int, default=None, help="random seed for reproducibility")
    ap.add_argument("--bias", type=str, default=None,
                    help="comma-separated face:weight list, e.g. '1:2,6:1.5' (others default to 1.0)")
    ap.add_argument("--export", action="store_true", help="print a summary block for copy/paste")
    args = ap.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    bias_map = parse_bias(args.bias, args.sides)
    results = simulate(args.num_dice, args.sides, args.rolls, bias=bias_map)
    face_counts, sum_counts, stats, _ = summarize(results)

    # Tables
    print(f"\nRolled {args.rolls} times with {args.num_dice}d{args.sides}" +
          (f" (seed={args.seed})" if args.seed is not None else "") +
          (f" (biased)" if bias_map else ""))
    print(f"Sum mean={stats['mean']:.3f}, min={stats['min']}, max={stats['max']}")

    # Histograms
    print_histogram(dict(sorted(face_counts.items())), "Face frequencies (text chart)")
    print_histogram(dict(sorted(sum_counts.items())), "Sum frequencies (text chart)")

    # Optional export
    if args.export:
        print("\n----- COPY/PASTE SUMMARY -----")
        print(export_summary(face_counts, sum_counts, stats, args.rolls, args.num_dice, args.sides))

if __name__ == "__main__":
    main()