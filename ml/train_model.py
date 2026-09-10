"""
Machine Learning Model Training Pipeline
Algorithm: Isolation Forest (Scikit-Learn)
Target: Unsupervised Anomaly Detection on Multi-Sensor Telemetry
Features: Temperature (°C), Humidity (%), Pressure (hPa)
"""

import os
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib

def generate_synthetic_sensor_dataset(n_normal=5000, n_anomalies=250, random_seed=42):
    """
    Generate realistic multi-modal industrial sensor telemetry distributions.
    Normal Operational Ranges:
      - Temperature: 20.0 to 40.0 °C (Mean ~ 29.5, Std ~ 4.2)
      - Humidity:    30.0 to 80.0 %  (Mean ~ 55.0, Std ~ 9.5)
      - Pressure:    990.0 to 1030.0 hPa (Mean ~ 1013.25, Std ~ 6.5)
    """
    np.random.seed(random_seed)
    
    # Generate Normal Operational Stream
    normal_temp = np.random.normal(loc=29.5, scale=4.0, size=n_normal)
    normal_temp = np.clip(normal_temp, 20.0, 40.0)
    
    normal_hum = np.random.normal(loc=55.0, scale=9.0, size=n_normal)
    normal_hum = np.clip(normal_hum, 30.0, 80.0)
    
    normal_press = np.random.normal(loc=1013.25, scale=6.0, size=n_normal)
    normal_press = np.clip(normal_press, 990.0, 1030.0)
    
    normal_df = pd.DataFrame({
        "temperature": normal_temp,
        "humidity": normal_hum,
        "pressure": normal_press,
        "label": 1  # Inlier / Normal
    })
    
    # Generate Anomaly Signatures
    # Pattern A: Extreme Boiler overheating (80 - 105 °C)
    # Pattern B: Severe humidity desiccation (3 - 15 %) or condensation flooding (90 - 99 %)
    # Pattern C: Vacuum depressurization (780 - 910 hPa) or pressure surge (1060 - 1120 hPa)
    anom_temps = []
    anom_hums = []
    anom_presss = []
    
    for _ in range(n_anomalies):
        anomaly_type = np.random.choice(["temp_spike", "temp_freeze", "hum_dry", "hum_high", "press_drop", "compound"])
        if anomaly_type == "temp_spike":
            t = np.random.uniform(75.0, 105.0)
            h = np.random.uniform(30.0, 70.0)
            p = np.random.uniform(995.0, 1025.0)
        elif anomaly_type == "temp_freeze":
            t = np.random.uniform(-10.0, 10.0)
            h = np.random.uniform(20.0, 50.0)
            p = np.random.uniform(995.0, 1025.0)
        elif anomaly_type == "hum_dry":
            t = np.random.uniform(25.0, 38.0)
            h = np.random.uniform(4.0, 15.0)
            p = np.random.uniform(1000.0, 1025.0)
        elif anomaly_type == "hum_high":
            t = np.random.uniform(22.0, 35.0)
            h = np.random.uniform(92.0, 99.5)
            p = np.random.uniform(995.0, 1020.0)
        elif anomaly_type == "press_drop":
            t = np.random.uniform(24.0, 36.0)
            h = np.random.uniform(40.0, 60.0)
            p = np.random.uniform(780.0, 910.0)
        else:
            # Compound crisis (Boiler critical failure: extreme temp + pressure drop)
            t = np.random.uniform(85.0, 110.0)
            h = np.random.uniform(10.0, 25.0)
            p = np.random.uniform(820.0, 920.0)
            
        anom_temps.append(t)
        anom_hums.append(h)
        anom_presss.append(p)
        
    anom_df = pd.DataFrame({
        "temperature": anom_temps,
        "humidity": anom_hums,
        "pressure": anom_presss,
        "label": -1  # Outlier / Anomaly
    })
    
    full_dataset = pd.concat([normal_df, anom_df], ignore_index=True)
    # Shuffle
    full_dataset = full_dataset.sample(frac=1.0, random_state=random_seed).reset_index(drop=True)
    return full_dataset

def train_and_export_model(output_path="backend/ml/isolation_forest_model.joblib"):
    print("[*] Generating industrial training dataset...")
    df = generate_synthetic_sensor_dataset(n_normal=6000, n_anomalies=300)
    features = ["temperature", "humidity", "pressure"]
    X = df[features].values
    
    print(f"[*] Training Isolation Forest model on {len(X)} samples with features {features}...")
    # Scikit-Learn IsolationForest
    # Contamination set to 0.05 as specified in requirements
    model = IsolationForest(
        n_estimators=150,
        max_samples="auto",
        contamination=0.05,
        random_state=42,
        bootstrap=False,
        n_jobs=-1
    )
    
    model.fit(X)
    
    # Evaluate baseline accuracy on dataset
    preds = model.predict(X)
    # IsolationForest: 1 is normal, -1 is anomaly
    anomalies_detected = np.sum(preds == -1)
    normals_detected = np.sum(preds == 1)
    print(f"[+] Training completed. Model detected {anomalies_detected} anomalies ({anomalies_detected/len(X):.2%}) and {normals_detected} inliers.")
    
    # Benchmark specific test cases
    test_cases = [
        {"name": "Normal Plant Floor", "features": [28.5, 52.4, 1012.5], "expected": "NORMAL"},
        {"name": "Boiler Overheat", "features": [92.0, 48.0, 1010.0], "expected": "ANOMALY"},
        {"name": "Dry Storage Dehydration", "features": [31.0, 8.5, 1015.0], "expected": "ANOMALY"},
        {"name": "Vacuum Depressurization", "features": [26.0, 50.0, 840.0], "expected": "ANOMALY"},
    ]
    
    print("\n--- Validation Benchmarks ---")
    for case in test_cases:
        feat = np.array([case["features"]])
        pred = model.predict(feat)[0]
        score = model.score_samples(feat)[0]
        status = "NORMAL" if pred == 1 else "ANOMALY"
        match = "[PASS]" if status == case["expected"] else "[FAIL]"
        print(f"Test: {case['name']:<25} Features: {case['features']} -> Result: {status:<8} Score: {score:+.4f} {match}")
        
    # Save the model
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    joblib.dump(model, output_path)
    print(f"\n[SUCCESS] Trained Isolation Forest model successfully serialized to '{output_path}'")
    return model

if __name__ == "__main__":
    train_and_export_model()
