-- =====================================================
-- DATABASE SETUP WITH TRIGGERS AND PROCEDURES
-- =====================================================

-- Create database
CREATE DATABASE IF NOT EXISTS job_application_tracker;
USE job_application_tracker;

-- =====================================================
-- TABLES
-- =====================================================

CREATE TABLE IF NOT EXISTS Users (
    UserID VARCHAR(10) PRIMARY KEY,
    FName VARCHAR(25) NOT NULL,
    LName VARCHAR(25) NOT NULL,
    Email VARCHAR(40) NOT NULL UNIQUE,
    UserPassword VARCHAR(255) NOT NULL,
    DOB DATE
);

CREATE TABLE IF NOT EXISTS Company (
    CompanyID VARCHAR(10) PRIMARY KEY,
    Company_Name VARCHAR(80) NOT NULL,
    Website VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS Recruitment (
    RecruitmentID VARCHAR(10) PRIMARY KEY,
    FName VARCHAR(25),
    LName VARCHAR(25),
    Phonenumber VARCHAR(15),
    CompanyID VARCHAR(10),
    Email VARCHAR(40) UNIQUE,
    SUPERVISOR VARCHAR(10),
    FOREIGN KEY (CompanyID) REFERENCES Company(CompanyID) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (SUPERVISOR) REFERENCES Recruitment(RecruitmentID) ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS Job (
    JobID VARCHAR(10) PRIMARY KEY,
    Dateofapplication DATE NOT NULL,
    Status ENUM('Applied', 'Interview', 'Rejected', 'Hired', 'Offered', 'Withdrawn') NOT NULL,
    Link VARCHAR(100),
    Role VARCHAR(50) NOT NULL,
    Updation_Date TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CompanyID VARCHAR(10),
    RecruitmentID VARCHAR(10),
    FOREIGN KEY (CompanyID) REFERENCES Company(CompanyID) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (RecruitmentID) REFERENCES Recruitment(RecruitmentID) ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS Interview (
    InterviewID VARCHAR(10) PRIMARY KEY,
    IDate DATE
);

CREATE TABLE IF NOT EXISTS Attachments (
    AttachmentID VARCHAR(10) PRIMARY KEY,
    File_url VARCHAR(100),
    File_Name VARCHAR(30),
    Type ENUM('Resume', 'Cover Letter','Portfolio','Others') NOT NULL,
    UserID VARCHAR(10),
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS Interview_Process (
    UserID VARCHAR(10),
    InterviewID VARCHAR(10),
    JobID VARCHAR(10),
    Mode ENUM('Online','Offline') NOT NULL,
    PRIMARY KEY (UserID, InterviewID, JobID),
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (InterviewID) REFERENCES Interview(InterviewID) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (JobID) REFERENCES Job(JobID) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS RoundsofInterview (
    InterviewID VARCHAR(10),
    Rounds INT CHECK(Rounds>0),
    RoundStatus ENUM('Pending','Completed','In Progress','Cancelled') NOT NULL,
    Description VARCHAR(255),
    FOREIGN KEY (InterviewID) REFERENCES Interview(InterviewID) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS UserPhone (
    UserID VARCHAR(10),
    PhoneNo VARCHAR(15),
    PRIMARY KEY (UserID, PhoneNo),
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS JobLocation (
    JobID VARCHAR(10),
    Street VARCHAR(35),
    City VARCHAR(20),
    PRIMARY KEY (JobID),
    FOREIGN KEY (JobID) REFERENCES Job(JobID) ON DELETE CASCADE ON UPDATE CASCADE
);

-- =====================================================
-- TRIGGERS
-- =====================================================

-- Trigger 1: Validate DOB (Date of Birth shouldn't be after today)
DELIMITER //
CREATE TRIGGER IF NOT EXISTS validate_dob
BEFORE INSERT ON Users
FOR EACH ROW
BEGIN
    IF NEW.DOB IS NOT NULL AND NEW.DOB >= CURDATE() THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'DOB must be before today';
    END IF;
END//

CREATE TRIGGER IF NOT EXISTS validate_dob_update
BEFORE UPDATE ON Users
FOR EACH ROW
BEGIN
    IF NEW.DOB IS NOT NULL AND NEW.DOB >= CURDATE() THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'DOB must be before today';
    END IF;
END//

-- Trigger 2: Validate phone number uniqueness
CREATE TRIGGER IF NOT EXISTS validate_phone_unique
BEFORE INSERT ON UserPhone
FOR EACH ROW
BEGIN
    IF EXISTS (SELECT 1 FROM UserPhone WHERE PhoneNo = NEW.PhoneNo AND UserID != NEW.UserID) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Error: Phone number already exists';
    END IF;
END//

CREATE TRIGGER IF NOT EXISTS validate_phone_unique_update
BEFORE UPDATE ON UserPhone
FOR EACH ROW
BEGIN
    IF EXISTS (SELECT 1 FROM UserPhone WHERE PhoneNo = NEW.PhoneNo AND UserID != NEW.UserID) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Error: Phone number already exists';
    END IF;
END//

-- Trigger 3: Auto-update interview status when rounds completed
CREATE TRIGGER IF NOT EXISTS update_interview_status
BEFORE UPDATE ON RoundsofInterview
FOR EACH ROW
BEGIN
    IF NEW.RoundStatus = 'Completed' AND OLD.RoundStatus != 'Completed' THEN
        IF NEW.Rounds <= 1 OR NEW.Rounds IS NULL THEN
            SET NEW.RoundStatus = 'Completed';
        END IF;
    END IF;
END//

-- Trigger 4: Validate recruitment email uniqueness
CREATE TRIGGER IF NOT EXISTS validate_recruitment_email
BEFORE INSERT ON Recruitment
FOR EACH ROW
BEGIN
    IF NEW.Email IS NOT NULL AND EXISTS (SELECT 1 FROM Recruitment WHERE Email = NEW.Email) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Error: Email already exists';
    END IF;
END//

CREATE TRIGGER IF NOT EXISTS validate_recruitment_email_update
BEFORE UPDATE ON Recruitment
FOR EACH ROW
BEGIN
    IF NEW.Email IS NOT NULL AND EXISTS (SELECT 1 FROM Recruitment WHERE Email = NEW.Email AND RecruitmentID != NEW.RecruitmentID) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Error: Email already exists';
    END IF;
END//

-- Trigger 5: Validate interview date is not in the past (if not allowed)
CREATE TRIGGER IF NOT EXISTS validate_interview_date
BEFORE INSERT ON Interview
FOR EACH ROW
BEGIN
    IF NEW.IDate < CURDATE() AND DAY(CURDATE()) - DAY(NEW.IDate) > 365 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Error: Interview date cannot be too far in the past (older than 1 year)';
    END IF;
END//

-- Trigger 6: Auto-generate InterviewID if not provided
CREATE TRIGGER IF NOT EXISTS auto_generate_interview_id
BEFORE INSERT ON Interview
FOR EACH ROW
BEGIN
    IF NEW.InterviewID IS NULL OR NEW.InterviewID = '' THEN
        SET NEW.InterviewID = CONCAT('I', LPAD(
            (SELECT COALESCE(MAX(CAST(SUBSTRING(InterviewID, 2) AS UNSIGNED)), 0) + 1 FROM Interview),
            3, '0'
        ));
    END IF;
END//

DELIMITER ;

-- =====================================================
-- STORED PROCEDURES
-- =====================================================

-- Procedure 1: Get application count for a user
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS getApplicationCount(IN user_id VARCHAR(10))
BEGIN
    SELECT COUNT(*) AS ApplicationCount
    FROM Job j
    WHERE j.JobID IN (
        SELECT DISTINCT JobID 
        FROM Interview_Process 
        WHERE UserID = user_id
    );
END//

-- Procedure 2: Get interview count for a user
CREATE PROCEDURE IF NOT EXISTS getUserInterviewCount(IN user_id VARCHAR(10))
BEGIN
    SELECT COUNT(*) AS InterviewCount
    FROM Interview_Process
    WHERE UserID = user_id;
END//

-- Procedure 3: Assign recruiter to job
CREATE PROCEDURE IF NOT EXISTS assignRecruiterToJob(
    IN job_id VARCHAR(10),
    IN recruiter_id VARCHAR(10)
)
BEGIN
    UPDATE Job
    SET RecruitmentID = recruiter_id
    WHERE JobID = job_id;
END//

-- Procedure 4: Schedule interview
CREATE PROCEDURE IF NOT EXISTS scheduleInterview(
    IN user_id VARCHAR(10),
    IN job_id VARCHAR(10),
    IN interview_date DATE,
    IN interview_mode ENUM('Online', 'Offline')
)
BEGIN
    DECLARE interview_id VARCHAR(10);
    DECLARE num_rounds INT DEFAULT 1;
    
    -- Generate interview ID
    SELECT CONCAT('I', LPAD(
        COALESCE((SELECT MAX(CAST(SUBSTRING(InterviewID, 2) AS UNSIGNED)) FROM Interview), 0) + 1,
        3, '0'
    )) INTO interview_id;
    
    -- Insert into Interview table
    INSERT INTO Interview (InterviewID, IDate)
    VALUES (interview_id, interview_date);
    
    -- Insert into Interview_Process
    INSERT INTO Interview_Process (UserID, InterviewID, JobID, Mode)
    VALUES (user_id, interview_id, job_id, interview_mode);
    
    -- Insert default round
    INSERT INTO RoundsofInterview (InterviewID, Rounds, RoundStatus, Description)
    VALUES (interview_id, num_rounds, 'Pending', 'Initial round scheduled.');
END//

DELIMITER ;

-- =====================================================
-- SAMPLE DATA
-- =====================================================

INSERT INTO Users (UserID, FName, LName, Email, UserPassword, DOB) VALUES
('U001', 'Alice', 'Smith', 'alice@example.com', 'password123', '1995-05-12'),
('U002', 'Bob', 'Johnson', 'bob@example.com', 'securepass', '1990-03-22'),
('U003', 'Charlie', 'Lee', 'charlie@example.com', 'mypassword', '1988-12-09'),
('U004', 'Diana', 'Brown', 'diana@example.com', 'passDiana', '1993-07-15'),
('U005', 'Ethan', 'Davis', 'ethan@example.com', 'ethanPass', '1997-10-02');

INSERT INTO Company (CompanyID, Company_Name, Website) VALUES
('C001', 'TechCorp', 'https://techcorp.com'),
('C002', 'InnovateX', 'https://innovatex.com'),
('C003', 'DevSolutions', 'https://devsolutions.com'),
('C004', 'WebGen', 'https://webgen.io'),
('C005', 'NextStep', 'https://nextstep.ai');

INSERT INTO Recruitment (RecruitmentID, FName, LName, Phonenumber, CompanyID, Email, SUPERVISOR) VALUES
('R001', 'Laura', 'King', '1234567890', 'C001', 'laura@techcorp.com', NULL),
('R002', 'Tom', 'Wills', '2345678901', 'C002', 'tom@innovatex.com', 'R001'),
('R003', 'Jane', 'Moore', '3456789012', 'C003', 'jane@devsolutions.com', NULL),
('R004', 'Mike', 'Taylor', '4567890123', 'C004', 'mike@webgen.io', 'R003'),
('R005', 'Sara', 'Clark', '5678901234', 'C005', 'sara@nextstep.ai', NULL);

INSERT INTO Job (JobID, Dateofapplication, Status, Link, Role, CompanyID, RecruitmentID) VALUES
('J001', '2023-10-10', 'Applied', 'https://job1.com', 'Software Engineer', 'C001', 'R001'),
('J002', '2024-02-14', 'Interview', 'https://job2.com', 'Data Analyst', 'C002', 'R002'),
('J003', '2024-05-08', 'Hired', 'https://job3.com', 'Frontend Developer', 'C003', 'R003'),
('J004', '2024-07-01', 'Rejected', 'https://job4.com', 'Backend Developer', 'C004', 'R004'),
('J005', '2024-08-20', 'Offered', 'https://job5.com', 'DevOps Engineer', 'C005', 'R005');

INSERT INTO Interview (InterviewID, IDate) VALUES
('I001', '2024-03-01'),
('I002', '2024-04-05'),
('I003', '2024-06-10'),
('I004', '2024-07-20'),
('I005', '2024-08-25');

INSERT INTO Attachments (AttachmentID, File_url, File_Name, Type, UserID) VALUES
('A001', 'http://files.com/resume1.pdf', 'Resume1', 'Resume', 'U001'),
('A002', 'http://files.com/cl1.pdf', 'CoverLetter1', 'Cover Letter', 'U002'),
('A003', 'http://files.com/portfolio1.pdf', 'Portfolio1', 'Portfolio', 'U003'),
('A004', 'http://files.com/resume2.pdf', 'Resume2', 'Resume', 'U004'),
('A005', 'http://files.com/other1.pdf', 'Cert1', 'Others', 'U005');

INSERT INTO Interview_Process (UserID, InterviewID, JobID, Mode) VALUES
('U001', 'I001', 'J001', 'Online'),
('U002', 'I002', 'J002', 'Offline'),
('U003', 'I003', 'J003', 'Online'),
('U004', 'I004', 'J004', 'Offline'),
('U005', 'I005', 'J005', 'Online');

INSERT INTO RoundsofInterview (InterviewID, Rounds, RoundStatus, Description) VALUES
('I001', 2, 'Completed', 'Initial screening and technical round.'),
('I002', 3, 'In Progress', 'HR, technical, and final interview.'),
('I003', 1, 'Completed', 'One technical round.'),
('I004', 2, 'Cancelled', 'Interview cancelled due to position closure.'),
('I005', 2, 'Pending', 'Scheduled for next week.');

INSERT INTO UserPhone (UserID, PhoneNo) VALUES
('U001', '9876543210'),
('U002', '8765432109'),
('U003', '7654321098'),
('U004', '6543210987'),
('U005', '5432109876');

INSERT INTO JobLocation (JobID, Street, City) VALUES
('J001', '123 Main St', 'New York'),
('J002', '456 Elm St', 'San Francisco'),
('J003', '789 Oak St', 'Seattle'),
('J004', '321 Pine St', 'Chicago'),
('J005', '654 Maple St', 'Austin');

-- =====================================================
-- COMPLETION MESSAGE
-- =====================================================

SELECT 'Database setup completed successfully!' AS Status;

