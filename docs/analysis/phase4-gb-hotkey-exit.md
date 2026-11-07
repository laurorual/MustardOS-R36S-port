# C50 — saída voluntária por Fn+Start

Concluído em02/11/2026, C07/boot68/IP192.168.15.14:2222. Super Mario Land
fechou pela combinação física e voltou ao launcher; usuário respondeu
**“Tudo certo”** à pergunta específica sobre fechamento e retorno. Log confirmou
`C50_EXIT reason=hotkey frames=547` e `expired=0`, sem esperar o prazo45s.
Ambas as sessões terminaram com operação0/cleanup0; console restaurado ao
diagnóstico, PCMclosed, rootRO0755/fundação97/taint0 e sem UI/core/áudio/input
residuais. Prefs55/70/mounts globais/infraPIDs preservados, cápsulas RAM removidas.
Não houve reboot, instalação, alteração do cartão original32 ou uso do Deck.

## Mudança restrita ao diagnóstico

Host C47 já tratava quit nativo, mas seu prazoC44 exigia expired=1 paraexit0.
Patch0015 adiciona `--diagnostic-hotkey-exit`, aceito apenas junto de conteúdo
diagnóstico com prazo1..60s; herda fresh e as recusas a no-content, restart,
netplay, subsistema e single-screen. Sem a flag, a regra C44 permanece igual.

`phase4-diagnostic-exit.h` distingue origem nativa “hotkey” de “internal”,
“remote”, NULL e outros valores. `request_quit("hotkey")` usa a detecção do
muOS existente; não há injeção ou emulação de botões no console. Setter direto
ou novo pedido de outra origem apaga a procedência de hotkey. main aceita a
procedência somente ao consumir o pedido de quit. A classificação final exige
frames reais: prazo→deadline, ou flag+pedido nativo aceito→hotkey; outras saídas
continuam falha. Se os indicadores coincidirem, prazo tem prioridade. Sinais
não geram uma saída normal aceita, e o supervisor mantém seus limites.

No modo novo, autosave, timeline e flush periódico de SRAM são desligados nos
settings em memória. Não são gravadas preferências ou habilitados saves duráveis;
outros caminhos de salvamento não foram qualificados. O runtime confere quit
habilitado/Start e publica `C50_HOTKEY_READY` com os três valores zero. Fn foi
conferido no perfilPanel0: BTN_TRIGGER_HAPPY5→BTN_MODE; SDL GUIDE→mux_input_menu.
Start normalizado é BTN_TRIGGER_HAPPY2→BTN_START. O usuário segurou Fn antes do
toque de Start, depois soltou ambos. Power, volume e brilho ficaram fora do teste.

## Build e checks

`build-phase4-gb-exit-host.py` clona somente o stage privado C47, aplica o patch,
inclui o helper MIT e recompila com o SDKcontainer/A35. Frontend base GPLv3,
licenças preservadas; nenhum ref ou SDK foi alterado. Guardas comparam todos os
demais fontes C/H e o ELF pai. CoreGambatte/ROM/UIlib/runner não foram recompilados.

Stage gb-exit/host.uuixcmie, ELF SHA
4f230ad1ca347a889e5eda2b5171aba4568670ae28a1b2d294abf4a95e8a44dd,
pai C47host._t02eefb SHA
2ba1ca32d2e3c7c9157d07043ecab26a8ef0913871dca0400fe57b66b92d7bc1.
`checks.8wl70wak` executou noQEMU40parsers de regressão,12novos e26casos da
política/origem/frames/precedência; loader/CLI passaram. Não repetir a API615
frames do C49: core e conteúdo estão byte-idênticos, com hashes conferidos.

`gb-exit/app-launch.sh` é exatamente o launcherC49 com marcador novo e flag
adicional; preserva manifesto/root/modos/links/SHA/ROMS emtmpfs. SelectC49 muda
somente a verificação do motivo de saída, aceitando hotkey ou deadline com
frames>0. A nova sessão automática exercita deadline45s→launcher20s, antes da
observação A→jogo→Fn+Start→launcher. WorkerC46 byte-idêntico, owner210/externo240,
quarentena de opções e restore existentes. `dispatch-check.eupxwstf` passou9
fixtures sem ROM privada/hardware: deadline, hotkey, motivo inesperado, falha,
zero frames, ready incorreto, erro do app, execução duplicada e argumentos reais
do launcher. Não contam como teste físico do hotkey.

## Rodadas nativas

- deadline.2ff2o774:2691frames/45s≈59,8fps, reason=deadline/expired1, retorno
  normal ao launcher, zero faltas/frames ausentes noCSV e cleanup0.
- observe.nc73v_sv: menu comprovadamente ativo antes da pergunta, seleçãoA,
  Start normal e Fn+Start físicos.547frames, reason=hotkey/expired0, app_status0,
  launcher apresentado e encerrado normalmente; zero faltas de áudio/cleanup0.
  Confirmação física do fechamento e retorno preservada.

`analyze-phase4-gb-exit.py` cruza motivo, frames, expiração, ready, log do pedido
nativo, retorno e CSV. **Não divide547por45:** a sessão voluntária foi curta,
sem medida própria de duração absoluta. O último core_hz do CSV foi59,88;
isso não é uma nova prova de throughput total. Janelas de até1024 amostras e
stages aninhados mantêm as limitações dos incrementos anteriores. Não houve
recalibração, ajuste de IRQ, quantum1024, codec215 ou clocks.

ROM continua privada/ignorada peloGit, bytes originais preservados; cópia do
console existiu somente emRAM e foi removida. Prova pública deve conter apenas
fontes próprios, relatório/recibos permitidos e metadados, com hashROM redigido:
sem ELF, ROM, frames, PCM, saves, preferências reais, chaves ou credenciais.
Bases C47/C48/C49 permanecem congeladas. O desempenhoNES continua pendente.

## Próximo incremento

C51: salvar e restaurar manualmente um estado pela interface/hotkeys nativos,
somente emRAM, com autosave desligado. Conferir Fn+R2/Fn+L2, suporte do core e
caminhos antes de pedir operação física; comparar metadados/retorno do jogo,
sem publicar estado bruto. Não unir persistência, Power ou instalação a esse
teste. Nenhum novo ensaio foi armado; estabilidade prolongada e novo boot
seguem sem qualificação.
