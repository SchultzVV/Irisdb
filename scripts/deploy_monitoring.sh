#!/bin/bash

# Deploy ElasticSearch Monitoring Infrastructure for Iris Pipeline
# This script sets up the complete monitoring stack

set -e

echo "🚀 Deploying Iris Pipeline Monitoring Infrastructure..."

# Configuration
ELASTICSEARCH_HOST="${ELASTICSEARCH_HOST:-localhost}"
ELASTICSEARCH_PORT="${ELASTICSEARCH_PORT:-9200}"
KIBANA_HOST="${KIBANA_HOST:-localhost}"
KIBANA_PORT="${KIBANA_PORT:-5601}"
INDEX_NAME="iris-pipeline-logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required tools are installed
check_dependencies() {
    print_status "Checking dependencies..."
    
    if ! command -v curl &> /dev/null; then
        print_error "curl is required but not installed"
        exit 1
    fi
    
    if ! command -v jq &> /dev/null; then
        print_warning "jq not found, installing..."
        sudo apt-get update && sudo apt-get install -y jq
    fi
    
    print_success "Dependencies checked"
}

# Test ElasticSearch connectivity
test_elasticsearch() {
    print_status "Testing ElasticSearch connectivity..."
    
    if curl -s -f "http://${ELASTICSEARCH_HOST}:${ELASTICSEARCH_PORT}/_cluster/health" > /dev/null; then
        print_success "ElasticSearch is accessible at ${ELASTICSEARCH_HOST}:${ELASTICSEARCH_PORT}"
    else
        print_error "Cannot connect to ElasticSearch at ${ELASTICSEARCH_HOST}:${ELASTICSEARCH_PORT}"
        print_error "Please ensure ElasticSearch is running and accessible"
        exit 1
    fi
}

# Create ElasticSearch index template
create_index_template() {
    print_status "Creating ElasticSearch index template..."
    
    curl -X PUT "http://${ELASTICSEARCH_HOST}:${ELASTICSEARCH_PORT}/_index_template/iris-pipeline-template" \
    -H "Content-Type: application/json" \
    -d '{
        "index_patterns": ["iris-pipeline-*"],
        "template": {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "index.lifecycle.name": "iris-pipeline-policy",
                "index.lifecycle.rollover_alias": "iris-pipeline-logs"
            },
            "mappings": {
                "properties": {
                    "@timestamp": {
                        "type": "date"
                    },
                    "level": {
                        "type": "keyword"
                    },
                    "logger": {
                        "type": "keyword"
                    },
                    "message": {
                        "type": "text",
                        "analyzer": "standard"
                    },
                    "pipeline_name": {
                        "type": "keyword"
                    },
                    "pipeline_status": {
                        "type": "keyword"
                    },
                    "table_name": {
                        "type": "keyword"
                    },
                    "metric_name": {
                        "type": "keyword"
                    },
                    "metric_value": {
                        "type": "double"
                    },
                    "execution_time_seconds": {
                        "type": "double"
                    },
                    "record_count": {
                        "type": "long"
                    },
                    "error_details": {
                        "type": "text"
                    },
                    "environment": {
                        "type": "keyword"
                    },
                    "host": {
                        "type": "keyword"
                    },
                    "application": {
                        "type": "keyword"
                    }
                }
            }
        }
    }' > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        print_success "Index template created successfully"
    else
        print_error "Failed to create index template"
        exit 1
    fi
}

# Create ILM policy
create_ilm_policy() {
    print_status "Creating Index Lifecycle Management policy..."
    
    curl -X PUT "http://${ELASTICSEARCH_HOST}:${ELASTICSEARCH_PORT}/_ilm/policy/iris-pipeline-policy" \
    -H "Content-Type: application/json" \
    -d '{
        "policy": {
            "phases": {
                "hot": {
                    "actions": {
                        "rollover": {
                            "max_size": "1GB",
                            "max_age": "1d"
                        }
                    }
                },
                "warm": {
                    "min_age": "2d",
                    "actions": {
                        "shrink": {
                            "number_of_shards": 1
                        }
                    }
                },
                "delete": {
                    "min_age": "30d"
                }
            }
        }
    }' > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        print_success "ILM policy created successfully"
    else
        print_warning "Failed to create ILM policy (may already exist)"
    fi
}

# Create initial index
create_initial_index() {
    print_status "Creating initial index..."
    
    curl -X PUT "http://${ELASTICSEARCH_HOST}:${ELASTICSEARCH_PORT}/${INDEX_NAME}-000001" \
    -H "Content-Type: application/json" \
    -d '{
        "aliases": {
            "iris-pipeline-logs": {
                "is_write_index": true
            }
        }
    }' > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        print_success "Initial index created successfully"
    else
        print_warning "Failed to create initial index (may already exist)"
    fi
}

# Test Kibana connectivity
test_kibana() {
    print_status "Testing Kibana connectivity..."
    
    if curl -s -f "http://${KIBANA_HOST}:${KIBANA_PORT}/api/status" > /dev/null; then
        print_success "Kibana is accessible at ${KIBANA_HOST}:${KIBANA_PORT}"
    else
        print_warning "Cannot connect to Kibana at ${KIBANA_HOST}:${KIBANA_PORT}"
        print_warning "Dashboard import will be skipped"
        return 1
    fi
}

# Import Kibana dashboard
import_kibana_dashboard() {
    print_status "Importing Kibana dashboard..."
    
    if test_kibana; then
        # Create index pattern first
        curl -X POST "http://${KIBANA_HOST}:${KIBANA_PORT}/api/saved_objects/index-pattern" \
        -H "Content-Type: application/json" \
        -H "kbn-xsrf: true" \
        -d '{
            "attributes": {
                "title": "iris-pipeline-*",
                "timeFieldName": "@timestamp"
            }
        }' > /dev/null 2>&1
        
        # Import dashboard configuration
        if [ -f "config/kibana_dashboard.json" ]; then
            curl -X POST "http://${KIBANA_HOST}:${KIBANA_PORT}/api/saved_objects/_import" \
            -H "kbn-xsrf: true" \
            -F "file=@config/kibana_dashboard.json" > /dev/null 2>&1
            
            if [ $? -eq 0 ]; then
                print_success "Kibana dashboard imported successfully"
                print_success "Dashboard available at: http://${KIBANA_HOST}:${KIBANA_PORT}/app/dashboards#/view/iris-pipeline-overview"
            else
                print_warning "Failed to import Kibana dashboard"
            fi
        else
            print_warning "Dashboard configuration file not found"
        fi
    fi
}

# Upload log4j configuration to Databricks Workspace
upload_log4j_config() {
    print_status "Uploading log4j configuration to Databricks Workspace..."
    
    if command -v databricks &> /dev/null; then
        # Create workspace directory (not DBFS)
        databricks workspace mkdir -p /Workspace/Shared/iris_monitoring/ 2>/dev/null || true
        
        # Upload log4j.properties to workspace as RAW format
        if [ -f "config/log4j.properties" ]; then
            databricks workspace import --file config/log4j.properties /Workspace/Shared/iris_monitoring/log4j.properties --format RAW --overwrite
            
            if [ $? -eq 0 ]; then
                print_success "log4j.properties uploaded to Workspace"
                print_success "Configuration available at: /Workspace/Shared/iris_monitoring/log4j.properties"
            else
                print_error "Failed to upload log4j.properties"
            fi
        else
            print_error "log4j.properties not found in config directory"
        fi
    else
        print_warning "Databricks CLI not found, skipping log4j upload"
        print_warning "Please manually upload config/log4j.properties to Workspace"
    fi
}

# Validate Teams webhook
validate_teams_webhook() {
    if [ -n "$TEAMS_WEBHOOK_URL" ]; then
        print_status "Testing Teams webhook..."
        
        curl -X POST "$TEAMS_WEBHOOK_URL" \
        -H "Content-Type: application/json" \
        -d '{
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "summary": "Iris Pipeline Monitoring Test",
            "themeColor": "0078d4",
            "sections": [{
                "activityTitle": "🧪 Monitoring Setup Test",
                "activitySubtitle": "Iris MLOps Pipeline",
                "text": "This is a test message to validate Teams webhook integration.",
                "facts": [
                    {"name": "Status", "value": "Testing"},
                    {"name": "Component", "value": "Monitoring Infrastructure"},
                    {"name": "Timestamp", "value": "'$(date -Iseconds)'"}
                ]
            }]
        }' > /dev/null 2>&1
        
        if [ $? -eq 0 ]; then
            print_success "Teams webhook test message sent successfully"
        else
            print_warning "Failed to send Teams webhook test message"
        fi
    else
        print_warning "TEAMS_WEBHOOK_URL not set, skipping webhook test"
    fi
}

# Deploy monitoring utilities
deploy_monitoring_utils() {
    print_status "Deploying monitoring utilities to Databricks Workspace..."
    
    if command -v databricks &> /dev/null; then
        # Create utils directory in workspace
        databricks workspace mkdir -p /Workspace/Shared/iris_monitoring/utils/ 2>/dev/null || true
        
        # Upload monitoring utilities
        if [ -f "utils/monitoring.py" ]; then
            databricks workspace import --file utils/monitoring.py /Workspace/Shared/iris_monitoring/utils/monitoring.py --language PYTHON --format SOURCE --overwrite
            
            if [ $? -eq 0 ]; then
                print_success "Monitoring utilities uploaded to Workspace"
            else
                print_error "Failed to upload monitoring utilities"
            fi
        else
            print_error "monitoring.py not found in utils directory"
        fi
    else
        print_warning "Databricks CLI not found, skipping utilities upload"
    fi
}

# Generate deployment summary
generate_summary() {
    print_status "Generating deployment summary..."
    
    cat << EOF

════════════════════════════════════════════════════════════════
🎉 IRIS PIPELINE MONITORING DEPLOYMENT COMPLETE
════════════════════════════════════════════════════════════════

📊 ElasticSearch Configuration:
   • Host: ${ELASTICSEARCH_HOST}:${ELASTICSEARCH_PORT}
   • Index: ${INDEX_NAME}
   • Template: iris-pipeline-template ✅
   • ILM Policy: iris-pipeline-policy ✅

📈 Kibana Dashboard:
   • Host: ${KIBANA_HOST}:${KIBANA_PORT}
   • Dashboard: iris-pipeline-overview
   • URL: http://${KIBANA_HOST}:${KIBANA_PORT}/app/dashboards#/view/iris-pipeline-overview

🔧 Databricks Configuration:
   • log4j.properties: /Workspace/Shared/iris_monitoring/log4j.properties
   • monitoring.py: /Workspace/Shared/iris_monitoring/utils/monitoring.py

📧 Teams Integration:
   • Webhook: $([ -n "$TEAMS_WEBHOOK_URL" ] && echo "Configured ✅" || echo "Not configured ⚠️")

🚀 Next Steps:
   1. Update databricks.yml variables:
      - elasticsearch_host: ${ELASTICSEARCH_HOST}
      - elasticsearch_port: ${ELASTICSEARCH_PORT}
      - log4j_path: /Workspace/Shared/iris_monitoring/log4j.properties
      - teams_webhook: \${TEAMS_WEBHOOK_URL} (when available)
   
   2. Deploy bundle with monitoring:
      databricks bundle deploy --target dev
   
   3. Run a pipeline to test monitoring:
      databricks jobs run-now <job-id>
   
   4. Check logs in Kibana dashboard

════════════════════════════════════════════════════════════════

EOF
}

# Main execution
main() {
    echo "🎯 Starting Iris Pipeline Monitoring Deployment"
    echo "Environment: ElasticSearch=${ELASTICSEARCH_HOST}:${ELASTICSEARCH_PORT}, Kibana=${KIBANA_HOST}:${KIBANA_PORT}"
    echo ""
    
    check_dependencies
    test_elasticsearch
    create_index_template
    create_ilm_policy
    create_initial_index
    import_kibana_dashboard
    upload_log4j_config
    deploy_monitoring_utils
    validate_teams_webhook
    generate_summary
    
    print_success "🎉 Monitoring infrastructure deployment completed successfully!"
}

# Run main function
main "$@"
