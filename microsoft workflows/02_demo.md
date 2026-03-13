Below is a **complete, production-level walkthrough of building a multi-agent workflow in the Azure AI Foundry NextGen portal (`ai.azure.com/nextgen`)** including:

* multi-agent orchestration
* parallel agents
* if/else conditional routing
* human-in-the-loop
* Azure AI Search grounding
* chat-style multi-agent system

The explanation strictly follows the **Azure AI Foundry workflow documentation and current portal workflow builder behavior**.

Workflows in Foundry are **visual orchestration graphs where agents, tools, and logic nodes are connected to create intelligent automation pipelines** that combine AI reasoning and business processes. ([Microsoft Learn][1])

---

# End-to-End Example System We Will Build

Before opening the portal, first understand the **target architecture**.

We will build a **multi-agent enterprise chat system**:

User asks a question → system retrieves enterprise knowledge → agents analyze → human approves → answer returned.

Workflow graph:

```
User Input
   ↓
Intent Classifier Agent
   ↓
IF / ELSE
   ├── Knowledge Question
   │      ↓
   │   Parallel Agents
   │      ├── Azure AI Search Agent
   │      ├── Web Research Agent
   │
   │      ↓
   │   Merge Results
   │      ↓
   │   Summarization Agent
   │      ↓
   │   Human Approval
   │      ↓
   │   Response Agent
   │
   └── General Chat Agent
```

This includes **all orchestration primitives**:

* conditional routing
* parallel execution
* human review
* knowledge grounding
* agent chat generation

---

# PART 1 — Environment Setup in Azure AI Foundry

## Step 1 — Open the NextGen Portal

Open

```
https://ai.azure.com
```

Switch to the **NextGen experience**.

Create or open a **Foundry Project**.

Inside a project you manage:

* models
* agents
* workflows
* tools
* datasets

The Foundry project acts as the **central control plane for AI agents, orchestration, and monitoring**. ([Microsoft Learn][2])

---

## Step 2 — Deploy a Model

Navigate

```
Models → Deployments
```

Deploy one model such as:

```
gpt-4o
gpt-4o-mini
```

Configuration example:

```
Deployment name: gpt4o-chat
Region: East US
Scale: Standard
```

This deployment becomes the **LLM backend used by agents**.

---

# PART 2 — Create Azure AI Search (Knowledge Source)

Because we will use enterprise RAG.

## Step 3 — Create Azure AI Search

In Azure Portal create:

```
Azure AI Search
```

Configuration:

```
Search Service Name: enterprise-search
Pricing tier: Basic
Region: Same as Foundry
```

---

## Step 4 — Create Index

Example index:

```
knowledge-index
```

Schema:

```
id
content
source
embedding
```

Example document:

```
{
  "id": "doc1",
  "content": "Azure AI Foundry enables building multi-agent workflows.",
  "source": "internal_docs"
}
```

---

## Step 5 — Connect AI Search to Foundry

Go back to Foundry portal.

Navigate:

```
Project Settings → Connections
```

Add connection:

```
Azure AI Search
```

Provide:

```
search_endpoint
search_key
index_name
```

Now agents can **retrieve enterprise knowledge via tools**.

This enables grounding answers using indexed documents. ([GitHub][3])

---

# PART 3 — Create the Agents

Navigate:

```
Agents → Create Agent
```

---

# Agent 1 — Intent Classifier

Purpose:

Detect query type.

Configuration:

```
Name: intent-classifier
Model: gpt4o-chat
Temperature: 0
```

System Prompt:

```
Classify the user query into one of the following:

knowledge_query
general_chat

Return JSON:
{
 "intent": "<type>"
}
```

---

# Agent 2 — Azure AI Search Agent

Purpose:

Retrieve enterprise documents.

Tools:

```
Azure AI Search tool
```

Prompt:

```
Retrieve relevant documents from the enterprise knowledge base
and provide supporting context for answering the question.
```

---

# Agent 3 — Web Research Agent

Purpose:

External information retrieval.

Tools:

```
Bing Search
Browser tool
```

Prompt:

```
Search the web for recent and relevant information.
Return concise research notes.
```

---

# Agent 4 — Summarization Agent

Prompt:

```
Combine research results from multiple agents and produce
a concise structured summary with citations.
```

---

# Agent 5 — Response Agent

Prompt:

```
Generate the final answer to the user based on
the summarized knowledge.
Ensure clarity and correctness.
```

---

# Agent 6 — General Chat Agent

Prompt:

```
Handle general conversation that does not require
enterprise knowledge retrieval.
```

---

# PART 4 — Create the Workflow

Navigate:

```
Agents → Workflows
```

Click:

```
Create Workflow
```

Name:

```
enterprise-chat-workflow
```

Workflows in Foundry are **visual graphs connecting agents and logic nodes to orchestrate execution**. ([Microsoft Learn][1])

---

# PART 5 — Build the Workflow Graph

The UI builder shows a **canvas graph**.

---

# Step 1 — Start Node

Add node:

```
Trigger
```

Input variable:

```
user_query
```

---

# Step 2 — Add Intent Classifier Agent

Add node:

```
Agent Node
```

Select agent:

```
intent-classifier
```

Input:

```
user_query
```

Output variable:

```
intent_result
```

---

# Step 3 — Add IF / ELSE Condition

Add node:

```
Condition Node
```

Condition expression:

```
intent_result.intent == "knowledge_query"
```

Routes:

```
True → Knowledge workflow
False → Chat agent
```

---

# PART 6 — Build Knowledge Branch

---

# Step 4 — Add Parallel Execution

Add node:

```
Parallel Node
```

Add branches:

```
branch_1 → AI Search Agent
branch_2 → Web Research Agent
```

Parallel orchestration is one of the recommended multi-agent execution patterns. ([Microsoft Learn][4])

---

# Branch 1 — Azure AI Search Agent

Node:

```
Agent Node
```

Agent:

```
search-agent
```

Input:

```
user_query
```

Output:

```
search_results
```

---

# Branch 2 — Web Research Agent

Node:

```
Agent Node
```

Agent:

```
web-research-agent
```

Output:

```
web_results
```

---

# Step 5 — Merge Parallel Outputs

Add node:

```
Transform Node
```

Combine outputs:

```
merged_context = search_results + web_results
```

Example structured variable:

```
{
 "enterprise_knowledge": search_results,
 "web_context": web_results
}
```

---

# Step 6 — Summarization Agent

Add node:

```
Agent Node
```

Agent:

```
summarization-agent
```

Input:

```
merged_context
```

Output:

```
summary
```

---

# PART 7 — Human-in-the-Loop

Now we add **human approval step**.

Human review steps allow workflows to pause and wait for manual input or approval. ([Microsoft Learn][5])

---

Add node:

```
Human Approval Node
```

Configuration:

```
Approver: Admin group
Timeout: 24h
Action options:
  approve
  reject
```

Inputs:

```
summary
```

Outputs:

```
approved_summary
```

Flow:

```
If Approved → Response Agent
If Rejected → Escalation
```

---

# PART 8 — Generate Final Answer

Add node:

```
Agent Node
```

Agent:

```
response-agent
```

Input:

```
approved_summary
user_query
```

Output:

```
final_answer
```

---

# PART 9 — Chat Branch

Return to the **false condition path**.

Add node:

```
Agent Node
```

Agent:

```
general-chat-agent
```

Input:

```
user_query
```

Output:

```
chat_response
```

---

# PART 10 — End Node

Add node:

```
Output
```

Return:

```
final_answer OR chat_response
```

---

# Final Workflow Graph

```
Trigger
   ↓
Intent Classifier
   ↓
Condition
 ┌───────────────┴───────────────┐
 │                               │
Knowledge Flow                Chat Flow
 │                               │
Parallel Execution           Chat Agent
 │
├─ AI Search Agent
├─ Web Research Agent
 │
Merge
 │
Summarization Agent
 │
Human Approval
 │
Response Agent
 │
Final Answer
```

---

# PART 11 — Test the Workflow

Inside the workflow UI:

Click

```
Run Test
```

Example input:

```
How does Azure AI Foundry support multi-agent orchestration?
```

Expected system execution:

1 classify intent
2 run parallel retrieval
3 summarize
4 wait for human approval
5 generate final answer

---

# PART 12 — Export YAML Workflow

Foundry allows exporting workflow to YAML.

Example simplified YAML:

```yaml
workflow:
  trigger: user_query

  steps:

  - name: classify_intent
    agent: intent-classifier

  - name: check_intent
    condition: intent == "knowledge_query"

  - parallel:
      - agent: search-agent
      - agent: web-research-agent

  - transform:
      merge: [search_results, web_results]

  - agent: summarization-agent

  - human_approval:
      approver: admin

  - agent: response-agent
```

Portal workflows can later be **opened in VS Code for advanced editing**. ([Microsoft for Developers][6])

---

# Production Architecture (Recommended)

```
Frontend Chat UI
      ↓
API Gateway
      ↓
Azure AI Foundry Workflow
      ↓
Agents
   ├ AI Search Agent
   ├ Web Agent
   ├ Summarization Agent
   └ Response Agent
      ↓
Azure AI Search
Cosmos DB
Monitoring
```

---

# Best Practices for Enterprise Workflows

## Agent specialization

Never overload one agent.

Use separate agents for:

```
retrieval
reasoning
summarization
response
```

---

## Parallel retrieval

Parallel search dramatically reduces latency.

---

## Structured outputs

Agents should return JSON.

---

## Human governance

Add approval steps for:

```
financial
legal
compliance
```

---

# Summary

Using **Azure AI Foundry NextGen workflows**, you can build enterprise multi-agent systems that include:

* multi-agent orchestration
* conditional routing
* parallel agent execution
* human-in-the-loop review
* enterprise knowledge via Azure AI Search

The visual workflow builder orchestrates these agents into a **structured execution graph**, allowing complex AI systems to run reliably in production. ([Microsoft Learn][1])

---


[1]: https://learn.microsoft.com/en-us/azure/ai-foundry/agents/concepts/workflow?view=foundry&utm_source=chatgpt.com "Build a Workflow in Microsoft Foundry"
[2]: https://learn.microsoft.com/en-us/azure/foundry/agents/overview?utm_source=chatgpt.com "What is Foundry Agent Service?"
[3]: https://github.com/Azure-Samples/get-started-with-ai-agents?utm_source=chatgpt.com "Getting Started with Agents Using Microsoft Foundry"
[4]: https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns?utm_source=chatgpt.com "AI Agent Orchestration Patterns - Azure Architecture Center"
[5]: https://learn.microsoft.com/en-us/agent-framework/workflows/human-in-the-loop?utm_source=chatgpt.com "Human-in-the-Loop Workflows"
[6]: https://devblogs.microsoft.com/foundry/introducing-multi-agent-workflows-in-foundry-agent-service/?utm_source=chatgpt.com "Introducing Multi-Agent Workflows in Foundry Agent Service"
