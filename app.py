import streamlit as st
import time
import json
from datetime import datetime
import requests
from utils.database import Database
from utils.simulator import BenchmarkSimulator
from utils.stripe_handler import StripeHandler

# Page config
st.set_page_config(
    page_title="ArchNet SaaS Demo",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize components
db = Database()
simulator = BenchmarkSimulator()
stripe_handler = StripeHandler()

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 2rem;
    }
    .credit-badge {
        background-color: #10B981;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
    }
    .job-card {
        border: 1px solid #E5E7EB;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #F9FAFB;
    }
    .stButton button {
        width: 100%;
        border-radius: 10px;
        padding: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

def login_section():
    """User login/registration"""
    st.sidebar.title("🔐 Login")
    email = st.sidebar.text_input("Enter your email", placeholder="user@example.com")
    
    if st.sidebar.button("Login / Register", type="primary"):
        if "@" in email and "." in email:
            # Check if user exists
            user = db.get_user(email)
            if not user:
                # Create new user
                user = db.create_user(email)
                st.sidebar.success(f"Welcome! You get 3 free credits!")
            else:
                st.sidebar.success(f"Welcome back, {email}!")
            
            # Store in session
            st.session_state["user_email"] = email
            st.session_state["user"] = user
            st.rerun()
        else:
            st.sidebar.error("Please enter a valid email")

def user_dashboard():
    """Main user dashboard"""
    user_email = st.session_state["user_email"]
    user = st.session_state["user"]
    
    # Header
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.markdown(f"<h1 class='main-header'>🤖 ArchNet SaaS Platform</h1>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='credit-badge'>Credits: {user['credits']}</div>", unsafe_allow_html=True)
    with col3:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🚀 Run Benchmark", "📊 My Results", "💰 Buy Credits", "ℹ️ About"])
    
    with tab1:
        run_benchmark_tab(user)
    
    with tab2:
        results_tab(user_email)
    
    with tab3:
        buy_credits_tab(user_email, user)
    
    with tab4:
        about_tab()

def run_benchmark_tab(user):
    """Tab for running benchmarks"""
    st.subheader("Run New Benchmark")
    
    col1, col2 = st.columns(2)
    
    with col1:
        disease = st.selectbox(
            "Select Disease Type",
            ["pneumonia", "skin_cancer", "covid_19", "brain_tumor"],
            format_func=lambda x: x.replace("_", " ").title()
        )
        
        job_type = st.radio(
            "Benchmark Type",
            ["quick", "advanced"],
            format_func=lambda x: f"⚡ {x.title()} (Free)" if x == "quick" else f"🚀 {x.title()} (1 Credit)"
        )
    
    with col2:
        st.info("""
        **Benchmark Types:**
        - **Quick**: Free, uses cached results (3 seconds)
        - **Advanced**: 1 credit, simulated training with detailed analysis (8 seconds)
        """)
        
        # Show user credits
        st.metric("Your Credits", user["credits"])
    
    # Run button
    if st.button("🚀 Start Benchmark", type="primary"):
        # Check credits for advanced jobs
        if job_type == "advanced" and user["credits"] < 1:
            st.error("❌ Not enough credits! Please buy more credits.")
            return
        
        # Create job record
        job_id = db.create_job(
            user_email=user["email"],
            job_type=job_type,
            parameters={"disease": disease}
        )
        
        if job_id:
            # Deduct credit for advanced jobs
            if job_type == "advanced":
                new_credits = db.update_credits(user["email"], -1)
                st.session_state["user"]["credits"] = new_credits
            
            # Show progress
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # For quick jobs, process immediately
            if job_type == "quick":
                for i in range(100):
                    progress_bar.progress(i + 1)
                    status_text.text(f"Processing... {i+1}%")
                    time.sleep(0.03)  # Quick simulation
                
                # Get results
                results = simulator.simulate_benchmark(disease, "quick")
                db.update_job(job_id, "completed", results)
                
                progress_bar.empty()
                status_text.empty()
                
                # Show results
                show_results(results, job_id)
            
            else:
                # For advanced jobs, trigger background processing
                st.info("⏳ Job queued for background processing. Check 'My Results' tab in a few seconds.")
                
                # Trigger background worker (simulated for demo)
                # In production, you would call QStash here
                try:
                    # Simulate async call
                    import threading
                    def process_async():
                        time.sleep(8)  # Simulate processing time
                        results = simulator.simulate_benchmark(disease, "advanced")
                        db.update_job(job_id, "completed", results)
                    
                    thread = threading.Thread(target=process_async)
                    thread.start()
                    
                except Exception as e:
                    st.error(f"Error queueing job: {e}")

def show_results(results: dict, job_id: int):
    """Display benchmark results beautifully"""
    st.success("✅ Benchmark completed!")
    
    # Show recommendation
    st.markdown(f"### 🎯 Recommendation")
    st.info(results["recommendation"])
    
    # Create visualizations
    fig1, fig2 = simulator.create_results_visualization(results)
    
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig1, use_container_width=True)
    with col2:
        st.plotly_chart(fig2, use_container_width=True)
    
    # Show data table
    st.markdown("### 📋 Detailed Results")
    import pandas as pd
    df = pd.DataFrame(results["models"])
    st.dataframe(df, use_container_width=True)
    
    # Job info
    with st.expander("📝 Job Details"):
        st.json({
            "job_id": job_id,
            "disease": results["disease"],
            "job_type": results["job_type"],
            "processing_time": results["processing_time"],
            "timestamp": results["timestamp"]
        })

def results_tab(user_email: str):
    """Tab showing user's job history"""
    st.subheader("📊 My Benchmark History")
    
    # Fetch jobs
    jobs = db.get_user_jobs(user_email, limit=20)
    
    if not jobs:
        st.info("No benchmarks run yet. Go to 'Run Benchmark' to get started!")
        return
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        filter_status = st.selectbox("Filter by status", ["all", "completed", "pending", "failed"])
    with col2:
        if st.button("🔄 Refresh Jobs"):
            st.rerun()
    
    # Filter jobs
    if filter_status != "all":
        jobs = [j for j in jobs if j["status"] == filter_status]
    
    # Display jobs
    for job in jobs:
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                disease = job["parameters"].get("disease", "unknown") if job["parameters"] else "unknown"
                st.markdown(f"**{disease.replace('_', ' ').title()}**")
                st.caption(f"Job #{job['id']} • {job['job_type'].title()}")
            
            with col2:
                status_color = {
                    "completed": "✅",
                    "processing": "🔄",
                    "pending": "⏳",
                    "failed": "❌"
                }
                st.markdown(f"{status_color.get(job['status'], '❓')} {job['status']}")
            
            with col3:
                if job.get("created_at"):
                    date_str = job["created_at"][:19].replace("T", " ")
                    st.caption(date_str)
            
            with col4:
                if job["status"] == "completed" and job.get("results"):
                    if st.button("View", key=f"view_{job['id']}"):
                        show_results(job["results"], job["id"])
            
            st.divider()

def buy_credits_tab(user_email: str, user: dict):
    """Tab for purchasing credits"""
    st.subheader("💰 Buy More Credits")
    
    st.info("""
    💡 **This is a DEMO using Stripe Test Mode**
    - Use test card: `4242 4242 4242 4242`
    - Any future date, any CVC
    - No real money charged
    """)
    
    # Credit packages
    packages = stripe_handler.get_credit_packages()
    
    cols = st.columns(len(packages))
    for idx, (col, package) in enumerate(zip(cols, packages)):
        with col:
            st.markdown(f"### {package['credits']} Credits")
            st.markdown(f"**${package['price']/100:.2f}**")
            
            if st.button(f"Buy {package['credits']} Credits", key=f"buy_{idx}"):
                # Create checkout session
                checkout_url = stripe_handler.create_checkout_session(
                    user_email=user_email,
                    credits=package["credits"],
                    price=package["price"]
                )
                
                if checkout_url:
                    st.markdown(f"[Complete Payment]({checkout_url})")
                    st.info("After payment, refresh this page to see updated credits")
                else:
                    st.error("Error creating payment session")
    
    # Current balance
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Current Credits", user["credits"])
    with col2:
        if st.button("🔄 Update Balance"):
            # Refresh user data
            updated_user = db.get_user(user_email)
            if updated_user:
                st.session_state["user"] = updated_user
            st.rerun()

def about_tab():
    """Information about the platform"""
    st.subheader("ℹ️ About ArchNet SaaS")
    
    st.markdown("""
    ## 🚀 What is ArchNet?
    
    ArchNet is a **Software-as-a-Service (SaaS) platform** for benchmarking AI models in medical imaging.
    
    ### ✨ Features:
    1. **Multi-Model Benchmarking**: Compare VGG16, ResNet, EfficientNet, etc.
    2. **Medical Datasets**: Pneumonia X-rays, Skin Cancer, COVID-19, Brain Tumor MRI
    3. **Smart Recommendations**: Get AI-powered model suggestions
    4. **Scalable Architecture**: Built for production deployment
    
    ### 🛠️ Technical Stack:
    - **Frontend**: Streamlit (Python)
    - **Backend**: Supabase (PostgreSQL)
    - **Job Queue**: QStash (Upstash)
    - **Payments**: Stripe (Test Mode)
    - **Deployment**: Streamlit Community Cloud
    
    ### 📊 This Demo Shows:
    - User authentication & credit system
    - Background job processing
    - Payment integration
    - Results visualization
    - Full SaaS workflow
    
    ### 🔒 Important Notes:
    - This is a **DEMO ONLY** for educational purposes
    - No real medical data is processed
    - No real payments are processed
    - Results are simulated from pre-computed data
    """)

def main():
    """Main application logic"""
    
    # Check if user is logged in
    if "user_email" not in st.session_state:
        # Show login page
        st.markdown("<h1 class='main-header'>🤖 ArchNet SaaS Platform</h1>", unsafe_allow_html=True)
        st.markdown("### Welcome to the ArchNet Demo")
        
        col1, col2 = st.columns(2)
        with col1:
            st.image("https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=400", 
                    caption="Medical AI Benchmarking")
        with col2:
            st.write("""
            ### Get Started:
            1. Enter your email in the sidebar
            2. Get 3 free credits
            3. Run benchmarks
            4. View results
            
            **Features:**
            - Quick (free) and Advanced (1 credit) benchmarks
            - Beautiful visualizations
            - Job history tracking
            - Payment simulation
            """)
        
        # Show login in sidebar
        login_section()
        
    else:
        # User is logged in - show dashboard
        login_section()  # Still show login in sidebar
        user_dashboard()

if __name__ == "__main__":
    main()