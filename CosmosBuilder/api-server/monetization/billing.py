"""
CosmosBuilder Monetization Application
Author: MiniMax Agent
Date: 2025-11-27

This module handles all monetization aspects including:
- Subscription management
- Payment processing
- Usage tracking
- Billing and invoicing
- Revenue analytics
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Optional
import logging
import stripe
import json
import uuid
from dataclasses import dataclass, asdict

from ..models import User, Subscription, UsageRecord, Invoice, Payment
from ..utils.decorators import subscription_required, plan_required
from ..utils.validators import validate_subscription_data
from ..utils.email import send_email
from ..utils.logging import get_logger

logger = get_logger(__name__)
billing_bp = Blueprint('billing', __name__, url_prefix='/api/billing')

@dataclass
class UsageMetrics:
    """Usage tracking for billing calculations"""
    chain_deployments: int = 0
    api_requests: int = 0
    storage_gb: float = 0.0
    bandwidth_gb: float = 0.0
    computing_hours: float = 0.0
    additional_features: List[str] = None
    
    def __post_init__(self):
        if self.additional_features is None:
            self.additional_features = []

@dataclass
class BillingCalculation:
    """Billing calculation result"""
    base_amount: Decimal
    usage_amount: Decimal
    overage_amount: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    usage_details: Dict

class BillingManager:
    """Central billing management class"""
    
    def __init__(self):
        self.logger = logger
        
    def get_subscription_plans(self) -> List[Dict]:
        """Get all available subscription plans"""
        plans = [
            {
                'id': 'starter',
                'name': 'Starter',
                'display_name': 'Starter',
                'description': 'Perfect for individual developers and small projects',
                'price_monthly': 199.00,
                'price_yearly': 1990.00,
                'currency': 'USD',
                'max_chains': 1,
                'max_deployments_per_month': 100,
                'max_storage_gb': 10,
                'max_api_requests_per_month': 10000,
                'max_bandwidth_gb_per_month': 100,
                'support_level': 'community',
                'features': [
                    'basic_monitoring',
                    'community_support',
                    'standard_templates',
                    'email_support'
                ],
                'billing_cycles': ['monthly', 'yearly'],
                'trial_days': 14
            },
            {
                'id': 'professional',
                'name': 'professional',
                'display_name': 'Professional',
                'description': 'Ideal for growing businesses and development teams',
                'price_monthly': 999.00,
                'price_yearly': 9990.00,
                'currency': 'USD',
                'max_chains': 5,
                'max_deployments_per_month': 500,
                'max_storage_gb': 50,
                'max_api_requests_per_month': 100000,
                'max_bandwidth_gb_per_month': 500,
                'support_level': 'priority',
                'features': [
                    'advanced_monitoring',
                    'priority_support',
                    'custom_templates',
                    'analytics',
                    'webhook_support',
                    'api_rate_limiting',
                    'dedicated_support'
                ],
                'billing_cycles': ['monthly', 'yearly'],
                'trial_days': 14
            },
            {
                'id': 'enterprise',
                'name': 'enterprise',
                'display_name': 'Enterprise',
                'description': 'Advanced features for large organizations',
                'price_monthly': 4999.00,
                'price_yearly': 49990.00,
                'currency': 'USD',
                'max_chains': -1,  # Unlimited
                'max_deployments_per_month': -1,  # Unlimited
                'max_storage_gb': 500,
                'max_api_requests_per_month': 1000000,
                'max_bandwidth_gb_per_month': 5000,
                'support_level': 'dedicated',
                'features': [
                    'dedicated_support',
                    'custom_integrations',
                    'white_label',
                    'advanced_analytics',
                    'compliance_tools',
                    'sla_guarantee',
                    'custom_development',
                    'priority_feature_requests'
                ],
                'billing_cycles': ['monthly', 'yearly'],
                'trial_days': 30
            },
            {
                'id': 'sovereign',
                'name': 'sovereign',
                'display_name': 'Sovereign',
                'description': 'Government-grade solutions for institutions',
                'price_monthly': 19999.00,
                'price_yearly': 199990.00,
                'currency': 'USD',
                'max_chains': -1,  # Unlimited
                'max_deployments_per_month': -1,  # Unlimited
                'max_storage_gb': -1,  # Unlimited
                'max_api_requests_per_month': -1,  # Unlimited
                'max_bandwidth_gb_per_month': -1,  # Unlimited
                'support_level': 'concierge',
                'features': [
                    'concierge_support',
                    'on_premise',
                    'custom_development',
                    'government_compliance',
                    'training',
                    'dedicated_infrastructure',
                    'custom_compliance_frameworks',
                    '24_7_support'
                ],
                'billing_cycles': ['monthly', 'yearly'],
                'trial_days': 30
            }
        ]
        return plans
    
    def calculate_billing(self, user: User, period_start: datetime, period_end: datetime) -> BillingCalculation:
        """Calculate billing for a user for a specific period"""
        from ..models import db, Subscription, UsageRecord
        
        subscription = Subscription.query.filter_by(
            user_id=user.id,
            status='active'
        ).first()
        
        if not subscription:
            return BillingCalculation(
                base_amount=Decimal('0'),
                usage_amount=Decimal('0'),
                overage_amount=Decimal('0'),
                discount_amount=Decimal('0'),
                tax_amount=Decimal('0'),
                total_amount=Decimal('0'),
                usage_details={}
            )
        
        plan = self.get_subscription_plans().get(subscription.plan_name)
        if not plan:
            raise ValueError(f"Unknown plan: {subscription.plan_name}")
        
        # Get usage records for the period
        usage_records = UsageRecord.query.filter(
            and_(
                UsageRecord.user_id == user.id,
                UsageRecord.timestamp >= period_start,
                UsageRecord.timestamp < period_end
            )
        ).all()
        
        # Calculate base subscription amount
        base_amount = Decimal(str(plan['price_monthly']))
        
        # Calculate usage fees
        usage_metrics = self._aggregate_usage(usage_records)
        usage_amount, usage_details = self._calculate_usage_fees(usage_metrics, plan)
        
        # Calculate overages
        overage_amount, overage_details = self._calculate_overages(usage_metrics, plan)
        
        # Apply discounts
        discount_amount = self._calculate_discounts(subscription)
        
        # Calculate taxes
        tax_amount = self._calculate_taxes(base_amount + usage_amount + overage_amount - discount_amount)
        
        # Calculate total
        subtotal = base_amount + usage_amount + overage_amount - discount_amount
        total_amount = subtotal + tax_amount
        
        return BillingCalculation(
            base_amount=base_amount,
            usage_amount=usage_amount,
            overage_amount=overage_amount,
            discount_amount=discount_amount,
            tax_amount=tax_amount,
            total_amount=total_amount,
            usage_details={
                'usage': usage_details,
                'overage': overage_details,
                'discounts': [asdict(d) for d in self._get_applied_discounts(subscription)],
                'taxes': self._get_tax_breakdown()
            }
        )
    
    def _aggregate_usage(self, usage_records: List[UsageRecord]) -> UsageMetrics:
        """Aggregate usage records into metrics"""
        metrics = UsageMetrics()
        
        for record in usage_records:
            if record.metric_name == 'chain_deployments':
                metrics.chain_deployments += record.metric_value
            elif record.metric_name == 'api_requests':
                metrics.api_requests += record.metric_value
            elif record.metric_name == 'storage_gb':
                metrics.storage_gb += record.metric_value
            elif record.metric_name == 'bandwidth_gb':
                metrics.bandwidth_gb += record.metric_value
            elif record.metric_name == 'computing_hours':
                metrics.computing_hours += record.metric_value
            
            # Handle additional features
            if record.metadata and 'feature' in record.metadata:
                if record.metadata['feature'] not in metrics.additional_features:
                    metrics.additional_features.append(record.metadata['feature'])
        
        return metrics
    
    def _calculate_usage_fees(self, metrics: UsageMetrics, plan: Dict) -> tuple[Decimal, Dict]:
        """Calculate fees for usage within plan limits"""
        usage_amount = Decimal('0.00')
        usage_details = {}
        
        # API requests (if applicable)
        api_fee_per_1000 = Decimal('0.10')  # $0.10 per 1000 requests
        api_over_100k = max(0, metrics.api_requests - 100000) // 1000
        api_usage_fee = api_over_100k * api_fee_per_1000
        usage_amount += api_usage_fee
        usage_details['api_requests'] = {
            'count': metrics.api_requests,
            'within_limit': min(metrics.api_requests, 100000),
            'over_limit': api_over_100k * 1000,
            'fee': float(api_usage_fee)
        }
        
        # Storage overage
        storage_fee_per_gb = Decimal('0.05')  # $0.05 per GB
        storage_limit = plan.get('max_storage_gb', 10)
        storage_overage = max(0, metrics.storage_gb - storage_limit)
        storage_fee = storage_overage * storage_fee_per_gb
        usage_amount += storage_fee
        usage_details['storage'] = {
            'gb_used': metrics.storage_gb,
            'limit': storage_limit,
            'overage_gb': storage_overage,
            'fee': float(storage_fee)
        }
        
        # Bandwidth overage
        bandwidth_fee_per_gb = Decimal('0.10')  # $0.10 per GB
        bandwidth_limit = plan.get('max_bandwidth_gb_per_month', 100)
        bandwidth_overage = max(0, metrics.bandwidth_gb - bandwidth_limit)
        bandwidth_fee = bandwidth_overage * bandwidth_fee_per_gb
        usage_amount += bandwidth_fee
        usage_details['bandwidth'] = {
            'gb_used': metrics.bandwidth_gb,
            'limit': bandwidth_limit,
            'overage_gb': bandwidth_overage,
            'fee': float(bandwidth_fee)
        }
        
        return usage_amount, usage_details
    
    def _calculate_overages(self, metrics: UsageMetrics, plan: Dict) -> tuple[Decimal, Dict]:
        """Calculate overage fees"""
        overage_amount = Decimal('0.00')
        overage_details = {}
        
        # Chain deployment overage
        deployments_limit = plan.get('max_deployments_per_month', 100)
        if deployments_limit > 0:  # Only if there's a limit
            deployment_overage = max(0, metrics.chain_deployments - deployments_limit)
            if deployment_overage > 0:
                deployment_fee = deployment_overage * Decimal('10.00')  # $10 per deployment
                overage_amount += deployment_fee
                overage_details['chain_deployments'] = {
                    'count': metrics.chain_deployments,
                    'limit': deployments_limit,
                    'overage_count': deployment_overage,
                    'fee': float(deployment_fee)
                }
        
        # Additional feature fees
        feature_fee_per_month = Decimal('50.00')  # $50 per additional feature
        additional_features = len(metrics.additional_features)
        if additional_features > 0:
            feature_fee = additional_features * feature_fee_per_month
            overage_amount += feature_fee
            overage_details['additional_features'] = {
                'features': metrics.additional_features,
                'count': additional_features,
                'fee': float(feature_fee)
            }
        
        return overage_amount, overage_details
    
    def _calculate_discounts(self, subscription: Subscription) -> Decimal:
        """Calculate discount amounts"""
        discount_amount = Decimal('0.00')
        
        # Yearly subscription discount (20% off)
        if subscription.billing_cycle == 'yearly':
            yearly_discount = Decimal('0.20')
            plan_price = Decimal('0')  # This would come from plan data
            discount_amount += subscription.amount * yearly_discount
        
        # Volume discounts for Enterprise plans
        if subscription.plan_name in ['enterprise', 'sovereign']:
            # 5% discount for subscriptions > 1 year
            if subscription.created_at < (datetime.now() - timedelta(days=365)):
                volume_discount = Decimal('0.05')
                discount_amount += subscription.amount * volume_discount
        
        return discount_amount
    
    def _calculate_taxes(self, subtotal: Decimal) -> Decimal:
        """Calculate tax amounts (simplified)"""
        # This would integrate with tax calculation services
        # For now, use a simple tax rate
        tax_rate = Decimal('0.08')  # 8% tax rate
        return subtotal * tax_rate
    
    def _get_applied_discounts(self, subscription: Subscription) -> List[Dict]:
        """Get list of applied discounts"""
        discounts = []
        
        if subscription.billing_cycle == 'yearly':
            discounts.append({
                'type': 'yearly_subscription',
                'description': '20% yearly subscription discount',
                'amount': float(subscription.amount * Decimal('0.20'))
            })
        
        return discounts
    
    def _get_tax_breakdown(self) -> Dict:
        """Get tax breakdown (simplified)"""
        return {
            'tax_rate': '8%',
            'jurisdiction': 'US',
            'tax_type': 'sales_tax'
        }

# Initialize billing manager
billing_manager = BillingManager()

@billing_bp.route('/plans', methods=['GET'])
def get_subscription_plans():
    """Get all available subscription plans"""
    try:
        plans = billing_manager.get_subscription_plans()
        return jsonify({
            'success': True,
            'data': plans,
            'message': 'Subscription plans retrieved successfully'
        })
    except Exception as e:
        logger.error(f"Error retrieving subscription plans: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve subscription plans'
        }), 500

@billing_bp.route('/current-plan', methods=['GET'])
@jwt_required()
def get_current_plan():
    """Get current user's subscription plan"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        subscription = Subscription.query.filter_by(
            user_id=user.id,
            status='active'
        ).first()
        
        if not subscription:
            return jsonify({
                'success': True,
                'data': None,
                'message': 'No active subscription found'
            })
        
        plan_details = next((p for p in billing_manager.get_subscription_plans() 
                           if p['name'] == subscription.plan_name), None)
        
        return jsonify({
            'success': True,
            'data': {
                'subscription': asdict(subscription),
                'plan': plan_details,
                'usage': get_current_usage_summary(user.id)
            },
            'message': 'Current plan retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error retrieving current plan: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve current plan'
        }), 500

@billing_bp.route('/usage', methods=['GET'])
@jwt_required()
def get_usage_summary():
    """Get usage summary for current billing period"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Get current billing period
        subscription = Subscription.query.filter_by(
            user_id=user.id,
            status='active'
        ).first()
        
        if not subscription:
            return jsonify({
                'success': False,
                'error': 'No active subscription'
            }), 404
        
        # Calculate billing period dates
        period_start = subscription.billing_cycle_start
        period_end = subscription.billing_cycle_start + timedelta(days=30)
        
        # Calculate billing
        billing_calc = billing_manager.calculate_billing(user, period_start, period_end)
        
        return jsonify({
            'success': True,
            'data': {
                'period': {
                    'start': period_start.isoformat(),
                    'end': period_end.isoformat()
                },
                'usage': billing_calc.usage_details,
                'estimated_bill': {
                    'base_amount': float(billing_calc.base_amount),
                    'usage_amount': float(billing_calc.usage_amount),
                    'overage_amount': float(billing_calc.overage_amount),
                    'discount_amount': float(billing_calc.discount_amount),
                    'tax_amount': float(billing_calc.tax_amount),
                    'total_amount': float(billing_calc.total_amount)
                }
            },
            'message': 'Usage summary retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error retrieving usage summary: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve usage summary'
        }), 500

@billing_bp.route('/billing-history', methods=['GET'])
@jwt_required()
def get_billing_history():
    """Get billing history for user"""
    try:
        user_id = get_jwt_identity()
        
        # Get invoices for user
        invoices = Invoice.query.filter_by(
            user_id=user_id
        ).order_by(Invoice.created_at.desc()).limit(50).all()
        
        invoices_data = [asdict(invoice) for invoice in invoices]
        
        return jsonify({
            'success': True,
            'data': invoices_data,
            'message': 'Billing history retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error retrieving billing history: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve billing history'
        }), 500

@billing_bp.route('/subscription/change', methods=['POST'])
@jwt_required()
@validate_subscription_data
def change_subscription_plan():
    """Change subscription plan"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        data = request.get_json()
        new_plan = data.get('plan_name')
        billing_cycle = data.get('billing_cycle', 'monthly')
        immediate_change = data.get('immediate', False)
        
        # Get subscription plans
        plans = billing_manager.get_subscription_plans()
        new_plan_details = next((p for p in plans if p['name'] == new_plan), None)
        
        if not new_plan_details:
            return jsonify({
                'success': False,
                'error': 'Invalid plan name'
            }), 400
        
        # Get current subscription
        current_subscription = Subscription.query.filter_by(
            user_id=user.id,
            status='active'
        ).first()
        
        if not current_subscription:
            return jsonify({
                'success': False,
                'error': 'No active subscription found'
            }), 404
        
        # Calculate pro-rated pricing
        price = new_plan_details['price_monthly']
        if billing_cycle == 'yearly':
            price = new_plan_details['price_yearly']
        
        # Create new subscription or update existing
        if immediate_change:
            # Update existing subscription immediately
            current_subscription.plan_name = new_plan
            current_subscription.billing_cycle = billing_cycle
            current_subscription.amount = Decimal(str(price))
            current_subscription.updated_at = datetime.utcnow()
            
            # Create billing record
            self._create_subscription_change_record(user, current_subscription, 'immediate')
        else:
            # Schedule change for next billing cycle
            self._schedule_subscription_change(user, current_subscription, new_plan, billing_cycle)
        
        return jsonify({
            'success': True,
            'data': {
                'plan_name': new_plan,
                'billing_cycle': billing_cycle,
                'price': price,
                'effective_date': datetime.utcnow().isoformat() if immediate_change else 'next_billing_cycle'
            },
            'message': f'Subscription changed to {new_plan} plan successfully'
        })
        
    except Exception as e:
        logger.error(f"Error changing subscription plan: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to change subscription plan'
        }), 500

@billing_bp.route('/payment/methods', methods=['GET'])
@jwt_required()
def get_payment_methods():
    """Get user's payment methods"""
    try:
        user_id = get_jwt_identity()
        
        # In a real implementation, this would integrate with Stripe
        # For now, return placeholder payment methods
        payment_methods = [
            {
                'id': 'pm_123456789',
                'type': 'card',
                'card': {
                    'brand': 'visa',
                    'last4': '4242',
                    'exp_month': 12,
                    'exp_year': 2025
                },
                'is_default': True,
                'created': datetime.utcnow().isoformat()
            }
        ]
        
        return jsonify({
            'success': True,
            'data': payment_methods,
            'message': 'Payment methods retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error retrieving payment methods: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve payment methods'
        }), 500

@billing_bp.route('/payment/methods', methods=['POST'])
@jwt_required()
def add_payment_method():
    """Add a new payment method"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # In a real implementation, this would integrate with Stripe
        # For now, simulate adding a payment method
        payment_method_id = f"pm_{str(uuid.uuid4())[:12]}"
        
        # Log the payment method addition
        logger.info(f"Added payment method {payment_method_id} for user {user_id}")
        
        return jsonify({
            'success': True,
            'data': {
                'payment_method_id': payment_method_id,
                'type': data.get('type', 'card'),
                'is_default': data.get('is_default', False)
            },
            'message': 'Payment method added successfully'
        })
        
    except Exception as e:
        logger.error(f"Error adding payment method: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to add payment method'
        }), 500

@billing_bp.route('/invoice/<invoice_id>', methods=['GET'])
@jwt_required()
def get_invoice(invoice_id):
    """Get specific invoice details"""
    try:
        user_id = get_jwt_identity()
        
        invoice = Invoice.query.filter_by(
            id=invoice_id,
            user_id=user_id
        ).first()
        
        if not invoice:
            return jsonify({
                'success': False,
                'error': 'Invoice not found'
            }), 404
        
        # In a real implementation, generate PDF invoice
        return jsonify({
            'success': True,
            'data': asdict(invoice),
            'message': 'Invoice retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error retrieving invoice: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve invoice'
        }), 500

@billing_bp.route('/analytics', methods=['GET'])
@jwt_required()
def get_billing_analytics():
    """Get billing analytics (for admin users)"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        # Only allow admin users to access billing analytics
        if user.role != 'admin':
            return jsonify({
                'success': False,
                'error': 'Insufficient permissions'
            }), 403
        
        # Calculate various analytics metrics
        analytics = self._calculate_billing_analytics()
        
        return jsonify({
            'success': True,
            'data': analytics,
            'message': 'Billing analytics retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error retrieving billing analytics: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve billing analytics'
        }), 500

def get_current_usage_summary(user_id: str) -> Dict:
    """Get current usage summary for a user"""
    from ..models import db, UsageRecord, Subscription
    
    subscription = Subscription.query.filter_by(
        user_id=user_id,
        status='active'
    ).first()
    
    if not subscription:
        return {}
    
    period_start = subscription.billing_cycle_start
    period_end = period_start + timedelta(days=30)
    
    usage_records = UsageRecord.query.filter(
        and_(
            UsageRecord.user_id == user_id,
            UsageRecord.timestamp >= period_start,
            UsageRecord.timestamp < period_end
        )
    ).all()
    
    usage_metrics = billing_manager._aggregate_usage(usage_records)
    
    plan_details = next((p for p in billing_manager.get_subscription_plans() 
                        if p['name'] == subscription.plan_name), {})
    
    return {
        'period_start': period_start.isoformat(),
        'period_end': period_end.isoformat(),
        'metrics': {
            'chain_deployments': usage_metrics.chain_deployments,
            'api_requests': usage_metrics.api_requests,
            'storage_gb': round(usage_metrics.storage_gb, 2),
            'bandwidth_gb': round(usage_metrics.bandwidth_gb, 2),
            'computing_hours': round(usage_metrics.computing_hours, 2),
            'additional_features': usage_metrics.additional_features
        },
        'limits': {
            'max_chains': plan_details.get('max_chains', 1),
            'max_deployments_per_month': plan_details.get('max_deployments_per_month', 100),
            'max_storage_gb': plan_details.get('max_storage_gb', 10),
            'max_api_requests_per_month': plan_details.get('max_api_requests_per_month', 10000),
            'max_bandwidth_gb_per_month': plan_details.get('max_bandwidth_gb_per_month', 100)
        },
        'usage_percentages': {
            'chains': (usage_metrics.chain_deployments / max(1, plan_details.get('max_chains', 1))) * 100,
            'deployments': (usage_metrics.chain_deployments / max(1, plan_details.get('max_deployments_per_month', 100))) * 100,
            'storage': (usage_metrics.storage_gb / max(1, plan_details.get('max_storage_gb', 10))) * 100,
            'api_requests': (usage_metrics.api_requests / max(1, plan_details.get('max_api_requests_per_month', 10000))) * 100,
            'bandwidth': (usage_metrics.bandwidth_gb / max(1, plan_details.get('max_bandwidth_gb_per_month', 100))) * 100
        }
    }

def _create_subscription_change_record(self, user: User, subscription: Subscription, change_type: str):
    """Create record for subscription change"""
    from ..models import SubscriptionChange
    
    change = SubscriptionChange(
        user_id=user.id,
        subscription_id=subscription.id,
        change_type=change_type,
        old_plan=subscription.plan_name,
        new_plan=subscription.plan_name,
        effective_date=datetime.utcnow(),
        processed=True
    )
    
    db.session.add(change)
    db.session.commit()
    
    logger.info(f"Subscription change recorded: {user.id} - {change_type}")

def _schedule_subscription_change(self, user: User, subscription: Subscription, new_plan: str, billing_cycle: str):
    """Schedule subscription change for next billing cycle"""
    from ..models import SubscriptionChange
    
    change = SubscriptionChange(
        user_id=user.id,
        subscription_id=subscription.id,
        change_type='scheduled',
        old_plan=subscription.plan_name,
        new_plan=new_plan,
        new_billing_cycle=billing_cycle,
        effective_date=subscription.billing_cycle_start + timedelta(days=30),
        processed=False
    )
    
    db.session.add(change)
    db.session.commit()
    
    logger.info(f"Subscription change scheduled: {user.id} - {new_plan}")

def _calculate_billing_analytics(self) -> Dict:
    """Calculate billing analytics for admin dashboard"""
    from ..models import db, Subscription, User, Invoice, UsageRecord
    from sqlalchemy import func
    
    # Revenue metrics
    current_month_revenue = db.session.query(
        func.sum(Invoice.amount)
    ).filter(
        Invoice.status == 'paid',
        Invoice.created_at >= datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    ).scalar() or 0
    
    # Subscription metrics
    total_subscriptions = Subscription.query.filter_by(status='active').count()
    plan_distribution = db.session.query(
        Subscription.plan_name,
        func.count(Subscription.id).label('count')
    ).filter_by(status='active').group_by(Subscription.plan_name).all()
    
    # Customer metrics
    total_customers = User.query.filter_by(is_active=True).count()
    new_customers_this_month = User.query.filter(
        User.created_at >= datetime.utcnow().replace(day=1)
    ).count()
    
    # Usage metrics
    total_api_requests = UsageRecord.query.filter(
        UsageRecord.metric_name == 'api_requests',
        UsageRecord.timestamp >= datetime.utcnow().replace(day=1)
    ).count()
    
    total_deployments = UsageRecord.query.filter(
        UsageRecord.metric_name == 'chain_deployments',
        UsageRecord.timestamp >= datetime.utcnow().replace(day=1)
    ).count()
    
    return {
        'revenue': {
            'current_month': float(current_month_revenue),
            'currency': 'USD'
        },
        'subscriptions': {
            'total_active': total_subscriptions,
            'by_plan': {plan: count for plan, count in plan_distribution}
        },
        'customers': {
            'total': total_customers,
            'new_this_month': new_customers_this_month
        },
        'usage': {
            'total_api_requests': total_api_requests,
            'total_deployments': total_deployments
        },
        'generated_at': datetime.utcnow().isoformat()
    }

# Usage tracking endpoints
@billing_bp.route('/track-usage', methods=['POST'])
@jwt_required()
def track_usage():
    """Track user usage for billing"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        metric_name = data.get('metric_name')
        metric_value = data.get('metric_value', 0)
        metadata = data.get('metadata', {})
        
        if not metric_name:
            return jsonify({
                'success': False,
                'error': 'metric_name is required'
            }), 400
        
        # Create usage record
        usage_record = UsageRecord(
            user_id=user_id,
            metric_name=metric_name,
            metric_value=metric_value,
            metadata=metadata,
            timestamp=datetime.utcnow()
        )
        
        db.session.add(usage_record)
        db.session.commit()
        
        logger.info(f"Usage tracked: {user_id} - {metric_name}: {metric_value}")
        
        return jsonify({
            'success': True,
            'message': 'Usage tracked successfully'
        })
        
    except Exception as e:
        logger.error(f"Error tracking usage: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to track usage'
        }), 500

@billing_bp.route('/billing-portal', methods=['POST'])
@jwt_required()
def create_billing_portal_session():
    """Create billing portal session for customer self-service"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # In a real implementation, create Stripe billing portal session
        portal_url = f"https://billing.cosmosbuilder.com/portal/{user_id}"
        
        return jsonify({
            'success': True,
            'data': {
                'portal_url': portal_url,
                'expires_at': (datetime.utcnow() + timedelta(hours=24)).isoformat()
            },
            'message': 'Billing portal session created successfully'
        })
        
    except Exception as e:
        logger.error(f"Error creating billing portal session: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to create billing portal session'
        }), 500

# Webhook endpoints for payment processing
@billing_bp.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    try:
        payload = request.get_data()
        sig_header = request.headers.get('Stripe-Signature')
        
        # In a real implementation, verify webhook signature
        # and process Stripe webhook events
        
        event = json.loads(payload)
        
        if event['type'] == 'payment_intent.succeeded':
            payment_id = event['data']['object']['id']
            # Process successful payment
            logger.info(f"Payment succeeded: {payment_id}")
        
        elif event['type'] == 'payment_intent.payment_failed':
            payment_id = event['data']['object']['id']
            # Handle failed payment
            logger.warning(f"Payment failed: {payment_id}")
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        logger.error(f"Stripe webhook error: {str(e)}")
        return jsonify({'success': False}), 400