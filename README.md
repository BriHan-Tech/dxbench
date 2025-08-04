# DXBench

A benchmark for evaluating LLMs on how well they can improve the developer experience.

One thing that developers hate is writing tests, so this benchmark evaluates how well LLMs are able to write tests for different features developers are working on.

## Evaluate Your LLM

To evaluate your LLM on this benchmark:

1. Install the `dxbench` package from pip: `pip install dxbench`
2. Setup your LLM by implementing the `Bot` class
3. Run the benchmark by: `run(your_bot)`

Here is an example:

```
from dxbench.bot import Bot
from dxbench.runner import run


class TestBot(Bot):
    def get_response(self, prompt: str) -> str:
        # Get your response here
        return response


bot = TestBot()
run(bot)

```

## Contribute Test Cases

To contribute test cases, please:

1. Fork this repository
2. Install the dev packages: `pip install ".[dev]"`
3. Add a function that should be tested in `dxbench/cut`. Make sure that your code is runnable!
4. Register your code in `dxbench/registry.py`
