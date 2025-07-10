from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from typing import Any, List, Optional

@CrewBase
class CreateMermaidCrew():
    """LatestAiDevelopment crew"""

    agents_config = "./agents.yaml"
    tasks_config = "./tasks.yaml"

    def __init__(self, tools: Optional[List[Any]] = None):
        """Initialize the crew with external tools"""
        self._tools = tools or []
        super().__init__()

    def log_step_callback(self, output):
        print(
            f"""
            Step completed!
            details: {output.__dict__}
        """
        )

    def log_task_callback(self, output):
        print(
            f"""
            Task completed!
            details: {output.__dict__}
        """
        )

    @property
    def tools(self) -> List[Any]:
        """Return the tools assigned during initialization"""
        return self._tools
    
    @tools.setter
    def tools(self, tools: List[Any]):
        """Set tools after initialization if needed"""
        self._tools = tools

    @agent
    def mcp_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['mcp_agent'], # type: ignore[index]
            verbose=True,
            tools=self.tools
        )

    @task
    def read_data_task(self)->Task:
        return Task(
            config=self.tasks_config['read_data_task'], # type: ignore[index]
        )

    @task
    def create_mermaid_graph_task(self)->Task:
        return Task(
            config=self.tasks_config['create_mermaid_task'], # type: ignore[index]
            agent=self.mcp_agent(),
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,  # Automatically collected by the @agent decorator
            tasks=self.tasks,    # Automatically collected by the @task decorator.
            process=Process.sequential,
            verbose=True,
        )