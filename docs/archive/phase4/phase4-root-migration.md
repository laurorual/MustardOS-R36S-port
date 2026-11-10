# C80 — plano de migração da raiz e recuperação

Concluído em04/11/2026. O R35S foi observado em192.168.15.18/boot72, com a
mesma instalação C76/C77. Este incremento implementa um planner e um validador
de recibos futuros, sem writer, provisionador ou operação física armada.
Não houve backup offline nem construção de candidato provisionado.

## Estratégia e evidência real

A factory C79 contém duas partições; o cartão128 atual contém três, incluindo
o userdata C20 com preferências e snapshot. Aplicar a raw inteira não preserva
essa instalação. O [planner](../../port/scripts/phase4_root_migration.py)
seleciona somente p2, offset134.217.728bytes/tamanho536.870.912bytes. Protege
explicitamente os intervalos0..128MiB e640MiB..fim do cartão; MBR, bootchain,
FAT e p3 permanecem fora da futura escrita. Os intervalos cobrem exatamente
os127.934.660.608bytes do test128, sem sobreposição.

O [coletor](../../port/scripts/prepare-phase4-root-migration.py) verificou
rootRO0755/quiescência,40folhas host/provider/core e132pré-requisitos,
fundação97, boot/UUID, capacidade/setor/CID/modelo/kernel/PARTUUID e MBR
completo. Leu16MiB do prefixo público e comparou com C79 após inserir somente
a entrada p3 existente; o restante coincidiu. Infraestrutura PID/starttime e
MBR ficaram iguais ao final. Não montou p3, não iniciou áudio/UI, não
recarregou RNG/rede, não alterou arquivo nem solicitou reboot.

Foram registrados metadados e hashes de seis arquivos de provisionamento,
sem exportar conteúdo de configuração de rede, seed ou chave privada:

| Arquivo | Modo observado/política |
| --- | --- |
| etc/muos-network-authorized_key | root0644, chave pública |
| var/lib/muos-network/network.conf | root0600 |
| var/lib/muos-network/dropbear_ed25519_host_key | root0600 |
| var/lib/muos-network/dropbear_ed25519_host_key.tmp.pub | root0600, auxiliar opcional preservado |
| var/lib/muos-seedrng/seed.credit | root0400,32..256bytes |
| var/lib/muos-diagnostic/boot-seq | root0600, valor72 |

`seed.no-credit` também é admitido opcionalmente em0400. Diretórios privados
precisam ser root0700, folhas regulares sem symlink/link extra; o coletor
recusa entradas desconhecidas, inclusive ocultas, nos diretórios de rede e
seed. As regras reproduzem o contrato nativo C06/C07: `entropy_file_valid()`
exige0400 e `network.sh` exige0600 para configuração e host key. A chave
autorizada pública e o `.tmp.pub` são preservados com seus modos reais.

A primeira coleta parou na entrada `.tmp.pub`, ausente da política inicial;
também revelou os modos0400/0644 distintos da hipótese0600 geral. A política
foi corrigida por caminho, sem mudar modos no aparelho ou aceitar caminhos
arbitrários. A segunda coleta passou com a guarda do prefixo C79 e enumeração
incluindo arquivos ocultos. Nenhum conteúdo privado foi copiado nas tentativas.

## Contrato de backup e provisionamento

O validador `bind_backup()` recebe recibos **calculados pelo futuro controller**.
Não autentica JSON fornecido por terceiros e não autoriza IO; seu resultado
continua `execution_enabled=false`/`device_writer_available=false`. O backend
deverá conferir a integridade do plano e derivar os recibos dos descritores
guardados, em vez de aceitar hashes/booleans prontos por RPC.

1. Fazer desligamento normal após preflight; colocar somente o test128 no
   leitor offline. O original32 permanece separado. Observar novamente a
   identidade real; se o contador mudou desde o survey, gerar um novo vínculo.
2. Usar helper temporário com operações de backup/leitura limitadas. Recusar
   cartão original/desconhecido, mounts em qualquer namespace, swap/holders,
   aliases ou geometria incorretos. Revalidar CID exato específico do leitor
   Deck, MBR e prefixo16MiB. Sincronizar caches dos aliases identificados,
   incorporando a correção C20; não usar `drop_caches` global.
3. Copiar o prefixo atual640MiB para arquivo privado fora do cartão, conferir
   fsync/readback/hash e fsck offline sem reparo. Copiar uma segunda versão
   independente para este host, verificar hash/fsync e só então reconhecer o
   backup. Não reutilizar o prefixo histórico C20 como backup atual.
4. Fazer também backup lógico verificado de preferências e store de saves em
   p3, por mount privado ro,noload,nosuid,nodev,noexec e guardas C20/C53. Não
   executar código da mídia, formatar p3, recriar markers ou inicializar saves.
5. Preparar cópia da raiz C78 extraída da C79. Inserir apenas os arquivos da
   allowlist obtidos do **backup offline fresco**, com modos/owners/link1 e
   contador preservados. Seed pode ter mudado no desligamento: a candidata
   precisa do seed desse backup, não da amostra live nem de backups antigos.
   Rede, host key e chave autorizada devem manter a identidade do survey.
6. Conferir árvore pública byte-idêntica à factory, exceto allowlist/novos
   diretórios privados previstos; recusar tokens, PIDs, caches e runtime.
   Não carregar o seed, gerar chaves ou executar init na montagem host.
   A candidata provisionada tem hash próprio e não pode ser a factory nua.
7. Somente um backend futuro testado poderá publicar os512MiB na p2 offline,
   com descritor exclusivo, tamanho/identidade fixos, fsync e readback. Conferir
   prefixo protegido, MBR/p1 e identidade/conteúdo lógico p3 preservados,
   sincronizando aliases antes das leituras. Não habilitar escrita de raw640MiB,
   reparticionamento ou restore global. O planner atual não faz esse passo.

## Recuperação e seed

`recovery_policy()` distingue duas fases, ambas sem execução automática:

- **Antes de qualquer tentativa de boot:** restauração byte a byte somente
  da p2 pode ser elegível a partir do backup novo verificado, conservando
  MBR/p1/p3. Essa elegibilidade é uma regra; não é evidência de operação feita.
- **Depois de uma tentativa, mesmo falha:** restauração cega da p2 antiga fica
  inelegível. Pode repetir seed já creditado e recuar contador. Será necessário
  procedimento separado para seed fresco/sem crédito e contador monotônico,
  baseado no estado observado. Não afirmar que uma tela apagada prova ausência
  de boot. A futura operação precisa de um marco conservador de tentativa
  antes de entregar a mídia ao aparelho, sem inferir sucesso pela rede.

Não rearmar C12/C25, não usar uma segunda carga de seed no mesmo boot e não
fazer rollback automático após perder SSH. A revisão da recuperação pós-boot
é pré-requisito para a qualificação física da candidata; C80 não a implementa.

## Verificações e artefatos

[84 casos puros](../../port/scripts/check-phase4-root-migration.py) passaram,
com registros sintéticos e sem dispositivos/secrets. Cobrem geometria de três
partições, proteção de toda a mídia, CID original/leitor errado, modelo/kernel,
tipos/MBR/PARTUUID/saúde, allowlist/modos/owners/links/seed/contador, factory
inadequada, mounts/swap/cache, backups independentes/fsync/fsck/userdata,
mudanças de identidade, seed live antigo na candidata, reset de contador,
tokens/árvore pública e recuperação antes/depois de tentativa de boot.

Survey/plano privados em `build/phase4/root-migration/plan.fobcof88`;
checks em `checks.m3djb50i`. Prefixo público/MBR e metadados ficam sob0700/0600
no build ignorado. O plano público na prova é redigido e não executável.
Prova `dist/phase4/root-migration` contém fontes, casos sintéticos e resumos,
sem UUID live, hashes de arquivos privados, MBR/prefixo binários ou credenciais.

C80 não alterou o console, cartões, SDK, imagens C78/C79 ou Steam Deck.
O console continua sem sessão armada; último pre/postflight aprovado foi no72,
com rootRO/PCMclosed/p3off/UIoff/taint0/rede e infraestrutura preservados.
Não houve novo jogo nem teste físico repetido. Licenças/private-only do C79
permanecem pendentes. Próximo C81: implementar/testar o helper offline de
backup limitado e recuperação pós-boot antes de propor qualquer escrita real.
