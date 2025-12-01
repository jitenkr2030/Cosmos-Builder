#!/usr/bin/env python3
"""
CosmosBuilder Developer Tools & SDK Generator
Generates client libraries, smart contract tools, and developer APIs
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from dataclasses import dataclass
import subprocess
import tempfile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SDKConfig:
    """SDK generation configuration"""
    chain_id: str
    chain_name: str
    chain_address_prefix: str
    rpc_endpoint: str
    rest_endpoint: str
    denoms: List[str]
    bech32_hrp: str
    min_tx_fee: int
    gas_adjustment: float
    features: List[str]

@dataclass
class ContractTemplate:
    """Smart contract template"""
    contract_name: str
    contract_type: str  # wasm, solidity, rust
    template_path: str
    description: str
    dependencies: List[str]
    build_commands: List[str]

class SDKGenerator:
    """Multi-language SDK generator"""
    
    def __init__(self, storage_path: str = "developer-tools/sdks"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # SDK templates and configurations
        self.java_script_template = self.storage_path / "templates" / "javascript"
        self.python_template = self.storage_path / "templates" / "python"
        self.go_template = self.storage_path / "templates" / "go"
        self.mobile_template = self.storage_path / "templates" / "mobile"
        
        # Contract templates
        self.contract_templates = self.storage_path / "contract-templates"
        self.contract_templates.mkdir(exist_ok=True)
        
        # Initialize templates
        self._initialize_templates()
    
    def _initialize_templates(self):
        """Initialize SDK templates"""
        try:
            # Create template directories
            for template_dir in [self.java_script_template, self.python_template, 
                               self.go_template, self.mobile_template]:
                template_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize JavaScript template
            self._create_javascript_template()
            
            # Initialize Python template
            self._create_python_template()
            
            # Initialize Go template
            self._create_go_template()
            
            # Initialize Mobile template
            self._create_mobile_template()
            
            # Initialize contract templates
            self._create_contract_templates()
            
            logger.info("SDK templates initialized")
            
        except Exception as e:
            logger.error(f"Error initializing templates: {str(e)}")
    
    def _create_javascript(self):
        """Create JavaScript/TypeScript SDK"""
        pass
    
    def _create_javascript_template(self):
        """Create JavaScript SDK template"""
        try:
            # Package.json
            package_json = {
                "name": f"@cosmjs-{self.sdk_config.chain_id}",
                "version": "1.0.0",
                "description": f"{self.sdk_config.chain_name} JavaScript SDK",
                "main": "dist/index.js",
                "types": "dist/index.d.ts",
                "scripts": {
                    "build": "tsc",
                    "dev": "ts-node src/index.ts",
                    "test": "jest",
                    "lint": "eslint src/**/*.ts",
                    "format": "prettier --write src/**/*.ts"
                },
                "dependencies": {
                    "@cosmjs/amino": "^0.32.0",
                    "@cosmjs/ledger-cosmos": "^0.32.0",
                    "@cosmjs/math": "^0.32.0",
                    "@cosmjs/proto-signing": "^0.32.0",
                    "@cosmjs/stargate": "^0.32.0",
                    "@cosmjs/tendermint-rpc": "^0.32.0"
                },
                "devDependencies": {
                    "@types/node": "^20.0.0",
                    "typescript": "^5.0.0",
                    "eslint": "^8.0.0",
                    "prettier": "^3.0.0",
                    "jest": "^29.0.0",
                    "ts-jest": "^29.0.0",
                    "@types/jest": "^29.0.0"
                },
                "keywords": ["cosmos", "blockchain", "sdk"],
                "author": "CosmosBuilder",
                "license": "MIT"
            }
            
            # TypeScript config
            ts_config = {
                "compilerOptions": {
                    "target": "ES2020",
                    "module": "commonjs",
                    "lib": ["ES2020"],
                    "declaration": True,
                    "outDir": "./dist",
                    "rootDir": "./src",
                    "strict": True,
                    "esModuleInterop": True,
                    "skipLibCheck": True,
                    "forceConsistentCasingInFileNames": True,
                    "resolveJsonModule": True
                },
                "include": ["src/**/*"],
                "exclude": ["node_modules", "dist", "**/*.test.ts"]
            }
            
            # Main SDK file
            sdk_main = self._get_javascript_sdk_main()
            
            # Account utilities
            account_utils = self._get_javascript_account_utils()
            
            # Transaction utilities
            tx_utils = self._get_javascript_tx_utils()
            
            # Save files
            self._save_template_file(self.java_script_template / "package.json", json.dumps(package_json, indent=2))
            self._save_template_file(self.java_script_template / "tsconfig.json", json.dumps(ts_config, indent=2))
            
            src_dir = self.java_script_template / "src"
            src_dir.mkdir(exist_ok=True)
            self._save_template_file(src_dir / "index.ts", sdk_main)
            self._save_template_file(src_dir / "account.ts", account_utils)
            self._save_template_file(src_dir / "transactions.ts", tx_utils)
            
            logger.info("JavaScript template created")
            
        except Exception as e:
            logger.error(f"Error creating JavaScript template: {str(e)}")
    
    def _create_python_template(self):
        """Create Python SDK template"""
        try:
            # Setup.py
            setup_py = f'''
from setuptools import setup, find_packages

setup(
    name="cosmosbuilder-{self.sdk_config.chain_id}",
    version="1.0.0",
    description="{self.sdk_config.chain_name} Python SDK",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/cosmosbuilder/{self.sdk_config.chain_id}",
    author="CosmosBuilder",
    author_email="contact@cosmosbuilder.com",
    packages=find_packages(),
    install_requires=[
        "cosmos-py>=0.45.0",
        "bech32>=1.2.0",
        "typing-extensions>=4.0.0",
        "requests>=2.25.0",
        "websocket-client>=1.0.0",
        "protobuf>=4.21.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
'''
            
            # Main SDK file
            sdk_main = self._get_python_sdk_main()
            
            # Client utilities
            client_utils = self._get_python_client_utils()
            
            # Save files
            self._save_template_file(self.python_template / "setup.py", setup_py)
            self._save_template_file(self.python_template / "README.md", self._get_python_readme())
            
            src_dir = self.python_template / f"cosmosbuilder_{self.sdk_config.chain_id.replace('-', '_')}"
            src_dir.mkdir(exist_ok=True)
            self._save_template_file(src_dir / "__init__.py", f'"""\\n{self.sdk_config.chain_name} Python SDK\\n"""\\n\\n__version__ = "1.0.0"\\n')
            self._save_template_file(src_dir / "client.py", client_utils)
            self._save_template_file(src_dir / "utils.py", self._get_python_utils())
            
            logger.info("Python template created")
            
        except Exception as e:
            logger.error(f"Error creating Python template: {str(e)}")
    
    def _create_go_template(self):
        """Create Go SDK template"""
        try:
            # go.mod
            go_mod = f'''
module github.com/cosmosbuilder/{self.sdk_config.chain_id}

go 1.20

require (
    github.com/cosmos/cosmos-sdk v0.47.0
    github.com/cosmos/gaia/v7 v7.0.0
    github.com/tendermint/tendermint v0.34.26
    github.com/cosmos/relayer/v2 v2.4.0
)

require (
    github.com/99designs/keyring v1.2.1 // indirect
    github.com/bech32/bech32 v1.2.0 // indirect
    github.com/bgentry/speakeasy v0.1.0 // indirect
    github.com/davecgh/go-spew v1.1.1 // indirect
    github.com/google/uuid v1.3.0 // indirect
    github.com/gorilla/websocket v1.4.2 // indirect
    github.com/grpc-ecosystem/go-grpc-middleware v1.3.0 // indirect
    github.com/grpc-ecosystem/go-grpc-prometheus v1.2.0 // indirect
    github.com/pkg/errors v0.9.1 // indirect
    github.com/spf13/cobra v1.6.1 // indirect
    github.com/spf13/pflag v1.0.5 // indirect
    github.com/spf13/viper v1.14.0 // indirect
    github.com/stretchr/testify v1.8.2 // indirect
    golang.org/x/crypto v0.5.0 // indirect
    golang.org/x/sys v0.4.0 // indirect
    golang.org/x/text v0.7.0 // indirect
    gopkg.in/yaml.v2 v2.4.0 // indirect
)
'''
            
            # Main SDK file
            sdk_main = self._get_go_sdk_main()
            
            # Client utilities
            client_utils = self._get_go_client_utils()
            
            # Save files
            self._save_template_file(self.go_template / "go.mod", go_mod)
            
            src_dir = self.go_template / "internal" / "client"
            src_dir.mkdir(parents=True, exist_ok=True)
            self._save_template_file(src_dir / "client.go", client_utils)
            self._save_template_file(src_dir / "config.go", self._get_go_config())
            self._save_template_file(src_dir / "queries.go", self._get_go_queries())
            
            logger.info("Go template created")
            
        except Exception as e:
            logger.error(f"Error creating Go template: {str(e)}")
    
    def _create_mobile_template(self):
        """Create Mobile SDK template (Swift & Kotlin)"""
        try:
            # Swift package
            swift_package = {
                "name": "CosmosBuilderSDK",
                "platforms": ["iOS", "macOS"],
                "products": [
                    {
                        "name": "CosmosBuilderSDK",
                        "targets": ["CosmosBuilderSDK"]
                    }
                ],
                "targets": [
                    {
                        "name": "CosmosBuilderSDK",
                        "type": "library",
                        "path": "Sources",
                        "sources": ["CosmosBuilderSDK.swift", "Account.swift", "Transactions.swift"],
                        "dependencies": [
                            {"product": "CosmosCryptoSwift", "type": "upToNextMajor", "minimumVersion": "1.0.0"},
                            {"product": "Tendermint", "type": "upToNextMajor", "minimumVersion": "1.0.0"}
                        ]
                    }
                ]
            }
            
            # Swift main file
            swift_main = self._get_swift_sdk_main()
            
            # Kotlin gradle
            gradle_build = '''
plugins {
    id 'com.android.library'
    id 'org.jetbrains.kotlin.android'
    id 'org.jetbrains.kotlin.plugin.serialization'
}

android {
    namespace 'com.cosmosbuilder.sdk'
    compileSdk 33

    defaultConfig {
        minSdk 21
        targetSdk 33
        versionCode 1
        versionName "1.0.0"

        testInstrumentationRunner "androidx.test.runner.AndroidJUnitRunner"
        consumerProguardFiles "consumer-rules.pro"
    }

    buildTypes {
        release {
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }
    compileOptions {
        sourceCompatibility JavaVersion.VERSION_1_8
        targetCompatibility JavaVersion.VERSION_1_8
    }
    kotlinOptions {
        jvmTarget = '1.8'
    }
}

dependencies {
    implementation 'org.jetbrains.kotlinx:kotlinx-coroutines-android:1.6.4'
    implementation 'io.ktor:ktor-client-android:2.3.0'
    implementation 'com.squareup.okhttp3:okhttp:4.10.0'
    implementation 'com.google.protobuf:protobuf-kotlin-lite:3.21.0'
    testImplementation 'junit:junit:4.13.2'
    androidTestImplementation 'androidx.test.ext:junit:1.1.5'
    androidTestImplementation 'androidx.test.espresso:espresso-core:3.5.1'
}
'''
            
            # Kotlin main file
            kotlin_main = self._get_kotlin_sdk_main()
            
            # Save files
            # Swift files
            swift_dir = self.mobile_template / "ios" / "CosmosBuilderSDK"
            swift_dir.mkdir(parents=True, exist_ok=True)
            self._save_template_file(swift_dir / "Package.swift", json.dumps(swift_package, indent=2))
            self._save_template_file(swift_dir / "CosmosBuilderSDK.swift", swift_main)
            
            # Kotlin files
            kotlin_dir = self.mobile_template / "android"
            kotlin_dir.mkdir(exist_ok=True)
            self._save_template_file(kotlin_dir / "build.gradle", gradle_build)
            
            src_dir = kotlin_dir / "src" / "main" / "kotlin" / "com" / "cosmosbuilder" / "sdk"
            src_dir.mkdir(parents=True, exist_ok=True)
            self._save_template_file(src_dir / "CosmosBuilderSDK.kt", kotlin_main)
            self._save_template_file(src_dir / "Account.kt", self._get_kotlin_account())
            self._save_template_file(src_dir / "Transactions.kt", self._get_kotlin_transactions())
            
            logger.info("Mobile template created")
            
        except Exception as e:
            logger.error(f"Error creating mobile template: {str(e)}")
    
    def _create_contract_templates(self):
        """Create smart contract templates"""
        try:
            # WASM contract templates
            wasm_dir = self.contract_templates / "wasm"
            wasm_dir.mkdir(exist_ok=True)
            
            # Simple counter contract
            counter_contract = '''// Simple Counter Contract for CosmWasm
#[cfg(not(feature = "library"))]
use cosmwasm_std::entry_point;
use cosmwasm_std::{Binary, Deps, DepsMut, Env, MessageInfo, Response, StdError, StdResult};
use cw2::set_contract_version;

use crate::msg::{ExecuteMsg, InstantiateMsg, QueryMsg, CountResponse};
use crate::state::State;

const CONTRACT_NAME: &str = "cosmos-builder:counter";
const CONTRACT_VERSION: &str = env!("CARGO_PKG_VERSION");

#[cfg_attr(not(feature = "library"), entry_point)]
pub fn instantiate(
    deps: DepsMut,
    _env: Env,
    info: MessageInfo,
    msg: InstantiateMsg,
) -> StdResult<Response> {
    let state = State {
        count: msg.count,
        owner: info.sender,
    };
    set_contract_version(deps.storage, CONTRACT_NAME, CONTRACT_VERSION)?;
    state.save(deps.storage)?;
    Ok(Response::new()
        .add_attribute("method", "instantiate")
        .add_attribute("owner", info.sender)
        .add_attribute("count", msg.count.to_string()))
}

#[cfg_attr(not(feature = "library"), entry_point)]
pub fn execute(
    deps: DepsMut,
    _env: Env,
    info: MessageInfo,
    msg: ExecuteMsg,
) -> StdResult<Response> {
    match msg {
        ExecuteMsg::Increment {} => try_increment(deps, info),
        ExecuteMsg::Reset { count } => try_reset(deps, info, count),
    }
}

pub fn try_increment(deps: DepsMut, info: MessageInfo) -> StdResult<Response> {
    let state = State::load(deps.storage)?;
    if info.sender != state.owner {
        return Err(StdError::generic_err("Unauthorized"));
    }
    state.count += 1;
    state.save(deps.storage)?;
    Ok(Response::new()
        .add_attribute("method", "increment")
        .add_attribute("count", state.count.to_string()))
}

pub fn try_reset(deps: DepsMut, info: MessageInfo, count: u64) -> StdResult<Response> {
    let state = State::load(deps.storage)?;
    if info.sender != state.owner {
        return Err(StdError::generic_err("Unauthorized"));
    }
    state.count = count;
    state.save(deps.storage)?;
    Ok(Response::new()
        .add_attribute("method", "reset")
        .add_attribute("count", count.to_string()))
}

#[cfg_attr(not(feature = "library"), entry_point)]
pub fn query(deps: Deps, _env: Env, msg: QueryMsg) -> StdResult<Binary> {
    match msg {
        QueryMsg::GetCount {} => try_get_count(deps),
    }
}

pub fn try_get_count(deps: Deps) -> StdResult<Binary> {
    let state = State::load(deps.storage)?;
    let resp = CountResponse { count: state.count };
    to_binary(&resp)
}

#[cfg(test)]
mod tests {
    use super::*;
    use cosmwasm_std::testing::{mock_dependencies, mock_env, mock_info};
    use cosmwasm_std::{coins, from_binary};

    #[test]
    fn proper_initialization() {
        let mut deps = mock_dependencies(&[]);
        let info = mock_info("creator", &coins(1000, "earth"));
        let msg = InstantiateMsg { count: 17 };
        let res = instantiate(deps.as_mut(), mock_env(), info, msg).unwrap();
        assert_eq!(0, res.messages.len());
        let res = query(deps.as_ref(), mock_env(), QueryMsg::GetCount {}).unwrap();
        let value: CountResponse = from_binary(&res).unwrap();
        assert_eq!(17, value.count);
    }

    #[test]
    fn increment() {
        let mut deps = mock_dependencies(&coins(2, "token"));
        let info = mock_info("creator", &coins(2, "token"));
        let msg = InstantiateMsg { count: 0 };
        let _res = instantiate(deps.as_mut(), mock_env(), info, msg).unwrap();

        let info = mock_info("anyone", &coins(2, "token"));
        let msg = ExecuteMsg::Increment {};
        let _res = execute(deps.as_mut(), mock_env(), info, msg).unwrap();

        let res = query(deps.as_ref(), mock_env(), QueryMsg::GetCount {}).unwrap();
        let value: CountResponse = from_binary(&res).unwrap();
        assert_eq!(1, value.count);
    }
}
'''
            
            # Contract Cargo.toml
            cargo_toml = '''[package]
name = "counter"
version = "0.1.0"
edition = "2021"
description = "A simple counter contract for CosmWasm"

[lib]
crate-type = ["cdylib", "rlib"]
edition = "2021"

[dependencies]
cosmwasm-std = "1.3"
cw-storage-plus = "1.0"
cw2 = "1.0"
serde = { version = "1.0", features = ["derive"] }
thiserror = "1.0"

[dev-dependencies]
cosmwasm-schema = "1.3"
'''
            
            # Save WASM contract files
            self._save_template_file(wasm_dir / "Cargo.toml", cargo_toml)
            self._save_template_file(wasm_dir / "src" / "contract.rs", counter_contract)
            
            # EVM contract templates (Solidity)
            evm_dir = self.contract_templates / "evm"
            evm_dir.mkdir(exist_ok=True)
            
            # Simple ERC20 contract
            erc20_contract = '''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title Token Contract
 * @dev ERC20 token implementation for {chain_name}
 */
contract Token is ERC20, Ownable {
    /**
     * @dev Constructor that mints initial supply to msg.sender
     */
    constructor(
        string memory name,
        string memory symbol,
        uint256 initialSupply
    ) ERC20(name, symbol) {
        _mint(msg.sender, initialSupply * (10**decimals()));
    }

    /**
     * @dev Mint tokens to an address
     */
    function mint(address to, uint256 amount) external onlyOwner {
        _mint(to, amount);
    }

    /**
     * @dev Burn tokens from msg.sender
     */
    function burn(uint256 amount) external {
        _burn(msg.sender, amount);
    }

    /**
     * @dev Transfer tokens to multiple addresses
     */
    function batchTransfer(address[] calldata recipients, uint256[] calldata amounts) external {
        require(recipients.length == amounts.length, "Length mismatch");
        
        for (uint256 i = 0; i < recipients.length; i++) {
            transfer(recipients[i], amounts[i]);
        }
    }
}
'''
            
            self._save_template_file(evm_dir / "Token.sol", erc20_contract)
            
            # Hardhat configuration
            hardhat_config = '''require("@nomicfoundation/hardhat-toolbox");

module.exports = {
  solidity: {
    version: "0.8.19",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200
      }
    }
  },
  networks: {
    hardhat: {},
    localhost: {
      url: "http://127.0.0.1:8545"
    },
    testnet: {
      url: "https://rpc.testnet.cosmosbuilder.com",
      chainId: 9000,
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : []
    }
  },
  gasReporter: {
    enabled: process.env.REPORT_GAS !== undefined,
    currency: "USD"
  },
  etherscan: {
    apiKey: process.env.ETHERSCAN_API_KEY
  }
};
'''
            
            self._save_template_file(evm_dir / "hardhat.config.js", hardhat_config)
            
            logger.info("Contract templates created")
            
        except Exception as e:
            logger.error(f"Error creating contract templates: {str(e)}")
    
    def generate_javascript_sdk(self, sdk_config: SDKConfig, output_path: str) -> bool:
        """Generate JavaScript/TypeScript SDK"""
        try:
            self.sdk_config = sdk_config  # Store for template generation
            
            output_dir = Path(output_path)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy template files
            shutil.copytree(self.java_script_template, output_dir, dirs_exist_ok=True)
            
            # Update package.json with chain-specific details
            self._update_javascript_package_json(output_dir, sdk_config)
            
            # Generate Protobuf types
            self._generate_protobuf_types(output_dir, sdk_config)
            
            # Generate query methods
            self._generate_query_methods(output_dir, sdk_config)
            
            logger.info(f"JavaScript SDK generated at {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating JavaScript SDK: {str(e)}")
            return False
    
    def generate_python_sdk(self, sdk_config: SDKConfig, output_path: str) -> bool:
        """Generate Python SDK"""
        try:
            self.sdk_config = sdk_config
            
            output_dir = Path(output_path)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy template files
            shutil.copytree(self.python_template, output_dir, dirs_exist_ok=True)
            
            # Update setup.py with chain details
            self._update_python_setup_py(output_dir, sdk_config)
            
            logger.info(f"Python SDK generated at {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating Python SDK: {str(e)}")
            return False
    
    def generate_go_sdk(self, sdk_config: SDKConfig, output_path: str) -> bool:
        """Generate Go SDK"""
        try:
            self.sdk_config = sdk_config
            
            output_dir = Path(output_path)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy template files
            shutil.copytree(self.go_template, output_dir, dirs_exist_ok=True)
            
            # Update go.mod
            self._update_go_mod(output_dir, sdk_config)
            
            logger.info(f"Go SDK generated at {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating Go SDK: {str(e)}")
            return False
    
    def generate_mobile_sdk(self, sdk_config: SDKConfig, output_path: str) -> bool:
        """Generate Mobile SDK (Swift & Kotlin)"""
        try:
            self.sdk_config = sdk_config
            
            output_dir = Path(output_path)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy template files
            shutil.copytree(self.mobile_template, output_dir, dirs_exist_ok=True)
            
            logger.info(f"Mobile SDK generated at {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating Mobile SDK: {str(e)}")
            return False
    
    def setup_development_environment(self, chain_config: Dict[str, Any], output_path: str) -> bool:
        """Setup complete development environment"""
        try:
            output_dir = Path(output_path)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Create directory structure
            dirs = [
                output_dir / "contracts" / "wasm",
                output_dir / "contracts" / "solidity",
                output_dir / "scripts",
                output_dir / "tests",
                output_dir / "docs",
                output_dir / "examples"
            ]
            
            for dir_path in dirs:
                dir_path.mkdir(parents=True, exist_ok=True)
            
            # Setup WASM development
            self._setup_wasm_development(output_dir, chain_config)
            
            # Setup EVM development
            self._setup_evm_development(output_dir, chain_config)
            
            # Setup deployment scripts
            self._setup_deployment_scripts(output_dir, chain_config)
            
            # Create documentation
            self._create_dev_documentation(output_dir, chain_config)
            
            logger.info(f"Development environment setup complete at {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up development environment: {str(e)}")
            return False
    
    def _update_javascript_package_json(self, output_dir: Path, sdk_config: SDKConfig):
        """Update JavaScript package.json"""
        try:
            package_json_path = output_dir / "package.json"
            with open(package_json_path, 'r') as f:
                package_json = json.load(f)
            
            # Update package name and description
            package_json["name"] = f"@{sdk_config.chain_id.replace('-', '')}-sdk"
            package_json["description"] = f"{sdk_config.chain_name} JavaScript SDK"
            
            # Update dependencies based on chain features
            dependencies = package_json["dependencies"]
            if "wasm" in sdk_config.features:
                dependencies["@cosmwasm/cosmwasm"] = "^1.3.0"
            if "nft" in sdk_config.features:
                dependencies["@cosmjs/stargate"] = "^0.32.0"
            
            # Save updated package.json
            with open(package_json_path, 'w') as f:
                json.dump(package_json, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error updating JavaScript package.json: {str(e)}")
    
    def _generate_protobuf_types(self, output_dir: Path, sdk_config: SDKConfig):
        """Generate TypeScript types from protobuf"""
        try:
            types_dir = output_dir / "src" / "types"
            types_dir.mkdir(exist_ok=True)
            
            # Generate basic types
            types_content = f'''// Auto-generated types for {sdk_config.chain_name}

export interface AccountData {{
  address: string;
  pubkey: Uint8Array;
  accountNumber: number;
  sequence: number;
}}

export interface FeeData {{
  amount: number;
  denom: string;
  gas: number;
}}

export interface ChainConfig {{
  chainId: string;
  chainName: string;
  rpcUrl: string;
  restUrl: string;
  addressPrefix: string;
  denom: string;
  decimals: number;
}}

export const {sdk_config.chain_id.replace('-', '').title()}Config: ChainConfig = {{
  chainId: "{sdk_config.chain_id}",
  chainName: "{sdk_config.chain_name}",
  rpcUrl: "{sdk_config.rpc_endpoint}",
  restUrl: "{sdk_config.rest_endpoint}",
  addressPrefix: "{sdk_config.chain_address_prefix}",
  denom: "{sdk_config.denoms[0]}",
  decimals: 6
}};
'''
            
            self._save_template_file(types_dir / "types.ts", types_content)
            
        except Exception as e:
            logger.error(f"Error generating protobuf types: {str(e)}")
    
    def _generate_query_methods(self, output_dir: Path, sdk_config: SDKConfig):
        """Generate query methods"""
        try:
            queries_content = f'''// Query methods for {sdk_config.chain_name}

import {{ StdClient, ClientFactory }} from "@cosmjs/cosmwasm-stargate";
import {{ QueryClient, setupBankQueryExtension }} from "@cosmjs/stargate";
import {{ QueryDelegatorDelegationsRequest, QueryDelegatorUnbondingDelegationsRequest }} from "cosmjs-types/cosmos/staking/v1beta1/query";
import {{ QueryProposalsRequest, QueryVotesRequest }} from "cosmjs-types/cosmos/gov/v1beta1/query";

export class {sdk_config.chain_id.replace('-', '').title()}QueryClient {{
  private client: QueryClient;
  private rpc: string;

  constructor(rpc: string) {{
    this.rpc = rpc;
    this.client = QueryClient.withExtensions(
      this.rpc,
      setupBankQueryExtension
    );
  }}

  // Bank module queries
  async getBalance(address: string, denom?: string): Promise<any> {{
    return this.client.bank.balance(address, denom);
  }}

  async getTotalSupply(): Promise<any> {{
    return this.client.bank.totalSupply();
  }}

  async getSupplyByDenom(denom: string): Promise<any> {{
    return this.client.bank.supplyOf(denom);
  }}

  // Staking module queries
  async getValidators(status?: string): Promise<any> {{
    return this.client.staking.validators(status);
  }}

  async getDelegatorDelegations(delegator: string): Promise<any> {{
    const request = QueryDelegatorDelegationsRequest.fromJSON({{
      delegatorAddress: delegator
    }});
    return this.client.staking.delegatorDelegations(request);
  }}

  async getUnbondingDelegations(delegator: string): Promise<any> {{
    const request = QueryDelegatorUnbondingDelegationsRequest.fromJSON({{
      delegatorAddress: delegator
    }});
    return this.client.staking.delegatorUnbondingDelegations(request);
  }}

  // Governance module queries
  async getProposals(proposalStatus?: number): Promise<any> {{
    const request = QueryProposalsRequest.fromJSON({{
      proposalStatus
    }});
    return this.client.gov.proposals(request);
  }}

  async getProposalVotes(proposalId: string): Promise<any> {{
    const request = QueryVotesRequest.fromJSON({{
      proposalId
    }});
    return this.client.gov.proposalVotes(request);
  }}
}}
'''
            
            queries_dir = output_dir / "src" / "queries"
            queries_dir.mkdir(exist_ok=True)
            self._save_template_file(queries_dir / "queries.ts", queries_content)
            
        except Exception as e:
            logger.error(f"Error generating query methods: {str(e)}")
    
    def _setup_wasm_development(self, output_dir: Path, chain_config: Dict[str, Any]):
        """Setup WASM contract development"""
        try:
            # Setup Cargo.toml for WASM contracts
            cargo_toml = f'''[package]
name = "{chain_config.get("chain_id", "my-chain")}-contracts"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["cdylib", "rlib"]

[dependencies]
cosmwasm-std = "1.3"
cw-storage-plus = "1.0"
cw2 = "1.0"
serde = {{ version = "1.0", features = ["derive"] }}
thiserror = "1.0"

[dev-dependencies]
cosmwasm-schema = "1.3"
'''
            
            self._save_template_file(output_dir / "contracts" / "Cargo.toml", cargo_toml)
            
            # Setup contract template
            contract_src_dir = output_dir / "contracts" / "src"
            contract_src_dir.mkdir(exist_ok=True)
            
            contract_template = '''use cosmwasm_std::{entry_point, Binary, Deps, DepsMut, Env, MessageInfo, Response, StdResult};
use cw2::set_contract_version;

#[cfg(test)]
mod tests;

const CONTRACT_NAME: &str = "cosmos-builder:contract";
const CONTRACT_VERSION: &str = env!("CARGO_PKG_VERSION");

#[entry_point]
pub fn instantiate(
    deps: DepsMut,
    _env: Env,
    _info: MessageInfo,
    msg: InstantiateMsg,
) -> StdResult<Response> {
    set_contract_version(deps.storage, CONTRACT_NAME, CONTRACT_VERSION)?;
    // TODO: Implement initialization logic
    Ok(Response::new().add_attribute("method", "instantiate"))
}

#[entry_point]
pub fn execute(
    deps: DepsMut,
    _env: Env,
    _info: MessageInfo,
    msg: ExecuteMsg,
) -> StdResult<Response> {
    match msg {
        // TODO: Implement execution logic
        _ => Ok(Response::new().add_attribute("method", "execute")),
    }
}

#[entry_point]
pub fn query(_deps: Deps, _env: Env, msg: QueryMsg) -> StdResult<Binary> {
    match msg {
        // TODO: Implement query logic
        _ => Ok(Binary::new()),
    }
}

#[derive(serde::Serialize, serde::Deserialize, Clone, Debug, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum InstantiateMsg {}

#[derive(serde::Serialize, serde::Deserialize, Clone, Debug, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ExecuteMsg {}

#[derive(serde::Serialize, serde::Deserialize, Clone, Debug, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum QueryMsg {}
'''
            
            self._save_template_file(contract_src_dir / "lib.rs", contract_template)
            
        except Exception as e:
            logger.error(f"Error setting up WASM development: {str(e)}")
    
    def _setup_evm_development(self, output_dir: Path, chain_config: Dict[str, Any]):
        """Setup EVM contract development"""
        try:
            # Setup Hardhat configuration
            hardhat_config = f'''require("@nomicfoundation/hardhat-toolbox");

module.exports = {{
  solidity: {{
    version: "0.8.19",
    settings: {{
      optimizer: {{
        enabled: true,
        runs: 200
      }}
    }}
  }},
  networks: {{
    hardhat: {{}},
    localhost: {{
      url: "http://127.0.0.1:8545"
    }},
    {chain_config.get("chain_id", "my-chain")}: {{
      url: "https://rpc.{chain_config.get("chain_id", "my-chain")}.cosmosbuilder.com",
      chainId: {chain_config.get("evm_chain_id", 9000)},
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : []
    }}
  }},
  gasReporter: {{
    enabled: process.env.REPORT_GAS !== undefined,
    currency: "USD"
  }}
}};
'''
            
            self._save_template_file(output_dir / "contracts" / "hardhat.config.js", hardhat_config)
            
            # Setup package.json for EVM development
            evm_package_json = {
                "name": f"{chain_config.get('chain_id', 'my-chain')}-evm-contracts",
                "version": "1.0.0",
                "scripts": {
                    "build": "hardhat compile",
                    "test": "hardhat test",
                    "deploy": "hardhat run scripts/deploy.js --network localhost",
                    "deploy:testnet": f"hardhat run scripts/deploy.js --network {chain_config.get('chain_id', 'my-chain')}",
                    "lint": "eslint . --ext .js",
                    "format": "prettier --write ."
                },
                "devDependencies": {
                    "@nomicfoundation/hardhat-toolbox": "^3.0.0",
                    "@openzeppelin/contracts": "^4.9.0",
                    "hardhat": "^2.17.0",
                    "eslint": "^8.0.0",
                    "prettier": "^3.0.0"
                }
            }
            
            self._save_template_file(output_dir / "contracts" / "package.json", json.dumps(evm_package_json, indent=2))
            
        except Exception as e:
            logger.error(f"Error setting up EVM development: {str(e)}")
    
    def _setup_deployment_scripts(self, output_dir: Path, chain_config: Dict[str, Any]):
        """Setup deployment scripts"""
        try:
            # WASM deployment script
            wasm_deploy_script = f'''const {{ deploy }} = require("cosmwasm-uploader");

async function main() {{
  // Deploy WASM contracts to {chain_config.get("chain_id", "my-chain")}
  const result = await deploy({{
    contractDir: "./src/contracts",
    contractName: "my-contract",
    network: "{chain_config.get("rpc_endpoint", "http://localhost:26657")}",
    codeId: undefined,
    instantiateMsg: {{}}
  }});
  
  console.log("Contract deployed:", result);
}}

main().catch((error) => {{
  console.error(error);
  process.exitCode = 1;
}});
'''
            
            scripts_dir = output_dir / "scripts"
            self._save_template_file(scripts_dir / "deploy-wasm.js", wasm_deploy_script)
            
            # EVM deployment script
            evm_deploy_script = f'''const hre = require("hardhat");

async function main() {{
  const [deployer] = await hre.ethers.getSigners();
  console.log("Deploying with account:", deployer.address);
  console.log("Account balance:", hre.ethers.utils.formatEther(await deployer.getBalance()));
  
  const Contract = await hre.ethers.getContractFactory("Token");
  const contract = await Contract.deploy("MyToken", "MTK", hre.ethers.utils.parseEther("1000000"));
  
  await contract.deployed();
  console.log("Contract deployed to:", contract.address);
}}

main().catch((error) => {{
  console.error(error);
  process.exitCode = 1;
}});
'''
            
            self._save_template_file(scripts_dir / "deploy-evm.js", evm_deploy_script)
            
        except Exception as e:
            logger.error(f"Error setting up deployment scripts: {str(e)}")
    
    def _create_dev_documentation(self, output_dir: Path, chain_config: Dict[str, Any]):
        """Create development documentation"""
        try:
            readme_content = f'''# {chain_config.get("chain_name", "My Chain")} Development Guide

## Quick Start

This development environment includes all necessary tools for building on {chain_config.get("chain_name", "My Chain")}.

### Prerequisites

- Node.js 18+ and npm
- Rust and wasm-pack
- Docker (for local development)
- {chain_config.get("chain_name", "My Chain")} CLI tools

### Project Structure

```
{output_dir.name}/
├── contracts/              # Smart contracts (WASM and EVM)
├── scripts/               # Deployment scripts
├── tests/                 # Test suites
├── docs/                  # Documentation
└── examples/              # Usage examples
```

### WASM Contracts

WASM contracts use CosmWasm framework:

```bash
cd contracts
wasm-pack build --target web
```

### EVM Contracts

EVM contracts use Hardhat framework:

```bash
cd contracts
npm install
npm run build
npm run test
```

### Deployment

- **WASM**: `npm run deploy-wasm`
- **EVM**: `npm run deploy-evm`

### Testing

Run all tests:
```bash
npm run test
```

## SDK Usage

### JavaScript

```javascript
import {{ {chain_config.get("chain_id", "my-chain").replace('-', '').title()}Client }} from '@{chain_config.get("chain_id", "my-chain").replace('-', '')}-sdk';

const client = new {chain_config.get("chain_id", "my-chain").replace('-', '').title()}Client('https://rpc.{chain_config.get("chain_id", "my-chain")}.cosmosbuilder.com');
const balance = await client.getBalance('cosmos1...');
```

### Python

```python
from cosmosbuilder_{chain_config.get("chain_id", "my-chain").replace('-', '_')} import {chain_config.get("chain_id", "my-chain").replace('-', '').title()}Client

client = {chain_config.get("chain_id", "my-chain").replace('-', '').title()}Client('https://api.{chain_config.get("chain_id", "my-chain")}.cosmosbuilder.com')
balance = client.get_balance('cosmos1...')
```

## Development Resources

- [CosmWasm Documentation](https://docs.cosmwasm.com/)
- [Solidity Documentation](https://docs.soliditylang.org/)
- [{chain_config.get("chain_name", "My Chain")} Explorer](https://explorer.{chain_config.get("chain_id", "my-chain")}.cosmosbuilder.com)
- [Faucet](https://faucet.{chain_config.get("chain_id", "my-chain")}.cosmosbuilder.com)
'''
            
            self._save_template_file(output_dir / "README.md", readme_content)
            
        except Exception as e:
            logger.error(f"Error creating dev documentation: {str(e)}")
    
    def _save_template_file(self, file_path: Path, content: str):
        """Save template file"""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w') as f:
                f.write(content)
        except Exception as e:
            logger.error(f"Error saving template file {file_path}: {str(e)}")
    
    # Template content generation methods
    def _get_javascript_sdk_main(self) -> str:
        return '''import { SigningStargateClient, StargateClient } from "@cosmjs/stargate";
import { DirectSecp256k1HdWallet } from "@cosmjs/proto-signing";
import { Bech32Address } from "@cosmjs/cosmwasm-stargate";

export class CosmosBuilderSDK {
  private client: SigningStargateClient;
  private addressPrefix: string;

  constructor(rpcEndpoint: string, privateKey?: string, addressPrefix = "cosmos") {
    this.addressPrefix = addressPrefix;
  }

  static async connect(rpcEndpoint: string, privateKey?: string, addressPrefix = "cosmos") {
    let client: SigningStargateClient | StargateClient;
    
    if (privateKey) {
      const wallet = await DirectSecp256k1HdWallet.fromPrivateKey(
        Buffer.from(privateKey, "hex"),
        { prefix: addressPrefix }
      );
      client = await SigningStargateClient.connectWithWallet(rpcEndpoint, wallet);
    } else {
      client = await StargateClient.create(rpcEndpoint);
    }
    
    return new CosmosBuilderSDK(rpcEndpoint, privateKey, addressPrefix);
  }

  async getAccount(address: string) {
    return await this.client.getAccount(address);
  }

  async getBalance(address: string, denom?: string) {
    return await this.client.getBalance(address, denom);
  }

  async getSequence(address: string) {
    const account = await this.client.getAccount(address);
    return account?.sequence || 0;
  }

  async sendTokens(fromAddress: string, toAddress: string, amount, fee, memo = "") {
    return await this.client.sendTokens(fromAddress, toAddress, amount, fee, memo);
  }

  async delegateTokens(delegatorAddress: string, validatorAddress: string, amount, fee) {
    return await this.client.delegateTokens(delegatorAddress, validatorAddress, amount, fee);
  }

  async undelegateTokens(delegatorAddress: string, validatorAddress: string, amount, fee) {
    return await this.client.undelegateTokens(delegatorAddress, validatorAddress, amount, fee);
  }

  async vote(proposalId: string, voter: string, option: number, fee) {
    return await this.client.vote(proposalId, voter, option, fee);
  }
}

export default CosmosBuilderSDK;
'''
    
    def _get_javascript_account_utils(self) -> str:
        return '''import { Bech32Address } from "@cosmjs/cosmwasm-stargate";
import { DirectSecp256k1HdWallet } from "@cosmjs/proto-signing";

export async function generateWallet(mnemonic: string, addressPrefix = "cosmos") {
  return await DirectSecp256k1HdWallet.fromMnemonic(mnemonic, { prefix: addressPrefix });
}

export async function getAddressFromMnemonic(mnemonic: string, addressPrefix = "cosmos") {
  const wallet = await generateWallet(mnemonic, addressPrefix);
  const accounts = await wallet.getAccounts();
  return accounts[0].address;
}

export function validateAddress(address: string, addressPrefix = "cosmos"): boolean {
  try {
    Bech32Address.fromBech32(address);
    return address.startsWith(addressPrefix);
  } catch {
    return false;
  }
}

export function convertToBech32(address: string, addressPrefix = "cosmos"): string {
  try {
    return Bech32Address.fromBech32(address).toBech32(addressPrefix);
  } catch (error) {
    throw new Error(`Invalid address: ${address}`);
  }
}

export function convertFromBech32(address: string): string {
  try {
    const addr = Bech32Address.fromBech32(address);
    return addr.data;
  } catch (error) {
    throw new Error(`Invalid Bech32 address: ${address}`);
  }
}
'''
    
    def _get_javascript_tx_utils(self) -> str:
        return '''import { Coin } from "@cosmjs/stargate";

export function createCoins(amounts: { amount: string; denom: string }[]): Coin[] {
  return amounts.map(({ amount, denom }) => ({
    amount,
    denom
  }));
}

export function createFee(amount: number, denom: string, gas: string = "200000") {
  return {
    amount: [{ amount: amount.toString(), denom }],
    gas
  };
}

export function createSendMessage(fromAddress: string, toAddress: string, amounts: Coin[]) {
  return {
    typeUrl: "/cosmos.bank.v1beta1.MsgSend",
    value: {
      fromAddress,
      toAddress,
      amounts
    }
  };
}

export function createDelegateMessage(delegatorAddress: string, validatorAddress: string, amount: Coin) {
  return {
    typeUrl: "/cosmos.staking.v1beta1.MsgDelegate",
    value: {
      delegatorAddress,
      validatorAddress,
      amount
    }
  };
}

export function createVoteMessage(proposalId: string, voter: string, option: number) {
  return {
    typeUrl: "/cosmos.gov.v1beta1.MsgVote",
    value: {
      proposalId,
      voter,
      option
    }
  };
}

export function estimateFee(tx: any[], gasLimit: string = "200000") {
  // Simple fee estimation - in practice, use actual gas calculation
  const gasPrice = 0.025; // uatom per gas unit
  const fee = gasLimit * gasPrice;
  return createFee(fee, "uatom", gasLimit);
}
'''
    
    def _get_python_sdk_main(self) -> str:
        return f'''"""
{sdk_config.chain_name} Python SDK
"""

import asyncio
from typing import Dict, List, Optional, Union
from cosmosclient import CosmosClient
from cosmosclient.client import wallet
from cosmosclient.client.lcd import LCDClient
from cosmosclient.client.tendermint import TendermintClient
from cosmospy.cosmos.account import Account
from cosmospy.cosmos.transaction import Transaction

class {sdk_config.chain_id.replace('-', '').title()}Client:
    def __init__(self, rpc_endpoint: str = "{sdk_config.rpc_endpoint}", 
                 lcd_endpoint: str = "{sdk_config.rest_endpoint}",
                 prefix: str = "{sdk_config.chain_address_prefix}"):
        self.rpc = rpc_endpoint
        self.lcd = lcd_endpoint
        self.prefix = prefix
        
        # Initialize clients
        self.tendermint = TendermintClient(self.rpc)
        self.lcd_client = LCDClient(self.lcd)
        self.cosmos_client = CosmosClient(self.lcd, prefix=prefix)
    
    async def get_account(self, address: str) -> Dict:
        """Get account information"""
        account = await self.cosmos_client.get_account(address)
        return account
    
    async def get_balance(self, address: str, denom: str = "{sdk_config.denoms[0]}") -> Dict:
        """Get account balance"""
        balance = await self.cosmos_client.get_balance(address, denom)
        return balance
    
    async def get_sequence(self, address: str) -> int:
        """Get account sequence"""
        account = await self.get_account(address)
        return account.get("sequence", 0)
    
    async def send_tokens(self, from_key: str, to_address: str, 
                         amount: int, denom: str = "{sdk_config.denoms[0]}",
                         fee_amount: int = 2000, gas_limit: int = 80000) -> str:
        """Send tokens"""
        account = await self.get_account(to_address)
        if not account:
            raise ValueError("Account not found")
        
        # Create transaction
        tx = Transaction()
        tx = tx.with_messages(
            self.cosmos_client.message.msg_send(
                from_key=from_key,
                to_address=to_address,
                amount=[
                    dict(
                        amount=str(amount),
                        denom=denom,
                    )
                ],
            )
        )
        
        # Calculate fees
        fee = dict(amount=[dict(amount=str(fee_amount), denom=denom)], gas_limit=str(gas_limit))
        tx = tx.with_fee(fee)
        tx = tx.with_memo("")
        
        # Get sequence and account number
        account = await self.get_account(from_key)
        tx = tx.with_sequence(account["sequence"])
        tx = tx.with_account_number(account["account_number"])
        
        # Sign and broadcast
        tx = tx.with_chain_id("{sdk_config.chain_id}")
        tx = await tx.try_broadcast()
        
        return tx["txhash"]
    
    async def delegate_tokens(self, delegator_key: str, validator_address: str,
                            amount: int, denom: str = "{sdk_config.denoms[0]}") -> str:
        """Delegate tokens to validator"""
        account = await self.get_account(delegator_key)
        
        tx = Transaction()
        tx = tx.with_messages(
            self.cosmos_client.message.msg_delegate(
                delegator_address=delegator_key,
                validator_address=validator_address,
                amount=[dict(amount=str(amount), denom=denom)]
            )
        )
        
        # Add fee and sign
        fee = dict(amount=[dict(amount="2000", denom=denom)], gas_limit="100000")
        tx = tx.with_fee(fee)
        tx = tx.with_sequence(account["sequence"])
        tx = tx.with_account_number(account["account_number"])
        tx = tx.with_chain_id("{sdk_config.chain_id}")
        tx = await tx.try_broadcast()
        
        return tx["txhash"]
    
    async def vote_proposal(self, proposal_id: str, voter_address: str, 
                          option: int, depositor_key: str) -> str:
        """Vote on governance proposal"""
        account = await self.get_account(depositor_key)
        
        tx = Transaction()
        tx = tx.with_messages(
            self.cosmos_client.message.msg_vote(
                proposal_id=int(proposal_id),
                voter_address=voter_address,
                option=option
            )
        )
        
        # Add fee and sign
        fee = dict(amount=[dict(amount="2000", denom="{sdk_config.denoms[0]}")], gas_limit="80000")
        tx = tx.with_fee(fee)
        tx = tx.with_sequence(account["sequence"])
        tx = tx.with_account_number(account["account_number"])
        tx = tx.with_chain_id("{sdk_config.chain_id}")
        tx = await tx.try_broadcast()
        
        return tx["txhash"]
    
    async def get_proposals(self) -> List[Dict]:
        """Get all proposals"""
        proposals = await self.cosmos_client.gov.proposals()
        return proposals
    
    async def get_validators(self) -> List[Dict]:
        """Get validators"""
        validators = await self.cosmos_client.staking.validators()
        return validators

# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def main():
        client = {sdk_config.chain_id.replace('-', '').title()}Client()
        
        # Get account balance
        balance = await client.get_balance("cosmos1...")
        print(f"Balance: {{balance}}")
        
        # Get proposals
        proposals = await client.get_proposals()
        print(f"Proposals: {{proposals}}")
    
    asyncio.run(main())
'''
    
    def _get_python_client_utils(self) -> str:
        return f'''"""
Client utilities for {sdk_config.chain_name}
"""

import hashlib
import bech32
from typing import Optional
from cosmospy.cosmos.account import Account
from cosmospy.key.key import Key
from cosmospy.util.config import Config

class AccountManager:
    """Account management utilities"""
    
    def __init__(self, prefix: str = "{sdk_config.chain_address_prefix}"):
        self.prefix = prefix
        self.config = Config(prefix=prefix)
    
    def generate_account(self) -> Key:
        """Generate new account"""
        return Key.generate()
    
    def derive_account(self, mnemonic: str, index: int = 0) -> Key:
        """Derive account from mnemonic"""
        return Key.derive(mnemonic, index=index)
    
    def validate_address(self, address: str) -> bool:
        """Validate address format"""
        try:
            bech32.bech32_decode(address)
            return True
        except:
            return False
    
    def convert_address(self, address: str, new_prefix: str = None) -> Optional[str]:
        """Convert address prefix"""
        try:
            decoded = bech32.bech32_decode(address)
            if decoded[0] is None or decoded[1] is None:
                return None
            
            prefix, words = decoded
            new_words = bech32.convertbits(words, 5, 8, False)
            return bech32.bech32_encode(new_prefix or self.prefix, new_words)
        except:
            return None
    
    def get_address_type(self, address: str) -> str:
        """Get address type"""
        if not self.validate_address(address):
            return "invalid"
        
        prefix = address.split("1")[0]
        if prefix == self.prefix:
            return "account"
        
        # Could extend to detect other address types
        return "unknown"

def format_amount(amount: int, denom: str = "{sdk_config.denoms[0]}", decimals: int = 6) -> str:
    """Format amount with proper decimal places"""
    if amount is None:
        return "0"
    
    amount_str = str(amount)
    if len(amount_str) <= decimals:
        return f"0.{amount_str.zfill(decimals)} {{denom}}"
    else:
        integer_part = amount_str[:-decimals]
        decimal_part = amount_str[-decimals:]
        return f"{{integer_part}}.{{decimal_part}} {{denom}}"

def parse_amount(amount_str: str, denom: str = "{sdk_config.denoms[0]}", decimals: int = 6) -> int:
    """Parse amount string to integer"""
    try:
        # Remove denom and whitespace
        amount_str = amount_str.replace(denom, "").strip()
        
        if "." in amount_str:
            integer_part, decimal_part = amount_str.split(".")
            # Pad or truncate decimal part
            decimal_part = decimal_part.ljust(decimals, "0")[:decimals]
            amount_str = integer_part + decimal_part
        else:
            amount_str = amount_str.ljust(decimals + len(amount_str), "0")
        
        return int(amount_str) if amount_str else 0
    except:
        return 0

def calculate_fee(gas_limit: int, gas_price: float = 0.025) -> Dict[str, int]:
    """Calculate transaction fee"""
    fee_amount = int(gas_limit * gas_price)
    return {{
        "amount": [{"amount": str(fee_amount), "denom": "{sdk_config.denoms[0]}"}],
        "gas": str(gas_limit)
    }}
'''
    
    def _get_go_sdk_main(self) -> str:
        return f'''package main

import (
    "context"
    "fmt"
    "log"

    "github.com/cosmos/cosmos-sdk/codec"
    "github.com/cosmos/cosmos-sdk/codec/types"
    "github.com/cosmos/cosmos-sdk/types"
    "github.com/cosmos/cosmos-sdk/types/module"
    "github.com/cosmos/cosmos-sdk/x/bank"
    "github.com/cosmos/cosmos-sdk/x/staking"
    "github.com/tendermint/tendermint/libs/log"
    tmtypes "github.com/tendermint/tendermint/types"
)

type {sdk_config.chain_id.replace('-', '').title()}Client struct {{
    codec  *codec.LegacyAmino
    client tmtypes.HTTPClient
}}

func New{sdk_config.chain_id.replace('-', '').title()}Client(rpcEndpoint string) (*Client, error) {{
    client, err := tmtypes.NewHTTPClient(rpcEndpoint)
    if err != nil {{
        return nil, err
    }}

    codec := codec.NewLegacyAmino()
    
    // Register modules
    bank.RegisterCodec(codec)
    staking.RegisterCodec(codec)

    return &Client{{
        codec: codec,
        client: client,
    }}, nil
}}

func (c *Client) GetAccount(address string) (*types.AccountI, error) {{
    // Implementation for getting account information
    // This is a simplified example - real implementation would make RPC calls
    return nil, nil
}}

func (c *Client) GetBalance(address string, denom string) (*types.Coins, error) {{
    // Implementation for getting balance
    // This is a simplified example - real implementation would make RPC calls
    return types.Coins{{}}, nil
}}

func (c *Client) SendCoins(fromAddress, toAddress string, amount types.Coins, fees types.Coins, memo string) (*types.TxResponse, error) {{
    // Implementation for sending coins
    // This is a simplified example - real implementation would build, sign, and broadcast tx
    return nil, nil
}}

func (c *Client) DelegateTokens(delegatorAddress, validatorAddress string, amount types.Coin, fees types.Coins) (*types.TxResponse, error) {{
    // Implementation for delegating tokens
    return nil, nil
}}

func (c *Client) UndelegateTokens(delegatorAddress, validatorAddress string, amount types.Coin, fees types.Coins) (*types.TxResponse, error) {{
    // Implementation for undelegating tokens
    return nil, nil
}}

func (c *Client) VoteProposal(proposalID uint64, voterAddress string, option types.ProposalVoteOption, fees types.Coins) (*types.TxResponse, error) {{
    // Implementation for voting on proposals
    return nil, nil
}}

func (c *Client) GetProposals() ([]types.Proposal, error) {{
    // Implementation for getting proposals
    return nil, nil
}}

func (c *Client) GetValidators() ([]types.Validator, error) {{
    // Implementation for getting validators
    return nil, nil
}}

func main() {{
    // Example usage
    client, err := New{sdk_config.chain_id.replace('-', '').title()}Client("http://localhost:26657")
    if err != nil {{
        log.Fatal(err)
    }}

    balance, err := client.GetBalance("cosmos1...", "{sdk_config.denoms[0]}")
    if err != nil {{
        log.Fatal(err)
    }}

    fmt.Printf("Balance: %v\\n", balance)
}}
'''
    
    def _get_go_client_utils(self) -> str:
        return f'''package client

import (
    "crypto/sha256"
    "encoding/hex"
    "fmt"
    "strings"

    "github.com/cosmos/cosmos-sdk/crypto/keys/hd"
    "github.com/cosmos/cosmos-sdk/types"
    "github.com/cosmos/go-bip39"
    bech32lib "github.com/cosmos/bsc/go-bech32"
    "github.com/tendermint/tendermint/crypto/secp256k1"
)

const (
    {sdk_config.chain_id.replace('-', '').title()}Bech32Prefix = "{sdk_config.chain_address_prefix}"
)

type KeyManager struct {{
    Prefix string
}}

func NewKeyManager(prefix string) *KeyManager {{
    return &KeyManager{{Prefix: prefix}}
}}

func (km *KeyManager) GenerateMnemonic() (string, error) {{
    entropy, err := bip39.NewEntropy(256)
    if err != nil {{
        return "", err
    }}
    
    mnemonic, err := bip39.NewMnemonic(entropy)
    if err != nil {{
        return "", err
    }}
    
    return mnemonic, nil
}}

func (km *KeyManager) DeriveKeyFromMnemonic(mnemonic string, index uint32) (*types.KeyInfo, error) {{
    seed, err := bip39.NewSeedWithErrorChecking(mnemonic, "")
    if err != nil {{
        return nil, err
    }}
    
    masterKey, ch := hd.ComputeMastersFromSeed(seed)
    if ch != nil {{
        return nil, ch
    }}
    
    // Cosmos default HD path: 44'/118'/0'/0/0
    derivedKey, ch := hd.DeriveKeyForPath(masterKey, fmt.Sprintf("44'/118'/0'/0/%d", index))
    if ch != nil {{
        return nil, ch
    }}
    
    privateKey := secp256k1.PrivKey(derivedKey)
    publicKey := privateKey.PubKey()
    
    // Generate Bech32 address
    address := types.AccAddress(publicKey.Address())
    bech32Addr, err := bech32lib.ConvertAndEncode(km.Prefix, address.Bytes())
    if err != nil {{
        return nil, err
    }}
    
    // Generate Bech32 pubkey
    bech32PubKey, err := bech32lib.ConvertAndEncode(km.Prefix+"pub", publicKey.Bytes())
    if err != nil {nil err
    }}
    
    return &types.KeyInfo{{
        Address:  bech32Addr,
        PubKey:   bech32PubKey,
        Mnemonic: mnemonic,
    }}, nil
}}

func (km *KeyManager) ValidateAddress(address string) bool {{
    _, _, err := bech32lib.ConvertAndDecode(address)
    return err == nil
}}

func (km *KeyManager) ConvertAddressPrefix(address string, newPrefix string) (string, error) {{
    _, data, err := bech32lib.ConvertAndDecode(address)
    if err != nil {{
        return "", err
    }}
    
    newAddress, err := bech32lib.ConvertAndEncode(newPrefix, data)
    if err != nil {{
        return "", err
    }}
    
    return newAddress, nil
}}

func (km *KeyManager) GetAddressType(address string) string {{
    if !km.ValidateAddress(address) {{
        return "invalid"
    }}
    
    if strings.HasPrefix(address, km.Prefix) {{
        return "account"
    }}
    
    return "unknown"
}}

func (km *KeyManager) GenerateWallet() (*types.KeyInfo, error) {{
    mnemonic, err := km.GenerateMnemonic()
    if err != nil {{
        return nil, err
    }}
    
    return km.DeriveKeyFromMnemonic(mnemonic, 0)
}}

func FormatAmount(amount int64, denom string, decimals int) string {{
    if amount == 0 {{
        return fmt.Sprintf("0.%s", strings.Repeat("0", decimals) + denom)
    }}
    
    amountStr := fmt.Sprintf("%d", amount)
    if len(amountStr) <= decimals {{
        return fmt.Sprintf("0.%s %s", strings.Repeat("0", decimals-len(amountStr)) + amountStr, denom)
    }}
    
    integerPart := amountStr[:len(amountStr)-decimals]
    decimalPart := amountStr[len(amountStr)-decimals:]
    return fmt.Sprintf("%s.%s %s", integerPart, decimalPart, denom)
}}

func ParseAmount(amountStr string, denom string, decimals int) (int64, error) {{
    amountStr = strings.TrimSpace(strings.Replace(amountStr, denom, "", 1))
    
    if strings.Contains(amountStr, ".") {{
        parts := strings.Split(amountStr, ".")
        integerPart := parts[0]
        decimalPart := parts[1]
        
        if len(decimalPart) < decimals {{
            decimalPart = decimalPart + strings.Repeat("0", decimals-len(decimalPart))
        }} else if len(decimalPart) > decimals {{
            decimalPart = decimalPart[:decimals]
        }}
        
        amountStr = integerPart + decimalPart
    }}
    
    if amountStr == "" {{
        return 0, nil
    }}
    
    return fmt.Sscanf(amountStr, "%d")
}}

func CalculateFee(gasLimit int64, gasPrice float64) types.Fees {{
    feeAmount := int64(float64(gasLimit) * gasPrice)
    return types.Fees{{
        Amount: types.Coins{{{{Amount: feeAmount, Denom: "{sdk_config.denoms[0]}"}}}},
        GasLimit: gasLimit,
    }}
}}
'''
    
    def _get_go_config(self) -> str:
        return f'''package client

import "time"

type {sdk_config.chain_id.replace('-', '').title()}Config struct {{
    ChainID       string    `json:"chain_id"`
    ChainName     string    `json:"chain_name"`
    RPCEndpoint   string    `json:"rpc_endpoint"`
    RESTEndpoint  string    `json:"rest_endpoint"`
    AddressPrefix string    `json:"address_prefix"`
    Denom         string    `json:"denom"`
    Decimals      int       `json:"decimals"`
    MinFeeAmount  int64     `json:"min_fee_amount"`
    GasAdjustment float64   `json:"gas_adjustment"`
    Timeout       time.Duration `json:"timeout"`
}}

var DefaultConfig = &{sdk_config.chain_id.replace('-', '').title()}Config{{
    ChainID:       "{sdk_config.chain_id}",
    ChainName:     "{sdk_config.chain_name}",
    RPCEndpoint:   "{sdk_config.rpc_endpoint}",
    RESTEndpoint:  "{sdk_config.rest_endpoint}",
    AddressPrefix: "{sdk_config.chain_address_prefix}",
    Denom:         "{sdk_config.denoms[0]}",
    Decimals:      6,
    MinFeeAmount:  2000,
    GasAdjustment: 1.5,
    Timeout:       30 * time.Second,
}}

func (c *Client) Config() *{sdk_config.chain_id.replace('-', '').title()}Config {{
    return DefaultConfig
}}

func (c *Client) SetConfig(config *{sdk_config.chain_id.replace('-', '').title()}Config) {{
    DefaultConfig = config
}}
'''
    
    def _get_go_queries(self) -> str:
        return f'''package client

import (
    "context"
    "fmt"
    "strconv"
    "strings"

    "github.com/cosmos/cosmos-sdk/types"
    "github.com/tendermint/tendermint/rpc/client"
    tmclient "github.com/tendermint/tendermint/rpc/client"
)

type QueryClient struct {{
    client    client.Client
    codec     *types.LegacyAmino
}}

func NewQueryClient(rpcEndpoint string) (*QueryClient, error) {{
    tmClient, err := tmclient.New(rpcEndpoint)
    if err != nil {{
        return nil, err
    }}

    codec := types.NewLegacyAmino()
    // Register modules here

    return &QueryClient{{
        client: tmClient,
        codec:  codec,
    }}, nil
}}

func (qc *QueryClient) GetAccountBalance(address string, denom string) (types.Coins, error) {{
    // This is a simplified implementation
    // In practice, you'd use the REST API or gRPC for proper queries
    return types.Coins{{}}, nil
}}

func (qc *QueryClient) GetAccountSequence(address string) (uint64, error) {{
    // Get account from ABCI query
    result, err := qc.client.ABCIQuery(context.Background(), 
        "store/account/key", 
        []byte(address))
    if err != nil {{
        return 0, err
    }}

    if len(result.Response.Value) == 0 {{
        return 0, fmt.Errorf("account not found")
    }}

    // Parse account data
    // This is a simplified example
    return 0, nil
}}

func (qc *QueryClient) GetValidators() ([]types.Validator, error) {{
    result, err := qc.client.Validators(context.Background(), nil, nil, nil)
    if err != nil {{
        return nil, err
    }}

    validators := make([]types.Validator, len(result.Validators))
    for i, v := range result.Validators {{
        validators[i] = types.Validator{{
            OperatorAddress: v.Address.String(),
            Commission:      v.Commission.Rate,
            Status:          v.VotingPower > 0,
        }}
    }}

    return validators, nil
}}

func (qc *QueryClient) GetProposals() ([]types.Proposal, error) {{
    // This would query the governance module
    // Simplified implementation
    return []types.Proposal{{}}, nil
}}

func (qc *QueryClient) GetProposalVotes(proposalID uint64) ([]types.Vote, error) {{
    // This would query the governance module for votes
    // Simplified implementation
    return []types.Vote{{}}, nil
}}

func (qc *QueryClient) GetNetworkInfo() (map[string]string, error) {{
    status, err := qc.client.Status(context.Background())
    if err != nil {{
        return nil, err
    }}

    info := map[string]string{{
        "chain_id":        status.NodeInfo.Network,
        "latest_block":    strconv.FormatInt(status.SyncInfo.LatestBlockHeight, 10),
        "latest_app_hash": strings.ToUpper(hex.EncodeToString(status.SyncInfo.LatestAppHash)),
    }}

    return info, nil
}}
'''

# Add remaining methods for Swift, Kotlin, etc.
def _get_python_readme(self) -> str:
        return f'''
# {self.sdk_config.chain_name} Python SDK

## Installation

```bash
pip install cosmosbuilder-{self.sdk_config.chain_id.replace('-', '_')}
```

## Quick Start

```python
from cosmosbuilder_{self.sdk_config.chain_id.replace('-', '_')} import {self.sdk_config.chain_id.replace('-', '').title()}Client

# Initialize client
client = {self.sdk_config.chain_id.replace('-', '').title()}Client()

# Get balance
balance = await client.get_balance("cosmos1...")
print(f"Balance: {{balance}}")

# Send tokens
tx_hash = await client.send_tokens(
    from_key="your_private_key",
    to_address="cosmos1...",
    amount=1000000
)
print(f"Transaction: {{tx_hash}}")
```

## Features

- Full Cosmos SDK integration
- Support for all core modules
- Async/await patterns
- Comprehensive error handling

## Documentation

For complete documentation, visit [docs.cosmosbuilder.com](https://docs.cosmosbuilder.com)

## Contributing

Contributions are welcome! Please read our contributing guidelines.

## License

MIT License
'''

# Example usage and testing
if __name__ == "__main__":
    # Initialize SDK generator
    generator = SDKGenerator()
    
    # Create SDK config
    sdk_config = SDKConfig(
        chain_id="testnet-1",
        chain_name="TestNet",
        chain_address_prefix="cosmos",
        rpc_endpoint="https://rpc.testnet.cosmosbuilder.com",
        rest_endpoint="https://api.testnet.cosmosbuilder.com",
        denoms=["uatom"],
        bech32_hrp="cosmos",
        min_tx_fee=2000,
        gas_adjustment=1.5,
        features=["bank", "staking", "gov", "wasm"]
    )
    
    # Generate SDKs
    output_base = "test_output"
    
    print("Generating JavaScript SDK...")
    generator.generate_javascript_sdk(sdk_config, f"{output_base}/javascript")
    
    print("Generating Python SDK...")
    generator.generate_python_sdk(sdk_config, f"{output_base}/python")
    
    print("Generating Go SDK...")
    generator.generate_go_sdk(sdk_config, f"{output_base}/go")
    
    print("Generating Mobile SDK...")
    generator.generate_mobile_sdk(sdk_config, f"{output_base}/mobile")
    
    # Setup development environment
    print("Setting up development environment...")
    chain_config = {
        "chain_id": "testnet-1",
        "chain_name": "TestNet",
        "rpc_endpoint": "https://rpc.testnet.cosmosbuilder.com",
        "evm_chain_id": 9000
    }
    generator.setup_development_environment(chain_config, f"{output_base}/dev-env")
    
    print("SDK generation complete!")