terraform {
  required_version = ">= 1.3.0"
  required_providers {
    aiven = {
      source  = "aiven/aiven"
      version = ">= 4.0.0, < 5.0.0"
    }
  }
}

provider "aiven" {
  api_token = var.aiven_api_token
}

# Serviço Gerenciado Aiven for PostgreSQL (Camada Gratuita)
resource "aiven_pg" "pg_service" {
  project                 = var.aiven_project_name
  cloud_name              = var.aiven_cloud_region
  plan                    = var.aiven_plan
  service_name            = var.aiven_service_name
  maintenance_window_dow  = "sunday"
  maintenance_window_time = "04:00:00"

  pg_user_config {
    pg_version = "16"
    public_access {
      pg = true
    }
  }

  tag {
    key   = "projeto"
    value = "auditoria-ods5-ods18"
  }
  tag {
    key   = "grupo"
    value = "grupo-3"
  }
}

# Banco de dados dedicado para o pipeline de dados de fomento
resource "aiven_pg_database" "fomento_db" {
  project       = var.aiven_project_name
  service_name  = aiven_pg.pg_service.service_name
  database_name = var.database_name
}

# Usuário de leitura/escrita para a aplicação e ETL
resource "aiven_pg_user" "fomento_user" {
  project      = var.aiven_project_name
  service_name = aiven_pg.pg_service.service_name
  username     = var.db_username
  password     = var.db_password
}
