# Enhanced Function Calling Tools API

ALMA now includes a comprehensive set of **13 intelligent tools** that can be called by the LLM to perform infrastructure operations. This dramatically expands the capabilities beyond simple blueprint generation.

## Overview

The enhanced function calling system enables:

- **Automated Infrastructure Operations**: LLM can execute complex tasks autonomously
- **Natural Language Interface**: Users describe what they want, LLM selects appropriate tools
- **Composable Actions**: Tools can be chained for complex workflows
- **Type-Safe Execution**: Fully typed parameters with validation

## Available Tools

### 1. **create_blueprint**
Create a new infrastructure blueprint from specifications.

```json
{
  "name": "create_blueprint",
  "parameters": {
    "name": "my-infrastructure",
    "description": "Production web application",
    "resources": [...]
  }
}
```

### 2. **validate_blueprint**
Validate a blueprint for correctness and best practices.

```json
{
  "name": "validate_blueprint",
  "parameters": {
    "blueprint": {...},
    "strict": false
  }
}
```

### 3. **estimate_resources**
Estimate resource requirements for a workload.

```json
{
  "name": "estimate_resources",
  "parameters": {
    "workload_type": "web",
    "expected_load": "1000 requests/sec",
    "availability": "high"
  }
}
```

### 4. **optimize_costs**
Analyze and suggest cost optimizations.

```json
{
  "name": "optimize_costs",
  "parameters": {
    "blueprint": {...},
    "provider": "aws",
    "optimization_goal": "balanced"
  }
}
```

### 5. **security_audit**
Perform security audit on infrastructure.

```json
{
  "name": "security_audit",
  "parameters": {
    "blueprint": {...},
    "compliance_framework": "pci-dss",
    "severity_threshold": "medium"
  }
}
```

### 6. **generate_deployment_plan**
Generate step-by-step deployment plan.

```json
{
  "name": "generate_deployment_plan",
  "parameters": {
    "blueprint": {...},
    "strategy": "blue-green",
    "rollback_enabled": true
  }
}
```

### 7. **troubleshoot_issue**
Diagnose and suggest fixes for infrastructure issues.

```json
{
  "name": "troubleshoot_issue",
  "parameters": {
    "issue_description": "High latency on API endpoints",
    "symptoms": ["slow response times", "timeouts"],
    "logs": "..."
  }
}
```

### 8. **compare_blueprints**
Compare two blueprints and identify differences.

```json
{
  "name": "compare_blueprints",
  "parameters": {
    "blueprint_a": {...},
    "blueprint_b": {...},
    "show_details": true
  }
}
```

### 9. **suggest_architecture**
Suggest optimal architecture for given requirements.

```json
{
  "name": "suggest_architecture",
  "parameters": {
    "requirements": {
      "application_type": "e-commerce",
      "expected_users": 100000,
      "data_size": "500GB"
    },
    "constraints": {
      "preferred_provider": "aws",
      "budget": "$5000/month"
    }
  }
}
```

### 10. **calculate_capacity**
Calculate required capacity for scaling.

```json
{
  "name": "calculate_capacity",
  "parameters": {
    "current_metrics": {
      "cpu_usage": 70,
      "memory_usage": 65
    },
    "growth_rate": 25,
    "time_horizon": "6 months"
  }
}
```

### 11. **migrate_infrastructure**
Plan migration between different platforms.

```json
{
  "name": "migrate_infrastructure",
  "parameters": {
    "source_platform": "on-premise",
    "target_platform": "aws",
    "blueprint": {...},
    "migration_strategy": "replatform"
  }
}
```

### 12. **check_compliance**
Check infrastructure compliance against standards.

```json
{
  "name": "check_compliance",
  "parameters": {
    "blueprint": {...},
    "standards": ["pci-dss", "hipaa", "gdpr"],
    "generate_report": true
  }
}
```

### 13. **forecast_metrics**
Forecast infrastructure metrics and resource needs.

```json
{
  "name": "forecast_metrics",
  "parameters": {
    "historical_data": [...],
    "forecast_period": "90 days",
    "confidence_level": 0.95
  }
}
```

## API Endpoints

### List All Tools

```bash
GET /api/v1/tools/
```

**Response:**
```json
{
  "tools": [...],
  "count": 13
}
```

### Execute Tool (Natural Language)

```bash
POST /api/v1/tools/execute
```

**Request:**
```json
{
  "query": "I need to validate my blueprint and check if it's secure",
  "context": {}
}
```

The LLM will automatically select and execute the appropriate tool(s).

### Execute Tool (Direct)

```bash
POST /api/v1/tools/execute-direct
```

**Request:**
```json
{
  "tool_name": "validate_blueprint",
  "arguments": {
    "blueprint": {...},
    "strict": true
  }
}
```

### Get Tool Info

```bash
GET /api/v1/tools/{tool_name}
```

Returns detailed information about a specific tool.

### Convenience Endpoints

#### Validate Blueprint
```bash
POST /api/v1/tools/validate-blueprint
```

#### Estimate Resources
```bash
POST /api/v1/tools/estimate-resources?workload_type=web&expected_load=1000%20req/s
```

#### Security Audit
```bash
POST /api/v1/tools/security-audit
```

## Usage Examples

### Example 1: Natural Language Tool Selection

```python
from alma.core.llm_orchestrator import EnhancedOrchestrator
from alma.core.llm_qwen import Qwen3LLM

llm = Qwen3LLM()
orchestrator = EnhancedOrchestrator(llm=llm, use_llm=True)

# LLM will automatically select the right tool
result = await orchestrator.execute_function_call(
    "I need to estimate resources for a high-traffic web application"
)

print(result)
```

### Example 2: Direct Tool Execution

```python
from alma.core.tools import InfrastructureTools

tools = InfrastructureTools()

# Execute specific tool directly
result = tools.execute_tool(
    "estimate_resources",
    {
        "workload_type": "database",
        "expected_load": "10000 transactions/sec",
        "availability": "critical"
    }
)

print(result["result"])
```

### Example 3: Complex Workflow

```bash
# Step 1: Generate architecture
curl -X POST http://localhost:8000/api/v1/tools/execute \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Suggest architecture for a microservices platform with 50000 users"
  }'

# Step 2: Validate generated blueprint
curl -X POST http://localhost:8000/api/v1/tools/validate-blueprint \
  -H "Content-Type: application/json" \
  -d '{...}'

# Step 3: Security audit
curl -X POST http://localhost:8000/api/v1/tools/security-audit \
  -H "Content-Type: application/json" \
  -d '{...}'

# Step 4: Cost optimization
curl -X POST http://localhost:8000/api/v1/tools/execute-direct \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "optimize_costs",
    "arguments": {...}
  }'
```

## Integration with LLM

The tools are designed to work seamlessly with function calling:

1. **User makes request** in natural language
2. **LLM analyzes** the request and available tools
3. **LLM selects** the most appropriate tool(s)
4. **System executes** the tool with LLM-generated parameters
5. **Result is returned** to user (optionally processed by LLM for explanation)

## Best Practices

### Tool Selection
- Use natural language endpoint when user intent is unclear
- Use direct execution when you know exactly which tool to call
- Chain multiple tools for complex workflows

### Error Handling
All tools return structured responses:
```json
{
  "success": true/false,
  "tool": "tool_name",
  "result": {...},
  "error": "error message if failed",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Performance
- Tools execute synchronously - consider async for long operations
- Cache results when appropriate
- Use batch operations where available

## Extending Tools

To add a new tool:

1. Add tool definition to `InfrastructureTools.get_available_tools()`
2. Implement tool logic as static method
3. Add to tool_map in `execute_tool()`
4. Write tests in `test_tools.py`

Example:

```python
{
    "name": "my_new_tool",
    "description": "Does something useful",
    "parameters": {
        "type": "object",
        "properties": {
            "param1": {"type": "string"},
            "param2": {"type": "number"}
        },
        "required": ["param1"]
    }
}

@staticmethod
def _my_new_tool(args: Dict[str, Any], ctx: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    # Implementation
    return {"result": "success"}
```

## Future Enhancements

- [ ] Async tool execution
- [ ] Tool chaining/composition
- [ ] Tool result caching
- [ ] Custom tool plugins
- [ ] Tool analytics and monitoring
- [ ] Rate limiting per tool
- [ ] Tool versioning
- [ ] Parallel tool execution

## Testing

Run tool tests:

```bash
pytest tests/unit/test_tools.py -v
```

All 13 tools have comprehensive test coverage.
