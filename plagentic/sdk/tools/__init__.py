from plagentic.sdk.tools.baseTool import BaseTool
from plagentic.sdk.tools.toolManager import ToolManager

from plagentic.sdk.tools.googleSearch.searchGoogle import GoogleSearch
from plagentic.sdk.tools.fileSave.saveFile import FileSave
from plagentic.sdk.tools.terminal.terminal import Terminal


def _import_browserTool():
    try:
        from plagentic.sdk.tools.browser.browserTool import BrowserTool
        return BrowserTool
    except ImportError:
        class BrowserToolPlaceholder:
            def __init__(self, *args, **kwargs):
                raise ImportError(
                    "The 'browser-use' package is required to use BrowserTool. "
                    "Please install it with 'pip install browser-use>=0.1.40' or "
                    "'pip install plagentic-sdk[full]'."
                )

        return BrowserToolPlaceholder


BrowserTool = _import_browserTool()

__all__ = [
    'BaseTool',
    'ToolManager',
    'GoogleSearch',
    'FileSave',
    'BrowserTool',
    'Terminal'
]

"""
Tools module for Plagentic.
"""