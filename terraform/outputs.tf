output "service_name" {
  description = "Nome do serviço PostgreSQL criado na Aiven"
  value       = aiven_pg.pg_service.service_name
}

output "service_host" {
  description = "Host (FQDN) do cluster PostgreSQL"
  value       = aiven_pg.pg_service.service_host
}

output "service_port" {
  description = "Porta pública para conexão PostgreSQL"
  value       = aiven_pg.pg_service.service_port
}

output "database_name" {
  description = "Nome da base de dados analítica criada"
  value       = aiven_pg_database.fomento_db.database_name
}

output "database_username" {
  description = "Nome de usuário de acesso à base analítica"
  value       = aiven_pg_user.fomento_user.username
}

output "connection_string_template" {
  description = "Modelo de URI de conexão para aplicações e SQLAlchemy (senha ocultada)"
  value       = "postgresql://${aiven_pg_user.fomento_user.username}:<SUA_SENHA>@${aiven_pg.pg_service.service_host}:${aiven_pg.pg_service.service_port}/${aiven_pg_database.fomento_db.database_name}?sslmode=require"
}
