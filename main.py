def main():
    """
    Main entry point for the Google Workspace MCP server.
    Uses FastMCP's native streamable-http transport.
    """
    # --- Argument parsing removed ---
    # In a deployed Cloud Run environment, we'll use environment variables
    # and set the transport mode directly.
    transport_mode = 'streamable-http'
    single_user_mode = os.getenv('MCP_SINGLE_USER_MODE', 'false').lower() in ('true', '1')

    # Set port and base URI once for reuse throughout the function
    port = int(os.getenv("PORT", 8000))
    # In Cloud Run, the base URI is determined by the service URL, not an env var.
    # We will let the server run on all interfaces (0.0.0.0) and Cloud Run handles the public URL.
    base_uri = "http://0.0.0.0" 

    safe_print("🔧 Google Workspace MCP Server")
    safe_print("=" * 35)
    safe_print("📋 Server Information:")
    try:
        version = metadata.version("workspace-mcp")
    except metadata.PackageNotFoundError:
        version = "dev"
    safe_print(f"   📦 Version: {version}")
    safe_print(f"   🌐 Transport: {transport_mode}")
    safe_print(f"   👤 Mode: {'Single-user' if single_user_mode else 'Multi-user'}")
    safe_print(f"   🐍 Python: {sys.version.split()[0]}")
    safe_print("")

    # Active Configuration
    safe_print("⚙️ Active Configuration:")
    client_secret = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET', 'Not Set')
    redacted_secret = f"{client_secret[:4]}...{client_secret[-4:]}" if len(client_secret) > 8 else "Invalid or too short"
    config_vars = {
        "GOOGLE_OAUTH_CLIENT_ID": os.getenv('GOOGLE_OAUTH_CLIENT_ID', 'Not Set'),
        "GOOGLE_OAUTH_CLIENT_SECRET": redacted_secret,
        "USER_GOOGLE_EMAIL": os.getenv('USER_GOOGLE_EMAIL', 'Not Set'),
        "MCP_SINGLE_USER_MODE": os.getenv('MCP_SINGLE_USER_MODE', 'false'),
    }
    for key, value in config_vars.items():
        safe_print(f"   - {key}: {value}")
    safe_print("")

    # Import all tool modules
    tool_imports = {
        'gmail': lambda: __import__('gmail.gmail_tools'),
        'drive': lambda: __import__('gdrive.drive_tools'),
        'calendar': lambda: __import__('gcalendar.calendar_tools'),
        'docs': lambda: __import__('gdocs.docs_tools'),
        'sheets': lambda: __import__('gsheets.sheets_tools'),
        'chat': lambda: __import__('gchat.chat_tools'),
        'forms': lambda: __import__('gforms.forms_tools'),
        'slides': lambda: __import__('gslides.slides_tools'),
        'tasks': lambda: __import__('gtasks.tasks_tools'),
        'search': lambda: __import__('gsearch.search_tools')
    }
    tools_to_import = list(tool_imports.keys())
    
    from auth.scopes import set_enabled_tools
    set_enabled_tools(tools_to_import)

    safe_print(f"🛠️  Loading {len(tools_to_import)} tool modules:")
    for tool in tools_to_import:
        tool_imports[tool]()
        safe_print(f"   - Google {tool.title()} API integration enabled")
    safe_print("")

    if single_user_mode:
        os.environ['MCP_SINGLE_USER_MODE'] = '1'
        safe_print("🔐 Single-user mode enabled")
        safe_print("")

    try:
        check_credentials_directory_permissions()
    except Exception as e:
        safe_print(f"❌ Credentials directory permission check failed: {e}")
        sys.exit(1)

    @server.tool(name="health_check", description="A simple health check to confirm the server is running.")
    def health_check():
        return {"status": "ok"}
    
    try:
        set_transport_mode(transport_mode)
        configure_server_for_http()
        safe_print(f"🚀 Starting HTTP server on port {port}")
        server.run(transport="streamable-http", host="0.0.0.0", port=port)
    except KeyboardInterrupt:
        safe_print("\n👋 Server shutdown requested")
        sys.exit(0)
    except Exception as e:
        safe_print(f"\n❌ Server error: {e}")
        logger.error(f"Unexpected error running server: {e}", exc_info=True)
        sys.exit(1)
