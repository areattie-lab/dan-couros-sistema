from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

TIPOS_CLIENTE = ["Concessionária", "Agência", "Particular", "Loja"]

FORMAS_PAGAMENTO = ["Cartão", "Pix", "Cheque", "Dinheiro", "Boleto"]

COMPOSICOES = [
    "100% Couro de 1a. Qualidade",
    "70% / 30%",
    "50% / 50%",
    "100% Courvin Comum",
]

# Itens adicionais do pedido — vistos no material mais recente (OS e mock atualizados).
# Multi-select: um pedido pode incluir vários.
ADICIONAIS_OPCOES = [
    "Assoalho",
    "100% Couro",
    "Misto",
    "Sintético",
    "Volante",
    "Teto",
]

TIPOS_PEDIDO = ["Diversos", "Revenda"]

# Status principal do pedido (1a linha do tempo).
# "Pago" é tratado como flag separada (um pedido finalizado pode estar pago ou não).
STATUS_PEDIDO = [
    "Aberto",
    "Em Produção",
    "Desmontagem",
    "Montagem",
    "Finalizado",
    "Cancelado",
]

# Status que saem da consulta principal (ficam numa aba separada)
STATUS_FORA_CONSULTA_PRINCIPAL = ["Finalizado", "Cancelado"]


class Cliente(db.Model):
    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20), nullable=False)  # Concessionária/Agência/Particular/Loja
    unidade = db.Column(db.String(150))  # filial/loja específica, ex: "Concessionária XYZ - Loja Centro"
    nome_razao_social = db.Column(db.String(200), nullable=False)
    cpf_cnpj = db.Column(db.String(20), nullable=False)
    is_pessoa_juridica = db.Column(db.Boolean, default=False)
    telefone = db.Column(db.String(30), nullable=False)
    celular = db.Column(db.String(30))
    email = db.Column(db.String(120), nullable=False)
    contato_nome = db.Column(db.String(120))  # obrigatório se PJ
    endereco = db.Column(db.String(300))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    pedidos = db.relationship("Pedido", backref="cliente", lazy=True)

    def __repr__(self):
        return f"<Cliente {self.nome_razao_social}>"


class Pedido(db.Model):
    __tablename__ = "pedidos"

    id = db.Column(db.Integer, primary_key=True)  # "chave" - número de pedido automático
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False)

    # Snapshot editável (carregado do cadastro, mas pode variar por pedido)
    contato_pedido = db.Column(db.String(120))
    telefone_pedido = db.Column(db.String(30))
    celular_pedido = db.Column(db.String(30))
    unidade_pedido = db.Column(db.String(150))
    endereco_pedido = db.Column(db.String(300))

    tipo_pedido = db.Column(db.String(20))  # Diversos / Revenda
    tipo_fiscal = db.Column(db.String(50))  # a confirmar com Welington/Dan Couros

    data_pedido = db.Column(db.Date, default=datetime.utcnow)
    data_entrega = db.Column(db.Date)

    # Veículo
    veiculo = db.Column(db.String(100))
    modelo = db.Column(db.String(100))
    ano = db.Column(db.String(10))
    chassis = db.Column(db.String(50))

    # Revestimento
    cor_revestimento_1 = db.Column(db.String(50))
    cor_revestimento_2 = db.Column(db.String(50))
    cor_linha = db.Column(db.String(50))
    banco_acabamento = db.Column(db.String(20))  # Liso / Enrugado / Furado
    laterais_acabamento = db.Column(db.String(20))
    logomarca = db.Column(db.Boolean, default=False)  # Sim / Não
    apoio_braco = db.Column(db.Boolean, default=False)
    volante = db.Column(db.String(20))  # Liso / Furado (acabamento, se volante fizer parte do pedido)
    encosto = db.Column(db.String(20))  # Inteiro / Bi-partido
    assento = db.Column(db.String(20))  # Inteiro / Bi-partido
    composicao = db.Column(db.String(50))  # uma das COMPOSICOES
    adicionais = db.Column(db.JSON, default=list)  # lista de ADICIONAIS_OPCOES

    observacoes = db.Column(db.Text)

    # Comercial
    forma_pagamento = db.Column(db.String(20))  # uma das FORMAS_PAGAMENTO
    preco = db.Column(db.Numeric(10, 2))
    nf_numero = db.Column(db.String(30))

    status = db.Column(db.String(20), default="Aberto", nullable=False)
    pago = db.Column(db.Boolean, default=False)

    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Pedido #{self.id}>"
