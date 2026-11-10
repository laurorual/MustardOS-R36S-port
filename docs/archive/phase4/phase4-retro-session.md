# C44 — sessão gráfica Libretro nativa com saída e restauração

Em 01/11/2026, no mesmo boot65/C07, o muxretro executou o core diagnóstico
C40 no R35S. O usuário confirmou a imagem e o movimento do quadrado pelo
direcional com o processo comprovadamente ativo. A sessão apresentou 2700
frames em 45 segundos e terminou normalmente, com limpeza e restauração
aprovadas. Nenhum executável foi instalado na raiz.

## Implementação

A base é o [muxretro C41–C43](phase4-muxretro-integration.md), snapshot
`5e8635b3b485eec9ad2ace141c415fd2df47d8f1`, com o caminho nativo de vídeo,
áudio e input. O patch0009 adiciona `--diagnostic-seconds=1..60`, permitido
somente com `--no-content`. Ele registra a primeira apresentação e termina
pelo fluxo normal de cleanup do SDL/core, recusando sucesso sem frames ou
sem expiração. A modalidade normal de conteúdo permanece separada.

`port/utils/muos-retro-runner.c` supervisiona o processo e descendentes:
sessão própria, subreaper, PDEATHSIG, prazo, TERM/KILL e reaping. O líder
permanece não colhido até a limpeza do grupo para impedir reutilização de PID.
Diretórios/recibos exigem dono, modo700 e ausência de symlink; não reutilizam
estado de execução anterior. Descendentes que abrem outra sessão também são
recolhidos. O prazo externo é recuperação, separado da saída normal do host.

O worker em `port/device/rk-r35s-p0/retro-session/worker.sh` combina preparo e
restauração C22 com dados RO/RAM do C43 em namespace privado e sob a trava
de sessão. Inicia DBus/storage/core/input, sem S99UI e sem simular seus
marcadores. Usa o ambiente SDL/EGL/KMSDRM/PipeWire do S99 já validado.
MUOSDATA real fica RO+noload; somente a cópia RAM de preferências é carregada
em55/70. Escritas de sysfs CPU/power são bloqueadas por binds RO no namespace.
Configurações, HOME, logs e userdata temporários ficam em RAM. C36 instalado
(IRQ/RW/ganho215/quantum1024) permanece preservado.

Foram inspecionados os caminhos nativos de startup/main/SDL do snapshot C41 e
o S99 instalado antes de adaptar o ciclo de vida. O core original C40 é MIT,
sem ROM ou BIOS. As dependências upstream mantêm as licenças e pins já
verificados em C41; nenhuma árvore refs/ foi modificada.

## Verificação

| Prova | Resultado |
| --- | --- |
| Parser/loader real no QEMU | 18 casos, mais 11 casos do prazo e CLI/LD_BIND_NOW |
| Supervisor com processos reais no host | 10 casos, incluindo timeout, sinal, grupo e sessão escapada |
| Worker com fixtures de guardas/rollback | 10 casos |
| Falha parcial nativa antes da gráfica | operação42/cleanup0 |
| Sinal nativo com filho ativo | operação143/cleanup0 |
| Gráfica final nativa | operação0/cleanup0, first-present e normal-exit, 2700frames/45s |
| Imagem e direcional físicos | usuário: “O quadrado se move corretamente” |
| PCM durante a janela ativa | 44099,15frames/s para44100, mesmo owner/trigger |
| Estado após encerramento | raizRO, fundação97/rede/PIDs preservados, mounts globais idênticos, RAM removida |

Build final: `build/phase4/retro-session/build.ghlnog9b`, ELF SHA256
`0e14879cf2fc7f72871bcf522a2c842654876bb9feb5feedd71eb4e9e4ba3068`.
Audit `audit.ddn0j999`; supervisor `runner.je_ael7e` e
`runner-checks.24ada8zp`; worker `worker-checks.8o3407co`.
Ensaios nativos finais `prepare-failure.epsgon78`, `signal-test.o2d69qem`
e `graphics.9s3c88qs`. Os ponteiros latest respectivos apontam para essas provas.

A primeira gráfica `graphics.o761lya4` falhou antes do frame por ambiente EGL
incompleto. A correção foi alinhar os exports aos do S99; depois foram
requalificados os dois ensaios de rollback antes de abrir a gráfica.
`graphics.6mz7gxbz` passou automaticamente, mas o relato de imagem sem movimento
chegou quando o processo já havia terminado. Esse relato não qualifica input.
A repetição final foi justificada por essa janela perdida: o recibo ACTIVE_PID
e first-present foi registrado antes do pedido físico; nela o movimento foi
confirmado. O framebuffer pode conservar o último frame após a saída.

Provas públicas congeladas em `dist/phase4/retro-session-native`, geradas por
`port/scripts/package-phase4-retro-session.py`, com SHA256SUMS. Incluem fontes
próprias, relatórios, marcadores selecionados e observação física; excluem ELFs,
imagens, blobs, cópias/fingerprints de preferências reais, backups e credenciais.
As fontes de cada relatório são conferidas individualmente; o worker anterior
da falha EGL permanece identificado como histórico, não como fonte atual.

## Limites e próximo incremento

O core gera áudio digital zero. A taxa PCM foi verificada, mas não houve teste
acústico de jogo. Os 2700frames qualificam este diagnóstico, sem estabelecer
compatibilidade ou desempenho geral de emulação. Preferências/saves só em RAM;
nada é salvo de volta. Não houve reboot, token C12/C25, mudança de kernel/DTB,
particionamento ou gravação da imagem C38. Original32 preservado, Deck fora
do fluxo. C07 segue acessível no65/IP192.168.15.8:2222, sem sessão ativa.

Próximo incremento proposto: integrar o ciclo launcher → muxretro → launcher
usando o mesmo core diagnóstico, sem conteúdo comercial nem saves persistentes.
Primeiro inspecionar o contrato nativo de despacho/retorno do frontend e construir
o adaptador em cópia privada; provar erro, sinal e retorno antes de pedir nova
observação física. Só depois planejar core de emulação e conteúdo redistribuível.
Não repetir C39 áudio, calibração, Wi-Fi, C44 aprovado ou instalação C36 sem
uma mudança concreta que exija regressão.
