#!/usr/bin/env python3
"""
DEBUG CALCULATION - Test the exact calculation logic
"""

from datetime import datetime, timedelta
import time

def test_calculation_logic():
    print("🔍 TESTING CALCULATION LOGIC")
    
    # Simulate the exact logic from the backend
    heure_arrivee_str = "2025-08-11T09:02:17.074967"
    print(f"heure_arrivee_attente: {heure_arrivee_str}")
    
    # Parse the timestamp (ISO format)
    arrivee_time = datetime.fromisoformat(heure_arrivee_str.replace("Z", "+00:00"))
    print(f"Parsed arrivee_time: {arrivee_time}")
    
    # Simulate waiting 10 seconds
    time.sleep(10)
    
    current_time = datetime.now()
    print(f"Current time: {current_time}")
    
    # Calculate duration exactly as backend does
    time_diff = current_time - arrivee_time
    total_seconds = time_diff.total_seconds()
    duree_calculee = int(total_seconds / 60)  # This is the key line
    calculated_duration = max(0, duree_calculee)
    
    print(f"Time difference: {time_diff}")
    print(f"Total seconds: {total_seconds}")
    print(f"duree_calculee (int(seconds/60)): {duree_calculee}")
    print(f"calculated_duration (max(0, duree_calculee)): {calculated_duration}")
    
    # Test different scenarios
    print("\n--- Testing different durations ---")
    test_scenarios = [
        {"seconds": 10, "description": "10 seconds"},
        {"seconds": 30, "description": "30 seconds"},
        {"seconds": 59, "description": "59 seconds"},
        {"seconds": 60, "description": "60 seconds"},
        {"seconds": 61, "description": "61 seconds"},
        {"seconds": 90, "description": "90 seconds"},
        {"seconds": 120, "description": "120 seconds"}
    ]
    
    base_time = datetime.now()
    
    for scenario in test_scenarios:
        future_time = base_time + datetime.timedelta(seconds=scenario["seconds"])
        time_diff = future_time - base_time
        total_seconds = time_diff.total_seconds()
        duree_calculee = int(total_seconds / 60)
        calculated_duration = max(0, duree_calculee)
        
        print(f"{scenario['description']}: {total_seconds}s → int({total_seconds}/60) = {duree_calculee} → max(0, {duree_calculee}) = {calculated_duration}")

if __name__ == "__main__":
    test_calculation_logic()