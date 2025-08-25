import click
import uvicorn

import ca2roi.gui  # Load


@click.command()
@click.option("--host", default="127.0.0.1", help="Host to bind the server to")
@click.option("--port", default=8000, type=int, help="Port to bind the server to")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
def main(host: str, port: int, reload: bool):
    """Start the Ca2ROI GUI server."""
    click.echo(f"Starting Ca2ROI GUI server at http://{host}:{port}")
    click.echo("Press Ctrl+C to stop the server")

    uvicorn.run("ca2roi.gui:app", host=host, port=port, reload=reload)
