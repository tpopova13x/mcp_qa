import asyncio
from mcp.client.streamable_http import streamablehttp_client
from mcp.client.session import ClientSession

MCP_URL = "http://localhost:8080/mcp"


async def call_tool(session: ClientSession, tool_name: str, arguments: dict) -> str:
    result = await session.call_tool(tool_name, arguments)
    return result.content[0].text


async def test_search_user_docu(session: ClientSession):
    print("=== test_search_user_docu ===")
    result = await call_tool(session, "search_user_docu", {"query": "folder", "n_results": 2})
    print(result)
    assert result and "No results found" not in result, "Expected results from user docs"
    print("PASSED\n")


async def test_search_internal_docu(session: ClientSession):
    print("=== test_search_internal_docu ===")
    result = await call_tool(session, "search_internal_docu", {"query": "folder", "n_results": 2})
    print(result)
    assert result and "No results found" not in result, "Expected results from internal docs"
    print("PASSED\n")


async def test_search_tests(session: ClientSession):
    print("=== test_search_tests ===")
    result = await call_tool(session, "search_tests", {"query": "admin"})
    print(result)
    assert result and "No matching tests found" not in result, "Expected test results for 'admin'"
    print("PASSED\n")


async def main():
    async with streamablehttp_client(MCP_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            tool_names = [t.name for t in tools.tools]
            print(f"Available tools: {tool_names}\n")
            assert "search_user_docu" in tool_names
            assert "search_internal_docu" in tool_names
            assert "search_tests" in tool_names

            await test_search_user_docu(session)
            await test_search_internal_docu(session)
            await test_search_tests(session)

            print("All tests passed!")


if __name__ == "__main__":
    asyncio.run(main())
