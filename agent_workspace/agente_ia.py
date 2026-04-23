import functools
import time

def log_execucao(func):
    """Decorador para registrar o tempo de execução de uma função."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        inicio = time.time()
        resultado = func(*args, **kwargs)
        fim = time.time()
        print(f"Função '{func.__name__}' executada em {fim - inicio:.4f} segundos.")
        return resultado
    return wrapper

def validar_entrada(validador):
    """Decorador para validar a entrada de uma função."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Assume que o primeiro argumento é o dado a ser validado
            dado_para_validar = args[0] if args else kwargs.get('data')
            if not validador(dado_para_validar):
                raise ValueError("Entrada inválida.")
            return func(*args, **kwargs)
        return wrapper
    return decorator

def eh_string_nao_vazia(valor):
    """Validador simples para strings não vazias."""
    return isinstance(valor, str) and len(valor) > 0

class AgenteIA:
    def __init__(self, nome):
        self.nome = nome
        print(f"Agente '{self.nome}' inicializado.")

    @log_execucao
    @validar_entrada(eh_string_nao_vazia)
    def processar_comando(self, comando: str):
        """Processa um comando simples."""
        print(f"Processando comando: '{comando}'")
        # Simulação de processamento
        time.sleep(0.5)
        return f"Comando '{comando}' processado com sucesso."

    def obter_dados_processados(self, lista_dados):
        """Exemplo de uso de list comprehension."""
        if not isinstance(lista_dados, list):
            raise TypeError("Esperado uma lista de dados.")
        
        # Filtra e transforma dados usando list comprehension
        dados_processados = [item.upper() for item in lista_dados if isinstance(item, str)]
        return dados_processados

# Exemplo de uso:
if __name__ == "__main__":
    meu_agente = AgenteIA("Ajax-v1")

    try:
        resultado = meu_agente.processar_comando("iniciar_tarefa")
        print(resultado)
    except ValueError as e:
        print(f"Erro: {e}")

    try:
        resultado_invalido = meu_agente.processar_comando("") # Comando vazio
        print(resultado_invalido)
    except ValueError as e:
        print(f"Erro esperado: {e}")

    dados_brutos = ["item1", 123, "item2", None, "item3"]
    dados_finais = meu_agente.obter_dados_processados(dados_brutos)
    print(f"Dados processados: {dados_finais}")
