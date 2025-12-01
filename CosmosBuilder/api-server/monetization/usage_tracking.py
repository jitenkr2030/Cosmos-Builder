"""
Usage Tracking System for CosmosBuilder
Author: MiniMax Agent
Date: 2025-11-27

Comprehensive usage tracking and billing system for CosmosBuilder platform.
Tracks API requests, deployments, storage, bandwidth, and other billable metrics.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import logging
import json
from decimal import Decimal
from dataclasses import dataclass

from .models import db, UsageRecord, BillingAlert, Subscription
from .billing import billing_manager
from ..utils.decorators import rate_limit
from ..utils.logging import get_logger

logger = get_logger(__name__)
usage_bp = Blueprint('usage', __name__, url_prefix='/api/usage')

@dataclass
class UsageLimit:
    """Usage limit configuration"""
    metric_name: str
    display_name: str
    limit: Union[int, float]
    unit: str
    warning_threshold: float  # Percentage for warnings
    overage_rate: Optional[Decimal] = None

@dataclass
class UsageSummary:
    """Usage summary for a user"""
    period_start: datetime
    period_end: datetime
    metrics: Dict[str, Dict[str, Union[int, float, Decimal]]]
    limits: Dict[str, UsageLimit]
    warnings: List[Dict]
    totals: Dict[str, Union[int, float]]

class UsageTracker:
    """Central usage tracking manager"""
    
    def __init__(self):
        self.logger = logger
        self._setup_usage_limits()
    
    def _setup_usage_limits(self):
        """Set up usage limits for different subscription plans"""
        self.usage_limits = {
            'starter': [
                UsageLimit('api_requests', 'API Requests', 10000, 'requests', 0.8),
                UsageLimit('chain_deployments', 'Chain Deployments', 100, 'deployments', 0.8, Decimal('10.00')),
                UsageLimit('storage_gb', 'Storage', 10, 'GB', 0.8, Decimal('0.05')),
                UsageLimit('bandwidth_gb', 'Bandwidth', 100, 'GB', 0.8, Decimal('0.10')),
                UsageLimit('computing_hours', 'Computing Hours', 24, 'hours', 0.8, Decimal('5.00'))
            ],
            'professional': [
                UsageLimit('api_requests', 'API Requests', 100000, 'requests', 0.8),
                UsageLimit('chain_deployments', 'Chain Deployments', 500, 'deployments', 0.8, Decimal('10.00')),
                UsageLimit('storage_gb', 'Storage', 50, 'GB', 0.8, Decimal('0.05')),
                UsageLimit('bandwidth_gb', 'Bandwidth', 500, 'GB', 0.8, Decimal('0.10')),
                UsageLimit('computing_hours', 'Computing Hours', 120, 'hours', 0.8, Decimal('5.00'))
            ],
            'enterprise': [
                UsageLimit('api_requests', 'API Requests', 1000000, 'requests', 0.7),
                UsageLimit('chain_deployments', 'Chain Deployments', -1, 'deployments', 0.8),
                UsageLimit('storage_gb', 'Storage', 500, 'GB', 0.7, Decimal('0.03')),
                UsageLimit('bandwidth_gb', 'Bandwidth', 5000, 'GB', 0.7, Decimal('0.05')),
                UsageLimit('computing_hours', 'Computing Hours', 720, 'hours', 0.7, Decimal('3.00'))
            ],
            'sovereign': [
                UsageLimit('api_requests', 'API Requests', -1, 'requests', 0.8),
                UsageLimit('chain_deployments', 'Chain Deployments', -1, 'deployments', 0.8),
                UsageLimit('storage_gb', 'Storage', -1, 'GB', 0.8),
                UsageLimit('bandwidth_gb', 'Bandwidth', -1, 'GB', 0.8),
                UsageLimit('computing_hours', 'Computing Hours', -1, 'hours', 0.8)
            ]
        }
    
    def track_usage(self, user_id: str, metric_name: str, value: Union[int, float], 
                   metadata: Optional[Dict] = None, timestamp: Optional[datetime] = None) -> bool:
        """Track usage for a user"""
        try:
            if timestamp is None:
                timestamp = datetime.utcnow()
            
            usage_record = UsageRecord(
                user_id=user_id,
                metric_name=metric_name,
                metric_value=Decimal(str(value)),
                metadata=metadata or {},
                timestamp=timestamp
            )
            
            db.session.add(usage_record)
            db.session.commit()
            
            # Check for usage warnings and alerts
            self._check_usage_alerts(user_id, metric_name, value)
            
            self.logger.info(f"Usage tracked: {user_id} - {metric_name}: {value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error tracking usage: {str(e)}")
            db.session.rollback()
            return False
    
    def get_usage_summary(self, user_id: str, period_days: int = 30) -> UsageSummary:
        """Get usage summary for a user"""
        try:
            # Get user's subscription
            subscription = Subscription.query.filter_by(
                user_id=user_id,
                status='active'
            ).first()
            
            if not subscription:
                return UsageSummary(
                    period_start=datetime.utcnow(),
                    period_end=datetime.utcnow(),
                    metrics={},
                    limits={},
                    warnings=[],
                    totals={}
                )
            
            # Calculate period
            period_end = datetime.utcnow()
            period_start = period_end - timedelta(days=period_days)
            
            # Get usage records for period
            usage_records = UsageRecord.query.filter(
                UsageRecord.user_id == user_id,
                UsageRecord.timestamp >= period_start,
                UsageRecord.timestamp < period_end
            ).all()
            
            # Aggregate usage by metric
            metrics = {}
            for record in usage_records:
                if record.metric_name not in metrics:
                    metrics[record.metric_name] = {
                        'total': Decimal('0'),
                        'count': 0,
                        'avg': Decimal('0'),
                        'max': Decimal('0')
                    }
                
                metrics[record.metric_name]['total'] += record.metric_value
                metrics[record.metric_name]['count'] += 1
                metrics[record.metric_name]['max'] = max(metrics[record.metric_name]['max'], record.metric_value)
            
            # Calculate averages
            for metric_name in metrics:
                if metrics[metric_name]['count'] > 0:
                    metrics[metric_name]['avg'] = metrics[metric_name]['total'] / metrics[metric_name]['count']
            
            # Get limits for user's plan
            plan_limits = self.usage_limits.get(subscription.plan_name, [])
            limits = {limit.metric_name: limit for limit in plan_limits}
            
            # Check for warnings
            warnings = self._generate_usage_warnings(metrics, limits)
            
            # Calculate totals
            totals = {}
            for metric_name in metrics:
                totals[metric_name] = float(metrics[metric_name]['total'])
            
            return UsageSummary(
                period_start=period_start,
                period_end=period_end,
                metrics=metrics,
                limits=limits,
                warnings=warnings,
                totals=totals
            )
            
        except Exception as e:
            self.logger.error(f"Error getting usage summary: {str(e)}")
            return UsageSummary(
                period_start=datetime.utcnow(),
                period_end=datetime.utcnow(),
                metrics={},
                limits={},
                warnings=[],
                totals={}
            )
    
    def _check_usage_alerts(self, user_id: str, metric_name: str, current_value: Union[int, float]):
        """Check if usage triggers any alerts"""
        try:
            subscription = Subscription.query.filter_by(
                user_id=user_id,
                status='active'
            ).first()
            
            if not subscription:
                return
            
            # Get limit for this metric
            limits = self.usage_limits.get(subscription.plan_name, [])
            limit = next((l for l in limits if l.metric_name == metric_name), None)
            
            if not limit or limit.limit <= 0:  # Unlimited metric
                return
            
            # Get current usage for this metric in current period
            period_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(days=30)
            
            current_usage = db.session.query(func.sum(UsageRecord.metric_value)).filter(
                and_(
                    UsageRecord.user_id == user_id,
                    UsageRecord.metric_name == metric_name,
                    UsageRecord.timestamp >= period_start,
                    UsageRecord.timestamp < period_end
                )
            ).scalar() or Decimal('0')
            
            # Check if usage exceeds limits
            usage_percentage = (current_usage / limit.limit) * 100 if limit.limit > 0 else 0
            
            # Create alert if threshold exceeded
            if usage_percentage >= (limit.warning_threshold * 100):
                self._create_usage_alert(
                    user_id=user_id,
                    metric_name=metric_name,
                    usage_value=current_value,
                    limit_value=limit.limit,
                    usage_percentage=usage_percentage
                )
        
        except Exception as e:
            self.logger.error(f"Error checking usage alerts: {str(e)}")
    
    def _create_usage_alert(self, user_id: str, metric_name: str, usage_value: Union[int, float],
                          limit_value: Union[int, float], usage_percentage: float):
        """Create a usage alert"""
        try:
            # Check if alert already exists for this metric and period
            existing_alert = BillingAlert.query.filter(
                and_(
                    BillingAlert.user_id == user_id,
                    BillingAlert.alert_type == 'usage_threshold',
                    BillingAlert.metadata.contains({'metric_name': metric_name}),
                    BillingAlert.is_read == False
                )
            ).first()
            
            if existing_alert:
                return  # Don't create duplicate alerts
            
            # Get limit details for alert
            limits = self._get_all_limits()
            limit = next((l for l in limits if l.metric_name == metric_name), None)
            
            if not limit:
                return
            
            alert = BillingAlert(
                user_id=user_id,
                alert_type='usage_threshold',
                title=f'{limit.display_name} Usage Warning',
                message=f'Your {limit.display_name.lower()} usage is at {usage_percentage:.1f}% of your limit ({usage_value} of {limit_value} {limit.unit})',
                severity='high' if usage_percentage >= 90 else 'normal',
                threshold_percentage=usage_percentage,
                current_usage=Decimal(str(usage_value)),
                limit_value=Decimal(str(limit_value)),
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            
            db.session.add(alert)
            db.session.commit()
            
            self.logger.info(f"Usage alert created: {user_id} - {metric_name} ({usage_percentage:.1f}%)")
            
        except Exception as e:
            self.logger.error(f"Error creating usage alert: {str(e)}")
    
    def _generate_usage_warnings(self, metrics: Dict, limits: Dict[str, UsageLimit]) -> List[Dict]:
        """Generate usage warnings"""
        warnings = []
        
        for metric_name, usage_data in metrics.items():
            if metric_name in limits:
                limit = limits[metric_name]
                if limit.limit > 0:  # Not unlimited
                    usage_value = float(usage_data['total'])
                    usage_percentage = (usage_value / limit.limit) * 100
                    
                    if usage_percentage >= (limit.warning_threshold * 100):
                        warnings.append({
                            'metric_name': metric_name,
                            'display_name': limit.display_name,
                            'current_usage': usage_value,
                            'limit': limit.limit,
                            'usage_percentage': usage_percentage,
                            'severity': 'high' if usage_percentage >= 90 else 'warning'
                        })
        
        return warnings
    
    def _get_all_limits(self) -> List[UsageLimit]:
        """Get all usage limits (flattened)"""
        all_limits = []
        for plan_limits in self.usage_limits.values():
            all_limits.extend(plan_limits)
        return all_limits

# Initialize usage tracker
usage_tracker = UsageTracker()

# API Endpoints

@usage_bp.route('/track', methods=['POST'])
@jwt_required()
@rate_limit(limit=100, per='hour')
def track_api_usage():
    """Track API usage endpoint"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        metric_name = data.get('metric_name')
        metric_value = data.get('metric_value', 1)
        metadata = data.get('metadata', {})
        
        if not metric_name:
            return jsonify({
                'success': False,
                'error': 'metric_name is required'
            }), 400
        
        success = usage_tracker.track_usage(user_id, metric_name, metric_value, metadata)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Usage tracked successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to track usage'
            }), 500
        
    except Exception as e:
        logger.error(f"Error in track_api_usage: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@usage_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_usage_summary():
    """Get usage summary for current user"""
    try:
        user_id = get_jwt_identity()
        period_days = request.args.get('period_days', '30', type=int)
        
        usage_summary = usage_tracker.get_usage_summary(user_id, period_days)
        
        # Convert to dict for JSON serialization
        result = {
            'period_start': usage_summary.period_start.isoformat(),
            'period_end': usage_summary.period_end.isoformat(),
            'metrics': {
                name: {
                    'total': float(data['total']),
                    'count': data['count'],
                    'avg': float(data['avg']),
                    'max': float(data['max'])
                }
                for name, data in usage_summary.metrics.items()
            },
            'warnings': usage_summary.warnings,
            'totals': usage_summary.totals
        }
        
        return jsonify({
            'success': True,
            'data': result,
            'message': 'Usage summary retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error getting usage summary: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve usage summary'
        }), 500

@usage_bp.route('/limits', methods=['GET'])
@jwt_required()
def get_usage_limits():
    """Get usage limits for user's subscription plan"""
    try:
        user_id = get_jwt_identity()
        
        subscription = Subscription.query.filter_by(
            user_id=user_id,
            status='active'
        ).first()
        
        if not subscription:
            return jsonify({
                'success': False,
                'error': 'No active subscription found'
            }), 404
        
        limits = usage_tracker.usage_limits.get(subscription.plan_name, [])
        limits_data = [
            {
                'metric_name': limit.metric_name,
                'display_name': limit.display_name,
                'limit': limit.limit,
                'unit': limit.unit,
                'warning_threshold': limit.warning_threshold,
                'overage_rate': float(limit.overage_rate) if limit.overage_rate else None
            }
            for limit in limits
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'plan_name': subscription.plan_name,
                'limits': limits_data
            },
            'message': 'Usage limits retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error getting usage limits: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve usage limits'
        }), 500

@usage_bp.route('/metrics', methods=['GET'])
@jwt_required()
def get_usage_metrics():
    """Get detailed usage metrics for a specific metric"""
    try:
        user_id = get_jwt_identity()
        metric_name = request.args.get('metric_name')
        period_days = request.args.get('period_days', '30', type=int)
        
        if not metric_name:
            return jsonify({
                'success': False,
                'error': 'metric_name is required'
            }), 400
        
        # Calculate period
        period_end = datetime.utcnow()
        period_start = period_end - timedelta(days=period_days)
        
        # Get usage records
        usage_records = UsageRecord.query.filter(
            UsageRecord.user_id == user_id,
            UsageRecord.metric_name == metric_name,
            UsageRecord.timestamp >= period_start,
            UsageRecord.timestamp < period_end
        ).order_by(UsageRecord.timestamp.asc()).all()
        
        # Process data for charting
        daily_usage = {}
        hourly_usage = {}
        
        for record in usage_records:
            # Daily aggregation
            day_key = record.timestamp.strftime('%Y-%m-%d')
            daily_usage[day_key] = daily_usage.get(day_key, 0) + float(record.metric_value)
            
            # Hourly aggregation (for more detailed charts)
            hour_key = record.timestamp.strftime('%Y-%m-%d %H:00')
            hourly_usage[hour_key] = hourly_usage.get(hour_key, 0) + float(record.metric_value)
        
        # Calculate statistics
        total_usage = sum(float(record.metric_value) for record in usage_records)
        avg_usage = total_usage / len(usage_records) if usage_records else 0
        max_usage = max([float(record.metric_value) for record in usage_records], default=0)
        
        result = {
            'metric_name': metric_name,
            'period_start': period_start.isoformat(),
            'period_end': period_end.isoformat(),
            'total_usage': total_usage,
            'average_usage': avg_usage,
            'max_usage': max_usage,
            'record_count': len(usage_records),
            'daily_usage': [{'date': date, 'usage': usage} for date, usage in sorted(daily_usage.items())],
            'hourly_usage': [{'timestamp': timestamp, 'usage': usage} for timestamp, usage in sorted(hourly_usage.items())]
        }
        
        return jsonify({
            'success': True,
            'data': result,
            'message': 'Usage metrics retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error getting usage metrics: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve usage metrics'
        }), 500

@usage_bp.route('/alerts', methods=['GET'])
@jwt_required()
def get_usage_alerts():
    """Get usage alerts for current user"""
    try:
        user_id = get_jwt_identity()
        include_read = request.args.get('include_read', 'false').lower() == 'true'
        limit = request.args.get('limit', '50', type=int)
        
        query = BillingAlert.query.filter_by(user_id=user_id)
        
        if not include_read:
            query = query.filter_by(is_read=False)
        
        alerts = query.order_by(BillingAlert.created_at.desc()).limit(limit).all()
        
        alerts_data = [alert.to_dict() for alert in alerts]
        
        return jsonify({
            'success': True,
            'data': alerts_data,
            'message': 'Usage alerts retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error getting usage alerts: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve usage alerts'
        }), 500

@usage_bp.route('/alerts/<alert_id>/read', methods=['POST'])
@jwt_required()
def mark_alert_read(alert_id):
    """Mark a usage alert as read"""
    try:
        user_id = get_jwt_identity()
        
        alert = BillingAlert.query.filter_by(
            id=alert_id,
            user_id=user_id
        ).first()
        
        if not alert:
            return jsonify({
                'success': False,
                'error': 'Alert not found'
            }), 404
        
        alert.is_read = True
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Alert marked as read'
        })
        
    except Exception as e:
        logger.error(f"Error marking alert as read: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to mark alert as read'
        }), 500

# Helper endpoints for specific usage types

@usage_bp.route('/deployments/track', methods=['POST'])
@jwt_required()
def track_chain_deployment():
    """Track chain deployment usage"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        chain_id = data.get('chain_id')
        deployment_type = data.get('deployment_type', 'standard')
        
        metadata = {
            'chain_id': chain_id,
            'deployment_type': deployment_type,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        success = usage_tracker.track_usage(
            user_id=user_id,
            metric_name='chain_deployments',
            value=1,
            metadata=metadata
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Chain deployment tracked successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to track chain deployment'
            }), 500
        
    except Exception as e:
        logger.error(f"Error tracking chain deployment: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@usage_bp.route('/storage/track', methods=['POST'])
@jwt_required()
def track_storage_usage():
    """Track storage usage"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        operation_type = data.get('operation_type')  # upload, download, delete
        file_size = data.get('file_size', 0)
        storage_path = data.get('storage_path')
        
        # Storage operations impact bandwidth, not storage itself
        # Only track actual storage usage separately
        if operation_type in ['upload']:
            usage_tracker.track_usage(
                user_id=user_id,
                metric_name='storage_gb',
                value=file_size / (1024 * 1024 * 1024),  # Convert bytes to GB
                metadata={
                    'operation': operation_type,
                    'storage_path': storage_path,
                    'file_size': file_size
                }
            )
        
        # Track bandwidth for all operations
        usage_tracker.track_usage(
            user_id=user_id,
            metric_name='bandwidth_gb',
            value=file_size / (1024 * 1024 * 1024),
            metadata={
                'operation': operation_type,
                'storage_path': storage_path,
                'file_size': file_size
            }
        )
        
        return jsonify({
            'success': True,
            'message': 'Storage usage tracked successfully'
        })
        
    except Exception as e:
        logger.error(f"Error tracking storage usage: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@usage_bp.route('/api/track', methods=['POST'])
@jwt_required()
def track_api_request():
    """Track API request usage"""
    try:
        user_id = get_jwt_identity()
        
        # Track API request
        usage_tracker.track_usage(
            user_id=user_id,
            metric_name='api_requests',
            value=1,
            metadata={
                'endpoint': request.endpoint,
                'method': request.method,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
        return jsonify({
            'success': True,
            'message': 'API usage tracked successfully'
        })
        
    except Exception as e:
        logger.error(f"Error tracking API usage: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

# Import required modules
from sqlalchemy import and_, func

# Automatic usage tracking middleware
class UsageTrackingMiddleware:
    """Middleware for automatic usage tracking"""
    
    @staticmethod
    def track_request_before_request():
        """Track API requests before each request"""
        if request.endpoint and request.endpoint.startswith('api.'):
            try:
                # Get user ID from JWT if available
                if hasattr(request, 'get_json') and request.get_json():
                    user_id = get_jwt_identity() if get_jwt_identity() else None
                    if user_id:
                        usage_tracker.track_usage(
                            user_id=user_id,
                            metric_name='api_requests',
                            value=1,
                            metadata={
                                'endpoint': request.endpoint,
                                'method': request.method,
                                'remote_addr': request.remote_addr,
                                'user_agent': request.headers.get('User-Agent')
                            }
                        )
            except Exception as e:
                logger.warning(f"Failed to track API usage: {str(e)}")
    
    @staticmethod
    def track_request_after_request(response):
        """Track API requests after each request for response-based billing"""
        try:
            if request.endpoint and request.endpoint.startswith('api.'):
                user_id = get_jwt_identity() if get_jwt_identity() else None
                if user_id and response.status_code == 200:
                    # Track successful operations for billing
                    if 'deploy' in request.endpoint:
                        usage_tracker.track_usage(
                            user_id=user_id,
                            metric_name='api_operations',
                            value=1,
                            metadata={
                                'endpoint': request.endpoint,
                                'response_size': len(response.get_data()),
                                'success': True
                            }
                        )
        except Exception as e:
            logger.warning(f"Failed to track after-request usage: {str(e)}")
        
        return response