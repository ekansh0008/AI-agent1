import os
import random
import json
from openai import OpenAI

def get_openai_client(api_key=None):
    key = api_key or os.environ.get("OPENAI_API_KEY")
    if key:
        return OpenAI(api_key=key)
    return None

def research_prospect(company_name, domain, api_key=None):
    """
    Researches a prospect company using OpenAI if available, or highly detailed template engine if in Demo mode.
    """
    client = get_openai_client(api_key)
    
    if client:
        try:
            prompt = f"""
            You are an elite B2B Sales Prospecting Agent.
            Conduct thorough research on the following company:
            Company Name: {company_name}
            Domain/Website: {domain}

            Provide a detailed profile in JSON format with the following keys. Do not include any markdown fences or text outside the JSON:
            {{
                "company_name": "...",
                "domain": "...",
                "estimated_size": "Enterprise / Mid-Market / Startup",
                "core_industry": "...",
                "company_mission_and_focus": "One line summary of what they do and their target market.",
                "likely_tech_stack": ["Tech1", "Tech2", ...],
                "three_major_pain_points": [
                    "Detailed pain point 1 related to business operations, scalability, conversion, or efficiency.",
                    "Detailed pain point 2.",
                    "Detailed pain point 3."
                ],
                "key_decision_makers": [
                    {{"name": "Name 1", "title": "e.g. CTO / VP Operations", "email": "email1@domain.com"}},
                    {{"name": "Name 2", "title": "e.g. Head of E-commerce", "email": "email2@domain.com"}}
                ],
                "recent_news_or_initiatives": "A fictionalized or factual recent milestone, such as expanding in Europe or launching a new warehouse, to use as a sales trigger.",
                "custom_value_hook": "A highly targeted value proposition hook explaining why they need an AI automation agent."
            }}
            """
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert sales intelligence tool. Return strictly valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            # Fall back to demo mode on error
            pass

    # --- DEMO MODE PRE-BAKED KNOWLEDGE ---
    # Normalize inputs
    company_lower = company_name.lower()
    
    # Pre-baked popular company mock data
    if "stripe" in company_lower:
        return {
            "company_name": "Stripe",
            "domain": "stripe.com",
            "estimated_size": "Enterprise",
            "core_industry": "Financial Technology & Payment Processing",
            "company_mission_and_focus": "Building financial infrastructure for the internet to increase the GDP of the digital economy.",
            "likely_tech_stack": ["Ruby", "Scala", "React", "AWS", "Rust", "Kafka"],
            "three_major_pain_points": [
                "Minor payment latency gaps in European card-routing (averaging 180ms overhead).",
                "Authentication declines during heavy flash-sales traffic, leading to cart dropouts.",
                "Elevated overhead in maintaining cross-border tax compliance interfaces for secondary methods."
            ],
            "key_decision_makers": [
                {"name": "David Singleton", "title": "Chief Technology Officer", "email": "david.s@stripe.com"},
                {"name": "Claire Hughes Johnson", "title": "Corporate Officer / Advisor", "email": "claire.hj@stripe.com"}
            ],
            "recent_news_or_initiatives": "Recently announced expansion of regional settlement networks in EMEA to support enterprise localized merchants.",
            "custom_value_hook": "Optimize multi-region payment auth pipelines using local-edge predictive model routing to trim latencies by 40%."
        }
    elif "shopify" in company_lower:
        return {
            "company_name": "Shopify",
            "domain": "shopify.com",
            "estimated_size": "Enterprise",
            "core_industry": "E-commerce Platform & Retail Software",
            "company_mission_and_focus": "Making commerce better for everyone by empowering independent merchants globally with comprehensive store-operating tools.",
            "likely_tech_stack": ["Ruby on Rails", "React", "GraphQL", "GCP", "Kubernetes", "Tailwind CSS"],
            "three_major_pain_points": [
                "Cart abandonment on mobile checkout flow remains high at 14% on non-optimized themes.",
                "Product recommendation carousels display static options that fail to capture real-time user intent hover signals.",
                "Merchant support tickets spike during peak seasons due to general inventory tracking latency errors."
            ],
            "key_decision_makers": [
                {"name": "Sarah Harvey", "title": "Head of Merchant Experience", "email": "sarah.h@shopify.com"},
                {"name": "Tobi Lütke", "title": "Chief Executive Officer", "email": "tobi@shopify.com"}
            ],
            "recent_news_or_initiatives": "Expanded Shop Pay integration in global markets and integrated AI-assisted description generators.",
            "custom_value_hook": "Inject session-aware real-time intent triggers directly into merchant themes, lifting recommendation revenue by 8%."
        }
    elif "tesla" in company_lower:
        return {
            "company_name": "Tesla",
            "domain": "tesla.com",
            "estimated_size": "Enterprise",
            "core_industry": "Automotive, Clean Energy & Robotics",
            "company_mission_and_focus": "Accelerating the world's transition to sustainable energy through electric vehicles and scalable energy storage.",
            "likely_tech_stack": ["Python", "C++", "SCADA Systems", "Kubernetes", "Docker", "Proprietary MES"],
            "three_major_pain_points": [
                "Intermittent sensor noise on conveyor SCADA lines at Giga Texas causing false-alarm shutdowns.",
                "Lack of unified, predictive wear forecasts for multi-ton mechanical stamping presses, leading to unexpected repair downtime.",
                "Logistics bottlenecking in component arrival and propagation of delays to line assemblers."
            ],
            "key_decision_makers": [
                {"name": "Jerome Guillen", "title": "VP of Gigafactory Operations", "email": "jguillen@tesla.com"},
                {"name": "Drew Baglino", "title": "Former SVP Powertrain / Operations Expert", "email": "dbaglino@tesla.com"}
            ],
            "recent_news_or_initiatives": "Scaling Model Y production throughput and upgrading SCADA infrastructure across Giga Texas and Berlin.",
            "custom_value_hook": "Connect plug-and-play edge predictive neural models to live SCADA feeds to forecast component degradation 48 hours early."
        }
    
    # Generic intelligent generation for any other typed company
    words = company_name.split()
    first_word = words[0] if words else "Company"
    domain_clean = domain if domain else f"{first_word.lower()}.com"
    
    industries = ["Software-as-a-Service (SaaS)", "Logistics & Supply Chain", "Digital Health & Biotech", "Fintech & Wealth Management", "Cybersecurity", "E-commerce & Retail Tech"]
    industry = random.choice(industries)
    
    techs = [["React", "Node.js", "AWS", "Python", "PostgreSQL"], ["Angular", "Java", "Azure", "Spring Boot", "Oracle"], ["Vue.js", "Python", "Django", "GCP", "Kubernetes"], ["TypeScript", "Next.js", "Serverless", "Supabase", "Vercel"]]
    tech_stack = random.choice(techs)
    
    pain_points = [
        f"Difficulty scaling lead acquisition and follow-up, causing high sales team overhead at {company_name}.",
        f"Data silos between marketing outreach campaigns and active CRM contact management.",
        f"Manual preparation of sales decks and technical proposals, leading to high sales-cycle latency."
    ]
    
    return {
        "company_name": company_name,
        "domain": domain_clean,
        "estimated_size": "Mid-Market",
        "core_industry": industry,
        "company_mission_and_focus": f"Delivering state-of-the-art solutions in {industry} to accelerate digital transformation for global clients.",
        "likely_tech_stack": tech_stack,
        "three_major_pain_points": pain_points,
        "key_decision_makers": [
            {"name": f"Alex Carter", "title": "VP of Growth & Strategy", "email": f"alex.c@{domain_clean}"},
            {"name": f"Marcus Vance", "title": "Director of Sales Operations", "email": f"marcus.v@{domain_clean}"}
        ],
        "recent_news_or_initiatives": f"Completed an expansion of regional business divisions and announced a focus on automating internal workflows.",
        "custom_value_hook": f"Automate sales research and objection answering cycles using localized agentic workflows to increase conversions."
    }

def generate_outreach(prospect_data, tone, contact_name, api_key=None):
    """
    Generates cold emails, LinkedIn messages, phone scripts, and objections.
    """
    client = get_openai_client(api_key)
    company = prospect_data.get("company_name", "your company")
    pain_point = prospect_data.get("three_major_pain_points", ["general efficiency"])[0]
    hook = prospect_data.get("custom_value_hook", "optimize workflows")
    industry = prospect_data.get("core_industry", "business services")
    news = prospect_data.get("recent_news_or_initiatives", "scaling growth")
    
    if client:
        try:
            prompt = f"""
            You are a master copywriter and sales closer.
            Create highly persuasive sales outreach copy based on the following company research:
            - Company: {company}
            - Industry: {industry}
            - Decision Maker Name: {contact_name}
            - Main Pain Point: {pain_point}
            - Recent News/Trigger: {news}
            - Value Prop Hook: {hook}
            - Selected Tone: {tone}

            Generate structured JSON copy with the following keys. Do not include markdown fences:
            {{
                "cold_email_subject": "...",
                "cold_email_body": "...",
                "linkedin_message": "A hyper-compelling LinkedIn message under 300 characters.",
                "phone_script": "A 30-second conversational, low-pressure cold call script. Use spoken cues.",
                "objection_handling": [
                    {{"objection": "Budget is frozen right now", "rebuttal": "..."}},
                    {{"objection": "We already have an in-house tool or competitor", "rebuttal": "..."}},
                    {{"objection": "Send me some slides and email me later", "rebuttal": "..."}}
                ]
            }}
            """
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an elite sales outreach generator. Return strictly valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            pass

    # --- DEMO MODE COPYWRITING ENGINE ---
    # Custom email & messaging templates based on chosen Tone
    if tone.lower() == "assertive/results-driven":
        email_subj = f"Reducing {company}'s operations drag by 15% (Data inside)"
        email_body = f"Hi {contact_name},\n\nMost operations leaders we speak with in the {industry} space waste substantial developer or team hours addressing {pain_point.lower()}.\n\nOur platform connects directly to your systems to {hook.lower()}, bypassing these overhead bottlenecks.\n\nI’m looking to connect with the operations owner at {company} to coordinate a brief, data-backed 10-minute audit. Are you available for a brief call next Thursday at 10 AM EST?\n\nBest regards,\n[Your Name]\nApexSales Agent"
        
        li_msg = f"Hi {contact_name} - caught the news about {company}'s focus on {news.lower()}. We're helping {industry} leaders solve {pain_point[:60]}... by applying edge automation. Can we exchange a quick note here?"
        
        phone_script = f"(Friendly but commanding) 'Hi {contact_name}, this is [Your Name] with Apex. Look, I know you weren't expecting my call. I'm calling because we've engineered a direct fix for {company}'s ongoing {pain_point[:45]} issue. We typically save teams in {industry} about 15% in operating costs. Would you be open to a 5-minute diagnostic chat next week, or are you fully satisfied with your current metrics?'"
    
    elif tone.lower() == "casual/conversational":
        email_subj = f"Quick question regarding {company}'s workflow"
        email_body = f"Hi {contact_name},\n\nHope your week is off to a great start.\n\nI was researching {company} and saw your recent expansion. It looks incredible! I did notice that with rapid growth, managing {pain_point.lower()} can become a real headache.\n\nWe built a lightweight automation tool that helps companies like yours {hook.lower()} without any heavy IT lifting.\n\nWould you be open to checking out a quick 2-minute video overview of how it works? No pressure at all.\n\nCheers,\n[Your Name]"
        
        li_msg = f"Hey {contact_name}! Love your profile. Saw that {company} is growing fast. We designed a simple way to address {pain_point[:40]} without complex setups. Let's connect if you're open to a casual brainstorm!"
        
        phone_script = f"(Warm and highly relaxed) 'Hey {contact_name}, hope you're having a good day! This is [Your Name] from Apex. I'll be super brief—I was looking at {company}'s setup, specifically around {pain_point[:45]}. We built a tiny tool that makes this completely automatic. Just wanted to see if this is something on your radar right now, or if your team has it totally handled?'"
        
    elif tone.lower() == "storytelling/value-first":
        email_subj = f"How we helped a peer in {industry} bypass {pain_point[:30]}..."
        email_body = f"Hi {contact_name},\n\nA few months ago, an enterprise player in the {industry} space was hit with a major bottleneck: they were losing millions in efficiency due to {pain_point.lower()}.\n\nThey implemented our AI-driven orchestration layers. Within 30 days, they were able to {hook.lower()}, recovering 22% in overhead margins.\n\nI put together a custom projection map for {company} showing how these same patterns apply to your current stack. Let's hop on a brief call on Tuesday to go over the map.\n\nSincerely,\n[Your Name]"
        
        li_msg = f"Hi {contact_name}, we recently helped a {industry} company save 22% in overhead caused by {pain_point[:50]}. Saw your focus at {company} and thought of you. Open to a quick strategy share?"
        
        phone_script = f"(Intriguing and consultative) 'Hi {contact_name}, this is [Your Name] from Apex. I'm actually calling because we just published a case study on how we helped an organization very similar to {company} completely eliminate {pain_point[:45]}. Since you're heading operations there, I wanted to share those metrics. Would you be open to a brief meeting to see if we can replicate those results for {company}?'"
    
    else: # Standard Professional
        email_subj = f"Strategic efficiency proposal for {company}"
        email_body = f"Dear {contact_name},\n\nI am writing to you because of {company}'s notable initiatives in {news.lower()}.\n\nWith increased scale, addressing operational challenges such as {pain_point.lower()} becomes paramount. Our company provides advanced enterprise agents designed to {hook.lower()}, aligning with your technical infrastructure.\n\nI would welcome the opportunity to discuss a tailored solution with you. Are you available for a brief introduction call next Wednesday afternoon?\n\nSincerely,\n[Your Name]\nApexSales Agent"
        
        li_msg = f"Dear {contact_name}, I am reaching out regarding {company}'s outstanding growth. We specialize in automated solutions that resolve {pain_point[:50]} for enterprise organizations. I would appreciate connecting to share ideas."
        
        phone_script = f"(Professional and polite) 'Hello {contact_name}, my name is [Your Name] and I'm calling from ApexSales AI. I am calling because we have developed a tailored solution specifically targeting the {pain_point[:40]} challenges that top-tier {industry} firms face. I wanted to request a brief 10-minute meeting to present our findings. Would Wednesday at 2 PM work for you?'"

    # Objection matrix rebuttal templates
    objections = [
        {
            "objection": "We have no budget or budget is currently frozen",
            "rebuttal": "I completely understand—most companies have tighter belts now. That's why we structure our initial phase as a zero-risk Proof of Concept. If we don't prove we can increase operational margins by at least 3x our cost within 30 days, you pay absolutely nothing. Let's build the projection first, then talk about budget when it makes commercial sense."
        },
        {
            "objection": "We already have an in-house tool or are using a competitor",
            "rebuttal": "That's fantastic, it means you already recognize the massive ROI of solving this. What our clients (who also had in-house tools) discover is that our specialized neural layers run at the system edge, which bypasses general-purpose bottlenecks. We actually run in parallel with your existing systems to squeeze out an extra 10-15% of performance without requiring a rip-and-replace."
        },
        {
            "objection": "Send me some slides and email me later",
            "rebuttal": "I'd be happy to send over some reading material. However, because our agents are custom-built for {company}'s tech stack, general slides won't show you the real impact. What if we do a 5-minute live screen share? If you don't find it immediately relevant, I promise I won't follow up again. How does Tuesday sound?"
        }
    ]
    
    return {
        "cold_email_subject": email_subj,
        "cold_email_body": email_body,
        "linkedin_message": li_msg,
        "phone_script": phone_script,
        "objection_handling": objections
    }

def generate_proposal(prospect_data, product_offering, api_key=None):
    """
    Generates a formal, detailed markdown proposal.
    """
    client = get_openai_client(api_key)
    company = prospect_data.get("company_name", "your company")
    pain_points = prospect_data.get("three_major_pain_points", ["general efficiency"])
    hook = prospect_data.get("custom_value_hook", "optimize workflows")
    industry = prospect_data.get("core_industry", "business services")
    
    if client:
        try:
            prompt = f"""
            You are a senior enterprise solution architect.
            Draft a comprehensive, highly persuasive sales proposal in Markdown.
            
            Prospect Company: {company}
            Target Industry: {industry}
            Core Product Offering: {product_offering}
            Client Pain Points:
            1. {pain_points[0]}
            2. {pain_points[1]}
            3. {pain_points[2]}
            Value Hook: {hook}
            
            The proposal must look professional and include these exact sections:
            1. Executive Summary: Empathize with their scale and pain points.
            2. Proposed Architecture & Solution: How {product_offering} integrates and resolves their challenges.
            3. Operational ROI & Impact: Quantified metrics (e.g., latency cuts, time saved, cost reduction).
            4. Phased Implementation Roadmap: Week-by-week plan from setup to go-live.
            5. Commercial Terms & Investment: Standard enterprise tiers.
            
            Use bolding, bullet points, and high-impact language. Return ONLY markdown.
            """
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a master enterprise solution architect."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4
            )
            return response.choices[0].message.content
        except Exception as e:
            pass

    # --- DEMO MODE PROPOSAL GENERATOR ---
    proposal_md = f"""# ENTERPRISE SOLUTION PROPOSAL

**Prepared For:** {company}  
**Prepared By:** ApexSales Enterprise Architecture Team  
**Date:** July 26, 2026  
**Subject:** High-Impact Operational Optimization via **{product_offering}**

---

## 1. Executive Summary
As a market leader in the **{industry}** sector, {company} operates on a scale where even minor technical and operational inefficiencies compound into substantial revenue leaks. 

Our analysis indicates that {company} currently faces distinct hurdles that directly degrade efficiency and customer retention:
* **Primary Bottleneck:** {pain_points[0]}
* **Secondary Bottleneck:** {pain_points[1]}
* **Tertiary Bottleneck:** {pain_points[2]}

The implementation of **{product_offering}** is designed to systematically eliminate these friction points. By deploying specialized, low-latency agentic layers directly into your operations, we can **{hook.lower()}**, converting operational cost centers into high-yielding margin engines.

---

## 2. Proposed Architecture & Solution
The proposed deployment of **{product_offering}** does not require a costly "rip-and-replace" of your current legacy systems. Instead, our agent runs as a containerized edge daemon, connecting seamlessly to your core API layer:

```
  ┌────────────────────────┐         ┌────────────────────────┐
  │   {company} Core Stack  │ ◄─────► │  {product_offering}   │
  │ (React/Ruby/Cloud APIs)│  JSON   │ (Edge Predictive Agent)│
  └────────────────────────┘  REST   └────────────────────────┘
```

### Key Functional Modules:
1. **Intelligent Edge Router**: Decodes incoming traffic or sensor feeds, predicting failures or bottlenecks in real-time.
2. **Dynamic Queue Dispatcher**: Automatically schedules maintenance or transaction routing parameters, resolving spikes before propagation.
3. **Continuous Reinforcement Layer**: Learns from daily resolution cycles to continuously shrink decision latency.

---

## 3. Operational ROI & Impact
Our models project the following performance improvements within the first 60 days of deployment:

| Metric | Historical Baseline | Post-Implementation (Projected) | Financial Net Impact |
| :--- | :--- | :--- | :--- |
| **System Latency / Delay** | High overhead / manual queues | **45% reduction** in delay | $180k annual resource recovery |
| **Transaction Success Rate** | Decaying auth/conveyor rates | **+3.2% increase** in uptime | $420k net revenue lift |
| **Team Hours Spent Triaging** | 22 hours weekly average | **< 3 hours weekly** | Redirects engineering to core IP |

---

## 4. Phased Implementation Roadmap
We suggest a structured, non-disruptive, 4-week integration cycle:

* **Week 1: Architecture & Sandbox Integration**
  * Conduct a joint review with {company} systems team.
  * Establish secure, encrypted API endpoints and launch container sandbox.
* **Week 2: Shadow Mode Activation**
  * Run {product_offering} in "Shadow Mode" to process real-time feeds without altering production states.
  * Train edge weights on historical log anomalies.
* **Week 3: Managed Pilot (10% Traffic/Feeds)**
  * Route 10% of operational pipelines through active agent resolution loops.
  * Compare telemetry against shadow metrics.
* **Week 4: Full Deployment & Handover**
  * Scale to 100% processing traffic.
  * Finalize administrator dashboard training and hand over API documentation.

---

## 5. Commercial Terms & Investment
To minimize friction and align our incentives with {company}'s success, we propose a performance-based enterprise structure:

* **Pilot Phase (Month 1):** **$0 Initial Fee** (Zero-risk, fully backed proof-of-concept).
* **Enterprise Licensing Tier:** **$8,500 / month** (Billed annually).
* **Guaranteed Performance SLA:** If the agent fails to secure a minimum of **2x operational ROI** against the subscription cost, the monthly licensing fee is discounted by 50%.

---

### Next Steps
1. Approve this technical blueprint for Pilot phase scheduling.
2. Identify 2 key technical points of contact for the sandbox setup next week.
"""
    return proposal_md

# --- SALES NEGOTIATION SIMULATOR ENGINE ---

CLIENT_PERSONAS = {
    "cfo": {
        "name": "Sarah Jenkins",
        "title": "Chief Financial Officer (Budget Skeptic)",
        "personality": "Extremely detail-oriented, obsessed with bottom-line costs, skeptical of 'AI hype', demands immediate hard ROI, dislikes long contracts.",
        "initial_message": "Thanks for getting on the call. Look, I'll be honest. We have had five vendors pitch us 'AI optimization' this month, and we froze software budgets last quarter. Why is your tool anything more than a luxury nice-to-have?"
    },
    "cto": {
        "name": "Arjun Mehta",
        "title": "Technical Gatekeeper (Security & Architecture)",
        "personality": "Wants to build everything in-house, paranoid about data privacy and hosting, demands to know details of security layers, hates magic boxes.",
        "initial_message": "Thanks for the intro. My main concern is security and resource overhead. We don't send customer logs outside our VPC, and we don't want a heavy agent slow-polling our databases. Why shouldn't we just spin up a couple of developers and build this ourselves?"
    },
    "founder": {
        "name": "Brooke Lawson",
        "title": "Indecisive Startup Founder (Time & Urgency)",
        "personality": "Stretched extremely thin, constantly changing focus, distracted, fears complex integrations that steal her attention, wants rapid plug-and-play.",
        "initial_message": "Hey! Sorry I'm a few minutes late, things are chaotic today. We have about 50 other priorities right now. This sounds cool, but we just don't have the time to deal with a big implementation project. Can't we talk about this next quarter?"
    }
}

def generate_simulated_objection(client_persona, message_history, user_pitch, api_key=None):
    """
    Generate the next response from the simulated buyer.
    """
    persona = CLIENT_PERSONAS.get(client_persona.lower(), CLIENT_PERSONAS["cfo"])
    client = get_openai_client(api_key)
    
    if client:
        try:
            # Format history for LLM
            formatted_messages = [
                {"role": "system", "content": f"You are acting as {persona['name']}, the {persona['title']}. Your personality is: {persona['personality']}. Be highly realistic, push back sharply but professionally on sales tactics. Do not make it easy. Do not break character under any circumstances. Keep your answers under 4-5 sentences, conversational and direct."}
            ]
            for m in message_history:
                formatted_messages.append({"role": m["role"], "content": m["content"]})
            
            # Add latest user pitch
            formatted_messages.append({"role": "user", "content": user_pitch})
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=formatted_messages,
                temperature=0.8
            )
            return response.choices[0].message.content
        except Exception as e:
            pass

    # --- DEMO MODE CHAT SIMULATOR (Rules/Keywords Based) ---
    pitch_lower = user_pitch.lower()
    history_len = len(message_history)
    
    # Simple rule-based chatbot for Demo Mode
    if client_persona.lower() == "cfo":
        if "roi" in pitch_lower or "save" in pitch_lower or "revenue" in pitch_lower or "cost" in pitch_lower or "free" in pitch_lower or "zero" in pitch_lower:
            replies = [
                "Okay, saving money sounds good on paper, but how much implementation work does my team have to do? Time is money too, and I can't spare any developers.",
                "Alright, you talk about a 3x return. Can we structure our contract so that we only pay you a percentage of the actual, audited savings? Let's put your money where your mouth is.",
                "Interesting. If we do a pilot, what guarantee do I have that this won't break our current pipelines and cause a costly outage?"
            ]
            return random.choice(replies)
        elif "easy" in pitch_lower or "simple" in pitch_lower or "api" in pitch_lower or "days" in pitch_lower:
            return "You say it's easy, but standard enterprise integrations always drag on for months. If this takes longer than two weeks, we're losing money on internal meetings. Can you write a penalty clause in the contract for late delivery?"
        else:
            return "That sounds nice, but it doesn't solve my core issue: why should I spend dollars on this right now instead of putting those dollars into customer acquisition? Explain the direct cash-flow impact."
            
    elif client_persona.lower() == "cto":
        if "security" in pitch_lower or "private" in pitch_lower or "vpc" in pitch_lower or "encrypt" in pitch_lower or "data" in pitch_lower:
            return "Good to hear you take security seriously. Do you have a SOC 2 Type II report? And can we deploy your agent completely self-hosted in our AWS environment, or do you require egress to your servers?"
        elif "in-house" in pitch_lower or "build" in pitch_lower or "developers" in pitch_lower or "custom" in pitch_lower:
            return "We have a highly talented platform team. If we just write a customized script and pipe the telemetry to an open-source model, we own the IP and don't have another recurring bill. Why shouldn't we build it?"
        else:
            return "I need to understand the underlying architecture. How does your agent handle API rate limits and network drops? If your service goes down, does it block our core transaction processing or fail gracefully?"
            
    else: # Founder
        if "fast" in pitch_lower or "minutes" in pitch_lower or "setup" in pitch_lower or "handle" in pitch_lower or "automatic" in pitch_lower:
            return "If it truly takes 15 minutes of our time, I might be able to let my lead dev take a look. But if he says it's going to take him away from our core product launch, we'll have to push this off. Can we do a live walkthrough of the integration?"
        elif "later" in pitch_lower or "next quarter" in pitch_lower or "busy" in pitch_lower:
            return "Exactly, we are just swamped. Send me a calendar link and let's aim for late October once our new version is out in the wild."
        else:
            return "I'm pulled in ten directions today. Your pitch is interesting, but I need a bulletproof summary. What are the three exact things your tool does that would make my life easier tomorrow morning?"

def evaluate_negotiation(client_persona, chat_history, api_key=None):
    """
    Evaluates the sales negotiation session and provides a report card.
    """
    persona = CLIENT_PERSONAS.get(client_persona.lower(), CLIENT_PERSONAS["cfo"])
    client = get_openai_client(api_key)
    
    # Format the entire chat history for evaluation
    chat_transcript = ""
    for m in chat_history:
        sender = "Buyer" if m["role"] == "assistant" else "Salesperson"
        chat_transcript += f"{sender}: {m['content']}\n\n"
        
    if client:
        try:
            prompt = f"""
            You are a world-class Sales Performance Assessor and Objections Coach.
            Review the following sales chat transcript between a salesperson and a skeptical buyer:
            Buyer Persona: {persona['name']} - {persona['title']}
            Personality Context: {persona['personality']}
            
            Transcript:
            {chat_transcript}
            
            Analyze the salesperson's performance. Return a structured JSON assessment with the exact keys. Do not include markdown fences:
            {{
                "objection_handling_score": 85, 
                "value_proposition_clarity_score": 75,
                "closing_strength_score": 60,
                "overall_score": 73,
                "strengths": [
                    "Point 1...",
                    "Point 2..."
                ],
                "areas_for_improvement": [
                    "Point 1...",
                    "Point 2..."
                ],
                "coaching_advice": "A paragraph of highly actionable, encouraging advice from an expert sales director, giving specific lines they could say next time."
            }}
            """
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a professional sales coach. Return strictly valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            pass

    # --- DEMO MODE COOPERATIVE EVALUATOR ---
    # Give a dynamic evaluation based on message count and keywords in the transcript
    total_messages = len(chat_history)
    transcript_lower = chat_transcript.lower()
    
    # Simple heuristic scoring
    objection_score = 75
    value_score = 70
    closing_score = 65
    
    strengths = []
    improvements = []
    
    if total_messages >= 4:
        objection_score += 10
        strengths.append("Demonstrated high persistence and kept the buyer engaged across multiple conversational turns.")
    else:
        improvements.append("The sales process was rushed. Try asking more diagnostic questions before pitching solutions.")
        
    if "roi" in transcript_lower or "percent" in transcript_lower or "saving" in transcript_lower or "dollar" in transcript_lower:
        value_score += 15
        strengths.append("Effectively anchored the conversation on commercial outcomes, margins, and quantitative benefits.")
    else:
        improvements.append("Missed opportunities to quantify the savings. Skeptical buyers need hard numbers (ROI projections) to justify spend.")
        
    if "security" in transcript_lower or "api" in transcript_lower or "private" in transcript_lower:
        strengths.append("Addressed key technical integration and security concerns directly, helping de-risk the deployment.")
        
    if "trial" in transcript_lower or "pilot" in transcript_lower or "free" in transcript_lower or "schedule" in transcript_lower or "tuesday" in transcript_lower or "call" in transcript_lower:
        closing_score += 20
        strengths.append("Successfully pushed for a low-friction next step (pilot/diagnostic call) to close the objection gap.")
    else:
        improvements.append("Lacked a clear call to action (CTA). Always suggest a specific, small next action (e.g., '10-minute demo this Tuesday') rather than leaving it open-ended.")

    # Fill in defaults if list is empty
    if not strengths:
        strengths.append("Maintained a professional, polite, and responsive tone throughout.")
    if not improvements:
        improvements.append("Explore deeper discovery. Ask 'What does your current backlog look like?' to build urgency.")
        
    overall_score = int((objection_score + value_score + closing_score) / 3)
    
    coaching_advice = f"Good job practicing against {persona['name']}. "
    if persona['title'].find("CFO") != -1:
        coaching_advice += "CFOs respond best to cash flow and risk reduction. Instead of describing *how* your product works, describe the *financial cost* of their current problem. Next time, try saying: 'I understand budget is frozen, Sarah. That's why we frame this around capturing lost margins that are currently leaking out of your checkout daily. If we save you $30k this month in shadow declines, does it make sense to talk?'"
    elif persona['title'].find("CTO") != -1:
        coaching_advice += "CTOs hate technical lock-in and high maintenance. Reassure Arjun immediately about security boundaries. Next time, try saying: 'Arjun, we completely support self-hosted, on-prem container deployments. Your customer data never leaves your infrastructure. We run in silent telemetry mode so there is zero latency impact on your live transactional databases.'"
    else:
        coaching_advice += "Busy founders suffer from choice overload. Give Brooke high convenience. Next time, try saying: 'Brooke, I know you're running a million miles an hour. We handle 100% of the integration lift ourselves, taking up less than 15 minutes of your developer's time. If it doesn't work, you've lost nothing; if it does, you've automated 10 hours of work weekly.'"

    return {
        "objection_handling_score": min(objection_score, 100),
        "value_proposition_clarity_score": min(value_score, 100),
        "closing_strength_score": min(closing_score, 100),
        "overall_score": min(overall_score, 100),
        "strengths": strengths,
        "areas_for_improvement": improvements,
        "coaching_advice": coaching_advice
    }
