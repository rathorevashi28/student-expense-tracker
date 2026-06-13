-- Run this in MySQL Workbench to set up the database
-- Or the app creates tables automatically on first run

CREATE DATABASE IF NOT EXISTS expense_tracker;
USE expense_tracker;

CREATE TABLE IF NOT EXISTS users (
    id       INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80)  UNIQUE NOT NULL,
    password VARCHAR(200) NOT NULL,
    budget   FLOAT DEFAULT 5000,
    created  DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS expenses (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT NOT NULL,
    type       ENUM('expense','income') NOT NULL,
    amount     FLOAT NOT NULL,
    category   VARCHAR(50),
    note       VARCHAR(200),
    date       DATE NOT NULL,
    created    DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS budgets (
    id       INT AUTO_INCREMENT PRIMARY KEY,
    user_id  INT NOT NULL,
    month    INT NOT NULL,
    year     INT NOT NULL,
    amount   FLOAT NOT NULL,
    UNIQUE KEY uniq_budget (user_id, month, year),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
