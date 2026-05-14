-- Add missing columns to main_loan table
ALTER TABLE main_loan ADD COLUMN IF NOT EXISTS amount decimal(12,2) NULL;
ALTER TABLE main_loan ADD COLUMN IF NOT EXISTS approved_line decimal(12,2) NULL;
ALTER TABLE main_loan ADD COLUMN IF NOT EXISTS remaining_balance decimal(12,2) NULL;
ALTER TABLE main_loan ADD COLUMN IF NOT EXISTS disbursed_date timestamp NULL;
ALTER TABLE main_loan ADD COLUMN IF NOT EXISTS status varchar(50) DEFAULT 'pending';

-- Add missing columns to main_member table
ALTER TABLE main_member ADD COLUMN IF NOT EXISTS civil_status varchar(50) NULL;
ALTER TABLE main_member ADD COLUMN IF NOT EXISTS nickname varchar(100) NULL;
ALTER TABLE main_member ADD COLUMN IF NOT EXISTS middle_initial varchar(10) NULL;
