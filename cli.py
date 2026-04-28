import argparse

from agent.material_agent import UseCase, recommend
from agent.materials import CLIMATE_PROFILES, SECTOR_PROFILES


def main() -> None:
    parser = argparse.ArgumentParser(description="Indian heavy-truck carrier material selection agent")
    parser.add_argument("--sector", choices=SECTOR_PROFILES.keys(), default="General logistics")
    parser.add_argument("--climate", choices=CLIMATE_PROFILES.keys(), default="Mixed pan-India")
    parser.add_argument("--payload", type=float, default=16.0)
    parser.add_argument("--production", choices=["Prototype / pilot", "Small batch", "Fleet production"], default="Prototype / pilot")
    parser.add_argument("--budget", type=int, choices=range(1, 6), default=5)
    parser.add_argument("--weight", type=int, choices=range(1, 6), default=4)
    parser.add_argument("--corrosion", type=int, choices=range(1, 6), default=4)
    parser.add_argument("--abrasion", type=int, choices=range(1, 6), default=3)
    parser.add_argument("--fire", type=int, choices=range(1, 6), default=3)
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    use_case = UseCase(
        sector=args.sector,
        climate=args.climate,
        payload_tonnes=args.payload,
        budget_priority=args.budget,
        weight_priority=args.weight,
        corrosion_priority=args.corrosion,
        abrasion_priority=args.abrasion,
        fire_priority=args.fire,
        production_volume=args.production,
        notes=args.notes,
    )
    result = recommend(use_case)
    best = result["best"]

    print("\nBEST MATERIAL SYSTEM")
    print(f"{best['name']} | Score: {best['score']}/100 | Approx weight saving: {best['weight_saving_pct']}%")
    print(best["summary"])

    if best["bonuses"]:
        print("\nFit signals:")
        for item in best["bonuses"]:
            print(f"- {item}")
    if best["penalties"]:
        print("\nRisks:")
        for item in best["penalties"]:
            print(f"- {item}")

    print("\nSuggested carrier architecture:")
    for step in result["architecture"]:
        print(f"- {step}")

    print("\nTop ranked options:")
    for index, item in enumerate(result["ranked"][:5], start=1):
        print(f"{index}. {item['name']} - {item['score']}/100")


if __name__ == "__main__":
    main()
    