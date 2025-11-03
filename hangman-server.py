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
            msg_string = msg_bytes.decode('ascii',errors='replace')
            buffer_do_cliente = buffer_do_cliente[indice_terminador + 2:]

            return msg_string, buffer_do_cliente


# Função para fechar conexão de todos os clientes
def fechar_conexao(clientes_conectados):
    for client in clientes_conectados:
        client['socket'].close()

# Função para mandar uma certa mensagem para todos os clientes
def mensagem_todos_clientes(clientes_conectados, message):
    for client in clientes_conectados:
        client['socket'].send(message.encode('ascii'))

def Contem_invalido(mensagem):
    mensagem = mensagem.split()
    for x in mensagem:
        if not mensagem.isalnum():
            return True
        
def Valida_espaco(mensagem):
    palavras = mensagem.split()
    if len(palavras) == 1:
        return mensagem.count(' ') == 0
    return len(palavras)-1 == mensagem.count(' ')

def E_INVALID_FORMAT(mensagem_original, player_atual):
    if Contem_invalido(mensagem_original) or Valida_espaco(mensagem_original):
        player_atual['socket'].send('ERROR INVALID_FORMAT\r\n'.encode('ascii'))
        fechar_conexao(player_atual)
        sys.exit('ERROR INVALID_FORMAT')

def E_UNEXPECTED_MESSAGE(esperado, mensagem, player_atual):
    if mensagem != esperado and mensagem.find('ERROR') == -1:
        player_atual['socket'].send('ERROR UNEXPECTED_MESSAGE\r\n'.encode('ascii'))
        fechar_conexao(player_atual)
        sys.exit('ERROR UNEXPECTED_MESSAGE')

def E_INVALID_MASTER_MESSAGE(comando, mensagem, player, player_atual):
    if comando != 'WORD' or len(mensagem) == 0 or Contem_invalido(mensagem):
        mensagem_todos_clientes(player, 'ERROR INVALID_MASTER_MESSAGE\r\n')
        fechar_conexao(player_atual)
        sys.exit('ERROR INVALID_MASTER_MESSAGE')

def E_INVALID_PLAYER_NAME(player_atual):
    if player_atual['nome'].find(' ') or player_atual['nome'] == '' or not player_atual['nome'].isalnum():
        player_atual['socket'].send('ERROR INVALID_PLAYER_NAME\r\n'.encode('ascii'))
        fechar_conexao(player_atual)
        sys.exit('ERROR INVALID_PLAYER_NAME')

def E_NOT_ENOUGH_PLAYERS(mestre, player):
    if (len(player) < 2):
        mestre['socket'].send('ERROR NOT_ENOUGH_PLAYERS\r\n'.encode('ascii'))
        fechar_conexao(mestre)
        sys.exit('ERROR NOT_ENOUGH_PLAYERS')

def E_ALREADY_GUESSED(palpites, mensagem, player_atual):
    for x in palpites:
        if x == mensagem:
            player_atual['socket'].send('ERROR ALREADY_GUESSED\r\n'.encode('ascii'))
            return True
        return False

def E_INVALID_LETTER(mensagem, player_atual):
    if not mensagem.isalpha():
        player_atual['socket'].send('ERROR INVALID_LETTER\r\n'.encode('ascii'))
        return True
    return False

def E_INVALID_WORD_LENGTH(mensagem, palavra, player_atual):
    if len(mensagem) != len(palavra):
        player_atual['socket'].send('ERROR INVALID_WORD_LENGTH\r\n'.encode('ascii'))
        return True
    return False

def QUIT(player,N_player_atual):
    player[N_player_atual]['socket'].send('OK\r\n'.encode('ascii'))
    fechar_conexao(player[N_player_atual])
    player.pop(N_player_atual)
    return

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
print(f'Servidor inicializado na porta {porta_server}')

# Loop principal do jogo
while True:
    # Aguardando os jogadores entrarem no servidor
    print('Iniciando novo jogo...')
    vidas = 7
    player = []
    try:
        while len(player) < jog_sup:
            print(f'Aguardando jogador {len(player) + 1}...')
            socket_comunicacao, end_client = socket_server.accept()
            mensagem, buffer = ler_msg_completo(socket_comunicacao, b'')
            player.append({
                'socket': socket_comunicacao,
                'nome': mensagem[mensagem.find('')+1:],
                'buffer_recebimento': buffer
            })
            E_INVALID_PLAYER_NAME(player)
            E_INVALID_FORMAT(mensagem, player)
            E_UNEXPECTED_MESSAGE('NEWPLAYER', mensagem, player)
            print(f'Jogador conectado: {player['nome']}')
            print()
            socket_comunicacao.send('STANDBY\r\n'.encode('ascii'))
    except KeyboardInterrupt:
        print('\n[Servidor] Interrupção. Fechando recursos...')
        socket_server.close()
        fechar_conexao(player)
        sys.exit(0)

    # Escolhendo o jogador mestre e a palavra
    x = random.randint(0, len(player) - 1)
    mestre = player[x]
    player.pop(x)
    player.append(mestre)

    print(f'Jogador mestre: {mestre['nome']}')
    mestre['socket'].send('MASTER\r\n'.encode('ascii'))
    mensagem, mestre['buffer_recebimento'] = ler_msg_completo(mestre['socket'], mestre['buffer_recebimento'])
    E_INVALID_MASTER_MESSAGE(mensagem.split[0], mensagem.split[1], mestre)
    palavra = list(mensagem.split()[1].lower())
    if not palavra[0].isalpha():
        mensagem_todos_clientes(player, 'ERROR INVALID_FORMAT\r\n')
        fechar_conexao(player)
        sys.exit('ERROR INVALID_FORMAT')
    E_UNEXPECTED_MESSAGE('WORD', mensagem.split[0], mestre)
    print(f'jogador mestre forneceu a palavra: {''.join(palavra)}')
    print()
    mestre['socket'].send('OK\r\n'.encode('ascii'))
    print('Jogo iniciado com sucesso!')
    print()
    mensagem_todos_clientes(player, f'NEWGAME {vidas} {len(palavra)}\r\n')

    # Parte principal do jogo
    estado = False
    atual = 0
    status = list('_' * len(palavra))
    lista_palpites = list()
    while True:

        if atual >= len(player)- 1:
            atual = 0
        try:
            player_atual = player[atual]
            print(f'Vez do jogador {player_atual['nome']}')
            player[atual]['socket'].send('YOURTURN\r\n'.encode('ascii'))
            mensagem, player_atual['buffer_recebimento'] = ler_msg_completo(player_atual['socket'],
                                                                            player_atual['buffer_recebimento'])
            comando_palpite = mensagem.split()[1]
            palpite = list(mensagem.split()[2].lower())
            
            if mensagem.spli[0] == 'QUIT':
                QUIT(player_atual, atual)
                E_NOT_ENOUGH_PLAYERS(mestre, player_atual)
            E_UNEXPECTED_MESSAGE('GUESS', mensagem.split[0])
            if E_INVALID_WORD_LENGTH(palpite, palavra, player_atual) or E_INVALID_LETTER(palpite, player_atual):
                vidas -= 1
                comando_palpite = 'invalido'
                estado = True
            E_INVALID_FORMAT(mensagem, player_atual)
            lista_palpites.append(palpite)
            if E_ALREADY_GUESSED(lista_palpites, palpite):
                vidas -= 1
                comando_palpite = 'invalido'
                estado = True

            
        except KeyboardInterrupt:
            print('\n[Servidor] Interrupção. Fechando recursos...')
            socket_server.close()
            fechar_conexao(player)
            sys.exit(0)
        player_atual['socket'].send('OK\r\n'.encode('ascii'))

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
            print(f'Jogador {player_atual['nome']} advinhou a palvra!')
            mensagem_todos_clientes(player, f'GAMEOVER WIN {player_atual['nome']} {''.join(palavra)}\r\n')
            break

        if vidas == 0:
            print(f'A palavra não foi advinhada. Último jogador: {player_atual['nome']}')
            mensagem_todos_clientes(player, f'GAMEOVER LOSE {player_atual['nome']} {''.join(palavra)}\r\n')
            break

        print(f'Continuando jogo. Estado atual: {''.join(status)}, vidas restantes: {vidas}.')
        mensagem_todos_clientes(player, f'STATUS {vidas} {''.join(status)} {player[atual]['nome']} {''.join(palpite)}\r\n')
        atual += 1

    # Finalizando o jogo
    print('Finalizando jogo...')
    fechar_conexao(player)
    print()
    print()
