# C52 — armazenamento versionado de quicksave

Concluído em 02/11/2026, C07/boot68/IP192.168.15.14:2222. O novo utilitário
muos-save-store passou 34 fixtures A35/QEMU e transações nativas em ext4 numa
imagem temporária de 16MiB em RAM. O volume real de dados foi auditado apenas
ro,noload; preferências55/70 ficaram byte-idênticas. Nenhum save comercial,
ROM, áudio, frontend ou input foi executado neste incremento.

## Auditoria e decisão

O muOS nativo mantém estados em pickles/state, além de histórico, trash,
manifestos e índices de retomada. Conferidos refs/muos/frontend/retro/state/
gamestate.c, core/paths.h e refs/muos/internal/script/device/bind.sh. Frontend
e internal são referências GPLv3 somente leitura. S90muos-storage do port faz
bind de toda a árvore pickles e de outros diretórios; C43/C51 já qualificaram
os aliases em RAM. Liberar esse bind inteiro para ext4 permitiria escritores
além do quicksave. A integração futura usará cópia seletiva RAM↔store após
saída limpa/flush do host, mantendo os demais escritores temporários.

A auditoria real C52 confirmou pickles e save preexistentes, root:root0700,
e MUOS/port-saves-v1 ausente. O novo store ficará separado dessas árvores;
nenhum diretório foi criado no cartão. O C20/C22 data-functions continua
pinando UUID/label/layout e cartão128 antes da montagem privada. Rootglobal
permaneceu ro, p3 apenas ro,noload/nosuid/nodev/noexec. A leitura do record de
preferências usou cmp; o helper de preferências abre seu lock em modo de
escrita, portanto não foi chamado sobre o volume somente leitura.

## Implementação própria MIT

port/utils/muos-save-store.c é uma biblioteca CLI limitada ao diagnóstico;
não é instalada nem chamada pelo boot. Compilada AArch64/A35, PIE, relro/now,
stack protector, -Wall/-Wextra/-Werror e zlib do SDK existente. Não copia
implementação upstream; usa os fatos de formato PKST já conferidos no C51.
O contrato executável/documentado está em save-store/contract.json.

O diretório deve preexistir, root:root0700, sem componentes symlink, em ext4
ou tmpfs, com marcador próprio600/nlink1. O guard de mídia/mount é obrigação
do adaptador chamador, como no store de preferências. Input e exportação são
restritos a diretórios tmpfs0700; exportação exige destino vazio. Cada folha
deve ser regular, root:root600, nlink1 e no mesmo filesystem/dispositivo do
diretório aberto. Leituras usam openat/O_NOFOLLOW/O_NONBLOCK e limites prévios
à alocação. O store não aceita caminhos arbitrários de conteúdo nos bundles.

Cada geração é um único arquivo imutável NNNNNNNN.bundle contendo exatamente
quicksave.state, states.ini e quicksave.png. Header MUOSSAV1 de128bytes guarda
versão, tamanhos, CRCs, identidade privada e padding zero. O PKST interno
também passa tamanho/flags/coreCRC; o manifesto deve conter grupo quicksave
e nenhum NUL; a miniatura passa assinatura PNG. O inspetor C51 continua
necessário para validação semântica adicional dos campos do manifesto. PNG
não é decodificado. CRC detecta corrupção acidental, não autentica dados.

HEAD contém identidade, CURRENT, PREVIOUS e NEXT. O chamador deve derivar a
identidade de domínio versionado mais hashes exatos de ROM/core, mantendo-a
privada. Fixtures usam identidade sintética constante. O utilitário confere
a identidade em HEAD e no bundle antes de ler/restaurar; não decide sozinho
qual ROM/core estão executando.

Commit: flock exclusivo não bloqueante → criação exclusiva da geração →
fsync arquivo → fsync diretório → .head.new exclusivo → fsync → rename HEAD
→ fsync diretório. Os três arquivos não são publicados separadamente, evitando
um ponteiro de geração que misture estado e manifesto. Gerações anteriores
permanecem intactas. Há teto explícito de32 commits e nenhuma coleta de lixo;
ao atingir o teto, retorna73 preservando os dados. Esse limite é adequado ao
ensaio; manutenção para uso permanente ainda precisa de implementação.

Recover é explícito: valida PREVIOUS, publica-o como CURRENT, zera PREVIOUS
e preserva NEXT e todas as gerações, inclusive a corrompida. Não há fallback
automático, reset de defaults ou adoção de órfãos. Falha antes de publicar
HEAD mantém o anterior; uma geração órfã pode bloquear o próximo commit para
inspeção. Falha de sync após rename retorna74, com durabilidade desconhecida;
não tenta desfazer o HEAD visível. Staging desconhecido nunca é removido.
Inicialização recusa diretório com órfãos e HEAD ausente. Marcador e seus
diretórios devem ser criados exclusivamente e sincronizados pelo adaptador
antes do primeiro uso durável.

## Verificação

check-phase4-save-store.py, stage checks.ddn_42op: 34 fixtures sintéticas,
incluindo duas gerações, exportação byte-exata, corrupção/recuperação, próxima
sequência após recover, identidade errada, PKST/manifesto/PNG inválidos,
modos/links/FIFO/tamanho, destino não vazio, lock concorrente, HEAD inválido,
limite32 e falhas de fsync em quatro fronteiras. Fixtures distinguem a falha
de sync depois de rename e conferem que o HEAD novo permanece visível; não
simulam perda elétrica. SAVE_STORE_TEST existe só no ELF de teste.

A primeira preparação de container recusou acesso ao stage como usuário0
mapeado; foi separada em compilação com keep-id e execução root em tmpfs,
sem afrouxar o diretório do store. A primeira execução QEMU também mostrou
que -L sysroot redirecionava a abertura de / durante o walk por descritores.
O runner agora usa loader AArch64 explícito/-L /, como no laboratório C19.
As tentativas anteriores foram preservadas em build; nenhuma chegou ao console.

prepare-phase4-save-store-ext4.py, ext4.uc9ox2nw: reutiliza as funções de
ownership/mount/loop do C19 byte-idênticas, verificadas pelo script. O helper
aceita apenas uma imagem regular tmpfs16MiB num diretório próprio com prefixo
fixo, nunca cartão/bloco por argumento. Kernel LOOP_SET_FD não substitui loop
ocupado, backing inode/dev é conferido, AUTOCLEAR e namespace privado. A imagem
foi formatada somente no container sob build/, com features compatíveis com
kernel4.4. SDK/config e refs preservados.

run-phase4-save-store.py, native.0o0k0_gb, boot68: auditoria real RO seguida
do laboratório novo. Gravou gerações A/B, desmontou, remontou RO, exportou B
byte-exato e recusou init/commit RO e fonte ext4. Em RW corrompeu somente a
geração B sintética; export foi recusado; recover selecionou A e preservou B.
Nova desmontagem/remontagem RO exportou A byte-exato. Imagem coletada apenas
após loop desmontado/desanexado; fsck -fn offline passou e HEAD final tem
CURRENT1/PREVIOUS0/NEXT3. Não repetiu API/emulação/hotkeys/rollback/UI/áudio.

InfraPIDs, mounts globais, rootRO/fundação97/taint0/PCMclosed e preferências
preservados; cápsulas, imagem e executáveis RAM removidos. Tela permanece no
diagnóstico C51, pois não houve sessão gráfica. Cartão original32 e SteamDeck
não participaram. Não houve instalação, reboot, token ou escritor durável novo
no cartão. Prova save-store-laboratory contém apenas fontes/análises/recibos,
sem ELF, imagem ext4, estado ou miniatura, mesmo sendo dados sintéticos.

## C53 preparado — integração limitada ao conteúdo já qualificado

1. Derivar/pinar a identidade privada do ROM/core C49/C50. Usar o guard C20,
   namespace e lifetime lock existentes; montar p3 privadamente e conferir a
   ausência de MUOS/port-saves-v1 antes da inicialização exclusiva e seus syncs.
   Preservar hashes das preferências antes/depois. Não instalar o CLI no root.
2. Após S90 criar storage RAM, exportar um snapshot válido à pasta temporária
   vazia e colocar apenas as três folhas no caminho nativo core.so/GB/private.
   Preservar --fresh/autosave0; recuperação no jogo será manual por Fn+L2.
3. Depois de save/saída limpa, flush e inspetorC51 aprovado, montar o store RW
   apenas no namespace e publicar nova geração. Não persistir histórico,
   resume index, opções, CSV, SRAM ou preferências através desse caminho.
4. Fazer duas sessões supervisionadas: salvar/sair, depois carregar/confirmar
   a mesma posição/voltar ao menu. Conferir desmontagem/remontagem, backup e
   limpeza sem coletar qualquer estado comercial. Reboot é passo posterior.

Ainda não qualificados: save comercial no cartão, integração automática,
durabilidade após reboot/perda elétrica, coleta de lixo e longa duração.
Os underruns agregados C51 permanecem pendentes; C52 não executou áudio nem
atribuiu causalidade a save/load. Power/suspend/flash permanecem fora do ensaio.
