import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import json

class Database:
    def __init__(self):
        self.url = st.secrets["supabase_url"]
        self.key = st.secrets["supabase_key"]
        self.client: Client = create_client(self.url, self.key)
    
    def get_user(self, email: str):
        """Get user by email"""
        try:
            response = self.client.table("users").select("*").eq("email", email).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            st.error(f"Database error: {e}")
            return None
    
    def create_user(self, email: str):
        """Create new user with 3 free credits"""
        try:
            user_data = {
                "email": email,
                "credits": 3,
                "tier": "free",
                "created_at": datetime.utcnow().isoformat()
            }
            response = self.client.table("users").insert(user_data).execute()
            return response.data[0]
        except Exception as e:
            st.error(f"Error creating user: {e}")
            return None
    
    def update_credits(self, email: str, credit_change: int):
        """Add or subtract credits"""
        try:
            user = self.get_user(email)
            new_credits = user["credits"] + credit_change
            response = self.client.table("users").update(
                {"credits": new_credits}
            ).eq("email", email).execute()
            return new_credits
        except Exception as e:
            st.error(f"Error updating credits: {e}")
            return None
    
    def create_job(self, user_email: str, job_type: str, parameters: dict):
        """Create a new job record"""
        try:
            job_data = {
                "user_email": user_email,
                "job_type": job_type,
                "status": "pending",
                "parameters": parameters,
                "created_at": datetime.utcnow().isoformat()
            }
            response = self.client.table("jobs").insert(job_data).execute()
            return response.data[0]["id"]
        except Exception as e:
            st.error(f"Error creating job: {e}")
            return None
    
    def update_job(self, job_id: int, status: str, results: dict = None):
        """Update job status and results"""
        try:
            update_data = {"status": status}
            if results:
                update_data["results"] = results
                update_data["completed_at"] = datetime.utcnow().isoformat()
            
            response = self.client.table("jobs").update(
                update_data
            ).eq("id", job_id).execute()
            return True
        except Exception as e:
            print(f"Error updating job: {e}")
            return False
    
    def get_user_jobs(self, user_email: str, limit: int = 10):
        """Get user's job history"""
        try:
            response = self.client.table("jobs").select(
                "*"
            ).eq("user_email", user_email).order(
                "created_at", desc=True
            ).limit(limit).execute()
            return response.data
        except Exception as e:
            st.error(f"Error fetching jobs: {e}")
            return []
