#!/bin/bash

# 📲 Script de Configuração do Microsoft Teams Webhook
# Este script ajuda a configurar o webhook do Teams no Databricks Secrets

echo "🔧 Configuração do Microsoft Teams Webhook para Monitoramento"
echo "============================================================="
echo

echo "📋 Pré-requisitos:"
echo "1. Webhook URL do Microsoft Teams configurado"
echo "2. Databricks CLI configurado"
echo "3. Permissões para criar secrets no workspace"
echo

# Verificar se o Databricks CLI está configurado
if ! command -v databricks &> /dev/null; then
    echo "❌ Databricks CLI não encontrado. Instale primeiro:"
    echo "   pip install databricks-cli"
    exit 1
fi

echo "✅ Databricks CLI encontrado"

# Solicitar URL do webhook
echo
echo "📝 Por favor, forneça a URL do webhook do Microsoft Teams:"
echo "   (Você pode obtê-la em: Teams > Canal > Conectores > Webhook de Entrada)"
echo
read -p "🔗 Webhook URL: " WEBHOOK_URL

if [ -z "$WEBHOOK_URL" ]; then
    echo "❌ URL do webhook é obrigatória"
    exit 1
fi

# Validar formato básico da URL
if [[ ! "$WEBHOOK_URL" == https://outlook.office.com/webhook/* ]]; then
    echo "⚠️ Aviso: A URL não parece ser um webhook válido do Teams"
    echo "   URLs válidas começam com: https://outlook.office.com/webhook/"
    read -p "Continuar mesmo assim? (y/N): " CONTINUE
    if [[ ! "$CONTINUE" =~ ^[Yy]$ ]]; then
        echo "❌ Operação cancelada"
        exit 1
    fi
fi

echo
echo "🔐 Configurando secret no Databricks..."

# Criar scope se não existir
echo "📁 Criando scope 'teams' (se não existir)..."
databricks secrets create-scope --scope teams --initial-manage-principal users 2>/dev/null || true

# Criar secret com o webhook
echo "🔑 Configurando webhook URL..."
echo "$WEBHOOK_URL" | databricks secrets put --scope teams --key webhook_url --binary-file /dev/stdin

if [ $? -eq 0 ]; then
    echo "✅ Webhook configurado com sucesso!"
    echo
    echo "🧪 Testando configuração..."
    
    # Testar se o secret foi criado
    databricks secrets list --scope teams | grep -q webhook_url
    if [ $? -eq 0 ]; then
        echo "✅ Secret 'teams/webhook_url' verificado"
        echo
        echo "🎯 Configuração completa! O monitoramento avançado agora pode enviar notificações."
        echo
        echo "📝 Próximos passos:"
        echo "   1. Execute: make run_advanced_monitoring"
        echo "   2. Verifique as notificações no canal do Teams"
        echo "   3. Configure o trigger automático para a tabela Silver"
        echo
        echo "🔧 Para testar o webhook manualmente:"
        echo "   databricks secrets get --scope teams --key webhook_url"
    else
        echo "❌ Erro: Secret não foi criado corretamente"
        exit 1
    fi
else
    echo "❌ Erro ao configurar webhook"
    exit 1
fi

echo
echo "📖 Documentação adicional:"
echo "   - Configuração de webhooks: https://docs.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/"
echo "   - Databricks Secrets: https://docs.databricks.com/security/secrets/"
echo
