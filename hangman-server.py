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
            msg_string = msg_bytes.decode('ascii', errors='replace')
            buffer_do_cliente = buffer_do_cliente[indice_terminador + 2:]

            return msg_string, buffer_do_cliente


# Função para fechar conexão de um ou mains clientes
def fechar_conexao(clientes_conectados):
    if isinstance(clientes_conectados, dict):
        try:
            clientes_conectados['socket'].close()
        except Exception:
            pass
    else:
        for client in clientes_conectados:
            try:
                client['socket'].close()
            except Exception:
                pass

    if isinstance(mestre, dict):
        try:
            mestre['socket'].close()
        except Exception:
            pass


# Função para mandar uma certa mensagem para todos os clientes
def mensagem_todos_clientes(clientes_conectados, mensagem, mestre=None):
    for client in clientes_conectados:
        try:
            client['socket'].send(mensagem.encode('ascii', errors='replace'))
        except:
            pass
    if mestre is not None:
        try:
            mestre['socket'].send(mensagem.encode('ascii', errors='replace'))
        except:
            pass


def Contem_invalido(mensagem):
    mensagem = mensagem.split()
    for x in mensagem:
        if not x.isalnum():
            return True


def Valida_espaco(mensagem):
    palavras = mensagem.split()
    contagem = mensagem.count(' ')
    if len(palavras) == 1:
        return contagem == 0
    return len(palavras)-1 == contagem


def E_INVALID_FORMAT(mensagem_original, player_atual,player):
    if Contem_invalido(mensagem_original) or not Valida_espaco(mensagem_original):
        player_atual['socket'].send('ERROR INVALID_FORMAT\r\n'.encode('ascii', errors='replace'))
        fechar_conexao(player)
        sys.exit('ERROR INVALID_FORMAT')


def E_UNEXPECTED_MESSAGE(esperado, mensagem, player_atual,player):
    if mensagem != esperado and mensagem.find('ERROR') == -1:
        player_atual['socket'].send('ERROR UNEXPECTED_MESSAGE\r\n'.encode('ascii', errors='replace'))
        fechar_conexao(player)
        sys.exit('ERROR UNEXPECTED_MESSAGE')


def E_INVALID_MASTER_MESSAGE(comando, mensagem, mestre,player):
    if comando != 'WORD' or len(mensagem) == 0 or Contem_invalido(mensagem):
        mensagem_todos_clientes(player, 'ERROR INVALID_MASTER_MESSAGE\r\n', mestre)
        fechar_conexao(player)
        sys.exit('ERROR INVALID_MASTER_MESSAGE')


def E_INVALID_PLAYER_NAME(player_atual,player):
    if player_atual['nome'] == '' or not player_atual['nome'].isalnum():
        player_atual['socket'].send('ERROR INVALID_PLAYER_NAME\r\n'.encode('ascii', errors='replace'))
        fechar_conexao(player)
        sys.exit('ERROR INVALID_PLAYER_NAME')


def E_NOT_ENOUGH_PLAYERS(mestre, player):
    if len(player) == 0:
        mestre['socket'].send('ERROR NOT_ENOUGH_PLAYERS\r\n'.encode('ascii', errors='replace'))
        fechar_conexao(player)
        sys.exit('ERROR NOT_ENOUGH_PLAYERS')


def E_ALREADY_GUESSED(palpites, mensagem, player_atual):
    for x in palpites:
        if x == mensagem:
            player_atual['socket'].send('ERROR ALREADY_GUESSED\r\n'.encode('ascii', errors='replace'))
            return True
    return False


def E_INVALID_LETTER(mensagem, player_atual):
    if not mensagem.isalpha():
        player_atual['socket'].send('ERROR INVALID_LETTER\r\n'.encode('ascii', errors='replace'))
        return True
    return False


def E_INVALID_WORD_LENGTH(mensagem, palavra, player_atual):
    if len(mensagem) != len(palavra):
        player_atual['socket'].send('ERROR INVALID_WORD_LENGTH\r\n'.encode('ascii', errors='replace'))
        return True
    return False


def QUIT(player, N_player_atual):
    player[N_player_atual]['socket'].send('OK\r\n'.encode('ascii', errors='replace'))
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
        if jog_sup < 2:
            sys.exit('ERROR NOT_ENOUGH_PLAYERS')

        while len(player) < jog_sup:
            Indice_player = len(player)
            print(f'Aguardando jogador {Indice_player+1}...')
            socket_comunicacao, end_client = socket_server.accept()
            mensagem, buffer = ler_msg_completo(socket_comunicacao, b'')
            partes = mensagem.split(" ", 1)
            comando = partes[0]
            nome = partes[1] if len(partes) > 1 else ""
            player.append({
                'socket': socket_comunicacao,
                'nome': nome,
                'buffer_recebimento': buffer
            })
            E_INVALID_PLAYER_NAME(player[Indice_player], player)
            E_INVALID_FORMAT(mensagem, player[Indice_player], player)
            E_UNEXPECTED_MESSAGE('NEWPLAYER', comando, player[Indice_player], player)
            print(f"Jogador conectado: {player[Indice_player]['nome']}")
            print()
            socket_comunicacao.send('STANDBY\r\n'.encode('ascii', errors='replace'))
    except KeyboardInterrupt:
        print('\n[Servidor] Interrupção. Fechando recursos...')
        socket_server.close()
        fechar_conexao(player)
        sys.exit(0)

    # Escolhendo o jogador mestre e a palavra
    indice_mestre = random.randint(0, len(player) - 1)
    mestre = player[indice_mestre]

    print(f"Jogador mestre: {mestre['nome']}")
    mestre['socket'].send('MASTER\r\n'.encode('ascii', errors='replace'))
    mensagem, mestre['buffer_recebimento'] = ler_msg_completo(mestre['socket'], mestre['buffer_recebimento'])
    E_INVALID_MASTER_MESSAGE(mensagem.split()[0], mensagem.split()[1], mestre, player)
    palavra = list(mensagem.split()[1].lower())
    if not palavra[0].isalpha():
        mensagem_todos_clientes(player, 'ERROR INVALID_FORMAT\r\n', mestre)
        fechar_conexao(player)
        sys.exit('ERROR INVALID_FORMAT')
    E_UNEXPECTED_MESSAGE('WORD', mensagem.split()[0], mestre, player)
    print(f"jogador mestre forneceu a palavra: {''.join(palavra)}")
    print()
    mestre['socket'].send('OK\r\n'.encode('ascii', errors='replace'))
    print('Jogo iniciado com sucesso!')
    print()
    mensagem_todos_clientes(player, f'NEWGAME {vidas} {len(palavra)}\r\n', mestre)

    # Parte principal do jogo
    estado = False
    atual = 0
    status = list('_' * len(palavra))
    lista_palpites = list()
    while True:
        while True:
            if atual >= len(player):
                atual = 0

            if atual == indice_mestre:
                atual += 1
                continue

            player_atual = player[atual]
            break
        try:
            player_atual = player[atual]
            print(f"Vez do jogador {player_atual['nome']}")
            player_atual['socket'].send('YOURTURN\r\n'.encode('ascii', errors='replace'))
            mensagem, player_atual['buffer_recebimento'] = ler_msg_completo(player_atual['socket'],
                                                                            player_atual['buffer_recebimento'])
            if mensagem.split()[0] == 'QUIT':
                QUIT(player, atual)
                E_NOT_ENOUGH_PLAYERS(mestre, player)

            comando_palpite = mensagem.split()[1]
            palpite = mensagem.split()[2]

            E_UNEXPECTED_MESSAGE('GUESS', mensagem.split()[0], player_atual, player)
            player_atual['socket'].send('OK\r\n'.encode('ascii', errors='replace'))
            E_INVALID_FORMAT(mensagem, player_atual, player)
            if E_ALREADY_GUESSED(lista_palpites, palpite, player_atual):
                vidas -= 1
                comando_palpite = 'invalido'
            lista_palpites.append(palpite)
            
        except KeyboardInterrupt:
            print('\n[Servidor] Interrupção. Fechando recursos...')
            socket_server.close()
            fechar_conexao(player)
            sys.exit(0)
        player_atual['socket'].send('OK\r\n'.encode('ascii', errors='replace'))

        if comando_palpite == 'LETTER':
            print(f"Processando palpite de letra: '{''.join(palpite)}'")
            acertou = False
            if not E_INVALID_LETTER(palpite, player_atual):
                for c in range(0, len(palavra)):
                    if '_' == status[c] and palpite[0].lower == palavra[c].lower:
                        status[c] = palpite[0]
                        acertou = True
                if status == palavra:
                    estado = True
                if not acertou:
                    vidas -= 1
            else:
                vidas -= 1

        if comando_palpite == 'WORD':
            palavra_correta = ''.join(palavra).lower()
            palpite_normalizado = palpite.lower()
            print(f"Processando palpite de palavra: '{palpite_normalizado}'")
            if not E_INVALID_WORD_LENGTH(palpite, palavra, player_atual) and palpite_normalizado == palavra_correta:
                estado = True
            else:
                vidas -= 1

        if estado:
            print(f"Jogador {player_atual['nome']} advinhou a palvra!")
            mensagem_todos_clientes(player, f"GAMEOVER WIN {player_atual['nome']} {''.join(palavra)}\r\n", mestre)
            break

        if vidas == 0:
            print(f"A palavra não foi advinhada. Último jogador: {player_atual['nome']}")
            mensagem_todos_clientes(player, f"GAMEOVER LOSE {player_atual['nome']} {''.join(palavra)}\r\n", mestre)
            break

        print(f"Continuando jogo. Estado atual: {''.join(status)}, vidas restantes: {vidas}.")
        mensagem_todos_clientes(player,
                                f"STATUS {vidas} {''.join(status)} {player[atual]['nome']} {''.join(palpite)}\r\n",
                                mestre)
        atual += 1

    # Finalizando o jogo
    print('Finalizando jogo...')
    fechar_conexao(player)
    print()
    print()
