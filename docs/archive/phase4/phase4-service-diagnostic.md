# Fase 4 — C01: BusyBox PID 1 e serviços selecionados

**Resultado: C01 aprovado em boot nativo, com logs coletados e retorno
verificado ao dArkOSen.** O B01 anterior foi fechado com logs e
fsck/saúde aprovados em `dist/phase4/native-ext4-boot/`.

## Recorte e contrato

O [bootstrap](../../port/device/rk-r35s-p0/service-diagnostic/bootstrap)
confere modelo, release, CID, MAJ:MIN e raiz ext4 inicialmente ro; exige UI
e áudio desativados e o marcador C01. Recusa o dongle 0bda:c820 para limitar
o coldplug aos dispositivos do console. Depois executa `/sbin/init` como
PID 1. A symlink aponta ao BusyBox da base própria.

O inittab deriva da base, preservando copyright e montagem/hostname dos
sysinit. Retira o getty serial e o mount proc duplicado. A entrada que
chamava rcS chama o [runner diagnóstico](../../port/device/rk-r35s-p0/service-diagnostic/run).
O shutdown aponta à parada do mesmo recorte; shutdown de software não é
exercitado neste ensaio. Não é uma aprovação do rcS completo.

A [cadeia](../../port/device/rk-r35s-p0/service-diagnostic/chain.sh) aciona
S10udev → S30dbus-daemon → S90 → S95 → S96 → S99 com `enabled=0`.
S95 usa `audio=0,input=1`. Seedrng, syslog, sysctl, rede e cron não são
acionados pelo runner. Udev real dispara os eventos de subsistemas/devices;
o callback exige gpio_keys e odroidgo3-keys, sem modprobe explícito de
fallback. D-Bus precisa responder ListNames; S90/S95/S96 precisam status
positivo, com controle normalizado e mapping SDL publicados.

S99 desativado e a ausência de muxfrontend/muhotkey/pipewire/wireplumber
são verificadas. Depois a cadeia para em ordem inversa, aguardando os
processos saírem. Restos de muinput/D-Bus/udevd são tratados como falha;
o diagnóstico tenta terminá-los e salvar evidências. A raiz deve voltar
ro e o FAT ser desmontado antes do marcador final DIAG03.

O novo [executor](../../port/utils/muos-run-bounded.c) é compilado pelo SDK
AArch64/Cortex-A35 do userspace próprio. Cada comando de serviço tem 45 s;
D-Bus RPC tem 5 s. Após o limite, TERM e KILL atingem o process group.
Daemons que usam setsid dependem dos scripts nativos de stop e da limpeza
específica do diagnóstico. I/O bloqueado no kernel não tem garantia de
limite rígido. Não apresentar esse mecanismo como contenção geral.

## Preparação e escrita delimitadas

O [preparador](../../port/scripts/prepare-phase4-service-diagnostic.py)
clona a ext4 B01 corrigida em arquivo regular, incorpora sete arquivos e
confere o restante dos arquivos/links sem alterações. Fsck, ELF, shell e
QEMU passaram. Testes do executor cobrem sucesso, exit 7 e timeout com
TERM ignorado; fixtures da cadeia cobrem sucesso, falha de start/coldplug
e falha de stop, com rollback reverso e stop idempotente. Essas fixtures
não executam os serviços de hardware nem simulam aprovação nativa.

O [instalador](../../port/scripts/install-phase4-service-diagnostic.py)
confere cartões, root/boot originais, PARTUUID/capacidade, hash do instalador
e de cada novo arquivo, além dos hashes anteriores. A p2 precisa estar
sem montagem. Opera em namespace privado com noexec e backup das preimages;
ativa o bootstrap por último, usa substituições atômicas/fsync, desmonta
e roda fsck read-only. Há rollback em falhas de instalação. O kernel,
U-Boot, p1 e tabela de partições não foram alterados.
O caminho de rollback do instalador não recebeu injeção de falha nesta
rodada; os testes de rollback descritos acima exercitam a cadeia de
serviços, não uma interrupção da escrita do payload na mídia.

A mídia continua com PARTUUID `4d554432-02` e `DIAG.ID` B01 no FAT. O
bootstrap do cmdline ainda se chama muos-ext4-diag e passa ao BusyBox;
o marcador C01 na raiz e os logs DIAG03 identificam o novo experimento.
Portanto o cartão atual é B01 + correção + payload C01, não o raw original.
Nunca usar o raw B01 antigo sem as correções/overlay apropriados.

Build/payload: `build/phase4/linux-diagnostic/services.kd5t73ez`.
Prova anterior ao boot: `dist/phase4/service-diagnostic-preboot/`, com
fontes, executável próprio, payload, backups e auditorias. A imagem raiz
privada com Mali e outros payloads proprietários permanece em build.
Licenças pendentes seguem o registro privado e o relatório final único.

## Ensaio físico previsto

Desligar dArkOSen normalmente; só depois guardar o cartão original de
32 GB, colocar o de 128 GB no slot OS e deixar o segundo vazio. Retirar
o dongle Wi-Fi para este recorte. Esperar até cerca de dois minutos por
`C01: BUSYBOX_INIT / COLDPLUG / INPUT OK`, serviços parados, raiz ro e
`Logs saved: DIAG03 (FAT unmounted)`. Não testar botões, volume ou Power
curto durante a subida.

Depois voltar ao dArkOSen com o console desligado para trocar a mídia,
reconectar o dongle e coletar logs/fsck em modo read-only. Em caso de
STOPPED, guardar a mensagem antes do retorno. A tela e os logs precisam
confirmar o resultado; o host não valida o boot, eventos de controles,
UI/áudio/GLES, Wi-Fi, shutdown ou outros painéis.


## Resultado físico e fechamento

O usuário confirmou a tela final e retornou ao dArkOSen. DIAG03 foi
recuperado por namespace privado/read-only; fsck offline da ext4 retornou
0. O [analisador](../../port/scripts/analyze-phase4-service-boot.py)
conferiu PID 1 BusyBox, inittab diagnóstico, serviços, mapping e limpeza.
Prova imutável: `dist/phase4/native-service-boot/`.

Trechos relevantes do report e do RPC:

```text
Linux muos-r35s 4.4.189-muos-r35s-p4
PID1
/bin/busybox
init
ACTIVE STATUS
0
FINAL STATUS
0
TAINT
0
C01_DIAGNOSTIC_STATUS=0
string "org.freedesktop.DBus"
```

Amostragem de uptime no report: **10,34 s**. O dmesg inclui root inicialmente
ro, remount rw, e remount final ro aos 10,46 s. Coldplug registrou
odroidgo3-keys/gpio_keys; S95 criou muOS-Keys e S96 publicou mapping SDL
GUID `06004ca66d750000043500006f730000`. O controle virtual desapareceu no
stop, os binds foram removidos e a raiz terminou ro. Não houve necessidade
de terminar daemons remanescentes pelo fallback de cleanup.

A parada de udev registrou `No such process` para alguns workers que
saíram durante killall. Os scripts de stop, os testes pidof e o status
final passaram. O ps padrão pode filtrar processos de outro UID; a prova
do D-Bus ativo é o RPC, e a parada é conferida por PID/pidof, não somente
pela tabela filtrada. Não houve Oops/BUG/panic/call trace ou erros de
I/O/MMC/ext4 na busca documentada do log coletado. Isso não é um teste
prolongado nem prova de ausência de todo problema.

**Pendência observada:** udev leu urandom enquanto o pool ainda não estava
inicializado, com avisos aos 5,0 s. Seedrng foi omitido intencionalmente
da cadeia selecionada. Integrar origem/armazenamento do seed e avaliar
a inicialização de entropia antes de aprovar o init completo. Não inferir
que esses avisos sejam uma regressão resolvida ou que o arranque completo
esteja aprovado. Wi-Fi e serviços de rede permaneceram fora do teste.

Após a volta, duas conferências SSH mostraram Image `31bdb671…b0577`
preservado, taint 0, cinco contadores Btrfs 0, ES/ogage/Fn ativos e nenhuma
unidade muos carregada. A coleta privada foi desmontada, seu temporário
removido e SSH encerrado. SD2 continua montado pelo próprio dArkOSen;
a p2 da candidata está desmontada. Não há operação de escrita ou ensaio ativo.

## Próximo incremento

Fechar o bootstrap inicial/seedrng para o init completo e preparar o
primeiro ensaio de UI e áudio/GLES no kernel próprio, com supervisão,
logs e retorno. O C01 mantém UI/áudio inativos: não basta ligar flags e
presumir compatibilidade do renderer ou do codec. Eventos dos controles,
volume/brilho, Power/idle/shutdown e Wi-Fi ainda precisam de validação
nesse conjunto nativo. Não reconstruir os marcos anteriores só para retomar.
