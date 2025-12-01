#!/usr/bin/env python3
"""
CosmosBuilder Enterprise Compliance & Business Integration
Advanced compliance features, business logic, and enterprise integrations
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
import enum
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComplianceLevel(enum.Enum):
    BASIC = "basic"
    STANDARD = "standard"
    ENHANCED = "enhanced"
    ENTERPRISE = "enterprise"
    REGULATORY = "regulatory"

class BusinessRuleType(enum.Enum):
    TRANSACTION_LIMIT = "transaction_limit"
    TIME_RESTRICTION = "time_restriction"
    GEOGRAPHIC_RESTRICTION = "geographic_restriction"
    WHITELIST_ONLY = "whitelist_only"
    KYC_REQUIRED = "kyc_required"
    APPROVAL_WORKFLOW = "approval_workflow"
    AUDIT_REQUIRED = "audit_required"
    TEMPLATE_ENFORCEMENT = "template_enforcement"

class RiskLevel(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class KYCDocument:
    """KYC document verification"""
    document_id: str
    user_id: str
    document_type: str  # passport, national_id, driver's_license
    document_number: str
    issued_by: str
    issued_date: datetime
    expiry_date: datetime
    verification_status: str  # pending, verified, rejected
    verification_date: Optional[datetime] = None
    verification_method: Optional[str] = None
    metadata: Dict[str, Any] = None

@dataclass
class BusinessEntity:
    """Business entity (KYB) information"""
    entity_id: str
    entity_name: str
    entity_type: str  # corporation, llc, partnership, etc.
    registration_number: str
    jurisdiction: str
    industry_sector: str
    business_address: Dict[str, Any]
    directors: List[Dict[str, Any]]
    beneficial_owners: List[Dict[str, Any]]
    verification_status: str
    created_at: datetime
    compliance_documents: List[str]

@dataclass
class TransactionTemplate:
    """Transaction template for approval workflow"""
    template_id: str
    name: str
    description: str
    template_type: str
    required_fields: List[str]
    field_validations: Dict[str, Any]
    approval_workflow: List[Dict[str, Any]]
    execution_script: str
    risk_score: int
    enabled: bool
    created_by: str
    created_at: datetime

@dataclass
class ComplianceRule:
    """Compliance rule configuration"""
    rule_id: str
    rule_name: str
    rule_type: BusinessRuleType
    compliance_level: ComplianceLevel
    chain_id: str
    parameters: Dict[str, Any]
    conditions: Dict[str, Any]
    actions: List[Dict[str, Any]]
    enabled: bool
    priority: int
    created_at: datetime

@dataclass
class RiskAssessment:
    """Risk assessment for transaction"""
    assessment_id: str
    transaction_id: str
    risk_score: int
    risk_factors: List[str]
    recommendations: List[str]
    review_required: bool
    flagged_keywords: List[str]
    geographic_risk: str
    compliance_score: float
    assessed_at: datetime

class ComplianceEngine:
    """Enterprise compliance and risk management engine"""
    
    def __init__(self, storage_path: str = "enterprise/compliance"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Database files
        self.kyc_db = self.storage_path / "kyc_documents.json"
        self.kyb_db = self.storage_path / "business_entities.json"
        self.templates_db = self.storage_path / "transaction_templates.json"
        self.rules_db = self.storage_path / "compliance_rules.json"
        self.risk_db = self.storage_path / "risk_assessments.json"
        
        # In-memory storage
        self.kyc_documents = {}
        self.business_entities = {}
        self.transaction_templates = {}
        self.compliance_rules = {}
        self.risk_assessments = {}
        
        # Load data
        self._load_data()
    
    def _load_data(self):
        """Load compliance data"""
        self._load_kyc_documents()
        self._load_business_entities()
        self._load_transaction_templates()
        self._load_compliance_rules()
        self._load_risk_assessments()
    
    def _load_kyc_documents(self):
        """Load KYC documents"""
        try:
            if self.kyc_db.exists():
                with open(self.kyc_db, 'r') as f:
                    data = json.load(f)
                    for doc_id, doc_data in data.items():
                        doc_data['issued_date'] = datetime.fromisoformat(doc_data['issued_date'])
                        doc_data['expiry_date'] = datetime.fromisoformat(doc_data['expiry_date'])
                        if doc_data.get('verification_date'):
                            doc_data['verification_date'] = datetime.fromisoformat(doc_data['verification_date'])
                        self.kyc_documents[doc_id] = KYCDocument(**doc_data)
                logger.info(f"Loaded {len(self.kyc_documents)} KYC documents")
        except Exception as e:
            logger.error(f"Error loading KYC documents: {str(e)}")
    
    def _load_business_entities(self):
        """Load business entities"""
        try:
            if self.kyb_db.exists():
                with open(self.kyb_db, 'r') as f:
                    data = json.load(f)
                    for entity_id, entity_data in data.items():
                        entity_data['created_at'] = datetime.fromisoformat(entity_data['created_at'])
                        self.business_entities[entity_id] = BusinessEntity(**entity_data)
                logger.info(f"Loaded {len(self.business_entities)} business entities")
        except Exception as e:
            logger.error(f"Error loading business entities: {str(e)}")
    
    def _load_transaction_templates(self):
        """Load transaction templates"""
        try:
            if self.templates_db.exists():
                with open(self.templates_db, 'r') as f:
                    data = json.load(f)
                    for template_id, template_data in data.items():
                        template_data['created_at'] = datetime.fromisoformat(template_data['created_at'])
                        self.transaction_templates[template_id] = TransactionTemplate(**template_data)
                logger.info(f"Loaded {len(self.transaction_templates)} transaction templates")
        except Exception as e:
            logger.error(f"Error loading transaction templates: {str(e)}")
    
    def _load_compliance_rules(self):
        """Load compliance rules"""
        try:
            if self.rules_db.exists():
                with open(self.rules_db, 'r') as f:
                    data = json.load(f)
                    for rule_id, rule_data in data.items():
                        rule_data['created_at'] = datetime.fromisoformat(rule_data['created_at'])
                        rule_data['rule_type'] = BusinessRuleType(rule_data['rule_type'])
                        rule_data['compliance_level'] = ComplianceLevel(rule_data['compliance_level'])
                        self.compliance_rules[rule_id] = ComplianceRule(**rule_data)
                logger.info(f"Loaded {len(self.compliance_rules)} compliance rules")
        except Exception as e:
            logger.error(f"Error loading compliance rules: {str(e)}")
    
    def _load_risk_assessments(self):
        """Load risk assessments"""
        try:
            if self.risk_db.exists():
                with open(self.risk_db, 'r') as f:
                    data = json.load(f)
                    for assessment_id, assessment_data in data.items():
                        assessment_data['assessed_at'] = datetime.fromisoformat(assessment_data['assessed_at'])
                        self.risk_assessments[assessment_id] = RiskAssessment(**assessment_data)
                logger.info(f"Loaded {len(self.risk_assessments)} risk assessments")
        except Exception as e:
            logger.error(f"Error loading risk assessments: {str(e)}")
    
    def _save_data(self):
        """Save all compliance data"""
        self._save_kyc_documents()
        self._save_business_entities()
        self._save_transaction_templates()
        self._save_compliance_rules()
        self._save_risk_assessments()
    
    def _save_kyc_documents(self):
        """Save KYC documents"""
        try:
            data = {}
            for doc_id, doc in self.kyc_documents.items():
                doc_data = asdict(doc)
                doc_data['issued_date'] = doc.issued_date.isoformat()
                doc_data['expiry_date'] = doc.expiry_date.isoformat()
                if doc.verification_date:
                    doc_data['verification_date'] = doc.verification_date.isoformat()
                data[doc_id] = doc_data
            
            with open(self.kyc_db, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving KYC documents: {str(e)}")
    
    def _save_business_entities(self):
        """Save business entities"""
        try:
            data = {}
            for entity_id, entity in self.business_entities.items():
                entity_data = asdict(entity)
                entity_data['created_at'] = entity.created_at.isoformat()
                data[entity_id] = entity_data
            
            with open(self.kyb_db, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving business entities: {str(e)}")
    
    def _save_transaction_templates(self):
        """Save transaction templates"""
        try:
            data = {}
            for template_id, template in self.transaction_templates.items():
                template_data = asdict(template)
                template_data['created_at'] = template.created_at.isoformat()
                data[template_id] = template_data
            
            with open(self.templates_db, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving transaction templates: {str(e)}")
    
    def _save_compliance_rules(self):
        """Save compliance rules"""
        try:
            data = {}
            for rule_id, rule in self.compliance_rules.items():
                rule_data = asdict(rule)
                rule_data['created_at'] = rule.created_at.isoformat()
                rule_data['rule_type'] = rule.rule_type.value
                rule_data['compliance_level'] = rule.compliance_level.value
                data[rule_id] = rule_data
            
            with open(self.rules_db, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving compliance rules: {str(e)}")
    
    def _save_risk_assessments(self):
        """Save risk assessments"""
        try:
            data = {}
            for assessment_id, assessment in self.risk_assessments.items():
                assessment_data = asdict(assessment)
                assessment_data['assessed_at'] = assessment.assessed_at.isoformat()
                data[assessment_id] = assessment_data
            
            with open(self.risk_db, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving risk assessments: {str(e)}")
    
    # KYC/KYB Management
    
    def submit_kyc_document(self, user_id: str, document_type: str, document_data: Dict[str, Any]) -> KYCDocument:
        """Submit KYC document for verification"""
        try:
            document_id = f"kyc_{secrets.token_hex(8)}"
            
            # Parse document data
            document_number = document_data.get('document_number', '')
            issued_by = document_data.get('issued_by', '')
            issued_date = datetime.fromisoformat(document_data.get('issued_date'))
            expiry_date = datetime.fromisoformat(document_data.get('expiry_date'))
            
            # Create KYC document
            kyc_doc = KYCDocument(
                document_id=document_id,
                user_id=user_id,
                document_type=document_type,
                document_number=document_number,
                issued_by=issued_by,
                issued_date=issued_date,
                expiry_date=expiry_date,
                verification_status="pending",
                metadata=document_data
            )
            
            self.kyc_documents[document_id] = kyc_doc
            self._save_kyc_documents()
            
            logger.info(f"Submitted KYC document {document_id} for {user_id}")
            return kyc_doc
            
        except Exception as e:
            logger.error(f"Error submitting KYC document: {str(e)}")
            raise
    
    def verify_kyc_document(self, document_id: str, verification_status: str, 
                          verification_method: str, verifier_id: str) -> bool:
        """Verify KYC document"""
        try:
            if document_id not in self.kyc_documents:
                return False
            
            doc = self.kyc_documents[document_id]
            doc.verification_status = verification_status
            doc.verification_date = datetime.now()
            doc.verification_method = verification_method
            
            # Additional verification logic could be added here
            # e.g., AI document verification, database cross-reference, etc.
            
            self._save_kyc_documents()
            
            logger.info(f"Verified KYC document {document_id}: {verification_status}")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying KYC document: {str(e)}")
            return False
    
    def register_business_entity(self, entity_data: Dict[str, Any]) -> BusinessEntity:
        """Register business entity (KYB)"""
        try:
            entity_id = f"kyb_{secrets.token_hex(8)}"
            
            entity = BusinessEntity(
                entity_id=entity_id,
                entity_name=entity_data['entity_name'],
                entity_type=entity_data['entity_type'],
                registration_number=entity_data['registration_number'],
                jurisdiction=entity_data['jurisdiction'],
                industry_sector=entity_data['industry_sector'],
                business_address=entity_data['business_address'],
                directors=entity_data.get('directors', []),
                beneficial_owners=entity_data.get('beneficial_owners', []),
                verification_status="pending",
                created_at=datetime.now(),
                compliance_documents=entity_data.get('compliance_documents', [])
            )
            
            self.business_entities[entity_id] = entity
            self._save_business_entities()
            
            logger.info(f"Registered business entity {entity_id}: {entity.entity_name}")
            return entity
            
        except Exception as e:
            logger.error(f"Error registering business entity: {str(e)}")
            raise
    
    def verify_business_entity(self, entity_id: str, verification_status: str, 
                              verification_notes: str) -> bool:
        """Verify business entity"""
        try:
            if entity_id not in self.business_entities:
                return False
            
            entity = self.business_entities[entity_id]
            entity.verification_status = verification_status
            
            # Update metadata with verification notes
            if not entity.compliance_documents:
                entity.compliance_documents = []
            entity.compliance_documents.append({
                'type': 'verification',
                'status': verification_status,
                'notes': verification_notes,
                'verified_at': datetime.now().isoformat()
            })
            
            self._save_business_entities()
            
            logger.info(f"Verified business entity {entity_id}: {verification_status}")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying business entity: {str(e)}")
            return False
    
    # Transaction Template Management
    
    def create_transaction_template(self, template_data: Dict[str, Any], created_by: str) -> TransactionTemplate:
        """Create transaction template"""
        try:
            template_id = f"template_{secrets.token_hex(8)}"
            
            template = TransactionTemplate(
                template_id=template_id,
                name=template_data['name'],
                description=template_data['description'],
                template_type=template_data['template_type'],
                required_fields=template_data['required_fields'],
                field_validations=template_data.get('field_validations', {}),
                approval_workflow=template_data.get('approval_workflow', []),
                execution_script=template_data.get('execution_script', ''),
                risk_score=template_data.get('risk_score', 0),
                enabled=template_data.get('enabled', True),
                created_by=created_by,
                created_at=datetime.now()
            )
            
            self.transaction_templates[template_id] = template
            self._save_transaction_templates()
            
            logger.info(f"Created transaction template {template_id}: {template.name}")
            return template
            
        except Exception as e:
            logger.error(f"Error creating transaction template: {str(e)}")
            raise
    
    def validate_transaction_template(self, template_id: str, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate transaction against template"""
        try:
            if template_id not in self.transaction_templates:
                return {'valid': False, 'error': 'Template not found'}
            
            template = self.transaction_templates[template_id]
            
            if not template.enabled:
                return {'valid': False, 'error': 'Template is disabled'}
            
            violations = []
            warnings = []
            
            # Check required fields
            for field in template.required_fields:
                if field not in transaction_data:
                    violations.append(f"Missing required field: {field}")
            
            # Check field validations
            for field, validation in template.field_validations.items():
                if field in transaction_data:
                    value = transaction_data[field]
                    
                    # Type validation
                    expected_type = validation.get('type')
                    if expected_type and not isinstance(value, expected_type):
                        violations.append(f"Field {field} should be of type {expected_type}")
                    
                    # Range validation
                    min_val = validation.get('min')
                    max_val = validation.get('max')
                    if isinstance(value, (int, float)):
                        if min_val is not None and value < min_val:
                            violations.append(f"Field {field} is below minimum {min_val}")
                        if max_val is not None and value > max_val:
                            violations.append(f"Field {field} exceeds maximum {max_val}")
                    
                    # Pattern validation
                    pattern = validation.get('pattern')
                    if pattern and not re.match(pattern, str(value)):
                        violations.append(f"Field {field} does not match required pattern")
            
            # Check approval workflow requirements
            approval_required = len(template.approval_workflow) > 0
            if approval_required and not transaction_data.get('approved', False):
                violations.append("Transaction requires approval workflow completion")
            
            return {
                'valid': len(violations) == 0,
                'violations': violations,
                'warnings': warnings,
                'template_id': template_id,
                'risk_score': template.risk_score
            }
            
        except Exception as e:
            logger.error(f"Error validating transaction template: {str(e)}")
            return {'valid': False, 'error': str(e)}
    
    # Compliance Rules Management
    
    def create_compliance_rule(self, rule_data: Dict[str, Any]) -> ComplianceRule:
        """Create compliance rule"""
        try:
            rule_id = f"rule_{secrets.token_hex(8)}"
            
            rule = ComplianceRule(
                rule_id=rule_id,
                rule_name=rule_data['rule_name'],
                rule_type=BusinessRuleType(rule_data['rule_type']),
                compliance_level=ComplianceLevel(rule_data['compliance_level']),
                chain_id=rule_data['chain_id'],
                parameters=rule_data.get('parameters', {}),
                conditions=rule_data.get('conditions', {}),
                actions=rule_data.get('actions', []),
                enabled=rule_data.get('enabled', True),
                priority=rule_data.get('priority', 0),
                created_at=datetime.now()
            )
            
            self.compliance_rules[rule_id] = rule
            self._save_compliance_rules()
            
            logger.info(f"Created compliance rule {rule_id}: {rule.rule_name}")
            return rule
            
        except Exception as e:
            logger.error(f"Error creating compliance rule: {str(e)}")
            raise
    
    def check_transaction_compliance(self, transaction_data: Dict[str, Any], chain_id: str) -> Dict[str, Any]:
        """Check transaction against compliance rules"""
        try:
            # Get applicable rules for chain
            applicable_rules = [
                rule for rule in self.compliance_rules.values()
                if rule.enabled and (rule.chain_id == chain_id or rule.chain_id == "*")
            ]
            
            # Sort by priority (higher first)
            applicable_rules.sort(key=lambda x: x.priority, reverse=True)
            
            violations = []
            warnings = []
            triggered_rules = []
            
            for rule in applicable_rules:
                rule_violations, rule_warnings = self._evaluate_rule(rule, transaction_data)
                
                if rule_violations or rule_warnings:
                    triggered_rules.append(rule.rule_id)
                    violations.extend(rule_violations)
                    warnings.extend(rule_warnings)
            
            # Calculate compliance score
            total_rules = len(applicable_rules)
            passed_rules = total_rules - len(set(triggered_rules))
            compliance_score = (passed_rules / total_rules * 100) if total_rules > 0 else 100
            
            return {
                'compliant': len(violations) == 0,
                'compliance_score': compliance_score,
                'violations': violations,
                'warnings': warnings,
                'triggered_rules': triggered_rules,
                'total_applicable_rules': total_rules,
                'checked_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error checking transaction compliance: {str(e)}")
            return {
                'compliant': False,
                'compliance_score': 0,
                'violations': [f"System error: {str(e)}"],
                'warnings': [],
                'triggered_rules': [],
                'total_applicable_rules': 0,
                'checked_at': datetime.now().isoformat()
            }
    
    def _evaluate_rule(self, rule: ComplianceRule, transaction_data: Dict[str, Any]) -> tuple:
        """Evaluate a single compliance rule"""
        violations = []
        warnings = []
        
        try:
            if rule.rule_type == BusinessRuleType.TRANSACTION_LIMIT:
                amount = transaction_data.get('amount', 0)
                max_amount = rule.parameters.get('max_amount', float('inf'))
                daily_limit = rule.parameters.get('daily_limit', float('inf'))
                
                if amount > max_amount:
                    violations.append(f"Amount {amount} exceeds limit {max_amount}")
                
                # Check daily limits (would need transaction history)
                if amount > daily_limit:
                    violations.append(f"Amount {amount} exceeds daily limit {daily_limit}")
            
            elif rule.rule_type == BusinessRuleType.KYC_REQUIRED:
                user_id = transaction_data.get('sender')
                if user_id and not self._is_user_kyc_verified(user_id):
                    violations.append("KYC verification required for sender")
                
                user_id = transaction_data.get('recipient')
                if user_id and not self._is_user_kyc_verified(user_id):
                    violations.append("KYC verification required for recipient")
            
            elif rule.rule_type == BusinessRuleType.WHITELIST_ONLY:
                sender = transaction_data.get('sender')
                whitelist = rule.parameters.get('whitelist', [])
                admins = rule.parameters.get('admins', [])
                
                if sender not in whitelist and sender not in admins:
                    violations.append(f"Sender {sender} not in whitelist")
            
            elif rule.rule_type == BusinessRuleType.APPROVAL_WORKFLOW:
                if not transaction_data.get('approved', False):
                    violations.append("Transaction requires approval workflow")
                
                required_approvers = rule.parameters.get('required_approvers', [])
                actual_approvers = transaction_data.get('approvers', [])
                
                for required in required_approvers:
                    if required not in actual_approvers:
                        violations.append(f"Missing required approver: {required}")
            
            # Add other rule types as needed
            
        except Exception as e:
            logger.error(f"Error evaluating rule {rule.rule_id}: {str(e)}")
            violations.append(f"Rule evaluation error: {str(e)}")
        
        return violations, warnings
    
    def _is_user_kyc_verified(self, user_id: str) -> bool:
        """Check if user has verified KYC"""
        try:
            # Find user's KYC documents
            user_docs = [
                doc for doc in self.kyc_documents.values()
                if doc.user_id == user_id and doc.verification_status == "verified"
            ]
            return len(user_docs) > 0
        except:
            return False
    
    # Risk Assessment
    
    def assess_transaction_risk(self, transaction_data: Dict[str, Any], transaction_id: str) -> RiskAssessment:
        """Assess transaction risk"""
        try:
            assessment_id = f"risk_{secrets.token_hex(8)}"
            
            # Analyze transaction data for risk factors
            risk_factors = []
            recommendations = []
            flagged_keywords = []
            risk_score = 0
            
            # Amount-based risk
            amount = transaction_data.get('amount', 0)
            if amount > 1000000:
                risk_factors.append("High transaction amount")
                risk_score += 30
            
            # Time-based risk (late night transactions)
            transaction_time = datetime.now()
            if transaction_time.hour < 6 or transaction_time.hour > 22:
                risk_factors.append("Unusual transaction time")
                risk_score += 10
            
            # Keyword scanning
            risky_keywords = ['anonymous', 'mixer', 'tumbler', 'darknet', 'illegal']
            transaction_description = transaction_data.get('description', '').lower()
            
            for keyword in risky_keywords:
                if keyword in transaction_description:
                    flagged_keywords.append(keyword)
                    risk_factors.append(f"Flagged keyword: {keyword}")
                    risk_score += 20
            
            # Velocity risk (check for rapid transactions)
            sender = transaction_data.get('sender')
            if sender:
                # This would check transaction history in a real system
                recent_transactions = 0  # Mock value
                if recent_transactions > 10:
                    risk_factors.append("High transaction velocity")
                    risk_score += 15
            
            # Geographic risk (would use geolocation data in real system)
            geographic_risk = "unknown"  # Mock value
            if transaction_data.get('ip_address'):
                # Check IP against sanctions lists, high-risk jurisdictions, etc.
                geographic_risk = self._assess_geographic_risk(transaction_data.get('ip_address'))
                if geographic_risk == "high":
                    risk_factors.append("High-risk geographic location")
                    risk_score += 25
            
            # Calculate compliance score
            max_risk_score = 100
            compliance_score = max(0, (max_risk_score - risk_score) / max_risk_score * 100)
            
            # Determine if review is required
            review_required = risk_score > 50 or len(risk_factors) > 3
            
            # Generate recommendations
            if risk_score > 70:
                recommendations.append("Manual review required")
                recommendations.append("Consider additional KYC verification")
            elif risk_score > 40:
                recommendations.append("Enhanced monitoring recommended")
            else:
                recommendations.append("Standard monitoring sufficient")
            
            if flagged_keywords:
                recommendations.append("Review flagged keywords and context")
            
            if geographic_risk == "high":
                recommendations.append("Verify geographic legitimacy")
            
            # Create risk assessment
            risk_assessment = RiskAssessment(
                assessment_id=assessment_id,
                transaction_id=transaction_id,
                risk_score=risk_score,
                risk_factors=risk_factors,
                recommendations=recommendations,
                review_required=review_required,
                flagged_keywords=flagged_keywords,
                geographic_risk=geographic_risk,
                compliance_score=compliance_score,
                assessed_at=datetime.now()
            )
            
            self.risk_assessments[assessment_id] = risk_assessment
            self._save_risk_assessments()
            
            logger.info(f"Completed risk assessment {assessment_id} for transaction {transaction_id}: score {risk_score}")
            return risk_assessment
            
        except Exception as e:
            logger.error(f"Error assessing transaction risk: {str(e)}")
            raise
    
    def _assess_geographic_risk(self, ip_address: str) -> str:
        """Assess geographic risk based on IP address"""
        # This would integrate with geolocation services, sanctions lists, etc.
        # For now, return a mock assessment
        try:
            # Simple mock - in production, use services like MaxMind, IP2Location, etc.
            # Also check against OFAC sanctions lists, EU sanctions lists, etc.
            
            # Mock implementation
            if ip_address.startswith('192.168') or ip_address.startswith('10.') or ip_address.startswith('172.'):
                return "internal"  # Internal network
            elif ip_address.endswith('.1') or ip_address.endswith('.254'):
                return "low"  # Network equipment
            else:
                # Random mock for demo
                import random
                risk_levels = ["low", "medium", "high"]
                return random.choice(risk_levels)
                
        except Exception as e:
            logger.error(f"Error assessing geographic risk: {str(e)}")
            return "unknown"
    
    # Business Integration Features
    
    def create_invoice_chain(self, chain_config: Dict[str, Any]) -> str:
        """Create blockchain specifically for invoice management"""
        try:
            # Add invoice-specific modules
            invoice_modules = [
                "invoice",
                "payment_settlement",
                "dispute_resolution",
                "automated_accounting"
            ]
            
            # Configure invoice-specific parameters
            invoice_params = {
                "invoice_expiry_days": 30,
                "auto_settlement": True,
                "dispute_timeout_hours": 72,
                "integration_webhooks": chain_config.get("webhook_urls", []),
                "accounting_system_integration": chain_config.get("accounting_system"),
                "compliance_level": "enhanced"
            }
            
            # This would integrate with blockchain generation engine
            # For now, return mock chain ID
            chain_id = f"invoice-{secrets.token_hex(6)}"
            
            logger.info(f"Created invoice chain {chain_id} with modules: {invoice_modules}")
            return chain_id
            
        except Exception as e:
            logger.error(f"Error creating invoice chain: {str(e)}")
            raise
    
    def create_supply_chain(self, chain_config: Dict[str, Any]) -> str:
        """Create blockchain for supply chain management"""
        try:
            supply_modules = [
                "product_tracking",
                "authentication",
                "quality_assurance",
                "logistics_coordination",
                "regulatory_compliance"
            ]
            
            supply_params = {
                "product_lifecycle_management": True,
                "regulatory_reporting": chain_config.get("compliance_regions", []),
                "integration_systems": chain_config.get("erp_systems", []),
                "quality_score_weight": 0.3,
                "traceability_depth": "full"
            }
            
            chain_id = f"supply-{secrets.token_hex(6)}"
            
            logger.info(f"Created supply chain {chain_id} with modules: {supply_modules}")
            return chain_id
            
        except Exception as e:
            logger.error(f"Error creating supply chain: {str(e)}")
            raise
    
    def setup_fiat_ramp(self, chain_id: str, ramp_config: Dict[str, Any]) -> Dict[str, Any]:
        """Setup fiat on/off-ramp integration"""
        try:
            ramp_service = ramp_config.get('service', 'simplex')  # simplex, moonpay, etc.
            
            # Configure based on service
            if ramp_service == 'simplex':
                integration_config = {
                    'api_endpoint': 'https://api.simplex.com/v1',
                    'supported_currencies': ['USD', 'EUR', 'GBP'],
                    'min_amount': 20,
                    'max_amount': 20000,
                    'kyc_required': True,
                    'geographic_restrictions': ['US', 'UK', 'EU']  # Would be more comprehensive
                }
            elif ramp_service == 'moonpay':
                integration_config = {
                    'api_endpoint': 'https://api.moonpay.io/v3',
                    'supported_currencies': ['USD', 'EUR', 'GBP', 'CAD'],
                    'min_amount': 10,
                    'max_amount': 50000,
                    'kyc_required': True,
                    'verification_levels': ['basic', 'enhanced']
                }
            else:
                raise ValueError(f"Unsupported ramp service: {ramp_service}")
            
            # Add chain-specific integration
            integration_config['chain_id'] = chain_id
            integration_config['integration_id'] = f"{ramp_service}_{chain_id}"
            integration_config['webhook_url'] = ramp_config.get('webhook_url', '')
            integration_config['api_key'] = ramp_config.get('api_key', '')  # Should be encrypted
            
            logger.info(f"Setup fiat ramp for {chain_id} with {ramp_service}")
            return integration_config
            
        except Exception as e:
            logger.error(f"Error setting up fiat ramp: {str(e)}")
            raise
    
    # Analytics and Reporting
    
    def generate_compliance_report(self, chain_id: str, report_period: str = "30d") -> Dict[str, Any]:
        """Generate compliance report"""
        try:
            # Calculate date range
            end_date = datetime.now()
            if report_period == "30d":
                start_date = end_date - timedelta(days=30)
            elif report_period == "90d":
                start_date = end_date - timedelta(days=90)
            elif report_period == "1y":
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(days=30)
            
            # Filter data by date range
            relevant_docs = [
                doc for doc in self.kyc_documents.values()
                if doc.issued_date >= start_date and doc.issued_date <= end_date
            ]
            
            relevant_entities = [
                entity for entity in self.business_entities.values()
                if entity.created_at >= start_date and entity.created_at <= end_date
            ]
            
            relevant_assessments = [
                assessment for assessment in self.risk_assessments.values()
                if assessment.assessed_at >= start_date and assessment.assessed_at <= end_date
            ]
            
            # Calculate statistics
            total_documents = len(relevant_docs)
            verified_docs = len([doc for doc in relevant_docs if doc.verification_status == "verified"])
            verification_rate = (verified_docs / total_documents * 100) if total_documents > 0 else 0
            
            total_entities = len(relevant_entities)
            verified_entities = len([entity for entity in relevant_entities if entity.verification_status == "verified"])
            entity_verification_rate = (verified_entities / total_entities * 100) if total_entities > 0 else 0
            
            # Risk statistics
            total_assessments = len(relevant_assessments)
            high_risk_assessments = len([a for a in relevant_assessments if a.risk_score >= 70])
            review_required_count = len([a for a in relevant_assessments if a.review_required])
            
            # Compliance rules statistics
            total_rules = len([rule for rule in self.compliance_rules.values() if rule.enabled])
            rules_by_type = {}
            for rule in self.compliance_rules.values():
                rule_type = rule.rule_type.value
                rules_by_type[rule_type] = rules_by_type.get(rule_type, 0) + 1
            
            report = {
                'chain_id': chain_id,
                'report_period': report_period,
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'kyc_statistics': {
                    'total_documents': total_documents,
                    'verified_documents': verified_docs,
                    'verification_rate': verification_rate,
                    'pending_documents': len([doc for doc in relevant_docs if doc.verification_status == "pending"]),
                    'rejected_documents': len([doc for doc in relevant_docs if doc.verification_status == "rejected"])
                },
                'kyb_statistics': {
                    'total_entities': total_entities,
                    'verified_entities': verified_entities,
                    'verification_rate': entity_verification_rate,
                    'pending_entities': len([entity for entity in relevant_entities if entity.verification_status == "pending"])
                },
                'risk_statistics': {
                    'total_assessments': total_assessments,
                    'high_risk_transactions': high_risk_assessments,
                    'review_required': review_required_count,
                    'avg_risk_score': sum(a.risk_score for a in relevant_assessments) / total_assessments if total_assessments > 0 else 0,
                    'high_risk_rate': (high_risk_assessments / total_assessments * 100) if total_assessments > 0 else 0
                },
                'compliance_rules': {
                    'total_active_rules': total_rules,
                    'rules_by_type': rules_by_type
                },
                'generated_at': datetime.now().isoformat()
            }
            
            logger.info(f"Generated compliance report for {chain_id}")
            return report
            
        except Exception as e:
            logger.error(f"Error generating compliance report: {str(e)}")
            raise
    
    def export_compliance_data(self, chain_id: str, export_path: str) -> bool:
        """Export compliance data"""
        try:
            export_data = {
                'chain_id': chain_id,
                'exported_at': datetime.now().isoformat(),
                'kyc_documents': [asdict(doc) for doc in self.kyc_documents.values()],
                'business_entities': [asdict(entity) for entity in self.business_entities.values()],
                'transaction_templates': [asdict(template) for template in self.transaction_templates.values()],
                'compliance_rules': [asdict(rule) for rule in self.compliance_rules.values()],
                'risk_assessments': [asdict(assessment) for assessment in self.risk_assessments.values()]
            }
            
            # Convert datetime objects to strings
            for category in ['kyc_documents', 'business_entities', 'transaction_templates', 
                           'compliance_rules', 'risk_assessments']:
                for item in export_data[category]:
                    for key, value in item.items():
                        if isinstance(value, datetime):
                            item[key] = value.isoformat()
            
            # Save export file
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Exported compliance data for {chain_id} to {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting compliance data: {str(e)}")
            return False

# Example usage and testing
if __name__ == "__main__":
    import re  # Add missing import
    import secrets  # Add missing import
    
    # Initialize compliance engine
    compliance = ComplianceEngine()
    
    # Test KYC document submission
    kyc_doc = compliance.submit_kyc_document(
        user_id="user123",
        document_type="passport",
        document_data={
            "document_number": "P123456789",
            "issued_by": "United States",
            "issued_date": "2020-01-01",
            "expiry_date": "2030-01-01"
        }
    )
    
    print(f"Submitted KYC document: {kyc_doc.document_id}")
    
    # Verify KYC document
    compliance.verify_kyc_document(
        kyc_doc.document_id,
        "verified",
        "manual_review",
        "admin_user"
    )
    
    # Create transaction template
    template = compliance.create_transaction_template(
        {
            "name": "High Value Transfer",
            "description": "Template for high-value transfers requiring approval",
            "template_type": "transfer",
            "required_fields": ["sender", "recipient", "amount", "approved"],
            "field_validations": {
                "amount": {"min": 1000, "type": int},
                "approved": {"type": bool}
            },
            "approval_workflow": [
                {"role": "compliance_officer", "required": True},
                {"role": "risk_manager", "required": True}
            ],
            "risk_score": 80
        },
        "admin_user"
    )
    
    print(f"Created template: {template.template_id}")
    
    # Create compliance rule
    rule = compliance.create_compliance_rule(
        {
            "rule_name": "High Amount Transaction Limit",
            "rule_type": "transaction_limit",
            "compliance_level": "standard",
            "chain_id": "*",
            "parameters": {
                "max_amount": 1000000,
                "daily_limit": 5000000
            },
            "priority": 10
        }
    )
    
    print(f"Created rule: {rule.rule_id}")
    
    # Test risk assessment
    risk_assessment = compliance.assess_transaction_risk(
        {
            "sender": "cosmos1test",
            "recipient": "cosmos1other",
            "amount": 2000000,
            "description": "High value transfer for business purposes"
        },
        "tx123"
    )
    
    print(f"Risk assessment: score {risk_assessment.risk_score}, factors: {risk_assessment.risk_factors}")
    
    # Generate compliance report
    report = compliance.generate_compliance_report("testnet-1")
    print(f"Compliance report: {json.dumps(report, indent=2)}")