#!/usr/bin/env python3
"""
Test script to analyze 4x6-13 pump data loading and context generation
This script helps diagnose why PatchAI might not be responding to pump queries
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.data.pumps.data_loader import PumpDataLoader
from backend.services.pump_context_service import PumpContextService

def main():
    print("=== 4x6-13 PUMP DATA ANALYSIS ===\n")
    
    # Test 1: Pump Data Loading
    print("1. TESTING PUMP DATA LOADING")
    print("-" * 40)
    try:
        loader = PumpDataLoader()
        print(f"[OK] PumpDataLoader initialized successfully")
        print(f"   Total pumps loaded: {len(loader.pumps)}")
        print(f"   Available pump sizes: {[pump['size'] for pump in loader.pumps]}")
        
        # Test 4x6-13 pump specifically
        pump_4x6 = loader.get_pump_by_size('4x6-13')
        if pump_4x6:
            print(f"[OK] 4x6-13 pump found successfully")
            print(f"   Model: {pump_4x6['model']}")
            print(f"   Type: {pump_4x6['type']}")
            print(f"   Max HP: {pump_4x6['specs']['max_hp']}")
            print(f"   RPM options: {pump_4x6['specs']['rpm_options']}")
            print(f"   Has curve data: {'curve_data' in pump_4x6}")
            
            # Check curve data structure
            if 'curve_data' in pump_4x6:
                curve_data = pump_4x6['curve_data']
                rpm_keys = list(curve_data.keys())
                print(f"   Available RPM curves: {rpm_keys}")
                
                # Check first RPM curve structure
                if rpm_keys:
                    first_rpm = rpm_keys[0]
                    first_curve = curve_data[first_rpm]
                    print(f"   Sample curve ({first_rpm}) contains:")
                    for key in first_curve.keys():
                        if isinstance(first_curve[key], list) and first_curve[key]:
                            print(f"     - {key}: {len(first_curve[key])} data points")
        else:
            print("[ERROR] 4x6-13 pump NOT found in data")
            
    except Exception as e:
        print(f"[ERROR] Error loading pump data: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60 + "\n")
    
    # Test 2: Pump Context Service
    print("2. TESTING PUMP CONTEXT SERVICE")
    print("-" * 40)
    try:
        context_service = PumpContextService()
        print("[OK] PumpContextService initialized successfully")
        
        # Test pump query detection
        test_queries = [
            "What is the flowrate vs pressure table for the 4x6-13 pump?",
            "Show me pump curve data for 4x6-13",
            "I need performance data for the 4x6-13 transfer pump",
            "Can you provide the head vs flow curve for 4x6-13 at 1750 RPM?",
            "What's the efficiency of the 4x6-13 pump at 500 GPM?"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\nTest Query {i}: \"{query}\"")
            
            # Test detection
            is_pump_query = context_service.detect_pump_query(query)
            print(f"   Pump query detected: {is_pump_query}")
            
            if is_pump_query:
                # Test parameter extraction
                params = context_service.extract_pump_parameters(query)
                print(f"   Extracted parameters: {params}")
                
                # Test context generation
                context = context_service.generate_pump_context(query)
                if context:
                    print(f"   [OK] Context generated: {len(context)} characters")
                    
                    # Show context preview
                    lines = context.split('\n')
                    preview_lines = lines[:10]  # First 10 lines
                    print("   Context preview:")
                    for line in preview_lines:
                        print(f"     {line}")
                    if len(lines) > 10:
                        print(f"     ... ({len(lines) - 10} more lines)")
                else:
                    print("   [ERROR] No context generated")
            else:
                print("   [WARN] Query not detected as pump-related")
                
    except Exception as e:
        print(f"[ERROR] Error testing pump context service: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60 + "\n")
    
    # Test 3: Direct 4x6-13 Context Generation
    print("3. TESTING DIRECT 4x6-13 CONTEXT GENERATION")
    print("-" * 50)
    try:
        context_service = PumpContextService()
        
        # Test with specific 4x6-13 query
        specific_query = "What is the flowrate vs pressure table for the 4x6-13 pump?"
        print(f"Query: {specific_query}")
        
        # Generate context
        full_context = context_service.generate_pump_context(specific_query)
        
        if full_context:
            print(f"[OK] Full context generated successfully")
            print(f"   Total length: {len(full_context)} characters")
            
            # Check if 4x6-13 data is included
            if "4x6-13" in full_context:
                print("[OK] 4x6-13 pump data found in context")
            else:
                print("[ERROR] 4x6-13 pump data NOT found in context")
            
            # Check for performance tables
            if "Flow (GPM)" in full_context and "Head (ft)" in full_context:
                print("[OK] Performance tables found in context")
            else:
                print("[ERROR] Performance tables NOT found in context")
                
            # Save full context to file for inspection
            with open('4x6_pump_context_debug.txt', 'w') as f:
                f.write(full_context)
            print("[OK] Full context saved to '4x6_pump_context_debug.txt'")
            
        else:
            print("[ERROR] No context generated for 4x6-13 query")
            
    except Exception as e:
        print(f"[ERROR] Error in direct context generation: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("ANALYSIS COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()
