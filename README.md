# Corporate Cyber Risk Scorecard

A lightweight Streamlit web application for performing a structured self-assessment of an organisation's cyber-security controls. Designed as an educational tool.

---

## What it does

Users answer **20 yes/no-style questions** (on a 4-point scale) across five security categories:

| Category | Weight |
|---|---|
| Access Control | 30 % |
| Patching & Vulnerability Management | 25 % |
| Backup & Recovery | 20 % |
| Incident Response | 15 % |
| Third-Party & Vendor Risk | 10 % |

The app then:
- Calculates an **overall security score (0–100)** and assigns a risk level (Low / Medium / High / Critical).
- Displays a **colour-coded bar chart** of scores per category.
- Surfaces the **Top 5 prioritised recommendations**, ranked by how much impact fixing each gap would have on the overall score.
- Offers a **plain-text report download** summarising the results.

> **Disclaimer:** This is an educational self-assessment tool only. It is not a substitute for a professional security audit.

---

## How scoring works

Each question is answered on a 4-point scale:

| Answer | Points |
|---|---|
| Not in place | 0 |
| Partially in place | 1 |
| Mostly in place | 2 |
| Fully in place | 3 |

**Category score (%)** = points earned ÷ 12 (maximum) × 100

**Overall score** = weighted sum of all five category scores

**Recommendations** are ranked by `gap × category weight`, where `gap = 3 − points earned`. This surfaces the highest-impact missing controls first.

---

## How to run

### Prerequisites

- Python 3.9 or later
- pip

### Steps

```bash
# 1. Clone or copy the project folder
cd path/to/project

# 2. (Recommended) Create a virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate   # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch the app
streamlit run app.py
```

The app opens automatically in your browser at `http://localhost:8501`.

---

## File structure

```
.
├── app.py            ← Entire application (single file)
├── requirements.txt  ← Python dependencies (Streamlit + Plotly)
└── README.md         ← This file
```

---

## Code walkthrough (for interview preparation)

The file is divided into clearly numbered sections:

| Section | What it does |
|---|---|
| **0 – Imports** | Brings in `streamlit`, `plotly`, and `io.StringIO`. |
| **1 – CATEGORY_WEIGHTS** | A single dictionary controlling every weight in the app. Change a number here and every score, chart, and recommendation updates automatically. |
| **2 – QUESTIONS** | A list of 20 dictionaries, one per question. Each holds a unique `id`, its `category`, the question `text`, and a one-sentence `rec`ommendation. This separation of data from logic keeps the code clean and easy to extend. |
| **3 – Scoring constants** | Defines `ANSWER_OPTIONS` and `ANSWER_POINTS` so the mapping from text to numbers lives in one place. Also defines `risk_level()`. |
| **4 – Helper functions** | `compute_scores()` sums points per category and applies weights. `get_top_recommendations()` calculates each question's *priority score* (gap × weight) and returns the top 5. `build_text_report()` uses `StringIO` to assemble a downloadable text file in memory — no temp files needed. |
| **5 – Page config** | `st.set_page_config()` must be the first Streamlit call; it sets the browser tab title and icon. |
| **6 – Header** | Title, disclaimer, and optional company-name input. |
| **7a – Questionnaire tab** | Iterates over `QUESTIONS`, groups them by category, and renders a `st.selectbox` for each. Answers are stored in Streamlit's `session_state` (a dictionary that persists across re-runs). The *Calculate* button sets a `"calculated"` flag. An expander explains the methodology. |
| **7b – Results tab** | Reads answers from `session_state`, calls the helper functions, and renders the score metric, risk badge, Plotly bar chart, top-5 recommendations (inside expanders), and a `st.download_button` with the text report. |

### Key Streamlit concepts used

- **`st.session_state`** – Persists data (answers, the "calculated" flag) across reruns triggered by widget interactions.
- **`st.tabs`** – Splits the UI into two named tabs without any routing logic.
- **`st.selectbox(key=...)`** – Binds a widget directly to `session_state`; no manual callback needed.
- **`st.download_button`** – Serves an in-memory string as a file download, so no files are written to disk.
- **`st.expander`** – Keeps the recommendations section compact; each recommendation collapses until clicked.
