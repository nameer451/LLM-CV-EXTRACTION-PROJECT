-- =========================================
-- 1. TABLE CREATION (CORE SCHEMA)
-- =========================================

-- 1. CANDIDATES (Master Profile)
CREATE TABLE candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_by UUID,
    full_name TEXT NOT NULL,
    email TEXT,
    phone_number TEXT,
    total_experience_years FLOAT,
    research_summary TEXT,
    metadata JSONB,
    cv_file_path TEXT,
    processing_status TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. EDUCATION
CREATE TABLE education (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID REFERENCES candidates(id) ON DELETE CASCADE,
    degree_name TEXT,
    specialization TEXT,
    institution_name TEXT,
    grade_value FLOAT,
    grade_metric TEXT,
    passing_year INT,
    is_sse_hssc BOOLEAN DEFAULT FALSE,
    qs_ranking INT,
    the_ranking INT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. EXPERIENCE
CREATE TABLE experience (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID REFERENCES candidates(id) ON DELETE CASCADE,
    job_title TEXT,
    organization TEXT,
    location TEXT,
    start_date TEXT,
    end_date TEXT,
    is_current BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. CERTIFICATIONS
CREATE TABLE certifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID REFERENCES candidates(id) ON DELETE CASCADE,
    qualification_name TEXT,
    institution_name TEXT,
    passing_year INT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. AWARDS
CREATE TABLE awards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID REFERENCES candidates(id) ON DELETE CASCADE,
    award_type TEXT,
    detail TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. REFERENCES
CREATE TABLE references_table (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID REFERENCES candidates(id) ON DELETE CASCADE,
    reference_name TEXT,
    designation TEXT,
    address TEXT,
    phone TEXT,
    email TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. RESEARCH OUTPUTS
CREATE TABLE research_outputs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID REFERENCES candidates(id) ON DELETE CASCADE,
    title TEXT,
    venue_name TEXT,
    output_type TEXT CHECK (output_type IN ('Journal', 'Conference', 'Book', 'Patent', 'Unknown')),
    publication_year INT,
    impact_factor FLOAT,
    author_names TEXT,
    research_topics TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 8. SUPERVISION
CREATE TABLE supervision (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID REFERENCES candidates(id) ON DELETE CASCADE,
    student_name TEXT,
    degree_level TEXT CHECK (degree_level IN ('BS', 'MS', 'PhD', 'Unknown')),
    status TEXT CHECK (status IN ('Completed', 'Ongoing', 'Unknown')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 9. SKILLS
CREATE TABLE skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID REFERENCES candidates(id) ON DELETE CASCADE,
    skill_name TEXT NOT NULL,
    skill_category TEXT CHECK (skill_category IN ('Technical', 'Research', 'Soft', 'Tool', 'Unknown')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);


-- =========================================
-- 2. SECURITY (ROW LEVEL SECURITY)
-- =========================================

ALTER TABLE candidates ENABLE ROW LEVEL SECURITY;
ALTER TABLE education ENABLE ROW LEVEL SECURITY;
ALTER TABLE experience ENABLE ROW LEVEL SECURITY;
ALTER TABLE certifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE awards ENABLE ROW LEVEL SECURITY;
ALTER TABLE references_table ENABLE ROW LEVEL SECURITY;
ALTER TABLE research_outputs ENABLE ROW LEVEL SECURITY;
ALTER TABLE supervision ENABLE ROW LEVEL SECURITY;
ALTER TABLE skills ENABLE ROW LEVEL SECURITY;


-- =========================================
-- 3. POLICIES (READ ACCESS)
-- =========================================

CREATE POLICY "Allow authenticated read access" 
ON candidates FOR SELECT 
USING (auth.role() = 'authenticated');

CREATE POLICY "Allow authenticated read access" 
ON education FOR SELECT 
USING (auth.role() = 'authenticated');

CREATE POLICY "Allow authenticated read access" 
ON experience FOR SELECT 
USING (auth.role() = 'authenticated');

CREATE POLICY "Allow authenticated read access" 
ON certifications FOR SELECT 
USING (auth.role() = 'authenticated');

CREATE POLICY "Allow authenticated read access" 
ON awards FOR SELECT 
USING (auth.role() = 'authenticated');

CREATE POLICY "Allow authenticated read access" 
ON references_table FOR SELECT 
USING (auth.role() = 'authenticated');

CREATE POLICY "Allow authenticated read access" 
ON research_outputs FOR SELECT 
USING (auth.role() = 'authenticated');

CREATE POLICY "Allow authenticated read access" 
ON supervision FOR SELECT 
USING (auth.role() = 'authenticated');

CREATE POLICY "Allow authenticated read access" 
ON skills FOR SELECT 
USING (auth.role() = 'authenticated');


-- =========================================
-- 4. PERFORMANCE (INDEXES)
-- =========================================

CREATE INDEX idx_education_candidate_id ON education(candidate_id);
CREATE INDEX idx_experience_candidate_id ON experience(candidate_id);
CREATE INDEX idx_certifications_candidate_id ON certifications(candidate_id);
CREATE INDEX idx_awards_candidate_id ON awards(candidate_id);
CREATE INDEX idx_references_candidate_id ON references_table(candidate_id);
CREATE INDEX idx_research_outputs_candidate_id ON research_outputs(candidate_id);
CREATE INDEX idx_supervision_candidate_id ON supervision(candidate_id);
CREATE INDEX idx_skills_candidate_id ON skills(candidate_id);