const { DatabaseSync } = require('node:sqlite');
const path = require('node:path');

const DB_PATH = path.join(__dirname, 'users.db');

function getDb() {
  return new DatabaseSync(DB_PATH);
}

function initDb() {
  const db = getDb();
  db.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT UNIQUE NOT NULL,
      password TEXT NOT NULL,
      full_name TEXT NOT NULL,
      role TEXT DEFAULT 'Student',
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
  `);

  const countRow = db.prepare('SELECT COUNT(*) as count FROM users').get();
  if (countRow.count === 0) {
    const insert = db.prepare('INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)');
    insert.run('admin', 'admin123', 'System Administrator', 'Administrator');
    insert.run('john_doe', 'password123', 'John Doe', 'Student');
    insert.run('alice', 'securePass2024', 'Alice Smith', 'Instructor');
    console.log('Database initialized and pre-seeded with sample users.');
  }
  db.close();
}

function validateUser(username, password) {
  const db = getDb();
  const query = db.prepare('SELECT id, username, password, full_name, role FROM users WHERE username = ? AND password = ?');
  const user = query.get(username.trim(), password.trim());
  db.close();
  return user || null;
}

function createUser(username, password, fullName, role = 'Student') {
  const db = getDb();
  try {
    const insert = db.prepare('INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)');
    const result = insert.run(username.trim(), password.trim(), fullName.trim(), (role || 'Student').trim());
    db.close();
    return { success: true, id: result.lastInsertRowid };
  } catch (err) {
    db.close();
    if (err.message && err.message.includes('UNIQUE constraint failed')) {
      return { success: false, error: 'Username already exists in the database.' };
    }
    return { success: false, error: err.message };
  }
}

function getAllUsers() {
  const db = getDb();
  const users = db.prepare('SELECT id, username, password, full_name, role, created_at FROM users ORDER BY id ASC').all();
  db.close();
  return users;
}

module.exports = {
  initDb,
  validateUser,
  createUser,
  getAllUsers
};

if (require.main === module) {
  initDb();
  console.log('Users in DB:');
  console.log(getAllUsers());
}
