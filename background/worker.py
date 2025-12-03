# This will run on Vercel serverless function
from http.server import BaseHTTPRequestHandler
import json
import os
from utils.database import Database
from utils.simulator import BenchmarkSimulator

def handle_job(job_data: dict):
    """Process a background job"""
    print(f"Processing job: {job_data}")
    
    # Initialize components
    db = Database()
    simulator = BenchmarkSimulator()
    
    try:
        # Extract job data
        job_id = job_data.get("job_id")
        user_email = job_data.get("user_email")
        disease = job_data.get("disease", "pneumonia")
        job_type = job_data.get("job_type", "quick")
        
        # Update job status to processing
        db.update_job(job_id, "processing")
        
        # Run simulation
        results = simulator.simulate_benchmark(disease, job_type)
        
        # Update job with results
        db.update_job(job_id, "completed", results)
        
        # Log completion
        print(f"Job {job_id} completed successfully")
        return {"success": True, "job_id": job_id}
        
    except Exception as e:
        print(f"Error processing job: {e}")
        db.update_job(job_id, "failed")
        return {"success": False, "error": str(e)}

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle POST requests from QStash"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        job_data = json.loads(post_data)
        
        # Process the job
        result = handle_job(job_data)
        
        # Send response
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())