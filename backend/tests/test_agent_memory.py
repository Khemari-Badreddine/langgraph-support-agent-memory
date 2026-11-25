import pytest
from deepeval.test_case import ConversationalTestCase, ConversationTurn
from deepeval.metrics import ConversationalGEval
from deepeval import assert_test

# Import your graph and store infrastructure
from app.services.graph import graph
from app.store import get_store

async def run_graph_turn(messages: list, user_id: str) -> str:
    """Helper to pass state into your compiled LangGraph instance."""
    initial_state = {
        "messages": messages,
        "user_id": user_id,
        "trace": []
    }
    
    # Execute the graph asynchronously
    final_state = await graph.ainvoke(initial_state)
    
    # Return the last assistant message
    return final_state["messages"][-1]["content"]

@pytest.mark.asyncio
async def test_graph_memory_lifecycle():
    user_id = "test-user-999"
    store = get_store()
    
    # ── TURN 1: User logs a complaint ──
    messages = [{"role": "user", "content": "My internet speed is dropping every day at 5 PM."}]
    assistant_output_1 = await run_graph_turn(messages, user_id)
    
    # Intercept and verify memory creation in the DB
    stored_memories_1 = await store.asearch(("memories", user_id))
    assert any(m.value.get("badge") == "open" for m in stored_memories_1), "Failed to store open tech issue."

    # ── TURN 2: User states it's resolved ──
    messages.append({"role": "assistant", "content": assistant_output_1})
    messages.append({"role": "user", "content": "Thanks, the tech fixed it. You can close that internet speed ticket."})
    assistant_output_2 = await run_graph_turn(messages, user_id)

    # Intercept and verify memory modification/resolution in the DB
    stored_memories_2 = await store.asearch(("memories", user_id))
    assert any(m.value.get("badge") == "res" for m in stored_memories_2), "Failed to change badge to 'res'."
    assert not any(m.value.get("badge") == "open" for m in stored_memories_2), "Open issues remained unlinked."

    # ── TURN 3: Context Recall verification ──
    messages.append({"role": "assistant", "content": assistant_output_2})
    messages.append({"role": "user", "content": "What was that ticket about again?"})
    assistant_output_3 = await run_graph_turn(messages, user_id)

    # ── DEEPEVAL CONVERSATIONAL EVALUATION ──
    # Construct the deepEval conversational test structure
    test_case = ConversationalTestCase(turns=[
        ConversationTurn(user_input=messages[0]["content"], assistant_output=assistant_output_1),
        ConversationTurn(user_input=messages[2]["content"], assistant_output=assistant_output_2),
        ConversationTurn(user_input=messages[4]["content"], assistant_output=assistant_output_3),
    ])

    # G-Eval custom metrics specific to your memory_node requirements
    memory_mutation_metric = ConversationalGEval(
        name="State-Driven Memory Recall",
        criteria="""Ensure the assistant properly remembers past events. 
                    When asked what the ticket was about in the last turn, the assistant must 
                    accurately recall that it was an internet speed issue and recognize it was marked resolved.""",
        threshold=0.7
    )

    # Execute DeepEval's LLM judge assertion
    assert_test(test_case, [memory_mutation_metric])
