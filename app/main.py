from uuid import uuid4
import asyncio

from fastapi import FastAPI, BackgroundTasks
import aioredis


async def wait_for_cancel(conn: aioredis.Connection, task_id: str):
    """ This waits for a task cancellation message. Does not check if the task is
        actually valid.
    """
    return await conn.brpop(f"cancel-{task_id}")


async def cancel_task(conn: aioredis.Connection, task_id: str):
    """ Send a task cancellation message. Does not check if the task is
        actually valid.
    """
    return await conn.lpush(f"cancel-{task_id}", "cancel")


async def long_running_task(conn: aioredis.Connection, task_id: str):
    """ Stub for the actual task to be performed
    """
    # set the initial status to "started"
    try:
        await conn.set(f"status-{task_id}", "started")
        await asyncio.sleep(10)
        await conn.set(f"status-{task_id}", "finished")
    except asyncio.CancelledError:
        await conn.set(f"status-{task_id}", "cancelled")


def get_redis():
    """ Helper to get a redis client.
    """
    return aioredis.from_url(
        "redis://127.0.0.1", encoding="utf-8", decode_responses=True
    )


async def task_wrapper(task_id: str):
    """ Wrap a processing task to allow it beeing cancellable. Starts two futures,
        one for the actual processing, and one for the cancellation. The one
        finishing first triggers the cancellation of the other.
    """
    print(f"Starting task {task_id}")
    redis = get_redis()
    async with redis.client() as conn, redis.client() as conn2:
        # create an asyncio.Task for both the actual task and the cancellation
        # task. This is required so that we can call `.cancel()` on that future
        task_future = asyncio.create_task(long_running_task(conn, task_id))
        cancel_future = asyncio.create_task(wait_for_cancel(conn2, task_id))

        _, pending = await asyncio.wait(
            [task_future, cancel_future],
            return_when=asyncio.FIRST_COMPLETED
        )

        # cancel the "other" task
        for future in pending:
            future.cancel()


app = FastAPI()


@app.get("/start")
def start(background_tasks: BackgroundTasks):
    task_id = uuid4().hex
    background_tasks.add_task(task_wrapper, task_id)
    return {"task_id": task_id}


@app.get("/status/{task_id}")
async def status(task_id: str):
    redis = get_redis()
    async with redis.client() as conn:
        status = await conn.get(f"status-{task_id}")

    return {"task_id": task_id, "status": status or "unknown"}


@app.get("/cancel/{task_id}")
async def cancel(task_id: str):
    redis = get_redis()
    async with redis.client() as conn:
        status = await conn.get(f"status-{task_id}")

        if status == "started":
            await cancel_task(conn, task_id)

        status = await conn.get(f"status-{task_id}")

    return {"task_id": task_id, "status": status or "unknown"}
