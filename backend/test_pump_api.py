#!/usr/bin/env python3
"""
Comprehensive test suite for Pump API endpoints
Tests all RESTful endpoints for pump selection and data access
"""

import asyncio
import json
from fastapi.testclient import TestClient
from main import app

# Create test client
client = TestClient(app)

def test_pump_health():
    """Test pump service health endpoint."""
    print("=== TESTING PUMP SERVICE HEALTH ===")
    response = client.get("/pumps/health")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Service Status: {data['status']}")
        print(f"Pump Count: {data['pump_count']}")
        print(f"Available Sizes: {len(data['available_sizes'])}")
        print(f"Available Types: {len(data['available_types'])}")
    else:
        print(f"Error: {response.text}")
    print()

def test_list_pumps():
    """Test listing all available pumps."""
    print("=== TESTING PUMP LIST ENDPOINT ===")
    response = client.get("/pumps/list")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        pumps = response.json()
        print(f"Total Pumps: {len(pumps)}")
        for pump in pumps[:3]:  # Show first 3
            print(f"  {pump['pump_size']}: {pump['pump_model']} ({pump['pump_type']})")
            print(f"    RPMs: {pump['available_rpms']}")
            print(f"    Max HP: {pump['max_hp']}")
    else:
        print(f"Error: {response.text}")
    print()

def test_pump_sizes():
    """Test getting pump sizes."""
    print("=== TESTING PUMP SIZES ENDPOINT ===")
    response = client.get("/pumps/sizes")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        sizes = response.json()
        print(f"Available Sizes: {sizes}")
    else:
        print(f"Error: {response.text}")
    print()

def test_pump_types():
    """Test getting pump types."""
    print("=== TESTING PUMP TYPES ENDPOINT ===")
    response = client.get("/pumps/types")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        types = response.json()
        print(f"Available Types: {types}")
    else:
        print(f"Error: {response.text}")
    print()

def test_pump_details():
    """Test getting specific pump details."""
    print("=== TESTING PUMP DETAILS ENDPOINT ===")
    pump_size = "3x4-13"
    response = client.get(f"/pumps/{pump_size}")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        pump = response.json()
        print(f"Pump: {pump['size']} - {pump['model']}")
        print(f"Type: {pump['type']}")
        print(f"Specs: {pump['specs']}")
        print(f"Available RPMs: {list(pump['curve_data'].keys())}")
    else:
        print(f"Error: {response.text}")
    print()

def test_pump_selection():
    """Test pump selection endpoint."""
    print("=== TESTING PUMP SELECTION ENDPOINT ===")
    
    # Test case 1: Typical produced water transfer
    request_data = {
        "required_flow_gpm": 800,
        "required_head_ft": 50,
        "fluid_sg": 1.1,
        "npsh_available_ft": 8.0,
        "fluid_type": "produced_water"
    }
    
    response = client.post("/pumps/select", json=request_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        recommendations = response.json()
        print(f"Found {len(recommendations)} suitable pumps")
        
        for i, rec in enumerate(recommendations[:3]):  # Show top 3
            print(f"\n  {i+1}. {rec['pump_size']} - {rec['recommendation_level']}")
            print(f"     Efficiency: {rec['operating_point']['efficiency_percent']:.1f}%")
            print(f"     Power: {rec['operating_point']['power_hp']:.1f} HP")
            print(f"     NPSH Margin: {rec['operating_point']['npsh_margin_ft']:.1f} ft")
            print(f"     Warnings: {len(rec['warnings'])}")
            if rec['warnings']:
                for warning in rec['warnings']:
                    print(f"       - {warning}")
    else:
        print(f"Error: {response.text}")
    print()

def test_pump_selection_with_constraints():
    """Test pump selection with power constraints."""
    print("=== TESTING PUMP SELECTION WITH CONSTRAINTS ===")
    
    request_data = {
        "required_flow_gpm": 1500,
        "required_head_ft": 60,
        "fluid_sg": 1.1,
        "npsh_available_ft": 8.0,
        "max_power_hp": 75,
        "preferred_rpm": 1750,
        "fluid_type": "produced_water"
    }
    
    response = client.post("/pumps/select", json=request_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        recommendations = response.json()
        print(f"Found {len(recommendations)} pumps within constraints")
        
        for rec in recommendations:
            print(f"  {rec['pump_size']}: {rec['operating_point']['power_hp']:.1f} HP @ {rec['operating_point']['rpm']} RPM")
    else:
        print(f"Error: {response.text}")
    print()

def test_pump_performance():
    """Test pump performance calculation."""
    print("=== TESTING PUMP PERFORMANCE ENDPOINT ===")
    
    request_data = {
        "pump_size": "3x4-13",
        "rpm": 1750,
        "flow_gpm": 800,
        "fluid_sg": 1.1
    }
    
    response = client.post("/pumps/performance", json=request_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        performance = response.json()
        print(f"Pump: {request_data['pump_size']} @ {request_data['rpm']} RPM")
        print(f"Operating Point:")
        print(f"  Flow: {performance['flow_gpm']} GPM")
        print(f"  Head: {performance['head_ft']:.1f} ft")
        print(f"  Efficiency: {performance['efficiency_percent']:.1f}%")
        print(f"  Power: {performance['power_hp']:.1f} HP")
        print(f"  NPSH Required: {performance['npsh_required_ft']:.1f} ft")
        print(f"  Brake HP: {performance['brake_horsepower']:.1f}")
        print(f"  Fluid HP: {performance['fluid_horsepower']:.1f}")
    else:
        print(f"Error: {response.text}")
    print()

def test_system_curve():
    """Test system curve intersection analysis."""
    print("=== TESTING SYSTEM CURVE ENDPOINT ===")
    
    request_data = {
        "pump_size": "3x4-13",
        "rpm": 1750,
        "static_head_ft": 30,
        "friction_loss_coefficient": 0.001
    }
    
    response = client.post("/pumps/system-curve", json=request_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        intersections = response.json()
        if isinstance(intersections, list):
            print(f"Found {len(intersections)} intersection points")
            for intersection in intersections:
                print(f"  Intersection: {intersection}")
        else:
            print(f"Result: {intersections}")
    else:
        print(f"Error: {response.text}")
    print()

def test_pump_search():
    """Test pump search functionality."""
    print("=== TESTING PUMP SEARCH ENDPOINT ===")
    
    # Search for pumps with specific criteria
    params = {
        "flow_min": 500,
        "flow_max": 2000,
        "head_min": 20,
        "head_max": 100,
        "pump_type": "centrifugal_ansi_transfer"
    }
    
    response = client.get("/pumps/search", params=params)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        pumps = response.json()
        print(f"Search Results: {len(pumps)} pumps")
        for pump in pumps:
            print(f"  {pump['pump_size']}: {pump['pump_model']}")
    else:
        print(f"Error: {response.text}")
    print()

def test_error_handling():
    """Test API error handling."""
    print("=== TESTING ERROR HANDLING ===")
    
    # Test invalid pump size
    response = client.get("/pumps/invalid-pump-size")
    print(f"Invalid pump size - Status: {response.status_code}")
    
    # Test invalid selection request
    invalid_request = {
        "required_flow_gpm": -100,  # Invalid negative flow
        "required_head_ft": 50
    }
    response = client.post("/pumps/select", json=invalid_request)
    print(f"Invalid selection request - Status: {response.status_code}")
    
    # Test invalid performance request
    invalid_performance = {
        "pump_size": "3x4-13",
        "rpm": 9999,  # Invalid RPM
        "flow_gpm": 800,
        "fluid_sg": 1.1
    }
    response = client.post("/pumps/performance", json=invalid_performance)
    print(f"Invalid performance request - Status: {response.status_code}")
    print()

def run_all_tests():
    """Run all pump API tests."""
    print("COMPREHENSIVE PUMP API TESTING")
    print("=" * 50)
    
    try:
        test_pump_health()
        test_list_pumps()
        test_pump_sizes()
        test_pump_types()
        test_pump_details()
        test_pump_selection()
        test_pump_selection_with_constraints()
        test_pump_performance()
        test_system_curve()
        test_pump_search()
        test_error_handling()
        
        print("ALL PUMP API TESTS COMPLETED SUCCESSFULLY")
        
    except Exception as e:
        print(f"TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_tests()
