"""
Payment Processing for CosmosBuilder
Author: MiniMax Agent
Date: 2025-11-27

Payment processing module with Stripe integration for handling subscriptions,
payments, invoices, and financial transactions.
"""

from flask import Blueprint, request, jsonify, current_app, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import stripe
import json
from decimal import Decimal
from uuid import uuid4

from .models import db, User, Subscription, Invoice, Payment, DiscountCode, DiscountUsage
from .billing import billing_manager
from ..utils.decorators import subscription_required
from ..utils.logging import get_logger

logger = get_logger(__name__)
payments_bp = Blueprint('payments', __name__, url_prefix='/api/payments')

class PaymentProcessor:
    """Payment processing manager"""
    
    def __init__(self):
        self.stripe = stripe
        # In production, these would be loaded from environment variables
        self.stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY', 'sk_test_your_key')
        self.webhook_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET', 'whsec_your_secret')
    
    def create_subscription(self, user: User, plan_name: str, billing_cycle: str,
                          payment_method_id: str = None, trial_days: int = None) -> Dict:
        """Create a new Stripe subscription"""
        try:
            # Get subscription plans
            plans = billing_manager.get_subscription_plans()
            plan_details = next((p for p in plans if p['name'] == plan_name), None)
            
            if not plan_details:
                raise ValueError(f"Plan not found: {plan_name}")
            
            # Get price ID for Stripe (in production, map plan names to Stripe price IDs)
            price_id = self._get_stripe_price_id(plan_name, billing_cycle)
            
            # Create Stripe customer if needed
            stripe_customer = self._get_or_create_stripe_customer(user)
            
            # Create subscription
            subscription_params = {
                'customer': stripe_customer['id'],
                'items': [{'price': price_id}],
                'billing_cycle_anchor': 'now',
                'proration_behavior': 'none',
                'payment_behavior': 'default_incomplete',
                'expand': ['latest_invoice.payment_intent']
            }
            
            # Add trial period if specified
            if trial_days and trial_days > 0:
                subscription_params['trial_period_days'] = trial_days
            
            # Attach payment method if provided
            if payment_method_id:
                self.stripe.Customer.modify(stripe_customer['id'], invoice_settings={
                    'default_payment_method': payment_method_id
                })
            
            # Create subscription in Stripe
            stripe_subscription = self.stripe.Subscription.create(**subscription_params)
            
            # Create subscription in database
            price = plan_details['price_monthly']
            if billing_cycle == 'yearly':
                price = plan_details['price_yearly']
            
            subscription = Subscription(
                user_id=user.id,
                plan_name=plan_name,
                billing_cycle=billing_cycle,
                amount=Decimal(str(price)),
                stripe_subscription_id=stripe_subscription['id'],
                stripe_customer_id=stripe_customer['id'],
                stripe_price_id=price_id,
                trial_start=datetime.utcnow() if trial_days and trial_days > 0 else None,
                trial_end=datetime.utcnow() + timedelta(days=trial_days) if trial_days and trial_days > 0 else None,
                billing_cycle_start=datetime.utcnow()
            )
            
            # Set trial end if applicable
            if trial_days and trial_days > 0:
                subscription.trial_end = datetime.utcnow() + timedelta(days=trial_days)
            
            db.session.add(subscription)
            db.session.commit()
            
            # Create invoice for the subscription
            self._create_subscription_invoice(subscription)
            
            return {
                'success': True,
                'subscription_id': subscription.id,
                'stripe_subscription_id': stripe_subscription['id'],
                'client_secret': stripe_subscription['latest_invoice']['payment_intent']['client_secret'] if stripe_subscription['latest_invoice']['payment_intent']['client_secret'] else None,
                'status': stripe_subscription['status']
            }
            
        except Exception as e:
            logger.error(f"Error creating subscription: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_subscription(self, subscription: Subscription, new_plan: str, 
                          billing_cycle: str = None) -> Dict:
        """Update existing subscription"""
        try:
            # Get Stripe subscription
            stripe_subscription = self.stripe.Subscription.retrieve(subscription.stripe_subscription_id)
            
            # Get new price ID
            new_price_id = self._get_stripe_price_id(new_plan, billing_cycle or subscription.billing_cycle)
            
            # Update subscription
            update_params = {
                'items': [{
                    'id': stripe_subscription['items']['data'][0]['id'],
                    'price': new_price_id,
                }],
                'proration_behavior': 'create_prorations'
            }
            
            updated_stripe_subscription = self.stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                **update_params
            )
            
            # Update database subscription
            subscription.plan_name = new_plan
            if billing_cycle:
                subscription.billing_cycle = billing_cycle
            subscription.updated_at = datetime.utcnow()
            
            # Update amount
            plans = billing_manager.get_subscription_plans()
            plan_details = next((p for p in plans if p['name'] == new_plan), None)
            if plan_details:
                price = plan_details['price_monthly']
                if billing_cycle == 'yearly':
                    price = plan_details['price_yearly']
                subscription.amount = Decimal(str(price))
            
            db.session.commit()
            
            return {
                'success': True,
                'stripe_subscription_id': updated_stripe_subscription['id'],
                'status': updated_stripe_subscription['status']
            }
            
        except Exception as e:
            logger.error(f"Error updating subscription: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def cancel_subscription(self, subscription: Subscription, 
                          end_of_period: bool = True) -> Dict:
        """Cancel subscription"""
        try:
            # Cancel in Stripe
            if subscription.stripe_subscription_id:
                self.stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    cancel_at_period_end=end_of_period
                )
            
            # Update database
            subscription.status = 'cancelled' if not end_of_period else subscription.status
            subscription.cancelled_at = datetime.utcnow()
            subscription.end_of_billing_period = end_of_period
            subscription.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return {
                'success': True,
                'cancelled_at': subscription.cancelled_at.isoformat(),
                'end_of_period': end_of_period
            }
            
        except Exception as e:
            logger.error(f"Error cancelling subscription: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_payment_method(self, user: User, payment_method_data: Dict) -> Dict:
        """Create a new payment method"""
        try:
            # Get or create Stripe customer
            stripe_customer = self._get_or_create_stripe_customer(user)
            
            # Create payment method
            payment_method = self.stripe.PaymentMethod.create(**payment_method_data)
            
            # Attach payment method to customer
            self.stripe.PaymentMethod.attach(payment_method['id'], customer=stripe_customer['id'])
            
            # Set as default if specified
            if payment_method_data.get('set_as_default'):
                self.stripe.Customer.modify(
                    stripe_customer['id'],
                    invoice_settings={'default_payment_method': payment_method['id']}
                )
            
            return {
                'success': True,
                'payment_method_id': payment_method['id'],
                'type': payment_method['type'],
                'is_default': payment_method_data.get('set_as_default', False)
            }
            
        except Exception as e:
            logger.error(f"Error creating payment method: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_payment(self, invoice: Invoice, payment_method_id: str = None) -> Dict:
        """Process payment for an invoice"""
        try:
            # Get Stripe customer
            user = User.query.get(invoice.user_id)
            stripe_customer = self._get_or_create_stripe_customer(user)
            
            # Create payment intent
            payment_intent = self.stripe.PaymentIntent.create(
                amount=int(invoice.total_amount * 100),  # Convert to cents
                currency=invoice.currency.lower(),
                customer=stripe_customer['id'],
                payment_method=payment_method_id,
                confirm=True,
                off_session=True,
                description=f'Invoice {invoice.invoice_number}'
            )
            
            # Create payment record
            payment = Payment(
                user_id=invoice.user_id,
                invoice_id=invoice.id,
                payment_method='card',
                amount=invoice.total_amount,
                currency=invoice.currency,
                stripe_payment_intent_id=payment_intent['id'],
                status='pending',
                transaction_id=payment_intent['id']
            )
            
            db.session.add(payment)
            db.session.commit()
            
            # Update payment status if succeeded
            if payment_intent['status'] == 'succeeded':
                payment.status = 'completed'
                payment.payment_date = datetime.utcnow()
                invoice.status = 'paid'
                db.session.commit()
            
            return {
                'success': payment_intent['status'] in ['succeeded', 'processing'],
                'payment_id': payment.id,
                'stripe_payment_intent_id': payment_intent['id'],
                'status': payment_intent['status'],
                'client_secret': payment_intent['client_secret']
            }
            
        except Exception as e:
            logger.error(f"Error processing payment: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_or_create_stripe_customer(self, user: User) -> Dict:
        """Get or create Stripe customer"""
        try:
            # Check if user already has a Stripe customer
            subscription = Subscription.query.filter_by(
                user_id=user.id
            ).first()
            
            if subscription and subscription.stripe_customer_id:
                # Retrieve existing customer
                customer = self.stripe.Customer.retrieve(subscription.stripe_customer_id)
                return customer
            
            # Create new customer
            customer = self.stripe.Customer.create(
                email=user.email,
                name=user.full_name or user.username,
                metadata={
                    'user_id': user.id,
                    'username': user.username
                }
            )
            
            return customer
            
        except Exception as e:
            logger.error(f"Error getting/creating Stripe customer: {str(e)}")
            raise
    
    def _get_stripe_price_id(self, plan_name: str, billing_cycle: str) -> str:
        """Get Stripe price ID for a plan"""
        # In production, these would be stored in database or environment
        price_mapping = {
            'starter': {
                'monthly': 'price_starter_monthly',
                'yearly': 'price_starter_yearly'
            },
            'professional': {
                'monthly': 'price_professional_monthly',
                'yearly': 'price_professional_yearly'
            },
            'enterprise': {
                'monthly': 'price_enterprise_monthly',
                'yearly': 'price_enterprise_yearly'
            },
            'sovereign': {
                'monthly': 'price_sovereign_monthly',
                'yearly': 'price_sovereign_yearly'
            }
        }
        
        return price_mapping.get(plan_name, {}).get(billing_cycle, 'price_starter_monthly')
    
    def _create_subscription_invoice(self, subscription: Subscription):
        """Create invoice for subscription"""
        # This would create an invoice in both Stripe and local database
        # For now, return a placeholder
        pass

# Initialize payment processor
payment_processor = PaymentProcessor()

# Payment endpoints

@payments_bp.route('/subscribe', methods=['POST'])
@jwt_required()
def create_subscription():
    """Create a new subscription"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        data = request.get_json()
        plan_name = data.get('plan_name')
        billing_cycle = data.get('billing_cycle', 'monthly')
        payment_method_id = data.get('payment_method_id')
        trial_days = data.get('trial_days')
        
        if not plan_name:
            return jsonify({
                'success': False,
                'error': 'plan_name is required'
            }), 400
        
        result = payment_processor.create_subscription(
            user=user,
            plan_name=plan_name,
            billing_cycle=billing_cycle,
            payment_method_id=payment_method_id,
            trial_days=trial_days
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result,
                'message': 'Subscription created successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
        
    except Exception as e:
        logger.error(f"Error creating subscription: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to create subscription'
        }), 500

@payments_bp.route('/subscription/change', methods=['POST'])
@jwt_required()
@subscription_required()
def change_subscription():
    """Change subscription plan"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        subscription = Subscription.query.filter_by(
            user_id=user.id,
            status='active'
        ).first()
        
        if not subscription:
            return jsonify({
                'success': False,
                'error': 'No active subscription found'
            }), 404
        
        data = request.get_json()
        new_plan = data.get('plan_name')
        billing_cycle = data.get('billing_cycle')
        
        if not new_plan:
            return jsonify({
                'success': False,
                'error': 'plan_name is required'
            }), 400
        
        result = payment_processor.update_subscription(
            subscription=subscription,
            new_plan=new_plan,
            billing_cycle=billing_cycle
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result,
                'message': 'Subscription updated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
        
    except Exception as e:
        logger.error(f"Error changing subscription: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to update subscription'
        }), 500

@payments_bp.route('/subscription/cancel', methods=['POST'])
@jwt_required()
@subscription_required()
def cancel_subscription():
    """Cancel subscription"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        subscription = Subscription.query.filter_by(
            user_id=user.id,
            status='active'
        ).first()
        
        if not subscription:
            return jsonify({
                'success': False,
                'error': 'No active subscription found'
            }), 404
        
        data = request.get_json()
        end_of_period = data.get('end_of_period', True)
        reason = data.get('reason')
        
        result = payment_processor.cancel_subscription(
            subscription=subscription,
            end_of_period=end_of_period
        )
        
        if result['success']:
            # Record cancellation reason
            subscription.cancellation_reason = reason
            db.session.commit()
            
            return jsonify({
                'success': True,
                'data': result,
                'message': 'Subscription cancelled successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
        
    except Exception as e:
        logger.error(f"Error cancelling subscription: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to cancel subscription'
        }), 500

@payments_bp.route('/payment-methods', methods=['GET'])
@jwt_required()
def get_payment_methods():
    """Get user's payment methods"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        # Get Stripe customer
        subscription = Subscription.query.filter_by(user_id=user.id).first()
        
        if not subscription or not subscription.stripe_customer_id:
            return jsonify({
                'success': True,
                'data': [],
                'message': 'No payment methods found'
            })
        
        # Get payment methods from Stripe
        payment_methods = payment_processor.stripe.PaymentMethod.list(
            customer=subscription.stripe_customer_id,
            type='card'
        )
        
        methods_data = []
        for pm in payment_methods['data']:
            methods_data.append({
                'id': pm['id'],
                'type': pm['type'],
                'card': {
                    'brand': pm['card']['brand'],
                    'last4': pm['card']['last4'],
                    'exp_month': pm['card']['exp_month'],
                    'exp_year': pm['card']['exp_year']
                },
                'is_default': pm.get('is_default', False),
                'created': datetime.fromtimestamp(pm['created']).isoformat()
            })
        
        return jsonify({
            'success': True,
            'data': methods_data,
            'message': 'Payment methods retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error retrieving payment methods: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve payment methods'
        }), 500

@payments_bp.route('/payment-methods', methods=['POST'])
@jwt_required()
def add_payment_method():
    """Add a new payment method"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        data = request.get_json()
        
        # Create payment method in Stripe
        result = payment_processor.create_payment_method(user, data)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result,
                'message': 'Payment method added successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
        
    except Exception as e:
        logger.error(f"Error adding payment method: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to add payment method'
        }), 500

@payments_bp.route('/payment-methods/<payment_method_id>', methods=['DELETE'])
@jwt_required()
def remove_payment_method(payment_method_id):
    """Remove a payment method"""
    try:
        user_id = get_jwt_identity()
        
        # Detach payment method from Stripe
        payment_processor.stripe.PaymentMethod.detach(payment_method_id)
        
        return jsonify({
            'success': True,
            'message': 'Payment method removed successfully'
        })
        
    except Exception as e:
        logger.error(f"Error removing payment method: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to remove payment method'
        }), 500

@payments_bp.route('/checkout-session', methods=['POST'])
@jwt_required()
def create_checkout_session():
    """Create Stripe checkout session"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        data = request.get_json()
        plan_name = data.get('plan_name')
        billing_cycle = data.get('billing_cycle', 'monthly')
        
        # Get subscription plan
        plans = billing_manager.get_subscription_plans()
        plan_details = next((p for p in plans if p['name'] == plan_name), None)
        
        if not plan_details:
            return jsonify({
                'success': False,
                'error': 'Plan not found'
            }), 400
        
        # Get Stripe price ID
        price_id = payment_processor._get_stripe_price_id(plan_name, billing_cycle)
        
        # Create checkout session
        checkout_session = payment_processor.stripe.checkout.Session.create(
            customer_email=user.email,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=url_for('frontend.success_page', _external=True),
            cancel_url=url_for('frontend.billing_page', _external=True),
            client_reference_id=user.id,
            metadata={
                'plan_name': plan_name,
                'billing_cycle': billing_cycle,
                'user_id': user.id
            }
        )
        
        return jsonify({
            'success': True,
            'data': {
                'session_id': checkout_session['id'],
                'url': checkout_session['url']
            },
            'message': 'Checkout session created successfully'
        })
        
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to create checkout session'
        }), 500

@payments_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks"""
    try:
        payload = request.get_data()
        sig_header = request.headers.get('Stripe-Signature')
        
        # Verify webhook signature (in production)
        # event = stripe.Webhook.construct_event(payload, sig_header, self.webhook_secret)
        
        event = json.loads(payload)
        
        # Handle different event types
        if event['type'] == 'invoice.payment_succeeded':
            _handle_invoice_payment_succeeded(event['data']['object'])
        elif event['type'] == 'invoice.payment_failed':
            _handle_invoice_payment_failed(event['data']['object'])
        elif event['type'] == 'customer.subscription.updated':
            _handle_subscription_updated(event['data']['object'])
        elif event['type'] == 'customer.subscription.deleted':
            _handle_subscription_deleted(event['data']['object'])
        elif event['type'] == 'payment_intent.succeeded':
            _handle_payment_intent_succeeded(event['data']['object'])
        elif event['type'] == 'payment_intent.payment_failed':
            _handle_payment_intent_failed(event['data']['object'])
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        logger.error(f"Stripe webhook error: {str(e)}")
        return jsonify({'success': False}), 400

# Webhook event handlers

def _handle_invoice_payment_succeeded(invoice_data):
    """Handle successful invoice payment"""
    try:
        # Find subscription
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=invoice_data['subscription']
        ).first()
        
        if subscription:
            # Update subscription status
            subscription.status = 'active'
            db.session.commit()
        
        # Update invoice status
        invoice = Invoice.query.filter_by(
            stripe_invoice_id=invoice_data['id']
        ).first()
        
        if invoice:
            invoice.status = 'paid'
            invoice.updated_at = datetime.utcnow()
            db.session.commit()
        
        logger.info(f"Invoice payment succeeded: {invoice_data['id']}")
        
    except Exception as e:
        logger.error(f"Error handling invoice payment succeeded: {str(e)}")

def _handle_invoice_payment_failed(invoice_data):
    """Handle failed invoice payment"""
    try:
        # Update invoice status
        invoice = Invoice.query.filter_by(
            stripe_invoice_id=invoice_data['id']
        ).first()
        
        if invoice:
            invoice.status = 'overdue'
            invoice.updated_at = datetime.utcnow()
            db.session.commit()
        
        logger.warning(f"Invoice payment failed: {invoice_data['id']}")
        
    except Exception as e:
        logger.error(f"Error handling invoice payment failed: {str(e)}")

def _handle_subscription_updated(subscription_data):
    """Handle subscription update"""
    try:
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=subscription_data['id']
        ).first()
        
        if subscription:
            subscription.status = subscription_data['status']
            subscription.updated_at = datetime.utcnow()
            db.session.commit()
        
        logger.info(f"Subscription updated: {subscription_data['id']}")
        
    except Exception as e:
        logger.error(f"Error handling subscription updated: {str(e)}")

def _handle_subscription_deleted(subscription_data):
    """Handle subscription deletion"""
    try:
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=subscription_data['id']
        ).first()
        
        if subscription:
            subscription.status = 'cancelled'
            subscription.cancelled_at = datetime.utcnow()
            subscription.updated_at = datetime.utcnow()
            db.session.commit()
        
        logger.info(f"Subscription deleted: {subscription_data['id']}")
        
    except Exception as e:
        logger.error(f"Error handling subscription deleted: {str(e)}")

def _handle_payment_intent_succeeded(payment_intent_data):
    """Handle successful payment intent"""
    try:
        # Update payment status
        payment = Payment.query.filter_by(
            stripe_payment_intent_id=payment_intent_data['id']
        ).first()
        
        if payment:
            payment.status = 'completed'
            payment.payment_date = datetime.utcnow()
            payment.updated_at = datetime.utcnow()
            db.session.commit()
        
        logger.info(f"Payment intent succeeded: {payment_intent_data['id']}")
        
    except Exception as e:
        logger.error(f"Error handling payment intent succeeded: {str(e)}")

def _handle_payment_intent_failed(payment_intent_data):
    """Handle failed payment intent"""
    try:
        # Update payment status
        payment = Payment.query.filter_by(
            stripe_payment_intent_id=payment_intent_data['id']
        ).first()
        
        if payment:
            payment.status = 'failed'
            payment.updated_at = datetime.utcnow()
            db.session.commit()
        
        logger.warning(f"Payment intent failed: {payment_intent_data['id']}")
        
    except Exception as e:
        logger.error(f"Error handling payment intent failed: {str(e)}")

# Discount code endpoints

@payments_bp.route('/discount/validate', methods=['POST'])
@jwt_required()
def validate_discount_code():
    """Validate a discount code"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        data = request.get_json()
        code = data.get('code')
        
        if not code:
            return jsonify({
                'success': False,
                'error': 'Discount code is required'
            }), 400
        
        # Find discount code
        discount_code = DiscountCode.query.filter_by(code=code.upper()).first()
        
        if not discount_code or not discount_code.is_valid():
            return jsonify({
                'success': False,
                'error': 'Invalid or expired discount code'
            }), 400
        
        # Check if user can use this code
        if not discount_code.can_be_used_by_user(user):
            return jsonify({
                'success': False,
                'error': 'Discount code cannot be used with your current subscription'
            }), 400
        
        # Calculate discount amount (assuming $100 base amount)
        discount_amount = discount_code.calculate_discount(Decimal('100'))
        
        return jsonify({
            'success': True,
            'data': {
                'code': discount_code.code,
                'description': discount_code.description,
                'discount_type': discount_code.discount_type,
                'discount_value': float(discount_code.discount_value),
                'discount_amount': float(discount_amount),
                'applies_to': discount_code.applicable_plans,
                'valid': True
            },
            'message': 'Discount code is valid'
        })
        
    except Exception as e:
        logger.error(f"Error validating discount code: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to validate discount code'
        }), 500