#!/usr/bin/env python3
"""
CosmosBuilder Monitoring & Analytics Engine
Real-time blockchain monitoring, analytics, and alerting system
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import statistics
import threading
import time
from collections import deque
import requests
import websockets

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MetricPoint:
    """Single metric data point"""
    timestamp: datetime
    value: float
    chain_id: str
    metric_type: str
    metadata: Dict[str, Any]

@dataclass
class Alert:
    """Alert configuration and status"""
    alert_id: str
    chain_id: str
    alert_type: str
    condition: str
    threshold: float
    severity: str  # low, medium, high, critical
    status: str  # active, resolved, suppressed
    triggered_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    message: str = ""

@dataclass
class NetworkMetrics:
    """Network performance metrics"""
    chain_id: str
    block_height: int
    block_time_avg: float
    tps: float
    mempool_size: int
    active_validators: int
    total_delegations: float
    network_uptime: float
    gas_consumption: float
    governance_proposals: int
    ibc_channels: int
    last_updated: datetime

class BlockExplorer:
    """Block explorer for blockchain data"""
    
    def __init__(self, rpc_endpoint: str):
        self.rpc_endpoint = rpc_endpoint
        self.client = None
    
    async def connect(self):
        """Connect to blockchain RPC"""
        try:
            self.client = websockets.connect(self.rpc_endpoint)
            logger.info(f"Connected to RPC endpoint: {self.rpc_endpoint}")
        except Exception as e:
            logger.error(f"Failed to connect to RPC: {str(e)}")
            raise
    
    async def get_block_height(self) -> int:
        """Get current block height"""
        try:
            if not self.client:
                await self.connect()
            
            # Mock implementation - replace with actual RPC call
            # For real implementation, make JSON-RPC request to blockchain
            return 125000 + int(time.time() % 1000)
            
        except Exception as e:
            logger.error(f"Error getting block height: {str(e)}")
            return 0
    
    async def get_latest_blocks(self, limit: int = 10) -> List[Dict]:
        """Get latest blocks"""
        try:
            # Mock implementation - replace with actual RPC calls
            blocks = []
            for i in range(limit):
                block_height = 125000 - i
                blocks.append({
                    'height': block_height,
                    'time': datetime.now() - timedelta(minutes=i),
                    'tx_count': 150 + (i * 10),
                    'hash': f"block_hash_{block_height}",
                    ' proposer': f"validator_{i % 10}"
                })
            return blocks
            
        except Exception as e:
            logger.error(f"Error getting blocks: {str(e)}")
            return []
    
    async def get_transaction_data(self) -> Dict:
        """Get transaction statistics"""
        try:
            # Mock implementation - replace with actual analysis
            return {
                'total_txs': 1523456,
                'daily_volume': 125000,
                'avg_fee': 0.025,
                'success_rate': 98.5,
                'gas_usage': 21000,
                'unique_addresses': 45321
            }
            
        except Exception as e:
            logger.error(f"Error getting transaction data: {str(e)}")
            return {}

class MetricsCollector:
    """Collects and stores metrics from multiple sources"""
    
    def __init__(self, storage_path: str = "data/metrics"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.metrics_buffer = deque(maxlen=10000)
        self.collectors = {}
        self.running = False
        self.collection_interval = 30  # seconds
    
    def register_blockchain(self, chain_id: str, rpc_endpoint: str):
        """Register a blockchain for monitoring"""
        explorer = BlockExplorer(rpc_endpoint)
        self.collectors[chain_id] = explorer
        logger.info(f"Registered blockchain {chain_id} at {rpc_endpoint}")
    
    def start_collection(self):
        """Start metrics collection"""
        self.running = True
        threading.Thread(target=self._collection_loop, daemon=True).start()
        logger.info("Metrics collection started")
    
    def stop_collection(self):
        """Stop metrics collection"""
        self.running = False
        logger.info("Metrics collection stopped")
    
    def _collection_loop(self):
        """Main collection loop"""
        while self.running:
            try:
                for chain_id, explorer in self.collectors.items():
                    self._collect_chain_metrics(chain_id, explorer)
                time.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Error in collection loop: {str(e)}")
                time.sleep(5)
    
    def _collect_chain_metrics(self, chain_id: str, explorer: BlockExplorer):
        """Collect metrics for a specific chain"""
        try:
            # Get basic metrics
            block_height = asyncio.run(explorer.get_block_height())
            latest_blocks = asyncio.run(explorer.get_latest_blocks(20))
            tx_data = asyncio.run(explorer.get_transaction_data())
            
            # Calculate derived metrics
            if latest_blocks:
                block_times = []
                for i in range(1, len(latest_blocks)):
                    time_diff = (latest_blocks[i-1]['time'] - latest_blocks[i]['time']).total_seconds()
                    block_times.append(time_diff)
                
                block_time_avg = statistics.mean(block_times) if block_times else 6.0
            else:
                block_time_avg = 6.0
            
            # TPS calculation (simplified)
            total_txs = sum(block['tx_count'] for block in latest_blocks[:10])
            tps = total_txs / (block_time_avg * 10) if block_time_avg > 0 else 0
            
            # Create metrics point
            metrics = NetworkMetrics(
                chain_id=chain_id,
                block_height=block_height,
                block_time_avg=block_time_avg,
                tps=tps,
                mempool_size=125,  # Mock data
                active_validators=45,
                total_delegations=1_500_000.0,
                network_uptime=99.95,
                gas_consumption=85.2,
                governance_proposals=12,
                ibc_channels=8,
                last_updated=datetime.now()
            )
            
            # Store metrics
            metric_point = MetricPoint(
                timestamp=datetime.now(),
                value=tps,
                chain_id=chain_id,
                metric_type="tps",
                metadata=asdict(metrics)
            )
            
            self.metrics_buffer.append(metric_point)
            self._save_metrics(chain_id, metrics)
            
            logger.debug(f"Collected metrics for {chain_id}: TPS={tps:.2f}, Block Height={block_height}")
            
        except Exception as e:
            logger.error(f"Error collecting metrics for {chain_id}: {str(e)}")
    
    def _save_metrics(self, chain_id: str, metrics: NetworkMetrics):
        """Save metrics to storage"""
        try:
            filename = self.storage_path / f"{chain_id}_metrics.json"
            
            # Load existing metrics
            if filename.exists():
                with open(filename, 'r') as f:
                    data = json.load(f)
            else:
                data = {'chain_id': chain_id, 'metrics': []}
            
            # Add new metrics
            data['metrics'].append(asdict(metrics))
            
            # Keep only last 1000 entries
            if len(data['metrics']) > 1000:
                data['metrics'] = data['metrics'][-1000:]
            
            # Save back to file
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Error saving metrics for {chain_id}: {str(e)}")
    
    def get_current_metrics(self, chain_id: str) -> Optional[NetworkMetrics]:
        """Get current metrics for a chain"""
        try:
            filename = self.storage_path / f"{chain_id}_metrics.json"
            if not filename.exists():
                return None
            
            with open(filename, 'r') as f:
                data = json.load(f)
            
            if data['metrics']:
                latest = data['metrics'][-1]
                # Convert string timestamps back to datetime
                latest['last_updated'] = datetime.fromisoformat(latest['last_updated'])
                return NetworkMetrics(**latest)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting current metrics for {chain_id}: {str(e)}")
            return None
    
    def get_historical_metrics(self, chain_id: str, hours: int = 24) -> List[NetworkMetrics]:
        """Get historical metrics"""
        try:
            filename = self.storage_path / f"{chain_id}_metrics.json"
            if not filename.exists():
                return []
            
            with open(filename, 'r') as f:
                data = json.load(f)
            
            # Filter by time range
            cutoff_time = datetime.now() - timedelta(hours=hours)
            filtered_metrics = []
            
            for metric in data['metrics']:
                metric_time = datetime.fromisoformat(metric['last_updated'])
                if metric_time >= cutoff_time:
                    metric['last_updated'] = metric_time
                    filtered_metrics.append(NetworkMetrics(**metric))
            
            return filtered_metrics
            
        except Exception as e:
            logger.error(f"Error getting historical metrics for {chain_id}: {str(e)}")
            return []

class AlertManager:
    """Manages alerts and notifications"""
    
    def __init__(self):
        self.active_alerts = {}
        self.alert_configurations = {}
        self.notification_channels = []
    
    def add_alert_rule(self, alert: Alert):
        """Add an alert rule"""
        self.alert_configurations[alert.alert_id] = alert
        logger.info(f"Added alert rule: {alert.alert_id}")
    
    def check_alerts(self, chain_id: str, metrics: NetworkMetrics):
        """Check metrics against alert rules"""
        try:
            for alert_id, alert in self.alert_configurations.items():
                if alert.chain_id != chain_id or alert.status == 'suppressed':
                    continue
                
                # Evaluate condition
                triggered = self._evaluate_condition(alert, metrics)
                
                if triggered and alert.status == 'active':
                    # Alert already triggered
                    continue
                elif triggered and alert.status != 'active':
                    # Trigger alert
                    self._trigger_alert(alert, metrics)
                elif not triggered and alert.status == 'active':
                    # Resolve alert
                    self._resolve_alert(alert)
        
        except Exception as e:
            logger.error(f"Error checking alerts for {chain_id}: {str(e)}")
    
    def _evaluate_condition(self, alert: Alert, metrics: NetworkMetrics) -> bool:
        """Evaluate if alert condition is met"""
        try:
            metric_value = self._get_metric_value(alert.metric_type, metrics)
            
            if alert.condition == 'greater_than':
                return metric_value > alert.threshold
            elif alert.condition == 'less_than':
                return metric_value < alert.threshold
            elif alert.condition == 'equals':
                return abs(metric_value - alert.threshold) < 0.001
            
            return False
            
        except Exception as e:
            logger.error(f"Error evaluating condition: {str(e)}")
            return False
    
    def _get_metric_value(self, metric_type: str, metrics: NetworkMetrics) -> float:
        """Get metric value by type"""
        metric_mapping = {
            'tps': metrics.tps,
            'block_time': metrics.block_time_avg,
            'uptime': metrics.network_uptime,
            'validators': metrics.active_validators,
            'gas_consumption': metrics.gas_consumption,
            'mempool': metrics.mempool_size
        }
        
        return metric_mapping.get(metric_type, 0.0)
    
    def _trigger_alert(self, alert: Alert, metrics: NetworkMetrics):
        """Trigger an alert"""
        alert.status = 'active'
        alert.triggered_at = datetime.now()
        
        message = f"{alert.severity.upper()} Alert: {alert.alert_type} on {alert.chain_id}"
        
        if alert.alert_type == 'high_tps':
            message += f" - TPS ({metrics.tps:.2f}) exceeded threshold ({alert.threshold})"
        elif alert.alert_type == 'validator_downtime':
            message += f" - Active validators ({metrics.active_validators}) below threshold ({alert.threshold})"
        elif alert.alert_type == 'network_issues':
            message += f" - Uptime ({metrics.network_uptime:.2f}%) below threshold ({alert.threshold}%)"
        
        alert.message = message
        self.active_alerts[alert.alert_id] = alert
        
        # Send notifications
        self._send_notifications(alert)
        
        logger.warning(f"ALERT TRIGGERED: {message}")
    
    def _resolve_alert(self, alert: Alert):
        """Resolve an alert"""
        alert.status = 'resolved'
        alert.resolved_at = datetime.now()
        
        if alert.alert_id in self.active_alerts:
            del self.active_alerts[alert.alert_id]
        
        # Send resolution notification
        self._send_notifications(alert, resolved=True)
        
        logger.info(f"Alert resolved: {alert.alert_id}")
    
    def _send_notifications(self, alert: Alert, resolved: bool = False):
        """Send alert notifications"""
        try:
            # In production, integrate with:
            # - Email (SendGrid, AWS SES)
            # - Slack/Discord webhooks
            # - SMS (Twilio)
            # - Push notifications
            
            if resolved:
                message = f"✅ RESOLVED: {alert.message}"
            else:
                message = f"🚨 TRIGGERED: {alert.message}"
            
            # Log notification (replace with actual notification service)
            logger.info(f"NOTIFICATION: {message}")
            
        except Exception as e:
            logger.error(f"Error sending notifications: {str(e)}")

class AnalyticsEngine:
    """Main analytics and monitoring engine"""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        self.dashboards = {}
        self._setup_default_alerts()
    
    def _setup_default_alerts(self):
        """Setup default alert rules"""
        # High TPS alert
        high_tps_alert = Alert(
            alert_id="high_tps_default",
            chain_id="*",  # Apply to all chains
            alert_type="high_tps",
            condition="greater_than",
            threshold=10000.0,
            severity="high",
            status="active"
        )
        self.alert_manager.add_alert_rule(high_tps_alert)
        
        # Validator downtime alert
        validator_alert = Alert(
            alert_id="validator_downtime_default",
            chain_id="*",
            alert_type="validator_downtime",
            condition="less_than",
            threshold=10.0,
            severity="critical",
            status="active"
        )
        self.alert_manager.add_alert_rule(validator_alert)
        
        # Network issues alert
        uptime_alert = Alert(
            alert_id="network_issues_default",
            chain_id="*",
            alert_type="network_issues",
            condition="less_than",
            threshold=99.0,
            severity="medium",
            status="active"
        )
        self.alert_manager.add_alert_rule(uptime_alert)
    
    def start_monitoring(self, chain_id: str, rpc_endpoint: str):
        """Start monitoring a blockchain"""
        self.metrics_collector.register_blockchain(chain_id, rpc_endpoint)
        self.metrics_collector.start_collection()
        logger.info(f"Started monitoring {chain_id}")
    
    def stop_monitoring(self, chain_id: str):
        """Stop monitoring a blockchain"""
        if chain_id in self.metrics_collector.collectors:
            del self.metrics_collector.collectors[chain_id]
        logger.info(f"Stopped monitoring {chain_id}")
    
    def get_analytics_dashboard(self, chain_id: str) -> Dict[str, Any]:
        """Get analytics dashboard data"""
        try:
            current_metrics = self.metrics_collector.get_current_metrics(chain_id)
            historical_metrics = self.metrics_collector.get_historical_metrics(chain_id, 24)
            
            if not current_metrics:
                return {'error': 'No metrics available for chain'}
            
            # Calculate analytics
            dashboard = {
                'chain_id': chain_id,
                'current_metrics': asdict(current_metrics),
                'analytics': {
                    'performance_trends': self._calculate_trends(historical_metrics),
                    'health_score': self._calculate_health_score(current_metrics, historical_metrics),
                    'active_alerts': len(self.alert_manager.active_alerts),
                    'recommendations': self._generate_recommendations(current_metrics, historical_metrics)
                },
                'charts_data': {
                    'tps_history': self._format_timeseries(historical_metrics, 'tps'),
                    'block_time_history': self._format_timeseries(historical_metrics, 'block_time_avg'),
                    'uptime_history': self._format_timeseries(historical_metrics, 'network_uptime')
                }
            }
            
            return dashboard
            
        except Exception as e:
            logger.error(f"Error generating dashboard for {chain_id}: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_trends(self, metrics: List[NetworkMetrics]) -> Dict[str, str]:
        """Calculate performance trends"""
        if len(metrics) < 2:
            return {'tps': 'stable', 'uptime': 'stable'}
        
        recent = metrics[-6:]  # Last 6 data points
        older = metrics[-12:-6]  # Previous 6 data points
        
        if not older:
            return {'tps': 'stable', 'uptime': 'stable'}
        
        recent_tps_avg = sum(m.tps for m in recent) / len(recent)
        older_tps_avg = sum(m.tps for m in older) / len(older)
        
        recent_uptime_avg = sum(m.network_uptime for m in recent) / len(recent)
        older_uptime_avg = sum(m.network_uptime for m in older) / len(older)
        
        tps_trend = 'increasing' if recent_tps_avg > older_tps_avg * 1.1 else 'decreasing' if recent_tps_avg < older_tps_avg * 0.9 else 'stable'
        uptime_trend = 'improving' if recent_uptime_avg > older_uptime_avg else 'declining' if recent_uptime_avg < older_uptime_avg else 'stable'
        
        return {
            'tps': tps_trend,
            'uptime': uptime_trend
        }
    
    def _calculate_health_score(self, current: NetworkMetrics, historical: List[NetworkMetrics]) -> float:
        """Calculate network health score (0-100)"""
        try:
            score = 100.0
            
            # Deduct for low uptime
            if current.network_uptime < 99.0:
                score -= (99.0 - current.network_uptime) * 10
            
            # Deduct for high block times
            if current.block_time_avg > 8.0:
                score -= (current.block_time_avg - 6.0) * 5
            
            # Deduct for low validator count
            if current.active_validators < 10:
                score -= (10 - current.active_validators) * 2
            
            # Deduct for active alerts
            score -= len(self.alert_manager.active_alerts) * 5
            
            return max(0.0, min(100.0, score))
            
        except Exception as e:
            logger.error(f"Error calculating health score: {str(e)}")
            return 50.0
    
    def _generate_recommendations(self, current: NetworkMetrics, historical: List[NetworkMetrics]) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []
        
        try:
            if current.tps < 100:
                recommendations.append("Consider optimizing transaction processing to improve TPS")
            
            if current.block_time_avg > 7.0:
                recommendations.append("Block time is above target - consider validator optimization")
            
            if current.network_uptime < 99.5:
                recommendations.append("Network uptime below optimal - check validator health")
            
            if current.active_validators < 20:
                recommendations.append("Low validator count - consider validator incentive programs")
            
            if current.gas_consumption > 90:
                recommendations.append("High gas consumption - optimize contract code")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return ["Unable to generate recommendations"]
    
    def _format_timeseries(self, metrics: List[NetworkMetrics], field: str) -> List[Dict]:
        """Format metrics for charting"""
        try:
            result = []
            for metric in metrics[-50:]:  # Last 50 data points
                value = getattr(metric, field, 0)
                result.append({
                    'timestamp': metric.last_updated.isoformat(),
                    'value': value
                })
            return result
            
        except Exception as e:
            logger.error(f"Error formatting timeseries: {str(e)}")
            return []

# Example usage and testing
if __name__ == "__main__":
    # Initialize analytics engine
    analytics = AnalyticsEngine()
    
    # Start monitoring a test chain
    test_chain_id = "testnet-1"
    test_rpc_endpoint = "ws://localhost:26657"
    
    analytics.start_monitoring(test_chain_id, test_rpc_endpoint)
    
    # Run for a short test period
    print("Analytics engine started. Collecting metrics...")
    time.sleep(30)
    
    # Get dashboard data
    dashboard = analytics.get_analytics_dashboard(test_chain_id)
    print(f"Dashboard data: {json.dumps(dashboard, indent=2, default=str)}")
    
    # Stop monitoring
    analytics.stop_monitoring(test_chain_id)
    print("Analytics engine stopped")