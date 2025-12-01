-- Supabase 테이블 생성 SQL 스크립트 (단일 사용자 프로젝트용)
-- File과 Quiz 테이블만 사용
-- Supabase 대시보드의 SQL Editor에서 실행하세요

-- 1. File 테이블 생성 (folder_id는 NULL 허용)
CREATE TABLE IF NOT EXISTS "File" (
    file_id BIGSERIAL PRIMARY KEY,
    folder_id BIGINT,  -- NULL 허용 (단일 사용자 프로젝트)
    title VARCHAR(255) NOT NULL,
    file_path VARCHAR(500),
    convert_file_path VARCHAR(500),
    summary_file_path VARCHAR(500),
    keywords TEXT,
    summary TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Quiz 테이블 생성
CREATE TABLE IF NOT EXISTS "Quiz" (
    quiz_id BIGSERIAL PRIMARY KEY,
    file_id BIGINT NOT NULL REFERENCES "File"(file_id) ON DELETE CASCADE,
    question VARCHAR(1000) NOT NULL,
    example VARCHAR(1000),
    correct_answer VARCHAR(500) NOT NULL,
    explanation VARCHAR(1000),
    user_answer VARCHAR(500),
    correct_is BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 인덱스 생성 (성능 향상)
CREATE INDEX IF NOT EXISTS idx_file_folder_id ON "File"(folder_id);
CREATE INDEX IF NOT EXISTS idx_quiz_file_id ON "Quiz"(file_id);

-- RLS (Row Level Security) 정책 설정
ALTER TABLE "File" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "Quiz" ENABLE ROW LEVEL SECURITY;

-- 모든 사용자가 접근 가능하도록 정책 생성 (개발용)
CREATE POLICY "Allow all operations on File" ON "File" FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations on Quiz" ON "Quiz" FOR ALL USING (true) WITH CHECK (true);

