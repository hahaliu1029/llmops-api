from langchain_core.runnables import RunnablePassthrough, RunnableLambda

counter = -1


def func(x):
    global counter
    counter += 1
    print(f"func {counter}")
    return x / counter


chain = (
    RunnableLambda(func).with_retry(stop_after_attempt=2)
    | RunnablePassthrough()
    | RunnableLambda(func)
)

res = chain.invoke(2)

print(res)
