import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { Props } from "../types";
import { registerDatabaseTools } from "../../examples/database-tools";
import { registerNewsTools } from "./news-tools";

/**
 * Register all MCP tools based on user permissions
 */
export function registerAllTools(server: McpServer, env: Env, props: Props) {
	// Register database tools
	registerDatabaseTools(server, env, props);
	
	// Register AI news aggregator tools
	registerNewsTools(server, env, props);
	
	// Future tools can be registered here
	// registerOtherTools(server, env, props);
}