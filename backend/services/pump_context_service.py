"""
Pump Context Service for OpenAI Integration
Provides real-time pump data and expertise to enhance chat responses
"""

import logging
from typing import Dict, List, Optional, Any
from services.pump_service import PumpSelectionService
from data.pumps.data_loader import PumpDataLoader

logger = logging.getLogger(__name__)


class PumpContextService:
    """Service to provide pump expertise context for OpenAI chat responses"""
    
    def __init__(self):
        self.pump_data_loader = PumpDataLoader()
        self.pump_selection_service = PumpSelectionService()
    
    def detect_pump_query(self, user_message: str) -> bool:
        """Detect if user message is asking about pumps or pump-related topics"""
        pump_keywords = [
            'pump', 'pumps', 'pumping', 'transfer', 'centrifugal',
            'flow', 'gpm', 'head', 'feet', 'ft', 'pressure',
            'npsh', 'cavitation', 'efficiency', 'horsepower', 'hp',
            'rpm', 'impeller', 'trim', 'vfd', 'produced water',
            'brine', 'fluid', 'suction', 'discharge', 'curve',
            'performance', 'selection', 'sizing', 'goulds'
        ]
        
        message_lower = user_message.lower()
        return any(keyword in message_lower for keyword in pump_keywords)
    
    def get_pump_inventory_context(self) -> str:
        """Get current pump inventory as context for OpenAI"""
        try:
            pumps = self.pump_data_loader.load_transfer_pumps()
            
            context = "CURRENT PUMP INVENTORY:\n"
            for pump in pumps:
                available_rpms = [int(rpm_key.split('_')[1]) for rpm_key in pump['curve_data'].keys()]
                context += f"- {pump['size']}: {pump['model']} ({pump['type']})\n"
                context += f"  Max HP: {pump['specs']['max_hp']}, RPMs: {sorted(available_rpms)}\n"
                context += f"  Fluids: {', '.join(pump['specs']['fluid_types'])}\n"
                context += f"  SG Range: {pump['specs']['sg_range'][0]}-{pump['specs']['sg_range'][1]}\n"
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting pump inventory context: {str(e)}")
            return "PUMP INVENTORY: Error loading pump data"
    
    def get_pump_recommendations_context(self, flow_gpm: float, head_ft: float, 
                                       fluid_type: str = "produced_water", 
                                       fluid_sg: float = 1.1) -> str:
        """Get pump recommendations as context for specific requirements"""
        try:
            recommendations = self.pump_selection_service.find_suitable_pumps(
                required_flow_gpm=flow_gpm,
                required_head_ft=head_ft,
                fluid_sg=fluid_sg,
                fluid_type=fluid_type
            )
            
            if not recommendations:
                return f"PUMP RECOMMENDATIONS: No suitable pumps found for {flow_gpm} GPM @ {head_ft} ft"
            
            context = f"PUMP RECOMMENDATIONS for {flow_gpm} GPM @ {head_ft} ft:\n"
            for i, rec in enumerate(recommendations[:3], 1):  # Top 3 recommendations
                context += f"{i}. {rec.pump_size} - {rec.recommendation_level.value} match\n"
                context += f"   Efficiency: {rec.operating_point.efficiency_percent:.1f}%, Power: {rec.operating_point.power_hp:.1f} HP\n"
                context += f"   NPSH Required: {rec.operating_point.npsh_required_ft:.1f} ft, RPM: {rec.operating_point.rpm}\n"
                if rec.warnings:
                    context += f"   Warnings: {len(rec.warnings)} items\n"
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting pump recommendations: {str(e)}")
            return f"PUMP RECOMMENDATIONS: Error calculating recommendations for {flow_gpm} GPM @ {head_ft} ft"
    
    def get_pump_performance_context(self, pump_size: str, flow_gpm: float, 
                                   rpm: int = 1750, fluid_sg: float = 1.1) -> str:
        """Get specific pump performance data as context"""
        try:
            pump = self.pump_data_loader.get_pump_by_size(pump_size)
            if not pump:
                return f"PUMP PERFORMANCE: Pump {pump_size} not found"
            
            rpm_key = f"rpm_{rpm}"
            if rpm_key not in pump['curve_data']:
                available_rpms = [int(k.split('_')[1]) for k in pump['curve_data'].keys()]
                return f"PUMP PERFORMANCE: RPM {rpm} not available for {pump_size}. Available: {available_rpms}"
            
            curve_data = pump['curve_data'][rpm_key]
            
            # Calculate performance at specified flow
            efficiency = self.pump_selection_service._interpolate_curve(curve_data['efficiency'], flow_gpm)
            power_hp = self.pump_selection_service._interpolate_curve(curve_data['power_required'], flow_gpm)
            npsh_req = self.pump_selection_service._interpolate_curve(curve_data['npsh_required'], flow_gpm)
            head_at_flow = self.pump_selection_service._interpolate_curve(curve_data['head_vs_flow'], flow_gpm)
            
            if any(x is None for x in [efficiency, power_hp, npsh_req, head_at_flow]):
                return f"PUMP PERFORMANCE: Flow {flow_gpm} GPM outside curve range for {pump_size}"
            
            brake_hp = power_hp * fluid_sg
            
            context = f"PUMP PERFORMANCE - {pump_size} @ {flow_gpm} GPM, {rpm} RPM:\n"
            context += f"Head: {head_at_flow:.1f} ft, Efficiency: {efficiency:.1f}%\n"
            context += f"Power Required: {power_hp:.1f} HP, Brake HP: {brake_hp:.1f} HP\n"
            context += f"NPSH Required: {npsh_req:.1f} ft\n"
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting pump performance: {str(e)}")
            return f"PUMP PERFORMANCE: Error calculating performance for {pump_size}"
    
    def extract_pump_parameters(self, user_message: str) -> Dict[str, Any]:
        """Extract pump-related parameters from user message using simple parsing"""
        import re
        
        params = {}
        message_lower = user_message.lower()
        
        # Extract flow rate (GPM)
        flow_patterns = [
            r'(\d+(?:\.\d+)?)\s*gpm',
            r'(\d+(?:\.\d+)?)\s*gallons?\s*per\s*minute',
            r'flow.*?(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*gallon'
        ]
        for pattern in flow_patterns:
            match = re.search(pattern, message_lower)
            if match:
                params['flow_gpm'] = float(match.group(1))
                break
        
        # Extract head (feet)
        head_patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:ft|feet)',
            r'head.*?(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*foot'
        ]
        for pattern in head_patterns:
            match = re.search(pattern, message_lower)
            if match:
                params['head_ft'] = float(match.group(1))
                break
        
        # Extract RPM
        rpm_patterns = [
            r'(\d+)\s*rpm',
            r'(\d+)\s*revolutions?\s*per\s*minute'
        ]
        for pattern in rpm_patterns:
            match = re.search(pattern, message_lower)
            if match:
                params['rpm'] = int(match.group(1))
                break
        
        # Extract pump size
        pump_size_patterns = [
            r'(\d+x\d+-\d+)',
            r'(\d+\s*x\s*\d+\s*-\s*\d+)'
        ]
        for pattern in pump_size_patterns:
            match = re.search(pattern, message_lower.replace(' ', ''))
            if match:
                params['pump_size'] = match.group(1).replace(' ', '')
                break
        
        # Extract fluid type
        if 'produced water' in message_lower:
            params['fluid_type'] = 'produced_water'
        elif 'brine' in message_lower:
            params['fluid_type'] = 'brine'
        elif 'oil' in message_lower:
            params['fluid_type'] = 'oil'
        
        return params
    
    def generate_pump_context(self, user_message: str) -> Optional[str]:
        """Generate relevant pump context based on user message"""
        if not self.detect_pump_query(user_message):
            return None
        
        try:
            # Extract parameters from user message
            params = self.extract_pump_parameters(user_message)
            
            context_parts = []
            
            # Always include inventory for pump-related queries
            context_parts.append(self.get_pump_inventory_context())
            
            # If flow and head specified, provide recommendations
            if 'flow_gpm' in params and 'head_ft' in params:
                fluid_type = params.get('fluid_type', 'produced_water')
                recommendations_context = self.get_pump_recommendations_context(
                    params['flow_gpm'], params['head_ft'], fluid_type
                )
                context_parts.append(recommendations_context)
            
            # If specific pump and flow specified, provide performance data
            if 'pump_size' in params and 'flow_gpm' in params:
                rpm = params.get('rpm', 1750)
                performance_context = self.get_pump_performance_context(
                    params['pump_size'], params['flow_gpm'], rpm
                )
                context_parts.append(performance_context)
            
            return "\n\n".join(context_parts) if context_parts else None
            
        except Exception as e:
            logger.error(f"Error generating pump context: {str(e)}")
            return "PUMP CONTEXT: Error generating pump-specific context"
