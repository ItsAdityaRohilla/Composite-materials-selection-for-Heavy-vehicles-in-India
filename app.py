import os

import pandas as pd
import streamlit as st

from agent.material_agent import UseCase, format_prompt_context, recommend
from agent.materials import CLIMATE_PROFILES, SECTOR_PROFILES


st.set_page_config(page_title="Indian Truck Carrier Material Agent", layout="wide")


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


st.title("Indian Heavy-Truck Carrier Material Selection Agent")
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
    