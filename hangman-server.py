import socket
import sys
import random


# Função para ler a mensagem recebida do cliente
def ler_msg_completo(socket_do_cliente, buffer_do_cliente):
    while True:
        dados = socket_do_cliente.recv(1024)

        if not dados:
            return None, buffer_do_cliente

        buffer_do_cliente += dados

        if b'\r\n' in buffer_do_cliente:
            indice_terminador = buffer_do_cliente.find(b'\r\n')
            msg_bytes = buffer_do_cliente[:indice_terminador]
            msg_string = msg_bytes.decode('ascii')
            buffer_do_cliente = buffer_do_cliente[indice_terminador + 2:]

            return msg_string, buffer_do_cliente


# Função para fechar conexão de todos os clientes
def fechar_conexao(clientes_conectados):
    for client in clientes_conectados:
        client['socket'].close()


# FUnção para mandar uma certa mensagem para todos os clientes
def mensagem_todos_clientes(clientes_conectados, message):
    for client in clientes_conectados:
        client['socket'].send(message.encode('ascii'))


# Armazenando os parâmetros de execução
jog_sup = int(sys.argv[1])
host_server = '0.0.0.0'
if len(sys.argv) > 2:
    porta_server = int(sys.argv[2])
else:
    porta_server = 6891

# Criando a conexão
socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket_server.bind((host_server, porta_server))
socket_server.listen(5)
print(f"Servidor inicializado na porta {porta_server}")

# Loop principal do jogo
while True:
    # Aguardando os jogadores entrarem no servidor
    print("Iniciando novo jogo...")
    vidas = 7
    player = []
    try:
        while len(player) < jog_sup:
            print(f"Aguardando jogador {len(player) + 1}...")
            socket_comunicacao, end_client = socket_server.accept()
            mensagem, buffer = ler_msg_completo(socket_comunicacao, b'')

            socket_comunicacao.send("STANDBY\r\n".encode('ascii'))

            nome = mensagem.split()[1]
            print(f"Jogador conectado: {nome}")
            print()
            player.append({
                'socket': socket_comunicacao,
                'nome': nome,
                'buffer_recebimento': buffer
            })
    except KeyboardInterrupt:
        print("\n[Servidor] Interrupção. Fechando recursos...")
        socket_server.close()
        fechar_conexao(player)
        sys.exit(0)

    # Escolhendo o jogador mestre e a palavra
    x = random.randint(0, len(player) - 1)
    print(f"Jogador mestre: {player[x]['nome']}")
    player[x]['socket'].send("MASTER\r\n".encode('ascii'))
    mensagem, player[x]['buffer_recebimento'] = ler_msg_completo(player[x]['socket'], player[x]['buffer_recebimento'])
    palavra = list(mensagem.split()[1].lower())
    print(f"jogador mestre forneceu a palavra: {''.join(palavra)}")
    print()
    player[x]['socket'].send("OK\r\n".encode('ascii'))
    print("Jogo iniciado com sucesso!")
    print()
    mensagem_todos_clientes(player, f"NEWGAME {vidas} {len(palavra)}\r\n")

    # Parte principal do jogo
    estado = False
    atual = 0
    status = list('_' * len(palavra))
    while True:
        while atual == x:
            atual = (atual + 1) % len(player)
        try:
            player_atual = player[atual]
            print(f"Vez do jogador {player_atual['nome']}")
            player[atual]['socket'].send("YOURTURN\r\n".encode('ascii'))
            mensagem, player_atual['buffer_recebimento'] = ler_msg_completo(player_atual['socket'],
                                                                            player_atual['buffer_recebimento'])
            comando_palpite = mensagem.split()[1]
            palpite = list(mensagem.split()[2].lower())
        except KeyboardInterrupt:
            print("\n[Servidor] Interrupção. Fechando recursos...")
            socket_server.close()
            fechar_conexao(player)
            sys.exit(0)
        player_atual['socket'].send("OK\r\n".encode('ascii'))

        if comando_palpite == 'LETTER':
            print(f"Processando palpite de letra: '{''.join(palpite)}'")
            acertou = False
            for c in range(0, len(palavra)):
                if '_' == status[c] and palpite[0] == palavra[c]:
                    status[c] = palpite[0]
                    acertou = True
            if status == palavra:
                estado = True
            if not acertou:
                vidas -= 1

        elif comando_palpite == 'WORD':
            print(f"Processando palpite de palavra: '{''.join(palpite)}'")
            if palpite == palavra:
                estado = True
            else:
                vidas -= 1

        if estado:
            print(f"Jogador {player_atual['nome']} advinhou a palvra!")
            mensagem_todos_clientes(player, f"GAMEOVER WIN {player_atual['nome']} {''.join(palavra)}\r\n")
            break

        if vidas == 0:
            print(f"A palavra não foi advinhada. Último jogador: {player_atual['nome']}")
            mensagem_todos_clientes(player, f"GAMEOVER LOSE {player_atual['nome']} {''.join(palavra)}\r\n")
            break

        print(f"Continuando jogo. Estado atual: {''.join(status)}, vidas restantes: {vidas}.")
        mensagem_todos_clientes(player, f"STATUS {vidas} {''.join(status)} {player[atual]['nome']} {''.join(palpite)}\r\n")
        atual += 1

    # Finalizando o jogo
    print("Finalizando jogo...")
    fechar_conexao(player)
    print()
    print()
