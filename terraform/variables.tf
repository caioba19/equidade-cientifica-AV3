variable "aiven_api_token" {
  description = "Token de API pessoal da Aiven (obtenha em https://console.aiven.io/profile/auth)"
  type        = string
  sensitive   = true
}

variable "aiven_project_name" {
  description = "Nome do projeto na Aiven (identificador existente na sua conta)"
  type        = string
}

variable "aiven_service_name" {
  description = "Nome do serviço PostgreSQL que será criado"
  type        = string
  default     = "pg-ods5-ods18"
}

variable "aiven_cloud_region" {
  description = "Região da nuvem para o cluster (ex: google-southamerica-east1, aws-sa-east-1)"
  type        = string
  default     = "google-southamerica-east1"
}

variable "aiven_plan" {
  description = "Plano de hospedagem Aiven (utilizar free-1gb para plano gratuito)"
  type        = string
  default     = "free-1gb"
}

variable "database_name" {
  description = "Nome do banco de dados relacional para o fomento"
  type        = string
  default     = "fomento_db"
}

variable "db_username" {
  description = "Usuário para acesso ao banco de dados"
  type        = string
  default     = "fomento_analyst"
}

variable "db_password" {
  description = "Senha segura para o usuário do banco de dados"
  type        = string
  sensitive   = true
}
