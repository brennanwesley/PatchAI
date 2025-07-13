"""
Pump data loader utility for accessing and validating pump curve data.
"""
import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

class PumpDataLoader:
    """Utility class for loading and accessing pump curve data."""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent
        self.transfer_pumps_file = self.data_dir / "transfer_pumps.json"
        self._transfer_pumps_data = None
    
    def load_transfer_pumps(self) -> List[Dict[str, Any]]:
        """Load transfer pump data from JSON file."""
        if self._transfer_pumps_data is None:
            try:
                with open(self.transfer_pumps_file, 'r') as f:
                    self._transfer_pumps_data = json.load(f)
            except FileNotFoundError:
                raise FileNotFoundError(f"Transfer pumps data file not found: {self.transfer_pumps_file}")
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in transfer pumps data file: {e}")
        
        return self._transfer_pumps_data
    
    def get_pump_by_size(self, size: str) -> Optional[Dict[str, Any]]:
        """Get pump data by size (e.g., '3x4-13')."""
        pumps = self.load_transfer_pumps()
        for pump in pumps:
            if pump.get('size') == size:
                return pump
        return None
    
    def get_pumps_by_type(self, pump_type: str) -> List[Dict[str, Any]]:
        """Get all pumps of a specific type."""
        pumps = self.load_transfer_pumps()
        return [pump for pump in pumps if pump.get('type') == pump_type]
    
    def get_all_pump_sizes(self) -> List[str]:
        """Get list of all available pump sizes."""
        pumps = self.load_transfer_pumps()
        return [pump.get('size') for pump in pumps if pump.get('size')]
    
    def validate_data_structure(self) -> Dict[str, Any]:
        """Validate the pump data structure and return validation results."""
        try:
            pumps = self.load_transfer_pumps()
            results = {
                'valid': True,
                'pump_count': len(pumps),
                'sizes': [],
                'types': set(),
                'errors': []
            }
            
            for i, pump in enumerate(pumps):
                # Check required fields
                required_fields = ['type', 'model', 'size', 'specs', 'curve_data', 'sensitivity_factors']
                for field in required_fields:
                    if field not in pump:
                        results['errors'].append(f"Pump {i}: Missing required field '{field}'")
                        results['valid'] = False
                
                if 'size' in pump:
                    results['sizes'].append(pump['size'])
                if 'type' in pump:
                    results['types'].add(pump['type'])
                
                # Validate curve data structure
                if 'curve_data' in pump:
                    for rpm_key, rpm_data in pump['curve_data'].items():
                        required_curves = ['head_vs_flow', 'efficiency', 'npsh_required', 'power_required']
                        for curve in required_curves:
                            if curve not in rpm_data:
                                results['errors'].append(f"Pump {i}, {rpm_key}: Missing curve '{curve}'")
                                results['valid'] = False
            
            results['types'] = list(results['types'])
            return results
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'pump_count': 0,
                'sizes': [],
                'types': [],
                'errors': [str(e)]
            }

# Global instance for easy access
pump_data_loader = PumpDataLoader()
