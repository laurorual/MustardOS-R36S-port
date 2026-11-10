# C100 — layout mínimo para a fábrica C79

Data: 05/11/2026. Código próprio MIT. As duas tentativas iniciais C99 mostraram
que a árvore C79 não tem /etc/asound.conf nem /mnt/mmc. A sessão aprovada
contornou essas ausências com visões privadas em RAM. O C100 incorpora os dois
pontos a uma fábrica derivada regular, sem modificar a fábrica/prova C79 ou
a imagem privada já provisionada e consumida no primeiro boot.

## Alteração

| Caminho | Conteúdo ou função | Metadados |
| --- | --- | --- |
| /etc/asound.conf | Os mesmos444bytes do template existente /opt/muos/share/conf/rootfs/asound.conf | root:root0644, arquivo regular/link único |
| /mnt/mmc | Ponto vazio para o bind do serviço S90muos-storage | root:root0755, diretório/link count2 |

Além das duas novas entradas, só o link count de /mnt cresce2→3 no inventário
existente. A comparação da árvore completa inclui conteúdo, tipo, modos,
proprietário, links, flags e atributos de todas as entradas anteriores.
Timestamps de inodes não integram esse inventário e não são alegados invariantes.
UUID/features/quantidade e tamanho de blocos/inodes do ext4 permanecem iguais;
contagens livres naturalmente mudam com as novas entradas.

O template é conferido por hash/tamanho/modo/proprietário/link antes de copiar.
Nenhum recurso novo de upstream é distribuído: reaproveita os bytes já presentes
na fábrica e testados pelo C99. A inspeção de S80pipewire.sh upstream confirmou
o destino /etc/asound.conf; bind.sh e o adaptador S90 existente fundamentam o
ponto /mnt/mmc. Refs somente leitura. A revisão conjunta de licenças permanece
pendente, e o pacote completo continua privado/sem redistribuição aprovada.

## Execução offline

`phase4_c79_layout.py` reutiliza apenas operações de arquivo ext4 regular de
C85/C88. Abre a fonte privada sem seguir links, confere modo/link/tamanho/hash,
segura flock e revalida assinatura/hash ao terminar. A fonte é somente leitura.
Cria saída exclusiva e esparsa, aplica exatamente as duas adições com debugfs,
faz fsync, fsck e nova leitura integral da árvore. Não monta sistemas de arquivos,
gera seed, altera contador/identidade, cria token.once ou fornece writer físico.

O entrypoint `phase4-c79-layout.py` aceita somente request privado em /work,
fábrica C79 pinada e tamanho512MiB. O host `compose-phase4-c79-layout.py`
confere provas C79/C97/C99 e os checks antes de usar o container existente,
sem rede, dispositivos físicos ou capabilities. Reutiliza a fábrica privada
original; não recompila SDK/core e não cria outro raw640MiB ou gzip.
`compose.claim` persistente impede repetir cópias após interrupção sem inspeção.

`check-phase4-c79-layout.py` passou29casos em ext4 reais32MiB/container isolado.
Cobrem árvore completa/modos/links/contador/symlink preservados, template
alterado/ausente, caminhos existentes, aliases e hardlinks, metadados inválidos,
conteúdo estranho em /mnt, hash inválido, mudança pública durante aplicação,
cópia interrompida, falha de sincronização, ext4 danificado e caminhos fora de
/work. As imagens sintéticas são removidas após os logs; a primeira rodada
terminou a fixture mas recusou sua limpeza por um alias de teste ainda presente.
O alias foi retirado pela própria fixture e o conjunto completo passou.

## Resultado da composição real

29casos aprovados em `c79-layout/checks.b8l3vm4g`; composição positiva completa
em `c79-layout/compose.1yrez0md`. A releitura da saída512MiB confirmou3406entradas,
fsck0 e o delta exato, com fábrica fonte preservada. O host conferiu novamente
hash, tamanho, metadados e a derivação do inventário. A saída esparsa ocupa
aproximadamente159MiB físicos e permanece privada em `output/factory.ext4`.
Não foi criado raw640MiB ou gzip adicional. Prova sanitizada
`dist/phase4/c79-layout` contém somente fontes, checks e relatório; nenhum payload.

## Limites de uso

A saída é uma fábrica sem provisionamento: contador0, placeholder público de
autorização inalterado e nenhum seed/host key/ROM/estado acrescentado. Não usar
essa fábrica diretamente para rede nem regravar a candidata77 após boot78.
Instalação no console e boot desta revisão não são qualificados por esses checks.

O próximo incremento pode preparar um instalador aditivo finito de444bytes e
um diretório, com preflight/ausência/recuperação e rootRO ao terminar. Não exige
uma nova migração integral512MiB nem acesso ao Steam Deck. Frontend permanente
e autostart continuam separados e desabilitados. Original32 permanece guardado.
