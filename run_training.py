# =============================================================
# STANDALONE TRAINING SCRIPT
# =============================================================
# Run this to train the ML model before starting the FastAPI server.
#
# Usage:
#   python run_training.py
#
# This will:
#   1. Load train.jsonl + test.jsonl (+ Cybersecurity_Dataset.csv if present)
#   2. Train a VotingClassifier (XGBoost + RandomForest)
#   3. Save model artifacts to models/
# =============================================================
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ml_model import train_model

if __name__ == "__main__":
    print("=" * 60)
    print(" CYBER INCIDENT PORTAL - Model Training")
    print("=" * 60)

    data_dir = os.path.dirname(os.path.abspath(__file__))
    accuracy = train_model(data_dir=data_dir)

    print("=" * 60)
    print(f" Training complete! Accuracy: {accuracy * 100:.2f}%")
    print(f"   Model saved to: models/")
    print(f"   Start the server with: python -m uvicorn app.main:app --reload")
    print("=" * 60)
