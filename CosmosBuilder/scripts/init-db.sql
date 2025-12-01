-- CosmosBuilder Database Initialization Script
-- Run this script to set up the initial database schema

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create custom types
CREATE TYPE deployment_status AS ENUM ('pending', 'in_progress', 'completed', 'failed', 'cancelled');
CREATE TYPE user_role AS ENUM ('admin', 'user', 'viewer');
CREATE TYPE chain_status AS ENUM ('draft', 'building', 'deployed', 'stopped', 'error');
CREATE TYPE module_type AS ENUM ('consensus', 'governance', 'staking', 'mint', 'params', 'auth', 'bank', 'slashing', 'distribution', 'evidence', 'crisis', 'genutil', 'upgrade', 'custom');
CREATE TYPE consensus_type AS ENUM ('poa', 'pos', 'pbft');
CREATE TYPE deployment_provider AS ENUM ('aws', 'gcp', 'azure', 'local', 'custom');

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    organization VARCHAR(255),
    role user_role NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT true,
    email_verified BOOLEAN NOT NULL DEFAULT false,
    api_key VARCHAR(255) UNIQUE,
    subscription_tier VARCHAR(50) NOT NULL DEFAULT 'starter',
    subscription_expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE,
    login_count INTEGER NOT NULL DEFAULT 0
);

-- Sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true
);

-- Chains table
CREATE TABLE IF NOT EXISTS chains (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    chain_id VARCHAR(50) UNIQUE NOT NULL,
    genesis_config JSONB NOT NULL,
    consensus_config JSONB NOT NULL,
    consensus_type consensus_type NOT NULL,
    status chain_status NOT NULL DEFAULT 'draft',
    network_type VARCHAR(20) NOT NULL DEFAULT 'mainnet',
    chain_version VARCHAR(20),
    cosmos_sdk_version VARCHAR(20),
    modules JSONB NOT NULL DEFAULT '[]',
    deployment_config JSONB,
    deployment_provider deployment_provider,
    deployed_at TIMESTAMP WITH TIME ZONE,
    deployed_url VARCHAR(500),
    rpc_endpoint VARCHAR(500),
    rest_endpoint VARCHAR(500),
    grpc_endpoint VARCHAR(500),
    metrics_endpoint VARCHAR(500),
    public_endpoint BOOLEAN NOT NULL DEFAULT false,
    is_template BOOLEAN NOT NULL DEFAULT false,
    template_category VARCHAR(100),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Deployments table
CREATE TABLE IF NOT EXISTS deployments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chain_id UUID NOT NULL REFERENCES chains(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    deployment_type VARCHAR(50) NOT NULL DEFAULT 'standard',
    provider deployment_provider NOT NULL,
    provider_config JSONB NOT NULL,
    status deployment_status NOT NULL DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    deployment_logs JSONB DEFAULT '[]',
    monitoring_enabled BOOLEAN NOT NULL DEFAULT true,
    auto_scaling_enabled BOOLEAN NOT NULL DEFAULT false,
    backup_enabled BOOLEAN NOT NULL DEFAULT true,
    cost_estimate DECIMAL(12,2),
    actual_cost DECIMAL(12,2),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Modules table
CREATE TABLE IF NOT EXISTS modules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    module_type module_type NOT NULL,
    version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
    cosmos_sdk_version VARCHAR(20),
    configuration_schema JSONB,
    default_parameters JSONB,
    dependencies JSONB DEFAULT '[]',
    conflicts_with JSONB DEFAULT '[]',
    is_official BOOLEAN NOT NULL DEFAULT false,
    author VARCHAR(255),
    license VARCHAR(100),
    category VARCHAR(100),
    tags JSONB DEFAULT '[]',
    download_count INTEGER NOT NULL DEFAULT 0,
    rating DECIMAL(3,2),
    reviews_count INTEGER NOT NULL DEFAULT 0,
    documentation_url VARCHAR(500),
    repository_url VARCHAR(500),
    source_code_url VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Chain Modules (many-to-many relationship)
CREATE TABLE IF NOT EXISTS chain_modules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chain_id UUID NOT NULL REFERENCES chains(id) ON DELETE CASCADE,
    module_id UUID NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
    configuration JSONB NOT NULL DEFAULT '{}',
    is_enabled BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(chain_id, module_id)
);

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chain_id UUID NOT NULL REFERENCES chains(id) ON DELETE CASCADE,
    tx_hash VARCHAR(100) UNIQUE NOT NULL,
    block_number BIGINT,
    tx_index INTEGER,
    type VARCHAR(50) NOT NULL,
    from_address VARCHAR(100),
    to_address VARCHAR(100),
    value DECIMAL(20,8),
    gas_used INTEGER,
    gas_price DECIMAL(20,8),
    status VARCHAR(20) NOT NULL,
    raw_data JSONB,
    processed BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- API Keys table
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    key_hash VARCHAR(255) NOT NULL,
    key_prefix VARCHAR(20) NOT NULL,
    permissions JSONB DEFAULT '[]',
    rate_limit_per_hour INTEGER DEFAULT 1000,
    rate_limit_per_day INTEGER DEFAULT 10000,
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    usage_count INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Audit Logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    session_id UUID,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    data JSONB DEFAULT '{}',
    is_read BOOLEAN NOT NULL DEFAULT false,
    priority VARCHAR(20) NOT NULL DEFAULT 'normal',
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Subscription Plans table
CREATE TABLE IF NOT EXISTS subscription_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    price_monthly DECIMAL(10,2) NOT NULL,
    price_yearly DECIMAL(10,2),
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    max_chains INTEGER NOT NULL,
    max_deployments_per_month INTEGER,
    max_storage_gb INTEGER,
    support_level VARCHAR(50),
    features JSONB DEFAULT '[]',
    is_active BOOLEAN NOT NULL DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Usage Analytics table
CREATE TABLE IF NOT EXISTS usage_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,4),
    metric_data JSONB DEFAULT '{}',
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, metric_name, period_start)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_api_key ON users(api_key);
CREATE INDEX IF NOT EXISTS idx_chains_user_id ON chains(user_id);
CREATE INDEX IF NOT EXISTS idx_chains_status ON chains(status);
CREATE INDEX IF NOT EXISTS idx_chains_chain_id ON chains(chain_id);
CREATE INDEX IF NOT EXISTS idx_deployments_chain_id ON deployments(chain_id);
CREATE INDEX IF NOT EXISTS idx_deployments_user_id ON deployments(user_id);
CREATE INDEX IF NOT EXISTS idx_deployments_status ON deployments(status);
CREATE INDEX IF NOT EXISTS idx_transactions_chain_id ON transactions(chain_id);
CREATE INDEX IF NOT EXISTS idx_transactions_hash ON transactions(tx_hash);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at);

-- Create full-text search indexes
CREATE INDEX IF NOT EXISTS idx_chains_search ON chains USING gin(to_tsvector('english', name || ' ' || description));
CREATE INDEX IF NOT EXISTS idx_modules_search ON modules USING gin(to_tsvector('english', name || ' ' || display_name || ' ' || description));

-- Create functions for updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for automatic timestamp updates
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_chains_updated_at BEFORE UPDATE ON chains FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_deployments_updated_at BEFORE UPDATE ON deployments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_modules_updated_at BEFORE UPDATE ON modules FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_api_keys_updated_at BEFORE UPDATE ON api_keys FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default data
INSERT INTO subscription_plans (name, display_name, description, price_monthly, price_yearly, max_chains, max_deployments_per_month, max_storage_gb, support_level, features) VALUES
('starter', 'Starter', 'Perfect for individual developers and small projects', 199.00, 1990.00, 1, 100, 10, 'community', '["basic_monitoring", "community_support", "standard_templates"]'),
('professional', 'Professional', 'Ideal for growing businesses and development teams', 999.00, 9990.00, 5, 500, 50, 'priority', '["advanced_monitoring", "priority_support", "custom_templates", "analytics"]'),
('enterprise', 'Enterprise', 'Advanced features for large organizations', 4999.00, 49990.00, -1, -1, 500, 'dedicated', '["dedicated_support", "custom_integrations", "white_label", "advanced_analytics", "compliance_tools"]'),
('sovereign', 'Sovereign', 'Government-grade solutions for institutions', 19999.00, 199990.00, -1, -1, -1, 'concierge', '["concierge_support", "on_premise", "custom_development", "government_compliance", "training"]')
ON CONFLICT DO NOTHING;

-- Insert official modules
INSERT INTO modules (name, display_name, description, module_type, version, is_official, author, configuration_schema, default_parameters) VALUES
('auth', 'Authentication', 'Handles accounts and signatures', 'auth', '1.0.0', true, 'Cosmos SDK', '{"max_memo_characters": 256, "sig_verify_cost_ed25519": 590, "sig_verify_cost_secp256k1": 1000}', '{"max_memo_characters": 256}'),
('bank', 'Banking', 'Coin transfer and balance tracking', 'bank', '1.0.0', true, 'Cosmos SDK', '{"max_denom_length": 128, "_comment": "Banking module configuration"}', '{}'),
('staking', 'Staking', 'Proof of stake consensus mechanism', 'staking', '1.0.0', true, 'Cosmos SDK', '{"unbonding_time": "259200000000000", "max_validators": 100, "max_entries": 7}', '{"unbonding_time": "259200000000000", "max_validators": 100}'),
('governance', 'Governance', 'On-chain governance and proposals', 'governance', '1.0.0', true, 'Cosmos SDK', '{"min_deposit": "10000000", "max_deposit_period": "172800000000000", "voting_period": "259200000000000"}', '{"min_deposit": "10000000", "max_deposit_period": "172800000000000", "voting_period": "259200000000000"}'),
('mint', 'Minting', 'Token inflation and minting', 'mint', '1.0.0', true, 'Cosmos SDK', '{"mint_denom": "stake", "inflation_rate_change": "0.130000000000000000", "inflation_max": "0.200000000000000000"}', '{"mint_denom": "stake", "inflation_rate_change": "0.130000000000000000", "inflation_max": "0.200000000000000000"}')
ON CONFLICT DO NOTHING;

-- Create admin user (password: admin123 - change in production!)
INSERT INTO users (email, username, password_hash, full_name, role, is_active, email_verified, api_key) VALUES
('admin@cosmosbuilder.com', 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewlLw6xE6M0Kj3eW', 'Administrator', 'admin', true, true, 'cb_admin_' || substr(md5(random()::text), 1, 32))
ON CONFLICT (email) DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO cosmosbuilder;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO cosmosbuilder;