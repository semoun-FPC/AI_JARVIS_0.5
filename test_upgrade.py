#!/usr/bin/env python3
"""Quick test of the upgraded Jarvis conversational features."""

import sys

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import jarvis

print("=" * 60)
print("Testing Jarvis Conversational Upgrade")
print("=" * 60)

print("\n[Test 1: Greeting]")
jarvis.handle_command('hello')

print("\n[Test 2: Status Report]")
jarvis.handle_command('status report')

print("\n[Test 3: Personal Question]")
jarvis.handle_command('how are you')

print("\n[Test 4: Help Command]")
jarvis.handle_command('help')

print("\n[Test 5: Specific Board Command]")
jarvis.handle_command('specific raspberry pi blink led')

print("\n" + "=" * 60)
print("All tests completed!")
print("=" * 60)
