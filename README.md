# Dan Couros — Sistema de Pedidos (protótipo v1)

Protótipo funcional cobrindo o núcleo do sistema descrito no documento: **Cadastro de Clientes** + **Pedido/OS**, com o cliente carregado automaticamente no pedido (contato e telefone puxados do cadastro, mas editáveis por pedido) para eliminar a redigitação que hoje acontece entre WhatsApp, OS em papel e planilha.

## O que já funciona

- Cadastro de clientes (Concessionária, Agência, Particular, Loja), com contato obrigatório quando é pessoa jurídica. Inclui telefone + celular, unidade/filial e endereço.
- Pedido/OS com todos os campos da OS em papel (veículo, revestimento, cor da linha, composição, adicionais, forma de pagamento pré-formatada, NF), já incorporando os campos do material mais recente (fotos e vídeo da OS/planilha atualizadas).
- Número de pedido (chave) gerado automaticamente, nunca se repete.
- Ao escolher o cliente no pedido, contato, telefone, celular, unidade e endereço vêm preenchidos sozinhos — mas continuam editáveis nesse pedido específico (o carro pode ser retirado num endereço diferente do cadastro, por exemplo).
- Adicionais do pedido (Assoalho, 100% Couro, Misto, Sintético, Volante, Teto) como seleção múltipla, e Logomarca como Sim/Não — refletindo o formulário mais recente.
- Lista de pedidos com abas: **Ativos** (visão inicial), **Finalizados/Cancelados**, **Todos**.

## Fora do escopo desta v1 (próximos passos)

Ainda não implementados, para não travar a entrega do núcleo: Controle de Produção (2ª linha do tempo), Checklist de retirada/montagem, Recibo, Certificado, e os relatórios (forma de pagamento por período; comissionamento por cliente/período). O modelo de dados já foi pensado para esses módulos se conectarem ao Pedido sem duplicar cadastro.

## Publicar na nuvem sem usar terminal (caminho recomendado)

Não precisa saber programar nem instalar nada no computador. São três sites gratuitos, todos pelo navegador. Leva uns 15-20 minutos na primeira vez.

**Passo 1 — Colocar o código no GitHub**
1. Crie uma conta grátis em [github.com](https://github.com).
2. Clique em "New repository", dê um nome (ex: `dan-couros-sistema`) e clique em "Create repository".
3. Na página do repositório, clique em "uploading an existing file" (ou "Add file" → "Upload files").
4. Extraia o zip que te enviei no seu computador e arraste **o conteúdo da pasta** (`app.py`, `models.py`, a pasta `templates`, etc. — não a pasta em si) para essa página. Clique em "Commit changes".

**Passo 2 — Criar o banco de dados**
1. Crie uma conta grátis em [supabase.com](https://supabase.com) e crie um novo projeto (ele pede pra você definir uma senha do banco — anote essa senha).
2. Espere o projeto terminar de criar (1-2 minutos). Vá em "Project Settings" (ícone de engrenagem) → "Database".
3. Procure "Connection string" e copie a opção no formato URI. Troque `[YOUR-PASSWORD]` pela senha que você definiu.

**Passo 3 — Publicar o app**
1. Crie uma conta grátis em [render.com](https://render.com), de preferência conectando com o mesmo GitHub do passo 1.
2. Clique em "New" → "Web Service" e escolha o repositório `dan-couros-sistema`.
3. Render detecta o `Procfile` sozinho. Se pedir, preencha: Build command `pip install -r requirements.txt`, Start command `gunicorn app:app`.
4. Em "Environment Variables", adicione duas: `DATABASE_URL` (cole a connection string do Supabase) e `SECRET_KEY` (qualquer texto, ex: `dancouros2026`).
5. Clique em "Create Web Service" e espere o deploy (alguns minutos). Quando terminar, Render te dá um link (algo como `dan-couros-sistema.onrender.com`) — esse é o endereço do sistema, acessível de qualquer computador ou celular.

Se travar em algum desses passos, me diga em qual e eu ajudo a resolver.

## Rodar no seu computador (opcional, para quem já usa terminal/Python)

Requer Python 3.10+.

```bash
cd dan-couros-sistema
python3 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
python3 app.py
```

Abra `http://localhost:5000`. Um banco SQLite (`dan_couros.db`) é criado automaticamente na primeira execução — nenhuma configuração extra é necessária para testar.

## Decisões que tomei e que valem alinhar com o Welington / Dan Couros

- **Status do pedido**: usei `Aberto → Em Produção → Desmontagem → Montagem → Finalizado`, com `Cancelado` como estado terminal à parte, e "Pago" como marcador independente (um pedido pode estar Finalizado e ainda não pago). O rascunho do quadro branco tinha mais anotações soltas (Em Aberto, Produção, Pago com símbolos riscados) que não deu para decifrar com certeza — vale confirmar esse fluxo com eles antes de avançar para o Controle de Produção.
- **CPF/CNPJ**: pedi para marcar manualmente "é pessoa jurídica" em vez de validar o formato do documento, para não travar o cadastro por um CPF/CNPJ digitado fora do padrão.
- **"Fechamentos"**: entendi como os relatórios por período (forma de pagamento, comissionamento) — ainda não implementados nesta v1. Se "fechamento" também significa algo como fechamento de caixa/mês, vale confirmar antes de desenhar esse relatório.
- **Tipo fiscal**: apareceu como pendência anotada à mão na planilha mais recente ("Acrescentar: Tipo Fiscal"), mas sem as opções específicas. Deixei como campo de texto livre por enquanto — assim que soubermos as opções reais (ex: "Com nota" / "Sem nota" / regime específico), transformo num select.
- **Adicionais vs. Composição**: o formulário antigo tinha "Composição" (100% Couro 1a. Qualidade / 70-30 / 50-50 / 100% Courvin Comum) e o material novo mostra uma lista diferente de checkboxes (Assoalho, 100% Couro, Misto, Sintético, Volante, Teto). Mantive os dois campos por enquanto — parecem cobrir coisas um pouco diferentes (composição = mix de material no banco; adicionais = quais partes do carro entram no serviço). Vale confirmar se "Composição" ainda é usada ou se foi substituída pelos "Adicionais".
- **Logomarca**: mudou de Bordado/Prensado/Nada (documento original) para Sim/Não (mockup mais recente) — segui a versão mais recente.
- **Unidade**: no mockup aparece como campo de texto solto ao lado de "Cliente" (ex: nome da filial/loja), separado do "Tipo" (Concessionária/Agência/Particular/Loja). Adicionei como campo livre no cadastro do cliente, editável também por pedido.

## Estrutura do projeto

```
dan-couros-sistema/
  app.py            # rotas Flask
  models.py         # modelo de dados (Cliente, Pedido)
  templates/         # telas (Jinja2)
  static/style.css   # estilo
  requirements.txt
  Procfile           # comando de start para deploy na nuvem
```
