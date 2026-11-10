# C92 — composição inicial C79 com estado privado atualizado

Em05/11/2026, foi implementado um compositor de arquivo ext4 para a migração
inicial C79. Esta etapa é offline: o test128 pode permanecer no R35S. Não há
controlador físico novo, acesso por SSH, escrita de cartão ou solicitação de
boot. A recuperação C89 e seu boot75 continuam aprovados, sem repetir testes
físicos. A candidata C88 com estado72 permanece desatualizada e não é usada.

## Composição e elegibilidade

`phase4_initial_migration.py` reutiliza o provisionador C88, o scanner C85 e a
política C84, todos próprios MIT e preservados sem alterações. A consulta
upstream/licenças da fábrica e da rede está registrada no
[C88](phase4-initial-image.md); nenhum subsistema upstream novo foi copiado.

As entradas são fábrica pública e captura offline pós-handoff, ambas regulares
e verificadas por descritor/hash, mais o backup e registro C84 vinculados à
captura. O intermediário C88 existe apenas dentro do estágio privado; é
consumido por link exclusivo/unlink antes da transformação, sem duplicar outra
imagem de512MiB. Seu recibo não é conclusão C92 nem candidata de handoff.

A árvore pública e seus metadados precisam corresponder à fábrica C79.
Identidade de rede, EAs privados e históricos consumidos vêm da captura; os
dois diretórios privados novos mantêm0700. Seeds anteriores são removidos e
substituídos por seed.no-credit256 novo, gerado por getrandom não bloqueante
do host pronto, sem carga/crédito de entropia. O contador reserva max conhecido
+1. Exemplo sintético: backup72, registro74 e captura75 produzem76; o primeiro
C07 incrementaria para77. Nenhum registro de handoff é criado pelo compositor.

Fsck0 e nova leitura integral verificam conteúdo público, identidade, EAs,
históricos, seed e contador antes de publicar conclusão. Fontes são novamente
conferidas depois da composição. EAs externos nos privados substituídos são
recusados, mantendo o limite já observado do debugfs. O estágio ganha um
marcador exclusivo e sincronizado antes do processamento: falhas conservam
parciais e uma nova chamada nesse estágio é recusada antes de gerar outro seed.

`phase4-initial-migration.py` aceita somente caminhos privados sob `/work`,
schema finito e imagens regulares512MiB. O módulo e os testes também usam
32MiB sintéticos. **Contexto/JSON não autentica captura nem libera gravação:**
o futuro preparador/controlador precisa fixar a factory C79 aprovada, o registro
mais recente já coletado independentemente, o contador conhecido, a captura
física nova e a custódia offline do cartão. C92 sozinho não faz esses vínculos
com o estado vivo. Não usar registro/captura antigos para tornar uma imagem
desatualizada elegível.

## Verificação e próximo passo

**25casos passaram**, com ext4 sintéticos reais e sem dispositivo/rede:
fábrica nova em lugar da árvore pública antiga; identidade/histórico/symlink/
EAs/fontes preservados; seed novo sem crédito e contador76/primeiro77; recusas
de estado72 abaixo do registro74, identidade/modos/contador/seed/EAs alterados,
contexto inválido, RNG indisponível/curto/repetido, clone ou troca de seed
interrompidos, estágio parcial/concluído repetido e saída symlink. Entradas
fora de `/work` são recusadas. Imagens sintéticas foram descartadas após logs.

Estágio `build/phase4/initial-migration/checks.kmmw5f7q`, pointer latest-checks.
Nenhuma nova candidata de produção512MiB foi composta e nenhum seed real de
produção foi gerado nesta etapa. A prova sanitizada fica em
`dist/phase4/initial-migration`.

Próximo incremento: preparador e controlador finito da migração inicial,
com qualificação de bindings/captura/backup/fence antes da escrita p2-only.
Depois será necessário desligar normalmente o R35S e levar test128 ao Deck
para captura atualizada. Não mover mídia até essa preparação estar pronta.
Original32, backups, ferramentas do Deck, SDK e referências permanecem intactos.
