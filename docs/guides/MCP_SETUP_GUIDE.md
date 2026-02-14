# MCP Server Setup Guide

This guide explains how to obtain credentials and configure the four MCP (Model Context Protocol) servers for this project.

## Overview

The project uses these MCP servers to enhance Claude Code's capabilities:

| MCP Server | Purpose | Package |
|------------|---------|---------|
| **Context7** | Version-specific documentation injection | `@upstash/context7-mcp` |
| **Firecrawl** | Advanced web scraping with JS rendering | `firecrawl-mcp` |
| **Figma** | Design file access and asset management | `@nvanexan/figma-mcp` |
| **Supabase** | Database access and project management | `@supabase/mcp-server-supabase` |

## Configuration File

MCP servers are configured in [`.claude/settings.local.json`](../../.claude/settings.local.json) with credentials stored in `.env.mcp` at the project root.

## Step 1: Obtain API Keys and Tokens

### Context7 API Key

**What it does:** Injects up-to-date, version-specific documentation for frameworks and libraries directly into Claude's context.

**How to get it:**

1. Visit [context7.com/dashboard](https://context7.com/dashboard)
2. Sign up or log in
3. Navigate to **API Keys** section
4. Click **Generate API Key**
5. Copy the key (format: `ctx7sk_*`)

**Expected format:** `ctx7sk_abc123def456...`

---

### Firecrawl API Key

**What it does:** Enables advanced web scraping with JavaScript rendering, batch processing, and structured data extraction.

**How to get it:**

1. Visit [firecrawl.dev/app/api-keys](https://firecrawl.dev/app/api-keys)
2. Sign up or log in
3. Click **Generate API Key**
4. Copy the key (format: `fc-*`)

**Expected format:** `fc-abc123def456...`

**Note:** Firecrawl offers a free tier for testing. Check their pricing page for limits.

---

### Figma Personal Access Token

**What it does:** Allows Claude to access Figma design files, retrieve components, styles, and export assets.

**How to get it:**

1. Open Figma (desktop app or web)
2. Go to **Settings** (click your profile picture)
3. Navigate to **Security** tab
4. Scroll to **Personal Access Tokens**
5. Click **Generate new token**
6. Name it (e.g., "Claude Code MCP")
7. Copy the token immediately (shown only once!)

**Expected format:** Long hexadecimal string (e.g., `1234567890abcdef...`)

**Documentation:** [Manage Personal Access Tokens](https://help.figma.com/hc/en-us/articles/8085703771159-Manage-personal-access-tokens)

---

### Supabase Personal Access Token

**What it does:** Enables Claude to query your Supabase database tables, view logs, and access project configuration.

**How to get it:**

1. Visit [supabase.com](https://supabase.com) and log in
2. Click on your profile (top right)
3. Go to **Account Settings**
4. Select **Access Tokens** from left sidebar
5. Click **Generate new token**
6. Name it (e.g., "Claude Code MCP")
7. Select appropriate scopes (read access recommended)
8. Copy the token (format: `sbp_*`)

**Expected format:** `sbp_abc123def456...`

**Note:** Your Supabase project reference is already configured (`cexurvymsvbmqpigfzuj` from `backend/.env`).

**Documentation:** [Supabase MCP Getting Started](https://supabase.com/docs/guides/getting-started/mcp)

---

## Step 2: Configure Credentials

1. **Copy the example file:**
   ```bash
   copy .env.mcp.example .env.mcp
   ```

2. **Edit `.env.mcp`** and replace placeholders with your actual credentials:

   ```bash
   CONTEXT7_API_KEY=ctx7sk_YOUR_ACTUAL_KEY_HERE
   FIRECRAWL_API_KEY=fc-YOUR_ACTUAL_KEY_HERE
   FIGMA_API_KEY=YOUR_ACTUAL_FIGMA_PAT_HERE
   SUPABASE_ACCESS_TOKEN=YOUR_ACTUAL_SUPABASE_PAT_HERE
   SUPABASE_PROJECT_REF=cexurvymsvbmqpigfzuj
   ```

3. **Save the file**

**Security Note:** `.env.mcp` is gitignored and will never be committed to version control.

---

## Step 3: Verify Configuration

The MCP servers are already configured in `.claude/settings.local.json`. You don't need to modify this file.

**To verify:**

1. **Restart Claude Code** (MCPs load at startup)
2. Run the following command in Claude Code:
   ```
   /mcp list
   ```

You should see all four MCPs listed:
- context7
- firecrawl
- figma
- supabase

---

## Step 4: Test Each MCP

### Test Context7

Ask Claude Code:
```
Can you fetch the latest Next.js 14 App Router documentation?
```

**Expected:** Claude uses Context7 to retrieve current, version-specific docs.

---

### Test Firecrawl

Ask Claude Code:
```
Use Firecrawl to scrape https://example.com and extract the main heading.
```

**Expected:** Claude uses Firecrawl MCP to fetch and parse the page with JavaScript rendering.

---

### Test Figma

First, share a Figma file URL with Claude, then ask:
```
Can you read the Figma file at [URL] and list its top-level frames?
```

**Expected:** Claude accesses the Figma API and retrieves file structure.

---

### Test Supabase

Ask Claude Code:
```
Can you list the tables in my Supabase database?
```

**Expected:** Claude connects to your Supabase project and queries the schema.

**Note:** The Supabase MCP is configured with `--read-only` flag for safety. Claude can query data but cannot modify tables.

---

## Troubleshooting

### MCP Not Showing in `/mcp list`

- Ensure `.env.mcp` exists and contains valid credentials
- Restart Claude Code completely
- Check for syntax errors in `.claude/settings.local.json`

### "API Key Invalid" Errors

- Verify the API key format matches expected format (see Step 1)
- Check for extra spaces or quotes in `.env.mcp`
- Regenerate the API key if needed

### Supabase MCP Not Connecting

- Verify your Supabase Access Token is valid
- Check that the project reference (`cexurvymsvbmqpigfzuj`) matches your project
- Ensure your Supabase project is active (not paused)

### Figma Token Expired

- Figma PATs can expire or be revoked
- Generate a new token in Figma Settings → Security
- Update `.env.mcp` with the new token
- Restart Claude Code

---

## Security Best Practices

1. **Never commit `.env.mcp`** - It's gitignored, but double-check before pushing
2. **Use read-only tokens** where possible (Supabase MCP uses `--read-only` flag)
3. **Rotate tokens regularly** - Regenerate API keys every 90 days
4. **Scope permissions tightly** - Figma tokens should only access needed files, Supabase tokens should use minimal scopes
5. **Don't share tokens** - Each developer should generate their own credentials

---

## MCP-Specific Features

### Context7

**Supported frameworks:**
- React, Next.js, Vue, Angular
- Python (FastAPI, Django, Flask)
- Node.js frameworks
- Database libraries

**Usage:**
- Automatically fetches docs when you ask about a framework/library
- Always provides version-specific information
- No need to explicitly call Context7 - it works transparently

---

### Firecrawl

**Features:**
- JavaScript rendering (handles SPAs)
- Batch scraping (multiple URLs)
- Structured data extraction
- Rate limiting and retries (5 attempts, 2s initial delay)

**Configuration:**
- `FIRECRAWL_RETRY_MAX_ATTEMPTS=5` - Max retry attempts
- `FIRECRAWL_RETRY_INITIAL_DELAY=2000` - Initial delay in milliseconds

---

### Figma

**Capabilities:**
- Read Figma files and frames
- Access components and styles
- Retrieve design tokens
- Export assets (images, SVGs)

**Limitations:**
- Cannot modify Figma files (read-only access)
- Requires file URLs or file IDs

---

### Supabase

**Features:**
- Query database tables
- View project logs
- Access migrations
- Monitor project health

**Configuration:**
- `--read-only` flag prevents modifications
- `--project-ref` scopes access to specific project

**Limitations:**
- Cannot create/modify tables in read-only mode
- Cannot execute destructive operations

---

## Additional Resources

- [Official MCP Registry](https://registry.modelcontextprotocol.io/)
- [Claude Code MCP Documentation](https://code.claude.com/docs/en/mcp)
- [Context7 Documentation](https://context7.com/docs)
- [Firecrawl MCP Server Docs](https://docs.firecrawl.dev/mcp-server)
- [Figma MCP Guide](https://help.figma.com/hc/en-us/articles/32132100833559-Guide-to-the-Figma-MCP-server)
- [Supabase MCP Getting Started](https://supabase.com/docs/guides/getting-started/mcp)

---

## Support

If you encounter issues with MCP configuration:

1. Check the [Troubleshooting](#troubleshooting) section above
2. Verify credentials in `.env.mcp`
3. Review logs in Claude Code (if available)
4. Check each MCP's official documentation linked above

For project-specific questions, refer to [CLAUDE.md](../../CLAUDE.md).
