from ..agents.knowledge_agent import KnowledgeAgent


class RetrievalNode:
    def __init__(self, knowledge_agent: KnowledgeAgent):
        self.knowledge_agent = knowledge_agent

    def run(self, query: str, top_k: int = 3):
        return self.knowledge_agent.retrieve(query, top_k=top_k)
