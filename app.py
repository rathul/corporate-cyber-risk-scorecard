"""
Corporate Cyber Risk Scorecard
================================
A Streamlit web app that lets a user answer 20 security-control questions
across five categories and immediately see an overall cyber-risk score,
a per-category bar chart, and prioritised remediation recommendations.

Author : forensic-student project
Python : 3.9+
Run    : streamlit run app.py
"""

# ---------------------------------------------------------------------------
# 0. IMPORTS
# ---------------------------------------------------------------------------
import streamlit as st          # The web-app framework
import plotly.graph_objects as go  # Interactive bar chart
from io import StringIO         # Lets us build a text report in memory

# ---------------------------------------------------------------------------
# 1. CONFIGURATION  ← Change weights here; everything else adapts automatically
# ---------------------------------------------------------------------------

# Category weights must sum to 1.0 (i.e. 100 %).
# These reflect how often each weakness appears in real breach investigations:
#   • Most breaches start with stolen/weak credentials  → Access Control is highest
#   • Unpatched systems are the #2 attack vector        → Patching second
#   • Ransomware impact depends on backup quality       → Backup third
#   • Fast containment reduces damage                  → IR fourth
#   • Third-party breaches are growing but less common  → Vendor lowest
CATEGORY_WEIGHTS = {
    "Access Control":                   0.30,
    "Patching & Vulnerability Mgmt":    0.25,
    "Backup & Recovery":                0.20,
    "Incident Response":                0.15,
    "Third-Party & Vendor Risk":        0.10,
}

# ---------------------------------------------------------------------------
# 2. QUESTIONNAIRE DATA
#    Each question is a dict with:
#      "id"       – unique short key used to store the answer in session state
#      "category" – must match a key in CATEGORY_WEIGHTS
#      "text"     – the question shown to the user
#      "rec"      – one-sentence recommendation shown when the answer is low
# ---------------------------------------------------------------------------

QUESTIONS = [
    # --- Access Control (4 questions) ---
    {
        "id": "ac_mfa",
        "category": "Access Control",
        "text": "Multi-factor authentication (MFA) is enforced on all user accounts, including email and remote access.",
        "rec": "Enable MFA immediately on all accounts, prioritising email, VPN, and admin portals, using an authenticator app rather than SMS where possible.",
    },
    {
        "id": "ac_password",
        "category": "Access Control",
        "text": "A formal password policy is in place and enforced (minimum length, complexity, no reuse).",
        "rec": "Implement a technical password policy (minimum 12 characters, checked against breach databases) and enforce it through Active Directory or your identity provider.",
    },
    {
        "id": "ac_pam",
        "category": "Access Control",
        "text": "Privileged accounts (admin, root, service accounts) are managed with the principle of least privilege.",
        "rec": "Audit all privileged accounts, remove unnecessary rights, and adopt a Privileged Access Management (PAM) tool or time-limited just-in-time access.",
    },
    {
        "id": "ac_offboard",
        "category": "Access Control",
        "text": "There is a documented and consistently followed offboarding process that revokes access on an employee's last day.",
        "rec": "Create a checklist-driven offboarding workflow that triggers automatic account disabling on the termination date and is verified by IT within 24 hours.",
    },

    # --- Patching & Vulnerability Management (4 questions) ---
    {
        "id": "pvm_patching",
        "category": "Patching & Vulnerability Mgmt",
        "text": "Critical security patches are applied to all systems within an agreed SLA (e.g., 14 days for critical, 30 days for high).",
        "rec": "Define a formal patching SLA, deploy a patch management tool (e.g., WSUS, Automox), and produce a monthly compliance report for leadership.",
    },
    {
        "id": "pvm_scanning",
        "category": "Patching & Vulnerability Mgmt",
        "text": "Vulnerability scans are run regularly (at least monthly) across all internet-facing and internal systems.",
        "rec": "Schedule authenticated vulnerability scans at least monthly using a tool such as Nessus, Qualys, or OpenVAS, and assign findings to owners with remediation deadlines.",
    },
    {
        "id": "pvm_inventory",
        "category": "Patching & Vulnerability Mgmt",
        "text": "A complete, up-to-date inventory of all hardware and software assets is maintained.",
        "rec": "Deploy an automated asset discovery tool to maintain a live CMDB; you cannot patch or protect assets you do not know you have.",
    },
    {
        "id": "pvm_eol",
        "category": "Patching & Vulnerability Mgmt",
        "text": "End-of-life (EoL) software and operating systems are identified and either upgraded, replaced, or isolated.",
        "rec": "Produce an EoL register, plan migrations for unsupported software within 90 days, and network-isolate any systems that cannot be upgraded immediately.",
    },

    # --- Backup & Recovery (4 questions) ---
    {
        "id": "br_backups",
        "category": "Backup & Recovery",
        "text": "All critical data is backed up regularly (daily or more frequently) according to a documented schedule.",
        "rec": "Automate daily backups for all critical data and confirm success via alerts; a backup that is not monitored should be treated as no backup.",
    },
    {
        "id": "br_offsite",
        "category": "Backup & Recovery",
        "text": "Backup copies are stored offline or offsite (e.g., air-gapped media or a separate cloud account) to protect against ransomware.",
        "rec": "Apply the 3-2-1 rule: keep 3 copies of data, on 2 different media types, with 1 stored offsite or in an isolated cloud storage account the production environment cannot reach.",
    },
    {
        "id": "br_restore",
        "category": "Backup & Recovery",
        "text": "Backup restores are tested at least quarterly to confirm data can actually be recovered.",
        "rec": "Schedule quarterly restore tests for each critical system, document the recovery time achieved, and compare it against your Recovery Time Objective (RTO).",
    },
    {
        "id": "br_plan",
        "category": "Backup & Recovery",
        "text": "A documented disaster recovery / business continuity plan exists, is approved by management, and is reviewed annually.",
        "rec": "Draft a Business Continuity Plan that names responsible owners, specifies RTO/RPO targets per system, and is reviewed after every significant incident or annually.",
    },

    # --- Incident Response (4 questions) ---
    {
        "id": "ir_plan",
        "category": "Incident Response",
        "text": "A written Incident Response (IR) plan exists, covering detection, containment, eradication, recovery, and lessons learned.",
        "rec": "Create an IR plan following the NIST SP 800-61 lifecycle; include contact trees, severity classifications, and step-by-step runbooks for the most likely incident types.",
    },
    {
        "id": "ir_team",
        "category": "Incident Response",
        "text": "A named incident response team (or retainer with an external firm) is in place with defined roles and responsibilities.",
        "rec": "Designate an IR team with named primary and backup contacts for each role (incident commander, technical lead, legal/comms), and maintain an external IR retainer for surge capacity.",
    },
    {
        "id": "ir_reporting",
        "category": "Incident Response",
        "text": "Breach notification obligations (e.g., regulatory, legal, to affected parties) are documented and understood.",
        "rec": "Map all applicable breach notification laws (GDPR 72-hour rule, state laws, sector regulators) and include a notification checklist in the IR plan so deadlines are never missed.",
    },
    {
        "id": "ir_drills",
        "category": "Incident Response",
        "text": "Staff participate in at least one tabletop exercise or security drill per year.",
        "rec": "Run an annual tabletop exercise using a realistic scenario (e.g., ransomware outbreak), capture lessons learned, and update the IR plan within 30 days of the exercise.",
    },

    # --- Third-Party & Vendor Risk (4 questions) ---
    {
        "id": "vr_assessments",
        "category": "Third-Party & Vendor Risk",
        "text": "Security assessments (questionnaires, audits, or certifications review) are conducted before onboarding new vendors.",
        "rec": "Implement a vendor tiering system; require ISO 27001 certification or a completed security questionnaire from all Tier-1 (high-access) vendors before contract signature.",
    },
    {
        "id": "vr_contracts",
        "category": "Third-Party & Vendor Risk",
        "text": "Contracts with key vendors include security requirements, data protection clauses, and the right to audit.",
        "rec": "Work with legal to add a standard security addendum to all vendor contracts covering data handling, encryption standards, incident notification timescales, and the right to audit.",
    },
    {
        "id": "vr_access",
        "category": "Third-Party & Vendor Risk",
        "text": "Vendor and third-party access to systems is scoped to the minimum necessary and is monitored.",
        "rec": "Enforce least-privilege access for all vendors, use time-limited credentials, and log all vendor sessions; review and revoke unused vendor access quarterly.",
    },
    {
        "id": "vr_notification",
        "category": "Third-Party & Vendor Risk",
        "text": "Key vendors are contractually required to notify the organisation within a defined timeframe if they suffer a security incident.",
        "rec": "Require a maximum 24–72-hour incident notification SLA in all key vendor contracts and establish a contact point so notifications reach your security team, not just procurement.",
    },
]

# ---------------------------------------------------------------------------
# 3. SCORING CONSTANTS
# ---------------------------------------------------------------------------

# Answer options shown in every selectbox, mapped to point values 0–3
ANSWER_OPTIONS = [
    "Not in place",       # 0 points
    "Partially in place", # 1 point
    "Mostly in place",    # 2 points
    "Fully in place",     # 3 points
]
ANSWER_POINTS = {opt: i for i, opt in enumerate(ANSWER_OPTIONS)}  # {"Not in place": 0, ...}

MAX_POINTS_PER_QUESTION = 3          # "Fully in place" = 3
QUESTIONS_PER_CATEGORY   = 4
MAX_POINTS_PER_CATEGORY  = MAX_POINTS_PER_QUESTION * QUESTIONS_PER_CATEGORY  # 12

# Risk-level thresholds applied to the final weighted score (0–100)
def risk_level(score: float) -> tuple[str, str]:
    """Return (label, hex-colour) based on the overall score."""
    if score >= 80:
        return "🟢 Low Risk",      "#2ecc71"
    elif score >= 60:
        return "🟡 Medium Risk",   "#f39c12"
    elif score >= 40:
        return "🟠 High Risk",     "#e67e22"
    else:
        return "🔴 Critical Risk", "#e74c3c"

# ---------------------------------------------------------------------------
# 4. HELPER FUNCTIONS
# ---------------------------------------------------------------------------

def compute_scores(answers: dict) -> dict:
    """
    Given a dict of {question_id: answer_string}, compute:
      - category_scores: {category_name: percentage 0–100}
      - overall_score: weighted float 0–100
      Returns a result dict.
    """
    # Group raw points by category
    category_points = {cat: 0 for cat in CATEGORY_WEIGHTS}
    for q in QUESTIONS:
        pts = ANSWER_POINTS.get(answers.get(q["id"], ANSWER_OPTIONS[0]), 0)
        category_points[q["category"]] += pts

    # Convert to percentage scores per category
    category_scores = {
        cat: (pts / MAX_POINTS_PER_CATEGORY) * 100
        for cat, pts in category_points.items()
    }

    # Weighted overall score
    overall = sum(
        category_scores[cat] * weight
        for cat, weight in CATEGORY_WEIGHTS.items()
    )

    return {"category_scores": category_scores, "overall_score": overall}


def get_top_recommendations(answers: dict, n: int = 5) -> list[dict]:
    """
    Score every question by its 'gap' (lost points × category weight).
    Return the top-n questions with the biggest gap, i.e. the highest priority fixes.
    """
    scored = []
    for q in QUESTIONS:
        pts = ANSWER_POINTS.get(answers.get(q["id"], ANSWER_OPTIONS[0]), 0)
        gap = MAX_POINTS_PER_QUESTION - pts                  # 0 = no gap, 3 = fully missing
        weight = CATEGORY_WEIGHTS[q["category"]]
        priority_score = gap * weight                        # bigger = more important to fix
        if gap > 0:                                          # only include incomplete controls
            scored.append({"question": q, "gap": gap, "priority_score": priority_score})

    # Sort highest priority first
    scored.sort(key=lambda x: x["priority_score"], reverse=True)
    return scored[:n]


def build_text_report(company: str, results: dict, answers: dict) -> str:
    """
    Build a plain-text summary suitable for download.
    Uses StringIO to construct the string line by line.
    """
    buf = StringIO()

    def w(line=""):  # small helper to write a line
        buf.write(line + "\n")

    w("=" * 60)
    w("CORPORATE CYBER RISK SCORECARD")
    if company:
        w(f"Organisation: {company}")
    w("=" * 60)
    w()

    overall = results["overall_score"]
    label, _ = risk_level(overall)
    w(f"OVERALL SECURITY SCORE : {overall:.1f} / 100")
    w(f"RISK LEVEL             : {label}")
    w()

    w("-" * 60)
    w("CATEGORY SCORES")
    w("-" * 60)
    for cat, score in results["category_scores"].items():
        weight_pct = int(CATEGORY_WEIGHTS[cat] * 100)
        w(f"  {cat:<35} {score:5.1f}%  (weight {weight_pct}%)")
    w()

    w("-" * 60)
    w("TOP 5 PRIORITISED RECOMMENDATIONS")
    w("-" * 60)
    recs = get_top_recommendations(answers, n=5)
    for i, item in enumerate(recs, 1):
        q = item["question"]
        w(f"{i}. [{q['category']}]")
        w(f"   Control  : {q['text']}")
        w(f"   Current  : {answers.get(q['id'], ANSWER_OPTIONS[0])}")
        w(f"   Action   : {q['rec']}")
        w()

    w("=" * 60)
    w("DISCLAIMER: Educational self-assessment tool.")
    w("Not a substitute for a professional security audit.")
    w("=" * 60)

    return buf.getvalue()


# ---------------------------------------------------------------------------
# 5. PAGE CONFIG  (must be first Streamlit call)
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Cyber Risk Scorecard",
    page_icon="🛡️",
    layout="wide",
)

# ---------------------------------------------------------------------------
# 6. HEADER
# ---------------------------------------------------------------------------

st.title("🛡️ Corporate Cyber Risk Scorecard")
st.markdown(
    "> **Disclaimer:** This is an educational self-assessment tool only. "
    "It is **not** a substitute for a professional security audit."
)
st.divider()

# Optional company name — shown in the report heading
company_name = st.text_input(
    "Organisation name (optional)",
    placeholder="e.g. Acme Ltd",
    help="Used only in the report heading. Nothing is stored.",
)

# ---------------------------------------------------------------------------
# 7. TABS  (Questionnaire | Results)
# ---------------------------------------------------------------------------

tab_q, tab_r = st.tabs(["📋 Questionnaire", "📊 Results"])

# ── 7a. QUESTIONNAIRE TAB ──────────────────────────────────────────────────
with tab_q:

    st.subheader("Answer all 20 questions, then click 'Calculate Score'.")

    # We store answers in session_state so they persist when switching tabs.
    # Initialise any missing keys with the lowest option.
    for q in QUESTIONS:
        if q["id"] not in st.session_state:
            st.session_state[q["id"]] = ANSWER_OPTIONS[0]

    # Render each category as a labelled section
    current_category = None
    for q in QUESTIONS:
        # Print a section header when the category changes
        if q["category"] != current_category:
            current_category = q["category"]
            weight_pct = int(CATEGORY_WEIGHTS[current_category] * 100)
            st.markdown(f"### {current_category}  *(weight: {weight_pct}%)*")

        # The selectbox key links directly to session_state
        st.selectbox(
            label=q["text"],
            options=ANSWER_OPTIONS,
            key=q["id"],          # Streamlit automatically reads/writes session_state[q["id"]]
            help=f"Category: {q['category']}",
        )

    st.divider()

    # Big green button to trigger calculation
    if st.button("✅  Calculate Score", type="primary", use_container_width=True):
        st.session_state["calculated"] = True
        st.success("Score calculated! Switch to the **📊 Results** tab.")

    # "How scoring works" explainer
    with st.expander("ℹ️  How scoring works"):
        st.markdown(
            """
Each question is worth **0–3 points**:

| Answer | Points |
|---|---|
| Not in place | 0 |
| Partially in place | 1 |
| Mostly in place | 2 |
| Fully in place | 3 |

**Category score** = points earned ÷ 12 (max) × 100 %

**Overall score** = weighted average of all five category scores:

| Category | Weight | Rationale |
|---|---|---|
| Access Control | **30 %** | Compromised credentials are the #1 cause of breaches (phishing, password spray, insider threat). Controlling who gets in is the most effective first line of defence. |
| Patching & Vulnerability Mgmt | **25 %** | Unpatched systems are the second most common attack vector. Ransomware and supply-chain attacks routinely exploit known CVEs that have had patches available for months. |
| Backup & Recovery | **20 %** | If prevention fails, good backups are what let a business survive ransomware without paying. Backup maturity directly determines recovery cost and time. |
| Incident Response | **15 %** | Organisations with mature IR contain breaches faster and suffer less regulatory and reputational damage. However, IR is only useful *after* a failure, so it is weighted lower. |
| Third-Party & Vendor Risk | **10 %** | Third-party breaches are growing rapidly (see SolarWinds, MOVEit) but are harder to control unilaterally, and many SMEs have limited vendor exposure. |

**Risk level** is derived from the overall score (which measures *security*; risk is its inverse):

| Overall Score | Risk Level |
|---|---|
| 80 – 100 | 🟢 Low Risk |
| 60 – 79 | 🟡 Medium Risk |
| 40 – 59 | 🟠 High Risk |
| Below 40 | 🔴 Critical Risk |

**Recommendations** are ranked by *priority score = gap × category weight*, so a missing critical control in a high-weight category rises to the top of the list.
            """
        )

# ── 7b. RESULTS TAB ──────────────────────────────────────────────────────
with tab_r:

    # Only show results if the Calculate button has been pressed
    if not st.session_state.get("calculated"):
        st.info("Complete the questionnaire and click **'Calculate Score'** to see results here.")
        st.stop()

    # Collect current answers from session state
    current_answers = {q["id"]: st.session_state[q["id"]] for q in QUESTIONS}
    results = compute_scores(current_answers)

    overall   = results["overall_score"]
    label, colour = risk_level(overall)

    # ── Overall score headline ──────────────────────────────────────────
    if company_name:
        st.subheader(f"Results for: {company_name}")

    col_score, col_label = st.columns([1, 2])

    with col_score:
        # Display the numeric score in a large coloured metric
        st.metric(label="Overall Security Score", value=f"{overall:.1f} / 100")

    with col_label:
        # Coloured risk-level badge
        st.markdown(
            f"<h2 style='color:{colour}; margin-top:10px'>{label}</h2>",
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Per-category bar chart ──────────────────────────────────────────
    st.subheader("Category Scores")

    cats   = list(results["category_scores"].keys())
    scores = list(results["category_scores"].values())

    # Colour each bar green/amber/orange/red based on its individual score
    bar_colours = []
    for s in scores:
        if s >= 80:   bar_colours.append("#2ecc71")
        elif s >= 60: bar_colours.append("#f39c12")
        elif s >= 40: bar_colours.append("#e67e22")
        else:         bar_colours.append("#e74c3c")

    fig = go.Figure(
        go.Bar(
            x=cats,
            y=scores,
            marker_color=bar_colours,
            text=[f"{s:.0f}%" for s in scores],   # label on top of each bar
            textposition="outside",
        )
    )
    fig.update_layout(
        yaxis=dict(range=[0, 110], title="Score (%)"),
        xaxis_title="Category",
        plot_bgcolor="rgba(0,0,0,0)",   # transparent background
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        margin=dict(t=30, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── Top 5 recommendations ───────────────────────────────────────────
    st.subheader("🔧 Top 5 Prioritised Recommendations")
    st.caption(
        "Ranked by: (missing points) × (category weight). "
        "Controls with the biggest impact on your overall score appear first."
    )

    recs = get_top_recommendations(current_answers, n=5)

    if not recs:
        st.success("🎉 All controls are fully in place. Excellent security posture!")
    else:
        for rank, item in enumerate(recs, 1):
            q = item["question"]
            current_answer = current_answers.get(q["id"], ANSWER_OPTIONS[0])
            # Expander per recommendation so the page doesn't get too long
            with st.expander(
                f"**#{rank}  [{q['category']}]** — {q['text'][:70]}…"
                if len(q["text"]) > 70 else f"**#{rank}  [{q['category']}]** — {q['text']}"
            ):
                st.markdown(f"**Current status:** {current_answer}")
                st.markdown(f"**Recommended action:** {q['rec']}")
                priority_pct = item["priority_score"] / (3 * 1.0) * 100  # normalise to %
                st.progress(
                    min(item["priority_score"] / 0.9, 1.0),   # 0.9 = max possible gap×weight
                    text=f"Priority score: {item['priority_score']:.3f}",
                )

    st.divider()

    # ── Download report ─────────────────────────────────────────────────
    st.subheader("📄 Download Report")

    report_text = build_text_report(company_name, results, current_answers)

    st.download_button(
        label="⬇️  Download plain-text report (.txt)",
        data=report_text,
        file_name=f"cyber_risk_scorecard_{company_name or 'report'}.txt",
        mime="text/plain",
        use_container_width=True,
    )
