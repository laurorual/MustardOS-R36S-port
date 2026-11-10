# C46 — seleção nativa da aplicação diagnóstica

Aprovado em01/11/2026, no boot67/C07 do R35S. O usuário cancelou com B sem
executar o core e, em rodada separada, selecionou R35S-Diagnostic com A, moveu
o quadrado e confirmou “Tudo certo. Ao fim, voltou ao menu principal do muOS”.
Core1801frames/30s, retorno ao launcher normal20s, operação0/cleanup0.
Página final C46 restaurada; nenhuma sessão permaneceu aberta.

## Implementação

Inspecionados muxapp.handle_a/get_app_base/create_app_items/module_app e os
contratos de frontend.sh, launch.sh, runtime.sh, fileio.c e fileio_lite.c nas
refs somente leitura. A seleção nativa escreve application; module_app escreve
action=app e safe_quit. Não se habilita o frontend.sh inteiro, que inclui power,
reboot e governor fora do contrato deste ensaio.

Patch0011 em libmuxmod privada mantém handle_a nativo. Com opt-in
MUOS_PORT_APP_DIAGNOSTIC=1, mostra somente R35S-Diagnostic, verifica o alvo antes
de A e desativa aplicações embutidas, outros botões/combos/tour. B cancela
normalmente; espera por A expira120s após apresentação real. Idle delega ao
handler nativo para preservar LVGL/render. Sem opt-in, mantém o comportamento
upstream. Fonte upstream GPLv3, patch mantém licença; helpers do port MIT.
Nenhuma modificação em refs/ ou bibliotecas instaladas.

A árvore própria RAM é bindada em /opt/muos/config/port-apps/R35S-Diagnostic,
dentro da configuração já isolada pelo C45. O opt-in aponta só para esse catálogo
e reconhece apenas esse diagnóstico próprio como aplicação do port. Não se
fabrica ROM, não se registra app persistente nem se amplia confiança em outros
nomes. O bind é registrado por último no journal, para desmontar antes do config.

adapter.sh exige action/application regulares, sem symlink, com dono/modo/nlink,
conteúdo byte-exato, diretório canônico, inode igual à árvore própria e SHA256
do único mux_launch.sh contra manifest verificado pelo host. Consome uma vez;
executa somente launcher e argumentos fixos, sem eval ou comando vindo do pedido.
Application é CHAR sem LF; action é app+LF, como nas funções nativas.

A seleção também gera governor/controller escalares. O adaptador valida
respectivamente contra device/config/cpu/default e system, com tipos/modos/
links exatos, e os arquiva/remove antes do core. Não aplica opções de CPU.
Isso impede que o próximo frontend os interprete como pedidos de configuração.
Os valores conhecidos ficam nos recibos, neste aparelho schedutil/system.

CoreC40 semROM/BIOS roda30s com muxretroC44 e áudiozero. Cancel/timeout não o
executam. Falha de aplicativo ainda tenta retorno ao launcher com status separado.
O retorno usa ganchoC45 por20s, só D-pad, e saída normal. O marker C45_CYCLE_COMPLETE
é protocolo de término do worker herdado; controller exige marcadores C46 próprios
para distinguir guardas, cancel e seleção real, sem fingir prova de UI/input.

## Supervisão e isolamento

Worker C46 difere do C45 somente no prazo do filho150→210, comprovado por
comparação literal; lógica de preparo/rollback/cleanup intacta. Supervisor externo
240s, frontend135s, espera por A120s; core30s/retorno20s. O supervisor C44 é
inalterado. Provas imutáveis de preparo42/sinal143 do C45 são conferidas por
checksums e SHA do parent, sem repetir serviços já qualificados.

Mantém RO+noload+RAMprefs, /run/muos e /tmp privados, sysfsCPU/powerRO e nenhuma
escrita de preferências de volta. C36 IRQ/RW/215/q1024 e preferências55/70
preservados. O helper de página final roda somente após c25_ready/boot correto/
PCMclosed/ausência de UI, depois da coleta e remoção da cápsula.

## Provas finais

Build `app-selection/build.srarmig3`, libmuxmod SHA256
`1ec8acd906ee25bd83b59c0c5818e7310d62bfeaabadb2b473e03562d7d6bcc9`.
Somente muxapp recompilado; C45/baseSDK/libs instaladas preservados.
Checks `checks.xi4zo5pf`: hook AArch64/QEMU, binding imediato, escritores e leitor
REAIS do snapshot compilados em AArch64,13casos de coordenador com supervisor
real e seis guardas de arquivo em fixture. Incluem app/caminho estranho, symlink,
modo/hash alterados, consumo repetido, mount ocupado, argc extra, LF indevido,
governor inesperado, cancel/timeout e falha de app com retorno. Fixture do
retorno recusa governor/controller pendentes.

| Prova nativa | Stage em build/phase4/app-selection | Resultado |
| --- | --- | --- |
| Guardas finais, semUI/semapp | cycle.8sde38we | 6casos, operação0/cleanup0 |
| B cancela | observe.rheerwqk | cancelled/0/cleanup0; usuário confirmou |
| A/core/input/retorno final | observe.ltxracns | selected-app-returned/0/cleanup0;1801frames/30s, retorno20→84 apresentações |

B foi aprovado antes da correção do formato das opções e ampliação do prazo.
Esse caminho não executa adapter/launcher; muxapp.c e ramo de cancelamento
continuam idênticos. O publisher verifica código do ramo e header com único
delta60→120s, mantendo os IDs/SHA realmente usados no recibo, sem reclassificá-lo.
Não houve repetição física de B.

Perguntas físicas vieram após recibos independentes de apresentação e PID/starttime
ativo. Todas as coletas finais preservaram raizRO/fundação97/taint0/rede/PIDs,
bytes de preferências e mounts globais; MUOSDATA desmontado, RAM removida,
PCMclosed e sem UI. Página final C46 enviada. Console no67/IP192.168.15.16:2222.
Sem reboot/token C12/C25/instalação/kernel/DTB/partição/uso do Deck. Original
32GB dArkOSen intacto; C38 privado não gravado nem recomposto.

Prova pública dist/phase4/native-app-selection, gerada por
port/scripts/package-phase4-app-selection.py, SHA256SUMS conferidos. Fontes,
relatórios, bytes de pedidos do teste e marcadores selecionados; sem ELF/imagem/
blob, cópias/fingerprints de preferências reais, backups, chaves, seed ou credenciais.

## Ocorrências preservadas

- cycle.85guoo0j: imagem mínima não contém pasta bundled /opt/muos/share/application;
  parou antes de UI, cleanup0. Catálogo transferido à configuração RAM existente.
- Recusa de mount ocupado foi convertida de !findmnt/set-e em if/exit64 explícito;
  acrescentados testes de mount ocupado e argc extra antes da UI.
- observe.fn6v2kt7: A recebido e saída normal da UI, mas adapter esperava LF em
  application. Writer CHAR nativo não o grava. Corrigida comparação estrita e
  fixture; writer real noQEMU passou a garantir o formato antes de testes de host.
- observe.ox7plzw_: core e D-pad passaram, mas retorno abriu muxgov/No Governors
  Found. Opções escalares pendentes eram lidas como pedido; read_line_char_from
  devolve string vazia não-NULL para linha ausente, e process_action testa NULL.
  Corrigido consumo de opções. Operação1/cleanup0; não qualifica retorno.
- observe.tjq6258h e observe.w84de_5z: expiraram sem A; sem core e cleanup0.
  Usuário pediu explicitamente repetição em ambos. Dois timeouts justificaram
  janela por A120s e limites maiores, mantendo core/retorno curtos e bounded.

Relatos e resultados negativos permanecem separados das provas finais positivas.
Um outcome antigo app-failed-returned sem marcador de retorno foi corrigido no
controller para unexpected-exit; o recibo histórico não foi reescrito.

## Limites e próximo incremento

Qualifica o contrato de aplicação nativa com core diagnóstico, sem emulador real,
conteúdo comercial, BIOS ou saves persistentes. Áudiozero não qualifica acústica
de jogo; não demonstra desempenho ou estabilidade geral. UI permanente continuaoff.

Próximo C47: escolher um core real com licença verificada e conteúdo original ou
redistribuível, fixar fontes/ABI e compilar em container com o SDK existente.
Antes de qualquer implantação, conferir loader/API e adaptar o contrato explícito
de conteúdo, distinto de --no-content. Manter execução RAM/RO e erro/sinal/retorno
bounded; não ampliar o despachante para comandos arbitrários nem habilitar power.
Só então pedir teste físico de gameplay. Ainda não implementado/armado.
