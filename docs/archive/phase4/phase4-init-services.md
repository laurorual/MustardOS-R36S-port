# Fase 4 — espera de input e supervisão da interface

Incremento de 25/10/2026, exclusivo do R35S RK3326 com modelo
`R36S-V12 2023-08-18 Panel 0`. Os serviços passaram em namespace/RAM no
kernel dArkOSen instalado. A candidata foi reconstruída com autostart
configurado, **sem gravação de cartão ou boot independente**.

## Ordem e contratos

Buildroot continua proprietário de PID1, rcS/rcK, eudev e D-Bus. A ordem
do adaptador passa a ser:

```text
eudev → D-Bus → S90 storage → S95 core/audio/muinput
             → S96 input-ready/mapping → S99 UI
```

A parada usa a ordem inversa: UI/hotkeys, mapping, core/áudio/input e storage.
Não se executou o rcS inteiro no Debian anfitrião. O
[frontend.sh nativo](../../refs/muos/internal/script/mux/frontend.sh) foi
inspecionado: ele também depende de um pai vivo, mas agrega dispatch de
conteúdo, governadores, boot guard e outros contratos ainda ausentes.
O adaptador mantém os binários e helpers nativos e limita sua supervisão ao
bring-up, sem importar esses subsistemas em bloco.

- [S95](../../port/device/rk-r35s-p0/S95muos-foundation-core) mantém a guarda
  do storage e passa a exportar HOME/XDG/PipeWire/D-Bus/PATH explicitamente,
  sem depender do ambiente do executor de testes.
- [S96](../../port/device/rk-r35s-p0/S96muos-input-ready) espera pelo processo
  real de `muinput`, confere seu executável/PID/starttime, executa o mapper
  AArch64, grava e relê o SDL_MAP e só então publica `ready`.
- [S99](../../port/device/rk-r35s-p0/S99muos-ui) exige S96 pronto, prepara
  diretórios/associações nativos e inicia o supervisor. Repetir `start` não
  cria outro supervisor; `stop` pode ser repetido.

O mapper ganhou `alarm(2)` para limitar cada tentativa de SDL. S96 limita
tentativas e verifica deadline de12s; uma chamada iniciada perto do limite
pode consumir os2s restantes do mapper. Não declara pronto com descritor
incorreto, PID morto/trocado ou mapping sem readback.

## Supervisor nativo

[muos-ui-supervisor](../../port/utils/muos-ui-supervisor.c) é código original
MIT, compilado para Cortex-A35 com o SDK GCC13.4/glibc2.41 da candidata.
É o pai de `muxfrontend` e, quando habilitado, `muhotkey`, evitando a guarda
`getppid()==1` do frontend. O controle do supervisor usa PID+starttime e
lock próprio, para não sinalizar um PID reaproveitado.

O marcador de prontidão exige processos vivos e um **novo**
`/run/muos/first_paint`, produzido pelo frontend nativo em
`common/platform/display.c:1131`. O marcador anterior é removido a cada
início. Sem novo frame, o serviço falha por timeout. Isso não substitui a
confirmação de cores, orientação ou navegação pelo usuário.

Falha de um filho ou perda de `muinput` encerra a UI e registra a causa em
`/run/muos/ui/failed`. Não há relançamento automático em loop. A parada
envia TERM aos grupos próprios e usa KILL após a margem limitada.

**Fechamento adicional de ownership:** `common/runtime/exec.c:134–142` usa
`setsid` e duplo fork para tarefas de fundo. Portanto matar só os grupos
originais da UI não cobre todos os helpers. O supervisor usa
`PR_SET_CHILD_SUBREAPER` e recolhe filhos adotados, conferindo PPID e
identidade em procfs antes de sinalizá-los. O teste foi ampliado para essa
forma real de destacamento, incluindo helpers que ignoram TERM.

O serviço não interpreta ações de conteúdo/reboot/shutdown do frontend.
Saídas de fluxo que ainda dependam do dispatcher nativo deixam o serviço
parado e diagnosticável. Não é uma implementação completa de lançamento
de jogos, energia ou recuperação de crash do próprio supervisor.

## Testes automáticos no aparelho

O [executor](../../port/scripts/phase4-init-native.py) usou uma extração da
imagem finalizada, com metadados preservados por debugfs/fakeroot. No
namespace havia somente os nós necessários; cartões, PMIC e `/dev/fb0`
ficaram ausentes. A publicação de event/js foi feita pelo executor para
substituir **somente** devtmpfs/udev no `/dev` privado. O controlador foi o
`muinput` real: não houve injeção de eventos. Coldplug do boot real não foi
exercitado.

Passaram:

1. Autostart desabilitado não inicia UI; ausência de core bloqueia S96/S99.
2. Ausência dos nós do controle termina sem marcador pronto; publicação
   tardia permite gerar/confirmar o mapping nativo.
3. Start/stop repetidos não duplicam processos nem deixam filhos vivos.
4. Saída antecipada do filho gera falha; frame antigo não basta; processo
   vivo sem novo frame termina por timeout.
5. Morte inesperada do frontend encerra o irmão e descendentes, sem loop.
6. Perda do `muinput` real encerra UI e invalida a prontidão do mapping.
7. Helpers com `setsid`/duplo fork e TERM ignorado são recolhidos.

Os testes de falha substituíram os executáveis da UI **só no rootfs de RAM**
pela [fixture AArch64](../../port/diagnostics/service-child.c). Ela não entra
na imagem de firmware. Seus marcadores de frame simulam o handshake e não
contam como teste de pixels. Os binários reais foram restaurados, e as
sessões visuais seguintes usaram a imagem/serviços reais.

## Testes visuais e áudio

Duas sessões pelo próprio S99 passaram. A primeira,100,635s, confirmou
launcher/Informações/Configurações, áudio, volume100→95→100 e
brilho80→75→70→75→80. O PCM amostrado foi S32_LE/stereo/44100Hz,
period512/buffer2048, com Playback157,157 ajustado previamente pelo usuário.
O ganho de software unity foi um override de diagnóstico; o preset35 da
imagem não foi alterado.

Após ampliar o recolhimento de helpers destacados e repetir as falhas,
a sessão final terminou por solicitação aos **53,746s**. O usuário confirmou
“Tudo certo”. O frontend teve o supervisor como pai e produziu first_paint
novo; foram observados launcher/Exploração/Informações/Configurações.
A saída foi feita por `S99muos-ui stop`, não pelo supervisor Python matando
o frontend diretamente.

Os WAVs originais foram mantidos nas duas sessões. O usuário confirmou
novamente que o som da ajuda é muito baixo/estranho. Ele **não está aprovado**;
isso não demonstra corrupção do arquivo nem aprova uma substituição definitiva.

Após as cinco sessões: serviços dArkOSen ativos, mixer igual ao snapshot,
brilho80, kernel instalado inalterado, taint0 e cinco contadores Btrfs0.
Sessões de RAM foram coletadas e removidas. Não houve instalação no Debian,
gravação de imagem ou carga de módulos candidatos no kernel instalado.

## Imagem e próximo passo

O instalador exige `--validated-runtime --init-services --enable-ui` para
configurar autostart. O último argumento só é aceito se os serviços atuais
corresponderem aos aprovados nos testes automático e visual.

Imagem privada final:512MiB ext4, **283 ELF AArch64**, SHA256
`5bf98b953d09253e8b1fe0bf5559e6848649fff274090b5755c5fdf01235a0a9`.
QEMU/link/ABI/GBM, readelf do supervisor, status3 sem runtime, comparação
byte a byte dos componentes, configuração enabled1 e fsck passaram.
Autostart está configurado na candidata do host; **não foi instalado no
dArkOSen nem validado por cold boot**.

Faltam módulos/firmware do BSP na raiz, cadeia U-Boot/DDR/BL31/BL32/DTB,
boot em mídia identificada, bateria/energia/blank/suspend, dispatcher de
conteúdo e ensaios prolongados. O timer externo de restauração não foi
disparado à força. Termos de blobs continuam no registro privado para o
Markdown consolidado ao fim do projeto.

Provas/fontes estão no
[checkpoint](../../dist/phase4/init-services-native/native-results.json)
`dist/phase4/init-services-native/`, com checksum de cada arquivo. Ele separa
as versões intermediárias e as aprovações finais, e exclui imagem/runtime
Mali. A imagem privada e o staging permanecem em `build/phase4/`, sob os
controladores foundation; os checkpoints anteriores não foram sobrescritos.
