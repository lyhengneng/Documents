#!/usr/bin/env python3
"""
WebSocket Test Script for OpenIM Server
This script tests the basic WebSocket connectivity and messaging
"""

import asyncio
import websockets
import json
import base64
import sys
import time

# Configuration
WS_HOST = "localhost"
WS_PORT = 10001
TEST_USER = "test_user_001"
TEST_TOKEN = "test_token"
OPERATION_ID = "test_operation_001"

# ANSI color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def print_success(message):
    print(f"{GREEN}✓ PASS{RESET}: {message}")

def print_error(message):
    print(f"{RED}✗ FAIL{RESET}: {message}")

def print_info(message):
    print(f"{YELLOW}ℹ INFO{RESET}: {message}")

def build_ws_url(compression=False):
    """Build WebSocket URL with query parameters"""
    base_url = f"ws://{WS_HOST}:{WS_PORT}/"
    params = {
        "token": TEST_TOKEN,
        "sendID": TEST_USER,
        "platformID": "1",
        "operationID": OPERATION_ID
    }
    if compression:
        params["compression"] = "gzip"
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    return f"{base_url}?{query_string}"

async def test_connection():
    """Test 1: Basic WebSocket connection"""
    print("\n" + "="*50)
    print("Test 1: Basic WebSocket Connection")
    print("="*50)

    uri = build_ws_url()

    try:
        async with websockets.connect(uri, ping_timeout=10) as websocket:
            print_success("Connected to WebSocket")

            # Wait for connection to establish
            await asyncio.sleep(1)

            # Send a ping
            await websocket.ping()
            print_success("Sent ping successfully")

            # Wait for pong
            await asyncio.sleep(1)

            print_success("Connection test passed")
            return True

    except Exception as e:
        print_error(f"Connection test failed: {e}")
        return False

async def test_message_send():
    """Test 2: Send a message"""
    print("\n" + "="*50)
    print("Test 2: Send Message")
    print("="*50)

    uri = build_ws_url()

    try:
        async with websockets.connect(uri, ping_timeout=10) as websocket:
            print_info("Connected to WebSocket")

            # Prepare message
            message_data = "Hello World from Python!"
            message = {
                "reqIdentifier": 1003,  # WSSendMsg
                "sendID": TEST_USER,
                "operationID": OPERATION_ID,
                "msgIncr": "msg_001",
                "data": base64.b64encode(message_data.encode()).decode()
            }

            print_info(f"Sending message: {message_data}")

            # Send message
            await websocket.send(json.dumps(message))
            print_success("Message sent successfully")

            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                print_success("Received response")
                print_info(f"Response: {response[:200]}...")  # Print first 200 chars

                return True
            except asyncio.TimeoutError:
                print_error("No response received within timeout")
                return False

    except Exception as e:
        print_error(f"Message send test failed: {e}")
        return False

async def test_compression():
    """Test 3: Connection with compression"""
    print("\n" + "="*50)
    print("Test 3: Connection with Compression")
    print("="*50)

    uri = build_ws_url(compression=True)

    try:
        async with websockets.connect(uri, ping_timeout=10) as websocket:
            print_success("Connected with compression enabled")

            # Send a message
            message_data = "Test message with compression"
            message = {
                "reqIdentifier": 1003,
                "sendID": TEST_USER,
                "operationID": OPERATION_ID,
                "msgIncr": "msg_002",
                "data": base64.b64encode(message_data.encode()).decode()
            }

            await websocket.send(json.dumps(message))
            print_success("Sent compressed message successfully")

            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            print_success("Received compressed response")

            return True

    except Exception as e:
        print_error(f"Compression test failed: {e}")
        return False

async def test_multiple_messages():
    """Test 4: Send multiple messages"""
    print("\n" + "="*50)
    print("Test 4: Send Multiple Messages")
    print("="*50)

    uri = build_ws_url()
    num_messages = 5

    try:
        async with websockets.connect(uri, ping_timeout=10) as websocket:
            print_info(f"Connected to WebSocket")
            print_info(f"Sending {num_messages} messages...")

            for i in range(num_messages):
                message_data = f"Message #{i+1}"
                message = {
                    "reqIdentifier": 1003,
                    "sendID": TEST_USER,
                    "operationID": OPERATION_ID,
                    "msgIncr": f"msg_{i+3:03d}",
                    "data": base64.b64encode(message_data.encode()).decode()
                }

                await websocket.send(json.dumps(message))
                print_info(f"Sent message #{i+1}")

                # Wait a bit between messages
                await asyncio.sleep(0.5)

            print_success(f"Successfully sent {num_messages} messages")

            # Receive responses
            responses_received = 0
            timeout_task = asyncio.create_task(asyncio.sleep(5))

            while responses_received < num_messages:
                try:
                    await asyncio.wait_for(websocket.recv(), timeout=1)
                    responses_received += 1
                except asyncio.TimeoutError:
                    break

            print_success(f"Received {responses_received} responses")
            return responses_received > 0

    except Exception as e:
        print_error(f"Multiple messages test failed: {e}")
        return False

async def test_heartbeat():
    """Test 5: Heartbeat/ping-pong"""
    print("\n" + "="*50)
    print("Test 5: Heartbeat/Ping-Pong")
    print("="*50)

    uri = build_ws_url()

    try:
        async with websockets.connect(uri, ping_timeout=10) as websocket:
            print_info("Connected to WebSocket")

            # Send multiple pings
            for i in range(3):
                await websocket.ping()
                print_info(f"Sent ping #{i+1}")
                await asyncio.sleep(1)

            print_success("Heartbeat test passed")
            return True

    except Exception as e:
        print_error(f"Heartbeat test failed: {e}")
        return False

async def run_all_tests():
    """Run all tests"""
    print("="*50)
    print("WebSocket Test Suite")
    print("="*50)
    print(f"WebSocket URL: ws://{WS_HOST}:{WS_PORT}")
    print(f"Test User: {TEST_USER}")
    print("="*50)

    tests = [
        ("Basic Connection", test_connection),
        ("Send Message", test_message_send),
        ("Compression", test_compression),
        ("Multiple Messages", test_multiple_messages),
        ("Heartbeat", test_heartbeat),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = await asyncio.wait_for(test_func(), timeout=15)
            results.append((test_name, result))
        except asyncio.TimeoutError:
            print_error(f"{test_name} timed out")
            results.append((test_name, False))
        except Exception as e:
            print_error(f"{test_name} encountered unexpected error: {e}")
            results.append((test_name, False))

    # Print summary
    print("\n" + "="*50)
    print("Test Summary")
    print("="*50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        if result:
            print_success(test_name)
        else:
            print_error(test_name)

    print("\n" + "-"*50)
    print(f"Total: {passed}/{total} tests passed")
    print("-"*50)

    if passed == total:
        print_success("All tests passed!")
        return 0
    else:
        print_error(f"{total - passed} test(s) failed")
        return 1

def main():
    """Main function"""
    print(f"\nWebSocket Test Script for OpenIM Server")
    print(f"Make sure the msggateway service is running on port {WS_PORT}")
    print(f"Start the service with: mage start")

    # Install dependencies if needed
    try:
        import websockets
    except ImportError:
        print("\nInstalling required dependencies...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
        print("Dependencies installed successfully\n")

    # Run tests
    try:
        exit_code = asyncio.run(run_all_tests())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)

if __name__ == "__main__":
    main()