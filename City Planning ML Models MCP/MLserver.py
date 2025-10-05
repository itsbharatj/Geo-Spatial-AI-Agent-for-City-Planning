#!/usr/bin/env python3
"""
City Planning MCP Server
A Model Context Protocol server providing ML and statistical models for urban planning
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import numpy as np
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.cluster import DBSCAN
from sklearn.linear_model import Ridge
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.seasonal import seasonal_decompose
import pandas as pd
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("city-planning-mcp")

class CityPlanningModels:
    """Collection of ML and statistical models for city planning"""
    
    def __init__(self):
        self.models = {}
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize base model structures"""
        # These will be trained on-demand with actual data
        self.models['traffic_predictor'] = None
        self.models['aqi_forecaster'] = None
        self.models['growth_predictor'] = None
        self.models['transit_optimizer'] = None
        self.models['hotspot_detector'] = None
        self.models['demand_forecaster'] = None
        self.models['land_use_classifier'] = None
    
    # Model 1: Traffic Flow Prediction
    async def predict_traffic_flow(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predicts traffic flow and congestion using Random Forest
        
        Input format:
        {
            "historical_traffic": [[timestamp, flow_rate, speed, occupancy], ...],
            "weather_conditions": {"temperature": float, "precipitation": float, "visibility": float},
            "events": [{"type": str, "location": str, "time": str}, ...],
            "prediction_horizon": int (hours)
        }
        """
        try:
            # Convert historical data to features
            historical = np.array(data.get('historical_traffic', []))
            if len(historical) < 10:
                return {"error": "Insufficient historical data (need at least 10 data points)"}
            
            # Extract features
            X = historical[:, 1:4]  # flow_rate, speed, occupancy
            y = historical[:, 1]     # predicting flow_rate
            
            # Add weather features if available
            weather = data.get('weather_conditions', {})
            weather_features = np.array([
                weather.get('temperature', 20),
                weather.get('precipitation', 0),
                weather.get('visibility', 10)
            ])
            
            # Train Random Forest model
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X, y)
            
            # Make predictions
            horizon = data.get('prediction_horizon', 1)
            predictions = []
            
            last_features = X[-1].reshape(1, -1)
            for h in range(horizon):
                pred = model.predict(last_features)[0]
                predictions.append({
                    "hour_ahead": h + 1,
                    "predicted_flow": float(pred),
                    "congestion_level": self._calculate_congestion_level(pred)
                })
            
            return {
                "model": "Random Forest Traffic Predictor",
                "predictions": predictions,
                "feature_importance": {
                    "flow_rate": float(model.feature_importances_[0]),
                    "speed": float(model.feature_importances_[1]),
                    "occupancy": float(model.feature_importances_[2])
                },
                "confidence_score": float(model.score(X, y))
            }
            
        except Exception as e:
            return {"error": f"Traffic prediction failed: {str(e)}"}
    
    def _calculate_congestion_level(self, flow_rate: float) -> str:
        """Calculate congestion level from flow rate"""
        if flow_rate < 30:
            return "low"
        elif flow_rate < 60:
            return "moderate"
        elif flow_rate < 80:
            return "high"
        else:
            return "severe"
    
    # Model 2: Air Quality Index Forecasting
    async def forecast_air_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Forecasts AQI using ARIMA time series model
        
        Input format:
        {
            "historical_aqi": [[timestamp, aqi_value, pm25, pm10, o3, no2], ...],
            "weather_forecast": {"temperature": float, "humidity": float, "wind_speed": float},
            "forecast_days": int
        }
        """
        try:
            historical = data.get('historical_aqi', [])
            if len(historical) < 30:
                return {"error": "Need at least 30 days of historical AQI data"}
            
            # Extract AQI values
            aqi_values = [h[1] for h in historical]
            
            # Fit ARIMA model
            model = ARIMA(aqi_values, order=(2, 1, 2))
            fitted_model = model.fit()
            
            # Forecast
            forecast_days = data.get('forecast_days', 7)
            forecast = fitted_model.forecast(steps=forecast_days)
            
            # Calculate health recommendations
            recommendations = []
            for aqi in forecast:
                recommendations.append(self._get_aqi_recommendation(aqi))
            
            return {
                "model": "ARIMA AQI Forecaster",
                "forecasts": [
                    {
                        "day": i + 1,
                        "predicted_aqi": float(aqi),
                        "category": self._get_aqi_category(aqi),
                        "health_recommendation": rec
                    }
                    for i, (aqi, rec) in enumerate(zip(forecast, recommendations))
                ],
                "model_metrics": {
                    "aic": float(fitted_model.aic),
                    "bic": float(fitted_model.bic),
                    "mae": float(np.mean(np.abs(fitted_model.resid)))
                }
            }
            
        except Exception as e:
            return {"error": f"AQI forecasting failed: {str(e)}"}
    
    def _get_aqi_category(self, aqi: float) -> str:
        """Get AQI category based on value"""
        if aqi <= 50:
            return "Good"
        elif aqi <= 100:
            return "Moderate"
        elif aqi <= 150:
            return "Unhealthy for Sensitive Groups"
        elif aqi <= 200:
            return "Unhealthy"
        elif aqi <= 300:
            return "Very Unhealthy"
        else:
            return "Hazardous"
    
    def _get_aqi_recommendation(self, aqi: float) -> str:
        """Get health recommendation based on AQI"""
        if aqi <= 50:
            return "Air quality is satisfactory"
        elif aqi <= 100:
            return "Unusually sensitive people should consider limiting prolonged outdoor exertion"
        elif aqi <= 150:
            return "People with respiratory or heart conditions should limit prolonged outdoor exertion"
        elif aqi <= 200:
            return "Everyone should avoid prolonged outdoor exertion"
        elif aqi <= 300:
            return "Everyone should avoid all outdoor exertion"
        else:
            return "Everyone should remain indoors"
    
    # Model 3: Urban Growth Prediction
    async def predict_urban_growth(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predicts urban expansion and population growth using Ridge Regression
        
        Input format:
        {
            "historical_data": [[year, population, built_area, gdp, employment_rate], ...],
            "infrastructure_plans": [{"type": str, "capacity": int, "year": int}, ...],
            "projection_years": int
        }
        """
        try:
            historical = np.array(data.get('historical_data', []))
            if len(historical) < 5:
                return {"error": "Need at least 5 years of historical data"}
            
            # Prepare features and target
            X = historical[:, [0, 2, 3, 4]]  # year, built_area, gdp, employment
            y = historical[:, 1]  # population
            
            # Normalize year feature
            X[:, 0] = X[:, 0] - X[0, 0]
            
            # Train Ridge Regression model
            model = Ridge(alpha=1.0)
            model.fit(X, y)
            
            # Make projections
            projection_years = data.get('projection_years', 5)
            projections = []
            
            last_row = X[-1].copy()
            for year in range(1, projection_years + 1):
                last_row[0] += 1  # increment year
                # Simple growth assumptions for other features
                last_row[1] *= 1.02  # 2% built area growth
                last_row[2] *= 1.03  # 3% GDP growth
                
                pop_prediction = model.predict(last_row.reshape(1, -1))[0]
                
                projections.append({
                    "year": int(historical[-1, 0] + year),
                    "predicted_population": int(pop_prediction),
                    "growth_rate": float((pop_prediction / historical[-1, 1] - 1) * 100),
                    "infrastructure_needs": self._calculate_infrastructure_needs(pop_prediction)
                })
            
            return {
                "model": "Ridge Regression Urban Growth Predictor",
                "projections": projections,
                "model_coefficients": {
                    "year_impact": float(model.coef_[0]),
                    "built_area_impact": float(model.coef_[1]),
                    "gdp_impact": float(model.coef_[2]),
                    "employment_impact": float(model.coef_[3])
                },
                "r_squared": float(model.score(X, y))
            }
            
        except Exception as e:
            return {"error": f"Urban growth prediction failed: {str(e)}"}
    
    def _calculate_infrastructure_needs(self, population: int) -> Dict[str, int]:
        """Calculate infrastructure needs based on population"""
        return {
            "schools_needed": int(population / 5000),
            "hospitals_needed": int(population / 50000),
            "parks_needed": int(population / 10000),
            "water_capacity_mld": int(population * 0.15 / 1000)  # 150 liters per person per day
        }
    
    # Model 4: Public Transit Optimization
    async def optimize_transit_routes(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimizes public transit routes using clustering (DBSCAN)
        
        Input format:
        {
            "demand_points": [[lat, lon, demand_weight], ...],
            "existing_stops": [[lat, lon, capacity], ...],
            "constraints": {"max_distance": float, "min_demand": float}
        }
        """
        try:
            demand_points = np.array(data.get('demand_points', []))
            if len(demand_points) < 10:
                return {"error": "Need at least 10 demand points"}
            
            # Extract coordinates and weights
            coords = demand_points[:, :2]
            weights = demand_points[:, 2]
            
            # Apply DBSCAN clustering
            constraints = data.get('constraints', {})
            eps = constraints.get('max_distance', 0.01)  # ~1km in lat/lon
            min_samples = max(3, int(len(coords) * 0.05))
            
            clustering = DBSCAN(eps=eps, min_samples=min_samples)
            clusters = clustering.fit_predict(coords, sample_weight=weights)
            
            # Calculate optimal stop locations for each cluster
            unique_clusters = set(clusters[clusters != -1])
            optimal_stops = []
            
            for cluster_id in unique_clusters:
                cluster_points = coords[clusters == cluster_id]
                cluster_weights = weights[clusters == cluster_id]
                
                # Weighted centroid
                centroid = np.average(cluster_points, axis=0, weights=cluster_weights)
                total_demand = np.sum(cluster_weights)
                
                optimal_stops.append({
                    "cluster_id": int(cluster_id),
                    "location": {
                        "lat": float(centroid[0]),
                        "lon": float(centroid[1])
                    },
                    "expected_demand": float(total_demand),
                    "coverage_area": float(self._calculate_coverage_area(cluster_points)),
                    "suggested_frequency": self._suggest_frequency(total_demand)
                })
            
            # Calculate route efficiency metrics
            existing_stops = data.get('existing_stops', [])
            efficiency = self._calculate_route_efficiency(optimal_stops, existing_stops)
            
            return {
                "model": "DBSCAN Transit Route Optimizer",
                "optimal_stops": optimal_stops,
                "route_metrics": {
                    "total_clusters": len(unique_clusters),
                    "unclustered_points": int(np.sum(clusters == -1)),
                    "average_cluster_size": float(len(coords[clusters != -1]) / len(unique_clusters)),
                    "coverage_efficiency": efficiency
                },
                "recommendations": self._generate_transit_recommendations(optimal_stops)
            }
            
        except Exception as e:
            return {"error": f"Transit optimization failed: {str(e)}"}
    
    def _calculate_coverage_area(self, points: np.ndarray) -> float:
        """Calculate coverage area of points in sq km"""
        if len(points) < 3:
            return 0.0
        # Simplified area calculation using bounding box
        lat_range = np.ptp(points[:, 0]) * 111  # km per degree latitude
        lon_range = np.ptp(points[:, 1]) * 111 * np.cos(np.radians(np.mean(points[:, 0])))
        return lat_range * lon_range
    
    def _suggest_frequency(self, demand: float) -> str:
        """Suggest service frequency based on demand"""
        if demand < 100:
            return "Every 30 minutes"
        elif demand < 500:
            return "Every 15 minutes"
        elif demand < 1000:
            return "Every 10 minutes"
        else:
            return "Every 5 minutes"
    
    def _calculate_route_efficiency(self, optimal: List, existing: List) -> float:
        """Calculate route efficiency score"""
        if not existing:
            return 100.0
        # Simplified efficiency calculation
        return min(100.0, (len(optimal) / max(len(existing), 1)) * 100)
    
    def _generate_transit_recommendations(self, stops: List) -> List[str]:
        """Generate transit recommendations"""
        recommendations = []
        
        if len(stops) > 20:
            recommendations.append("Consider implementing express routes for high-demand corridors")
        
        high_demand = [s for s in stops if s['expected_demand'] > 500]
        if high_demand:
            recommendations.append(f"Prioritize {len(high_demand)} high-demand stops for immediate implementation")
        
        low_coverage = [s for s in stops if s['coverage_area'] < 1.0]
        if low_coverage:
            recommendations.append(f"Add feeder routes for {len(low_coverage)} areas with limited coverage")
        
        return recommendations
    
    # Model 5: Crime Hotspot Detection
    async def detect_crime_hotspots(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detects anomalous crime patterns using Isolation Forest
        
        Input format:
        {
            "crime_incidents": [[lat, lon, timestamp, crime_type, severity], ...],
            "temporal_window": int (days),
            "contamination": float (expected anomaly rate)
        }
        """
        try:
            incidents = data.get('crime_incidents', [])
            if len(incidents) < 50:
                return {"error": "Need at least 50 crime incidents for analysis"}
            
            # Prepare features
            incident_array = np.array(incidents)
            coords = incident_array[:, :2].astype(float)
            
            # Add temporal features
            timestamps = incident_array[:, 2]
            # Convert to hours since first incident (simplified)
            time_features = np.arange(len(timestamps)).reshape(-1, 1)
            
            # Combine spatial and temporal features
            features = np.hstack([coords, time_features])
            
            # Train Isolation Forest
            contamination = data.get('contamination', 0.1)
            model = IsolationForest(contamination=contamination, random_state=42)
            predictions = model.fit_predict(features)
            
            # Identify hotspots (anomalies)
            hotspot_indices = np.where(predictions == -1)[0]
            hotspots = []
            
            for idx in hotspot_indices:
                hotspots.append({
                    "location": {
                        "lat": float(coords[idx, 0]),
                        "lon": float(coords[idx, 1])
                    },
                    "anomaly_score": float(model.score_samples([features[idx]])[0]),
                    "incident_type": str(incident_array[idx, 3]),
                    "severity": int(incident_array[idx, 4]),
                    "risk_level": self._calculate_risk_level(model.score_samples([features[idx]])[0])
                })
            
            # Calculate prevention strategies
            strategies = self._generate_prevention_strategies(hotspots)
            
            return {
                "model": "Isolation Forest Crime Hotspot Detector",
                "hotspots": hotspots[:20],  # Top 20 hotspots
                "statistics": {
                    "total_incidents": len(incidents),
                    "hotspots_detected": len(hotspots),
                    "anomaly_rate": float(len(hotspots) / len(incidents)),
                    "high_risk_areas": sum(1 for h in hotspots if h['risk_level'] == 'high')
                },
                "prevention_strategies": strategies
            }
            
        except Exception as e:
            return {"error": f"Crime hotspot detection failed: {str(e)}"}
    
    def _calculate_risk_level(self, anomaly_score: float) -> str:
        """Calculate risk level from anomaly score"""
        if anomaly_score < -0.5:
            return "high"
        elif anomaly_score < -0.3:
            return "medium"
        else:
            return "low"
    
    def _generate_prevention_strategies(self, hotspots: List) -> List[str]:
        """Generate crime prevention strategies"""
        strategies = []
        
        high_risk = [h for h in hotspots if h['risk_level'] == 'high']
        if high_risk:
            strategies.append(f"Deploy additional patrols to {len(high_risk)} high-risk areas")
        
        violent_crimes = [h for h in hotspots if h.get('severity', 0) > 3]
        if violent_crimes:
            strategies.append("Install CCTV cameras and improve lighting in violent crime hotspots")
        
        strategies.append("Implement community policing programs in identified hotspot areas")
        strategies.append("Coordinate with social services for intervention programs")
        
        return strategies
    
    # Model 6: Energy Demand Forecasting
    async def forecast_energy_demand(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Forecasts energy demand using seasonal decomposition and trend analysis
        
        Input format:
        {
            "historical_demand": [[timestamp, demand_mw, temperature, day_type], ...],
            "weather_forecast": [{"date": str, "temp_high": float, "temp_low": float}, ...],
            "forecast_horizon": int (days)
        }
        """
        try:
            historical = data.get('historical_demand', [])
            if len(historical) < 90:
                return {"error": "Need at least 90 days of historical demand data"}
            
            # Extract demand values
            demand_values = [h[1] for h in historical]
            temperatures = [h[2] for h in historical]
            
            # Create pandas series for seasonal decomposition
            demand_series = pd.Series(demand_values)
            
            # Perform seasonal decomposition
            decomposition = seasonal_decompose(demand_series, model='additive', period=7)
            
            # Calculate temperature sensitivity
            temp_correlation = np.corrcoef(demand_values, temperatures)[0, 1]
            
            # Simple forecast based on trend and seasonality
            forecast_horizon = data.get('forecast_horizon', 7)
            forecasts = []
            
            trend_slope = np.polyfit(range(len(demand_values)), demand_values, 1)[0]
            last_value = demand_values[-1]
            
            for day in range(forecast_horizon):
                # Simple linear projection with seasonal adjustment
                base_forecast = last_value + (trend_slope * day)
                seasonal_adj = decomposition.seasonal.iloc[day % 7]
                
                forecast_value = base_forecast + seasonal_adj
                
                forecasts.append({
                    "day": day + 1,
                    "predicted_demand_mw": float(forecast_value),
                    "peak_hours": self._identify_peak_hours(forecast_value),
                    "recommended_capacity": float(forecast_value * 1.15)  # 15% safety margin
                })
            
            # Calculate grid recommendations
            recommendations = self._generate_grid_recommendations(forecasts, temp_correlation)
            
            return {
                "model": "Seasonal Decomposition Energy Forecaster",
                "forecasts": forecasts,
                "demand_patterns": {
                    "trend_direction": "increasing" if trend_slope > 0 else "decreasing",
                    "trend_rate_mw_per_day": float(trend_slope),
                    "temperature_sensitivity": float(temp_correlation),
                    "weekly_seasonality_strength": float(np.std(decomposition.seasonal))
                },
                "grid_recommendations": recommendations
            }
            
        except Exception as e:
            return {"error": f"Energy demand forecasting failed: {str(e)}"}
    
    def _identify_peak_hours(self, daily_demand: float) -> List[str]:
        """Identify likely peak hours based on demand level"""
        if daily_demand > 1000:
            return ["07:00-09:00", "17:00-20:00"]
        else:
            return ["08:00-09:00", "18:00-19:00"]
    
    def _generate_grid_recommendations(self, forecasts: List, temp_correlation: float) -> List[str]:
        """Generate grid management recommendations"""
        recommendations = []
        
        max_demand = max(f['predicted_demand_mw'] for f in forecasts)
        if max_demand > 1500:
            recommendations.append("Prepare reserve capacity for peak demand periods")
        
        if abs(temp_correlation) > 0.7:
            recommendations.append("Implement dynamic pricing based on temperature forecasts")
        
        recommendations.append("Consider demand response programs during peak hours")
        recommendations.append("Optimize renewable energy integration during low-demand periods")
        
        return recommendations
    
    # Model 7: Land Use Classification and Optimization
    async def classify_land_use(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classifies and optimizes land use patterns
        
        Input format:
        {
            "parcels": [[lat, lon, current_use, size_sqm, value], ...],
            "zoning_rules": {"residential": float, "commercial": float, "industrial": float, "green": float},
            "development_goals": {"housing_units": int, "jobs": int, "green_space_sqm": int}
        }
        """
        try:
            parcels = data.get('parcels', [])
            if len(parcels) < 20:
                return {"error": "Need at least 20 land parcels for analysis"}
            
            parcel_array = np.array(parcels)
            coords = parcel_array[:, :2].astype(float)
            sizes = parcel_array[:, 3].astype(float)
            values = parcel_array[:, 4].astype(float)
            
            # Calculate land use metrics
            current_uses = parcel_array[:, 2]
            use_distribution = pd.Series(current_uses).value_counts().to_dict()
            
            # Simple optimization based on goals
            goals = data.get('development_goals', {})
            zoning = data.get('zoning_rules', {})
            
            recommendations = []
            total_area = np.sum(sizes)
            
            # Calculate optimal distribution
            optimal_distribution = {
                "residential": goals.get('housing_units', 1000) * 50 / total_area,  # 50sqm per unit
                "commercial": goals.get('jobs', 500) * 20 / total_area,  # 20sqm per job
                "green": goals.get('green_space_sqm', 10000) / total_area,
                "industrial": 0.1  # Default 10%
            }
            
            # Normalize to sum to 1
            total_ratio = sum(optimal_distribution.values())
            optimal_distribution = {k: v/total_ratio for k, v in optimal_distribution.items()}
            
            # Calculate conversion recommendations
            conversions = []
            for use_type, target_ratio in optimal_distribution.items():
                current_ratio = use_distribution.get(use_type, 0) / len(parcels)
                if target_ratio > current_ratio * 1.1:  # Need 10% more
                    conversions.append({
                        "convert_to": use_type,
                        "parcels_needed": int((target_ratio - current_ratio) * len(parcels)),
                        "area_needed_sqm": float((target_ratio - current_ratio) * total_area)
                    })
            
            # Calculate sustainability metrics
            sustainability_score = self._calculate_sustainability_score(
                use_distribution, optimal_distribution, coords
            )
            
            return {
                "model": "Land Use Classifier and Optimizer",
                "current_distribution": {
                    k: {"parcels": int(v), "percentage": float(v/len(parcels)*100)}
                    for k, v in use_distribution.items()
                },
                "optimal_distribution": {
                    k: {"target_percentage": float(v*100)}
                    for k, v in optimal_distribution.items()
                },
                "conversion_recommendations": conversions,
                "metrics": {
                    "total_area_sqm": float(total_area),
                    "average_parcel_size": float(np.mean(sizes)),
                    "land_value_per_sqm": float(np.sum(values) / total_area),
                    "sustainability_score": sustainability_score
                },
                "development_priorities": self._generate_development_priorities(conversions, goals)
            }
            
        except Exception as e:
            return {"error": f"Land use classification failed: {str(e)}"}
    
    def _calculate_sustainability_score(self, current: Dict, optimal: Dict, coords: np.ndarray) -> float:
        """Calculate sustainability score for land use"""
        # Simplified scoring based on green space and mixed use
        green_ratio = current.get('green', 0) / max(sum(current.values()), 1)
        diversity = len(current) / 4  # Diversity of land uses
        
        # Spatial clustering (lower is better for mixed use)
        clustering = DBSCAN(eps=0.01, min_samples=3)
        clusters = clustering.fit_predict(coords)
        cluster_diversity = len(set(clusters)) / len(coords)
        
        score = (green_ratio * 40 + diversity * 30 + cluster_diversity * 30)
        return min(100, max(0, score))
    
    def _generate_development_priorities(self, conversions: List, goals: Dict) -> List[str]:
        """Generate development priorities"""
        priorities = []
        
        if any(c['convert_to'] == 'residential' for c in conversions):
            priorities.append("Priority 1: Increase residential zoning to meet housing targets")
        
        if goals.get('green_space_sqm', 0) > 0:
            priorities.append("Priority 2: Preserve and expand green spaces for sustainability")
        
        priorities.append("Priority 3: Ensure mixed-use development for walkable neighborhoods")
        priorities.append("Priority 4: Create transit-oriented development zones")
        
        return priorities


# MCP Server Implementation
class CityPlanningMCPServer(Server):
    def __init__(self):
        super().__init__("city-planning-mcp")
        self.models = CityPlanningModels()
        
    async def handle_initialize(self, params: InitializationOptions) -> None:
        logger.info("Initializing City Planning MCP Server")
        
    async def handle_list_tools(self) -> List[types.Tool]:
        return [
            types.Tool(
                name="predict_traffic_flow",
                description="Predicts traffic flow and congestion using Random Forest. Requires historical traffic data, weather conditions, and events.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "historical_traffic": {
                            "type": "array",
                            "description": "Array of [timestamp, flow_rate, speed, occupancy]"
                        },
                        "weather_conditions": {
                            "type": "object",
                            "properties": {
                                "temperature": {"type": "number"},
                                "precipitation": {"type": "number"},
                                "visibility": {"type": "number"}
                            }
                        },
                        "events": {"type": "array"},
                        "prediction_horizon": {"type": "integer", "default": 1}
                    },
                    "required": ["historical_traffic"]
                }
            ),
            types.Tool(
                name="forecast_air_quality",
                description="Forecasts AQI using ARIMA time series model. Requires historical AQI data and weather forecast.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "historical_aqi": {
                            "type": "array",
                            "description": "Array of [timestamp, aqi_value, pm25, pm10, o3, no2]"
                        },
                        "weather_forecast": {"type": "object"},
                        "forecast_days": {"type": "integer", "default": 7}
                    },
                    "required": ["historical_aqi"]
                }
            ),
            types.Tool(
                name="predict_urban_growth",
                description="Predicts urban expansion and population growth using Ridge Regression. Requires historical population, economic, and infrastructure data.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "historical_data": {
                            "type": "array",
                            "description": "Array of [year, population, built_area, gdp, employment_rate]"
                        },
                        "infrastructure_plans": {"type": "array"},
                        "projection_years": {"type": "integer", "default": 5}
                    },
                    "required": ["historical_data"]
                }
            ),
            types.Tool(
                name="optimize_transit_routes",
                description="Optimizes public transit routes using DBSCAN clustering. Requires demand points and constraints.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "demand_points": {
                            "type": "array",
                            "description": "Array of [lat, lon, demand_weight]"
                        },
                        "existing_stops": {"type": "array"},
                        "constraints": {"type": "object"}
                    },
                    "required": ["demand_points"]
                }
            ),
            types.Tool(
                name="detect_crime_hotspots",
                description="Detects anomalous crime patterns using Isolation Forest. Requires crime incident data.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "crime_incidents": {
                            "type": "array",
                            "description": "Array of [lat, lon, timestamp, crime_type, severity]"
                        },
                        "temporal_window": {"type": "integer"},
                        "contamination": {"type": "number", "default": 0.1}
                    },
                    "required": ["crime_incidents"]
                }
            ),
            types.Tool(
                name="forecast_energy_demand",
                description="Forecasts energy demand using seasonal decomposition. Requires historical demand data.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "historical_demand": {
                            "type": "array",
                            "description": "Array of [timestamp, demand_mw, temperature, day_type]"
                        },
                        "weather_forecast": {"type": "array"},
                        "forecast_horizon": {"type": "integer", "default": 7}
                    },
                    "required": ["historical_demand"]
                }
            ),
            types.Tool(
                name="classify_land_use",
                description="Classifies and optimizes land use patterns. Requires parcel data and development goals.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "parcels": {
                            "type": "array",
                            "description": "Array of [lat, lon, current_use, size_sqm, value]"
                        },
                        "zoning_rules": {"type": "object"},
                        "development_goals": {"type": "object"}
                    },
                    "required": ["parcels"]
                }
            )
        ]
    
    async def handle_call_tool(
        self, name: str, arguments: Optional[Dict[str, Any]]
    ) -> List[types.TextContent]:
        logger.info(f"Calling tool: {name}")
        
        try:
            if name == "predict_traffic_flow":
                result = await self.models.predict_traffic_flow(arguments or {})
            elif name == "forecast_air_quality":
                result = await self.models.forecast_air_quality(arguments or {})
            elif name == "predict_urban_growth":
                result = await self.models.predict_urban_growth(arguments or {})
            elif name == "optimize_transit_routes":
                result = await self.models.optimize_transit_routes(arguments or {})
            elif name == "detect_crime_hotspots":
                result = await self.models.detect_crime_hotspots(arguments or {})
            elif name == "forecast_energy_demand":
                result = await self.models.forecast_energy_demand(arguments or {})
            elif name == "classify_land_use":
                result = await self.models.classify_land_use(arguments or {})
            else:
                result = {"error": f"Unknown tool: {name}"}
            
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": str(e)}, indent=2)
            )]


async def main():
    """Main entry point for the MCP server"""
    server = CityPlanningMCPServer()
    
    # Run the server using stdio transport
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="city-planning-mcp",
                server_version="1.0.0"
            )
        )

if __name__ == "__main__":
    asyncio.run(main())