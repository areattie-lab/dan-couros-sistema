import os
from datetime import datetime, date

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

from models import (
    db,
    Cliente,
    Pedido,
    Producao,
    TIPOS_CLIENTE,
    FORMAS_PAGAMENTO,
    COMPOSICOES,
    STATUS_PEDIDO,
    STATUS_FORA_CONSULTA_PRINCIPAL,
    ADICIONAIS_OPCOES,
    TIPOS_PEDIDO,
    STATUS_PRODUCAO,
    ETAPAS_COSTURA,
)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-troque-em-producao")

# DATABASE_URL vem de variável de ambiente quando publicado na nuvem (ex: Postgres/Supabase).
# Localmente cai para um arquivo SQLite, sem precisar configurar nada.
database_url = os.environ.get("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'dan_couros.db')}")
if database_url.startswith("postgres://"):
    # Compatibilidade com URLs antigas de provedores (Render/Heroku/Supabase)
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


def parse_date(value):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


@app.context_processor
def inject_globals():
    return dict(
        tipos_cliente=TIPOS_CLIENTE,
        formas_pagamento=FORMAS_PAGAMENTO,
        composicoes=COMPOSICOES,
        status_pedido=STATUS_PEDIDO,
        adicionais_opcoes=ADICIONAIS_OPCOES,
        tipos_pedido=TIPOS_PEDIDO,
        status_producao=STATUS_PRODUCAO,
        etapas_costura=ETAPAS_COSTURA,
    )


# ---------- Home ----------

@app.route("/")
def home():
    return redirect(url_for("listar_pedidos"))


# ---------- Clientes ----------

@app.route("/clientes")
def listar_clientes():
    busca = request.args.get("q", "").strip()
    query = Cliente.query
    if busca:
        like = f"%{busca}%"
        query = query.filter(
            db.or_(
                Cliente.nome_razao_social.ilike(like),
                Cliente.cpf_cnpj.ilike(like),
                Cliente.telefone.ilike(like),
            )
        )
    clientes = query.order_by(Cliente.nome_razao_social).all()
    return render_template("clientes_list.html", clientes=clientes, busca=busca)


@app.route("/clientes/novo", methods=["GET", "POST"])
def novo_cliente():
    if request.method == "POST":
        erro = _validar_cliente(request.form)
        if erro:
            flash(erro, "error")
            return render_template("cliente_form.html", cliente=None, form=request.form)

        cliente = Cliente(
            tipo=request.form["tipo"],
            unidade=request.form.get("unidade", "").strip() or None,
            nome_razao_social=request.form["nome_razao_social"].strip(),
            cpf_cnpj=request.form["cpf_cnpj"].strip(),
            is_pessoa_juridica=bool(request.form.get("is_pessoa_juridica")),
            telefone=request.form["telefone"].strip(),
            celular=request.form.get("celular", "").strip() or None,
            email=request.form["email"].strip(),
            contato_nome=request.form.get("contato_nome", "").strip() or None,
            endereco=request.form.get("endereco", "").strip() or None,
        )
        db.session.add(cliente)
        db.session.commit()
        flash("Cliente cadastrado com sucesso.", "success")
        return redirect(url_for("listar_clientes"))

    return render_template("cliente_form.html", cliente=None, form=None)


@app.route("/clientes/<int:cliente_id>/editar", methods=["GET", "POST"])
def editar_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)

    if request.method == "POST":
        erro = _validar_cliente(request.form)
        if erro:
            flash(erro, "error")
            return render_template("cliente_form.html", cliente=cliente, form=request.form)

        cliente.tipo = request.form["tipo"]
        cliente.unidade = request.form.get("unidade", "").strip() or None
        cliente.nome_razao_social = request.form["nome_razao_social"].strip()
        cliente.cpf_cnpj = request.form["cpf_cnpj"].strip()
        cliente.is_pessoa_juridica = bool(request.form.get("is_pessoa_juridica"))
        cliente.telefone = request.form["telefone"].strip()
        cliente.celular = request.form.get("celular", "").strip() or None
        cliente.email = request.form["email"].strip()
        cliente.contato_nome = request.form.get("contato_nome", "").strip() or None
        cliente.endereco = request.form.get("endereco", "").strip() or None
        db.session.commit()
        flash("Cliente atualizado.", "success")
        return redirect(url_for("listar_clientes"))

    return render_template("cliente_form.html", cliente=cliente, form=None)


def _validar_cliente(form):
    if not form.get("nome_razao_social", "").strip():
        return "Nome / Razão social é obrigatório."
    if not form.get("cpf_cnpj", "").strip():
        return "CPF/CNPJ é obrigatório."
    if not form.get("telefone", "").strip():
        return "Telefone é obrigatório."
    if not form.get("email", "").strip():
        return "Email é obrigatório."
    if form.get("is_pessoa_juridica") and not form.get("contato_nome", "").strip():
        return "Para pessoa jurídica (CNPJ), o nome do contato é obrigatório."
    return None


# API pequena usada pelo formulário de Pedido para auto-preencher contato/telefone
@app.route("/api/clientes/<int:cliente_id>")
def api_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    return jsonify(
        {
            "id": cliente.id,
            "telefone": cliente.telefone,
            "celular": cliente.celular or "",
            "contato": cliente.contato_nome or cliente.nome_razao_social,
            "tipo": cliente.tipo,
            "unidade": cliente.unidade or "",
            "endereco": cliente.endereco or "",
        }
    )


# ---------- Pedidos ----------

@app.route("/pedidos")
def listar_pedidos():
    aba = request.args.get("aba", "ativos")  # ativos | finalizados | todos
    query = Pedido.query

    if aba == "ativos":
        query = query.filter(~Pedido.status.in_(STATUS_FORA_CONSULTA_PRINCIPAL))
    elif aba == "finalizados":
        query = query.filter(Pedido.status.in_(STATUS_FORA_CONSULTA_PRINCIPAL))
    # "todos" não filtra

    pedidos = query.order_by(Pedido.id.desc()).all()
    return render_template("pedidos_list.html", pedidos=pedidos, aba=aba)


@app.route("/pedidos/novo", methods=["GET", "POST"])
def novo_pedido():
    clientes = Cliente.query.order_by(Cliente.nome_razao_social).all()

    if request.method == "POST":
        pedido = Pedido(status=request.form.get("status", "Aberto"))
        _preencher_pedido(pedido, request.form)
        db.session.add(pedido)
        db.session.commit()
        flash(f"Pedido #{pedido.id} criado.", "success")
        return redirect(url_for("listar_pedidos"))

    return render_template("pedido_form.html", pedido=None, clientes=clientes)


@app.route("/pedidos/<int:pedido_id>/editar", methods=["GET", "POST"])
def editar_pedido(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    clientes = Cliente.query.order_by(Cliente.nome_razao_social).all()

    if request.method == "POST":
        _preencher_pedido(pedido, request.form)
        pedido.status = request.form.get("status", pedido.status)
        db.session.commit()
        flash(f"Pedido #{pedido.id} atualizado.", "success")
        return redirect(url_for("listar_pedidos"))

    return render_template("pedido_form.html", pedido=pedido, clientes=clientes)


def _preencher_pedido(pedido, form):
    pedido.cliente_id = int(form["cliente_id"])
    pedido.contato_pedido = form.get("contato_pedido", "").strip() or None
    pedido.telefone_pedido = form.get("telefone_pedido", "").strip() or None
    pedido.celular_pedido = form.get("celular_pedido", "").strip() or None
    pedido.unidade_pedido = form.get("unidade_pedido", "").strip() or None
    pedido.endereco_pedido = form.get("endereco_pedido", "").strip() or None

    pedido.tipo_pedido = form.get("tipo_pedido") or None
    pedido.tipo_fiscal = form.get("tipo_fiscal", "").strip() or None

    pedido.data_pedido = parse_date(form.get("data_pedido")) or date.today()
    pedido.data_entrega = parse_date(form.get("data_entrega"))

    pedido.veiculo = form.get("veiculo", "").strip() or None
    pedido.modelo = form.get("modelo", "").strip() or None
    pedido.ano = form.get("ano", "").strip() or None
    pedido.chassis = form.get("chassis", "").strip() or None

    pedido.cor_revestimento_1 = form.get("cor_revestimento_1", "").strip() or None
    pedido.cor_revestimento_2 = form.get("cor_revestimento_2", "").strip() or None
    pedido.cor_linha = form.get("cor_linha", "").strip() or None
    pedido.banco_acabamento = form.get("banco_acabamento") or None
    pedido.laterais_acabamento = form.get("laterais_acabamento") or None
    pedido.logomarca = bool(form.get("logomarca"))
    pedido.apoio_braco = bool(form.get("apoio_braco"))
    pedido.volante = form.get("volante") or None
    pedido.encosto = form.get("encosto") or None
    pedido.assento = form.get("assento") or None
    pedido.composicao = form.get("composicao") or None
    pedido.adicionais = form.getlist("adicionais") or []

    pedido.observacoes = form.get("observacoes", "").strip() or None

    pedido.forma_pagamento = form.get("forma_pagamento") or None
    preco_raw = form.get("preco", "").replace(",", ".").strip()
    pedido.preco = float(preco_raw) if preco_raw else None
    pedido.nf_numero = form.get("nf_numero", "").strip() or None
    pedido.pago = bool(form.get("pago"))


@app.route("/pedidos/<int:pedido_id>")
def ver_pedido(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    return render_template("pedido_detalhe.html", pedido=pedido)


# ---------- Produção (2ª linha do tempo) ----------

@app.route("/producao")
def listar_producao():
    # Chão de fábrica: só pedidos que já têm registro de produção e não terminaram.
    registros = (
        Producao.query.join(Pedido)
        .filter(Producao.status_producao != "OK")
        .order_by(Producao.prioridade.asc().nullslast(), Producao.data_entrada.asc())
        .all()
    )
    return render_template("producao_list.html", registros=registros)


@app.route("/pedidos/<int:pedido_id>/producao", methods=["GET", "POST"])
def editar_producao(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    producao = pedido.producao or Producao(pedido_id=pedido.id)

    if request.method == "POST":
        producao.prioridade = int(request.form["prioridade"]) if request.form.get("prioridade") else None
        producao.fornecedor_responsavel = request.form.get("fornecedor_responsavel", "").strip() or None

        producao.data_entrada = parse_date(request.form.get("data_entrada"))
        producao.data_saida = parse_date(request.form.get("data_saida"))
        producao.status_producao = request.form.get("status_producao") or "Pendente"

        producao.etapa_costura = request.form.get("etapa_costura") or None
        producao.montagem_feita = bool(request.form.get("montagem_feita"))
        producao.laterais_feita = bool(request.form.get("laterais_feita"))
        producao.ruga = bool(request.form.get("ruga"))

        for campo in ("metros_couro", "metros_sintetico", "metros_espuma"):
            valor = request.form.get(campo, "").replace(",", ".").strip()
            setattr(producao, campo, float(valor) if valor else None)

        producao.data_desmontagem = parse_date(request.form.get("data_desmontagem"))
        producao.motorista_desmontagem = request.form.get("motorista_desmontagem", "").strip() or None
        producao.data_montagem = parse_date(request.form.get("data_montagem"))
        producao.motorista_montagem = request.form.get("motorista_montagem", "").strip() or None

        producao.checklist_pecas_plasticas_desmontagem = bool(request.form.get("checklist_pecas_plasticas_desmontagem"))
        producao.checklist_parte_eletrica_desmontagem = bool(request.form.get("checklist_parte_eletrica_desmontagem"))
        producao.checklist_banco_laterais_desmontagem = bool(request.form.get("checklist_banco_laterais_desmontagem"))
        producao.checklist_de_acordo_desmontagem = request.form.get("checklist_de_acordo_desmontagem", "").strip() or None

        producao.checklist_pecas_plasticas_montagem = bool(request.form.get("checklist_pecas_plasticas_montagem"))
        producao.checklist_parte_eletrica_montagem = bool(request.form.get("checklist_parte_eletrica_montagem"))
        producao.checklist_banco_laterais_montagem = bool(request.form.get("checklist_banco_laterais_montagem"))
        producao.checklist_de_acordo_montagem = request.form.get("checklist_de_acordo_montagem", "").strip() or None
        producao.checklist_observacoes = request.form.get("checklist_observacoes", "").strip() or None

        producao.observacoes = request.form.get("observacoes", "").strip() or None

        if producao.id is None:
            db.session.add(producao)
        db.session.commit()
        flash(f"Produção do pedido #{pedido.id} salva.", "success")
        return redirect(url_for("ver_pedido", pedido_id=pedido.id))

    return render_template("producao_form.html", pedido=pedido, producao=producao)


@app.route("/pedidos/<int:pedido_id>/checklist")
def imprimir_checklist(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    producao = pedido.producao or Producao(pedido_id=pedido.id)
    return render_template("checklist_print.html", pedido=pedido, producao=producao)


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
