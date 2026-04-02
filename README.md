# kb

A cli-based knowledge base for referencing commands and techniques. Built for fast lookup during engagements and study sessions.

## What it does

`kb` loads JSON files from `~/kb/` and gives you a searchable, self-categorised reference of commands with notes. Any `.json` file dropped into the directory is picked up automatically — no code changes needed.

## Usage

```
kb                        # show the full category tree
kb nmap                   # search for entries matching "nmap"
kb sql union              # search with multiple keywords (AND logic)
kb help 3                 # expand entry 3 from your last search
```

## Setup

```bash
git clone https://github.com/StarkSec/kb.git
mkdir -p ~/kb
# add your .json knowledge base files to ~/kb/
```

Optionally alias it in your shell config:

```bash
alias kb='python3 /path/to/kb.py'
```

## JSON format

Each `.json` file represents a category. Entries are nested objects — any node with a `cmd` key is treated as a leaf entry:

```json
{
  "enumeration": {
    "port-scanning": {
      "1": {
        "cmd": "nmap -sC -sV -oA scan 10.10.10.1",
        "note": "Default scripts + version detection with full output"
      }
    }
  }
}
```

You can nest as deep as you like — `kb` walks the tree recursively.

## Requirements

- Python 3.10+
- No external dependencies
