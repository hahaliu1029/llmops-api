import time

from langchain_core.runnables import RunnableLambda, RunnableConfig
from langchain_core.tracers.schemas import Run


def on_start(run_obj: Run, config: RunnableConfig) -> None:
    print(f"Starting... with config: {config}")
    print(f"Run object: {run_obj}")
    print("==================")


def on_end(run_obj: Run, config: RunnableConfig) -> None:
    print(f"Ending... with config: {config}")
    print(f"Run object: {run_obj}")
    print("==================")


def on_error(run_obj: Run, config: RunnableConfig) -> None:
    print(f"Error... with config: {config}")
    print(f"Run object: {run_obj}")
    print("==================")


runnable = RunnableLambda(lambda x: time.sleep(x)).with_listeners(
    on_start=on_start,
    on_end=on_end,
    on_error=on_error,
)

chain = runnable

chain.invoke(
    2,
    config={
        "configurable": {
            "name": "RunnableLambda",
        }
    },
)
