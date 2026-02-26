-- Mr. Oldverdict Council Engine Schema
-- Run this in your Supabase SQL editor

-- Topics table
-- Stores raw ingested topics before they reach the Council
CREATE TABLE topics (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  raw_topic TEXT NOT NULL,
  category CHAR(1) CHECK (category IN ('A', 'B', 'C', 'D', 'E')) NOT NULL,
  source TEXT,
  engagement_score INTEGER DEFAULT 0,
  blacklist_cleared BOOLEAN DEFAULT FALSE,
  used BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Scripts table
-- Stores completed Mr. Oldverdict scripts with full Council output
-- This is the Council's long term memory
CREATE TABLE scripts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  topic_id UUID REFERENCES topics(id),
  category CHAR(1) CHECK (category IN ('A', 'B', 'C', 'D', 'E')) NOT NULL,
  raw_topic TEXT NOT NULL,
  scene TEXT NOT NULL,
  lines JSONB NOT NULL,
  prop TEXT,
  expression TEXT,
  theme_tags TEXT[] DEFAULT '{}',
  published BOOLEAN DEFAULT FALSE,
  published_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Connected scripts table
-- Tracks which scripts were connected by the Council for memory recall
CREATE TABLE script_connections (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  new_script_id UUID REFERENCES scripts(id),
  connected_script_id UUID REFERENCES scripts(id),
  connection_reason TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Videos table
-- Tracks assembled videos ready for publishing
CREATE TABLE videos (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  script_id UUID REFERENCES scripts(id),
  voice_file_url TEXT,
  image_url TEXT,
  video_url TEXT,
  caption TEXT,
  scheduled_at TIMESTAMP WITH TIME ZONE,
  published_youtube BOOLEAN DEFAULT FALSE,
  published_instagram BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_topics_category ON topics(category);
CREATE INDEX idx_topics_used ON topics(used);
CREATE INDEX idx_scripts_category ON scripts(category);
CREATE INDEX idx_scripts_theme_tags ON scripts USING GIN(theme_tags);
CREATE INDEX idx_scripts_published ON scripts(published);
CREATE INDEX idx_videos_scheduled_at ON videos(scheduled_at);
