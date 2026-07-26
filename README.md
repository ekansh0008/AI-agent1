# 🚀 ApexSales AI — Autonomous Client Acquisition & Pitch Agent

ApexSales AI is a production-grade, state-of-the-art AI Sales Agent Dashboard engineered to automate prospecting, outreach generation, live sales negotiations, and enterprise-grade business agreements. 

Featuring built-in **cognitive reasoning fallback layers**, **unified CRM pipeline tracking**, and **synthesized AI sales pitches (speech nodes)**, ApexSales AI is a high-impact platform for automating the entire B2B sales cycle.

---

## 📸 System Architecture & Agent Flow

```
                      ┌─────────────────────────────────┐
                      │    🔍 Prospect Intelligence     │ (Sweeps corporate data & tech stacks)
                      └────────────────┬────────────────┘
                                       │ Import Lead
                                       ▼
                      ┌─────────────────────────────────┐
                      │       🚀 CRM Pipeline           │ (Local JSON persistence & deal stages)
                      └────────────────┬────────────────┘
                                       │ Selection
                                       ▼
     ┌─────────────────────────────────┴─────────────────────────────────┐
     ▼                                 ▼                                 ▼
┌───────────────┐              ┌───────────────┐                 ┌───────────────┐
│  ✉️ Campaign  │              │  🎙️ Speech    │                 │  📄 Proposal  │
│  Generator    │              │  Synthesizer  │                 │  Draftsman    │
└───────────────┘              └───────────────┘                 └───────────────┘
 (Email, InMail,             (Custom audio files               (Compiles markdown
  Objections)                 for default leads)                enterprise deals)
```

---

## ✨ Primary Agent Modules

### 1. 🚀 CRM Dashboard & Task Hub
* **Unified Pipeline Analytics**: Track total active pipelines, won values, averages, and deal progression in real-time.
* **Inspect & Update Leads**: Instantly modify deal stages, values, close probabilities, call notes, and action plans.
* **Tactical Checklist Board**: Dynamic task lists driven by AI to highlight urgent actions across active accounts.
* **Persistent Local Ledger**: All modifications, logs, and activity events persist inside a secured `data/crm_data.json` ledger.

### 2. 🔍 Prospect Intelligence Hub
* **Deep Domain Scan**: Enter any corporation and domain (e.g., Stripe, Shopify, Tesla) to invoke an automated research agent.
* **Granular Extraction**: Evaluates estimated company size, core mission, probable technical stack (React, Ruby, SCADA, etc.), and recent corporate press events.
* **Strategic Pain Identification**: Identifies the 3 most critical pain points and lists decision-makers.
* **Direct CRM Integration**: Clicking "Import to CRM" instantly loads the prospect into your pipeline with pre-filled metadata.

### 3. ✉️ Hyper-Personalized Outreach & Pitch Synthesizer
* **Omnichannel Copy Generation**: Instantly craft emails, LinkedIn InMail copy, and conversational 30-second cold-calling scripts based on selected tones (*Assertive*, *Casual*, *Storytelling*, *Professional*).
* **Vocal Speech Agents**: Audio files synthesized using high-fidelity voice profiles are pre-loaded for Stripe, Shopify, and Tesla. Listen to the custom audio pitch directly inside the application.
* **Objection Countermeasures Matrix**: Outlines exact pushback triggers and custom rebuttals.

### 4. 🧠 Skeptical Buyer Negotiation Simulator
* **Interactive Live Simulation**: Roleplay and test objection-handling skills against specialized buyer personas (Sarah Jenkins - CFO, Arjun Mehta - CTO, Brooke Lawson - Startup Founder).
* **Real-time Console**: Practice holding value, countering concerns about budgets, self-hosting, VPC privacy, or time schedules.
* **AI Sales Performance Coaching**: Request a comprehensive report card scoring your performance. Receives feedback on Objection Handling, Value Prop Clarity, Closing Strength, and personalized coaching scripts.

### 5. 📄 Enterprise Proposal & Deck Draftsman
* **Architect Tailored Solutions**: Input any custom SaaS or technical offering (e.g., *Apex AI-Edge Processing Engine*) to generate tailored business proposals.
* **Structured Markdown Agreements**: Drafts executive summaries, proposed container architectures, quantified ROI schedules, phased week-by-week implementation paths, and performance SLA terms.
* **Instant Export**: Download full documents as markdown (`.md`) files with a single click.

---

## ⚡ Quick Start & Run Instructions

### Prerequisites
* Python 3.11+
* Node.js (Optional, Python serves the UI via Streamlit)

### Running on This Workspace (Pre-Configured)
The workspace already has a virtual environment (`venv`) created with all dependencies fully installed. Simply run:

```bash
# 1. Activate the pre-configured virtual environment
source venv/bin/activate

# 2. Run the Streamlit UI application
streamlit run app.py
```

### Manual/Alternative Setup
If you want to reinstall dependencies or host the app elsewhere:

```bash
# 1. Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install all required packages
pip install -r requirements.txt

# 3. Launch the app
streamlit run app.py
```

Once running, copy the provided local URL (typically `http://localhost:8501`) into your browser.

---

## 🔑 Live Mode vs. Demo Mode

To ensure full utility right out of the box, ApexSales AI is built with an **intelligent dual-processing core**:

1. **Demo Mode (No API Key Required)**: Runs fully local rules engines, pre-baked corporate dossiers, and keyword-responsive chat agents. Perfect for offline environments, demos, and testing.
2. **Live Mode (With OpenAI API Key)**: Simply input your OpenAI API Key (`sk-...`) in the left-hand sidebar. The application will instantly switch to live generative models, executing custom deep-completions for any target company and client response you input!

---

## 📂 Project Structure

```
AI-agent1/
├── app.py                     # Main Streamlit web application
├── requirements.txt           # Python dependency lists
├── README.md                  # Comprehensive Documentation
├── assets/                    # Image and pre-generated audio files
│   ├── audio/                 # Pre-generated vocal sales pitches
│   │   ├── shopify_pitch.mp3
│   │   ├── stripe_pitch.mp3
│   │   └── tesla_pitch.mp3
│   └── images/                # Visual banner & logo assets
│       ├── logo.png
│       └── dashboard_banner.png
├── data/                      # File persistence databases
│   └── crm_data.json          # Pre-loaded and persistent CRM database
└── utils/                     # Modular backend utility layers
    ├── __init__.py
    ├── ai_engine.py           # Handles OpenAI live completions & demo fallbacks
    └── crm_store.py           # Handles CRUD operations on local CRM json file
```
