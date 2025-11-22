# mcp-gateway
At present this project is a simple proxy that will print the requests and response going back and forth between MCP client and MCP server.

## Prerequisite
You need to install flask python module

## Setup
First run your MCP server that you want the call to route to.

In the .env file, add the base url to the MCP server. Replace "http://localhost:8500" with your MCP server url.
By default, the proxy runs on 8080 port. You can provide your own port as a part of the run call
Run the proxy simply by mking the call:
`python http_proxy.py [port]`

In the MCP client, you need to point to the proxy base url instead of the MCP server url.

Once the MCP client starts, you can start seeing the request response.

