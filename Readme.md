# FastAPI Task Management

This is a simple app to demonstrate a simple task management API.

Tasks are run using [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/) as async functions. The "task" is a sleep for 10 seconds.

The following endpoints are provided:

- `/docs` - the SwaggerUI for this App. Also usable to try out the service.
- `/start`: starts a new task, returns something like:

    ```json
    {"task_id":"4d15b40a748341358a6024437ef7de4c"}
    ```

    The task is started in a Background Task and listens also on a redis queue specific for this task to await potential cancellation.

- `/status/{task_id}`: returns the status of the given task which is either `unknown`, `started`, `finished` or `cancelled`.
- `/cancel/{task_id}`: cancel a task when it is `started`, no-op if status is otherwise. This sends a message via Redis to a task specific queue.

## Development

To set up everything:

```bash
pip install -r requirements.txt
```

To start redis:
```bash
docker run --name my-redis -p 6379:6379 --rm redis
```

To start the app:

```bash
uvicorn app.main:app --reload
```

Which now listens on `127.0.0.1:8000`

