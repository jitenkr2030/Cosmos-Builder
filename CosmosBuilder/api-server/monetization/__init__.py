"""
CosmosBuilder Monetization Module
Author: MiniMax Agent
Date: 2025-11-27

Complete monetization system for CosmosBuilder platform including:
- Subscription management
- Payment processing
- Usage tracking
- Billing and invoicing
- Customer portal
- Revenue analytics
"""

__version__ = '1.0.0'
__author__ = 'MiniMax Agent'

# Import main components
from .app import (
    create_monetization_app,
    init_monetization,
    get_user_usage_summary,
    track_api_usage,
    check_usage_limits,
    get_billing_estimate,
    create_usage_alert,
    validate_discount_code,
    get_subscription_metrics,
    is_trial_user,
    get_trial_remaining_days,
    subscription_required,
    usage_limit_check,
    configure_monetization
)

from .models import (
    Subscription,
    UsageRecord,
    Invoice,
    Payment,
    BillingAlert,
    DiscountCode,
    DiscountUsage,
    SubscriptionChange,
    create_monetization_tables
)

from .billing import BillingManager, billing_manager
from .usage_tracking import UsageTracker, usage_tracker
from .payment_processing import PaymentProcessor, payment_processor
from .portal_analytics import CustomerPortal, RevenueAnalytics, customer_portal, revenue_analytics

# Import blueprints
from .billing import billing_bp
from .usage_tracking import usage_bp
from .payment_processing import payments_bp
from .portal_analytics import portal_bp, analytics_bp

# Main monetization blueprint
from .app import monetization_bp

__all__ = [
    # Main functions
    'create_monetization_app',
    'init_monetization',
    'get_user_usage_summary',
    'track_api_usage',
    'check_usage_limits',
    'get_billing_estimate',
    'create_usage_alert',
    'validate_discount_code',
    'get_subscription_metrics',
    'is_trial_user',
    'get_trial_remaining_days',
    'subscription_required',
    'usage_limit_check',
    'configure_monetization',
    
    # Models
    'Subscription',
    'UsageRecord',
    'Invoice',
    'Payment',
    'BillingAlert',
    'DiscountCode',
    'DiscountUsage',
    'SubscriptionChange',
    'create_monetization_tables',
    
    # Core managers
    'BillingManager',
    'billing_manager',
    'UsageTracker',
    'usage_tracker',
    'PaymentProcessor',
    'payment_processor',
    'CustomerPortal',
    'customer_portal',
    'RevenueAnalytics',
    'revenue_analytics',
    
    # Blueprints
    'billing_bp',
    'usage_bp',
    'payments_bp',
    'portal_bp',
    'analytics_bp',
    'monetization_bp'
]

# Module configuration
MONETIZATION_CONFIG = {
    'version': __version__,
    'author': __author__,
    'description': 'Complete monetization system for CosmosBuilder platform',
    'features': [
        'Subscription Management',
        'Payment Processing',
        'Usage Tracking',
        'Billing & Invoicing',
        'Customer Portal',
        'Revenue Analytics',
        'Discount Management',
        'Usage Alerts',
        'Multi-plan Support',
        'Trial Management'
    ]
}

# Quick setup functions
def setup_monetization_for_flask(app, database):
    """Quick setup function for Flask applications"""
    from .app import init_monetization, configure_monetization
    
    # Configure monetization
    configure_monetization(app)
    
    # Initialize with provided database
    init_monetization(app, database)
    
    # Set up monetization models in database
    with app.app_context():
        create_monetization_tables()

def get_monetization_status():
    """Get monetization system status"""
    return {
        'version': __version__,
        'status': 'ready',
        'config': MONETIZATION_CONFIG,
        'components': {
            'billing': 'active',
            'payment_processing': 'active',
            'usage_tracking': 'active',
            'customer_portal': 'active',
            'analytics': 'active'
        }
    }

# Usage examples and integration patterns
INTEGRATION_EXAMPLES = {
    'flask_app_integration': '''
from flask import Flask
from your_database import db
from cosmosbuilder.monetization import setup_monetization_for_flask

app = Flask(__name__)
app.config['DATABASE_URL'] = 'postgresql://...'

# Initialize database
db.init_app(app)

# Setup monetization
setup_monetization_for_flask(app, db)

@app.route('/api/your-endpoint')
@subscription_required
@usage_limit_check('api_requests', 1)
def your_api_endpoint():
    return {"message": "Protected by subscription and usage limits"}
    ''',
    
    'manual_integration': '''
from cosmosbuilder.monetization import check_usage_limits, track_api_usage

# Check if user can perform action
check_result = check_usage_limits(user_id, 'api_requests', 1)
if not check_result['allowed']:
    return {"error": check_result['reason']}, 429

# Track usage after successful operation
track_api_usage(user_id, '/api/some-endpoint', 'POST')
    ''',
    
    'billing_integration': '''
from cosmosbuilder.monetization import get_billing_estimate, create_usage_alert

# Get current billing estimate
billing = get_billing_estimate(user_id)
print(f"Current estimated bill: ${billing.total_amount}")

# Create alert for high usage
create_usage_alert(
    user_id=user_id,
    alert_type='usage_threshold',
    title='Storage Limit Warning',
    message='You have used 90% of your storage limit',
    severity='high'
)
    '''
}