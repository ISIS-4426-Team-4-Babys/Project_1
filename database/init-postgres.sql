-- Set pgcrypto extension to create ids
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create users table to store application users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('student', 'professor', 'admin')),
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

-- Relationship between courses and teachers 
-- 1 teacher teaches N courses
ALTER TABLE courses
ADD COLUMN taught_by UUID NOT NULL,
ADD CONSTRAINT fk_taught_by FOREIGN KEY (taught_by) REFERENCES users (id);

-- Relationship between courses and students
-- 1 student can take N courses
-- 1 course can have  N students
CREATE TABLE courses_students (
    course_id UUID NOT NULL,
    student_id UUID NOT NULL,
    PRIMARY KEY(course_id, student_id),
    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Create agents table to store application agents
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL, 
    is_working BOOLEAN NOT NULL,
    system_prompt TEXT NOT NULL,
    model VARCHAR(100) NOT NULL,
    language VARCHAR(20) NOT NULL CHECK (language IN ('es', 'en')),
    retrieval_k INT NOT NULL,
    associated_course UUID NOT NULL,
    CONSTRAINT fk_associated_course FOREIGN KEY (associated_course) REFERENCES courses (id) ON DELETE CASCADE
);

-- Create resources table to store application resources
CREATE TABLE resources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    filetype VARCHAR(100) NOT NULL,
    filepath TEXT NOT NULL,
    size INT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    consumed_by UUID NOT NULL,
    CONSTRAINT fk_consumed_by FOREIGN KEY (consumed_by) REFERENCES agents (id) ON DELETE CASCADE
);
