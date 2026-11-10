# C119 — adoção versionada do validador em RAM

09/11/2026, R35S Panel0. C118 reduziu o custo do check completo do host, mas
o caller C105 fixa os dez scripts da cápsula preparada. C119 acrescenta um
contrato explícito de adoção para integrar o host otimizado sem modificar o
pacote instalado ou invalidar as provas antigas. A operação gráfica continua
desabilitada nesta versão; este incremento qualifica adoção, integridade e
recusas, não o tempo de abertura de um jogo.

## Implementação

O preparador residente C112 continua fornecendo a ROM interna, os onze assets
e os dez scripts originais. Um pacote novo de seis arquivos de código e
metadados entra somente em `contract-v2`, dentro da cápsula tmpfs de uso único.
Manifesto, hashes, modos, donos, links e quantidade exata de arquivos são
conferidos. Não há ROM, ELF ou asset nesse upload.

A adoção exige o pacote C105, suas dependências, o stage original, os assets e
os marcadores residentes válidos no boot atual. Ela cria um stage novo e
reserva atomicamente o `caller-stage/run.once` antigo **antes** de substituir
qualquer script. Essa reserva resolve a concorrência com o caller antigo e
contém o digest do contrato novo. Não é um token persistente de boot.

Uma cópia em RAM preserva os três metadados antigos e o host original. A
substituição por rename altera somente `installed-host.sh` da cápsula. O
pacote em `/usr/libexec/muos-caller`, os outros nove scripts, o provider e o
worker permanecem originais. Os metadados antigos não são regravados; o stage
novo registra seu próprio manifesto e o contador/UUID do boot atual.

O novo host mantém os ramos check/launch e todas as validações de conteúdo
originais. Somente o loop de metadata/SHA usa o lote C118; o provider permanece
original porque sua otimização isolada teve ganho pequeno. Uma transformação
inversa reconstrói exatamente a fonte anterior fora desse bloco e do marker.
O entrypoint C119 admite apenas check/adopt/staged e recusa run antes de ler a
plataforma. Preservar um ramo no host não equivale a qualificar sua execução.

Uma falha parcial conserva o stage e a reserva para inspeção e recusa nova
adoção. Não há retry, rearm ou rollback automático. No ensaio concluído, a
remoção da cápsula própria elimina somente essas cópias e reservas em RAM.

## Referências e testes

O fluxo upstream foi consultado em `internal/script/mux/frontend.sh` e
`internal/script/mux/launch.sh`: preparação, execução e retorno são etapas
distintas. C119 reutiliza os adaptadores originais MIT do port, preserva o
worker existente e não copia nem altera código das referências.

As verificações offline usam os contratos shell reais em container rootless,
sem rede, com port/rootfs somente leitura e fixtures em tmpfs. Cobrem adoção,
recusa de repetição, boot diferente, corrupção/ausência de assets e markers,
modos/ownership/hardlinks, reserva antiga adulterada e falha no rename. Também
verificam preservação dos metadados e a recusa do caller antigo após a adoção.
O teste não abre a ROM local nem instala dependências no host.

## Qualificação nativa

39checks offline passaram em `batch-caller/checks.no0hwt5f`, incluindo32casos
do contrato shell real. O publicador foi renderizado e parseado também com as
fontes `.sh` admitidas. A prova pública continua recusando outros tipos e
conteúdo privado; acrescentar fontes shell não libera ROM, ELF ou credenciais.

`batch-caller/profile.3ku0s6rs`, boot83/IP192.168.15.13: quinze recibos nativos0
confirmaram preparo residente, upload de seis arquivos, check, adoção, recusa
de repetição/run, staged e check do host adotado. A verificação completa do
host, incluindo o provider original, levou **1190ms**. É uma amostra por
`/proc/uptime` centesimal, sem controle de frequência; não mede abertura real
nem estabelece uma nova comparação estatística com C118.

Guard191, hashes/modos dos scripts e onze assets, metadados antigos/novos e
bundle foram conferidos. Infraestrutura antes/depois/pós-cleanup e mountinfo
global byte-idênticos; cápsula removida, raizRO0755/PCMclosed/UIoff/p1p3off.
Não houve UI/core/input/áudio, escrita persistente, save, reboot, nova imagem
ou acesso ao Steam Deck/original32. O pacote instalado C105 permanece intacto.

A primeira rodada `profile.yr9jhwfk` também encerrou com quinze recibos0 e
1190ms. Antes da publicação, a revisão detectou que o publicador herdado não
admitia a extensão `.sh` das novas fontes. Seu código exato e recibos foram
preservados; após a correção somente do publicador, checks e ensaio numa cápsula
nova vincularam o conjunto final de fontes. A primeira análise não foi
reescrita nem promovida como prova do publicador corrigido.

Prova sanitizada `dist/phase4/batch-caller`: análise, casos e fontes, sem ROM,
ELFs, UUID, snapshot, seed ou credenciais. Nenhuma aprovação gráfica/acústica
nova pode ser inferida dela. O incremento utiliza poucos MiB de registros,
sem clonar rootfs ou acrescentar uma versão de firmware/checkpoint Git nomeado.

## Próxima integração

Criar uma versão explícita para run e adaptar os vínculos do executor gráfico
ao stage novo, mantendo o worker e a restauração load-only. Só então medir
seleção → primeiro frame e qualificar menu → jogo → menu. C116 continua sendo
a última aprovação física desse fluxo; C119 não muda autostart, saves, imagem,
SDK, kernel, DTB ou política do dongle.
