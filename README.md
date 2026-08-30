# ✈️ T10 Flight Option Finder

An autonomous, deterministic AI Flight Option Finder & Verification Agent powered by **NVIDIA NIM**, **AviationStack Schedules**, **Ignav Real-Time Fare Engine**, and **Scrapling Web Verifier**.

[![Tests](https://img.shields.io/badge/Tests-52%20Passed-success.svg)](#testing)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-blue.svg)](#installation)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](#license)

---

## 🌟 Key Capabilities & Architecture

- **Real Live Data (Zero Fake / Mock Data)**: Every schedule, fare amount, and booking deep-link is retrieved in real-time from authoritative external APIs.
- **Autonomous Multi-Stage Decision Flow**: Operates strictly on a transparent `PLAN` ➔ `ACT` ➔ `OBSERVE` ➔ `EVALUATE` ➔ `DECIDE` loop.
- **Deterministic Flight Matching**: Validates exact carrier codes, flight numbers, routes, and dates without LLM hallucination.
- **Multi-Hub Connecting Flight Synthesizer**: When direct point-to-point flights do not exist (e.g. Amritsar ➔ Chennai), automatically searches and connects flights across primary transit hubs (`DEL`, `BOM`, `BLR`, `HYD`) with valid layovers (1–12 hours).
- **140+ Indian Regional & Global Airports**: Supports all metro, Tier-2, Tier-3, and UDAN regional airports across India, plus major global hubs worldwide with typo-tolerant fuzzy matching.
- **Scrapling Web Verification**: Auxiliary DOM-level verification cross-checking booking target pages.
- **Interactive Modern Web Dashboard**: Clean light-mode UI featuring structured forms, live animated execution steppers, and smart fallback recommendation cards.

---

## 🏗️ 7-Stage Agent Pipeline

```
[ User Query / Structured Form ]
               │
               ▼
1. 🧠 NLU & Airport Resolution (Typo-Tolerant)
   Resolves "Amritsar (ATQ)" ➔ "ATQ", "Chennai (MAA)" ➔ "MAA", "amrister" ➔ "ATQ"
               │
               ▼
2. 🛫 Tool 1: search_flights(origin, destination, date)
   Queries AviationStack for active carrier route schedules
               │
               ▼
3. 💰 Tool 2: compare_price(origin, destination, date, budget)
   Queries Ignav API (POST /api/fares/one-way) for real-time GDS & direct airline fares
               │
               ▼
4. ⚙️ Deterministic Matching Engine
   Normalizes flight numbers (6E, AI, etc.) and eliminates hallucinations
               │
               ▼
5. 🔄 Multi-Hub Connecting Engine (Fallback for 0-direct routes)
   Synthesizes 1-stop connections via DEL, BOM, BLR, HYD with valid layovers
               │
               ▼
6. ⚖️ Hard Budget Filter & Preference Ranker
   Eliminates fares > budget, prioritizes verified fares, nonstop, and preferred times
               │
               ▼
7. 🔗 Booking Link Extraction & Scrapling Verification
   Queries Ignav (POST /api/fares/booking-links) and performs live page verification
```

---

## 📁 Repository Structure

```
flights-agent/
├── agent.py                 # Core AI Agent controller (PLAN -> ACT -> OBSERVE -> EVALUATE -> DECIDE)
├── airport_resolver.py      # Comprehensive worldwide & 140+ Indian airports database & fuzzy matcher
├── aviationstack_client.py  # AviationStack API schedule client
├── ignav_client.py          # Ignav Live Fare & Booking Link API client
├── llm_client.py            # NVIDIA NIM (Llama-3.3-70B) reasoning client
├── matching.py              # Deterministic flight matching engine
├── memory.py                # Multi-turn conversational session memory
├── models.py                # Pydantic domain models
├── tools.py                 # Exactly two agent-facing tools (search_flights, compare_price)
├── web_app.py               # FastAPI application & responsive Web UI
├── scraping/
│   └── booking_verifier.py  # Scrapling auxiliary web verification module
├── tests/                   # 52 comprehensive unit & integration tests
│   ├── test_agent.py
│   ├── test_airport_resolver.py
│   ├── test_audits.py
│   ├── test_aviationstack.py
│   ├── test_config.py
│   ├── test_ignav.py
│   ├── test_matching.py
│   ├── test_memory.py
│   ├── test_models.py
│   ├── test_scraping.py
│   ├── test_tools.py
│   └── test_web_app.py
├── notebook/
│   └── flight_agent_demo.ipynb # Jupyter notebook demonstration
├── requirements.txt         # Project dependencies
├── .env.example             # Environment variable template
└── README.md
```

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/kollisathwikkumar/flights-agent.git
cd flights-agent
```

### 2. Create and Activate Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the root directory (refer to `.env.example`):

```bash
cp .env.example .env
```

Add your API credentials:

```env
IGNAV_API_KEY=your_ignav_api_key
IGNAV_AUTH_TOKEN=your_ignav_bearer_token
IGNAV_BASE_URL=https://api.ignav.com

AVIATIONSTACK_API_KEY=your_aviationstack_api_key
AVIATIONSTACK_BASE_URL=http://api.aviationstack.com/v1

NVIDIA_NIM_API_KEY=your_nvidia_nim_api_key
NVIDIA_NIM_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_NIM_MODEL=meta/llama-3.3-70b-instruct
```

---

## 💻 Usage

### Launch Web Dashboard

```bash
python3 web_app.py
```

Open your browser at **[http://127.0.0.1:8000](http://127.0.0.1:8000)**.

### Run Python Agent CLI

```python
from agent import agent

# Natural language search
result = agent.run("Find me a flight from Amritsar to Chennai on September 27 under ₹25,000")
print(result.formatted_response)
```

---

## 🧪 Testing

Run the full suite of 52 unit and integration tests:

```bash
pytest -v tests/
```

Test coverage includes:
- Query extraction & route normalization
- Exact deterministic matching & carrier normalization
- Point-to-point and connecting flight synthesis
- Budget rejection & preference ranking
- Security audit (zero hardcoded secrets)
- Fake data audit (zero mock/synthetic prices)

---

## 🛡️ Security & Integrity

- **Zero Hardcoded Secrets**: Secrets are loaded dynamically via masked environment variables.
- **Cabotage Compliance**: Automatically excludes foreign carriers for domestic Indian routes.
- **Fail-Closed Budget Enforcement**: Never recommends options exceeding user budgets without explicit alternative flags.

---

## 📄 License

MIT License. See `LICENSE` for details.
