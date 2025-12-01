"""
Customer Portal and Revenue Analytics for CosmosBuilder
Author: MiniMax Agent
Date: 2025-11-27

Customer self-service portal and comprehensive revenue analytics system.
"""

from flask import Blueprint, request, jsonify, render_template_string
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
import logging
from decimal import Decimal
import json

from .models import db, User, Subscription, Invoice, Payment, UsageRecord, BillingAlert
from .billing import billing_manager
from .usage_tracking import usage_tracker
from ..utils.decorators import subscription_required
from ..utils.logging import get_logger

logger = get_logger(__name__)
portal_bp = Blueprint('portal', __name__, url_prefix='/api/portal')
analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

class CustomerPortal:
    """Customer self-service portal manager"""
    
    def __init__(self):
        self.logger = logger
    
    def get_dashboard_data(self, user_id: str) -> Dict:
        """Get customer dashboard data"""
        try:
            # Get user and subscription
            user = User.query.get(user_id)
            subscription = Subscription.query.filter_by(
                user_id=user_id,
                status='active'
            ).first()
            
            # Get usage summary
            usage_summary = usage_tracker.get_usage_summary(user_id)
            
            # Get recent invoices
            recent_invoices = Invoice.query.filter_by(
                user_id=user_id
            ).order_by(Invoice.invoice_date.desc()).limit(10).all()
            
            # Get recent payments
            recent_payments = Payment.query.filter_by(
                user_id=user_id
            ).order_by(Payment.created_at.desc()).limit(10).all()
            
            # Get unread alerts
            unread_alerts = BillingAlert.query.filter_by(
                user_id=user_id,
                is_read=False
            ).order_by(BillingAlert.created_at.desc()).limit(5).all()
            
            # Calculate billing estimate for current period
            billing_estimate = None
            if subscription:
                billing_estimate = billing_manager.calculate_billing(
                    user=user,
                    period_start=subscription.billing_cycle_start,
                    period_end=subscription.billing_cycle_end
                )
            
            dashboard_data = {
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                    'organization': user.organization,
                    'created_at': user.created_at.isoformat()
                },
                'subscription': subscription.to_dict() if subscription else None,
                'usage': {
                    'period_start': usage_summary.period_start.isoformat(),
                    'period_end': usage_summary.period_end.isoformat(),
                    'metrics': {
                        name: {
                            'total': float(data['total']),
                            'limit': limit.limit if limit and limit.limit > 0 else None,
                            'usage_percentage': (float(data['total']) / limit.limit * 100) if limit and limit.limit > 0 else 0
                        }
                        for name, data in usage_summary.metrics.items()
                        for limit in [usage_summary.limits.get(name)]
                    },
                    'warnings': usage_summary.warnings
                },
                'billing': {
                    'estimated_total': float(billing_estimate.total_amount) if billing_estimate else 0,
                    'breakdown': {
                        'base_amount': float(billing_estimate.base_amount) if billing_estimate else 0,
                        'usage_amount': float(billing_estimate.usage_amount) if billing_estimate else 0,
                        'overage_amount': float(billing_estimate.overage_amount) if billing_estimate else 0
                    } if billing_estimate else None
                },
                'recent_invoices': [invoice.to_dict() for invoice in recent_invoices],
                'recent_payments': [payment.to_dict() for payment in recent_payments],
                'alerts': [alert.to_dict() for alert in unread_alerts],
                'generated_at': datetime.utcnow().isoformat()
            }
            
            return dashboard_data
            
        except Exception as e:
            self.logger.error(f"Error getting dashboard data: {str(e)}")
            return {}
    
    def generate_invoice_pdf(self, invoice_id: str, user_id: str) -> str:
        """Generate PDF invoice (simplified)"""
        try:
            invoice = Invoice.query.filter_by(
                id=invoice_id,
                user_id=user_id
            ).first()
            
            if not invoice:
                return None
            
            # In production, this would generate a real PDF using a library like ReportLab
            # For now, return a placeholder URL
            pdf_url = f"/api/portal/invoices/{invoice_id}/pdf"
            
            # Update invoice with PDF URL
            invoice.pdf_url = pdf_url
            db.session.commit()
            
            return pdf_url
            
        except Exception as e:
            self.logger.error(f"Error generating invoice PDF: {str(e)}")
            return None
    
    def get_usage_analytics(self, user_id: str, period_days: int = 30) -> Dict:
        """Get detailed usage analytics for customer"""
        try:
            usage_summary = usage_tracker.get_usage_summary(user_id, period_days)
            
            # Get daily usage breakdown
            daily_usage = self._get_daily_usage_breakdown(user_id, period_days)
            
            # Get usage trends
            usage_trends = self._get_usage_trends(user_id, period_days)
            
            # Get usage forecasts
            usage_forecasts = self._get_usage_forecasts(user_id, usage_summary)
            
            return {
                'period': {
                    'start': usage_summary.period_start.isoformat(),
                    'end': usage_summary.period_end.isoformat(),
                    'days': period_days
                },
                'current_usage': {
                    name: float(data['total']) for name, data in usage_summary.metrics.items()
                },
                'usage_limits': {
                    name: limit.limit for name, limit in usage_summary.limits.items()
                },
                'usage_percentages': {
                    name: (float(data['total']) / limit.limit * 100) if limit and limit.limit > 0 else 0
                    for name, data in usage_summary.metrics.items()
                    for limit in [usage_summary.limits.get(name)]
                },
                'daily_breakdown': daily_usage,
                'trends': usage_trends,
                'forecasts': usage_forecasts,
                'warnings': usage_summary.warnings,
                'recommendations': self._generate_usage_recommendations(usage_summary)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting usage analytics: {str(e)}")
            return {}
    
    def _get_daily_usage_breakdown(self, user_id: str, period_days: int) -> List[Dict]:
        """Get daily usage breakdown"""
        try:
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=period_days)
            
            daily_data = []
            
            for single_date in (start_date + timedelta(days=n) for n in range(period_days + 1)):
                day_start = datetime.combine(single_date, datetime.min.time())
                day_end = day_start + timedelta(days=1)
                
                usage_records = UsageRecord.query.filter(
                    UsageRecord.user_id == user_id,
                    UsageRecord.timestamp >= day_start,
                    UsageRecord.timestamp < day_end
                ).all()
                
                day_metrics = {}
                for record in usage_records:
                    if record.metric_name not in day_metrics:
                        day_metrics[record.metric_name] = 0
                    day_metrics[record.metric_name] += float(record.metric_value)
                
                daily_data.append({
                    'date': single_date.isoformat(),
                    'metrics': day_metrics
                })
            
            return daily_data
            
        except Exception as e:
            self.logger.error(f"Error getting daily usage breakdown: {str(e)}")
            return []
    
    def _get_usage_trends(self, user_id: str, period_days: int) -> Dict:
        """Analyze usage trends"""
        try:
            # This would implement trend analysis logic
            # For now, return placeholder data
            return {
                'api_requests': {
                    'trend': 'increasing',
                    'change_percentage': 15.5,
                    'predicted_next_period': 8500
                },
                'chain_deployments': {
                    'trend': 'stable',
                    'change_percentage': 2.1,
                    'predicted_next_period': 45
                },
                'storage_gb': {
                    'trend': 'increasing',
                    'change_percentage': 8.7,
                    'predicted_next_period': 12.3
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting usage trends: {str(e)}")
            return {}
    
    def _get_usage_forecasts(self, user_id: str, usage_summary) -> Dict:
        """Generate usage forecasts"""
        try:
            forecasts = {}
            
            for metric_name, data in usage_summary.metrics.items():
                current_usage = float(data['total'])
                limit = usage_summary.limits.get(metric_name).limit if usage_summary.limits.get(metric_name) else None
                
                # Simple forecast: assume linear growth
                daily_average = current_usage / 30  # Assuming 30-day period
                days_in_current_period = usage_summary.days_until_billing_cycle_end
                forecasted_usage = daily_average * days_in_current_period
                
                overage_risk = False
                if limit and limit > 0:
                    overage_risk = forecasted_usage > (limit * 0.9)  # 90% of limit
                
                forecasts[metric_name] = {
                    'forecasted_usage': round(forecasted_usage, 2),
                    'limit': limit,
                    'overage_risk': overage_risk,
                    'days_to_limit': None  # Calculate days to reach 80% of limit
                }
            
            return forecasts
            
        except Exception as e:
            self.logger.error(f"Error generating usage forecasts: {str(e)}")
            return {}
    
    def _generate_usage_recommendations(self, usage_summary) -> List[str]:
        """Generate usage optimization recommendations"""
        recommendations = []
        
        try:
            for metric_name, data in usage_summary.metrics.items():
                current_usage = float(data['total'])
                limit = usage_summary.limits.get(metric_name).limit if usage_summary.limits.get(metric_name) else None
                
                if limit and limit > 0:
                    usage_percentage = (current_usage / limit) * 100
                    
                    if usage_percentage >= 90:
                        recommendations.append(f"You're approaching your {metric_name} limit. Consider upgrading your plan.")
                    elif usage_percentage <= 50 and limit > 10:
                        recommendations.append(f"You're using only {usage_percentage:.1f}% of your {metric_name} limit. You might consider a lower tier plan.")
            
            # Usage pattern recommendations
            if 'chain_deployments' in usage_summary.metrics and usage_summary.metrics['chain_deployments']['total'] < 10:
                recommendations.append("Consider batching multiple deployments to optimize your usage.")
            
            if 'api_requests' in usage_summary.metrics and usage_summary.metrics['api_requests']['total'] > 50000:
                recommendations.append("High API usage detected. Consider implementing caching to reduce API calls.")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {str(e)}")
            return []

class RevenueAnalytics:
    """Revenue analytics and reporting system"""
    
    def __init__(self):
        self.logger = logger
    
    def get_revenue_analytics(self, user_id: Optional[str] = None, 
                            period_start: Optional[datetime] = None,
                            period_end: Optional[datetime] = None) -> Dict:
        """Get comprehensive revenue analytics"""
        try:
            # Set default period (last 30 days)
            if not period_end:
                period_end = datetime.utcnow()
            if not period_start:
                period_start = period_end - timedelta(days=30)
            
            if user_id:
                return self._get_user_revenue_analytics(user_id, period_start, period_end)
            else:
                return self._get_platform_revenue_analytics(period_start, period_end)
            
        except Exception as e:
            self.logger.error(f"Error getting revenue analytics: {str(e)}")
            return {}
    
    def _get_user_revenue_analytics(self, user_id: str, period_start: datetime, period_end: datetime) -> Dict:
        """Get revenue analytics for a specific user"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {}
            
            # Get user invoices
            invoices = Invoice.query.filter(
                Invoice.user_id == user_id,
                Invoice.invoice_date >= period_start,
                Invoice.invoice_date <= period_end
            ).all()
            
            # Get user payments
            payments = Payment.query.filter(
                Payment.user_id == user_id,
                Payment.created_at >= period_start,
                Payment.created_at <= period_end
            ).all()
            
            # Calculate metrics
            total_revenue = sum(float(invoice.total_amount) for invoice in invoices)
            total_paid = sum(float(payment.amount) for payment in payments if payment.status == 'completed')
            total_outstanding = total_revenue - total_paid
            payment_success_rate = (len([p for p in payments if p.status == 'completed']) / len(payments) * 100) if payments else 0
            
            # Revenue by plan
            plan_revenue = {}
            for invoice in invoices:
                subscription = Subscription.query.get(invoice.subscription_id)
                if subscription:
                    plan_name = subscription.plan_name
                    plan_revenue[plan_name] = plan_revenue.get(plan_name, 0) + float(invoice.total_amount)
            
            # Monthly revenue trends (if period is long enough)
            monthly_revenue = self._calculate_monthly_revenue(user_id, period_start, period_end)
            
            return {
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                    'created_at': user.created_at.isoformat()
                },
                'period': {
                    'start': period_start.isoformat(),
                    'end': period_end.isoformat()
                },
                'revenue': {
                    'total_revenue': total_revenue,
                    'total_paid': total_paid,
                    'total_outstanding': total_outstanding,
                    'payment_success_rate': payment_success_rate
                },
                'breakdown': {
                    'by_plan': plan_revenue,
                    'invoices_count': len(invoices),
                    'payments_count': len(payments)
                },
                'trends': {
                    'monthly_revenue': monthly_revenue
                },
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting user revenue analytics: {str(e)}")
            return {}
    
    def _get_platform_revenue_analytics(self, period_start: datetime, period_end: datetime) -> Dict:
        """Get platform-wide revenue analytics (admin only)"""
        try:
            # Get all invoices in period
            invoices = Invoice.query.filter(
                Invoice.invoice_date >= period_start,
                Invoice.invoice_date <= period_end
            ).all()
            
            # Get all payments in period
            payments = Payment.query.filter(
                Payment.created_at >= period_start,
                Payment.created_at <= period_end
            ).all()
            
            # Get active subscriptions
            active_subscriptions = Subscription.query.filter_by(status='active').all()
            
            # Calculate platform metrics
            total_revenue = sum(float(invoice.total_amount) for invoice in invoices)
            total_paid = sum(float(payment.amount) for payment in payments if payment.status == 'completed')
            
            # Revenue by plan
            plan_revenue = {}
            plan_subscriptions = {}
            
            for invoice in invoices:
                subscription = Subscription.query.get(invoice.subscription_id)
                if subscription:
                    plan_name = subscription.plan_name
                    plan_revenue[plan_name] = plan_revenue.get(plan_name, 0) + float(invoice.total_amount)
                    plan_subscriptions[plan_name] = plan_subscriptions.get(plan_name, 0) + 1
            
            # Revenue by month
            monthly_revenue = self._calculate_platform_monthly_revenue(period_start, period_end)
            
            # Customer metrics
            total_customers = User.query.filter_by(is_active=True).count()
            new_customers = User.query.filter(
                User.created_at >= period_start,
                User.created_at <= period_end
            ).count()
            
            # Churn analysis
            churned_subscriptions = Subscription.query.filter(
                Subscription.cancelled_at >= period_start,
                Subscription.cancelled_at <= period_end
            ).count()
            
            churn_rate = (churned_subscriptions / len(active_subscriptions) * 100) if active_subscriptions else 0
            
            return {
                'platform_metrics': {
                    'total_revenue': total_revenue,
                    'total_paid': total_paid,
                    'active_customers': total_customers,
                    'new_customers': new_customers,
                    'churn_rate': churn_rate,
                    'average_revenue_per_user': total_revenue / total_customers if total_customers > 0 else 0
                },
                'plan_breakdown': {
                    'revenue_by_plan': plan_revenue,
                    'subscriptions_by_plan': plan_subscriptions
                },
                'revenue_trends': {
                    'monthly_revenue': monthly_revenue
                },
                'period': {
                    'start': period_start.isoformat(),
                    'end': period_end.isoformat()
                },
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting platform revenue analytics: {str(e)}")
            return {}
    
    def _calculate_monthly_revenue(self, user_id: str, period_start: datetime, period_end: datetime) -> List[Dict]:
        """Calculate monthly revenue for a user"""
        try:
            monthly_data = []
            
            # Group invoices by month
            invoices = Invoice.query.filter(
                Invoice.user_id == user_id,
                Invoice.invoice_date >= period_start,
                Invoice.invoice_date <= period_end
            ).all()
            
            monthly_totals = {}
            for invoice in invoices:
                month_key = invoice.invoice_date.strftime('%Y-%m')
                monthly_totals[month_key] = monthly_totals.get(month_key, 0) + float(invoice.total_amount)
            
            for month_key, total in sorted(monthly_totals.items()):
                monthly_data.append({
                    'month': month_key,
                    'revenue': total
                })
            
            return monthly_data
            
        except Exception as e:
            self.logger.error(f"Error calculating monthly revenue: {str(e)}")
            return []
    
    def _calculate_platform_monthly_revenue(self, period_start: datetime, period_end: datetime) -> List[Dict]:
        """Calculate platform monthly revenue"""
        try:
            monthly_data = []
            
            # Get all invoices in period
            invoices = Invoice.query.filter(
                Invoice.invoice_date >= period_start,
                Invoice.invoice_date <= period_end
            ).all()
            
            # Group by month
            monthly_totals = {}
            for invoice in invoices:
                month_key = invoice.invoice_date.strftime('%Y-%m')
                monthly_totals[month_key] = monthly_totals.get(month_key, 0) + float(invoice.total_amount)
            
            for month_key, total in sorted(monthly_totals.items()):
                monthly_data.append({
                    'month': month_key,
                    'revenue': total,
                    'invoice_count': len([inv for inv in invoices if inv.invoice_date.strftime('%Y-%m') == month_key])
                })
            
            return monthly_data
            
        except Exception as e:
            self.logger.error(f"Error calculating platform monthly revenue: {str(e)}")
            return []
    
    def get_usage_analytics(self, period_days: int = 30) -> Dict:
        """Get platform usage analytics"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_days)
            
            # Get usage records
            usage_records = UsageRecord.query.filter(
                UsageRecord.timestamp >= start_date,
                UsageRecord.timestamp < end_date
            ).all()
            
            # Aggregate by metric
            usage_summary = {}
            for record in usage_records:
                metric_name = record.metric_name
                if metric_name not in usage_summary:
                    usage_summary[metric_name] = {
                        'total': 0,
                        'count': 0,
                        'users': set()
                    }
                
                usage_summary[metric_name]['total'] += float(record.metric_value)
                usage_summary[metric_name]['count'] += 1
                usage_summary[metric_name]['users'].add(record.user_id)
            
            # Convert sets to counts
            for metric_name in usage_summary:
                usage_summary[metric_name]['user_count'] = len(usage_summary[metric_name]['users'])
                usage_summary[metric_name]['users'] = None  # Remove set for JSON serialization
            
            return {
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat(),
                    'days': period_days
                },
                'usage_summary': usage_summary,
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting usage analytics: {str(e)}")
            return {}

# Initialize portal and analytics managers
customer_portal = CustomerPortal()
revenue_analytics = RevenueAnalytics()

# Customer Portal Endpoints

@portal_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    """Get customer dashboard data"""
    try:
        user_id = get_jwt_identity()
        dashboard_data = customer_portal.get_dashboard_data(user_id)
        
        if not dashboard_data:
            return jsonify({
                'success': False,
                'error': 'Failed to load dashboard data'
            }), 500
        
        return jsonify({
            'success': True,
            'data': dashboard_data,
            'message': 'Dashboard data retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve dashboard data'
        }), 500

@portal_bp.route('/usage-analytics', methods=['GET'])
@jwt_required()
def get_portal_usage_analytics():
    """Get usage analytics for customer portal"""
    try:
        user_id = get_jwt_identity()
        period_days = request.args.get('period_days', '30', type=int)
        
        analytics_data = customer_portal.get_usage_analytics(user_id, period_days)
        
        if not analytics_data:
            return jsonify({
                'success': False,
                'error': 'Failed to load usage analytics'
            }), 500
        
        return jsonify({
            'success': True,
            'data': analytics_data,
            'message': 'Usage analytics retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error getting usage analytics: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve usage analytics'
        }), 500

@portal_bp.route('/invoices/<invoice_id>/pdf', methods=['GET'])
@jwt_required()
def get_invoice_pdf(invoice_id):
    """Get invoice PDF"""
    try:
        user_id = get_jwt_identity()
        pdf_url = customer_portal.generate_invoice_pdf(invoice_id, user_id)
        
        if not pdf_url:
            return jsonify({
                'success': False,
                'error': 'Invoice not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': {'pdf_url': pdf_url},
            'message': 'Invoice PDF URL generated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error generating invoice PDF: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate invoice PDF'
        }), 500

# Revenue Analytics Endpoints

@analytics_bp.route('/revenue', methods=['GET'])
@jwt_required()
def get_revenue_analytics():
    """Get revenue analytics"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        # Check if user is admin
        if user.role != 'admin':
            return jsonify({
                'success': False,
                'error': 'Insufficient permissions'
            }), 403
        
        period_days = request.args.get('period_days', '30', type=int)
        
        period_start = datetime.utcnow() - timedelta(days=period_days)
        period_end = datetime.utcnow()
        
        analytics_data = revenue_analytics.get_revenue_analytics(
            period_start=period_start,
            period_end=period_end
        )
        
        if not analytics_data:
            return jsonify({
                'success': False,
                'error': 'Failed to load revenue analytics'
            }), 500
        
        return jsonify({
            'success': True,
            'data': analytics_data,
            'message': 'Revenue analytics retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error getting revenue analytics: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve revenue analytics'
        }), 500

@analytics_bp.route('/revenue/user/<user_id>', methods=['GET'])
@jwt_required()
def get_user_revenue_analytics(user_id):
    """Get revenue analytics for specific user"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        # Check if user can access this data
        if current_user.role != 'admin' and current_user_id != user_id:
            return jsonify({
                'success': False,
                'error': 'Insufficient permissions'
            }), 403
        
        period_days = request.args.get('period_days', '30', type=int)
        
        period_start = datetime.utcnow() - timedelta(days=period_days)
        period_end = datetime.utcnow()
        
        analytics_data = revenue_analytics.get_revenue_analytics(
            user_id=user_id,
            period_start=period_start,
            period_end=period_end
        )
        
        if not analytics_data:
            return jsonify({
                'success': False,
                'error': 'Failed to load user revenue analytics'
            }), 500
        
        return jsonify({
            'success': True,
            'data': analytics_data,
            'message': 'User revenue analytics retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error getting user revenue analytics: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve user revenue analytics'
        }), 500

@analytics_bp.route('/usage', methods=['GET'])
@jwt_required()
def get_platform_usage_analytics():
    """Get platform usage analytics"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        # Only allow admin users
        if user.role != 'admin':
            return jsonify({
                'success': False,
                'error': 'Insufficient permissions'
            }), 403
        
        period_days = request.args.get('period_days', '30', type=int)
        
        analytics_data = revenue_analytics.get_usage_analytics(period_days)
        
        if not analytics_data:
            return jsonify({
                'success': False,
                'error': 'Failed to load usage analytics'
            }), 500
        
        return jsonify({
            'success': True,
            'data': analytics_data,
            'message': 'Platform usage analytics retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error getting platform usage analytics: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve platform usage analytics'
        }), 500

@analytics_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_analytics_summary():
    """Get comprehensive analytics summary"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        # Only allow admin users
        if user.role != 'admin':
            return jsonify({
                'success': False,
                'error': 'Insufficient permissions'
            }), 403
        
        # Get revenue analytics
        revenue_data = revenue_analytics.get_revenue_analytics()
        
        # Get usage analytics
        usage_data = revenue_analytics.get_usage_analytics()
        
        # Get subscription metrics
        total_subscriptions = Subscription.query.filter_by(status='active').count()
        total_users = User.query.filter_by(is_active=True).count()
        
        summary = {
            'generated_at': datetime.utcnow().isoformat(),
            'revenue_metrics': revenue_data.get('platform_metrics', {}),
            'usage_metrics': usage_data.get('usage_summary', {}),
            'subscription_metrics': {
                'total_active_subscriptions': total_subscriptions,
                'total_active_users': total_users
            },
            'plans': {
                'distribution': {}
            }
        }
        
        # Get plan distribution
        plan_distribution = db.session.query(
            Subscription.plan_name,
            func.count(Subscription.id)
        ).filter_by(status='active').group_by(Subscription.plan_name).all()
        
        summary['plans']['distribution'] = dict(plan_distribution)
        
        return jsonify({
            'success': True,
            'data': summary,
            'message': 'Analytics summary retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error getting analytics summary: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve analytics summary'
        }), 500

# Import required modules
from sqlalchemy import func

# Export management endpoints

@portal_bp.route('/export/invoices', methods=['GET'])
@jwt_required()
def export_invoices():
    """Export invoices as CSV"""
    try:
        user_id = get_jwt_identity()
        
        invoices = Invoice.query.filter_by(user_id=user_id).order_by(Invoice.invoice_date.desc()).all()
        
        # Generate CSV data
        csv_data = "Invoice Number,Date,Amount,Status\n"
        for invoice in invoices:
            csv_data += f"{invoice.invoice_number},{invoice.invoice_date.date()},{invoice.total_amount},{invoice.status}\n"
        
        return jsonify({
            'success': True,
            'data': {
                'csv_data': csv_data,
                'filename': f"invoices_{user_id}.csv"
            },
            'message': 'Invoice export data generated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error exporting invoices: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to export invoices'
        }), 500