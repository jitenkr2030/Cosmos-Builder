"""
CosmosBuilder Monetization Application
Author: MiniMax Agent
Date: 2025-11-27

Main monetization application module that integrates all monetization components
including billing, payments, usage tracking, and analytics.
"""

from flask import Flask, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

# Import monetization modules
from .billing import billing_bp
from .usage_tracking import usage_bp
from .payment_processing import payments_bp
from .portal_analytics import portal_bp, analytics_bp
from .models import db, create_monetization_tables

def create_monetization_app(config=None):
    """Create monetization application"""
    app = Flask(__name__)
    
    # Default configuration
    app.config.update({
        'SQLALCHEMY_DATABASE_URI': 'postgresql://cosmosbuilder:cosmosbuilder_dev_password@localhost:5432/cosmosbuilder',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'JWT_SECRET_KEY': 'dev-jwt-secret-key',
        'STRIPE_SECRET_KEY': 'sk_test_your_key',
        'STRIPE_WEBHOOK_SECRET': 'whsec_your_secret'
    })
    
    # Override with custom config if provided
    if config:
        app.config.update(config)
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    jwt = JWTManager(app)
    
    # Register blueprints
    app.register_blueprint(billing_bp)
    app.register_blueprint(usage_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(portal_bp)
    app.register_blueprint(analytics_bp)
    
    # Initialize database tables
    with app.app_context():
        create_monetization_tables()
    
    return app

# Monetization API Blueprint for main application integration
monetization_bp = Blueprint('monetization', __name__)

# Helper functions for main application integration

def init_monetization(app: Flask, db_instance):
    """Initialize monetization system in main application"""
    from .billing import billing_bp
    from .usage_tracking import usage_bp
    from .payment_processing import payments_bp
    from .portal_analytics import portal_bp, analytics_bp
    
    # Register blueprints
    app.register_blueprint(billing_bp)
    app.register_blueprint(usage_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(portal_bp)
    app.register_blueprint(analytics_bp)
    
    # Make monetization models available to main app
    app.monetization_models = {
        'Subscription': db_instance.model('Subscription'),
        'UsageRecord': db_instance.model('UsageRecord'),
        'Invoice': db_instance.model('Invoice'),
        'Payment': db_instance.model('Payment'),
        'BillingAlert': db_instance.model('BillingAlert'),
        'DiscountCode': db_instance.model('DiscountCode')
    }
    
    # Add usage tracking middleware
    from .usage_tracking import UsageTrackingMiddleware
    app.before_request(UsageTrackingMiddleware.track_request_before_request)
    app.after_request(UsageTrackingMiddleware.track_request_after_request)

def get_user_usage_summary(user_id: str, period_days: int = 30) -> dict:
    """Get usage summary for a user (helper function)"""
    from .usage_tracking import usage_tracker
    from .billing import billing_manager
    from .models import Subscription
    
    subscription = Subscription.query.filter_by(
        user_id=user_id,
        status='active'
    ).first()
    
    if not subscription:
        return {'error': 'No active subscription'}
    
    usage_summary = usage_tracker.get_usage_summary(user_id, period_days)
    billing_calc = billing_manager.calculate_billing(
        user_id=user_id,
        period_start=usage_summary.period_start,
        period_end=usage_summary.period_end
    )
    
    return {
        'usage': usage_summary,
        'billing': billing_calc
    }

def track_api_usage(user_id: str, endpoint: str, method: str = 'GET') -> bool:
    """Track API usage for billing"""
    from .usage_tracking import usage_tracker
    
    return usage_tracker.track_usage(
        user_id=user_id,
        metric_name='api_requests',
        value=1,
        metadata={
            'endpoint': endpoint,
            'method': method,
            'timestamp': datetime.utcnow().isoformat()
        }
    )

def check_usage_limits(user_id: str, metric_name: str, requested_value: int = 1) -> dict:
    """Check if user can perform action based on usage limits"""
    from .usage_tracking import usage_tracker
    from .billing import billing_manager
    from .models import Subscription
    
    subscription = Subscription.query.filter_by(
        user_id=user_id,
        status='active'
    ).first()
    
    if not subscription:
        return {'allowed': False, 'reason': 'No active subscription'}
    
    # Get current usage
    usage_summary = usage_tracker.get_usage_summary(user_id)
    current_usage = usage_summary.metrics.get(metric_name, {}).get('total', 0)
    
    # Get limit
    limit = usage_summary.limits.get(metric_name)
    if not limit:
        return {'allowed': True, 'reason': 'No limit defined'}
    
    if limit.limit <= 0:  # Unlimited
        return {'allowed': True, 'reason': 'Unlimited usage'}
    
    # Check if request would exceed limit
    total_usage = current_usage + requested_value
    usage_percentage = (total_usage / limit.limit) * 100
    
    if usage_percentage > 100:
        return {
            'allowed': False, 
            'reason': 'Usage limit exceeded',
            'current_usage': current_usage,
            'limit': limit.limit,
            'overage': total_usage - limit.limit
        }
    elif usage_percentage >= (limit.warning_threshold * 100):
        return {
            'allowed': True,
            'warning': 'Approaching usage limit',
            'current_usage': current_usage,
            'limit': limit.limit,
            'usage_percentage': usage_percentage
        }
    
    return {
        'allowed': True,
        'current_usage': current_usage,
        'limit': limit.limit,
        'usage_percentage': usage_percentage
    }

def get_billing_estimate(user_id: str) -> dict:
    """Get current billing estimate for user"""
    from .billing import billing_manager
    from .models import Subscription, User
    
    user = User.query.get(user_id)
    subscription = Subscription.query.filter_by(
        user_id=user_id,
        status='active'
    ).first()
    
    if not user or not subscription:
        return {'error': 'User or subscription not found'}
    
    return billing_manager.calculate_billing(
        user=user,
        period_start=subscription.billing_cycle_start,
        period_end=subscription.billing_cycle_end
    )

def create_usage_alert(user_id: str, alert_type: str, title: str, message: str, 
                      severity: str = 'normal') -> str:
    """Create usage alert for user"""
    from .models import BillingAlert, db
    
    alert = BillingAlert(
        user_id=user_id,
        alert_type=alert_type,
        title=title,
        message=message,
        severity=severity,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    
    db.session.add(alert)
    db.session.commit()
    
    return alert.id

def validate_discount_code(code: str, user_id: str) -> dict:
    """Validate discount code for user"""
    from .models import DiscountCode, User
    
    code = code.upper().strip()
    discount = DiscountCode.query.filter_by(code=code).first()
    
    if not discount or not discount.is_valid():
        return {'valid': False, 'error': 'Invalid or expired discount code'}
    
    user = User.query.get(user_id)
    if not discount.can_be_used_by_user(user):
        return {'valid': False, 'error': 'Discount code cannot be used with your current subscription'}
    
    return {
        'valid': True,
        'code': discount.code,
        'discount_type': discount.discount_type,
        'discount_value': float(discount.discount_value),
        'description': discount.description
    }

def get_subscription_metrics() -> dict:
    """Get platform subscription metrics"""
    from .models import Subscription, User
    from sqlalchemy import func
    
    # Total subscriptions
    total_subscriptions = Subscription.query.filter_by(status='active').count()
    
    # Subscriptions by plan
    plan_distribution = db.session.query(
        Subscription.plan_name,
        func.count(Subscription.id)
    ).filter_by(status='active').group_by(Subscription.plan_name).all()
    
    # New subscriptions this month
    current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_subscriptions = Subscription.query.filter(
        Subscription.created_at >= current_month
    ).count()
    
    # Churned subscriptions this month
    churned_subscriptions = Subscription.query.filter(
        Subscription.cancelled_at >= current_month
    ).count()
    
    # Revenue by plan
    plan_revenue = {}
    for plan_name, count in plan_distribution:
        plan_revenue[plan_name] = {
            'subscription_count': count,
            'estimated_monthly_revenue': count * get_plan_price(plan_name)
        }
    
    return {
        'total_active_subscriptions': total_subscriptions,
        'new_subscriptions_this_month': new_subscriptions,
        'churned_subscriptions_this_month': churned_subscriptions,
        'plan_distribution': dict(plan_distribution),
        'plan_revenue': plan_revenue,
        'generated_at': datetime.utcnow().isoformat()
    }

def get_plan_price(plan_name: str) -> float:
    """Get price for a subscription plan"""
    from .billing import billing_manager
    
    plans = billing_manager.get_subscription_plans()
    plan = next((p for p in plans if p['name'] == plan_name), None)
    
    return plan['price_monthly'] if plan else 0.0

def is_trial_user(user_id: str) -> bool:
    """Check if user is on trial"""
    from .models import Subscription
    
    subscription = Subscription.query.filter_by(
        user_id=user_id,
        status='active'
    ).first()
    
    return subscription.is_trial_active if subscription else False

def get_trial_remaining_days(user_id: str) -> int:
    """Get remaining trial days"""
    from .models import Subscription
    
    subscription = Subscription.query.filter_by(
        user_id=user_id,
        status='active'
    ).first()
    
    if subscription and subscription.is_trial_active:
        remaining = (subscription.trial_end - datetime.utcnow()).days
        return max(0, remaining)
    
    return 0

# Import datetime for helper functions
from datetime import datetime, timedelta

# Decorators for easy integration
def subscription_required(view_func):
    """Decorator to require active subscription"""
    from flask_jwt_extended import get_jwt_identity
    from functools import wraps
    from .models import Subscription
    
    @wraps(view_func)
    def decorated_function(*args, **kwargs):
        user_id = get_jwt_identity()
        subscription = Subscription.query.filter_by(
            user_id=user_id,
            status='active'
        ).first()
        
        if not subscription:
            return {'error': 'Active subscription required'}, 403
        
        if subscription.is_trial_active:
            remaining_days = get_trial_remaining_days(user_id)
            if remaining_days <= 0:
                return {'error': 'Trial period has expired'}, 403
        
        return view_func(*args, **kwargs)
    
    return decorated_function

def usage_limit_check(metric_name: str, max_value: int = 1):
    """Decorator to check usage limits before API calls"""
    from flask_jwt_extended import get_jwt_identity
    from functools import wraps
    
    def decorator(view_func):
        @wraps(view_func)
        def decorated_function(*args, **kwargs):
            user_id = get_jwt_identity()
            check_result = check_usage_limits(user_id, metric_name, max_value)
            
            if not check_result['allowed']:
                return {'error': check_result['reason']}, 429
            
            return view_func(*args, **kwargs)
        
        return decorated_function
    
    return decorator

# Configuration management
def configure_monetization(app: Flask):
    """Configure monetization for Flask app"""
    
    # Environment variables
    app.config['STRIPE_SECRET_KEY'] = app.config.get('STRIPE_SECRET_KEY', '')
    app.config['STRIPE_PUBLISHABLE_KEY'] = app.config.get('STRIPE_PUBLISHABLE_KEY', '')
    app.config['STRIPE_WEBHOOK_SECRET'] = app.config.get('STRIPE_WEBHOOK_SECRET', '')
    
    # Billing settings
    app.config['BILLING_CURRENCY'] = app.config.get('BILLING_CURRENCY', 'USD')
    app.config['BILLING_TAX_RATE'] = app.config.get('BILLING_TAX_RATE', 0.08)
    
    # Usage tracking settings
    app.config['USAGE_TRACKING_ENABLED'] = app.config.get('USAGE_TRACKING_ENABLED', True)
    app.config['USAGE_BATCH_SIZE'] = app.config.get('USAGE_BATCH_SIZE', 100)
    
    # Alert settings
    app.config['USAGE_ALERT_THRESHOLDS'] = app.config.get('USAGE_ALERT_THRESHOLDS', {
        'warning': 0.8,
        'critical': 0.9
    })

# Health check endpoint
@monetization_bp.route('/health')
def monetization_health():
    """Health check for monetization system"""
    try:
        # Check database connection
        db.engine.execute('SELECT 1')
        
        # Check Stripe connection
        # In production, this would test Stripe connectivity
        
        return {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'components': {
                'database': 'healthy',
                'billing': 'healthy',
                'usage_tracking': 'healthy'
            }
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }, 500

# API documentation endpoint
@monetization_bp.route('/docs')
def monetization_docs():
    """API documentation for monetization endpoints"""
    docs = {
        'title': 'CosmosBuilder Monetization API',
        'version': '1.0',
        'base_url': '/api',
        'endpoints': {
            'billing': {
                'GET /billing/plans': 'Get subscription plans',
                'GET /billing/current-plan': 'Get current subscription',
                'GET /billing/usage': 'Get usage summary',
                'GET /billing/billing-history': 'Get billing history'
            },
            'usage': {
                'POST /usage/track': 'Track usage',
                'GET /usage/summary': 'Get usage summary',
                'GET /usage/limits': 'Get usage limits'
            },
            'payments': {
                'POST /payments/subscribe': 'Create subscription',
                'POST /payments/subscription/change': 'Change subscription',
                'GET /payments/payment-methods': 'Get payment methods'
            },
            'portal': {
                'GET /portal/dashboard': 'Get customer dashboard',
                'GET /portal/usage-analytics': 'Get usage analytics'
            },
            'analytics': {
                'GET /analytics/revenue': 'Get revenue analytics',
                'GET /analytics/summary': 'Get analytics summary'
            }
        }
    }
    return docs

# Main initialization
if __name__ == '__main__':
    # Create and run monetization app for testing
    app = create_monetization_app()
    app.run(debug=True, host='0.0.0.0', port=8001)