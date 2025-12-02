"""Prompt templates for LLM infrastructure tasks."""

from __future__ import annotations
from typing import Any


class InfrastructurePrompts:
    """Collection of prompt templates for infrastructure tasks."""

    @staticmethod
    def blueprint_generation(description: str) -> str:
        """
        Generate prompt for creating a blueprint from description.

        Args:
            description: Natural language infrastructure description

        Returns:
            Formatted prompt
        """
        return f"""Generate an infrastructure blueprint in YAML format based on this description:

"{description}"

The blueprint should follow this structure:
```yaml
version: "1.0"
name: <descriptive-name>
description: <brief description>
resources:
  - type: <compute|network|storage|service>
    name: <resource-name>
    provider: <proxmox|fake|docker>
    specs:
      <resource-specific specs>
    dependencies:
      - <list of dependencies>
    metadata:
      <additional metadata>
metadata:
  <blueprint-level metadata>
```

Guidelines:
- Include appropriate resources based on the description
- Add load balancers for multi-server setups
- Include database servers if data persistence is mentioned
- Add proper dependencies between resources
- Use realistic resource specifications
- Consider security and high availability

Respond with ONLY the YAML blueprint, no additional text."""

    @staticmethod
    def blueprint_description(blueprint: dict[str, Any]) -> str:
        """
        Generate prompt for describing a blueprint.

        Args:
            blueprint: Blueprint dictionary

        Returns:
            Formatted prompt
        """
        import yaml

        blueprint_yaml = yaml.dump(blueprint, default_flow_style=False)

        return f"""Describe this infrastructure blueprint in clear, natural language:

```yaml
{blueprint_yaml}
```

Provide:
1. A high-level overview of what this infrastructure does
2. List of main components and their purposes
3. How the components work together
4. Any notable architectural decisions

Keep it concise and easy to understand."""

    @staticmethod
    def improvement_suggestions(blueprint: dict[str, Any]) -> str:
        """
        Generate prompt for suggesting improvements.

        Args:
            blueprint: Blueprint dictionary

        Returns:
            Formatted prompt
        """
        import yaml

        blueprint_yaml = yaml.dump(blueprint, default_flow_style=False)

        return f"""Analyze this infrastructure blueprint and suggest improvements:

```yaml
{blueprint_yaml}
```

Consider:
1. High availability and redundancy
2. Security best practices
3. Performance optimization
4. Cost efficiency
5. Scalability
6. Monitoring and observability
7. Disaster recovery

Provide 3-5 specific, actionable recommendations.
For each recommendation:
- Explain the current limitation
- Suggest the improvement
- Explain the benefit

Format as a numbered list."""

    @staticmethod
    def resource_sizing(workload: str, expected_load: str) -> str:
        """
        Generate prompt for resource sizing recommendations.

        Args:
            workload: Type of workload
            expected_load: Expected load description

        Returns:
            Formatted prompt
        """
        return f"""Recommend resource specifications for this workload:

Workload Type: {workload}
Expected Load: {expected_load}

Provide specific recommendations for:
1. CPU (number of cores)
2. Memory (in GB)
3. Storage (size and type)
4. Network (bandwidth requirements)

Consider:
- Performance requirements
- Cost optimization
- Headroom for growth
- Best practices for this workload type

Respond in JSON format:
{{
  "cpu": <number>,
  "memory": "<size>GB",
  "storage": "<size>GB",
  "storage_type": "<SSD|HDD>",
  "network": "<bandwidth>",
  "reasoning": "<brief explanation>"
}}"""

    @staticmethod
    def troubleshooting(issue: str, context: dict[str, Any]) -> str:
        """
        Generate prompt for troubleshooting.

        Args:
            issue: Description of the issue
            context: Additional context

        Returns:
            Formatted prompt
        """
        import json

        context_str = json.dumps(context, indent=2)

        return f"""Help troubleshoot this infrastructure issue:

Issue: {issue}

Context:
{context_str}

Provide:
1. Possible root causes (3-5 most likely)
2. Step-by-step diagnostic steps
3. Recommended solutions
4. Preventive measures for the future

Be specific and technical."""

    @staticmethod
    def security_audit(blueprint: dict[str, Any]) -> str:
        """
        Generate prompt for security audit.

        Args:
            blueprint: Blueprint to audit

        Returns:
            Formatted prompt
        """
        import yaml

        blueprint_yaml = yaml.dump(blueprint, default_flow_style=False)

        return f"""Perform a security audit of this infrastructure blueprint:

```yaml
{blueprint_yaml}
```

Check for:
1. Exposed services and ports
2. Network segmentation
3. Encryption (data at rest and in transit)
4. Access control and authentication
5. Secrets management
6. Compliance considerations
7. Monitoring and logging

For each finding:
- Severity: Critical/High/Medium/Low
- Issue description
- Recommendation

Format as a structured list."""

    @staticmethod
    def cost_estimation(blueprint: dict[str, Any], provider: str = "aws") -> str:
        """
        Generate prompt for cost estimation.

        Args:
            blueprint: Blueprint to estimate
            provider: Cloud provider

        Returns:
            Formatted prompt
        """
        import yaml

        blueprint_yaml = yaml.dump(blueprint, default_flow_style=False)

        return f"""Estimate the monthly cost of running this infrastructure on {provider}:

```yaml
{blueprint_yaml}
```

Provide:
1. Cost breakdown by resource type
2. Total estimated monthly cost
3. Cost optimization suggestions
4. Reserved instance/committed use recommendations

Respond in JSON format:
{{
  "resources": [
    {{
      "name": "<resource-name>",
      "type": "<type>",
      "monthly_cost": <cost>,
      "currency": "USD"
    }}
  ],
  "total_monthly": <total>,
  "currency": "USD",
  "optimizations": [
    "<suggestion 1>",
    "<suggestion 2>"
  ]
}}"""

    @staticmethod
    def migration_plan(source: str, target: str, blueprint: dict[str, Any]) -> str:
        """
        Generate prompt for migration planning.

        Args:
            source: Source platform
            target: Target platform
            blueprint: Current blueprint

        Returns:
            Formatted prompt
        """
        import yaml

        blueprint_yaml = yaml.dump(blueprint, default_flow_style=False)

        return f"""Create a migration plan to move this infrastructure from {source} to {target}:

Current Infrastructure:
```yaml
{blueprint_yaml}
```

Provide:
1. Migration strategy (lift-and-shift, re-platform, re-architect)
2. Step-by-step migration plan
3. Resource mapping ({source} → {target})
4. Risks and mitigation strategies
5. Estimated timeline
6. Rollback plan

Be specific and practical."""

    @staticmethod
    def intent_classification(user_input: str) -> str:
        """
        Generate prompt for intent classification.

        Args:
            user_input: User's natural language input

        Returns:
            Formatted prompt
        """
        return f"""Classify the user's intent from this input:

"{user_input}"

Available intents:
- create_blueprint: User wants to create new infrastructure
- deploy: User wants to deploy infrastructure
- list: User wants to see existing resources
- status: User wants to check infrastructure status
- update: User wants to modify existing infrastructure
- delete: User wants to remove infrastructure
- rollback: User wants to revert changes
- troubleshoot: User needs help with an issue
- optimize: User wants performance/cost optimization
- security: User has security concerns

Respond with JSON:
{{
  "intent": "<intent>",
  "confidence": <0-1>,
  "entities": {{
    "<entity_type>": "<entity_value>"
  }},
  "reasoning": "<brief explanation>"
}}

Only respond with valid JSON."""


# Convenience functions
def get_blueprint_prompt(description: str) -> str:
    """Get blueprint generation prompt."""
    return InfrastructurePrompts.blueprint_generation(description)


def get_description_prompt(blueprint: dict[str, Any]) -> str:
    """Get blueprint description prompt."""
    return InfrastructurePrompts.blueprint_description(blueprint)


def get_improvement_prompt(blueprint: dict[str, Any]) -> str:
    """Get improvement suggestions prompt."""
    return InfrastructurePrompts.improvement_suggestions(blueprint)


def get_intent_prompt(user_input: str) -> str:
    """Get intent classification prompt."""
    return InfrastructurePrompts.intent_classification(user_input)
