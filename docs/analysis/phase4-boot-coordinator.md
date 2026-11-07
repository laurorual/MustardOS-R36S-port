# Fase 4 — C12: coordenador de init/shutdown

## Estado corrente — parada durável30 e retorno31 aprovados

O [incremento de energia](phase4-boot-power.md) qualifica reboot controlado
após diagnóstico C12 concluído, com seis passosRC0 persistidos na FAT antes
do pedido ao PID1.116 checks host, atualização dirigida/rollback e recusas
nativas passaram; retorno31/C07/rootRO/FAT desmontada/taint0/hashes conferidos.
Token consumido/allow_power0; poweroff físico/Power/suspend continuam pendentes.
Rede quente agora aprovada no37/38/39 com [políticaWi-Fi-only](phase4-usb-control.md),
bloqueando autoloadbtusb. A sequência de parada sozinha não resolvia. Próximo:
dadosrw/rootro e preferências, mantendo a política. BluetoothUSB não qualificado.

## Marco anterior — boot C12/27 e fallback C07/28 aprovados

Ver [boot de uso único](phase4-boot-once.md). Wrapper/seletor/recovery e
instalação dirigida passaram88 checks host e teste nativo. A candidata agora
tem seleção ativa opt-in: token consumido antes do27, menu90s confirmado,
reconexão física com ownership dos novos daemons, logs públicos duráveis e
retorno automático C07 no28. Sem token pendente/menu permanente. RootRO,
FAT desmontada/taint0 e restaurações conferidos. Áudio presente porém baixo,
SPK_HP/157/software100, ainda sem calibração. Shutdown/energia completos
continuam pendentes: nenhuma prova durável de todos os passos do shutdown27.
As seções abaixo registram a barreiraRAM anterior, não o estado atual do cartão.

## Marco anterior — barreira RAM em 2026-10-28

Adaptadores, controlador e seleção de init implementados como pacote opt-in.
Passaram20 fixtures de ordem e33 de controle/identidade/quiescência, macro real
de instalação, loader/shell AArch64 e Kconfig isolado. No console, a checagem
de encerramento passou sem sessão, recusou a sessão ativa e passou após
stop/cleanup do C11. Usuário confirmou o menu visível.

**Ainda não houve boot ou shutdown pelo C12.** A inittab nova é um template
inativo. Defaults enabled0/allow_power0; persistência continua desabilitada.
O cartão mantém C06r4+C07r3. Não promover este recorte a firmware/autostart
aprovados. O registro host antigo abaixo permanece como histórico.

### Implementação, evidência e limites

Código original MIT em `port/device/rk-r35s-p0/boot/`: `order.sh` define ordem;
`native-functions.sh` oferece guards/adaptadores; `step.sh` despacha cada passo;
`service.sh` oferece start/status/check-stop/prepare-stop/shutdown/reboot/poweroff.
`muos-boot.default`, `inittab` e `contract.json` completam a seleção opt-in.

O guard exige root, PID1 BusyBox, namespace igual ao PID1, kernel próprio
4.4.189, modelo Panel0 exato, taint0, /run tmpfs, CID/tamanho do cartão de
teste, PARTUUID4d554432-02 e raiz ext4 correspondente; recusa o cartão original
presente e FAT montada. É identidade de bancada, não suporte a qualquer cartão.

O controlador serializa transações com flock não bloqueante e fecha esse FD
nos filhos. Reutiliza muos-run-bounded AArch64 byte idêntico ao C11. Nenhum
script genérico rcS/rcK concorre com a cadeia da sessão. A seleção segue a
ordem de dependências já analisada no upstream: internal/script/init/sysinit
inicia udev/D-Bus/áudio/modo antes de S99; shutdown:8–9 percorre ordem inversa.

Reutiliza S05/S10 e helpers USB/rede C07 da candidata. O start de RNG recusa
estado preexistente, e stop sem marcador próprio não para o RNG do C07. Rede
registra PID/starttime/exe dos daemons criados, inclusive após retorno parcial;
recusa daemons/PID files preexistentes e stop sem ownership. Udev registra o
principal e aplica TERM direcionado; não usa killall no novo stop. Timeout que
impeça registrar identidade é falha fechada, sem assumir processos alheios.

`check-stop` não para serviços nem cria estado de boot. Exige status3, worker
sem identidade ativa, done/result0 e cadeia limpa quando existe geração,
lifetime lock livre e ausência de processos/sockets/readiness/montagens próprios.
Procura binds da sessão também nos mountinfo de outros processos. Status3
sozinho não comprova término do cleanup.

`prepare-stop` só aceita infraestrutura iniciada pelo C12. Recusa da sessão
ocorre antes de network.stop; não se garante conservar SSH se uma falha ocorrer
**depois** de network.stop. Reboot/poweroff exigem enabled1/allow_power1 e esse
preflight antes do pedido ao PID1. Defaults e teste nativo negaram ambos.
Power/suspend e chamadas diretas ao PID1 continuam sem aprovação.

Receita `port/buildroot/package/muos-r35s-boot/` depende de muos-r35s-session.
Instala a inittab em `/usr/share/muos-r35s-boot/inittab`, sem substituir
`/etc/inittab`, INSTALL_INIT_SYSV ou novo S??. Fragmento `phase4-boot.fragment`
é opt-in. Helpers diagnósticos C07 ainda são pré-requisito explícito; não se
afirma que este pacote sozinho constrói uma imagem funcional independente.

### Testes e provas

Stages relativos a build/phase4: boot-order/checks.huc6ivzq (20),
boot-order/adapters-checks.a2cqpw3v (33), boot-order/kconfig.edxi7sfh e
boot-order/coordinator.hvxl0yxe (receita, cópia de init e auditoria nativa).
Os fixtures de controlador substituem guard/dispatcher somente na cópia
descartável do container. As funções nativas são testadas separadamente com
estado sintético: PID reusado, cleanup incompleto, processo/bind/lock retido,
config gravável, concorrência, falha em cada passo impedindo energia e não
adoção de rede/seed C07. Não validam drivers/boot, timeout real ou syscall de
energia. Kconfig/parse usaram output separado; SDK .config manteve baseline.

`prepare-phase4-boot-coordinator.py` testa macro de instalação e loader/shell,
confere hashes C11 e seleção única em cópia host. Não gera imagem inteira.
`audit-phase4-boot-coordinator.py` instala somente pacoteRAM e testa a barreira
com uma sessão C11. Resultado nativo:

```text
idle-quiescent                       expected=0 actual=0
boot-disabled                       expected=0 actual=0
power-disabled                      expected=64 actual=64
foreign-infrastructure-not-adopted   expected=64 actual=64
active-session-blocks-quiescence     expected=1 actual=1
session-still-ready                  expected=0 actual=0
stopped-session-quiescent            expected=0 actual=0
```

Menu run-0001/lease60, worker857/start62600, firstpaint637.60, usuário “estou
vendo”; stop explícito result0/manual-stop. Perfil21 hashes e21 originais
passaram; mixer/brilho80/DRM/volume-store iguais antes/depois, sem writers da
raiz no relatório. Udev207/wpa302/DHCP303/Dropbear342 mantiveram PID/starttime.
Rootro/FAT desmontada/taint0; coleta final confirmou BOOT_SEQUENCE=26 e zero
assinaturas selecionadas de falha kernel/storage. Pacote /run/muos-c12.DzUEL2 e estado da sessão
removidos após coleta. Não houve reboot, C12 persistente, exportação de
seed/PSK/chave privada ou fsck na raiz viva. A transação C11 de cache/restore
foi executada: não se afirma identidade byte a byte de todo o filesystem.

Novo IP192.168.15.13:2222, confirmado pelo usuário e testado com a identidade
fixada: HostKeyAlias=[192.168.15.17]:2222, sem alterar known_hosts ou aceitar
outra chave. Provas imutáveis boot-coordinator-preflight e boot-coordinator-native
em dist/phase4/, com SHA256SUMS. Fonte executada da auditoria preservada no stage;
ajuste posterior apenas esclarece metadado de instalação C12 versus transação C11.

### Próximo incremento e persistência

Menor próximo teste: boot C12 controlado no mesmo cartão, com lease e logs
públicos, sem mudar bootloader/kernel/DTB. Antes de gravar qualquer integração:

1. Criar wrapper diagnóstico de boot com saída visível e relatório público
   durável. Não ativar a inittab com enabled0: ela não inicia rede/menu por si só.
2. Integrar recuperação física C07 à ownership C12. Rede criada pelo recover
   precisa receber identidades do coordenador; chamá-lo à parte faria o novo
   stop corretamente recusá-la como alheia. Warm Wi-Fi segue sem causa resolvida.
3. Testar seleção ativa/rollback no host e conservar recuperação C07. Ensaio
   de shutdown/PID1 separado; sucesso da barreiraRAM não o aprova.

Persistência continua volatile/false. Dadosrw com rootro, defaults só no
primeiro uso, retenção limitada de logs e recuperação sem formatar permanecem
requisitos. Política3 C10 força software100; bind persistente sozinho não
preserva volume. Revisar/testar política salva antes de volume60→reboot→60 e
brilho escolhido. Mapping/cache/PIDs/ready seguem runtime; templates de
placa/rota/ganho separados e seed/credenciais/chaves apenas no dispositivo.

## Registro anterior — preparação host com orçamento de7%

Rodada limitada pelo orçamento de sessão: somente host. A biblioteca de ordem
e o contrato foram preparados/testados; nenhum adaptador nativo, inittab,
imagem ou mecanismo de persistência foi ativado. C11 continua sendo o último
serviço validado no console. Não executar esta preparação como firmware.

## Evidências e decisão

A inittab da candidata (blueprint network-recovery.zz7sq2ve/extracted/etc/inittab)
chama muos-c07-run em sysinit e muos-c07-run stop em shutdown, depois swapoff
/umount. Esse stop não conhece o C11. Já o rcS/rcK genérico Buildroot percorre
S?? em ordem direta/reversa; ativá-lo junto com S98 duplicaria ownership de
D-Bus/storage/core/input, iniciados antes do coordenador de sessão.

O upstream internal/script/init/shutdown percorre serviços em ordem inversa;
sysinit inicia serviços críticos e S99 após áudio/modo, com outras ações de
manutenção. O C12 preparará uma única seleção explícita de serviços, com a
sessão C11 proprietária de D-Bus/storage/core/input/UI e a infraestrutura de
RNG/udev/USB/rede fora dela. Não encadear o runner C07 inteiro, que pode parar
aguardando recuperação: reutilizar helpers com resultados explícitos.

Detalhe decisivo: BusyBox1.37.0 init/init.c:758–775 executa run_actions(SHUTDOWN)
e depois kill(-1,SIGTERM)/kill(-1,SIGKILL). O retorno nãozero de um script não
cancela o desligamento. Portanto uma checagem de parada deve ocorrer ANTES
da solicitação de reboot/poweroff ao PID1. A ação shutdown da inittab pode
repetir cleanup idempotente, mas não garante manter SSH diante de uma falha.
Reboot/desligamento reais ainda não foram exercitados nessa integração.

## Código preparado

port/device/rk-r35s-p0/boot/order.sh é uma biblioteca; exige callbacks
boot_exec STEP LIMIT e diretório boot_state previamente guardados pelo futuro
adaptador. Não contém comandos reais de montagem, rede, energia ou instalação.
Não foi adicionada a nenhum serviço, receita, hook ou inittab.

Início: entropy.start → udev.start → usb.switch/rede opcionais → entropy.stop
→ root.seal → session.start/status. A carga do seed é tentada uma vez por
boot, protegida por mkdir start-once; chamada repetida pronta só consulta
status. Depois de falha, não repetir bootstrap/seed no mesmo boot: diagnosticar
ou reiniciar o ciclo da sessão independentemente quando apropriado.

Falha USB permite modo offline. Falha da rede só permite UI depois de parar
a inicialização parcial da rede. Falha crítica impede session.start; falha
de UI tenta stop/quiescent, mantém rede/udev para diagnóstico e sela a raiz.
Callbacks futuros precisam oferecer prazos reais; os valores fixados estão
no contrato e todos são1..120s, respeitando o executor já existente.

prepare_shutdown: session.stop → session.quiescent → network.stop → udev.stop
→ root.sync → root.seal. Erro interrompe os passos posteriores. Quiescent
precisará verificar status3, identidade do worker encerrada, ausência dos
processos próprios e montagens liberadas; não equivale apenas a aceitar stop0.
Nenhum umount global, swapoff ou pedido ao PID1 faz parte da biblioteca.
Se o PID1 já recebeu o pedido de shutdown, essa política não revoga sua ação.

## Contrato de persistência

boot/contract.json mantém implemented_mode=volatile e persistent_mode_enabled=false.
Global settings editáveis e volumes por saída são candidatos a armazenamento
persistente, ainda sem implementação. Templates de capacidades/defaults de
hardware permanecem separados de flags de sessão; mapping SDL, readiness,
PIDs/sockets e cache muvarctl nunca devem ser restaurados como estado válido
após reboot. Seed, credenciais e chave SSH privada continuam somente no
dispositivo; não exportar/hashar seus bytes para artefatos.

Antes de habilitar persistência, comprovar mount de dados rw com root globalro,
criação de defaults apenas no primeiro uso e tratamento de mídia indisponível
sem formatação. O perfil C10 usa política3, que volta ao máximo de software:
criar binds persistentes por si só não fará o volume escolhido sobreviver.
A política de volume salvo precisa de revisão do S80pipewire/var/audio e teste
volume60 → stop/start/reboot →60; brilho escolhido também deve sobreviver.
Não mudar para outro número de política sem conferir o comportamento real.
Configurações de placa/rota/ganho são templates, não autorização para persistir
flags como audio/ready ou board/sdl_map. Retenção/rotação de logs é requisito
antes de serviço permanente; esta rodada não criou uma partição de dados.

## Verificação e retomada

check-phase4-boot-order.py passou20 casos com callbacks simulados: início/
idempotência, recusa de recarga após falha, dependências críticas, offline,
limpeza parcial de rede falhando, falha de UI preservando infraestrutura,
ordem/parada idempotente e interrupção em cada estágio do shutdown.
Nenhum serviço real, seed, mount, SSH ou reboot foi executado. Os fixtures
não validam integração BusyBox/driver/boot ou recuperação física do aparelho.

Próximo, com orçamento restaurado: revisar adapters e guards; ligar a seleção
à montagem/inittab de uma cópia host, preservando bytes/kernel/DTB/bootloader
e identidade da mídia; conferir fallback/headless e parada antes da rede.
Só depois preparar ensaio nativo controlado com serviço/lease desabilitados
por padrão e recuperação C07 preservada. Ainda falta resolver ownership do
rcS e os efeitos do PID1 em shutdown; não publicar como init concluído.
