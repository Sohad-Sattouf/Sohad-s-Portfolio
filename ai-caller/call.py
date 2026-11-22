#!/usr/bin/env python3
"""Place an outbound AI voice call through Bland AI.

The API key is NOT stored here. The session's network proxy adds it to
requests sent to api.bland.ai, so this script sends a placeholder.

Usage:
  python3 call.py --list-voices
  python3 call.py --to me --task "remind you about the meeting at 3 pm"          # preview only
  python3 call.py --to +14165550000 --task "confirm your appointment" --confirm  # places the call
  python3 call.py --status CALL_ID
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

API = "https://api.bland.ai/v1"
OWNER_NUMBER = os.environ.get("OWNER_PHONE", "")  # set OWNER_PHONE to use --to me
DEFAULT_VOICE = "mason"  # male voice; verify with --list-voices and change if needed
GREETING = "Hello, I am the AI assistant of Mr. Sohad Sattouf, and I am calling you to {task}."


def request(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        API + path,
        data=data,
        method=method,
        headers={"authorization": "placeholder", "content-type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code}: {e.read().decode(errors='replace')}")


def normalize(number):
    if number.lower() == "me":
        if not OWNER_NUMBER:
            sys.exit("Set OWNER_PHONE to use --to me")
        number = OWNER_NUMBER
    digits = re.sub(r"\D", "", number)
    if len(digits) == 10:
        digits = "1" + digits
    if not (11 <= len(digits) <= 15):
        sys.exit(f"Invalid phone number: {number}")
    return "+" + digits


def build_payload(to, task, voice):
    task = task.strip().rstrip(".")
    return {
        "phone_number": to,
        "voice": voice,
        "first_sentence": GREETING.format(task=task),
        "task": (
            "You are the AI assistant of Mr. Sohad Sattouf, making a phone call on his behalf. "
            f"You opened the call by saying: \"I am calling you to {task}.\" That is the purpose of the call. "
            "You have already introduced yourself and stated the purpose. Stay polite, brief and "
            "on topic. If asked, confirm you are an AI. If the person asks not to be called "
            "again, apologize, confirm, and end the call. When the purpose is done, thank them "
            "and say goodbye."
        ),
        "wait_for_greeting": True,
        "record": True,
        "max_duration": 5,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--to", help="phone number, or 'me' for the owner's number")
    p.add_argument("--task", help="what the call is for; completes 'I am calling you to ...'")
    p.add_argument("--voice", default=DEFAULT_VOICE)
    p.add_argument("--confirm", action="store_true", help="actually place the call")
    p.add_argument("--list-voices", action="store_true")
    p.add_argument("--status", metavar="CALL_ID", help="show details/transcript of a call")
    a = p.parse_args()

    if a.list_voices:
        print(json.dumps(request("GET", "/voices"), indent=2))
        return
    if a.status:
        print(json.dumps(request("GET", f"/calls/{a.status}"), indent=2))
        return
    if not (a.to and a.task):
        p.error("--to and --task are required")

    payload = build_payload(normalize(a.to), a.task, a.voice)
    print(json.dumps(payload, indent=2))
    if not a.confirm:
        print("\nPreview only. Add --confirm to place the call.")
        return
    print(json.dumps(request("POST", "/calls", payload), indent=2))


if __name__ == "__main__":
    main()
