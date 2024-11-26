"""
This test ensures the basic LLM cache model is working properly, but also runs some basic sanity checks on the ORM.

SQLModel is the most risky part of the stack so we should be defensive about it
"""

from app.models.llm_response import LLMResponse


def test_basic_llm_response():
    # ensure that database cleaning is working
    assert LLMResponse.count() == 0

    llm_response = LLMResponse(
        model="gpt-4", response="bar", prompt="foo", category="test"
    ).save()

    # ensure that basic DB operation is working
    assert llm_response.id
    assert llm_response.response == "bar"
    assert str(llm_response.id).startswith("user_")
    assert llm_response.prompt_hash

    llm_response.response = "bar2"
    llm_response.save()

    fresh_llm_response = LLMResponse.get(llm_response.id)
    assert fresh_llm_response.response == "bar2"


def test_avoid_prompt_mutation():
    assert LLMResponse.count() == 0

    llm_response = LLMResponse(
        model="gpt-4", response="bar", prompt="foo", category="test"
    ).save()
