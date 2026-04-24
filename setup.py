
import asyncio
from datetime import datetime, UTC
from agent_control import AgentControlClient, controls, agents
from agent_control_models import Agent

async def setup():
    async with AgentControlClient() as client:

        # 1. Register agent
        agent = Agent(
            agent_name="moderated_rag_chatbot_v2",
            agent_description="RAG chatbot with moderation",
            agent_created_at=datetime.now(UTC).isoformat(),
        )

        await agents.register_agent(client, agent, steps=[])

        # 2. Prompt Injection Control
        injection_control = await controls.create_control(
            client,
            name="block-prompt-injection-v2",
            data={
                "enabled": True,
                "execution": "server",
                "scope": {"stages": ["pre"]},
                "condition": {
                    "selector": {"path": "input"},
                    "evaluator": {
                        "name": "regex",
                        "config": {
                            "pattern": r"\b(ignore previous instructions|system prompt|bypass|jailbreak)\b"
                        },
                    },
                },
                "action": {"decision": "deny"},
            },
        )

        # 3. Harmful Output Control
        harmful_output_control = await controls.create_control(
            client,
            name="block-harmful-output-v2",
            data={
                "enabled": True,
                "execution": "server",
                "scope": {"stages": ["post"]},
                "condition": {
                    "selector": {"path": "output"},
                    "evaluator": {
                        "name": "regex",
                        "config": {
                            "pattern": r"\b(kill|attack|illegal|harm|exploit)\b"
                        },
                    },
                },
                "action": {"decision": "deny"},
            },
        )

        # 4. Sensitive Data Leak Control
        data_leak_control = await controls.create_control(
            client,
            name="block-sensitive-data-v2",
            data={
                "enabled": True,
                "execution": "server",
                "scope": {"stages": ["post"]},
                "condition": {
                    "selector": {"path": "output"},
                    "evaluator": {
                        "name": "regex",
                        "config": {
                            "pattern": r"\b(password|api_key|secret|token)\b"
                        },
                    },
                },
                "action": {"decision": "deny"},
            },
        )

        # 5. Attach controls to agent
        for ctrl in [injection_control, harmful_output_control, data_leak_control]:
            await agents.add_agent_control(
                client,
                agent_name=agent.agent_name,
                control_id=ctrl["control_id"],
            )

        print("✅ RAG Controls Setup Complete!")

asyncio.run(setup())