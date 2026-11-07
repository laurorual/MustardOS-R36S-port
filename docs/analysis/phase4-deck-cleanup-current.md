# C101 — limpeza do Steam Deck após C99

Data: 05/11/2026. O leitor não é necessário para preparar o próximo layout
offline. Antes da limpeza foram reconferidos os12artefatos do backup independente
no host, o novo fence C94 e as provas C97/C99. Backups e ferramentas locais
permanecem disponíveis para reconstruir pacotes se o leitor voltar a ser necessário.

O inventário SSH encontrou42diretórios do projeto em /home/deck e /var/tmp,
leitor vazio e regra temporária C83 ativa. O helper C101 passou14testes de
escopo/aliases/remoção em diretórios descartáveis e foi transferido com hash
conferido. O usuário executou com sudo local, informou falha e preferiu apagar
os diretórios manualmente. A causa não foi investigada nem o helper repetido.
Isso não constitui aprovação nativa do helper.

Foram fornecidos comandos restritos aos prefixos muos-r35s-c* nos diretórios
/home/deck, /var/tmp, /tmp e /run, mais o caminho exato da regra temporária
/run/udev/rules.d/99-holo-automount.rules e o eventual recibo temporário.
A orientação para authorized_keys foi remover somente a entrada com comentário
muos-r35s-offline-c20, preservando outras chaves e o serviço SSH.

O usuário confirmou: “Terminei e deu tudo certo”. Limpeza registrada conforme
essa confirmação, sem nova auditoria SSH e sem afirmar quantidade exata de
bytes liberados ou conclusão pelo helper. Não pedir reinstalação da chave
somente para repetir essa auditoria. O cartão128 permaneceu no R35S; original32
guardado. Não houve gravação de cartão por esta limpeza.
