# Agents: Building Autonomous Systems

An agent is more than a workflow; it is an autonomous system that uses an LLM to decide which tools to use and how to handle unexpected results. In Python, the ecosystem is rapidly maturing, moving from experimental scripts to production-grade frameworks.

## 1. Choosing Your Framework

For a seasoned engineer, the choice of framework depends on the required balance between **Autonomy** and **Control**.

| Framework            | Mental Model          | When to Use                                                                                                                                                   |
| :------------------- | :-------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **PydanticAI** | Type-Safe Functions   | Use this for**Production**. It feels like FastAPI for agents. It uses Pydantic for strict validation, making it highly reliable and easy to debug.      |
| **CrewAI**     | Role-Based Agents     | Use this for**Business Logic**. If you need an "Accountant Agent" and a "Manager Agent" to collaborate, CrewAI’s role-playing abstraction is powerful. |
| **LangGraph**  | Cyclic Graphs         | Use this for**Custom Architectures**. If you need to build a bespoke reasoning loop that doesn't fit the standard ReAct pattern.                        |
| **AutoGen**    | Conversational Agents | Use this for**Creative Problem Solving**. Ideal for multi-agent brainstorming or coding tasks.                                                          |

### Practical Recommendation

For this workshop, the default production recommendation is:

1. **Use PydanticAI when you are building a Python application service** and want typed dependencies, structured outputs, ordinary Python functions, and clear failure handling.
2. **Use LangGraph when the agent is really a state machine** with explicit loops, checkpoints, interrupts, and multiple known phases.
3. **Use CrewAI or AutoGen for multi-agent experiments** where role design, collaboration, and conversation patterns are the main thing being explored.
4. **Use no agent framework when the task is a simple workflow.** A queue, state machine, and direct LLM calls are easier to debug than an agent abstraction you do not need.

The selection criterion is not popularity. It is how much control you need over state, tools, retries, review gates, and traces.

### Framework Selection Checklist

Before choosing a framework, check:

* **Typing:** Can tool inputs, tool outputs, dependencies, and final responses be represented as schemas?
* **Lifecycle:** Can you start and stop tool servers, browser sessions, database sessions, or sandboxes cleanly?
* **Persistence:** Can the run resume after a crash or deployment?
* **Observability:** Can every model call, tool call, retry, and final output be traced?
* **Human control:** Can the framework pause before sensitive actions and resume with approval state?
* **Deployment fit:** Does it work in your runtime model: long-lived service, serverless function, background worker, or local CLI?
* **Escape hatch:** Can you drop down to normal Python or TypeScript when the abstraction gets in the way?

---

## 2. The Tooling Revolution: Model Context Protocol (MCP)

In the past, giving an agent a tool meant writing a custom wrapper for every API. The **Model Context Protocol (MCP)** changes this. It is a universal standard that allows agents to connect to tools and data sources seamlessly.

### Why MCP?

An API allows you to *get* data. MCP allows you to *provide context*.

* **FastMCP:** A framework that allows you to turn any Python function into an MCP-compatible tool in minutes.
* **Motivation:** APIs are often too rigid for LLMs. MCP servers can expose not just functions, but also local files, database schemas, and even browser sessions in a way that the LLM can "understand" and navigate.

### What MCP Adds Beyond a Normal API

A normal API is designed for application code that already knows which endpoint to call. MCP is designed for a model runtime that needs to discover available capabilities and context at runtime.

MCP servers can expose:

* **Tools:** Callable functions with typed arguments, such as `check_stock(item_id)`.
* **Resources:** Readable context, such as files, database schemas, traces, or design documents.
* **Prompts:** Reusable prompt templates or task recipes supplied by the tool provider.

This does not mean MCP replaces your product API. Treat MCP as the agent-facing adapter layer. The actual business rules, auth checks, and side effects should still live in normal application services.

### Tool Interface Design

Good tools are narrow, typed, and boring:

* Prefer `refund_order(order_id: str, amount_cents: int, reason_code: RefundReason)` over `handle_refund(text: str)`.
* Return structured results with status codes the agent can reason about, such as `not_found`, `requires_approval`, or `completed`.
* Include domain constraints in the tool description: limits, permissions, side effects, and examples.
* Separate read tools from write tools. A read tool can often run automatically; a write tool usually needs authorization and idempotency.
* Make tool errors useful. Return validation and permission errors as observations the model can use, not stack traces.

---

## 3. Production Considerations for Agents

### State Management

State is the "memory" of your agent. In production, you must handle:

* **Persistence:** Saving the agent's state to a database (Postgres/Redis) so it can resume after a crash.
* **Context Pruning:** Agents can "forget" the original goal if the conversation gets too long. You must implement strategies to summarize old turns or "slide" the window of active context.
* **State Ownership:** Separate user-visible memory, private scratchpad, workflow state, and audit logs. These have different retention and privacy requirements.
* **Versioning:** Store a schema version with persisted state so in-flight runs can survive prompt, model, or code changes.

### Failure Handling: The "Retry" isn't enough

In agentic engineering, a "failure" might be the LLM calling a tool with the wrong arguments.

* **Self-Correction:** Catch the error, pass it back to the LLM as a "Thought," and let it try again with a different argument.
* **Fallback Models:** If a cheap model (GPT-4o-mini) fails the reasoning task, automatically "escalate" the task to a more capable model (Claude 3.5 Sonnet).
* **Circuit Breakers:** Stop the loop after repeated invalid tool calls, repeated identical actions, or no progress toward the acceptance criteria.
* **Human Escalation:** Convert unknown or high-risk failures into a review task rather than forcing the model to improvise.

### Evaluation & Observability

You cannot "unit test" an agent's path. You must use **Traces**.

* **LangSmith / Langfuse:** These tools allow you to visualize the "Trajectory" of the agent. You can see exactly why an agent chose Tool A over Tool B.
* **Evals:** Create a dataset of "Golden Trajectories"—expected sequences of tool calls for specific prompts—and run them against new versions of your agent to check for regressions.
* **Assertions:** Even when the path varies, assert invariants: no prohibited tools, no writes before approval, final answer cites required evidence, and total spend stays under budget.
* **Replay:** Keep enough trace data to replay a run against a new prompt, model, or tool implementation.

### Security: The "Sandboxing" Mandate

Never give an agent direct access to your host shell.

1. **Code Interpreters:** Use tools like **E2B** to run agent-generated code in a secure, isolated sandbox.
2. **Least Privilege:** Scoped API keys are mandatory. If an agent only needs to read a Google Sheet, do not give it access to the entire Google Drive.
3. **Policy Enforcement Outside the Model:** The runtime must reject prohibited actions even if the LLM asks for them confidently.
4. **Prompt Injection Boundaries:** Treat retrieved documents, webpages, emails, and tickets as untrusted input. They should not be allowed to override system instructions or tool permissions.

### Cost / Latency Tradeoffs

Agents are expensive. A single user request might trigger 10 LLM calls.

* **Parallelism:** If the LLM determines it needs to call three tools, use a framework that supports parallel tool execution.
* **Prefetching:** Use "Cheap" models for classification and routing, and "Expensive" models only for the final reasoning or tool argument generation.
* **Budget-Aware Looping:** Pass remaining budget into the agent state and stop gracefully when the task cannot be completed inside the limit.
* **Caching:** Cache read-only tool results and deterministic LLM sub-results where policy allows.

---

## 4. Engineering Heuristics for Performance

1. **Prompt as Code:** Treat your system prompts like code. Use version control. A one-word change can break an agent's tool-calling capability.
2. **Explicit Tool Descriptions:** The LLM's "vision" of a tool is its description. Be verbose. Instead of `get_data`, use `fetches_user_billing_history_as_json_for_the_last_30_days`.
3. **Always Validate:** If a tool returns data, validate it with Pydantic before the agent sees it. Garbage In, Garbage Out still applies to AI.

## 5. Step-by-Step Implementation: Pydantic AI + FastMCP

This section provides a concrete roadmap to building a production-ready agent that consumes external tools via MCP and manages long-term state.

### 5.1. Precision Tool Design

The "Intelligence" of an agent is limited by the clarity of its tools. When designing tools for Pydantic AI or MCP:

* **Rich Docstrings as UI:** The model doesn't see your code; it only sees the function signature and the docstring. Be explicit about *when* and *why* a tool should be used.
* **Complex Inputs with Pydantic:** Use Pydantic models for tool arguments to provide automatic validation and clear schema definitions to the model.
* **Feedback Loops:** Tools should return clear error messages that the model can use to self-correct (e.g., "The item ID must be 4 characters long").

```python
from pydantic import BaseModel, Field

class StockUpdate(BaseModel):
    item_id: str = Field(description="Unique identifier for the product")
    quantity: int = Field(gt=0, description="Number of units to add (must be positive)")

# A well-designed tool
@agent.tool
async def update_stock(ctx: RunContext[Deps], data: StockUpdate) -> str:
    """Updates inventory levels. Use this when a shipment arrives or a return is processed."""
    return f"Successfully updated {data.item_id} by {data.quantity} units."
```

#### Reuse Existing MCP Servers Before Writing New Tools

Precision tool design also includes deciding when **not** to design a new tool. In many teams, the fastest path is to adopt an existing MCP server and only build custom tools for domain-specific gaps.

Practical places to find existing tools:

* **MCP Registry:** Browse published MCP servers and choose maintained, installable options.
* **Official MCP reference servers:** Useful for learning patterns quickly, but treat them as references, not production defaults.
* **Vendor-maintained servers:** Prefer the server maintained by the product owner (for example, observability, issue tracker, or source-control providers) when available.

#### Choosing the Right MCP Tools (Selection Rubric)

When comparing candidate MCP servers, score them on:

* **Task fit:** Does the server expose the exact tools/resources/prompts your agent needs, or only a rough approximation?
* **Safety model:** Can you separate read vs. write actions, require approval for writes, and enforce least privilege credentials?
* **Schema quality:** Are tool names, descriptions, and JSON schemas explicit enough that the model can pick and call them correctly?
* **Transport fit:** Use **stdio** for local trusted tools, and **Streamable HTTP/SSE** for remote shared services.
* **Operational maturity:** Active maintenance, versioning, changelog, and clear ownership.
* **Latency and cost:** Remote tools add network overhead; oversized tool catalogs increase prompt tokens and routing ambiguity.
* **Observability:** You can log and trace tool calls, inputs, outputs, failures, and retries.

A useful default is: **start with the smallest trusted set of read-only tools**, then add write tools only behind approval gates.

#### Integrating Existing MCP Servers into the App (Pydantic AI)

In Pydantic AI, each MCP server becomes a `toolset`. You can connect multiple servers and manage them together:

```python
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio, MCPServerStreamableHTTP

local_git = MCPServerStdio(
    "uv",
    args=["run", "mcp-server-git", "stdio"],
    tool_prefix="git",
)

remote_observability = MCPServerStreamableHTTP(
    "https://mcp.example.com/observability",
    tool_prefix="obs",
    include_instructions=True,
)

agent = Agent(
    "openai:gpt-4o",
    toolsets=[local_git, remote_observability],
    instructions="Use git_* tools for repo actions and obs_* tools for production diagnostics.",
)

async def run_query():
    async with agent:
        result = await agent.run("Find the failing commit and summarize the production error.")
        print(result.output)
```

For larger deployments, load server definitions from config instead of hard-coding:

```python
from pydantic_ai import Agent
from pydantic_ai.mcp import load_mcp_servers

servers = load_mcp_servers("mcp_config.json")
agent = Agent("openai:gpt-4o", toolsets=servers)
```

Design notes for production integration:

* Use `tool_prefix` to prevent name collisions across servers.
* Use environment-variable expansion in MCP config to keep secrets out of source control.
* Keep server scopes narrow (specific roots, API scopes, and tenant boundaries).
* Pass request metadata via `process_tool_call` when servers need tenant/user context for authorization.
* Periodically review and prune tool catalogs so the model only sees tools that matter for the current app surface.

### 5.2. Defining Behavior with skills

In agentic engineering, a **skill** is a modular, versioned instruction set that defines the "personality" and operational constraints of an agent. Instead of one massive system prompt, you can treat behavior as a collection of skills:

* **Encapsulation:** Group related instructions (e.g., "Conflict Resolution," "Compliance Check") into discrete skill blocks.
* **Dynamic Injection:** Inject specific skills into the system prompt based on the user's current goal or the agent's detected state.
* **Composition:** Build specialized agents by composing standard skills like building blocks.

### 5.3. Permanent State & Memory Persistence

Production agents cannot rely on in-memory lists. You must persist the conversation history (the "memory") to a durable store like **PostgreSQL** or **Redis**.

* **Postgres (JSONB):** Store the list of `ModelMessage` objects as a JSONB blob associated with a `conversation_id`.
* **Redis:** Use Redis for high-performance session state where latency is critical.
* **Pattern:** Always load the history before a run and save the `result.all_messages()` immediately after.

```python
# Conceptual Persistence Pattern
existing_messages = await db.load_messages(conversation_id)

result = await agent.run(
    "How many widgets do we have?",
    message_history=existing_messages
)

# result.all_messages() contains both the old history and the new turn
await db.save_messages(conversation_id, result.all_messages())
```

### 5.4. Execution Roadmap (Setup Steps)

1. **Environment:** Create a virtual environment and install dependencies:
   ```bash
   pip install "pydantic-ai-slim[mcp]" mcp python-dotenv
   ```

   If the project already uses the full Pydantic AI package, `pip install pydantic-ai` is also acceptable.
2. **Build the Tool Server (FastMCP):** Create a separate file `server.py` to host your tools. This isolates the "Execution Layer" from the "Intelligence Layer."
3. **Define the Agent:** Create `agent_app.py`, initialize the `Agent` with Pydantic validation for structured outputs.
4. **Connect via Stdio:** Use `MCPServerStdio` to allow the agent to launch and communicate with the tool server.
5. **Inject Dependencies:** Use Pydantic AI's `RunContext` to pass stateful objects (like database connections) into tools.
6. **Set Boundaries:** Define maximum retries, tool-call budgets, approval requirements, and trace metadata before adding more tools.

### Code Implementation

#### Part A: The MCP Tool Server (`server.py`)

This follows the **Least Privilege** principle by only exposing specific functions.

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("InventoryManager")

@mcp.tool()
async def check_stock(item_id: str) -> int:
    """Check the current stock level for a specific item ID."""
    # Engineering Note: This is where you connect to your real DB
    inventory_db = {"A101": 50, "B202": 0}
    return inventory_db.get(item_id, 0)

if __name__ == "__main__":
    mcp.run()
```

#### Part B: The Pydantic AI Agent (`agent_app.py`)

This demonstrates **State Management**, **Type Safety**, and **Observability**.

```python
import asyncio
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
from dotenv import load_dotenv

load_dotenv()

# 1. Structured Output Schema (Validation)
class PurchaseRecommendation(BaseModel):
    item_id: str
    should_buy: bool
    reasoning: str

# 2. Define the Agent with Intelligence and Toolsets
# The 'toolsets' parameter is where the MCP integration happens
mcp_server = MCPServerStdio("python", args=["server.py"])

agent = Agent(
    'openai:gpt-4o',
    output_type=PurchaseRecommendation,
    toolsets=[mcp_server],
    instructions="Analyze inventory levels and recommend if we should restock."
)

# 3. Execution Loop with Lifecycle Management
async def main():
    # Use 'async with' to handle the subprocess lifecycle of the MCP server
    async with mcp_server:
        result = await agent.run("Should we restock item A101?")
      
        # Accessing validated data
        print(f"Recommendation for {result.output.item_id}:")
        print(f"Should Buy: {result.output.should_buy}")
        print(f"Reason: {result.output.reasoning}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Factoring in Production Concepts

* **Stateful Dependencies:** Use `RunContext` in Pydantic AI to pass a `User` object or a `DatabaseSession` to your local tools. This ensures the agent's tools are grounded in the current **State**.
* **Tool Validation:** By using Pydantic models for `output_type`, the agent is forced to "Reason" toward a structured schema. If it fails, Pydantic AI's internal **Failure Handling** can retry the prompt with the validation error.
* **Security:** The FastMCP server runs in a separate process. You can further secure this by running the server in a **Docker Sandbox** while the agent remains in your primary application environment.
* **Cost/Latency:** Notice that `check_stock` is a fast, local function. By using MCP, the agent only calls this tool when its "Intelligence" (GPT-4o) determines it is necessary, saving expensive tokens on unnecessary lookups.

### Adding a Local Tool with Dependencies

Not every tool needs MCP. If the tool is private to one service, a local typed function is often simpler. Use dependency injection for request-specific state such as the authenticated user, tenant id, or database session.

```python
from dataclasses import dataclass
from pydantic_ai import Agent, RunContext

@dataclass
class AgentDeps:
    user_id: str
    tenant_id: str
    inventory: dict[str, int]

local_agent = Agent(
    "openai:gpt-4o-mini",
    deps_type=AgentDeps,
    output_type=PurchaseRecommendation,
    instructions="Recommend restocking only from the current tenant inventory.",
)

@local_agent.tool
async def check_local_stock(ctx: RunContext[AgentDeps], item_id: str) -> int:
    """Check stock for an item visible to the current tenant."""
    # The tool can enforce tenant and user policy before returning data.
    return ctx.deps.inventory.get(item_id, 0)
```

This pattern is easier to test than a fully remote tool server. Use MCP when the tool should be reused across agents, languages, hosts, or products.

### Minimal Evaluation Set

Create a small eval set before adding more capabilities:

| Case                                 | Expected behavior                                                                 |
| :----------------------------------- | :-------------------------------------------------------------------------------- |
| In-stock item                        | Agent recommends no restock and cites the stock count.                            |
| Out-of-stock item                    | Agent recommends restock and calls the inventory tool once.                       |
| Unknown item                         | Agent asks for clarification or reports that the item was not found.              |
| Prompt injection in item description | Agent ignores the injected instruction and follows the system instructions.       |
| Write action requested               | Agent produces a plan or review request instead of performing the write directly. |

Track both final answer quality and trajectory quality. A correct final answer reached through prohibited tools is still a failing run.

### Deployment Checklist

Before deploying an agent service, confirm:

1. The agent process has no broad shell, filesystem, database, or cloud credentials.
2. Every write tool has authorization, idempotency, and audit logging.
3. The model cannot see secrets unless they are required for the task and scoped to that run.
4. Tool descriptions are versioned with the code that implements the tools.
5. Traces include model name, prompt version, tool version, state version, and approval records.
6. There is a kill switch or feature flag to disable the agent without disabling the whole product.
