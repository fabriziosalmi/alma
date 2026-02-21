# ALMA Cognitive Engine Guide

The **Cognitive Engine** provides context tracking, risk assessment, and dynamic persona selection to provide a safer and more intuitive conversational experience.

## How it Works

The engine sits in the request loop:
`User Input` -> **`Cognitive Engine`** -> `LLM Orchestrator` -> `Execution`

### 1. Frustration Detection & Safety
The system analyzes your input text for keywords that indicate frustration (e.g., "fail", "error", "broken", "wrong").

| Frustration Level | System Response |
|-------------------|-----------------|
| **Low (0.0 - 0.3)** | Standard operation. Helpful hints enabled. |
| **Medium (0.4 - 0.7)** | Terse mode. Removes "fluff", focuses on execution. |
| **High (0.8 - 1.0)** | **Safety Lock**. Destructive commands are blocked. Requires explicit "I confirm" syntax. |

### 2. Adaptive Personas
The AI changes its response style based on the task.

#### The Architect
*Activates when:* You ask to create blueprints or design systems.
*Style:* Creative, suggests improvements, explains "why".
> "I've designed a Redis Cluster. I suggest adding 3 sentinels for HA. Here is the blueprint..."

#### The Operator
*Activates when:* You deploy, rollback, or scale.
*Style:* Military precision. Confirms actions. No chatty text.
> "Deploying ID: 592. Status: PENDING. Engine: K8s."

#### The Medic
*Activates when:* Things go wrong (errors, logs, troubleshooting).
*Style:* Calm, step-by-step diagnosis.
> "I see a 503 error. Let's check the ingress controller first. Logs show..."

### 3. Context Shifting
ALMA remembers what you are working on.

**Example Flow:**
1. User: "Deploy `web-app-01`" -> *Context set to `web-app-01`*
2. User: "Scale **it** to 5 replicas" -> *System knows "it" is `web-app-01`*
3. User: "What about the database?" -> *Context Shift Detected! Focus moved to `database`*

## Configuration

You can tune the sensitivity in `.env`:

```bash
COGNITIVE_FRUSTRATION_THRESHOLD=0.7
COGNITIVE_SAFETY_OVERRIDE=true
```