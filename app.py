import os
import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image

# Import custom modules
from utils.crm_store import load_leads, save_leads, add_lead, update_lead, delete_lead, add_activity
from utils.ai_engine import research_prospect, generate_outreach, generate_proposal, generate_simulated_objection, evaluate_negotiation, CLIENT_PERSONAS

# Set up Streamlit page config
st.set_page_config(
    page_title="ApexSales AI - Autonomous Acquisition & Pitch Agent",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern design
st.markdown("""
<style>
    /* Main body background styling */
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    
    /* Header fonts & gradients */
    h1, h2, h3 {
        color: #58a6ff !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Metrics panel card style */
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        color: #58a6ff;
        font-weight: bold;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #161b22 !important;
        border-right: 1px solid #30363d;
    }
    
    /* Tables design */
    .dataframe {
        border: 1px solid #30363d !important;
        background-color: #161b22 !important;
        color: #c9d1d9 !important;
    }
    
    /* Buttons */
    div.stButton > button:first-child {
        background-color: #1f6feb;
        color: white;
        border-radius: 6px;
        border: none;
        padding: 0.5rem 1.2rem;
        font-weight: bold;
        transition: all 0.2s ease-in-out;
    }
    div.stButton > button:first-child:hover {
        background-color: #388bfd;
        border: none;
        box-shadow: 0 0 10px rgba(56, 139, 253, 0.4);
    }
    
    /* Cards styling */
    .sales-card {
        background-color: #161b22;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #30363d;
        margin-bottom: 15px;
    }
    
    /* Chat message styles */
    .chat-bubble {
        padding: 12px 16px;
        border-radius: 12px;
        margin-bottom: 10px;
        max-width: 80%;
    }
    .user-bubble {
        background-color: #1f6feb;
        color: white;
        margin-left: auto;
    }
    .buyer-bubble {
        background-color: #30363d;
        color: #c9d1d9;
        margin-right: auto;
    }
</style>
""", unsafe_allow_html=True)

# Define directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
AUDIO_DIR = os.path.join(ASSETS_DIR, "audio")
IMAGES_DIR = os.path.join(ASSETS_DIR, "images")

# App title and sidebar layout
st.sidebar.image(os.path.join(IMAGES_DIR, "logo.png"), use_container_width=True)
st.sidebar.markdown("<h2 style='text-align: center; margin-top:-10px;'>ApexSales AI</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='text-align: center; color: #8b949e; font-size: 14px; font-style: italic;'>Autonomous Prospecting & Closing Agent</p>", unsafe_allow_html=True)
st.sidebar.divider()

# Navigation choice
menu_options = [
    "🚀 CRM Dashboard & Task Hub",
    "🔍 Prospect Intelligence (Research)",
    "✉️ Outreach Builder & Pitch Advisor",
    "🧠 Objection Negotiation Simulator",
    "📄 Enterprise Proposal Draftsman"
]
choice = st.sidebar.selectbox("Navigate Agent Modules", menu_options)

st.sidebar.divider()

# API Configuration block
st.sidebar.markdown("### 🔑 API Configuration")
api_key_input = st.sidebar.text_input(
    "OpenAI API Key (Optional)", 
    type="password", 
    placeholder="sk-...", 
    help="Provide an OpenAI API key to run real-time LLM requests. If left blank, ApexSales AI will operate in highly smart local Demo Mode."
)

# Active credentials warning/status
if api_key_input:
    st.sidebar.success("Live Mode: Connected to OpenAI API")
    api_key = api_key_input
else:
    st.sidebar.warning("Demo Mode: Powered by smart rules & knowledge matrices")
    api_key = None

st.sidebar.divider()
st.sidebar.markdown("""
<div style='font-size: 12px; color: #8b949e; text-align: center;'>
    <strong>ApexSales AI v1.2.0</strong><br>
    Ready for Client Acquisition<br>
    Today: 2026-07-26
</div>
""", unsafe_allow_html=True)


# =====================================================================
# MODULE 1: CRM DASHBOARD & TASK HUB
# =====================================================================
if choice == "🚀 CRM Dashboard & Task Hub":
    st.image(os.path.join(IMAGES_DIR, "dashboard_banner.png"), use_container_width=True)
    st.title("🚀 Enterprise Sales CRM & Active Tasks")
    st.markdown("Monitor pipeline analytics, manage hot leads, track communications, and complete AI-generated tasks.")
    
    # Load current leads from local JSON store
    leads = load_leads()
    
    # Calculate key metrics
    total_pipeline = sum(l['value'] for l in leads)
    active_deals = sum(1 for l in leads if l['stage'] not in ["Closed Won", "Closed Lost"])
    won_deals = sum(1 for l in leads if l['stage'] == "Closed Won")
    won_value = sum(l['value'] for l in leads if l['stage'] == "Closed Won")
    avg_probability = int(sum(l['probability'] for l in leads) / len(leads)) if leads else 0
    
    # Display top metric panels
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total Pipeline Value", f"${total_pipeline:,.2f}", help="Cumulative value of all leads in CRM")
    with m2:
        st.metric("Active Sales Cycles", f"{active_deals} Deals", help="Leads not in Closed Won or Closed Lost")
    with m3:
        st.metric("Avg. Win Probability", f"{avg_probability}%", help="Average probability of winning active deals")
    with m4:
        st.metric("Closed Won Value", f"${won_value:,.2f}", help="Total value of secured clients")
        
    st.divider()
    
    # --- PIPELINE SEGMENTS (TABS) ---
    tab1, tab2, tab3 = st.tabs(["📊 Live Deal Pipeline", "📝 AI Active Task Board", "➕ Create Custom Lead"])
    
    with tab1:
        st.subheader("Active Pipeline Overview")
        # Build clean data view
        df_leads = pd.DataFrame([{
            "ID": l["id"],
            "Company": l["company"],
            "Contact Person": f"{l['contact_name']} ({l['contact_title']})",
            "Stage": l["stage"],
            "Deal Value ($)": f"${l['value']:,}",
            "Probability (%)": f"{l['probability']}%",
            "AI Next Best Action": l["next_action"]
        } for l in leads])
        
        st.dataframe(df_leads, use_container_width=True, hide_index=True)
        
        # Lead inspector & modifier
        st.divider()
        st.subheader("🔍 Lead Detail Inspector & Status Updater")
        col_sel, col_action = st.columns([1, 2])
        
        with col_sel:
            lead_names = [l['company'] for l in leads]
            selected_company = st.selectbox("Select Lead to Inspect", lead_names)
            selected_lead = next(l for l in leads if l['company'] == selected_company)
            
            st.markdown(f"**Domain:** [{selected_lead['domain']}](https://{selected_lead['domain']})")
            st.markdown(f"**Contact:** {selected_lead['contact_name']}")
            st.markdown(f"**Title:** {selected_lead['contact_title']}")
            st.markdown(f"**Email:** {selected_lead['contact_email']}")
            
            # Delete button
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️ Delete Lead", help="Permanently remove this lead from CRM"):
                delete_lead(selected_lead['id'])
                st.success(f"Lead for {selected_lead['company']} deleted successfully!")
                st.rerun()
                
        with col_action:
            # Edit fields form
            with st.form(key=f"edit_form_{selected_lead['id']}"):
                st.markdown(f"### Edit Lead: **{selected_lead['company']}**")
                
                c_stage, c_val, c_prob = st.columns(3)
                with c_stage:
                    new_stage = st.selectbox(
                        "Deal Stage", 
                        ["New Lead", "Outreach Sent", "Pitch Scheduled", "Negotiation", "Closed Won", "Closed Lost"],
                        index=["New Lead", "Outreach Sent", "Pitch Scheduled", "Negotiation", "Closed Won", "Closed Lost"].index(selected_lead['stage'])
                    )
                with c_val:
                    new_value = st.number_input("Deal Value ($)", value=selected_lead['value'], step=5000)
                with c_prob:
                    new_prob = st.slider("Win Probability (%)", 0, 100, selected_lead['probability'])
                    
                new_action = st.text_input("AI Next Best Action", value=selected_lead['next_action'])
                new_notes = st.text_area("Latest Call Notes", value=selected_lead['notes'])
                
                submit_edit = st.form_submit_button("💾 Save Lead Updates")
                
                if submit_edit:
                    updates = {
                        "stage": new_stage,
                        "value": new_value,
                        "probability": new_prob,
                        "next_action": new_action,
                        "notes": new_notes
                    }
                    
                    # Log activity if stage changed
                    if new_stage != selected_lead['stage']:
                        add_activity(selected_lead['id'], f"Stage updated from {selected_lead['stage']} to {new_stage}.")
                    else:
                        add_activity(selected_lead['id'], "Lead details and next actions updated.")
                        
                    update_lead(selected_lead['id'], updates)
                    st.success(f"Successfully saved modifications to {selected_lead['company']}!")
                    st.rerun()
            
            # Activity Log Viewer
            with st.expander("⏳ Timeline & Activity Log", expanded=False):
                for act in selected_lead.get('activity_log', []):
                    st.markdown(f"**`{act['date']}`**: {act['action']}")
                    
    with tab2:
        st.subheader("📋 AI-Generated Tactical Tasks")
        st.markdown("These task cards represent localized micro-actions prioritized by ApexSales AI algorithms to progress deals forward.")
        
        # Generate clean interactive task checklist based on CRM leads
        active_leads = [l for l in leads if l['stage'] not in ["Closed Won", "Closed Lost"]]
        for idx, lead in enumerate(active_leads):
            task_text = f"**{lead['company']} Follow-Up:** {lead['next_action']}"
            due_date = "Urgent" if lead['stage'] in ["Negotiation", "Pitch Scheduled"] else "This Week"
            
            with st.container():
                st.markdown(f"""
                <div class="sales-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-size: 16px; font-weight: bold; color: #58a6ff;">{lead['company']} - Stage: {lead['stage']}</span>
                        <span style="background-color: {'#f25c54' if due_date=='Urgent' else '#f8bbd0'}; color: black; font-size:11px; font-weight:bold; padding:2px 8px; border-radius:12px;">{due_date}</span>
                    </div>
                    <p style="margin-top: 8px; font-size: 14px; color:#c9d1d9;">{task_text}</p>
                    <div style="font-size:12px; color:#8b949e; margin-bottom:12px;">Contact: <b>{lead['contact_name']}</b> ({lead['contact_email']}) | Deal: <b>${lead['value']:,}</b></div>
                </div>
                """, unsafe_allow_html=True)
                
                # Custom completion buttons
                btn_cols = st.columns([1, 4])
                with btn_cols[0]:
                    if st.button("Mark Completed", key=f"complete_btn_{lead['id']}_{idx}"):
                        new_act = f"Completed task: {lead['next_action']}. Re-evaluating next strategic step."
                        add_activity(lead['id'], new_act)
                        update_lead(lead['id'], {"next_action": "Run Prospect Outreacher to define next step."})
                        st.success(f"Task for {lead['company']} completed!")
                        st.rerun()
                st.write("")
                st.markdown("---")
                
    with tab3:
        st.subheader("➕ Create a New Lead Manually")
        with st.form(key="create_lead_form"):
            c1, c2 = st.columns(2)
            with c1:
                new_comp = st.text_input("Company Name*", placeholder="Acme Inc.")
                new_dom = st.text_input("Website Domain*", placeholder="acme.com")
                new_contact = st.text_input("Contact Name*", placeholder="John Doe")
                new_title = st.text_input("Contact Title*", placeholder="Director of Engineering")
            with c2:
                new_email = st.text_input("Contact Email*", placeholder="john.doe@acme.com")
                new_val_input = st.number_input("Estimated Deal Value ($)", min_value=0, value=50000, step=5000)
                new_stage_sel = st.selectbox("Initial Stage", ["New Lead", "Outreach Sent", "Pitch Scheduled", "Negotiation"])
                new_prob_sel = st.slider("Initial Win Probability (%)", 0, 100, 20)
                
            new_pains = st.text_area("Identified Pain Points (One per line)", placeholder="Slow data sync latency\nManual order processing cost\nPoor lead conversions")
            new_desc = st.text_area("General Notes/Context", placeholder="Met them briefly on LinkedIn. High interest in automation.")
            
            submit_create = st.form_submit_button("✨ Add Lead to Pipeline")
            
            if submit_create:
                if not new_comp or not new_dom or not new_contact or not new_email:
                    st.error("Please fill in all mandatory fields (starred*) to add the lead.")
                else:
                    pain_list = [p.strip() for p in new_pains.split("\n") if p.strip()]
                    if not pain_list:
                        pain_list = ["Operational scalability bottleneck"]
                        
                    new_lead_dict = {
                        "company": new_comp,
                        "domain": new_dom,
                        "contact_name": new_contact,
                        "contact_title": new_title,
                        "contact_email": new_email,
                        "stage": new_stage_sel,
                        "value": new_val_input,
                        "probability": new_prob_sel,
                        "pain_points": pain_list,
                        "tech_stack": ["React", "AWS", "Python"],
                        "next_action": "Initiate automated outreacher script or proposal generator",
                        "notes": new_desc
                    }
                    add_lead(new_lead_dict)
                    st.success(f"Successfully added {new_comp} into active sales pipeline!")
                    st.rerun()


# =====================================================================
# MODULE 2: PROSPECT INTELLIGENCE (RESEARCH)
# =====================================================================
elif choice == "🔍 Prospect Intelligence (Research)":
    st.title("🔍 Autonomous Prospect Intelligence Hub")
    st.markdown("Deploy our specialized scraping and research agent to sweep corporate pages, news, and technical vectors, returning structured strategic files.")
    
    col_input, col_preset = st.columns([2, 1])
    
    with col_input:
        with st.form(key="research_form"):
            st.markdown("### 🧬 Query Target Domain")
            rc_name = st.text_input("Target Company Name", placeholder="e.g. Stripe, Zoom, Snowflake")
            rc_dom = st.text_input("Target Website Domain", placeholder="e.g. stripe.com, zoom.us")
            
            submit_research = st.form_submit_button("⚡ Run AI Agent Intelligence Scan")
            
    with col_preset:
        st.markdown("### 💡 Quick Launch Preset")
        st.markdown("Select a sample client below to inspect instantaneous high-profile AI research dossiers:")
        preset_stripe = st.button("🔍 Scan Stripe (Fintech)")
        preset_shopify = st.button("🔍 Scan Shopify (E-commerce)")
        preset_tesla = st.button("🔍 Scan Tesla (Automotive/Energy)")
        
    # Set search values based on presets
    selected_comp = None
    selected_dom = None
    
    if preset_stripe:
        selected_comp, selected_dom = "Stripe", "stripe.com"
    elif preset_shopify:
        selected_comp, selected_dom = "Shopify", "shopify.com"
    elif preset_tesla:
        selected_comp, selected_dom = "Tesla", "tesla.com"
    elif submit_research:
        if rc_name and rc_dom:
            selected_comp, selected_dom = rc_name, rc_dom
        else:
            st.error("Please fill in both Company Name and Website Domain to begin.")
            
    if selected_comp and selected_dom:
        with st.spinner(f"Agent executing deep-web sweep on {selected_comp}... Parsing technical assets..."):
            # Call our AI research engine
            profile = research_prospect(selected_comp, selected_dom, api_key)
            
        st.success("🎉 Intelligence Scan Completed successfully! Strategic File generated:")
        
        # Display Research Dossier in standard cards
        st.markdown(f"## 📋 Company Intelligence Profile: {profile['company_name']}")
        
        r1, r2, r3 = st.columns(3)
        with r1:
            st.markdown(f"**🏢 Core Industry:** {profile.get('core_industry', 'Unknown')}")
            st.markdown(f"**🌐 Website:** [{profile['domain']}](https://{profile['domain']})")
        with r2:
            st.markdown(f"**📈 Corporate Size:** {profile.get('estimated_size', 'Mid-Market')}")
            st.markdown(f"**🎯 Primary Goal:** {profile.get('company_mission_and_focus', 'N/A')}")
        with r3:
            st.markdown("**🛡️ Technology Stack:**")
            st.write(", ".join(profile.get('likely_tech_stack', [])))
            
        st.divider()
        
        c_left, c_right = st.columns(2)
        with c_left:
            st.markdown("### 🚨 Identified Corporate Pain Points & Latent Leaks")
            for idx, pain in enumerate(profile.get('three_major_pain_points', [])):
                st.markdown(f"**{idx+1}.** {pain}")
                
            st.markdown("### 🔔 Key Decision Makers (Warm Leads)")
            for d in profile.get('key_decision_makers', []):
                st.markdown(f"👤 **{d['name']}** - *{d['title']}* (`{d['email']}`)")
                
        with c_right:
            st.markdown("### 📢 Recent Strategic Trigger / News Event")
            st.info(profile.get('recent_news_or_initiatives', 'Expanding core operational throughput globally.'))
            
            st.markdown("### ⚡ AI Recommendation Hook (Value Proposal)")
            st.warning(profile.get('custom_value_hook', 'Automate key operational bottlenecks via adaptive workflows.'))
            
        st.divider()
        
        # Import to CRM logic
        st.markdown("### 📥 CRM Synchronization Pipeline")
        st.markdown("Would you like to register this researched prospect and decision makers directly into your CRM deal tracking pipeline?")
        
        # Inputs for CRM registration
        crm_col1, crm_col2 = st.columns(2)
        with crm_col1:
            dm_selection = st.selectbox(
                "Select Main Point of Contact", 
                [f"{d['name']} ({d['title']})" for d in profile.get('key_decision_makers', [])]
            )
        with crm_col2:
            deal_val = st.number_input("Estimated Account Value ($)", min_value=1000, value=75000, step=5000)
            
        if st.button("🚀 Push to CRM Lead Board"):
            # Extract decision maker detail
            selected_dm = next(d for d in profile['key_decision_makers'] if f"{d['name']} ({d['title']})" == dm_selection)
            
            # Check if company already in CRM to avoid duplicates
            current_leads = load_leads()
            if any(l['company'].lower() == profile['company_name'].lower() for l in current_leads):
                st.error(f"Lead for {profile['company_name']} is already active in your CRM pipeline. Please edit it on the Dashboard.")
            else:
                new_crm_lead = {
                    "company": profile['company_name'],
                    "domain": profile['domain'],
                    "contact_name": selected_dm['name'],
                    "contact_title": selected_dm['title'],
                    "contact_email": selected_dm['email'],
                    "stage": "New Lead",
                    "value": deal_val,
                    "probability": 25,
                    "pain_points": profile['three_major_pain_points'],
                    "tech_stack": profile['likely_tech_stack'],
                    "next_action": f"Reach out to {selected_dm['name']} regarding: {profile['custom_value_hook'][:50]}...",
                    "notes": f"Imported from autonomous research scan. Custom Hook: {profile['custom_value_hook']}"
                }
                add_lead(new_crm_lead)
                st.success(f"🎉 Lead successfully injected into CRM! Added {profile['company_name']} under contact {selected_dm['name']}.")
                


# =====================================================================
# MODULE 3: OUTREACH BUILDER & PITCH ADVISOR
# =====================================================================
elif choice == "✉️ Outreach Builder & Pitch Advisor":
    st.title("✉️ Hyper-Personalized Outreach & Pitch Synthesizer")
    st.markdown("Generate high-converting outbound copy across channels. Tap into synthesized personalized audio memos designed to hook high-tier prospects.")
    
    # Select lead from existing CRM leads
    leads = load_leads()
    active_leads = [l for l in leads if l['stage'] not in ["Closed Won", "Closed Lost"]]
    
    if not active_leads:
        st.error("No active leads found in the CRM. Please create a lead on the CRM Dashboard or import one from the Research Hub first.")
    else:
        lead_names = [l['company'] for l in active_leads]
        selected_company = st.selectbox("Select Target Client Lead", lead_names)
        target_lead = next(l for l in active_leads if l['company'] == selected_company)
        
        st.markdown(f"**Target Contact:** {target_lead['contact_name']} — *{target_lead['contact_title']}*")
        st.markdown(f"**Pain Hook:** *\"{target_lead['pain_points'][0]}\"*")
        
        st.divider()
        
        c_opts, c_output = st.columns([1, 2])
        
        with c_opts:
            st.markdown("### 🎨 Synthesizer Settings")
            tone = st.selectbox(
                "Select Voice Pitch/Tone",
                ["Standard Professional", "Assertive/Results-Driven", "Casual/Conversational", "Storytelling/Value-First"]
            )
            
            st.markdown("<br>", unsafe_allow_html=True)
            run_outreach_gen = st.button("⚡ Generate Omnichannel Campaign")
            
            # --- AUDIO MEMO SECTION ---
            st.markdown("<br><hr>", unsafe_allow_html=True)
            st.markdown("### 🎙️ AI Voice Pitch Synthesizer")
            st.markdown("ApexSales features unified vocal speech agents. Listen to our tailored voice pitch memo designed for this prospect:")
            
            # Use pre-generated high-fidelity voice files for default demo companies
            if target_lead['company'].lower() == "stripe":
                st.audio(os.path.join(AUDIO_DIR, "stripe_pitch.mp3"), format="audio/mp3")
                st.success("🔊 Custom voice generated (Identity: Masculine, Advertising/Pitch, Accent: Neutral)")
            elif target_lead['company'].lower() == "shopify":
                st.audio(os.path.join(AUDIO_DIR, "shopify_pitch.mp3"), format="audio/mp3")
                st.success("🔊 Custom voice generated (Identity: Feminine, Advertising/Pitch, Accent: Neutral)")
            elif target_lead['company'].lower() == "tesla":
                st.audio(os.path.join(AUDIO_DIR, "tesla_pitch.mp3"), format="audio/mp3")
                st.success("🔊 Custom voice generated (Identity: Masculine Enterprise, Accent: US Standard)")
            else:
                st.info("💡 Personalized voice memos are pre-rendered for our showcase leads: **Stripe**, **Shopify**, and **Tesla**.")
                st.markdown("""
                <div style='background-color:#161b22; padding:10px; border-radius:6px; border:1px solid #30363d; font-size:12px; color:#8b949e;'>
                    <b>Apex Speech Agent API Integration:</b><br>
                    To activate on-demand vocal synthesis for custom accounts, connect your backend voice node endpoint.
                </div>
                """, unsafe_allow_html=True)
                
        with c_output:
            if run_outreach_gen or 'outreach_cache' not in st.session_state or st.session_state.get('outreach_lead_id') != target_lead['id'] or st.session_state.get('outreach_tone') != tone:
                with st.spinner("Synthesizing copy across cold channels... Drafting objection matrix..."):
                    # Generate the outreach bundle
                    outreach_bundle = generate_outreach(target_lead, tone, target_lead['contact_name'], api_key)
                    # Cache in session state
                    st.session_state['outreach_cache'] = outreach_bundle
                    st.session_state['outreach_lead_id'] = target_lead['id']
                    st.session_state['outreach_tone'] = tone
                    
                    # Log activity in CRM
                    add_activity(target_lead['id'], f"Generated and reviewed outreach campaign bundle using '{tone}' tone.")
            
            bundle = st.session_state['outreach_cache']
            
            # Display channels in beautiful tabs
            st.subheader("📬 Outbound Multi-Channel Campaign")
            o_tab1, o_tab2, o_tab3, o_tab4 = st.tabs(["📧 Cold Email", "💬 LinkedIn InMail", "📞 Cold Call Script", "🛡️ Objection Cheat-Sheet"])
            
            with o_tab1:
                st.markdown(f"**Subject:** `{bundle['cold_email_subject']}`")
                st.markdown("<hr style='margin:5px 0;'>", unsafe_allow_html=True)
                st.text_area("Email Body", value=bundle['cold_email_body'], height=280)
                st.caption("💡 Tip: Copy-paste directly into your mail client or mail merges. Keep tracking pixel tags active.")
                
            with o_tab2:
                st.markdown("**LinkedIn Connection / InMail:**")
                st.text_area("Message Body", value=bundle['linkedin_message'], height=120)
                char_count = len(bundle['linkedin_message'])
                st.caption(f"📏 Character Count: {char_count} / 300 (LinkedIn standard constraint)")
                
            with o_tab3:
                st.markdown("**30-Second Phone Pitch Script:**")
                st.text_area("Spoken Flow", value=bundle['phone_script'], height=160)
                st.caption("🎙️ Spoken Cues: Adjust speech tempo during commas, keep tone friendly but assertive.")
                
            with o_tab4:
                st.markdown("### 🛠️ Strategic Objection Countermeasures")
                st.markdown("Be prepared with tactical counters when the prospect tries to push back:")
                
                for idx, obj in enumerate(bundle.get('objection_handling', [])):
                    with st.expander(f"🛑 Objection: \"{obj['objection']}\""):
                        st.markdown(f"**💡 AI Rebuttal Phrase:**  \n*\"{obj['rebuttal']}\"*")
                        


# =====================================================================
# MODULE 4: OBJECTION NEGOTIATION SIMULATOR
# =====================================================================
elif choice == "🧠 Objection Negotiation Simulator":
    st.title("🧠 Skeptical Buyer Negotiation Simulator")
    st.markdown("Test your negotiation, objections handling, and close-won skills. Practice in a highly interactive environment against realistic corporate personas.")
    
    # Select Persona Sidebar/Left Panel
    p_left, p_right = st.columns([1, 2.5])
    
    with p_left:
        st.markdown("### 👤 Choose Buyer Persona")
        persona_key = st.radio(
            "Select corporate buyer profile:",
            ["cfo", "cto", "founder"],
            format_func=lambda x: CLIENT_PERSONAS[x]["title"]
        )
        
        current_persona = CLIENT_PERSONAS[persona_key]
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"**Target Bio:**  \n*{current_persona['personality']}*")
        
        # Danger zone buttons
        st.divider()
        if st.button("🔄 Reset Conversation Thread"):
            st.session_state['sales_chat_history'] = []
            st.session_state['sales_chat_persona'] = persona_key
            st.success("Simulation reset! Ready for a new pitch.")
            st.rerun()
            
    with p_right:
        st.subheader(f"💬 Simulated Live Call: {current_persona['name']}")
        st.markdown(f"**Role:** {current_persona['title']}")
        st.divider()
        
        # Initialize chat states if empty or persona changed
        if 'sales_chat_history' not in st.session_state or st.session_state.get('sales_chat_persona') != persona_key:
            st.session_state['sales_chat_history'] = []
            st.session_state['sales_chat_persona'] = persona_key
            
        # Display existing messages
        chat_container = st.container()
        
        with chat_container:
            # Show initial greeting
            st.markdown(f"""
            <div style="display:flex; margin-bottom:12px;">
                <div class="chat-bubble buyer-bubble">
                    <b>{current_persona['name']}:</b><br>{current_persona['initial_message']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            for msg in st.session_state['sales_chat_history']:
                bubble_class = "user-bubble" if msg["role"] == "user" else "buyer-bubble"
                sender_name = "You" if msg["role"] == "user" else current_persona['name']
                
                st.markdown(f"""
                <div style="display:flex; margin-bottom:12px;">
                    <div class="chat-bubble {bubble_class}">
                        <b>{sender_name}:</b><br>{msg['content']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
        # Chat input box
        with st.form(key="chat_input_form", clear_on_submit=True):
            user_msg = st.text_input("Type your response / counter-pitch:", placeholder="e.g. I completely understand budget is frozen, Sarah. Let's look at how much you lose daily...")
            submit_msg = st.form_submit_button("Send Pitch Message")
            
        if submit_msg and user_msg.strip():
            # Append user message
            st.session_state['sales_chat_history'].append({"role": "user", "content": user_msg})
            
            # Fetch response
            with st.spinner(f"{current_persona['name']} is typing pushback..."):
                response_text = generate_simulated_objection(
                    persona_key, 
                    st.session_state['sales_chat_history'][:-1], 
                    user_msg, 
                    api_key
                )
                
            st.session_state['sales_chat_history'].append({"role": "assistant", "content": response_text})
            st.rerun()
            
        # Evaluation block
        st.divider()
        st.markdown("### 📊 Performance Coaching Analysis")
        st.markdown("Are you ready to submit the transcript of this interaction to the AI Sales Coach for performance assessment and strategy tips?")
        
        if st.button("🎯 Submit Pitch & Get Report Card"):
            if not st.session_state['sales_chat_history']:
                st.warning("Please type a message and converse with the buyer first before evaluating your performance.")
            else:
                with st.spinner("Analyzing pitch patterns... Scoring objection counters..."):
                    score_card = evaluate_negotiation(persona_key, st.session_state['sales_chat_history'], api_key)
                    
                st.subheader("🎯 Sales Performance Assessment Dossier")
                
                col_sc1, col_sc2 = st.columns([1, 2])
                with col_sc1:
                    # Circular score displays
                    st.markdown(f"""
                    <div style="background-color:#161b22; border-radius:10px; border:1px solid #30363d; padding:20px; text-align:center;">
                        <span style="font-size:14px; color:#8b949e; text-transform:uppercase;">Overall Score</span><br>
                        <span style="font-size:72px; font-weight:bold; color:{'#2ea043' if score_card['overall_score']>=80 else '#d29922' if score_card['overall_score']>=60 else '#f25c54'};">{score_card['overall_score']}%</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.metric("Objection Handling", f"{score_card['objection_handling_score']}%")
                    st.metric("Value Prop Clarity", f"{score_card['value_proposition_clarity_score']}%")
                    st.metric("Closing Strength", f"{score_card['closing_strength_score']}%")
                    
                with col_sc2:
                    st.markdown("### 🌟 Performance Breakdown")
                    st.markdown("**Key Identified Strengths:**")
                    for stg in score_card.get('strengths', []):
                        st.markdown(f"✅ *{stg}*")
                        
                    st.markdown("<br>**Key Areas for Improvement:**", unsafe_allow_html=True)
                    for imp in score_card.get('areas_for_improvement', []):
                        st.markdown(f"⚠️ *{imp}*")
                        
                    st.divider()
                    st.markdown("### 🎓 Expert Coach's Masterclass Advice")
                    st.info(score_card.get('coaching_advice', 'Keep practicing! Symmetrical objection pacing yields stronger closes.'))


# =====================================================================
# MODULE 5: ENTERPRISE PROPOSAL DRAFTSMAN
# =====================================================================
elif choice == "📄 Enterprise Proposal Draftsman":
    st.title("📄 Enterprise Business Proposal & Deck Draftsman")
    st.markdown("Draft and compile a highly detailed, corporate enterprise-grade sales proposal. Tailored specifically around client technical stacks and operational bottlenecks.")
    
    leads = load_leads()
    active_leads = [l for l in leads if l['stage'] not in ["Closed Won", "Closed Lost"]]
    
    if not active_leads:
        st.error("No active leads found in the CRM. Please create or import a lead first.")
    else:
        lead_names = [l['company'] for l in active_leads]
        selected_company = st.selectbox("Select Target Lead for Proposal", lead_names)
        target_lead = next(l for l in active_leads if l['company'] == selected_company)
        
        p_col1, p_col2 = st.columns([1.2, 2])
        
        with p_col1:
            st.markdown("### 🛠️ Architect Proposal Settings")
            product_offering = st.text_input(
                "Your Specific Product / Service Solution", 
                value="Apex AI-Edge Processing Engine", 
                placeholder="e.g. Apex SCADA Edge Neural Shield"
            )
            
            st.markdown("<br>**Recipient Account Context:**", unsafe_allow_html=True)
            st.markdown(f"🏢 **Company:** {target_lead['company']}")
            st.markdown(f"👤 **Lead Recipient:** {target_lead['contact_name']} ({target_lead['contact_title']})")
            st.markdown(f"🔥 **Primary Focus Point:** *\"{target_lead['pain_points'][0]}\"*")
            
            st.markdown("<br>", unsafe_allow_html=True)
            generate_prop_btn = st.button("📄 Draft Enterprise Proposal")
            
        with p_col2:
            st.markdown("### 📝 Drafted Enterprise Agreement")
            
            # Cache proposal drafts to prevent accidental triggers
            if generate_prop_btn or 'proposal_cache' not in st.session_state or st.session_state.get('proposal_lead_id') != target_lead['id'] or st.session_state.get('proposal_product') != product_offering:
                with st.spinner("Generating proposal sections... Crafting financial grids..."):
                    proposal_text = generate_proposal(target_lead, product_offering, api_key)
                    st.session_state['proposal_cache'] = proposal_text
                    st.session_state['proposal_lead_id'] = target_lead['id']
                    st.session_state['proposal_product'] = product_offering
                    
                    # Update lead activities
                    add_activity(target_lead['id'], f"Generated professional business proposal for '{product_offering}'.")
                    
            proposal_md = st.session_state['proposal_cache']
            
            st.markdown(proposal_md)
            
            # Download file option
            st.divider()
            st.markdown("### 💾 Export Proposal")
            st.download_button(
                label="📥 Download Proposal as Markdown (.md)",
                data=proposal_md,
                file_name=f"{target_lead['company'].lower()}_apex_sales_proposal.md",
                mime="text/markdown"
            )
