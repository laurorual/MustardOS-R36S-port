# C120 — execução limitada pelo contrato versionado

09/11/2026, R35S Panel0. O usuário solicitou somente testes automáticos nesta
rodada. A integração acrescenta uma versão própria para run, sem alterar as
fontes/provas C119 ou o pacote instalado C105. Nenhuma confirmação física nova
é presumida.

## Contrato

O bundle de seis arquivos fica em `contract-v3` numa cápsula tmpfs nova. A
adoção reaproveita as mesmas verificações, backup e reserva atômica do caller
antigo aprovados em C119, com manifesto e stage novos. O host usa o lote; o
provider, os outros nove scripts e o worker instalado permanecem originais.
Não há ROM ou ELF no bundle. O preparador continua lendo a ROM interna e
copiando os assets residentes, sem uploads de conteúdo.

`run <capsule> observe` verifica pacote/dependências, readiness/PCM fechado,
boot, metadados, assets e todos os scripts antes de criar seu próprio
`run.once`. O mkdir consome a tentativa antes do exec; erro no runner não
permite reenvio. Outros modos, aridades, cápsulas e stage incompleto são
recusados. O argv do exec preserva exatamente o subreaper de 240s, namespace
privado e worker instalado C105; filho de 210s e jogo de 45s permanecem no
caminho original. Não há save ou autostart novo.

O executor gráfico foi adaptado para adoção do contrato novo, witness do host
em lote e conferência de ambas as reservas e metadados. O watcher e os checks
de mapas, snapshot load-only, restauração, cleanup e timing continuam os de
C116/C109. Preparação, execução e retorno upstream foram conferidos em
`internal/script/mux/frontend.sh` e `launch.sh`; nenhum arquivo de referência
ou subsistema foi copiado/alterado. A implementação do port é MIT.

## Testes e limites da qualificação

O laboratório usa funções shell reais num container sem rede, port/rootfs RO
com fixtures em tmpfs. O runner da fixture apenas registra argv e retorna um
status controlado: não cria namespace de dispositivo nem inicia UI. Assim é
possível conferir o exec real, dono/modo do claim, recusa de repetição e falha
74, sem confundir isso com uma execução gráfica nativa.

47checks offline passaram em `batch-run/checks.4gt4zitu`, incluindo43casos
com funções shell reais. A transformação conserva os testes de adoção C119,
acrescentando execução bem-sucedida do runner de fixture, argv exato, claim
modo0700, erro74 sem retry e recusas antes do claim para modo/aridade/cápsula,
boot, plataforma, host, asset ou reserva inválidos. O harness gráfico foi
parseado, assim como os comandos de validação antes/depois da adoção e o
executor nativo sem GUI. Não houve rede nem leitura da ROM local nesses testes.

`batch-run/profile.o2mnkrh6`, mesmo boot83/IP192.168.15.13: quinze etapas
nativas0. Preparo residente, upload do bundle29.161bytes, check/adopt/staged,
recusa de nova adoção, run com modo save e aridade incompleta, verificação do
host adotado e conferência posterior passaram. A nova reserva de run ficou
ausente: o comando válido de execução **não foi chamado no console**.

Host em lote incluindo provider original:1190ms numa amostra, relógio uptime
centesimal sem controle de frequência. Não mede abertura real ou comprova
melhoria percebida. Guard191, hashes/modos/links do bundle, scripts/assets e
metadados conferidos; infraestrutura antes/depois/pós-cleanup e mountinfo
global byte-idênticos. Cápsula removida, raizRO0755/PCMclosed/UIoff/p1p3off.
Sem core, áudio, botões, reboot, save, instalação ou escrita persistente.
Original32/Deck/SDK/imagens não foram acessados nem alterados.

Prova sanitizada `dist/phase4/batch-run`: resumo/checks/fontes, sem ROM, ELF,
UUID, seeds ou snapshot. Fontes/provas C119 anteriores preservadas. O trace
de retenção passa a incluir a prova nova, bundle e recibos; permanecem cinco
versões de firmware e cinco checkpoints Git nomeados, sem imagem integral nova.

O fluxo menu → jogo → restauração → menu com este contrato continua pendente;
C116 permanece a aprovação física do caminho anterior. Não há medição nova
seleção → primeiro frame nem confirmação acústica ou de controles nesta rodada.
