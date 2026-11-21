#!/usr/bin/env python3
"""
Automated Verification Test Suite for User Validation Web Application
Tests:
  1. Server initialization & database table seeding
  2. GET / (Login page form delivery)
  3. POST /login with valid credentials -> Successful Login Page
  4. POST /login with invalid credentials -> Failure Message Page
  5. POST /register with new user -> Successful DB insert
  6. POST /login with new user credentials -> Successful Login Page
"""

import urllib.request
import urllib.parse
import threading
import time
import socketserver
import os
import sys

from server import ValidationHandler, PORT
import database

def run_test_server(port):
    database.init_db()
    server = socketserver.TCPServer(("127.0.0.1", port), ValidationHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    return server

def main():
    test_port = 8899
    print(f"Starting test server on http://127.0.0.1:{test_port}...")
    server = run_test_server(test_port)
    time.sleep(0.5)

    base_url = f"http://127.0.0.1:{test_port}"
    passed = 0
    total = 0

    def assert_test(name, condition, details=""):
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  [PASS] {name}")
        else:
            print(f"  [FAIL] {name}: {details}")

    print("\n--- Running Test Cases ---")

    # Test 1: GET /
    try:
        req = urllib.request.Request(f"{base_url}/")
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            assert_test(
                "GET / returns login form",
                resp.status == 200 and '<form action="/login" method="POST">' in content,
                "Form missing or status not 200"
            )
    except Exception as e:
        assert_test("GET / returns login form", False, str(e))

    # Test 2: POST /login with VALID credentials (admin / admin123)
    try:
        data = urllib.parse.urlencode({"username": "admin", "password": "admin123"}).encode("utf-8")
        req = urllib.request.Request(f"{base_url}/login", data=data, method="POST")
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            assert_test(
                "POST /login valid credentials returns Successful Login Page",
                resp.status == 200 and "Login Successful!" in content and "System Administrator" in content,
                "Success message or user full name not found in response"
            )
    except Exception as e:
        assert_test("POST /login valid credentials", False, str(e))

    # Test 3: POST /login with INVALID credentials (admin / wrongpass)
    try:
        data = urllib.parse.urlencode({"username": "admin", "password": "wrongpass"}).encode("utf-8")
        req = urllib.request.Request(f"{base_url}/login", data=data, method="POST")
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            assert_test(
                "POST /login invalid password returns Failure Message",
                resp.status == 200 and "Login Failed" in content and "Authentication Failure" in content,
                "Failure message not found in response"
            )
    except Exception as e:
        assert_test("POST /login invalid password", False, str(e))

    # Test 4: POST /login with NON-EXISTENT user
    try:
        data = urllib.parse.urlencode({"username": "ghost_user", "password": "anypassword"}).encode("utf-8")
        req = urllib.request.Request(f"{base_url}/login", data=data, method="POST")
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            assert_test(
                "POST /login non-existent user returns Failure Message",
                resp.status == 200 and "Login Failed" in content and "ghost_user" in content,
                "Failure page not displayed for non-existent user"
            )
    except Exception as e:
        assert_test("POST /login non-existent user", False, str(e))

    # Test 5: Register new user and login
    try:
        reg_data = urllib.parse.urlencode({
            "username": "new_tester",
            "password": "testerpass123",
            "full_name": "Test Engineer",
            "role": "QA"
        }).encode("utf-8")

        # Disable automatic redirect following to verify 303 redirect response
        class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None

        opener = urllib.request.build_opener(NoRedirectHandler)
        req = urllib.request.Request(f"{base_url}/register", data=reg_data, method="POST")
        try:
            resp = opener.open(req)
            code = resp.status
        except urllib.error.HTTPError as err:
            code = err.code

        assert_test("POST /register creates user and redirects", code in (302, 303), f"Received code {code}")

        # Now test login with the newly registered user
        login_data = urllib.parse.urlencode({"username": "new_tester", "password": "testerpass123"}).encode("utf-8")
        req2 = urllib.request.Request(f"{base_url}/login", data=login_data, method="POST")
        with urllib.request.urlopen(req2) as resp2:
            content2 = resp2.read().decode("utf-8")
            assert_test(
                "POST /login with newly registered user succeeds",
                resp2.status == 200 and "Login Successful!" in content2 and "Test Engineer" in content2,
                "Failed to login with newly registered user"
            )
    except Exception as e:
        assert_test("User registration and login flow", False, str(e))

    print(f"\nResult: {passed}/{total} tests passed.")
    server.shutdown()
    if passed == total:
        print("ALL TESTS PASSED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    main()
