"""
Test script for pump context service integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.pump_context_service import PumpContextService

def test_pump_context_service():
    """Test pump context service functionality"""
    print("TESTING PUMP CONTEXT SERVICE")
    print("=" * 50)
    
    # Initialize service
    pump_context_service = PumpContextService()
    
    # Test 1: Pump query detection
    print("\n=== TEST 1: Pump Query Detection ===")
    test_messages = [
        "I need a pump for 800 GPM at 50 feet",
        "What's the weather like today?",
        "Can you recommend a centrifugal pump for produced water?",
        "How do I calculate NPSH for my application?",
        "Tell me about oil and gas operations"
    ]
    
    for msg in test_messages:
        is_pump_query = pump_context_service.detect_pump_query(msg)
        print(f"'{msg[:40]}...' -> Pump query: {is_pump_query}")
    
    # Test 2: Parameter extraction
    print("\n=== TEST 2: Parameter Extraction ===")
    test_msg = "I need a 3x4-13 pump for 800 GPM at 50 feet with 1750 RPM for produced water"
    params = pump_context_service.extract_pump_parameters(test_msg)
    print(f"Message: {test_msg}")
    print(f"Extracted parameters: {params}")
    
    # Test 3: Pump inventory context
    print("\n=== TEST 3: Pump Inventory Context ===")
    inventory_context = pump_context_service.get_pump_inventory_context()
    print(inventory_context[:500] + "..." if len(inventory_context) > 500 else inventory_context)
    
    # Test 4: Pump recommendations context
    print("\n=== TEST 4: Pump Recommendations Context ===")
    recommendations_context = pump_context_service.get_pump_recommendations_context(800, 50)
    print(recommendations_context)
    
    # Test 5: Pump performance context
    print("\n=== TEST 5: Pump Performance Context ===")
    performance_context = pump_context_service.get_pump_performance_context("3x4-13", 800)
    print(performance_context)
    
    # Test 6: Full context generation
    print("\n=== TEST 6: Full Context Generation ===")
    full_context = pump_context_service.generate_pump_context("I need a pump for 800 GPM at 50 feet")
    if full_context:
        print("Generated context length:", len(full_context))
        print("Context preview:", full_context[:300] + "..." if len(full_context) > 300 else full_context)
    else:
        print("No context generated")
    
    print("\n" + "=" * 50)
    print("PUMP CONTEXT SERVICE TESTING COMPLETE")

if __name__ == "__main__":
    test_pump_context_service()
