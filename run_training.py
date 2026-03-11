import os
import sys

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
