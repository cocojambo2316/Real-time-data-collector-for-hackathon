CREATE TABLE IF NOT EXISTS parkings (
    name VARCHAR(255) PRIMARY KEY,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    address TEXT,
    manager VARCHAR(255),
    category VARCHAR(100),
    total_spots INT
);

CREATE TABLE IF NOT EXISTS parking_occupancy_logs (
    id BIGSERIAL PRIMARY KEY,
    parking_name VARCHAR(255) REFERENCES parkings(name),
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    free_public INT,
    free_disabled INT,
    free_electric INT,
    total_free INT,
    raw_payload JSONB
);

CREATE INDEX IF NOT EXISTS idx_occupancy_name_time 
ON parking_occupancy_logs (parking_name, recorded_at);