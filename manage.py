#!/usr/bin/env python
"""
Script para inicializar banco de dados e gerenciar clientes
"""
import sys
import argparse
from database import init_db, reset_db, SessionLocal
from client_manager import ClientManager


def setup_database():
    """Inicializa banco de dados"""
    print("🔧 Inicializando banco de dados...")
    if init_db():
        print("✅ Banco de dados criado com sucesso!")
    else:
        print("❌ Erro ao criar banco de dados")
        sys.exit(1)


def reset_database():
    """Reseta banco de dados (CUIDADO!)"""
    confirm = input("⚠️  ATENÇÃO: Isso irá APAGAR todos os dados! Digite 'CONFIRMAR' para continuar: ")
    if confirm == 'CONFIRMAR':
        print("🔄 Resetando banco de dados...")
        reset_db()
        print("✅ Banco resetado!")
    else:
        print("❌ Operação cancelada")


def add_client_cli():
    """Adiciona cliente via CLI"""
    print("\n📝 Adicionar Novo Cliente")
    print("=" * 50)
    
    name = input("Nome da empresa: ")
    email = input("Email: ")
    access_token = input("Access Token (Instagram Graph API): ")
    instagram_account_id = input("Instagram Account ID: ")
    page_id = input("Page ID (Facebook): ")
    
    keywords_input = input("Keywords (separadas por vírgula): ")
    keywords = [k.strip() for k in keywords_input.split(',') if k.strip()]
    
    daily_limit = input("Limite diário de mensagens (padrão 1000): ")
    daily_limit = int(daily_limit) if daily_limit else 1000
    
    # Cria cliente
    db = SessionLocal()
    manager = ClientManager(db)
    
    try:
        client = manager.create_client(
            name=name,
            email=email,
            access_token=access_token,
            instagram_account_id=instagram_account_id,
            page_id=page_id,
            keywords=keywords,
            daily_limit=daily_limit
        )
        
        # Gera API Key
        api_key = manager.generate_api_key(client.id, "CLI Generated")
        
        print("\n✅ Cliente criado com sucesso!")
        print("=" * 50)
        print(f"ID: {client.id}")
        print(f"Nome: {client.name}")
        print(f"Email: {client.email}")
        print(f"Keywords: {', '.join(client.keywords)}")
        print(f"\n🔑 API Key: {api_key.key}")
        print(f"\n🔗 Webhook URL: /webhook/{client.verify_token}")
        print(f"🔐 Verify Token: {client.verify_token}")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ Erro ao criar cliente: {e}")
    finally:
        db.close()


def list_clients_cli():
    """Lista todos os clientes"""
    db = SessionLocal()
    manager = ClientManager(db)
    
    clients = manager.list_clients(active_only=False)
    
    if not clients:
        print("\n📋 Nenhum cliente cadastrado")
        db.close()
        return
    
    print("\n📋 Clientes Cadastrados")
    print("=" * 80)
    
    for client in clients:
        status = "✅ Ativo" if client.active else "❌ Inativo"
        print(f"\nID: {client.id} | {status}")
        print(f"Nome: {client.name}")
        print(f"Email: {client.email}")
        print(f"Instagram ID: {client.instagram_account_id}")
        print(f"Keywords: {', '.join(client.keywords)}")
        print(f"Limite diário: {client.daily_message_limit}")
        print(f"Mensagens hoje: {client.messages_sent_today}")
        print("-" * 80)
    
    db.close()


def get_client_stats_cli():
    """Mostra estatísticas de um cliente"""
    client_id = input("\nDigite o ID do cliente: ")
    
    try:
        client_id = int(client_id)
    except ValueError:
        print("❌ ID inválido")
        return
    
    db = SessionLocal()
    manager = ClientManager(db)
    
    stats = manager.get_client_stats(client_id)
    
    if not stats:
        print(f"❌ Cliente {client_id} não encontrado")
        db.close()
        return
    
    print("\n📊 Estatísticas do Cliente")
    print("=" * 50)
    print(f"ID: {stats['client_id']}")
    print(f"Nome: {stats['name']}")
    print(f"Status: {'✅ Ativo' if stats['active'] else '❌ Inativo'}")
    print(f"\nTotal de mensagens: {stats['total_messages']}")
    print(f"Mensagens hoje: {stats['messages_today']}")
    print(f"Webhooks recebidos: {stats['webhooks_received']}")
    print(f"\nLimite diário: {stats['daily_limit']}")
    print(f"Restante hoje: {stats['limit_remaining']}")
    print("=" * 50)
    
    db.close()


def deactivate_client_cli():
    """Desativa cliente"""
    client_id = input("\nDigite o ID do cliente para desativar: ")
    
    try:
        client_id = int(client_id)
    except ValueError:
        print("❌ ID inválido")
        return
    
    confirm = input(f"Confirma desativação do cliente {client_id}? (s/n): ")
    if confirm.lower() != 's':
        print("❌ Operação cancelada")
        return
    
    db = SessionLocal()
    manager = ClientManager(db)
    
    if manager.deactivate_client(client_id):
        print(f"✅ Cliente {client_id} desativado com sucesso")
    else:
        print(f"❌ Cliente {client_id} não encontrado")
    
    db.close()


def main():
    parser = argparse.ArgumentParser(description='Instagram Agent - Gerenciamento')
    parser.add_argument('action', choices=[
        'init',
        'reset',
        'add-client',
        'list-clients',
        'stats',
        'deactivate'
    ], help='Ação a ser executada')
    
    args = parser.parse_args()
    
    if args.action == 'init':
        setup_database()
    elif args.action == 'reset':
        reset_database()
    elif args.action == 'add-client':
        add_client_cli()
    elif args.action == 'list-clients':
        list_clients_cli()
    elif args.action == 'stats':
        get_client_stats_cli()
    elif args.action == 'deactivate':
        deactivate_client_cli()


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print("\n🤖 Instagram Agent Multi-Tenant - CLI")
        print("=" * 50)
        print("\nComandos disponíveis:")
        print("  python manage.py init           - Inicializa banco de dados")
        print("  python manage.py add-client     - Adiciona novo cliente")
        print("  python manage.py list-clients   - Lista todos os clientes")
        print("  python manage.py stats          - Estatísticas de um cliente")
        print("  python manage.py deactivate     - Desativa cliente")
        print("  python manage.py reset          - Reseta banco (CUIDADO!)")
        print("=" * 50)
        print()
    else:
        main()
