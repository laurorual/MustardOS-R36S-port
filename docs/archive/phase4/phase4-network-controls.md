# Fase 4 — C09: volume e brilho com frontend e SSH

O incremento preserva o acesso C07 e a cadeia temporária C08. Habilita
muhotkey junto ao supervisor S99 somente na sessão de120s, sem alterar boot,
kernel, perfil persistente ou executáveis instalados. O recorte nativo de valores medidos e restauração passou, com ressalvas
visuais/acústicas descritas ao final; preparo em `port/scripts/prepare-phase4-network-controls.py`.

## Evidência e escolha

- `port/device/rk-r35s-p0/session-hotkeys.json`: apenas VOL_DOWN/UP com
  negateMENU e BRIGHT_DOWN/UP com MENU. Perfil instalado contém só esses quatro
  atalhos; `refs/muos/frontend/module/muhotkey.c:1077–1098` carrega os JSON de
  share/hotkey (`common/base/options.h:151`). Não acrescentar Power/suspend.
- Helpers instalados `opt/muos/script/device/audio.sh` usam wpctl, flock,
  incvolume e SET_SAVED_AUDIO_VOLUME. `script/var/audio.sh:115–165` também
  salva volume por saída em share/volume: diretório precisa de bindRAM além
  dos binds de config do C06. C08 não media integralmente esse diretório;
  não afirmar restauração byte a byte de todo o rootfs nos ensaios anteriores.
- `script/device/bright.sh` usa Fn+volume e DISPLAY_WRITE; em
  `script/var/display.sh:225–235`, setbl escreve no sysfs backlight detectado.
  Leitura nativa Panel0: brightness80/max160, configuração80, incrementos5.
- `port/patches/0006-frontend-r35s-normalized-volume.patch` remove a leitura
  raw duplicada no frontend; volume chega pelo gamepad muinput. Isso evita
  reutilizar a correção apenas como suposição: o trace medirá os passos reais.

Somente o helper C06 copiado para o pacoteRAM é adaptado: hotkeys1, janela120s
e checks do volume software permitem0..100% durante interação. Grupos de
referência continuam unity; efeitos C06 aprovados e hardwareSPK_HP/157 ficam.
As substituições são ancoradas/contadas e o helper instalado é pré-requisito
por SHA. Não substituir o arquivo instalado para esse ensaio.

## Guardas e restauração

`network-controls-diagnostic/extension.sh` exige max160 e brilho inicial40..160,
salva valor real, hashes adicionais de brilho/incrementos/overdrive/perfil,
e snapshot/hash da pasta de volumes. Sobrepõe config e share/volume comRAM;
overdrive0 e incrementos5. Antes do menu, executa os helpers reais D/U uma
vez cada e exige volume95→100 e brilho75→80 nesse aparelho. Falha interrompe
antes de iniciar o frontend. O fixture de passo duplicado identificou que
set-e dentro de função usada em condição não bastava: readbacks agora têm
saídas explícitas, validadas nos caminhos negativos.

Durante a janela, monitor registra somente mudança de volume configurado,
backlight e leitura wpctl. Não abre evdev, evita um segundo leitor de botões.
Esperado manual: (100,80)→(95,80)→(100,80)→(100,75)→(100,80), com pausas1s.
Confirmação visual/auditiva ainda é necessária; trace isolado não prova isso.

Supervisor para UI/hotkeys/grandchildren antes do cleanup. Monitor é encerrado;
core/áudio param, binds são removidos, brilho real é restaurado com readback,
pasta de volume comparada, config/cache conferidos. Herdam-se checks C08 de
mixer/13hashes/DRM/PIDs de rede e udev/rootro/socket/logger. Watchdog300s e
parada supervisionada continuam ativos. SSH global usa raizro enquanto a
sessão opera em namespace privado. Sem recarregar seed nem trocar cartões.

## Validação disponível

Nove fixtures de helpers, passos duplicados, parada do monitor, restauração,
mudança de máximo/config e brilho fora do intervalo passaram em container
sem acesso ao hardware. Oito fixtures de cadeia e sete de identidadeudev do
C08 são reexecutados. Shell do pacote é verificado no BusyBox AArch64/QEMU.
Isso não substitui ensaio nativo, nem aprova outros painéis, Power/suspend,
fones, volume persistente após reboot ou estabilidade prolongada.


## Primeira sessão nativa: helpers e restauração passaram

Pacote network-controls.r749y74h, C07r3/BOOT0025 recuperado. Helpers automáticos
confirmaram software95→100 e backlight75→80. Supervisor iniciou muhotkey
PID4143 com pai/manager4140; menu/áudio/SSH simultâneos. Usuário confirmou
funcionamento geral, relatando volume percebido40–60% apesar da barra100%.
A barra reflete software, ganho codec157 permanece fixo; loudness e máximo
acústico não foram calibrados. Não aumentar indiscriminadamente o codec ou
inferir equivalência numérica com o driver stock.

Resultado nativo0; mixer/13hashes C06+5hashes controles, pasta de volumes,
cache, DRM e brilho80 restaurados. Infraestrutura preservada, rootro/FAT
 desmontado/taint0, sem processos de UI/áudio/socket D-Bus, assinaturas
fatais/storage selecionadas0. Coleta não incluiu logs privados de rede/seed/key.
Prova network-controls-exploratory-session guarda essa evidência parcial.

Trace mostrou várias mudanças: volume100→55→100 e brilho80→20→115, com
restauração80 no cleanup. Perguntado se houve exploração/hold/vários toques;
sem essa confirmação não atribuir repetição ao software/hardware nem aprovar
um passo por toque. Amostragem200ms pode agrupar mudanças rápidas; helpers
CLI dão passo5 com readback, mas isso não prova o caminho botão→helper.


Usuário esclareceu que fez vários toques para explorar os níveis, mantendo
apenasFn pressionado. Portanto o trace não indica repetição indevida por si.
Nova rodada60s fará somente quatro toques com pausas, sem exigir perceber
acusticamente/visualmente a diferença pequena de5; leitura SSH comprovará
os valores. Efeitos/ganho/fluxo de cleanup iguais, somente janela menor.


## Rodada isolada: valores por toque aprovados, ressalva visual preservada

Pacote network-controls._yj3a8oo, janela60s e mesmos assets/helpers. Usuário
fez os quatro toques pedidos. Trace exato: (100,80),(95,80),(100,80),(100,75),
(100,80). Software lido0,95/1,00 acompanha volume. Todos os checks de
restauração e saúde passaram, com33probesSSH/30comUI e61,99s simultâneos.
Prova network-controls-session, análise no stage final. PacotesRAM removidos
após saída do supervisor; console continua C07r3/BOOT0025 com SSH e rootro.

Usuário achou que o brilho visualmente mudou dois passos por toque. A medida
estável foi5unidades, não10. O fonte em frontend/common/platform/sysinfo.c:394–397
usa val*100/device.screen.bright com divisão inteira:80/160→50 e75/160→46.
common/ui/common.c:1585–1588 aplica percentual com LV_ANIM_OFF. Isso explica
que um incremento nativo ocupe vários pontos percentuais; não prova a causa
precisa da percepção visual. Mantida como observação para próxima revisão da
escala/UX. Não foi coletada captura visual dessa barra nem alterada sua escala.

O resultado aprovado é o caminho nativo de controles/valores e seu cleanup.
Calibração acústica/máximo, percepção visual, parâmetros persistentes ao ligar,
Power/suspend/fones/longa duração continuam pendentes. Nenhuma política de
volume/boot foi promovida a permanente a partir desse diagnóstico.
