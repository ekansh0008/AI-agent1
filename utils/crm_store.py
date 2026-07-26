import os
import json
from datetime import datetime

CRM_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'crm_data.json')

DEFAULT_LEADS = [
    {
        "id": "lead_1",
        "company": "Stripe",
        "domain": "stripe.com",
        "contact_name": "David Singleton",
        "contact_title": "Chief Technology Officer",
        "contact_email": "david.s@stripe.com",
        "stage": "Pitch Scheduled",
        "value": 120000,
        "probability": 65,
        "pain_points": [
            "Payment latency overhead in European cross-border checkouts",
            "Slight increase in auth failures during high-traffic sales events",
            "High integration maintenance costs for secondary payment methods"
        ],
        "tech_stack": ["Ruby", "Scala", "AWS", "React", "Rust"],
        "next_action": "Conduct technical demo of Edge-AI Optimizer on Tuesday at 2 PM",
        "notes": "Met David at a fintech forum. He was highly receptive to optimization and latency-reduction solutions.",
        "activity_log": [
            {"date": "2026-07-20", "action": "Lead created via Prospector Hub"},
            {"date": "2026-07-22", "action": "AI-generated cold email sent to David"},
            {"date": "2026-07-24", "action": "David replied booking a technical demo! Stage updated to Pitch Scheduled."}
        ]
    },
    {
        "id": "lead_2",
        "company": "Shopify",
        "domain": "shopify.com",
        "contact_name": "Sarah Harvey",
        "contact_title": "Head of Merchant Experience",
        "contact_email": "sarah.h@shopify.com",
        "stage": "Outreach Sent",
        "value": 85000,
        "probability": 40,
        "pain_points": [
            "Static recommended item carousels have decaying click-through rates (CTR)",
            "Cart abandonment remains high on mobile web interface (14% drop-off)",
            "Merchant complaints regarding generic search recommendation results"
        ],
        "tech_stack": ["Ruby on Rails", "React", "GraphQL", "GCP"],
        "next_action": "Follow up on personalized audio memo and proposal presentation",
        "notes": "Sarah has been championing mobile web optimization inside Shopify. Our session-aware AI recommender is a direct match.",
        "activity_log": [
            {"date": "2026-07-23", "action": "Lead created via Prospector Hub"},
            {"date": "2026-07-25", "action": "Generated personalized email and voice-pitch memo and sent."}
        ]
    },
    {
        "id": "lead_3",
        "company": "Tesla",
        "domain": "tesla.com",
        "contact_name": "Jerome Guillen",
        "contact_title": "VP of Gigafactory Operations",
        "contact_email": "jguillen@tesla.com",
        "stage": "New Lead",
        "value": 250000,
        "probability": 20,
        "pain_points": [
            "Unexpected downtime in conveyor SCADA lines at Giga Texas",
            "Inefficient predictive scheduling for multi-ton heavy machinery maintenance",
            "Inventory delivery delay propagation from external component suppliers"
        ],
        "tech_stack": ["Python", "C++", "SCADA", "Kubernetes", "Proprietary MES"],
        "next_action": "Generate and send customized Factory SCADA Maintenance Proposal",
        "notes": "High value, complex enterprise sale. Needs hard metrics on downtime reduction. SCADA wear-forecasting is our hook.",
        "activity_log": [
            {"date": "2026-07-26", "action": "Lead identified and added to the CRM pipeline."}
        ]
    },
    {
        "id": "lead_4",
        "company": "Acme Corporation",
        "domain": "acme.com",
        "contact_name": "Wile E. Coyote",
        "contact_title": "Director of Logistics",
        "contact_email": "wcoyote@acme.com",
        "stage": "Negotiation",
        "value": 45000,
        "probability": 85,
        "pain_points": [
            "Anvil delivery speeds are insufficient for capturing fast-moving roadrunners",
            "High explosive equipment failure rates causing self-inflicted injuries",
            "Lack of real-time shipment routing"
        ],
        "tech_stack": ["COBOL", "FTP", "SnailMail"],
        "next_action": "Close contract for Apex AI-guided routing software",
        "notes": "Long-time buyer of eccentric devices. Extremely eager to modernize logistics with AI guidance.",
        "activity_log": [
            {"date": "2026-07-10", "action": "Lead added"},
            {"date": "2026-07-12", "action": "Initial proposal sent"},
            {"date": "2026-07-18", "action": "Demo complete - Wile was extremely enthusiastic"},
            {"date": "2026-07-25", "action": "Contract details sent. Negotiation initiated regarding licensing fees."}
        ]
    }
]

def ensure_data_dir():
    os.makedirs(os.path.dirname(CRM_FILE), exist_ok=True)

def load_leads():
    ensure_data_dir()
    if not os.path.exists(CRM_FILE):
        save_leads(DEFAULT_LEADS)
        return DEFAULT_LEADS
    try:
        with open(CRM_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading leads: {e}")
        return DEFAULT_LEADS

def save_leads(leads):
    ensure_data_dir()
    try:
        with open(CRM_FILE, 'w') as f:
            json.dump(leads, f, indent=4)
    except Exception as e:
        print(f"Error saving leads: {e}")

def get_lead(lead_id):
    leads = load_leads()
    for l in leads:
        if l['id'] == lead_id:
            return l
    return None

def add_lead(lead_data):
    leads = load_leads()
    new_id = f"lead_{len(leads) + 1}_{int(datetime.now().timestamp())}"
    lead_data['id'] = new_id
    if 'activity_log' not in lead_data:
        lead_data['activity_log'] = [{"date": datetime.now().strftime("%Y-%m-%d"), "action": "Lead created."}]
    leads.append(lead_data)
    save_leads(leads)
    return lead_data

def update_lead(lead_id, updated_fields):
    leads = load_leads()
    for i, l in enumerate(leads):
        if l['id'] == lead_id:
            leads[i].update(updated_fields)
            save_leads(leads)
            return leads[i]
    return None

def delete_lead(lead_id):
    leads = load_leads()
    leads = [l for l in leads if l['id'] != lead_id]
    save_leads(leads)

def add_activity(lead_id, action_text):
    lead = get_lead(lead_id)
    if lead:
        activity = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "action": action_text
        }
        lead['activity_log'].insert(0, activity) # Add to top
        update_lead(lead_id, {"activity_log": lead['activity_log']})
