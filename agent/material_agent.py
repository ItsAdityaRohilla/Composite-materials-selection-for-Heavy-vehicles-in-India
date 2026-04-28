from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .materials import CLIMATE_PROFILES, MATERIALS, SECTOR_PROFILES


@dataclass
class UseCase:
    sector: str
    climate: str
    payload_tonnes: float
    budget_priority: int
    weight_priority: int
    corrosion_priority: int
    abrasion_priority: int
    fire_priority: int
    production_volume: str
    notes: str = ""


def clamp(value: float, low: float = 0, high: float = 100) -> float:
    return max(low, min(high, value))


def score_material(material: dict[str, Any], use_case: UseCase) -> dict[str, Any]:
    sector = SECTOR_PROFILES[use_case.sector]
    climate = CLIMATE_PROFILES[use_case.climate]

    budget_weight = use_case.budget_priority * 1.5
    weight_weight = use_case.weight_priority * 1.4
    corrosion_weight = max(use_case.corrosion_priority, climate["corrosion"]) * 1.5
    abrasion_weight = max(use_case.abrasion_priority, sector["abrasion"]) * 1.2
    fire_weight = max(use_case.fire_priority, sector["fire"]) * 1.1

    economy_score = (7 - material["cost"]) * 10
    weight_score = material["weight_saving_pct"]
    base = (
        economy_score * budget_weight
        + weight_score * weight_weight
        + material["corrosion"] * 20 * corrosion_weight
        + material["abrasion"] * 20 * abrasion_weight
        + material["fire"] * 20 * fire_weight
        + material["availability_india"] * 18
        + material["manufacturing_fit"] * 16
        + material["repairability"] * 12
        + material["strength"] * 18
    )

    max_possible = (
        60 * budget_weight
        + 60 * weight_weight
        + 100 * corrosion_weight
        + 100 * abrasion_weight
        + 100 * fire_weight
        + 90
        + 80
        + 60
        + 90
    )
    score = (base / max_possible) * 100

    penalties: list[str] = []
    bonuses: list[str] = []

    if use_case.payload_tonnes >= 18 and material["category"] in {"Composite", "Premium composite"}:
        score -= 12
        penalties.append("High payload needs validated metallic hard points or hybrid structure.")

    if sector["abrasion"] >= 5 and material["abrasion"] <= 2:
        score -= 14
        penalties.append("Severe abrasion requires sacrificial steel/UHMW liners.")

    if sector["hygiene"] >= 5 and "SS304" in material["name"]:
        score += 8
        bonuses.append("Hygienic contact surfaces fit food/cold-chain washdown duty.")

    if use_case.climate == "Coastal humid / saline" and material["corrosion"] >= 4:
        score += 6
        bonuses.append("Good fit for salt, humidity, and monsoon corrosion risk.")

    if use_case.budget_priority >= 4 and material["cost"] >= 5:
        score -= 10
        penalties.append("Likely difficult to justify economically for Indian fleet use.")

    if use_case.production_volume == "Prototype / pilot" and material["manufacturing_fit"] <= 2:
        score -= 8
        penalties.append("Needs controlled process development before field pilot.")

    score = clamp(score)

    return {
        **material,
        "score": round(score, 1),
        "penalties": penalties,
        "bonuses": bonuses,
    }


def recommend(use_case: UseCase) -> dict[str, Any]:
    ranked = sorted(
        (score_material(material, use_case) for material in MATERIALS),
        key=lambda item: item["score"],
        reverse=True,
    )
    best = ranked[0]
    return {
        "best": best,
        "ranked": ranked,
        "architecture": build_architecture(best, use_case),
        "validation": validation_plan(best, use_case),
    }


def build_architecture(best: dict[str, Any], use_case: UseCase) -> list[str]:
    sector = SECTOR_PROFILES[use_case.sector]
    steps = [
        f"Use {best['name']} as the main material system.",
        "Keep chassis mounting brackets, twist-lock points, hinge points, and lashing points in steel or aluminium inserts.",
        "Replace large welded side sheets with modular bolted/bonded panels sized for repair and transport.",
        "Seal all panel edges, drilled holes, overlaps, and floor-wall joints against monsoon water ingress.",
    ]
    if use_case.climate == "Coastal humid / saline":
        steps.append("Specify galvanizing or epoxy-zinc primer on steel, galvanic isolation at mixed-metal joints, and marine-grade fasteners.")
    if sector["abrasion"] >= 4:
        steps.append("Add replaceable wear liners on floor, tailgate, loading edge, and lower side walls.")
    if sector["hygiene"] >= 4:
        steps.append("Use washable inner skins, rounded internal corners, sealed joints, and food/chemical-compatible liners.")
    if use_case.payload_tonnes >= 18:
        steps.append("Treat composite panels as skins/stiffeners until FEA, prototype load testing, and fatigue testing prove primary structural use.")
    return steps


def validation_plan(best: dict[str, Any], use_case: UseCase) -> list[str]:
    return [
        "Create a load map: payload distribution, point loads, dynamic braking, cornering, road vibration, and loading equipment impact.",
        "Run FEA for frame, panel deflection, joint peel/shear, and local insert stresses.",
        "Build one instrumented pilot carrier and test overload, water ingress, cyclic vibration, thermal exposure, and rough-road use.",
        "Check AIS/CMVR/RTO/OEM body-builder requirements before production; use BIS-marked aluminium products where applicable.",
        "Calculate total cost of ownership: material cost, fabrication hours, payload gain, fuel saving, corrosion warranty, downtime, and repair cost.",
    ]


def format_prompt_context(use_case: UseCase, result: dict[str, Any]) -> str:
    top = result["ranked"][:3]
    lines = [
        "You are advising an Indian heavy-truck carrier manufacturer on material selection.",
        f"Use case: sector={use_case.sector}, climate={use_case.climate}, payload={use_case.payload_tonnes} tonnes.",
        f"Priorities: budget={use_case.budget_priority}/5, weight={use_case.weight_priority}/5, corrosion={use_case.corrosion_priority}/5, abrasion={use_case.abrasion_priority}/5, fire={use_case.fire_priority}/5.",
        f"User notes: {use_case.notes or 'None'}",
        "Top scored options:",
    ]
    for item in top:
        lines.append(f"- {item['name']}: score {item['score']}, cost tier {item['cost']}/6, weight saving approx {item['weight_saving_pct']}%.")
    lines.append("Give a concise recommendation with manufacturing route, economics, risks, and next validation steps.")
    return "\n".join(lines)


