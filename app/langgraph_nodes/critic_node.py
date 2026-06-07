from ..agents.critic_agent import CriticAgent
from ..models import AgentResponse


class CriticNode:
    def __init__(self):
        self.critic = CriticAgent()

    async def run(self, answer: AgentResponse) -> AgentResponse:
        return await self.critic.critique(answer)
