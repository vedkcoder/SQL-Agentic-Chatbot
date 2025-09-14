from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import HumanMessage,SystemMessage,AnyMessage,ToolMessage
from typing import TypedDict, Annotated
import operator


class SQLAgentState(TypedDict):
    messages : Annotated[list[AnyMessage], operator.add]


class SQLAgent:

    def __init__(self, model, tools, system_prompt):
        self.system_prompt = system_prompt
        self.model = model

        SQLAgent_graph = StateGraph(SQLAgentState)
        SQLAgent_graph.add_node('call_llm', self.call_llm)
        SQLAgent_graph.add_node('call_tool', self.call_tool)
        SQLAgent_graph.add_edge('call_tool', 'call_llm')
        SQLAgent_graph.add_conditional_edges('call_llm', self.is_tool_call)
        SQLAgent_graph.set_entry_point('call_llm')
        self.memory = InMemorySaver()
        self.graph = SQLAgent_graph.compile(checkpointer=self.memory)
        self.tools = { tool.name : tool for tool in tools}

    def is_tool_call(self, state: SQLAgentState):

        recent_message = state['messages'][-1]
        if len(recent_message.tool_calls) > 0:
            return 'call_tool'
        else:
            return END

    def call_llm(self, state:SQLAgentState):

        messages = state['messages']

        if self.system_prompt:
            messages = [SystemMessage(content=self.system_prompt)] + messages

            response = self.model.invoke(messages)
            return {'messages' : [response]}
        
    def call_tool(self, state:SQLAgentState):

        tools = state['messages'][-1].tool_calls
        response = []

        for tool in tools:

            if not tool['name'] in tools:
                print(f'Tool: {tool} does not exist')
                result = 'Invalid tool called. Please retry'

            else:
                result = self.tools[tool['name'].invoke(tool['args'])]

            response.append(ToolMessage(tool_call_id=tool['id'], name=tool['name'], content=str(result)))

        return { "messages" : response}