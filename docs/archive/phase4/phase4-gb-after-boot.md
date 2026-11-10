# C54 — restauração do snapshot em um novo boot

Concluído em 02/11/2026, consoleC07/IP192.168.15.14:2222. A primeira leitura
real já mostrou boot69, enquanto C53save/load foram concluídos no68. Kernel
4.4.189-muos-r35s-p4, uptime153,85s, rootRO0755/taint0/PCMclosed e rede pronta.
Não foi solicitado outro reboot: o ensaio aproveita o novo boot observado.
O método de desligamento anterior não foi acompanhado; não qualificar
shutdown normal controlado ou perda elétrica a partir do contador.

## Integração restrita à leitura

run-phase4-gb-reboot.py exige --source-save e --source-load explícitos. Ambos
devem estar em build/phase4/gb-persist e coincidir, após redação de identidade
e hashROM, com os recibos imutáveis C53. Confere todos os SHA256SUMS e hashes
dos fontes, prova física C53, limpeza/RAMremovida/rootRO/mounts e assets atuais.
Deriva novamente a identidade privada dos mesmos bytes de ROM/core.

phase4_gb_reboot.bind_source exige origem save/load do mesmo boot, roles e
resultados corretos, identidade/assets idênticos, contadores inteiros e boot
atual exatamente origem+1. C53 original continua exigindo mesmo boot; sua
guarda não foi removida. Este adaptador é limitado ao ensaio68→69.

Novo gate gb-reboot/store.sh aceita somente seed/verify e role exatamente
loadLF, arquivo root600/nlink1. BackendC53 é conferido por SHA, tipo, owner,
modo e links antes de delegar. Inicializador e prepare.sh não são enviados.
Store é montado RO/noload e exportado para RAM; C52 valida bundle/identidade,
C51 valida estado/manifesto/assinatura PNG. Antes e depois do jogo, o
inventário/hash do store deve coincidir com o registro final do boot68.
Geração1 não pode ser regravada ou removida pelo fluxo C54.

HostC50, GambatteC49, ROM, UIlibC46, runner, worker e sessão/seletor/launcher
C53 permanecem byte-idênticos. Refs não foram modificados. Não houve novo
build de ELF, SDK ou imagem; somente adaptador/gate próprios MIT. Não se
repetiram API, USB, rollback, bootstrap do store, save, áudio ou reboot.
Prazos herdados: menu120s, conteúdo45s, retorno20s, owner210s/externo240s.
Autosave/timeline/flush periódico/autoloadoff, --fresh e runtimeRAM preservados.

## Checks

checks.guod5xw0 passou26casos locais: novo boot vinculado, recusas a mesmo
contador/salto/bool/origens divergentes, falha/cleanup/RAM/root/mounts, roles,
identidade/core/ROM/host e gate seed/verify versus prepare/commit, role incorreta,
LFextra, backend adulterado/symlink/hardlink. Backend das fixtures é um stub;
não há acesso ao dispositivo ou ROM privada nesses testes. C53/32casos e
C52/34casos são reutilizados por provas/hashes, não reexecutados.

## Resultado

Usuário confirmou presença e respondeu **“Tudo certo”** à pergunta específica
do boot69: mover Mario, Fn+L2 restaurar a posição do boot68 e Fn+Start voltar
ao menu, sem salvar. Stage load.x7a7858i registrou load real, saída hotkey/
expired0/906frames e retorno normal. Metadados de26861bytes do core passaram
PKST/CRC/manifesto/assinatura PNG e coincidiram antes/depois do jogo.

Inventário/hash do store no boot69 ficou byte-idêntico antes/depois e ao
registro final do boot68. HEAD permanececurrent1/previous0/next2. Nenhum save
novo, reset ou recuperação foi executado. Operação0/cleanup0, rootRO0755/
fundação97/taint0/PCMclosed, prefs55/70/mixer/DRM/WirePlumber, infraPIDs e
mounts globais preservados. p3 desmontado; cápsula, ROM/helpers/estado RAM
removidos, tela finalC54 enviada. Geração1 comercial permanece somente no128.
Original32 e SteamDeck preservados; sem instalação, token, flash ou reboot
solicitado pelo agente. Nenhum estado, manifesto, PNG ou PCM foi coletado.

CSV registrou4callbacks de underrun/3eventos/1932frames ausentes(~0,059s),
semtimestamps dos eventos; não atribuir causa ao load. O core_hz recente foi
58,9971; isso não mede throughput absoluto da sessão. Não dividir906por45,
pois o encerramento foi voluntário. Não houve nova calibração de áudio ou
clocks. Estabilidade de áudio nas interações e duração prolongada continuam
abertas. Usuário não relatou problema audível.

Prova gameboy-after-boot contém somente fontes/análises/observação/recibos,
com identidade/hashROM/bootUUID redigidos. Nenhum ELF, imagem, estado, PNG,
PCM ou segredo. Provas C53/C52 e suas guardas permaneceram imutáveis. O
resultado qualifica restauração após o novo boot observado68→69, sem
qualificar o método de shutdown, coldboot controlado ou perda elétrica.

## Próximo incremento proposto

Consolidar o utilitário genérico C52 como pacote/receita Buildroot opt-in,
com dependência zlib e licença MIT, defaults desativados e sem ROM/core/estado
privado no payload. Conferir ABI e manifests da composição privada antes de
qualquer instalação. O bridge de diagnóstico C53 não deve virar writer amplo
de pickles nem autostart por efeito da receita. SRAM, GC, longa duração,
recuperação de corrupção real, shutdown/Power/suspend e desempenhoNES seguem
trabalhos separados. Nenhum C55 está armado.
