import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run():
    server_params = StdioServerParameters(
        command="/Users/giosem/Desktop/Università/ILP/genius-confuc-io/.venv/bin/python",
        args=["mcp_server.py"]
    )
    
    print("Avvio connessione MCP...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Connessione inizializzata.")
            

            tools = await session.list_tools()
            print("\n--- TOOLS DISPONIBILI ---")
            for t in tools.tools:
                print(f"- {t.name}: {t.description}")
                

            resources = await session.list_resources()
            print("\n--- RESOURCES DISPONIBILI ---")
            for r in resources.resources:
                print(f"- {r.uri}: {r.name}")
                

            if resources.resources:
                res_content = await session.read_resource(resources.resources[0].uri)
                print(f"\n--- CONTENUTO RISORSA ({resources.resources[0].uri}) ---")
                print(res_content.contents[0].text[:200] + "...")


            prompts = await session.list_prompts()
            print("\n--- PROMPTS DISPONIBILI ---")
            for p in prompts.prompts:
                print(f"- {p.name}: {p.description}")

if __name__ == "__main__":
    asyncio.run(run())
