"""
This test ensures the basic LLM cache model is working properly, but also runs some basic sanity checks on the ORM.

SQLModel is the most risky part of the stack so we should be defensive about it
"""

from app.models.llm_response import LLMResponse


def test_basic_llm_response():
    # ensure that database cleaning is working
    assert LLMResponse.count() == 0

    response = LLMResponse(
        model="gpt-4", response="bar", prompt="foo", category="test"
    ).save()

    # ensure that basic DB operation is working
    assert response.id
    assert str(response.id).startswith("user_")
    assert response.prompt_hash
