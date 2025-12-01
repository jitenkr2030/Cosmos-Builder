#!/usr/bin/env python3
"""
CosmosBuilder Security & Key Management System
Enterprise-grade security features for blockchain operations
"""

import os
import json
import hashlib
import hmac
import base64
import secrets
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ec, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
import bcrypt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class KeyRecord:
    """Key management record"""
    key_id: str
    chain_id: str
    key_type: str  # validator, treasury, governance, operational
    encrypted_private_key: str
    public_key: str
    key_derivation_path: str
    backup_status: bool
    hsm_enabled: bool
    created_at: datetime
    last_used: Optional[datetime] = None
    usage_count: int = 0

@dataclass
class SecurityEvent:
    """Security event log"""
    event_id: str
    event_type: str  # key_access, failed_attempt, backup, rotation
    chain_id: str
    key_id: Optional[str]
    severity: str  # low, medium, high, critical
    timestamp: datetime
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

@dataclass
class ComplianceRule:
    """Compliance rule configuration"""
    rule_id: str
    rule_type: str  # kyc_required, whitelist_only, transaction_limits
    chain_id: str
    parameters: Dict[str, Any]
    enabled: bool
    created_at: datetime

class KeyManager:
    """Enterprise key management system"""
    
    def __init__(self, storage_path: str = "security/keys"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.keys_db = self.storage_path / "keys.json"
        self.security_events_db = self.storage_path / "security_events.json"
        self.compliance_db = self.storage_path / "compliance.json"
        
        # In-memory cache
        self.keys_cache = {}
        self.security_events = []
        self.compliance_rules = {}
        
        # Load existing data
        self._load_keys_database()
        self._load_security_events()
        self._load_compliance_rules()
    
    def _load_keys_database(self):
        """Load keys database"""
        try:
            if self.keys_db.exists():
                with open(self.keys_db, 'r') as f:
                    data = json.load(f)
                    for key_id, key_data in data.items():
                        key_data['created_at'] = datetime.fromisoformat(key_data['created_at'])
                        if key_data.get('last_used'):
                            key_data['last_used'] = datetime.fromisoformat(key_data['last_used'])
                        self.keys_cache[key_id] = KeyRecord(**key_data)
                logger.info(f"Loaded {len(self.keys_cache)} keys from database")
        except Exception as e:
            logger.error(f"Error loading keys database: {str(e)}")
    
    def _load_security_events(self):
        """Load security events"""
        try:
            if self.security_events_db.exists():
                with open(self.security_events_db, 'r') as f:
                    data = json.load(f)
                    for event_data in data:
                        event_data['timestamp'] = datetime.fromisoformat(event_data['timestamp'])
                        self.security_events.append(SecurityEvent(**event_data))
                logger.info(f"Loaded {len(self.security_events)} security events")
        except Exception as e:
            logger.error(f"Error loading security events: {str(e)}")
    
    def _load_compliance_rules(self):
        """Load compliance rules"""
        try:
            if self.compliance_db.exists():
                with open(self.compliance_db, 'r') as f:
                    data = json.load(f)
                    for rule_id, rule_data in data.items():
                        rule_data['created_at'] = datetime.fromisoformat(rule_data['created_at'])
                        self.compliance_rules[rule_id] = ComplianceRule(**rule_data)
                logger.info(f"Loaded {len(self.compliance_rules)} compliance rules")
        except Exception as e:
            logger.error(f"Error loading compliance rules: {str(e)}")
    
    def _save_keys_database(self):
        """Save keys database"""
        try:
            data = {}
            for key_id, key_record in self.keys_cache.items():
                data[key_id] = asdict(key_record)
                # Convert datetime to string
                data[key_id]['created_at'] = key_record.created_at.isoformat()
                if key_record.last_used:
                    data[key_id]['last_used'] = key_record.last_used.isoformat()
            
            with open(self.keys_db, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving keys database: {str(e)}")
    
    def _save_security_events(self):
        """Save security events"""
        try:
            data = [asdict(event) for event in self.security_events[-1000:]]  # Keep last 1000
            for event_data in data:
                event_data['timestamp'] = event_data['timestamp'].isoformat()
            
            with open(self.security_events_db, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving security events: {str(e)}")
    
    def _save_compliance_rules(self):
        """Save compliance rules"""
        try:
            data = {}
            for rule_id, rule in self.compliance_rules.items():
                data[rule_id] = asdict(rule)
                data[rule_id]['created_at'] = rule.created_at.isoformat()
            
            with open(self.compliance_db, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving compliance rules: {str(e)}")
    
    def generate_key_pair(self, chain_id: str, key_type: str, hsm_enabled: bool = False) -> KeyRecord:
        """Generate new key pair"""
        try:
            key_id = f"{chain_id}_{key_type}_{secrets.token_hex(8)}"
            
            if key_type == 'validator' and hsm_enabled:
                # Generate HSM-backed key (mock implementation)
                private_key, public_key = self._generate_hsm_key()
            else:
                # Generate software key
                private_key, public_key = self._generate_software_key(key_type)
            
            # Generate derivation path
            derivation_path = self._generate_derivation_path(chain_id, key_type)
            
            # Encrypt private key
            encrypted_private_key = self._encrypt_private_key(private_key)
            
            # Create key record
            key_record = KeyRecord(
                key_id=key_id,
                chain_id=chain_id,
                key_type=key_type,
                encrypted_private_key=encrypted_private_key,
                public_key=public_key,
                key_derivation_path=derivation_path,
                backup_status=False,
                hsm_enabled=hsm_enabled,
                created_at=datetime.now()
            )
            
            # Store key
            self.keys_cache[key_id] = key_record
            self._save_keys_database()
            
            # Log security event
            self._log_security_event(
                'key_generation',
                chain_id,
                key_id,
                'low',
                {'key_type': key_type, 'hsm_enabled': hsm_enabled}
            )
            
            logger.info(f"Generated {key_type} key for {chain_id}: {key_id}")
            return key_record
            
        except Exception as e:
            logger.error(f"Error generating key pair: {str(e)}")
            raise
    
    def _generate_software_key(self, key_type: str) -> Tuple[str, str]:
        """Generate software-based key pair"""
        try:
            if key_type == 'validator':
                # Use secp256k1 for validator keys
                private_key = ec.generate_private_key(ec.SECP256K1(), default_backend())
            else:
                # Use RSA for other keys
                private_key = rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=2048,
                    backend=default_backend()
                )
            
            # Export keys
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode()
            
            public_key = private_key.public_key()
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode()
            
            return private_pem, public_pem
            
        except Exception as e:
            logger.error(f"Error generating software key: {str(e)}")
            raise
    
    def _generate_hsm_key(self) -> Tuple[str, str]:
        """Generate HSM-backed key (mock implementation)"""
        # In production, integrate with:
        # - AWS CloudHSM
        # - Azure Key Vault
        # - HashiCorp Vault
        # - Thales Luna HSM
        
        # Mock implementation
        hsm_key_id = f"hsm_key_{secrets.token_hex(16)}"
        
        # Generate a secure random key identifier
        private_key = f"HSM_KEY_ID:{hsm_key_id}"
        public_key = f"HSM_PUBLIC_{hsm_key_id}"
        
        return private_key, public_key
    
    def _generate_derivation_path(self, chain_id: str, key_type: str) -> str:
        """Generate BIP-32 derivation path"""
        # Standard Cosmos derivation paths
        if key_type == 'validator':
            return f"m/44'/118'/0'/0/0"  # Cosmos validator path
        elif key_type == 'governance':
            return f"m/44'/118'/0'/1/0"  # Cosmos governance path
        elif key_type == 'treasury':
            return f"m/44'/118'/0'/2/0"  # Cosmos treasury path
        else:
            return f"m/44'/118'/0'/3/0"  # General operational path
    
    def _encrypt_private_key(self, private_key: str) -> str:
        """Encrypt private key with master key"""
        try:
            # Generate or load master key
            master_key_path = self.storage_path / ".master_key"
            
            if master_key_path.exists():
                with open(master_key_path, 'rb') as f:
                    master_key = f.read()
            else:
                # Generate new master key
                master_key = Fernet.generate_key()
                with open(master_key_path, 'wb') as f:
                    f.write(master_key)
                # Set restrictive permissions
                os.chmod(master_key_path, 0o600)
            
            # Encrypt private key
            fernet = Fernet(master_key)
            encrypted_key = fernet.encrypt(private_key.encode())
            
            return base64.b64encode(encrypted_key).decode()
            
        except Exception as e:
            logger.error(f"Error encrypting private key: {str(e)}")
            raise
    
    def _decrypt_private_key(self, encrypted_private_key: str) -> str:
        """Decrypt private key with master key"""
        try:
            master_key_path = self.storage_path / ".master_key"
            
            if not master_key_path.exists():
                raise Exception("Master key not found")
            
            with open(master_key_path, 'rb') as f:
                master_key = f.read()
            
            # Decrypt private key
            fernet = Fernet(master_key)
            encrypted_data = base64.b64decode(encrypted_private_key.encode())
            private_key = fernet.decrypt(encrypted_data).decode()
            
            return private_key
            
        except Exception as e:
            logger.error(f"Error decrypting private key: {str(e)}")
            raise
    
    def sign_transaction(self, key_id: str, transaction_data: bytes) -> str:
        """Sign transaction with specified key"""
        try:
            if key_id not in self.keys_cache:
                raise Exception(f"Key not found: {key_id}")
            
            key_record = self.keys_cache[key_id]
            
            # Check if key is HSM-backed
            if key_record.hsm_enabled:
                signature = self._hsm_sign(key_record, transaction_data)
            else:
                signature = self._software_sign(key_record, transaction_data)
            
            # Update usage statistics
            key_record.usage_count += 1
            key_record.last_used = datetime.now()
            
            # Save changes
            self._save_keys_database()
            
            # Log security event
            self._log_security_event(
                'key_usage',
                key_record.chain_id,
                key_id,
                'low',
                {'usage_count': key_record.usage_count}
            )
            
            return signature
            
        except Exception as e:
            logger.error(f"Error signing transaction: {str(e)}")
            self._log_security_event(
                'key_access_failed',
                '',
                key_id,
                'medium',
                {'error': str(e)}
            )
            raise
    
    def _software_sign(self, key_record: KeyRecord, data: bytes) -> str:
        """Sign data using software key"""
        try:
            # Decrypt private key
            private_key_pem = self._decrypt_private_key(key_record.encrypted_private_key)
            
            # Load private key
            private_key = serialization.load_pem_private_key(
                private_key_pem.encode(),
                password=None,
                backend=default_backend()
            )
            
            # Sign data
            if isinstance(private_key, ec.EllipticCurvePrivateKey):
                # ECDSA signing
                signature = private_key.sign(data, ec.ECDSA(hashes.SHA256()))
            else:
                # RSA signing
                signature = private_key.sign(
                    data,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
            
            return base64.b64encode(signature).decode()
            
        except Exception as e:
            logger.error(f"Error in software signing: {str(e)}")
            raise
    
    def _hsm_sign(self, key_record: KeyRecord, data: bytes) -> str:
        """Sign data using HSM key"""
        # Mock HSM signing - in production integrate with actual HSM
        hsm_key_id = key_record.encrypted_private_key.replace("HSM_KEY_ID:", "")
        
        # Simulate HSM signing
        signature_data = f"HSM_SIGNATURE:{hsm_key_id}:{data.hex()}"
        signature = hashlib.sha256(signature_data.encode()).hexdigest()
        
        return signature
    
    def backup_key(self, key_id: str, backup_location: str) -> bool:
        """Backup key to secure location"""
        try:
            if key_id not in self.keys_cache:
                return False
            
            key_record = self.keys_cache[key_id]
            
            # Create backup
            backup_data = {
                'key_record': asdict(key_record),
                'backup_timestamp': datetime.now().isoformat(),
                'checksum': hashlib.sha256(key_record.encrypted_private_key.encode()).hexdigest()
            }
            
            # Save backup
            backup_path = Path(backup_location) / f"{key_id}_backup.json"
            with open(backup_path, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            # Update key record
            key_record.backup_status = True
            
            # Save changes
            self._save_keys_database()
            
            # Log security event
            self._log_security_event(
                'key_backup',
                key_record.chain_id,
                key_id,
                'medium',
                {'backup_location': backup_location}
            )
            
            logger.info(f"Key {key_id} backed up to {backup_location}")
            return True
            
        except Exception as e:
            logger.error(f"Error backing up key: {str(e)}")
            return False
    
    def rotate_key(self, key_id: str) -> KeyRecord:
        """Rotate (regenerate) a key"""
        try:
            if key_id not in self.keys_cache:
                raise Exception(f"Key not found: {key_id}")
            
            old_key = self.keys_cache[key_id]
            
            # Generate new key with same parameters
            new_key = self.generate_key_pair(
                old_key.chain_id,
                old_key.key_type,
                old_key.hsm_enabled
            )
            
            # Log security event
            self._log_security_event(
                'key_rotation',
                old_key.chain_id,
                key_id,
                'high',
                {'new_key_id': new_key.key_id}
            )
            
            logger.info(f"Key {key_id} rotated to {new_key.key_id}")
            return new_key
            
        except Exception as e:
            logger.error(f"Error rotating key: {str(e)}")
            raise
    
    def _log_security_event(self, event_type: str, chain_id: str, key_id: Optional[str], 
                          severity: str, details: Dict[str, Any]):
        """Log security event"""
        try:
            event = SecurityEvent(
                event_id=f"{event_type}_{secrets.token_hex(8)}",
                event_type=event_type,
                chain_id=chain_id,
                key_id=key_id,
                severity=severity,
                timestamp=datetime.now(),
                details=details
            )
            
            self.security_events.append(event)
            
            # Keep only last 1000 events
            if len(self.security_events) > 1000:
                self.security_events = self.security_events[-1000:]
            
            self._save_security_events()
            
        except Exception as e:
            logger.error(f"Error logging security event: {str(e)}")
    
    def add_compliance_rule(self, rule_type: str, chain_id: str, parameters: Dict[str, Any]) -> ComplianceRule:
        """Add compliance rule"""
        try:
            rule_id = f"{chain_id}_{rule_type}_{secrets.token_hex(8)}"
            
            rule = ComplianceRule(
                rule_id=rule_id,
                rule_type=rule_type,
                chain_id=chain_id,
                parameters=parameters,
                enabled=True,
                created_at=datetime.now()
            )
            
            self.compliance_rules[rule_id] = rule
            self._save_compliance_rules()
            
            logger.info(f"Added compliance rule: {rule_id}")
            return rule
            
        except Exception as e:
            logger.error(f"Error adding compliance rule: {str(e)}")
            raise
    
    def check_compliance(self, chain_id: str, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check transaction compliance"""
        try:
            violations = []
            warnings = []
            
            # Get rules for this chain
            chain_rules = [rule for rule in self.compliance_rules.values() 
                          if rule.chain_id == chain_id and rule.enabled]
            
            for rule in chain_rules:
                if rule.rule_type == 'kyc_required':
                    if not transaction_data.get('kyc_verified', False):
                        violations.append({
                            'rule': rule.rule_id,
                            'violation': 'KYC verification required',
                            'severity': 'high'
                        })
                
                elif rule.rule_type == 'whitelist_only':
                    sender = transaction_data.get('sender', '')
                    whitelist = rule.parameters.get('whitelist', [])
                    if sender not in whitelist and sender not in rule.parameters.get('admins', []):
                        violations.append({
                            'rule': rule.rule_id,
                            'violation': 'Sender not in whitelist',
                            'severity': 'high',
                            'sender': sender
                        })
                
                elif rule.rule_type == 'transaction_limits':
                    amount = transaction_data.get('amount', 0)
                    max_amount = rule.parameters.get('max_amount', float('inf'))
                    max_daily = rule.parameters.get('max_daily', float('inf'))
                    
                    if amount > max_amount:
                        violations.append({
                            'rule': rule.rule_id,
                            'violation': f'Amount {amount} exceeds limit {max_amount}',
                            'severity': 'medium'
                        })
            
            # Log compliance check
            self._log_security_event(
                'compliance_check',
                chain_id,
                None,
                'low',
                {
                    'violations': len(violations),
                    'warnings': len(warnings),
                    'tx_data': str(transaction_data)[:200]  # Truncate for logging
                }
            )
            
            return {
                'compliant': len(violations) == 0,
                'violations': violations,
                'warnings': warnings,
                'checked_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error checking compliance: {str(e)}")
            return {
                'compliant': False,
                'violations': [{'rule': 'system_error', 'violation': str(e), 'severity': 'critical'}],
                'warnings': [],
                'checked_at': datetime.now().isoformat()
            }
    
    def get_security_dashboard(self, chain_id: Optional[str] = None) -> Dict[str, Any]:
        """Get security dashboard data"""
        try:
            # Filter events by chain if specified
            relevant_events = self.security_events
            if chain_id:
                relevant_events = [e for e in self.security_events if e.chain_id == chain_id]
            
            # Get recent events (last 24 hours)
            cutoff_time = datetime.now() - timedelta(hours=24)
            recent_events = [e for e in relevant_events if e.timestamp >= cutoff_time]
            
            # Calculate security metrics
            security_metrics = {
                'total_keys': len(self.keys_cache),
                'hsm_keys': sum(1 for k in self.keys_cache.values() if k.hsm_enabled),
                'backed_up_keys': sum(1 for k in self.keys_cache.values() if k.backup_status),
                'active_rules': len([r for r in self.compliance_rules.values() if r.enabled]),
                'recent_events': len(recent_events),
                'security_score': self._calculate_security_score()
            }
            
            # Get event categories
            event_categories = {}
            for event in recent_events:
                category = event.event_type
                event_categories[category] = event_categories.get(category, 0) + 1
            
            # Get severity breakdown
            severity_breakdown = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
            for event in recent_events:
                severity_breakdown[event.severity] += 1
            
            return {
                'chain_id': chain_id,
                'metrics': security_metrics,
                'event_categories': event_categories,
                'severity_breakdown': severity_breakdown,
                'recent_events': [asdict(e) for e in recent_events[-10:]],  # Last 10 events
                'dashboard_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating security dashboard: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_security_score(self) -> float:
        """Calculate overall security score (0-100)"""
        try:
            score = 100.0
            
            # Deduct for missing backups
            total_keys = len(self.keys_cache)
            backed_keys = sum(1 for k in self.keys_cache.values() if k.backup_status)
            if total_keys > 0:
                backup_ratio = backed_keys / total_keys
                score -= (1 - backup_ratio) * 20
            
            # Deduct for non-HSM keys (if any exist)
            software_keys = sum(1 for k in self.keys_cache.values() if not k.hsm_enabled)
            if total_keys > 0:
                software_ratio = software_keys / total_keys
                score -= software_ratio * 15
            
            # Deduct for recent security events
            cutoff_time = datetime.now() - timedelta(hours=24)
            recent_critical = sum(1 for e in self.security_events 
                                if e.timestamp >= cutoff_time and e.severity == 'critical')
            score -= recent_critical * 10
            
            return max(0.0, min(100.0, score))
            
        except Exception as e:
            logger.error(f"Error calculating security score: {str(e)}")
            return 50.0

# Example usage and testing
if __name__ == "__main__":
    # Initialize key manager
    key_manager = KeyManager()
    
    # Generate test keys
    print("Generating test keys...")
    validator_key = key_manager.generate_key_pair("testnet-1", "validator", hsm_enabled=True)
    governance_key = key_manager.generate_key_pair("testnet-1", "governance", hsm_enabled=False)
    
    print(f"Validator key ID: {validator_key.key_id}")
    print(f"Governance key ID: {governance_key.key_id}")
    
    # Test signing
    test_data = b"test transaction data"
    signature = key_manager.sign_transaction(validator_key.key_id, test_data)
    print(f"Transaction signature: {signature[:50]}...")
    
    # Test compliance
    compliance = key_manager.check_compliance("testnet-1", {
        'sender': 'cosmos1...',
        'amount': 1000000,
        'kyc_verified': True
    })
    print(f"Compliance check: {json.dumps(compliance, indent=2)}")
    
    # Get security dashboard
    dashboard = key_manager.get_security_dashboard()
    print(f"Security dashboard: {json.dumps(dashboard, indent=2)}")