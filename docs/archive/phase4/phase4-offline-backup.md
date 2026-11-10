# C81 — helper de backup offline, preparado e testado no host

Preparado em **04/11/2026**, seguindo a instrução do usuário: **“Prepare
somente offline por enquanto.”** Não houve SSH, acesso ao R35S/Steam Deck,
desligamento, troca de cartão ou backup real. O último estado nativo conhecido
continua sendo o survey C80, boot72; não foi revalidado neste incremento.

O próximo passo da migração C79 exige preservar o estado privado e os saves
do cartão de teste. Este incremento fornece esse caminho de backup; não
implementa provisionamento, gravação de raiz nem recuperação pós-boot.

## Implementação

| Componente em `port/scripts/` | Responsabilidade |
| --- | --- |
| `phase4-offline-backup.py` | Helper local de execução única no Deck, somente `backup` |
| `phase4_backup_core.py` | Cópias delimitadas, extração privada e arquivo lógico p3 |
| `collect-phase4-offline-backup.py` | Conferência e `fsync` da segunda cópia no host |
| `prepare-phase4-offline-backup.py` | Pacote privado vinculado ao survey e às fontes testadas |
| `check-phase4-offline-backup.py` | Casos sintéticos e teste de filesystem em container |
| `package-phase4-offline-backup.py` | Prova pública sem pacote privado ou payloads |

O helper usa Python/stdlib e ferramentas já existentes no Deck. Nenhuma
dependência foi instalada no host, nenhum ELF AArch64 foi alterado e nenhuma
referência upstream foi modificada. A política C80 é importada sem alterações.
O primitivo de sincronização dos aliases reaproveita o contrato MIT do helper
C20, sem incorporar seu servidor, formatador, reparador ou comandos de restore.
Marcadores e permissões de userdata seguem C20/preferences e o store nativo
`installed-core-session/store-base.sh`.

Antes de importar o núcleo de IO, o bootstrap exige sudo local/Deck x86_64
Jupiter ou Galileo e copia os quatro arquivos permitidos para diretório
root0700 imprevisível em `/run`, com folhas0400 e hashes conferidos. Reexecuta
esse snapshot com ambiente fixo. Isso protege a transferência e a execução
contra alteração posterior do pacote; não autentica um pacote malicioso criado
por alguém com poder de sudo. O pacote precisa de revisão e origem confiável.
Não há socket, servidor persistente, shell remoto nem ação `serve`, `format`,
`partition` ou `restore`.

## Leitura planejada no Deck

O fluxo ainda **não foi executado em hardware**:

1. Isolar namespace de montagem; conferir CID exato do alias do test128,
   ausência do original32, capacidade/setor e geometria das três partições.
   Recusar mounts em qualquer namespace, swap e holders, sem desmontar volumes
   alheios. ENOENT/ESRCH/EINVAL de processos sem namespace são os únicos erros
   ignorados; acesso negado aborta.
2. Sincronizar/invalidar caches p1→p2→p3→whole por descritores somente leitura;
   abrir o cartão exclusivamente, conferir rdev/capacidade/MBR/prefixo C80.
   `fsync`/BLKFLSBUF podem concluir buffers pendentes anteriores: não representam
   um writer de payload e não são uma garantia de ausência de IO físico.
3. Criar em `/var/tmp` persistente e fora do cartão um diretório root0700,
   exigindo pelo menos3GiB livres. Copiar640MiB de prefixo, conferir segunda
   leitura da fonte e hash da cópia após `fsync`. Extrair FAT100MiB e raiz512MiB
   desse arquivo regular, com hashes e `fsck.fat -n`/`e2fsck -fn` retornando0.
4. Ler a allowlist privada da raiz copiada via `debugfs` sem `-w`. Validar pais,
   tipos, modos, dono, link único, tamanhos e membros ocultos. Rede/key/auth
   precisam coincidir com C80; contador deve manter o mesmo boot; seed pode ser
   o mais recente salvo no desligamento. Não executar código da imagem,
   carregar seed, gerar chave ou inicializar serviços.
5. Conferir tipo/label/UUID p3 e exigir `e2fsck -fn`0 sem reparos. Montar apenas
   p3 no namespace privado com `ro,noload,nosuid,nodev,noexec`; conferir também
   `noload`/`norecovery` no mount real. Criar USTAR somente com marcador do
   volume, `MUOS/preferences` e `MUOS/port-saves-v1`, com duplo inventário e
   leitura integral do tar. ROMs e o restante da p3 ficam fora do backup lógico.
6. Desmontar somente o mount próprio, abrir novamente o cartão guardado e
   confirmar hash dos640MiB. Só então produzir recibo, sincronizar arquivos e
   diretórios e entregar o backup privado ao usuário `deck`, folhas0400.

Limites: arquivos privados<=64KiB; userdata até2048entradas/profundidade12,
32MiB por arquivo/64MiB total, diretórios0700/folhas0600 e dono root. Não admite
symlinks, hardlinks, objetos especiais ou nomes fora da allowlist de caracteres.
Esses limites cobrem o contrato atual de bancada; excedê-los exige revisão,
não fallback. Comandos externos têm prazo180s e qualquer retorno nãozero
aborta, inclusive filesystem sujo e timeout. Não tenta reparar nem retomar.

O coletor local exige diretório privado0700 e inventário exato. Confere cada
hash/tamanho, FAT/raiz contra os intervalos do prefixo, identidade C80,
arquivos privados e tar com marcadores, modos, caminhos e conteúdo. Sincroniza
cada arquivo e diretório antes de emitir `independent_host_copy_verified=true`.
O recibo inicial do Deck traz esse campo falso. JSON recebido isoladamente
não autoriza IO, e nenhum desses recibos habilita escrita ou provisionamento.

Em erro, cópias parciais ficam privadas e não devem ser assumidas completas.
O cleanup recusa remover recursivamente o snapshot se ainda existir mount
sob ele. SIGINT/TERM passam pelo cleanup; SIGKILL/queda elétrica podem deixar
snapshot/mount/cópia incompleta, exigindo inspeção posterior. Não há restore
automático nem garantia de atomicidade contra perda elétrica.

## Validação concluída

**72 casos passaram** em `checks.y1i3sznc`. Os testes do host usam sysfs/proc,
descritores e recibos sintéticos; nunca abriram dispositivo físico. Cobrem
cartão original/desconhecido, host/capacidade/setor/partições errados, holders,
swap, mount de outro namespace, permissões negadas e processos já encerrados;
também falhas de fsck/timeout, opções de mount, cópias curtas, arquivo existente,
symlink, falha de escrita/fsync e fonte alterada.

O teste da segunda cópia usa arquivos regulares esparsos de dimensões reais e
recibo sintético: seus campos fsck0 não são resultados de fsck de um cartão.
Os casos verificam hash/fsync e recusam arquivo extra, payload alterado, outro
plano/boot, provisionamento, fsck inválido e tar com duplicata/traversal/link/
escopo/modo/marcador incorretos. O pacote tem inventário/hash/modos conferidos;
bootstrap é exercitado com exec e privilégios simulados, sem montar ou iniciar
o snapshot de produção.

Em container existente, sem rede/dispositivos/privilégios, uma ext4 sintética
de16MiB passou por `mke2fs`, `e2fsck -fn` e extração real via `debugfs`, incluindo
os modos seed0400/auth0644 e contador. O backup lógico real em tar passou por
leitura e inventário repetido, com recusas de links, modos, marcador e tamanho.
Isso valida os componentes; não qualifica namespace, reader, ferramentas,
filesystem de destino ou operação completa no Steam Deck real.

Pacote privado: `build/phase4/offline-backup/package.hnizy8zj/bundle`.
Contém o plano C80 do boot72 com hashes privados; não deve ser publicado.
Prova em `dist/phase4/offline-backup` contém fontes, casos e resumos, sem plano
privado, UUID live, hashes das folhas privadas, ROM, seed, chave ou backup.
Configuração SDK comparada ao baseline, sem alteração.

## Retomada

Na próxima etapa autorizada para hardware, verificar o estado real do R35S;
se houve novo boot, refazer somente o survey/vínculo C80 e regenerar o pacote.
Depois preparar o Deck e agendar desligamento normal e transferência física
do test128. Não reutilizar o helper C20 de formatação. Nenhuma dessas ações
foi iniciada agora; o original32 permanece fora do fluxo.

Após qualificar backup real e cópia independente, ainda é obrigatório
implementar recuperação pós tentativa de boot com seed fresco/sem crédito e
contador monotônico antes de instalar/bootar uma candidata C79. Restore
byte-exato da p2 antiga continua inelegível após qualquer tentativa de boot.
Licenças conjuntas pendentes e artefatos private-only permanecem como C79.
