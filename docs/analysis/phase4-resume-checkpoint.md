# Fase 4 — ponto seguro de retomada

## Estado atual — C121 menu → GB → menu APROVADO no boot84

**09/11/2026:** R35S **192.168.15.15:2222**, **boot84/C07 pronto**. Cartão128GB
no console; original32 guardado e Deck fora do fluxo. Novo boot observado, sem
pedido de reboot nesta rodada. C112/C113/C114 continuam aprovados; instalações,
importação e claims anteriores não foram repetidos. [C116](phase4-resident-boot-session.md)
constrói o contexto atual sem alterar fontes/provas/UUIDs históricos.

**C121 APROVADO gráfico/físico:** [sessão e métricas](phase4-batch-graphics-session.md),
observação `batch-graphics/observe.g0k9zci0` vinculada ao novo84/UUID real, guard191.
Rodada única `load.0hrtc9t5`,17recibos0/OPERATION0/CLEANUP0/1134frames.
Menu→GB→restoreFn+L2→exitFn+Start→menu confirmados; usuário relatou abertura
“melhorou um pouco”. Host C120 em lote executou launch; worker instalado e
três mapas reais conferidos. Provider original, pacote C105 e metadados
antigos preservados; reservas RAM antiga/nova e seis arquivos do bundle
conferidos. Onze assets+ROM internos, zero uploads de inputs/ROM/ELFs; só
bundle de código29.161bytes enviado à RAM. Snapshot/inventários C63 byte-idênticos,
nenhum save novo. Análise técnica/física/fechamento vinculados à mesma sessão.
Prova sanitizada **`dist/phase4/batch-graphics`** publicada; fontes congeladas.

Seleção consumida→primeiro frame observado**4,27s**, versus7,37s registrado no
C116. Amostragem nominal1s, sem timestamp físicoA/controle de cache/frequência
ou limite de atraso do watcher: indicação nesta rodada, não percentual de
ganho garantido. Startup interno1369,42ms;59,8802Hz recentes/frame16,6834ms.
Áudio4underruns/1971frames ausentes, sem distorção relatada; não é áudio sem
perdas nem estabilidade longa. Infra/mountinfo/mixer/DRM/WirePlumber/preferências
preservados; raizRO0755/PCMclosed/UIoff/p1p3off/taint0, RAM removida e tela final
diagnóstica escrita. SDK/imagem C64 intactos. Sem instalação/reboot/Deck/original32.

**Histórico C121 PREPARADO/OBSERVADO sem GUI:** [contexto corrigido](phase4-batch-graphics.md),
oito checks `batch-graphics/checks.kkoqulgn` e observação nativa somente leitura
`observe.t97ip2u4`, mesmo83/IP13, guard191/infra/UUID aprovados. Detectada colisão
de `NAMES` no harness gráfico C120: seis arquivos do bundle versus quatro
bibliotecas. C121 separa os namespaces sem alterar fontes/prova C120; executa
os loops reais com os quatro arquivos corretos, zero uploads de inputs e
recusa vínculos de observação C120 incorretos. Usar o novo entrypoint
`run-phase4-batch-graphics.py`, NÃO o harness `run-phase4-batch-run.py`.
Não houve novo preparo/GUI/áudio/botões/reboot/escrita no aparelho no C121.
Naquela etapa não havia prova gráfica. Adaptadores próprios
de análise/fechamento preparados; CLI help e recusa de estágio C120 passaram.
Análise/fechamento ainda estavam pendentes; ambos qualificados na rodada84 acima.

**C120 contrato/adoção APROVADOS; gráfico pendente:** [execução versionada](phase4-batch-run.md).
Por solicitação do usuário, sem teste físico/GUI nesta rodada.47checks offline
`batch-run/checks.4gt4zitu`, incluindo43casos shell reais, passaram. Bundle de
seis arquivos/29.161bytes, `contract-v3`, host em lote e provider/worker
originais. Run admite apenas observe, cria claim próprio antes de exec e
mantém subreaper240s/filho210s/jogo45s. Fixture registra argv real e erro74,
sem iniciar UI; repetição/modos/boot/asset/claim inválidos recusados.
Executor gráfico preparado para o stage novo e witness C120; parse/routing
testados, **nenhum ciclo gráfico novo aprovado ou cronometrado**.
`batch-run/profile.o2mnkrh6`, mesmo83/IP13,15recibos nativos0: check/adopt/staged,
refusals de repetição/run save/aridade e check host1190ms numa amostra. Run
válido NÃO foi chamado no console; claim novo ausente. Guard191/bundle/assets/
scripts/metadados aprovados, infra/mountinfo iguais, RAM removida e raizRO0755/
PCMclosed/UIoff/p1p3off. Sem save/reboot/GUI/escrita persistente/Deck. Prova
sanitizada `dist/phase4/batch-run`, sem ampliar a aprovação física C116.

**C119 APROVADO sem UI:** [contrato versionado](phase4-batch-caller.md),
`batch-caller/profile.3ku0s6rs`, mesmo83/IP13.39checks offline
`checks.no0hwt5f`, incluindo32casos com os contratos shell reais em container.
Bundle de seis arquivos/28.743bytes somente em RAM; substitui apenas o host
da cápsula por validação em lote, preservando provider/worker e pacote C105
instalados. Cópia anterior e stage próprio ligados ao boot atual. Os três
metadados antigos ficam byte-idênticos; seu `run.once` RAM é reservado
atomicamente antes da troca para impedir corrida com o caller antigo.
CLI admite check/adopt/staged; run e nova adoção são recusados. Não remover
reservas de uma tentativa parcial para repeti-la. GUI/abertura real ainda
não qualificadas pelo C119; C116 permanece a aprovação física vigente.
Quinze recibos nativos0; host adotado+provider original1190ms numa amostra
uptime centesimal, sem medir abertura. Infra/mountinfo byte-idênticos, RAM
removida, raizRO0755/PCMclosed/UIoff/p1p3off; sem escrita persistente/save/reboot/
imagem/instalação/Deck/original32. Prova sanitizada `dist/phase4/batch-caller`.
Primeira rodada `profile.yr9jhwfk` também fechou0; fontes/recibos preservados.
Repetição necessária após corrigir apenas a admissão de fontes `.sh` no
publicador, vinculando o conjunto final sem reescrever a análise anterior.

**C118 APROVADO sem UI:** [validação em lote](phase4-batch-validation.md),
`batch-validation/profile.k9alzk15`, mesmo83/IP13.51checks offline
`checks.y3mlvyey`, incluindo36casos reais de paridade stat/SHA em container
rootless e recusa launch. Fontes originais MIT/manifestos40+7 fixados em C116;
um stat e um sha256sum por lote, mesmos donos/modos/tipos/links/ancestrais/hash,
headers preservados e sem cache persistente de confiança. Fonte/documentação
usam scripts shell (o termo “bytecode” no registro C118 refere-se aos bytes
desses scripts; nenhum bytecode ou ELF foi compilado).

12recibos nativos0, três rodadas de ordem alternada: host original mediana2990ms
(2980/3010/2990), lote1130ms (1150/1120/1130), redução62,2% do check completo;
provider original600ms e lote560ms, ganho pequeno. Host já inclui provider.
Relógio uptime centesimal/caches aquecidos/frequência não controlada. NÃO é ganho
de abertura real medido. **Launcher/caller instalados continuam no caminho antigo.**
Dois protótipos shell enviados somente à RAM (19836+2406bytes), modos700/hashes
conferidos antes/depois; zero upload de ROM/ELFs/assets e openROMlocal proibido.
Originais/11assets/10scripts/metadados intactos, run.once ausente; infra/mountinfo
byte-idênticos, RAM removida, raizRO0755/PCMclosed/UIoff/p1p3off. Sem save/reboot/
imagem/instalação/Deck/original32. Prova **`dist/phase4/batch-validation`** congelada.
C118 qualifica somente check; aprovação gráfica/física C116 permanece separada.

**C117 APROVADO sem intervenção física:** [perfil da abertura](phase4-launch-profile.md),
`launch-profile/profile.8ov5rk96`, boot83 confirmado novamente.17checks offline
`checks.7hihu0kr` e11recibos nativos0. Preparo residente, scripts originais em
check e três repetições: host40+provider7 mediana3000ms (2990/3000/3000),
provider isolado610ms (610/610/610), hashes core/ROM+cópiaRAM160ms (160/160/150).
Host já inclui provider: não somar as duas linhas. Medição por uptime centesimal,
cache aquecido/overhead incluído, sem controle de frequência; NÃO é abertura
gráfica perfilada nem ganho comprovado. Leitura das fontes aponta duas passagens
completas no caminho check→launch; otimizar o custo preservando os checks.

Zero uploads de inputs/openROMlocal proibido;11assets/10scripts/metadados
conferidos antes/depois, run.once ausente. Sem UI/core/input/áudio/reboot ou
escrita persistente; infra/mountinfo idênticos, RAM removida, raizRO/p3off/
PCMclosed/UIoff. Prova congelada **`dist/phase4/launch-profile`** sem privados.
Não amplia nem repete a aprovação gráfica/física C116. Nesta etapa o usuário
não precisou interagir; conferência física fica para marcos que afetem painel,
alto-falante, botões, energia/suspend ou recuperação/troca de cartão.

21checks offline `resident-boot-session/checks.0u1yo3at` passaram; observação
`observe.a8wgi4yu` confirmou191hashes/identidade/readiness/infra no83. Rodada
`load.i2yt7sk0` preparou11assets+ROM internos sem uploads, validou ABI e abriu
o primeiro menu com cmdline do worker e mapas conferidos. **A seleção A não
foi registrada: `C46_CANCELLED kind=timeout`; jogo não abriu nessa tentativa.**
Preservar esse resultado negativo separado da repetição aprovada abaixo.
**Fechamento conferido:** `closed-timeout.json`, cleanup0/PCMclosed/UIoff,
RAM removida, raizRO/p1p3off, infraestrutura e montagens preservadas; tela final
de diagnóstico escrita. Todos os recibos de pós-voo/cleanup0, fontes intactas.
Resultado gráfico falso preservado (`analysis.json`): não publicar como sucesso.
**C116 APROVADO:** usuário pediu repetição sem ampliar prazos; rodada
`load.0tjkp099`, mesma observação83, passou operação0/cleanup0/1051frames.
Imagem/direcional/som/Fn+L2/Fn+Start/retorno confirmados. EstadoC63 byte-idêntico,
nenhum save novo.11assets+10scripts+ROM internos, zero uploads e leitura da
ROMlocal proibida. Três mapas reais e cmdline do worker instalado conferidos.
Análise técnica/física/fechamento vinculados à mesma sessão; prova sanitizada
**`dist/phase4/resident-boot-session`** publicada, fontes congeladas.
RaizRO0755/PCMclosed/UIoff/p1p3off/taint0, RAM removida, hardware55/70 e
infra/mountinfo preservados; tela final diagnóstica escrita. SDK/imagem C64 intactos.

**Demora na abertura:** usuário confirmou funcionamento e relatou demora.
Observador mediu seleção consumida→primeiro frame7,37s (amostragem nominal1s,
atraso não limitado, sem timestamp físicoA); startup interno1338,99ms e carga
do conteúdo27,95ms. Não inferir causa ou ganho sobre C109.59,9401Hz recentes,
frame médio16,6995ms; áudio reportou4underruns/1556frames ausentes, sem distorção
relatada. Não equivale a estabilidade longa nem áudio sem underruns.

**Histórico de observação C112–C115:** observado82/UUID real/identidade4 estável, guardas178 preservados,
sem editar/reutilizar UUID81 ou pedir reboot. C112 `observe.xx0kthce`; C115
`observe.npmqzojq` já confere191hashes com o pacote instalado. Se houver outro
boot/IP, reconstruir o contexto novo antes da sessão; não reimportar/reinstalar
nem relaxar vínculos por rotina. Inserção tardia do dongle continua adiada.

**C112 assets residentes:** [registro](phase4-resident-assets.md), pacote
`resident-assets/package.2p14ff4n`,13arquivos/1.871.877bytes em
`/usr/libexec/muos-resident`. Quatro ELFs públicos C109 exatos, scripts/licenças/
manifestos e novo helper MIT sync-path A35/fsync, compilado pelo SDK em container.
Frontend/provider/core não recompilados; nenhum arquivo anterior substituído.
52casos `checks.obt45s39` passaram, incluindo modo real755 dos helpers session,
0644 das bibliotecas,13folhas/rollback, ROM/aliases/modos/guardas e novo boot.
Instalação `install.0uvf0x6y` concluída: check/recusa ocupada/fechamento0,
fingerprint/infra/mountinfo preservados e RAM removida/raizRO. Prova congelada
`dist/phase4/resident-assets-installed`, sem ELFs/ROM/seed/UUID.
**Preservar install.0uvf0x6y/dispatch.claim; não repetir apply.**

**C113 ROM INTERNA:** [importação](phase4-internal-rom.md),
`internal-rom/import.tgknjpow`, latest-complete. Cópia legal fornecida64KiB em
**p3:`MUOS/port-roms-v1/gb/private.gb`**, arquivo0600, shelf/gb0700, registro e
marcador600. Não está no pacote raiz/Git/dist/imagem pública. Backup lógico
privado independente antes da escrita: `before.tar`,88.064bytes/43entradas;
hashes, tar, preferências55/70 e snapshotC109 completo conferidos no host.
Recuperações C82/C89 anteriores preservadas; não é backup de bloco do cartão.

21casos `internal-rom/checks.yolw4bqf` passaram. Escrita destaca UMA tentativa;
fsync arquivos/dirs→rename sem sobrescrita→fsync pai, recusa final/staging já
existentes. Falha retém o novo staging/final, sem rollback ou retry automático.
Nativo0, unmount/remountRO e verify separado aprovados; cinco inventários da
árvore anterior byte-idênticos. Infra/PID/starttime/mountinfo iguais, RAM removida,
p3 desmontada/raizRO. Sem format/repartição/p2rewrite/reboot/GUI. Prova congelada
`dist/phase4/internal-rom-imported`, sem ROM/backup/ELF/seed/UUID.
**Preservar import.tgknjpow/dispatch.claim e backup; não repetir apply/importação.**

**C114 automático sem UI:** [resultado](phase4-resident-preparation.md),
`resident-preparation/validate.5l2corol`, latest-complete. Zero uploads de inputs;
audit hook proíbe open da ROM local. Loader residente copia quatro assets,
lê ROMp3 RO/noload/nosuid/nodev/noexec num namespace privado, desmonta/remove
mountpoint e só então delega ao C111 no namespace GLOBAL original. C111 prepara
mais sete bibliotecas locais e stage C105 fornece dez scripts. São
**11assets RAM +10scripts**, todos hashes/modos/links conferidos; ROM/digest,
identidade, seis metadados/manifestos e boot/UUID do stage coincidem com C109/C113.
Run.once ausente: worker/jogo não iniciado. CLI host, quatro eager loads ABI,
--version/--help passaram. Todos os recibos0; rootRO/p3off/PCMclosed/UIoff,
infra/mountinfo iguais e RAM removida. Prova `dist/phase4/resident-preparation`.
Fontes C112/C113/C114 e provas congeladas; não editar para corrigir história.

**C115 implementação pronta:** [fluxo e instruções](phase4-resident-session.md),
16checks `resident-session/checks.v3fz80ec` aprovados sem rede/GUI/core e com
ROMlocal proibida. Adaptador em memória troca somente três admissões HOST-ROM
no histórico C63 por recibo nativo C113, mantendo todos os demais hashes/bindings.
Loop de upload executado em fixture com mapa vazio: zero leituras/envios de
assets/ROM. Scripts originais C105 e worker não alterados. Run/analyze/finish/
package próprios preparados, guardas191/mesmo boot82 e origem C113/C114 exigidos.
Observação nativa `observe.npmqzojq` aprovada; **nenhuma sessão gráfica executada**
e `dist/phase4/resident-session` NÃO existe. Não inventar confirmação física.

**Próximo incremento C122:** preparar componente residente versionado que
forneça o bundle C120 e adote a cápsula localmente, retirando os seis uploads
de código da preparação de cada sessão. Preservar o prefixo C105 e contratos
C112/C120/C121; novo prefixo/manifesto/receita com guardas e plano de instalação
aditiva no128 antes de qualquer escrita. Começar por testes offline de pacote,
modos/hash, recusa de repetição/parcial e boot atual; depois instalação guardada
e um ciclo pelo componente residente. Reutilizar worker/provider/load-only e
limites atuais; autostart/navegador geral/novos saves permanecem separados.
Preservar fontes/provas C112–C121, hashes/modos/ownership/ancestrais/RO/isolamento.
Reutilizar observação84 apenas
se contador/UUID/fontes/estado coincidirem; novo boot exige contexto fresco.
Não repetir C116/C121 aprovados sem razão concreta, nem instalação/importação/claims.

**Armazenamento/Git:** sem nova imagem integral ou clone de rootfs; C112–C115
geraram~16MiB e C116 somente fontes/recibos pequenos. Inventário mantém cinco
marcos de firmware. Trace C104–C121 protege backup/provas/pacotes e o fechamento
da tentativa expirada e prova nativa atual. Dry-run
`build/cleanup/retention-20261109T182539Z.json`:
1858arquivos protegidos/zero descartes, incluindo fechamento negativo e prova
aprovada. Não houve exclusão.
Não aplicar planos vazios/consumidos. ROM original local preservada fora do Git;
execução atual não a lê. Cinco checkpoints Git nomeados; C116 usa commit comum,
sem novo tag. C117 também somente fontes/recibos pequenos, sem imagem integral
ou novo checkpoint nomeado. Dry-run C117
`build/cleanup/retention-20261109T183806Z.json`:
1934arquivos protegidos, incluindo medições/prova C117, zero candidatos/zero
exclusões. Artefatos C117~1MiB no host; fontes versionadas no Git.
C118 também sem imagem integral/novo tag, artefatos~1,3MiB no host. Dry-run
`build/cleanup/retention-20261109T185425Z.json`:
2002arquivos protegidos, incluindo protótipos/recibos/prova C118, zero candidatos
e zero exclusões. Cinco versões de firmware e cinco checkpoints nomeados mantidos.
C119 gerou~3MiB de fontes/recibos/prova, sem imagem integral ou novo tag.
Dry-run `build/cleanup/retention-20261109T191749Z.json`:2169arquivos protegidos,
zero candidatos/zero exclusões. O trace inclui a prova atual e a primeira
rodada fechada com a cópia exata do publicador anterior; backup/claims intactos.
C120 acrescenta~1,6MiB, sem imagem integral ou tag. Dry-run anterior à
preparação C121 `build/cleanup/retention-20261109T193322Z.json`:2259arquivos
protegidos, zero candidatos/zero exclusões. O trace agora inclui também os
checks/contexto C121; inventário permanece com cinco firmwares/cinco tags.
Dry-run final `build/cleanup/retention-20261109T193912Z.json`:2276arquivos
protegidos, zero candidatos/zero exclusões, incluindo observação e ferramentas
de resultados C121. C121 acrescenta~188KiB; não foi criada imagem de firmware.
Qualificação gráfica C121 acrescentou~2MiB de recibos/prova. Dry-run
`build/cleanup/retention-20261109T235750Z.json`:2416arquivos protegidos,
zero candidatos/zero exclusões, incluindo coleta, observação84, fechamento,
prova gráfica e recusa de publicação prematura. Cinco firmwares/cinco tags
mantidos; nenhuma imagem nova ou alteração no Deck/original32.
Não tocar Deck/original32, investigar dongle, rearmar.once/C94/claims ou regravar
candidata77/fábrica C100 sem provisão. Autostart/navegador geral/SRAM/novos saves/
Power/suspend/boot frio/queda de energia/longa duração continuam separados.

## Marco anterior — C107–C111 concluídos; C109 com preparo local APROVADO

**07/11/2026:** R35S **192.168.15.8:2222**, mesmo **boot81**, C07 pronto/
raiz ext4RO0755. Cartão de teste128GB no console, original32 guardado; Deck
fora do fluxo. UI/jogo encerrados, PCMclosed/p1p3off/taint0; página diagnóstica
final escrita. Nenhum reboot nesta rodada. Dongle com inserção tardia continua
adiado pelo usuário. Incrementos agrupados antes de **um único teste físico**.

**Preparador local:** [C107/C108](phase4-local-preparation.md),
[C110 modos reais](phase4-local-preparation-v2.md) e
[C111 callback final](phase4-local-preparation-v3.md). Três prefixos próprios
`/usr/libexec/muos-capsule`, `muos-capsule-v2`, `muos-capsule-v3`, seis arquivos
cada; total31.689bytes, nenhuma substituição de arquivos anteriores. C105
inalterado, sem imagem integral nova/autostart/serviço/token. Provas sanitizadas
`capsule-preparer-installed`, `capsule-preparer-v2-installed`,
`capsule-preparer-v3-installed` congeladas em dist/phase4.

**Correções e limites históricos:** C109 inicial `load.pjofljbw` recusou modo
esperado0755 antes do stage: bibliotecas reais são0644. Cinco inputs foram
conferidos e removidos, recibo refusal-cleanup0, sem UI/jogo. C110 corrige os
modos; revisão antes da UI encontrou callback final sem caller_exec capsule,
necessário para c105_staged. C111 acrescenta findmnt/tmpfs nesse dispatch.
C108/C110 passaram somente instalação/check/recusa vazia, **sem aprovação de
preparo positivo/gráfico**. Não reescrever fontes/provas para corrigir história.

**C111:** pacote `capsule-prepare-v3/package.22ef4ve8`,10.602bytes; checks
`checks.21y_q3b5`:44casos, incluindo modo0644 e callback extraído da entrada
real com funções C105/tmpfs reais em container (boot/caminhos de fixture).
Instalação `install.enw93t77`, guardas172; todos os recibos0, fingerprint/
infra/mountinfo preservados, RAM removida/raizRO. C108 instalação
`capsule-prepare/install.0ebv0j0g`, C110 `capsule-prepare-v2/install.pfsk2m5s`.
**Preservar dispatch.claim nos três stages; não repetir apply.** Claims C105
install.322dqnrs e recovered-reboot também permanecem consumidos.

**C109 aprovado:** [sessão e métricas](phase4-prepared-capsule-session.md),
`prepared-capsule-session/load.ky2c382i`, latest-load; observação
`observe.w28rjklk`,22checks em `checks.ebuwz4o8`. Guarda178 e identidade real
core/ROM igual ao snapshot C63, fontes/provas históricas preservadas.
`prepare.sh prepare` C111 copia sete bibliotecas locais, stage C105 fornece
dez scripts e o aparelho gera identidade/metadados/manifestos. Host envia
**5inputs em vez de12uploads**: quatro assets públicos+ROM privada somenteRAM.
Sem montar/gravar p3 para persistir ROM. Check do host e ABI4 nativos0;
caller.sh run e worker instalado confirmados por run.once/PID/starttime/cmdline,
três mapas e preparation.once/ready. Jogo45s/worker210s/supervisor240s mantidos.

**Físico e fechamento:** usuário “Tudo certo” para imagem/direcional/som,
Fn+L2 e Fn+Start/retorno.1284frames, hotkey0/expired0; snapshot/metadados e
inventários byte-idênticos ao C63,2status/1export, nenhum QuickSave. Native/
OPERATION/CLEANUP/postflight/mount-health/caller-execution/cleanup/stopped-screen0.
Mixer/DRM/volume/brilho/WirePlumber/preferências55/70 restaurados; PID/starttime
infra e mountinfo global iguais, RAM removida. Fechamento offline autêntico
preservou imagem C64 e SDK. Prova `dist/phase4/prepared-capsule-session`.

**Medição:** seleção consumida→primeiro frame observado8,42s, polling nominal1s;
startup interno1373,11ms. Não mede instante físico de A, não limita atraso do
scheduler ou demonstra causa/comparação com C106. C44_FIRST_PRESENT seconds=45
é limite do jogo, não latência. Analisador C77 intacto:59,9401Hz recente,
4underruns/1546frames de áudio ausentes agregados; não localizam eventos nem
qualificam longa duração. Som limpo/audível confirmado fisicamente.

**Armazenamento/Git:** nenhuma nova imagem integral; artefatos desta rodada
~6MiB. Cinco marcos de firmware continuam no inventário, fonte/docs no Git
local, até5checkpoints nomeados. Trace C104–C111 passou; dry-run
`build/cleanup/retention-20261107T170957Z.json`: zero novos descartes, sem nova
liberação de bytes. Limpeza anterior~12,3GiB permanece; build/phase4~17GiB.
SDKs/backups/refs/provas/ROM preservados. Não aplicar planos vazios/consumidos.

**Próximo lote:** preparar residência dos quatro assets públicos remanescentes
(runner/state-metadata/libmuxmod diagnóstico/probe ABI), com origem/hashes/
licenças; instalação aditiva e integração antes do próximo teste físico. Meta:
apenas ROM como input, sem supor armazenamento privado em p3. Pode usar81 se
estado real/hashes atuais ainda passarem. Se houve novo boot, criar observador/
vínculo novo sem reutilizar UUID81 nem rearmar claims; não repetir C109/C105/
C104 por rotina. Autostart/navegador geral/SRAM/novos saves/Power/suspend/boot
frio/queda de energia/longa duração separados. Não tocar Deck, rearmar.once/
C94 ou regravar candidata77 consumida/fábrica C100 sem provisão. C99 não serve
após C102; C98 segue rascunho.

## Marco anterior — C106 sessão pelo caller instalado APROVADA; cartão no R35S

**07/11/2026:** [C106](phase4-installed-caller-session.md) concluído no
**boot81**, IP **192.168.15.8:2222**, C07 pronto/raiz ext4RO0755. Cartão de
teste128GB no R35S, original32 guardado; Steam Deck fora do fluxo. Nenhum
launcher/jogo aberto. **Cenário de inserção tardia do dongle adiado pelo usuário**;
não investigar/testar esse caso neste foco. Não houve reboot neste incremento.

**C106:** `build/phase4/installed-caller-session/load.mdsjxv2d`, latest-load;
observação `observe.c7dg6jhs`, checks `checks.0rskku83` com17casos novos.
Reutiliza43casos C105 e4grupos de vínculo por integridade. Guardas160hashes
(143fundação/layout+17caller), metadados, identidade4 e c25_ready integral.
Fontes/provas C77/C104/C105 intactas; usa o mesmo boot/UUID C105 observado.

**Integração real aprovada:** dez scripts não são enviados pelo host;
`/usr/libexec/muos-caller/caller.sh stage` os prepara em RAM e `run observe`
abre o worker instalado, com supervisor/namespace original. Marker run.once,
PID/starttime/cmdline do worker e três mapas menu→GB→menu comprovam esse
caminho. Assets/metadados/ROM privada ainda são preparados pelo harness:
não é navegador geral ou sessão inteiramente autônoma. Nenhum novo arquivo
persistente, autostart, imagem completa, serviço ou token instalado.

**Confirmação física:** usuário confirmou imagem/input/som/restauração Fn+L2/
saída Fn+Start/retorno. Informou abertura da ROM um pouco mais lenta;
registrado como percepção, sem medição ou causa demonstrada. Não repetir
o teste por isso sem plano concreto.1255frames, hotkey0/expired0; snapshot
e metadados idênticos ao C63,2status/1export, nenhum QuickSave. Jogo45s,
worker210s/supervisor240s preservados; prazo SSH300s inclui guardas prévias.

**Fechamento:** native/OPERATION/CLEANUP/postflight/mount-health/
caller-execution/cleanup/stopped-screen0. RaizRO0755/PCMclosed/p1p3off/UIoff/
taint0; mixer/DRM/volume/brilho/WirePlumber/preferências55/70 restaurados.
Infraestrutura PID/starttime e mountinfo global iguais; RAM removida e página
final diagnóstica C77 escrita. Analisador C77 congelado:59,9401Hz recente,
5underruns/1940frames de áudio ausentes agregados; sem inferência de momento
ou desempenho sustentado. Fechamento offline por recibos autênticos, imagem
C64/SDK preservados. Prova `dist/phase4/installed-caller-session`, sanitizada.

**Limpeza adicional:**1381 arquivos antigos,539.611.136bytes (**515MiB**)
físicos recuperados. Plano consumido
`build/cleanup/retention-20261107T162254Z.json.gz`;1484arquivos protegidos e
cadeia C104/C105/C106 reconferidos;9testes do limpador passaram. Foram
descartadas raízes/payloads sintéticos C72,fixtures32MiB C88 aprovados e
pacotes core-staging temporários antigos. Relatórios/scripts de reprodução,
SDKs/backups/refs/dist/ROM preservados. build/phase4 agora~17GiB, SSD~43GiB
livres; total desta rodada e anterior~12,3GiB físicos liberados. Resumo
`build/cleanup/retention-summary.json`. Cinco marcos de firmware e Git local
continuam vigentes; não gerar/copiar uma imagem inteira por edição.

**Próximo C107:** preparar os assets/cápsula no aparelho, reduzindo dependência
do harness. Planejar origem da ROM e acesso ao volume de dados antes de
alterar C105; sem mover ROM ou montar/gravar p3 por suposição. Pode reutilizar
boot81 depois de verificar estado real e integridade C105/C106. Não repetir
C106/C105/rebootC104, nem tocar no Deck por rotina. Manter claims consumidos
`manual-caller/recovered-reboot.claim` e `install.322dqnrs/dispatch.claim`.
Autostart/navegador geral/SRAM/novos saves/Power/suspend/boot frio/queda de
energia/longa duração separados. Não rearmar.once/C94 ou regravar candidata77
consumida/fábrica C100 sem provisão. C99 não serve após C102; C98 segue rascunho.

## Marco anterior — C105 caller manual instalado; cartão no R35S

**07/11/2026:** limpeza de builds e [C105](phase4-manual-caller.md) concluídos.
Console **192.168.15.8:2222**, C07/**boot81**, raiz ext4 RO0755. Cartão de teste
128GB no R35S; original32 guardado. Steam Deck segue limpo e fora do fluxo.
Nenhum launcher/jogo está aberto.

**Armazenamento:** removidos404.812 arquivos históricos, **11,8GiB físicos
recuperados**; build/phase4 caiu41→18GiB em du, espaço livre30→42GiB.
Planos consumidos `build/cleanup/retention-20261107T155500Z.json.gz` e
`retention-20261107T160455Z.json.gz`: hashes/metadados de1.391 arquivos protegidos
e cadeia offline reconferidos;9testes de segurança passaram. SDKs, downloads,
refs, dist, ROM e backups privados preservados. Não reutilizar os planos.
Código/docs agora no Git local com autor fornecido; baseline `ce01966` inclui
C104 aprovado e rascunho C105 interrompido. Builds por componente, sem rootfs
completa por edição. Política `port/packaging/storage-retention.json`: cinco
marcos C64/C79/C89/C93/C100, sete arquivos de imagem nesses marcos, exceções
concretas de recuperação/SDK/provas. Não são imagens prontas para regravar.
Histórico Git compacto é exceção de auditoria; até5 checkpoints nomeados.
Ver [retenção](storage-retention.md) e as regras novas em AGENTS.md.

**C105:** `build/phase4/manual-caller/install.322dqnrs`, latest-complete;
pacote `package.er1m0bnf`, **17arquivos0644/1diretório0755/60.276bytes** em
`/usr/libexec/muos-caller`, sem substituições. Dez scripts MIT byte-idênticos
ao C104. Entrada via sh: check, stage de cápsula tmpfs própria e run
observe/load-only.142dependências públicas/10assets fixados; nenhuma
ROM/ELF/identidade/seed. Preparo dos assets ainda pertence ao harness.
Checks `checks.hpybluli`:43casos caller/transação +4grupos de vínculo com
12variantes negativas. Guarda nova conserva inventário e c25_ready integral;
sh-n passou. Fixture não executa core/ROM/namespace. Adaptador derivado C76,
rollback só de folhas próprias e diretório vazio; preserva vizinhos.

**Boot80→81:** entrada80 falhou em usb-mode após inserir dongle durante o
boot; reinserção física recuperou SSH sem reclassificar C07. Pedido normal
único com guarda de recuperação e intent/claim fsync:
`reboot-recovered.zrm_92lu`; **NÃO remover `recovered-reboot.claim` nem repetir**.
Observação `observe.70yc6fne` qualificou81 por c25_ready, contador/UUID novos,
141arquivos/metadados/layout C102/identidade4. Usuário confirmou conexão.
Não reescreveu UUID antigo ou alterou C10478→79; observador não leu seeds.
Inserção tardia do dongle segue cenário pendente, separado do warm reboot
aprovado com dongle presente desde o início. Não repetir investigação por rotina.

**Fechamento nativo aprovado:** apply0;17folhas/hash/modos, check142dependências,
stage RAM dos10scripts, recusa de stage repetido/run incompleto. Fingerprint
privado, infraestrutura PID/starttime e mountinfo global iguais; raizRO/layout
preservados, duas cápsulas removidas, recibos esperados0. **NÃO remover
install.322dqnrs/dispatch.claim nem repetir apply.** Nenhuma UI/core/ROM/save/
token/serviço/autostart executado pela instalação. Prova sanitizada
`dist/phase4/manual-caller-installed`: payload público, adaptadores, fontes e
resultados; sem guardas privados/ROM/ELF/seed/UUID.

**Próximo C106:** qualificar menu→GB→menu pelo entrypoint instalado C105,
assets/cápsula em RAM, worker original e restauração do snapshot existente.
Sessão gráfica por esse entrypoint ainda NÃO aprovada. Pode usar81 após
verificar estado real/integridade C105 e vínculo atual, sem relaxar c25_ready.
Não exige Deck, migração ou nova imagem; não repetir C104 ou C105. Navegador
geral/autostart/Power/SRAM/novos saves/boot frio/queda de energia/longa duração
seguem separados. C99 exige ausência dos caminhos e não serve após C102.
Não reativar.once/C94/candidata77 consumida nem regravar fábrica C100 sem
provisão como atualização. C98 duas passagens segue rascunho não testado.

## Marco anterior — C104 fluxo após reboot APROVADO; cartão no R35S

**05/11/2026:** [C104](phase4-reboot-layout-session.md) concluído em
`build/phase4/reboot-layout-session/load.f412eeby`, latest-load; observação
`observe.itryybk_`. Console 192.168.15.8:2222, C07/boot **79**, UUID novo.
Cartão de teste de 128 GB no R35S; original de 32 GB guardado. Steam Deck
limpo manualmente pelo usuário e fora do fluxo, sem novo acesso/chave.

**Reboot normal78→79 aprovado:** `reboot.zsd5kwj4`, latest-reboot-request,
pedido único por /sbin/reboot normal/PID1 após guardas e sync. Claim/intent
fsync antes da chamada, sem força/sysrq/token.once. `reboot-request.claim`
permanece e NÃO deve ser removido para repetir. Retorno C07 pronto no mesmo
IP; observação completa confirmou contador79, UUID diferente, quatro arquivos
estáveis de rede/chave e o layout C102. Não leu seeds no observador nem repetiu
entropia C97; o bootstrap C07 executou seu ciclo normal de contador/RNG.

**Implementação nova:** `phase4_reboot_layout_session.py`, runner/fechamento/
checks/publicador e `reboot-phase4-native-layout.py`. Fontes/provas antigas
C77/C97/C102/C103 intactas. Guarda regenerada para79 com141arquivos/metadados,
template, asound.conf0644/444bytes/link único e /mnt/mmc0755 vazio, além de
identidade4; não troca o UUID antigo por texto nem relaxa o módulo C103.
Worker original app-selection/C77 sem helper/visões de diretórios C99.

**22 testes novos passaram:** `reboot-layout-session/checks.9g4vok9a`.
Transição de boot/UUID, contador igual/antigo/pulado/booleano/string/fora de
limite, observação sem vínculo C103 ou com hash errado, guarda/layout/
identidade sem seed e pedido normal. 26 testes C103/47 C77 reutilizados por
integridade, sem reexecução. Nenhum core/ROM/reboot/SSH nesses checks.

**Sessão física e técnica aprovadas:** usuário “Tudo certo” para imagem,
direcional, som limpo/audível, restauração Fn+L2 e retorno Fn+Start. Somente
A/Start/direcional/hotkeys permitidos, sem salvar/Power/volume/brilho.
1084 frames, hotkey0/expired0; três mapas menu C46 → host/provider4/core
instalados → menu. Snapshot/metadados iguais ao C63; duas chamadas status e
uma exportação, nenhum QuickSave. Preferências55/70/mixer/brilho/volume/DRM/
WirePlumber restaurados. CSV recente59,9401Hz,4underruns/1855frames ausentes:
agregados sem localização temporal ou alegação de desempenho sustentado.

**Fechamento aprovado:** native0/OPERATION0/CLEANUP0/postflight0/mount-health0/
cleanup0/stopped-screen0. Layout C102 preservado, raizRO0755, PCMclosed,
p1/p3 desmontadas, UIoff/taint0. Infraestrutura PID/starttime e mountinfo global
iguais dentro do boot79; cápsula removida e página final diagnóstica C77
herdada escrita. Nenhum jogo/menu continua rodando. Confirmação física e
análise técnica vinculadas à mesma análise nativa; fechamento confere recibos
autênticos, imagem ancestral e SDK preservados, sem simular nova conexão.
Prova sanitizada `dist/phase4/reboot-layout-session`, sem imagem/ELF/ROM/estado/
UUID/identidade privada/seed/chaves. Recibo do pedido mantém return_verified=false
do instante do despacho; observação/rodada79 posteriores comprovam o retorno.

**Próximo incremento:** preparar caller como componente instalado de execução
manual, com plano/testes próprios antes de instalar; autostart e navegador
geral separados. Não exige Deck, outra migração ou repetição deste reboot.
C103 exige boot78; C104 é vinculado à transição78→79. Se o usuário reiniciar,
observar contador/UUID reais e criar novo contexto, sem fingir continuidade.
C99 exige ausência dos caminhos e não deve ser repetido após C102. Não
reativar.once/C94/candidata77 consumida nem gravar fábrica C100 sem provisão
como atualização. Boot frio/queda de energia/SRAM/novos saves/suspend/longa
duração ainda pendentes. C98 duas passagens segue rascunho não testado.

## Marco anterior — C103 fluxo com layout instalado APROVADO; cartão no R35S

**05/11/2026:** [C103](phase4-native-layout-session.md) concluído em
`build/phase4/native-layout-session/load.dfmnvdli`, latest-load. Observação
`observe.iv1f5nxf`; console 192.168.15.8:2222, mesmo C07/boot 78. Cartão de
teste de 128 GB permanece no R35S; original de 32 GB guardado. Deck limpo
manualmente pelo usuário, fora do fluxo e não acessado; não reinstalar chave.

**Implementação:** `phase4_native_layout_session.py`, runner/fechamento/checks
e publicador próprios. Reutiliza runner C77 congelado com contexto vinculado
à instalação C102 e ao boot/UUID C97, em namespace de evidências novo.
Worker original `app-selection/worker.sh` byte-idêntico: NÃO transfere
etc-view.sh nem usa o worker C99. Mantém isolamento por arquivo, inclusive
bind de cópia RAM de asound.conf e verificação de seu hash original ao fim;
não copia/binda as árvores inteiras /etc ou /mnt. Usa /mnt/mmc instalado.
Nenhuma nova instalação, migração, seed/counter, save, token.once ou reboot.

**26 casos novos passaram:** `native-layout-session/checks.d564ang1`,
latest-checks. Vínculos C102/C97, flags/delta/layout/boot/UUID incorretos,
observação sem vínculo e uso do worker original. Os 47 casos aprovados C77
foram reutilizados por integridade de fontes/relatório, sem reexecução.
Sem core/ROM ou acesso físico nesses checks; não repetiu C97/C99 aprovados.

**Sessão nativa e física aprovadas:** usuário respondeu “Tudo certo” a imagem,
direcional, som limpo/audível, restauração Fn+L2 e retorno Fn+Start. A/Start
e direcional permitidos; sem salvar/Power/volume/brilho. 1160 frames,
hotkey0/expired0; três mapas confirmam menu C46 → host/provider4/core instalados
→ menu. Snapshot/metadados idênticos ao C63, duas chamadas status/uma export,
nenhum QuickSave. Preferências 55/70, mixer, DRM, brilho, volume e WirePlumber
restaurados. CSV recente 59,9401 Hz, três underruns/1224 frames ausentes:
agregados sem localização temporal ou alegação de desempenho sustentado.

**Limpeza e fechamento aprovados:** native0/OPERATION0/CLEANUP0, postflight0,
mount-health0, cleanup0, stopped-screen0. Layout C102 preservado, rootRO0755,
PCMclosed/p1p3off/UIoff/taint0, infraestrutura PID/starttime e mountinfo global
idênticos; cápsula removida e página final diagnóstica C77 herdada escrita.
Nada gráfico continua rodando. Confirmação física vinculada ao hash da análise;
analisador C77 congelado e fechamento de recibos autênticos passaram.
Prova sanitizada `dist/phase4/native-layout-session`, sem imagem/ELF/ROM/estado/
seed/chaves, identidade ou UUID reais. Fontes/provas/ponteiros C77/C99/C100/C102
históricos preservados. C102 e seus 35 testes não foram repetidos.

**Próximo incremento:** qualificar o fluxo com layout instalado após um novo
boot explicitamente observado. O módulo C103 exige exatamente o boot/UUID 78;
se houver reboot externo, criar vínculo próprio ao contador/UUID reais, sem
fingir continuidade nem reexecutar qualificação de entropia C97. Novo boot não
exige Deck ou migração. C99 antigo exige caminhos AUSENTES e não deve ser
repetido após C102. Nunca rearmar.once/C94/candidata77 já consumida ou gravar
fábrica C100 sem provisionamento como atualização. Frontend permanente/
autostart, navegador geral de ROMs, SRAM/novos saves, suspend/energia e longa
duração permanecem separados. C98 duas passagens ainda é rascunho não testado.

## Marco anterior — C102 layout instalado APROVADO; cartão no R35S

**05/11/2026:** [C102](phase4-c79-layout-install.md) concluído em
`build/phase4/c79-layout-install/install.s5gn_jxj`, latest-complete. Console
acessível192.168.15.8:2222, mesmo C07/boot78 qualificado por C97. Cartão de
teste128 nele; original32 guardado. Deck limpo manualmente conforme usuário,
fora do fluxo e não acessado nesta etapa; não reinstalar chave SSH.

**Delta C100 instalado:** /etc/asound.conf444bytes do template público já
presente, root:root0644/link único; /mnt/mmc root:root0755/links2 vazio.
/mnt links2→3. Sem substituir arquivos, gravar imagem completa, mexer em p3,
seed/counter/snapshot/ROM/preferências, habilitar serviço/token.once/autostart
ou reiniciar. Timestamps dos pais mudam; não são alegados invariantes.
Fábrica C100 continua sem provisionamento; NÃO gravá-la diretamente como
atualização. C94 continua pinado à C79 original; candidata77 já consumida.

**Implementação nova:** `run-phase4-c79-layout-install.py`,
`check-phase4-c79-layout-install.py`, fixture e
`port/device/rk-r35s-p0/c79-layout-install/{transaction,native}.sh`.
Plano de ausência/payload/manifesto fsync no host antes da escrita, vínculo ao
boot/UUID real C97, guardas141arquivos/metadados mais template, cartão/modelo/
kernel, lock de sessão, publicação exclusiva e retornoRO. Recuperação só
remove entradas da própria tentativa ainda íntegras; bytes parciais/aliases/
links extras/vizinhos permanecem para auditoria. Perda de energia/SIGKILL não
é recuperação automática qualificada; inspecionar sem repetir aplicação.

**35casos novos passaram:** `c79-layout-install/checks.7c3x0jfo`, latest-checks.
Container isolado sem rede/capabilities/dispositivos; árvores descartáveis,
remounts/guardas físicas substituídos por callbacks. Testes de destinos/pais/
template/fundação, falhas nos passos de escrita/sync/RO e retenção de conteúdo
desconhecido. Não repetiu investigações/testes físicos C97/C99 aprovados.

**Nativo aprovado:** inspect0/aplicação0/pós-checks0; raizRO0755,141arquivos
protegidos e template intactos, fingerprint de rede/seed/SSH/diagnóstico/
preferências idêntico, infraestrutura PID/starttime e mountinfo global iguais.
PCMclosed/p1p3off/UIoff; cápsula/run removida, nova conferência de saúde passou.
A primeira espera expirou enquanto hashes ainda rodavam, com raizRO. `collect`
retomou a MESMA tentativa; nenhum segundo despacho ou retry de instalação.
Recibos privados e claim em install.s5gn_jxj. Publicação sanitizada
`dist/phase4/c79-layout-installed`, sem UUID/fingerprint/guardas privadas ou
payload de imagem/ROM/estado/seed/chaves. Fontes/provas C77/C99/C100 preservadas.

**Próximo incremento:** preparar caller com os caminhos instalados, reutilizando
o worker original C77 sem o contorno RAM C99. C99 atual exige AUSÊNCIA dos dois
caminhos e NÃO deve ser repetido como está. Não precisa Deck nem nova migração.
Qualificar em sessão própria menu→GB→menu/restore/saída, sem novo save; não
reativar.once, C94, candidata77 ou teste de entropia C97. Caso o usuário tenha
reiniciado, verificar contador/UUID real e preparar vínculo explícito do novo
boot, sem fingir que continua78. Novo boot deste layout/autostart/navegador
geral de ROMs/SRAM/longa duração/energia seguem separados. C98 duas passagens
continua rascunho não testado, sem adaptador físico.

## Marco anterior — C100 layout offline APROVADO; Deck limpo pelo usuário

**05/11/2026:** usuário confirmou “Terminei e deu tudo certo” após instruções
de limpeza manual do Steam Deck e remoção apenas da chave da tarefa.
Registro local `build/phase4/deck-cleanup-current/manual-completion.json`;
[limites do registro](phase4-deck-cleanup-current.md). Não houve auditoria SSH
posterior nem aprovação nativa do helper C101, que falhou e não foi repetido.
Não reinstalar chave nem usar o Deck para esta etapa. Os12artefatos do backup,
fence C94 e provas C97/C99 locais haviam sido reconferidos antes da limpeza.

**C100 APROVADO offline:** [layout mínimo](phase4-c79-layout.md).
`phase4_c79_layout.py`/entrypoint/host builder/publicador geram uma fábrica
derivada em arquivo regular512MiB, com duas adições: /etc/asound.conf444bytes
root0644 (template público já presente) e /mnt/mmc root0755 vazio. Só /mnt
ganha um link adicional entre os metadados existentes do inventário.
Releitura completa3406entradas, fsck0 e UUID/features/geometria preservados;
fonte C79 byte-idêntica. Não provisiona seed/chave/rede/ROM/estado nem muda
contador0/defaults/autostart. Timestamps não são alegados invariantes.

**29casos novos passaram:** `build/phase4/c79-layout/checks.b8l3vm4g`,
latest-checks. Ext4 reais32MiB em container sem rede/dispositivos/capabilities;
guardas de template/aliases/links/modos/owner, mudanças públicas indevidas,
cópia interrompida/fsync/FS danificado e caminhos fora de /work. A primeira
rodada passou na fixture mas recusou limpeza de um alias sintético; corrigido
apenas o harness e o conjunto completo passou. Imagens sintéticas descartadas
após logs, sem repetir testes aprovados C77/C99 ou acessar hardware.

**Composição real completa:** `c79-layout/compose.1yrez0md`, latest-complete.
`compose.claim` persistido: não repetir composição após interrupção sem inspecionar.
Fonte reutilizada `initial-image/provision.evbj4tey/factory.ext4`, pinada à
fábrica pública C79, NÃO a candidata provisionada77 já consumida no boot78.
Saída privada `output/factory.ext4` ocupa~159MiB físicos, sem raw640/gzip extra.
Host conferiu hash/tamanho/metadados/delta completo e preservação da fonte.
Prova sanitizada `dist/phase4/c79-layout` congelada,14arquivos/3provas ancestrais
conferidos por hash, fontes dos checks atuais iguais. Sem imagem/ELF/ROM/estado/
identidade real. Imagens sintéticas, inclusive parciais, descartadas após logs.

**Console não acessado nesta etapa:** último estado confirmado R35S192.168.15.8,
C07/boot78 após C99 aprovado; cartão128 permanece nele conforme usuário.
Original32 guardado. Não repetir C94/compose77/seeds, C97 ou C99 aprovados.
Nenhuma instalação, reboot, token.once ou teste físico novo foi solicitado.

**Próximo incremento:** preparar instalador aditivo finito de444bytes e um
diretório para o console, com plano/ausência/recuperação e raizRO no fim, sem
regravar512MiB nem alterar seed/counter/snapshot. Só depois qualificar o caller
com layout instalado, substituindo o contorno RAM C99 que exige ausência dos
dois caminhos. A fábrica C100 é SEM provisionamento e não pode ser gravada
diretamente como atualização de test128; writer C94 permanece pinado à C79 antiga.
Deck não é necessário para preparar esse delta. SRAM/novos saves, navegador
geral de ROMs, frontend permanente/autostart, longa duração e energia separados.
C98 duas passagens continua rascunho não testado, sem adaptador físico.

## Marco anterior — C99 fluxo instalado C79 aprovado; cartão no R35S

**Limpeza do Deck CONFIRMADA pelo usuário,05/11/2026:** usuário pediu remover todos arquivos
do projeto caso leitor não seja necessário. Próximo incremento de layout pode
ser preparado neste host, sem Deck. Foram reconferidos12artefatos do backup
local, fence C94 e provas C97/C99 (`deck-cleanup-current/host-retention.json`).
Inventário SSH encontrou42diretórios em /home/deck e /var/tmp, leitor vazio,
sem sudo sem senha e regra temporária C83 ainda instalada. Limpador C101 passou
14casos e foi transferido para `/home/deck/muos-r35s-c101-cleanup-cfe09c125a37`.
Usuário informou FAILED e preferiu receber somente os diretórios para apagar
manualmente; não repetir o helper nem presumir limpeza completa. Falha não
investigada por preferência do usuário. Plano/inspeção em
`build/phase4/deck-cleanup-current` e latest-package; possível claim temporário
`/run/muos-r35s-c101-cleanup.claim` deve entrar na limpeza manual. Prefixos
restritos a /home/deck/muos-r35s-c*, /var/tmp/muos-r35s-c*, /tmp/muos-r35s-c* e
/run/muos-r35s-c*. Também remover somente a regra C83 em
/run/udev/rules.d/99-holo-automount.rules e eventual recibo
/home/deck/.muos-r35s-c101-cleanup-result.json. Remover apenas a chave da tarefa
em authorized_keys, preservando outras entradas e serviço SSH. Não alegar
limpeza/key removal concluídos sem confirmação. **A confirmação chegou nesta
retomada: usuário executou os comandos manuais e informou “Terminei e deu tudo
certo”.** Limpeza manual e remoção da chave da tarefa registradas conforme esse
relato, sem nova conexão SSH ao Deck. Não repetir o helper C101 nem pedir
reinstalação da chave para auditar limpeza já confirmada. Backups/fence locais
permanecem; Deck fica fora do fluxo até uma futura necessidade de leitor.
C100 está sendo implementado offline neste host; C99/console preservados.

**05/11/2026:** usuário autorizou continuar e confirmou presença para teste.
test128 permanece no R35S192.168.15.8/C07/boot78; original32 guardado.
Migração C94 (`p2-initial/copy.cba4yn92`, prova p2-initial-native) e primeiro
boot C97 (`initial-boot/collect.kz1a9jg7`, prova initial-boot-native) aprovados.
Não repetir migrate/compose77/seeds ou a coleta C97 já aprovada.

**C99 novo:** [contrato](phase4-c79-session.md), fontes
`phase4_c79_session.py`, `run-phase4-c79-session.py`, checker/closure/publisher.
Reusa executor C77 congelado e host/provider/core instalados; namespace host
`build/phase4/c79-session` separado, sem alterar fontes/provas/pointers C77.
Exige prova/recibos C97, mesmo boot78/UUID, guarda141arquivos C79 e infraestrutura.
38casos novos passaram em `checks.fz22lya7`, latest-checks; 47casos C77
inalterados reutilizados por hashes, sem repetir testes antigos. Nova fixture
faz cópias reais de /etc fictício, com mount substituído e container isolado.

**Primeira abertura falhou antes de GUI:** observação `observe.6f2_dxjc` passou,
sessão `load.i_3vi975` teve native125/startup-failed. C79 não tem /etc/asound.conf;
worker antigo pressupõe arquivo existente. Confirmado na árvore da candidata
e no console. Nenhum menu/core/áudio iniciou. CLEANUP1 acompanhou restauração
de preparo parcial (writer-original vazio e wireplumber-before ausente).
Postflight/infrastructure e mountinfo global já passaram. Inspeção extra
comparou mixer/DRM/brilho/volume/preferências e ausência de processo/mount; cápsula
removida, `failure-cleanup.exit=0`. Registros/failure-analysis preservados no estágio.

**Ajuste somente RAM:** `port/device/rk-r35s-p0/c79-session/etc-view.sh` e worker
derivado por `prepare-phase4-c79-worker.py`. Copia /etc preservando links/modos
em cápsula root-only tmpfs, cria asound.conf644 a partir do template público
C79 pinado e faz bind de /etc só no namespace privado ANTES do perfil.
Não remonta rootRW nem escreve no cartão. Ao restaurar, compara ALSA original
e exige que asound.conf continue ausente na raiz original; arquivos privados
eventualmente copiados permanecem em RAM e não são coletados/publicados.
OverlayFS não está disponível; não carregar módulo nem alterar kernel.
Check nativo `check-native-phase4-c79-etc.py` APROVADO em `native-etc.i5gzc639`:
copy/bind/restore reais sem GUI/core/ROM/áudio; cápsula removida, rootRO,
mountinfo global/infraestrutura preservados e asound original ausente.
Nova observação `observe.r3l93ohc` passou com fontes corrigidas no boot78.
Sessão `load.buzw5gwl` parou no S90storage: falta /mnt/mmc na raiz C79 RO.
Operação1/CLEANUP0; postflight/mountinfo/remoção da cápsula/página final passaram.
Ainda sem GUI/core; não declarar resultado funcional. Helper revisado também
isola /mnt vazio em RAM com mmc, e exige ausência original após restauração.
38casos acima são da revisão atual. Check nativo revisado APROVADO em
`native-etc.nau45w73`: duas visões criadas/bindadas/desmontadas, rootRO e
infraestrutura/mountinfo preservados, asound.conf e /mnt/mmc originais ausentes.
Observação atual `observe.zo30k5jc` passou; terceira abertura
`load._68hm2gh` passou com essa revisão. Usuário respondeu “Tudo certo” à
conferência de imagem/direcional/som/restauração/retorno. Saída hotkey0,
1001frames/expired0, operação0/cleanup0. Mapas confirmaram menuC46→host/provider4/
core instalados→menuC46. Snapshot e metadata idênticos ao C63, sem QuickSave.
Recibo físico ligado por hash a analysis.json; análise técnica e fechamento
por recibos autênticos passaram. CSV recente61Hz, quatro underruns/1971frames
ausentes agregados, sem atribuição temporal; não alegar estabilidade longa.
RootRO0755/PCMclosed/p3off/UIoff/taint0, preferências55/70, mixer/DRM/brilho,
mountinfo global e infraestrutura restaurados; cápsula removida/página final.
Não existe GUI ou worker ativo dessa sessão. Publicador C99 não acessa console.
Prova sanitizada `dist/phase4/c79-session` congelada:26arquivos e3provas
ancestrais conferidos por hash; fontes dos38checks continuam iguais. Sem
ROM/estado/ELF/UUID/identidade privada ou cópia de /etc nos artefatos públicos.

Nenhum teste físico pendente nesta sessão; não repetir C99 aprovado. As visões
RAM resolvem asound.conf e /mnt/mmc somente durante a cápsula: raiz C79 original
continua sem esses pontos. Próximo incremento útil é preparar uma correção de
layout pequena e verificável para imagem/instalação antes de autostart, sem
regravar512MiB por rotina nem tocar seeds/contador/snapshot. Frontend permanente,
menu geral de ROMs, SRAM/novos saves, longa duração e perda elétrica não qualificados.
C98 duas passagens continua rascunho sem testes/adaptador físico; não implantar.
Backups/fences/preimages locais preservados; arquivos no Deck foram removidos
manualmente conforme confirmação acima. Original32 nunca acessado.

## Marco anterior — migração C94 e primeiro boot C79/C97 aprovados

**05/11/2026:** usuário informou `C94 INITIAL MIGRATION COMPLETE`.
test128 foi transferido do Deck ao R35S, que respondeu em192.168.15.8,
C07/boot78. Original32 permanece guardado. Não trocar cartão nem reiniciar
para repetir validação já aprovada. Antes da transferência, no Deck:
Verificação SSH confirmou resultado concluído, nenhum helper/mount, guarda
temporária intacta, quatro aliases RO1 e nenhum relatório de falha.
Observador PID139073 foi interrompido sem ter iniciado coleta: sem processo,
sem arquivos collect/proof e sem estágio copy anterior. Não houve retry do writer.
Estado privado `p2-initial/resume-completion-status.json`; inspeção permitiu
uma coleta manual finita e publicação de prova, ambas concluídas.

**C94 nativo e coleta APROVADOS:**
`build/phase4/p2-initial/copy.cba4yn92`, `latest-complete`.
Recibo/journal/captura/fontes/pacote/lineage verificados: exatamente536870912bytes
na p2, complemento integral MBR/p1/p3 preservado, releitura fria correta,
contador reservado77 e novo fence com cópia independente sincronizada no host.
Prova sanitizada `dist/phase4/p2-initial-native`, 20arquivos com hashes conferidos.
`manual-resume-complete.json` registra retomada da coleta sem repetição do writer.
C93 compose real `initial-migration/compose.h5mhulhi` e C86atual76
`physical-capture/copy-postboot.mt5xfcij` permanecem vinculados ao pacote
`p2-initial/package.1at_m_2h`. **Não repetir compose/migrate nem restaurar seeds.**

**C97 primeiro boot físico APROVADO:**
`port/scripts/collect-phase4-initial-boot.py --host IP_DO_R35S`.
25casos offline aprovados em `initial-boot/checks.iqf0zim8`, fontes atuais iguais.
Pré-condições reais `lineage()` agora passaram: prova C94/fence/journal,
candidata C93 e identidade4; todos141arquivos da guarda C76 correspondem à
árvore C79, com140públicos/1identidade. Usuário confirmou cartão no R35S/IP.8.
Tentativa `initial-boot/collect.r9a0gvf9` expirou antes de SSH (exit255/stdout
vazio). Após ping/porta2222 disponíveis, foi repetida somente leitura no mesmo
boot: `initial-boot/collect.kz1a9jg7`, latest-complete, exit0. Boot78 confirmou
consumo NC2048bits sem crédito, readiness/start+stop, seed creditável novo256bytes,
seeds anteriores ausentes, identidade4 preservada e guardas141hashes/metadados.
Root0755/ext4RO, p1/p3 desmontadas, PCM fechado, sem UI/BT/.once. Coletor não
escreveu/reiniciou/rearmou testes; main nativo positivo exercitado.
Reusa somente render/decoder puros C91; main C91 continua não qualificado.

**C97 prova nativa congelada:** `port/scripts/package-phase4-initial-boot.py`
revalida lineage/script/recibos/vínculos e exporta somente campos permitidos.
`dist/phase4/initial-boot-native`, 14arquivos e5provas ancestrais conferidos por
hash, fontes atuais iguais. Sem bootID, shell gerado, fence ou hashes privados
de seed/identidade/imagem. Ver [contrato C97](phase4-initial-boot.md).
Não repetir coleta bem-sucedida, migrar a candidata77 novamente ou recuar seeds:
o primeiro boot já consumiu essa candidata. Eventual recuperação exige captura
atualizada e novo seed/contador monotônicos, conforme contratos C84/C85.

**C98 otimização futura ainda rascunho NÃO TESTADO:**
`port/scripts/phase4_p2_two_pass.py`, sem CLI/adaptador físico. Propõe duas
passagens integrais em vez de cinco (~60% menos leitura), com FD exclusivo p2.
Sem medição ou qualificação física; não implantar. Nenhuma fonte do C94 foi
alterada. Próximo incremento pode qualificar o fluxo instalado sobre a nova
árvore C79, com razão concreta de regressão após migração integral. Áudio/jogos
não foram repetidos neste boot; não alegar validação funcional nova só por C97.

Deck ainda necessário para eventual recuperação; não limpar backups, fences,
preimages ou ferramentas. Guarda `/run/udev/rules.d/99-holo-automount.rules`
é temporária e desaparece em reboot do Deck: em futura reinserção não assumir
que continua instalada. C95/C96 já repararam o último automount, provas intactas.
SSD host~26GiB livres: reutilizar factory privada, evitar imagens extras.
Refs/SDK/ROM/saves/original32 e provas ancestrais preservados.

## Marco anterior — C94 migrate ativo no Deck; observador iniciado

**05/11/2026:** usuário retomou implementações. Original32 permanece guardado.
**test128 está no Steam Deck192.168.15.13/deck:22**, sem sudo sem senha;
usuário executa comandos root no Konsole. Não trocar cartão/reiniciar Deck nem
abrir partições. Guarda temporária C83 ativa e quatro aliases RO1, p2/p3
root0755, fsck0 e userdata igualC82 foram conferidos após C96. Agora o helper
C94 está ativo; as proteções RO podem mudar durante sua transação controlada.

**C94 preparado offline:** entrada finita migrate separada de recover C89,
fábrica C79 pinada, pacote19folhas, backup/lineage, recaptura física nova e três
scans por FD antes do controller C87/C90 sóp2. Preparador, receivers, coletor,
observador e prova nativa implementados. 84casos passaram (43entrada/41transporte),
ext4 reais sintéticos32MiB e adaptadores físicos substituídos; mains positivos
completos de deploy/coleta nativa ainda não exercitados. Prova congelada
`dist/phase4/p2-initial-prepared`. Checks `p2-initial/entry-checks._vzxw9di` e
`transport-checks.u9t5p4uf`; imagens sintéticas removidas após logs. Captura73
antiga foi recusada antes de SSH/RNG/subprocess/estágio. A preparação offline foi seguida de composição/deploy reais descritos abaixo;
prova preparada é histórica e não deve ser alterada. Ainda sem escrita/boot C94
confirmados neste registro.

**Estado R35S anterior à transferência:** usuário atualizou IP para192.168.15.16.
Probe e guardas C76 passaram no boot76, CIDtest128, root0755/RO, p3 desmontada,
PCM fechado, sem UI/.once. Desligamento normal sync+/sbin/poweroff retornou0
(`p2-initial/shutdown.11if09mg`). Usuário confirmou cartão no Deck e iniciou
sshd após conexão recusada. Boot75 pós-C89 continua qualificado; não foi
repetido. Counter76 reflete reboot posterior do usuário, sem rearmar `.once`.

**Desvio real de automount resolvido:** Deck voltou sem regra em `/run`;
SteamOS montou ROOTFS e MUOSDATA RW, alterando ambas raízes para0777. Preflight
recusou corretamente (`p2-initial/deck-preflight.6t1_p8pa`). Usuário desmontou
os dois mounts. Plano C83 original prefix/estado72 NÃO foi reaplicado ao estado76;
fontes, pointers e provas C83 permanecem intactos.

**C95 proteção/captura nativa aprovada:** [contrato](phase4-card-rearm.md).
Helper sem writer/SETRO0, 27casos offline, pacote `card-rearm/package.y4zvuazg`;
usuário executou sudo protect e informou COMPLETE. Coleta independente
`card-rearm/copy.xiayo6hd`, latest-complete: guarda restaurada/RO1, prefix640MiB
atual e seis cápsulas verificadas por hash/reconstrução, boot76, fsck0, userdata
igualC82. Ambas raízes0777; plano de6bytes em dois setores512:
p2offset134385664 (5bytes modo/checksum), p3offset675295232 (1byte modo).
Prova `dist/phase4/card-rearm-native` congelada, sem payload/seed/boot C95.

**C96 reparo nativo APROVADO:** [contrato](phase4-root-repair-current.md).
29casos offline em par ext4 reais32MiB passaram, incluindo fsck após extração,
journal/unlock parcial/shortwrite/segundo setor/fsync/userdata/lineage. Controles
físicos substituídos, writes512/hashes reais; fontes C83/C87 inalteradas.
`root-repair-current/checks.e1xuak57`, latest-checks. Pacote18folhas
`package.t03kf_sn`; usuário executou sudo repair e informou COMPLETE.
Coleta independente `root-repair-current/copy.9uyv21bh`, latest-complete:
recibo/journal/cápsulas/source/context verificados, 1024bytes físicos/6bytes
alterados, root0755, fsck0 p2/p3, prefix depois esperado, SB/GDT e userdata
preservados. RO1/guard/kernel conferidos, sem mounts/helpers. Sem seed novo,
boot ou migração C79. Prova `dist/phase4/root-repair-current-native` congelada.
Não alega hash de todos setores livres p3; C94 fará complemento completo.

**C86 captura atual APROVADA:** pacote `physical-capture/package-postboot.xe4qjehs`,
latest-package-postboot, usuário sudo `/home/deck/muos-r35s-c86-postboot-aceda424ba8f/phase4-physical-capture.py postboot`
informou CAPTURE COMPLETE. Coleta/scan C85 independente passaram:
`physical-capture/copy-postboot.mt5xfcij`, latest-complete-postboot. Fonte76,
root0755/fsck0, árvore/observação/artefatos iguais, vinculada ao fence EXISTENTE74
C89 (`p2-recovery/copy-recover.4sw5hjzf/host-copy.json`). Sem escrita de payload.

**C93 COMPOSE APROVADO em produção:**
`initial-migration/compose.h5mhulhi`, latest-complete. CLI qualificada completou
fsck0/árvore pública C79/identidade/históricos/EAs, removendo seeds antigos e
gerando uma vez seed.no-credit256 sem carregá-lo/creditá-lo. Fonte76→candidata77,
primeiroC07esperado78. analysis/host-analysis/request e bytes fontes conferidos;
claim compose.claim persistido. **Não regenerar/repetir compose.** Factory privada
C88/C79 reutilizada, não antiga candidata72. Não publicar imagens/seed/ROM.

**C94 PREPARE APROVADO:** `p2-initial/package.1at_m_2h`, latest-package.
`package.claim` persistido. Fábrica/candidata512MiB transferidas como arquivos
privados regulares, stream/hash/readback e mapa de fontes/provas/lineage, kernel,
RO/guard conferidos. Pacote19folhas target
`/home/deck/muos-r35s-c94-initial-ae2bb645d4a2`.
Solicitado ao usuário sudo local `phase4-p2-initial.py migrate`, mantendo Deck
alimentado/Konsole aberto/cartão no leitor. **Usuário confirmou primeiro C94_STEP; MIGRATE EM EXECUÇÃO.** Nunca repetir
ou matar writer durante hashes; manter Deck alimentado e Konsole aberto.
O writer grava512MiB sóp2 e faz5passagens de complemento integral (~596GiB de
leitura), podendo levar mais de1hora; preserva MBR/p1/p3, sem retry/rollback.

**Observador iniciado UMA vez:** result
`/var/tmp/muos-r35s-c94-initial.upacga49`, root-helper `muos-r35s-c94.8ybaup20`;
request privado `p2-initial/observer-request.json`. CLI watch-phase4-p2-initial.py
com esses argumentos/host192.168.15.13. Verificar latest-watch/status/claim antes
de qualquer nova invocação; não repetir observador/coletor automaticamente.
Ele não inicia/para writer, acompanha estado kernel por metadados e coleta uma
vez ao concluir, publicando prova. Em falha preservar journal/estágio, não
retirar cartão, não matar writer nem fazer retry. **Não entregar cartão antes
de novo fence independente no host e conferência RO/unmounted/semhelpers.**
Depois boot físico C79 esperado78, fence77/seedNC, com verificação SSH de
árvore pública C79 e entropy. Trabalho host adicional possível durante hashes.
**Ponto de espera solicitado pelo usuário:** root writer PID15713 no Deck;
observador host PID139073, sessão21606, estágio privado
`build/phase4/p2-initial/watch.25bhbgqy` (`latest-watch`). Última observação
status-0034: 106,8GiB lidos, 0,09MiB escritos, RO[1,1,1,1], sem falhas;
`complete.json`/`failure.json` ainda ausentes. Não interpretar isso como migração
concluída. Cinco fontes ativas C94 iguais ao snapshot preparado congelado.
O observador continua sem chamadas ao modelo e fará coleta/prova uma vez.
Antes de retomar, conferir seus arquivos de estado; não iniciar outra instância.

Usuário executou localmente o bloqueio de suspensão:
`sudo systemd-inhibit --what=sleep:idle --mode=block --who=muos-r35s-c94 /usr/bin/tail --pid=15713 -f /dev/null`.
Bloqueio sleep:idle verificado ativo; evidência privada
`p2-initial/sleep-inhibitor-active.json`. Ele termina quando o writer sai.
Manter Deck alimentado, computador ligado, ambas abas Konsole abertas e cartão
no leitor. Usuário chamará quando aparecer `C94 INITIAL MIGRATION COMPLETE`;
isso ainda exige conferir coleta automática e fence independente antes da troca.
Em FAILED não repetir comando nem retirar cartão. Não há pausa do processo
nativo: somente encerramento da interação para economizar tokens.

**C97 preparado offline, sem boot físico:**
`port/scripts/collect-phase4-initial-boot.py`, checker homônimo e fixture
`port/diagnostics/phase4-initial-boot-fixture.py`; 25casos passaram em
`initial-boot/checks.iqf0zim8` (`latest-checks`), com sintaxe shell conferida.
Exige coleta/prova/fence C94 nativos antes de SSH; reusa funções puras C91,
não o main antigo. Os141arquivos C76 foram comparados à candidata C79 por
hash/tipo/modo/uid/gid/nlink/tamanho, incluindo busybox04755 explícito.
Verifica boot78, root0755/ext4RO, p1/p3 desmontadas, ausência de UI/BT,
identidade estável e consumo/rotação NC sem crédito; rejeita seeds anteriores.
Main positivo de coleta nativa ainda não exercitado; não há prova pública C97.
common.sh/guard-tree.json e vínculos gerados são privados, não exportar.
Não repetir testes de áudio/jogo antigos sem divergência.

**C98 rascunho futuro para reduzir tempo, NÃO TESTADO:**
`port/scripts/phase4_p2_two_pass.py` propõe duas leituras integrais do complemento
(antes/depois), em vez de cinco, e escrita por FD exclusivo da partição p2.
Sem amostragem nem exclusão de setores livres. Redução teórica de leitura~60%
(~238GiB contra596GiB), sem medição/qualificação física. Não possui CLI nem
adaptador físico; não implantar ou usar no cartão. Faltam testes de falhas,
contagem de I/O e qualificação dos controles/descritores em disco virtual.
Nenhuma fonte/guarda/prova do C94 ativo foi alterada para essa otimização.
C91main continua rascunho semsuite; não invocá-lo como coletor qualificado.

Não executar outro helper enquanto um root estiver ativo. Em FAILED nunca
repetir/rollback automaticamente; inspecionar estágio/journal e reforçar RO.
Guardar C82backup, C89fence, C95preimage/cápsulas e todas ferramentas do Deck,
ainda necessário. SSD host~26GiB livres; reutilizar factory privadaC88/C79,
evitar cópias extras e remover só fixtures descartáveis. Refs/SDK/ROM/saves e
original32 preservados. C91 main permanece rascunho sem suite, não requisito.

## Marco anterior — C93 preparador e callback aprovados offline; cartão no R35S

**05/11/2026:** retomada de implementações autorizada. Manter test128 no console
por enquanto; não foi solicitada troca ao Deck. Último estado físico confirmado:
R35S/IP192.168.15.10, C07/boot75 após recuperação C89. Nenhum SSH, reboot,
acesso a cartão ou operação no Steam Deck nesta etapa. Original32, refs, SDK,
ROM/saves, backups e ferramentas do Deck preservados.

**C93 concluído:** [preparador e callback inicial](phase4-initial-preparer.md).
`prepare-phase4-initial-migration.py check|compose` vincula último fence C89,
boot de recuperação qualificado, captura C86 pós-handoff nova, backup host
atual e fábrica C79. Refusa cabeçalhos antigos antes de ler imagens grandes,
criar estágio, container ou seed. Revalida por descritores os bytes dos backups
locais, usa somente factory.ext4 privada do C88 (NÃO a candidata estado72),
compara com prova C79 e executaria CLI C92 em container sem rede/dispositivos.
Claim exclusivo sincronizado recusa repetição após interrupção. Não foi composta
candidata nova: captura C86 disponível73 está desatualizada para o fence C89/boot75.

`phase4_p2_initial.validate_fd` prepara validação pré-desbloqueio do futuro
controller: descritor privado regular/nlink1/tamanho/hash/flock, scans reais da
fábrica/snapshot/candidata, elegibilidade C92 e assinatura/hash novamente.
Não fornece target/discovery/SETRO/writer. C89 recover-p2-only permanece intacto.

**30casos passaram** em ext4 sintéticos32MiB/container isolado, incluindo headers
atuais/antigos/contadores, backup com hash/metadados/link/tamanho inválidos,
três scans por FD e alteração da candidata durante scan. Bytes fontes e FD do
chamador preservados; imagens sintéticas removidas após logs.
`build/phase4/initial-migration/preparer-checks.96fs6x7v`, latest-preparer-checks.
Auditorias reais somente leitura:12artefatos atuais do backup host íntegros;
factory privada512MiB igual à C79 sem cópia extra; captura73 recusada antes de
container/RNG/estágio. Prova `dist/phase4/initial-preparer` congelada, fontes e
ancestrais conferidos. **Main positivo de composição completo ainda não
exercitado; sem candidata512MiB/seed real novo/deploy/fence/escrita/boot C93.**
C92 preservado com25casos/prova initial-migration, checks.kmmw5f7q.

**Próximo incremento C94:** entrada privilegiada FINITA de migração inicial,
preparador de pacote/recebimento, coletor/fence e testes de falhas/bootstrapping.
Reutilizar controlador C87 e guardas de cartão, sem transformar C89 recover em
writer inicial. Fixar hash factoryC79, conferir backup remoto/kernel/aliases,
recapturar p2 e derivar elegibilidade pelos FDs antes de SETRO0/escrita. Somente
p2; nunca flash raw640MiB sobre cartão três partições. Preparar/testar backend
antes de pedir cartão no Deck para captura atualizada. C79 NÃO liberada.

Fontes futuras: `p2-recovery/copy-recover.4sw5hjzf`, latest-complete-recover;
host-copy.json contém next_attempt_directory/id/sha256 do fence EXISTENTE74.
Boot75 válido: `recovery-boot/final-check.4y9cip12`, latest-final-check;
provas p2-recovery-native/p2-recovery-boot. Não repetir teste físico aprovado.
C88 candidata72 e C86 postboot73 não podem servir de migração. O main C91
continua rascunho sem suite; não é necessário para usar a evidência válida75.
C82backup/C83cápsulas permanecem no histórico; Deck ainda necessário, último
IP192.168.15.13/deck:22, SSH sem sudo sem senha; não limpar backups/ferramentas.
SSD host ~28GiB livres: reutilizar a factory privada em vez de duplicá-la.

## Marco anterior — C92 compositor inicial aprovado offline; cartão permanece no R35S

**05/11/2026:** usuário retomou implementações e perguntou onde manter o cartão.
Orientação dada: **manter test128 no console por enquanto**; preparar offline
compositor/preparador/controlador da migração inicial e só depois pedir mudança
ao Deck para captura atualizada/escrita p2. A pausa anterior foi encerrada pelo
pedido atual. Nenhuma operação SSH, reboot ou acesso ao cartão nesta etapa.
Último estado confirmado do R35S: IP192.168.15.10, C07/boot75 aprovado após C89.
Original32 guardado; refs/SDK/ROM/backups e ferramentas do Deck preservados.

**C92 concluído offline:** [composição inicial atualizada](phase4-initial-migration.md).
Novo módulo `phase4_initial_migration.py` e CLI `phase4-initial-migration.py`
reutilizam C88/C85/C84 sem modificar suas fontes congeladas. Factory pública
mais captura pós-handoff vinculada produzem árvore C79, identidade/EAs/históricos
preservados, seeds antigos removidos, seed.no-credit256 novo e contador=max+1.
Exemplo sintético backup72/registro74/captura75→candidata76/primeiroC07=77.
Intermediário C88 é consumido privadamente, sem outra cópia512MiB, e nunca é
candidata de handoff. Marcador de estágio exclusivo+fsync recusa composição
interrompida antes de outra geração de seed. Fsck0/readback/comparação integral
antes de completar; contexto/JSON sozinho NÃO autentica captura/libera escrita.

**25casos passaram** em ext4 reais sintéticos32MiB e container existente sem
rede/dispositivos. Incluem fonte pública antiga diferente da nova fábrica,
identidade/EAs/históricos/symlink, seed e contador76/77, contador72 abaixo do
registro74, contextos/modos alterados, RNG indisponível/curto/repetido,
clone/troca de seed interrompidos, estágio repetido e saída symlink/caminhos
inválidos. `build/phase4/initial-migration/checks.kmmw5f7q`, latest-checks.
Prova sanitizada `dist/phase4/initial-migration` congelada; imagens sintéticas
descartadas após logs. **Nenhuma nova candidata de produção512MiB/seed real,
nenhum preparador/controlador físico/deploy/fence/boot C92.**

**Próximo incremento:** preparador e controlador FINITO de migração INICIAL,
com fonte factory C79 pinada por prova, captura física recente vinculada ao
último fence C89 e estado conhecido, backup independente, validação por scans
de descritores e novo fence/coleta antes de entregar mídia ao console. Não
reutilizar o modo recover-p2-only C89 como se aceitasse a árvore nova C79.
C88 candidata estado72 e C86 postboot antigo73 estão desatualizados: não usar
para migração. Preparar/testar backend antes de pedir nova troca de cartão.
A migração C79 ainda NÃO está liberada para escrita/boot.

Referências privadas válidas: C89 `p2-recovery/copy-recover.4sw5hjzf`,
latest-complete-recover; host-copy.json fornece next_attempt_directory/id/sha256
para uma futura captura C86 postboot com o fence EXISTENTE (contador74).
Boot75 aprovado por SSH: `recovery-boot/final-check.4y9cip12`, latest-final-check;
provas p2-recovery-native e p2-recovery-boot preservadas. Não repetir esses
ensaios sem divergência. Rascunho CLI C91 ainda exige suite própria ausente;
seu main não está qualificado e não é pré-requisito para reutilizar a evidência
válida do boot75. C82backup/C83cápsulas e guardas permanecem no histórico abaixo.
Deck último IP192.168.15.13/deck:22, sem sudo sem senha; será necessário para
migração offline, portanto não limpar arquivos/backups agora. Cartão NÃO foi
solicitado no Deck nesta retomada. SSD host ~28GiB livres, evitar duplicações.

## Marco anterior — recuperação C89 e boot75 aprovados; encerrado por hoje

**05/11/2026:** usuário pediu somente verificações finais e encerramento para
poder desligar o computador. **Não iniciar novas integrações, reboots ou
operações no Deck nesta sessão.** R35S com test128 ligado/IP192.168.15.10,
C07/boot75. Original32 guardado; refs/SDK/ROM/backups preservados.

**C89 físico concluído e conferido:** helper Deck retornou RECOVERY COMPLETE.
Gravou exatamente536.870.912bytes somente na p2; releitura fria/hash e
complemento integral (MBR/p1/p3) preservados. Cinco passagens, cerca de596GiB
lidos no total e512MiB gravados, sem retry/rollback. Quatro aliases RO, cartão
sem mounts/helper antes da retirada. Observador coletou recibo/journal/árvore
nova e próximo fence no host, publicou prova sanitizada e terminou sem falha.
`build/phase4/p2-recovery/copy-recover.4sw5hjzf`, latest-complete-recover;
prova `dist/phase4/p2-recovery-native`. Recibo de recuperação mantém
physical_boot_after_recovery_qualified=false por ser anterior ao boot; o
resultado posterior está separado abaixo, não alterar prova congelada.

**Boot físico pós-recuperação aprovado:** próximo fence foi verificado no host
ANTES da entrega ao console. Seed.no-credit256 novo/contador74 na recuperação;
C07 incrementou para75. Verificação SSH somente leitura passou: arquivos C76
instalados e quatro arquivos de identidade iguais, guardas C07/media/kernel,
root0755/RO, p3/FAT desmontadas, PCM fechado, sem UI/.once ativo. Caminho
entropy mode=seedless; log confirma2048bits consumidos SEM crédito, readiness
antes da geração de novo seed creditável e parada, seed.no-credit ausente e
hash do seed atual diferente dos seeds anteriores. Sem alteração/reboot pelo
verificador. Host: `build/phase4/recovery-boot/final-check.4y9cip12`, pointer
latest-final-check; análise e script privados600, sem exportar bytes de seed.
Prova sanitizada `dist/phase4/p2-recovery-boot` conferida, sem boot_id ou hashes
privados. Detalhes em [qualificação nativa](phase4-p2-recovery-boot.md).

**Steam Deck ainda necessário:** futura migração inicial C79 exige novamente
leitor/offline e cópias de recuperação. Usuário pediu limpeza apenas se não
fosse mais necessário; condição não atendida, arquivos/backups preservados.
Último IP Deck192.168.15.13, usuário deck/SSH22 com chave pinada, sem sudo sem
senha. Cartão está no R35S, NÃO no Deck. Manter regra temporária C83 de automount
até terminar trabalho offline; reinserção pode trazer kernelRO0 e deve seguir
preflight/SETRO1. Não fazer limpeza genérica nem apagar backups/cápsulas/fences.

**Próxima retomada:** C79 ainda NÃO liberada para escrita/boot. C88 provisionada
com seed/contador72 está desatualizada após boots73/75; não gravar essa imagem.
Preparar atualização do estado privado a partir de captura nova e controlador
finito de migração INICIAL (C89 oferece só recover-p2-only), com backup/fence e
validações antes de nova entrega. Não repetir C89/C90 ou testes físicos já
aprovados sem divergência concreta. Rascunho `collect-phase4-recovery-boot.py`
foi usado apenas para render/decodificação da checagem final; main automatizado
C91 ainda exige suite própria ausente. Não forjar latest-checks nem tratar CLI
como qualificada. Os contratos/scanners/controlador e artefatos anteriores
permanecem válidos; consultar histórico apenas conforme necessário.

## Marco anterior — C89 em execução no Deck; observador/coleta preparados

**04/11/2026:** test128 voltou ao R35S/IP192.168.15.10; boot73 observado e
arquivos C76 instalados conferidos por SSH. CID test128 correto, root:root0755,
raiz somente leitura, p3 desmontada, PCM fechado, sem menu/jogo/.once ativo;
kernel confirmou RNG inicializado. O desligamento normal `/sbin/poweroff` foi
solicitado após as guardas, SSH retornou0. **Usuário retornou e confirmou o
test128 novamente no Steam Deck.** SSH/IP192.168.15.13, identidade do cartão,
ausência de mounts/helpers antigos e regra C83 conferidos pelo preparador.
Original32/refs/SDK/ROM/backups preservados. **C79 continua sem liberação de
escrita/boot.** Recuperação C89 em andamento; não presumir conclusão de escrita.

**C86 postboot aprovado:** Deck `/var/tmp/muos-r35s-c86-capture.gd72ysqm`;
coleta host e scan C85 independente em `physical-capture/copy-postboot.u28hpe9v`,
latest-complete-postboot. Fsck0, contador73, seis privados, hashes/árvore/
observação iguais; sem escrita de payload. Pacote package-postboot.9yprvwra.
**C85 compose aprovado:** `recovery-image/compose.lru8bw5e`, latest-compose;
imagem regular512MiB, contador74, seed.no-credit256 fresco, seeds antigos
removidos, fsck0, árvore/identidade/históricos preservados. Não gerar outro seed
ou repetir composição por causa de interrupção do chat.

**C89 em execução:** pacote `p2-recovery/package-recover.fvxfpv3y`,
latest-package-recover; comando local já iniciou no Deck:
`/home/deck/muos-r35s-c89-recover-52ad70832915/phase4-p2-recover.py recover`.
Snapshot root `/run/muos-r35s-c89.pl9io3wj`; estágio ainda root700
`/var/tmp/muos-r35s-c89-recovery.r249cbhv` (inacessível por SSH enquanto ativo,
isso é esperado). Em última observação ~31GiB lidos, zero bytes gravados,
sem falha. Há cinco passagens integrais do complemento no caminho completo,
incluindo118GiB p3 cada; pode levar mais de uma hora. Não interromper/repetir
helper, não abrir partições nem mover cartão antes da coleta independente.
Manter Deck alimentado/Konsole aberto.

Observador sem sudo ativo no host, sessão exec93000:
`p2-recovery/watch-recover.s41pudb2`, latest-watch-recover.
Lê estado a cada30s por até6h; não inicia/interrompe/reexecuta writer. Após
conclusão e remoção do snapshot root, chama coletor e publicador nativo UMA VEZ.
17casos offline aprovados (`watch-checks.nc6use10`, latest-watch-checks),
incluindo identidade/guardas/RO, falha SSH, timeout, coleta falha e claim
exclusivo durável `watch-recover.claim`. **Não reiniciar observador/limpar claim
às cegas:** conferir status-*.json, complete.json/failure.json e processo/sessão
existente primeiro. Timeout/falha do observador não cancela o helper do Deck.
Publicador nativo syntax/precondição validados: recusa sem latest-complete-
recover; nenhuma prova nativa publicada ainda. [Detalhes](phase4-p2-recovery-native.md).

**Próximas ações:** observar tentativa existente; se concluída, conferir
latest-complete-recover/host-copy.json e prova p2-recovery-native. Se observador
falhar, ler seus logs e falha privada do Deck sem repetir writer automaticamente.
O próximo fence precisa estar verificado no host ANTES de devolver mídia ao
R35S. Só então solicitar boot de qualificação (contador esperado75), RNG/rede/
identidade; esse ciclo precede migraçãoC79. Não fabricar observação, substituir
fence ou restaurar seed/contador antigos.

Registro C84 de handoff REAL selado ANTES do boot73:
`build/phase4/p2-recovery/reference-handoff.13dh7j54`, pointer
`latest-reference-handoff`; analysis.json contém attempt_directory/id/sha256
para `prepare-phase4-physical-capture.py postboot --host ... --journal ...
--attempt-id ... --attempt-sha256 ...`. Vincula root ATUAL C76/C86 e contador72,
não candidata C88. Registro conservador boot-may-have-occurred, exclusivo0400,
fsync/readback; não gerar substituto mesmo se faltar pointer. Observação SSH
privada: `p2-recovery/reference-boot.pon164nz`, latest-reference-boot.

C87: [controlador p2](phase4-p2-controller.md),16+46+24casos e quatro casos
em loop real/kernel7.2.7-valve2. Escrita512MiB/fsck/readback/complemento,
short-pwrite sem retry/complete e quatro aliasesRO. Prova p2-controller
congelada. `p2-writer/copy-qualify.eu471jrh`, package-qualify.12vlbtbq.
Duas falhas anteriores antes de unlock: FUSE LocalSend corrigido por stat como
UID dono/starttime; aliases de loop divergiram sem valores, causa não provada.
Rodada com settle passou. Parciais/journals retidos; snapshots antigos auditados.

C88: [provisionador inicial](phase4-initial-image.md),17casos passaram.
FactoryC79+referênciaC86 geraram candidata regular512MiB com fsck0, árvore
pública/metadados iguais, seis privados, contador72 e nove históricos iguais.
Prova initial-image congelada; `initial-image/provision.evbj4tey`,
checks.3zx9m7um, latest-complete/latest-checks; Deck arquivo privado
`/home/deck/muos-r35s-c88-candidate.pp__3brn/candidate.ext4`, stream/readback/
fsync e releitura conferidos. **DESATUALIZADA após boot73: atualizar estado
privado/seed/contador antes de qualquer elegibilidade futura.** Não está na mídia.

C89: [recuperador p2 preparado](phase4-p2-recovery.md),21casos de elegibilidade
com ext4 reais32MiB,27de entrada/contexto/cópias/bootstrap,22de transporte e
cinco de handoff:75passaram. Prova `dist/phase4/p2-recovery-prepared` congelada,
fontes atuais e provas ancestrais conferidas. Helper finito recover-p2-only
agora implantado e em execução; recuperação física ainda sem conclusão
qualificada, ver andamento acima. Sem modo de migração inicial. Preparador recusa antes de SSH se
faltar captura física C86 pós-handoff independente (agora aprovada). Deriva árvore/
identidade/EAs/seed.no-credit256 fresco/contador=max+1; entrada recaptura p2,
valida backup/ack host, lê complemento inteiro inclusive118GiB p3 em várias
passagens, usa controlador C87 e sela próximo fence. Sem retry/rollback/boot
implícitos. Coleta independente host obrigatória antes de entregar mídia.
Pointers `p2-recovery/latest-checks`, latest-entry-checks,
latest-transport-checks, latest-handoff-checks (21/27/22/5).

C90: [MMC real sem payload](phase4-p2-card-readiness.md),17casos de controlador
+19de transporte passaram; ensaio nativo e coletor aprovados. Claim exclusivo
O_RDWR, RO1→whole/p2RO0→RO1 mantendo p1/p3RO1; três leituras da p2 inteira,
MBR/prefixo16MiB iguais à C86. Sem writer/pwrite/write-intent/seed/fence/boot.
`card-readiness/package.dfrpf2_2`, checks.slu36_9j,
transport-checks.bf_kbplk; Deck `/var/tmp/muos-r35s-c90-readiness.5u4bjdhb`;
host `card-readiness/copy.vd5atohm`, latest-complete. Prova card-readiness
congelada. Kernel qualificado7.2.7-valve2-2-neptune-72-g31504582a073.
Não repetir C90 sem divergência concreta.

C86 reference físico+scan C85 independente aprovados:536.870.912bytes,
fsck0, contador72, seis privados,3.669entradas; árvore e hashes iguais.
Postboot real aprovado no boot73; ver retomada acima. `physical-capture/copy-reference.5zp_8jgi`,
latest-complete-reference/latest-package-reference; Deck
`/var/tmp/muos-r35s-c86-capture.f_gz9vwf`. Prova physical-capture preservada.
Contexto/tree/privados não publicar. Reinserção no Deck pode trazer kernelRO0;
helper postboot reforçaRO1, sem limpar proteções implicitamente.

C82 backup Deck `/var/tmp/muos-r35s-c81-backup._nmzl6wx`; host
`build/phase4/offline-backup/download.l9t_h7tc`, recibo native-copy.pojr1cyp.
Preserva0777 histórico; C83 reparou cartão para0755 (não repetir).
C83 cápsulas/pointers sob build/phase4/root-permissions intactos.
C84 política85casos/fence/seed semcrédito e C85 compositor36casos válidos;
C85 reference.2iv_egpo sob build/phase4/recovery-image. Históricos consumidos
C12/C25 preservados, .once ativo recusado; EAs externos nos privados
substituídos recusados por limite observado de debugfs unlink.
Não usar restore/formatter C20, escrever p1/p3, desbloquear cartão
implicitamente ou remover regraC83. SSH Deck sem sudo sem senha; execução local
só quando necessária. `.vscode/settings.json` exclui refs/build/dist de Pylance/
watchers. SSD host com cerca de29GiB livres nesta retomada; evitar duplicações
supérfluas, preservar backups e fixtures referenciadas pelas provas.

## Marco anterior — C82 causa do backup diagnosticada; nova execução pendente

Retomada04/11: Deck/IP192.168.15.13/test128 conferidos, p1/p2/p3 desmontadas.
Auditoria apenas da cópia parcial confirmou boot72 e root da p2 root:root0777;
demais pais0755 e privados0700 corretos. Script nativo SteamOS
`/usr/lib/hwsupport/steamos-automount.sh` linha99 aplica chmod777 ao mount root
quando deck não pode escrever; causa concreta do desvio após automount rw.
Não houve novo boot nem mudança de identidade. [Registro C82](phase4-backup-native.md).

Implementado auditor limitado à cópia regular com snapshot protegido;11casos
passaram. Cópia privada da raiz parcial e relatório coletados por hash em
`build/phase4/offline-backup/audit-native.u81m_f4b`, sem abrir cartão.
Validação local dos seis arquivos privados contra C80/boot72 passou e preservou
imagem; padrão0755 continua recusando0777.

Helper agora tem política explícita para preservar fonte0777 **somente para
backup**, selada e vinculada a SHA do automounter e da raiz diagnosticada.
Outro modo/script/raiz aborta; plano C80, uid/gid e demais guardas mantidos.
Recibos propagam obrigação de reparo de metadata antes de boot. Nenhum reparo,
writer/provisionamento/restore/format/novo boot ou carregamento de seed ocorreu.
86casos passaram (72anteriores reexecutados por mudança real do núcleo +14
novos),17 de transporte. Prova C81 anterior continua congelada e intacta.

Novo pacote `package.g1b5afk1`, checks `checks.idd2hzax`, transporte
`transport-checks.vocrj86t`; deploy verificado no Deck em
`/home/deck/muos-r35s-c82-backup-44a850297f33`. Usuário foi solicitado a iniciar
backup por sudo local. **Backup nativo revisado/host-copy ainda pendentes.**
Parcial inicial `...chy99nhv` permanece protegida, sem recibo válido.

Próximo: colher resultado do helper revisado e cópia independente; conferir
p3 e fonte exata. Reparar modos0755 de forma guardada após backups, preparar
recuperação pósboot monotônica e só depois instalar/bootar candidata. Manter
cartão no Deck; original32 fora do fluxo. Limpeza anterior do SSD concluída,
SDKs e C78/C79 íntegros; não reconstruir caches/SDK sem motivo.

## Marco anterior — limpeza urgente do SSD; C82 backup nativo pendente

**04/11/2026:** usuário priorizou limpeza de `/home/lauro/dev` durante a
qualificação do helper. [Escopo, auditoria e efeitos no build](storage-cleanup.md).
Removidas145 árvores sintéticas de testes e191 diretórios de intermediários
Buildroot, preservando SDKs instalados/sysroots/targets/config/licenças,
Mali/libnl usados diretamente, código/docs/refs/dist/ROMs/chaves/backups.
53 imagens foram tornadas esparsas com SHA-256 integral igual. Recuperados
cerca de15,6GiB físicos; dev64→40GiB e espaço livre9,4→25GiB. Relatório final
`build/cleanup/summary.json`, com detalhes em [limpeza](storage-cleanup.md).
Os dois SDKs compilaram ELF64/AArch64 após a limpeza; baseline e provas
C78/C79/C80/C81 íntegros. Intermediários antigos podem exigir regeneração
para rebuild completo; não reconstruir automaticamente o SDK congelado.

**C82 pendente:** [registro nativo](phase4-backup-native.md). Cartão test128
está no Deck/IP192.168.15.13, Jupiter/CID/capacidade/setor corretos. Usuário
reativou sshd e reinstalou chave pública removida na limpeza anterior.
P2/p3 foram desmontadas normalmente após automount rw. Transporte novo com
17casos passou, pacote C81 transferido e hashes conferidos, sem alterar
fontes C81 ou repetir seus72casos. Usuário executou helper com sudo local;
retornou **C81 FAILED (ValueError)**, causa ainda desconhecida.

Parcial privada no Deck: `/var/tmp/muos-r35s-c81-backup.chy99nhv`; snapshot
root já não foi observado depois. Coleta recusou, sem backup real aprovado
nem host-copy válido. Não apagar parcial antes do diagnóstico nem repetir
leitura completa/editar contador/afrouxar guardas. Último survey live continua
C80/boot72; estado corrente deve ser estabelecido por evidência, não presumido.
Nenhum writer/provisionamento/format/restore/boot candidato executado.
Nenhuma ação adicional no Deck/cartão durante a limpeza local.

**Próximo:** diagnosticar apenas a cópia
parcial com privilégio local. Resolver eventual novo boot por vínculo novo,
qualificar backup+host-copy e implementar recuperação pósboot antes de
provisionar/gravar/bootar C79. Original32 permanece fora da operação.

## Marco anterior — C81 helper de backup preparado e validado offline

**C81 concluído offline em04/11/2026**, conforme pedido explícito “Prepare
somente offline por enquanto.” [Implementação e limites](phase4-offline-backup.md).
Sem SSH/R35S/Steam Deck, desligamento, troca de cartão, mount real ou backup
real. Último estado nativo conhecido continua C80/IP18/boot72, não revalidado.

Implementados helper Python local de execução única, núcleo de backup,
coletor da cópia independente, preparador/checker/empacotador. Não há servidor,
writer, formatação, restore, provisionamento ou operação de boot. C80 e refs
intocados. Cartão original32 fora do fluxo; instrução offline suspende ações
de hardware nesta etapa, apesar da autorização geral anterior do test128.

**72casos passaram:** guardas de identidade/aliases/todos namespaces/swap/
holders/erros; cópia/hash/fsync/falhas; opções ro+noload; host-copy sintético;
tar seguro e pacote com snapshot protegido. Container existente sem rede/
dispositivos qualificou extração debugfs/fsck de ext4 sintética16MiB e backup
lógico tar. Não qualifica operação completa, namespace ou reader no Deck.
Recibos sintéticos não representam backup/fsck do cartão real.

Fluxo futuro exige backup fresco640MiB, FAT/raiz extraídas e fsck0, allowlist
privada offline com seed recente e contador do survey, p3 fsck0/mount privado
ro,noload para prefs/store, desmontagem e nova conferência do prefixo. Segunda
cópia no host precisa hash/inventário/tar/fsync independentes; até lá o recibo
do helper mantém independent_host_copy_verified=false. Todos os resultados
continuam execution_enabled=false/device_writer_available=false.

Checks `build/phase4/offline-backup/checks.y1i3sznc`; pacote privado
`package.hnizy8zj/bundle` no mesmo diretório, vinculado ao plano C80/boot72.
Prova `dist/phase4/offline-backup` somente fontes/casos/resumos, sem plano
privado/UUID live/hashes de folhas privadas/ROM/seed/key/backup. SDK baseline
idêntico. Nenhum payload C78/C79 ou instalação nativa foi modificado.

**Próximo:** verificar boot real quando hardware for retomado; novo boot exige
survey/vínculo C80 novo e regeneração do pacote. Qualificar helper no Deck e
backup real+host somente quando a operação física for agendada. Implementar
recuperação pósboot com seed fresco/semcrédito e contador monotônico antes de
provisionar/gravar/bootar candidata C79. Restore byte-exato da p2 antiga após
QUALQUER tentativa de boot continua inelegível. Não reutilizar formatter/
servidor C20, não rearmar tokens e não repetir testes físicos já aprovados.

## Marco anterior — C80 plano p2/backup/recuperação e survey live aprovados

**C80 concluído em04/11/2026.** [Plano, contratos e limites](phase4-root-migration.md).
R35S respondeu em192.168.15.18, ainda boot72; survey somenteleitura aprovou
rootRO0755/quiet/40folhas instaladas/132preservados/fundação97/PCMclosed/
p3off/UIoff/taint0 e infra PID/starttime iguais. MBR real tem3partições,
capacidade/setor/CID/modelo/kernel/PARTUUID corretos. Prefixo16MiB coincide
com C79 após considerar somente a entrada p3 existente. MBR final idêntico.
Semreboot/GUI/novoSave/mountp3/escrita no cartão; Deck/original32 intocados.

**Implementado:** phase4_root_migration.py (planner puro, validação de recibos
futuros e política de recuperação), prepare/check/package-phase4-root-migration.py.
Plano limita a futura escrita à p2, offset128MiB/tamanho512MiB, protegendo
0..128MiB e640MiB..fim do128GB. Não autoriza rawfactory640MiB, mudançaMBR/p1/
p3 ou rollback automático. Todos os resultados execution_enabled=false e
device_writer_available=false. Não existe backend de escrita/provisionamento.

**84casos sintéticos passaram**, sem dispositivos/secrets: MBR/geometria/
CID/modelo/kernel/partições/saúde/tipos, allowlist/ownership/modos/links,
backup independente/fsync/fsck/cache/semconsumidores/userdata, factorynua,
seed antigo/reset decontador/tokens/árvore alterada e recuperação pré/pósboot.
Recibos de backup nos testes são sintéticos, sem alegação de backup real.
Código exige plano íntegro e recibos calculados pelo futuro helper guardado;
JSON de terceiros não é autenticação nem autorização para IO.

**Provisionamento planejado:** backup offline fresco do prefixo640MiB +segunda
cópiahost fsynced/hash ebackup lógico prefs/storep3 antes de escrita. Candidata
baseC78 recebe só allowlist do backupoffline, contador72 e seed maisrecente,
rede/key/auth identidade igual, sem init/loadseed/keygen/cache/token. Novo
boot antes dobackup exige survey/vínculo novo. Após QUALQUER tentativa deboot,
restore byte-exato de p2 antiga fica inelegível: pode repetir seed creditado e
recuar contador. Recuperação pósboot comseed fresco/semcrédito econtador
monotônico precisa de implementação própria antes de qualificar boot real.

**Survey privado:** seisarquivos registrados por metadata/hash, sem conteúdo
dechave/seed/config exportado. Seed0400, authpública0644, network/hostkey/
contador0600 eauxiliar hostkey.tmp.pub0600; seed.no-credit0400 opcional.
Primeiro survey recusou auxiliar/modes diferentes da hipótese600 geral;
política corrigida porarquivo e enumeraçãoinclui ocultos, sem alterar mídia.

**Artefatos:** build/phase4/root-migration/plan.fobcof88 echecks.m3djb50i;
prova dist/phase4/root-migration sófontes/casos/resumos/plano redigido.
Não inclui UUIDlive, hashes das folhas privadas, MBR/prefixobinários ou
credenciais. Guarda deprivacidade recusou primeira publicação porque hash do
reciboMBR também era hashprivado; redigido antes do freeze, sem publicar falha.
Nenhum backup offline/candidato provisionado/writer/serviço/token armado.

**Próximo C81 proposto:** helper offline limitado a backup, com testes de
identidade/aliascache/todosnamespaces/fsck/duascópias e inventário lógico p3;
preparar recuperação pósboot antes de qualquer publicação de raiz ou teste
físicoC79. Não reutilizar helper C20 de partition/format/resume nesse cartão.
C78/C79 continuam factory não bootadas, SDK/imagens intactos e licenças
pendentes/private-only. Revalidar IP/boot/UUID reais antes de retomar nativo.

## Marco anterior — C79 imagem completa com Gambatte aprovada offline

**C79 concluído em04/11/2026, inteiramente offline.**
[Composição, recibos e limites](phase4-gambatte-card-image.md).
Nova raw privada640MiB SHA256
`e9deed97f5d1ae7a9644f0fe20bd8918c7ab3a84c5c172493fcb27912540da4e`,
gzip64.988.906bytes/SHA499d48fe...; raizC78 a09edf63... integrada ao
bootchain/kernel/DTB/layout C70 fixados. MBR/offsets/duaspartições/Panel0/
ro/initC07/marcadorB01 mantidos. Core3e0940da instalado no caminho nativo.
Nenhum componente recompilado, nenhum cartão/console/Deck acessado.

**Verificações:** MBR canônico+cinco regiões e gapszero; seis folhasFAT
extraídas idênticas aos assets; FAT novo/fsck0; duas partições extraídas e
hashes iguais às fontes; gzip descomprimido igual à raw. Bootchain3regiões
byte-idêntico C70, Image/DTB/tamanhos/SHA embutidos noU-Boot conferidos.
Só PROBE.TXT mudou entre as6folhasFAT, agora identifica C79/C78/corepresente.
Raiz extraída é exatamente C78: fsck0/3403itens/18inodes/308ELFs/555módulos/
174loaders/probeAPI1 aproveitados porhash.27fixtures C70 reusadas por fonte
e recibos idênticos, sem alegar nova execução de fixtures ou físicaC77.

**Código/prova:** port/scripts/compose-phase4-gambatte-card-image.py e
package-phase4-gambatte-card-image.py. Stage
build/phase4/gambatte-card-image/image.efszbcqw, raw/gzip
muos-r35s-panel0-c79-private.img[.gz]. Prova
dist/phase4/gambatte-card-image sófontes/recibos, sempayload privado.
Raw/gzip C70, ext4C78, inventárioC78 eSDK conferidos intactos.
Licenças boot/GPU/core seguem pendentes; private-only/REDISTRIBUTE=NO.

**Factory:** C07/contador0/UIoff/sessãooff/preferênciasoff; semcredenciais,
seed RNG, hostkeys, ROM/snapshot/userdata/resize/callerC77. Não provisionada,
semflash/boot/reprodutibilidade/suspensão/Power/perdaelétrica qualificados.
Não confundir aprovação dos componentes C77/C78 com boot da imagemC79.
Não usar a rawfactory como atualização que preserve o userdata atual.

**Console não acessado neste recorte.** Última observação continua C77:
192.168.15.18/boot72/rootRO0755/fundação97/PCMclosed/p3off/UIoff/taint0,
preferências55/70 restauradas, RAMremovida/páginaC77; conferir novamente
antes de retomarnativo. Save C63/HEAD1/0/2 não foi acessado; demora abertura
C77 sem medição e paletaGB-DMG verde nativa seguem documentadas.
Original32 e Deck intocados; nenhuma sessão ou token armado.

**Próximo C80 proposto:** plano/ferramentas de provisionamento e recuperação
para boot supervisionado, com backup do estado real128GB antes de escrita.
Preservar instalação atual, MBR/p3/userdata/saves e estado privado de rede/
seed/chaves/contador; a imagemfactory tem duaspartições e não resolve essa
migração sozinha. Semwriter ou operação física armados. Caller permanente/
menu geralROMs/Power/suspend/SRAM/novos saves/longarun/perdaelétrica seguem
separados. Observar IP/boot/UUID reais quando precisar do console/Deck.

## Marco anterior — C78 imagem ext4 com Gambatte aprovada offline

**C78 concluído inteiramente offline.** [Implementação e limites](phase4-gambatte-image.md).
Nova ext4 privada512MiB SHA256
`a09edf63ac5397b0adc5bdf7d9eb7413f6e02e7963e569b915df0ffe674d08fc`,
com a composiçãoC75/coreGambatte no caminho nativo. Acrescenta9folhas0644 e
8dirs0755; preserva todos os3386itens C69, total3403, zero substituições.
Core3e0940da... byte-idêntico C76/C77, cuja aprovação física foi aproveitada.
Nenhum novo teste físico, SSH, escrita no cartão, reboot ou token.

**Verificação:** fsck0 sem alterarhash; releitura integral3403,18inodes
owner/modos da raiz+acréscimos,9folhas regulares/link1 passaram. Fundação97/
perfil21/payload15 e manifestos core/provider/host/store aprovados. C07/
contador0/UIoff/sessãooff/preferênciasoff antes e após extração. Auditoria
308ELFs AArch64 userspace+555módulos; ABI4.4.0/intérprete/release/features
ext4 iguais à C69.174loaders C69 reusados após conferir hashes transitivos
inalterados e ausência de acréscimos nos diretórios de busca. Probe MIT novo
compilado do fonte fixado/header extraído confirmou dlopen eager/Gambatte/
API1/conteúdo emmemória viaQEMU/A35, sem retro_init/ROM. RELRO/NOW passaram.

**Artefatos:** port/scripts/compose-phase4-gambatte-image.py e
package-phase4-gambatte-image.py; stage build/phase4/gambatte-image/image.zal39n7u,
imagem images/rootfs.ext4. Prova dist/phase4/gambatte-image sófontes/recibos,
semimagem/ELF/ROM/snapshot/UUID privado. Hashes C69/C70, inventários da base/
composição e configuraçãoSDK conferidos intactos. Primeira execução parou
antes decriar stage/imagem por exigir árvore completa ausente da provaC75;
expectativa corrigida para C69+deltaC75 congelados, sem editar provas antigas.
Licença conjunta GPLv2/GPLv3/MIT continua pendente/private-only/REDISTRIBUTE=NO.

**Console não acessado neste recorte.** Último estado observado é C77:
192.168.15.18/boot72/rootRO0755/fundação97/PCMclosed/p3off/UIoff/taint0,
infra/mounts idênticos, preferências55/70 restauradas, RAMremovida/páginaC77.
Não tratar isso como nova verificação de estado atual. Original32 e Deck não
acessados. Save C63/HEAD1/0/2 preservado pela sessão anterior; nomegambatte
ativa paletaGB-DMG verde nativa. Demora de abertura C77 segue sem medição.

**Próximo C79 proposto:** imagem privada completa de cartão com raizC78 e
bootchain/kernel/DTB/layout C70 já fixados; verificar regiões/FAT/extração/
hashes e preservar C70. Semflash/provisionamento/boot automático. Boot desta
nova imagem precisa de etapa própria; não confundir aprovação de componentes
com aprovação deboot. Caller permanente/menu geralROMs/Power/suspend/SRAM/
novos saves/longarun/perdaelétrica permanecem separados. Nenhuma sessão ou
token armado; conferir IP/boot/UUID reais quando voltar a usar o console.

## Marco anterior — C77 caller com core instalado aprovado

**C77 concluído em03/11/2026**, cartão de teste128GB/R35S,
**192.168.15.18 / boot72 / UUID observado e ligado ao C76**.
[Implementação, observações e limites](phase4-installed-core-session.md).
Host/providerC72 e coreC76 instalados foram usados pelo jogo; core ELF não é
mais copiado para RAM. Caller e argumentos fixos, guardas de40folhas e mapas
confirmam `/opt/muos/share/core/gambatte_libretro.so`. Nenhuma folha instalada
foi modificada; menu ainda usa C46 emRAM, storeC57 permanece load-only.

**Física aprovada pelo usuário:** abertura comA, Start, imagem, direcional,
som, restauração Fn+L2 e saída Fn+Start com retorno ao menu.1161frames,
hotkey/expired0/operação0/cleanup0. Metadata e seed PKST/26861bytes/CRC/PNG
byte-idênticos C63;2status/1export, inventários anteriores/depois iguais,
semQuickSave. Ao usar o nome nativo `gambatte`, adaptadores novos exportam o
snapshot para `/run/muos/storage/pickles/state/gambatte/GB/private` emtmpfs;
snapshot/identidade no cartão não foram renomeados nem alterados.

**47casos offline e check nativo do dispatcher passaram**, sem executar core
nas fixtures. C77 observa novo vínculo próprio, sem relaxar C73/C68 do71.
9folhas C76+132pré-requisitos e40folhas do dispatcher conferidos. ABIprovider4/
CLIhost e mapas menu→jogo→menu passaram. Saúde final real do72: rootRO0755/
fundação97/PCMclosed/p3off/UIoff/taint0; infra PID/starttime e mountinfo global
idênticos; preferências55/70/mixer/DRM/volume/wireplumber restaurados. Cápsulas
RAM removidas e página “C77 diagnostic finished” escrita. Sem reboot, token,
serviço/autostart, novoSave ou escrita persistente. Original32/Deck intocados.

**Observações:** usuário percebeu abertura um pouco mais lenta, sem medição
A→primeiroframe; causa permanece pendente. Paleta verde explicada: logs C73
colorization=disabled e C77=internal, ambas GB-DMG. `coredef/gambatte.c` do
hostC67 fixa internal para nome `gambatte`; nenhum core/ROM foi alterado.
CSV:59,8802Hz/3underruns/1499frames ausentes agregados, sem inferir momento
ou continuidade acústica; usuário aprovou o funcionamento. Texto piscando
anterior continua sem causa comprovada; sumiu após reboot e não foi novo
relato nesta sessão. Não repetir jogo por rotina para essas observações.

**Código/prova:** device/rk-r35s-p0/installed-core-session/ e scripts
prepare/run/check/check-native/analyze/finish/package-phase4-installed-core-session.py,
phase4_installed_core_session.py. Prova `dist/phase4/installed-core-session`,
sófontes/recibos sanitizados; semELF/ROM/estado/UUID/identidade privada.
Stages build/phase4/installed-core-session: checks.sqbqeova, observe.o6ydal_q,
native-guard.k9k1vgq9 e load.20cdfwd1. Fechamento usa recibos autênticos da
sessão72, semnovoSSH fictício. Fontes/provas históricas mantidas intactas.

**Próximo C78 proposto:** imagem ext4 offline com a composição GambatteC75,
manifesto/fsck/readback e preservação das bases C69/C70/SDK. Semflash/boot/
provisionamento automático. Medição da demora de abertura pode ser preparada
separadamente; caller permanente/menu geral deROMs/Power/suspend/SRAM/novos
saves/longarun/perdaelétrica continuam fora desta aprovação. Licença conjunta
GPLv2/GPLv3/MIT pendente, private-only/REDISTRIBUTE=NO mantidos.
Nenhuma sessão ou token armado; conferir IP/boot/UUID reais antes de retomar.

## Marco anterior — C76 core Gambatte instalado

**C76 concluído em03/11/2026**, no cartão de teste128GB/R35S,
**192.168.15.18 / boot72 / mesmo UUID observado no preparo**. Core instalado
em `/opt/muos/share/core/gambatte_libretro.so`, modo0644, SHA256
3e0940dacb9cbcdde1b55ebc0e1d275b1dc8b034bba0e235bc56b46651200a57,
byte-idêntico C49/C73/C75. [Implementação e limites](phase4-gambatte-installed.md).

Nove folhas e oito diretórios acrescentados; zero substituições. Survey novo
confirmou ausência das3raízes/temporários e pais root0755 sem symlink.
50fixtures passaram: falhas em8criações/9staging/9publicações, schema/guardas/
colisões e rollback, preservação de vizinhos inclusive sob core e dirname
BusyBox/A35 com //, sem executar core/ROM. Inspect/apply0;9hashes/modos/link1,
8dirs root0755,manifesto e132pré-requisitos preservados passaram. Probe MIT
recompilado de fontes/header fixados confirmou nativamente loader eager,
Gambatte/API1/conteúdo emmemória. Não chama retro_init nem carregaROM.

**Estado final real:** rootRO0755/fundação97/132preservados/PCMclosed/p3off/
UIoff/taint0, rede e infraestrutura PID/starttime/mounts iguais. Fingerprint
privado rede/seed/SSH/contador idêntico. Cápsula RAM removida e saúde final
conferida. SemGUI/áudio/jogo/novoSave/reboot/caller/serviço/token/autostart.
Tela continua no diagnósticoC07. Original32 e Deck não acessados; SDK/imagens
intactos. Não foi necessário repetir o jogoC73 para instalar esses mesmosbytes.

**Código:** device/rk-r35s-p0/gambatte-install/{transaction,native}.sh;
scripts prepare/run/check/package-phase4-gambatte-install.py e
phase4_gambatte_install.py. Deriva C62 congelado sem alterar fontes/provas
históricas; nova política9folhas0644/8dirs/3raízes, boot/UUID exatos e lock.
Prova `dist/phase4/gambatte-installed`, só fontes/recibos sanitizados;
semELF/ROM/tar/UUID/estado privado. Revisão conjunta GPLv2/GPLv3/MIT continua
pendente e pacote segue privado/REDISTRIBUTE=NO.

**Recuperação:** `build/phase4/gambatte-install/install.ucdyhb4b` guarda plano,
backup de ausência fsynced e tar independente nohost;0originais copiados.
Cápsula remota já removida. Não reaplicar nem executar rollback por rotina.
Recuperação explícita remove só9folhas reconhecidas e8dirs vazios registrados;
vizinhos/conteúdo inesperado são preservados. Outroboot exige novo vínculo;
rollback/perda elétrica não foram exercidos no cartão. Não restaurar seed,
contador, keys, preferências ou saves antigos para recuperar esse pacote.

**Próximo C77 proposto:** novo vínculo de sessão/dispatcher para host/provider
C72 e coreC76 instalados (9folhas adicionais), executável/caminho fixos,
sem copiar core para RAM. Guardar manifests/modos/hash e conferir mapas.
Manter C46 apenas no menu e storeC57 load-only. Validar guardas offline antes
física; o teste deve qualificar o caller novo, sem repetir C73 por rotina.
Nenhuma sessão ou token está armado. Verificar IP/boot/UUID reais antes de
qualquer novaoperação; não rodar guardas históricas71 contra72.

**Marcos preservados:** C75 receita Gambatte Buildroot defaultoff/composição
3403itens; C74 retomada no72/novoUUID após reboot do usuário, com31host/provider/
101preservados aprovados; C73 físico no71 fechado por recibos autênticos sem
novoSSH/novo jogo. Host cd67ce60... eproviderC65 instalados; CLIstoreC57 e
snapshotHEAD1/0/2 intactos. Backup17públicos C72 eminstall.otw0lflu.
Texto piscando sumiu após reboot do usuário; causa não comprovada, investigar
se reaparecer. C70 factory privada ainda semboot/provisionamento. Frontend
permanente/Power/suspend/SRAM/perda elétrica/longarun permanecem separados.

## Marco anterior — C72 provider e muxretro instalados; C73 próximo

**C72 concluído em03/11/2026:** providerC65 +hostC67 instalados seletivamente
nocartão128, IP192.168.15.10/mesmo71/UUID C68. [Implementação e limites](phase4-provider-upgrade-native.md).
5folhas substituídas(4libs+host),26novas,12metadados/licençasC60 removidos;
29dirsnovos/13antigosvaziosremovidos. 31folhas root/link1/modos/hash exatosC67.
Host instalado agoraSHAcd67ce605cfa406f6084c7348ebf27d475b73340edd981c1343f07b00a995e9d.
LibsproviderC65 no /opt/muos/frontend/lib modo0644. Metadados antigosC60ausentes;
novos /usr/share/muos-frontend-libs e /usr/share/muos-muxretro-provider.

**Saúde final real:** raizRO0755/taint0/PCMclosed/p3off/UIoff/fundação97/
101pré-requisitos preservados/manifestos válidos. InfraPIDstarttime/mounts
iguaisC68, privadofingerprint rede/seed/SSH/contador inalterado. RAMremovida,
página “C72 diagnostic finished”; semGUI/core/ROM/novoSave/reboot/serviço/token.
CLIstoreC57 passivo intacto; storeHEAD1/0/2 nãoacessado nemmodificado.
Original32 e Deck preservados. SDK/imagemC70 intactos; nenhumaimagemflash.

**Verificações:** 140casosC71 reutilizados;18fixtures adaptadorC72 passaram,
com6redirecionamentosfixos/hardwaremock. Apply0/modelonativo0/mounts0 e
4dlopen eager+hostversion/help instalados passaram. PrimeiraABIprobe falhou3
porque caller ordenouargumentos alfabeticamente, incompatível com ABI
posicionalC65 ui/common/mod/svg. Erro arquivado native-ABI-positional-failure.*;
resume-phase4-provider-upgrade.py executousóverify comordemC65/C68, sem
reaplicar/rollback. Fonteoriginal/binding intactos; nãoexecutar novamente
apply/runneroriginal porrotina. Prova dist/phase4/provider-upgrade-native
sófontes/recibossanitizados, semUUID/fingerprint/ELF/ROM/save/implantação.

**Recuperação:** build/phase4/provider-upgrade-native/install.otw0lflu
backup17públicos/plan/tar fsynced nohost; offlineprepare.agnhn2y8 também
preservado. Cápsularemotajáremovida. RollbackC62 deausência NÃO é válido
paraessenovoestado; recuperação exige nova cápsula combackupC72 e guarda
adequada, semrestaurarcontador/seed/keys/saveantigos. Rollback nativonãoexercido.

**Próximo C73:** adaptar sessão load-only para host/provider instalados31,
com vínculo novoaC72 e guards próprios, semrelaxar C68/C66 históricos de13
arquivos antigos. ReusarROM/core/lifecycle/áudio qualificados; manter variante
C46 de menus emRAM. Validar dispatcher/mapas/cleanup antesfísica. Usuário
consultado secontinua junto; perguntapendente, nãoarmarGUIsemresposta.
SemnovoSave/Power/volume/brilho/reboot; GB existente basta.

**Imagem:** C70factory640MiB image.ce6thxbu SHAf82f9ddd...93671,
rootC69b03842ff...b3e6c, C07/contador0/defaultsoff/semprovisionamento/p3/ROM.
Boot daconjunção/provisionamento ainda pendentes. Frontendpermanente/Power/
suspend/SRAM/GC/perdaelétrica/longarun separados. Continuidade autorizada
semparadasentremarcos atéusuáriopedirpausa ouinterrupçãodolimite; original32
preservado. Nenhum saldoquota legível.

## Marco anterior — C71 transação offline aprovada; C72 nativo em preparação

**C71 concluído em03/11/2026:** plano seletivo providerC65+hostC67 em
`build/phase4/provider-upgrade/prepare.agnhn2y8`, política fixa/backup17arquivos
públicos/5substituições+26adições+12remoções metadados/29dirsnovos+13antigos.
[Implementação e limites](phase4-provider-upgrade.md). Checks.tvie8_8z passou
140casos: aplicação/rollback completo, todas falhas nas etapas de diretório/
staging/publicação/remoção,guard/rw/verify/sync/ro,colisões/symlinks/hardlinks/
drift/corrupção/vizinhos. Conteúdo inesperado preservado. Fonte transação
provider-upgrade/transaction.sh; scripts prepare/check/package-phase4-provider-upgrade.
Prova dist/phase4/provider-upgrade sófontes/política/planos/recibos; backup e
ELFs/tar ficam embuild. Semremount/instalação/serviço/reboot/flash no C71.

**C72 transação concluída; verificação em retomada:** apply.result0/native-tree0/
after0/mounts-after0,rootRO/31folhas novas/ausência metadados antigos válidos.
Primeira CLIprobe falhou3 porcaller ordenar alfabeticamente argumentos do
probe C65 posicional (terceiro deve serlibmuxmod; referências UI/common
cruzadas). Nenhum defeito depayload demonstrado; não reaplicar/rollback.
`resume-phase4-provider-upgrade.py build/phase4/provider-upgrade-native/install.otw0lflu`
emcurso: somentebranch verify, ordemNAMES C65/C68, erro original preservado
native-ABI-positional-failure.*, fonteoriginal/binding/cápsula intactos.
Sóusar se aindanãoexistirinstall-analysis.json; depoisfinish e package.

**C72 APPLY INICIADO:** stage `build/phase4/provider-upgrade-native/install.otw0lflu`.
Survey vinculado ao71/UUID C68/infra exata; backup17públicos fsynced.
Checkeradaptador passou18casos. Comando apply disparado nesta retomada;
seinterrompido, inspecionar remote-directory/apply.done/result/raizRO e usar
`run-phase4-provider-upgrade.py verify --host 192.168.15.10 --stage ...`.
NUNCA repetirapply; nãoassumirinstalação concluída seminstall-analysis.json.
Não executarguardaC68 de13arquivos após mudança. Finalização/limpeza ainda
pendentes e cápsula de rollback precisa ser preservada atéfecharrecibos.

**C72 implementação:** executor run-phase4-provider-upgrade.py e adaptador
provider-upgrade-native/native.sh, guard próprio antes/depois, locklifetime,
bootUUID71 exatoC68, backuphostsincronizado, rollbacke sealRO. Ainda requer
checker do adaptador e survey vinculados antesapply; não redisparar se já
existir remote-directory. PreservarCapsula atéfechamento, depoisremoverRAM.
Não alterar fontes/provasC71/C68/C67 ou usar guardahistórica após novosbytes.

**Estado real lido durantepreparoC72:** 192.168.15.10, mesmo71/UUID C68,
rootRO0755/fundação97/payloadC62 íntegro/PCMclosed/p3off/UIoff/taint0/quiet;
final-healthC68 reutilizado como somenteleitura de drift. Nenhumaescrita
persistente nova. AindaC62host8d519958 instalado e libsantigas; C57store
passivo, snapshotHEAD1/0/2 inalterado pelo trabalho atual. Original32/Deck
nãoacessados. Todaescrita futura exige nova guarda no ponto de aplicação.

**Imagem:** C70 rawprivada640MiB image.ce6thxbu SHAf82f9ddd...93671,
rootC69SHA b03842ff...b3e6c; factoryC07/contador0/defaultsoff/semredeprivada/
seed/hostkeys/ROM/corelibretro/save/p3. Não serágravada naatualização C72;
provisionamento/boot próprios continuam pendentes. SDK/B01/C69/C70 intactos.
Frontendpermanente/Power/suspend/SRAM/GC/perdaelétrica/longarun separados.

**Continuidade autorizada:** encadear integrações sempausas entremarcos até
usuário pedirpausa/interrupção dolimite; nãoencerrar sópor fecharum marco.
Autorização128 persiste; original32preservado. Semsaldoquota legível.

## Marco anterior — C70 imagem de cartão privada concluída; C71 próximo

**C70 concluído em 03/11/2026:** imagem privada completa de640MiB em
`build/phase4/card-image/image.ce6thxbu/muos-r35s-panel0-c70-private.img`,
SHAf82f9ddd56b29765a4d852c6ef7dce0a0a6678915a4426d3c706155b77293671.
[Implementação e limites](phase4-card-image.md). MBR2partições/layout B01/
5regiões/releituraFAT6folhas/fsckFAT/gzip passaram. RootfsC69 byte-idêntico,
fsck0C69 reutilizado; kernel/DTB/UBoot/trust/idbloader B01 semrecompilação.
Verifier27fixtures checks.o9c6w_ot: corrupção/truncamento/overlap/partiçãoextra/
symlink/hardlink/gaps etc. Duastentativas falhas registradas: comparaçãoatime
corrigida; e2fsck ausente nocontainer mídia substituído porreuso C69 exato.
Fontes/recibos emdist/phase4/card-image, sempayload privado.

**Imagem factory, ainda não bootada:** C07/ro/contador0/UIoff/sessãooff/
preferênciasoff; semredeprivada/seed/hostkeys/ROM/corelibretro/save/p3.
Requerprovisionamento antesSSH; não é atualização quepreserve cartãoativo.
Nenhumwriter/flash/reboot/console/cartão/Deck acessado. SDK/C69/B01 intactos.

**Últimoestado real C68:** IP192.168.15.10/boot71/UUID C66/kernel4.4.189,
rootRO0755/97/105prereqs/13C62/PCMclosed/taint0/p3off/UIoff/prefs55/70/
infra/mounts preservados/RAMremovida/páginaC68. HostC62 instalado passivo,
CLIstoreC57 e storeHEAD1/0/2 intactos. Verificar IP/boot/estado antes SSH novo.

**Próximo C71:** preparar transação seletiva providerC65+hostC67 para cartão128,
antesqualificadosC66/C68. Cincofolhas compartilhadas(4libs+host),26novas,
12metadados/licençasC60 obsoletos; backup seletivo dos17originais públicos,
semcopiar privados/contador/seed/saves. Validar plano/rollback/falhas offline
antesde survey/escrita. Não afrouxarguardas históricas, não reusar instalador
C62 deausência para substituição. ImagemC70 não serágravada neste passo.
Frontendpermanente/Power/suspend/SRAM/GC/perdaelétrica/longarun separados.

**Continuidade autorizada:** usuário pediu integrações sempausas entremarcos
até pedirpausa ou interrupção do limite. Nãoencerrar só por concluir ummarco;
checkpoint a cada etapa, perguntas sópara informações/testes necessários.
Original32 preservado; autorização128 persiste. Nenhum saldoquota legível.

## Marco anterior — C69 imagem provider/host concluída; C70 em preparação

**C69 concluído em 03/11/2026:** composição C67 serializada na ext4 privada
`build/phase4/provider-image/image.izief28e/images/rootfs.ext4`, 512MiB,
SHAb03842ff7ce2a8ddc22948c3bd8002cef832222dd54c3b58e79ae54b587b3e6c.
[Implementação e limites](phase4-provider-image.md). fsck0/releitura3386itens/
owner root/modos60inodes+raiz/31folhas link1/manifests/C07/contador0 passaram.
BaseC56 e imagemC64 preservadas; 27files+29dirs novos,4libs existentes mudam
(2hashes/4modos),3326itens base intactos. Estático307ELFs+555módulos/ABI4.4.
Loaders mubattery/muhotkey/muxfrontend/muxretro refrescados em QEMU/A35;
170reusados sócom fechamento NEEDED/intérprete byte-idêntico C38/C56.
Prova dist/phase4/provider-image,51hashes,sófontes/recibos,semimagem/ELF/privados.
Não houve SSH/boot/escrita de cartão; componentes nativos qualificados emC68.

**Último estado real C68:** IP192.168.15.10/boot71/UUID C66/kernel4.4.189,
rootRO0755/fundação97/105prereqs/13C62/PCMclosed/taint0/p3off/UIoff,
prefs55/70/infra/mounts preservados; RAMremovida/páginaC68. HostC62 instalado
passivo e CLIstoreC57 inalterados; snapshotHEAD1/0/2 byte-exato,semnovoSave.
Não presumir IP/boot atuais antes de próxima operação remota.

**C70 em preparação:** imagem privada completa de cartão com rootfsC69,
FAT/kernel/DTB e bootchain B01 já aprovados. Reusar layout640MiB/MBR4d554432/
p1FAT100MiB@16MiB/p2ext4512MiB@128MiB; root bootstrap continuaC07 e nenhum
serviço automático extra. Não adicionar p3/store/ROM/credenciais. Releitura
integral das regiões e assets FAT, fsckFAT, contrato de boot e hashes contra
recibos imutáveis. Imagem factory ainda requer provisionamento de rede/RNG
para SSH; não gravar sobre cartão ativo nem perder seu estado atual.
Nada armado; original32 e Deck não acessados. Boot da nova imagem, frontend
permanente/Power/suspend/SRAM/GC/perdaelétrica/longarun continuam separados.

**Continuidade autorizada:** encadear integrações sempausas entre marcos até
usuário pedirpausa ou interrupção do limite; não terminar só por concluir um
incremento. Manter checkpoint e solicitar observação só para teste físico.
Nenhum saldo de quota é legível; não inferir orçamento de tokens.

## Marco anterior — C68 host C67 aprovado em RAM; C69 próximo

**C68 concluído em 03/11/2026:** ELF C67 SHA
cd67ce605cfa406f6084c7348ebf27d475b73340edd981c1343f07b00a995e9d
aprovado nativamente em RAM com provider C65 e menus C46. Usuário confirmou
“Tudo certo” para imagem/entrada/áudio/FnL2/FnStart/retorno. Host C62 instalado
8d519958... preservado; seminstalação/novosave/reboot/imagem/cartãooriginal/Deck.
[Implementação e limites](phase4-muxretro-provider-session.md).

**Estado final confirmado:** IP192.168.15.10/boot71/mesmoUUID C66, kernel4.4.189,
rootRO0755/fundação97/105pré-requisitos/13C62/taint0/PCMclosed/p3off/UIoff;
prefs55/70/mixer/DRM/brilho/volume/WirePlumber/infraPIDstarttime/mounts iguais.
RAMremovida e páginaC68. CLI C57 instalado/passivo; storeHEAD1/0/2 byte-exato.

**Código:** device/rk-r35s-p0/muxretro-provider-session; scripts
prepare/check/run/analyze/finish/package-phase4-muxretro-provider-session.py e
phase4_muxretro_provider_session.py. Deltas de fontes C66 congeladas, semeditar
histórico. Vínculos C53–C63/C65/C66/C67 verificados; exige mesmo71/UUID C66,
observação nova de IP/infra/recibos. Outro boot recusado, semadaptar automaticamente.
Worker/runner/select/store/C65/C46 iguais; 66checks C66/lifecycle reutilizados.
Novo host em capsule/host/muxretro, guard root700/link1/hash C67 fixo; pacote
instalado13folhas e7libsRAM continuam obrigatórios. Exec somenteRAM, semfallback.

**Recibos:** build/phase4/muxretro-provider-session/checks.rb4jrjgv(28casos:
11binding/syntax+17dispatcher), observe.jsyy7ay0 e load.8ef49rho. Probe4libs+
CLI do novoELF eager nativos passaram; /proc/exe e maps confirmaramRAMhost
comprovider4 e ambosmenus provider3+C46. 903frames/hotkey/expired0/op0/cleanup0,
usuário confirmou física vinculada à análise. CLIstore2status/1export,
PKST/CRC/manifesto/PNG/26861bytes, snapshots/inventários C66/C63/C61/C58/C54
iguais; zero novosave. CSV5underrun/1637frames ausentes/Hzrecente58,8813;
semqualificar FPSpor45s/deadline interno/áudiocontínuo/longarun.
Prova dist/phase4/muxretro-provider-session/SHA256SUMS,28hashes, sófontes/
recibossanitizados, semELF/ROM/estado/IDs. Final-health e ancestralidade passaram;
C65/C66/C67/SDK/imagens antigos intactos.

**C67/composição:** muxretro-provider/build.f9a1ac69/composition,3386itens;
baseC56+27files/29dirs e4libs alteradas(2hashes/4modos755→644). Target31files,
C07/contador0/defaultsoff/fundação97/manifests válidos. HostC67 agora qualificado
nesse runtimeRAM; imagem C64 continua image.n_uthilw/images/rootfs.ext4,
SHA671a738792d5a6b718d698f8386488d14216c8f539541f2b6160e1bbc98a62a6.
Recuperações C62install.67io22z3/C57install.0kvv3gdl preservadas; não repetir
instalação/rollback/C68 ou afrouxar guardas históricas por rotina.

**Continuidade autorizada:** usuário pediu encadear integrações sempausas entre
marcos até pedirpausa ou interrupção do limite; não terminar só por concluir
um incremento. Manter checkpoint a cada marco e janelas físicas via pergunta.
Não inferir saldo de limite; nenhum orçamento de tokens foi informado.

**Próximo C69:** serializar composição C67 em novo rootfs.ext4 privado offline,
fsck/readback/owners/modos/manifests/C07/contador0. Refresh loaders afetados
pelos hashes novos UI/common; reusar demais sócom bytes/deps idênticos e
recibosC38/C56. C64 e cartões intactos; semboot/flash/serviços. Nada armado.
Frontend permanente/bootimagem/Power/suspend/SRAM/GC/perda elétrica/longarun/
áudio contínuo continuam separados. GB existente basta para próximos testes.

## Marco anterior — C67 muxretro integrado ao provider Buildroot offline

**C67 concluído em 03/11/2026:** receita muos-muxretro-provider consome staging
do provider C65/C66, sem SDK privado das quatro bibliotecas muOS. Kconfig,
fontes/licenças, guardas, build, composição e CLI eager passaram offline.
Novo ELF diferente do instalado, ainda NÃO qualificado nativamente.
[Implementação, reprodução e limites](phase4-muxretro-provider.md).

**Código:** nova árvore port/buildroot-muxretro/MUOS_R35S_MUXRETRO, opção
BR2_PACKAGE_MUOS_MUXRETRO_PROVIDER defaultoff/AArch64, seleciona C65 e tem
dependência real muos-frontend-libs. Recusa coexistência com MUOS_MUXRETRO
histórico. Config.in/receitas C60/C65 e refs não editados. Scripts
build/package-phase4-muxretro-provider.py; helper usa staging/usr/lib e
--sysroot explícito em compilação/link, RUNPATH runtime/opt/muos/frontend/lib.
Sem core/ROM/save/caller/serviço/token. Novaárvore preserva Config.in fixados
nas provas; BR2_EXTERNAL inclui buildroot +buildroot-frontend +buildroot-muxretro.

**Stage:** build/phase4/muxretro-provider/build.f9a1ac69; SITE muxretro-provider/source,
1.302 textos,10licenças consumidor e982arquivos frontend compartilhados exatos
C65. Fontes C60 reutilizadas após manifesto/prova verificados, sem repetir
extração/patches; frontend5e8635b3/rcheevos2ad0b867. Legal-info archive SHA
a7a7f4093734e79d558388d1fca5c3f677e186243ec6bc5b6fc7f44417d682c7.
Provider4libs C65/C66 com hashes exatos, semrecompilar; stagingisolado é cópia
do sysroot existente +macroINSTALL_STAGING real. SDK compartilhado intacto.
Kconfig defaultoff/optin/deps, recusa i386/hostantigo; O= restaurado AArch64.
Cinco recusas de staging ausente/cada libcorrompida, antesde chamar compilador.
Kconfig/rsync/legal-info reais; build/install macros comSDK existente,
sem fullrebuild de toolchain/deps/firmware.

**Novo host:** SHA256
cd67ce605cfa406f6084c7348ebf27d475b73340edd981c1343f07b00a995e9d,
AArch64/PIE, intérprete AArch64, ABI Linux4.4.0, RELRO/NOW/RUNPATH fixo.
Version/help QEMU/A35 e LD_DEBUG confirmam4libs da composição. Difere do
C60/C62/C66 SHA8d519958...; a evidência física C66 NÃO é transferida ao novo
ELF. Nada instalado/ensaiado no console. 74warnings de truncamento,7avisos
dynsym EGL privado existente, zero erros finais; semeditar GPU/upstream.

**Composição local:** base C56 save-store-image/image.nlnmgzzb/target, antes
do host C60, evitando metadados SDK antigos inconsistentes com novaslibs.
Target31arquivos(17provider+14host), composição3.386itens =3330base+27arquivos/
29dirs novos;0remoções. Só4folhas antigas mudam: ui/common hashes novos,
4libs de0755 para0644 conforme receitaC65. Outros3.326itens base intactos.
Fundação97/payload15/perfil21/storeC57/manifests host/provider, C07/contador0/
autostartoff e CLI passaram. Nãoimagem/boot/fullrebuild; não reivindicar reuso
dos172loadersC38 para dependências diferentes. Futuracomposição de imagem
precisa validar loaders afetados além do novo host nativo.

**Primeira tentativa:** build.ispvtcnb falhou no link: scripts glibc do staging
copiado usam caminhos absolutos /lib64; faltava --sysroot explícito. Corrigido
somente helper, comrevalidação emstage novo. SITE anterior preservado em
source.before-explicit-sysroot, falha registrada; semação nativa inválida.
**Prova:** dist/phase4/muxretro-provider/SHA256SUMS,102hashes, sófontes/licenças/
recibos; semELF/rootfs/ROM/estado/imagem. C56/C60/C64/C65/C66/SDK intactos.

**Imagem e console:** C64 continua muxretro-image/image.n_uthilw/images/rootfs.ext4,
SHA671a738792d5a6b718d698f8386488d14216c8f539541f2b6160e1bbc98a62a6.
Console/cartões/Deck não acessados no C67. Últimoestado real C66/boot71/IP10,
rootRO0755/97/105prereqs/13instalados/PCMclosed/p3off/UIoff/taint0/prefs55/70,
storeHEAD1/0/2 e páginaC66; não presumir contador/IP atuais. C62host8d519958
e C57CLI instalados/passivos. Original32 preservado. Recuperações:
muxretro-install/install.67io22z3 e save-store-install/install.0kvv3gdl.
Não repetir instalações/rollback/C66 por rotina, nem usar guardaC63 contra71.

**Próximo C68 proposto:** qualificar novo host C67 emRAM com providerC65,
menusC46 e CLIstoreC57 load-only, sem substituir host C62. Primeiro verificar
estado atual/boot/UUID porSSH fixado/alias17; usar observação exata, adaptando
vínculo em incremento próprio se mudou. Guard deve permitir só ELF C67
fixado na cápsula, sem fallback/argslivres; manter pacote instalado íntegro.
GB existente/FnL2/FnStart/semnovo save; nenhumteste físico armado.
Frontend permanente/bootimagem/Power/suspend/SRAM/GC/perda elétrica/longa
duração/áudio contínuo seguem separados.

## Marco anterior — C66 bibliotecas frontend aprovadas em RAM no boot 71

**C66 concluído em 03/11/2026:** provider C65 passou no console em RAM:
menu → GB → Fn+L2 → Fn+Start → menu. Usuário confirmou “Tudo certo!” para
imagem/entrada/áudio/restauração/retorno. Sem instalar bibliotecas, salvar,
solicitar reboot ou alterar C64. [Implementação e limites](phase4-frontend-libs-session.md).

**Estado real final:** IP192.168.15.10, kernel4.4.189-muos-r35s-p4, boot71/UUID
novo observado (diferente do70/C63), rootRO0755, fundação97,105pré-requisitos,
13arquivos C62 válidos, PCMclosed/taint0/p3off/UIoff, infraestrutura PID/starttime
e mounts globais preservados, prefs55/70/mixer/DRM/volume/brilho/WirePlumber
iguais, RAM removida. Página “C66 diagnostic finished”. Host C62 e store C57
instalados/passivos; original32 e Steam Deck não acessados. C65 não instalado.

**Novo vínculo, sem relaxar C63:** módulo phase4_frontend_libs_session.py usa
prefixo offline do runner C63 congelado antes de qualquer SSH/alocação. Todos
os vínculos C53–C63 são validados com boot70 histórico; C66 exige observação
separada71, UUID exato, IP, recibos C63/C65 e infra. Três testes do contador
derivados para71 + UUID em cada operação remota. Não executar C63 contra71;
ele permanece exigindo70/UUID antigo. Histórico/source assets/identidade e
inventários store C54/C58/C61/C63 foram novamente amarrados no fechamento.

**Código/delta:** device/rk-r35s-p0/frontend-libs-session e scripts
prepare/check/run/analyze/finish/package-phase4-frontend-libs-session.py.
Worker/runner/session/select/store originais mantidos, lifecycle C45 e104checks
C63 reutilizados sem replay. Launcher só define LD_BIND_NOW/provider-lib para
app; dispatcher C63 mantém13hashes e acrescenta guard C66 de7folhas RAM,
hash/mode700/root/link1/dirs700/tmpfs/sem symlinks e ambiente exato em launch.
Sem ELF muxretro/save-store na cápsula, host executa absoluto instalado.

**Escopo das bibliotecas:** menus usam C65 ui/muxcom/plutosvg + libmuxmod C46
diagnóstica em capsule/lib; jogo usa as4C65 em capsule/provider-lib. Serviços
mantêm libs originais do worker. Probe RTLD_NOW4libs e CLI instalada version/help
nativos passaram. Mapas /proc +exe confirmaram ambos menus e jogo, sem inferir
carregamento só pela presença do arquivo. C65libui639c1df8 e muxcom2913dbf7,
antes nãoqualificadas, agora aprovadas nesse runtime RAM; modbfd909c6/pluto99377c31
iguais à fundação, C46 variante separada.

**Recibos:** observe._b95qe9h; checks.d8df13w5 (66cases =27binding/delta/syntax+
39guard RAM, semhardware/core/ROM); load.o2agwm0q, todos em
build/phase4/frontend-libs-session. Física vinculada ao hash da análise.
1.732frames/saída hotkey/expired0/op0/cleanup0, retorno20s; não houve repetição
nativa ou extensão da janela. CLIstore2status/1export, PKST/CRC/manifesto/PNG/
26861bytes e storeHEAD1/0/2 byte-idênticos à cadeia C63/C61/C58/C54.
CSV5underruns/1737frames ausentes semtimestamps; Hzrecente59,9401, média16,6828ms.
Som limpo confirmado no teste curto, semqualificar áudio contínuo/deadline
interno/estabilidade prolongada ou FPS por frames/45.

**Prova:** dist/phase4/frontend-libs-session/SHA256SUMS,28hashes, só fontes/
recibos sanitizados; sem ELF/ROM/estado/PNG/PCM/INI/identidade/UUID/hash da ROM.
Primeira composição do trecho Python acusou indentação no preparo offline;
corrigida por AST/shell antes de observe/run, sem execução nativa inválida.
Final-health confirmou quiescência e auditoria; C63/C62/C65/C64/SDK intactos.

**Imagem/recuperação:** C64 permanece muxretro-image/image.n_uthilw/images/rootfs.ext4,
SHA671a738792d5a6b718d698f8386488d14216c8f539541f2b6160e1bbc98a62a6,
sem libs C65/flash/boot. Recuperações C62 muxretro-install/install.67io22z3 e
C57 save-store-install/install.0kvv3gdl preservadas. Não repetir install/rollback,
teste que exige host ausente ou C66 aprovado por rotina. .config SDK inalterado.

**Próximo C67 proposto:** receita consumidora muxretro dependente do provider
C65, com fontes/headers/hashes qualificados e staging/link/composição offline.
Usar nova receita/Config.in na árvore port/buildroot-frontend, sem reescrever
C60 histórica nem substituir componentes instalados. Novo host com bytes
diferentes exige qualificação própria; não repetir GB para bytes iguais sem razão.
ROM GB atual é suficiente; pedir outras apenas ao qualificar outros cores.
Nada C67 armado. Sessão manual no novo boot observada, sem determinar origem
desse reboot ou aprovar startup automático. Frontend permanente/bootimagem/
Power/suspend/SRAM/GC/perda elétrica/longa duração/áudio contínuo separados.

## Marco anterior — C65 provider das bibliotecas frontend aprovado offline

**C65 concluído em 03/11/2026:** receita opt-in das quatro bibliotecas frontend,
compiladas de fontes limpas e sem SDK privado pré-compilado muOS. Kconfig,
rsync/legal-info, target/staging, ABI e loader/CLI passaram. Nenhuma alteração
no console, cartões, Steam Deck ou imagem C64.
[Implementação, reprodução e limites](phase4-frontend-libs.md).

**Código:** port/buildroot-frontend é uma segunda árvore BR2_EXTERNAL,
MUOS_R35S_FRONTEND, compatível com a histórica port/buildroot. Opção
BR2_PACKAGE_MUOS_FRONTEND_LIBS default off/AArch64; sem selecionar SDK privado,
C60, serviços ou boot. Helpers build/package-phase4-frontend-libs.py,
phase4-frontend-libs.mk e probe phase4-frontend-libs-load.c. Config.in/receitas
C60 e refs não modificados. C60 ainda usa seu SDK fixado; a nova receita é
provider das quatro libs, não integração completa do consumidor/firmware.

**Stage concluído:** build/phase4/frontend-libs/build.84o1r4aj; SITE
frontend-libs/source, 1.274 textos/1.195 frontend iguais à fundação. Origem
frontend5e8635b3 + mojibake0.3.6; patches0003/0006, onze licenças incluindo
LVGL/LICENCE e mojibake MIT. Sem patches0010/0011/variante C46, objetos ou
ELFs prévios no SITE/legal-info. Archive legal-info SHA
b18feeda16c9e276ab7a0d102674db1649531b84192aa991299b3e5c93a0ff02.

**Resultados:** configuração real defaultoff/optin/deps e recusa i386;
rsync+legalarchive exatos. Build/install macros reais com SDK existente,
sem fullrebuild das dependências/toolchain. Target17arquivos:4libs+11licenças+
proveniência+manifesto. Staging isolado4libs em usr/lib, sem escrever SDK;
headers do consumidor devem ter revisão/patches iguais. O= termina no teste
i386; opt-in.config preserva AArch64, não usar .config desse O= como firmware.
AArch64/shared/RELRO/NOW/NEEDED/exports/tamanhos globais/versões GLIBC iguais
à fundação, RUNPATH ORIGIN onde existente. QEMU/A35 RTLD_NOW confirmou os
quatro caminhos novos e muxretro C60 version/help com as novas libs.

**ELFs novos diferentes e NÃO qualificados nativamente:** libui.so
639c1df8c75dc5007abfb87817d8cb1ea6b3ed7e0366f008e976a0e74491791e;
libmuxcom.so 2913dbf7d901a258d338995e0d937c2f6559465c41a3bd0e097072820f57cd21.
libmuxmod.so bfd909c6... e libplutosvg.so 99377c31... idênticas à fundação,
sem substituir a variante diagnóstica C46. As duas compilações limpas C65
produziram os quatro ELFs iguais entre si; não determina a causa da diferença
para os dois ELFs históricos nem aprova GUI/áudio/boot. 254 warnings upstream
(253 truncamentos+1 macro), zero erros; sem limpeza de fontes fora do escopo.

**Primeira tentativa:** build.fr0v680t compilou, mas probe abriu libui isolada
e recusou mux_tick. Correção só no probe: carregar libmuxmod primeiro resolve
UI/common como grupo, sem stubs nem mudanças nas bibliotecas. Não converter
a primeira falha de probe em aprovação; logs mantidos. Prova final
**dist/phase4/frontend-libs/SHA256SUMS, 96 hashes**, só fontes/licenças/recibos,
sem ELF/ROM/estado/imagem. Provas C60/C62/C63/C64 e .config SDK intactas.

**Imagem e estado vivo anteriores:** imagem C64 permanece em
muxretro-image/image.n_uthilw/images/rootfs.ext4, SHA
671a738792d5a6b718d698f8386488d14216c8f539541f2b6160e1bbc98a62a6,
sem overlay das libs C65, boot ou flash. IP192.168.15.10 informado pelo
usuário, não verificado neste incremento. Última saúde real C63/boot70/IP14,
rootRO/hostC62 e storeC57 passivos/p3off/UIoff/prefs55/70/storeHEAD1/0/2.
Não inferir estado ou contador atual pelo IP. Guardas C63 seguem fixadas ao
boot70/UUID; não afrouxá-las ou repetir install/rollback por rotina.
Recuperações: muxretro-install/install.67io22z3 e
save-store-install/install.0kvv3gdl preservadas. Original32 intocado.

**Próximo C66 proposto:** qualificar as novas bibliotecas em RAM no runtime
supervisionado, mantendo override C46 dos menus e host instalado. Primeiro
inspecionar estado real via SSH fixado/alias17 no IP atual; se outro boot,
adaptar o caller com novos vínculos em incremento próprio. ABI/CLI offline
não autorizam substituição dos ELFs qualificados. Depois, receita consumidora
com dependência no provider e hashes fixados, preservando a C60 histórica.
Nada C66 armado. Provider completo/frontend permanente/boot da imagem/
Power/suspend/SRAM/GC/perda elétrica/longa duração/áudio contínuo separados.

## Marco anterior — C64 imagem privada com muxretro aprovada offline

**C64 concluído em 03/11/2026:** imagem ext4 privada de 512 MiB com C56 +
13 arquivos/13 diretórios C60/C62. Fsck, releitura integral e contrato C07
passaram, sem acessar console, cartões ou Steam Deck. Não houve boot/flash.
[Artefato, reprodução e limites](phase4-muxretro-image.md).

**Imagem:** build/phase4/muxretro-image/image.n_uthilw/images/rootfs.ext4,
SHA256 `671a738792d5a6b718d698f8386488d14216c8f539541f2b6160e1bbc98a62a6`.
É rootfs, não imagem completa de cartão/FAT/bootloader. Base C56 permanece
em save-store-image/image.nlnmgzzb/images/rootfs.ext4, SHA07a18d14ef54c91b7e463a016155165deff33296fdf833b8dbca51ff38780ef6.
Composição fonte: muxretro-package/build.mdou4mqr/composition. Provas
C56/C60/C62/C63 e ligações de hashes/modos conferidas antes da escrita local.

**Código e verificações:** compose/package-phase4-muxretro-image.py, sem
alterar C56 ou compositores históricos. Container existente sem rede; só
arquivo regular novo recebe debugfs-w, sem mount/loop/bloco/SSH/init.
e2fsck-fn0; rdump 3.356 itens exatos, preservando os 3.330 itens C56.
Root0755/uid0/gid0 e 26 novos inodes com modos/owners conferidos; 13 folhas
regulares/link1. Fundação97/payload15/perfil21, manifestos store/host e quatro
links privados válidos. Gate C07 antes/depois, contador de fábrica0/defaults
automáticos desativados, sem tokens/seeds/credenciais/dados privados gerados.
Estático: 307 ELFs userspace +555 módulos AArch64/4.4.189-muos-r35s-p4,
glibc ABI4.4.0/intérprete AArch64; ROOTFS/512MiB/features3c/242/46b iguais C56.

**Reuso e escopo:** bytes do host SHA8d519958cdb1ae599e2b2af2f6ee90053bca1a83cce0380baa3a1d7150983f05
iguais C62/C63, sem recompilação/fullrebuild. Loaders C38(172), storeC56(1)
e hostC60(1) reutilizados para mesmos bytes/deps; nenhum loader/UI/jogo foi
reexecutado. Evidência nativa C63 permanece dos componentes, não do boot da
imagem. Caller/dispatcherC63, lib diagnósticaC46, core/ROM/save comercial e
preferências do128 não entram. Host/store ficam instalados/passivos. SDK
privado/provider incompleto e pendências de licença gráfica continuam; imagem
só em build/, não aprovada para redistribuição. Reprodutibilidade binária de
datas/metadados ext4 não qualificada. Nenhuma inicialização nativa da imagem.

**Prova:** dist/phase4/muxretro-image/SHA256SUMS, 37 hashes, só fontes/recibos/
comandos/auditoria; sem imagem/ELF/ROM/estados. Imagem/árvores de origem,
provas C56/C60/C62/C63 e .config compartilhado SDK intactos.

**Console e novo IP:** usuário informou **192.168.15.10** nesta retomada;
não foi conferido por SSH no C64. Última saúde verificada é C63/boot70,
então IP14: rootRO0755/97/105prereqs/13instalados/taint0/PCMclosed/p3off/UIoff,
prefs55/70/storegen1HEAD1/0/2 intactos e páginaC63. Não inferir boot/UUID/saúde
atual pela mudança de IP. Antes de nova ação física, reler estado real com
SSH fixado/alias17; não afrouxar vínculos antigos se outro boot for observado.
Original32/128/Deck não acessados no C64; sem remount/token/save/reboot.

**Operações de recuperação anteriores:** não repetir C62prepare/apply ou
rollback por rotina. Preservar build/phase4/muxretro-install/install.67io22z3
(tar/plan/manifest/absence-backup); C57 em save-store-install/install.0kvv3gdl.
Não usar saúdeC61 que exige host ausente nem sobrescrever a raiz viva com a
imagem C64. C63 aprovado em load.szcr_1jo; primeira janela load.2_wgmc5y
expirou sem jogo e teve erro de análise de log ausente após cleanup seguro.
Essa limitação de coleta em cancelamento está documentada no marco C63;
não converter timeout em aprovação ou redisparar sem inspecionar.

**Próximo C65 proposto:** preparar integração Buildroot das quatro bibliotecas
muOS ainda exigidas pelo SDK privado C60, com origem/licenças/patches/deps/ABI
fixados. Distinguir fundação e variante C46 dos menus; stages offline separados,
sem substituir bytes qualificados. Novo ELF diferente exige qualificação
própria antes de instalar. Nada C65 armado. Provider completo/frontend
permanente/boot da imagem/host após novo boot/Power/suspend/SRAM/GC/perda
elétrica/longa duração/áudio contínuo permanecem separados.

## Marco anterior — C63 diagnóstico com host instalado aprovado; console70 seguro

**C63 concluído em03/11/2026:** diagnóstico executou hostC62 e CLIstoreC57
instalados, sem enviar ELF muxretro/store na cápsula. Usuário confirmou
“Tudo certo” para imagem/direcional/som limpo/FnL2/FnStart/retorno.104checks e
nativo aprovados, semnovo save/reinstalação/reboot/autostart.
[Implementação, escopo e provas](phase4-installed-host-session.md).

**Código/vínculos:** installed-host-session/{installed-host,app-launch,
stopped-screen}.sh + module phase4_installed_host_session e scripts
prepare/check/run/analyze/package-phase4-installed-host-session.py. Delta
exato C61congelado, preservando vínculos históricos C53/54/58/59/61 e exigindo
mesmo contador inteiro70 E UUID C61/C59, mais plano/reciboC62 exatos. Remove
muxretro dos arquivos/hashes antes de transferir; save-store segueausente.
Novo app-launch muda sólinhafinal e seu hash no seletor. Guard aceitaapenas
check/launch/cápsula, rootfixo/, execabsoluto comflags45s/hotkey/fresh fixas.
Valida13hashes/modos/nlink1/owner/pais semsymlink, manifestoinclusive, rootRO,
cápsulatmpfs/root700/roleload600 e conteúdoRAM400 igualàROM. Semfallback.

**Checks:** checks.ju_b1x85 (build/phase4/installed-host-session),104casos:
45vínculo/recusa e59dispatcher (13folhas hash/modo/symlink, pais, hardlinks,
hostausente/RAMalternativa/args/role/rootRW/tmpfs/conteúdo/core). Fixtures só
filesystem sintético/mountmock/execregistrado; semhost/core/ROMcomercial.
BusyBoxA35 dirname exercitado. Primeirofixture corrigiu escrita de corrupção
em arquivo400 semDAC_OVERRIDE; semhardware nessa tentativa. C58/C45 estáveis
reutilizados, semreplay de serviços/falhas aprovados.

**Nativo aprovado:** load.szcr_1jo, mesmo C07/70/IP192.168.15.14:2222/UUIDC61.
Guard check0 e launch único; /proc/PID/exe observado em
/opt/muos/frontend/muxretro (SHA8d519958cdb1ae599e2b2af2f6ee90053bca1a83cce0380baa3a1d7150983f05).
954frames/hotkey/expired0/operação0/cleanup0, primeiroframe/loadFnL2/retorno
técnicos e físicos aprovados. PKST/CRC/manifesto/PNG/26861bytes válidos, CLI
instalado2status/1export; store geração1/HEAD1/0/2 e inventários byte-idênticos
C61/C58/C54 e antes/depois. Semnovo save/commit/estado comercial coletado.
CSV5callbacks/2091frames ausentes semtimestamps/causa; Hzrecente59,9401 e
médiaframe16,6783ms NÃO são FPS absoluto/throughput. Não dividir954por45s.
Som limpo no teste curto, sem áudio contínuo/deadline interno qualificados.

**Primeira janela:** load.2_wgmc5y expirou semseleção/jogo; usuário pediu
reabrir semaumentar duração. Cleanup0/rootRO/mounts/RAMremovida conferidos
antes da repetição. Coletor herdado tentou ler store-verify.log ausente após
cleanup; NÃO foi aprovação. timeout-analysis.json separado registra ausência
do jogo/limitação de análise em cancelamento; seocorrer, inspecionar antesde
redisparar, semafrouxar validações. Segunda rodada usa mesma duração.

**Final conferido:** rootRO0755/fundação97/105prereqsC62/13instalados válidos,
taint0/PCMclosed/p3off/UIoff. Prefs55/70/mixer/DRM/brilho/volume/WirePlumber/
infraPIDstart/mounts globais preservados. Runtime/ROM/core/estado/helpersRAM
removidos; hostC62 e CLIstoreC57 passivos, páginaC63 enviada. SeleçãoC46RAM
aplicada aosmenus; hostherda libs padrão do worker, comoC62documentou.
Nenhuma instalação/escrita rootfs/save/reboot/token; original32/Deck não
acessados. Prova dist/phase4/installed-host-session sófontes/recibos sanitizados,
comtimeout separado, semELF/ROM/estado/PNG/INI/PCM/identidade/hashROM/bootUUID.
C60/C61/C62 e .configSDK intactos; diagnóstico/caller ainda sóRAM.

**Operações:** não repetir C62prepare/apply/rollback porrotina. Recuperação
C62 em build/phase4/muxretro-install/install.67io22z3 (preservar tar/plan/
manifest/absence-backup); C57 em save-store-install/install.0kvv3gdl. Saúde
C61queexigehostausente nãoaplica. Store origem68/recibos69 retido sóno128,
não apagar/repetirprepare/save comercial. ImagemC56 privada/nãoflashada.

**Próximo C64 proposto:** imagemext4 privada offline com arquivos C56+C60/C62,
usando composição build/phase4/muxretro-package/build.mdou4mqr/composition
(baseC56+13arquivos/13dirs,3356itens). Fixar provas C56/C60/C62/C63 e imagens
de origem; conferir inventário/readback/fsck/contratoC07/contadorfábrica0/
manifests/modos/owners. Semcore/ROM/save/callerC63 no payload, autostartOFF;
reusar loaders para bytesiguais, sem fullrebuild/flash/SSH/reboot nessaetapa.
NadaC64armado. Provider completo/frontendpermanente/novo boot dohost/boot da
imagem/Power/suspend/SRAM/GC/perdaelétrica/longaduração/áudiocontínuo separados.

## Marco anterior — C62 muxretro instalado passivamente; console70 seguro

**C62 concluído em 03/11/2026:**13arquivos/13diretórios C60 instalados no128,
zero arquivos existentes substituídos.61fixtures + inspect0/apply0/CLI nativa
version/help aprovados, raizRO e p3desmontada. Semnova GUI/save/reboot/token.
[Implantação, contrato e recuperação](phase4-muxretro-installed.md).

**Payload/procedência:** /opt/muos/frontend/muxretro0755, três metadados em
/usr/share/muos-muxretro e nove avisos de licença em /usr/share/licenses/
muos-muxretro0644. Folhas root:root/nlink1, novosdirs0755; bytes exatos C60,
host SHA8d519958cdb1ae599e2b2af2f6ee90053bca1a83cce0380baa3a1d7150983f05.
Pacote C60 e confirmação C61 vinculados antes do plano. Nenhuma lib/core/ROM/
save/serviço/caller/boot hook instalado. Provider completo continua pendente.

**Código/testes:** muxretro-install/{transaction,native}.sh e scripts
run/check/package-phase4-muxretro-install.py. Política exata separada doC57,
pai compartilhado + dirs aninhados, journaldecriação e rollbackinverso.
61fixtures emcontainer incluem falha emcada13mkdir/13staging/13publicações,
recusas hash/modo/schema/symlink/pais/destinos/fundação, rollback exato,
conteúdo/vizinhos/temporário inesperados preservados e dirnameBusyBoxA35//.
Nenhuma falha injetada/rollback físico no cartão; sem dependências nohost.

**Plano/backup/recuperação:** build/phase4/muxretro-install/install.67io22z3.
Preservar plan.json, absence-backup.json, manifest.json e deployment.tar;
fsynced nohost antesdeRW. Backup registra ausência13folhas/13dirs, zero
originais copiados; NÃO backup integral. Nativevalida105pré-requisitos:
fundação97 +quatro libsC38 +quatro arquivosC57; manifesto publicado97 intacto.
Lifetime lock/mídia128/CID/capacidade/kernel/modelo/PARTUUID/RO/quiescência,
schema/ausência repetidos antesdeRW; noclobber+hardlink exclusivo, sync/RO.
Fingerprint network/seed/SSH/contador comparado sóemRAMremota, nãocoletado.
Trap selaRO mesmo se conteúdo/temporário inesperado impedir rollback;
recuperação explícita exige validação, não apagar conteúdo divergente.

**Nativo final conferido:** C07/boot70/IP192.168.15.14:2222/aliasSSH17,
rootRO0755/fundação97/taint0/PCMclosed/p3off/UIoff, infraestrutura PID/starttime
e mountsglobais antes/depois idênticos.13hashes/modos/links/dirs e105prereqs
passaram, CLI instalada comLD_BIND_NOW e libs padrão respondeu interface1/help.
CapsulaRAM removida; hostC62 e CLIstoreC57 passivos. PáginaC61 anterior fica.
Prefs55/70/storegen1HEAD1/0/2 são últimoestadoC61, semmontagem/acesso noC62;
nenhum novo save/estado comercial coletado. Original32/Deck nãoacessados.
Prova dist/phase4/muxretro-installed sófontes/plano/recibos, semELF/tar/ROM/
estado/PNG/PCM/fingerprint/segredos. C60/C61/C57 e .configSDK intactos.

**Escopo runtime:** GUI C61 permanece aprovação dos mesmos bytes emRAM,
semnovo jogo porrotina. Precisão porcomponente: worker herda libs padrão;
select.sh aplica libmuxmodC46RAM(hash1ec8acd9) aos menus muxfrontend, enquanto
app-launch herda libs padrão. ProbeCLI C61 também testou override, C62 testou
CLI instalada com libs padrão. Nãoinferir GUI/caller/autostart instalado.
Deadline interno/áudiocontínuo/reboot dohost/imagem nãoqualificados.

**Retomada/operações:** NÃO repetir prepare/apply ou rollback porrotina.
verify apenaspara aplicação pendente comcápsula; final-health.sh do stageC62
éRO/independente decápsula, fixa boot70. Nãoexecutar saúdeC61queexigehostausente.
Rollback se necessário: run-phase4-muxretro-install.py rollback --host IP
--stage build/phase4/muxretro-install/install.67io22z3 (usa bytesarquivados).
BackupC57 anterior continua em save-store-install/install.0kvv3gdl.

**Próximo C63 proposto:** diagnóstico usa hostC62 instalado, commanifesto/
hash/modos/pais e recibos fixados; semcópia muxretro na cápsula/fallback.
Manter seleçãoC46RAM, CLIstoreC57/loadonly/rootRO e assetsC61. Preparar
recusas/vínculo próprio e ler IP/boot reais antesde sessãoGBsupervisionada
FnL2/FnStart/retorno, semnovo save. NadaC63armado. Bootimagem/frontendpermanente/
novohostapósreboot/Power/suspend/SRAM/GC/perdaelétrica/áudiocontínuo separados.

## Marco anterior — C61 host C60 aprovado em RAM; console70 seguro

**C61 concluído em 03/11/2026:** novo ELF da receita C60 executou GB no R35S,
com CLI C57 instalado e backend load-only C58. Usuário confirmou “tudo certo”
à pergunta explícita de imagem/direcional/som/restauração FnL2/saída FnStart/
retorno.52checks e ensaio nativo aprovados, seminstalar host/novo save/reboot.
[Implementação, escopo e provas](phase4-muxretro-package-session.md).

**Vínculo/implementação:** module phase4_muxretro_package_session + scripts
prepare/check/run/analyze/package-phase4-muxretro-package-session.py e página
final própria. Renderer deriva exatamente do C59 congelado. Primeiro mantém
C53assets68/C54-C58origem69/C59boot70 com host antigo; sódepois substitui
payload pelo ELF C60 e valida prova/manifests/proveniência. Exige mesmo
contador E UUID C59 antes de alocar RAM; guardas antigas intactas.
52casos de recusa/vínculo/delta + loader eager A35/QEMU com override passaram
em checks.ds8r19g3. Dispatcher34/lifecycleC45 reutilizados para bytes iguais.

**ELF/runtime qualificado:** SHA256
`8d519958cdb1ae599e2b2af2f6ee90053bca1a83cce0380baa3a1d7150983f05`,
build C60 build.mdou4mqr, fontes originais/licenças descritas no marco abaixo.
Quatro links SDK C38 conferidos no rootfs, mas runtime usa libmuxmod C46 RAM
hash1ec8acd9 da seleção diagnóstica, comoC59. Esse override faz parte do escopo;
não presumir que o pacote isolado reproduz o ensaio. Core/ROM/runner/worker/
inspetor/scripts/library restantes iguaisC59. Novo ELF passou --version/help
eager no R35S antes de serviços/gráficos. Checks do host antigo são históricos,
não aprovação reaproveitada para novos bytes. Provider completo ainda pendente.

**Nativo:** load.upr3y148 em build/phase4/muxretro-package-session, mesmo
C07/boot70/IP192.168.15.14:2222/UUID C59.1197frames/hotkey/expired0/operação0/
cleanup0; primeiroframe, FnL2/load real e retorno ao menu aprovados. Dois
status/umaexport peloCLI instalado, sem enviar ELFstore. PKST/CRC/manifesto/
assinaturaPNG/26861bytes válidos. Geração1/HEAD1/0/2 e storebyte-idênticos
C59/C58/C54 e antes/depois; nenhum commit/novo save/estado comercial coletado.
CSV4callbacks/1932frames ausentes, semtimestamps/causa; core_hzrecente59,9401 e
médiaframe16,6833ms não são FPS absoluto/throughput da sessão. Não dividir1197
por45s (saída voluntária). Som limpo no teste curto, sem áudio contínuo aprovado.
Deadline interno novo não exercitado; runner externo inalterado limita sessão.

**Final conferido:** rootRO0755/fundação97/taint0/PCMclosed/p3desmontada,
prefs55/70/mixer/DRM/brilho/volume/WirePlumber/infra/mounts globais preservados.
RAM/ROM/core/host/estado/helpers removidos, nenhuma UI/serviço temporário ativo;
página C61 enviada. /opt/muos/frontend/muxretro ausente; pacoteC57 passivo.
Semreboot/tokenC12-C25/escrita rootfs/preferências/save; original32/Deck não
acessados. Backup C57 em build/phase4/save-store-install/install.0kvv3gdl;
store origem68/recibos69 retido sóno128, não apagar/repetirprepare/save.
Prova dist/phase4/muxretro-package-session sófontes/recibos sanitizados, sem
ELF/ROM/estado/PNG/INI/PCM/identidade/hashROM/bootUUID. C59/C60/C58 e SDK intactos.

**Próximo C62 proposto:** preparar implantação seletiva dos13arquivos C60,
inventário/ausência prévia/backup/rollback e guardas, mantendo ativação manual.
Tratar explicitamente dependência runtime C46 e scope aprovado, antesde
aplicar; instalar sóELF não implica frontend permanente. Autorização existente
para alterações planejadas no128 permanece; reler estado real/IP/boot antes.
NadaC62armado. Provider completo/bootimagem/novohostapósreboot/frontendpermanente/
Power/suspend/SRAM/GC/perdaelétrica/longaduração/áudiocontínuo permanecem separados.

## Marco anterior — C60 receita muxretro aprovada offline; novo ELF aguardava teste nativo

**C60 concluído em 03/11/2026:** receita Buildroot opt-in do host muxretro,
desativada por padrão e dependente de SDK privado explícito. Kconfig, rsync,
legal-info, compilação limpa, ABI/loader A35/QEMU e composição aditiva passaram.
[Implementação, reprodução e limites](phase4-muxretro-package.md).

**Fontes e fronteira:** `port/buildroot/package/muos-muxretro/` e scripts
build/package-phase4-muxretro-package.py. Frontend fixado em5e8635b3, rcheevos
2ad0b867; patches0003/0006/0007/0008/0009/0012/0015 + diagnostic-exit.h.
1.195 fontes/build/licenças frontend coincidem em lista/hash com C50; SITE
legal contém1.300 arquivos textuais, nove licenças/hash GPL/MIT/BSD/Unlicense.
Arquivo legal real coincide byte a byte com SITE, semELF/objetos/blobs.
SDK externo fixa libui/libmuxcom/libmuxmod/libplutosvg C38. Kconfig exige
BR2_MUOS_PRIVATE_FRONTEND_SDK; provider completo das bibliotecas ainda pendente.
Receita declara deps padrão; SDK ausente/adulterado recusa antes do compilador.

**Build/composição:** `build/phase4/muxretro-package/build.mdou4mqr`, pointer
latest-build. ELF AArch64/PIE/ABI4.4.0/RELRO/NOW, RUNPATH apenas
/opt/muos/frontend/lib; loader eager A35/QEMU e --version/--help passaram.
SHA256 `8d519958cdb1ae599e2b2af2f6ee90053bca1a83cce0380baa3a1d7150983f05`
**difere do C50 aprovado no console**. Não transferir aprovação nativa dos
bytes antigos; causa da diferença/reprodutibilidade bit a bit não qualificadas.
Warnings upstream e dynsym do EGL/SDK preservados; sem promessa de build
livre de avisos ou de GPU validada. Sem fullrebuild Buildroot/provider novo.

Macro real instala13arquivos/13diretórios numa cópia C56, preservando todos
os3.330itens anteriores: host0755, nove licenças e três metadados0644; payload
cobre12arquivos. Manifests host/store e linksSDK conferidos, fundação97/
payload15/perfil21/contador0/defaultsoff/contratoC07 preservados. Nenhum core,
ROM/save/writer/serviço/autostart/biblioteca de plataforma no payload novo.
Sem imagem nova, instalação no cartão ou sessão/boot nativo. Compositores
históricos podem recusar o menu estendido por suas guardas; C60 usa adaptador
próprio sem alterar/relaxar suas fontes ou provas. Prova dist/phase4/muxretro-package
contém fontes/licenças/metadados, semELF/SDK/rootfs/conteúdo/estados. C50/C59/C56
e .config compartilhado conferidos intactos; lint magic segue indisponível.

**Console não consultado no C60:** último estado verificado é C59/C07/boot70/
IP192.168.15.14:2222/aliasSSH17, rootRO/quiescente/p3desmontada/C57passivo.
Não assumir IP/boot atuais sem conferir. Store geração1 HEAD1/0/2, origem68,
recibosC54/C58do69 e leituraC59no70; não apagar store ou repetir prepare/save
por rotina. Backup/rollback C57: build/phase4/save-store-install/install.0kvv3gdl.
Imagem C56 privada/nãoflashada; boot da imagem não qualificado. C60 não
acessou cartões, console ou Deck; original32 permanece fora do fluxo.

**Próximo C61 proposto:** qualificar o ELF C60 em RAM com adapter/recibos
próprios antes de instalar. Primeiro reler estado real/IP/boot e hashes;
preservar C59 e seus vínculos, sem afrouxar guarda se o boot mudou. Sessão GB
limitada/supervisionada para imagem/entrada/áudio/FnL2/FnStart/retorno,
backend instalado em leitura, semnovo save. Instalação seletiva/recuperação
sódepois dessa qualificação. Nada armado. Provider completo/frontendpermanente/
bootimagem/Power/suspend/SRAM/GC/perdaelétrica/áudiocontínuo/NES seguem separados.

## Marco anterior — C59 restauração GB com CLI instalado aprovada; console70 seguro

**C59 concluído em 03/11/2026:** sessão Game Boy usou CLI C57 instalado,
sem enviar outra cópia do store. Usuário restaurou comFnL2 e saiuFnStart,
confirmando “Tudo certo” à pergunta específica de posição/retorno.29checks +
nativo aprovados, semnovo save/instalação/reboot pedido peloagente.
[Implementação, proveniência e resultado](phase4-gb-installed-session.md).

**Boot/proveniência:** retomada já encontrou C07/boot70 (C54/C58 eram69).
Novo módulo phase4_gb_installed_session exige C54/C58 explícitos coincidentes
comprovas, mesmaidentidade/assets, reciboleituraC58RO/cleanup/RAM/root/mounts/
semwrites/CLIinstalado e current=origem69+1. C53sameboot68 e C54regra68→69
continuam intactos; vínculo original validado emseparado. UUIDatual difere
C54, shutdown não observado. PacoteC57/hash4/modes/links foi conferido no70,
semreinstalar. Nada de qualificar rebootcontrolado/coldboot/perdaelétrica.

**Fontes/checks:** prepare/check/run/analyze/package-phase4-gb-installed-session.py,
phase4_gb_installed_session.py e gb-installed-session/stopped-screen.sh.
Renderer gera deltaexato do runnerC54congelado; mesmos host/core/ROM/UIlib/
runner/worker/session/select/app-launch C53, backend/gate/dispatcher C58.
Checks.zebm2adj passou29recusas/vínculos/delta, semhardware/ROM privada.
34fixturesC58 e falhas/lifecycleC45 reutilizados, semreplay. Backendread-only
semprepare/commit/RW, roleload, rootRO e hash4 antesdecada status/export.

**Nativo:** load.uzlnx4ac (build/phase4/gb-installed-session), origemsave68,
recibosC54/C58do69, execução70.623frames/hotkey/expired0, operação0/cleanup0,
FnL2/load real e retorno aomenu confirmados; doisstatus/umaexport peloCLI
instalado. PKST/CRC/manifesto/assinaturaPNG/26861bytes válidos, HEAD1/0/2 e
inventário store byte-idênticos C58/C54 e antes/depois. Sem novo save/commit
ou estado comercial coletado. RootRO0755/fundação97/taint0/PCMclosed, prefs55/70,
mixer/DRM/volume/WirePlumber/infraPIDs/mountsglobais preservados. P3desmontada,
ROM/core/host/inspetor/helpers/estados RAM removidos; tela finalC59 enviada.
CSV4callbacks/1539frames áudioausentes, semtimestamps/causa localizada;
core_hzrecente59,9401 NÃO é FPS absoluto, não dividir623por45 (saída voluntária).
Continuidade acústica não requalificada. Prova gameboy-installed-store/
SHA256SUMS sófontes/recibos sanitizados, semELF/ROM/estado/PNG/INI/PCM/IDs/
hashROM/bootUUID/hashbundles/segredos. Provas antigas e SDKconferidos intactos.

**Console final:** C07/boot70/IP192.168.15.14:2222/aliasSSH17, rootRO/quiescente,
p3desmontado, pacoteC57 instalado/passivo e aprovado após novo bootobservado.
C12/C25off/IRQ/RW/215/q1024/prefs55/70 intactos. Geração1 sóno128 continua
HEAD1/0/2; não apagar store/repetirprepare/saveC53 ou repetirC59porrotina.
Original32/Deck não acessados. Backup/rollbackC57 permanece em
build/phase4/save-store-install/install.0kvv3gdl. ImagemC56 privada/nãoflashada,
bootdaimagem não qualificado. Nenhuma nova sessão permanece emexecução.

**Próximo C60 proposto:** preparar receitaBuildroot opt-in do host nativo
muxretro jávalidado, conferindo origem/licença/ABI/dependências antes de
instalar. Core/ROM/saves fora do payload, autostartOFF, semnovoswriters. Não
repetir áudio/USB/API/restauração ou alterarfontes/provas antigas porrotina.
NadaC60armado. Frontendpermanente/bootimagem/Power/suspend/SRAM/GC/perdaelétrica/
longaduração/continuidadeáudio/performanceNES permanecem separados.

## Marco anterior — C58 backend usa CLI instalado; leitura nativa aprovada

**C58 concluído em 02/11/2026:** diagnóstico load-only usa CLI C57 instalado,
sem enviar outra cópia ELF do store.34fixtures + seed/verify nativo semGUI
aprovados no C07/boot69. Geração1 exportada paraRAM e validada semnovo save,
store byte-idêntico aoC54. [Implementação e provas](phase4-installed-store-backend.md).

**Fontes:** gb-installed/{installed-store,store,headless}.sh e scripts
phase4_installed_store.py, check/run/package-phase4-installed-store.py,
diagnostics/phase4-installed-store-check.py. Dispatcher aceita sóstatus/export,
roleloadLF/identidade exata, rootRO/cápsulatmpfs/root700, quatro hashes C57/
modos/owner/nlink/pais semsymlink. Qualquer capsule/save-store é recusado;
sem fallback ou executável porambiente. Gate valida backend+dispatcher.
Backend gerado do C53congelado remove prepare/commit/transiçãoRW e adapta só
status/export; C53/C54 e vínculo deboot originais permanecem intactos.

**Checks:** checks.x59krv2o/34casos de operações/argumentos/role/identidade/
LF/ELFalternativo/pacote corrompido/modes/links/gate, pacote/backend sintéticos.
stat/dirname reais BusyBox A35/QEMU. Fixture inicial exigiu saída explícita
emguard composto &&; corrigido ||exit64 antes dehardware. Primeira rodada
native.8_7554tn parou antesdoCLI porque BusyBoxnãoinclui stat-f; trocado por
findmnt. P3RO/cleanup0/rootRO/mounts conferidos e cápsula falha removida.

**Nativo final:** native.ewspqvb0, source-load C54 load.x7a7858i explícito e
coincidente com prova; mesmo boot69/identidade/assets/inventário C54. SemROM/
core/UI/áudio enviados/iniciados; sóinspetor existente foi transferido comoELF.
Namespaceprivada/lock/executor45s, tmpfs privado sobre/run/muos (storageglobal
não existia), p3ro,noload/nosuid/nodev/noexec. Doisstatus/umaexport usamCLI
instalado, hashes4verificados. PKSTv1/CRC/manifesto/assinaturaPNG válidos,
26861bytescore, HEAD1/0/2 e inventário store idênticos aoC54 e antes/depois.
Prefs55/70 e hashes preservados. Operação0/cleanup0/RAM removida; rootRO0755/
fundação97/taint0/PCMclosed, infraPIDs/starttime/mountsglobais idênticos.
Não houve novo jogo, restauraçãofísica/FnL2, escrita no cartão ou reboot.
Prova dist/phase4/installed-store-backend/SHA256SUMS sófontes/recibos sanitizados,
semELF/ROM/estado/PNG/INI/PCM/identidade/hashbundle/segredos. SDK/C53/C54/C57
conferidos intactos;34transaçõesC52/USB/áudio/navegação não repetidos.

**Console final:** C07/boot69/IP192.168.15.14:2222/aliasSSH17, rootRO/quiescente,
p3desmontado. PacoteC57 permanece instalado e passivo, nenhuma nova instalação.
C12/C25off/IRQ/RW/215/q1024/prefs55/70 preservados. Geração1 sóno128 foi lida
RO e exportada apenasRAM; não apagar store ou repetir prepare/saveC53.
Cápsulas/recibos/estado/inspetor removidos, tela anterior mantida. Original32/
Deck não acessados. ImagemC56 ainda privada/nãoflashada/bootnãoqualificado;
novo bootdoCLI instalado não qualificado. Backup/rollbackC57 em
build/phase4/save-store-install/install.0kvv3gdl continua preservado.

**Próximo C59:** integrar esse despacho na sessãoGB e qualificar uma restauração
FnL2 e saídaFnStart supervisionadas, semnovo save. Preservar lifecycle/runner/
host/core e recibos explícitos; secontador mudou, não afrouxar guardabootC54.
RuntimeRAM/p3RO padrão, nenhuma gravaçãoautomática. NenhumC59armado/menuaberto.
Power/suspend/GC/SRAM/perdaelétrica/continuidadeáudio/performanceNES e frontend
permanente permanecem separados. Não repetir C58aprovado porrotina.

## Marco anterior — C57 pacote de saves instalado e validado; console69 seguro

**C57 concluído em 02/11/2026:** quatro arquivos C55 instalados seletivamente
no cartão de teste128; zero arquivos existentes substituídos. CLI/manifesto/
contrato/MIT em três diretórios novos root:root0755; folhas root:root/nlink1,
ELF0755 e demais0644. Sem serviço, writer automático, token, menu ou reboot.
[Implementação, teste nativo e rollback](phase4-save-store-installed.md).

**Plano e recuperação:** build/phase4/save-store-install/install.0kvv3gdl,
plan.json/absence-backup.json/manifest.json/deployment.tar preservados no host,
fsynced antes do remount. Backup registra ausência anterior/zero originais,
restauração remove só quatro folhas hash-exatas e três diretórios vazios.
Não repetir prepare/applyC57 agora que destinos existem; rollback não depende
da cápsula RAM removida e usa bytes arquivados. Modo verify é só retomada de
aplicação pendente; final-health.sh serve leitura final sem cápsula. Guardas
CID128/recusa32, modelo/kernel/rootext4/PARTUUID/boot/quiescência/lifetime lock.
Nunca usar imagemC56 para sobrescrever raiz viva. Nenhuma imagem enviada.

**Verificação:**26fixtures de política/aplicação/falhasparciais/rollback passaram.
Primeiro stage install.a4fy86sk travou em dirname('//') doBusyBox, antesdequalquer
RW/apply; processo próprio terminado, rootRO/pacoteausente/cápsularemovida.
Corrigido terminador '/' e '//', caso real BusyBox A35/QEMU adicionado, novo
plano/fixtures antes da instalação. Final inspect0/apply0/manifesto3/modes/
links/hash4 aprovados, fundação97 inalterada. CLI instalado init0/status0 em
RAM sintética HEAD0/current0/previous0/next1; recover3 sem anterior. Nada de
estado/ROM comercial.34fixtures/labext4C52 reutilizados para mesmoELF SHA
 e9540c40e00a9b46b3eee0efbb2a669bdc16f6721359a1fd2a1800836929056d.
Fingerprint privado sóRAMcomparado, não coletado; infraPIDs/starttime e mounts
globais antes/depois iguais. Auxiliares/payload/fingerprint/testeRAM removidos.
Prova dist/phase4/save-store-installed/SHA256SUMS sófontes/recibos, semELF/tar/
rootfs/ROM/estado/PNG/PCM/segredos. C52/C54/C55/C56 e SDK preservados.

**Console real final:** C07/boot69/IP192.168.15.14:2222/aliasSSH17, rootRO0755/
fundação97/taint0/PCMclosed, semUI/core/input/PipeWire; p3desmontado TODO C57.
Pacote instalado, passivo. C12/C25off; IRQ/RW/215/q1024/prefs55/70 intactos.
Geração1 C53/C54 sóno128 não foi relida/remontada/alterada, HEAD1/0/2 conforme
reciboC54. Não apagar store nem repetirprepare/saveC53. Original32/Deck fora
do fluxo. Página de diagnóstico anterior mantida, sem novo ensaio físico.
Pacote ainda não qualificado em novo boot; imagemC56 segueprivada/nãoflashada
image.nlnmgzzb SHA07a18d14ef54c91b7e463a016155165deff33296fdf833b8dbca51ff38780ef6.

**Próximo C58:** adaptar diagnóstico de persistência para consumir CLI instalado
com manifesto/hash aprovado, evitando transportar outra cópia de ELF emRAM.
Runtime/estados intermediários continuam RAM; identidade exata/p3RO padrão,
commit somente explícito. Preparar fixtures de despacho/recusa antes de futura
sessão supervisionada. Preservar C53/C54 originais, semprepare/save automático.
NadaC58armado. Bootdaimagem/novobootdopacote/perdaelétrica/Power/suspend/SRAM/
GC/continuidadeáudio/performanceNES e frontendpermanente continuam separados.

## Marco anterior — C56 imagem ext4 privada aprovada offline

**C56 concluído em 02/11/2026:** imagem ext4 privada de512MiB gerada a partir
C38 + somente os quatro arquivos/três diretórios do pacote C55. Fonte explícita
composition.d0qpit_q coincide com provaC55 congelada. Nenhuma instalação,
flash, reboot ou acesso ao console/cartões/Deck neste incremento.
[Implementação, artefato e verificações](phase4-save-store-image.md).

**Artefato:** build/phase4/save-store-image/image.nlnmgzzb/images/rootfs.ext4,
SHA256 07a18d14ef54c91b7e463a016155165deff33296fdf833b8dbca51ff38780ef6,
536870912bytes/ROOTFS. Cópia doC38 recebe só adiçõesC55 via debugfs; não é
imagem completa de cartão e não deve sobrescrever a raiz viva. C38SHA
7b2718beec0aa75fd5b6d81570c9e98857efa00f01638d7f04159a73d711320d preservado.
GPU R13/pendências de licença herdadas mantêm uso privado; imagem em build/.

**Verificação:** fsck-fn/5passes/status0, raiz0755/root:root e sete inodes novos
com donos/modos conferidos; releitura integral3330itens byte/mode/type/symlink
idêntica aoC55, nenhum itemC38 alterado. Fundação97/payload15/perfil21 e novo
manifesto3 válidos. Gateboot antes/depois passa C07/contadorfábrica0/defaultsoff,
semestado privado/tokens. Auditoria861ELFs=306userspace+555módulosAArch64,
ABI4.4.0, ext4features0x3c/0x242/0x46b iguais à base. LoaderA35/QEMU do CLI
relido resolve zlib/libc e recusa semargs64; não executou init nem jogo.
172loadersC38 e34fixtures/labext4C52 reutilizados para bytes idênticos, sem
repetição física/USB/áudio. SDK.config compartilhado/fontes/provasC55 intactos.
Sem recompilação/fullBuildroot/bootnativo ou reprodutibilidadebitabit qualificada.
Prova dist/phase4/save-store-image/SHA256SUMS contém só fontes/recibos/metadados,
semELF/rootfs/ROM/estados/segredos. Scripts compose/package-phase4-save-store-image.py.

**Console:** NÃO consultado nesta rodada offline. Último estado vivo verificado
é C55: C07/boot69/IP192.168.15.14:2222/aliasSSH17, rootRO0755/fundação97/taint0/
PCMclosed/p3desmontado e pacoteC55ausente. Conferir novamente antes de qualquer
deploy; não assumirIP/boot atuais. C12/C25off/IRQ/RW/215/q1024/prefs55/70 e
storeC53/C54 geração1 sóno128 preservados por ausência de acesso. Não apagar
store/repetirprepare/saveC53. Original32/Deck continuam fora do fluxo.

**Próximo C57:** preparar implantação seletiva dos quatro arquivosC55 no128,
com inventário, backup/rollback e vínculo aos hashes. Primeiro verificar estado
real e ausência dos destinos. Manter fundação97/áudio/prefs/store intactos,
serviços/autostart/writer automáticosoff; não sobrescrever raiz com imagem.
Qualquer verificação nativa deve usar RAM sintética e encerrar rootRO/p3off,
sem replay de jogos/USB/áudio. NenhumC57armado/instalado. Boot desta imagem,
coldboot controlado/perdaelétrica/SRAM/GC/Power/suspend/continuidadeáudio e
performanceNES continuam separados.

## Marco anterior — C55 pacote Buildroot opt-in aprovado; console69 preservado

**C55 concluído em 02/11/2026:** utilitário genérico C52 integrado como
BR2_PACKAGE_MUOS_SAVE_STORE, AArch64/defaultoff/zlib/MIT. Instala somente CLI,
contrato/licença e manifesto: quatro arquivos, sem serviço/mount/writer/
inicializador/defaults/identidade/ROM/core/save privado. Não promove o bridge
C53 a serviço permanente. [Implementação e provas](phase4-save-store-package.md).

**Verificação:** Kconfig/rsync/legal-info reais em O=isolado; defaultoff,
opt-in seleciona zlib/libzlib sem serviços, i386 confirmado e pacote recusado.
Fontes e arquivo legal restritos a C/LICENSE/contract.json; licença/hash válidos.
Macros reais com SDK geram ELF PIE A35/ABI4.4.0/RELRO/NOW, semRPATH; loader
A35/QEMU/LD_BIND_NOW recusa argumentos ausentes com64. SHAELF
 e9540c40e00a9b46b3eee0efbb2a669bdc16f6721359a1fd2a1800836929056d
byte-idêntico ao C52: reutilizadas34fixtures/labext4, semrepetição física.
Lintcheck-package indisponível no container por faltarmóduloPythonmagic;
não instalar dependências no host nem declarar esse lint aprovado.

**Composição privada C55:** cópia da árvoreC38 recebe quatro arquivos/três
diretórios; inventárioC38 inteiro inalterado, fundação97/payload15/perfil21,
C07/contadorfábrica0/defaultsoff semtokens ouestado privado. Manifesto3 válido
e loader da composição aprovado. Nenhuma nova imagem foi gerada: imagemC38
composition.w59vz7vo512MiB SHA7b2718beec0aa75fd5b6d81570c9e98857efa00f01638d7f04159a73d711320d
permanece intacta/nãoflashada. Compositor legado tem guard de menu atualizado
apenas para extensão exataC55; composiçãoaditiva usa novo adaptador próprio.
SDK.config compartilhado e provas C52/C54 conferidos intactos. Prova congelada
emdist/phase4/save-store-package/SHA256SUMS, sófontes/metadados, semELF/rootfs/
archive/ROM/estado/PNG/PCM/segredos. Sem rebuild completo ou novo boot do pacote.

**Console real final:** C07/boot69/IP192.168.15.14:2222, aliasSSH17. Checagem
somenteleitura passou rootRO0755/fundação97/taint0/PCMclosed, semUI/core/input/
PipeWire/p3montada; infraPIDs coincidem com fimC54. PacoteC55 ausente no cartão.
Nenhuma alteração/reboot/token/mount/menu/testefísico neste incremento.
IRQ/RW/215/q1024/prefs55/70 e geração1C53/C54 somente no128 preservados;
HEADcurrent1/previous0/next2 conforme último reciboC54, semremontar para repetir
leitura. Não apagar store ou repetir prepare/saveC53. Original32/Deck intactos.
C12/C25 desativados. C54 restaurou posição do68 no69; método shutdown não
observado e não equivale a teste de perda elétrica/coldboot controlado.

**Próximo C56:** gerar imagemext4 privada/offline da árvoreC55 e conferir
readback completo/fsck/manifests/contratoboot, mantendo writer/autostartoff.
Não instalar, flashar ou rearmar console para esse incremento; futuro deploy
exige plano seletivo/rollback. Não repetir áudio/USB/API/estado aprovado sem
regressão concreta. SRAM/GC/corrupção real/longaduração/continuidadeáudio/
Power/suspend/performanceNES seguem separados. NenhumC56 armado.

## Marco anterior — C54 restauração após novo boot aprovada; console69 seguro

**C54 concluído em 02/11/2026:** console já estavaC07/boot69 ao retomar;
snapshot1 foi criado/validado no68. Usuário restaurou a mesma posição por
Fn+L2 e saiu Fn+Start, confirmando “Tudo certo” à pergunta específica. Não
foi solicitado outro reboot; método do shutdown anterior não foi observado.
[Implementação e prova C54](phase4-gb-after-boot.md).

**Console real final:** C07/boot69/IP192.168.15.14:2222, aliasSSH17 fixado.
RootRO0755/fundação97/taint0/PCMclosed, semUI/core/input/PipeWire. Prefs55/70,
mixer/DRM/WirePlumber, infraPIDs e mounts globais preservados; p3 desmontado.
Cápsulas/ROM/helpers/estados RAM removidos, tela finalC54 enviada. Geração1
comercial permanece apenas no p3 do128, MUOS/port-saves-v1/gb/<identidade
privada>, HEADcurrent1/previous0/next2, byte-idêntica ao fim do boot68. Nada
novo salvo ou transferido ao host. Não apagar store/repetir prepare/save C53;
original32/Deck preservados. Sem instalação, token, flash ou reboot do agente.
C12/C25 permanecemoff; nenhuma alteração em IRQ/RW/215/q1024/prefs55/70.

**C54 fontes/provas:** run/check/analyze/package-phase4-gb-reboot.py,
phase4_gb_reboot.py e gb-reboot/{store,stopped-screen}.sh. Adaptador exige
recibos --source-save/save.hi07rjg_ e --source-load/load.i2to6dts C53explícitos,
coincidentes com prova imutável e mesmos assets/identidade; origem68/current69.
C53original continua exigindo mesmo boot. Gatepermite só seed/verify com
roleloadLF e backendC53pinned; inicializador/prepare não enviados. RuntimeRAM,
p3RO/noload, comparação de todo store com registro final do68. Host/core/UI/
runner/worker/session/select/app-launch C53 byte-idênticos, semrecompilação.

checks.guod5xw0 passou26fixtures de vínculo/gate, semhardware/ROM privada.
load.x7a7858i: load real/26861bytes PKST/CRC/manifesto/assinaturaPNG válidos,
906frames/expired0/hotkey, retorno físico/técnico e operação0/cleanup0. Store
byte-idêntico entreboots e antes/depois. CSV4callbacks de underrun/3eventos/
1932frames ausentes(~0,059s), agregado semtimestamps; não atribuir causa ao
load. Core_hz recente58,9971, NÃO calcular906/45fps. Continuidade de áudio em
interações segue aberta. Prova gameboy-after-boot/SHA256SUMS semestado/ROM/
PNG/ELF/PCM/segredos, identidade/hashROM/bootUUID redigidos. C53/C52 congelados.

**Bases preservadas:** C53 persistência entre sessões e C52store/34fixtures/
labext4, limite32 semGC. C51RAM/C50FnStart aprovados. HostC50host.uuixcmie SHA
4f230ad1ca347a889e5eda2b5171aba4568670ae28a1b2d294abf4a95e8a44dd;
GambatteGPLv2 commit77f2567d718b8973d02caa2daa8dce4953faf811, ELFSHA
3e0940dacb9cbcdde1b55ebc0e1d275b1dc8b034bba0e235bc56b46651200a57.
ROM privada65536B port/roms/gb/Super Mario Land (World) (Rev 1).gb ignoradaGit/
byte-exata. Não repetir API/USB/rollback/áudio por rotina. NES C48 segueaberto
51,4baseline/53,57O3LTO; imagemC38 composition.w59vz7vo512MiB privada não
flashada, SDKconfig inalterado. Limites/provas anteriores nos marcos/docs.

**Próximo C55 proposto:** integrar utilitário genérico C52 como pacote/receita
Buildroot opt-in, dependênciazlib/licençaMIT/defaultsoff, semconteúdo privado.
Conferir ABI/manifests da composição privada; não promover bridge diagnóstico
C53 a writer amplo ou autostart. Nenhum C55 armado/instalado. Resultado C54
não prova shutdown normal/coldboot controlado/perda elétrica. SRAM/GC/
recuperação de corrupção real/longa duração e Power/suspend/performanceNES
seguem separados. Não provocar novo reboot só para repetir a leitura aprovada.

## Marco anterior — C53 persistência entre sessões aprovada; console68 seguro

**C53 concluído em 02/11/2026:** integração seletiva no cartão128 salvou uma
posição de Super Mario Land porFn+R2; runtime/RAM foi totalmente encerrado e
removido. Nova sessão montou p3RO, carregou a geração1 e restaurou a posição
porFn+L2. Usuário confirmou “Voltei ao menu” na primeira e “Tudo certo!” na
segunda pergunta específica de restauração exata/saída. Ambas saíram Fn+Start,
retornaram ao launcher e terminaram operação0/cleanup0.
[Implementação, resultados e plano C54](phase4-gb-persistence.md).

**Console real final:** C07/boot68/IP192.168.15.14:2222, aliasSSH17 fixado.
RootRO0755/fundação97/taint0/PCMclosed, semUI/core/input/PipeWire. Prefs55/70,
mixer/DRM/WirePlumber, infraPIDs e mounts globais preservados; p3 desmontado.
Cápsulas/ROM/ELFs/helpers/estados RAM removidos, página finalC53 enviada.
Geração1 comercial RETIDA somente em MUOS/port-saves-v1/gb/<identidade privada>
no p3 do cartão128, HEADcurrent1/previous0/next2. Nenhum estado/PNG/manifesto
comercial foi transferido ao host. Não apagar o store ou repetir prepare/save:
esses modos C53 exigem árvore ausente/store vazio e devem recusar repetição.
Original32 dArkOSen intacto, Deck já limpo/fora do fluxo. Nada instalado,
rebootado, armado ou reflashado; C12/C25 permanecem desativados.

**Fontes/provas C53:** gb-persist/{store,prepare,session,select,app-launch,
stopped-screen}.sh, diagnostics/phase4-save-directory.c e phase4-gb-persist-
check.py, scripts check/run/analyze/package-phase4-gb-persist.py. Bootstrap
exclusivo/fsync/renameNOREPLACE; paiMUOS0755 existente preservado, nova árvore
0700/markers600. Bridge monta p3RW apenas para inicializar/commit explícito;
restauraRO/noload, verifica preferências, mantém runtime/storages emtmpfs.
Seed copia apenas três folhas à RAM com identidade ROM/core exata; autosave,
timeline, flush periódico e autoloadoff/--fresh. Commit exige saída hotkey e
writer/inspetor aprovados. Roleload não publica e compara todo o store antes/
depois. Falha de transação retorna ao launcher antes de falhar a operação.

checks.o2w1sbb5:32fixtures A35/QEMU aprovadas. prepare.d9p3tciz inicializou
HEAD0, ausência anterior registrada; tentativa9e0hu87x recusou pai0755 antes de
criar árvore, semchmod/overwrite, cleanup0. save.hi07rjg_:1216frames/expired0/
hotkey/26861bytes válidos/commit1/zero faltas de áudio. load.i2to6dts:1214frames/
expired0/hotkey/load real/mesma posição física, store byte-idêntico/p3RO/cleanup0.
CSVload tem4callbacks de underrun/1971frames ausentes (~0,060s), semtimestamp:
não atribuir causa ao load nem declarar continuidade de áudio sem faltas.
Core_hz recente59,9401(save)/59,8802(load); NÃO dividir frames voluntários por45.
Prova gameboy-selective-persistence/SHA256SUMS semestado/ROM/PNG/ELF/PCM/segredos,
identidade/hashROM redigidos. Bases C51/C52 congeladas e verificadas.

**Bases preservadas:** C52store/34fixtures/laboratório ext4 sintético com backup/
recover, limite32 semGC. C51 save/loadRAM e C50 FnStart aprovados. HostC50
host.uuixcmie SHA4f230ad1ca347a889e5eda2b5171aba4568670ae28a1b2d294abf4a95e8a44dd;
GambatteGPLv2 commit77f2567d718b8973d02caa2daa8dce4953faf811, ELFSHA
3e0940dacb9cbcdde1b55ebc0e1d275b1dc8b034bba0e235bc56b46651200a57.
UIlibC46/runnerC44/workerC46/coreROM não recompilados ou alterados. ROM privada
65536B emport/roms/gb/Super Mario Land (World) (Rev 1).gb, ignoradaGit/byte-exata.
Não repetir API615frames/USB/rollback/áudio por rotina. ÁudioC36 IRQ/RW/215/
q1024/prefs55/70 preservado; NÃO reaplicar/recalibrar sem regressão concreta.
NES C48 segue51,4baseline/53,57O3LTO sem promoção. ImagemC38 privada512MiB
composition.w59vz7vo segue não flashada; SDKconfig inalterado.

**Próximo C54 preparado:** reboot normal controlado C07 e roleload da geração1
com observação Fn+L2, semnovo save. Primeiro conferir quiescência/p3desmontado/
rootRO/provas C53; após reboot novo contador/rede/fundação/taint/rootRO. Runner
C53 exige mesmo boot por projeto: novo adaptador deve vincular explicitamente
recibo de boot anterior e a mesma identidade; não remover guardas por rotina.
Não rearmarC12/C25/menu permanente. Nada C54 armado. Novo boot, perda elétrica,
recuperação de corrupção real, GC, SRAM e longa duração não qualificados;
Power/suspend/flash e performanceNES fora desse ensaio.

## Marco anterior — C52 store e laboratório ext4 aprovados; console 68 seguro

**C52 concluído em 02/11/2026:** novo muos-save-store MIT, 34 fixtures A35/QEMU
aprovadas, duas gerações/recuperação explícita verificadas nativamente em uma
imagem ext4 de16MiB em RAM. Cartão de dados real auditado apenas ro,noload;
nenhum save comercial ou novo escritor durável foi habilitado no cartão.
[Implementação, contrato e plano C53](phase4-save-store.md).

**Console real final:** C07/boot68/IP192.168.15.14:2222, chave fixada alias17.
RootRO0755/fundação97/taint0/PCMclosed, sem UI/core/input/PipeWire. Prefs55/70,
infraPIDs e mounts globais idênticos. p3 desmontado; cápsulas, loop, imagem e
executáveis RAM removidos. Tela de diagnóstico C51 permanece, pois C52 não
abriu gráfica/áudio. Nada instalado, rebootado ou armado. Original32 dArkOSen
intacto; SteamDeck já limpo e fora do fluxo. Não repetir API/rollback/USB/áudio
ou sessões coletadas por rotina.

**C52 fontes/provas:** port/utils/muos-save-store.c, diagnostics/phase4-save-
store-{check.py,ext4.c}, device/rk-r35s-p0/save-store/{contract.json,audit-data.sh,
transaction.sh} e scripts check/prepare/run/package-phase4-save-store*.py.
Store em diretório próprio0700 com marker600, sem symlinks, ext4/tmpfs;
input/export apenas tmpfs. Bundle imutável de estado/manifesto/miniatura com
CRC e identidade privada; HEAD atômico current/previous/next, fsyncs ordenados,
flock não bloqueante e recover explícito. Sem fallback automático/adoção de
órfão/GC; teto32 gerações recusa sem sobrescrever. Guard de mídia/mount cabe ao
adaptador. Não instalar nem ligar ao S90/pickles inteiro neste estágio.

checks.ddn_42op passou34/34, incluindo corrupção, links/tipos/modos, identidade,
lock, quota e fsync antes/depois de publicar HEAD. ext4.uc9ox2nw preserva funções
de ownership/loop/mount C19 por comparação exata. native.0o0k0_gb passou duas
gerações, RO recusado, fonte ext4 recusada, exportação B após remount, corrupção
B preservada/recover A e nova exportação A após remount. Fsck offline passou.
Dados reais: pickles/save existentes root700, port-saves-v1 ausente. Prova
save-store-laboratory/SHA256SUMS sem ROM/ELF/imagem/estado/PNG/segredos. C51 e
provas anteriores preservadas. Nenhum teste físico foi necessário no C52.

**C51 preservado:** Fn+R2/Fn+L2/Fn+Start aprovados pelo usuário “Tudo certo!”.
Uma gravação/dois loads,26861bytes PKST/CRC/manifesto/assinatura PNG válidos;
2453frames/expired0/reasonhotkey, retorno/cleanup0. observe.dj2lowrs emgb-state;
prova gameboy-ram-state congelada. 8callbacks de underrun/5eventos/3471frames
(0,106s), agregado semtimestamps: causa não atribuída, continuidade de áudio
nas interações ainda aberta. C52 não executou áudio nem recalibrou nada.

**Bases preservadas:** hostC50 gb-exit/host.uuixcmie SHA
4f230ad1ca347a889e5eda2b5171aba4568670ae28a1b2d294abf4a95e8a44dd;
GambatteGPLv2 commit77f2567d718b8973d02caa2daa8dce4953faf811, ELFSHA
3e0940dacb9cbcdde1b55ebc0e1d275b1dc8b034bba0e235bc56b46651200a57.
UIlibC46build.srarmig3 e runnerC44runner.je_ael7e intactos. ROM privada65536B
port/roms/gb/Super Mario Land (World) (Rev 1).gb ignoradaGit/bytes preservados.
C49/C50/C51 têm provas completas; não repetirAPI615frames por rotina. NES C48
continua pendente51,4baseline/53,57O3LTO. ÁudioC36 IRQ/RW/215/q1024/prefs55/70
instalado; NÃO reaplicar/recalibrar sem regressão concreta. ImagemC38 privada
composition.w59vz7vo512MiB segue não flashada; SDKconfig inalterado. C12/C25
não rearmar. Limites/backup históricos nos marcos anteriores e docs vinculados.

**Próximo C53 preparado:** integrar cópia seletiva ao fluxo C51, com identidade
ROM/core privada, inicialização/backup exclusivos sob MUOS/port-saves-v1,
guardC20/C22 e syncs; duas sessões supervisionadas salvar/sair e carregar/
confirmar posição/retornar. Manter todo o runtime em RAM, autosave0 e --fresh;
export apenas três folhas e commit só após flush/validador. Preservar hashes
prefs antes/depois, não coletar estado comercial. Nenhum C53 armado. Saves
comerciais no cartão, novo boot, perda elétrica, GC e longa duração ainda não
qualificados; não unir Power/suspend/flash ou nova calibração.

## Marco anterior — C51 save/load em RAM aprovado; console 68 seguro

**C51 concluído em 02/11/2026:** Super Mario Land salvou por Fn+R2 e restaurou
por Fn+L2; usuário confirmou “Tudo certo!” à sequência salvar/mover/restaurar/
sair. Uma gravação e dois loads reais, payload 26861 bytes, PKST/CRC/manifesto/
assinatura PNG válidos em tmpfs. Fn+Start encerrou 2453 frames, expired=0,
reason=hotkey; retorno ao launcher e operação=0/cleanup=0.
[Implementação, evidências e limites](phase4-gb-state.md).

**Console real final:** C07/boot68/IP192.168.15.14:2222, chave fixada alias17.
Root RO0755/fundação97/taint0, PCM closed, sem UI/core/worker/input/PipeWire.
Mounts globais, prefs55/70, mixer/DRM/WirePlumber e infraPIDs preservados;
MUOSDATA desmontado. Cápsula/ROM/ELFs/estados/miniaturas RAM removidos, página
final C51 enviada. Nada armado, rebootado ou instalado. Original32 dArkOSen
intacto; SteamDeck já limpo e fora do fluxo. Não redisparar sessões coletadas.

**Fontes e provas C51:** helper MIT phase4-state-metadata.c, scripts gb-state/
e run/check/analyze/package-phase4-gb-state*.py. Novo helper A35 valida dados
somente leitura antes de desmontar a sessão; coleta só metadados. Folhas com
links/modos/tamanhos/filesystem incorretos são recusadas. Estado/PNG/INI nunca
exportados. Sinais/supervisão/rollback mantêm workerC46, owner210/externo240;
seleção120s, jogo45s e retorno20s. Falha na inspeção retorna ao launcher antes
de propagar erro. Autosave/timeline/flush periódico permanecem off em RAM.

checks.3dn_w575: 18 fixtures QEMU sintéticas aprovadas; inspector SHA
7b51f9c0975fbf8374b6c4873a9761f28b1e904614af0a136ee1ad343872b64f.
dispatch-check.lg1_yd5y: 5 cenários, inclusive falha do helper/log/app com
retorno antes de erro. Nativo observe.dj2lowrs, análise/observação/coleta em
build/phase4/gb-state. Prova dist/phase4/gameboy-ram-state/SHA256SUMS sem ROM,
ELF, estado, PNG, PCM, prefs ou segredos; hash ROM redigido. Bases C49/C50
imutáveis preservadas; testes de API/deadline/rollback reutilizados por SHA.

**Limitação observada:** CSV C51 tem 8 callbacks de underrun/5 eventos/3471
frames ausentes (0,106s), sem timestamps de eventos. Não atribuir causa a
save/load nem declarar áudio sem faltas. core_hz recente59,9401; saída
voluntária não mede2453/45fps. Usuário aprovou funcionalidade, sem relato de
problema audível; continuidade de áudio durante interações não foi qualificada.

**Bases preservadas:** hostC50 gb-exit/host.uuixcmie, SHA
4f230ad1ca347a889e5eda2b5171aba4568670ae28a1b2d294abf4a95e8a44dd;
GambatteGPLv2 commit77f2567d718b8973d02caa2daa8dce4953faf811, ELFSHA
3e0940dacb9cbcdde1b55ebc0e1d275b1dc8b034bba0e235bc56b46651200a57.
UIlibC46build.srarmig3 e runnerC44runner.je_ael7e intactos. ROM privada
port/roms/gb/Super Mario Land (World) (Rev 1).gb, 65536 bytes, ignoradaGit/
bytes preservados. [C49](phase4-gb-content.md) e [C50](phase4-gb-hotkey-exit.md)
têm provas completas. Não repetir API615frames/cancelamento/rollback/USB por
rotina. NES C48 continua pendente51,4baseline/53,57O3LTO, sem promoção.

Áudio C36 IRQ/RW/codec215/q1024/prefs55/70 e primeiros menus62/64 aprovados;
NÃO reaplicar/recalibrar por rotina. ImagemC38 composition.w59vz7vo512MiB,
SHA7b2718beec0aa75fd5b6d81570c9e98857efa00f01638d7f04159a73d711320d
continua privada e não flashada; SDKconfig inalterado. C12/C25 não rearmar.

**Próximo C52:** preparar persistência limitada a saves, começando por auditoria
somente leitura do contrato/caminhos e plano de backup/recuperação. Estado
comercial não pode entrar em prova pública. Medir por interação os underruns
se a próxima etapa exigir continuidade de áudio; o agregado C51 não localiza a
causa. Não unir Power/suspend/flash, instalação ou nova calibração. Nada C52
armado; saves duráveis, novo boot e estabilidade prolongada não qualificados.

## Marco anterior — C50 Fn+Start aprovado; console68 seguro

**C50 concluído em02/11/2026:** jogoGB encerrou por hotkey nativo e retornou ao
launcher; usuário confirmou “Tudo certo” à pergunta específica Fn+Start/retorno.
observe.nc73v_sv registrou547frames/expired0/reasonhotkey/app_status0, zero
faltas de áudio e operação0/cleanup0. Fallback deadline.2ff2o774 passou antes:
2691/45≈59,8fps/expired1/reasondeadline/retorno/zero faltas/cleanup0.
[Implementação, provas e limites](phase4-gb-hotkey-exit.md).

**Console real final:** C07/boot68/IP192.168.15.14:2222, chave fixada alias17.
RootRO0755/fundação97/taint0, PCMclosed e sem UI/core/worker/input/PipeWire.
Mounts globais/prefs55/70/infraPIDs idênticos, MUOSDATA desmontado. Cápsulas/
ROM/ELFs/helpers RAM removidos, página finalC50 enviada. Nada armado, rebootado
ou instalado. Original32 dArkOSen intacto, SteamDeck limpo e fora do fluxo.
Não redisparar sessões já coletadas ou repetir B/rollback/USB por rotina.

**C50 fontes/provas:** patch0015 +phase4-diagnostic-exit.h, host privado
gb-exit/host.uuixcmie, ELF SHA
4f230ad1ca347a889e5eda2b5171aba4568670ae28a1b2d294abf4a95e8a44dd,
paiC47host._t02eefb SHA2ba1ca32d2e3c7c9157d07043ecab26a8ef0913871dca0400fe57b66b92d7bc1.
--diagnostic-hotkey-exit só com conteúdo diagnóstico/fresh/prazo1..60; semflag
comportamentoC44 preservado. Origemhotkey separada deinternal/remote; main
aceita apenas o pedido nativo consumido, exige frames e dá prioridade ao prazo.
Sinais/outras causas não qualificam hotkey. Auto_save/timeline/sram_flush=0 nos
settingsRAM deste modo, sem preferências/saves duráveis. READY confereStart;
Fnnormalizado BTN_TRIGGER_HAPPY5→BTN_MODE→SDLGUIDE→mux_input_menu. Power,
volume e brilho não foram usados ou habilitados.

checks.8wl70wak passou noQEMU40parsers de regressão+12novos+26policy/origem,
loader/CLI. dispatch-check.eupxwstf passou9fixtures semhardware/ROM comercial:
normalização exataC49 +flag/marker, motivos/frames/ready/erro/execução duplicada/
argumentos. Novo session.sh testa deadline45→launcher20 antes do A/jogo/FnStart/
launcher, com workerC46 byte-idêntico/owner210/externo240. Source/SDK/refs/UIlib/
runner/coreROM anteriores preservados; não repetiuAPI C49 ou rollbackC45.
A saída voluntária547frames não durou45s: NÃO calcular547/45 comofps. CSV
reportou core_hz59,88 e zero faltas, sem nova medida de throughput absoluto.
Prova dist/phase4/gameboy-hotkey-exit/SHA256SUMS conferida, semELF/ROM/frames/
PCM/saves/prefs/segredos, hashROM redigido. C49 e demais provas congelados.

**Game Boy/C49 preservados:** GambatteGPLv2 commit
77f2567d718b8973d02caa2daa8dce4953faf811, fonteSHA
45e63bc79390093b78de025172ea289ded139f4ecf1e8072242f34d7dd540338,
build.lgsx_3c2 emgb-core, ELFSHA
3e0940dacb9cbcdde1b55ebc0e1d275b1dc8b034bba0e235bc56b46651200a57.
SDKC++A35/O2/PIC/RGB565/HAVE_NETWORK0, fontes/COPYING retidos. ROM privada
port/roms/gb/Super Mario Land (World) (Rev 1).gb,65536bytes, ignoradaGit/bytes
preservados; já executadaAPI/nativo e enviada apenas aRAM. Não publicar ROM,
capturas/PCM/saves; hashes/recibos completos só embuild. C49 APIapi.hnkaejde e
nativecycle.c7l1qqdr passaram615frames/160x144RGB565/áudio32768nãozero/input/
reset/serializeRAM. Perfil2691/45≈59,8 e físicoobserve.6at5n4_r2690/45≈59,78,
zero faltas; usuário aprovou imagem/Start/Dpad/som. SDL32768→backendALSA48000
viaPipeWire, medido48000,49frames/s. C50 não recalibrou IRQ/215/q1024/volume55.
[DetalhesC49](phase4-gb-content.md), prova gameboy-private-content preservada.

**Bases instaladas preservadas:** UI/libC46build.srarmig3 SHA
1ec8acd906ee25bd83b59c0c5818e7310d62bfeaabadb2b473e03562d7d6bcc9,
runnerC44runner.je_ael7e, C47host e provasC45/C46 intactos. C47NES funcional
aprovado; C48 desempenho aberto51,4baseline/53,57O3LTO/640faltas, sem candidato
promovido. C50 não corrige NES. [MediçõesC48](phase4-nes-performance.md).

C39 áudio primeiros menus62/64 aprovado, C36IRQ/RW/215/q1024/prefs55/70
instalado; NÃO reaplicar/recalibrar por rotina. C36sourcec36-update.m4ji3sr0,
backup2 c24-backup.zqk7wvsb/original-files.tar SHA
3b122a90f041bd935089ed0b4f03a827e181ff5d2e27a09809e2672e5756e0a1.
C38 composition.w59vz7vo SHA
7b2718beec0aa75fd5b6d81570c9e98857efa00f01638d7f04159a73d711320d,
512MiB/fundação97, não gravado/bootado inteiro. Kernel/DTB/bootloader/partições
intactos. UI permanenteoff; coldboot/fones/energia/suspend/longa duração/imagem
inteira não qualificados. Não resetar68/rearmarC12/C25 ou rebootar por rotina.

**Próximo C51:** salvar/restaurar estado manual pela UI/hotkeys nativos somente
emRAM, com autosaveoff. Conferir Fn+R2/Fn+L2, suporte do core e caminhos antes
de pedir teste físico; registrar metadados, sem publicar estado bruto. Não unir
saves duráveis, Power ou instalação. Nenhum C51 armado; confirmar disponibilidade
na rodada seguinte. NES requer separar tempoCPU/espera/apresentação antes de
outra otimização, semclocks ou reboot por rotina.

## Marco anterior — C30–C33 antes da interrupção


**C33 instalado; C34 preparando validação após boot:** RW em RAM no57/run-0002,
audio-buffers/session.9tikayjz, passou≈44100frames/s e usuário “Audio ok, porem baixo”
com55/215/q1024/RW confirmado ativo. Sem recalibrar volume. Stop/coleta/restore0,
config+fundação privadas limpas. C33_ALSA_RW aplicado RC0 por2públicos/config+
fundação97, stage rootfs-candidate/c30-update.eizgds2m (latest-update), backup2 e
14checks de transação passaram. Cartão agoraRW/IRQ, raizRO/rede/prefs preservadas;
NÃO repetir apply. Fonte/ABI/ELF/kernel/perfil não mudaram. C34 runner suportaC33;
20checks host passaram; stage C34 rootfs-candidate/c25-physical.v2xt46_i
(latest-c25-physical), base57/boot58/fallback59. Arm/request serão despachados
uma vez. Conferir seus recibos antes de qualquer repetição; precisa running/
coleta/fallback. C12 inativo/sem UI permanente.




**31/10/2026: áudio após reboot continua NÃO aprovado.** A política IRQ passou
na audição da sessão quente55, mas usuário confirmou “O audio esta distorcido”
no boot56, com a política instalada/ativa. PCM≈22050 contra44100 declarados,
mesmo SEM falta de buffers. C32 forçou48000 em RAM:≈24000; voltar ao automático
não recuperou e cruzou resets de PCM. Zero avisos/exit0 de auditoria de props
não significam som correto. [Detalhes C30–C32](phase4-irq-rate-negotiation.md).

**Estado vivo final:** boot57/C07/IP192.168.15.8:2222, chave fixada alias17.
Raiz ext4RO/0755, contador57/0600 emdir0700, brilho80, FAT/p3 desmontadas,
taint0,97hashes/payload C22/15/perfil21/C25/5 válidos e rede pronta. Última tela
C11 session stopped/manual-stop/result0; sem UI/PipeWire/input/player/profiler/
logger/worker ativo, PCMclosed. Metadata force-rate0 foi restaurada ANTES de
parar o daemon; helpers RAM e debugfs próprios limpos. C25/C12 SEM.once;
recibos usados48/50/54/56 preservados. Sem reboot/transação/teste físico pendente.
Original dArkOSen32GB preservado; Steam Deck limpo/fora do fluxo.
Recibo: build/phase4/audio-buffers/session.3rmqqwti/final-health.stdout,
KERNEL_STORAGE_SIGNATURES=0/C32_STOPPED_BOOT57_C07_ROOT_RO_FOUNDATION97_NETWORK_OK.

**Instalado C30_ALSA_IRQ:** rootfs-candidate/c30-update.19pb66vi (latest-update),
no55 por somente2públicos: /opt/muos/device/control/wireplumber.conf e fundação97,
agora cobrindo esse arquivo. SHAconfig8bb127e9ee9aaeacaf295fa70d49f0f31b4ea47567b1117ca59694ce1a37d898.
Perfilv3/codec215 e quantum1024 continuam; par persistente55/70 preservado.
Política experimental api.alsa.disable-tsched=true altera também geometria derivada:
period1024/buffer4096/headroom0. Não basta para áudio apósboot; não promover
como correção final. Sem novoELF/kernel/DTB/bootloader/partição/flash.
Backup2 públicos build/phase4/private/c24-backup.k66d0mis/original-files.tar,
600/pai700, SHA20e645f7f7b35381b307fa79e2dcbc00682f5bb911476c1f127c7c5221b819c4.
Rollback seletivo disponível se necessário, preserva contador/privados atuais;
NÃO repetir apply, reverter por rotina ou restaurar backups C20 antigos.

**C30 evidências:** zeros diretos com MESMA rotaSPK_HP/215 mediram≈44033,7frames/s,
audio-clock-audit/silent.rshsx1ml sob build/phase4. Ensaio RAM IRQ55/run-0002,
audio-buffers/session.bvdpctw8, mediu44099,736frames/s/log final sem buffers, mas
usuário pediu repetir por não observar. Repetição explícita session.fr_x6czx/
run-0003/lease600: “Ok tudo certo”, recibo com alvo ativo55/215/1024/IRQ.
Ambas stop/coleta0/mixer/DRM/caches/brilho80/prefs55/70/restauração da fonteglobal
original passaram.9wrapper/9candidate/14transação e20checks do runner C31 passaram.
Guarda !findmnt/set-e foi corrigida para recusa explícita antes do teste; whitelist
transacional passou a permitir só wireplumber.conf, vizinho não planejado recusado.
Falhas host anteriores preservadas. Nenhuma delas autoriza ignorar guardas.

**C31:** stage rootfs-candidate/c25-physical.0af7u42a (latest-c25-physical),
55→56/C25/run-0001/lease180→57/C07. Token56 consumido, firstpaint/navegação
solicitada, settings55/70, IRQ/gain/q efetivos e SSH automático passaram;
áudio físico REPROVADO. Lease/coleta/restauração/FATreadback e fallback57 limpos.
Contrato host valida C30/97 e somente2deltas versusC27; não finge imagem nova.
Não repetir arm/request/fallback. C12 permanece inativo; launcher permanente off.

**C32:** session.3rmqqwti/run-0001 no57/lease600, C22 NORMAL instalado, sem
novos overrides IRQ/gain/q. rate-cycle.sh executado UMA vez,48000→0, limitado25s,
identidade PW/worker e trap de restore. Antes22049,450; forçado23999,718frames/s.
Após restore trigger_time mudou entre amostras: taxa INVÁLIDA, não calcular
sobre resets. Analyzer distingue mesmo owner/trigger e delta válido. Software55,
quantum1024 e force-rate0 confirmados; stop/coleta0 e limpeza final passaram.
SWparams capturados: timestampENABLE, avail_min3072, start_thresholdLONG_MAX,
stop_threshold4096, silence0/0 e boundary2^62. Não houve novo som solicitado,
reboot, gravação de microfone ou configuração persistente por esse diagnóstico.

**Provas novas**, todas dist/phase4, SHA256SUMS conferidos: alsa-irq-ram-preparation
(técnica, audição pendente histórica), alsa-irq-installed (aprovação quente55),
irq-launcher-boot-audio-regression (áudiofalse no56), irq-launcher-fallback,
audio-rate-cycle (diagnóstico negativo no57). Sem rootfs/GPU/raw/backup privado/
segredos. Preservar como imutáveis, não transformar warm55 em boot aprovado.
Imagem privada C27/96 composition.cb2rb8ls/images/rootfs.ext4 permanece histórica,
NÃO inclui C30 nem foi bootada inteira; não forçar pins antigos para a fonte atual.

**Próximo incremento:** reproduzir os SWparams efetivos com libasound e zeros,
sem SDL/PipeWire, uma opção por ensaio (timestamp, avail_min, partida manual/poll).
Aplay direto usava parâmetros software diferentes; hardware/MMAP/formato/período/
buffer/rota já foram comparados. Se necessário utilitário novo, compilar no SDK
isolado e validar ABI/loader antes de RAM, sem instalar na raiz. Depois decidir
startup/kernel pela evidência; não repetir rate-cycle/reboot/calibração/USB ou
baseline ruidosa como tentativa cega. Não habilitar UI permanente/rearmarC12/
resetarcontador/gravarimagem na raizviva. SPL/fones/bateria/energia/suspend/
outros painéis/longa duração continuam não qualificados.

## Marco anterior — C28/C29, boot55 seguro e isolamento inicial

**31/10/2026: áudio após reboot NÃO aprovado.** Boot único com perfil215/quantum1024
abriu menu e navegação corretos, mas usuário confirmou “O som está distorcido
novamente, mas o resto esta ok”. Configuração real estava correta; snapshot
pós-toques mostrou46 linhas de falta de buffers e contador PCM≈22050frames/s
contra44100 declarados. Zero avisos no primeiro snapshot não era aprovação
sustentada. Não aumentar ganho, repetir calibração ou promover imagem como
áudio corrigido após boot. [C28/C29: evidências e próximo passo](phase4-calibrated-boot-audio-clock.md).

**Estado vivo conferido:** boot55/C07, IP192.168.15.8:2222, chave fixada pelo
alias17. Raiz ext4RO/0755, boot-seq55/0600 emdir0700, brilho80, FAT/p3 desmontadas,
taint0,96hashes/payload C22/15/perfil21/C25/5 válidos e rede pronta. Sem UI,
PipeWire/player/arecord/profiler/logger/worker ativo, PCM closed; nenhum mount
debugfs global ou /run/muos-clock.*/muos-c28-profiler.* restante. C25/C12 SEM.once;
recibos48/50/54 preservados. Sem reboot, transação ou teste físico pendente.
Original dArkOSen32GB preservado; Steam Deck limpo/fora do fluxo.
Recibo final: build/phase4/audio-clock-audit/silent.kjral1dx/final-health.stdout,
KERNEL_STORAGE_SIGNATURES=0 e BOOT55_C07_QUIET_ROOT_RO_96HASHES_MIXER_RESTORED_NETWORK_OK.

**C28 concluído:**53→54/C25/run-0001/lease180→55/C07 sem novo pedido de launcher.
Boot/UI/input/lifecycle/cleanup/coleta/restauração e FATreadback passaram;
áudio físico reprovado. Par p3 continua55/70. Stage efetivo
build/phase4/rootfs-candidate/c25-physical.mhdme9fw (latest-c25-physical).
Host ganhou phase4_launcher_trial.py/contrato C27 +23checks de proveniência,
recusas e despacho único. Primeiro arm mmdoszo0 recusou antes de RW/token por
exigir done de fallback no C07 normal; corrigido/registro preservado; não repetir
seus despachos. Nenhum código nativo, perfil, ELF ou imagem foi alterado.
C28 provas dist/phase4/calibrated-launcher-boot-audio-regression (áudio false,
lifecycle true) e calibrated-launcher-fallback, SHA256SUMS conferidos.

**C29 diagnóstico silencioso concluído:** helper original com entrada /dev/zero,
namespace/debugfsRO privados, lock, players limitados12s e mixer byte-exato.
Direto RW S32/S16 default, stage silent.bt7y1e3u em build/phase4/audio-clock-audit:
≈44252,7/44039,6frames/s. MMAP S32/S16 e RW S32 com period512/buffer2048, stage
silent.kjral1dx (latest):≈44071,3/44258,7/44033,7frames/s. Todos próximos44100,
medição uptime10ms/intervalo≈2s, sem precisão elétrica. Esses zeros usaram rota
originalC07 OFF; não equivalem ainda à rota SPK_HP/215 do menu.
C22 temporário normal55/run-0001, audio-buffers/session.a6py0d1b, reproduziu
≈22049,590frames/s SEM toques; metadata1024/codec215. CKR0x00033f3f/div4/64bits
e clock reportado11,2896MHz implicam44100, mas são visão do driver/cache.
Stop/coleta0/restauração/prefs55/70/rede passaram; nenhum novo som foi pedido.

Primeira coleta silent.50_22hut concluiu players/restauração, mas análise falhou
porque aplay deixa ALSA timestamp0. Corrigido para uptime, limpeza de recuperação
confirmada; não usar timestamp0 para taxa. Primeiro comando unshare ausente
recusou sem montar; leitura com mount-namespace já instalado passou/limpou.
Profiler54 gerou auxiliares extras, removidos em followup com whitelist.
Fontes enviadas recuperadas dos heredocs e SHA verificados após colisão host
probe.sh; arquivo agora native-probe.sh, sem repetir players por isso.
Prova dist/phase4/pcm-clock-isolation inclui sucessos/falhas/recuperação,
SHA256SUMS conferido, sem rootfs/blob/áudio raw/segredos. Passou diagnóstico,
NÃO correção de áudio. Host tools em phase4-silent-clock-audit.py e
port/device/rk-r35s-p0/audio-buffers/silent-clock-probe.sh; nenhum deles instalado
permanentemente no cartão.

**Instalação atual continua C27:** latest-update=c26-update._dzvsts7,
experimento C27_VOLUME_CALIBRATION/target c26-source.wfwxb76w, perfilv3/215,
quantum1024, defaults/UIoff. Backup7 públicos private/c24-backup.zmw_itus sob
build/phase4; não executar rollback no estado íntegro nem restaurar C20 antigo.
Imagem privada composition.cb2rb8ls/images/rootfs.ext4, SHA256
6977d8174ec2e89f0f1a4964f1ee533d7720acd47e28b231151ed478534af826,
permanece não gravada/bootada inteira. Counter factory0 nunca substituiu vivo55.
Provas C27 calibram somente a audição estável do52; C28 demonstra regressão
após reboot. Preservar todas como históricas, sem sobrescrever.

**Próximo incremento:** testar zeros diretos com MESMA rota SPK_HP/215 e buffers
do menu, snapshot/restore e sem sons adicionais. Se correto, isolar criação
sink/capture e parâmetros software do PCM antes de alterar startup. Há motivo
concreto: metade só apareceu no caminho completo até aqui; causa física/software
ainda não provada. Não repetir reboots como tentativa cega, baseline ruidosa,
monitor60s, calibração, edição55/70 ou USB. Não rearmar C12/habilitar menu
permanente/gravar imagem sobre raiz viva/resetar contador. Fones/SPL/energia/
bateria/suspend/outros painéis/longa duração seguem não qualificados.

## Marco anterior — C27 imagem integrada e volume calibrado no boot52

**31/10/2026: integração e calibração concluídas.** Perfil v3 instalado com
codec215 e quantum1024 aplicado por S95 antes da UI. Máximo software100:
usuário confirmou “Limpo e máximo adequado”. Validação final do perfil nativo,
sem overrides:0 “Silêncio completo”;65 “Limpo e confortável”. Par persistente
continua55/70, curva cúbica nativa preservada. Não repetir a calibração aprovada.
Detalhes, falhas, fontes e recuperação: [C27](phase4-image-volume-calibration.md).

Console52/C07 base/IP192.168.15.8:2222/chave fixada (alias17), ligado e sem UI.
Última tela: C11 session stopped/manual-stop/result0. Raiz ext4 RO/0755,
contador52/0600 emdir0700, brilho80, FAT/p3 desmontadas, taint0 e rede pronta.
Sem worker/arecord/profiler/áudio/logger pendentes. C25/C12 SEM.once; recibos
usados48/50 preservados. Sem transação/reboot/ação crítica em curso. Original
32GB preservado; Deck permanece limpo/fora do fluxo. Nenhum reboot nesta rodada.
Recibo final em volume-calibration/calibration.3agzv4fb/final-health.stdout,
sob build/phase4: boot52/rootRO/perfil215/96hashes/quiet/rede/erros selecionados0.

**Instalação C27:** oito arquivos públicos (sete existentes + certificado novo),
sem novo ELF/diretório/kernel/DTB/bootloader/partição. Fundação96, payload C22/15,
perfil21 e payload C25/5 conferidos com bytes ATUAIS. Plano em
build/phase4/rootfs-candidate/c26-update._dzvsts7 (latest-update), experimento
C27_VOLUME_CALIBRATION; target c26-source.wfwxb76w. Prefixos c26 são históricos.
Backup7 públicos em private/c24-backup.zmw_itus/original-files.tar sob
build/phase4,600/pai700, SHA/descriptor no stage. Transação14/perfil10 checks
passaram. Não restaurar backups antigos ou exigir hashes anteriores C25/C26.
Rollback seletivo existe para falhas, não executar no estado aprovado.

**Imagem integrada privada final:**
build/phase4/rootfs-candidate/composition.cb2rb8ls/images/rootfs.ext4,
512MiB, SHA2566977d8174ec2e89f0f1a4964f1ee533d7720acd47e28b231151ed478534af826.
latest-composition aponta para esse stage. Macros reais C25+C26/coreS95/perfilv3,
hook final e fundação regenerada;96hashes/payload15 idênticos ao alvo nativo215.
Fsck offline/readback integral/raiz0755/172loadersQEMU/26fixtures passaram.
C07/defaultsoff/SEM token, contador DE FÁBRICA0/600, SEM privados/seed/chaves.
Não gravada nem bootada inteira; contador vivo52 preservado. SDK/base intactos;
sem rebuild integral/garantia bit a bit. Blobs continuam privados em build.
Composição anterior composition.95gyixar/ganho195 é intermediária; prova
rootfs-c25-c26-composition histórica, não usar como imagem final calibrada.

**Ensaios/limites preservados:**195/65/75/85 limpos,100 ainda baixo;205/100 limpo
alto, usuário pediu comparar215;215/100 adequado. Certificado público vincula
hash da observação do máximo ao perfil. Primeira janela0/45s expirou e ficou
inconclusiva; janela180s confirmou silêncio com readback contínuo. Rodada
C22/run-0007 expirou durante100 por prazo calculado tarde na preparação:
result1/checkpoint recusado ANTES de save, mixer/DRM/cache/brilho/raizRO
restaurados byte a byte, prefs não gravadas. Diagnóstico preservado em
build/phase4/audio-buffers/session.ki7r_i3z/failed-lease-collection. Corrigido
para primeiro paint monotônico+570s e mais210s disponíveis antes de cada ponto.
13fixtures do controlador passaram; rodadas posteriores encerraram/coletaram0.
Final nativo: audio-buffers/session.0x_he_be/run-0010 e
volume-calibration/calibration.3agzv4fb sob build/phase4; stop/coleta0,
restauração integral e prefs55/70 confirmados. Nenhum teste físico pendente.

**Provas finais:** dist/phase4/speaker-volume-calibration e
 dist/phase4/rootfs-c25-c26-calibrated, SHA256SUMS conferidos, sem áudio raw,
rootfs/blobs/backup privado/segredos. Provas C25 launcher-once-* e C26
 audio-buffers-correction permanecem históricas/imutáveis. A [C26](phase4-audio-buffers.md)
estabeleceu quantum1024/eliminação do chiado e monitor digital correto; C27
substitui somente a escolha de ganho195 por215 e integra a imagem.

**Próximo incremento:** preparar boot único C25 com S95/perfil215 atuais e
fallback C07. Há motivo concreto: C25 boot/UI/input/fallback48→49 e50→51 foram
aprovados ANTES do áudio C26/C27; essa combinação ainda não teve reboot.
Verificar estado real primeiro; adaptar helpers host ao experimento C27 sem
forçar guardas C25 antigas. Não rearmar C12 nem habilitar menu permanente.
Não gravar imagem inteira sobre raiz viva ou resetar contador/privados.
SPL/fones/música/emuladores/outros painéis/coldboot/energia/bateria/suspend/
longa duração continuam não qualificados. Não repetir baseline ruidosa,
monitor60s, edição55/70, C20 hardcoded60/75 ou USB sem motivo concreto.

## Marco anterior — C24r1 instalado; C07 direto/boot47 aprovado

Console47/C07/IP192.168.15.13:2222/chavefixada(alias17), ligado e quiescente.
Rootext4RO/mode0755/FAT e p3 desmontadas/taint0/brilho80/rede aprovados.
Fundação AGORA89 hashes +payload15 +perfil C10; não exigir o manifesto antigo55.
Sem worker, transação, token ou ação crítica pendente. Original dArkOSen32
preservado. Steam Deck já limpo/fora do fluxo. Par persistente p3 continua55/70.

**C24 instalação seletiva APROVADA:** update.dbsu4g2h instalou56 arquivos/
25dirs no45,18 já iguais pulados.16 fixtures de transação/rollback nv5h9mzu
passaram. Backup21originais em private/c24-backup.1dagpi05/original-files.tar,
modo600/parent700; SHA em backup-descriptor.json do stage. Counter45, seed,
SSH/rede e p3 foram excluídos do write-set. Siblings conferidos antes de commit;
bootstrap/inittab por último. RC0/rootRO/89 hashes/15payload/privados idênticos/
mesmos PIDstarttime da rede passaram. Provas dist/phase4/candidate-update-installed.

BootNORMAL45→46 voltou rede/SSH/rootRO/89 hashes, mas o gate pósboot recusou
counter644: C07direto herdouumask022, enquanto o seletor C12 antes dava077.
Somente modo600 foi restaurado, hash/valor46 intactos. Não confundir esse
retorno reparado com aprovação sem intervenção. Diagnóstico explícito nas provasr1.

**C24r1 APROVADO:** source network-diagnostic/run.sh agora defineumask077 e
chmod600 do tmp antes do mv.7 regressões ybpk24tm reproduzem644 no código
antigo e600 no novo. update-r1.zoj0rcgv aplicou só C07run+hash na fundação89;
13fixtures te7bgjqz passaram (inclui DIRSvazio e recuperação com contador novo).
Backup2originais em private/c24-backup.d3oxb7f_/original-files.tar; descriptor no
stage r1. Privados/counter46/p3 inalterados na aplicação. Provas
 dist/phase4/candidate-update-r1-installed e candidate-update-r1-boot.
RebootNORMAL46→47 passou sem reparo/replug: counter47 root600 emdir700,
C07DIRETO/sem /run/muos/selection/mode,89 hashes/payload15/perfil válidos,
rootRO/rede/chaveSSH/brilho80/taint0/erros selecionadoskernel-storage0 íntegros.
Não repetir apply ou os pedidos de reboot. RAM de instalação desapareceu ao
reiniciar; backups privados independentes ficaram no host. Detalhes [C24](phase4-candidate-update.md).

**Estado de boot/runtime:** inittab despacha C07 diretamente; C12 antigo foi
retido INATIVO para rollback, sem.once/allow_power0. Não usar seus helpers/
marcadorRAM como pré-requisito dos novos ensaios. Guards atuais em
boot-phase4-candidate-update.py e candidate-update/native.sh são independentes.
Defaults enabled0/preferences_enabled0/UIoff. Perfil C10 estático100/80/policy3
é template passivo, sem iniciar S95/áudio na cadeia C07. Sessão opt-in deve
carregar55/70 do p3 emRAM/policy0 e restaurar originais ao sair, como C21/C22.

**Novo candidato privado corrigido:** rootfs-candidate/composition.0bpyh9h_/
images/rootfs.ext4,512MiB, SHA2e9c572f9fbfbf5782e48b3b08d12a0aa1ebe7ee09fe649d502ac870b3e84fb0.
C07+fundação89 correspondem ao r1 instalado; fsck/releitura integral/raiz0755,
305ELF+555módulos/172loadersQEMU e14fixtures tvuvyz__ passaram. Imagem NÃO foi
gravada/bootada inteira; source C23compõe base C07 limpa+macros C10/C22/Wi-Fi+
hook final. Counterfactory0 NUNCA sobrepor ao vivo47. Sem seed/chave privada/
credencial na imagem; pendênciaGPU mantém uso privado/fora dedist. Provas
 dist/phase4/candidate-update-r1-rootfs; C23r0 anterior agora só histórico.
SDKbaseline/base inalterados, sem rebuild completo/bitreprodutibilidade qualificada.

**Próximo incremento:** preparar ensaio próprio de boot de USO ÚNICO da sessão
C22 instalada, preferências55/70 e lease, com C07 no boot seguinte. Não rearmar
C12 nem menu permanente. Planejar seleção/consumo durável/relatórios/rollback e
validar guardas com o contrato C07direto/89 hashes. Instalação/boot47 já aprovados;
não repetir a edição física55/70, store, reboot ou USB sem razão concreta.

**Recuperação:** run-phase4-candidate-update.py rollback --stage permite cada
revisão (r1 antes de inicial), preservando counter/seed/SSH/rede ATUAIS.
Testada em fixtures, não executada nativamente. Não usar no estado aprovado.
Estados parciais desconhecidos recusados; perda elétrica no commit/recuperação
semSSH não qualificadas. Nunca restaurar/recarregar seed no kernel vivo.

**Provas anteriores preservadas:** C21 botões60/75→55/75→55/70, inode novo,
stop/start/reboot42→43→reload aprovados. C22 serviço sem dependência muos-boot,
manifesto15,8fixtures/4Kconfig e sessão43/run0002 com boot oculto aprovados.
C23host r0 detectou/corrigiu templateaudio0 incompatível e contador ausente;
ainda tinha dependência deumask descoberta e corrigida em C24r1. Todos os proofs
antigos imutáveis. Não repetir C20 initialize/verify hardcoded60/75 no cartão55/70.

**Dados/limites:** p3ext4MUOSDATA UUID6d756f73-c020-4000-8000-000000000001,
start1310720/len248561664/PARTUUID4d554432-03. Markers600/prefs700/registrotyped.
Sem repartição/reformat/flash kernelDTBbootloader ou fsck na raiz viva. Brilho
usa0..160 (faixa40..160), volume software0..100. Power/shutdown físico/suspend/
bateria/fones/calibração/longaduração/outros painéis continuam pendentes.
Wi-Fi-only instalado;37/38/39 e boots atuais aprovados, sem reinvestigarUSB.

**Deck/backup antigo:** limpeza concluída (5dirs/671261976bytes/chave da tarefa;
outras chaves e serviçoSSH preservados), recibo dist/phase4/deck-cleanup.
BackupC20 prefix640MiB privado só no host private/c20-backup.*, descriptor em
independent-backup.json do offline-package.b3km738d. Contém seed/credenciais e
rootmodo0777/seed antigos: não distribuir/não restaurar automaticamente.
C24 possui seus próprios backups seletivos; nunca confundir os dois escopos.

## Marco anterior — C19 preparado/testado; persistência real ainda desabilitada

Ler [preparação de preferências](phase4-preferences-preparation.md). Rodada com
saldo limitado: nenhum reboot, menu, remountRW da raiz, alteração persistente,
particionamento ou formatação. Console continua39/C07/IP192.168.15.17:2222/chave
fixada, rootext4RO/FAT desmontada/taint0/brilho80/quiescência/Wi-Fi e55 hashes
conferidos. Política Wi-Fi-only permanece; original dArkOSen32 preservado.
Nenhuma ação crítica em curso e nenhum novo token/serviço pendente.

Inventário real128:249872384setores de512; p1start32768/len204800 (FAT100MiB),
p2start262144/len1048576 (ext4ROOT512MiB), semp3. Primeiro setor após p2:
1310720. Não há dadosrw existentes. NÃO criar p3 com base apenas nesses números:
próxima rodada deve conferir tabela completa/plano/recuperação, preservar
p1/p2/diskid/bootprefixo e preferir operação offline. Nunca fsck na raiz viva.

Código originalMIT port/utils/muos-preferences.c preparado; não integrado ao
C11/C12/firmware. CLItyped init/load/save num diretório root0700 marcado600,
sem links; registroversionado único volume0..100/brilho40..160. Defaults100/80
só se ausente; inválido não é sobrescrito. Flocknão bloqueante→stagingexclusivo→
fsyncarquivo→rename→fsyncdiretório; erro apósrename retorna74/durabilidadeincerta,
não faz rollbackfalso. Sem cache/ready/PIDs/rotas/ganho/seed/credenciais no store.
Contrato port/device/rk-r35s-p0/preferences/contract.json continua enabledfalse.
O adaptador de identidade/mount/ext4 ainda NÃO existe; não usar como serviço.

16 fixtures AArch64 em tmpfs real/QEMU passaram, incluindo links/formato/
lock/corrupção e falhas antes/depoiscommit; SDKconfig preservada. Stage
build/phase4/preferences/checks.6hmt3nzp (latest-checks). Primeirafixturevkm0szva
recusou por prefixo/ doQEMU; corrigidoharness via loaderexplícito, sem relaxar
segurança do helper. Só binário produção deve ser usado: variante -DPREFS_TEST
com injeção de falha NÃO pode ser implantada.

Teste nativo breve em /run passou (native-analysis.json): init100/80, save60/75,
novo init/loadpreservaram60/75 e101 recusado64. Não aplicou valoresao hardware;
brilho80 antes/depois. Binário/dados RAM removidos e rootRO/rede preservados.
Isso prova ABI/IOemtmpfs, NÃO persistênciaext4, reboot ou rootRO durante menu.
Provas/contrato/plano em dist/phase4/preferences-preparation com SHA256SUMS.

**Próximo:** qualificar mount ext4 de laboratório rw com rootglobalRO e
ownership/cleanup (imagemRAM/loop em namespaceprivado é opção, validar suporte
antes). Testarstoreporunmount/remount. Depois preparar dados reais/offline e
integraroptin aoC11 com RAMoverrides. Não apagarremountRW do worker ainda:
S90precisa /userdataRW eS80restaura /etc/asound.conf e/usr/share/alsa/alsa.conf;
auditar/bindar todos os rootwriters antes. PerfilC10/21 originais intactos.

Política3 força100. Política0 usa salvo, mas LOAD_SINK_VOLUME pode sobrepor
valor global: reconciliar slotdospeaker/volumeRAM antes da aplicação. Brilho
é unidade0..160, primeiroteste guarda40..160, não porcentagem. Validarvolume60/
brilho75 atravésstop/start/reboot somente após storage/lifecycle preparado.
Manterlease/menupermanenteoff, Wi-Fi-only e C12inativo; não rearmarC12 nem
assumir infraestruturaC07/recarregarseed. Wi-Fi37/38/39 já aprovado: não repetir
investigaçãoUSB. Não iniciar teste longo enquanto orçamento não for restaurado.

## Marco anterior — Wi-Fi automático aprovado no37/38/39; política estável instalada

Ler [controleUSB/políticaWi-Fi-only](phase4-usb-control.md). Console teste128 noOS,
original dArkOSen32 preservado/guardado, segundo slot vazio, dongle conectado.
SSH192.168.15.17:2222/chave fixada, último boot39/C07. Rootext4RO/FAT desmontada/
taint0/brilho80/quiescência/rede pronta; todos55 pré-requisitos e hashes públicos
anteriores íntegros, contagem selecionada kernel/storage0. Nenhuma ação crítica
em curso. Usuário confirmou37/38/39 sem retirar o dongle; nenhum recover foi usado.

**Correção de bancada mantida:** bloquear alias autoload de btusb evita a
inicializaçãoHCI automática do composto neste kernel/dongle. Bluetooth USB fica
sem suporte/autoload, inclusive outros adaptadoresbtusb desta imagem. Não é
bloqueio de modprobe manual. Não habilitarBluetooth por outro init sem novo
ensaio. Validado só Panel0/0bda:c820/kernel4.4.189, três reboots quentes; coldboot
com pacote final/longa duração ainda não medidos. Causa interna exata do comando
HCI que bloqueia EP0 não foi decodificada; não alegar isso como demonstrado.

Novos arquivos persistentes SOMENTE: etc/modprobe.d/90-muos-r35s-wifi-only.conf e
usr/share/licenses/muos-r35s-wifi-only/LICENSE (root644/hash/licença conferidos).
Não remover essa política aprovada como se fosse trial. Fonte em port/device/
rk-r35s-p0/wifi-only; pacoteBuildroot opt-in muos-r35s-wifi-only, fragmento
phase4-wifi-only.fragment. Macro real instala só esses dois arquivos; Kconfig
separado defaultoff/optinpassou, SDKconfigbyteidêntica. Nova imagem inteira não
foi reconstruída. Kernel/DTB/bootloader/partições/módulos/libs/init/perfil/ELFsC11
não alterados. Tabela55/SHA/USBhelper C07 voltaram aos bytes aprovados.

C18/37 semBTnovo passou;38 comBTausente dosdoislados passou. Política temporária
foi promovida ao payload estável;39 também passou, mesmo reset/probe originalC07,
mesma chave/IP, sem qualquer replug. Stage bt-isolation.khs5p7ey; pacote
wifi-policy-build.bxac7so2; promoção/final wifi-policy.jdhc3olf em
build/phase4/network-warm. Arquivo trialC18 removido, não executar cleanupC18antigo.
Fontes/ações/confirmacões/analyses/recipe/finalSHA preservados. Coletor final teve
só erro de escapingawk após checar rede/hashes/FAT; fonte negativa preservada,
leitura corrigida terminou com erros0 e testeawkAArch64 contou2assinaturasfake.
Não houve outro reboot para corrigir coleta.

C16/35 qualificou probe próprioIN: baseline/replug seteMATCH1; estado retido
post-helper sete-110, inclusive controlesUSB padrão. Pre-probe35 recusou64 sem
saída: estado ANTES do helper não medido, motivo da guarda não identificado.
C17/36 retirouDWC2 enquantofuncionava ANTES doPID1 (C17PREdurável comRC0), mas
NÃO resolveu; replug foi necessário. Trials removidos; não repetir como hipótese
nova reset/reprobe/unload/parada/config0→1/DWC2apósfalha/retiradaDWC2antesreboot.
Fontes control.dexdwque, pre-shutdown.9jl4ldqy;24checks (7AArch64+8wrapper+9ordem)
e shell/loader passaram. Nenhum C16/C17/helper/token/probe ficou instalado.

Provas imutáveis com SHA256SUMS em dist/phase4/usb-control-observation,
usb-pre-shutdown-negative, wifi-bt-isolation e wifi-only-policy. Nada de payloadUSB,
dmesg bruto, MAC/SSID/PSK/seed/chave privada exportado. Último fsck offline após21;
22..39 pendentes. Nunca fsck na raiz viva. Sem manipulação direta de GPIO/EEPROM/
registrador; trials de controlador usaram callbacks existentes e foram retirados.

C12/energia30→31 continua aprovado, instalado mas inativo noC07: c12.once ausente,
c12.used permanece, defaultC07/allow_power0, sessão90s; não rearmar/começarC12noC07
nem assumir infraestrutura/recarregarseed. Não aprovar Power/suspend/poweroff
físico/menu permanente/calibração por estes testes de rede.

**Próximo:** dadosrw com root globalro, defaults só no primeiro uso e preferências
volume/brilho persistentes antes de removerlease/habilitar menu permanente.
Manter o pacote Wi-Fi-only selecionado nas futuras receitas/ensaios; não voltar
à investigação do dongle sem regressão concreta ou novo escopoBluetooth.
Áudio baixo/escalaUI, bateria/suspend/fones/conteúdo/licenças completas/longa
duração seguem abertos. Não usar dois chats modificando o console em paralelo.

## Marco anterior — C17/boot36 retirada DWC2 ANTES do reboot em curso

Ler [controle USB](phase4-usb-control.md). C16/35 comprovou post-helper com
TODOS sete controlesUSB (padrões e vendor) em timeout-110; após replug, todos
passaram. Baseline34 durável conferida; pre-probe35 recusou64 sem saída, logo
não medir/atribuir o estado ANTES do helper. Usuário precisou replug. Log3,
rootRO/FAT desmontada/taint0/55 hashes do trial passaram, original32 guardado.

C16 ainda instalado TEMPORARIAMENTE (usr/libexec/muos-c16, USBwrapper e tabela55
com só hash do wrapper/SHA atualizado). Stage control.dexdwque, builder3xa7w1ka,
checks8+7. Não fazer cleanup enquantoC17 estiver em curso: depende desse probe.
C12 continua inativo/sem token/allow_power0; kernel/DTB/init/libs/módulos intactos.

C17 stage build/phase4/network-warm/pre-shutdown.9jl4ldqy. Baseline35 sete leituras
OK, salva em DIAG09/BOOT0035/C16PRE.TXT. Native/scriptRAM de pre-shutdown, nove
fixtures/shellAArch64. Lançamento explícito já agendado: snapshotPID da rede→
stopC07→unbindDWC2→ausência→C17PRE durável/sync/readback/desmontagem→checagemfinal
→PID1. Só único controlador/dongle trabalhando, nada de GPIO/registradores diretos.
Diferença temporal em relação aoC15: ANTES, não depois, de o periférico falhar.
Falha de qualquer passo bloqueiaPID1 e tenta restaurar vínculo/rede/tokens.

c16.used anterior foi movido para var/lib/muos-diagnostic/c17.c16-used, UMA nova
observaçãoC16 foi armada para36; isso não rearmaC12 nem relê seed no mesmo boot.
NÃO repetir launch/boot: marcadores existem. Usuário instruído a manter dongle
até tela pedir fallback. IP192.168.15.17:2222/chave fixada. Se não houve reboot,
conferir tela e preservar energia antes de agir; execução emRAM pode ter abortado.

Após SSH: audit-phase4-usb-pre-shutdown.py collect --stage caminhoCompleto9jl4ldqy
--host192.168.15.17 (separar argumento com espaço). Coletor confere C17PRE35 e
observações/baseline/FAT/C07 no36. Depois cleanup noMESMOstage remove token
retirado e chama cleanupC16 que restaura USBhelper/tabela55/SHA anteriores.
Não promover hipótese a correção antes da evidência e confirmação física.

## Marco anterior — C16/boot35 comparação USB em curso

Ler [controle USB](phase4-usb-control.md). Ensaio em curso. Baseline34/C07
conferida:rootRO/FAT desmontada/taint0/55 hashes, original32 guardado/teste128,
IP192.168.15.17:2222/chave fixada. Nenhum C12/token/menu ou operação de energia
nova. Não repetir reset/configuração/DWC2 já negativos.

Stage build/phase4/network-warm/control.dexdwque, builder control-build.3xa7w1ka
(7 checksAArch64/loader/ELF ABI4.4), wrappercontrol-checks.4zs8ipbr(8).
Binário próprio MIT só sete requestsIN fixos (descriptor/config/status,
chipID0xfc, três padrõesdepois), sem endereço/pedido livre, OUT ou reset.
Dados retornados não são exportados, apenas RC/tempos/MATCH. Baseline nativa
seteRC/comparações corretos, rede preservada, salva/sync/readback/desmontada
em DIAG09/BOOT0034/C16PRE.TXT.

Wrappertemporário USB C07 com tokenc16.once→used (600, syncantes); C07 guarda
pre/post no REPORT público/FAT antes de recovery físico. Tabela55 só muda hash
esperado do helper e SHA da tabela. Kernel/DTB/init/libs/módulos/perfil/ELFsC11
não alterados; binário de probe e originalUSB em usr/libexec/muos-c16.
Reboot34→35 já solicitado; NÃO repetir boot (reboot-attempted no stage).
Usuário deve deixar dongle e replug apenas se tela pedir fallback.

Depois SSH: audit-phase4-usb-control.py collect --stage (caminho completo de
control.dexdwque) --host192.168.15.17 (separar argumento com espaço). Módulo
usb_control_actions.py participa e está congelado no stage. Coletor verifica
REPORT naFAT/baseline durável e lê de novo após replug observado. Então cleanup
restaura USBhelper/tabela55/SHA originais e remove trial/token. Não promover
mudança de timing/leituraisolada a fix sem evidência. Se falhar, preservar
aparelho ligado e conferir a tela com usuário antes de qualquer reset.

## Marco anterior — C13 diagnóstico localizado; C14/C15 negativos; C07/34 seguro

Ler [warm Wi-Fi](phase4-network-warm.md). Console teste128 ligado no OS,
original dArkOSen32 preservado/guardado, segundo slot vazio, dongle conectado.
SSH192.168.15.17:2222/chave fixada, boot34/C07/rootext4RO/FAT desmontada/taint0,
brilho80/quiescência/rede pronta. Todos os hashes públicos anteriores e55
pré-requisitos foram restaurados; zero assinaturas selecionadas kernel/storage,
DWC2 reset-timeouts0. Nenhuma ação crítica em curso.

**Não existe correção automática aprovada:** replug físico foi necessário em
32/33/34. C13 elevou log8821cu para4 por UM boot e localizou a falha: dez
transferências vendor de leitura do identificador SYS_CFG2/0xfc com USB-110,
HALMAC54 duas vezes ANTES de chip-info.54 é CHIP_NOT_SUPPORT por leitura falha,
não prova hardware incompatível. Filtro emAArch64 só exportou rótulos/contagens/
tempos/statusnuméricos, nunca dmesg bruto ou dados privados. Log4 removido,
parâmetro runtime3. Buffer observado desde0s, sem perda dos eventos iniciais.

C14/33 tentou SET_CONFIGURATION0→1 (RC0/0), sem driver/netdev; restore1RC0.
C15/34 tentou lifecycle do único controlador DWC2/ff300000.usb (unbind0/bind0),
sem driver/netdev; restore-bind0. Usuário confirmou replug nos dois. Resultados
NEGATIVOS: não promover nem repetir essas hipóteses como novas. Fontekernel
mostra remove com teardown PHY/recursos/reset opcional; shutdown só disable_irq.
C15 ocorreu DEPOIS da falha, não antes do reboot. PatchROCKNIX de HANG/PM não
é sustentado pelos contadores atuais.

Três trials terminaram com cleanup comprovado. HelperUSB C07, tabela55 e SHA
da sessão voltaram aos bytes aprovados; muos-c14/muos-c15 e tokens once/used
foram removidos. ConfigmodprobeC13 ausente. Nenhum kernel/DTB/bootloader/partição/
lib/módulo/perfil/ELF/init mudou. Root foi selada após cada instalação/cleanup.
37 checks host (5 filtroAArch64+20 C14+12 C15) e shellAArch64 passaram. Não se
repete UI/DPAD/áudio nesta rodada. Sem manipulação direta de GPIO/VBUS/registrador/EEPROM (C15 usou callbacks
existentes do kernel), geração de chave/releitura de seed no recover ou fsck
na raiz viva.

Stages em build/phase4/network-warm: probe.nsbst7kz (32),
reconfigure.0y8luql1 (33), controller.i16vj5bd (34); fontes/ações/preimages públicas
congeladas em cada um. analysis/collection-analysis e cleanup-analysis registram
resultados separadamente. Provas imutáveis com SHA256SUMS em dist/phase4/
network-warm-probe, network-reconfigure-trial e network-controller-trial.
Último fsck offline após21;22..34 ainda pendentes. Nunca fsck na raiz viva.

C12/energia30→31 segue aprovado no recorte anterior, instalado e inativo neste
bootC07; tokenc12.once ausente/c12.used permanece, defaultC07/allow_power0,
sessão90s. Não rearmar C12 ou chamar seu start no C07 automaticamente. Isso
não pode assumir infraestrutura alheia/recarregar seed. Poweroff físico/Power/
suspend/menu permanente/calibração/longa duração continuam sem aprovação.

**Próximo:** auditar transição ANTES do reboot e distinguir controle USB padrão
versus vendor no estado retido, com probe de leitura de pedidos conhecidos e
relatório filtrado/durável antes do replug. Eventual teste de lifecycle DWC2
no shutdown precisa diferença temporal/hipótese explícita; C15 só tentou após
falha. Reset/reprobe/unload/parada ordenada/config0→1/cicloDWC2 já falharam;
não repetir sem evidência/diferença concreta. Não forçar chip-ID/RFE/efuse.
Powercycle VBUS somente após comprovar circuito/consumidores, nunca por nomes
boost/otg_switch. Preservar recovery físico, privados e original32. Preferências
persistentes/rootRO ficam após esse bloqueio prioritário. Não usar dois chats
modificando o mesmo console.

## Marco anterior — C14/boot33 reconfiguração USB em curso

Ler [warm Wi-Fi](phase4-network-warm.md). Stage C13final probe.nsbst7kz:
boot32 localizou HALMACstatus54/identificação do chip após10 timeouts USB-110
na leitura0xfc. Não é evidência de hardware incompatível. Log4 temporário foi
removido; runtime3 e todos55 hashes/rootRO/rede passaram. Original32 guardado.

Stage de ensaio C14: build/phase4/network-warm/reconfigure.0y8luql1.
SSH192.168.15.17:2222/chave fixada. Instalação/token e shellAArch64 passaram;
20 fixtures host. Reboot32→33 solicitado, NÃO repetir boot (marcador no stage).
Usuário foi instruído a NÃO tocar no dongle, exceto se tela pedir fallback.

Única hipótese nova: SET_CONFIGURATION0→1 no c820 composto/3interfaces com
Wi-Fi desvinculado e sem rede/UI/BlueZ. Sem GPIO/VBUS/registrador/EEPROM,
reset em loop ou driver novo. Wrappertemporário no helperC07 chama original,
consome c14.once→used/sync uma vez e tenta reconfiguração com prazos/restore1.
Sem token chama só original. muos-c14 contém cópia pública original e helpers.
Tabela55 mantém todas as entradas, muda apenas hash do helperUSB; SHA da sessão
regenerado. Binários/perfil/init/kernel/DTB/partições/libs não mudaram.

Após SSH, ação collect no stage coleta relatórioC14 eC07. Se automático,
exigir confirmação do usuário sem replug. Se falhar, fallback físicoC07 intacto.
Depois cleanup RESTAURA helperUSB/tabela55/SHA anteriores e remove helper/token
C14, ainda que piloto falhe. Não promover ensaio a correção permanente sem nova
integração explícita. Root deve voltarRO/FAT desmontada/taint0; não rearmarC12
ou recarregar seed. Fontes/ações/preimages públicas congeladas no stage.

## Marco anterior — C13/boot32 diagnóstico de probe em curso

Ensaio em curso: ler [warm Wi-Fi](phase4-network-warm.md). Stage
build/phase4/network-warm/probe.nsbst7kz, fonte executada audit-phase4-network-warm.py
congelada no stage. Baseline31/C07/IP192.168.15.17:2222/chave fixada, rootRO/
FAT desmontada/taint0/sem sessão ou tokenC12 foi conferido, hashes preservados.
Original dArkOSen32 guardado; somente cartão128 autorizado.

Mudança temporária ÚNICA: /etc/modprobe.d/muos-c13-warm-probe.conf,
options8821cu rtw_drv_log_level4; instalação/hash/modo/kmod-c passou. Demais
scripts/binários/init/kernel/DTB não alterados. Reboot31→32 já solicitado
para observar a falha com RTW_INFO visível, não para repetir reset como fix.
Não repetir boot: reboot-attempted já existe. Usuário deve reinserir dongle
quando C07 pedir; não haverá launcher. Não rearmar C12/recarregar seed.

Após SSH voltar, ação collect do script no mesmo stage/--host192.168.15.17
(separar argumento com espaço) coleta somente eventos classificados e relatórios
públicos. Nenhum dmesg bruto deve ser exportado. Depois cleanup remove somente
config com hash conferido e volta parâmetro runtime3/rootRO. FiltroAWK tem cinco
casos no BusyBox AArch64 real. Não concluir causa/correção antes da coleta.
Preservar aparelho ligado se não retornar e conferir tela com o usuário.

## Marco anterior — energia durável30 e retorno C07/31 aprovados

Ler [energia durável](phase4-boot-power.md); seleção em
[boot único](phase4-boot-once.md), infraestrutura no [coordenador](phase4-boot-coordinator.md).
Console ligado com teste128 no OS, original dArkOSen32 preservado/guardado,
segundo slot vazio. SSH192.168.15.17:2222/chave fixada. Boot31/C07, rootext4RO,
FAT desmontada/taint0,55 pré-requisitos e todos os hashes instalados íntegros,
sem sessão/UI/D-Bus e zero assinaturas selecionadas de erro kernel/storage.
Usuário reconectou dongle após30 e31. Nenhuma ação crítica em curso.

C12 e seletor continuam instalados. Atualização dirigida trocou somente
power-functions.sh (novo), service/order/native-functions/diagnostic-save.
Inittab/configs/kernel/DTB/bootloader/partições/libs/módulos não alterados.
Pedido c12.once consumido no30; c12.used permanece. NÃO rearmar/repetir C12
nem chamar start no C07 automaticamente; isso não pode assumir infraestrutura
alheia/recarregar seed. Receita enabled0/allow_power0. Config instalada
enabled1/recover_network1/allow_power0 e sessão90s fica inativa sem token.
Habilitação de energia deste ensaio existiu somente emRAM e sumiu no reboot.

116 checks host (20 ordem+32 adapters+35 diagnóstico+29 energia/update), macro
real/loader/shell AArch64 e atualização dirigida passaram. Stage final
build/phase4/boot-order/power-test.feak98w7, coordenador57ed__3c, power-checks.tobo6nyg.
Cinco ELF/perfil aprovados preservados. Negativa9ac7v5on falhou no manifesto
relativo fora de /; rollback0 restaurou todos os bytes/rootRO/rede, sem token
ou reboot. Corrigido cd / e adicionada regressão do comando real do wrapper.
Prova negativa separada; não repetir a instalação em stage já executado.

Boot30: warmrede falhou; recovery físico passou com ownership novo e RNG atual,
sem releitura de seed. Launcher confirmado pelo usuário. Recusa nativa de
energia durante diagnóstico retornou64, sem power state/pedido/perda de rede;
C07 também recusou64 sem criar coordenador. Lease90/result0,21 hashes efetivos/
21 originais, mixer/brilho80/DRM/volume-store e quiescência/rede própria passaram.
Não repetimos DPAD/áudio já aprovados; calibração acústica continua pendente.

Reboot controlado30→31 passou PELO novo controlador. Antes do pedido ao PID1,
PBEGIN e PREADY foram salvos/sync/readback/desmontados; os seis passos de parada
RC0 constam em DIAG10/BOOT0030/PREADY.TXT. Após31, leituraRO comprovou persistência,
sem PFAIL; START/FINAL idênticos à coleta30. PREADY registra intenção/preflight,
não prova isoladamente a syscall ou poweroff físico. Boot31 prova o retorno.
Nenhuma aprovação de botão Power/suspend/desligamento físico ou menu permanente.

boot-analysis.json é pré-energia; power-analysis.json é o resultado final.
Provas imutáveis com SHA256SUMS em dist/phase4/boot-power-preflight,
boot-power-native e boot-power-update-rollback. Nada de seed/PSK/chave privada
exportado. Último fsck offline após21;22..31 ainda pendentes. Nunca fsck na raiz viva.

**Próximo, conforme usuário:** corrigir recuperação automática USB/Wi-Fi após
warm reboot, que ainda exige reinserção física. Reset/reprobe/unload8821cu já
falharam; stop de rede/udev agora comprovado também não resolveu. Exigir hipótese
nova/diferença causal concreta antes de repetir ensaios. Preservar recovery
físico/credenciais/chave e original32. Depois dadosrw com rootro/defaults uma
vez/preferências volume-brilho persistentes antes de remover lease/habilitar
menu permanente. Áudio baixo/escalaUI/bateria/suspend/fones/conteúdo/licenças/
longa duração seguem abertos. Não executar dois chats modificando o console.

## Marco anterior — C12/boot27 aprovado; retorno C07/boot28 confirmado

Ler [boot de uso único](phase4-boot-once.md) e [coordenador](phase4-boot-coordinator.md).
Console com teste128 no OS, original dArkOSen32 guardado, segundo slot vazio,
dongle conectado. SSH192.168.15.13:2222/chave fixada, root ext4RO, FAT desmontada,
taint0, sem processos de sessão muOS ou D-Bus. Último boot28 selecionou C07;
usuário reconectou dongle e saúde foi conferida. Nenhuma ação crítica em curso.

C12 instalado em usr/libexec/muos-boot e muos-session, dois defaults e
usr/share/muos-r35s-boot. /etc/inittab agora chama select.sh start/stop, com
as demais linhas C07 intactas. Default do seletor é C07. O pedido root600
/var/lib/muos-diagnostic/c12.once foi CONSUMIDO no27; c12.used permanece.
Não rearmar/repetir C12 automaticamente. Defaults da RECEITA seguem0;
configs da bancada instalada enabled1/recover_network1/allow_power0, sessão90s.
Sem token, essas configs não habilitam menu no boot C07. Não chamar C12 start
no boot C07: não pode assumir sua infraestrutura ou reler seed.

88 checks host (20+33+35), macro/shell AArch64 e instalação dirigida passaram.
Stage final build/phase4/boot-order/boot-test.mp19ei2w, coordenador7j2f32yp,
diagnostic-checks.mbg52i6k. Pré-requisito C11 preserva todos55 hashes, mudando
somente o hash esperado da inittab selecionada; cinco ELF/perfil permanecem
os aprovados. Primeira tentativa zw07_f5k ficou no preflight por dirname('//')
não terminar; processo5644 encerrado porTERM, rootRO/nenhuma escrita habilitada.
RAM anterior removida; regressão corrigida/prova negativa preservada.

Boot27: entropy/udev/USB passaram; rede inicial falhou por warmboot conhecido.
Uma retirada/reinserção física recuperou, registrando PID/starttime/exe NOVOS.
Sem reload de seed; só consulta RNG atual. Menu90s/DPAD/A/B/Fn confirmados;
usuário ouviu áudio baixo. SPK_HP/157 e software1.00 ativos comprovados;
calibração acústica NÃO aprovada. Lease expirou0,21 hashes perfil/21 originais,
mixer/brilho80/DRM/volume-store/55 pré-requisitos e quiescência passaram.
START/FINAL da FAT DIAG10/BOOT0027 conferiram comRAM e sobreviveram ao reboot28.
Token consumido fez28 selecionar C07 sem menu; replug físico foi necessário
novamente. Chave SSH igual, rootRO/FAT desmontada/taint0/erros selecionados0.

boot-analysis.json, native/, install-analysis.json, fallback-health.stdout e
confirmações no stage final. Provas imutáveis dist/phase4/boot-once-preflight,
boot-once-native e boot-once-root-path-preflight-failure. Nada de seed/PSK/chave
privada exportado. Kernel/DTB/bootloader/partições/libs/módulos não alterados.
Último fsck offline após21; não após22..28. Nunca fsck na raiz viva.

**Próximo:** qualificar preflight de energia/encerramento com prova durável
ANTES do pedido ao PID1; o retorno28 por si só não prova o resultado de cada
passo de shutdown perdido emRAM. Depois dadosrw com rootro e preferências/
volume/brilho persistentes, antes de remover lease/habilitar menu permanente.
Áudio baixo/escala UI e warmWi-Fi seguem pendentes; reset/reprobe/unload já
falharam. Bateria/suspend/fones/conteúdo/longa duração/licenças também abertos.

Para retomar em NOVO CHAT, abrir o mesmo projeto e pedir: “Leia AGENTS.md,
este checkpoint, roadmap.md e phase4-boot-once.md. Confira o estado real do
console antes de agir, preserve o dArkOSen original e retome o próximo
incremento registrado.” Não executar dois chats modificando o mesmo console
em paralelo. As decisões estão nos arquivos; não é preciso copiar o histórico.

## Marco anterior — C12: adaptadores host e barreira nativa aprovados

Em2026-10-28, [C12](phase4-boot-coordinator.md) avançou para adaptadores reais,
controlador start/status/check-stop/prepare-stop/shutdown/reboot/poweroff,
receita opt-in e template inativo de inittab.20 checks de ordem e33 de
controle/identidade/quiescência, macro real, loader/QEMU e Kconfig isolado
passaram. O pacote mantém enabled0/allow_power0 e NÃO substitui /etc/inittab
nem instala S?? concorrente. SDK compartilhado confere com baseline.

No console, check-stop passou em idle, recusou com menu ativo sem pará-lo,
e passou após stop/cleanup C11. Configuração desabilitada não criou estado
C12; energia e tentativa de assumir infraestrutura C07 foram recusadas64.
Usuário confirmou “estou vendo”. C11 run-0001/lease60, worker857/start62600,
firstpaint637.60, stop manual0.21 hashes de perfil e21 originais, mixer,
brilho80, DRM, volume-store e ausência de writers passaram. Rede/udev mantiveram
PID/starttime; rootro/FAT desmontada/taint0. RAM /run/muos-c12.DzUEL2 e estado
/run/muos/session removidos após coleta. Não houve reboot/C12 em boot/shutdown
nem instalação C12 persistente. Cache/restore C11 foi executado; não afirmar
identidade byte a byte de todo o filesystem.

Console continua com teste128 no OS, original32 guardado, segundo slot vazio,
dongle conectado. **IP atual192.168.15.13:2222**, informado pelo usuário e
verificado com a mesma chave pública fixada. Usar:

```sh
ssh -p 2222 -i build/phase4/private/c07-client \
  -oIdentitiesOnly=yes -oStrictHostKeyChecking=yes \
  -oHostKeyAlias='[192.168.15.17]:2222' \
  -oUserKnownHostsFile=build/phase4/private/c07-known_hosts \
  -oBatchMode=yes root@192.168.15.13
```

Não mudar known_hosts para acomodar IP. Cartão permanece C06r4+C07r3.
Coleta final confirmou BOOT_SEQUENCE=26; o aparelho já estava nesse boot
ao retomar, sem reboot solicitado nesta rodada.
Warm Wi-Fi ainda requer reconexão física; reset/reprobe/unload já falharam.
Nenhum processo/build/gravação crítico em andamento. Último fsck offline foi
após21, não após22..26/rodadasRAM. Nunca fsck na raiz viva ou exportar/hashar
seed/PSK/chaves privadas.

Stages build/phase4/boot-order/: checks.huc6ivzq, adapters-checks.a2cqpw3v,
kconfig.edxi7sfh, coordinator.hvxl0yxe; ponteiros latest-*. Pacote/fonte/receita
C12 testados em coordinator.hvxl0yxe. audit-executed.py preserva exatamente o
script nativo; fonte posterior só esclarece metadado de instalação C12 versus
transação C11. Provas imutáveis dist/phase4/boot-coordinator-preflight e
boot-coordinator-native, SHA reconferidos.

**Próximo:** wrapper diagnóstico C12 com tela/logs públicos duráveis e recuperação
física de rede com ownership/identidades C12, depois seleção ativa/rollback em
cópia host. Não chamar recover à parte sem registrar os daemons: stop C12
corretamente os recusaria como alheios. Só após isso instalar incremento de
boot com lease no cartão identificado, preservando recuperação C07. Não ativar
a inittab com enabled0 nem rcS inteiro. Reboot/shutdown pelo C12 ainda precisam
de teste físico separado; script SHUTDOWN não veta TERM/KILL do BusyBox.
Depois de network.stop não se garante SSH diante de erro posterior.

Persistência continua false/volatile; política3 C10 força volume100. Dadosrw
com rootro, defaults uma vez, retenção de logs, volume/brilho salvos, sessão
permanente, calibração, Power/suspend/bateria/fones/conteúdo/longa duração e
licenças privadas finais continuam abertos.

Os registros abaixo são históricos; o estado corrente está acima.

## C12 — preparação host anterior com orçamento de7%

Rodada com7% de orçamento: nenhum SSH, teste interativo, build de imagem,
instalação ou gravação no dispositivo foi feito. Último estado do aparelho
é o confirmado ao fim do C11 abaixo; verificar ao retomar, sem assumir estado
atual da rede por esta anotação. Nenhum processo/build crítico em andamento.

Preparados boot/order.sh e boot/contract.json: biblioteca de callbacks,
SEM adaptadores nativos/inittab, não integrada a receitas ou serviços.
Vinte fixtures host passaram; prova boot-order-host-preparation e stage
boot-order/checks.9xqwux0f. Ler phase4-boot-coordinator.md antes de implementar.

Decisão: ownership única, sessão antes de rede/udev no preparo do shutdown,
sem recarregar seed no mesmo boot; UI offline só após limpeza parcial da
rede. Persistência continua false/volatile. Política3 C10 ainda força100:
não afirmar que binds persistentes guardarão o volume sem alterar/testar política.
Flags de runtime/cache/mapping nunca devem virar configurações persistentes.

Achado crítico BusyBox init.c:758–775: script shutdown que falha não impede
TERM/KILL posteriores do PID1. Checagem abortável deve preceder o pedido de
reboot/poweroff; não prometer manter SSH se PID1 já iniciou shutdown.
Próximo: adapters/guards, montagem/inittab em cópia host e teste do caminho
com falhas antes de qualquer ensaio real. Não instalar esta biblioteca como
coordenador pronto. Não habilitar rcS inteiro/UI permanente nem persistência.

## Marco anterior — C11 aprovado; sessão parada e SSH ativo

Teste128 no slot OS, original dArkOSen32 guardado, segundo slot vazio,
dongle conectado. Mesmo BOOT0025 recuperado, kernel4.4.189-muos-r35s-p4,
Panel0/PID1BusyBox. SSH2222 com chave fixada funciona. Raiz ext4ro, FAT
 desmontado, taint0, backlight80/max160. Menu/core/áudio/input/D-Bus próprios
parados, sem writers/socket órfão. PacoteRAM C11 e estado /run/muos/session
coletados/removidos após verificar saída das três gerações. Nenhum build,
gravação ou teste crítico em andamento. Cartão continua C06r4+C07r3; nada
C10/C11 foi instalado permanentemente e autostart permanece desabilitado.

### C11 — serviço independente start/status/stop

Ler [C11](phase4-session-service.md). Código em
port/device/rk-r35s-p0/session/, pacote muos-r35s-session e fragmento opt-in.
Não depende de executores C06/C09; possui cinco utilitários próprios (namespace,
bounded,RNGready,rootwriters,DRMprobe), compilados no SDK AArch64/Cortex-A35 e
conferidos contra libs da candidata. Usa perfil C10 congelado. Defaults
serviceenabled0/lease180; S98 é adaptador, sem habilitar rcS inteiro.

Oito fixtures de cadeia e dez de controle passaram: ordem/reversão, paradas
parciais, idempotência, restart/identidade, PID alheio não sinalizado,
transação suja/leases inválidas/namespace125. Macro real compilou/instalou
binários/scripts; Kconfig isolado confirmou perfil/libdrm. Nenhuma imagem
inteira ou rebuild de dependências/SDK. .config anterior permanece baseline.

Três gerações nativas no mesmo boot passaram:
- run-0001/lease120: start0/status0, segundo start manteve PID/geração;
  usuário “Tudo correto” em navegação/Informações/Configurações/ajuda/áudio.
  stop explícito0 em6,19s, status3; segundo stop0.
- run-0002/lease30: novo worker/firstpaint, encerrou sozinho0/lease-expired;
  usuário não viu a abertura, sem confirmação visual. Evidência preservada.
- run-0003/lease60: novo worker/firstpaint, usuário “Estou vendo”; encerramento
  autônomo0/lease-expired e status3. Repetição atendeu pedido de conferência.

Todos21 hashes do perfil ativos pré-core e21 originais depois passaram,
mixer/volume-store/backlight/DRM iguais ao snapshot e cache reconstruído.
Infraestrutura rede/udev manteve PID/starttime. 45probesSSH, 38com sessão ready;
coleta do ciclo2 começou após expiração (não aprovar simultaneidade contínua
nesse ciclo). Kernel/storage selecionados0, sem processos próprios/writers,
rootro/FAT desmontado/taint0 ao fim. Não houve fsck offline após22..25;
último fsck offline aprovado após21. Não rodar fsck na raiz viva.

Coleta2 recusou ui-start acumulado586837bytes (>512KiB); não foi falha do
serviço. Coletor passou a buscar só tail196608, mantendo resto da whitelist.
Fonte final também copia somente esse tail: comando testado no console.
Comparação com pacote nativo prova que só mudou cp→tail no worker e todos
os demais arquivos, incluindo os cinco ELF, são idênticos. Não houve novo
ciclo de GUI para essa mudança exclusiva de observabilidade.

Pacote nativo/coletas/análise: runtime-session/service.f5dx49ft.
Pacote fonte final recompilado/auditado: service.o2dd7b0x, latest-service;
fonte para receita em runtime-session/source. Relação exata/diff em
final-source-validation.json/final-source.diff no stage testado. Checks
checks.qju05y46, Kconfig kconfig.xltpzwkz. Provas imutáveis
session-service-preflight e session-service-native, SHA reconferidos.
Limites: lease/settings temporários por sessão; estado/logs entre gerações
retidos até coleta, não política de retenção final. Sem contrato de preferências
persistentes ou UI permanente.

Próximo incremento: coordenador único de init/shutdown. Buildroot rcS
iniciaria S30/S90/S95/S96 antes de S98; o worker corretamente recusaria esses
recursos como alheios. Resolver ownership/ordem antes de serviceenabled1 no
boot. Conectar stop da sessão antes de desmontagens/rede e definir persistência
de config/logs/volume, mantendo recuperação controlada. Não promover a bancada
C06/C09 nem o rcS inteiro a firmware. Calibração acústica/escala visual,
warm Wi-Fi, Power/suspend/bateria/fones/conteúdo/longa duração/licenças privadas
finais continuam abertos. Originais/seed/PSK/chaves privadas não foram exportados.

Os marcos abaixo são referência histórica; o estado corrente está acima.

### C10 — perfil/receita reproduzíveis, com aplicação nativa em RAM

Ler [C10](phase4-runtime-profile.md). runtime-profile.json reúne SPK_HP/157,
software100/política3/incrementos5/overdrive0/backlight80/max160/sound2/debug2/
idle0, quatro hotkeys, navegação normalizada idêntica ao C06 e ajuda com
confirm original. Defaults coreaudio1/input1 e UIenabled0/hotkeys1. Continua
perfil privado de bring-up, não calibração sonora ou política final de usuário.
Recursos GPLv3 fixados por revisão/hashes, originais/proveniência/licenças
acompanham payload; código originalMIT em port/LICENSE. Nenhum novo blob.

Pacote Buildroot muos-r35s-profile + phase4-runtime.fragment opt-in. O hook
pós-overlay aplica o perfil depois do overlay genérico (Buildroot Makefile
823–839); evita voltar silenciosamente a SPK/95/35. Dez checks de geração
byte idêntica, macro de instalação real, pós-overlay/idempotência/guardas/
rollback passaram. Kconfig/parse em output separado passaram. Não compilou
todas as dependências nem imagem completa. SDK .config confere com baseline
network-tools, SHA24fe1d62…e09c85. Não rodar controladores do SDK em paralelo.

Primeiro ensaio session.0sqz6utd parou antes do menu: após setters nativos,
volume/brilho perderam LF, causando dois hashes diferentes. Fonte
var_store.c:333–334 escreve strlen(value), sem LF. Helpers/cleanup/saúde
passaram; prova negativa runtime-profile-config-format-failure preservada.
Correção apenas no verificadorRAM: todos21 hashes antes dos consumidores;
19estáticos e valores semânticos depois. Não remover essas verificações.

Repetição session.rxvlawrp passou:21+19checks, cache/backlight100/80,
volume canônico3bytes e brilho2bytes, helpers95→100/75→80, UI/sons/submenus/
ajuda confirmados pelo usuário “Tudo certo”. Sem bipes de referência.
36probesSSH, 29comUI, 60.86s simultâneos; rede/udev preservaram
PID/starttime. Mixer/18checksC09, defaults UI/hotkeys, cache/pasta de volume/
DRM/backlight restaurados. Rootro/taint0/FAT desmontado, sem escritores ou
assinaturas fatais/storage selecionadas. Ressalvas C09 sonora/visual não
foram consideradas resolvidas por essa navegação.

Blueprint/coleta final build/phase4/runtime-profile/session.rxvlawrp,
ponteiro runtime-profile/latest-session. Geradorúltimo perfil em latest-profile,
fonte local para receita em runtime-profile/source. Checks checks.e2nrki2v,
Kconfig kconfig.inoz1cd7. Provas imutáveis runtime-profile-preflight,
runtime-profile-config-format-failure, runtime-profile-format-preflight e
runtime-profile-session (quatro grupos SHA reconferidos). O legado C09 abaixo
permanece referência. Fsck offline após22..25 continua pendente; último após21.
Nunca rodar fsck na raiz viva nem ler/copiar/hashar seed/chaves privadas/PSK.

C11 abaixo no histórico de provas valida o serviço independente. Próximo: integrar um coordenador único de init/shutdown e definir persistência de configuração antes de autostart. Ainda não habilitar rcS
inteiro/UI permanente nem promover executor de diagnóstico para init. Definir
contrato de configurações/volume persistentes antes do autostart. Warm Wi-Fi
segue com recuperação física; reset/reprobe/unload já falharam, não repetir
como novidade. Calibração acústica/escala visual, energia/bateria/fones/
conteúdo/estabilidade/painéis e licenças privadas finais continuam abertos.

### Marco anterior: C09 — volume/brilho e SSH

Ler [relatório C09](phase4-network-controls.md). Helpers e muhotkey/S99 nativos,
config/share-volume em bindsRAM e namespace privado. Primeira sessão120s:
usuário explorou com vários toques, confirmou funções/sons e achou máximo
acústico40–60% apesar da barra100%. Segunda sessão60s, somente quatro toques:
volume100→95→100 e brilho80→75→80. Medida200ms registrou exatamente cinco
estados esperados. Usuário percebeu brilho com aparência de dois passos;
observação visual segue registrada, sem evidência de dois incrementos reais.
Fonte transforma brilho0..160 em percentual inteiro50→46→50, LV_ANIM_OFF;
sem captura visual que feche a percepção. Barra100 é software; codec157 fixo,
sem calibração de máximo/loudness ou equivalência com driver stock.

Resultados0; helpersCLI95→100/75→80, pai do muhotkey correto, mixer/13hashesC06
+5hashes controles/cache/pasta de volume/DRM/backlight restaurados. Infraestrutura
C07/udev preservou PID/starttime. 33probesSSH, 30comUI, 61.99s simultâneos;
rootro/taint0/FAT desmontado, sem writers/serviços órfãos/socket D-Bus e
assinaturas fatais/storage selecionadas0.9 fixtures controles +8 cadeia +7udev,
QEMU BusyBox e hashes nativos passaram. Código foi somenteRAM; não atualizar
marcadores de boot para C09 nem inferir firmware completo aprovado.

Blueprint/coleta final `network-controls._yj3a8oo`, latest-network-controls;
primeiro ensaio `network-controls.r749y74h`. Provas imutáveis
`dist/phase4/network-controls-session/`, `network-controls-exploratory-session/`,
`network-controls-preflight/` e `network-controls-short-preflight/`.
11diretórios de provas desta rodada foram reconferidos por SHA. Remoção final
RAM em ram-cleanup.txt no stage final. Fsck offline depois22..25 ainda não
feito; último fsck offline aprovado foi após21. Não executar fsck na raiz viva.

### Rede: recuperação validada, reboot automático ainda falha

BOOT0022/23 frios passaram; reboot24 falhou com c820retido e interfaceFF sem
vínculo, apesar de reset USB e reprobeRC0. C07r3 oferece uma retirada/reinserção
física: funcionou24 e25 com a mesma chave, sem trocar cartões, rootro e RNG
atual consultado sem reler/creditar seed. REPORT/RESULT negativos preservados;
RECOVER.TXT separado comparado comRAM e arquivado. Prova network-physical-recovery.
Counteadores de falha0 não excluem erro: loglevel3 suprime RTW_INFO.

ExperimentoRAM de remover8821cu antes do reboot foi efetivamente executado
(PREBOOT.TXT no24) e não resolveu o25. Nenhuma alteração de shutdown
persistente foi adotada. Provas network-unload-preflight/reboot-failure;
fonte/blueprint `network-driver-diagnostic` / `network-unload.vq4y1x6v`.
Causa interna do warm boot permanece aberta; não repetir hipóteses de
reset/reprobe/unload como se não tivessem sido testadas. Recuperação física
serve à bancada, sem aprovação de hotplug geral/reconexão/estabilidade.

BOOT0021/19 negativos em network-reprobe-reboot-failure e
network-reboot-interface-failure; BOOT0018 aprovado em network-boot.
U-Boot/kernel/DTB/módulos/libs/partições não mudaram nesses incrementos.

### Acesso e próximo passo

```sh
ssh -p 2222 -i build/phase4/private/c07-client \
  -oIdentitiesOnly=yes -oStrictHostKeyChecking=yes \
  -oUserKnownHostsFile=build/phase4/private/c07-known_hosts \
  root@192.168.15.17
```

Fingerprint público já confirmado pelo usuário:
`SHA256:fDW+/iNaWgqPwqBtO/ESuKPSQHvYN1PSo2RHfilOxK0`.
Não substituir known_hosts; LAN somente, sem DNS/rota default configurados.
Não ler/copiar/hashar seed, credenciais/chaves privadas ou clonar a raiz viva.
Não regravar imagens antigas: blueprints não contêm os privados do cartão.

Perfil/receita consolidados no C10 acima. Próximo incremento: consolidar lifecycle/init de serviços a partir dos componentes aprovados, separando áudio e recuperação de rede. Calibração sonora/escala visual continuam pendências próprias. Não
habilitar rcS inteiro ou UI permanente sem conferir os contratos e shutdown.
Power/suspend, bateria/carga, fones, conteúdo/core, longa duração e outros
painéis não aprovados. Licenças faltantes: uso privado e consolidar MD no fim,
como solicitado, sem contato com terceiros. Original32 permanece recuperação.

**Marcos anteriores:** C08 menu/áudio/SSH aprovado com mesmo isolamento;
prova network-frontend-session. C06r4 tema adaptado navegação+8,8dB, confirmação/
back originais e confirmação de controle na ajuda. Help original quieto não
aprovado. C09 reutilizou esses efeitos, não restabeleceu o help original.
As seções abaixo são histórico, não o estado físico atual.

## Último marco concluído: C05 — áudio básico audível

**Revisão5 aprovada no recorte de três bipes no kernel próprio.** Ler
[o relatório C05](phase4-native-audio.md). Usuário: “Agora sim ouvi. Tudo
certo”. BOOT0012/DIAG07 status0, coleta/análise aprovadas. Rota SPK_HP,
ganho157, softwareunity, PCM S32_LE/stereo48k, period512/buffer2048.
Probe restaurou rotaSPK/ganho95/software0,35 por readback; depois core
restaurou snapshot ALSA pré-inicialização. Debugfs temporário removido,
logger encerrado via SIGTERM, zero writers, root ro e fsck0. Regressão
C02 persistida passou: RNG6814ms, rotação nativa, sem consumidores prematuros.
Audibilidade confirmada; calibração final, fones e duração prolongada pendentes.

**Por que funcionou:** SPK ficou inaudível em95 e157; mantendo157/mesmo
WAV/backend/formato, a rotaSPK_HP tornou os bipes audíveis. Driver ativa
estágios HP adicionais nessa rota. Não extrapolar para outros painéis/
revisões nem concluir a fiação sem medição. O mesmo WAV foi claramente
ouvido no dArkOSen via default/dmix, mixer preservado. Não comparar níveis
numéricos entre drivers como ganhos iguais; registros DAC observados diferem.

Provas imutáveis: `dist/phase4/native-audio-route-preboot/` e
`dist/phase4/native-audio-boot/`. Blueprint host **sem seed**:
`build/phase4/linux-diagnostic/audio-route.9tz8v3zh`, `latest-audio-route`;
coleta/análises `boot6`. Oito fixtures de aplicação/falha/restauração,
shell/QEMU/ext4/fsck e instalação com preimages passaram. Somente três
scripts atualizados; kernel/DTB/U-Boot/tabela/bibliotecas preservados.
As provas anteriores de FD mulog, ID_PATH ausente e PCM inaudível em95/157
permanecem separadas. Nunca aprovar áudio somente por status0.

**Estado ao encerrar:** original32 no slot OS, test128 no segundo, dArkOSen
ligado e saudável. Image31bdb671…b0577, taint0, cinco contadores Btrfs0,
ES/ogage/Fn ativos, nenhuma unidade muos carregada. Candidato p2 desmontado,
temporários de coleta/instalação/referência removidos, montagens FAT globais
preservadas. SSH encerrado. Nenhum build, gravação ou teste crítico ativo.

**Próximo incremento:** frontend sonoro supervisionado, inicialmente sem
hotkeys. Reutilizar C04/S99/supervisor com core/áudio e fechamento C05; usar
explicitamente SPK_HP e ganho limitado, testar navegação/A/B/Fn/submenus e
drenagem do último efeito. Configuração/cache/perfil devem ser coerentes.
O perfil persistente continua95/SPK e preset35: o sucesso C05 depende de
overrides temporários. Não habilitar UI permanente ou rcS completo para
contornar isso. Volume/brilho reais depois, em ensaio separado. Energia,
rede, conteúdo, fones, outros painéis e licenças de distribuição pendentes.

Cartão atual = rawB01 + findmnt corrigido + C01 + C02corrigido + C03 + C04
+ C05 até revisão5. Não regravar raw antigo nem aplicar instalador/preimages
antigos. Preservar identidade/CIDs/seed privado. Não ler/copiar/hashar seed,
nem clonar raiz viva para artefatos. Não carregar módulos candidatos no
kernel instalado; original32 preservado como recuperação.

## Último marco concluído: C04

**C04 frontend supervisionado aprovado no primeiro boot físico.** Ler
[o relatório](phase4-native-frontend.md). S99/supervisor/frontend reais,
first_paint novo, pai correto, menu/Informações/Configurações/ajuda e
retorno automático confirmados. Também observado muxplore; não houve teste
de conteúdo. Janela configurada para 75 s, silenciosa e sem hotkeys.
DIAG06/BOOT0005 status 0; UI parou pelo S99, modo DRM e console restaurados.
Bind temporário removido e enabled0 mantido; não há UI permanente habilitada.

Regressão C02 persistida: prontidão 7208 ms, refresh/rotação nativos;
aviso conservador do próprio seedrng preservado, nenhum de consumidores.
Input/mapping/D-Bus, parada, root ro, taint 0, fsck e saúde passaram.
Report em uptime 98,11 s. Não é rcS completo ou estabilidade prolongada.

Provas imutáveis: `dist/phase4/native-frontend-preboot/` e
`dist/phase4/native-frontend-boot/`. Blueprint **sem seed**:
`build/phase4/linux-diagnostic/native-frontend.urej9y1t`,
ponteiro `latest-native-frontend`, coleta/análises `boot1`.
SDK/ELF/loader/QEMU/shell/ext4 aprovados; nenhum binário recompilado ou
biblioteca copiada. Somente bootstrap/runner/marcador C04 atualizados,
com backup e preimages. Kernel/DTB/U-Boot/tabela e seed privado preservados.
Markers C02/C03 presentes; bootstrap agora exige C04. DIAG04/DIAG05 mantidos.

**Estado ao encerrar:** original de 32 GB no slot OS, test128 no segundo,
Wi-Fi conectado e dArkOSen saudável. Image `31bdb671…b0577`, taint 0,
cinco contadores Btrfs 0, ES/ogage/Fn ativos, nenhuma unidade muos carregada.
Raiz candidata desmontada, temporários removidos, montagens FAT globais
preservadas. SSH encerrado. Nenhum build, escrita ou teste crítico ativo.

**Próximo incremento:** áudio no kernel próprio. Começar por core/bipes
limitados, sink/PCM/ganho e confirmação auditiva; depois frontend sonoro e
hotkeys em testes separados. Não transportar aprovação anterior do kernel
instalado. Continuam pendentes áudio/ajustes, energia/shutdown normal,
rcS completo com S01/S05 ordenados, dispatcher/conteúdo, rede e outros painéis.
Licenças pendentes permanecem privadas, relatório único ao fim do projeto.

Não ler/copiar/hashar seed nem clonar raiz viva para artefatos. Não aplicar
instaladores C01–C03 sem adaptar preimages/guardas C04. Card atual = raw B01
+ findmnt corrigido + C01 + C02 corrigido + C03 + C04. Não representa o raw
B01 antigo nem um dump distribuível. Não carregar módulos candidatos no
kernel instalado. Original de 32 GB preservado como recuperação.

## Último marco concluído: C03

**C03 SDL/GLES aprovado no primeiro boot com kernel próprio.** Ler
[o relatório C03](phase4-native-graphics.md). EGL/readback passou; SDL
KMSDRM/opengles2 acelerado/vsync 640×480 produziu 1789 frames/30,002 s,
**59,630 fps**, mediana 16,687 ms, p95 16,904 ms, zero falhas de render.
Usuário confirmou cores/orientação/movimento e retorno ao console.
Modo DRM antes/depois idêntico; status DIAG05/BOOT0004 = 0.

Regressão C02 persistida passou: prontidão 6811 ms, refresh/rotação nativos;
aviso conservador do próprio seedrng preservado, nenhum de consumidores.
Input/mapping/D-Bus, parada, root ro, taint 0, fsck offline e retorno saudável
aprovados. Report em uptime 48,39 s; não é estabilidade prolongada nem
aprovação de recursos ES3.2 pelo simples texto da versão.

Provas imutáveis: `dist/phase4/native-graphics-preboot/` e
`dist/phase4/native-graphics-boot/`. Blueprint **sem seed**:
`build/phase4/linux-diagnostic/native-graphics.6qz6i3e7`;
ponteiro `latest-native-graphics`, coleta/análise `boot1`.
SDK próprio, QEMU/loader/contrato/shell/fsck e quatro fixtures passaram.
Somente seis arquivos de diagnóstico instalados; kernel/DTB/U-Boot/tabela,
bibliotecas e seed privado preservados. C03 usa marcador próprio;
S05 continua exigindo marcador C02. DIAG04 foi mantido, novos logs DIAG05.

**Dispositivo ao encerrar:** original de 32 GB no slot OS, test128 no segundo,
Wi-Fi conectado, dArkOSen saudável. Image `31bdb671…b0577`, taint 0,
cinco contadores Btrfs 0, ES/ogage/Fn ativos, nenhuma unidade muos carregada.
Raiz candidata desmontada, temporários removidos, montagens FAT globais
preservadas. SSH encerrado. Nenhum build, escrita ou teste crítico ativo.

**Próximo incremento:** frontend pelo serviço supervisionado no kernel
próprio, primeiro sem áudio/hotkeys e com prazo/logs/parada/root ro. Depois
áudio, eventos/ajustes e shutdown. Não transferir ensaios anteriores do
kernel instalado para esses recortes. O rcS completo ainda precisa ordenar
S01/S05 sem consumo antecipado duplicado. Rede/energia/outros painéis e
licenças para redistribuição continuam pendentes; uso privado mantido.

Nunca ler/copiar/hashar seed nem clonar raiz viva para artefatos. Não usar
instaladores antigos sem adaptar preimages/guardas C03. O cartão é raw B01
+ findmnt corrigido + C01 + C02 corrigido + overlay C03; raw B01 antigo não
representa esse estado. Seed vivo e contador mantidos. Não carregar módulos
candidatos no dArkOSen. Manter o original de 32 GB como recuperação.

## Último marco concluído: C02

**C02 aprovado no recorte seedless + um boot persistido corrigido.**
Ler [o relatório C02](phase4-entropy-diagnostic.md). Última prova imutável:
`dist/phase4/native-entropy-persisted/`. Usuário confirmou a tela esperada
na primeira tentativa após a correção; BOOT0003 foi coletado/analisado.

O seed foi consumido com crédito, RNG ficou pronto após **7114 ms**, e o
applet nativo consumiu o fallback conservador sem crédito para gerar um
novo seed creditável. Parada, input/mapping/D-Bus, root ro, fsck offline e
saúde do original passaram. Um aviso prematuro do próprio seedrng legado
foi preservado; nenhum dos consumidores. Isso não aprova a qualidade
criptográfica do kernel, AT_RANDOM ou hardware RNG.

A parada anterior foi reproduzida em BOOT0001: probe esgotou 5010 ms,
salvou não creditável e não iniciou udev/input. BOOT0002 passou seedless.
Prova `dist/phase4/native-entropy-deadline/`. Correção exata 5 → 60 s,
limitada à biblioteca, em `dist/phase4/entropy-deadline-preboot/`.
A mensagem da primeira falha não transcrita segue desconhecida; não
atribuir contato do cartão como causa. Históricos imutáveis preservados.

**Dispositivo ao encerrar:** dArkOSen no cartão de 32 GB, test128 no segundo
slot, rede reconectada. Image original `31bdb671…b0577`, taint 0, cinco
contadores Btrfs 0, ES/ogage/Fn ativos, nenhuma unidade muos carregada.
Raiz candidata desmontada, temporários removidos; montagens FAT globais
mantidas pelo dArkOSen. SSH encerrado. Nenhum build, escrita ou teste crítico ativo.

Blueprint final sem seed: `build/phase4/linux-diagnostic/entropy.rg3vmy8n`;
transação `deadline-update`, coleta `boot4`. Formato do runner revisão 1,
logs DIAG04/BOOTnnnn. Sete casos do probe, 13 fixtures de política,
QEMU/shell/ELF/fsck e teste de arquivamento passaram.

**Próximo incremento:** SDL/GLES limitado no kernel próprio, antes de UI e
áudio. Preparar logs, supervisão e retorno root ro antes da próxima escrita.
Não transferir aprovação gráfica anterior do kernel instalado para o novo.
S05 ainda é diagnóstico: rcS padrão executaria S01 antes dele; integração
de produto precisa impedir consumo antecipado duplicado e testar shutdown.
Não declarar rcS completo, energia, rede ou outros painéis aprovados.

Nunca ler/copiar/hashar seed nem capturar a raiz viva para artefatos.
Não reinstalar overlay C02 inicial, que exige C01/ausência de seed. Card
atual = raw B01 + correção findmnt + C01 + C02 + biblioteca corrigida e
runner com arquivos por boot. DIAG.ID B01 e PARTUUID 4d554432-02 mantidos;
U-Boot/kernel/DTB/tabela inalterados neste incremento. Raw B01 antigo
isolado não representa esse estado. Não carregar módulos candidatos no
kernel instalado. Licenças privadas: relatório único ao fim do projeto.

## Histórico: primeiro Linux/initramfs aprovado


**Último avanço: primeiro boot nativo do Linux próprio aprovado no recorte
mínimo, com logs coletados e retorno verificado.** Ler primeiro
[o relatório do diagnóstico](phase4-linux-diagnostic.md). O kernel
`4.4.189-muos-r35s-p4` iniciou com initramfs do sysroot próprio no secundário
de 128 GB, sem o cartão dArkOSen presente. O usuário confirmou a tela final.
Logs confirmam PID 1, raiz em RAM, console 640×480/80×30, MemTotal 916920 KiB,
taint 0 e nenhum módulo carregado. Amostragem do report em uptime 16,37 s;
sem Oops/BUG/panic/I/O/MMC na busca documentada dos logs dessa janela.
**Ext4 completa, frontend e serviços muOS ainda não deram boot próprio.**

Build `build/phase4/uboot-sd/probe.e1z1roxv`, pacote `package.z7v48cdq`,
imagem `linux-image.yu6fwzw8`, initramfs `linux-diagnostic/initramfs.rtp27nen`.
Raw pré-boot SHA256
`85f82bff8dfc512844121e0129e4849d0f30239d1eceb58d4348d8b0f7dca848`.
Provas imutáveis: `dist/phase4/uboot-sd-linux-diagnostic/`,
`dist/phase4/linux-diagnostic-media/` e `dist/phase4/native-linux-boot/`.
As duas primeiras preservam o estado anterior ao teste; a terceira contém
logs reais, análise, confirmação física e saúde após o retorno.

**Dispositivo restaurado:** o usuário retornou ao dArkOSen de 32 GB e
reconectou a rede. SSH confirmou Image `31bdb671…b0577` inalterado, taint 0,
cinco contadores Btrfs 0, ES/ogage/Fn ativos e nenhuma unidade `muos*`
carregada. O secundário de 128 GB está novamente no segundo slot, montado
pelo dArkOSen em `/roms2` e `/opt/system/Tools`, rw/noatime. A coleta usou
bind read-only em namespace privado e preservou essas montagens globais.
Temporário removido e SSH encerrado. Não há build, gravação ou teste ativo.
O cartão de teste contém logs e pastas criadas pelo dArkOSen; seu hash
integral atual já não representa o raw pré-boot.

**Pendências delimitadas:** os avisos selecionados de logo, IRQ170, clock
vcodec e rotas ASoC também aparecem no dArkOSen restaurado. Não presumir
que sejam inofensivos. DRM/DSI adiados terminaram em framebuffer e Mali em
`mali0`; isso não testa GLES/áudio. `CONFIG_KEYBOARD_GPIO=m` explica a
falta de `odroidgo3-keys` neste initramfs sem módulos. Não corrigir isso
alterando DTS ou renumerando input sem testar o módulo próprio.

**Próximo menor incremento:** preparar boot da ext4 própria em modo
diagnóstico, inicialmente com frontend/autostart bloqueados. Validar PID 1,
storage/identidade da mídia e carregamento de `gpio_keys`/coldplug dos
módulos do mesmo release; depois validar input e frontend no kernel próprio.
Definir coleta de logs e parada/retorno antes da próxima escrita. O writer
atual só aceita imagens de 128 MiB: não usá-lo para uma imagem maior sem
adaptar e verificar seus limites. O cartão de 32 GB continua a recuperação
preservada. Licenças pendentes permanecem para uso privado e relatório
único ao fim do projeto. A Fase 4 continua aberta.

## Histórico: monitor U-Boot e retorno ao dArkOSen aprovados


**Último avanço: primeiro boot nativo do monitor aprovado.** O U-Boot
próprio iniciou pelo cartão secundário de 128 GB no único R35S/Panel 0.
O usuário confirmou texto e orientação corretos, transcreveu o mapa de
memória, desligou por Power longo e recolocou o cartão dArkOSen de 32 GB,
que voltou a iniciar normalmente. Linux, rootfs e frontend candidatos
**ainda não foram iniciados por boot próprio**. A Fase 4 permanece aberta.

A proteção do DTB passou nos dois alocadores nativos em fixture/UBSan;
o monitor passou nas auditorias e no ensaio físico sem UART. Valores:
RAM top `40000000`, vídeo `3de00000–3fff0000`, U-Boot `3dd08000`,
stack `31cfd580`, DTB de controle `01e00000`. O endereço U-Boot confere
com a fórmula de relocação e o `__bss_end` compilado. O monitor não mede
a lista completa de bancos/ATAGS nem estabilidade prolongada.

Build: `build/phase4/uboot-sd/probe.xqc7am2o`; pacote `package.x5asz5qk`;
imagem privada `monitor-image.0c45_wjn`, 128 MiB, FAT32, sem Linux/rootfs,
autoboot desligado. SHA256 raw:
`6a67c21e7a00af92c785bf3d60ed81684e83b02c03c902ca80a51ec22cbfe2b7`.
U-Boot SHA256:
`18bf64186e08765f0c47d5b53dfb78497462abf3449819317cb253f3cb76b533`.

A escrita foi autorizada expressamente para o secundário de 128 GB via
SSH, identificado por CID/capacidade; raiz e boot originais foram excluídos.
Escrita/releitura integral com cache invalidado passou. Antes do poweroff,
Image original inalterado, taint 0 e cinco contadores Btrfs 0. A sessão
transitória de gravação terminou antes do desligamento. Não há operação
crítica de build, gravação ou monitor mantida em execução no dispositivo.

**Conferência após retorno: aprovada via SSH após reconectar o Wi-Fi.**
Kernel instalado `4.4.189`, Image SHA256 `31bdb671…b0577` inalterado,
taint 0 e cinco contadores Btrfs 0. ES/ogage/Fn ativos; nenhuma unidade
`muos*` ativa ou carregada. A busca no ring buffer não encontrou mensagens
classificadas como falha MMC/Btrfs/Oops/panic; o padrão amplo também
capturou a inicialização normal `ramoops: attached`, explicitamente
excluída da classificação de falhas. Isso não mede estabilidade prolongada.
O cartão original foi confirmado por CID, com raiz Btrfs e boot FAT nos
devices esperados. O secundário de 128 GB voltou ao segundo slot e está
presente, com sua FAT de 100 MiB **sem montagem**. Esta conferência não
alterou serviços, montagens, configuração ou conteúdo dos cartões.

Relatório: [memória e monitor](phase4-memory-monitor.md). Provas separadas:
`dist/phase4/uboot-sd-memory/`, `dist/phase4/uboot-sd-monitor/`,
`dist/phase4/monitor-media-proof/`, `dist/phase4/native-monitor-boot/` e
`dist/phase4/native-monitor-return/`.
As duas primeiras cobrem o host; a terceira, a escrita; a última, a
conferência SSH do retorno. A confirmação física está na quarta, que
preserva o estado anterior à reconexão de rede. Não reescrever estados
históricos de “boot pendente” dentro dos checkpoints anteriores.

**Próximo menor passo:** desenhar o boot diagnóstico do Linux próprio na
mídia secundária, com init mínimo, frontend desativado e registro observável
sem UART. O usuário não tem UART/prefere não abrir o console. Fechar layout,
mapa de carga/relocação, console e logs/marker do init antes da próxima
escrita. Conferir de novo mídia e estado do aparelho; o cartão de 32 GB
continua sendo a recuperação preservada. Não reconstruir checkpoints só
para retomar. O snapshot userspace abaixo permanece o mesmo.

## Histórico anterior ao monitor nativo

Os blocos seguintes descrevem rodadas anteriores. Seus ponteiros e
pendências de memória foram superados pelo estado acima.

---


**Último avanço:** [executável U-Boot SD](phase4-uboot-sd.md) compilado e
auditado; contêineres privados DDR/miniloader/U-Boot/trust empacotados e
conferidos. Trust reproduz byte a byte a referência instalada. Checkpoint
imutável em `dist/phase4/uboot-sd-probe/`, sem payloads proprietários.
Autoboot desligado, ambiente em RAM, panic sem reboot; recovery SPI/erase,
OP-TEE client/RPMB, ADC de painel e testes de fábrica selecionados excluídos.
Não houve acesso ao console nesta rodada. Nenhum cartão foi escrito.

Ponteiros atuais: `build/phase4/uboot-sd/latest-build` → `probe.yjv58qmi`,
`latest-package` desse diretório → `package.1p36kcrj`. Build 0 e auditorias
aprovadas, nenhum container em execução ao encerrar. Binário U-Boot:
`c2ebd0892a5f4588fd83d894a4cc36a0f0d9d0e1ba0c8fafab47756a31ed251b`.
Não reconstruir apenas para retomar; conferir os manifests e continuar a
pendência de memória abaixo. O snapshot do rootfs a seguir não mudou.

**Próximo menor passo:** proteger explicitamente o buffer do DTB de controle
no sysmem e fechar reservas/DRM/relocação. A leitura curta confirmou que o
`booti` desta revisão move o kernel de 0x02000000 para 0x02080000, sem colisão
com os buffers FDT fixos; isso não fecha o mapa dinâmico de RAM. O helper
de reservas não registra automaticamente o próprio buffer do DTB. Depois
definir coleta de logs/serial e preparar layout/FAT/raiz diagnóstica. A
candidata atual não tem shell operável pelos botões. Ainda não iniciar
Fase 5/gravação sem mídia identificada e confirmação da operação concreta.

---

**Estado mais recente, 25/10:** [módulos/firmware](phase4-modules-firmware.md)
integrados e auditados no host: 284 ELF userspace + 555 módulos = 839 ELF AArch64,
ext4 SHA256 `ccdb9c0a7d232f8dc628a86ceb911c53247d74dd0e14802e0907459bddf13fc0`.
Autostart dos [serviços aprovados](phase4-init-services.md) está configurado;
essa imagem/kernel continuam sem boot. O [DTB U-Boot Panel0](phase4-uboot-panel.md)
próprio também compilou e passou na comparação do contrato de display.
O marco U-Boot SD específico foi executado na continuação acima. Não há build crítico ou ensaio
pendente no console. Os blocos abaixo de 282/283 ELF são históricos.

Para retomar, ler primeiro os dois relatórios acima. `foundation/active`
continua dono da saída mutável; `image.exit` e `audit.exit` estão em 0,
staging aprovado `foundation/staging.YRRiUd`. O payload está no ponteiro
`modules/latest-payload`. O overlay atual exige **`--bsp-modules`** junto de
`--validated-runtime --init-services --enable-ui`; a omissão é recusada.
Não é necessário reconstruir para continuar. Evidências congeladas:
`dist/phase4/modules-firmware/` e `dist/phase4/uboot-panel/`.

Nesta continuação houve somente leitura SSH: taint 0, contadores Btrfs 0,
serviços ativos e kernel instalado inalterado. Nenhum módulo candidato foi
carregado e nenhum cartão foi escrito. Não testar .ko de release diferente
no Debian. Wi-Fi/BT e coldplug ainda não foram validados na candidata.

---

## Checkpoint histórico anterior

Rodada curta, limitada pelo saldo informado pelo usuário. Somente host:
**não houve conexão SSH, teste no console, gravação ou particionamento**.
Build e auditoria terminaram; não deixar trabalho crítico no dispositivo.

## Integração concluída

O [instalador do overlay](../../port/scripts/install-phase4-foundation.py)
ganhou `--validated-runtime`. Consome o checkpoint imutável
`dist/phase4/frontend-full-native/`, verifica hashes e incorpora:

- Frontend e bibliotecas com patch0006, que remove a leitura bruta duplicada
  de volume apenas no board R35S.
- `muos-sdl-map` AArch64, em `/opt/muos/frontend/`, e os scripts nativos
  `assign.sh`, `audio.sh`, `bright.sh`, `display.sh` e `governor.sh`.
- Manifesto `core.json`, conferido por Git blob, e os quatro bindings de
  volume/brilho já testados, sem Power/idle/hold.
- Paths de storage coerentes com S90 e incrementos de volume/brilho em5.

Não incorpora a troca temporária dos WAVs de ajuda. Os originais permanecem,
assim como o preset de volume35. **Autostart do frontend segue desligado.**
A seleção do som final e a política completa de energia continuam pendentes.

## Resultado auditado

A imagem ext4 de 512 MiB contém **282 ELF AArch64**, um a mais pelo mapper.
SHA256: `8e9146c2cabdc0121a7094b6869dfe3be743112cb3a1ee24472febd922cdc52f`.

Passaram: loader/ABI, grupo das bibliotecas da UI com `RTLD_NOW`, contrato GBM,
QEMU Cortex-A35, `muos-sdl-map --info`, recursos/scripts, configuração de
hotkeys, preservação dos sons originais e `e2fsck -fn`. O provider r13p0
mantém origem/transformações SDK/target já verificadas. Os avisos `.dynsym`
do blob continuam registrados; seus termos continuam pendentes para publicação.

Os oito ELF incorporados pelo overlay foram comparados **byte a byte** com
os componentes aprovados. Buildroot aplica strip em `Makefile:785` e copia
o overlay em `Makefile:824`; portanto esses oito arquivos permanecem sem
strip adicional. A primeira comparação que aplicava strip artificialmente
foi corrigida para refletir essa ordem. Isso difere do Mali instalado por
pacote, cujo strip é reproduzido separadamente. Não presumir que todo ELF
da imagem passe pela mesma transformação.

O [checkpoint](../../dist/phase4/integrated-userspace/build-manifest.json)
`dist/phase4/integrated-userspace/` contém auditoria, manifestos e fontes do
port, com checksums. Exclui Mali, ZIP, imagem e tar do runtime. Os artefatos
privados estão em `build/phase4/graphics-config/output/images/` e no staging
apontado por `build/phase4/foundation/latest-staging`.

**Limite:** os componentes foram aprovados no console na rodada anterior;
a nova imagem integrada passou somente em auditoria do host. Seus campos
de boot/runtime novo continuam falsos. Não é firmware pronto para gravar.

## Retomada após o limite restaurar

1. Ler este ponto e [o ensaio do frontend](phase4-full-frontend.md). Conferir
   `foundation/image.exit` e `foundation/audit.exit`, ambos0. O dono da saída
   mutável continua `foundation/active`; não usar controladores antigos de menu.
2. Próximo incremento: integrar espera de uinput, execução do mapper e
   supervisão/autostart do frontend. Manter pai intermediário: `muxfrontend`
   encerra quando `getppid()==1`. Só habilitar autostart depois de testar
   ordem, falha e stop em namespace; não disparar o rcS completo sobre o Debian.
3. Incorporar módulos/firmware do BSP e completar shutdown, bateria e energia.
   Os555 módulos são de `4.4.189-muos-r35s-p4`: **não carregar no kernel
   instalado nem forçar vermagic**. Auditar ET_REL/vermagic separadamente;
   o verificador atual de userspace assume program headers de executáveis.
4. Fechar U-Boot/DTB Panel0/DDR/BL31/BL32 e boot config antes da Fase 5.
   Não fazer escrita em cartões sem identificar mídia e confirmar a operação.
   Manter framebuffer mmap excluído. A licença privada não aprova publicação.

Para reconstruir este incremento no host, se necessário:

```sh
python3 port/scripts/install-phase4-foundation.py --validated-runtime
bash port/scripts/build-phase4-foundation.sh image
bash port/scripts/build-phase4-foundation.sh status
```

O build é destacado: aguardar `running=false`, exit0 e `image.exit`0 antes de:

```sh
bash port/scripts/audit-phase4-foundation.sh
```

Não é necessário repetir o build para continuar: a imagem auditada já existe.
Na retomada de testes físicos, conferir novamente saúde/IP/disponibilidade
do console e utilizar supervisor com restauração. Não há sessão SSH mantida
aberta nesta rodada.

Na configuração atual com serviços aprovados, a reinstalação do overlay usa:

```sh
python3 port/scripts/install-phase4-foundation.py --validated-runtime --init-services --enable-ui
```

Esse comando exige os manifests de aprovação correspondentes aos serviços
atuais. Não executar rcS global nem alterar o startup do Debian para testar.
