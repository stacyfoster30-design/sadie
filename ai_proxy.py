#!/usr/bin/env python3
"""
🤖 STACY'S AI PROXY AGENT
Built following the Google AI Mode instructions
Uses: AutoGen + Ollama (100% free, runs locally)
"""

import asyncio
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console


async def main():
    # Connect the proxy to your local, free Ollama server
    local_llm = OpenAIChatCompletionClient(
        model="llama3.1",
        base_url="http://localhost:11434/v1",
        api_key="ollama",  # Ollama doesn't require a real key, but a placeholder is needed
    )

    # Define the Proxy Agent with system instructions to handle local files and execution
    proxy_agent = AssistantAgent(
        name="AI_Proxy",
        model_client=local_llm,
        system_message=(
            "You are a local autonomous proxy agent with terminal and file system permissions. "
            "Your job is to read, edit, and fix files, or execute system scripts exactly as requested. "
            "Provide the literal code modifications or terminal commands needed to accomplish the task."
        ),
    )

    # Establish the automation team loop
    team = RoundRobinGroupChat([proxy_agent], max_turns=5)

    # Ask the user what they want the proxy to do
    user_task = input("What task should your AI Proxy execute? ")

    # Run the task autonomously through the console loop
    await Console(team.run_stream(task=user_task))


if __name__ == "__main__":
    asyncio.run(main())
