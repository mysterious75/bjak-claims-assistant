"""BJAK AI Claims Assistant - Streamlit UI"""

import streamlit as st
import os
import time
from datetime import datetime

from backend.llm_client import LLMClient
from backend.rag_engine import RAGEngine
from backend.claims_agent import ClaimsAgent
from backend.evaluator import Evaluator

# Page config
st.set_page_config(
    page_title="BJAK AI Claims Assistant",
    page_icon="🏥",
    layout="wide"
)

# Initialize session state
if "agent" not in st.session_state:
    st.session_state.llm = LLMClient()
    st.session_state.rag = RAGEngine(st.session_state.llm)
    st.session_state.agent = ClaimsAgent(st.session_state.llm, st.session_state.rag)
    st.session_state.evaluator = Evaluator()
    st.session_state.messages = []
    st.session_state.session_id = "streamlit_session"

# Header
st.title("🏥 BJAK AI Claims Assistant")
st.caption("AI-powered insurance claims processing | Built for BJAK Applied AI Engineer Role")

# Sidebar
with st.sidebar:
    st.header("Navigation")
    page = st.radio(
        "Go to",
        ["💬 Chat Assistant", "📝 File Claim", "📊 Track Claim", "❓ FAQ", "📈 Demo", "📊 Metrics"],
        label_visibility="collapsed"
    )
    
    st.divider()
    st.subheader("System Status")
    
    # Check LLM status
    if st.button("Check API Status"):
        with st.spinner("Checking..."):
            if st.session_state.llm.health_check():
                st.success("Gemini API: Connected")
            else:
                st.error("Gemini API: Failed")
    
    # RAG stats
    rag_stats = st.session_state.rag.get_stats()
    if rag_stats["status"] == "loaded":
        st.info(f"📚 FAQ Documents: {rag_stats['document_count']}")
    
    # Session metrics
    metrics = st.session_state.evaluator.get_session_metrics()
    if metrics.get("total_interactions", 0) > 0:
        st.metric("Interactions", metrics["total_interactions"])
        st.metric("Avg Response", f"{metrics.get('avg_response_time_ms', 0):.0f}ms")
    
    st.divider()
    st.caption("v1.0.0 | Built with Streamlit + Gemini")


def log_interaction(query, response, action, start_time, sources=None):
    """Log interaction to evaluator."""
    elapsed_ms = (time.time() - start_time) * 1000
    st.session_state.evaluator.log_interaction(
        session_id=st.session_state.session_id,
        user_query=query,
        assistant_response=response,
        action=action,
        response_time_ms=elapsed_ms,
        sources_used=len(sources) if sources else 0,
        success=True
    )


# Chat Assistant Page
if page == "💬 Chat Assistant":
    st.header("💬 Chat with Claims Assistant")
    
    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "sources" in msg and msg["sources"]:
                with st.expander("📚 Sources"):
                    for src in msg["sources"][:3]:
                        st.caption(f"📄 {src.get('source', 'unknown')}")
    
    # Chat input
    if prompt := st.chat_input("Ask about your insurance claim..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Process with agent
        with st.chat_message("assistant"):
            with st.spinner("Processing..."):
                start_time = time.time()
                result = st.session_state.agent.process_message(
                    prompt,
                    st.session_state.session_id
                )
                
                response = result.get("response", "I'm here to help!")
                sources = result.get("tool_result", {}).get("sources", [])
                
                # Log interaction
                log_interaction(prompt, response, result.get("action", "respond"), start_time, sources)
                
                st.markdown(response)
                
                # Show sources if available
                if sources:
                    with st.expander("📚 Sources"):
                        for src in sources[:3]:
                            st.caption(f"📄 {src.get('source', 'unknown')}")
        
        # Save to history
        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "sources": sources
        })

# File Claim Page
elif page == "📝 File Claim":
    st.header("📝 File New Insurance Claim")
    
    with st.form("claim_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            claim_type = st.selectbox(
                "Claim Type",
                ["health", "motor", "life", "travel"]
            )
            claimant_name = st.text_input("Your Full Name*")
            policy_number = st.text_input("Policy Number")
        
        with col2:
            amount = st.number_input("Amount Claimed (USD)", min_value=0, value=0)
            incident_date = st.date_input("Date of Incident")
        
        description = st.text_area("Description of Incident*", height=150)
        
        # Document upload
        st.subheader("📎 Supporting Documents")
        uploaded_files = st.file_uploader(
            "Upload documents (PDF, JPG, PNG)",
            type=["pdf", "jpg", "jpeg", "png"],
            accept_multiple_files=True
        )
        
        submitted = st.form_submit_button("Submit Claim", type="primary")
        
        if submitted:
            if not claimant_name or not description:
                st.error("Please fill in required fields (Name, Description)")
            else:
                start_time = time.time()
                
                # Process documents
                documents = []
                if uploaded_files:
                    for file in uploaded_files:
                        documents.append({
                            "filename": file.name,
                            "content": file.getvalue()
                        })
                
                # File claim
                result = st.session_state.agent.file_claim({
                    "claim_type": claim_type,
                    "claimant_name": claimant_name,
                    "description": description,
                    "amount_claimed": amount,
                    "policy_number": policy_number,
                    "documents": documents
                })
                
                # Log interaction
                log_interaction(
                    f"File claim: {claim_type}",
                    f"Claim {result.get('claim_id', 'failed')}",
                    "file_claim",
                    start_time
                )
                
                if result["success"]:
                    st.success(f"✅ Claim Filed Successfully!")
                    st.info(f"**Claim ID:** {result['claim_id']}")
                    st.info(f"**Status:** {result['claim']['status']}")
                    
                    with st.expander("View Claim Details"):
                        st.json(result["claim"])
                else:
                    st.error(f"❌ {result['error']}")

# Track Claim Page
elif page == "📊 Track Claim":
    st.header("📊 Track Your Claim")
    
    claim_id = st.text_input("Enter Claim ID (e.g., BJK-XXXXXXXX)")
    
    if claim_id:
        start_time = time.time()
        result = st.session_state.agent.check_status(claim_id)
        
        # Log interaction
        log_interaction(
            f"Check status: {claim_id}",
            f"Status: {result.get('status', 'not found')}",
            "check_status",
            start_time
        )
        
        if result["success"]:
            st.success(f"Claim Found: {result['claim_id']}")
            
            # Status badge
            status = result["status"]
            if status == "APPROVED":
                st.success(f"Status: {status}")
            elif status == "REJECTED":
                st.error(f"Status: {status}")
            elif status == "ESCALATED":
                st.warning(f"Status: {status}")
            else:
                st.info(f"Status: {status}")
            
            # Timeline
            st.subheader("📅 Timeline")
            for event in result["timeline"]:
                with st.container():
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        st.caption(event["timestamp"][:10])
                    with col2:
                        st.write(f"**{event['status']}**")
                        st.caption(event.get("note", ""))
        else:
            st.warning(f"Claim not found. Please check the ID.")

# FAQ Page
elif page == "❓ FAQ":
    st.header("❓ Insurance FAQ")
    
    # Sample questions
    st.subheader("Common Questions")
    sample_questions = [
        "What documents do I need for a motor insurance claim?",
        "How long does claim processing take?",
        "What is not covered under health insurance?",
        "How do I check my policy status?",
        "What should I do immediately after an accident?"
    ]
    
    for q in sample_questions:
        if st.button(q, key=q):
            with st.spinner("Searching..."):
                start_time = time.time()
                result = st.session_state.agent.ask_faq(q)
                
                # Log interaction
                log_interaction(q, result["answer"], "ask_faq", start_time, result.get("sources"))
                
                st.info(result["answer"])
                if result.get("sources"):
                    with st.expander("📚 Sources"):
                        for src in result["sources"][:3]:
                            st.caption(f"📄 {src.get('source', 'unknown')}")
    
    st.divider()
    
    # Custom question
    custom_q = st.text_input("Ask your own question:")
    if custom_q:
        with st.spinner("Searching..."):
            start_time = time.time()
            result = st.session_state.agent.ask_faq(custom_q)
            
            # Log interaction
            log_interaction(custom_q, result["answer"], "ask_faq", start_time, result.get("sources"))
            
            st.info(result["answer"])

# Demo Page
elif page == "📈 Demo":
    st.header("📈 Demo Scenarios")
    
    demo_type = st.selectbox(
        "Select Demo",
        ["Health Insurance Claim", "Motor Insurance Claim", "FAQ Interaction", "Human Escalation"]
    )
    
    if demo_type == "Health Insurance Claim":
        st.subheader("🏥 Health Insurance Claim Demo")
        
        if st.button("Run Demo"):
            with st.spinner("Running demo..."):
                # Demo conversation
                messages = [
                    "Hi, I need to file a health insurance claim",
                    "My name is John Doe, and I was hospitalized last week for 3 days",
                    "The total bill was $5,000. I have policy number HL-12345",
                    "I've uploaded the hospital bill and discharge summary"
                ]
                
                for msg in messages:
                    st.chat_message("user").markdown(msg)
                    start_time = time.time()
                    result = st.session_state.agent.process_message(
                        msg,
                        f"demo_health_{datetime.now().timestamp()}"
                    )
                    log_interaction(msg, result["response"], result.get("action", "respond"), start_time)
                    st.chat_message("assistant").markdown(result["response"])
                    st.divider()
    
    elif demo_type == "Motor Insurance Claim":
        st.subheader("🚗 Motor Insurance Claim Demo")
        
        if st.button("Run Demo"):
            with st.spinner("Running demo..."):
                messages = [
                    "I was in a car accident yesterday",
                    "My car has front bumper damage",
                    "The other driver was at fault",
                    "What documents do I need?"
                ]
                
                for msg in messages:
                    st.chat_message("user").markdown(msg)
                    start_time = time.time()
                    result = st.session_state.agent.process_message(
                        msg,
                        f"demo_motor_{datetime.now().timestamp()}"
                    )
                    log_interaction(msg, result["response"], result.get("action", "respond"), start_time)
                    st.chat_message("assistant").markdown(result["response"])
                    st.divider()
    
    elif demo_type == "FAQ Interaction":
        st.subheader("❓ FAQ Demo")
        
        if st.button("Run Demo"):
            with st.spinner("Running demo..."):
                questions = [
                    "What is covered under travel insurance?",
                    "How do I renew my policy?",
                    "What is the claim settlement ratio?"
                ]
                
                for q in questions:
                    st.chat_message("user").markdown(q)
                    start_time = time.time()
                    result = st.session_state.agent.ask_faq(q)
                    log_interaction(q, result["answer"], "ask_faq", start_time, result.get("sources"))
                    st.chat_message("assistant").markdown(result["answer"])
                    st.divider()
    
    elif demo_type == "Human Escalation":
        st.subheader("👤 Human Escalation Demo")
        
        if st.button("Run Demo"):
            with st.spinner("Running demo..."):
                messages = [
                    "I'm not happy with the claim decision",
                    "I want to speak to a manager",
                    "This is unacceptable, please escalate"
                ]
                
                for msg in messages:
                    st.chat_message("user").markdown(msg)
                    start_time = time.time()
                    result = st.session_state.agent.process_message(
                        msg,
                        f"demo_escalation_{datetime.now().timestamp()}"
                    )
                    log_interaction(msg, result["response"], result.get("action", "respond"), start_time)
                    st.chat_message("assistant").markdown(result["response"])
                    st.divider()

# Metrics Page
elif page == "📊 Metrics":
    st.header("📊 Session Metrics")
    
    metrics = st.session_state.evaluator.get_session_metrics()
    
    if metrics.get("total_interactions", 0) == 0:
        st.info("No interactions logged yet. Start chatting to see metrics!")
    else:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Interactions", metrics["total_interactions"])
        with col2:
            st.metric("Success Rate", f"{metrics['success_rate']*100:.1f}%")
        with col3:
            st.metric("Avg Response Time", f"{metrics['avg_response_time_ms']:.0f}ms")
        
        st.subheader("Action Distribution")
        action_dist = metrics.get("action_distribution", {})
        if action_dist:
            st.bar_chart(action_dist)
        
        # Export report
        if st.button("Export Report"):
            report = st.session_state.evaluator.export_report()
            st.json(report)
            st.success("Report exported to logs/evaluation_report.json")
