# Create PRP with MCP Integration

## Feature file: $ARGUMENTS

Generate a complete PRP for general feature implementation with thorough research, incorporating available MCP tools. Ensure context is passed to the AI agent to enable self-validation and iterative refinement. Read the feature file first to understand what needs to be created, how the examples provided help, and any other considerations.

The AI agent only gets the context you are appending to the PRP and training data. Assume the AI agent has access to the codebase, MCP tools, and the same knowledge cutoff as you, so it's important that your research findings and MCP usage instructions are included in the PRP. The Agent has WebSearch capabilities and MCP tools, so pass URLs to documentation and specify when to use MCP tools.

## Available MCP Tools

### 1. **Supabase MCP** (`mcp__supabase__*`)
- Database operations (create tables, migrations, queries)
- Branch management for testing
- Log retrieval for debugging
- Use for: Database schema changes, data operations, debugging

### 2. **Context7 MCP** (`mcp__context7__*`)
- Retrieve up-to-date library documentation
- Get code examples from popular packages
- Use for: Library research, API documentation, implementation patterns

## Subagent Considerations

When generating PRPs from specs, consider which specialized subagent might be used:

### For Different Spec Types:
1. **Frontend/UI Specs** (e.g., `frontend.md`, `website-copy.md`)
   - The `ui-component-builder` agent will likely implement
   - Include specific design tokens, animations, component examples
   - Reference existing UI patterns in the codebase
   - Specify MCP Playwright tests for visual validation

2. **Backend/API Specs** (e.g., `mcp-server.md`, `new-ai-news-sources.md`)
   - The `backend-api-architect` agent will likely implement
   - Include API endpoint patterns, error handling strategies
   - Specify Supabase MCP for database operations
   - Include rate limiting and performance considerations

3. **Database Specs** (e.g., `entity-extraction-story-clustering.md`)
   - The `database-architect` agent will likely implement
   - Include current schema context via Supabase MCP
   - Provide migration strategies and rollback plans
   - Include performance optimization queries

4. **UX/Flow Specs** (e.g., `engagement-trending-tracking.md`)
   - The `ux-design-architect` agent might be consulted
   - Include user journey maps and interaction patterns
   - Reference existing UX patterns in the codebase

### PRP Structure Tips by Agent Type:
- **UI PRPs**: Heavy on visual examples, component hierarchies, style systems
- **Backend PRPs**: Focus on data flow, error handling, API contracts
- **Database PRPs**: Emphasize data relationships, query patterns, indexes
- **Integration PRPs**: Clear interface definitions between systems

## Enhanced Research Process

1. **Codebase Analysis**
   - Search for similar features/patterns in the codebase
   - Identify files to reference in PRP
   - Note existing conventions to follow
   - Check test patterns for validation approach
   - **MCP Usage**: Use IDE diagnostics to validate existing code patterns

2. **External Research with MCP**
   - **Use Context7 MCP** to get latest library documentation:
     ```
     mcp__context7__resolve-library-id for library name resolution
     mcp__context7__get-library-docs for documentation retrieval
     ```
   - Search for implementation examples online
   - Note version-specific features and gotchas
   - **Document MCP queries used** for reproducibility

3. **Database Schema Research** (if applicable)
   - **Use Supabase MCP** to inspect current schema:
     ```
     mcp__supabase__list_tables
     mcp__supabase__list_extensions
     mcp__supabase__get_advisors for performance/security checks
     ```
   - Document required migrations or schema changes

4. **User Clarification** (if needed)
   - Specific patterns to mirror and where to find them?
   - Integration requirements and where to find them?
   - Which MCP tools should be prioritized?

## PRP Generation with MCP Context

Using PRPs/templates/prp_base.md as template:

### Critical Context to Include
- **Documentation**: URLs and Context7 queries for latest docs
- **Code Examples**: Real snippets from codebase and Context7 results
- **MCP Tool Instructions**: Specific tools and commands to use
- **Database Context**: Current schema and migration requirements
- **Testing Strategy**: Playwright commands for UI testing

### MCP-Enhanced Implementation Blueprint
1. **Research Phase Instructions**
   - List Context7 queries to run for documentation
   - Specify Supabase queries for schema inspection
   
2. **Implementation Phase Instructions**
   - Database migrations via Supabase MCP
   - Code validation via IDE MCP
   - Testing via Playwright MCP
   
3. **Validation Phase Instructions**
   - Automated tests using appropriate MCP tools
   - Performance checks via Supabase advisors

### Example MCP Usage in PRP
```markdown
## Pre-Implementation Research
1. Get latest FastAPI docs:
   ```
   mcp__context7__resolve-library-id("fastapi")
   mcp__context7__get-library-docs("/tiangolo/fastapi", topic="dependencies")
   ```

2. Check current database schema:
   ```
   mcp__supabase__list_tables(schemas=["public"])
   ```

## Implementation Steps
1. Create database migration:
   ```
   mcp__supabase__apply_migration(
     name="add_user_preferences",
     query="ALTER TABLE users ADD COLUMN preferences JSONB DEFAULT '{}';"
   )
   ```
```

### Validation Gates (Must be Executable)
```bash
# Syntax/Style
ruff check --fix && mypy .

# Unit Tests
uv run pytest tests/ -v

# Database validation (via MCP)
# Include Supabase MCP commands to verify schema

# UI Tests (if applicable, via MCP)
# Include Playwright MCP commands for E2E tests
```

### MCP Tool Decision Matrix
Include in PRP when to use each tool:
- **Supabase MCP**: Any database operations, schema changes, debugging
- **Context7 MCP**: Library research, API documentation needs
- **Playwright MCP**: Frontend changes requiring visual/interaction testing
- **IDE MCP**: Code execution validation, Jupyter notebook operations

*** CRITICAL AFTER YOU ARE DONE RESEARCHING AND EXPLORING THE CODEBASE BEFORE YOU START WRITING THE PRP ***

*** ULTRATHINK ABOUT THE PRP AND PLAN YOUR APPROACH INCLUDING MCP TOOL USAGE ***

## Output
Save as: `PRPs/{feature-name}.md`

## Quality Checklist
- [ ] All necessary context included
- [ ] MCP tool usage clearly specified
- [ ] Validation gates are executable by AI
- [ ] References existing patterns
- [ ] Clear implementation path with MCP integration
- [ ] Error handling documented
- [ ] MCP fallback strategies included

## MCP-Specific Checklist
- [ ] Context7 queries for all external libraries
- [ ] Supabase commands for database operations
- [ ] Playwright tests for UI changes
- [ ] IDE diagnostics for code validation

Score the PRP on a scale of 1-10 (confidence level to succeed in one-pass implementation using Claude Code with MCP tools)

Remember: The goal is one-pass implementation success through comprehensive context and proper MCP tool utilization.