# GCP Agents - Summoner

[![Google Cloud](https://img.shields.io/badge/Google_Cloud-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white)](https://cloud.google.com/)
[![Python](https://img.shields.io/badge/Python_3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![CI](https://img.shields.io/github/actions/workflow/status/TirtheshJani/GCP-Agents---Summoner/ci.yml?style=for-the-badge&label=CI)](https://github.com/TirtheshJani/GCP-Agents---Summoner/actions)

> An extensible AI agent framework built on Google Cloud Platform.  
> Agents follow a **plan-execute-reflect** lifecycle and integrate natively with Vertex AI, Cloud Storage, Pub/Sub, and Firestore.

---

## Features

- **Plan-Execute-Reflect loop** -- every agent follows a structured lifecycle with built-in retry logic.
- **Vertex AI integration** -- generate text with Gemini models out of the box.
- **GCP-native tools** -- thin wrappers for Cloud Storage, Pub/Sub, and Firestore.
- **In-memory & Firestore memory** -- agents persist state across tasks.
- **CLI interface** -- run agents from the command line with [Click](https://click.palletsprojects.com/) + [Rich](https://rich.readthedocs.io/).
- **Fully tested** -- unit tests with mocked GCP clients (no credentials required to run).

---

## Architecture

```
                         +---------------------+
                         |     CLI (main.py)   |
                         +----------+----------+
                                    |
                         +----------v----------+
                         |     BaseAgent       |
                         |  plan -> execute    |
                         |     -> reflect      |
                         +----+----------+-----+
                              |          |
                 +------------+--+  +----+-------------+
                 | ResearchAgent |  | DataProcessing   |
                 | (Vertex AI)   |  | Agent (GCS ETL)  |
                 +-------+------+  +-----+-------------+
                         |                |
              +----------v----------------v----------+
              |          GCP Tool Layer              |
              |  VertexAITool  CloudStorageTool      |
              |  PubSubTool    FirestoreTool         |
              +--------------------------------------+
```

### Agent Lifecycle

Every agent that extends `BaseAgent` follows three steps:

| Step | Method | Purpose |
|------|--------|---------|
| 1 | `plan(task)` | Decide *what* to do |
| 2 | `execute(plan)` | Carry out the plan (call APIs, models, tools) |
| 3 | `reflect(task, result)` | Evaluate the result; retry if unsatisfied |

The `run()` method orchestrates this loop with automatic retries via [tenacity](https://tenacity.readthedocs.io/).

---

## Project Structure

```
GCP-Agents---Summoner/
|-- agents/
|   |-- __init__.py
|   |-- base_agent.py              # Abstract base agent + MemoryStore
|   +-- specialized_agents/
|       |-- __init__.py
|       |-- research_agent.py      # Vertex AI research agent
|       +-- data_processing_agent.py  # GCS ETL agent
|-- config/
|   |-- __init__.py                # Settings loader (YAML + env vars)
|   +-- agent_config.yaml          # Default configuration
|-- tools/
|   |-- __init__.py
|   +-- gcp_tools.py               # VertexAI, GCS, Pub/Sub, Firestore wrappers
|-- tests/
|   |-- test_base_agent.py         # Agent lifecycle tests
|   |-- test_config.py             # Configuration tests
|   +-- test_gcp_tools.py          # GCP tool tests (mocked)
|-- examples/
|   +-- quickstart.py              # Run a custom agent locally
|-- main.py                        # CLI entry point
|-- requirements.txt               # Production dependencies
|-- requirements-dev.txt           # Dev/test dependencies
|-- CONTRIBUTING.md
|-- LICENSE
+-- README.md
```

---

## Getting Started

### Prerequisites

- Python 3.9+
- A GCP project with billing enabled (for cloud features)
- `gcloud` CLI installed and authenticated

### Installation

```bash
# Clone the repository
git clone https://github.com/TirtheshJani/GCP-Agents---Summoner.git
cd GCP-Agents---Summoner

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Copy the default config and set your GCP project:

```bash
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-central1"            # optional, defaults to us-central1
```

All settings live in `config/agent_config.yaml` and support `${ENV_VAR:default}` substitution. See `config/__init__.py` for the full schema.

### Quick Test (no GCP credentials needed)

```bash
python examples/quickstart.py
```

This runs a local `SummaryAgent` that demonstrates the plan-execute-reflect lifecycle without calling any cloud services.

---

## Usage

### CLI Commands

```bash
# Research a topic using Vertex AI
python main.py research "What are the latest trends in LLM agents?"

# Process files in a GCS bucket
python main.py process --prefix raw-data/

# View current configuration
python main.py config
```

### Building a Custom Agent

```python
from agents.base_agent import BaseAgent


class GreeterAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "greeter"

    def plan(self, task: str) -> str:
        return f"Greet the user about: {task}"

    def execute(self, plan: str) -> str:
        return f"Hello! {plan}"


agent = GreeterAgent()
result = agent.run("welcome message")
print(result.output)  # "Hello! Greet the user about: welcome message"
```

---

## Tech Stack

| Category | Technology | Purpose |
|----------|-----------|---------|
| **Cloud** | Google Cloud Platform | Infrastructure & AI services |
| **AI/ML** | Vertex AI (Gemini) | Text generation for agents |
| **Storage** | Cloud Storage | File-based data processing |
| **Messaging** | Pub/Sub | Agent-to-agent communication |
| **Database** | Firestore | Agent memory & state persistence |
| **Language** | Python 3.9+ | Core framework |
| **CLI** | Click + Rich | Command-line interface |
| **Config** | Pydantic + YAML | Type-safe configuration |
| **Testing** | pytest | Unit & integration tests |
| **CI** | GitHub Actions | Lint + test on push/PR |

---

## Development

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=agents --cov=tools --cov=config -v

# Lint & format
ruff check .
ruff format .
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for more details.

---

## Roadmap

- [x] Base agent framework with plan-execute-reflect lifecycle
- [x] Vertex AI, Cloud Storage, Pub/Sub, Firestore tool wrappers
- [x] Research agent and data processing agent
- [x] CLI interface
- [x] Unit tests with mocked GCP clients
- [x] GitHub Actions CI
- [ ] Multi-agent orchestration and task routing
- [ ] Firestore-backed persistent memory store
- [ ] Cloud Run deployment with Dockerfile
- [ ] Streaming agent responses
- [ ] Agent observability dashboard

---

## License

This project is licensed under the MIT License -- see the [LICENSE](LICENSE) file for details.

---

## Contact

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/tirthesh-jani)
[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/TirtheshJani)
