# C45 — ciclo diagnóstico launcher → muxretro → launcher

Em01/11/2026, no boot66/C07 do R35S, o ciclo diagnóstico corrigido foi aprovado
tecnicamente e pelo usuário: navegação nos menus, quadrado controlável e retorno.
A imagem estática conservada na saída foi substituída por uma página de término;
o usuário confirmou “Sim, apareceu a tela de diagnóstico”. O aparelho permaneceu
no66/IP192.168.15.15:2222, raizRO/fundação97/rede preservadas, PCMclosed e sem
sessão ativa. Nenhuma biblioteca ou executável foi instalado na raiz.

## Implementação e referências

Foram inspecionados como referências somente leitura o frontend upstream
module/muxfrontend.c, module/muxlaunch.c, common/runtime/exec.c, e os scripts
internal/script/mux/frontend.sh e script/launch/mu-general.sh. O contrato usa
pedido em /run/muos/action, saída do frontend, execução síncrona do host e nova
abertura do launcher. O supervisor instalado S99 considera qualquer saída da
UI uma falha; não foi reutilizado como despachante de conteúdo.

Patch0010 e port/diagnostics/phase4-launcher-cycle.h fornecem opt-in diagnóstico
na cópia privada de libmuxmod. Sem as duas variáveis de diagnóstico, mantém-se
o caminho anterior do launcher. O gancho delega ao ui_common_handle_idle nativo
para preservar LVGL/render, aguarda apresentação real e prazo1..30s, grava
pedido fixo pelo load_mux nativo, chama safe_quit e encerra o input. Registra
seriais inicial/final. Só o direcional é habilitado no diagnóstico: handlers
A/B/X/menu, combos default e tour são desativados. Não aceita comandos ou
caminhos arbitrários. Upstream GPLv3, patch conserva essa licença; helper
original do port MIT. Nenhuma árvore refs/ foi alterada.

cycle.sh consome somente o pedido exato após exit e reaping do frontend,
executa coreC40 no-content por15s via muxretroC44 e abre um segundo launcher.
Cada etapa tem estado novo do supervisor C44 já qualificado. Retorno também
exige apresentação e saída normal; falha intencional do core exige retorno
antes do resultado42. Uma execução por cápsula, sem repetição automática.

O worker reusa preparo/restore C44 e RO+noload+RAMuserdata do C43. Adiciona
namespace privado de /run/muos e tmpfs em /tmp para não alterar controle global
(action, safe_quit, first_paint, caches e temporários). A trava global é
adquirida antes da sobreposição e mantida pelo descritor aberto. Preferências
reais não recebem saveback. A biblioteca privada é escolhida via LD_LIBRARY_PATH
somente nas duas aberturas do frontend. SysfsCPU/power continuam protegidos RO.
C36 instalado IRQ/RW/215/q1024 e preferências55/70 são preservados.

## Provas finais

Build privado `launcher-cycle/build.bj_j_v6r`, libmuxmod SHA256
`5e14e0c7716a2671bfacbaf8659a5ec5de74a396f6f2045f845e09fbfd1237c2`.
Só module/muxlaunch.c foi recompilado antes do relink. Biblioteca original
bfd909c6... coincide com C38 e permanece intacta; SDKbaseline preservada.
Checks `checks.u1hv7yyu`: hook AArch64 real em QEMU, binding imediato da nova
biblioteca, mais14casos de coordenação/rollback/contrato da guarda de dados.
A regressão exige delegação ao idle original e serial atualizado por ele.

| Modo | Stage em build/phase4/launcher-cycle | Resultado |
| --- | --- | --- |
| Falha parcial de preparo | prepare-failure.vakz8s6f | operação42/cleanup0 |
| Sinal com filho ativo | signal-test.5eomen8f | operação143/cleanup0 |
| Falha do core e retorno, biblioteca corrigida | core-failure.qimujffn | doismenus com apresentação/exit0, core1, operação42/cleanup0 |
| Ciclo completo corrigido | cycle.vsygur6z | doismenus/exit0 e core15s, operação0/cleanup0 |
| Observação corrigida | observe.qmmr123o | core902frames/15s, menus20→94 e20→183 apresentações, operação0/cleanup0; usuário “Tudo pareceu funcionar normalmente” |
| Página final | stopped-screen.* no último stage | escrita protegida na tty0, sem iniciar sessão; confirmação física positiva |

Preparo/sinal não executam a biblioteca diagnóstica. Foram preservados seus
recibos anteriores: worker, coordenador e supervisor permaneceram byte-idênticos
quando apenas o gancho de render foi corrigido. Os relatórios mantêm as versões
de checks e biblioteca realmente usadas, sem reclassificar o histórico.

Todos os ensaios coletados preservaram raizRO/fundação97/rede/PIDs, preferências
reais e mounts globais. Cópias/ELFs/helpers RAM removidos; PCMclosed. A pergunta
física final foi enviada antes do dispatch; recibo separado confirmou PID/starttime
do retorno e marcadores do core. O relato integral foi preservado. Não houve
reboot, token C12/C25, flash, alteração de kernel/DTB/partição ou uso do Deck;
original dArkOSen32 intacto.

Prova congelada: dist/phase4/launcher-retro-cycle, gerada pelo script
port/scripts/package-phase4-launcher-cycle.py, com SHA256SUMS. Fontes próprias,
relatórios e marcadores selecionados, sem ELF/imagem/blob, preferências reais
ou seus fingerprints, backups, chaves, seed ou credenciais.

## Falhas resolvidas e distinção entre atividade e último frame

prepare-failure.ohpb_nap recusou64 antes dos serviços porque /run/muos-cycle
não está na whitelist da guarda instalada. Cleanup0; corrigido reutilizando
/run/muos-prefs-data, sem ampliar a guarda. O teste cruzado de whitelist foi
acrescentado. Uma falha de nome na fixture seguinte parou no host; o controller
recusou hashes incompatíveis antes de novo dispatch. Checks foram corrigidos.

A biblioteca inicial build.fq2iwo17 e os estágios core-failure.kmh2oef0,
cycle.15z8huhf e observe.hesjp4pt passaram tecnicamente. Porém, a observação
reprovou navegação visual: som sem mover seleção. O gancho substituíra
idle_handler sem executar ui_common_handle_idle, que init_input só instala
quando o campo é NULL. Faltavam lv_task_handler/lv_timer_handler. A correção
delegou ao handler original e passou a registrar progresso real de apresentação.
Retorno com falha e ciclo completo foram requalificados com a biblioteca nova.
O relato inicial também descreveu quadrado intermitente entre várias aparições;
não permitia atribuir cada uma a um stage. Não foi contado como aprovação.

Na observação corrigida tudo funcionou durante a sequência, mas o usuário viu
o quadrado parado antes/depois e perguntou se o jogo continuava aberto.
O muxretro espelha o último frame no framebuffer na saída; essa imagem estática
não significa processo ativo. SSH confirmou ausência de frontend/core/input/
áudio e PCMclosed. O helper stopped-screen.sh, executado SOMENTE após coleta,
valida c25_ready/boot/PCM/ausência de UI antes de escrever uma página na tty0,
como já faz o worker C22. Usuário confirmou a substituição da imagem. Não
mudamos o worker validado nem repetimos a sessão gráfica para essa escrita.

## Limites e próximo incremento

É despacho automático de diagnóstico, sem seleção de ROM, conteúdo comercial,
BIOS ou saves persistentes. CoreC40 gera áudiozero; não qualifica som de jogo
nem desempenho geral. Frontend.sh completo não foi instalado ou habilitado.

C46 preparado como plano: seleção da aplicação diagnóstica pelo menu nativo.
Inspeção inicial confirma que muxapp.handle_a grava application, module_app
escreve action=app e safe_quit, e frontend.sh consome APP_GO antes de executar
mux_launch.sh. O adaptador deverá aceitar só o diretório RAM criado pelo próprio
ensaio, conferir caminho canônico/dono/modo/hashes e chamar launcher fixo sem
eval. Provar recusa de app/caminho estranho, sinal e retorno antes de solicitar
A/B supervisionados. Não habilitar ações de power/reboot/governor fora da
qualificação. C46 ainda não implementado/armado; core real/conteúdo depois.
