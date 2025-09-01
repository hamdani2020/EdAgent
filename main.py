"""
EdAgent main application entry point
"""

import uvicorn
from edagent.config import get_settings


def main():
    """Run the EdAgent application"""
    settings = get_settings()
    
    uvicorn.run(
        "edagent.api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    main()