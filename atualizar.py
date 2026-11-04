#!/usr/bin/env python3
"""Gera o dados.json a partir da mensagem de WhatsApp com os números disponíveis.

Uso:
  1. Cole a mensagem inteira em mensagem.txt (mesma pasta deste script)
  2. python atualizar.py
  3. Suba o dados.json atualizado na Netlify

Dados fixos (prêmio, valor, data, regras...) ficam em PADRAO, no topo deste arquivo.

Opções:
  python atualizar.py outro_arquivo.txt   # lê de outro arquivo
  python atualizar.py -                   # lê da entrada padrão (cole e Ctrl+D / Ctrl+Z)
  python atualizar.py --carimbo           # preenche "atualizadoEm" com a data/hora atual
"""
import copy
import json
import re
import sys
from datetime import datetime
from pathlib import Path

PASTA = Path(__file__).resolve().parent
SAIDA = PASTA / "dados.json"
# Dados fixos do sorteio: edite aqui e rode o script para refletir no dados.json.
PADRAO = {
    "premio": "Yamaha Fazer 250cc 2025/2025",
    "totalNumeros": 1000,
    "valorNumero": 50,
    "dataSorteio": "2026-12-20",
    "atualizadoEm": None,
    "contato": {"telefone": "(91) 98563-0059", "whatsapp": "5591985630059"},
    "moto": {
        "imagem": None,  # ex.: "moto.jpg" (arquivo na mesma pasta do index.html)
        "detalhes": [
            "Será entregue selada e transferida para o nome do novo proprietário",
            "Moto seminova, com apenas 6.000 km rodados",
            "Ano/modelo: 2025/2025",
            "Yamaha Fazer 250cc",
            "Combustível: gasolina",
            "Cor: branca",
        ],
    },
    "loteria": {"nome": "Loteria Federal", "digitos": 3},
    "regras": [
        "Números só serão confirmados mediante a comprovação do pagamento.",
        "Informações e pagamentos serão apenas no número (91) 98563-0059. Não caia em golpes!",
        "Se todos os números forem comprados antes do dia 20/12/2026, faremos a antecipação do sorteio e divulgaremos a nova data no grupo.",
        "O sorteio será pela Loteria Federal: valem os 3 últimos números do 1º prêmio. Por exemplo, quem comprar o número 1.000 será válido pelo número 000.",
    ],
}


def extrair_numeros(texto: str, total: int) -> list[str]:
    """Pega os números de 4 dígitos (0001..total), sem repetir, em ordem."""
    achados = {int(m) for m in re.findall(r"(?<!\d)\d{4}(?!\d)", texto)}
    return [f"{n:04d}" for n in sorted(achados) if 1 <= n <= total]


def main() -> None:
    args = sys.argv[1:]
    carimbo = "--carimbo" in args
    args = [a for a in args if a != "--carimbo"]

    if args and args[0] == "-":
        texto = sys.stdin.read()
    else:
        origem = Path(args[0]) if args else PASTA / "mensagem.txt"
        if not origem.exists():
            sys.exit(f"Arquivo não encontrado: {origem}\nCole a mensagem do WhatsApp nele e rode de novo.")
        texto = origem.read_text(encoding="utf-8")

    # Dados fixos vêm do PADRAO acima; do arquivo anterior só se aproveita o que muda sozinho.
    dados = copy.deepcopy(PADRAO)
    anteriores: set[str] = set()
    if SAIDA.exists():
        try:
            antigo = json.loads(SAIDA.read_text(encoding="utf-8"))
            dados["atualizadoEm"] = antigo.get("atualizadoEm")
            dados["moto"]["imagem"] = (antigo.get("moto") or {}).get("imagem") or PADRAO["moto"]["imagem"]
            anteriores = set(antigo.get("disponiveis", []))
        except json.JSONDecodeError:
            print("Aviso: dados.json anterior estava inválido; usando valores padrão.")

    numeros = extrair_numeros(texto, int(dados["totalNumeros"]))
    if not numeros:
        sys.exit("Nenhum número de 4 dígitos encontrado na mensagem. Nada foi alterado.")

    dados["atualizadoEm"] = datetime.now().astimezone().isoformat(timespec="seconds") if carimbo else dados["atualizadoEm"]
    dados["disponiveis"] = numeros

    tmp = SAIDA.with_suffix(".tmp")
    tmp.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(SAIDA)

    novos = set(numeros)
    total = int(dados["totalNumeros"])
    print(f"dados.json atualizado: {len(numeros)} disponíveis, {total - len(numeros)} vendidos.")
    if anteriores:
        vendidos_agora = sorted(anteriores - novos)
        liberados = sorted(novos - anteriores)
        print(f"Vendidos desde a última lista: {len(vendidos_agora)} {vendidos_agora[:20]}")
        if liberados:
            print(f"Voltaram a ficar disponíveis: {len(liberados)} {liberados[:20]}")


if __name__ == "__main__":
    main()
