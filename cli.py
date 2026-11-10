#!python

import sys
import json
import time
import urllib.request
import argparse
import re
import os
import base64

from datetime import datetime
from urllib.request import Request
from urllib.request import urlopen

# Define our defaults here:
INFERENCE_URL   = "http://127.0.0.1:9931"
MCP_URL         = "http://127.0.0.1:4470/mcp"
MCP_DIRECTORY   = ""
SYSTEM_PROMPT   = "You are a helpful assistant with access to tools. Use them when appropriate."
INTERACTIVE     = 0
VERBOSE         = 0
COLOR           = 1
CONVERSATION    = ""
OPENAI_API_KEY  = ""

# Allow changing the settings via our environment variables:
globals().update(os.environ)

# Arguments take top priority:
ARG_PARSER = argparse.ArgumentParser(description="Simple MCP Chat CLI")

ARG_PARSER.add_argument("--inference-url", type=str, help="The address of the OpenAI-compatible llama.cpp (or alternative) inference server, e.g. http://localhost:9931 without the forward slash", default=INFERENCE_URL)
ARG_PARSER.add_argument("--mcp-url", type=str, help="The address of the FastMCP MCP server, e.g. http://localhost:8000/mcp including the /mcp portion", default=MCP_URL)
ARG_PARSER.add_argument("--mcp-directory", type=str, help="Call the change_directory tool to the given directory", default=MCP_DIRECTORY)
ARG_PARSER.add_argument("--system-prompt", type=str, help="The system prompt to be used, e.g. the first message sent by system", default=SYSTEM_PROMPT)
ARG_PARSER.add_argument("--prompt", type=str, help="Single-turn prompt", default="")
ARG_PARSER.add_argument("--interactive", action="store_true", help="Enable interactive mode", default=INTERACTIVE)
ARG_PARSER.add_argument("--verbose", action="store_true", help="Enable verbose logging", default=VERBOSE)
ARG_PARSER.add_argument("--color", action="store_true", help="Enable color", default=COLOR)
ARG_PARSER.add_argument("--conversation", type=str, help="The named conversation to continue", default=CONVERSATION)
ARG_PARSER.add_argument("--file", action="append")
ARG_PARSER.add_argument("--auto", action="store_true")

ARGS = ARG_PARSER.parse_args()



# The colors class below is from:
# https://www.geeksforgeeks.org/print-colors-python-terminal
class colors:
    reset           = "\033[0m"     if ARGS.color else ""
    bold            = "\033[01m"    if ARGS.color else ""
    disable         = "\033[02m"    if ARGS.color else ""
    underline       = "\033[04m"    if ARGS.color else ""
    reverse         = "\033[07m"    if ARGS.color else ""
    strikethrough   = "\033[09m"    if ARGS.color else ""
    invisible       = "\033[08m"    if ARGS.color else ""
     
    class fg:
        white       = "\033[97m"    if ARGS.color else ""
        black       = "\033[30m"    if ARGS.color else ""
        red         = "\033[31m"    if ARGS.color else ""
        green       = "\033[32m"    if ARGS.color else ""
        orange      = "\033[33m"    if ARGS.color else ""
        blue        = "\033[34m"    if ARGS.color else ""
        purple      = "\033[35m"    if ARGS.color else ""
        cyan        = "\033[36m"    if ARGS.color else ""
        lightgrey   = "\033[37m"    if ARGS.color else ""
        darkgrey    = "\033[90m"    if ARGS.color else ""
        lightred    = "\033[91m"    if ARGS.color else ""
        lightgreen  = "\033[92m"    if ARGS.color else ""
        yellow      = "\033[93m"    if ARGS.color else ""
        lightblue   = "\033[94m"    if ARGS.color else ""
        pink        = "\033[95m"    if ARGS.color else ""
        lightcyan   = "\033[96m"    if ARGS.color else ""

    class bg:
        black       = "\033[40m"    if ARGS.color else ""
        red         = "\033[41m"    if ARGS.color else ""
        green       = "\033[42m"    if ARGS.color else ""
        orange      = "\033[43m"    if ARGS.color else ""
        blue        = "\033[44m"    if ARGS.color else ""
        purple      = "\033[45m"    if ARGS.color else ""
        cyan        = "\033[46m"    if ARGS.color else ""
        lightgrey   = "\033[47m"    if ARGS.color else ""

if __name__ == "__main__":

    def log(*input_args):
        print(
            "".join(input_args),
            end="",
            flush=True)

    def save_messages(messages, file_name):
        with open(file_name, "w") as f:
            f.write(json.dumps(messages, indent=4))

    def load_messages(file_name):
        with open(file_name, "r") as f:
            data = f.read()
            data_json = json.loads(data)
            return data_json

    ARGS.inference_url   = re.sub(r"\/$", "", ARGS.inference_url)
    ARGS.mcp_url         = re.sub(r"\/$", "", ARGS.mcp_url)
    ARGS.system_prompt   = ARGS.system_prompt.strip()

    script_dir      = os.path.dirname(os.path.abspath(__file__))
    skills_dir      = f"{script_dir}{os.sep}skills"
    dated_timestamp = datetime.now().strftime("%A, %B %d, %Y at %X")

    complete_system_prompt = ""
    complete_system_prompt += f"The current date and time is {dated_timestamp}\n\n"
    complete_system_prompt += f"{ARGS.system_prompt}\n\n"

    # Temporarily removing skills, may be removed entirely:
    """
    for filename in sorted(os.listdir(skills_dir)):
        if filename.endswith(".md"):
            skill_path = f"{skills_dir}{os.sep}{filename}"

            with open(skill_path, "r", encoding="utf-8") as f:
                skill_text = f.read().strip()
                complete_system_prompt += f"Skill {filename}\n{skill_text}\n\n"
    """

    complete_system_prompt = complete_system_prompt.strip()

    messages = [{"role": "system", "content": complete_system_prompt}]

    def run_inference(messages, tools=None):
        """Call the LLM endpoint."""
        payload = {
            "model":        "qwen3.8-27b",
            "messages":     messages,
            "temperature":  0.7,
            "stream":       True
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        
        complete_content    = []
        complete_tool_calls = []
        finish_reason       = None
        role                = None

        data = json.dumps(payload).encode("utf-8")

        headers = {
            "Content-Type": "application/json"
        }

        if OPENAI_API_KEY is not None and len(OPENAI_API_KEY) > 0:
            headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"

        req = Request(
            f"{ARGS.inference_url}/v1/chat/completions",
            data=data,
            headers=headers,
            method="POST"
        )
        
        response = urlopen(req)

        buffer = b""
        is_reasoning = 0

        try:
            for chunk in iter(lambda: response.read(1024), b""):
                buffer += chunk
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)

                    line_text = line.decode("utf-8")
                    line_text = re.sub(r"^.*: ", "", line_text)
                    line_json = {}

                    #log(line_text)

                    try:
                        line_json = json.loads(line_text)
                    except:
                        continue
                
                    if "choices" not in line_json: continue

                    choice  = line_json["choices"][0]
                    delta   = choice["delta"]
                    role    = delta["role"] if "role" in delta else None

                    if "content" in delta:
                        chunk_content = delta["content"]

                        if chunk_content is not None:
                            if is_reasoning == 1:
                                is_reasoning = 0
                                log("\n\n")

                            if ARGS.verbose:
                                log(colors.fg.lightgrey)
                            log(chunk_content)
                            complete_content.append(chunk_content)

                    if "reasoning_content" in delta:
                        chunk_content = delta["reasoning_content"]

                        if chunk_content is not None:
                            if ARGS.verbose:
                                log(colors.fg.pink)
                                log(chunk_content)
                                complete_content.append(chunk_content)
                                is_reasoning = 1

                    if "tool_calls" in delta:
                        # Maybe this fixes things?
                        if is_reasoning == 1:
                            is_reasoning = 0
                            log("\n\n")

                        delta_tool_calls = delta["tool_calls"]
                        if delta_tool_calls:

                            tool_id_names = []

                            for tool_call_delta in delta_tool_calls:
                                idx = tool_call_delta.get("index")
                                if idx is not None:
                                    if len(complete_tool_calls) <= idx:
                                        complete_tool_calls.append({})
                                    
                                    if idx < len(complete_tool_calls):
                                        existing = complete_tool_calls[idx]

                                        if "id" in tool_call_delta:     existing["id"] = tool_call_delta["id"]
                                        if "type" in tool_call_delta:   existing["type"] = tool_call_delta["type"]
                                            
                                        if "function" in tool_call_delta:
                                            func_delta = tool_call_delta["function"]
                                            if "name" in func_delta:
                                                existing.setdefault("function", {})
                                                existing["function"].setdefault("name", "")
                                                existing["function"]["name"] += func_delta["name"]

                                                if idx > 0:
                                                    if not (idx, func_delta["name"]) in tool_id_names:
                                                        tool_id_names.append((idx, func_delta["name"]))

                                                        if ARGS.verbose:
                                                            log("\n\n")

                                                if ARGS.verbose:
                                                    log(colors.fg.darkgrey, "Calling ", colors.fg.lightgreen, func_delta["name"], colors.fg.darkgrey, " using ")

                                            if "arguments" in func_delta:
                                                existing.setdefault("function", {})
                                                existing["function"].setdefault("arguments", "")
                                                existing["function"]["arguments"] += func_delta["arguments"]

                                                if ARGS.verbose:
                                                    log(colors.fg.lightcyan)
                                                    log(func_delta["arguments"])

                                        complete_tool_calls[idx] = existing
                                    else:
                                        complete_tool_calls.append(tool_call_delta)

                    if choice.get("finish_reason"):
                        finish_reason = choice["finish_reason"]

                        if finish_reason == "tool_calls" and ARGS.verbose: log("\n\n", colors.fg.lightgrey)
                        if finish_reason == "stop":
                            log("\n", colors.fg.lightgrey if ARGS.verbose else "")
                            log("\n" if ARGS.interactive else "")
        except KeyboardInterrupt:
            complete_tool_calls = []
            log("\n\n")
            pass

        return {
            "role":             role,
            "content":          "".join(complete_content) if complete_content else None,
            "tool_calls":       complete_tool_calls if complete_tool_calls else None,
            "finish_reason":    finish_reason
        }

    def call_mcp(method, params=None, session_id=None):
        """Call MCP endpoint."""
        payload = {
            "jsonrpc":  "2.0",
            "id":       int(time.time() * 1000) % 1_000_000,
            "method":   method,
            "params":   params or {}
        }

        headers = {
            "Content-Type": "application/json",
            "Accept":       "application/json, text/event-stream" 
        }

        if session_id:
            headers["Mcp-Session-Id"] = session_id

        data    = json.dumps(payload).encode("utf-8")
        req     = Request(ARGS.mcp_url, data=data, headers=headers, method="POST")


        with urlopen(req, timeout=600) as resp:
            raw             = resp.read().decode("utf-8")
            resp_headers    = resp.headers


        new_session_id      = resp_headers.get("Mcp-Session-Id")

        # The SSE stuff:
        raw_text = raw
        events = raw_text.strip().split("\n\n")
        result = None
        for event in events:
            if not event.strip(): continue
            lines = event.split("\n")

            data_parts = []

            for line in lines:
                if re.match(r"data", line):
                    line = re.sub(r"^data: ", "", line)
                    data_parts.append(line)
            
            if data_parts:
                json_str = "\n".join(data_parts)
                try:
                    result = json.loads(json_str)
                    break
                except:
                    for part in data_parts:
                        try:
                            result = json.loads(part)
                            break
                        except:
                            continue

        return result, new_session_id

    # Get the first session ID
    init_resp, session_id = call_mcp(
        "initialize",
        {
            "protocolVersion":  "2024-11-05",
            "capabilities":     {},
            "clientInfo":       {"name": "simple_chat", "version": "0.1.0"}
        })
    
    call_mcp("notifications/initialized", session_id=session_id)

    tools_resp, _   = call_mcp("tools/list", session_id=session_id)
    mcp_tools       = tools_resp.get("result", {}).get("tools", [])

    if not mcp_tools:
        print("Warning: No tools discovered.")


    # We have to format the to
    openai_tools = []

    for t in mcp_tools:
        openai_tools.append({
            "type": "function",
            "function":
            {
                "name":         t["name"],
                "description":  t.get("description", ""),
                "parameters":   t.get("inputSchema", {"type": "object", "properties": {}})
            }
        })

    try:
        if len(ARGS.conversation) > 0:
            messages = load_messages(ARGS.conversation)
    except:
        pass

    if ARGS.file is None:
        ARGS.file = []

    for fi in ARGS.file:
        mime_type = "text/plain"
        mime_types = [
            ["image/png",   r"\.png$"],
            ["image/jpeg",  r"\.jpe?g$"],
            ["image/gif",   r"\.gif$"],
        ]

        for m in mime_types:
            if re.search(m[1], fi, flags=re.IGNORECASE):
                mime_type = m[0]

        if mime_type == "text/plain":
            with open(fi, "r") as f:
                text_str = f.read()
                messages.append({"role": "user", "content": text_str.strip()})
            continue
        
        with open(fi, "rb") as f:
            b64_str = base64.b64encode(f.read()).decode("utf-8")

        messages.append({
            "role": "user",
            "content": [{
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{b64_str}"
                }
            }]
        })

    turns_taken = 0

    # Forcibly enter interactive mode if no prompt was supplied via the CLI:
    if len(ARGS.prompt) < 1:
        ARGS.interactive = True
        turns_taken = 1

    if ARGS.interactive:
        log("\n")
        
    # Immediately change the MCP Server's directory
    if ARGS.mcp_directory:
        call_mcp(
            "tools/call",
            {
                "name":         "change_directory",
                "arguments":    { "path": ARGS.mcp_directory }
            },
            session_id=session_id)

    while True:
        # Clever way to control when we ask for the user's input:
        if turns_taken > 0:
            if ARGS.interactive == True:
                log(colors.fg.yellow, "> ")
                ARGS.prompt = input()
                log("\n", colors.fg.lightgrey)

        # At this point, the prompt is always either from the CLI or user input:
        messages.append({"role": "user", "content": ARGS.prompt})
        
        if len(ARGS.conversation) > 0:
            save_messages(messages, ARGS.conversation)

        # Max out at 100 turns for now...
        for r in range(100):
            try:
                resp = run_inference(messages, tools=openai_tools)
            except KeyboardInterrupt:
                log("\n\n")
                break

            # Append Assistant Response
            msg_to_append = {"role": "assistant", "content": resp["content"]}
            if resp["tool_calls"]:
                msg_to_append["tool_calls"] = resp["tool_calls"]
            messages.append(msg_to_append)
            
            if len(ARGS.conversation) > 0:
                save_messages(messages, ARGS.conversation)

            # If no tool calls, we are done with this turn
            if not resp["tool_calls"]:
                break

            # Execute Tool Calls
            for c in resp["tool_calls"]:
                tool_name = c["function"]["name"]
                try:
                    tool_args = c["function"]["arguments"]
                    if isinstance(tool_args, str):
                        tool_args = json.loads(tool_args)
                except:
                    tool_args = {}

                # Call MCP Tool
                tool_resp, _ = call_mcp(
                    "tools/call",
                    {
                        "name":         tool_name,
                        "arguments":    tool_args
                    },
                    session_id=session_id)
                    
                if not tool_resp:
                    continue
                
                result_content = tool_resp.get("result", {}).get("content", [])
                result_text = ""

                for item in result_content:
                    if item.get("type") == "text":
                        result_text += item.get("text", "")
                    elif item.get("type") == "image":
                        result_text += f"[image: {item.get("mimeType")}]"

                        mime_type = item.get("mimeType")
                        b64_str = item.get("data")

                        messages.append({
                            "role": "user",
                            "content": [{
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{b64_str}"
                                }
                            }]
                        })

                    else:
                        result_text += json.dumps(item)
                
                truncated = result_text[:500] + ("..." if len(result_text) > 500 else "")

                if ARGS.verbose:
                    log(colors.fg.darkgrey, "```\n", truncated, "\n```\n\n")

                # Append Tool Result to messages
                messages.append({
                    "role":         "tool",
                    "tool_call_id": c["id"],
                    "content":      result_text
                })

                if len(ARGS.conversation) > 0:
                    save_messages(messages, ARGS.conversation)

        turns_taken = turns_taken + 1

        if not ARGS.interactive:
            break
