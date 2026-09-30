from gaw.models import ProviderState, Task
from gaw.orchestrator import Orchestrator


providers = [
    ProviderState("free-primary", {"analysis"}, free=True, priority=1),
    ProviderState("free-fallback", {"analysis"}, free=True, priority=2),
]


def outage(_task):
    raise RuntimeError("synthetic provider outage")


orchestrator = Orchestrator(
    providers,
    {
        "free-primary": outage,
        "free-fallback": lambda task: f"completed {task.task_id} through fallback",
    },
)

result = orchestrator.run(
    Task(
        task_id="DEMO-1",
        capability="analysis",
        prompt="analyze synthetic quality event",
    )
)

print(result)
