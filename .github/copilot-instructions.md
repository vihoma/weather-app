# Copilot instructions specific to this repository (weather-app)

**Always start the conversation by calling:
`mcp_prism-mcp_session_load_context(project='weather-app', level='deep')`.
When wrapping up, always call:
`mcp_prism-mcp_session_save_ledger` and `mcp_prism-mcp_session_save_handoff`.**

## Key conventions specific to this repo

- For the current project and knowledge base, use the prism-mcp MCP server, if
  available, to access the knowledge base and gather information, such as
  preferences, dependencies, made decisions and functionality. This can help
  you understand the codebase and the users preferences and make informed
  decisions when planning and implementing code or other actions.
- When planning and implementing code, use the cocoindex-code MCP server, if
  available, to access the codebase and gather information about the code and its
  structure, dependencies, and functionality. This can help you understand the
  codebase and make informed decisions when planning and implementing code.
- When planning and implementing code use the context7 MCP server, if available,
  for the latest programming APIs and best practices for the libraries in use.
  This will help ensure that your code is up-to-date and follows the latest
  standards in software development.
