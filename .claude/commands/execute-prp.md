# Execute PRP

Implement a feature using the PRP file with comprehensive verification and quality assurance.

## PRP File: $ARGUMENTS

## Execution Process

### 1. **Load & Analyze PRP**
   - Read the specified PRP file thoroughly
   - Understand all context, requirements, and validation criteria
   - **CRITICAL: Make NO assumptions** - verify all requirements using MCP servers
   - **Use MCP servers for up-to-date information**:
     - `context7` for latest library documentation and API references
     - `supabase` for current database schema and table structures
     - `playwright` for UI testing and validation if needed
   - Extend research with web searches and codebase exploration as needed
   - Follow all instructions in the PRP completely

### 2. **Strategic Planning (ULTRATHINK)**
   - Create comprehensive implementation plan addressing all PRP requirements
   - **Use TodoWrite tool** to break down complex tasks into smaller, manageable steps
   - Identify implementation patterns from existing codebase to follow
   - Plan validation checkpoints throughout implementation
   - *Note: Appropriate specialized agents will be selected automatically based on task types*

### 3. **Execute Implementation**
   - Implement all PRP requirements following the planned approach
   - **Use appropriate MCP servers** for verification throughout:
     - `context7` for library documentation verification
     - `supabase` for database schema confirmation  
     - `playwright` for UI testing when applicable
   - **TodoWrite progress tracking** - mark items as completed throughout
   - *Code review agent automatically invokes* after significant code changes

### 4. **Validation & Quality Assurance**
   - Run each validation command specified in the PRP
   - Fix any failures using error patterns from PRP
   - Re-run validation until all checks pass
   - Automatic code review occurs before completion

### 5. **Completion & Verification**
   - Ensure all PRP checklist items are completed
   - Run final validation suite from PRP  
   - Report completion status with validation results
   - **Re-read PRP** to ensure 100% implementation compliance

## **MCP Verification Requirements**

### **Context7 MCP (Library Documentation)**
```bash
# Always verify library documentation before implementation
mcp__context7__resolve-library-id libraryName="library_name"
mcp__context7__get-library-docs context7CompatibleLibraryID="/org/project" topic="specific_topic"
```

### **Supabase MCP (Database Operations)** 
```bash
# Always verify database schema before making changes
mcp__supabase__list_tables
mcp__supabase__execute_sql query="DESCRIBE table_name"
mcp__supabase__apply_migration name="migration_name" query="SQL_COMMAND"
```

### **Playwright MCP (UI Testing)**
```bash
# Use for UI testing and validation when applicable
mcp__playwright__browser_navigate url="http://localhost:8000"
mcp__playwright__browser_snapshot
```

## **No Assumptions Policy**

**NEVER assume**:
- ❌ Library API methods or parameters
- ❌ Database table structure or column names  
- ❌ External API endpoints or authentication
- ❌ Framework patterns or best practices

**ALWAYS verify with MCP servers or appropriate tools before implementation**

## **Error Recovery**
If validation fails: analyze PRP error patterns → fix issues → re-run validation → repeat until passing

**Remember**: Agents are selected automatically. Focus on comprehensive verification and quality execution.