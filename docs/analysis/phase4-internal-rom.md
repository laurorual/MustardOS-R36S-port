# C113 — ROM interna no cartão de teste

Concluído em07/11/2026, boot82/R35S192.168.15.8. Autorização explícita do usuário
para ROM interna, com original32 guardado e cartão128 no console. Nenhum Deck,
format/repartição/regravação de p2 ou nova imagem integral. A ROM legal fornecida
pelo usuário foi importada uma vez e permanece privada, fora de Git/dist.

## Contrato

Destino p3: `MUOS/port-roms-v1/gb/private.gb`, arquivo0600, diretórios0700,
marcador próprio `.muos-rom-root-v1` e `ROM.sha256` privados0600. O importador
recusa shelf final ou staging já existentes, inclusive symlink, e não sobrescreve
conteúdo. Fonte limitada32KiB–8MiB/regular/root600/nlink1; esta ROM tem64KiB e
hash idêntico ao C109. A identidade do snapshot continua derivada de ROM/core.

O guard C112 confirma191 hashes, identidade do cartão128, geometria/UUID da p3,
C07 pronto/boot82/UUID real, rootRO e quiescência. Namespace de montagem privado
usa os data-functions/card-guard já instalados. Lock lifetime impede concorrência
com o worker. Apenas o novo shelf é gravado; configuração/saves existentes não
recebem alterações intencionais. Runtime futuro lê a p3 com ro,noload/noexec.

## Backup e escrita

`internal-rom/import.tgknjpow` guarda um backup lógico independente de43entradas,
88.064bytes, baixado antes da escrita e conferido por hashes. Tar é recusado se
contiver caminhos absolutos/.., aliases ou objetos especiais, e tem limites de
4096entradas/64MiB. Preferências55/70 e TODOS os arquivos da geração do snapshot
C109 foram comparados byte a byte por digest. Não é imagem de bloco nem backup
do cartão inteiro; recuperações C82/C89 anteriores continuam preservadas.

Uma claim host fsync impede redespacho. Escrita destacada tem done/exit/log e
collect separado: nunca repetir apply após interrupção. Depois de conferência RO,
monta RW privadamente e compara novamente o inventário antes de criar staging.
Copia ROM+registro+marcador sem clobber; fsync dos três arquivos e dos dois
diretórios; rename -nT; fsync do pai. O utilitário AArch64 do C112 passou em CLI
nativa e é verificado por hash. Falha retém staging/final para inspeção, sem
remoção/rollback automático ou repetição. Isso não qualifica queda de energia.

O inventário inclui modos/donos/tipos dos diretórios e modos/nlink/tamanho/
inode/mtime/hash dos arquivos existentes. Tamanho/nlink/mtime de diretórios não
são comparados porque o pai recebe uma nova entrada. O shelf novo próprio é
excluído desse inventário e conferido separadamente. Não há varredura raw de128GB.

## Resultado

21casos locais passaram em `checks.yolw4bqf`: shelf novo, cópia exata,
preferências preservadas, recusa de segunda importação/aliases/modos/hash/
registro/staging, retenção após falhas em cópia/flush/publicação e detecção de
alteração de arquivo externo. fsync executado por A35/QEMU em tmpfs; mídia/
namespace reais são cobertos pela execução nativa separada.

Importação nativa0, releitura após unmount/mountRO e outra verificação privada
RO passaram. Cinco inventários antes/RW/depois/remount/verify são byte-idênticos
ao original. Infraestrutura PID/starttime e mountinfo global iguais. Cápsula RAM
removida, p3 desmontada, raizRO0755/PCMclosed/UIoff; nenhum jogo/core/áudio/input
ou reboot executado. `dispatch.claim` CONSUMIDA: não repetir; backup preservado.
Prova sanitizada `dist/phase4/internal-rom-imported`, sem ROM, backup, seed,
ELF ou UUID privado. O teste gráfico fica pendente porque o usuário se ausentou.

Próximo: C114 prepara cápsula apenas com assets/ROM residentes, bloqueando leitura
da ROM local no host, valida identidade/manifestos/CLI/ABI e limpa sem abrir UI.
