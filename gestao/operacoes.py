import hashlib
import json
import uuid

from django.db import IntegrityError, transaction

from .models import OperacaoFormulario


def executar_operacao_unica(
    chave,
    usuario,
    acao,
    dados,
    executar,
):
    try:
        chave = uuid.UUID(str(chave))
    except (ValueError, TypeError, AttributeError):
        raise ValueError(
            "Identificador de envio inválido. "
            "Reabra a página e tente novamente."
        )

    dados_serializados = json.dumps(
        dados,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    assinatura = hashlib.sha256(
        dados_serializados.encode("utf-8")
    ).hexdigest()

    with transaction.atomic():
        try:
            # A restrição única no banco protege também
            # contra duas requisições simultâneas.
            with transaction.atomic():
                operacao = OperacaoFormulario.objects.create(
                    chave=chave,
                    usuario=usuario,
                    acao=acao,
                    assinatura_dados=assinatura,
                )

        except IntegrityError:
            operacao = OperacaoFormulario.objects.filter(
                chave=chave,
            ).first()

            if operacao is None:
                raise

            if (
                operacao.usuario_id != usuario.pk
                or operacao.acao != acao
                or operacao.assinatura_dados != assinatura
            ):
                raise ValueError(
                    "Este identificador já foi usado em outro envio. "
                    "Reabra a página para iniciar uma nova operação."
                )

            if not operacao.destino:
                raise ValueError(
                    "Não foi possível recuperar o resultado "
                    "deste envio."
                )

            return operacao.destino, False

        # Se a operação falhar, o registro do identificador
        # também será desfeito.
        destino = executar()

        if (
            not isinstance(destino, str)
            or not destino.startswith("/")
            or destino.startswith("//")
            or len(destino) > 250
        ):
            raise ValueError(
                "O destino da operação é inválido."
            )

        operacao.destino = destino
        operacao.save(update_fields=["destino"])

        return destino, True