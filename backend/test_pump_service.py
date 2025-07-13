"""
Comprehensive test suite for pump selection service.
Tests all engineering logic, calculations, and recommendations.
"""
from services.pump_service import pump_selection_service, PumpRecommendationLevel

def test_pump_selection_comprehensive():
    """Test comprehensive pump selection scenarios."""
    print("=== COMPREHENSIVE PUMP SELECTION TESTS ===\n")
    
    # Test Case 1: Typical produced water transfer
    print("1. TYPICAL PRODUCED WATER TRANSFER (800 GPM @ 50 ft)")
    recs = pump_selection_service.find_suitable_pumps(
        required_flow_gpm=800,
        required_head_ft=50,
        fluid_sg=1.1,
        npsh_available_ft=8.0,
        fluid_type="produced_water"
    )
    
    print(f"   Found {len(recs)} suitable pumps")
    if recs:
        best = recs[0]
        print(f"   Best: {best.pump_size} - {best.recommendation_level.value}")
        print(f"   Efficiency: {best.operating_point.efficiency_percent:.1f}%")
        print(f"   Power: {best.operating_point.brake_horsepower:.1f} HP")
        print(f"   NPSH Margin: {best.operating_point.npsh_margin_ft:.1f} ft")
        print(f"   Warnings: {len(best.warnings)}")
    print()
    
    # Test Case 2: High flow, low head
    print("2. HIGH FLOW, LOW HEAD (2000 GPM @ 25 ft)")
    recs = pump_selection_service.find_suitable_pumps(
        required_flow_gpm=2000,
        required_head_ft=25,
        fluid_sg=1.0,
        npsh_available_ft=10.0
    )
    
    print(f"   Found {len(recs)} suitable pumps")
    if recs:
        best = recs[0]
        print(f"   Best: {best.pump_size} - {best.recommendation_level.value}")
        print(f"   Efficiency: {best.operating_point.efficiency_percent:.1f}%")
    print()
    
    # Test Case 3: Low NPSH scenario
    print("3. LOW NPSH SCENARIO (1000 GPM @ 80 ft, NPSH=4 ft)")
    recs = pump_selection_service.find_suitable_pumps(
        required_flow_gpm=1000,
        required_head_ft=80,
        fluid_sg=1.1,
        npsh_available_ft=4.0
    )
    
    print(f"   Found {len(recs)} suitable pumps")
    cavitation_risks = sum(1 for r in recs if r.operating_point.cavitation_risk)
    print(f"   Pumps with cavitation risk: {cavitation_risks}")
    if recs:
        for rec in recs[:2]:
            print(f"   {rec.pump_size}: NPSH margin {rec.operating_point.npsh_margin_ft:.1f} ft")
    print()
    
    # Test Case 4: Power constraint
    print("4. POWER CONSTRAINT (1500 GPM @ 60 ft, Max 75 HP)")
    recs = pump_selection_service.find_suitable_pumps(
        required_flow_gpm=1500,
        required_head_ft=60,
        fluid_sg=1.1,
        npsh_available_ft=8.0,
        max_power_hp=75
    )
    
    print(f"   Found {len(recs)} pumps within power limit")
    if recs:
        for rec in recs[:2]:
            print(f"   {rec.pump_size}: {rec.operating_point.brake_horsepower:.1f} HP")
    print()
    
    # Test Case 5: RPM preference
    print("5. RPM PREFERENCE (800 GPM @ 40 ft, 1750 RPM only)")
    recs = pump_selection_service.find_suitable_pumps(
        required_flow_gpm=800,
        required_head_ft=40,
        fluid_sg=1.1,
        npsh_available_ft=8.0,
        preferred_rpm=1750
    )
    
    print(f"   Found {len(recs)} pumps at 1750 RPM")
    if recs:
        for rec in recs[:2]:
            print(f"   {rec.pump_size}: {rec.operating_point.rpm} RPM")
    print()

def test_engineering_calculations():
    """Test specific engineering calculations."""
    print("=== ENGINEERING CALCULATIONS TESTS ===\n")
    
    # Test trim recommendations
    recs = pump_selection_service.find_suitable_pumps(600, 30, 1.1, 8.0)
    if recs:
        pump = recs[0]
        print(f"TRIM RECOMMENDATIONS for {pump.pump_size}:")
        for trim in pump.trim_recommendations[:2]:
            print(f"   Trim to {trim['trim_diameter_inches']}\" - Power reduction: {trim['power_reduction_percent']:.1f}%")
        print()
        
        print(f"VFD RECOMMENDATIONS for {pump.pump_size}:")
        for vfd in pump.vfd_recommendations[:2]:
            print(f"   {vfd['frequency_hz']} Hz - Power savings: {vfd['power_savings_percent']:.1f}%")
        print()

def test_system_curve():
    """Test system curve intersection."""
    print("=== SYSTEM CURVE INTERSECTION TEST ===\n")
    
    intersections = pump_selection_service.calculate_system_curve_intersection(
        pump_size='3x4-13',
        rpm=1750,
        static_head_ft=20,
        friction_loss_coefficient=0.001
    )
    
    print(f"System curve intersections for 3x4-13 @ 1750 RPM: {len(intersections)}")
    for point in intersections[:3]:
        print(f"   {point['flow_gpm']} GPM @ {point['head_ft']:.1f} ft - {point['efficiency_percent']:.1f}% eff")
    print()

if __name__ == "__main__":
    test_pump_selection_comprehensive()
    test_engineering_calculations()
    test_system_curve()
    print("=== ALL TESTS COMPLETED ===")
