#!/usr/bin/env python3
"""
In-memory unit tests for ValidationHandler and Database functions (Sandbox safe - zero network sockets required)
"""

import io
import urllib.parse
from server import ValidationHandler, read_template
import database

class MockSocket:
    def __init__(self, data=b""):
        self._data = data

    def makefile(self, mode="r", *args, **kwargs):
        if "b" in mode:
            return io.BytesIO(self._data)
        return io.StringIO(self._data.decode("utf-8"))

    def sendall(self, data):
        pass

def run_mock_request(method, path, body=b"", headers=None):
    if headers is None:
        headers = {}
    
    # Construct raw HTTP request
    header_lines = [f"{method} {path} HTTP/1.1", "Host: localhost"]
    for k, v in headers.items():
        header_lines.append(f"{k}: {v}")
    if body and "Content-Length" not in headers:
        header_lines.append(f"Content-Length: {len(body)}")
    raw_req = ("\r\n".join(header_lines) + "\r\n\r\n").encode("utf-8") + body

    sock = MockSocket(raw_req)
    
    class TestHandler(ValidationHandler):
        def __init__(self):
            self.client_address = ("127.0.0.1", 12345)
            self.rfile = io.BytesIO(raw_req)
            self.wfile = io.BytesIO()
            self.raw_requestline = self.rfile.readline()
            self.parse_request()

        def log_message(self, format, *args):
            # Suppress console log spam during tests
            pass

    handler = TestHandler()
    if method == "GET":
        handler.do_GET()
    elif method == "POST":
        handler.do_POST()

    handler.wfile.seek(0)
    response_bytes = handler.wfile.read()
    response_text = response_bytes.decode("utf-8", errors="replace")
    return response_text

def main():
    print("Running in-memory verification tests...")
    database.init_db()

    # Test 1: GET /
    resp_get = run_mock_request("GET", "/")
    assert "User Validation" in resp_get, "GET / did not contain User Validation header"
    assert '<form action="/login" method="POST">' in resp_get, "GET / missing login form"
    print("✓ Test 1: GET / returns login page with form")

    # Test 2: POST /login with valid admin credentials
    body_admin = urllib.parse.urlencode({"username": "admin", "password": "admin123"}).encode("utf-8")
    resp_login_success = run_mock_request(
        "POST", 
        "/login", 
        body=body_admin, 
        headers={"Content-Type": "application/x-www-form-urlencoded", "Content-Length": str(len(body_admin))}
    )
    assert "Login Successful!" in resp_login_success, "Success heading missing"
    assert "System Administrator" in resp_login_success, "User full name missing"
    assert "Authentication Passed" in resp_login_success, "Success alert missing"
    print("✓ Test 2: POST /login with valid credentials returns Successful Login Page")

    # Test 3: POST /login with invalid password
    body_invalid_pass = urllib.parse.urlencode({"username": "admin", "password": "wrongpassword"}).encode("utf-8")
    resp_login_fail = run_mock_request(
        "POST", 
        "/login", 
        body=body_invalid_pass, 
        headers={"Content-Type": "application/x-www-form-urlencoded", "Content-Length": str(len(body_invalid_pass))}
    )
    assert "Login Failed" in resp_login_fail, "Failure heading missing"
    assert "Authentication Failure" in resp_login_fail, "Failure alert missing"
    print("✓ Test 3: POST /login with invalid password returns Failure Message")

    # Test 4: POST /login with non-existent user
    body_unknown_user = urllib.parse.urlencode({"username": "unknown_user", "password": "anypassword"}).encode("utf-8")
    resp_unknown = run_mock_request(
        "POST", 
        "/login", 
        body=body_unknown_user, 
        headers={"Content-Type": "application/x-www-form-urlencoded", "Content-Length": str(len(body_unknown_user))}
    )
    assert "Login Failed" in resp_unknown, "Failure heading missing for unknown user"
    assert "unknown_user" in resp_unknown, "Unknown username not shown"
    print("✓ Test 4: POST /login with unknown user returns Failure Message")

    # Test 5: Register new user (use unique username or clean up)
    import time
    unique_user = f"student_{int(time.time())}"
    body_reg = urllib.parse.urlencode({
        "username": unique_user,
        "password": "mypassword456",
        "full_name": "Lab Candidate",
        "role": "Researcher"
    }).encode("utf-8")
    resp_reg = run_mock_request(
        "POST", 
        "/register", 
        body=body_reg, 
        headers={"Content-Type": "application/x-www-form-urlencoded", "Content-Length": str(len(body_reg))}
    )
    assert "303 See Other" in resp_reg or "Location: /?registered=1" in resp_reg, "Registration should redirect"
    print("✓ Test 5: POST /register creates new user in database and redirects")

    # Test 6: Login with newly registered user
    body_new_login = urllib.parse.urlencode({"username": unique_user, "password": "mypassword456"}).encode("utf-8")
    resp_new_login = run_mock_request(
        "POST", 
        "/login", 
        body=body_new_login, 
        headers={"Content-Type": "application/x-www-form-urlencoded", "Content-Length": str(len(body_new_login))}
    )
    assert "Login Successful!" in resp_new_login, "Newly registered user login failed"
    assert "Lab Candidate" in resp_new_login, "New user name not shown on success page"
    assert "Researcher" in resp_new_login, "New user role not shown on success page"
    print("✓ Test 6: POST /login with newly created user succeeds")

    # Test 7: GET /users
    resp_users = run_mock_request("GET", "/users")
    assert "Database Users" in resp_users, "Users page heading missing"
    assert unique_user in resp_users, "New user not in users list"
    print("✓ Test 7: GET /users displays all database records")

    print("\n-------------------------------------------")
    print("ALL 7 IN-MEMORY VALIDATION TESTS PASSED!")
    print("-------------------------------------------")

if __name__ == "__main__":
    main()
