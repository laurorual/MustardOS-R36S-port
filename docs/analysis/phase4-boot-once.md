# C12 — boot diagnóstico de uso único

O C12 abaixo é histórico e permanece inativo. O incremento atual usa um
pedido **C25 próprio**, com C22 instalado, preferências e fundação96:
[boot único C25](phase4-launcher-once.md). Não rearmar o C12. O problema
warm Wi-Fi deste registro já foi corrigido e aprovado posteriormente com
a política Wi-Fi-only; consultar o checkpoint atual antes de agir.

## Estado corrente — reboot durável30→31 aprovado

Ver [energia durável](phase4-boot-power.md) para a atualização de cinco scripts,
116 checks host, recusa nativa e preflight/parada30 com PBEGIN/PREADY persistidos
antes do pedido ao PID1. Retorno31/C07/rootRO/FAT desmontada/taint0/hashes passou;
token consumido/allow_power0. WarmWi-Fi continua exigindo replug físico e é a
próxima prioridade do usuário. Registros abaixo descrevem o marco anterior27→28.

## Preparação host

Coordenador com sessão C11 e recuperação física do dongle. A seleção altera
somente dois dispatchers da inittab C07, preservando as demais linhas. Código
em `port/device/rk-r35s-p0/boot/`: select/select-functions, diagnostic,
diagnostic-save e adaptadores/ordem atualizados. Instalação dirigida em
`boot-diagnostic/install*.sh`, preparada/executada pelos scripts
`prepare-phase4-boot-diagnostic.py` e `install-phase4-boot-once.py`.

O marcador root600 `/var/lib/muos-diagnostic/c12.once` contém somente
`MUOS-C12-ONCE` mais LF. O seletor move-o para c12.used e sincroniza ANTES de
executar o coordenador. Sem marcador válido, o boot seleciona C07. Não há
fallback C07 no MESMO boot depois de iniciar C12: isso recarregaria o seed.
Falha do C12 fica registrada; o boot seguinte retorna ao C07 por ausência do
pedido. Esse mecanismo não resolve queda elétrica durante escrita nem dispensa
o cartão dArkOSen original como recuperação independente.

Sessão de90s, perfil C10 previamente aprovado, allow_power0 e preferências
voláteis. Recuperação opcional acontece após entropy.stop/root.seal e antes
da sessão: confirmar RNG atual/chave existente, limpar rede própria, observar
retirada por1s e reinserção física, executar ejeção USB quando necessária e
iniciar rede em modo recover. Cada comando tem prazo<=120s. Uma tentativa por
boot; PID/starttime/exe dos NOVOS daemons pertencem ao C12. Falha parcial só
permite UI offline depois de limpeza aprovada. Nenhuma nova leitura de seed
nem geração de chave ocorre no recover.

Relatórios públicos START.TXT/FINAL.TXT separados em DIAG10/BOOTnnnn, cada
arquivo<=64KiB, sem sobrescrever os existentes. FAT montada inicialmentero,
DIAG.ID conferido, remount temporáriorw e desmontagem após sync. Relatórios
trazem sequência/status/ordem numérica, modo da rede, rootro/taint/seedstopped
e resultado da sessão; não copiam logs privados, /run inteiro, PSK ou chaves.
O START resume o bootstrap completo, incluindo eventual reconnect; erros de
passos anteriores permanecem em steps.txt. FINAL registra cleanup/estado final.

A instalação valida CID/tamanho/PARTUUID/modelo/kernel, raizro, original ausente,
FAT desmontada, C07/55 hashes existentes, inittab original exata e ausência dos
novos destinos. Copia apenas usr/libexec/muos-boot, usr/libexec/muos-session,
usr/share/muos-r35s-boot e dois defaults novos. A seleção ativa é substituída
atomicamente depois dos payloads, e o marcador é armado por último. Trap de
erro restaura inittab C07 e remove somente os destinos comprovados ausentes
antes. Não toca bootloader/kernel/DTB/partições, módulos, libs ou credenciais.
Não roda fsck na raiz viva. Isso instala suporte de bancada, não firmware final.

## Evidências host e estado antes da instalação

20 checks de ordem +33 de adaptadores +35 de seletor/recovery/arquivo/rollback
passaram em container sem dispositivos/rede/montagens reais. Fixtures
substituem somente guard/mount/callbacks na cópia descartável. Incluem falta de
token, token inválido/symlink/gravável, consumo antes do bootstrap, próxima
seleção C07, falta de sync, recusa de bootstrap repetido, cleanup parcial,
relatórios imutáveis, erro de remount, rollback após arquivo e após seleção,
payload corrompido e destino/symlink alheio antes de habilitar escrita.

Stages em build/phase4/boot-order: checks.s0fi16cp,
adapters-checks.nf4ip13h, diagnostic-checks.mbg52i6k,
coordinator.7j2f32yp e boot-test.mp19ei2w. Macros reais de instalação e shell
BusyBox AArch64/QEMU passaram. SDK compartilhado segue baseline. Não houve
rebuild de imagem inteira. Scripts/ELF/perfil C11 mantêm os bytes aprovados;
somente o hash esperado de /etc/inittab na tabela de pré-requisitos foi
atualizado para a seleção revisada, e seu manifesto foi regenerado.

Antes do teste, console verificado em C07/BOOT0026, IP192.168.15.13:2222 com
chave fixada, rootro/FAT desmontada/taint0 e sem sessão ativa. Usuário disponível
para confirmação e eventual reconexão USB. Resultados nativos seguem abaixo.

## Tentativa negativa e correção

Primeira instalação zw07_f5k ficou no preflight de pais: dirname('//') devolvia
//, sem atingir a condição de término /. Processo5644 foi terminado porTERM;
root permaneceuRO, nenhum destino novo/token foi criado e C07 continuou online.
RAM anterior removida após conferir ausência de escritas. Corrigido o término
em //; regressão ganhou fixture específico. Não foi falha de boot ou mídia.
Prova negativa separada em dist/phase4/boot-once-root-path-preflight-failure.

## Instalação e boot27 reais

Instalação mp19ei2w passou com payloads/55 pré-requisitos, seleção/token/modos
conferidos, rootRO e os mesmos PID/starttime da rede C07. Nenhum reboot foi
solicitado pelo instalador; a solicitação foi uma ação separada após os checks.

No27, seletor consumiu o pedido antes do RNG. Inicialização/RNG/udev/USB passaram;
network.start falhou pelo warmboot conhecido. Recovery após root.seal consultou
RNG atual, observou retirada/reinserção, reaplicou eject quando necessário,
iniciou wpa/DHCP/SSH e registrou seus novos PID/starttime/exe. A identidade SSH
permaneceu fixada, IP192.168.15.13. Sessão iniciou com status0/firstpaint novo.

```text
STEP=network.start LIMIT=120 RC=1
STEP=entropy.stop LIMIT=30 RC=0
STEP=root.seal LIMIT=10 RC=0
STEP=recovery.ready LIMIT=5 RC=0
STEP=usb.wait-remove LIMIT=95 RC=0
STEP=usb.wait-add LIMIT=120 RC=0
STEP=network.recover LIMIT=120 RC=0
STEP=session.start LIMIT=120 RC=0
STEP=session.status LIMIT=5 RC=0
```

Usuário confirmou menu e D-pad/A/B/Fn. Áudio presente porém muito baixo:
software1.00, Playback Path3/SPK_HP e codec157/157 foram registrados. Esses
valores são o perfil conservador existente, não uma calibração de máximo.
Não houve aumento automático do codec nem aprovação acústica nesta rodada.

Lease90 terminou com result0/reason=lease-expired. Perfil21/originais21 hashes,
mixer/brilho80/DRM/volume-store antes/depois e ausência de writers passaram.
Quiescência0/rede própria0/rootro/taint0. START/FINAL separados na FAT conferiram
com RAM; o erro inicial de rede continuou registrado. Relatórios sem segredo.
Coletor foi chamado primeiro antes de FINAL existir (recusa sem coleta) e
ajustou a chamada da barreira sob set-e para aceitar o status3 intermediário
esperado. Não foi nova falha de serviço; dados finais preservados.

## Retorno C07/28 e estado final

Após coleta/preflight em chamada separada, reboot normal selecionou C07 sem
rearmar pedido e sem abrir menu. Usuário precisou reinserir o dongle novamente;
SSH fixado voltou no mesmo IP.55 pré-requisitos, payloads C12, rootro/FAT
desmontada/taint0/ausência de processos UI/D-Bus e erros kernel/storage
selecionados0 foram conferidos. Hashes dos dois relatórios C12 na FAT foram
comparados novamente DEPOIS do reboot: sua persistência foi demonstrada.

O seletor continua instalado, mas sem c12.once; c12.used registra consumo.
Configs da bancada enabled1/recover_network1/allow_power0 e sessão90s ficam
inativas no caminho C07. Defaults da receita continuam0. Não chamar start C12
no boot C07 nem repetir token sem novo ensaio planejado. Nenhuma mudança em
kernel/DTB/bootloader/partições/libs/módulos ou dArkOSen original.

Provas dist/phase4/boot-once-preflight e boot-once-native, além da negativa,
com SHA256SUMS. Stage contém install-analysis.json, boot-analysis.json,
native/, fallback-health.stdout e confirmações manuais. Não houve cópia/hash
de seed/credenciais/chaves privadas ou fsck na raiz viva. Último fsck offline
após21; posteriores22..28 seguem sem essa verificação.

## Próximo incremento registrado após boot28 (superado pelo ensaio30→31)

Qualificar pedido de energia abortável e parada com prova durável antes de
solicitar PID1. O reboot27→28 exerceu a seleção de shutdown, mas seus resultados
por passo ficaram emRAM; não aprovar esse fluxo inteiro apenas pelo retorno.
BusyBox não cancela TERM/KILL por erro em SHUTDOWN. Depois resolver armazenamento
de preferências, defaults uma vez e retenção de logs antes de sessão permanente.
Calibração sonora/escala UI, warmWi-Fi automático, Power/suspend/bateria/fones,
conteúdo e estabilidade longa continuam abertos. Reusar o dArkOSen original
como recuperação independente, sem modificá-lo.
