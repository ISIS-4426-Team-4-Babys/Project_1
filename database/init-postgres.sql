-- Set pgcrypto extension to create ids
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create users table to store application users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('student', 'professor', 'admin')),
    name VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    profile_image TEXT
);

-- Create courses table to store application courses
CREATE TABLE courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    code VARCHAR(20) NOT NULL UNIQUE,
    department VARCHAR(100) NOT NULL,
    description TEXT NOT NULL
);

-- Relationship between courses and teachers (1 teacher teaches N courses)
ALTER TABLE courses
ADD COLUMN professor_id UUID NOT NULL,
ADD CONSTRAINT fk_professor FOREIGN KEY (professor_id) REFERENCES users (id);
