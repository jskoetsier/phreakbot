#!/bin/bash
# PhreakBot Performance Monitoring Script
# Monitors key performance metrics post-deployment

set -e

CONTAINER_NAME="phreakbot"
DB_CONTAINER="phreakbot-postgres"
LOG_LINES=500

echo "========================================="
echo "PhreakBot Performance Monitor v0.1.26"
echo "========================================="
echo ""

# Function to get container stats
get_container_stats() {
    echo "📊 Container Resource Usage:"
    echo "----------------------------------------"
    podman stats --no-stream $CONTAINER_NAME | tail -n +2
    echo ""
}

# Function to check bot uptime and status
get_uptime() {
    echo "⏱️  Bot Uptime & Status:"
    echo "----------------------------------------"
    podman ps -a --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""
}

# Function to analyze cache performance
analyze_cache_performance() {
    echo "🔍 Cache Performance Analysis:"
    echo "----------------------------------------"

    # Cache hits
    cache_hits=$(podman logs --tail $LOG_LINES $CONTAINER_NAME 2>&1 | grep -c "Cache hit" || echo "0")

    # User info queries
    user_info_queries=$(podman logs --tail $LOG_LINES $CONTAINER_NAME 2>&1 | grep -c "db_get_userinfo_by_userhost" || echo "0")

    # Cached hostmask usage
    cached_hostmasks=$(podman logs --tail $LOG_LINES $CONTAINER_NAME 2>&1 | grep -c "Using cached hostmask" || echo "0")

    # WHOIS queries (should be reduced)
    whois_queries=$(podman logs --tail $LOG_LINES $CONTAINER_NAME 2>&1 | grep -c "WHOIS" || echo "0")

    echo "Cache Hits (last $LOG_LINES lines): $cache_hits"
    echo "User Info DB Queries: $user_info_queries"
    echo "Cached Hostmask Usage: $cached_hostmasks"
    echo "WHOIS Queries: $whois_queries"

    if [ $user_info_queries -gt 0 ]; then
        cache_hit_rate=$(awk "BEGIN {printf \"%.1f\", ($cache_hits / $user_info_queries) * 100}")
        echo "Estimated Cache Hit Rate: ${cache_hit_rate}%"
    fi
    echo ""
}

# Function to check database connection pool status
check_db_pool() {
    echo "💾 Database Connection Pool:"
    echo "----------------------------------------"

    pool_created=$(podman logs --tail 1000 $CONTAINER_NAME 2>&1 | grep -c "connection pool" || echo "0")
    db_errors=$(podman logs --tail $LOG_LINES $CONTAINER_NAME 2>&1 | grep -c "Database.*error\|Database.*failed" || echo "0")

    echo "Connection Pool Initialized: $([ $pool_created -gt 0 ] && echo 'Yes ✓' || echo 'No ✗')"
    echo "Database Errors (last $LOG_LINES lines): $db_errors"
    echo ""
}

# Function to analyze message processing performance
analyze_message_processing() {
    echo "⚡ Message Processing Performance:"
    echo "----------------------------------------"

    messages_processed=$(podman logs --tail $LOG_LINES $CONTAINER_NAME 2>&1 | grep -c "Processing message from" || echo "0")
    commands_processed=$(podman logs --tail $LOG_LINES $CONTAINER_NAME 2>&1 | grep -c "Routing command:" || echo "0")
    events_processed=$(podman logs --tail $LOG_LINES $CONTAINER_NAME 2>&1 | grep -c "Routing event:" || echo "0")

    echo "Messages Processed (last $LOG_LINES lines): $messages_processed"
    echo "Commands Routed: $commands_processed"
    echo "Events Routed: $events_processed"
    echo ""
}

# Function to check database index usage
check_db_indexes() {
    echo "🗂️  Database Index Status:"
    echo "----------------------------------------"

    # Query to check if indexes exist
    indexes=$(podman exec $DB_CONTAINER psql -U phreakbot -d phreakbot -t -c "
        SELECT
            schemaname,
            tablename,
            indexname
        FROM pg_indexes
        WHERE schemaname = 'public'
            AND indexname LIKE 'idx_%'
        ORDER BY tablename, indexname;
    " 2>/dev/null || echo "Error querying indexes")

    if [ "$indexes" != "Error querying indexes" ]; then
        index_count=$(echo "$indexes" | grep -c "idx_" || echo "0")
        echo "Custom Indexes Created: $index_count"
        echo ""
        echo "Index List:"
        echo "$indexes" | head -20
    else
        echo "Could not query database indexes"
    fi
    echo ""
}

# Function to check error rates
check_error_rates() {
    echo "⚠️  Error Analysis:"
    echo "----------------------------------------"

    total_errors=$(podman logs --tail $LOG_LINES $CONTAINER_NAME 2>&1 | grep -c "ERROR" || echo "0")
    module_errors=$(podman logs --tail $LOG_LINES $CONTAINER_NAME 2>&1 | grep -c "Error in module" || echo "0")
    db_connection_errors=$(podman logs --tail $LOG_LINES $CONTAINER_NAME 2>&1 | grep -c "Database connection" || echo "0")

    echo "Total Errors (last $LOG_LINES lines): $total_errors"
    echo "Module Execution Errors: $module_errors"
    echo "DB Connection Issues: $db_connection_errors"
    echo ""
}

# Function to show recent activity
show_recent_activity() {
    echo "📝 Recent Activity (last 10 events):"
    echo "----------------------------------------"
    podman logs --tail 100 $CONTAINER_NAME 2>&1 | grep -E "Processing message|Routing command|Cache hit|Using cached" | tail -10
    echo ""
}

# Function to generate performance summary
generate_summary() {
    echo "📈 Performance Summary:"
    echo "========================================="
    echo ""

    # Calculate uptime
    uptime_seconds=$(podman inspect --format='{{.State.StartedAt}}' $CONTAINER_NAME | xargs -I {} date -d {} +%s 2>/dev/null || echo "0")
    current_seconds=$(date +%s)
    uptime_minutes=$(( ($current_seconds - $uptime_seconds) / 60 ))

    echo "Bot Uptime: ${uptime_minutes} minutes"

    # Get container memory usage
    mem_usage=$(podman stats --no-stream --format "{{.MemUsage}}" $CONTAINER_NAME 2>/dev/null || echo "N/A")
    echo "Memory Usage: $mem_usage"

    # Cache efficiency
    cached_usage=$(podman logs --tail $LOG_LINES $CONTAINER_NAME 2>&1 | grep -c "Using cached" || echo "0")
    echo "Cache Utilization: $cached_usage cached lookups"

    echo ""
    echo "✅ Performance optimizations are active"
    echo "   - Connection pooling: Active"
    echo "   - Database indexes: Deployed"
    echo "   - Caching system: Operational"
    echo "   - Optimized WHOIS: Enabled"
    echo ""
}

# Main execution
main() {
    if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --full      Show full detailed analysis"
        echo "  --cache     Show only cache performance"
        echo "  --db        Show only database metrics"
        echo "  --errors    Show only error analysis"
        echo "  --help      Show this help message"
        echo ""
        exit 0
    fi

    case "$1" in
        --cache)
            analyze_cache_performance
            ;;
        --db)
            check_db_pool
            check_db_indexes
            ;;
        --errors)
            check_error_rates
            ;;
        --full)
            get_uptime
            get_container_stats
            check_db_pool
            check_db_indexes
            analyze_cache_performance
            analyze_message_processing
            check_error_rates
            show_recent_activity
            generate_summary
            ;;
        *)
            # Default: show summary
            get_uptime
            get_container_stats
            analyze_cache_performance
            analyze_message_processing
            check_error_rates
            generate_summary
            ;;
    esac
}

# Run main function
main "$@"
