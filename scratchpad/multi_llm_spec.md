---

# **Design Documentation: Multi-LLM Backend for Claude CLI**

This document contains the complete product and engineering plans for adding a configurable, multi-provider backend system to the claude-code-cli.

---

# **Part 1: Product Specification**

## **Table of Contents**

1. [Executive Summary](https://www.google.com/search?q=%23executive-summary)
2. [Goals & Objectives](https://www.google.com/search?q=%23goals--objectives)
3. [User Stories](https://www.google.com/search?q=%23user-stories)
4. [Feature Requirements](https://www.google.com/search?q=%23feature-requirements)
5. [UI/UX Requirements](https://www.google.com/search?q=%23uiux-requirements)
6. [Success Criteria](https://www.google.com/search?q=%23success-criteria)
7. [Metrics & KPIs](https://www.google.com/search?q=%23metrics--kpis)

## **Executive Summary**

This feature introduces a configurable backend system for the claude-code-cli, allowing users to direct API requests to multiple Large Language Model (LLM) providers beyond the default. The primary value is providing users with flexibility, cost control, and performance optimization by enabling the use of managed services like Cerebras or cost-effective, self-hosted solutions on Vast.ai and RunPod with enterprise-grade caching. Success is defined by the CLI's ability to seamlessly switch between these backends and return valid LLM responses for each configured provider.

## **Goals & Objectives**

### **Primary Goals**

* **Business Goal:** Reduce operational and development costs by up to 80% by shifting high-volume, repetitive tasks from premium SaaS LLMs to cached, self-hosted endpoints.
* **User Goal:** Empower users to select the optimal LLM backend based on their specific needs for performance (SaaS), cost (Vast.ai), or reliability (RunPod).
* **User Goal:** Enable access to specialized models like Qwen3-Coder that may not be available through the default provider.

### **Secondary Goals**

* **Resilience:** Create a system that can failover to an alternative backend if the primary provider is down.
* **Developer Experience:** Establish a modular architecture that allows new LLM providers to be added with minimal code changes.

## **User Stories**

1. **As a developer seeking simplicity**, I want to configure the CLI to use a Cerebras Qwen3-Coder endpoint, so that I can leverage a fully managed, high-performance service with zero setup overhead.
   * **Acceptance Criteria:**
     * \[ \] The CLI accepts a configuration pointing to the Cerebras API URL and an API key.
     * \[ \] A command successfully executes and returns a code generation response from the Cerebras endpoint.
2. **As a power user focused on cost optimization**, I want to configure the CLI to use a self-hosted Qwen3-Coder on Vast.ai with Redis Enterprise caching, so that I can dramatically reduce token costs for repeated queries.
   * **Acceptance Criteria:**
     * \[ \] The CLI accepts a configuration pointing to a self-hosted proxy URL.
     * \[ \] A command successfully executes and returns a response from the Vast.ai endpoint.
     * \[ \] A second, identical command is served from the Redis cache, confirmed by logging.
3. **As a developer prioritizing stability**, I want to configure the CLI to use a self-hosted Qwen3-Coder on RunPod with persistent storage, so that my self-hosted endpoint has higher uptime and my models persist across restarts.
   * **Acceptance Criteria:**
     * \[ \] The CLI accepts a configuration pointing to a self-hosted proxy URL on RunPod.
     * \[ \] A command successfully executes and returns a response from the RunPod endpoint.
     * \[ \] The RunPod instance can be stopped and restarted without needing to re-download the LLM.

## **Feature Requirements**

### **Functional Requirements**

1. **Configurable Backend:** The CLI must support a new configuration method (e.g., an environment variable LLM\_BACKEND\_CONFIG or a dedicated config file) to specify the active LLM backend.
2. **Request Routing:** The CLI's internal API client must interpret the configuration and route outgoing requests to the appropriate provider's endpoint.
3. **Authentication Handling:** The system must manage different authentication schemes (API keys for Cerebras, dummy keys for the self-hosted proxy).
4. **Provider Support:** The initial implementation must support three providers: Cerebras (SaaS), Vast.ai (self-hosted), and RunPod (self-hosted).

### **Non-Functional Requirements**

1. **Performance:** The overhead introduced by the routing logic should be negligible (\<50ms). End-to-end latency for self-hosted options should be under 3 seconds for a p95 response time.
2. **Security:** All secrets (API keys) must be handled securely and never logged or exposed in error messages.
3. **Usability:** Switching between backends should be achievable by changing a single configuration variable.

## **UI/UX Requirements**

This is a backend feature. The Command Line Interface (CLI) itself will not have any visual changes. All configuration will be handled via environment variables or a configuration file, as specified in the functional requirements. The user experience is defined by the ease of configuration.

## **Success Criteria**

* **Feature Complete Checklist:**
  * \[ \] CLI successfully processes requests using the Cerebras backend.
  * \[ \] CLI successfully processes requests using the Vast.ai \+ Redis backend.
  * \[ \] CLI successfully processes requests using the RunPod backend.
  * \[ \] Configuration is loaded correctly from environment variables.
* **User Acceptance Tests:**
  * \[ \] A user can successfully switch from the default backend to the Cerebras backend and get a valid response.
  * \[ \] A user can successfully deploy the self-hosted solution on Vast.ai and configure the CLI to use it.

## **Metrics & KPIs**

* **Adoption Rate:** Track the percentage of users who configure a non-default backend.
* **Performance:** Monitor average latency, p95 latency, and error rate for each supported backend.
* **Cost Savings:** Calculate the estimated monthly cost savings for users utilizing the self-hosted options versus the default SaaS provider based on usage volume.

---

---

# **Part 2: Engineering Design**

## **Table of Contents**

1. [Engineering Goals](https://www.google.com/search?q=%23engineering-goals)
2. [Engineering Tenets](https://www.google.com/search?q=%23engineering-tenets)
3. [Technical Overview](https://www.google.com/search?q=%23technical-overview)
4. [System Design](https://www.google.com/search?q=%23system-design)
5. [Implementation Plan](https://www.google.com/search?q=%23implementation-plan)
6. [Testing Strategy](https://www.google.com/search?q=%23testing-strategy)
7. [Risk Assessment](https://www.google.com/search?q=%23risk-assessment)
8. [Decision Records](https://www.google.com/search?q=%23decision-records)
9. [Rollout Plan](https://www.google.com/search?q=%23rollout-plan)
10. [Monitoring & Success Metrics](https://www.google.com/search?q=%23monitoring--success-metrics)
11. [Automation Hooks](https://www.google.com/search?q=%23automation-hooks)

## **Engineering Goals**

### **Primary Engineering Goals**

1. **Modularity:** Implement a "Strategy" design pattern for the API client, allowing new LLM providers to be added by creating a single new class, with zero changes to the core CLI logic.
2. **Reliability:** Achieve a \>99.9% successful API translation rate for the self-hosted LiteLLM proxy for all valid requests.
3. **Performance:** Ensure the self-hosted proxy adds less than 100ms of overhead to any request.

### **Secondary Engineering Goals**

* **Maintainability:** Refactor the existing API client to be more abstract and easier to test.
* **Developer Productivity:** Provide a clear, documented process for developers to add and test new LLM backends.

## **Engineering Tenets**

### **Core Principles**

1. **Simplicity**: The method for a user to switch between backends must be a single, simple configuration change.
2. **Reliability First**: The default recommendation for self-hosting will be RunPod with persistent storage due to its higher intrinsic reliability over a pure marketplace solution.
3. **Testability**: All backend client implementations must be unit-testable with mocked dependencies. An integration test suite will validate against live endpoints.
4. **Observability**: The chosen backend and the result of the API call (success, failure, latency) must be logged for debugging and performance monitoring.

## **Technical Overview**

The core of this feature is the refactoring of the CLI's API communication layer. We will introduce a BackendStrategy interface. A configuration loader will read an environment variable (e.g., LLM\_BACKEND\_CONFIG) which points to a JSON or YAML file defining the active backend and its credentials. A factory will then instantiate the correct concrete strategy (e.g., CerebrasStrategy, SelfHostedProxyStrategy). The self-hosted backends (Vast.ai, RunPod) will both use the SelfHostedProxyStrategy, which is configured to point to the appropriate URL. This proxy is the Ollama \+ LiteLLM service we've previously designed.

## **System Design**

### **Component Architecture**

Code snippet

graph TD
    subgraph "Claude Code CLI"
        A\[CLI Command\] \--\> B{Config Loader};
        B \-- reads LLM\_BACKEND\_CONFIG \--\> C\[Backend Factory\];
        C \-- instantiates \--\> D{BackendStrategy Interface};
    end

    D \--\> E\[CerebrasStrategy\];
    D \--\> F\[SelfHostedProxyStrategy\];

    subgraph "External Services"
        E \--\> G((Cerebras API));
        F \--\> H\[LiteLLM Proxy on Vast.ai/RunPod\];
        H \--\> I\[Ollama w/ Qwen3-Coder\];
        H \--\> J((Redis Enterprise API));
    end

### **API Design**

This feature introduces no new public-facing API endpoints. It modifies the CLI's *outbound* API calls. The BackendStrategy interface will define a standard method, e.g., execute\_request(prompt, options), and each implementation will be responsible for translating this call into the specific format required by its target (Cerebras, LiteLLM proxy, etc.).

### **Database Design**

The caching mechanism for self-hosted solutions will be managed by Redis Enterprise, interfaced via the LiteLLM proxy. LiteLLM has built-in support for Redis caching, so no custom database schema or logic is required. We only need to provide LiteLLM with the Redis endpoint credentials.

## **Implementation Plan**

### **AI-Assisted Timeline (Claude Code CLI)**

#### **Phase 1: Core Infrastructure (20 min \- 3 agents parallel)**

* **Agent 1 (Config):** Implements the logic to read and parse the LLM\_BACKEND\_CONFIG environment variable and config file.
* **Agent 2 (Architecture):** Defines the BackendStrategy interface and refactors the existing API client to use it. Creates a BackendFactory.
* **Agent 3 (IaC):** Creates a Terraform/Pulumi script to deploy the Ollama \+ LiteLLM server on RunPod, as this is the primary recommended self-hosted option.

#### **Phase 2: Strategy Implementation (20 min \- 2 agents parallel)**

* **Agent 4 (SaaS):** Implements the CerebrasStrategy class, including logic for API key authentication and request formatting.
* **Agent 5 (Self-Hosted):** Implements the SelfHostedProxyStrategy class, which takes a URL and dummy API key for connecting to any LiteLLM endpoint.

#### **Phase 3: Testing & Polish (20 min \- 2 agents parallel)**

* **Agent 6 (Unit Tests):** Writes unit tests for the Config Loader, Factory, and mocks for each Strategy.
* **Agent 7 (Integration Tests):** Writes an end-to-end integration test suite that can be configured to run against live Cerebras, Vast.ai, and RunPod endpoints.

**Total Estimated Time: 60 minutes**

## **Testing Strategy**

### **Unit Tests (/tdd)**

* Test the configuration loader with various valid and invalid config files.
* Test that the Backend Factory produces the correct strategy object based on the config.
* Test each BackendStrategy implementation with a mocked httpx client to ensure correct request headers, body, and URL are generated.

### **Integration Tests**

* A separate test suite will be created that reads a special test configuration (e.g., secrets.ci.json).
* This suite will contain "live fire" tests that make actual API calls to provisioned test endpoints for Cerebras, Vast.ai, and RunPod.
* These tests will be run nightly and on every merge to the main branch to detect provider API changes or regressions.

## **Risk Assessment**

### **Technical Risks**

* **High Risk**: **Self-Hosted Endpoint Instability.** Vast.ai instances can be unreliable. **Mitigation**: Strongly recommend RunPod Secure Cloud with persistent storage as the primary self-hosting option. Implement connection timeouts and retries in the SelfHostedProxyStrategy.
* **Medium Risk**: **Provider API Divergence.** Cerebras and the OpenAI-compatible API from LiteLLM may change. **Mitigation**: The nightly integration test suite will immediately detect breaking changes. The BackendStrategy pattern isolates the impact of any change to a single class.
* **Low Risk**: **Credential Leakage.** **Mitigation**: Enforce the use of environment variables for all secrets and ensure no secrets are ever logged.

## **Decision Records**

### **Architecture Decisions**

**\*\*Decision\*\***: Use the Strategy Design Pattern for backend communication.
**\*\*Date\*\***: 2025-08-03
**\*\*Context\*\***: The CLI needs to support multiple, swappable API backends with different authentication and request formats.
**\*\*Options\*\***: 1\) A large \`if/else\` block in the API client. 2\) The Strategy Pattern.
**\*\*Rationale\*\***: The Strategy Pattern is vastly more modular, scalable, and testable. Adding a new provider requires adding one new file, not modifying a complex conditional block.
**\*\*Consequences\*\***: Slightly more initial setup work to define the interface and factory.

**\*\*Decision\*\***: Use LiteLLM as the standard proxy for all self-hosted models.
**\*\*Date\*\***: 2025-08-03
**\*\*Context\*\***: We need a way to make self-hosted Ollama models compatible with clients expecting a standard API format.
**\*\*Options\*\***: 1\) Build a custom Flask/FastAPI proxy. 2\) Use LiteLLM.
**\*\*Rationale\*\***: LiteLLM is a production-ready, open-source tool specifically designed for this purpose. It supports caching, multiple backends, and a standard OpenAI-compatible API out of the box, saving significant development time.
**\*\*Consequences\*\***: Adds a dependency on the LiteLLM project.

## **Rollout Plan**

1. **Phase 1 (Internal Release):** The feature will be merged but disabled by default. It can be enabled by setting an environment variable ENABLE\_MULTI\_BACKEND=true.
2. **Phase 2 (Power-User Beta):** Document the new feature in advanced documentation and invite power users to test it. Gather feedback on the setup process for self-hosted options.
3. **Phase 3 (General Availability):** Once stable, enable the feature by default and update the main user documentation.

## **Monitoring & Success Metrics**

* **Logging:** The CLI will log which backend strategy is being used for each command invocation.
* **Performance Monitoring:** The CLI will log the end-to-end latency of each API call. This data can be optionally collected from users to build performance dashboards.
* **Error Tracking:** All API failures, connection errors, or timeouts will be logged with context, including which backend was used.

## **Automation Hooks**

### **CI/CD Integration**

* A GitHub Actions workflow will trigger on every Pull Request.
* **Unit Tests:** The workflow will run the full unit test suite.
* **Integration Tests:** For PRs merged to main, the workflow will run the integration test suite against live, sandboxed endpoints. A failure will trigger an alert.
* **Security:** A secret scanning tool will be run to ensure no credentials have been accidentally committed.
