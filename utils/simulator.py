import streamlit as st
import json
import time
import random
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import os

class BenchmarkSimulator:
    def __init__(self):
        # Load pre-computed results
        current_dir = os.path.dirname(__file__)
        results_path = os.path.join(current_dir, "..", "static", "sample_results.json")
        with open(results_path, 'r') as f:
            self.sample_data = json.load(f)
    
    def simulate_benchmark(self, disease_type: str, job_type: str = "quick"):
        """
        Simulate benchmarking process
        Returns fake results based on sample data
        """
        # Simulate processing time
        if job_type == "quick":
            time.sleep(3)  # 3 seconds for quick
        else:
            time.sleep(8)  # 8 seconds for advanced
        
        if disease_type not in self.sample_data:
            disease_type = "pneumonia"
        
        data = self.sample_data[disease_type]
        
        # Add some randomness to make it feel "real"
        for model in data["models"]:
            model["accuracy"] = round(model["accuracy"] + random.uniform(-0.02, 0.02), 3)
            model["speed"] = model["speed"] + random.randint(-2, 2)
        
        return {
            "disease": disease_type,
            "models": data["models"],
            "recommendation": data["recommendation"],
            "timestamp": datetime.utcnow().isoformat(),
            "job_type": job_type,
            "processing_time": "3s" if job_type == "quick" else "8s"
        }
    
    def create_results_visualization(self, results: dict):
        """
        Create beautiful visualizations for benchmark results
        """
        models = results["models"]
        df = pd.DataFrame(models)
        
        # Create scatter plot: Accuracy vs Speed
        fig1 = px.scatter(
            df, x="speed", y="accuracy", 
            size="size", color="cost",
            hover_name="name",
            title=f"{results['disease'].title()} Benchmark: Accuracy vs Speed",
            labels={"speed": "Inference Time (ms)", "accuracy": "Accuracy"}
        )
        fig1.update_layout(height=400)
        
        # Create bar chart
        fig2 = go.Figure(data=[
            go.Bar(name='Accuracy', x=df['name'], y=df['accuracy'], yaxis='y1'),
            go.Bar(name='Speed', x=df['name'], y=df['speed'], yaxis='y2')
        ])
        fig2.update_layout(
            title="Model Performance Comparison",
            yaxis=dict(title="Accuracy", side="left"),
            yaxis2=dict(title="Speed (ms)", side="right", overlaying="y"),
            height=400
        )
        
        return fig1, fig2