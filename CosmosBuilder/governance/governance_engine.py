#!/usr/bin/env python3
"""
CosmosBuilder Governance & Community Tools
Comprehensive governance system with proposal management, treasury control, and community features
"""

import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
import statistics
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProposalType(Enum):
    TEXT = "text"
    PARAMETER_CHANGE = "parameter_change"
    SOFTWARE_UPGRADE = "software_upgrade"
    TREASURY_SPENDING = "treasury_spending"
    COMMUNITY_POOL_SPEND = "community_pool_spend"
    TAX_RATE_CHANGE = "tax_rate_change"
    PARAMETER_CHANGE_COMPLEX = "parameter_change_complex"
    HALT_NETWORK = "halt_network"
    ENABLE_IBC = "enable_ibc"

class ProposalStatus(Enum):
    DEPOSIT_PERIOD = "deposit_period"
    VOTING_PERIOD = "voting_period"
    PASSED = "passed"
    REJECTED = "rejected"
    FAILED = "failed"
    UNSPECIFIED = "unspecified"

class VoteOption(Enum):
    YES = "yes"
    ABSTAIN = "abstain"
    NO = "no"
    NO_WITH_VETO = "no_with_veto"

@dataclass
class Proposal:
    """Governance proposal"""
    proposal_id: str
    chain_id: str
    title: str
    description: str
    proposal_type: str
    proposer: str
    initial_deposit: float
    status: str
    submit_time: datetime
    deposit_end_time: datetime
    voting_start_time: datetime
    voting_end_time: datetime
    total_deposit: float
    tally_results: Dict[str, float]
    metadata: Dict[str, Any]

@dataclass
class Vote:
    """Individual vote on a proposal"""
    vote_id: str
    proposal_id: str
    voter: str
    option: str
    weight: float
    voting_power: float
    voted_at: datetime

@dataclass
class GovernanceConfig:
    """Governance configuration for a chain"""
    chain_id: str
    voting_period: int  # days
    deposit_period: int  # days
    min_deposit: float
    max_deposit: float
    min_initial_deposit: float
    proposal_fee: float
    voting_threshold: float  # percentage
    veto_threshold: float    # percentage
    quorum: float           # minimum participation
    max_proposal_period: int  # days
    max_pending_proposals: int
    emergency_proposal_threshold: float  # voting power required

@dataclass
class TreasuryAccount:
    """Treasury account management"""
    account_id: str
    chain_id: str
    account_name: str
    account_type: str  # foundation, community_pool, ecosystem_fund
    balance: float
    frozen_balance: float
    authorized_spenders: List[str]
    spending_limits: Dict[str, float]
    created_at: datetime
    last_activity: Optional[datetime] = None

@dataclass
class TreasurySpending:
    """Treasury spending record"""
    spending_id: str
    chain_id: str
    account_id: str
    recipient: str
    amount: float
    purpose: str
    status: str  # pending, approved, rejected, executed
    proposal_id: Optional[str]
    requested_at: datetime
    approved_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None

@dataclass
class Airdrop:
    """Token airdrop management"""
    airdrop_id: str
    chain_id: str
    token_amount: float
    eligible_addresses: List[str]
    distribution_method: str  # equal, proportional, merkle
    start_date: datetime
    end_date: datetime
    status: str  # planned, active, completed, cancelled
    created_at: datetime
    metadata: Dict[str, Any]

@dataclass
class ValidatorOnboarding:
    """Validator onboarding record"""
    onboarding_id: str
    chain_id: str
    validator_address: str
    operator_address: str
    validator_name: str
    website: Optional[str]
    description: str
    commission_rate: float
    max_rate: float
    max_change_rate: float
    status: str  # pending, approved, active, suspended
    applied_at: datetime
    approved_at: Optional[datetime] = None
    metadata: Dict[str, Any]

class GovernanceEngine:
    """Main governance engine"""
    
    def __init__(self, storage_path: str = "governance/data"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Database files
        self.proposals_db = self.storage_path / "proposals.json"
        self.votes_db = self.storage_path / "votes.json"
        self.configs_db = self.storage_path / "governance_configs.json"
        self.treasury_db = self.storage_path / "treasury.json"
        self.airdrops_db = self.storage_path / "airdrops.json"
        self.validators_db = self.storage_path / "validators.json"
        
        # In-memory storage
        self.proposals = {}
        self.votes = {}
        self.governance_configs = {}
        self.treasury_accounts = {}
        self.airdrops = {}
        self.validator_onboardings = {}
        
        # Load data
        self._load_data()
    
    def _load_data(self):
        """Load all governance data"""
        self._load_proposals()
        self._load_votes()
        self._load_governance_configs()
        self._load_treasury_accounts()
        self._load_airdrops()
        self._load_validator_onboardings()
    
    def _load_proposals(self):
        """Load proposals from database"""
        try:
            if self.proposals_db.exists():
                with open(self.proposals_db, 'r') as f:
                    data = json.load(f)
                    for prop_id, prop_data in data.items():
                        prop_data['submit_time'] = datetime.fromisoformat(prop_data['submit_time'])
                        prop_data['deposit_end_time'] = datetime.fromisoformat(prop_data['deposit_end_time'])
                        prop_data['voting_start_time'] = datetime.fromisoformat(prop_data['voting_start_time'])
                        prop_data['voting_end_time'] = datetime.fromisoformat(prop_data['voting_end_time'])
                        self.proposals[prop_id] = Proposal(**prop_data)
                logger.info(f"Loaded {len(self.proposals)} proposals")
        except Exception as e:
            logger.error(f"Error loading proposals: {str(e)}")
    
    def _load_votes(self):
        """Load votes from database"""
        try:
            if self.votes_db.exists():
                with open(self.votes_db, 'r') as f:
                    data = json.load(f)
                    for vote_id, vote_data in data.items():
                        vote_data['voted_at'] = datetime.fromisoformat(vote_data['voted_at'])
                        self.votes[vote_id] = Vote(**vote_data)
                logger.info(f"Loaded {len(self.votes)} votes")
        except Exception as e:
            logger.error(f"Error loading votes: {str(e)}")
    
    def _load_governance_configs(self):
        """Load governance configurations"""
        try:
            if self.configs_db.exists():
                with open(self.configs_db, 'r') as f:
                    data = json.load(f)
                    for chain_id, config_data in data.items():
                        self.governance_configs[chain_id] = GovernanceConfig(**config_data)
                logger.info(f"Loaded {len(self.governance_configs)} governance configs")
        except Exception as e:
            logger.error(f"Error loading governance configs: {str(e)}")
    
    def _load_treasury_accounts(self):
        """Load treasury accounts"""
        try:
            if self.treasury_db.exists():
                with open(self.treasury_db, 'r') as f:
                    data = json.load(f)
                    for account_id, account_data in data.items():
                        account_data['created_at'] = datetime.fromisoformat(account_data['created_at'])
                        if account_data.get('last_activity'):
                            account_data['last_activity'] = datetime.fromisoformat(account_data['last_activity'])
                        self.treasury_accounts[account_id] = TreasuryAccount(**account_data)
                logger.info(f"Loaded {len(self.treasury_accounts)} treasury accounts")
        except Exception as e:
            logger.error(f"Error loading treasury accounts: {str(e)}")
    
    def _load_airdrops(self):
        """Load airdrops"""
        try:
            if self.airdrops_db.exists():
                with open(self.airdrops_db, 'r') as f:
                    data = json.load(f)
                    for airdrop_id, airdrop_data in data.items():
                        airdrop_data['start_date'] = datetime.fromisoformat(airdrop_data['start_date'])
                        airdrop_data['end_date'] = datetime.fromisoformat(airdrop_data['end_date'])
                        airdrop_data['created_at'] = datetime.fromisoformat(airdrop_data['created_at'])
                        self.airdrops[airdrop_id] = Airdrop(**airdrop_data)
                logger.info(f"Loaded {len(self.airdrops)} airdrops")
        except Exception as e:
            logger.error(f"Error loading airdrops: {str(e)}")
    
    def _load_validator_onboardings(self):
        """Load validator onboardings"""
        try:
            if self.validators_db.exists():
                with open(self.validators_db, 'r') as f:
                    data = json.load(f)
                    for onboarding_id, validator_data in data.items():
                        validator_data['applied_at'] = datetime.fromisoformat(validator_data['applied_at'])
                        if validator_data.get('approved_at'):
                            validator_data['approved_at'] = datetime.fromisoformat(validator_data['approved_at'])
                        self.validator_onboardings[onboarding_id] = ValidatorOnboarding(**validator_data)
                logger.info(f"Loaded {len(self.validator_onboardings)} validator onboardings")
        except Exception as e:
            logger.error(f"Error loading validator onboardings: {str(e)}")
    
    def _save_data(self):
        """Save all data to databases"""
        self._save_proposals()
        self._save_votes()
        self._save_governance_configs()
        self._save_treasury_accounts()
        self._save_airdrops()
        self._save_validator_onboardings()
    
    def _save_proposals(self):
        """Save proposals to database"""
        try:
            data = {}
            for prop_id, prop in self.proposals.items():
                prop_data = asdict(prop)
                prop_data['submit_time'] = prop.submit_time.isoformat()
                prop_data['deposit_end_time'] = prop.deposit_end_time.isoformat()
                prop_data['voting_start_time'] = prop.voting_start_time.isoformat()
                prop_data['voting_end_time'] = prop.voting_end_time.isoformat()
                data[prop_id] = prop_data
            
            with open(self.proposals_db, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving proposals: {str(e)}")
    
    def _save_votes(self):
        """Save votes to database"""
        try:
            data = {}
            for vote_id, vote in self.votes.items():
                vote_data = asdict(vote)
                vote_data['voted_at'] = vote.voted_at.isoformat()
                data[vote_id] = vote_data
            
            with open(self.votes_db, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving votes: {str(e)}")
    
    def _save_governance_configs(self):
        """Save governance configurations"""
        try:
            data = {}
            for chain_id, config in self.governance_configs.items():
                data[chain_id] = asdict(config)
            
            with open(self.configs_db, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving governance configs: {str(e)}")
    
    def _save_treasury_accounts(self):
        """Save treasury accounts"""
        try:
            data = {}
            for account_id, account in self.treasury_accounts.items():
                account_data = asdict(account)
                account_data['created_at'] = account.created_at.isoformat()
                if account.last_activity:
                    account_data['last_activity'] = account.last_activity.isoformat()
                data[account_id] = account_data
            
            with open(self.treasury_db, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving treasury accounts: {str(e)}")
    
    def _save_airdrops(self):
        """Save airdrops"""
        try:
            data = {}
            for airdrop_id, airdrop in self.airdrops.items():
                airdrop_data = asdict(airdrop)
                airdrop_data['start_date'] = airdrop.start_date.isoformat()
                airdrop_data['end_date'] = airdrop.end_date.isoformat()
                airdrop_data['created_at'] = airdrop.created_at.isoformat()
                data[airdrop_id] = airdrop_data
            
            with open(self.airdrops_db, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving airdrops: {str(e)}")
    
    def _save_validator_onboardings(self):
        """Save validator onboardings"""
        try:
            data = {}
            for onboarding_id, validator in self.validator_onboardings.items():
                validator_data = asdict(validator)
                validator_data['applied_at'] = validator.applied_at.isoformat()
                if validator.approved_at:
                    validator_data['approved_at'] = validator.approved_at.isoformat()
                data[onboarding_id] = validator_data
            
            with open(self.validators_db, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving validator onboardings: {str(e)}")
    
    # Governance Configuration Management
    
    def setup_governance_config(self, chain_id: str, config: Dict[str, Any]) -> GovernanceConfig:
        """Setup governance configuration for a chain"""
        try:
            governance_config = GovernanceConfig(
                chain_id=chain_id,
                voting_period=config.get('voting_period', 7),
                deposit_period=config.get('deposit_period', 14),
                min_deposit=config.get('min_deposit', 1000.0),
                max_deposit=config.get('max_deposit', 1000000.0),
                min_initial_deposit=config.get('min_initial_deposit', 1000.0),
                proposal_fee=config.get('proposal_fee', 0.1),
                voting_threshold=config.get('voting_threshold', 50.0),
                veto_threshold=config.get('veto_threshold', 33.4),
                quorum=config.get('quorum', 33.4),
                max_proposal_period=config.get('max_proposal_period', 14),
                max_pending_proposals=config.get('max_pending_proposals', 10),
                emergency_proposal_threshold=config.get('emergency_proposal_threshold', 60.0)
            )
            
            self.governance_configs[chain_id] = governance_config
            self._save_governance_configs()
            
            logger.info(f"Setup governance config for {chain_id}")
            return governance_config
            
        except Exception as e:
            logger.error(f"Error setting up governance config: {str(e)}")
            raise
    
    # Proposal Management
    
    def create_proposal(self, chain_id: str, title: str, description: str, 
                       proposal_type: str, proposer: str, initial_deposit: float,
                       metadata: Dict[str, Any] = None) -> Proposal:
        """Create a new governance proposal"""
        try:
            # Validate governance config exists
            if chain_id not in self.governance_configs:
                raise Exception(f"Governance config not found for chain {chain_id}")
            
            config = self.governance_configs[chain_id]
            
            # Check deposit amount
            if initial_deposit < config.min_initial_deposit:
                raise Exception(f"Initial deposit {initial_deposit} below minimum {config.min_initial_deposit}")
            
            # Generate proposal ID
            proposal_id = f"proposal_{chain_id}_{secrets.token_hex(8)}"
            
            # Calculate timing
            submit_time = datetime.now()
            deposit_end_time = submit_time + timedelta(days=config.deposit_period)
            voting_start_time = deposit_end_time  # Immediate voting start
            voting_end_time = voting_start_time + timedelta(days=config.voting_period)
            
            # Create proposal
            proposal = Proposal(
                proposal_id=proposal_id,
                chain_id=chain_id,
                title=title,
                description=description,
                proposal_type=proposal_type,
                proposer=proposer,
                initial_deposit=initial_deposit,
                status=ProposalStatus.DEPOSIT_PERIOD.value,
                submit_time=submit_time,
                deposit_end_time=deposit_end_time,
                voting_start_time=voting_start_time,
                voting_end_time=voting_end_time,
                total_deposit=initial_deposit,
                tally_results={'yes': 0.0, 'abstain': 0.0, 'no': 0.0, 'no_with_veto': 0.0},
                metadata=metadata or {}
            )
            
            self.proposals[proposal_id] = proposal
            self._save_proposals()
            
            logger.info(f"Created proposal {proposal_id}: {title}")
            return proposal
            
        except Exception as e:
            logger.error(f"Error creating proposal: {str(e)}")
            raise
    
    def submit_deposit(self, proposal_id: str, depositor: str, amount: float) -> bool:
        """Submit deposit to proposal"""
        try:
            if proposal_id not in self.proposals:
                raise Exception(f"Proposal not found: {proposal_id}")
            
            proposal = self.proposals[proposal_id]
            
            # Check proposal status
            if proposal.status != ProposalStatus.DEPOSIT_PERIOD.value:
                raise Exception(f"Proposal not in deposit period")
            
            # Check timing
            if datetime.now() > proposal.deposit_end_time:
                raise Exception("Deposit period has ended")
            
            # Update deposit
            proposal.total_deposit += amount
            
            # Check if deposit threshold reached
            config = self.governance_configs[proposal.chain_id]
            if proposal.total_deposit >= config.min_deposit:
                # Move to voting period
                proposal.status = ProposalStatus.VOTING_PERIOD.value
            
            self._save_proposals()
            
            logger.info(f"Deposit of {amount} submitted to {proposal_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error submitting deposit: {str(e)}")
            return False
    
    def cast_vote(self, proposal_id: str, voter: str, option: str, voting_power: float) -> Vote:
        """Cast vote on a proposal"""
        try:
            if proposal_id not in self.proposals:
                raise Exception(f"Proposal not found: {proposal_id}")
            
            proposal = self.proposals[proposal_id]
            
            # Check proposal status
            if proposal.status != ProposalStatus.VOTING_PERIOD.value:
                raise Exception(f"Proposal not in voting period")
            
            # Check timing
            if datetime.now() > proposal.voting_end_time:
                raise Exception("Voting period has ended")
            
            # Validate option
            if option not in ['yes', 'abstain', 'no', 'no_with_veto']:
                raise Exception(f"Invalid vote option: {option}")
            
            # Generate vote ID
            vote_id = f"vote_{proposal_id}_{hashlib.md5(voter.encode()).hexdigest()[:8]}"
            
            # Create vote
            vote = Vote(
                vote_id=vote_id,
                proposal_id=proposal_id,
                voter=voter,
                option=option,
                weight=voting_power,  # In practice, this would be based on stake
                voting_power=voting_power,
                voted_at=datetime.now()
            )
            
            self.votes[vote_id] = vote
            
            # Update proposal tally
            proposal.tally_results[option] += voting_power
            proposal.total_deposit = proposal.total_deposit  # Maintain for compatibility
            
            self._save_votes()
            self._save_proposals()
            
            logger.info(f"Vote cast on {proposal_id} by {voter}: {option}")
            return vote
            
        except Exception as e:
            logger.error(f"Error casting vote: {str(e)}")
            raise
    
    def tally_votes(self, proposal_id: str) -> Dict[str, Any]:
        """Tally votes for a proposal"""
        try:
            if proposal_id not in self.proposals:
                raise Exception(f"Proposal not found: {proposal_id}")
            
            proposal = self.proposals[proposal_id]
            config = self.governance_configs[proposal.chain_id]
            
            # Get all votes for this proposal
            proposal_votes = [vote for vote in self.votes.values() 
                            if vote.proposal_id == proposal_id]
            
            # Calculate totals
            total_voting_power = sum(vote.voting_power for vote in proposal_votes)
            turnout_rate = total_voting_power / config.quorum if config.quorum > 0 else 0
            
            # Get final tally
            yes_power = proposal.tally_results.get('yes', 0.0)
            abstain_power = proposal.tally_results.get('abstain', 0.0)
            no_power = proposal.tally_results.get('no', 0.0)
            veto_power = proposal.tally_results.get('no_with_veto', 0.0)
            
            total_power = yes_power + abstain_power + no_power + veto_power
            
            # Determine result
            passed = False
            if total_power > 0:
                yes_percentage = (yes_power / total_power) * 100
                veto_percentage = (veto_power / total_power) * 100
                
                if yes_percentage >= config.voting_threshold and veto_percentage < config.veto_threshold:
                    proposal.status = ProposalStatus.PASSED.value
                    passed = True
                else:
                    proposal.status = ProposalStatus.REJECTED.value
            
            result = {
                'proposal_id': proposal_id,
                'status': proposal.status,
                'passed': passed,
                'total_voting_power': total_power,
                'turnout_rate': turnout_rate,
                'tally': {
                    'yes': yes_power,
                    'abstain': abstain_power,
                    'no': no_power,
                    'no_with_veto': veto_power
                },
                'percentages': {
                    'yes': (yes_power / total_power * 100) if total_power > 0 else 0,
                    'abstain': (abstain_power / total_power * 100) if total_power > 0 else 0,
                    'no': (no_power / total_power * 100) if total_power > 0 else 0,
                    'no_with_veto': (veto_power / total_power * 100) if total_power > 0 else 0
                },
                'threshold_met': yes_power >= config.voting_threshold,
                'veto_threshold_met': veto_power >= config.veto_threshold,
                'tallied_at': datetime.now().isoformat()
            }
            
            self._save_proposals()
            logger.info(f"Tallied votes for {proposal_id}: {proposal.status}")
            return result
            
        except Exception as e:
            logger.error(f"Error tallying votes: {str(e)}")
            raise
    
    # Treasury Management
    
    def create_treasury_account(self, chain_id: str, account_name: str, account_type: str,
                              initial_balance: float, authorized_spenders: List[str] = None) -> TreasuryAccount:
        """Create a treasury account"""
        try:
            account_id = f"treasury_{chain_id}_{secrets.token_hex(8)}"
            
            account = TreasuryAccount(
                account_id=account_id,
                chain_id=chain_id,
                account_name=account_name,
                account_type=account_type,
                balance=initial_balance,
                frozen_balance=0.0,
                authorized_spenders=authorized_spenders or [],
                spending_limits={},
                created_at=datetime.now()
            )
            
            self.treasury_accounts[account_id] = account
            self._save_treasury_accounts()
            
            logger.info(f"Created treasury account {account_id}: {account_name}")
            return account
            
        except Exception as e:
            logger.error(f"Error creating treasury account: {str(e)}")
            raise
    
    def submit_spending_proposal(self, chain_id: str, account_id: str, recipient: str,
                               amount: float, purpose: str, proposer: str) -> Proposal:
        """Submit treasury spending proposal"""
        try:
            if account_id not in self.treasury_accounts:
                raise Exception(f"Treasury account not found: {account_id}")
            
            config = self.governance_configs[chain_id]
            
            # Create spending proposal
            proposal = self.create_proposal(
                chain_id=chain_id,
                title=f"Treasury Spending: {purpose}",
                description=f"Spend {amount} {self._get_chain_denom(chain_id)} from treasury account {account_id} to {recipient} for {purpose}",
                proposal_type=ProposalType.TREASURY_SPENDING.value,
                proposer=proposer,
                initial_deposit=config.proposal_fee,
                metadata={
                    'account_id': account_id,
                    'recipient': recipient,
                    'amount': amount,
                    'purpose': purpose
                }
            )
            
            logger.info(f"Created treasury spending proposal {proposal.proposal_id}")
            return proposal
            
        except Exception as e:
            logger.error(f"Error submitting spending proposal: {str(e)}")
            raise
    
    def execute_approved_spending(self, proposal_id: str) -> bool:
        """Execute approved treasury spending"""
        try:
            if proposal_id not in self.proposals:
                raise Exception(f"Proposal not found: {proposal_id}")
            
            proposal = self.proposals[proposal_id]
            
            # Check if proposal passed and is treasury spending
            if proposal.status != ProposalStatus.PASSED.value:
                return False
            
            if proposal.proposal_type != ProposalType.TREASURY_SPENDING.value:
                return False
            
            # Get spending details from metadata
            metadata = proposal.metadata
            account_id = metadata.get('account_id')
            recipient = metadata.get('recipient')
            amount = metadata.get('amount')
            
            if not all([account_id, recipient, amount]):
                return False
            
            # Execute spending
            account = self.treasury_accounts[account_id]
            if account.balance >= amount:
                account.balance -= amount
                account.last_activity = datetime.now()
                
                # Log spending record
                spending_id = f"spending_{secrets.token_hex(8)}"
                
                # In a real implementation, you would record this spending
                # and potentially trigger the actual transfer
                
                self._save_treasury_accounts()
                logger.info(f"Executed treasury spending: {amount} from {account_id} to {recipient}")
                return True
            else:
                logger.error(f"Insufficient balance for spending: {account.balance} < {amount}")
                return False
            
        except Exception as e:
            logger.error(f"Error executing spending: {str(e)}")
            return False
    
    # Community Tools
    
    def create_airdrop(self, chain_id: str, token_amount: float, 
                      distribution_method: str, eligible_addresses: List[str],
                      start_date: datetime, end_date: datetime,
                      metadata: Dict[str, Any] = None) -> Airdrop:
        """Create a token airdrop"""
        try:
            airdrop_id = f"airdrop_{chain_id}_{secrets.token_hex(8)}"
            
            airdrop = Airdrop(
                airdrop_id=airdrop_id,
                chain_id=chain_id,
                token_amount=token_amount,
                eligible_addresses=eligible_addresses,
                distribution_method=distribution_method,
                start_date=start_date,
                end_date=end_date,
                status="planned",
                created_at=datetime.now(),
                metadata=metadata or {}
            )
            
            self.airdrops[airdrop_id] = airdrop
            self._save_airdrops()
            
            logger.info(f"Created airdrop {airdrop_id}: {token_amount} tokens for {len(eligible_addresses)} addresses")
            return airdrop
            
        except Exception as e:
            logger.error(f"Error creating airdrop: {str(e)}")
            raise
    
    def start_airdrop(self, airdrop_id: str) -> bool:
        """Start an airdrop"""
        try:
            if airdrop_id not in self.airdrops:
                return False
            
            airdrop = self.airdrops[airdrop_id]
            airdrop.status = "active"
            
            self._save_airdrops()
            logger.info(f"Started airdrop {airdrop_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting airdrop: {str(e)}")
            return False
    
    def complete_airdrop(self, airdrop_id: str) -> bool:
        """Complete an airdrop"""
        try:
            if airdrop_id not in self.airdrops:
                return False
            
            airdrop = self.airdrops[airdrop_id]
            airdrop.status = "completed"
            
            self._save_airdrops()
            logger.info(f"Completed airdrop {airdrop_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error completing airdrop: {str(e)}")
            return False
    
    # Validator Onboarding
    
    def submit_validator_application(self, chain_id: str, validator_address: str,
                                   operator_address: str, validator_name: str,
                                   description: str, commission_rate: float,
                                   metadata: Dict[str, Any] = None) -> ValidatorOnboarding:
        """Submit validator application"""
        try:
            onboarding_id = f"onboarding_{chain_id}_{secrets.token_hex(8)}"
            
            onboarding = ValidatorOnboarding(
                onboarding_id=onboarding_id,
                chain_id=chain_id,
                validator_address=validator_address,
                operator_address=operator_address,
                validator_name=validator_name,
                website=metadata.get('website') if metadata else None,
                description=description,
                commission_rate=commission_rate,
                max_rate=metadata.get('max_rate', 100.0) if metadata else 100.0,
                max_change_rate=metadata.get('max_change_rate', 1.0) if metadata else 1.0,
                status="pending",
                applied_at=datetime.now(),
                metadata=metadata or {}
            )
            
            self.validator_onboardings[onboarding_id] = onboarding
            self._save_validator_onboardings()
            
            logger.info(f"Submitted validator application {onboarding_id}: {validator_name}")
            return onboarding
            
        except Exception as e:
            logger.error(f"Error submitting validator application: {str(e)}")
            raise
    
    def approve_validator_application(self, onboarding_id: str) -> bool:
        """Approve validator application"""
        try:
            if onboarding_id not in self.validator_onboardings:
                return False
            
            onboarding = self.validator_onboardings[onboarding_id]
            onboarding.status = "approved"
            onboarding.approved_at = datetime.now()
            
            self._save_validator_onboardings()
            logger.info(f"Approved validator application {onboarding_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error approving validator application: {str(e)}")
            return False
    
    # Analytics and Reporting
    
    def get_governance_dashboard(self, chain_id: str) -> Dict[str, Any]:
        """Get governance dashboard data"""
        try:
            # Get proposals for chain
            chain_proposals = [p for p in self.proposals.values() if p.chain_id == chain_id]
            
            # Calculate statistics
            total_proposals = len(chain_proposals)
            passed_proposals = len([p for p in chain_proposals if p.status == ProposalStatus.PASSED.value])
            pending_proposals = len([p for p in chain_proposals if p.status in [ProposalStatus.DEPOSIT_PERIOD.value, ProposalStatus.VOTING_PERIOD.value]])
            
            # Get treasury data
            chain_accounts = [a for a in self.treasury_accounts.values() if a.chain_id == chain_id]
            total_treasury_balance = sum(a.balance for a in chain_accounts)
            
            # Get airdrop data
            chain_airdrops = [a for a in self.airdrops.values() if a.chain_id == chain_id]
            active_airdrops = len([a for a in chain_airdrops if a.status == "active"])
            
            # Get validator applications
            chain_validators = [v for v in self.validator_onboardings.values() if v.chain_id == chain_id]
            pending_validators = len([v for v in chain_validators if v.status == "pending"])
            
            # Recent proposals
            cutoff_time = datetime.now() - timedelta(days=30)
            recent_proposals = [p for p in chain_proposals if p.submit_time >= cutoff_time]
            
            # Proposal type breakdown
            proposal_types = {}
            for proposal in chain_proposals:
                prop_type = proposal.proposal_type
                proposal_types[prop_type] = proposal_types.get(prop_type, 0) + 1
            
            dashboard = {
                'chain_id': chain_id,
                'governance_stats': {
                    'total_proposals': total_proposals,
                    'passed_proposals': passed_proposals,
                    'pending_proposals': pending_proposals,
                    'pass_rate': (passed_proposals / total_proposals * 100) if total_proposals > 0 else 0
                },
                'treasury_stats': {
                    'total_accounts': len(chain_accounts),
                    'total_balance': total_treasury_balance,
                    'active_accounts': len([a for a in chain_accounts if a.last_activity and 
                                         (datetime.now() - a.last_activity).days < 30])
                },
                'community_stats': {
                    'total_airdrops': len(chain_airdrops),
                    'active_airdrops': active_airdrops,
                    'pending_validators': pending_validators,
                    'total_validator_applications': len(chain_validators)
                },
                'recent_proposals': [
                    {
                        'id': p.proposal_id,
                        'title': p.title,
                        'type': p.proposal_type,
                        'status': p.status,
                        'submit_time': p.submit_time.isoformat(),
                        'total_deposit': p.total_deposit
                    } for p in sorted(recent_proposals, key=lambda x: x.submit_time, reverse=True)[:10]
                ],
                'proposal_types': proposal_types,
                'dashboard_updated': datetime.now().isoformat()
            }
            
            return dashboard
            
        except Exception as e:
            logger.error(f"Error generating governance dashboard: {str(e)}")
            return {'error': str(e)}
    
    def _get_chain_denom(self, chain_id: str) -> str:
        """Get chain denomination (mock implementation)"""
        # In production, this would query the chain configuration
        return "uatom"  # Default for Cosmos Hub
    
    def export_governance_data(self, chain_id: str, export_path: str) -> bool:
        """Export governance data for a chain"""
        try:
            export_data = {
                'chain_id': chain_id,
                'exported_at': datetime.now().isoformat(),
                'governance_config': asdict(self.governance_configs[chain_id]) if chain_id in self.governance_configs else {},
                'proposals': [asdict(p) for p in self.proposals.values() if p.chain_id == chain_id],
                'treasury_accounts': [asdict(a) for a in self.treasury_accounts.values() if a.chain_id == chain_id],
                'airdrops': [asdict(a) for a in self.airdrops.values() if a.chain_id == chain_id],
                'validator_onboardings': [asdict(v) for v in self.validator_onboardings.values() if v.chain_id == chain_id]
            }
            
            # Convert datetime objects to strings
            for item_list in ['proposals', 'treasury_accounts', 'airdrops', 'validator_onboardings']:
                for item in export_data[item_list]:
                    for key, value in item.items():
                        if isinstance(value, datetime):
                            item[key] = value.isoformat()
            
            # Save export file
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Exported governance data for {chain_id} to {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting governance data: {str(e)}")
            return False

# Example usage and testing
if __name__ == "__main__":
    # Initialize governance engine
    governance = GovernanceEngine()
    
    # Setup governance config for test chain
    config_data = {
        'voting_period': 7,
        'deposit_period': 14,
        'min_deposit': 1000.0,
        'voting_threshold': 50.0,
        'veto_threshold': 33.4,
        'quorum': 33.4
    }
    
    governance.setup_governance_config("testnet-1", config_data)
    
    # Create a test proposal
    proposal = governance.create_proposal(
        chain_id="testnet-1",
        title="Increase Block Size",
        description="Increase maximum block size to improve throughput",
        proposal_type=ProposalType.PARAMETER_CHANGE.value,
        proposer="cosmos1test",
        initial_deposit=1000.0
    )
    
    print(f"Created proposal: {proposal.proposal_id}")
    
    # Submit deposits
    governance.submit_deposit(proposal.proposal_id, "cosmos1test", 500.0)
    governance.submit_deposit(proposal.proposal_id, "cosmos1other", 500.0)
    
    # Cast votes
    governance.cast_vote(proposal.proposal_id, "cosmos1validator1", "yes", 1000000.0)
    governance.cast_vote(proposal.proposal_id, "cosmos1validator2", "yes", 500000.0)
    governance.cast_vote(proposal.proposal_id, "cosmos1validator3", "no", 200000.0)
    
    # Tally votes
    result = governance.tally_votes(proposal.proposal_id)
    print(f"Vote result: {json.dumps(result, indent=2)}")
    
    # Get dashboard
    dashboard = governance.get_governance_dashboard("testnet-1")
    print(f"Governance dashboard: {json.dumps(dashboard, indent=2)}")