# C12 — preflight de energia com prova durável

## Incremento e escopo

Retomada em 28/10/2026. O console respondeu em192.168.15.17:2222 com a
mesma chave fixada, boot29/C07, rootext4RO, FAT desmontada, taint0, brilho80,
55 pré-requisitos íntegros e zero assinaturas selecionadas de erro kernel/storage.
O checkpoint anterior registrava boot28 e IP.13; esta leitura atualiza essa
informação sem repetir os ensaios aprovados de tela/input/áudio. Cartão128
identificado pelo guard existente; original dArkOSen32 deve permanecer guardado.

O próximo incremento qualifica a parada antes do pedido ao PID1. BusyBox1.37.0
(`build/phase4/rootfs-output/build/busybox-1.37.0/init/init.c:758–775`)
executa SHUTDOWN e depois TERM/KILL independentemente do retorno do script.
O upstream muOS (`refs/muos/internal/script/init/shutdown`) também percorre
serviços na ordem inversa; foi consultado por leitura. Nenhum código upstream
novo foi copiado. Código original sob port/ continua MIT.

## Abordagem e limites

`power-functions.sh`, chamado pelo controlador sob seu lock, exige um boot
C12 próprio com diagnóstico concluído e rede própria. C07, sessão ainda ativa,
ausência de FINAL ou ciclo já parado não autorizam o novo fluxo. Não há retry
automático da transação no mesmo boot. Defaults da receita/cartão continuam
allow_power0; a habilitação do ensaio será somente por configuração root600
em RAM. Não há novo handler para o botão Power ou suspend.

Antes de parar a rede, PBEGIN.TXT é salvo em DIAG10/BOOTnnnn após comparar
o FINAL da FAT com o da RAM. A cadeia continua session.stop → quiescent →
network.stop → udev.stop → root.sync → root.seal. Os seis resultados entram
em PREADY.TXT, sincronizado, comparado e desmontado antes da última checagem
de rootRO/ausência de serviços/sessão/seed parado e do pedido ao PID1.
Falha bloqueia o pedido e tenta salvar PFAIL.TXT; mídia indisponível pode
impedir até esse registro. Falha após network.stop pode deixar SSH indisponível.

PREADY comprova o preflight e a intenção ANTES da chamada. Não comprova que
PID1 recebeu o pedido, o kernel terminou ou o hardware desligou. Após reboot,
o relatório precisa ser relido por montagem RO e comparado com a coleta host.
O shutdown da inittab repete cleanup idempotente. Não existe cancelamento
de um pedido já aceito por PID1. Falha/timeout de desmontagem bloqueia energia.
Sync/readback não oferecem atomicidade contra queda elétrica durante gravação.

Atualização dirigida troca somente power-functions.sh (novo), order.sh,
native-functions.sh, diagnostic-save.sh e service.sh. Exige todos os hashes
instalados,55 pré-requisitos, identidade de mídia/placa, C07 online/rootRO,
ausência de sessão/token e destinos sem symlinks. Backup dos quatro arquivos
anteriores fica em RAM; rollback restaura hashes e rootRO em falhas tratáveis.
Não arma token, não altera config/inittab/perfil/libs/kernel/DTB/partições.
Interrupção elétrica da atualização não é uma transação atômica de diretório.

## Validação e ensaio planejado

Host:29 cenários novos cobrem controlador/arquivo reais com guard, mount e
dispatcher simulados em container isolado; incluem os seis erros da parada,
falhas de arquivo/sync/unmount/rechecagem, imutabilidade, C07 e rollback após
cada um dos cinco arquivos. Regressões necessárias pelas alterações em
order/native/archive:20 de ordem,32 de adapters e35 de seleção/arquivo.
O antigo teste de energia sem journal migrou para a suíte nova. Macro real
de instalação, loader e shell BusyBox AArch64/QEMU são conferidos sem recompilar
ELF nem alterar a configuração compartilhada do SDK.

Ensaio: atualizar scripts em C07 e comprovar recusa nativa sem perder rede;
armar um único novo C12 para qualificação de energia, observar recuperação
física se necessária, esperar lease/FINAL e coletar. Habilitar energia somente
emRAM e executar reboot pelo novo controlador; após retorno C07, reler os
registros, conferir hashes/saúde e deixar token ausente/allow_power0. Não há
motivo para repetir DPAD/áudio/calibração. Preferências persistentes, desligamento
físico, Power/suspend e fsck offline continuam fora deste recorte.

Resultados nativos seguem abaixo; o recorte aprovado é reboot controlado,
não poweroff físico, Power/suspend nem firmware permanente.

## Atualização nativa

Primeira tentativa `power-test.9ac7v5on` escreveu os cinco arquivos, mas
`originals` usou o manifesto relativo fora de /. A verificação recusou a
transação; rollbackRC0 restaurou todos os hashes antigos, removeu a biblioteca
nova e deixou rootRO, C07/rede disponíveis e token ausente. Não houve reboot.
Prova negativa preservada separadamente. Corrigido `cd /` nessa verificação;
o29º cenário executa o comando real do wrapper a partir de /tmp para impedir
regressão. Não foi falha de boot/mídia nem motivo para repetir testes de UI.

Candidata final `power-test.feak98w7`, coordenador `57ed__3c`, checks de energia
`tobo6nyg` (29), ordem `499itqiw` (20), adapters `a3_exucv` (32), diagnóstico
`99ovj9nb` (35):116 checks host. Instalação dirigida e recusa nativa de energia
no C07 passaram. Todos os hashes instalados e55 pré-requisitos conferiram;
udev/wpa/DHCP/Dropbear mantiveram PID/starttime antes/depois e após recusa64.
Config persistente allow_power0, nenhum estado de coordenador criado no C07.
Token de uso único armado separadamente para o ensaio29→30; reboot inicial
foi outra ação explícita após os checks.

## Boot30 e barreira nativa

Usuário confirmou retirada/reinserção do dongle e launcher visível. C12/30
consumiu o token e executou uma única entropy.start; rede inicial falhou pelo
warmboot conhecido e recovery registrou novos daemons próprios. Sem nova
leitura de seed. Os16 passos do bootstrap, incluindo a falha inicial preservada,
ficaram no relatório; não se considera warmWi-Fi resolvido.

Com o diagnóstico ainda incompleto, configuração root600 temporária em RAM
habilitou apenas o teste de recusa. `service.sh reboot` retornou64, sem criar
boot/power ou power-request e mantendo network.status0. Config removida após
coleta. Não simulamos falha nos serviços reais; falhas de cada etapa foram
exercitadas somente nos fixtures. Nenhum pedido chegou ao PID1 nesse negativo.

Lease90 terminou com result0;21 hashes efetivos/21 originais, mixer/brilho80,
DRM/volume-store e ausência de writers passaram. Quiescência/rede própria0,
rootRO/FAT desmontada/taint0 e55 pré-requisitos conferidos. START/FINAL da FAT
idênticos aos da RAM. Após essa análise passed, uma ação explícita separada
criou /run/c12-power.conf allow_power1 e agendou o controlador de reboot
com stdin/stdout/stderr desvinculados do SSH e HUP ignorado. O arquivo persistente
continua allow_power0. Aguardando leitura pós-retorno dos relatórios de parada.

## Resultado final — parada30 e retorno31 aprovados

O retorno foi comprovado por SSH fixado em192.168.15.17:2222, boot31/C07.
Usuário reconectou o dongle; a necessidade física permanece. Montagem RO da
FAT recuperou DIAG10/BOOT0030/PBEGIN.TXT e PREADY.TXT, sem PFAIL.TXT. PREADY:

```text
BOOT_SEQ=30 PHASE=PREADY ACTION=reboot
OUTCOME=preflight-complete
PID1_REQUEST_NOT_YET_ATTEMPTED=1
STEP=session.stop LIMIT=110 RC=0
STEP=session.quiescent LIMIT=5 RC=0
STEP=network.stop LIMIT=20 RC=0
STEP=udev.stop LIMIT=20 RC=0
STEP=root.sync LIMIT=10 RC=0
STEP=root.seal LIMIT=10 RC=0
```

O marcador descreve o instante ANTES da chamada; o novo boot31 é evidência
separada do reboot ocorrido. PREADY não afirma que a alimentação foi removida.
Todos os hashes instalados e55 pré-requisitos passaram após retorno; sessão
inexistente/quiescência, rootRO/FAT desmontada/taint0 e zero assinaturas
selecionadas de erro kernel/storage conferidos. START/FINAL sobreviveram
idênticos à coleta anterior. Token ausente, seleção default C07 e config
persistente allow_power0. Config temporária e estado30 desapareceram com reboot.

`boot-analysis.json` registra o estado ANTES do teste de energia;
`power-analysis.json` é o resultado final separado. Fontes/ações executadas,
relatórios públicos, instalação e recusa ativa constam no stage final.
Provas imutáveis com SHA256SUMS em dist/phase4/boot-power-preflight,
boot-power-native e boot-power-update-rollback. Não houve exportação de seed,
PSK/chave privada, mudança de kernel/DTB/bootloader/partições/libs/módulos,
rebuild de imagem completa ou fsck na raiz viva. Último fsck offline após21;
22..31 ainda não foram verificados offline. dArkOSen original32 preservado.

**Próximo, conforme orientação do usuário:** investigar uma correção para o
USB/Wi-Fi após warm reboot, com hipótese nova baseada em evidência de driver,
USB e alimentação. Reset/reprobe/unload8821cu já falharam; este encerramento
com stop de rede/udev e prova durável também não removeu a necessidade de
replug. Não repetir esses testes sem uma diferença causal concreta. Preservar
a recuperação física e a chave/credenciais e limitar qualquer nova gravação
ao cartão128. Depois retomar dadosrw com rootro, defaults uma vez e preferências
(volume/brilho) persistentes antes de sessão permanente. Poweroff real,
Power/suspend/bateria/fones/conteúdo/longa duração e calibração seguem pendentes.
