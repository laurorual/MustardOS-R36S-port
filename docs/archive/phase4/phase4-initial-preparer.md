# C93 — preparador inicial e validação por descritores

Em05/11/2026, foi implementado o preparador da composição C92 e o callback
de elegibilidade para o futuro gravador inicial. O cartão pode permanecer no
R35S. Não houve SSH, acesso a dispositivos, deploy, desbloqueio ou escrita na
mídia; os testes físicos C89/boot75 continuam válidos e não foram repetidos.

## Vínculos antes de compor

`prepare-phase4-initial-migration.py check|compose` exige as provas congeladas,
o recibo C89, o journal e o próximo registro de handoff coletado independentemente.
A evidência do primeiro boot após recuperação precisa estar vinculada ao mesmo
recibo; o rascunho automatizado C91 não é executado nem usado como requisito.

Antes de ler imagens grandes ou gerar seed, os cabeçalhos C86 precisam apontar
para esse registro atual e um contador igual ou superior ao boot qualificado.
Depois, o coletor C86 existente revalida hash/árvore/observação da cópia host.
Captura73/registro anterior são recusados após a recuperação74/boot75.
Um novo boot do usuário pode elevar o contador; uma nova captura válida pode
trazer esse contador maior, sem presumir retrocesso ou repetir o teste75.

Os arquivos atuais do backup host são conferidos por descritores: tipos,
owner, modos privados, links, tamanho, hashes e assinatura de metadados.
Recibo, inventário, prefixo e cópia independente permanecem vinculados ao C82.
Não é suficiente que o backup tenha existido quando o C89 foi executado.

A fonte factory é a cópia privada `factory.ext4` já criada no C88, com hash
fixado à fábrica pública C79. A candidata antiga C88 e seus seeds não são
usados. Reutilizar essa cópia evita outra alocação de512MiB. O preparador
executa somente a CLI C92 no container existente, sem rede/dispositivos, e
confere candidata, contadores, fontes e recibos antes de publicar conclusão.
Um claim exclusivo e sincronizado impede repetir automaticamente a composição
após interrupção e gerar outro seed. Ainda não foi executada composição nova
de produção: falta captura física atualizada ligada ao fence correto.

## Callback do futuro controlador

`phase4_p2_initial.validate_fd` valida o descritor real da candidata, exige
arquivo privado regular do tamanho esperado, nlink1 e hash, e mantém flock.
Fábrica e snapshot atual passam pelos guardas de arquivos fonte e scans C88/
C85; a candidata é percorrida pelo próprio descritor. A política C92 deriva
árvore pública nova, identidade/históricos, seed e contador dessas leituras.
Hash e assinatura da candidata são novamente conferidos após os scans.

Isso prepara o callback anterior ao desbloqueio do Controller C87; **não cria
um gravador**. A futura entrada finita privilegiada ainda precisa fixar o hash
da fábrica C79, conferir o cartão test128/backup remoto/kernel/proteções, capturar
novamente a p2 física, comparar seu hash, usar o callback e selar/coletar o novo
fence. JSON ou sucesso do preparador não substitui essas operações.
O modo de recuperação C89 permanece inalterado e não aceita a árvore nova.

## Verificações e limites

**30casos passaram** em container sem rede/dispositivos, com ext4 sintéticos
reais32MiB: registro atual, boot conhecido e contador mais novo; recusas de
registro antigo, referência usada como pós-boot, contador73/booleano/esgotado,
hash/contexto alterado; arquivos de backup com bytes/metadados/tamanhos/links
inválidos; três scans reais derivados de descritores; candidata com hash,
tamanho, modo ou links incorretos, snapshot symlink, descritor não regular e
alteração concorrente de metadados. O callback preserva o descritor do chamador
e os bytes das fontes. Imagens sintéticas foram descartadas após logs.

Auditorias reais somente leitura confirmaram os12artefatos do backup host e
a cópia factory privada contra C79. O preparador recusou a captura73 existente
antes de iniciar container, RNG ou estágio. Logs privados em
`build/phase4/initial-migration/preparer-checks.96fs6x7v`,
pointer latest-preparer-checks. Fontes C92/C89 e referências não foram alteradas.
Código novo MIT; reutiliza contratos locais já revistos, sem código upstream novo.

O main de composição não foi exercitado de ponta a ponta com captura nova;
não há nova candidata512MiB de produção, seed real, handoff ou migração física
qualificados. Prova sanitizada `dist/phase4/initial-preparer`.
Próximo incremento: entrada finita privilegiada, preparação de pacote/recebimento,
coletor e testes de falhas. Só depois pedir cartão no Deck para nova captura.
Original32, saves/ROM, backups, SDK e ferramentas do Deck permanecem preservados.
