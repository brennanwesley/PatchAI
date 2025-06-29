-- Phase 3 Production Hardening Database Schema
-- Webhook redundancy, integrity validation, performance monitoring, and dashboard tables

-- Webhook Events Table (enhanced)
CREATE TABLE IF NOT EXISTS webhook_events (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    event_id VARCHAR(255) UNIQUE NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    received_at TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    attempts INTEGER DEFAULT 0,
    last_attempt TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    processed_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for webhook_events
CREATE INDEX IF NOT EXISTS idx_webhook_events_event_id ON webhook_events(event_id);
CREATE INDEX IF NOT EXISTS idx_webhook_events_status ON webhook_events(status);
CREATE INDEX IF NOT EXISTS idx_webhook_events_created_at ON webhook_events(created_at);
CREATE INDEX IF NOT EXISTS idx_webhook_events_event_type ON webhook_events(event_type);

-- Integrity Validation Results Table
CREATE TABLE IF NOT EXISTS integrity_validation_results (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    correlation_id VARCHAR(255) NOT NULL,
    total_issues INTEGER DEFAULT 0,
    issues_by_severity JSONB,
    issues_detail JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for integrity_validation_results
CREATE INDEX IF NOT EXISTS idx_integrity_validation_correlation ON integrity_validation_results(correlation_id);
CREATE INDEX IF NOT EXISTS idx_integrity_validation_created_at ON integrity_validation_results(created_at);

-- Performance Alerts Table
CREATE TABLE IF NOT EXISTS performance_alerts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    metric VARCHAR(100) NOT NULL,
    value DECIMAL(10,4) NOT NULL,
    threshold DECIMAL(10,4),
    context JSONB,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for performance_alerts
CREATE INDEX IF NOT EXISTS idx_performance_alerts_metric ON performance_alerts(metric);
CREATE INDEX IF NOT EXISTS idx_performance_alerts_status ON performance_alerts(status);
CREATE INDEX IF NOT EXISTS idx_performance_alerts_created_at ON performance_alerts(created_at);

-- Manual Intervention Alerts Table
CREATE TABLE IF NOT EXISTS manual_intervention_alerts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    alert_type VARCHAR(100) NOT NULL,
    event_id VARCHAR(255),
    event_type VARCHAR(100),
    attempts INTEGER,
    error_message TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by VARCHAR(255)
);

-- Create indexes for manual_intervention_alerts
CREATE INDEX IF NOT EXISTS idx_manual_alerts_status ON manual_intervention_alerts(status);
CREATE INDEX IF NOT EXISTS idx_manual_alerts_created_at ON manual_intervention_alerts(created_at);
CREATE INDEX IF NOT EXISTS idx_manual_alerts_alert_type ON manual_intervention_alerts(alert_type);

-- Sync Operations Table (enhanced from Phase 2)
CREATE TABLE IF NOT EXISTS sync_operations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    correlation_id VARCHAR(255) NOT NULL,
    operation_type VARCHAR(100) NOT NULL,
    user_email VARCHAR(255),
    status VARCHAR(50) NOT NULL,
    details JSONB,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER
);

-- Create indexes for sync_operations
CREATE INDEX IF NOT EXISTS idx_sync_operations_correlation ON sync_operations(correlation_id);
CREATE INDEX IF NOT EXISTS idx_sync_operations_status ON sync_operations(status);
CREATE INDEX IF NOT EXISTS idx_sync_operations_user_email ON sync_operations(user_email);
CREATE INDEX IF NOT EXISTS idx_sync_operations_started_at ON sync_operations(started_at);
CREATE INDEX IF NOT EXISTS idx_sync_operations_operation_type ON sync_operations(operation_type);

-- System Health Metrics Table
CREATE TABLE IF NOT EXISTS system_health_metrics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,4) NOT NULL,
    metric_unit VARCHAR(50),
    component VARCHAR(100),
    status VARCHAR(50),
    metadata JSONB,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for system_health_metrics
CREATE INDEX IF NOT EXISTS idx_health_metrics_name ON system_health_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_health_metrics_component ON system_health_metrics(component);
CREATE INDEX IF NOT EXISTS idx_health_metrics_recorded_at ON system_health_metrics(recorded_at);

-- Dashboard Cache Table
CREATE TABLE IF NOT EXISTS dashboard_cache (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    cache_data JSONB NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for dashboard_cache
CREATE INDEX IF NOT EXISTS idx_dashboard_cache_key ON dashboard_cache(cache_key);
CREATE INDEX IF NOT EXISTS idx_dashboard_cache_expires_at ON dashboard_cache(expires_at);

-- Add RLS policies for Phase 3 tables
ALTER TABLE webhook_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE integrity_validation_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE performance_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE manual_intervention_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE sync_operations ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_health_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE dashboard_cache ENABLE ROW LEVEL SECURITY;

-- Create RLS policies (admin/service access only)
CREATE POLICY "Admin access to webhook_events" ON webhook_events
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Admin access to integrity_validation_results" ON integrity_validation_results
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Admin access to performance_alerts" ON performance_alerts
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Admin access to manual_intervention_alerts" ON manual_intervention_alerts
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Admin access to sync_operations" ON sync_operations
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Admin access to system_health_metrics" ON system_health_metrics
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Admin access to dashboard_cache" ON dashboard_cache
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

-- Create functions for automatic cleanup
CREATE OR REPLACE FUNCTION cleanup_old_monitoring_data()
RETURNS void AS $$
BEGIN
    -- Cleanup webhook events older than 7 days
    DELETE FROM webhook_events 
    WHERE created_at < NOW() - INTERVAL '7 days';
    
    -- Cleanup integrity validation results older than 7 days
    DELETE FROM integrity_validation_results 
    WHERE created_at < NOW() - INTERVAL '7 days';
    
    -- Cleanup performance alerts older than 30 days
    DELETE FROM performance_alerts 
    WHERE created_at < NOW() - INTERVAL '30 days';
    
    -- Cleanup resolved manual intervention alerts older than 30 days
    DELETE FROM manual_intervention_alerts 
    WHERE status = 'resolved' AND resolved_at < NOW() - INTERVAL '30 days';
    
    -- Cleanup sync operations older than 7 days
    DELETE FROM sync_operations 
    WHERE started_at < NOW() - INTERVAL '7 days';
    
    -- Cleanup system health metrics older than 7 days
    DELETE FROM system_health_metrics 
    WHERE recorded_at < NOW() - INTERVAL '7 days';
    
    -- Cleanup expired dashboard cache
    DELETE FROM dashboard_cache 
    WHERE expires_at < NOW();
    
    RAISE NOTICE 'Monitoring data cleanup completed';
END;
$$ LANGUAGE plpgsql;

-- Create a scheduled job to run cleanup daily (if pg_cron is available)
-- SELECT cron.schedule('cleanup-monitoring-data', '0 2 * * *', 'SELECT cleanup_old_monitoring_data();');

-- Add comments for documentation
COMMENT ON TABLE webhook_events IS 'Phase 3: Webhook event tracking with redundancy and retry logic';
COMMENT ON TABLE integrity_validation_results IS 'Phase 3: Results from automated integrity validation checks';
COMMENT ON TABLE performance_alerts IS 'Phase 3: Performance monitoring alerts and thresholds';
COMMENT ON TABLE manual_intervention_alerts IS 'Phase 3: Alerts requiring manual intervention';
COMMENT ON TABLE sync_operations IS 'Phase 3: Enhanced sync operation tracking';
COMMENT ON TABLE system_health_metrics IS 'Phase 3: System health and performance metrics';
COMMENT ON TABLE dashboard_cache IS 'Phase 3: Dashboard data caching for performance';

-- Insert initial configuration data
INSERT INTO dashboard_cache (cache_key, cache_data, expires_at) VALUES 
('phase3_config', '{"version": "3.0.0", "features": ["webhook_redundancy", "integrity_validation", "performance_optimization", "monitoring_dashboard"], "initialized_at": "' || NOW() || '"}', NOW() + INTERVAL '1 year')
ON CONFLICT (cache_key) DO UPDATE SET 
    cache_data = EXCLUDED.cache_data,
    expires_at = EXCLUDED.expires_at,
    updated_at = NOW();
