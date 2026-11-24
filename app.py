"""VanDrishti - Forest Tree Registry & Carbon Portal (demo backend).

Run:  pip install flask
      python app.py        ->  http://127.0.0.1:5000
Put index.html in a folder named 'static' next to this file.
"""
import math
import random
from flask import Flask, jsonify, request, send_from_directory, abort

app = Flask(__name__, static_folder="static")

AREAS = {"A": "Demo Forest Block A", "B": "Demo Forest Block B", "C": "Demo Forest Block C"}
RHO = {"Sal": .75, "Teak": .6, "Hollong": .5, "Gamari": .55, "Other": .6}  # wood density, placeholder
SEED_A = [("Sal", 59.4, 14.6, "Healthy"), ("Gamari", 82.7, 14.9, "Stressed"), ("Hollong", 59.9, 11.4, "Healthy"),
          ("Other", 33, 18.4, "Diseased"), ("Hollong", 55.2, 14.5, "Diseased"), ("Teak", 44, 14.5, "Healthy"),
          ("Teak", 34.8, 18.3, "Healthy"), ("Hollong", 54.1, 16.6, "Healthy"), ("Hollong", 32.9, 13.1, "Healthy"),
          ("Other", 59.7, 13.4, "Healthy"), ("Teak", 74.6, 10.3, "Diseased"), ("Hollong", 81.6, 16.5, "Healthy"),
          ("Hollong", 42.9, 12.9, "Diseased"), ("Sal", 51.6, 14.9, "Healthy")]


def biomass_kg(t):
    """Above-ground biomass, general tropical form: 0.0673 * (rho * D^2 * H)^0.976 (placeholder)."""
    d = t["girth"] / math.pi
    return 0.0673 * (RHO[t["species"]] * d * d * t["height"]) ** 0.976


def carbon_kg(t):
    return biomass_kg(t) * 0.47          # carbon fraction 47%


def co2e_kg(t):
    return carbon_kg(t) * 44 / 12        # CO2 equivalent


def build():
    trees = []
    for k in AREAS:
        r = random.Random(ord(k) * 977)
        for i in range(14):
            if k == "A":
                sp, g, h, hl = SEED_A[i]
            else:
                sp = r.choice(list(RHO))
                g, h = round(30 + r.random() * 55, 1), round(10 + r.random() * 9, 1)
                hl = "Healthy" if r.random() < .7 else r.choice(["Stressed", "Diseased"])
            trees.append(dict(tag=f"AS-{k}-{i + 1:05d}", area=k, species=sp, girth=g, height=h, health=hl,
                              x=round(r.random() * .9 + .05, 3), y=round(r.random() * .8 + .08, 3)))
    return trees


TREES = build()


def enrich(t):
    return {**t, "area_name": AREAS[t["area"]], "biomass_kg": round(biomass_kg(t), 1),
            "carbon_kg": round(carbon_kg(t), 1), "co2e_kg": round(co2e_kg(t), 1)}


@app.route("/")
def home():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/summary")
def summary():
    return jsonify(trees=len(TREES), areas=len(AREAS),
                   carbon_tonnes=round(sum(carbon_kg(t) for t in TREES) / 1000, 2))


@app.get("/api/trees")
def list_trees():
    area, health, q = request.args.get("area"), request.args.get("health"), request.args.get("q", "").lower()
    out = [enrich(t) for t in TREES
           if (not area or t["area"] == area) and (not health or t["health"] == health)
           and q in (t["tag"] + t["species"]).lower()]
    return jsonify(out)


@app.get("/api/trees/<tag>")
def get_tree(tag):
    t = next((t for t in TREES if t["tag"].lower() == tag.lower()), None)
    return jsonify(enrich(t)) if t else abort(404)


@app.post("/api/trees")
def save_tree():
    d = request.get_json(force=True)
    t = next((t for t in TREES if t["tag"] == d.get("tag")), None)
    if t:
        t.update({k: d[k] for k in ("species", "girth", "height", "health") if k in d})
    else:
        area = d.get("area", "A")
        n = sum(1 for x in TREES if x["area"] == area) + 1
        t = dict(tag=f"AS-{area}-{n:05d}", area=area, species=d["species"], girth=float(d["girth"]),
                 height=float(d["height"]), health=d.get("health", "Healthy"),
                 x=random.random() * .9 + .05, y=random.random() * .8 + .08)
        TREES.append(t)
    return jsonify(enrich(t)), 201


@app.post("/api/reset")
def reset():
    TREES[:] = build()
    return jsonify(ok=True)


if __name__ == "__main__":
    app.run(debug=True)
