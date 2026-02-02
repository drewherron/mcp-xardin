from mcp.server.fastmcp import FastMCP

mcp = FastMCP("xardin")


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
