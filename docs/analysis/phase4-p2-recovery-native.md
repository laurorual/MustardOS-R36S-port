# C89 — qualificação nativa da recuperação p2

A [preparação C89](phase4-p2-recovery.md) e suas 75 verificações offline
precedem esta etapa. A candidata C79 continua separada: este ciclo recupera
a instalação C76 atual e qualifica o caminho de recuperação antes de migrar.
O cartão original de 32 GB permanece fora do fluxo.

## Captura pós-boot e composição aprovadas

Em 04/11/2026, o test128 retornou ao Steam Deck após o boot 73 e desligamento
normal do R35S. O helper C86 pós-boot usou o registro C84 selado antes da
entrega ao console. Capturou a p2 inteira de 512 MiB com fsck0, contador73,
seis arquivos privados e preservação de MBR/prefixo de boot. A cópia no host
passou nos hashes/fsync e num novo scan C85 independente; árvores e observações
coincidiram. A captura não escreveu payload nem gerou seed.

O compositor C85 produziu uma imagem regular de recuperação com contador74,
seed.no-credit novo de 256 bytes, remoção dos seeds antigos e fsck0. Árvore
pública, identidade estável e históricos foram preservados. Não houve carga
de seed no RNG nem operação de mídia pelo compositor.

## Verificação da execução física

O pacote C89 foi transferido com hashes/readback conferidos. A prova
`p2-recovery-native` só é publicada depois de verificar o recibo do helper,
o journal, a composição e a coleta independente do próximo fence. Sua ausência
não pode ser substituída pelo sucesso da composição ou do pacote.

A transação restringe a escrita à p2 e compara o complemento inteiro do cartão
em várias passagens, incluindo cerca de118GiB da p3. Exige fonte elegível,
backup independente e registro de intenção durável antes da escrita. Após
fsync, hash e releitura fria, restaura RO e sela um novo registro C84; esse
registro precisa ser copiado e conferido no host antes de mover o cartão.
Falhas conservam o estado parcial e não iniciam retry/rollback automático.

Um observador sem sudo pode acompanhar uma tentativa já em execução e chamar
o coletor e o publicador uma única vez após o término. Ele lê apenas estado
do kernel e metadados dos resultados; não inicia, interrompe ou repete o helper
do Deck. Mudança de identidade/proteção, falha de SSH, relatório de erro ou
timeout encerram somente o observador, preservando a operação e o cartão.

Mesmo após uma recuperação física concluída, o boot seguinte ainda precisa
qualificar RNG/rede/contador/identidade. O helper não inicia boot nem autoriza
migração C79. Os caminhos privados e a ação seguinte ficam no
[checkpoint](phase4-resume-checkpoint.md).
