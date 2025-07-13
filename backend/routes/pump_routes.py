"""
Pump Selection API Routes
RESTful endpoints for pump curve data access and intelligent pump selection
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.pump_service import pump_selection_service, PumpRecommendationLevel
from data.pumps.data_loader import pump_data_loader

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pumps", tags=["Pump Selection"])

# Request/Response Models
class PumpSelectionRequest(BaseModel):
    """Request model for pump selection."""
    required_flow_gpm: float = Field(..., gt=0, description="Required flow rate in GPM")
    required_head_ft: float = Field(..., gt=0, description="Required head in feet")
    fluid_sg: float = Field(1.1, ge=0.5, le=2.0, description="Specific gravity of fluid")
    npsh_available_ft: float = Field(8.0, ge=0, description="Available NPSH in feet")
    max_power_hp: Optional[float] = Field(None, gt=0, description="Maximum allowable power in HP")
    preferred_rpm: Optional[int] = Field(None, description="Preferred RPM (1200, 1750, 3550)")
    fluid_type: str = Field("produced_water", description="Type of fluid being pumped")

class SystemCurveRequest(BaseModel):
    """Request model for system curve intersection analysis."""
    pump_size: str = Field(..., description="Pump size (e.g., '3x4-13')")
    rpm: int = Field(..., description="Operating RPM")
    static_head_ft: float = Field(..., ge=0, description="Static head component in feet")
    friction_loss_coefficient: float = Field(0.001, ge=0, description="System friction coefficient")

class PumpPerformanceRequest(BaseModel):
    """Request model for specific pump performance calculation."""
    pump_size: str = Field(..., description="Pump size (e.g., '3x4-13')")
    rpm: int = Field(..., description="Operating RPM")
    flow_gpm: float = Field(..., gt=0, description="Flow rate in GPM")
    fluid_sg: float = Field(1.1, ge=0.5, le=2.0, description="Specific gravity of fluid")

class OperatingPointResponse(BaseModel):
    """Response model for pump operating point."""
    flow_gpm: float
    head_ft: float
    efficiency_percent: float
    power_hp: float
    npsh_required_ft: float
    rpm: int
    brake_horsepower: float
    fluid_horsepower: float
    npsh_margin_ft: Optional[float] = None
    cavitation_risk: bool = False

class PumpRecommendationResponse(BaseModel):
    """Response model for pump recommendation."""
    pump_size: str
    pump_model: str
    pump_type: str
    recommendation_level: str
    operating_point: OperatingPointResponse
    efficiency_rating: str
    npsh_analysis: str
    power_analysis: str
    operating_range_analysis: str
    warnings: List[str]
    notes: List[str]
    trim_recommendations: List[Dict[str, Any]]
    vfd_recommendations: List[Dict[str, Any]]

class PumpDataResponse(BaseModel):
    """Response model for pump data."""
    pump_size: str
    pump_model: str
    pump_type: str
    specs: Dict[str, Any]
    available_rpms: List[int]
    fluid_types: List[str]
    max_hp: int

# Pump Selection Endpoints
@router.post("/select", response_model=List[PumpRecommendationResponse])
async def select_pumps(request: PumpSelectionRequest):
    """
    Find and rank suitable pumps for given requirements.
    
    Returns a list of pump recommendations sorted by suitability,
    with comprehensive engineering analysis for each option.
    """
    try:
        logger.info(f"Pump selection request: {request.required_flow_gpm} GPM @ {request.required_head_ft} ft")
        
        recommendations = pump_selection_service.find_suitable_pumps(
            required_flow_gpm=request.required_flow_gpm,
            required_head_ft=request.required_head_ft,
            fluid_sg=request.fluid_sg,
            npsh_available_ft=request.npsh_available_ft,
            max_power_hp=request.max_power_hp,
            preferred_rpm=request.preferred_rpm,
            fluid_type=request.fluid_type
        )
        
        # Convert to response models
        response_data = []
        for rec in recommendations:
            response_data.append(PumpRecommendationResponse(
                pump_size=rec.pump_size,
                pump_model=rec.pump_model,
                pump_type=rec.pump_type,
                recommendation_level=rec.recommendation_level.value,
                operating_point=OperatingPointResponse(
                    flow_gpm=rec.operating_point.flow_gpm,
                    head_ft=rec.operating_point.head_ft,
                    efficiency_percent=rec.operating_point.efficiency_percent,
                    power_hp=rec.operating_point.power_hp,
                    npsh_required_ft=rec.operating_point.npsh_required_ft,
                    rpm=rec.operating_point.rpm,
                    brake_horsepower=rec.operating_point.brake_horsepower,
                    fluid_horsepower=rec.operating_point.fluid_horsepower,
                    npsh_margin_ft=rec.operating_point.npsh_margin_ft,
                    cavitation_risk=rec.operating_point.cavitation_risk
                ),
                efficiency_rating=rec.efficiency_rating,
                npsh_analysis=rec.npsh_analysis,
                power_analysis=rec.power_analysis,
                operating_range_analysis=rec.operating_range_analysis,
                warnings=rec.warnings,
                notes=rec.notes,
                trim_recommendations=rec.trim_recommendations,
                vfd_recommendations=rec.vfd_recommendations
            ))
        
        logger.info(f"Found {len(response_data)} pump recommendations")
        return response_data
        
    except Exception as e:
        logger.error(f"Error in pump selection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Pump selection failed: {str(e)}")

@router.post("/performance", response_model=OperatingPointResponse)
async def calculate_pump_performance(request: PumpPerformanceRequest):
    """
    Calculate performance for a specific pump at given operating conditions.
    
    Returns detailed operating point data including efficiency, power, and NPSH.
    """
    try:
        logger.info(f"Performance calculation: {request.pump_size} @ {request.flow_gpm} GPM")
        
        pump = pump_data_loader.get_pump_by_size(request.pump_size)
        if not pump:
            raise HTTPException(status_code=404, detail=f"Pump size '{request.pump_size}' not found")
        
        curve_data = pump['curve_data'].get(f'rpm_{request.rpm}')
        if not curve_data:
            raise HTTPException(status_code=400, detail=f"RPM {request.rpm} not available for pump {request.pump_size}")
        
        # Direct performance calculation at specified flow
        try:
            efficiency = pump_selection_service._interpolate_curve(curve_data['efficiency'], request.flow_gpm)
            power_hp = pump_selection_service._interpolate_curve(curve_data['power_required'], request.flow_gpm)
            npsh_req = pump_selection_service._interpolate_curve(curve_data['npsh_required'], request.flow_gpm)
            head_at_flow = pump_selection_service._interpolate_curve(curve_data['head_vs_flow'], request.flow_gpm)
            
            if any(x is None for x in [efficiency, power_hp, npsh_req, head_at_flow]):
                raise HTTPException(status_code=400, detail="Flow rate outside pump curve range")
            
            # Calculate brake horsepower accounting for specific gravity
            brake_hp = power_hp * request.fluid_sg
            
            # Calculate fluid horsepower
            fluid_hp = (request.flow_gpm * head_at_flow * request.fluid_sg) / (3960 * (efficiency / 100))
            
            operating_point = type('OperatingPoint', (), {
                'flow_gpm': request.flow_gpm,
                'head_ft': head_at_flow,
                'efficiency_percent': efficiency,
                'power_hp': power_hp,
                'npsh_required_ft': npsh_req,
                'rpm': request.rpm,
                'brake_horsepower': brake_hp,
                'fluid_horsepower': fluid_hp,
                'npsh_margin_ft': None,
                'cavitation_risk': False
            })()
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Performance calculation failed: {str(e)}")
        
        return OperatingPointResponse(
            flow_gpm=operating_point.flow_gpm,
            head_ft=operating_point.head_ft,
            efficiency_percent=operating_point.efficiency_percent,
            power_hp=operating_point.power_hp,
            npsh_required_ft=operating_point.npsh_required_ft,
            rpm=operating_point.rpm,
            brake_horsepower=operating_point.brake_horsepower,
            fluid_horsepower=operating_point.fluid_horsepower,
            npsh_margin_ft=operating_point.npsh_margin_ft,
            cavitation_risk=operating_point.cavitation_risk
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating pump performance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Performance calculation failed: {str(e)}")

@router.post("/system-curve", response_model=Dict[str, Any])
async def analyze_system_curve(request: SystemCurveRequest):
    """
    Calculate intersection points between pump curve and system curve.
    
    Returns operating points where pump curve intersects with system resistance curve.
    """
    try:
        logger.info(f"System curve analysis: {request.pump_size} @ {request.rpm} RPM")
        
        intersections = pump_selection_service.calculate_system_curve_intersection(
            pump_size=request.pump_size,
            rpm=request.rpm,
            static_head_ft=request.static_head_ft,
            friction_loss_coefficient=request.friction_loss_coefficient
        )
        
        if not intersections:
            return {"message": "No intersection points found - check system curve parameters", "intersections": []}
        
        return {"message": "Intersection points found", "intersections": intersections}
        
    except Exception as e:
        logger.error(f"Error in system curve analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"System curve analysis failed: {str(e)}")

# Health and Validation Endpoints (MUST come before parameterized routes)
@router.get("/health", response_model=Dict[str, Any])
async def pump_service_health():
    """
    Check pump service health and data integrity.
    
    Returns validation results and service status.
    """
    try:
        validation_results = pump_data_loader.validate_data_structure()
        
        health_status = {
            "status": "healthy" if validation_results['valid'] else "unhealthy",
            "pump_count": validation_results['pump_count'],
            "available_sizes": validation_results['sizes'],
            "available_types": validation_results['types'],
            "validation_errors": validation_results.get('errors', []),
            "service_version": "1.0.0",
            "last_updated": "2025-07-13"
        }
        
        logger.info("Pump service health check completed")
        return health_status
        
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.get("/search", response_model=List[PumpDataResponse])
async def search_pumps(
    flow_min: Optional[float] = Query(None, description="Minimum flow capacity"),
    flow_max: Optional[float] = Query(None, description="Maximum flow capacity"),
    head_min: Optional[float] = Query(None, description="Minimum head capacity"),
    head_max: Optional[float] = Query(None, description="Maximum head capacity"),
    pump_type: Optional[str] = Query(None, description="Pump type filter"),
    fluid_type: Optional[str] = Query(None, description="Fluid type filter")
):
    """
    Search pumps by performance criteria.
    
    Returns pumps that meet the specified flow, head, type, and fluid criteria.
    """
    try:
        pumps = pump_data_loader.load_transfer_pumps()
        filtered_pumps = []
        
        for pump in pumps:
            # Type filters
            if pump_type and pump['type'] != pump_type:
                continue
            if fluid_type and fluid_type not in pump['specs']['fluid_types']:
                continue
            
            # Performance filters (check against curve data)
            if any([flow_min, flow_max, head_min, head_max]):
                meets_criteria = False
                for rpm_key, curve_data in pump['curve_data'].items():
                    head_curve = curve_data['head_vs_flow']
                    flows = [point['flow'] for point in head_curve]
                    heads = [point['head'] for point in head_curve]
                    
                    pump_flow_min, pump_flow_max = min(flows), max(flows)
                    pump_head_min, pump_head_max = min(heads), max(heads)
                    
                    # Check if pump capabilities overlap with requirements
                    if flow_min and pump_flow_max < flow_min:
                        continue
                    if flow_max and pump_flow_min > flow_max:
                        continue
                    if head_min and pump_head_max < head_min:
                        continue
                    if head_max and pump_head_min > head_max:
                        continue
                    
                    meets_criteria = True
                    break
                
                if not meets_criteria:
                    continue
            
            # Add to results
            available_rpms = [int(rpm_key.split('_')[1]) for rpm_key in pump['curve_data'].keys()]
            filtered_pumps.append(PumpDataResponse(
                pump_size=pump['size'],
                pump_model=pump['model'],
                pump_type=pump['type'],
                specs=pump['specs'],
                available_rpms=sorted(available_rpms),
                fluid_types=pump['specs']['fluid_types'],
                max_hp=pump['specs']['max_hp']
            ))
        
        logger.info(f"Search returned {len(filtered_pumps)} pumps")
        return filtered_pumps
        
    except Exception as e:
        logger.error(f"Error in pump search: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Pump search failed: {str(e)}")

# Pump Data Endpoints
@router.get("/list", response_model=List[PumpDataResponse])
async def list_available_pumps():
    """
    Get list of all available pumps with basic specifications.
    
    Returns pump inventory with sizes, types, and key specifications.
    """
    try:
        pumps = pump_data_loader.load_transfer_pumps()
        
        response_data = []
        for pump in pumps:
            # Extract available RPMs from curve data
            available_rpms = [int(rpm_key.split('_')[1]) for rpm_key in pump['curve_data'].keys()]
            
            response_data.append(PumpDataResponse(
                pump_size=pump['size'],
                pump_model=pump['model'],
                pump_type=pump['type'],
                specs=pump['specs'],
                available_rpms=sorted(available_rpms),
                fluid_types=pump['specs']['fluid_types'],
                max_hp=pump['specs']['max_hp']
            ))
        
        logger.info(f"Listed {len(response_data)} available pumps")
        return response_data
        
    except Exception as e:
        logger.error(f"Error listing pumps: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list pumps: {str(e)}")

@router.get("/sizes", response_model=List[str])
async def get_pump_sizes():
    """
    Get list of available pump sizes.
    
    Returns simple list of pump size strings (e.g., ['2x3-13', '3x4-13', ...]).
    """
    try:
        sizes = pump_data_loader.get_all_pump_sizes()
        logger.info(f"Retrieved {len(sizes)} pump sizes")
        return sizes
        
    except Exception as e:
        logger.error(f"Error getting pump sizes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get pump sizes: {str(e)}")

@router.get("/types", response_model=List[str])
async def get_pump_types():
    """
    Get list of available pump types.
    
    Returns unique pump types (e.g., ['centrifugal_ansi_transfer', 'centrifugal_ansi_charge']).
    """
    try:
        pumps = pump_data_loader.load_transfer_pumps()
        types = list(set(pump['type'] for pump in pumps))
        logger.info(f"Retrieved {len(types)} pump types")
        return types
        
    except Exception as e:
        logger.error(f"Error getting pump types: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get pump types: {str(e)}")

# Parameterized route MUST come last to avoid conflicts
@router.get("/{pump_size}", response_model=Dict[str, Any])
async def get_pump_details(pump_size: str):
    """
    Get detailed specifications and curve data for a specific pump.
    
    Returns complete pump data including performance curves for all RPM options.
    """
    try:
        pump = pump_data_loader.get_pump_by_size(pump_size)
        if not pump:
            raise HTTPException(status_code=404, detail=f"Pump size '{pump_size}' not found")
        
        logger.info(f"Retrieved details for pump {pump_size}")
        return pump
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pump details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get pump details: {str(e)}")
