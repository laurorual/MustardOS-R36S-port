# C99 — fluxo instalado após migração C79

Data: 05/11/2026. Código próprio MIT. A migração C94 substituiu a p2 inteira;
o primeiro boot C97 conferiu arquivos, identidade e entropy, mas não executou
o menu ou o core. Esta sessão verifica regressões desse novo sistema instalado.

**Resultado aprovado:** sessão `c79-session/load._68hm2gh`, boot78/IP192.168.15.8,
observação `observe.zo30k5jc`. Usuário confirmou imagem, direcional, som limpo/
audível, restauração Fn+L2 e retorno Fn+Start. Recibos técnicos e fechamento
passaram:1001frames, saída hotkey0/expired0, operação0/cleanup0, mapas das três
etapas com host/provider4/core instalados, sem transferência desses ELF.
Snapshot/metadata byte-idênticos ao C63, somente status/export/verificação,
sem QuickSave. RootRO0755, PCM fechado, p3 desmontada, nenhum UI/processo da
sessão, taint0, infraestrutura e mountinfo global iguais. Cápsula removida e
página final diagnóstica escrita. Preferências55/70/mixer/DRM/brilho restaurados.

38casos novos offline e ensaio nativo de isolamento aprovados. `final-audit.json`
fecha somente os recibos autênticos da própria sessão; não simula novo SSH.
`package-phase4-c79-session.py` reúne prova sanitizada em
`dist/phase4/c79-session`, sem ROM/estado/ELF/identidade privada/UUID.
O CSV reportou61Hz recentes, quatro underruns e1971frames de áudio ausentes.
São contadores agregados, sem atribuição temporal; não contradizem nem substituem
a confirmação acústica curta do usuário. Não foi medido orçamento A→primeiro
frame, taxa sustentada ou estabilidade longa.

## Recorte

`phase4_c79_session.py` e `run-phase4-c79-session.py` reutilizam o executor
C77 congelado, sem editar suas fontes ou provas. A adaptação fica limitada
ao módulo de contexto, namespace `build/phase4/c79-session`, vínculos C97 nos
recibos e inclusão da fonte nova no mapa de integridade. Após a primeira
tentativa, inclui também um delta de isolamento de /etc descrito abaixo. Os marcadores internos
C77 continuam identificando o mesmo dispatcher e seus contratos.

Antes de SSH, verificam prova C97, recibos de coleta exit0, script regenerado,
identidade do boot, prova C94, journal, novo fence independente e composição
C93. O contador e UUID precisam corresponder ao boot C79 qualificado; um
reboot posterior exige outra observação explícita. A guarda do sistema reutiliza
os141arquivos comparados à candidata C79 por hash e metadados, root0755/ext4RO,
p1/p3 desmontadas, ausência de UI e módulos Bluetooth, além da infraestrutura.

Os ELF de host, provider e Gambatte são os instalados. Não recompila, reinstala
ou transfere core/host/store. A cápsula temporária usa o menu diagnóstico C46,
uma única ROM GB privada já fornecida e exportação somente leitura do snapshot
existente para tmpfs. O jogo tem limite45segundos e restauração Fn+L2; saída
Fn+Start. QuickSave é recusado pelo critério da sessão. Sem Power, reboot,
frontend permanente ou alteração de preferências persistentes.

O executor conserva validação de mapas, áudio, DRM, inventários do snapshot,
infraestrutura PID/starttime, montagem global, limpeza da cápsula e página
final. Término não significa aprovação sem conferir os recibos e a observação
física. Em interrupção, inspecionar estágio e processos antes de qualquer retry.

## Verificação inicial

18casos novos passaram em `c79-session/checks.149hgvpp`: lineage real C94/C97,
esquema/contador booleano ou divergente, identidade/inventário incompletos,
flags de entropy/RO inválidas, UUID diferente, observação sem vínculo C97,
adaptação finita do runner e sintaxe da guarda. Nenhuma execução no console,
rede ou core nesses checks. Os47casos aprovados C77 são reutilizados mediante
conferência de fontes e relatório byte a byte; não são contados como testes novos.

## Configuração ausente na C79

A primeira observação nativa passou no boot78, mas a abertura
`c79-session/load.i_3vi975` parou antes do menu: /etc/asound.conf não existe na
árvore C79. O worker C77 pressupunha esse arquivo. Seu manifesto de restauração
ficou parcial/vazio e registrou CLEANUP1; a inspeção adicional confirmou mixer,
DRM, brilho, volume, preferências e mountinfo restaurados, sem processos da
sessão. A cápsula foi removida com guardas verificadas; recibos preservados.

O novo worker deriva do original por três substituições finitas, sem editá-lo:
cria uma visão privada de /etc em tmpfs antes de aplicar o perfil, não inclui
o asound.conf inexistente no manifesto da raiz original e confirma sua ausência
depois de desmontar. O helper confere diretório original e template C79 por
hash/modo/tamanho/link, copia sem seguir symlinks, cria somente na cópia RAM
o arquivo644 e faz bind privado de /etc. Dados de identidade eventualmente
copiados ficam sob cápsula root-only, sem coleta/publicação. Não usa OverlayFS,
não remonta a raiz RW e não requer outra gravação de imagem.

34casos novos passaram em `c79-session/checks.e_cwdp67`: os18anteriores e
15casos de cópias reais/falhas mais verificação do worker. Cobrem preservação
de links/modos/identidade, arquivos existentes, aliases, template alterado,
hardlink, destino existente, FS incorreto e falhas de cópia/bind. Montagens
substituídas na fixture; check nativo separado verifica namespace/copy/bind/
restauração no aparelho sem iniciar GUI, áudio, core ou ROM. A primeira fixture
falhou pela umask077 no diretório fictício; corrigido apenas o preparo da fixture.

Check nativo aprovado em `c79-session/native-etc.i5gzc639`: cópia/bind real no
namespace privado, configuração444bytes/0644 correta, desmontagem e remoção da
cápsula, original ausente, rootRO, mountinfo global e infraestrutura preservados.
Não iniciou GUI, áudio ou core. Nova observação `observe.r3l93ohc` passou no
mesmo boot78 após mudança das fontes; não reaproveitou vínculo de código anterior.
Naquela revisão, sessão gráfica, confirmação física e fechamento ainda estavam pendentes.
Referências upstream somente leitura. A inspeção upstream sobre
nome do core e namespace dos saves foi reaproveitada do C77; não há nova cópia
de código upstream. Pacote permanece privado conforme revisão de licenças anterior.

### Segundo ponto ausente: /mnt/mmc

A tentativa `load.buzw5gwl` comprovou que a configuração de áudio deixou de
bloquear o preparo. O S90muos-storage parou ao criar /mnt/mmc na raiz RO;
/mnt é diretório vazio na C79. Nenhum menu/core iniciou. Operação1/CLEANUP0,
postflight, mountinfo, remoção da cápsula e página final passaram; evidências
preservadas. Não é uma aprovação funcional.

O helper passou a verificar /mnt original vazio/0755/sem alias, preparar
mnt-view/mmc em tmpfs e bindar /mnt somente no namespace da sessão. A restauração
exige /mnt/mmc ainda ausente na raiz original. Mais quatro casos de rejeição
(conteúdo, alias, modo, destino existente) elevam o conjunto novo a38casos,
`c79-session/checks.fz22lya7`. A fixture prepara as divergências antes de capturar
o inventário original; uma rodada anterior detectou erro nesse preparo e foi
preservada. As34verificações anteriores não são a suite da revisão atual.

Os serviços S90/S95/S96/S99 e o restaurador upstream de áudio foram inspecionados
para confrontar os caminhos criados com a árvore C79. /userdata, /root,
/opt/muos/log e /usr/share/alsa/alsa.conf já existem e têm isolamento herdado.
O contrato de armazenamento upstream foi reaproveitado do adaptador já GPL3;
não se copiou novo subsistema. A imagem C79 permanece inalterada: os dois pontos
ausentes deverão ser tratados no layout de uma futura imagem antes de autostart.

Check nativo da revisão atual aprovado em `native-etc.nau45w73`: cópia/bind
real dos dois diretórios, unmount e remoção da cápsula; rootRO, /etc/asound.conf
e /mnt/mmc originais ausentes, mountinfo/infraestrutura iguais. Nova observação
`observe.zo30k5jc` aprovada antes da próxima abertura gráfica. Nada foi escrito
na p2 ou em dados de usuário por esses checks.
