"""
Monetization Models for CosmosBuilder
Author: MiniMax Agent
Date: 2025-11-27

Database models for subscription management, billing, and usage tracking.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, Index, CheckConstraint

db = SQLAlchemy()

class Subscription(db.Model):
    """User subscription model"""
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # Plan information
    plan_name = db.Column(db.String(50), nullable=False)  # starter, professional, enterprise, sovereign
    billing_cycle = db.Column(db.String(10), nullable=False, default='monthly')  # monthly, yearly
    
    # Pricing
    amount = db.Column(db.Numeric(10, 2), nullable=False)  # Current billing amount
    
    # Subscription status
    status = db.Column(db.String(20), nullable=False, default='active')  # active, cancelled, past_due, suspended
    trial_start = db.Column(db.DateTime)
    trial_end = db.Column(db.DateTime)
    
    # Billing cycle
    billing_cycle_start = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    billing_cycle_end = db.Column(db.DateTime, nullable=False)
    
    # Stripe integration
    stripe_subscription_id = db.Column(db.String(100), unique=True)
    stripe_customer_id = db.Column(db.String(100))
    stripe_price_id = db.Column(db.String(100))
    
    # Cancellation
    cancelled_at = db.Column(db.DateTime)
    cancellation_reason = db.Column(db.String(100))
    end_of_billing_period = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('subscriptions', lazy=True))
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.billing_cycle_end:
            self._set_billing_cycle_end()
    
    def _set_billing_cycle_end(self):
        """Set billing cycle end date based on billing cycle"""
        if self.billing_cycle == 'monthly':
            self.billing_cycle_end = self.billing_cycle_start + timedelta(days=30)
        elif self.billing_cycle == 'yearly':
            self.billing_cycle_end = self.billing_cycle_start + timedelta(days=365)
        else:
            self.billing_cycle_end = self.billing_cycle_start + timedelta(days=30)
    
    @property
    def is_trial_active(self) -> bool:
        """Check if trial is currently active"""
        if not self.trial_end:
            return False
        return datetime.utcnow() < self.trial_end
    
    @property
    def days_until_billing_cycle_end(self) -> int:
        """Get days until current billing cycle ends"""
        return (self.billing_cycle_end - datetime.utcnow()).days
    
    @property
    def plan_tier(self) -> int:
        """Get plan tier level (1-4)"""
        tier_mapping = {
            'starter': 1,
            'professional': 2,
            'enterprise': 3,
            'sovereign': 4
        }
        return tier_mapping.get(self.plan_name, 1)
    
    def can_upgrade_to(self, new_plan: str) -> bool:
        """Check if subscription can be upgraded to new plan"""
        current_tier = self.plan_tier
        tier_mapping = {
            'starter': 1,
            'professional': 2,
            'enterprise': 3,
            'sovereign': 4
        }
        new_tier = tier_mapping.get(new_plan, 0)
        return new_tier > current_tier
    
    def can_downgrade_to(self, new_plan: str) -> bool:
        """Check if subscription can be downgraded to new plan"""
        current_tier = self.plan_tier
        tier_mapping = {
            'starter': 1,
            'professional': 2,
            'enterprise': 3,
            'sovereign': 4
        }
        new_tier = tier_mapping.get(new_plan, 0)
        return new_tier < current_tier and self.status == 'active'
    
    def to_dict(self) -> dict:
        """Convert subscription to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'plan_name': self.plan_name,
            'billing_cycle': self.billing_cycle,
            'amount': float(self.amount) if self.amount else 0,
            'status': self.status,
            'trial_start': self.trial_start.isoformat() if self.trial_start else None,
            'trial_end': self.trial_end.isoformat() if self.trial_end else None,
            'is_trial_active': self.is_trial_active,
            'billing_cycle_start': self.billing_cycle_start.isoformat() if self.billing_cycle_start else None,
            'billing_cycle_end': self.billing_cycle_end.isoformat() if self.billing_cycle_end else None,
            'days_until_billing_cycle_end': self.days_until_billing_cycle_end,
            'plan_tier': self.plan_tier,
            'stripe_subscription_id': self.stripe_subscription_id,
            'stripe_customer_id': self.stripe_customer_id,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None,
            'cancellation_reason': self.cancellation_reason,
            'end_of_billing_period': self.end_of_billing_period,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class UsageRecord(db.Model):
    """Usage tracking for billing"""
    __tablename__ = 'usage_records'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # Usage metrics
    metric_name = db.Column(db.String(50), nullable=False)  # api_requests, chain_deployments, storage_gb, etc.
    metric_value = db.Column(db.Numeric(15, 4), nullable=False, default=0)
    
    # Metadata for additional context
    metadata = db.Column(db.JSON)
    
    # Timestamps
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('usage_records', lazy=True))
    
    # Indexes
    __table_args__ = (
        Index('idx_usage_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_usage_metric_name', 'metric_name'),
        Index('idx_usage_timestamp', 'timestamp'),
    )
    
    @property
    def metric_display_name(self) -> str:
        """Get display name for metric"""
        display_names = {
            'api_requests': 'API Requests',
            'chain_deployments': 'Chain Deployments',
            'storage_gb': 'Storage (GB)',
            'bandwidth_gb': 'Bandwidth (GB)',
            'computing_hours': 'Computing Hours',
            'storage_operations': 'Storage Operations',
            'api_operations': 'API Operations'
        }
        return display_names.get(self.metric_name, self.metric_name.title())
    
    def to_dict(self) -> dict:
        """Convert usage record to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'metric_name': self.metric_name,
            'metric_display_name': self.metric_display_name,
            'metric_value': float(self.metric_value) if self.metric_value else 0,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Invoice(db.Model):
    """Invoice model"""
    __tablename__ = 'invoices'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    subscription_id = db.Column(db.String(36), db.ForeignKey('subscriptions.id'))
    
    # Invoice details
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    invoice_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=False)
    
    # Billing period
    period_start = db.Column(db.DateTime, nullable=False)
    period_end = db.Column(db.DateTime, nullable=False)
    
    # Amounts
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    tax_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    discount_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Currency
    currency = db.Column(db.String(3), nullable=False, default='USD')
    
    # Status
    status = db.Column(db.String(20), nullable=False, default='draft')  # draft, sent, paid, overdue, cancelled
    
    # Stripe integration
    stripe_invoice_id = db.Column(db.String(100), unique=True)
    
    # PDF storage
    pdf_url = db.Column(db.String(500))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('invoices', lazy=True))
    subscription = db.relationship('Subscription', backref=db.backref('invoices', lazy=True))
    
    # Indexes
    __table_args__ = (
        Index('idx_invoice_user_date', 'user_id', 'invoice_date'),
        Index('idx_invoice_status', 'status'),
        Index('idx_invoice_number', 'invoice_number'),
    )
    
    @property
    def is_overdue(self) -> bool:
        """Check if invoice is overdue"""
        return self.status == 'sent' and datetime.utcnow() > self.due_date
    
    @property
    def days_overdue(self) -> int:
        """Get days overdue"""
        if not self.is_overdue:
            return 0
        return (datetime.utcnow() - self.due_date).days
    
    def to_dict(self) -> dict:
        """Convert invoice to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'subscription_id': self.subscription_id,
            'invoice_number': self.invoice_number,
            'invoice_date': self.invoice_date.isoformat() if self.invoice_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'amount': float(self.amount) if self.amount else 0,
            'tax_amount': float(self.tax_amount) if self.tax_amount else 0,
            'discount_amount': float(self.discount_amount) if self.discount_amount else 0,
            'total_amount': float(self.total_amount) if self.total_amount else 0,
            'currency': self.currency,
            'status': self.status,
            'is_overdue': self.is_overdue,
            'days_overdue': self.days_overdue,
            'stripe_invoice_id': self.stripe_invoice_id,
            'pdf_url': self.pdf_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Payment(db.Model):
    """Payment model"""
    __tablename__ = 'payments'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    invoice_id = db.Column(db.String(36), db.ForeignKey('invoices.id'), nullable=False)
    
    # Payment details
    payment_method = db.Column(db.String(20), nullable=False)  # card, bank_transfer, check, etc.
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False, default='USD')
    
    # Payment status
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, completed, failed, refunded
    transaction_id = db.Column(db.String(100))
    
    # Stripe integration
    stripe_payment_intent_id = db.Column(db.String(100), unique=True)
    stripe_charge_id = db.Column(db.String(100))
    
    # Payment dates
    payment_date = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('payments', lazy=True))
    invoice = db.relationship('Invoice', backref=db.backref('payments', lazy=True))
    
    # Indexes
    __table_args__ = (
        Index('idx_payment_user_date', 'user_id', 'created_at'),
        Index('idx_payment_status', 'status'),
        Index('idx_payment_transaction', 'transaction_id'),
    )
    
    @property
    def is_successful(self) -> bool:
        """Check if payment was successful"""
        return self.status == 'completed'
    
    def to_dict(self) -> dict:
        """Convert payment to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'invoice_id': self.invoice_id,
            'payment_method': self.payment_method,
            'amount': float(self.amount) if self.amount else 0,
            'currency': self.currency,
            'status': self.status,
            'is_successful': self.is_successful,
            'transaction_id': self.transaction_id,
            'stripe_payment_intent_id': self.stripe_payment_intent_id,
            'stripe_charge_id': self.stripe_charge_id,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class SubscriptionChange(db.Model):
    """Track subscription changes"""
    __tablename__ = 'subscription_changes'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    subscription_id = db.Column(db.String(36), db.ForeignKey('subscriptions.id'), nullable=False)
    
    # Change details
    change_type = db.Column(db.String(20), nullable=False)  # immediate, scheduled, cancellation
    old_plan = db.Column(db.String(50))
    new_plan = db.Column(db.String(50))
    old_billing_cycle = db.Column(db.String(10))
    new_billing_cycle = db.Column(db.String(10))
    old_amount = db.Column(db.Numeric(10, 2))
    new_amount = db.Column(db.Numeric(10, 2))
    
    # Processing
    effective_date = db.Column(db.DateTime, nullable=False)
    processed = db.Column(db.Boolean, default=False)
    processed_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('subscription_changes', lazy=True))
    subscription = db.relationship('Subscription', backref=db.backref('changes', lazy=True))
    
    def to_dict(self) -> dict:
        """Convert subscription change to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'subscription_id': self.subscription_id,
            'change_type': self.change_type,
            'old_plan': self.old_plan,
            'new_plan': self.new_plan,
            'old_billing_cycle': self.old_billing_cycle,
            'new_billing_cycle': self.new_billing_cycle,
            'old_amount': float(self.old_amount) if self.old_amount else 0,
            'new_amount': float(self.new_amount) if self.new_amount else 0,
            'effective_date': self.effective_date.isoformat() if self.effective_date else None,
            'processed': self.processed,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class BillingAlert(db.Model):
    """Billing alerts and notifications"""
    __tablename__ = 'billing_alerts'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # Alert details
    alert_type = db.Column(db.String(50), nullable=False)  # usage_threshold, payment_failed, subscription_expiring
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), nullable=False, default='normal')  # low, normal, high, critical
    
    # Alert data
    threshold_percentage = db.Column(db.Numeric(5, 2))  # For usage alerts
    current_usage = db.Column(db.Numeric(15, 4))  # Current usage value
    limit_value = db.Column(db.Numeric(15, 4))  # Usage limit
    
    # Status
    is_read = db.Column(db.Boolean, default=False)
    action_required = db.Column(db.Boolean, default=False)
    action_taken_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('billing_alerts', lazy=True))
    
    # Indexes
    __table_args__ = (
        Index('idx_billing_alert_user_created', 'user_id', 'created_at'),
        Index('idx_billing_alert_unread', 'user_id', 'is_read'),
    )
    
    @property
    def is_expired(self) -> bool:
        """Check if alert has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self) -> dict:
        """Convert billing alert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'alert_type': self.alert_type,
            'title': self.title,
            'message': self.message,
            'severity': self.severity,
            'threshold_percentage': float(self.threshold_percentage) if self.threshold_percentage else None,
            'current_usage': float(self.current_usage) if self.current_usage else None,
            'limit_value': float(self.limit_value) if self.limit_value else None,
            'is_read': self.is_read,
            'action_required': self.action_required,
            'action_taken_at': self.action_taken_at.isoformat() if self.action_taken_at else None,
            'is_expired': self.is_expired,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }

class DiscountCode(db.Model):
    """Discount codes and promotions"""
    __tablename__ = 'discount_codes'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # Code details
    code = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))
    
    # Discount type and value
    discount_type = db.Column(db.String(20), nullable=False)  # percentage, fixed_amount
    discount_value = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Usage limits
    max_uses = db.Column(db.Integer)  # NULL = unlimited
    used_count = db.Column(db.Integer, default=0)
    per_user_limit = db.Column(db.Integer, default=1)
    
    # Validity
    is_active = db.Column(db.Boolean, default=True)
    starts_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    
    # Plan restrictions
    applicable_plans = db.Column(db.JSON)  # List of plan names
    min_plan_tier = db.Column(db.Integer)  # Minimum plan tier required
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def is_valid(self) -> bool:
        """Check if discount code is currently valid"""
        now = datetime.utcnow()
        
        if not self.is_active:
            return False
        
        if now < self.starts_at:
            return False
        
        if self.expires_at and now > self.expires_at:
            return False
        
        if self.max_uses and self.used_count >= self.max_uses:
            return False
        
        return True
    
    def can_be_used_by_user(self, user: 'User') -> bool:
        """Check if code can be used by specific user"""
        if not self.is_valid():
            return False
        
        # Check if user has already used this code
        from .models import DiscountUsage
        user_usage_count = DiscountUsage.query.filter_by(
            user_id=user.id,
            discount_code_id=self.id
        ).count()
        
        if user_usage_count >= self.per_user_limit:
            return False
        
        # Check plan restrictions
        subscription = Subscription.query.filter_by(
            user_id=user.id,
            status='active'
        ).first()
        
        if not subscription:
            return False
        
        if self.applicable_plans:
            if subscription.plan_name not in self.applicable_plans:
                return False
        
        if self.min_plan_tier and subscription.plan_tier < self.min_plan_tier:
            return False
        
        return True
    
    def calculate_discount(self, amount: Decimal) -> Decimal:
        """Calculate discount amount"""
        if self.discount_type == 'percentage':
            return amount * (self.discount_value / 100)
        elif self.discount_type == 'fixed_amount':
            return min(amount, self.discount_value)
        return Decimal('0')
    
    def to_dict(self) -> dict:
        """Convert discount code to dictionary"""
        return {
            'id': self.id,
            'code': self.code,
            'description': self.description,
            'discount_type': self.discount_type,
            'discount_value': float(self.discount_value) if self.discount_value else 0,
            'max_uses': self.max_uses,
            'used_count': self.used_count,
            'per_user_limit': self.per_user_limit,
            'is_active': self.is_active,
            'starts_at': self.starts_at.isoformat() if self.starts_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'applicable_plans': self.applicable_plans,
            'min_plan_tier': self.min_plan_tier,
            'is_valid': self.is_valid(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class DiscountUsage(db.Model):
    """Track discount code usage"""
    __tablename__ = 'discount_usages'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    discount_code_id = db.Column(db.String(36), db.ForeignKey('discount_codes.id'), nullable=False)
    
    # Usage details
    amount_discounted = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Timestamps
    used_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('discount_usages', lazy=True))
    discount_code = db.relationship('DiscountCode', backref=db.backref('usages', lazy=True))
    
    def to_dict(self) -> dict:
        """Convert discount usage to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'discount_code_id': self.discount_code_id,
            'amount_discounted': float(self.amount_discounted) if self.amount_discounted else 0,
            'used_at': self.used_at.isoformat() if self.used_at else None
        }

# Create database tables
def create_monetization_tables():
    """Create all monetization-related tables"""
    try:
        db.create_all()
        return True
    except Exception as e:
        print(f"Error creating monetization tables: {str(e)}")
        return False

# Add constraints
db.CheckConstraint('amount >= 0', name='check_amount_non_negative')
db.CheckConstraint('total_amount >= 0', name='check_total_amount_non_negative')
db.CheckConstraint('discount_value > 0', name='check_discount_value_positive')
db.CheckConstraint('metric_value >= 0', name='check_metric_value_non_negative')