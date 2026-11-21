#!/usr/bin/env node
/**
 * User Validation Web Application Server (Node.js native http + node:sqlite)
 * Zero external npm dependencies required.
 */

const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const querystring = require('node:querystring');
const url = require('node:url');
const database = require('./database');

const PORT = parseInt(process.env.PORT || '3000', 10);
const BASE_DIR = __dirname;

function readTemplate(filename) {
  return fs.readFileSync(path.join(BASE_DIR, 'templates', filename), 'utf8');
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

const server = http.createServer((req, res) => {
  const parsedUrl = url.parse(req.url, true);
  const pathname = parsedUrl.pathname;
  const method = req.method;

  // Serve static CSS
  if (method === 'GET' && pathname.startsWith('/public/css/')) {
    const filename = path.basename(pathname);
    const cssPath = path.join(BASE_DIR, 'public', 'css', filename);
    if (fs.existsSync(cssPath)) {
      const data = fs.readFileSync(cssPath);
      res.writeHead(200, { 'Content-Type': 'text/css' });
      return res.end(data);
    } else {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      return res.end('Not Found');
    }
  }

  // GET Routes
  if (method === 'GET') {
    if (pathname === '/' || pathname === '/login') {
      const prefill = escapeHtml(parsedUrl.query.username || '');
      let alertHtml = '';
      if (parsedUrl.query.registered) {
        alertHtml = '<div class="alert alert-success">User created successfully! You can now log in with your credentials.</div>';
      }

      let html = readTemplate('login.html');
      html = html.replace('{{PREFILL_USERNAME}}', prefill);
      html = html.replace('{{ALERT_HTML}}', alertHtml);

      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
      return res.end(html);
    }

    if (pathname === '/register') {
      let html = readTemplate('register.html');
      html = html.replace('{{ALERT_HTML}}', '');
      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
      return res.end(html);
    }

    if (pathname === '/users') {
      const users = database.getAllUsers();
      let rowsHtml = '';
      for (const u of users) {
        rowsHtml += `
          <tr>
            <td>#${u.id}</td>
            <td>${escapeHtml(u.full_name)}</td>
            <td><strong>${escapeHtml(u.username)}</strong></td>
            <td><span style="letter-spacing: 2px;">••••••••</span> <small style="color:var(--gray-600); font-family: monospace;">(${escapeHtml(u.password)})</small></td>
            <td><span class="badge">${escapeHtml(u.role)}</span></td>
          </tr>
        `;
      }

      let html = readTemplate('users.html');
      html = html.replace('{{USER_ROWS}}', rowsHtml);
      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
      return res.end(html);
    }

    res.writeHead(404, { 'Content-Type': 'text/plain' });
    return res.end('Page Not Found');
  }

  // POST Routes
  if (method === 'POST') {
    let body = '';
    req.on('data', chunk => {
      body += chunk.toString();
    });

    req.on('end', () => {
      const params = querystring.parse(body);

      if (pathname === '/login') {
        const username = (params.username || '').trim();
        const password = (params.password || '').trim();

        // Check credentials against database
        const user = database.validateUser(username, password);

        const now = new Date().toISOString().replace('T', ' ').substring(0, 19);

        if (user) {
          // Credentials matched -> Return successful login page
          let html = readTemplate('success.html');
          html = html.replace('{{FULL_NAME}}', escapeHtml(user.full_name));
          html = html.replace('{{USERNAME}}', escapeHtml(user.username));
          html = html.replace('{{ROLE}}', escapeHtml(user.role));
          html = html.replace('{{USER_ID}}', String(user.id));
          html = html.replace('{{LOGIN_TIME}}', now);

          res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
          return res.end(html);
        } else {
          // Credentials did not match -> Return failure message page
          let html = readTemplate('failure.html');
          html = html.replace(/{{USERNAME}}/g, escapeHtml(username || '(blank)'));
          html = html.replace('{{USERNAME_ENCODED}}', encodeURIComponent(username));
          html = html.replace('{{ATTEMPT_TIME}}', now);

          res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
          return res.end(html);
        }
      }

      if (pathname === '/register') {
        const username = (params.username || '').trim();
        const password = (params.password || '').trim();
        const fullName = (params.full_name || '').trim();
        const role = (params.role || 'Student').trim();

        if (!username || !password || !fullName) {
          let html = readTemplate('register.html');
          html = html.replace('{{ALERT_HTML}}', '<div class="alert alert-error">All fields are required.</div>');
          res.writeHead(400, { 'Content-Type': 'text/html; charset=utf-8' });
          return res.end(html);
        }

        const result = database.createUser(username, password, fullName, role);
        if (result.success) {
          res.writeHead(303, { Location: '/?registered=1&username=' + encodeURIComponent(username) });
          return res.end();
        } else {
          let html = readTemplate('register.html');
          html = html.replace('{{ALERT_HTML}}', `<div class="alert alert-error">${escapeHtml(result.error)}</div>`);
          res.writeHead(400, { 'Content-Type': 'text/html; charset=utf-8' });
          return res.end(html);
        }
      }

      res.writeHead(404, { 'Content-Type': 'text/plain' });
      return res.end('Endpoint Not Found');
    });
    return;
  }

  res.writeHead(405, { 'Content-Type': 'text/plain' });
  res.end('Method Not Allowed');
});

database.initDb();

server.listen(PORT, () => {
  console.log('==========================================================');
  console.log(` User Validation Web Application running on port ${PORT}`);
  console.log(` Open http://localhost:${PORT} in your browser`);
  console.log('==========================================================');
});
