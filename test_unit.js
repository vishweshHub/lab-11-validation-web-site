const assert = require('node:assert');
const database = require('./database');

console.log('Running Node.js validation test suite...');

database.initDb();

// Test 1: validate seeded user
const admin = database.validateUser('admin', 'admin123');
assert(admin !== null, 'admin login should succeed');
assert.strictEqual(admin.username, 'admin');
assert.strictEqual(admin.full_name, 'System Administrator');
console.log('✓ Test 1: Validate valid admin user credentials');

// Test 2: invalid password
const invalidPass = database.validateUser('admin', 'wrong_password');
assert.strictEqual(invalidPass, null, 'invalid password must return null');
console.log('✓ Test 2: Reject invalid password');

// Test 3: non-existent user
const ghostUser = database.validateUser('ghost_user', 'any_password');
assert.strictEqual(ghostUser, null, 'unknown user must return null');
console.log('✓ Test 3: Reject non-existent user');

// Test 4: create user
const uniqueNodeUser = 'node_user_' + Date.now();
const newUserResult = database.createUser(uniqueNodeUser, 'secretPass99', 'Node Tester', 'QA');
assert(newUserResult.success === true, 'create user should succeed');
console.log('✓ Test 4: Create new user in database');

// Test 5: validate new user
const nodeTester = database.validateUser(uniqueNodeUser, 'secretPass99');
assert(nodeTester !== null, 'new user login should succeed');
assert.strictEqual(nodeTester.username, uniqueNodeUser);
assert.strictEqual(nodeTester.full_name, 'Node Tester');
console.log('✓ Test 5: Validate new user credentials');

// Test 6: getAllUsers
const allUsers = database.getAllUsers();
assert(Array.isArray(allUsers) && allUsers.length >= 3, 'getAllUsers should return array of users');
console.log('✓ Test 6: Retrieve all database records');

console.log('\n-------------------------------------------');
console.log('ALL NODE.JS TESTS PASSED SUCCESSFULLY!');
console.log('-------------------------------------------');
