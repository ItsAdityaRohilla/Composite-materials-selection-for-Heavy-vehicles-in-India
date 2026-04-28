import os

import pandas as pd
import streamlit as st

from agent.material_agent import UseCase, format_prompt_context, recommend
from agent.materials import CLIMATE_PROFILES, SECTOR_PROFILES


st.set_page_config(page_title="Truck Carrier Material Agent", layout="wide")


def call_openai_explainer(prompt: str) -> str | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            input=prompt,
        )
        return response.output_text
    except Exception as exc:
        return f"OpenAI explanation unavailable: {exc}"


st.title("Composite Carrier Material Advisor for Indian Heavy Trucks")
st.caption("Composite-aware recommendations for economical carrier body design in Indian operating conditions.")

with st.sidebar:
    st.header("Use Case Input")
    sector = st.selectbox("Sector", list(SECTOR_PROFILES.keys()))
    climate = st.selectbox("Operating climate", list(CLIMATE_PROFILES.keys()), index=4)
    payload_tonnes = st.number_input("Rated payload (tonnes)", min_value=1.0, max_value=80.0, value=16.0, step=0.5)
    production_volume = st.selectbox("Production stage", ["Prototype / pilot", "Small batch", "Fleet production"])
    st.divider()
    budget_priority = st.slider("Budget importance", 1, 5, 5)
    weight_priority = st.slider("Weight reduction importance", 1, 5, 4)
    corrosion_priority = st.slider("Corrosion resistance importance", 1, 5, 4)
    abrasion_priority = st.slider("Abrasion / impact importance", 1, 5, 3)
    fire_priority = st.slider("Fire safety importance", 1, 5, 3)
    notes = st.text_area("Special requirements", placeholder="Example: coastal route, cement bags, daily washdown, forklift loading...")
    generate = st.button("Generate recommendation", type="primary", use_container_width=True)

use_case = UseCase(
    sector=sector,
    climate=climate,
    payload_tonnes=payload_tonnes,
    budget_priority=budget_priority,
    weight_priority=weight_priority,
    corrosion_priority=corrosion_priority,
    abrasion_priority=abrasion_priority,
    fire_priority=fire_priority,
    production_volume=production_volume,
    notes=notes,
)

if "last_use_case" not in st.session_state:
    st.session_state.last_use_case = None

if generate:
    st.session_state.last_use_case = use_case

active_use_case = st.session_state.last_use_case

# Only generate recommendation when user has clicked generate
if active_use_case is None:
    st.info(" Configure your use case and click **Generate recommendation** to get started.")
    st.stop()

try:
    result = recommend(active_use_case)
except Exception as exc:
    st.error("The material agent could not generate a recommendation.")
    st.exception(exc)
    st.stop()

best = result["best"]

st.success(
    f"Recommendation generated for {active_use_case.sector}, "
    f"{active_use_case.climate}, {active_use_case.payload_tonnes:g} tonne payload."
)

left, right = st.columns([1.1, 0.9], gap="large")

with left:
    st.subheader("Recommended Material System")
    st.metric(best["name"], f"{best['score']} / 100", f"~{best['weight_saving_pct']}% weight saving")
    st.write(best["summary"])

    st.subheader("Why This Material")
    st.markdown(f"- Estimated weight saving: **{best['weight_saving_pct']}%** versus conventional heavy welded sheet construction.")
    st.markdown(f"- India availability score: **{best['availability_india']} / 5**.")
    st.markdown(f"- Manufacturing practicality score: **{best['manufacturing_fit']} / 5**.")
    st.markdown(f"- Cost tier: **{best['cost']} / 6**, where lower is cheaper.")

    if best["bonuses"]:
        st.success("Fit signals: " + " ".join(best["bonuses"]))
    if best["penalties"]:
        st.warning("Risks: " + " ".join(best["penalties"]))

    st.subheader("Suggested Carrier Architecture")
    for step in result["architecture"]:
        st.markdown(f"- {step}")

with right:
    st.subheader("Input Profile Used")
    st.write(
        {
            "sector": active_use_case.sector,
            "climate": active_use_case.climate,
            "payload_tonnes": active_use_case.payload_tonnes,
            "production_stage": active_use_case.production_volume,
            "budget_priority": active_use_case.budget_priority,
            "weight_priority": active_use_case.weight_priority,
            "corrosion_priority": active_use_case.corrosion_priority,
            "abrasion_priority": active_use_case.abrasion_priority,
            "fire_priority": active_use_case.fire_priority,
            "notes": active_use_case.notes,
        }
    )

    st.subheader("Manufacturing Route")
    st.write(best["manufacturing"])
    st.subheader("Watchouts")
    st.write(best["watchouts"])

    st.subheader("Validation Before Production")
    for item in result["validation"]:
        st.markdown(f"- {item}")

st.subheader("Ranked Material Options")
rows = [
    {
        "Rank": index + 1,
        "Material system": item["name"],
        "Category": item["category"],
        "Score": item["score"],
        "Cost tier": item["cost"],
        "Weight saving %": item["weight_saving_pct"],
        "India availability": item["availability_india"],
        "Manufacturing fit": item["manufacturing_fit"],
    }
    for index, item in enumerate(result["ranked"])
]
ranked_df = pd.DataFrame(rows)
st.dataframe(ranked_df, hide_index=True, use_container_width=True)

st.subheader("Economic Interpretation")
if best["cost"] <= 3:
    st.write(
        "This option is suitable for an economical pilot because it uses materials and processes that are broadly available in India."
    )
elif best["cost"] == 4:
    st.write(
        "This option can be viable when payload gain, corrosion life, or fuel savings are important enough to offset higher material and process cost."
    )
else:
    st.write(
        "This option is technically attractive but should be treated as premium or specialized unless lifecycle savings are proven by fleet data."
    )

with st.expander("Optional AI Explanation"):
    st.write("Set `OPENAI_API_KEY` to enable a natural-language engineering explanation. The rule engine above works without it.")
    prompt = format_prompt_context(active_use_case, result)
    st.code(prompt, language="text")
    if st.button("Generate AI Explanation"):
        explanation = call_openai_explainer(prompt)
        if explanation:
            st.write(explanation)
        else:
            st.info("No API key found. Add `OPENAI_API_KEY` in your environment and restart Streamlit.")

st.caption(
    "Engineering note: this tool is for early material screening. Final carrier design must be checked by a qualified mechanical/automotive engineer."
)
