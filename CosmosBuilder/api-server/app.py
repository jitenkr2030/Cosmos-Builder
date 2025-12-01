#!/usr/bin/env python3
"""
CosmosBuilder API Server
Provides RESTful APIs and WebSocket connections for the platform
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from flask_restful import Api, Resource
import os
import json
import uuid
from datetime import datetime
import threading
import time
import sys
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from blockchain-engine.builder import CosmosChainBuilder, ChainConfig
from config-manager.manager import ChainConfigManager
from deployment.deployer import CosmosBuilderDeployment

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'cosmos-builder-secret-key-2025'
CORS(app, origins="*")
socketio = SocketIO(app, cors_allowed_origins="*")
api = Api(app)

# Initialize services
chain_builder = CosmosChainBuilder()
config_manager = ChainConfigManager()
deployment_manager = CosmosBuilderDeployment()

# In-memory storage for active chains (in production, use database)
active_chains = {}
deployment_status = {}

class ChainCreationAPI(Resource):
    """API for creating and managing blockchain configurations"""
    
    def post(self):
        """Create a new blockchain configuration"""
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['chain_name', 'chain_id', 'symbol']
            for field in required_fields:
                if field not in data:
                    return {'error': f'Missing required field: {field}'}, 400
            
            # Create configuration
            config = ChainConfig(
                chain_name=data['chain_name'],
                chain_id=data['chain_id'],
                symbol=data['symbol'],
                denomination=data.get('denomination', f"u{data['symbol'].lower()}"),
                description=data.get('description', ''),
                consensus_type=data.get('consensus_type', 'PoS'),
                initial_supply=data.get('initial_supply', 1000000000),
                min_stake=data.get('min_stake', 1000000),
                max_validators=data.get('max_validators', 100)
            )
            
            # Validate configuration
            if not config_manager.validate_chain_config(config.__dict__):
                return {'error': 'Invalid chain configuration'}, 400
            
            # Generate unique chain ID
            chain_uuid = str(uuid.uuid4())
            
            # Store configuration
            active_chains[chain_uuid] = {
                'config': config.__dict__,
                'created_at': datetime.now().isoformat(),
                'status': 'created',
                'build_progress': 0
            }
            
            # Start async build process
            threading.Thread(target=self._build_blockchain_async, args=(chain_uuid,)).start()
            
            return {
                'chain_id': chain_uuid,
                'config': config.__dict__,
                'status': 'created',
                'message': 'Blockchain creation started'
            }, 201
            
        except Exception as e:
            logger.error(f"Error creating blockchain: {str(e)}")
            return {'error': str(e)}, 500
    
    def _build_blockchain_async(self, chain_uuid):
        """Async blockchain building process"""
        try:
            chain_data = active_chains[chain_uuid]
            config = ChainConfig(**chain_data['config'])
            
            # Update status
            active_chains[chain_uuid]['status'] = 'building'
            active_chains[chain_uuid]['build_progress'] = 10
            socketio.emit('build_progress', {
                'chain_id': chain_uuid,
                'progress': 10,
                'status': 'Initializing build...'
            })
            
            # Generate blockchain code
            output_dir = f"generated_chains/{chain_uuid}"
            result = chain_builder.generate_blockchain(config, [], output_dir)
            
            active_chains[chain_uuid]['build_progress'] = 50
            socketio.emit('build_progress', {
                'chain_id': chain_uuid,
                'progress': 50,
                'status': 'Generating code...'
            })
            
            # Generate additional artifacts
            chain_builder.generate_docker_compose(config, output_dir)
            chain_builder.generate_helm_chart(config, output_dir)
            chain_builder.generate_docs(Path(output_dir), config, [])
            
            active_chains[chain_uuid]['build_progress'] = 90
            socketio.emit('build_progress', {
                'chain_id': chain_uuid,
                'progress': 90,
                'status': 'Finalizing...'
            })
            
            # Complete build
            active_chains[chain_uuid]['status'] = 'built'
            active_chains[chain_uuid]['build_progress'] = 100
            active_chains[chain_uuid]['output_dir'] = output_dir
            
            socketio.emit('build_complete', {
                'chain_id': chain_uuid,
                'status': 'completed',
                'output_dir': output_dir,
                'artifacts': [
                    'blockchain_code',
                    'docker_compose',
                    'helm_chart',
                    'documentation'
                ]
            })
            
        except Exception as e:
            logger.error(f"Error building blockchain {chain_uuid}: {str(e)}")
            active_chains[chain_uuid]['status'] = 'error'
            active_chains[chain_uuid]['error'] = str(e)
            socketio.emit('build_error', {
                'chain_id': chain_uuid,
                'error': str(e)
            })

class ChainDeploymentAPI(Resource):
    """API for deploying blockchains"""
    
    def post(self):
        """Deploy a built blockchain"""
        try:
            data = request.get_json()
            
            required_fields = ['chain_id', 'deployment_target']
            for field in required_fields:
                if field not in data:
                    return {'error': f'Missing required field: {field}'}, 400
            
            chain_uuid = data['chain_id']
            if chain_uuid not in active_chains:
                return {'error': 'Chain not found'}, 404
            
            if active_chains[chain_uuid]['status'] != 'built':
                return {'error': 'Chain not ready for deployment'}, 400
            
            # Initialize deployment specs
            deployment_specs = deployment_manager.DeploymentSpecs()
            deployment_specs.provider = data['deployment_target']
            deployment_specs.cloud_region = data.get('cloud_region', 'us-east-1')
            deployment_specs.node_count = data.get('node_count', 1)
            deployment_specs.vm_size = data.get('vm_size', 'medium')
            deployment_specs.storage_size = data.get('storage_size', 100)  # GB
            
            # Start deployment
            deployment_id = str(uuid.uuid4())
            threading.Thread(target=self._deploy_async, args=(deployment_id, chain_uuid, deployment_specs)).start()
            
            deployment_status[deployment_id] = {
                'chain_id': chain_uuid,
                'status': 'deploying',
                'created_at': datetime.now().isoformat()
            }
            
            return {
                'deployment_id': deployment_id,
                'chain_id': chain_uuid,
                'status': 'deploying'
            }, 202
            
        except Exception as e:
            logger.error(f"Error deploying blockchain: {str(e)}")
            return {'error': str(e)}, 500
    
    def _deploy_async(self, deployment_id, chain_uuid, specs):
        """Async deployment process"""
        try:
            chain_data = active_chains[chain_uuid]
            output_dir = chain_data['output_dir']
            
            deployment_status[deployment_id]['status'] = 'in_progress'
            socketio.emit('deployment_progress', {
                'deployment_id': deployment_id,
                'progress': 20,
                'status': 'Preparing infrastructure...'
            })
            
            # Deploy blockchain
            result = deployment_manager.deploy_blockchain(
                chain_data['config']['chain_id'],
                output_dir,
                specs
            )
            
            deployment_status[deployment_id]['status'] = 'completed'
            deployment_status[deployment_id]['endpoints'] = result.get('endpoints', {})
            deployment_status[deployment_id]['completed_at'] = datetime.now().isoformat()
            
            socketio.emit('deployment_complete', {
                'deployment_id': deployment_id,
                'status': 'completed',
                'endpoints': result.get('endpoints', {})
            })
            
        except Exception as e:
            logger.error(f"Error in deployment {deployment_id}: {str(e)}")
            deployment_status[deployment_id]['status'] = 'error'
            deployment_status[deployment_id]['error'] = str(e)
            socketio.emit('deployment_error', {
                'deployment_id': deployment_id,
                'error': str(e)
            })

class ChainStatusAPI(Resource):
    """API for checking chain status"""
    
    def get(self, chain_uuid):
        """Get chain status"""
        if chain_uuid not in active_chains:
            return {'error': 'Chain not found'}, 404
        
        return {
            'chain_id': chain_uuid,
            'status': active_chains[chain_uuid]['status'],
            'progress': active_chains[chain_uuid].get('build_progress', 0),
            'config': active_chains[chain_uuid]['config'],
            'created_at': active_chains[chain_uuid]['created_at']
        }

class DeploymentStatusAPI(Resource):
    """API for deployment status"""
    
    def get(self, deployment_id):
        """Get deployment status"""
        if deployment_id not in deployment_status:
            return {'error': 'Deployment not found'}, 404
        
        return deployment_status[deployment_id]

class MetricsAPI(Resource):
    """API for chain metrics"""
    
    def get(self, chain_uuid):
        """Get blockchain metrics"""
        # Mock metrics data (in production, collect from blockchain)
        return {
            'chain_id': chain_uuid,
            'metrics': {
                'block_height': 125000,
                'tps': 1250,
                'active_validators': 45,
                'total_delegations': '1.5M',
                'network_uptime': 99.95,
                'gas_consumption': 85.2,
                'governance_proposals': 12,
                'ibc_channels': 8
            },
            'timestamp': datetime.now().isoformat()
        }

# WebSocket events
@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')
    emit('connected', {'message': 'Connected to CosmosBuilder WebSocket'})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected')

@socketio.on('join_chain_room')
def handle_join_chain_room(data):
    chain_id = data['chain_id']
    socketio.emit('join_chain_room', {'chain_id': chain_id})

# Register API routes
api.add_resource(ChainCreationAPI, '/api/v1/chains')
api.add_resource(ChainStatusAPI, '/api/v1/chains/<string:chain_uuid>')
api.add_resource(ChainDeploymentAPI, '/api/v1/deploy')
api.add_resource(DeploymentStatusAPI, '/api/v1/deployments/<string:deployment_id>')
api.add_resource(MetricsAPI, '/api/v1/metrics/<string:chain_uuid>')

# Health check endpoint
@app.route('/health')
def health_check():
    return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}

# API documentation endpoint
@app.route('/api/docs')
def api_docs():
    return jsonify({
        'title': 'CosmosBuilder API',
        'version': '1.0.0',
        'description': 'RESTful API for CosmosBuilder platform',
        'endpoints': {
            'POST /api/v1/chains': 'Create new blockchain',
            'GET /api/v1/chains/{id}': 'Get chain status',
            'POST /api/v1/deploy': 'Deploy blockchain',
            'GET /api/v1/deployments/{id}': 'Get deployment status',
            'GET /api/v1/metrics/{id}': 'Get chain metrics'
        },
        'websocket': {
            'events': ['build_progress', 'build_complete', 'build_error', 'deployment_progress', 'deployment_complete', 'deployment_error']
        }
    })

if __name__ == '__main__':
    # Ensure required directories exist
    os.makedirs('generated_chains', exist_ok=True)
    os.makedirs('deployments', exist_ok=True)
    
    # Run the server
    logger.info("Starting CosmosBuilder API Server...")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)