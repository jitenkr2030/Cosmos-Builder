#!/usr/bin/env python3
"""
CosmosBuilder Blockchain Engine
Core system for generating Cosmos SDK blockchains from user configurations
"""

import os
import json
import yaml
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ChainConfig:
    """Blockchain configuration data structure"""
    chain_name: str = "MyChain"
    chain_id: str = "mychain-1"
    symbol: str = "TOKEN"
    denomination: str = "utoken"
    decimals: int = 6
    initial_supply: int = 1000000000
    description: str = "My custom blockchain"
    
    # Consensus parameters
    consensus_type: str = "PoS"
    min_stake: int = 1000000
    max_validators: int = 100
    unbonding_period: int = 21  # days
    
    # Governance parameters
    voting_period: int = 5  # days
    quorum: float = 33.4
    threshold: float = 50.0
    veto_threshold: float = 33.4
    
    # Inflation model
    inflation_type: str = "Dynamic"
    target_inflation: float = 10.0
    inflation_change_rate: float = 13.0
    target_validator_revenue: float = 25.0
    
    # Distribution percentages
    distribution: Dict[str, float] = None
    
    def __post_init__(self):
        if self.distribution is None:
            self.distribution = {
                "community": 30.0,
                "team": 20.0,
                "treasury": 25.0,
                "validators": 15.0,
                "investors": 10.0
            }

@dataclass
class ModuleConfig:
    """Module configuration"""
    name: str
    enabled: bool = True
    config: Dict[str, Any] = None
    is_premium: bool = False
    
    def __post_init__(self):
        if self.config is None:
            self.config = {}

class CosmosBuilderEngine:
    """Main blockchain generation engine"""
    
    def __init__(self, output_dir: str = "generated_chains"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        # Core modules (required)
        self.core_modules = [
            "auth",
            "bank",
            "staking",
            "slashing", 
            "mint",
            "gov",
            "distribution",
            "params",
            "upgrade",
            "ibc",
            "genutil"
        ]
        
        # Available modules
        self.available_modules = {
            "cosmwasm": {"name": "CosmWasm", "is_premium": True},
            "evm": {"name": "EVM", "is_premium": True},
            "nft": {"name": "NFT Module", "is_premium": False},
            "tokenfactory": {"name": "Token Factory", "is_premium": False},
            "oracle": {"name": "Oracle", "is_premium": True},
            "amm": {"name": "AMM DEX", "is_premium": True},
            "lending": {"name": "Lending Module", "is_premium": True},
            "staking": {"name": "Staking", "is_premium": False},
            "governance": {"name": "Governance", "is_premium": False},
            "ibc_transfer": {"name": "IBC Transfer", "is_premium": False},
            "kyc": {"name": "KYC/AML", "is_premium": True},
            "permissioned": {"name": "Permissioned", "is_premium": True},
        }
    
    def generate_blockchain(self, chain_config: ChainConfig, modules: List[ModuleConfig]) -> str:
        """Generate a complete Cosmos SDK blockchain"""
        chain_id = chain_config.chain_id
        chain_dir = self.output_dir / chain_id
        chain_dir.mkdir(exist_ok=True)
        
        logger.info(f"Generating blockchain: {chain_config.chain_name} ({chain_id})")
        
        try:
            # 1. Copy base Cosmos SDK template
            self._copy_template(chain_dir, chain_config)
            
            # 2. Generate application configuration
            self._generate_app_config(chain_dir, chain_config)
            
            # 3. Generate module configurations
            self._generate_modules(chain_dir, modules)
            
            # 4. Generate genesis file
            self._generate_genesis(chain_dir, chain_config)
            
            # 5. Generate CLI commands
            self._generate_cli(chain_dir, chain_config)
            
            # 6. Generate Docker configuration
            self._generate_docker(chain_dir, chain_config)
            
            # 7. Generate documentation
            self._generate_docs(chain_dir, chain_config, modules)
            
            # 8. Build the blockchain
            self._build_blockchain(chain_dir)
            
            logger.info(f"Blockchain generation complete: {chain_dir}")
            return str(chain_dir)
            
        except Exception as e:
            logger.error(f"Error generating blockchain: {e}")
            raise
    
    def _copy_template(self, chain_dir: Path, config: ChainConfig):
        """Generate blockchain from clean templates"""
        template_dir = Path(__file__).parent / "templates" / "basic"
        
        if not template_dir.exists():
            raise FileNotFoundError(f"Template directory not found: {template_dir}")
        
        # Copy template files and customize them
        template_files = [
            "app/app.go",
            "app/sim_test.go", 
            "Makefile",
            "go.mod",
            "go.sum",
            "proto/buf.yaml",
        ]
        
        for file_path in template_files:
            src = template_dir / file_path
            dst = chain_dir / file_path
            dst.parent.mkdir(parents=True, exist_ok=True)
            
            if src.exists():
                # Copy template file
                shutil.copy2(src, dst)
                logger.info(f"Copied template: {file_path}")
            else:
                logger.warning(f"Template file not found: {file_path}")
        
        # Customize the copied files with chain-specific configuration
        self._customize_template(chain_dir, config)
    
    def _customize_template(self, chain_dir: Path, config: ChainConfig):
        """Customize template files with chain-specific configuration"""
        try:
            # Customize go.mod with chain name
            self._update_go_mod(chain_dir, config)
            
            # Customize app.go with chain parameters
            self._update_app_go(chain_dir, config)
            
            # Update Makefile
            self._update_makefile(chain_dir, config)
            
            logger.info(f"Template customized for chain: {config.chain_name}")
            
        except Exception as e:
            logger.error(f"Error customizing template: {e}")
            raise
    
    def _update_go_mod(self, chain_dir: Path, config: ChainConfig):
        """Update go.mod with chain name"""
        go_mod_path = chain_dir / "go.mod"
        if go_mod_path.exists():
            with open(go_mod_path, 'r') as f:
                content = f.read()
            
            # Update module name to match chain
            module_name = config.chain_name.lower().replace(" ", "")
            content = content.replace("github.com/user/myapp", f"github.com/user/{module_name}")
            
            with open(go_mod_path, 'w') as f:
                f.write(content)
    
    def _update_app_go(self, chain_dir: Path, config: ChainConfig):
        """Update app.go with chain parameters"""
        app_path = chain_dir / "app" / "app.go"
        if app_path.exists():
            with open(app_path, 'r') as f:
                content = f.read()
            
            # Update chain ID and parameters
            content = content.replace("myapp", config.chain_name.lower())
            content = content.replace("mychain-1", config.chain_id)
            content = content.replace("stake", config.denomination)
            
            with open(app_path, 'w') as f:
                f.write(content)
    
    def _update_makefile(self, chain_dir: Path, config: ChainConfig):
        """Update Makefile with chain name"""
        makefile_path = chain_dir / "Makefile"
        if makefile_path.exists():
            with open(makefile_path, 'r') as f:
                content = f.read()
            
            # Update binary name
            binary_name = config.chain_name.lower().replace(" ", "")
            content = content.replace("myapp", binary_name)
            
            with open(makefile_path, 'w') as f:
                f.write(content)
    
    def _generate_app_config(self, chain_dir: Path, config: ChainConfig):
        """Generate application configuration"""
        app_dir = chain_dir / "app"
        
        # Generate app.go
        app_content = self._generate_app_go(config)
        app_file = app_dir / "app.go"
        app_file.write_text(app_content)
        
        # Generate app.toml (application config)
        app_toml = self._generate_app_toml(config)
        config_file = chain_dir / "config" / "app.toml"
        config_file.parent.mkdir(exist_ok=True)
        config_file.write_text(app_toml)
        
        logger.info("Generated application configuration")
    
    def _generate_app_go(self, config: ChainConfig) -> str:
        """Generate application Go file"""
        return f'''package app

import (
    "encoding/json"
    "fmt"
    "os"
    "path/filepath"

    "github.com/cosmos/cosmos-sdk/baseapp"
    "github.com/cosmos/cosmos-sdk/client"
    "github.com/cosmos/cosmos-sdk/client/grpc/tmservice"
    "github.com/cosmos/cosmos-sdk/client/rpc"
    "github.com/cosmos/cosmos-sdk/codec"
    "github.com/cosmos/cosmos-sdk/codec/types"
    "github.com/cosmos/cosmos-sdk/server/api"
    "github.com/cosmos/cosmos-sdk/server/config"
    "github.com/cosmos/cosmos-sdk/simapp"
    "github.com/cosmos/cosmos-sdk/snapshots"
    "github.com/cosmos/cosmos-sdk/store/streaming"
    "github.com/cosmos/cosmos-sdk/testutil/network"
    "github.com/cosmos/cosmos-sdk/types/module"
    "github.com/cosmos/cosmos-sdk/version"
    "github.com/cosmos/cosmos-sdk/x/auth"
    "github.com/cosmos/cosmos-sdk/x/auth/ante"
    authkeeper "github.com/cosmos/cosmos-sdk/x/auth/keeper"
    authmodule "github.com/cosmos/cosmos-sdk/x/auth/module"
    "github.com/cosmos/cosmos-sdk/x/auth/vesting"
    "github.com/cosmos/cosmos-sdk/x/authz"
    "github.com/cosmos/cosmos-sdk/x/bank"
    bankkeeper "github.com/cosmos/cosmos-sdk/x/bank/keeper"
    bankmodule "github.com/cosmos/cosmos-sdk/x/bank/module"
    "github.com/cosmos/cosmos-sdk/x/capability"
    "github.com/cosmos/cosmos-sdk/x/crisis"
    crisiskeeper "github.com/cosmos/cosmos-sdk/x/crisis/keeper"
    crisismodule "github.com/cosmos/cosmos-sdk/x/crisis/module"
    "github.com/cosmos/cosmos-sdk/x/distribution"
    distributionkeeper "github.com/cosmos/cosmos-sdk/x/distribution/keeper"
    distributionmodule "github.com/cosmos/cosmos-sdk/x/distribution/module"
    "github.com/cosmos/cosmos-sdk/x/evidence"
    evidencekeeper "github.com/cosmos/cosmos-sdk/x/evidence/keeper"
    evidencemodule "github.com/cosmos/cosmos-sdk/x/evidence/module"
    "github.com/cosmos/cosmos-sdk/x/feegrant"
    feegrantkeeper "github.com/cosmos/cosmos-sdk/x/feegrant/keeper"
    feegrantmodule "github.com/cosmos/cosmos-sdk/x/feegrant/module"
    "github.com/cosmos/cosmos-sdk/x/genutil"
    genutilmodule "github.com/cosmos/cosmos-sdk/x/genutil/module"
    "github.com/cosmos/cosmos-sdk/x/gov"
    govkeeper "github.com/cosmos/cosmos-sdk/x/gov/keeper"
    govmodule "github.com/cosmos/cosmos-sdk/x/gov/module"
    "github.com/cosmos/cosmos-sdk/x/mint"
    mintkeeper "github.com/cosmos/cosmos-sdk/x/mint/keeper"
    mintmodule "github.com/cosmos/cosmos-sdk/x/mint/module"
    "github.com/cosmos/cosmos-sdk/x/params"
    paramskeeper "github.com/cosmos/cosmos-sdk/x/params/keeper"
    paramsmodule "github.com/cosmos/cosmos-sdk/x/params/module"
    "github.com/cosmos/cosmos-sdk/x/slashing"
    slashingkeeper "github.com/cosmos/cosmos-sdk/x/slashing/keeper"
    slashingmodule "github.com/cosmos/cosmos-sdk/x/slashing/module"
    "github.com/cosmos/cosmos-sdk/x/staking"
    stakingkeeper "github.com/cosmos/cosmos-sdk/x/staking/keeper"
    stakingmodule "github.com/cosmos/cosmos-sdk/x/staking/module"
    "github.com/cosmos/cosmos-sdk/x/upgrade"
    upgradekeeper "github.com/cosmos/cosmos-sdk/x/upgrade/keeper"
    upgrademodule "github.com/cosmos/cosmos-sdk/x/upgrade/module"
    "github.com/cosmos/cosmos-sdk/x/wasm"
    wasmclient "github.com/cosmos/cosmos-sdk/x/wasm/client"
    "github.com/spf13/cast"
    abci "github.com/tendermint/tendermint/abci/types"
    "github.com/tendermint/tendermint/libs/log"
    tmdb "github.com/tendermint/tm-db"
)

const (
    Name = "{config.chain_name}"
    BondDenom = "{config.denomination}"
    ChainID = "{config.chain_id}"
)

var (
    // DefaultNodeHome default home directories for the application daemon
    DefaultNodeHome = os.ExpandEnv("$HOME/.{config.chain_id}")

    // ModuleBasics defines the module BasicConfig is
    // composed of all the modules that need to be included in a cosmos-sdk app.
    ModuleBasics = module.NewBasicManager(
        authmodule.AppModuleBasic{},
        genutilmodule.AppModuleBasic{},
        bankmodule.AppModuleBasic{},
        stakingmodule.AppModuleBasic{},
        mintmodule.AppModuleBasic{},
        distributionmodule.AppModuleBasic{},
        slashingmodule.AppModuleBasic{},
        govmodule.AppModuleBasic{},
        paramsmodule.AppModuleBasic{},
        crisismodule.AppModuleBasic{},
        evidencemodule.AppModuleBasic{},
        feegrantmodule.AppModuleBasic{},
        authzmodule.AppModuleBasic{},
        upgrademodule.AppModuleBasic{},
        vestingmodule.AppModuleBasic{},
    )

    // module account permissions
    maccPerms = map[string][]string{{
        "autModule": nil,
        "bonded_pool": {{"staking", "bond", "unbond", "claim"}},
        "not_bonded_pool": {{"staking", "bond", "unbond", "claim"}},
        "distribution": {{"claim"}},
        "mint": {{"mint", "burn"}},
        "gov": {{"burn"}},
        "treasury": nil,
    }}
)

// App extends an ABCI application, but with most of its parameters exported.
// They are exported for convenience in creating helper functions, as type
// assertions are useful on client app interface type.
type App struct {{
    *baseapp.BaseApp
    legacyAmino       *codec.LegacyAmino
    cdc               *codec.Codec
    interfaceRegistry types.InterfaceRegistry

    // keys to access the multistore
    keys map[string]*types.KVStoreKey

    // keepers
    accountKeeper    authkeeper.AccountKeeper
    bankKeeper       bankkeeper.BaseKeeper
    capabilityKeeper *capabilitykeeper.Keeper
    stakingKeeper    stakingkeeper.Keeper
    mintKeeper       mintkeeper.Keeper
    distributionKeeper distributionkeeper.Keeper
    slashingKeeper   slashingkeeper.Keeper
    govKeeper        govkeeper.Keeper
    crisisKeeper     crisiskeeper.Keeper
    feegrantKeeper   feegrantkeeper.Keeper
    upgradeKeeper    *upgradekeeper.Keeper
    evidenceKeeper   evidencekeeper.Keeper
    authzKeeper      authzkeeper.Keeper
    wasmKeeper       wasm.Keeper

    // modules
    mm *module.Manager

    // module configurator
    configurator module.Configurator
}}

func NewApp(
    logger log.Logger,
    db tmdb.DB,
    traceStore io.Writer,
    loadLatest bool,
    skipUpgradeHeights map[int64]bool,
    homePath string,
    invCheckPeriod uint,
    encodingConfig simapp.EncodingConfig,
    appOpts servertypes.AppOptions,
    wasmDir string,
) *App {{
    appCodec := encodingConfig.Marshaler
    legacyAmino := encodingConfig.Amino
    interfaceRegistry := encodingConfig.InterfaceRegistry

    bApp := baseapp.NewBaseApp(Name, logger, db, encodingConfig.TxConfig.TxDecoder(), baseapp.SetPruning(PruningOptionsNothing))
    bApp.SetCommitMultiStoreTracer(traceStore)
    bApp.SetVersion(version.Version)
    bApp.SetInterfaceRegistry(interfaceRegistry)

    keys := sdk.NewKVStoreKeys(...)
    storeKeys := getStoreKeys()

    app := &App{{
        BaseApp:           bApp,
        legacyAmino:       legacyAmino,
        cdc:               appCodec,
        interfaceRegistry: interfaceRegistry,
        keys:              storeKeys,
    }}

    app.paramsKeeper = initParamsKeeper(appCodec, legacyAmino, keys[types.ModuleName])
    app.capabilityKeeper = capabilitykeeper.NewKeeper(appCodec, keys[capabilitytypes.ModuleName], app.memKeys[capabilitytypes.MemStoreKey])
    app.stakingKeeper = stakingkeeper.NewKeeper(appCodec, keys[stakingtypes.StoreKey], app.accountKeeper, app.bankKeeper, app.GetSubspace(stakingtypes.ModuleName))
    app.mintKeeper = mintkeeper.NewKeeper(appCodec, keys[minttypes.StoreKey], app.GetSubspace(minttypes.ModuleName), app.stakingKeeper, app.accountKeeper, app.bankKeeper)
    app.distributionKeeper = distributionkeeper.NewKeeper(appCodec, keys[distributiontypes.StoreKey], app.GetSubspace(distributiontypes.ModuleName), app.accountKeeper, app.bankKeeper, app.stakingKeeper, authtypes.FeeCollectorName, app.ModuleAccountAddrs())
    app.slashingKeeper = slashingkeeper.NewKeeper(appCodec, keys[slashingtypes.StoreKey], app.stakingKeeper, app.GetSubspace(slashingtypes.ModuleName))
    app.crisisKeeper = crisiskeeper.NewKeeper(app.GetSubspace(crisistypes.ModuleName), invCheckPeriod, app.bankKeeper, authtypes.FeeCollectorName)
    app.feegrantKeeper = feegrantkeeper.NewKeeper(appCodec, keys[feegranttypes.StoreKey], app.accountKeeper)
    app.upgradeKeeper = upgradekeeper.NewKeeper(skipUpgradeHeights, keys[upgradetypes.StoreKey], appCodec, homePath)
    app.evidenceKeeper = evidencekeeper.NewKeeper(appCodec, keys[evidencetypes.StoreKey], app.stakingKeeper, app.slashingKeeper)
    
    // WASM module
    wasmDir := filepath.Join(homePath, "wasm")
    var wasmConfig wasm.Config
    app.wasmKeeper = wasm.NewKeeper(
        appCodec,
        keys[wasmtypes.StoreKey],
        app.GetSubspace(wasmtypes.ModuleName),
        app.accountKeeper,
        app.bankKeeper,
        app.stakingKeeper,
        app.distributionKeeper,
        app.govKeeper,
        app.crisisKeeper,
        &app.wasmOpts...,
    )

    app.govKeeper = govkeeper.NewKeeper(
        appCodec,
        keys[govtypes.StoreKey],
        app.GetSubspace(govtypes.ModuleName),
        app.accountKeeper,
        app.bankKeeper,
        app.stakingKeeper,
        govtypes.DefaultConfig(),
    )

    // create evidence Keeper with external ABCI
    app.evidenceKeeper = *evidencekeeper.NewKeeper(
        appCodec,
        keys[evidencetypes.StoreKey],
        app.stakingKeeper,
        app.slashingKeeper,
    )
    
    // create evidence Router and register routes
    var evidenceRouter evidencetypes.Router
    // add routes here
    app.evidenceKeeper = *evidencekeeper.NewKeeper(
        appCodec,
        keys[evidencetypes.StoreKey],
        app.stakingKeeper,
        app.slashingKeeper,
    )

    // register proposal types
    govRouter := govv1beta1.NewRouter()
    govRouter.AddRoute(govtypes.RouterKey, govv1beta1.ProposalHandler).
        AddRoute(params.RouterKey, params.ProposalHandler).
        AddRoute(upgradetypes.RouterKey, upgrade.NewProposalHandler(app.upgradeKeeper)).
        AddRoute(ibcclienttypes.RouterKey, ibcclient.NewClientProposalHandler(app.ibcKeeper.ClientKeeper))

    app.govKeeper = govkeeper.NewKeeper(
        appCodec,
        keys[govtypes.StoreKey],
        app.GetSubspace(govtypes.ModuleName),
        app.accountKeeper,
        app.bankKeeper,
        &app.stakingKeeper,
        govRouter,
    )

    // Create CapabilityKeeper and return if enabled
    app.capabilityKeeper = capabilitykeeper.NewKeeper(appCodec, keys[capabilitytypes.ModuleName], memKeys[capabilitytypes.MemStoreKey])
    app.ScopedIBCKeeper = app.capabilityKeeper.ScopeToModule(ibchost.ModuleName)
    app.ScopedTransferKeeper = app.capabilityKeeper.ScopeToModule(ibctransfertypes.ModuleName)
    app.ScopedWasmKeeper = app.capabilityKeeper.ScopeToModule(wasmtypes.ModuleName)

    // add keepers
    app.accountKeeper = authkeeper.NewAccountKeeper(
        appCodec,
        keys[authtypes.StoreKey],
        app.GetSubspace(authtypes.ModuleName),
        authtypes.ProtoBaseAccount,
        maccPerms,
    )
    app.bankKeeper = bankkeeper.NewBaseKeeper(
        appCodec,
        keys[banktypes.StoreKey],
        app.accountKeeper,
        app.GetSubspace(banktypes.ModuleName),
        app.ModuleAccountAddrs(),
    )
    
    // register the staking module's message router and the staking module's query router
    // and the evidence module's query router
    stakingModule := stakingmodule.NewAppModule(appCodec, app.stakingKeeper, app.accountKeeper, app.bankKeeper)

    // Initialize the upgrade module
    app.upgradeKeeper = upgradekeeper.NewKeeper(skipUpgradeHeights, keys[upgradetypes.StoreKey], appCodec, homePath, app.BaseApp)

    // register the staking module's message router and the staking module's query router
    var stakingRouter = stakingtypes.Router()
    stakingRouter.AddRoute(stakingtypes.ModuleName, staking.NewHandler(app.stakingKeeper))
    app.router = app.router.AddRoute(stakingtypes.ModuleName, stakingRouter)

    // Initialize stores
    app.MountKVStores(keys)
    app.MountTransientStores(tKeys)
    app.MountMemoryStores(memKeys)

    // Initialize BaseApp
    app.SetInitChainer(app.InitChainer)
    app.SetBeginBlocker(app.BeginBlocker)

    // set ante handler
    app.anteHandler = ante.NewAnteHandler(
        app.accountKeeper,
        app.bankKeeper,
        ante.DefaultSigVerificationGasConsumer,
        encodingConfig.TxConfig.SignModeHandler(),
    )
    app.SetAnteHandler(app.anteHandler)
    app.SetEndBlocker(app.EndBlocker)

    // Initialize the store updater and the upgrade module's keeper
    app.upgradeKeeper = upgradekeeper.NewKeeper(skipUpgradeHeights, keys[upgradetypes.StoreKey], appCodec, homePath, app.BaseApp)

    // add upgrades here
    app.upgradeKeeper.SetUpgradeHandler(...)
    
    // add the upgrade module's keeper to the router
    app.router.AddRoute(upgradetypes.ModuleName, upgrade.NewProposalsHandler(app.upgradeKeeper))

    // setup the upgrade module
    app.upgradeKeeper.SetUpgradeHandler(
        vName,
        func(ctx sdk.Context, plan upgradetypes.Plan) {{
            // set the governance module's proposal handler
            govRouter := app.govKeeper.GetRouter()
            govRouter.AddRoute(govtypes.RouterKey, govv1beta1.ProposalHandler)

            // perform any module migration
        }},
    )

    // Setup final app state and return
    app.setupUpgradeHandlers()
    app.setupUpgradeStoreLoaders()

    // if loadLatest, load the latest version
    if loadLatest {{
        if err := app.LoadLatestVersion(); err != nil {{
            tmos.Exit(err.Error())
        }}
    }}

    // Create snapshot manager for state sync
    app.SnapshotManager = snapshots.NewSnapshotManager(db, store.NewSnapshotStore(traceStore), encodingConfig.Marshaler, snapshottypes.Version)

    // load state sync if supported
    if manager := app.SnapshotManager; manager != nil {{
        if err := manager.RegisterFlushInterval(snapshottypes.FlushInterval); err != nil {{
            tmos.Exit(fmt.Sprintf("failed to register snapshot flush interval: %v", err))
        }}
    }}

    return app
}}

// Name returns the name of the App
func (app *App) Name() string {{ return app.BaseApp.Name() }}

// BeginBlocker application updates every begin block
func (app *App) BeginBlocker(ctx sdk.Context, req abci.RequestBeginBlock) abci.ResponseBeginBlock {{
    return app.mm.BeginBlock(ctx, req)
}}

// EndBlocker application updates every end block
func (app *App) EndBlocker(ctx sdk.Context, req abci.RequestEndBlock) abci.ResponseEndBlock {{
    return app.mm.EndBlock(ctx, req)
}}

// InitChainer application update at chain initialization
func (app *App) InitChainer(ctx sdk.Context, req abci.RequestInitChain) abci.ResponseInitChain {{
    var genesisState simapp.GenesisState
    if app.cdc.Unmarshal(req.AppStateBytes, &genesisState) != nil {{
        panic("failed to unmarshal genesis state")
    }}

    // Initialize the upgrade module
    app.upgradeKeeper.SetModuleVersionMap(ctx, app.mm.GetVersionMap())

    return app.mm.InitGenesis(ctx, app.cdc, genesisState)
}}

// LoadHeight loads a particular height
func (app *App) LoadHeight(height int64) error {{
    return app.LoadVersion(height)
}}

// ModuleAccountAddrs returns all the app's module account addresses.
func (app *App) ModuleAccountAddrs() map[string]bool {{
    modAccAddrs := make(map[string]bool)
    for acc := range maccPerms {{
        modAccAddrs[authtypes.NewModuleAddress(acc).String()] = true
    }}

    return modAccAddrs
}}

// GetSubspace returns a param subspace for a given module name.
func (app *App) GetSubspace(moduleName string) params.Subspace {{
    return app.paramsKeeper.GetSubspace(moduleName)
}}
'''

    def _generate_app_toml(self, config: ChainConfig) -> str:
        """Generate application configuration file"""
        return f'''# This is a TOML config file.
# For more information, see https://github.com/toml-lang/toml

minimum-gas-prices = "0{config.denomination}"
pruning = "nothing"
pruning-keep-recent = "0"
pruning-keep-every = "0"
pruning-interval = "0"

enable = false
html_laddr = "http://127.0.0.1:8080"
address = "127.0.0.1:6060"
stream-log = true
'''

    def _generate_modules(self, chain_dir: Path, modules: List[ModuleConfig]):
        """Generate module configurations"""
        modules_dir = chain_dir / "x"
        
        for module in modules:
            if not module.enabled:
                continue
                
            module_dir = modules_dir / module.name.lower()
            module_dir.mkdir(exist_ok=True)
            
            if module.name.lower() == "cosmwasm":
                self._generate_cosmwasm_module(module_dir, module)
            elif module.name.lower() == "nft":
                self._generate_nft_module(module_dir, module)
            elif module.name.lower() == "amm":
                self._generate_amm_module(module_dir, module)
            else:
                self._generate_basic_module(module_dir, module)
        
        logger.info("Generated module configurations")
    
    def _generate_cosmwasm_module(self, module_dir: Path, config: ModuleConfig):
        """Generate CosmWasm module"""
        keeper_file = module_dir / "keeper" / "keeper.go"
        keeper_file.parent.mkdir(parents=True, exist_ok=True)
        
        keeper_content = f'''package keeper

import (
    "context"
    "fmt"

    "github.com/CosmWasm/wasmd/x/wasm/keeper"
    wasmtypes "github.com/CosmWasm/wasmd/x/wasm/types"
    "github.com/cosmos/cosmos-sdk/codec"
    "github.com/cosmos/cosmos-sdk/store/prefix"
    sdk "github.com/cosmos/cosmos-sdk/types"
    sdkerrors "github.com/cosmos/cosmos-sdk/types/errors"
    "{config.chain_id}/x/wasm/types"
    paramtypes "github.com/cosmos/cosmos-sdk/x/params/types"
)

type Keeper struct {{
    keeper.Keeper
    accountKeeper wasmtypes.AccountKeeper
    bankKeeper    wasmtypes.BankKeeper
    stakingKeeper wasmtypes.StakingKeeper
    distribution  wasmtypes.DistributionKeeper
    govKeeper     wasmtypes.GovernanceKeeper
    crisisKeeper  wasmtypes.CrisisKeeper
    cdc           codec.Codec
    paramSpace    paramtypes.Subspace
    wasmDir       string
}}

func NewKeeper(
    cdc codec.Codec,
    storeKey sdk.StoreKey,
    paramSpace paramtypes.Subspace,
    accountKeeper wasmtypes.AccountKeeper,
    bankKeeper wasmtypes.BankKeeper,
    stakingKeeper wasmtypes.StakingKeeper,
    distribution wasmtypes.DistributionKeeper,
    govKeeper wasmtypes.GovernanceKeeper,
    crisisKeeper wasmtypes.CrisisKeeper,
    wasmDir string,
    wasmConfig wasmtypes.WasmConfig,
    availableCapabilities string,
    opts ...wasm.KeeperOption,
) Keeper {{
    keeper := wasm.NewKeeper(
        cdc,
        storeKey,
        paramSpace,
        accountKeeper,
        bankKeeper,
        stakingKeeper,
        distribution,
        govKeeper,
        crisisKeeper,
        wasmDir,
        wasmConfig,
        availableCapabilities,
        opts...,
    )
    
    return Keeper{{
        Keeper:         keeper,
        accountKeeper:  accountKeeper,
        bankKeeper:     bankKeeper,
        stakingKeeper:  stakingKeeper,
        distribution:   distribution,
        govKeeper:      govKeeper,
        crisisKeeper:   crisisKeeper,
        cdc:            cdc,
        paramSpace:     paramSpace,
        wasmDir:        wasmDir,
    }}
}}

func (k Keeper) Logger(ctx sdk.Context) wasmtypes.Logger {{
    return ctx.Logger().With("module", "x/wasm-keeper")
}}
'''
        
        keeper_file.write_text(keeper_content)
        
        # Generate types
        types_dir = module_dir / "types"
        types_dir.mkdir(exist_ok=True)
        (types_dir / "expected_keepers.go").write_text('''package types

// Expected interface for account keeper
type AccountKeeper interface {
    GetAccount(ctx sdk.Context, addr sdk.AccAddress) sdk.AccountI
    NewAccountWithAddress(ctx sdk.Context, addr sdk.AccAddress) sdk.AccountI
    NewAccount(ctx sdk.Context, acc sdk.AccountI) sdk.AccountI
    SetAccount(ctx sdk.Context, acc sdk.AccountI)
    IterateAccounts(ctx sdk.Context, process func(sdk.AccountI) bool)
    GetModuleAddress(name string) sdk.AccAddress
    GetModuleAccount(ctx sdk.Context, moduleName string) sdk.ModuleAccountI
}

// Expected interface for bank keeper
type BankKeeper interface {
    GetBalance(ctx sdk.Context, addr sdk.AccAddress, denom string) sdk.Coin
    GetAllBalances(ctx sdk.Context, addr sdk.AccAddress) sdk.Coins
    HasBalance(ctx sdk.Context, addr sdk.AccAddress, amt sdk.Coin) bool
    SendCoins(ctx sdk.Context, fromAddr, toAddr sdk.AccAddress, amt sdk.Coins) error
    SendCoinsFromModuleToAccount(ctx sdk.Context, senderModule string, recipientAddr sdk.AccAddress, amt sdk.Coins) error
    SendCoinsFromModuleToModule(ctx sdk.Context, senderModule, recipientModule string, amt sdk.Coins) error
    SendCoinsFromAccountToModule(ctx sdk.Context, senderAddr sdk.AccAddress, recipientModule string, amt sdk.Coins) error
    GetSupply(ctx sdk.Context, denom string) sdk.Coin
    SetSupply(ctx sdk.Context, coin sdk.Coin)
    MintCoins(ctx sdk.Context, moduleName string, amt sdk.Coins) error
    BurnCoins(ctx sdk.Context, moduleName string, amt sdk.Coins) error
}
''')

    def _generate_nft_module(self, module_dir: Path, config: ModuleConfig):
        """Generate NFT module"""
        keeper_file = module_dir / "keeper" / "keeper.go"
        keeper_file.parent.mkdir(parents=True, exist_ok=True)
        
        keeper_content = f'''package keeper

import (
    "context"
    "fmt"

    "github.com/cosmos/cosmos-sdk/codec"
    sdk "github.com/cosmos/cosmos-sdk/types"
    "{config.chain_id}/x/nft/types"
)

type Keeper struct {{
    cdc codec.Codec
}}

func NewKeeper(cdc codec.Codec) Keeper {{
    return Keeper{{
        cdc: cdc,
    }}
}}

// MintNFT mints an NFT to a recipient
func (k Keeper) MintNFT(
    ctx sdk.Context,
    classId, id, uri, uriHash, data string,
    recipient sdk.AccAddress,
) (types.Class, error) {{
    // Implementation here
    return types.Class{{}}, nil
}}

// TransferNFT transfers an NFT from one account to another
func (k Keeper) TransferNFT(
    ctx sdk.Context,
    classId, id string,
    from, to sdk.AccAddress,
) error {{
    // Implementation here
    return nil
}}

// GetNFT returns an NFT by class and ID
func (k Keeper) GetNFT(
    ctx sdk.Context,
    classId, id string,
) (types.NFT, error) {{
    // Implementation here
    return types.NFT{{}}, nil
}}
'''
        
        keeper_file.write_text(keeper_content)

    def _generate_amm_module(self, module_dir: Path, config: ModuleConfig):
        """Generate AMM DEX module"""
        keeper_file = module_dir / "keeper" / "keeper.go"
        keeper_file.parent.mkdir(parents=True, exist_ok=True)
        
        keeper_content = f'''package keeper

import (
    "context"

    "github.com/cosmos/cosmos-sdk/codec"
    sdk "github.com/cosmos/cosmos-sdk/types"
    "{config.chain_id}/x/amm/types"
)

type Keeper struct {{
    cdc codec.Codec
    bankKeeper types.BankKeeper
}}

func NewKeeper(
    cdc codec.Codec,
    bankKeeper types.BankKeeper,
) Keeper {{
    return Keeper{{
        cdc: cdc,
        bankKeeper: bankKeeper,
    }}
}}

// CreatePool creates a new liquidity pool
func (k Keeper) CreatePool(
    ctx sdk.Context,
    tokenA sdk.Coin,
    tokenB sdk.Coin,
    poolAddress sdk.AccAddress,
) (types.Pool, error) {{
    // Implementation here
    return types.Pool{{}}, nil
}}

// AddLiquidity adds liquidity to an existing pool
func (k Keeper) AddLiquidity(
    ctx sdk.Context,
    poolId string,
    maxTokenA sdk.Coin,
    maxTokenB sdk.Coin,
    minLiquidity sdk.Int,
    sender sdk.AccAddress,
) (sdk.Coin, error) {{
    // Implementation here
    return sdk.Coin{{}}, nil
}}

// Swap performs a token swap
func (k Keeper) Swap(
    ctx sdk.Context,
    poolId string,
    tokenIn sdk.Coin,
    minTokenOut sdk.Coin,
    swapper sdk.AccAddress,
) (sdk.Coin, error) {{
    // Implementation here
    return sdk.Coin{{}}, nil
}}
'''
        
        keeper_file.write_text(keeper_content)

    def _generate_basic_module(self, module_dir: Path, config: ModuleConfig):
        """Generate basic module structure"""
        # Create basic module structure
        for subdir in ['keeper', 'types', 'client']:
            (module_dir / subdir).mkdir(parents=True, exist_ok=True)
        
        # Generate basic keeper
        keeper_file = module_dir / "keeper" / "keeper.go"
        keeper_content = f'''package keeper

import (
    "github.com/cosmos/cosmos-sdk/codec"
    sdk "github.com/cosmos/cosmos-sdk/types"
    "{config.chain_id}/x/{config.name.lower()}/types"
)

type Keeper struct {{
    cdc codec.Codec
}}

func NewKeeper(cdc codec.Codec) Keeper {{
    return Keeper{{
        cdc: cdc,
    }}
}}

func (k Keeper) ExampleFunction(ctx sdk.Context) error {{
    // Implementation here
    return nil
}}
'''
        keeper_file.write_text(keeper_content)

    def _generate_genesis(self, chain_dir: Path, config: ChainConfig):
        """Generate genesis file"""
        genesis_dir = chain_dir / "genesis"
        genesis_dir.mkdir(exist_ok=True)
        
        # Calculate initial distribution
        total_supply = config.initial_supply
        distributions = {}
        
        for category, percentage in config.distribution.items():
            distributions[category] = int(total_supply * percentage / 100)
        
        genesis_content = {
            "genesis_time": datetime.now().isoformat() + "Z",
            "chain_id": config.chain_id,
            "initial_height": "1",
            "consensus_params": {
                "block": {
                    "max_bytes": "22020096",
                    "max_gas": "-1"
                },
                "evidence": {
                    "max_age_num_blocks": "100000",
                    "max_age_duration": "172800000000000",
                    "max_bytes": "1048576"
                },
                "validator": {
                    "pub_key_types": ["ed25519"]
                },
                "version": {
                    "block": "11",
                    "app": "0"
                }
            },
            "app_hash": "",
            "app_state": {
                "auth": {
                    "params": {
                        "max_memo_characters": "256",
                        "tx_sig_limit": "7",
                        "tx_size_cost_per_byte": "10",
                        "sig_verify_cost_ed25519": "590",
                        "sig_verify_cost_secp256k1": "1000"
                    },
                    "accounts": []
                },
                "bank": {
                    "params": {
                        "send_enabled": [],
                        "default_send_enabled": True
                    },
                    "balances": [],
                    "supply": [{
                        "denom": config.denomination,
                        "amount": str(total_supply)
                    }],
                    "denom_metadata": [{
                        "description": f"The native token of {config.chain_name}",
                        "denom_units": [{
                            "denom": config.denomination,
                            "exponent": 0
                        }, {
                            "denom": config.symbol.lower(),
                            "exponent": config.decimals
                        }],
                        "base": config.denomination,
                        "display": config.symbol.lower(),
                        "name": config.chain_name,
                        "symbol": config.symbol
                    }]
                },
                "staking": {
                    "params": {
                        "unbonding_time": f"{config.unbonding_period * 24}h",
                        "max_validators": config.max_validators,
                        "max_entries": 7,
                        "historical_entries": 10000,
                        "bond_denom": config.denomination
                    },
                    "last_total_power": "0",
                    "last_validator_powers": [],
                    "validators": [],
                    "delegations": [],
                    "unbonding_delegations": [],
                    "redelegations": [],
                    "exported": False
                },
                "mint": {
                    "minter": {
                        "inflation": str(config.target_inflation / 100),
                        "annual_provisions": "0.000000000000000000"
                    },
                    "params": {
                        "mint_denom": config.denomination,
                        "inflation_rate_change": str(config.inflation_change_rate / 100),
                        "inflation_max": "0.200000000000000000",
                        "inflation_min": "0.070000000000000000",
                        "goal_bonded": "0.670000000000000000",
                        "blocks_per_year": "6311520"
                    }
                },
                "distribution": {
                    "params": {
                        "community_tax": "0.020000000000000000",
                        "withdraw_addr_enabled": True
                    },
                    "fee_pool": {
                        "community_pool": []
                    },
                    "delayed_fee": [],
                    " proposer_delegations": [],
                    "delayed_proposer_delegations": []
                },
                "slashing": {
                    "params": {
                        "signed_blocks_window": "100",
                        "min_signed_per_window": "0.500000000000000000",
                        "downtime_jail_duration": "600s",
                        "slash_fraction_double_sign": "0.050000000000000000",
                        "slash_fraction_downtime": "0.010000000000000000",
                        "slash_fraction_duplicate_vote": "0.000000000000000000"
                    },
                    "missed_blocks": {},
                    "validator_signing_infos": []
                },
                "gov": {
                    "deposit_params": {
                        "min_deposit": [{
                            "denom": config.denomination,
                            "amount": "10000000"
                        }],
                        "max_deposit_period": f"{config.voting_period * 24}h"
                    },
                    "voting_params": {
                        "voting_period": f"{config.voting_period * 24}h"
                    },
                    "tally_params": {
                        "quorum": f"{config.quorum / 100}",
                        "threshold": f"{config.threshold / 100}",
                        "veto_threshold": f"{config.veto_threshold / 100}"
                    },
                    "deposits": [],
                    "votes": [],
                    "proposals": [],
                    "proposal_deposit_matches": [],
                    "deposit_ids": []
                },
                "crisis": {
                    "constant_fee": {
                        "denom": config.denomination,
                        "amount": "1000"
                    }
                },
                "genutil": {
                    "gentxs": []
                }
            }
        }
        
        genesis_file = genesis_dir / "genesis.json"
        with open(genesis_file, 'w') as f:
            json.dump(genesis_content, f, indent=2)
        
        logger.info("Generated genesis file")

    def _generate_cli(self, chain_dir: Path, config: ChainConfig):
        """Generate CLI commands"""
        cli_dir = chain_dir / "cmd" / config.chain_id
        cli_dir.mkdir(parents=True, exist_ok=True)
        
        main_file = cli_dir / "main.go"
        main_content = f'''package main

import (
    "os"
    "strings"
    "github.com/CosmosBuilder/{config.chain_id}/cmd/{config.chain_id}d/cmd"
    "github.com/cosmos/cosmos-sdk/server"
    svrcmd "github.com/cosmos/cosmos-sdk/server/cmd"
    "github.com/cosmos/cosmos-sdk/x/auth/simapp"
    banktypes "github.com/cosmos/cosmos-sdk/x/bank/types"
    "github.com/spf13/cast"
    "github.com/spf13/cobra"
    "github.com/tendermint/spm/cosmoscmd"
    "github.com/tendermint/spm/openapiconsole"
    genutiltypes "github.com/cosmos/cosmos-sdk/x/genutil/types"
)

func main() {{
    setup := cosmoscmd.NewSetup("genutil", genutiltypes.DefaultGenesisState)
    cdc := MakeEncodingConfig(simapp.ModuleBasics, banktypes.AppModuleBasic{{}})
    appGenTx := cmd.GenTxCmd(simapp.ModuleBasics, cdc.TxConfig, setup)
    appGenState := cmd.GenesisCmd(simapp.ModuleBasics, cdc)
    
    cmd := &cobra.Command{{
        Use:   "{config.chain_id}d",
        Short: f"{{config.chain_name}} app Daemon",
        Long:  strings.TrimSpace(`
{config.chain_name} application (https://{config.chain_id}.io)

Usage:
    {{.Name}} <command> [flags]
`),
        }}
    
    add := func(a cobra.PositionalArgs) cobra.PositionalArgs {{
        return cobra.Command{{Use: os.Args[0]}}.ArgsCompleter(a)
    }}
    
    // NewRootCmd creates a new root command for the CosmosBuilder daemon
    rootCmd := cosmoscmd.NewRootCmd(
        "{config.chain_id}d",
        "genesis.toml",
        cdc,
        config.GetViper("home"),
        app.GetTxCmd(),
        app.GetQueryCmd(),
        &cmd,
    )
    
    // Add the new {config.chain_id}d command to the root command
    cmd.AddCommand(appGenTx)
    cmd.AddCommand(appGenState)
    
    // Add the openapiconsole command
    rootCmd.AddCommand(
        svrcmd.ExtractFlags(cmd),
        server.StatusCmd(),
        openapiconsole.Console(),
        genutilcmd.ModuleGenStateCmd(simapp.ModuleBasics, cdc.TxConfig, cdc.Marshaler),
        genutilcmd.MsgInvokeGenTx(
            cdc.TxConfig,
            simapp.ModuleBasics,
            cdc.Marshaler,
            setup,
        ),
        genutilcmd.ModuleInitCmd(simapp.ModuleBasics, cdc.TxConfig, cdc.Marshaler, setup),
        genutilcmd.ModuleSimulateGenesisCmd(simapp.ModuleBasics, cdc.TxConfig, cdc.Marshaler, setup),
    )
    
    // Add the {config.chain_id}d command
    cmd.AddCommand(rootCmd)
    
    // Run the root command
    rootCmd.PersistentPreRunE = func(cmd *cobra.Command, args []string) error {{
        return server.InterceptConfigsPreRunHandler(cmd, cdc, "genesis.toml")
    }}
    
    svrcmd.Execute(rootCmd, cdc, cdc, setup)
}}
'''
        
        main_file.write_text(main_content)

    def _generate_docker(self, chain_dir: Path, config: ChainConfig):
        """Generate Docker configuration"""
        docker_dir = chain_dir / "docker"
        docker_dir.mkdir(exist_ok=True)
        
        # Dockerfile
        dockerfile_content = f'''# This is a multi-stage build for {config.chain_name}
FROM golang:{config.chain_name}:alpine AS builder

WORKDIR /app

# Install dependencies
RUN apk add --no-cache \
    git \
    build-base \
    ca-certificates \
    libc-dev \
    linux-headers \
    openssl-dev

# Copy go files
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build the {config.chain_id}d binary
RUN CGO_ENABLED=1 go build -o {config.chain_id}d -ldflags="-linkmode external -extldflags=-static" ./cmd/{config.chain_id}/main.go

# Final stage
FROM alpine:latest

WORKDIR /root

# Copy binary from builder stage
COPY --from=builder /app/{config.chain_id}d .

# Create directories
RUN mkdir -p ~/.{config.chain_id}/data

EXPOSE 26656 26657 1317 9090

CMD ["."]
'''
        
        (docker_dir / "Dockerfile").write_text(dockerfile_content)
        
        # Docker Compose
        compose_content = f'''version: '3.8'

services:
  {config.chain_id}d:
    build:
      context: .
      dockerfile: docker/Dockerfile
    ports:
      - "26656:26656"
      - "26657:26657"
      - "1317:1317"
      - "9090:9090"
    volumes:
      - ./.{config.chain_id}:/root/.{config.chain_id}
      - ./genesis:/root/genesis
    environment:
      - {config.chain_id}_CHAIN_ID={config.chain_id}
      - {config.chain_id}_DENOM={config.denomination}
    command: |
      {config.chain_id}d init node1
      {config.chain_id}d keys add validator --recover --keyring-backend file
      {config.chain_id}d add-genesis-account ${{VALIDATOR_ADDRESS}} 1000000000{config.denomination}
      {config.chain_id}d gentx validator 100000000{config.denomination} --keyring-backend file --chain-id {config.chain_id}
      {config.chain_id}d collect-gentxs
      {config.chain_id}d start
'''
        
        (docker_dir / "docker-compose.yml").write_text(compose_content)

    def _generate_docs(self, chain_dir: Path, config: ChainConfig, modules: List[ModuleConfig]):
        """Generate documentation"""
        docs_dir = chain_dir / "docs"
        docs_dir.mkdir(exist_ok=True)
        
        # README
        readme_content = f'''# {config.chain_name} Blockchain

{config.description}

## Overview

This blockchain was generated using CosmosBuilder with the following configuration:

- **Chain ID**: {config.chain_id}
- **Symbol**: {config.symbol}
- **Denomination**: {config.denomination}
- **Initial Supply**: {config.initial_supply:,} {config.symbol}
- **Consensus**: {config.consensus_type}

## Modules

The following modules are enabled in this blockchain:

'''
        
        for module in modules:
            if module.enabled:
                status = "Premium" if module.is_premium else "Free"
                readme_content += f"- **{module.name}** ({status})\n"
        
        readme_content += f'''

## Installation

### Prerequisites

- Go 1.19+
- Git

### Build from Source

```bash
# Clone the repository
git clone <repository-url>
cd {config.chain_id}

# Build the binary
make install

# Initialize the chain
{config.chain_id}d init <your-node-name> --chain-id {config.chain_id}
```

### Using Docker

```bash
# Build and run with Docker
docker-compose up -d
```

## Configuration

### Node Configuration

Edit the configuration files in `~/.{config.chain_id}/config/`:

- `config.toml` - Tendermint configuration
- `app.toml` - Application configuration
- `client.toml` - Client configuration

### Genesis File

The genesis file is located at `~/.{config.chain_id}/config/genesis.json`.

## Running the Blockchain

### Start a Node

```bash
{config.chain_id}d start
```

### Create Validator

```bash
# Create a key
{config.chain_id}d keys add validator

# Initialize validator
{config.chain_id}d init <validator-name> --chain-id {config.chain_id}

# Add genesis account
{config.chain_id}d add-genesis-account <validator-address> 1000000000{config.denomination}

# Create genesis transaction
{config.chain_id}d gentx <validator-address> 100000000{config.denomination} --chain-id {config.chain_id}

# Collect genesis transactions
{config.chain_id}d collect-gentxs
```

## API Endpoints

- **REST API**: http://localhost:1317
- **RPC**: http://localhost:26657
- **WebSocket**: ws://localhost:26657/websocket
- **gRPC**: http://localhost:9090

## Development

### Testing

```bash
# Run unit tests
go test ./...

# Run integration tests
make test-integration
```

### Module Development

Each module follows the Cosmos SDK module structure:

```
x/<module-name>/
├── keeper/          # Module logic
├── types/           # Type definitions
├── client/          # CLI and REST handlers
└── module.go        # Module configuration
```

## Deployment

### Testnet Deployment

1. Initialize testnet:
```bash
{config.chain_id}d testnet init-files --chain-id {config.chain_id}-testnet
```

2. Deploy to testnet:
```bash
{config.chain_id}d testnet start --chain-id {config.chain_id}-testnet
```

### Mainnet Deployment

Follow the mainnet deployment guide in the deployment documentation.

## Support

For support and questions:

- Documentation: https://docs.{config.chain_id}.io
- GitHub Issues: <repository-url>/issues
- Discord: https://discord.gg/{config.chain_id}

## License

This blockchain is generated using CosmosBuilder. See LICENSE for details.
'''
        
        (docs_dir / "README.md").write_text(readme_content)
        
        # API Documentation
        api_content = '''# API Documentation

## REST API

The blockchain exposes several REST endpoints:

### Authentication
- `POST /api/auth/bank/balances/{address}`
- `GET /api/auth/accounts/{address}`

### Banking
- `GET /api/bank/balances/{address}`
- `GET /api/bank/total`
- `GET /api/bank/spendable_balances/{address}`

### Staking
- `GET /api/staking/validators`
- `POST /api/staking/delegators/{delegatorAddr}/delegations`
- `GET /api/staking/delegators/{delegatorAddr}/delegations`

### Governance
- `GET /api/gov/proposals`
- `POST /api/gov/proposals`
- `POST /api/gov/proposals/{proposalId}/votes`

### Transactions
- `POST /api/txs`
- `GET /api/txs/{hash}`

## gRPC API

### Query Services
- `cosmos.auth.v1beta1.Query`
- `cosmos.bank.v1beta1.Query`
- `cosmos.staking.v1beta1.Query`
- `cosmos.gov.v1beta1.Query`

### Transaction Services
- `cosmos.tx.v1beta1.Service`

## WebSocket

Real-time subscriptions:

```javascript
const ws = new WebSocket('ws://localhost:26657/websocket');

ws.send(JSON.stringify({
  "jsonrpc": "2.0",
  "id": 1,
  "method": "subscribe",
  "params": ["tm.event='NewBlock'"]
}));
```
'''
        
        (docs_dir / "api.md").write_text(api_content)

    def _build_blockchain(self, chain_dir: Path):
        """Build the blockchain binary"""
        logger.info("Building blockchain...")
        
        try:
            # Build the binary
            os.chdir(chain_dir)
            result = subprocess.run(['go', 'build', '-o', f'{chain_dir.name}d', './cmd', './...'], 
                                  capture_output=True, text=True, check=True)
            
            logger.info("Blockchain build successful!")
            
            # Generate binaries
            binaries_dir = chain_dir / "binaries"
            binaries_dir.mkdir(exist_ok=True)
            
            # Copy binary
            shutil.copy2(chain_dir / f'{chain_dir.name}d', binaries_dir)
            
            logger.info(f"Binary generated: {binaries_dir / chain_dir.name}d")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Build failed: {e.stderr}")
            raise

def generate_chain_configuration(config_data: Dict[str, Any]) -> ChainConfig:
    """Generate ChainConfig from user configuration data"""
    return ChainConfig(**config_data)

def generate_module_list(selected_modules: List[str]) -> List[ModuleConfig]:
    """Generate ModuleConfig list from selected modules"""
    modules = []
    
    # Core modules (always included)
    core_modules = ['auth', 'bank', 'staking', 'slashing', 'mint', 'gov', 'distribution', 'params', 'upgrade', 'ibc', 'genutil']
    for module_name in core_modules:
        modules.append(ModuleConfig(name=module_name, enabled=True, is_premium=False))
    
    # Additional modules
    module_map = {
        'cosmwasm': {'name': 'CosmWasm', 'is_premium': True},
        'evm': {'name': 'EVM', 'is_premium': True},
        'nft': {'name': 'NFT Module', 'is_premium': False},
        'tokenfactory': {'name': 'Token Factory', 'is_premium': False},
        'oracle': {'name': 'Oracle', 'is_premium': True},
        'amm': {'name': 'AMM DEX', 'is_premium': True},
        'lending': {'name': 'Lending Module', 'is_premium': True},
        'kyc': {'name': 'KYC/AML', 'is_premium': True},
        'permissioned': {'name': 'Permissioned', 'is_premium': True},
    }
    
    for module_name in selected_modules:
        if module_name in module_map:
            module_info = module_map[module_name]
            modules.append(ModuleConfig(
                name=module_info['name'],
                enabled=True,
                is_premium=module_info['is_premium']
            ))
    
    return modules

# Example usage
if __name__ == "__main__":
    # Example configuration
    chain_config = ChainConfig(
        chain_name="MyAwesomeChain",
        chain_id="myawesomechain-1",
        symbol="MAW",
        denomination="umaw",
        initial_supply=1000000000,
        description="A revolutionary blockchain built with CosmosBuilder"
    )
    
    # Example module selection
    selected_modules = ['cosmwasm', 'nft', 'amm', 'oracle']
    modules = generate_module_list(selected_modules)
    
    # Generate the blockchain
    engine = CosmosBuilderEngine()
    chain_path = engine.generate_blockchain(chain_config, modules)
    
    print(f"Blockchain generated successfully at: {chain_path}")
