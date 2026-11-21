#!/usr/bin/env python3
"""
User Validation Web Application Server (Python Standard Library + SQLite)
Handles:
  - User login submission (POST /login)
  - Validation against database records
  - Success page on matching credentials
  - Failure page on invalid credentials
"""

import http.server
import socketserver
import urllib.parse
import os
import html
from datetime import datetime
import database

PORT = int(os.environ.get("PORT", 8000))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def read_template(filename):
    path = os.path.join(BASE_DIR, "templates", filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

class ValidationHandler(http.server.BaseHTTPRequestHandler):

    def send_html(self, content, status=200):
        data = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_file(self, file_path, content_type):
        if not os.path.isfile(file_path):
            self.send_error(404, "File Not Found")
            return
        with open(file_path, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query_params = urllib.parse.parse_qs(parsed_url.query)

        # Serve static assets (CSS, JS)
        if path.startswith("/public/css/"):
            file_name = os.path.basename(path)
            css_path = os.path.join(BASE_DIR, "public", "css", file_name)
            self.send_file(css_path, "text/css")
            return

        if path == "/" or path == "/login":
            prefill = html.escape(query_params.get("username", [""])[0])
            alert_html = ""
            if "registered" in query_params:
                alert_html = '<div class="alert alert-success">User created successfully! You can now log in with your credentials.</div>'

            template = read_template("login.html")
            template = template.replace("{{PREFILL_USERNAME}}", prefill)
            template = template.replace("{{ALERT_HTML}}", alert_html)
            self.send_html(template)
            return

        elif path == "/register":
            template = read_template("register.html")
            template = template.replace("{{ALERT_HTML}}", "")
            self.send_html(template)
            return

        elif path == "/users":
            users = database.get_all_users()
            rows_html = ""
            for u in users:
                rows_html += f"""
                <tr>
                  <td>#{u['id']}</td>
                  <td>{html.escape(u['full_name'])}</td>
                  <td><strong>{html.escape(u['username'])}</strong></td>
                  <td><span style="letter-spacing: 2px;">••••••••</span> <small style="color:var(--gray-600); font-family: monospace;">({html.escape(u['password'])})</small></td>
                  <td><span class="badge">{html.escape(u['role'])}</span></td>
                </tr>
                """
            template = read_template("users.html")
            template = template.replace("{{USER_ROWS}}", rows_html)
            self.send_html(template)
            return

        else:
            self.send_error(404, "Page Not Found")

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length).decode("utf-8")
        params = urllib.parse.parse_qs(post_data)

        if path == "/login":
            # Extract submitted username/login name & password
            username = params.get("username", [""])[0].strip()
            password = params.get("password", [""])[0].strip()

            # Check credentials against database
            user = database.validate_user(username, password)

            if user:
                # Credentials matched -> Return successful login page
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                template = read_template("success.html")
                template = template.replace("{{FULL_NAME}}", html.escape(user["full_name"]))
                template = template.replace("{{USERNAME}}", html.escape(user["username"]))
                template = template.replace("{{ROLE}}", html.escape(user["role"]))
                template = template.replace("{{USER_ID}}", str(user["id"]))
                template = template.replace("{{LOGIN_TIME}}", now_str)
                self.send_html(template, 200)
            else:
                # Credentials did not match -> Return failure message page
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                template = read_template("failure.html")
                template = template.replace("{{USERNAME}}", html.escape(username or "(blank)"))
                template = template.replace("{{USERNAME_ENCODED}}", urllib.parse.quote(username))
                template = template.replace("{{ATTEMPT_TIME}}", now_str)
                self.send_html(template, 200)

        elif path == "/register":
            username = params.get("username", [""])[0].strip()
            password = params.get("password", [""])[0].strip()
            full_name = params.get("full_name", [""])[0].strip()
            role = params.get("role", ["Student"])[0].strip()

            if not username or not password or not full_name:
                template = read_template("register.html")
                template = template.replace("{{ALERT_HTML}}", '<div class="alert alert-error">All fields are required.</div>')
                self.send_html(template, 400)
                return

            success, res = database.create_user(username, password, full_name, role)
            if success:
                # Redirect to login page with success param
                self.send_response(303)
                self.send_header("Location", "/?registered=1&username=" + urllib.parse.quote(username))
                self.end_headers()
            else:
                template = read_template("register.html")
                template = template.replace("{{ALERT_HTML}}", f'<div class="alert alert-error">{html.escape(res)}</div>')
                self.send_html(template, 400)
        else:
            self.send_error(404, "Endpoint Not Found")

def run(port=PORT):
    database.init_db()
    with socketserver.TCPServer(("", port), ValidationHandler) as httpd:
        print(f"==========================================================")
        print(f" User Validation Web Application running on port {port}")
        print(f" Open http://localhost:{port} in your browser")
        print(f" Database: {database.DB_PATH}")
        print(f"==========================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

if __name__ == "__main__":
    run()
