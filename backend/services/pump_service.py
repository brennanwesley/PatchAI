"""
Pump Selection Service - Engineering logic for pump curve analysis and selection.
Provides intelligent pump recommendations based on flow, head, and operating conditions.
"""
import math
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from data.pumps.data_loader import pump_data_loader


class PumpRecommendationLevel(Enum):
    """Recommendation confidence levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    MARGINAL = "marginal"
    NOT_RECOMMENDED = "not_recommended"


@dataclass
class OperatingPoint:
    """Represents a pump operating point with calculated performance."""
    flow_gpm: float
    head_ft: float
    efficiency_percent: float
    power_hp: float
    npsh_required_ft: float
    rpm: int
    
    # Calculated values
    brake_horsepower: float
    fluid_horsepower: float
    npsh_margin_ft: Optional[float] = None
    cavitation_risk: bool = False


@dataclass
class PumpRecommendation:
    """Complete pump recommendation with engineering analysis."""
    pump_size: str
    pump_model: str
    pump_type: str
    recommendation_level: PumpRecommendationLevel
    operating_point: OperatingPoint
    
    # Engineering analysis
    efficiency_rating: str
    npsh_analysis: str
    power_analysis: str
    operating_range_analysis: str
    warnings: List[str]
    notes: List[str]
    
    # Sensitivity analysis
    trim_recommendations: List[Dict[str, Any]]
    vfd_recommendations: List[Dict[str, Any]]


class PumpSelectionService:
    """Service for intelligent pump selection and performance analysis."""
    
    def __init__(self):
        self.data_loader = pump_data_loader
    
    def find_suitable_pumps(
        self,
        required_flow_gpm: float,
        required_head_ft: float,
        fluid_sg: float = 1.1,
        npsh_available_ft: float = 8.0,
        max_power_hp: Optional[float] = None,
        preferred_rpm: Optional[int] = None,
        fluid_type: str = "produced_water"
    ) -> List[PumpRecommendation]:
        """
        Find and rank suitable pumps for given requirements.
        
        Args:
            required_flow_gpm: Required flow rate in GPM
            required_head_ft: Required head in feet
            fluid_sg: Specific gravity of fluid (default 1.1 for produced water)
            npsh_available_ft: Available NPSH in feet (default 8.0)
            max_power_hp: Maximum allowable power in HP
            preferred_rpm: Preferred RPM (1200, 1750, 3550)
            fluid_type: Type of fluid being pumped
        
        Returns:
            List of pump recommendations sorted by suitability
        """
        pumps_data = self.data_loader.load_transfer_pumps()
        recommendations = []
        
        for pump in pumps_data:
            # Check if pump handles this fluid type
            if fluid_type not in pump['specs']['fluid_types']:
                continue
            
            # Check specific gravity range
            sg_range = pump['specs']['sg_range']
            if not (sg_range[0] <= fluid_sg <= sg_range[1]):
                continue
            
            # Analyze each RPM option
            for rpm_key, curve_data in pump['curve_data'].items():
                rpm = int(rpm_key.split('_')[1])
                
                # Skip if preferred RPM specified and doesn't match
                if preferred_rpm and rpm != preferred_rpm:
                    continue
                
                # Calculate operating point
                operating_point = self._calculate_operating_point(
                    curve_data, required_flow_gpm, required_head_ft, 
                    fluid_sg, rpm
                )
                
                if not operating_point:
                    continue
                
                # Check power constraint
                if max_power_hp and operating_point.brake_horsepower > max_power_hp:
                    continue
                
                # Perform engineering analysis
                recommendation = self._analyze_pump_suitability(
                    pump, operating_point, npsh_available_ft, 
                    required_flow_gpm, required_head_ft
                )
                
                if recommendation:
                    recommendations.append(recommendation)
        
        # Sort by recommendation level and efficiency
        recommendations.sort(key=lambda x: (
            self._get_recommendation_score(x.recommendation_level),
            -x.operating_point.efficiency_percent
        ))
        
        return recommendations
    
    def _calculate_operating_point(
        self, 
        curve_data: Dict[str, Any], 
        flow_gpm: float, 
        head_ft: float,
        fluid_sg: float,
        rpm: int
    ) -> Optional[OperatingPoint]:
        """Calculate pump operating point by interpolating curve data."""
        try:
            # Interpolate performance curves at required flow
            efficiency = self._interpolate_curve(curve_data['efficiency'], flow_gpm)
            power_hp = self._interpolate_curve(curve_data['power_required'], flow_gpm)
            npsh_req = self._interpolate_curve(curve_data['npsh_required'], flow_gpm)
            head_at_flow = self._interpolate_curve(curve_data['head_vs_flow'], flow_gpm)
            
            if any(x is None for x in [efficiency, power_hp, npsh_req, head_at_flow]):
                return None
            
            # Check if pump can deliver required head at this flow
            if head_at_flow < head_ft * 0.9:  # 10% tolerance
                return None
            
            # Calculate brake horsepower accounting for specific gravity
            brake_hp = power_hp * fluid_sg
            
            # Calculate fluid horsepower
            fluid_hp = (flow_gpm * head_ft * fluid_sg) / (3960 * (efficiency / 100))
            
            return OperatingPoint(
                flow_gpm=flow_gpm,
                head_ft=head_ft,
                efficiency_percent=efficiency,
                power_hp=power_hp,
                npsh_required_ft=npsh_req,
                rpm=rpm,
                brake_horsepower=brake_hp,
                fluid_horsepower=fluid_hp
            )
            
        except Exception:
            return None
    
    def _interpolate_curve(self, curve_points: List[Dict], target_flow: float) -> Optional[float]:
        """Interpolate curve value at target flow rate."""
        if not curve_points:
            return None
        
        # Sort by flow
        points = sorted(curve_points, key=lambda x: x['flow'])
        
        # Check if target flow is within curve range
        min_flow = points[0]['flow']
        max_flow = points[-1]['flow']
        
        if target_flow < min_flow or target_flow > max_flow:
            return None
        
        # Find surrounding points
        for i in range(len(points) - 1):
            if points[i]['flow'] <= target_flow <= points[i + 1]['flow']:
                # Linear interpolation
                x1, y1 = points[i]['flow'], list(points[i].values())[1]  # Second value (head, eff, etc.)
                x2, y2 = points[i + 1]['flow'], list(points[i + 1].values())[1]
                
                if x2 == x1:
                    return y1
                
                return y1 + (y2 - y1) * (target_flow - x1) / (x2 - x1)
        
        return None
    
    def _analyze_pump_suitability(
        self,
        pump: Dict[str, Any],
        operating_point: OperatingPoint,
        npsh_available: float,
        required_flow: float,
        required_head: float
    ) -> Optional[PumpRecommendation]:
        """Perform comprehensive engineering analysis of pump suitability."""
        warnings = []
        notes = []
        
        # NPSH Analysis
        npsh_margin = npsh_available - operating_point.npsh_required_ft
        operating_point.npsh_margin_ft = npsh_margin
        
        if npsh_margin < 2:
            operating_point.cavitation_risk = True
            warnings.append("CRITICAL: Insufficient NPSH margin - high cavitation risk")
        elif npsh_margin < 5:
            warnings.append("WARNING: Low NPSH margin - consider charge pump")
        
        # Apply sensitivity factor guidelines
        sensitivity = pump.get('sensitivity_factors', {})
        npshr_guideline = sensitivity.get('npshr_guideline', '')
        if operating_point.npsh_required_ft > 12 and npshr_guideline:
            warnings.append("NPSH exceeds standard tank levels - charge pump recommended")
        
        # Efficiency Analysis
        efficiency_rating = self._rate_efficiency(operating_point.efficiency_percent)
        
        if operating_point.efficiency_percent < 50:
            warnings.append("Low efficiency operation - consider larger pump or different RPM")
        elif operating_point.efficiency_percent > 65:
            notes.append("Excellent efficiency operation")
        
        # Operating Range Analysis
        range_analysis = self._analyze_operating_range(pump, required_flow, operating_point.rpm)
        
        # Power Analysis
        power_analysis = f"Brake HP: {operating_point.brake_horsepower:.1f}, Fluid HP: {operating_point.fluid_horsepower:.1f}"
        
        # Determine recommendation level
        recommendation_level = self._determine_recommendation_level(
            operating_point, npsh_margin, efficiency_rating
        )
        
        # Generate trim and VFD recommendations
        trim_recs = self._generate_trim_recommendations(pump, operating_point)
        vfd_recs = self._generate_vfd_recommendations(pump, operating_point, required_flow, required_head)
        
        return PumpRecommendation(
            pump_size=pump['size'],
            pump_model=pump['model'],
            pump_type=pump['type'],
            recommendation_level=recommendation_level,
            operating_point=operating_point,
            efficiency_rating=efficiency_rating,
            npsh_analysis=f"Required: {operating_point.npsh_required_ft:.1f} ft, Available: {npsh_available:.1f} ft, Margin: {npsh_margin:.1f} ft",
            power_analysis=power_analysis,
            operating_range_analysis=range_analysis,
            warnings=warnings,
            notes=notes,
            trim_recommendations=trim_recs,
            vfd_recommendations=vfd_recs
        )
    
    def _rate_efficiency(self, efficiency: float) -> str:
        """Rate pump efficiency performance."""
        if efficiency >= 70:
            return "Excellent"
        elif efficiency >= 60:
            return "Good"
        elif efficiency >= 50:
            return "Acceptable"
        elif efficiency >= 40:
            return "Poor"
        else:
            return "Very Poor"
    
    def _analyze_operating_range(self, pump: Dict, flow: float, rpm: int) -> str:
        """Analyze if operating point is within optimal range."""
        curve_data = pump['curve_data'][f'rpm_{rpm}']
        flow_points = [point['flow'] for point in curve_data['head_vs_flow']]
        
        min_flow = min(flow_points)
        max_flow = max(flow_points)
        optimal_range = (max_flow - min_flow) * 0.6  # Middle 60% is optimal
        optimal_start = min_flow + (max_flow - min_flow) * 0.2
        optimal_end = optimal_start + optimal_range
        
        if optimal_start <= flow <= optimal_end:
            return "Operating in optimal range"
        elif flow < optimal_start:
            return "Operating below optimal range - consider smaller pump"
        else:
            return "Operating above optimal range - consider larger pump"
    
    def _determine_recommendation_level(
        self, 
        op: OperatingPoint, 
        npsh_margin: float, 
        efficiency_rating: str
    ) -> PumpRecommendationLevel:
        """Determine overall recommendation level."""
        if op.cavitation_risk or npsh_margin < 2:
            return PumpRecommendationLevel.NOT_RECOMMENDED
        
        if efficiency_rating == "Excellent" and npsh_margin >= 5:
            return PumpRecommendationLevel.EXCELLENT
        elif efficiency_rating in ["Good", "Excellent"] and npsh_margin >= 3:
            return PumpRecommendationLevel.GOOD
        elif efficiency_rating == "Acceptable" and npsh_margin >= 2:
            return PumpRecommendationLevel.ACCEPTABLE
        else:
            return PumpRecommendationLevel.MARGINAL
    
    def _generate_trim_recommendations(self, pump: Dict, op: OperatingPoint) -> List[Dict[str, Any]]:
        """Generate impeller trim recommendations for optimization."""
        trim_options = pump['specs'].get('trim_options_inches', [])
        current_dia = pump['specs']['impeller_dia_inches']
        recommendations = []
        
        for trim_dia in trim_options:
            if trim_dia >= current_dia:
                continue
            
            # Calculate performance with trim
            trim_factor = trim_dia / current_dia
            new_head = op.head_ft * (trim_factor ** 2)
            new_power = op.power_hp * (trim_factor ** 3)
            
            recommendations.append({
                'trim_diameter_inches': trim_dia,
                'head_reduction_percent': (1 - trim_factor ** 2) * 100,
                'power_reduction_percent': (1 - trim_factor ** 3) * 100,
                'estimated_new_power_hp': new_power,
                'note': f"Trim to {trim_dia}\" for power savings"
            })
        
        return recommendations[:3]  # Top 3 recommendations
    
    def _generate_vfd_recommendations(
        self, 
        pump: Dict, 
        op: OperatingPoint, 
        req_flow: float, 
        req_head: float
    ) -> List[Dict[str, Any]]:
        """Generate VFD speed recommendations."""
        vfd_range = pump['specs'].get('vfd_hz_range', [40, 60])
        recommendations = []
        
        # Calculate required speed reduction for flow matching
        base_hz = 60
        for target_hz in [50, 45, 40]:
            if target_hz < vfd_range[0]:
                continue
            
            speed_ratio = target_hz / base_hz
            new_flow = op.flow_gpm * speed_ratio
            new_head = op.head_ft * (speed_ratio ** 2)
            new_power = op.power_hp * (speed_ratio ** 3)
            
            if abs(new_flow - req_flow) / req_flow < 0.1:  # Within 10%
                recommendations.append({
                    'frequency_hz': target_hz,
                    'speed_reduction_percent': (1 - speed_ratio) * 100,
                    'power_savings_percent': (1 - speed_ratio ** 3) * 100,
                    'estimated_flow_gpm': new_flow,
                    'estimated_head_ft': new_head,
                    'estimated_power_hp': new_power,
                    'note': f"VFD at {target_hz} Hz for optimal matching"
                })
        
        return recommendations
    
    def _get_recommendation_score(self, level: PumpRecommendationLevel) -> int:
        """Convert recommendation level to numeric score for sorting."""
        scores = {
            PumpRecommendationLevel.EXCELLENT: 1,
            PumpRecommendationLevel.GOOD: 2,
            PumpRecommendationLevel.ACCEPTABLE: 3,
            PumpRecommendationLevel.MARGINAL: 4,
            PumpRecommendationLevel.NOT_RECOMMENDED: 5
        }
        return scores.get(level, 6)
    
    def calculate_system_curve_intersection(
        self,
        pump_size: str,
        rpm: int,
        static_head_ft: float,
        friction_loss_coefficient: float = 0.001
    ) -> List[Dict[str, Any]]:
        """
        Calculate intersection points between pump curve and system curve.
        
        Args:
            pump_size: Pump size (e.g., '3x4-13')
            rpm: Operating RPM
            static_head_ft: Static head component
            friction_loss_coefficient: System friction coefficient
        
        Returns:
            List of intersection points with flow, head, and efficiency
        """
        pump = self.data_loader.get_pump_by_size(pump_size)
        if not pump:
            return []
        
        curve_data = pump['curve_data'].get(f'rpm_{rpm}')
        if not curve_data:
            return []
        
        intersections = []
        head_curve = curve_data['head_vs_flow']
        
        for point in head_curve:
            flow = point['flow']
            pump_head = point['head']
            
            # System curve: H_system = H_static + K * Q^2
            system_head = static_head_ft + friction_loss_coefficient * (flow ** 2)
            
            # Find approximate intersections (within 5% tolerance)
            if abs(pump_head - system_head) / max(pump_head, system_head) < 0.05:
                efficiency = self._interpolate_curve(curve_data['efficiency'], flow)
                power = self._interpolate_curve(curve_data['power_required'], flow)
                
                intersections.append({
                    'flow_gpm': flow,
                    'head_ft': pump_head,
                    'system_head_ft': system_head,
                    'efficiency_percent': efficiency,
                    'power_hp': power,
                    'operating_point_quality': 'good' if efficiency > 60 else 'acceptable'
                })
        
        return intersections


# Global service instance
pump_selection_service = PumpSelectionService()
