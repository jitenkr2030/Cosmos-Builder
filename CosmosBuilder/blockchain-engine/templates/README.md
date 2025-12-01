# CosmosBuilder Templates

This directory contains clean, template-based structures for generating Cosmos SDK blockchains.

## Why Templates Instead of Full Cosmos-SDK?

1. **Clean & Minimal**: Only the essential files needed
2. **Version Control**: Use exact cosmos-sdk versions via go.mod
3. **Maintainable**: Easy to update templates when SDK updates
4. **Customizable**: Templates can be modified for different use cases
5. **No Bloat**: 430MB → ~10MB template files

## Template Structure

```
templates/
├── basic/
│   ├── app/
│   │   ├── app.go          # Clean app template
│   │   └── sim_test.go     # Test template
│   ├── proto/
│   │   └── buf.yaml        # Protocol buffer config
│   ├── Makefile            # Build configuration
│   ├── go.mod              # Go module with cosmos-sdk dependency
│   └── go.sum              # Go dependencies
├── enterprise/
│   └── [Extended templates for enterprise features]
└── sovereign/
    └── [Templates for sovereign chain requirements]
```

## How It Works

1. **Generator reads templates** from this directory
2. **Customizes with user config** (chain name, params, etc.)
3. **Creates new project** with cosmos-sdk as dependency
4. **No source code copying** - only templates + generation

## Cosmos-SDK Version Management

Instead of copying SDK files, templates reference cosmos-sdk via go.mod:

```go
require github.com/cosmos/cosmos-sdk v0.47.0
```

This ensures:
- Consistent SDK version across projects
- Easy version updates
- Proper dependency management
- Official SDK updates available to users