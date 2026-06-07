"""VLM connector stub for Franka MCP server."""


class VLMConnector:
    def __init__(
        self,
        gpu: int = 0,
        model_id: str = "meta-llama/Llama-3.2-11B-Vision-Instruct",
    ):
        self.gpu = gpu
        self.model_id = model_id
        self.connected = False

    async def connect(self):
        """Stub: actual model loading deferred to Isaac Sim integration phase."""
        print(f"VLMConnector: stub mode (model={self.model_id}, gpu={self.gpu})")
        self.connected = False  # remains False in stub mode

    async def describe(self, image_path: str, query: str = "") -> str:
        """Describe image using VLM. Returns stub response when not connected."""
        if not self.connected:
            return "VLM not connected (stub mode)"
        return ""
