#!/usr/bin/env python3
"""
Quick test script to validate the Process Simulation Studio backend.
Run this after starting the backend to ensure all endpoints work correctly.
"""

import requests
import json
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint."""
    print("🏥 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_parse_prompt():
    """Test the prompt parsing endpoint."""
    print("🤖 Testing prompt parsing...")
    test_prompts = [
        "Add payment validation after invoice creation",
        "Remove order approval step",
        "Increase invoice creation time to 2 hours"
    ]
    
    success = True
    for prompt in test_prompts:
        try:
            response = requests.post(
                f"{BASE_URL}/api/parse-prompt",
                json={"prompt": prompt},
                timeout=10
            )
            if response.status_code == 200:
                result = response.json()
                print(f"  ✅ '{prompt}' -> {result.get('action', 'unknown')}")
            else:
                print(f"  ❌ Failed to parse: '{prompt}' ({response.status_code})")
                success = False
        except requests.RequestException as e:
            print(f"  ❌ Error parsing '{prompt}': {e}")
            success = False
    
    return success

def test_generate_log():
    """Test event log generation."""
    print("📊 Testing event log generation...")
    
    sample_graph = {
        "activities": ["Order Received", "Order Approved", "Invoice Created", "Payment Received"],
        "edges": [
            {"id": "e1", "from": "Order Received", "to": "Order Approved"},
            {"id": "e2", "from": "Order Approved", "to": "Invoice Created"},
            {"id": "e3", "from": "Invoice Created", "to": "Payment Received"}
        ],
        "kpis": {
            "Order Received": {"avg_time": 1.0, "cost": 5.0},
            "Order Approved": {"avg_time": 0.5, "cost": 3.0},
            "Invoice Created": {"avg_time": 1.0, "cost": 2.0},
            "Payment Received": {"avg_time": 0.3, "cost": 1.0}
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/generate-log",
            json={"graph": sample_graph},
            timeout=15
        )
        if response.status_code == 200:
            result = response.json()
            event_count = len(result.get("event_log", []))
            case_count = result.get("metadata", {}).get("total_cases", 0)
            print(f"  ✅ Generated {event_count} events for {case_count} cases")
            return True
        else:
            print(f"  ❌ Failed to generate log ({response.status_code}): {response.text}")
            return False
    except requests.RequestException as e:
        print(f"  ❌ Error generating log: {e}")
        return False

def test_simulate():
    """Test process simulation."""
    print("🎯 Testing simulation...")
    
    # First generate some event log data
    sample_graph = {
        "activities": ["Order Received", "Order Approved", "Invoice Created"],
        "edges": [
            {"id": "e1", "from": "Order Received", "to": "Order Approved"},
            {"id": "e2", "from": "Order Approved", "to": "Invoice Created"}
        ],
        "kpis": {
            "Order Received": {"avg_time": 1.0, "cost": 5.0},
            "Order Approved": {"avg_time": 0.5, "cost": 3.0},
            "Invoice Created": {"avg_time": 1.0, "cost": 2.0}
        }
    }
    
    # Generate sample event log
    try:
        log_response = requests.post(
            f"{BASE_URL}/api/generate-log",
            json={"graph": sample_graph},
            timeout=15
        )
        if log_response.status_code != 200:
            print("  ❌ Failed to generate sample data for simulation")
            return False
        
        event_log = log_response.json()["event_log"]
        
        # Run simulation
        sim_response = requests.post(
            f"{BASE_URL}/api/simulate",
            json={"event_log": event_log, "graph": sample_graph},
            timeout=20
        )
        
        if sim_response.status_code == 200:
            result = sim_response.json()
            print(f"  ✅ Simulation completed:")
            print(f"    Cycle time change: {result.get('cycle_time_change', 'N/A')}")
            print(f"    Cost change: {result.get('cost_change', 'N/A')}")
            print(f"    Confidence: {result.get('confidence', 'N/A')}")
            return True
        else:
            print(f"  ❌ Simulation failed ({sim_response.status_code}): {sim_response.text}")
            return False
            
    except requests.RequestException as e:
        print(f"  ❌ Error running simulation: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Process Simulation Studio Backend Tests")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_check),
        ("Prompt Parsing", test_parse_prompt),
        ("Event Log Generation", test_generate_log),
        ("Process Simulation", test_simulate)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        if test_func():
            passed += 1
        print("-" * 30)
    
    print(f"\n🏁 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The backend is ready to use.")
        return 0
    else:
        print("❌ Some tests failed. Check the backend setup and try again.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
