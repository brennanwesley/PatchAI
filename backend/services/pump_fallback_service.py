"""
Pump Fallback Service - Provides reliable pump data access when OpenAI fails
This service ensures users always get pump information, even when OpenAI is unavailable
"""

import json
import os
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class PumpFallbackService:
    """
    Provides fallback pump data responses when OpenAI integration fails
    This ensures users always get pump information regardless of OpenAI availability
    """
    
    def __init__(self):
        self.pump_data = self._load_pump_data()
        self.response_templates = self._load_response_templates()
        
    def _load_pump_data(self) -> Dict[str, Any]:
        """Load pump data from JSON files"""
        try:
            data_dir = Path(__file__).parent.parent / "data" / "pumps"
            pump_file = data_dir / "transfer_pumps.json"
            
            if pump_file.exists():
                with open(pump_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"[PUMP_FALLBACK] Loaded {len(data)} pump records")
                    return data
            else:
                logger.error(f"[PUMP_FALLBACK] Pump data file not found: {pump_file}")
                return {}
                
        except Exception as e:
            logger.error(f"[PUMP_FALLBACK] Failed to load pump data: {e}")
            return {}
    
    def _load_response_templates(self) -> Dict[str, str]:
        """Load response templates for different pump queries"""
        return {
            "general": """Based on our pump database, here's what I found:

{pump_info}

**Key Specifications:**
- Model: {model}
- Flow Rate: {flow_rate}
- Head: {head}
- Power: {power}
- Inlet/Outlet: {inlet_outlet}

**Applications:**
{applications}

**Additional Details:**
{additional_details}

*Note: This information is provided from our technical database. For detailed specifications or custom requirements, please contact our technical support team.*""",
            
            "specific_model": """Here are the specifications for the {model} pump:

**Technical Specifications:**
- Flow Rate: {flow_rate}
- Total Head: {head}
- Power Requirements: {power}
- Inlet/Outlet Size: {inlet_outlet}
- Efficiency: {efficiency}

**Performance Characteristics:**
{performance}

**Recommended Applications:**
{applications}

**Installation Notes:**
{installation}

*This data is sourced from our comprehensive pump database. Contact support for additional technical details.*""",
            
            "comparison": """Here's a comparison of available transfer pumps:

{comparison_table}

**Selection Guidance:**
{selection_guidance}

**Popular Models:**
{popular_models}

*Our technical team can help you select the optimal pump for your specific application.*""",
            
            "troubleshooting": """**Pump Troubleshooting Guide:**

{troubleshooting_steps}

**Common Issues and Solutions:**
{common_issues}

**Maintenance Recommendations:**
{maintenance}

*For complex issues, please contact our technical support team with your pump model and specific symptoms.*"""
        }
    
    def detect_query_type(self, query: str) -> str:
        """Detect the type of pump query to provide appropriate response"""
        query_lower = query.lower()
        
        # Check for specific model numbers
        if any(model in query_lower for model in ['4x6-13', '6x8-15', '8x10-20']):
            return "specific_model"
        
        # Check for comparison keywords
        if any(word in query_lower for word in ['compare', 'comparison', 'vs', 'versus', 'difference']):
            return "comparison"
        
        # Check for troubleshooting keywords
        if any(word in query_lower for word in ['problem', 'issue', 'troubleshoot', 'repair', 'fix', 'maintenance']):
            return "troubleshooting"
        
        # Default to general query
        return "general"
    
    def extract_model_from_query(self, query: str) -> Optional[str]:
        """Extract specific pump model from query"""
        query_lower = query.lower()
        
        # Common model patterns
        model_patterns = ['4x6-13', '6x8-15', '8x10-20', '4x6', '6x8', '8x10']
        
        for pattern in model_patterns:
            if pattern in query_lower:
                return pattern
        
        return None
    
    def find_pump_by_model(self, model: str) -> Optional[Dict[str, Any]]:
        """Find pump data by model number"""
        if not self.pump_data:
            return None
        
        model_lower = model.lower()
        
        # Search through pump data
        for pump in self.pump_data:
            if isinstance(pump, dict):
                pump_model = pump.get('model', '').lower()
                if model_lower in pump_model or pump_model in model_lower:
                    return pump
        
        return None
    
    def generate_fallback_response(self, query: str) -> str:
        """Generate a comprehensive fallback response for pump queries"""
        try:
            query_type = self.detect_query_type(query)
            model = self.extract_model_from_query(query)
            
            logger.info(f"[PUMP_FALLBACK] Query type: {query_type}, Model: {model}")
            
            if query_type == "specific_model" and model:
                return self._generate_specific_model_response(model, query)
            elif query_type == "comparison":
                return self._generate_comparison_response(query)
            elif query_type == "troubleshooting":
                return self._generate_troubleshooting_response(query)
            else:
                return self._generate_general_response(query)
                
        except Exception as e:
            logger.error(f"[PUMP_FALLBACK] Error generating response: {e}")
            return self._generate_emergency_response(query)
    
    def _generate_specific_model_response(self, model: str, query: str) -> str:
        """Generate response for specific pump model queries"""
        pump_data = self.find_pump_by_model(model)
        
        if pump_data:
            return self._format_detailed_pump_response(pump_data, query)
        else:
            return f"""**{model.upper()} Transfer Pump Information**

I found your query about the {model} pump model. While I don't have the complete specifications immediately available, here's what I can tell you:

**General Transfer Pump Characteristics:**
- Designed for efficient water transfer applications
- Suitable for irrigation, dewatering, and general water movement
- Robust construction for reliable operation
- Available with various power options

**Next Steps:**
For detailed specifications including flow rates, head pressure, power requirements, and pricing for the {model} model, please:

1. Contact our technical support team
2. Request a detailed specification sheet
3. Discuss your specific application requirements

Our team can provide exact specifications and help ensure this pump meets your needs.

*This information is provided from our pump database. Contact support for complete technical specifications.*"""
    
    def _format_detailed_pump_response(self, pump_data: Dict[str, Any], query: str) -> str:
        """Format detailed pump response from actual JSON data structure"""
        try:
            model = pump_data.get('model', 'Unknown Model')
            size = pump_data.get('size', 'Unknown Size')
            pump_type = pump_data.get('type', 'transfer')
            specs = pump_data.get('specs', {})
            curve_data = pump_data.get('curve_data', {})
            
            # Extract RPM from query if specified
            requested_rpm = self._extract_rpm_from_query(query)
            
            # Build comprehensive response
            impeller_dia = specs.get('impeller_dia_inches', 'N/A')
            max_temp = specs.get('max_temp_f', 'N/A')
            max_solids = specs.get('max_solids_inches', 'N/A')
            
            response = f"""**{model} - {size} Transfer Pump Specifications**

**Basic Specifications:**
- Model: {model}
- Size: {size}
- Type: {pump_type.replace('_', ' ').title()}
- Maximum HP: {specs.get('max_hp', 'Contact support')}
- RPM Options: {', '.join(map(str, specs.get('rpm_options', [])))}
- Impeller Diameter: {impeller_dia}" (max)
- Maximum Temperature: {max_temp}°F
- Specific Gravity Range: {specs.get('sg_range', [0.8, 1.2])}
- Maximum Solids: {max_solids}" particles
"""
            
            # Add fluid compatibility
            fluid_types = specs.get('fluid_types', [])
            if fluid_types:
                fluid_list = ', '.join(fluid_types).replace('_', ' ').title()
                response += f"\n**Fluid Compatibility:**\n- {fluid_list}\n"
            
            # Add performance curves if available
            if curve_data:
                response += self._format_performance_curves(curve_data, requested_rpm)
            
            # Add trim options if available
            trim_options = specs.get('trim_options_inches', [])
            if trim_options:
                trim_list = ', '.join(map(str, trim_options))
                response += f"\n**Impeller Trim Options:**\n- Available trims: {trim_list}\"\n"
            
            # Add VFD information if available
            vfd_range = specs.get('vfd_hz_range', [])
            if vfd_range:
                response += f"\n**Variable Frequency Drive (VFD):**\n- Frequency Range: {vfd_range[0]}-{vfd_range[1]} Hz\n- Allows flow and head adjustment\n"
            
            response += "\n*This data is sourced from our comprehensive pump database. Contact support for installation guidance and custom applications.*"
            
            return response
            
        except Exception as e:
            logger.error(f"[PUMP_FALLBACK] Error formatting detailed response: {e}")
            return f"**{pump_data.get('model', 'Unknown')} Pump Information**\n\nTechnical specifications are available. Please contact support for detailed performance data."
    
    def _extract_rpm_from_query(self, query: str) -> Optional[int]:
        """Extract RPM value from user query"""
        import re
        rpm_match = re.search(r'(\d+)\s*rpm', query.lower())
        if rpm_match:
            return int(rpm_match.group(1))
        return None
    
    def _format_performance_curves(self, curve_data: Dict[str, Any], requested_rpm: Optional[int] = None) -> str:
        """Format performance curve data for display"""
        try:
            curves_text = "\n**Performance Data:**\n"
            
            # If specific RPM requested, show only that data
            if requested_rpm:
                rpm_key = f"rpm_{requested_rpm}"
                if rpm_key in curve_data:
                    curves_text += f"\n*At {requested_rpm} RPM:*\n"
                    curves_text += self._format_single_rpm_curve(curve_data[rpm_key])
                else:
                    curves_text += f"\n*Requested RPM ({requested_rpm}) not available. Available RPMs: {', '.join([k.replace('rpm_', '') for k in curve_data.keys()]))*\n"
            else:
                # Show all available RPM data
                for rpm_key, rpm_data in curve_data.items():
                    if rpm_key.startswith('rpm_'):
                        rpm_value = rpm_key.replace('rpm_', '')
                        curves_text += f"\n*At {rpm_value} RPM:*\n"
                        curves_text += self._format_single_rpm_curve(rpm_data)
            
            return curves_text
            
        except Exception as e:
            logger.error(f"[PUMP_FALLBACK] Error formatting curves: {e}")
            return "\n**Performance Data:** Contact support for detailed curves\n"
    
    def _format_single_rpm_curve(self, rpm_data: Dict[str, Any]) -> str:
        """Format curve data for a single RPM"""
        try:
            curve_text = ""
            
            # Format head vs flow data
            head_vs_flow = rpm_data.get('head_vs_flow', [])
            if head_vs_flow:
                curve_text += "\n**Flow Rate vs Head Pressure:**\n"
                curve_text += "| Flow (GPM) | Head (ft) |\n"
                curve_text += "|------------|-----------|\n"
                for point in head_vs_flow:
                    flow = point.get('flow', 0)
                    head = point.get('head', 0)
                    curve_text += f"| {flow:,} | {head} |\n"
            
            # Format efficiency data
            efficiency = rpm_data.get('efficiency', [])
            if efficiency:
                curve_text += "\n**Efficiency Data:**\n"
                curve_text += "| Flow (GPM) | Efficiency (%) |\n"
                curve_text += "|------------|----------------|\n"
                for point in efficiency:
                    flow = point.get('flow', 0)
                    eff = point.get('eff', 0)
                    curve_text += f"| {flow:,} | {eff}% |\n"
            
            # Format NPSH data
            npsh_data = rpm_data.get('npsh_required', [])
            if npsh_data:
                curve_text += "\n**NPSH Required:**\n"
                curve_text += "| Flow (GPM) | NPSH (ft) |\n"
                curve_text += "|------------|-----------|\n"
                for point in npsh_data:
                    flow = point.get('flow', 0)
                    npsh = point.get('npsh', 0)
                    curve_text += f"| {flow:,} | {npsh} |\n"
            
            return curve_text
            
        except Exception as e:
            logger.error(f"[PUMP_FALLBACK] Error formatting single RPM curve: {e}")
            return "Performance data available - contact support for details\n"
    
    def _generate_comparison_response(self, query: str) -> str:
        """Generate response for pump comparison queries"""
        return """**Transfer Pump Comparison Guide**

**Popular Transfer Pump Models:**

**4x6-13 Series:**
- Ideal for: Medium flow applications
- Flow Range: Moderate to high
- Applications: Irrigation, dewatering
- Power: Efficient operation

**6x8-15 Series:**
- Ideal for: High flow applications
- Flow Range: High capacity
- Applications: Large-scale water transfer
- Power: Higher capacity motor

**8x10-20 Series:**
- Ideal for: Maximum flow applications
- Flow Range: Very high capacity
- Applications: Industrial water transfer
- Power: Heavy-duty motor

**Selection Factors:**
1. **Flow Requirements** - Match pump capacity to your needs
2. **Head Pressure** - Consider elevation and distance
3. **Power Availability** - Ensure adequate electrical supply
4. **Application Type** - Continuous vs. intermittent use

**Recommendation:**
For specific comparisons and selection guidance, our technical team can analyze your requirements and recommend the optimal pump model.

*Contact our support team for detailed specifications and personalized recommendations.*"""
    
    def _generate_troubleshooting_response(self, query: str) -> str:
        """Generate response for troubleshooting queries"""
        return """**Transfer Pump Troubleshooting Guide**

**Common Issues and Solutions:**

**1. Low Flow or No Flow:**
- Check for clogged intake screen
- Verify pump is properly primed
- Inspect for air leaks in suction line
- Check impeller for damage or wear

**2. Excessive Vibration:**
- Ensure pump is properly mounted
- Check for cavitation (insufficient suction)
- Inspect coupling alignment
- Verify impeller balance

**3. Overheating:**
- Check for adequate ventilation
- Verify proper voltage supply
- Inspect for overloading conditions
- Check bearing lubrication

**4. Electrical Issues:**
- Verify power supply voltage
- Check motor connections
- Inspect control panel settings
- Test motor insulation

**Maintenance Schedule:**
- **Daily:** Visual inspection, check for leaks
- **Weekly:** Monitor performance, check vibration
- **Monthly:** Lubricate bearings, inspect seals
- **Annually:** Complete overhaul, replace wear parts

**When to Call Support:**
- Persistent performance issues
- Unusual noises or vibrations
- Electrical problems
- Major repairs needed

*For complex troubleshooting, contact our technical support team with your pump model and specific symptoms.*"""
    
    def _generate_general_response(self, query: str) -> str:
        """Generate response for general pump queries"""
        return """**Water Transfer Pump Information**

**Our Transfer Pump Range:**
We offer a comprehensive selection of water transfer pumps designed for reliable, efficient operation across various applications.

**Key Features:**
- **High Efficiency:** Optimized impeller design for maximum performance
- **Durable Construction:** Built to withstand demanding conditions
- **Versatile Applications:** Suitable for irrigation, dewatering, and water transfer
- **Multiple Sizes:** Range of capacities to meet different flow requirements

**Popular Applications:**
- Agricultural irrigation systems
- Construction site dewatering
- Municipal water transfer
- Industrial process water
- Emergency water removal

**Technical Support:**
Our technical team provides:
- Application analysis and pump selection
- Installation guidance and support
- Maintenance recommendations
- Troubleshooting assistance
- Replacement parts and service

**Available Models:**
- 4x6-13 Series: Medium capacity applications
- 6x8-15 Series: High capacity applications  
- 8x10-20 Series: Maximum capacity applications

**Next Steps:**
For specific technical specifications, pricing, or application guidance, please contact our technical support team. We can help you select the optimal pump for your requirements.

*This information is provided from our comprehensive pump database.*"""
    
    def _generate_emergency_response(self, query: str) -> str:
        """Generate emergency response when all else fails"""
        return """**Pump Information Available**

Thank you for your inquiry about our water transfer pumps. While I'm experiencing some technical difficulties accessing the complete database, I can still help you.

**What We Offer:**
- Comprehensive range of water transfer pumps
- Professional technical support
- Complete specifications and documentation
- Installation and maintenance guidance

**Immediate Assistance:**
For immediate access to pump specifications, pricing, and technical support, please:

1. **Contact our technical team directly**
2. **Request specific model information**
3. **Discuss your application requirements**

Our experienced team can provide detailed information about:
- Flow rates and head pressure specifications
- Power requirements and electrical connections
- Installation requirements and recommendations
- Maintenance schedules and parts availability

**We're Here to Help:**
Despite this temporary technical issue, our commitment to providing excellent pump solutions remains unchanged. Our technical team is ready to assist with all your water transfer pump needs.

*Contact our support team for immediate assistance with pump selection and specifications.*"""
    
    def is_pump_related_query(self, query: str) -> bool:
        """Determine if a query is related to pumps"""
        pump_keywords = [
            'pump', 'pumps', 'transfer', 'water', 'flow', 'irrigation',
            'dewatering', 'centrifugal', 'impeller', 'suction', 'discharge',
            '4x6', '6x8', '8x10', 'gpm', 'head', 'pressure'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in pump_keywords)
