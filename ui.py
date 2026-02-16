import streamlit as st
import requests
import base64
import os
import time

API_URL = os.getenv("API_URL", "http://localhost:8000/optimize-resume")

st.set_page_config(
    page_title="AI Resume Optimizer",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("📄 AI Resume Optimizer")
st.caption("🤖 Autonomous Multi-Agent System • Planner → Executor → Quality Review")

# ===== ANIMATED TOP BANNER DISCLAIMER =====
if "disclaimer_dismissed" not in st.session_state:
    st.session_state.disclaimer_dismissed = False

if not st.session_state.disclaimer_dismissed:
    # Custom CSS for animated banner
    st.markdown("""
        <style>
        @keyframes slideDown {
            from {
                transform: translateY(-100%);
                opacity: 0;
            }
            to {
                transform: translateY(0);
                opacity: 1;
            }
        }
        .disclaimer-banner {
            background: linear-gradient(135deg, #fff3cd 0%, #ffe69c 100%);
            border-left: 5px solid #ff9800;
            padding: 16px 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            animation: slideDown 0.5s ease-out;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .disclaimer-text {
            color: #856404;
            font-size: 15px;
            line-height: 1.5;
            flex: 1;
        }
        .disclaimer-icon {
            font-size: 24px;
            margin-right: 12px;
        }
        </style>
        <div class="disclaimer-banner">
            <div style="display: flex; align-items: center; flex: 1;">
                <span class="disclaimer-icon">⚠️</span>
                <div class="disclaimer-text">
                    <strong>Beta Feature:</strong> PDF structure accuracy is currently being improved. 
                    We apologize for any formatting inconsistencies. For best results, review the Executor output.
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Dismiss button (positioned at top right)
    col1, col2, col3 = st.columns([5, 1, 0.3])
    with col2:
        if st.button("✕ Dismiss", key="dismiss_warning", type="secondary"):
            st.session_state.disclaimer_dismissed = True
            st.rerun()

# ===== TEMPLATE INFO BOX =====
st.info(
    " **Tip:** Review the Executor Agent output below. You can copy and manually "
    "customize the content for your preferred resume style if needed since the template used here is generic and ATS friendly.",
    icon="ℹ️"
)

resume = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
job_description = st.text_area(
    "Paste Job Description",
    height=220,
    placeholder="Paste the complete job description here..."
)
template = st.selectbox("Resume Template", ["harvard", "professional", "classic"])

if st.button("🚀 Start Multi-Agent Optimization", type="primary", use_container_width=True):
    if not resume or not job_description.strip():
        st.warning("⚠️ Please upload your resume and paste a job description.")
        st.stop()

    # ===== SUBMIT JOB =====
    status_container = st.empty()
    progress_bar = st.progress(0)
    
    status_container.info("🤖 **Submitting optimization job...**")
    progress_bar.progress(5)

    try:
        # Submit job to backend
        submit_res = requests.post(
            API_URL,
            files={"resume": resume},
            data={
                "job_description": job_description,
                "template": template
            },
            timeout=30
        )

        if submit_res.status_code != 200:
            st.error("❌ Failed to submit job")
            st.code(submit_res.text)
            st.stop()

        job_data = submit_res.json()
        job_id = job_data.get("job_id")
        
        if not job_id:
            st.error("❌ No job ID returned from server")
            st.stop()
        
        # ===== POLL FOR STATUS =====
        status_url = API_URL.replace("/optimize-resume", f"/status/{job_id}")
        max_attempts = 120  # 2 minutes max (120 * 1 second)
        attempt = 0
        
        while attempt < max_attempts:
            time.sleep(1)
            attempt += 1
            
            # Get job status
            status_res = requests.get(status_url, timeout=10)
            
            if status_res.status_code != 200:
                continue
            
            status_data = status_res.json()
            job_status = status_data.get("status")
            progress = status_data.get("progress", 0)
            agents = status_data.get("agents", {})
            
            # Update progress bar
            progress_bar.progress(min(progress, 100))
            
            # Display agent status
            planner_status = agents.get("planner", {}).get("status", "pending")
            executor_status = agents.get("executor", {}).get("status", "pending")
            critic_status = agents.get("critic", {}).get("status", "pending")
            
            if planner_status == "running":
                status_container.info("🧠 **Planner Agent:** Analyzing resume gaps and job requirements...")
            elif planner_status == "complete" and executor_status == "pending":
                status_container.success("✅ **Planner Agent:** Complete!")
                time.sleep(0.3)
                status_container.info("⚙️ **Executor Agent:** Rewriting for " + template.title() + " template...")
            elif executor_status == "complete" and critic_status == "pending":
                status_container.success("✅ **Executor Agent:** Complete!")
                time.sleep(0.3)
                status_container.info("🧐 **Critic Agent:** Validating field mapping and format...")
            elif critic_status == "complete":
                status_container.success("✅ **Critic Agent:** Validation complete!")
            
            # Check if job is complete
            if job_status == "complete":
                progress_bar.progress(100)
                status_container.success("✅ **Multi-Agent Optimization Complete!**")
                time.sleep(0.5)
                status_container.empty()
                progress_bar.empty()
                
                # Get final result
                data = status_data.get("result", {})
                break
            
            elif job_status == "error":
                st.error("❌ Job failed: " + status_data.get("error", "Unknown error"))
                st.stop()
        
        else:
            # Timeout
            st.error("⏱️ Job timeout. Please try again.")
            st.stop()

    except requests.exceptions.Timeout:
        st.error("⏱️ Request timeout. The backend may be cold-starting (wait 60s and retry).")
        st.stop()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Request failed: {e}")
        st.stop()

    st.success("🎉 Your resume has been optimized by our AI agents!")
    
    # ===== DISPLAY PRE-PDF VALIDATION RESULTS =====
    pre_pdf_validation = data.get("pre_pdf_validation", {})
    
    if pre_pdf_validation:
        integrity_score = pre_pdf_validation.get("data_integrity_score", 0)
        warnings = pre_pdf_validation.get("warnings", [])
        field_mapping = pre_pdf_validation.get("field_mapping", {})
        
        # Display data integrity score
        if integrity_score >= 90:
            st.success(f"✅ **Data Integrity: {integrity_score}%** - Excellent mapping!")
        elif integrity_score >= 70:
            st.info(f"ℹ️ **Data Integrity: {integrity_score}%** - Good mapping with minor issues")
        else:
            st.warning(f"⚠️ **Data Integrity: {integrity_score}%** - Some fields may be missing")
        
        # Show detailed field mapping in expander
        with st.expander("📊 **Detailed Field Mapping Report**", expanded=(integrity_score < 90)):
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.write("**Contact Information:**")
                st.write(f"{'✅' if field_mapping.get('name') else '❌'} Name")
                st.write(f"{'✅' if field_mapping.get('email') else '❌'} Email")
                st.write(f"{'✅' if field_mapping.get('phone') else '❌'} Phone")
                st.write(f"{'✅' if field_mapping.get('linkedin') else '❌'} LinkedIn")
                st.write(f"{'✅' if field_mapping.get('github') else '⚠️'} GitHub (optional)")
            
            with col_b:
                st.write("**Resume Sections:**")
                st.write(f"{'✅' if field_mapping.get('education') else '❌'} Education")
                
                exp_count = field_mapping.get('experience_count', {})
                exp_match = exp_count.get('match', False)
                st.write(f"{'✅' if exp_match else '⚠️'} Experience: {exp_count.get('original', 0)} → {exp_count.get('final', 0)}")
                
                proj_count = field_mapping.get('projects_count', {})
                proj_match = proj_count.get('match', False)
                st.write(f"{'✅' if proj_match else '⚠️'} Projects: {proj_count.get('original', 0)} → {proj_count.get('final', 0)}")
                
                skills_count = field_mapping.get('skills_count', {})
                st.write(f"ℹ️ Skills: {skills_count.get('original', 0)} → {skills_count.get('final', 0)}")
            
            # Display warnings
            if warnings:
                st.divider()
                st.write("**⚠️ Validation Warnings:**")
                for warning in warnings:
                    st.warning(warning, icon="⚠️")
            else:
                st.divider()
                st.success("✅ No validation warnings - All fields properly mapped!")
    
    # Display agent validation summary if available
    validation = data.get("validation", {})
    if validation and validation.get("validation_passed"):
        with st.expander("🧐 **Critic Agent Validation Report**", expanded=False):
            st.success(
                f"✅ **Agent Validation Passed**\n\n"
                f"• Jobs Mapped: {validation.get('jobs_mapped', {}).get('original', 0)} → "
                f"{validation.get('jobs_mapped', {}).get('optimized', 0)}\n"
                f"• Projects Mapped: {validation.get('projects_mapped', {}).get('original', 0)} → "
                f"{validation.get('projects_mapped', {}).get('optimized', 0)}\n"
                f"• Data Integrity: {validation.get('data_integrity', 'N/A')}"
            )
    elif validation and validation.get("warnings"):
        st.warning("⚠️ **Agent Validation Warnings:**\n" + "\n".join(f"• {w}" for w in validation["warnings"]))

    # ===== AGENT OUTPUTS (PLANNER & EXECUTOR ONLY) =====
    col1, col2 = st.columns(2)
    
    with col1:
        if "planner" in data:
            with st.expander("🧠 **Planner Agent** - Strategy & Analysis", expanded=False):
                st.markdown(data["planner"])

    with col2:
        if "executor" in data:
            with st.expander("⚙️ **Executor Agent** - Optimized Content", expanded=True):
                st.markdown(data["executor"])
                st.caption("💡 Copy this content to customize your resume template manually")

    # ===== PDF DOWNLOAD =====
    if "pdf_base64" in data:
        st.divider()
        pdf_bytes = base64.b64decode(data["pdf_base64"])
        
        col_download1, col_download2, col_download3 = st.columns([1, 2, 1])
        with col_download2:
            st.download_button(
                "📥 Download Optimized Resume (PDF)",
                pdf_bytes,
                file_name=f"resume_optimized_{template}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )