# C85 — coletor de snapshot e compositor de recuperação em arquivo regular

Concluído em **04/11/2026**. Núcleo de produção passou em36casos sintéticos;
conferência da cópia real C82 de512MiB aprovada. Não há captura física
pósboot, imagem real de recuperação, provisionamento, gravação ou boot C79.
O cartão não foi acessado nesta etapa; deve permanecer protegido no Deck.
Original32, SDK e imagens/provas anteriores fora das alterações.

## Escopo e implementação

`phase4_recovery_image.py` fornece coleta e composição sobre arquivos regulares.
`phase4-recovery-image.py` é o consumidor finito de512MiB, com ações
`reference`, `collect` e `compose`. `prepare-phase4-recovery-image.py` vincula
as fontes testadas e C82/C83/C84 antes de iniciar um container existente sem
rede/dispositivos/capabilities. Não instala dependências nem executa init,
ELF, shell ou SeedRNG da imagem. Código próprio MIT; contratos C80/C81/C84
reutilizados sem editar suas fontes ou referências upstream.

Foram consultados os seletores nativos C12/C25 para interpretar marcadores
consumidos, e exercitadas as ferramentas e2fsprogs existentes. O coletor usa
somente `debugfs -R` e `e2fsck -fn` em descritores regulares somente leitura,
sem montagem ou extração de árvore por nomes fornecidos pela imagem.

O arquivo fonte precisa ser regular, dono do executor, link único,0400/0600,
tamanho exato e hash esperado. Abertura NOFOLLOW/NONBLOCK recusa aliases,
dispositivos e FIFOs; flock e assinatura de inode/tamanho/mtime/ctime, além
de novo hash integral no fim, detectam alterações concorrentes. A referência
do comando externo é `/proc/self/fd/N`, com FD herdado, evitando reabertura
de um caminho que possa ser trocado. Flock é consultivo; não autentica o dono
do host. O consumidor de produção só aceita512MiB.32MiB é usado diretamente
pelas funções nos testes, sem modo de teste exposto na CLI de produção.

## Coleta derivada do filesystem

Após fsck0, percorre diretórios por número de inode, limita profundidade32,
8192entradas, arquivos64MiB, payload agregado768MiB e atributos16MiB/64KiB
por valor. Nomes de imagem nunca entram na sintaxe de comandos `debugfs`:
stat/listagem/dump usam inodes numéricos; folhas temporárias têm nomes fixos
em estágio privado0700. Nomes com espaços e links absolutos/longos são
exercitados sem seguir links no host. Tipos desconhecidos, ciclos, atributos
não interpretáveis ou limites excedidos abortam sem fallback.

Inventário inclui conteúdo/hash/tamanho, tipo, UID/GID, modo, links, flags,
destinos de symlinks em bytes, dispositivos especiais e valores brutos dos
atributos estendidos por hash. Diretórios não são comparados por tamanho
físico/timestamps: o contrato verifica membros e metadados sem exigir layout
binário idêntico após alterar a raiz. Timestamps não são qualificados.

Ancestors privados precisam ser diretórios root0755/0700, sem links. Rede,
seed e diagnóstico são enumerados integralmente; counter/allowlist/modos/
donos/links/bytes são derivados dos inodes e dumps, inclusive ausência de seeds
após uma falha. O contador precisa ter codificação decimal canônica com newline.
`collect` reconstrói a observação C84 e seu plano antes de publicar conclusão.

O contexto de captura exige hash/tamanho da imagem, fence pinado, CID/capacidade
e afirmações de captura offline posterior, caches e namespaces. **JSON não é
autenticação:** o futuro helper físico deverá produzir isso de seus descritores
guardados. C85 não implementa esse produtor, não comprova frescor físico de
um arquivo isolado e não recebe pedidos RPC para escrever dispositivos.

## Marcadores consumidos e composição

A primeira leitura real recusou marcadores históricos que o contrato inicial
tratava como tokens de execução. A cópia C82 contém `c12.used` e oito
`c25.used.BOOTnnnn` até64. A política nativa confirma que são evidências
consumidas, distintas de `.once`. O coletor agora admite somente esses nomes
canônicos em `/var/lib/muos-diagnostic`, com root0600/link1, conteúdo nativo
exato e bootC25 não superior ao contador observado. Marcador inválido, fora
do diretório ou token ativo `.once` aborta. Históricos entram na árvore a
preservar, sem exclusão nem rearmamento.

`compose` confere novamente o backup e sua identidade privada, coleta a fonte
pósboot e recalcula o plano C84. Só então gera256bytes por getrandom não
bloqueante e cria **um novo arquivo regular exclusivo**, cópia esparsa da raiz
do backup. Nunca aceita MBR/raw640MiB como destino, abre dispositivo, modifica
MBR/FAT/p3 ou limpa a proteção RO do Deck. As duas imagens fonte ficam abertas
somente leitura e seus hashes/assinaturas são reconferidos.

No clone: normaliza raiz0755; substitui apenas contador e ambos caminhos de
seed, deixando somente `seed.no-credit`0400, contador0600 e identidade estável
igual. Restaura atributos inline dos privados substituídos, quando existentes.
Faz fsync, fsck0, novo inventário completo e leitura dos privados. Árvore pública
e identidade devem ser iguais à base, incluindo marcadores consumidos; apenas
os três caminhos de seed/contador e modo da raiz são exceções. Hash próprio
da imagem precisa diferir do backup. Recibo de sucesso é publicado por último,
após plano/fsync/validação e conferência das fontes.

**Limite explícito:** e2fsprogs1.47.2 deixou bloco externo de atributos alocado
ao remover um inode privado nas fixtures, inclusive após `ea_rm`. O fsck sem
reparo detectou a divergência. O compositor recusa previamente atributos
externos nos três inodes a substituir; não tenta liberar blocos manualmente
nem executar fsck reparador. Atributos externos da árvore pública podem ser
lidos/conferidos e permanecem intactos. Essa recusa é coberta por teste antes
da criação do clone. Outros layouts exigirão novo incremento, se encontrados.

## Validação

36casos exercitam as funções de produção, sem rede, mounts ou blocos físicos:
captura de contador75/seed ausente, recuperação76 e fsck0, normalização real
0777→0755, atributos, symlinks/especiais/espaços, preservação dos históricos,
contexto adulterado, imagens com alias/hash/tamanho/modo incorretos, token
ativo/consumido inválido, escrita curta, fsync falho, mudança pública injetada
e recusa de sobrescrita. Fontes dos testes são pinadas antes/depois da execução.
Entrypoint de produção recusa32MiB, operações extras e pedidos permissivos.

**Ressalva sobre C84:** sua fixture passava0777 à pasta usada por `mke2fs -d`,
mas não verificava esse modo no inode raiz da imagem criada. Isso não demonstra
por si só a normalização0777→0755 alegada no texto C84. C85 fixa o modo via
debugfs e exige o valor real antes/depois. As provas C84 ficam históricas e
imutáveis; o reparo físico C83 continua comprovado por sua leitura de setores,
checksums e fsck independentes. Esta ressalva não invalida os testes C84 de
contador, RNG, fence e consumo sem crédito.

Execução reference sobre a cópia host C82 aprovada:536.870.912bytes, fsck0,
3.669entradas examinadas, seis privados iguais ao manifesto C82 e nove
marcadores históricos consumidos válidos. O hash integral da imagem fonte
permaneceu igual; nenhum dos inodes privados a substituir tem EAs externos.
Não foi fabricada captura pósboot nem fence real para permitir `compose` no
estado atual. Não houve seed novo/carga, imagem real de recuperação, SSH
ou acesso ao cartão.

Privados em `build/phase4/recovery-image`: checks `checks.93azzyii` e referência
`reference.2iv_egpo`, pointers latest-checks/latest-reference. Logs e inventário
completo, com hashes privados, ficam somente nesse build; não publicar requests,
tree.json, planos ou imagens. `dist/phase4/recovery-image` contém apenas fontes,
resultados sintéticos e resumo redigido. Provas C82/C83/C84 ficam intactas.
Imagens sintéticas de execuções C85 falhas podem ser descartadas após preservar
os logs; manter a fixture final e todas as imagens/backups reais.

## Próximo incremento

Implementar a captura física pósboot somente leitura que alimente o coletor,
e o backend p2-only de aplicação/recuperação com vínculos/fsync/readback/fence.
Antes de candidata C79, qualificar o ciclo completo e planejar explicitamente
a transição das proteções C83; não remover kernelRO/regra temporária como
efeito implícito. Nenhum teste físico de menu/áudio/save é necessário agora.
