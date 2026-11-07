# C106 — sessão gráfica pelo caller instalado

Data: 07/11/2026. Código próprio MIT, sem nova compilação upstream ou imagem.
O caller C105 passou agora pelo ciclo completo menu → Game Boy → menu,
usando o entrypoint e o worker instalados no boot81 já qualificado.

## Implementação

`phase4_installed_caller_session.py` confere instalação, plano, fontes,
recibos e prova congelada C105. A observação nova exige o contador/UUID reais
do mesmo boot81, layout C102 e a guarda original `c25_ready`. A conferência
externa inclui143 hashes da fundação/layout e17 arquivos do caller, com
metadados e diretório próprio verificados. C104/C105 permanecem intactos.

O harness C77 é adaptado por âncoras finitas: dez scripts deixam de ser
enviados pelo SSH. `caller.sh stage` os copia do componente instalado para
RAM, vinculando-os ao pacote e ao boot. A chamada nativa passa por
`/bin/sh /usr/libexec/muos-caller/caller.sh run <capsule> observe`, que verifica
os assets e executa o supervisor/namespace/worker original instalado.

A preparação restante de assets/metadados e da ROM privada continua no
harness explícito. O fluxo ainda não é navegador geral de ROMs nem launcher
automático. Nenhum script, serviço, token ou payload persistente novo foi
instalado neste incremento; dados persistentes foram usados somente leitura.
O limite do jogo continua45s, worker210s e supervisor240s. O prazo de coleta
SSH é300s para incluir as verificações anteriores à abertura do supervisor.

Além dos três mapas menu/jogo/retorno, o watcher confere PID/starttime e a
linha de comando real do manager: `/bin/sh` executando o worker instalado.
O fechamento exige o marcador de execução única criado pelo caller e compara
a cópia em RAM ao worker instalado antes de removê-la. Assim, a evidência
comprova o caminho executado, não apenas a presença dos novos arquivos.

## Verificação

**17 testes novos** em `installed-caller-session/checks.0rskku83`:
qualificação C105, boot antigo/novo/tipo inválido, inventário160, UUID/vínculos
C105 incorretos ou ausentes, roteamento stage/run sem upload dos scripts,
recusa de âncora alterada, evidência de worker/marcador único e watcher
limitado sem ler environment.43casos C105 e4grupos de vínculo foram reutilizados
por integridade, sem reexecução. Nenhum core/ROM/SSH/reboot/imagem nesses checks.

**Sessão nativa aprovada:** `installed-caller-session/load.mdsjxv2d`, observação
`observe.c7dg6jhs`, boot81 em192.168.15.8. O usuário confirmou imagem, controles,
som, restauração Fn+L2 e retorno Fn+Start: “Tudo certo. A ROM demorou um pouco
mais que o normal para carregar, mas o teste foi um sucesso.” A resposta está
guardada privadamente e vinculada à mesma análise da sessão.

A abertura mais lenta é observação subjetiva registrada; não foi medido o
intervalo entre A e o primeiro frame nem demonstrada uma causa. O marcador
`C44_FIRST_PRESENT seconds=45` indica o limite de sessão, não tempo de carga.
Não repetir o teste ou atribuir o atraso ao C105 sem uma medição específica.

1255frames, saída por hotkey sem expirar, mapas completos e worker instalado
confirmado. Snapshot/metadados idênticos ao C63, duas chamadas status e uma
exportação, sem QuickSave. Mixer/DRM/volume/brilho/WirePlumber e preferências
55/70 restaurados. Native0/OPERATION0/CLEANUP0, postflight/mount-health/
caller-execution/cleanup/stopped-screen0, raizRO0755, PCM fechado, p1/p3
desmontadas, UIoff/taint0, infraestrutura PID/starttime e mountinfo global
preservados. Cápsula removida; página final de diagnóstico escrita.

Analisador C77 congelado reutilizado sem alterações: taxa recente59,9401Hz,
5underruns/1940frames de áudio ausentes agregados. Não localizam o evento nem
qualificam desempenho sustentado; som limpo/audível foi confirmado pelo usuário.
O fechamento offline usa recibos autênticos, imagem ancestral e SDK preservados,
sem alegar uma nova observação do console. Prova sanitizada própria em
`dist/phase4/installed-caller-session`, sem ROM, ELF, estado, seed ou UUID real.

## Armazenamento e próxima etapa

Outra revisão descartou1381 arquivos de fixtures e pacotes temporários antigos,
recuperando539.611.136bytes, aproximadamente515MiB físicos. Relatórios,
scripts de reprodução e1484 entradas protegidas foram preservados; a cadeia
C104/C105/C106 passou novamente. `build/phase4` está aproximadamente17GiB,
com43GiB livres no SSD. Não foi criada imagem completa para C106.

O próximo recorte é preparar assets/cápsula no próprio aparelho para reduzir
a preparação ainda dependente do harness. Planejar a origem da ROM e os
acessos ao volume de dados antes de alterar o pacote instalado. Autostart,
navegador geral, SRAM/novos saves, Power/suspend/boot frio/longa duração
continuam separados. O cenário de inserção tardia do dongle foi adiado pelo
usuário; não investigado nem testado neste incremento. Não houve reboot ou
acesso ao Steam Deck/cartão original32.
