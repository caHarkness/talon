from fastmcp.tools import tool
from fastmcp.utilities.types import Image

@tool
def include_images(paths: list[str]) -> list[Image]:
    """
    Used to add visual information to the conversation.
    """
    output_images = []

    for p in paths:
        output_images.append(Image(path=p))

    return output_images
