#!/usr/bin/env python3
"""
CosmosBuilder Configuration Manager
Handles chain configurations, templates, and deployment settings
"""

import os
import json
import yaml
import jsonschema
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class NetworkConfig:
    """Network configuration"""
    name: str
    chain_id: str
    genesis_time: str
    network_type: str  # mainnet, testnet, devnet, localnet
    rpc_endpoint: str
    rest_endpoint: str
    grpc_endpoint: str

@dataclass
class ConsensusConfig:
    """Consensus configuration"""
    consensus_type: str  # PoS, PoA, DPoS
    min_stake: int
    max_validators: int
    unbonding_period: int  # days
    max_validators_change: int
    slash_fraction_downtime: float
    slash_fraction_double_sign: float
    downtime_jail_duration: int  # seconds

@dataclass
class GovernanceConfig:
    """Governance configuration"""
    voting_period: int  # days
    quorum: float
    threshold: float
    veto_threshold: float
    min_deposit_amount: int
    max_deposit_period: int  # days
    emergency_proposal: bool
    community_spend_proposal: bool

@dataclass
class SecurityConfig:
    """Security configuration"""
    max_memo_characters: int
    tx_sig_limit: int
    tx_size_cost_per_byte: int
    sig_verify_cost_ed25519: int
    sig_verify_cost_secp256k1: int
    enable_fee_allowance: bool
    enable_authz: bool

@dataclass
class PerformanceConfig:
    """Performance configuration"""
    max_block_gas: int
    block_time_target: float  # seconds
    max_validators_per_block: int
    max_inbound_peers: int
    max_outbound_peers: int
    pruning: str  # nothing, everything, custom
    snapshot_interval: int
    snapshot_keep_recent: int

@dataclass
class IBCConfig:
    """IBC configuration"""
    enabled: bool
    light_client_trust_period: int  # seconds
    max_clock_drift: int  # seconds
    proof_specs: List[Dict]
    trust_level: float
    connection_hops: List[str]

@dataclass
class MonitoringConfig:
    """Monitoring and observability"""
    prometheus_enabled: bool
    prometheus_port: int
    telemetry_enabled: bool
    telemetry_endpoint: str
    metrics_enabled: bool
    tracing_enabled: bool
    tracing_endpoint: str

@dataclass
class DeploymentConfig:
    """Deployment configuration"""
    deployment_type: str  # managed, cloud, self_hosted
    cloud_provider: str  # aws, gcp, azure, none
    region: str
    environment: str  # development, staging, production
    replicas: int
    auto_scaling: bool
    min_replicas: int
    max_replicas: int
    target_cpu_utilization: int
    persistent_storage: bool
    backup_enabled: bool
    backup_frequency: str  # daily, weekly, continuous

class ConfigurationManager:
    """Main configuration management system"""
    
    def __init__(self, config_dir: str = "configs"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.templates_dir = self.config_dir / "templates"
        self.templates_dir.mkdir(exist_ok=True)
        
        # Load built-in templates
        self._load_builtin_templates()
        
        # Schemas for validation
        self._load_validation_schemas()
    
    def _load_builtin_templates(self):
        """Load built-in configuration templates"""
        templates = {
            "mainnet_standard": {
                "description": "Standard mainnet configuration for production use",
                "network": {
                    "name": "Mainnet",
                    "chain_id": None,  # User will specify
                    "genesis_time": None,  # Will be calculated
                    "network_type": "mainnet",
                    "rpc_endpoint": "https://rpc.example.com",
                    "rest_endpoint": "https://rest.example.com",
                    "grpc_endpoint": "https://grpc.example.com"
                },
                "consensus": {
                    "consensus_type": "PoS",
                    "min_stake": 1000000,
                    "max_validators": 100,
                    "unbonding_period": 21,
                    "max_validators_change": 50,
                    "slash_fraction_downtime": 0.01,
                    "slash_fraction_double_sign": 0.05,
                    "downtime_jail_duration": 600
                },
                "governance": {
                    "voting_period": 7,
                    "quorum": 0.334,
                    "threshold": 0.5,
                    "veto_threshold": 0.334,
                    "min_deposit_amount": 10000000,
                    "max_deposit_period": 14,
                    "emergency_proposal": True,
                    "community_spend_proposal": True
                },
                "security": {
                    "max_memo_characters": 256,
                    "tx_sig_limit": 7,
                    "tx_size_cost_per_byte": 10,
                    "sig_verify_cost_ed25519": 590,
                    "sig_verify_cost_secp256k1": 1000,
                    "enable_fee_allowance": True,
                    "enable_authz": True
                },
                "performance": {
                    "max_block_gas": 50000000,
                    "block_time_target": 6.0,
                    "max_validators_per_block": 200,
                    "max_inbound_peers": 40,
                    "max_outbound_peers": 10,
                    "pruning": "nothing",
                    "snapshot_interval": 5000,
                    "snapshot_keep_recent": 2
                },
                "ibc": {
                    "enabled": True,
                    "light_client_trust_period": 2540400,
                    "max_clock_drift": 20,
                    "proof_specs": [
                        {
                            "leaf_spec": {"hash": "SHA256", "prehash_key": "NO_HASH", "prehash_value": "SHA256", "length": "VAR_PROTO", "prefix": "AA=="},
                            "inner_spec": {"child_order": [0, 1], "child_size": 33, "min_prefix_length": 4, "max_prefix_length": 12, "hash": "SHA256"},
                            "max_depth": 20,
                            "min_depth": 0
                        }
                    ],
                    "trust_level": "0.670000000000000000",
                    "connection_hops": ["connection-0"]
                },
                "monitoring": {
                    "prometheus_enabled": True,
                    "prometheus_port": 9090,
                    "telemetry_enabled": True,
                    "telemetry_endpoint": "/metrics",
                    "metrics_enabled": True,
                    "tracing_enabled": True,
                    "tracing_endpoint": "/v1/traces"
                },
                "deployment": {
                    "deployment_type": "managed",
                    "cloud_provider": "aws",
                    "region": "us-east-1",
                    "environment": "production",
                    "replicas": 3,
                    "auto_scaling": True,
                    "min_replicas": 3,
                    "max_replicas": 10,
                    "target_cpu_utilization": 70,
                    "persistent_storage": True,
                    "backup_enabled": True,
                    "backup_frequency": "continuous"
                }
            },
            "testnet_high_throughput": {
                "description": "Testnet configuration optimized for high throughput",
                "network": {
                    "name": "Testnet",
                    "chain_id": None,
                    "genesis_time": None,
                    "network_type": "testnet",
                    "rpc_endpoint": "https://testnet-rpc.example.com",
                    "rest_endpoint": "https://testnet-rest.example.com",
                    "grpc_endpoint": "https://testnet-grpc.example.com"
                },
                "consensus": {
                    "consensus_type": "PoS",
                    "min_stake": 100000,
                    "max_validators": 50,
                    "unbonding_period": 7,
                    "max_validators_change": 25,
                    "slash_fraction_downtime": 0.005,
                    "slash_fraction_double_sign": 0.01,
                    "downtime_jail_duration": 300
                },
                "governance": {
                    "voting_period": 3,
                    "quorum": 0.2,
                    "threshold": 0.4,
                    "veto_threshold": 0.3,
                    "min_deposit_amount": 1000000,
                    "max_deposit_period": 7,
                    "emergency_proposal": True,
                    "community_spend_proposal": True
                },
                "performance": {
                    "max_block_gas": 100000000,
                    "block_time_target": 3.0,
                    "max_validators_per_block": 100,
                    "max_inbound_peers": 20,
                    "max_outbound_peers": 5,
                    "pruning": "everything",
                    "snapshot_interval": 1000,
                    "snapshot_keep_recent": 1
                },
                "deployment": {
                    "deployment_type": "managed",
                    "cloud_provider": "gcp",
                    "region": "us-west-1",
                    "environment": "development",
                    "replicas": 1,
                    "auto_scaling": False,
                    "persistent_storage": False,
                    "backup_enabled": False
                }
            },
            "enterprise_permissioned": {
                "description": "Enterprise permissioned network configuration",
                "network": {
                    "name": "Enterprise",
                    "chain_id": None,
                    "genesis_time": None,
                    "network_type": "mainnet",
                    "rpc_endpoint": "https://enterprise-rpc.internal.com",
                    "rest_endpoint": "https://enterprise-rest.internal.com",
                    "grpc_endpoint": "https://enterprise-grpc.internal.com"
                },
                "consensus": {
                    "consensus_type": "PoA",
                    "min_stake": 0,
                    "max_validators": 10,
                    "unbonding_period": 1,
                    "max_validators_change": 5,
                    "slash_fraction_downtime": 0.1,
                    "slash_fraction_double_sign": 0.5,
                    "downtime_jail_duration": 60
                },
                "governance": {
                    "voting_period": 1,
                    "quorum": 0.5,
                    "threshold": 0.6,
                    "veto_threshold": 0.4,
                    "min_deposit_amount": 100000,
                    "max_deposit_period": 3,
                    "emergency_proposal": False,
                    "community_spend_proposal": False
                },
                "security": {
                    "max_memo_characters": 128,
                    "tx_sig_limit": 5,
                    "tx_size_cost_per_byte": 5,
                    "sig_verify_cost_ed25519": 300,
                    "sig_verify_cost_secp256k1": 500,
                    "enable_fee_allowance": False,
                    "enable_authz": True
                },
                "performance": {
                    "max_block_gas": 25000000,
                    "block_time_target": 2.0,
                    "max_validators_per_block": 50,
                    "max_inbound_peers": 10,
                    "max_outbound_peers": 5,
                    "pruning": "custom",
                    "snapshot_interval": 10000,
                    "snapshot_keep_recent": 10
                },
                "deployment": {
                    "deployment_type": "self_hosted",
                    "cloud_provider": "none",
                    "region": "on-premise",
                    "environment": "production",
                    "replicas": 5,
                    "auto_scaling": True,
                    "min_replicas": 5,
                    "max_replicas": 20,
                    "target_cpu_utilization": 80,
                    "persistent_storage": True,
                    "backup_enabled": True,
                    "backup_frequency": "daily"
                }
            }
        }
        
        # Save templates to files
        for template_name, template_data in templates.items():
            template_file = self.templates_dir / f"{template_name}.yaml"
            with open(template_file, 'w') as f:
                yaml.dump(template_data, f, default_flow_style=False)
        
        logger.info(f"Loaded {len(templates)} built-in templates")
    
    def _load_validation_schemas(self):
        """Load JSON schemas for configuration validation"""
        self.schemas = {
            "chain_config": {
                "type": "object",
                "required": ["chain_name", "chain_id", "symbol", "denomination"],
                "properties": {
                    "chain_name": {"type": "string", "minLength": 3, "maxLength": 50},
                    "chain_id": {"type": "string", "pattern": "^[a-z0-9-]+$"},
                    "symbol": {"type": "string", "minLength": 2, "maxLength": 10},
                    "denomination": {"type": "string", "pattern": "^[a-z0-9]+$"},
                    "decimals": {"type": "integer", "minimum": 0, "maximum": 18},
                    "initial_supply": {"type": "integer", "minimum": 0},
                    "description": {"type": "string", "maxLength": 200}
                }
            },
            "module_config": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["name", "enabled"],
                    "properties": {
                        "name": {"type": "string"},
                        "enabled": {"type": "boolean"},
                        "config": {"type": "object"},
                        "is_premium": {"type": "boolean"}
                    }
                }
            }
        }
    
    def get_template(self, template_name: str) -> Optional[Dict]:
        """Get a configuration template"""
        template_file = self.templates_dir / f"{template_name}.yaml"
        
        if not template_file.exists():
            logger.error(f"Template not found: {template_name}")
            return None
        
        try:
            with open(template_file, 'r') as f:
                template_data = yaml.safe_load(f)
            logger.info(f"Loaded template: {template_name}")
            return template_data
        except Exception as e:
            logger.error(f"Error loading template {template_name}: {e}")
            return None
    
    def list_templates(self) -> List[str]:
        """List available templates"""
        return [f.stem for f in self.templates_dir.glob("*.yaml")]
    
    def create_custom_template(self, template_name: str, template_data: Dict) -> bool:
        """Create a custom configuration template"""
        template_file = self.templates_dir / f"{template_name}.yaml"
        
        try:
            with open(template_file, 'w') as f:
                yaml.dump(template_data, f, default_flow_style=False)
            logger.info(f"Created custom template: {template_name}")
            return True
        except Exception as e:
            logger.error(f"Error creating template {template_name}: {e}")
            return False
    
    def validate_chain_config(self, config: Dict) -> bool:
        """Validate chain configuration against schema"""
        try:
            jsonschema.validate(config, self.schemas["chain_config"])
            logger.info("Chain configuration validation passed")
            return True
        except jsonschema.ValidationError as e:
            logger.error(f"Chain configuration validation failed: {e.message}")
            return False
    
    def validate_module_config(self, config: List[Dict]) -> bool:
        """Validate module configuration"""
        try:
            jsonschema.validate(config, self.schemas["module_config"])
            logger.info("Module configuration validation passed")
            return True
        except jsonschema.ValidationError as e:
            logger.error(f"Module configuration validation failed: {e.message}")
            return False
    
    def generate_chain_config(self, 
                            template_name: str,
                            chain_name: str,
                            chain_id: str,
                            symbol: str,
                            denomination: str,
                            **kwargs) -> Optional[Dict]:
        """Generate a complete chain configuration from a template"""
        
        # Get template
        template = self.get_template(template_name)
        if not template:
            return None
        
        # Create base configuration
        config = {
            "chain_name": chain_name,
            "chain_id": chain_id,
            "symbol": symbol,
            "denomination": denomination,
            "decimals": kwargs.get("decimals", 6),
            "initial_supply": kwargs.get("initial_supply", 1000000000),
            "description": kwargs.get("description", ""),
            "network": NetworkConfig(**template.get("network", {})),
            "consensus": ConsensusConfig(**template.get("consensus", {})),
            "governance": GovernanceConfig(**template.get("governance", {})),
            "security": SecurityConfig(**template.get("security", {})),
            "performance": PerformanceConfig(**template.get("performance", {})),
            "ibc": IBCConfig(**template.get("ibc", {})),
            "monitoring": MonitoringConfig(**template.get("monitoring", {})),
            "deployment": DeploymentConfig(**template.get("deployment", {})),
            "modules": kwargs.get("modules", []),
            "distribution": kwargs.get("distribution", {
                "community": 30.0,
                "team": 20.0,
                "treasury": 25.0,
                "validators": 15.0,
                "investors": 10.0
            })
        }
        
        # Validate configuration
        if not self.validate_chain_config(asdict(config)):
            return None
        
        # Set timestamps
        config["network"].genesis_time = datetime.now().isoformat() + "Z"
        
        logger.info(f"Generated chain configuration for {chain_name}")
        return config
    
    def save_chain_config(self, chain_id: str, config: Dict) -> bool:
        """Save chain configuration to file"""
        config_dir = self.config_dir / "chains"
        config_dir.mkdir(exist_ok=True)
        
        config_file = config_dir / f"{chain_id}.yaml"
        
        try:
            with open(config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            logger.info(f"Saved chain configuration: {chain_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration for {chain_id}: {e}")
            return False
    
    def load_chain_config(self, chain_id: str) -> Optional[Dict]:
        """Load chain configuration from file"""
        config_dir = self.config_dir / "chains"
        config_file = config_dir / f"{chain_id}.yaml"
        
        if not config_file.exists():
            logger.error(f"Configuration file not found: {chain_id}")
            return None
        
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded chain configuration: {chain_id}")
            return config
        except Exception as e:
            logger.error(f"Error loading configuration for {chain_id}: {e}")
            return None
    
    def export_config_for_deployment(self, chain_id: str) -> Optional[Dict]:
        """Export configuration specifically formatted for deployment"""
        config = self.load_chain_config(chain_id)
        if not config:
            return None
        
        # Create deployment-specific configuration
        deployment_config = {
            "chain_id": chain_id,
            "deployment": config["deployment"],
            "network": {
                "rpc_endpoint": config["network"].rpc_endpoint,
                "rest_endpoint": config["network"].rest_endpoint,
                "grpc_endpoint": config["network"].grpc_endpoint
            },
            "performance": {
                "max_block_gas": config["performance"].max_block_gas,
                "block_time_target": config["performance"].block_time_target
            },
            "monitoring": {
                "prometheus_enabled": config["monitoring"].prometheus_enabled,
                "prometheus_port": config["monitoring"].prometheus_port,
                "telemetry_enabled": config["monitoring"].telemetry_enabled
            },
            "security": {
                "enable_authz": config["security"].enable_authz,
                "enable_fee_allowance": config["security"].enable_fee_allowance
            }
        }
        
        # Add deployment-specific settings
        deployment_type = config["deployment"].deployment_type
        
        if deployment_type == "managed":
            deployment_config["kubernetes"] = {
                "replicas": config["deployment"].replicas,
                "auto_scaling": config["deployment"].auto_scaling,
                "min_replicas": config["deployment"].min_replicas,
                "max_replicas": config["deployment"].max_replicas,
                "target_cpu_utilization": config["deployment"].target_cpu_utilization
            }
        elif deployment_type == "cloud":
            deployment_config["cloud"] = {
                "provider": config["deployment"].cloud_provider,
                "region": config["deployment"].region,
                "environment": config["deployment"].environment
            }
        
        logger.info(f"Exported deployment configuration for {chain_id}")
        return deployment_config
    
    def estimate_monthly_cost(self, chain_id: str) -> Optional[Dict]:
        """Estimate monthly cost for chain deployment"""
        config = self.load_chain_config(chain_id)
        if not config:
            return None
        
        deployment_config = config["deployment"]
        
        # Cost estimation based on configuration
        base_cost = 299  # Base infrastructure cost
        
        # Add costs based on deployment type
        if deployment_config.deployment_type == "managed":
            if config["performance"].max_block_gas > 50000000:
                base_cost *= 1.5  # High performance multiplier
            if config["deployment"].replicas > 5:
                base_cost *= 1.3  # Multiple replica cost
            if config["monitoring"].prometheus_enabled:
                base_cost += 50  # Monitoring cost
        
        # Add module costs
        module_cost = 0
        for module in config.get("modules", []):
            if module.get("is_premium", False):
                module_cost += module.get("monthly_cost", 99)
        
        # Storage and backup costs
        storage_cost = 0
        if deployment_config.persistent_storage:
            storage_cost = 50
        if deployment_config.backup_enabled:
            if deployment_config.backup_frequency == "continuous":
                storage_cost += 100
            elif deployment_config.backup_frequency == "daily":
                storage_cost += 30
        
        total_cost = base_cost + module_cost + storage_cost
        
        cost_breakdown = {
            "base_infrastructure": base_cost,
            "premium_modules": module_cost,
            "storage_backup": storage_cost,
            "total_monthly": total_cost,
            "annual_cost": total_cost * 12
        }
        
        logger.info(f"Cost estimation for {chain_id}: ${total_cost}/month")
        return cost_breakdown
    
    def validate_deployment_readiness(self, chain_id: str) -> Dict:
        """Check if chain is ready for deployment"""
        config = self.load_chain_config(chain_id)
        if not config:
            return {"ready": False, "errors": ["Configuration not found"]}
        
        errors = []
        warnings = []
        
        # Check required fields
        required_fields = ["chain_name", "chain_id", "symbol", "denomination", "modules"]
        for field in required_fields:
            if not config.get(field):
                errors.append(f"Missing required field: {field}")
        
        # Check module configuration
        if not config.get("modules"):
            errors.append("No modules selected")
        
        # Check distribution
        distribution = config.get("distribution", {})
        total_percentage = sum(distribution.values())
        if abs(total_percentage - 100.0) > 0.1:
            errors.append(f"Token distribution must total 100%, got {total_percentage}%")
        
        # Check consensus parameters
        consensus = config.get("consensus", {})
        if consensus.get("consensus_type") == "PoS" and consensus.get("min_stake", 0) == 0:
            warnings.append("PoS network with zero minimum stake may have security implications")
        
        # Check governance parameters
        governance = config.get("governance", {})
        if governance.get("quorum", 0) > 0.5:
            warnings.append("High quorum requirement may make governance difficult")
        
        ready = len(errors) == 0
        
        result = {
            "ready": ready,
            "errors": errors,
            "warnings": warnings,
            "checks_passed": len(errors) == 0,
            "deployment_score": max(0, 100 - len(warnings) * 10)
        }
        
        logger.info(f"Deployment readiness check for {chain_id}: {'Ready' if ready else 'Not ready'}")
        return result

# Example usage
if __name__ == "__main__":
    # Initialize configuration manager
    config_manager = ConfigurationManager()
    
    # List available templates
    templates = config_manager.list_templates()
    print(f"Available templates: {templates}")
    
    # Generate a chain configuration
    chain_config = config_manager.generate_chain_config(
        template_name="mainnet_standard",
        chain_name="MyAwesomeChain",
        chain_id="myawesomechain-1",
        symbol="MAW",
        denomination="umaw",
        initial_supply=1000000000,
        description="A revolutionary blockchain",
        modules=[
            {"name": "CosmWasm", "enabled": True, "is_premium": True},
            {"name": "NFT Module", "enabled": True, "is_premium": False}
        ]
    )
    
    if chain_config:
        # Save configuration
        config_manager.save_chain_config("myawesomechain-1", chain_config)
        
        # Check deployment readiness
        readiness = config_manager.validate_deployment_readiness("myawesomechain-1")
        print(f"Deployment readiness: {readiness}")
        
        # Estimate costs
        costs = config_manager.estimate_monthly_cost("myawesomechain-1")
        print(f"Cost estimation: {costs}")
        
        # Export for deployment
        deploy_config = config_manager.export_config_for_deployment("myawesomechain-1")
        print(f"Deployment config exported: {deploy_config is not None}")
