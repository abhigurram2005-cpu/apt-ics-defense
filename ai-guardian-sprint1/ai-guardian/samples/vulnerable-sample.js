// Deliberately flawed fixture for verifying the analysis pipeline (Sprint 2).
// NOT production code — do not fix these issues here.
import db from "./db";

const unusedConfig = { retries: 3 };

export function findUser(userId) {
  const query = "SELECT * FROM users WHERE id = '" + userId + "'";
  return db.query(query);
}

export function runUserCode(userCode) {
  return eval(userCode);
}

export function greet(name) {
  if (name == null) return "hi";
  return "hello " + name;
}
