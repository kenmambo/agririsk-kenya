"""Methodology, Formulations & Ethical Guardrails Page."""

import streamlit as st
from agririsk.dashboard.formatting import render_disclaimer_banner

st.set_page_config(
    page_title="Methodology & Ethics - AgriRisk Kenya",
    page_icon="📖",
    layout="wide"
)

# Research Disclaimer Banner
st.markdown(render_disclaimer_banner(), unsafe_allow_html=True)

st.title("📖 Methodology, Mathematical Formulations & Ethical Guardrails")
st.markdown(
    "A rigorous, transparent documentation of the conceptual framework, feature transformations, "
    "temporal validation strategy, and humanitarian ethical boundaries underpinning AgriRisk Kenya."
)

tab1, tab2, tab3, tab4 = st.tabs([
    "📐 Feature Formulations",
    "⚖️ IPC Distinction",
    "🛡️ Ethical Guardrails",
    "⚠️ Limitations & Assumptions"
])

with tab1:
    st.subheader("Mathematical Feature Definitions")
    st.markdown("""
    All features in AgriRisk Kenya are engineered to capture the dynamic progression of drought, 
    forage degradation, and economic stress across county-month units:
    """)

    st.markdown("#### 1. Precipitation Anomalies")
    st.latex(r"\text{Rainfall Anomaly}_{c, m, t} = \frac{R_{c, m, t} - \mu_{c, m}^{\text{rain}}}{\mu_{c, m}^{\text{rain}}} \times 100\%")
    st.markdown("""
    Where $R_{c, m, t}$ is the observed rainfall for county $c$ in month $m$ of year $t$, and 
    $\mu_{c, m}^{\text{rain}}$ is the long-term historical baseline mean for that specific county and calendar month.
    """)

    st.markdown("#### 2. Consecutive Dry Months Streak")
    st.latex(r"D_{c, t} = \begin{cases} D_{c, t-1} + 1 & \text{if } \text{Rainfall Anomaly}_{c, t} < -20\% \\ 0 & \text{otherwise} \end{cases}")
    st.markdown("Quantifies prolonged meteorological drought duration without intermediate relief.")

    st.markdown("#### 3. Vegetation Health Anomaly (NDVI)")
    st.latex(r"\text{NDVI Anomaly}_{c, m, t} = \frac{\text{NDVI}_{c, m, t} - \mu_{c, m}^{\text{NDVI}}}{\mu_{c, m}^{\text{NDVI}}} \times 100\%")
    st.markdown("Measures photosynthetic activity and biomass departures from seasonal expectations.")

    st.markdown("#### 4. Staple Grain Market Price Z-Score")
    st.latex(r"Z_{c, t}^{\text{price}} = \frac{P_{c, t} - \mu_c^{\text{price}}}{\sigma_c^{\text{price}}}")
    st.markdown("""
    Where $P_{c, t}$ is the average wholesale price of dry maize (KES per 90kg bag), $\mu_c^{\text{price}}$ is 
    the county historical price mean, and $\sigma_c^{\text{price}}$ is the county standard deviation.
    """)

    st.markdown("#### 5. Binary Crisis Target Formulation")
    st.latex(r"y_{c, t} = \begin{cases} 1 & \text{if } \text{IPC Phase}_{c, t} \ge 3 \text{ (Crisis, Emergency, Catastrophe)} \\ 0 & \text{if } \text{IPC Phase}_{c, t} < 3 \text{ (Minimal, Stressed)} \end{cases}")

with tab2:
    st.subheader("Crucial Distinction: Official IPC Classifications vs. AgriRisk Model Risk")
    st.markdown("""
    To preserve institutional clarity and prevent misinformation, AgriRisk strictly enforces the 
    following distinction across all interfaces and documentation:

    | Dimension | Official IPC Classification | AgriRisk Early Warning Model |
    | :--- | :--- | :--- |
    | **Governing Authority** | Kenya Food Security Steering Group (KFSSG) & IPC Global Support Unit | Academic & Research Prototype |
    | **Primary Mechanism** | Multi-agency consensus, field surveys, SMART nutrition surveys, HEA | Supervised Machine Learning (Random Forest) |
    | **Output Type** | Categorical Phase Classification (Phase 1 to Phase 5) | Continuous Risk Probability $[0.0, 1.0]$ & Risk Bands |
    | **Update Cadence** | Biannual assessments (Long Rains / Short Rains) | Monthly interim monitoring & simulation |
    | **Operational Mandate** | Official authorization for humanitarian aid & emergency appeals | Decision-support guidance & proactive monitoring alert |

    > **Institutional Boundary:** AgriRisk model outputs must **never** be cited as official IPC phases or 
    > used to countermand official declarations by the Government of Kenya or United Nations agencies.
    """)

with tab3:
    st.subheader("Ethical Guardrails & Responsible AI in Humanitarian Contexts")
    st.markdown("""
    Food security monitoring directly impacts human livelihoods and vulnerability. 
    The following guardrails govern the design and deployment of AgriRisk Kenya:

    1. **Human-in-the-Loop Requirement:**
       - Model outputs are decision-support inputs, **never automated decision-makers**.
       - Automated resource allocation or aid withdrawal based solely on model risk probabilities is strictly prohibited.

    2. **Transparency & Explainability Over Black-Box Performance:**
       - Every risk probability estimate is accompanied by inspectable feature values, anomaly baselines, and historical trajectories.
       - Stakeholders can verify whether elevated risk is driven by rainfall failure, market spikes, or past vulnerability.

    3. **Prioritizing Recall (Avoiding Harmful Neglect):**
       - In humanitarian early warning, a false negative (failing to detect a crisis) carries severe human consequences, 
         whereas a false positive (precautionary monitoring) triggers benign field verification.
       - Model thresholds and architectures are optimized for high sensitivity.

    4. **Non-Causal Representation:**
       - All user interfaces explicitly state that model weights indicate statistical association rather than proven causality.
    """)

with tab4:
    st.subheader("System Limitations & Methodological Assumptions")
    st.markdown("""
    Users and evaluators should consider the following known constraints:

    - **Geographic Coverage:** The current pilot focuses on 5 high-vulnerability ASAL counties (Turkana, Marsabit, Mandera, Garissa, Baringo). 
      Generalizing to agricultural high-potential counties requires recalibration.
    - **Omitted Variables:** The current feature set does not explicitly model:
      - Armed conflict, cattle rustling, and localized displacement
      - Livestock epidemic disease outbreaks (e.g. PPR, CCPP)
      - Water, sanitation, and hygiene (WASH) infrastructure collapse
      - Volume and timing of humanitarian food assistance deliveries
    - **Administrative Boundary Resolution:** County-level aggregation masks intra-county inequalities between pastoral rangelands and riverine or urban settlements.
    - **Ground-Truth Cadence:** IPC assessments occur biannually; intermediate monthly ground-truth targets are forward-filled from the most recent official seasonal assessment.
    """)
