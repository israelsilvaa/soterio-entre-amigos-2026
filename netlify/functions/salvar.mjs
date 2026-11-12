// Grava o dados.json (Netlify Blobs). Sem login: a página /dados.html é de acesso direto.
import { getStore } from "@netlify/blobs";

// Dados fixos: mantenha igual ao PADRAO do atualizar.py.
const PADRAO = {
  nome: "Sorteio Mais que Vencedores",
  premio: "Yamaha Fazer 250cc 2025/2025",
  totalNumeros: 1000,
  valorNumero: 50,
  dataSorteio: "2026-12-20",
  atualizadoEm: null,
  contato: { telefone: "(91) 98563-0059", whatsapp: "5591985630059" },
  moto: {
    imagem: null,
    detalhes: [
      "Será entregue selada e transferida para o nome do novo proprietário",
      "Moto seminova, com apenas 6.000 km rodados",
      "Ano/modelo: 2025/2025",
      "Yamaha Fazer 250cc",
      "Combustível: gasolina",
      "Cor: branca",
    ],
  },
  loteria: { nome: "Loteria Federal", digitos: 3 },
  regras: [
    "Números só serão confirmados mediante a comprovação do pagamento.",
    "Informações e pagamentos serão apenas no número (91) 98563-0059. Não caia em golpes!",
    "Se todos os números forem comprados antes do dia 20/12/2026, faremos a antecipação do sorteio e divulgaremos a nova data no grupo.",
    "O sorteio será pela Loteria Federal: valem os 3 últimos números do 1º prêmio. Por exemplo, quem comprar o número 1.000 será válido pelo número 000.",
  ],
};

const json = (d, s = 200) => new Response(JSON.stringify(d), { status: s, headers: { "content-type": "application/json", "cache-control": "no-store" } });

// "" ou número 1..1000 -> "0001".."1000"; qualquer outra coisa -> null (inválido)
const numero = (v) => {
  const t = String(v ?? "").trim();
  if (t === "") return "";
  if (!/^\d{1,4}$/.test(t) || +t < 1 || +t > PADRAO.totalNumeros) return null;
  return t.padStart(4, "0");
};

export default async (req) => {
  if (req.method !== "POST") return json({ error: "Método não permitido" }, 405);
  try {
    const body = await req.json();
    const temLista = Array.isArray(body.disponiveis);
    const temSorteado = "valorNumeroSorteado" in body;

    // Revalida no servidor: 4 dígitos, 0001..1000, sem repetir, ordenado.
    let lista = null;
    if (temLista) {
      lista = [...new Set(body.disponiveis
        .map(String).filter((s) => /^\d{4}$/.test(s)).map(Number)
        .filter((n) => n >= 1 && n <= PADRAO.totalNumeros))]
        .sort((a, b) => a - b).map((n) => String(n).padStart(4, "0"));
      if (!lista.length) return json({ error: "Lista vazia: nada foi alterado" }, 400);
    }

    // Número sorteado: "" (sem selo) ou 0001..1000
    let sorteado = null, anterior = null;
    if (temSorteado) {
      sorteado = numero(body.valorNumeroSorteado);
      anterior = numero(body.valorNumeroSorteadoAnterior);
      if (sorteado === null || anterior === null) return json({ error: "Número sorteado deve estar entre 0001 e 1000" }, 400);
    }

    if (!temLista && !temSorteado) return json({ error: "Nada para salvar" }, 400);

    const store = getStore({ name: "sorteio", consistency: "strong" });
    let atual = null;
    try { atual = JSON.parse(await store.get("dados")); } catch {}
    if (!atual) { try { atual = await (await fetch(new URL("/dados-inicial.json", req.url))).json(); } catch {} }

    const dados = structuredClone(PADRAO);
    dados.moto.imagem = atual?.moto?.imagem ?? null; // preserva a imagem cadastrada
    // Só a lista mexe em disponiveis/atualizadoEm; definir o ganhador não altera nenhum dos dois.
    dados.atualizadoEm = temLista ? new Date().toISOString() : (atual?.atualizadoEm ?? null);
    dados.disponiveis = temLista ? lista : (atual?.disponiveis ?? []);
    // Preserva o ganhador ao atualizar só a lista; grava os novos valores quando enviados.
    dados.valorNumeroSorteado = temSorteado ? sorteado : (atual?.valorNumeroSorteado ?? "");
    dados.valorNumeroSorteadoAnterior = temSorteado ? anterior : (atual?.valorNumeroSorteadoAnterior ?? "");
    await store.set("dados", JSON.stringify(dados, null, 2) + "\n");
    return json({ ok: true, disponiveis: dados.disponiveis.length, atualizadoEm: dados.atualizadoEm, valorNumeroSorteado: dados.valorNumeroSorteado });
  } catch (e) {
    console.error(e);
    return json({ error: "Erro interno" }, 500);
  }
};
