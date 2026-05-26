# backend/mcp/tools/vision_tool.py
"""
MCP wrapper for GPT-4o Vision image analysis.
"""
from backend.mcp.schemas import MCPTool, MCPToolInputSchema, MCPToolCallResult, MCPContentItem

TOOL_DEFINITION = MCPTool(
    name="analyze_image",
    description=(
        "Analyze an image using GPT-4o Vision. Capabilities: "
        "OCR (extract text), chart/graph data extraction, diagram interpretation, "
        "code screenshot analysis, general image description. "
        "Best for: reading documents, understanding visual data, interpreting screenshots."
    ),
    inputSchema=MCPToolInputSchema(
        properties={
            "image_base64": {
                "type":        "string",
                "description": "Base64-encoded image data (JPEG, PNG, GIF, or WebP).",
            },
            "question": {
                "type":        "string",
                "description": "Specific question about the image. If not provided, gives a general analysis.",
                "default":     "Describe this image in detail.",
            },
            "mode": {
                "type":        "string",
                "enum":        ["auto", "ocr", "chart", "diagram", "code", "general"],
                "description": "Analysis mode. 'auto' detects from the question (default).",
                "default":     "auto",
            },
        },
        required=["image_base64"],
    ),
)


async def execute(arguments: dict, workspace_slug: str = "default") -> MCPToolCallResult:
    image_b64 = arguments.get("image_base64", "")
    question  = arguments.get("question", "Describe this image in detail.")
    mode      = arguments.get("mode", "auto")

    if not image_b64:
        return MCPToolCallResult(
            content=[MCPContentItem(type="text", text="Error: image_base64 is required")],
            isError=True,
        )

    try:
        from backend.llm.vision_preprocessor import encode_from_base64, ImageProcessingError
        from backend.agent.vision_agent import VisionAgent

        agent  = VisionAgent()
        result = await agent.run(
            query=question,
            context={"image_data": image_b64},
        )

        content_items = [
            MCPContentItem(type="text", text=result.content)
        ]

        # Also include the image back for context if MCP client supports it
        content_items.append(
            MCPContentItem(
                type="image",
                data=image_b64,
                mimeType="image/jpeg",
            )
        )

        return MCPToolCallResult(
            content=content_items,
            isError=bool(result.error),
        )

    except Exception as e:
        return MCPToolCallResult(
            content=[MCPContentItem(type="text", text=f"Vision analysis failed: {str(e)}")],
            isError=True,
        )