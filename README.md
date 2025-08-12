# SecureDev-Bench

*A benchmark for the modern AI security agent.*

---

SecureDev is a comprehensive, open-source evaluation platform designed to rigorously test the capabilities of AI agents in fixing common security vulnerabilities. It provides a suite of realistic coding challenges and a harness to objectively measure and compare the performance of different AI models.

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Code of Conduct](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](CODE_OF_CONDUCT.md)

---
![showcase](/docs/assets/screenshot.png)

## Key Features

* **Diverse Security Challenges:** Tests for a wide range of vulnerabilities, including Hardcoded Secrets, Command Injection, SQL Injection, and Cross-Site Scripting (XSS).
* **Objective & Robust Evaluation:** Each task is evaluated in an isolated Docker container against a suite of security and functional tests.
* **Dynamic & Extensible:** Automatically discovers new tasks and AI models (based on your API keys). The platform is designed to be easily extended.
* **Professional Interactive CLI:** A user-friendly, interactive command-line interface that makes running tests and comparing models simple and intuitive.
* **Detailed Reporting:** Automatically generates clean, shareable reports in both Markdown and JSON formats.

## Getting Started

### Prerequisites

* Python 3.9+
* Docker
* Git

### Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/samcodesign/securedev-bench.git
    cd securedev-bench
    ```

2. **Create and activate a virtual environment:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. **Install the required dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4. **Set up your API keys:**
    Create a `.env` file in the project root (you can copy the example):

    ```bash
    cp .env.example .env
    ```

    Then edit `.env` and add your API keys.

## Usage

Run the interactive benchmark CLI:

```bash
python run_benchmark.py
```

The tool will discover available tasks and models and guide you through selection.

For non-interactive usage and additional options:

```bash
python run_benchmark.py --help
```

## Documentation

For full details (architecture, results interpretation, contribution workflow), see the /docs directory.

Topics include:

* [How to Add a New Task](/docs/01-adding-tasks.md)
* [How to Add a New AI Provider](/docs/02-adding-providers.md)
* [Project Architecture](/docs/03-architecture.md)
* [Cli Reference](/docs/07-cli-reference.md)
* [Interpreting the Results](/docs/04-interpreting-results.md)
* [Credibility Shield](/docs/06-credibility-shield.md)
* [Contribute](/docs/05-contribute.md)

### Contributing

Contributions are welcome. Please review the guides in /docs before submitting changes. All contributors must follow the [Code of Conduct](/CODE_OF_CONDUCT.md).

### License

This project is licensed under the GNU General Public License v3.0. See the [LICENSE](/LICENSE) file for details.
