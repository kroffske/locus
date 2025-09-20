# LLM-Driven Development Templates & Guide

## LLM-Oriented Template Code (Python)

```python
from dataclasses import dataclass
from typing import List, Optional

# Core Layer: Data models and logic functions
@dataclass
class Plan:
    """Represents a plan of action with a sequence of steps."""
    steps: List[str]  # e.g., list of step descriptions

@dataclass
class TestResults:
    """Outcome of running tests on the code."""
    success: bool
    failures: Optional[List[str]] = None

    def summary(self) -> str:
        """Return a summary of test results."""
        if self.success:
            return "All tests passed."
        else:
            detail = f"{{len(self.failures)}} failures" if self.failures else "Unspecified failures"
            return f"Tests failed: {{detail}}"

def analyze_requirements(requirements: str) -> Plan:
    """Analyze requirements and produce a high-level Plan."""
    # 1. Parse and clarify the requirements.
    # 2. Identify sub-tasks or components needed to fulfill requirements.
    # 3. Formulate an ordered list of implementation steps.
    # NOTE: This function focuses on analysis only (no coding). If using an LLM,
    # instruct it to *not* write code yet, only to outline a solution.
    # TODO: Implement analysis logic or integrate an LLM call to generate the Plan.
    raise NotImplementedError

def implement_plan(plan: Plan) -> str:
    """Implement the solution according to the Plan. Returns code as a string."""
    # For each step in the plan, write the corresponding code.
    # Ensure each step's code is implemented in the appropriate function/file.
    # Fail-fast: if a step cannot be implemented, raise an error instead of returning partial code.
    # NOTE: Keep implementation focused and atomic. Avoid broad exception handling; let errors propagate.
    # TODO: Integrate LLM code generation for each plan step or call internal helper functions.
    raise NotImplementedError

def run_tests(code: str) -> TestResults:
    """Execute tests against the provided code and return the results."""
    # This function should run the project's test suite on the new code.
    # If using an AI agent, instruct it to run `pytest` or relevant test commands and capture results.
    # Only catch exceptions related to test execution (e.g., syntax errors) if needed, and otherwise fail-fast.
    # TODO: Implement actual test runner integration or simulate test results for the given code.
    raise NotImplementedError

def generate_documentation(code: str) -> str:
    """Generate documentation for the given code (e.g. README updates or docstrings)."""
    # Analyze the code to extract public interfaces and behaviors.
    # Produce markdown or docstring text explaining usage, parameters, and examples.
    # TODO: Use an LLM to draft documentation or parse code comments to assemble documentation.
    raise NotImplementedError

# Formatting Layer: Prompt and output formatting functions
def format_prompt_for_plan(requirements: str) -> str:
    """Create a prompt for an LLM to generate a plan from requirements."""
    return (
        "You are a senior software planner.\n"
        f"Project requirements:\n{{requirements}}\n\n"
        "Develop a step-by-step implementation plan *without writing code*. "
        "Focus on clarity and completeness of the plan."
    )

def parse_plan_from_response(response: str) -> Plan:
    """Parse the LLM's response into a Plan object."""
    # Assuming the LLM returns an ordered list of steps in text form.
    steps = []
    for line in response.splitlines():
        line = line.strip("- *1234567890. ")  # strip list markers
        if line:
            steps.append(line)
    # TODO: Adapt parsing as needed based on the LLM's actual format.
    return Plan(steps=steps)

def format_prompt_for_code(plan: Plan) -> str:
    """Create a prompt for an LLM to generate code based on a Plan."""
    steps_text = "\n".join(f"{{i+1}}. {{step}}" for i, step in enumerate(plan.steps))
    return (
        "Implement the following plan step by step in code:\n"
        f"{{steps_text}}\n\n"
        "Provide the complete code for the implementation. "
        "Ensure the code is well-structured and follows our style guidelines."
    )

# Orchestration Layer: High-level workflow coordination
def solve_task(requirements: str) -> str:
    """Orchestrate the end-to-end process from requirements to tested, documented code."""
    # Step 1: Analyze requirements to get a plan
    plan = analyze_requirements(requirements)
    if not plan or not plan.steps:
        raise RuntimeError("Analysis failed to produce a plan. Aborting.")

    # Step 2: Implement the plan to get code
    code = implement_plan(plan)
    if code is None or code.strip() == "":
        raise RuntimeError("Implementation produced no code. Aborting.")

    # Step 3: Test the code
    results = run_tests(code)
    if not results.success:
        raise RuntimeError(f"Test failures encountered: {{results.summary()}}")

    # Step 4: Generate documentation for the code
    documentation = generate_documentation(code)
    # (Optional) Combine code and documentation for output or further processing
    # For example, append documentation as comments or separate file.
    # TODO: Decide how to utilize `documentation` (e.g., write to README or include in output).

    return code  # Returning the code (the documentation can be returned or applied elsewhere)
```

In this template: We define clear **Core** functions for analysis, implementation, testing, and documentation generation. Each function has a single, well-defined purpose with explicit inputs and outputs (using type hints). We include #TODO comments where project-specific logic or integration (e.g. actual LLM calls, test runners) should be added. Inline notes guide an AI developer to follow best practices (e.g. plan first, avoid broad try/except, fail fast on errors). The **Formatting** layer handles prompt construction and parsing separately, keeping prompt logic isolated from core logic. Finally, an **Orchestration** function `solve_task` ties the steps together, enforcing the analyze → plan → code → test → document sequence and performing validations at each stage to avoid error-hiding or partial progress.

## AGENTS.md – Prompt Design & Architecture Guide

**Project AI Assistant Guide** – This file provides context and guidelines to help AI coding agents (OpenAI Codex, Anthropic Claude, Cursor, etc.) work effectively on this codebase. (Think of it as a README for AI agents.) It covers our development workflow, code structure, best practices, and preferred prompt patterns.

### Workflow: Analyze → Plan → Code → Test → Document

Our development workflow is structured into distinct phases that the AI agent should follow for each task:

1. **Analyze** – Carefully examine the requirements or problem. Identify what is being asked and clarify any ambiguities. The agent should not jump into coding at this stage; instead, it should gather context and possibly ask clarifying questions. (This corresponds to Anthropic's explore phase¹, ensuring the problem is well-understood before proceeding.)

2. **Plan** – Devise a step-by-step solution strategy before writing any code. Outline the components or functions needed, and how they interact. We explicitly instruct the agent not to write code yet during planning – just produce a clear plan (this prevents the model from rushing ahead). Planning first significantly improves results on complex tasks². The plan can be presented in a simple list format (even saved to a .md file for reference). Rationale: Upfront planning is crucial; without it, the AI may dive into coding blindly, whereas a verified plan guides focused implementation³.

3. **Code** – Implement the solution according to the approved plan. Write code for each step in a modular, incremental way. The agent should create or modify functions as needed, following the single-responsibility principle (each function does one thing). It should adhere to our style guidelines (naming, formatting) and fail fast if something is wrong (e.g. raise errors rather than continuing with bad state). This phase corresponds to actually coding the solution once the plan is validated. The agent should also self-check its work as it goes, verifying that each part of the code makes sense before moving on.

4. **Test** – After coding, run the automated tests or perform checks on the new code. The agent should execute the project's test suite (e.g. via pytest or relevant commands) and report the results. If any tests fail or new issues arise, the agent should stop and fix them before proceeding (do not ignore test failures). This iterative test-fix cycle continues until all tests pass. Note: Having a clear test target helps the AI verify correctness and is a recommended practice for AI-assisted coding⁴. If writing tests is part of the task, the agent should write tests in an earlier step, confirm they fail, then implement code to make them pass (a test-driven approach)⁵.

5. **Document** – Finally, generate or update documentation. The agent should add or update docstrings, README sections, or other docs to explain the changes and usage of the new code. This includes describing the purpose of new modules or functions and providing examples if helpful. By documenting at the end, we ensure the implementation and its intended use are clearly recorded. (This aligns with updating README/changelogs in Anthropic's workflow, where after coding, the agent updates documentation with what changed⁶.)

Following this analyze → plan → code → test → document cycle enforces discipline in the AI's workflow. It mirrors proven iterative development practices (Anthropic's internal guide describes a similar "explore, plan, code, commit" loop⁷, generalizable to any coding agent). Adhering to these phases step-by-step helps prevent errors and omissions, leading to more reliable outcomes.

### Layered Architecture and Task Separation

Our codebase is organized into layered components to separate concerns cleanly:

• **Core Layer (Logic)**: This contains the primary business logic and data models. Core functions perform computations or manipulate data without concerning themselves with input/output formatting or external interactions. Each core function has a clear purpose and does not implicitly depend on global state or config. For example, a function `process_data(input)` should directly return its result or raise an error – it should not print output or catch unrelated exceptions. This separation makes core logic easier to test and reuse.

• **Formatting Layer (Interface/Phrases)**: This layer handles how we communicate with the LLM or format data in/out. For instance, constructing prompt strings for the AI (`format_prompt_for_plan`) and parsing the AI's responses (`parse_plan_from_response`) are done here. Keeping prompt construction in its own functions means if the prompt format needs to change (say, a different model or style), we update it in one place. It also prevents cluttering core logic with prompt strings.

• **Orchestration Layer (Workflow Coordination)**: High-level functions or controllers (like `solve_task`) live here, steering the overall process. Orchestration functions call the core logic and formatting functions in sequence, implementing the workflow described above. They make sure each stage's output is handled properly (e.g., if planning returns no steps, the orchestrator will stop and raise an error rather than proceeding). This layer may also handle integration with external tools (running tests, committing code, etc.), but always by coordinating calls to lower-layer functions rather than doing the work itself.

Each layer has a single responsibility and clear boundaries. By strictly separating tasks, we avoid mixing, for example, prompt-generation code inside a core logic function or business logic inside the orchestration flow. This makes the code more maintainable and easier for both humans and AI to navigate. In fact, Anthropic's guidance suggests using distinct "sub-agents" or phases for different tasks (exploration vs implementation) – our architecture reflects a similar separation of concerns⁸. Maintaining this structure consistently prevents architecture drift, where ad-hoc code changes could blur these boundaries over time. Whenever extending functionality, determine which layer it belongs to (e.g., a new output format goes into Formatting, a new calculation goes into Core, a new multi-step process goes into Orchestration) and implement it in the appropriate place. This discipline keeps the project coherent and ensures the AI works within a predictable framework.

### Best Practices and Anti-Patterns

To ensure code quality and consistency, the following guidelines highlight patterns to avoid ("Bad") and the preferred approach ("Good"). The AI agent should abide by these when generating or modifying code:

• **Avoid Dynamic Introspection (e.g. getattr misuse)** – Bad: Using `getattr` or similar reflection to call functions or access attributes dynamically by name can make code harder to understand and prone to errors. For example:

```python
# Bad: dynamically calling a method by constructed name
action = "delete"
getattr(self, f"{{action}}_item")()  # calls delete_item(), or fails silently if not found
```

This implicit magic is discouraged. It hides functionality behind strings and can fail unpredictably. Instead, use explicit logic or direct mappings. Good:

```python
# Good: explicit dispatch via a dictionary (or simple if/elif)
def delete_item(self): ...
def create_item(self): ...

actions = {{"delete": self.delete_item, "create": self.create_item}}
if action in actions:
    actions[action]()
else:
    raise ValueError(f"Unknown action: {{action}}")
```

Here, the code's intent is clear and typos or invalid actions are caught explicitly. In general, explicit is better than implicit – code should not be "hidden behind obscure language" or reflection⁹. Prefer clarity even if it means a bit more verbosity.

• **Avoid Broad Exception Handling** – Bad: Catching all exceptions with a blanket `try/except Exception` (or even worse, a bare `except:`) and then doing nothing or just logging can hide errors:

```python
try:
    result = do_critical_operation()
except Exception as e:
    print("Error occurred:", e)  # Swallows all exceptions, potentially hiding issues
    return None  # (or pass, or some marker)
```

This is an anti-pattern because it turns bugs or unexpected conditions into silent failures. The code above would proceed as if things are fine, making debugging very difficult. Instead, handle exceptions in a targeted way or let them propagate. Good: Catch specific exceptions that you expect and know how to handle, and let others bubble up:

```python
try:
    result = do_critical_operation()
except SpecificError as e:
    handle_specific_error(e)
    # (maybe return a safe default or re-raise after logging)
```

If a problem is truly non-recoverable, it's often better to let the exception halt execution than to continue in a corrupt state. As the Zen of Python says, "Errors should never pass silently… unless explicitly silenced." In other words, don't blanket-catch everything only to ignore it; failing fast is preferable to running with hidden errors¹⁰.

• **Never Return None for Normal Errors** – Bad: Returning `None` (or a magic value) from a function to signal an error, and then expecting the caller to check for it:

```python
def find_user(username) -> User:
    user = db.lookup(username)
    if not user:
        return None  # signal not found
    return user

user = find_user("alice")
if not user:
    print("User not found")  # Could also catch other falsy cases by accident
```

This approach can lead to silent failures if the `None` is not handled everywhere, or if a valid result could coincidentally be falsy (empty string, 0, etc.). The intent is implicit and can be overlooked. Good: Raise an exception to indicate the error, or use a dedicated error type. For example:

```python
def find_user(username) -> User:
    user = db.lookup(username)
    if not user:
        raise UserNotFoundError(f"User '{{username}}' not found")
    return user
```

Now a missing user is an explicit error condition, not a vague `None` that might be ignored. This way, a program will crash rather than continue in an unknown state, which is easier to debug and aligns with Python's philosophy that a silent error (like returning None) is worse than a loud one¹⁰. The only time returning `None` might be acceptable is if `None` is a valid result with clear meaning – even then, document it. But for error cases, use exceptions or distinct error values.

• **Minimize Global Config and Implicit State** – Bad: Over-reliance on a global configuration object or global variables:

```python
# Global config dict used everywhere
CONFIG = {{"threshold": 5, "mode": "fast"}}

def check_value(x):
    # uses global CONFIG implicitly
    if x > CONFIG["threshold"]:
        ...
```

This makes functions dependent on external state that isn't obvious from their signature, and changes in global config can unpredictably affect behavior. It also hinders reuse (you can't easily use `check_value` with a different threshold without modifying global state). Good: Pass explicit parameters or use dependency injection:

```python
def check_value(x, threshold=5):
    if x > threshold:
        ...
```

Now the function's behavior is fully determined by its inputs, which is clearer and easier to test. If there is a lot of configuration, consider grouping them in a dataclass or object and passing that in, so it's still explicit. The key is to avoid "spooky action at a distance" where a function's outcome depends on invisible external settings. Each function should behave transparently given its arguments.

• **Avoid Code Duplication (DRY Principle)** – Don't repeat yourself. Bad: copying and pasting blocks of code in multiple places:

```python
def calculate_discount(order):
    # apply tax
    total = order.subtotal * 1.08
    # apply coupon
    if order.coupon:
        total *= (1 - order.coupon.discount)
    return total

def calculate_total_order_value(order):
    # apply tax
    total = order.subtotal * 1.08
    # apply coupon
    if order.coupon:
        total *= (1 - order.coupon.discount)
    # add shipping
    return total + order.shipping_fee
```

The tax and coupon logic is duplicated in two functions. This is problematic because any change (say the tax rate, or adding a new coupon rule) requires updating multiple places, with the risk of inconsistency. Good: Refactor the common logic into a shared helper:

```python
def apply_tax_and_coupon(subtotal, coupon=None) -> float:
    total = subtotal * 1.08  # tax
    if coupon:
        total *= (1 - coupon.discount)
    return total

def calculate_discount(order):
    return apply_tax_and_coupon(order.subtotal, order.coupon)

def calculate_total_order_value(order):
    total = apply_tax_and_coupon(order.subtotal, order.coupon)
    return total + order.shipping_fee
```

Now the tax and coupon calculation lives in one place, and both functions use it. This satisfies the DRY (Don't Repeat Yourself) principle, which aims to reduce repetition of knowledge in code¹¹. The system is easier to maintain since each piece of information (like how tax is applied) has a single authoritative implementation. As a bonus, the code is shorter and clearer.

In summary, the AI agent should produce clean, maintainable code by following these practices. Do not use reflection or dynamic tricks when a simple, explicit approach works. Do not catch or ignore errors indiscriminately – handle what you expect and let the rest surface (with meaningful errors). Make the control flow obvious, and keep functions and logic de-duplicated. By adhering to these guidelines, we avoid common pitfalls like hidden bugs, confusing code, or regression caused by one change not propagating everywhere. The result is code that is easier for humans to understand and for AI to safely modify in the future.

### Prompt Patterns for Effective AI Assistance

Below are some reusable prompt snippets and strategies to get the most out of AI coding assistants, aligned with our workflow and best practices. These can be used when interacting with the AI (in commit messages, PR comments, or chat instructions) to guide it:

• **"Analyze the requirements before coding."** – Use this instruction to remind the agent to start with analysis. For example: "Please analyze the above feature request and list the key tasks or questions before writing any code." This yields an outline of the problem and ensures the AI has a correct understanding. It corresponds to the Analyze phase and prevents hasty coding.

• **"Outline a step-by-step plan (no code yet)."** – Explicitly ask the AI to produce a plan. For instance: "Create a detailed implementation plan for this feature in bullet points, and do not write any code yet." This prompt forces the planning step. Many AI tools (Cursor, Claude, etc.) respond well to this: they will output a Markdown list of steps. Ensuring the instruction "no code yet" is included is important – it triggers an extended reasoning mode (Claude even has special handling for the word "think" to allocate more planning time¹²). This way we get a clear plan we can review or even commit as `PLAN.md`. For example, one might say: "Plan the solution as a series of steps in a PLAN.md file. Don't implement anything yet."¹³.

• **"Implement step X of the plan."** – Focus the AI on one sub-task at a time. You can say: "Now implement step 3 of the plan: 'Add the new API endpoint for retrieving user data'." By specifying a single step, the agent stays on track and doesn't stray into unrelated parts. In Cursor, a common workflow is to tell the AI something like "Work on task 3, then stop and report back." This ensures incremental progress and allows for review after each chunk. It's essentially instructing the agent to code in small pieces, which reduces errors and makes it easier to pinpoint any issues that arise.

• **"Run the tests and fix any failures."** – After code generation, prompt the AI to run the project's tests (if the tool supports execution) or to simulate running them. For example: "Run pytest and report if anything fails." In AI agents like Claude Code, you can explicitly instruct the agent to run tests; it will then execute them and provide output¹⁴. If failures occur, you can follow up with "Based on the failing test output, fix the code." This uses the agent to do the heavy lifting in debugging. Instructing the AI to focus on test results will guide it to address the exact failures rather than guessing. Always make sure to say something like "do not proceed until tests are passing" – this aligns the agent with our fail-fast philosophy.

• **"Update documentation to reflect these changes."** – Once code changes are complete (tests passing), ask the AI to produce documentation. For instance: "Summarize the above changes and update the README and docstrings accordingly." This can yield a nicely formatted Markdown that you can put into README.md or inline comments. The agent might need guidance on what level of detail to include (e.g. usage examples, any config changes, etc.). Because we explicitly list this as a final step, the AI will treat documentation as a first-class part of the task, not an afterthought. This is supported by many agents – for example, Claude can be instructed at commit time to also update docs¹⁵.

• **"Process my comments."** – When collaborating with Codex (especially via GitHub or VS Code), a powerful pattern is to do a code review on the AI's draft and annotate fixes (e.g. "// TODO: rename this variable for clarity" in code, or review comments on a PR). Then you simply tell the AI: "Process my comments." Codex will read your review notes and apply the changes in one go¹⁶. This snippet saves you from manually fixing what the AI can handle. It's critical that your comments are specific (e.g. "This function is too long, split it into two."), and the "process my comments" instruction triggers the agent to incorporate all those changes in the next iteration.

• **"Think step-by-step / Think harder.*"** – When you sense the problem is complex or the AI's first attempt was too superficial, you can encourage deeper reasoning. Phrases like "Let's think this through step by step" (in chat) or using Claude's special modes ("think", "think hard", "ultrathink") in a prompt can significantly improve the quality of the solution by having the AI allocate more time to reasoning¹². For example, you might prompt Claude: "Think harder about edge cases and design before coding." This usually leads to the AI enumerating considerations or exploring alternatives, which can prevent mistakes. It's essentially a way to invoke a more exhaustive Chain-of-Thought from the model.

By using these prompt patterns, we ensure the AI agent stays aligned with our development process. They help invoke the right behavior from Codex, Claude, Cursor, or others – these systems all respond well to clear, staged instructions. The goal is to have the AI function like a diligent junior developer: first understanding the task, then planning, then coding carefully, testing, and documenting – all while following our architectural conventions and coding standards. This guide (AGENTS.md) serves as both a reference for developers and as an in-context set of instructions for AI agents (many agents automatically consult this file). By maintaining it as a single source of truth for AI guidance, we can work seamlessly across different AI coding tools without duplicating instructions in multiple places¹⁷.

**Conclusion:** Adhering to the patterns and practices described above will result in consistent, high-quality contributions from AI agents. We avoid error-hiding, reduce code duplication, and prevent architectural drift by design. Both human developers and AI assistants should follow this guide to ensure we build software that is reliable, understandable, and easy to evolve. By analyzing and planning first, coding with clear structure, testing thoroughly, and documenting, we harness the strengths of AI while maintaining strict software engineering discipline. Let's build with confidence and clarity, together with our AI tools.

---

### References

1. [Best Practices for Coding with OpenAI Codex | by Ronny Roeller | NEXT AI Engineering | Medium](https://medium.com/collaborne-engineering/best-practices-for-coding-with-openai-codex-6907ba6f7596)
2. [Claude Code Best Practices \ Anthropic](https://www.anthropic.com/engineering/claude-code-best-practices)
3. [Anthropic Just Dropped an AI Coding Playbook — And It's Surprisingly Useful Beyond Claude | by Cloudperceptor | Medium](https://cloudperceptor.medium.com/anthropic-just-dropped-an-ai-coding-playbook-and-its-surprisingly-useful-beyond-claude-89a405dc2fa7)
4. [Lessons from the Zen of Python | DataCamp](https://www.datacamp.com/blog/lessons-from-the-zen-of-python)
5. [Don't repeat yourself - Wikipedia](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself)
6. [Do proper planning, rock on with 3.7 : r/cursor](https://www.reddit.com/r/cursor/comments/1jb2tk3/do_proper_planning_rock_on_with_37/)
7. [AGENTS.md](https://agents.md/)