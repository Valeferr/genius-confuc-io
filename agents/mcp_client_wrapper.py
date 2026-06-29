import asyncio
import threading
from typing import List, Dict, Any, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPClientWrapper:
    def __init__(self, command: str, args: List[str]):
        self.command = command
        self.args = args
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._start_loop, daemon=True)
        self._thread.start()
        
        self.server_params = StdioServerParameters(command=self.command, args=self.args, env=None)
        
        # Inizializza la sessione in modo sincrono aspettando il thread
        asyncio.run_coroutine_threadsafe(self._init_session(), self._loop).result()

    def _start_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    async def _init_session(self):
        # Manteniamo i context manager aperti a livello di istanza
        self._client_cm = stdio_client(self.server_params)
        self.read, self.write = await self._client_cm.__aenter__()
        
        self._session_cm = ClientSession(self.read, self.write)
        self.session = await self._session_cm.__aenter__()
        await self.session.initialize()
        
    def get_tools(self) -> List[Dict[str, Any]]:
        """Restituisce i tool disponibili dal server, in formato dict standard."""
        future = asyncio.run_coroutine_threadsafe(self.session.list_tools(), self._loop)
        result = future.result()
        tools = []
        for tool in result.tools:
            tools.append({
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema
            })
        return tools

    def call_tool(self, name: str, arguments: dict) -> str:
        """Chiama un tool sul server MCP e restituisce il risultato come stringa."""
        future = asyncio.run_coroutine_threadsafe(self.session.call_tool(name, arguments), self._loop)
        result = future.result()
        
        # Concatena il testo restituito dal tool
        output = []
        for content in result.content:
            if content.type == "text":
                output.append(content.text)
        return "\n".join(output)
        
    def close(self):
        """Chiude la connessione e la sessione MCP."""
        async def _cleanup():
            await self._session_cm.__aexit__(None, None, None)
            await self._client_cm.__aexit__(None, None, None)
        
        if self._loop.is_running():
            future = asyncio.run_coroutine_threadsafe(_cleanup(), self._loop)
            future.result()
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._thread.join()
