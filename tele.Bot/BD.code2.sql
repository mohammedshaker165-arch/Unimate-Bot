CREATE DATABASE IF NOT EXISTS unimate_assitant_materials;
USE unimate_assitant_materials;

CREATE TABLE IF NOT EXISTS materials (
    course_id VARCHAR(50) NOT NULL,       -- e.g., 'dl5', 'dm1'
    material_type VARCHAR(20) NOT NULL,   -- 'lec', 'prac', or 'q'
    part_number INT NOT NULL,             -- The specific part (1 to 12)
    file_id VARCHAR(255) NOT NULL,        -- The Telegram File ID or URL    
    -- Updated Primary Key to allow multiple parts per course/type
    PRIMARY KEY (course_id, material_type, part_number)
) ENGINE=InnoDB;

-- Optional example (replace the placeholder before running):
-- INSERT INTO materials (course_id, material_type, part_number, file_id)
-- VALUES ('da4', 'lec', 1, 'replace_with_telegram_file_id');
-- To see your data
SELECT * FROM materials;