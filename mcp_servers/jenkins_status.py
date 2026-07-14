#!/usr/bin/env python3
"""
Minimal MCP server that exposes Jenkins build status to an AI agent.
CSE636 Week 2 Lab — Part 2.

Install: pip install mcp requests
"""

import asyncio
import os

import requests
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool


# Read the Jenkins connection settings from environment variables.
# The defaults allow the server to connect to a local Jenkins instance.
JENKINS_URL = os.environ.get("JENKINS_URL", "http://localhost:8080")
JENKINS_USER = os.environ.get("JENKINS_USER", "admin")
JENKINS_TOKEN = os.environ.get("JENKINS_TOKEN", "")


# Create the MCP server that Claude Code will connect to.
app = Server("cse636-jenkins-mcp")


@app.list_tools()
async def list_tools():
    """Advertise the tools available to the AI agent."""
    return [
        Tool(
            name="get_build_status",
            description=(
                "Returns the status and number of the most recent Jenkins build "
                "for a given job. Use this to check if a CI pipeline is currently "
                "passing or failing before making code changes."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "job_name": {
                        "type": "string",
                        "description": (
                            "The Jenkins job name, for example 'ai-review-demo'"
                        ),
                    }
                },
                "required": ["job_name"],
            },
        ),
        Tool(
            name="list_jobs",
            description="Returns a list of all Jenkins job names.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls by querying the Jenkins REST API."""
    auth = (
        (JENKINS_USER, JENKINS_TOKEN)
        if JENKINS_TOKEN
        else None
    )

    if name == "list_jobs":
        response = requests.get(
            f"{JENKINS_URL}/api/json?tree=jobs[name]",
            auth=auth,
            timeout=10,
        )
        response.raise_for_status()

        jobs = [
            job["name"]
            for job in response.json().get("jobs", [])
        ]

        return [
            TextContent(
                type="text",
                text=f"Jenkins jobs: {', '.join(jobs)}",
            )
        ]

    if name == "get_build_status":
        job_name = arguments["job_name"]

        response = requests.get(
            f"{JENKINS_URL}/job/{job_name}/lastBuild/api/json",
            auth=auth,
            timeout=10,
        )

        if response.status_code == 404:
            return [
                TextContent(
                    type="text",
                    text=f"Job '{job_name}' not found.",
                )
            ]

        response.raise_for_status()
        build_data = response.json()

        result = build_data.get("result", "IN_PROGRESS")
        build_number = build_data.get("number", "?")

        return [
            TextContent(
                type="text",
                text=(
                    f"Job '{job_name}': "
                    f"build #{build_number} — {result}"
                ),
            )
        ]

    return [
        TextContent(
            type="text",
            text=f"Unknown tool: {name}",
        )
    ]


async def main():
    """Start the MCP server over standard input/output."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())